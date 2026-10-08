"""Local HTTP test doubles verify wiring. These tests do not call DeepSeek."""
from __future__ import annotations
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import re
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import httpx
from openai import OpenAI
from dotenv import dotenv_values
import configure
import live_client
import preview_agent as agent
import week1_demo as demos
from lesson_core import ROOT, LessonError, get_case, check_report, report_input, teaching_validation_case

OPTIONS = {"model": "deepseek-flash", "max_tokens": 2000, "extra_body": {"thinking": {"type": "disabled"}}}

def completion(text: str | None = "HTTP TEST DOUBLE", *, calls=None, finish="stop", refusal=None):
    message = {"role":"assistant", "content":text}
    if calls: message["tool_calls"] = calls; finish = "tool_calls"
    if refusal: message["refusal"] = refusal
    return {"id":"test-http-request", "object":"chat.completion", "created":0, "model":"deepseek-flash",
        "choices":[{"index":0,"finish_reason":finish,"message":message}],
        "usage":{"prompt_tokens":20,"completion_tokens":30,"total_tokens":50}}

def tool(name, arguments, call_id="test-call"):
    return {"id":call_id,"type":"function","function":{"name":name,"arguments":json.dumps(arguments)}}

def report_for(payload):
    # Only test doubles construct replies. Production code has no fixture path.
    return {"equipment_id":payload["equipment_id_in_record"], "observations":payload["available_observation_strings"],
            "diagnosis":None, "missing_information":payload["evidence_not_yet_available"]}

class OnlinePackageTests(unittest.TestCase):
    def setUp(self):
        work = (ROOT / 'outputs' / 'test_work').resolve()
        self.assertTrue(work.is_relative_to(ROOT.resolve()))
        work.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=work); self.output = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def client(self, handler, retries=0):
        client = OpenAI(api_key="TEST-KEY-NOT-A-REAL-CREDENTIAL",base_url=live_client.BASE_URL,
            max_retries=retries,http_client=httpx.Client(transport=httpx.MockTransport(handler)))
        self.addCleanup(client.close); return client

    def args(self, client, **changes):
        defaults = dict(case=None,temperature=None,instruction_file=None,retrieval_case="correct",include_injection=False,
                        output_dir=self.output,_client=client,_options=OPTIONS)
        return SimpleNamespace(**{**defaults,**changes})

    def test_key_only_config_uses_deepseek_defaults(self):
        with patch.dict(os.environ,{"DEEPSEEK_API_KEY":"TEST-KEY"},clear=True), patch("dotenv.load_dotenv"):
            client, request = live_client.load_settings()
        self.assertEqual(client["base_url"],"https://api.deepseek.com")
        self.assertEqual(request["model"],"deepseek-flash")
        self.assertEqual(request["extra_body"]["thinking"]["type"],"disabled")

    def test_missing_key_stops_without_fallback(self):
        with patch.dict(os.environ,{},clear=True), patch("dotenv.load_dotenv"):
            with self.assertRaisesRegex(LessonError,"configure.py"): live_client.load_settings()

    def test_retry_budget_is_bounded(self):
        with patch.dict(os.environ,{"DEEPSEEK_API_KEY":"TEST-KEY","DEEPSEEK_MAX_RETRIES":"99"},clear=True),patch("dotenv.load_dotenv"):
            with self.assertRaises(LessonError): live_client.load_settings()

    def test_configure_saves_key_and_preserves_other_values(self):
        path=self.output/'.env'; path.write_text('DEEPSEEK_MODEL=custom-model\nDEEPSEEK_API_KEY=old\n',encoding='utf-8')
        configure.save_key('TEST-NEW-KEY',path)
        self.assertEqual(dotenv_values(path)['DEEPSEEK_API_KEY'],'TEST-NEW-KEY')
        self.assertEqual(dotenv_values(path)['DEEPSEEK_MODEL'],'custom-model')

    def test_configure_rejects_multiline_key(self):
        with self.assertRaises(LessonError): configure.save_key('key\nother',self.output/'.env')

    def test_request_uses_chat_completions_and_real_response_content(self):
        seen=[]
        def handler(request):
            seen.append((request.url.path,json.loads(request.content)))
            return httpx.Response(200,json=completion('UNIQUE HTTP RESPONSE'))
        result=live_client.request_text('English facts only','Synthetic input',client=self.client(handler),options=OPTIONS,output_dir=self.output)
        self.assertEqual(result.text,'UNIQUE HTTP RESPONSE')
        self.assertEqual(seen[0][0],'/chat/completions')
        body=seen[0][1]; self.assertEqual(body['thinking'],{'type':'disabled'})
        self.assertNotIn('store',body);self.assertNotIn('max_output_tokens',body)
        self.assertEqual(body['messages'][0]['role'],'system')
        self.assertEqual(result.metadata['provider'],'DeepSeek')

    def test_json_mode_has_request_format_and_instruction(self):
        seen=[]
        def handler(r):seen.append(json.loads(r.content));return httpx.Response(200,json=completion('{}'))
        live_client.request_text('Return JSON only','input',json_output=True,client=self.client(handler),options=OPTIONS)
        self.assertEqual(seen[0]['response_format'],{'type':'json_object'})

    def test_json_mode_without_instruction_stops_before_network(self):
        calls=[]
        client=self.client(lambda r:calls.append(r))
        with self.assertRaisesRegex(LessonError,'JSON instruction'):
            live_client.request_text('Return text','input',json_output=True,client=client,options=OPTIONS)
        self.assertEqual(calls,[])

    def test_auth_error_is_not_retried_or_exposed(self):
        count=[]
        def handler(r):count.append(r);return httpx.Response(401,json={'error':{'message':'SECRET-RAW-BODY','type':'authentication_error'}})
        with self.assertRaises(LessonError) as error:
            live_client.request_text('task','input',client=self.client(handler,retries=1),options=OPTIONS,output_dir=self.output)
        self.assertEqual(len(count),1)
        logs=''.join(p.read_text(encoding='utf-8') for p in self.output.glob('*.json'))
        self.assertNotIn('SECRET-RAW-BODY',str(error.exception)+logs)
        self.assertNotIn('TEST-KEY-NOT-A-REAL-CREDENTIAL',logs)

    def test_transient_request_gets_one_retry(self):
        count=[]
        def handler(r):
            count.append(r)
            if len(count)==1:raise httpx.ReadTimeout('TEST ONLY',request=r)
            return httpx.Response(200,json=completion('AFTER RETRY'))
        with patch('openai._base_client.time.sleep'):
            result=live_client.request_text('task','input',client=self.client(handler,retries=1),options=OPTIONS)
        self.assertEqual(len(count),2);self.assertEqual(result.text,'AFTER RETRY')

    def test_empty_text_is_rejected(self):
        with self.assertRaises(LessonError):
            live_client.request_text('task','input',client=self.client(lambda r:httpx.Response(200,json=completion(''))),options=OPTIONS)

    def test_truncation_is_rejected(self):
        with self.assertRaisesRegex(LessonError,'finish_reason=length'):
            live_client.request_text('task','input',client=self.client(lambda r:httpx.Response(200,json=completion('{',finish='length'))),options=OPTIONS)

    def test_refusal_is_rejected(self):
        with self.assertRaisesRegex(LessonError,'refused'):
            live_client.request_text('task','input',client=self.client(lambda r:httpx.Response(200,json=completion('No',refusal='No'))),options=OPTIONS)

    def test_source_catalog_does_not_add_unqueried_alarm(self):
        payload=report_input(get_case('complete'))
        self.assertNotIn('14:32',json.dumps(payload))
        self.assertIn('Alarm history',payload['evidence_not_yet_available'])

    def test_format_and_evidence_failures_are_separate(self):
        case=get_case('complete'); good=report_for(report_input(case))
        self.assertTrue(check_report(json.dumps(good),case,False)['evidence_check_passed'])
        wrong=demos.mutate_report(good,'wrong_type'); unsupported=demos.mutate_report(good,'unsupported_claim')
        self.assertFalse(check_report(json.dumps(wrong),case,False)['valid_format'])
        check=check_report(json.dumps(unsupported),case,False)
        self.assertTrue(check['valid_format']);self.assertFalse(check['evidence_check_passed'])
        self.assertIsNone(good['diagnosis'])

    def test_contradiction_must_preserve_both_readings(self):
        case=get_case('contradictory'); output=report_for(report_input(case));output['observations']=output['observations'][:1]
        self.assertFalse(check_report(json.dumps(output),case,False)['evidence_check_passed'])

    def test_unknown_equipment_cannot_be_guessed(self):
        case=get_case('ambiguous'); output=report_for(report_input(case));output['equipment_id']='CONV-3'
        self.assertFalse(check_report(json.dumps(output),case,False)['evidence_check_passed'])

    def test_wrong_source_is_blocked_before_generation(self):
        calls=[];args=self.args(self.client(lambda r:calls.append(r)),retrieval_case='wrong-equipment')
        with contextlib.redirect_stdout(io.StringIO()):demos.run_rag(args)
        self.assertEqual(calls,[])

    def test_prompt_calls_twice_with_changed_requirement(self):
        seen=[]
        def handler(r):seen.append(json.loads(r.content));return httpx.Response(200,json=completion('HTTP TEST OUTPUT'))
        with contextlib.redirect_stdout(io.StringIO()):demos.run_prompt(self.args(self.client(handler)))
        self.assertEqual(len(seen),2)
        self.assertEqual(seen[0]['messages'][1],seen[1]['messages'][1])
        self.assertNotEqual(seen[0]['messages'][0],seen[1]['messages'][0])

    def test_context_includes_actual_assistant_reply_and_history(self):
        seen=[]
        def handler(r):
            seen.append(json.loads(r.content));return httpx.Response(200,json=completion('TEST RECEIVED'))
        with contextlib.redirect_stdout(io.StringIO()):demos.run_context(self.args(self.client(handler)))
        self.assertEqual(len(seen),3); self.assertEqual(len(seen[1]['messages']),2)
        self.assertEqual(seen[2]['messages'][2],{'role':'assistant','content':'TEST RECEIVED'})
        self.assertRegex(seen[2]['messages'][1]['content'],r'LAB-[0-9A-F]{6}')

    def agent_handler(self, seen, *, first='query_alarm_log', multiple=False):
        def handler(request):
            body=json.loads(request.content);seen.append(body)
            results=[m for m in body['messages'] if m['role']=='tool']
            done={c['function']['name'] for m in body['messages'] if m['role']=='assistant' for c in m.get('tool_calls',[])}
            if not results:
                names=['query_alarm_log','get_manual_entry'] if multiple else [first]
                calls=[tool(name,{'equipment_id':'CONV-3','time_window':'last 24 h'} if name=='query_alarm_log' else {'keyword':'overcurrent'},f'test-{name}') for name in names]
                return httpx.Response(200,json=completion(None,calls=calls))
            last=json.loads(results[-1]['content'])
            if last['status']=='unavailable':
                return httpx.Response(200,json=completion(None,calls=[tool('request_human_input',{'missing_source':last['missing_source']},'human-call')]))
            if len(done)<2:
                next_name='get_manual_entry' if 'query_alarm_log' in done else 'query_alarm_log'
                args={'keyword':'overcurrent'} if next_name=='get_manual_entry' else {'equipment_id':'CONV-3','time_window':'last 24 h'}
                return httpx.Response(200,json=completion(None,calls=[tool(next_name,args,'second-call')]))
            return httpx.Response(200,json=completion(json.dumps(report_for(last['updated_report_input']))))
        return handler

    def test_agent_roundtrip_keeps_matching_tool_call_ids(self):
        seen=[]
        with contextlib.redirect_stdout(io.StringIO()):result=agent.run_loop('normal',client=self.client(self.agent_handler(seen)),request_options=OPTIONS)
        self.assertEqual(result['model_calls'],3);self.assertEqual(result['status'],'draft_for_human_review')
        self.assertEqual(seen[1]['messages'][-1]['tool_call_id'],seen[1]['messages'][-2]['tool_calls'][0]['id'])
        self.assertEqual(seen[0]['tools'][0]['type'],'function');self.assertIn('function',seen[0]['tools'][0])
        self.assertNotIn('strict',seen[0]['tools'][0]['function'])

    def test_agent_accepts_an_alternative_model_chosen_order(self):
        seen=[]
        with contextlib.redirect_stdout(io.StringIO()):result=agent.run_loop('normal',client=self.client(self.agent_handler(seen,first='get_manual_entry')),request_options=OPTIONS)
        self.assertEqual([t['name'] for t in result['tool_trace']],['get_manual_entry','query_alarm_log'])
        self.assertEqual(result['status'],'draft_for_human_review')

    def test_agent_handles_multiple_calls_in_one_decision(self):
        seen=[]
        with contextlib.redirect_stdout(io.StringIO()):result=agent.run_loop('normal',client=self.client(self.agent_handler(seen,multiple=True)),request_options=OPTIONS)
        self.assertEqual(result['model_calls'],2);self.assertEqual(len(result['tool_trace']),2)
        self.assertEqual(len([m for m in seen[1]['messages'] if m['role']=='tool']),2)

    def test_agent_step_budget_does_not_supply_final_fixture(self):
        seen=[]
        with contextlib.redirect_stdout(io.StringIO()):result=agent.run_loop('normal',1,client=self.client(self.agent_handler(seen)),request_options=OPTIONS)
        self.assertEqual(result['status'],'incomplete');self.assertNotIn('raw_model_output',result);self.assertEqual(len(seen),1)

    def test_missing_alarm_yields_model_chosen_human_pause(self):
        seen=[]
        with contextlib.redirect_stdout(io.StringIO()):result=agent.run_loop('missing-alarm',client=self.client(self.agent_handler(seen)),request_options=OPTIONS)
        self.assertEqual(result['status'],'paused_for_human');self.assertEqual(result['model_calls'],2)
        self.assertEqual(result['tool_trace'][-1]['name'],'request_human_input')

    def test_unknown_tool_is_blocked_before_execution(self):
        client=self.client(lambda r:httpx.Response(200,json=completion(None,calls=[tool('restart_motor',{})])))
        with patch.object(agent,'execute_checked') as execute,contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(LessonError,'permission denied'):agent.run_loop('normal',client=client,request_options=OPTIONS)
        execute.assert_not_called()

    def test_invalid_arguments_are_blocked_before_execution(self):
        client=self.client(lambda r:httpx.Response(200,json=completion(None,calls=[tool('query_alarm_log',{'equipment_id':'OTHER','time_window':'last 24 h'})])))
        with patch.object(agent,'execute_checked') as execute,contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(LessonError,'Arguments rejected'):agent.run_loop('normal',client=client,request_options=OPTIONS)
        execute.assert_not_called()

    def test_fixed_workflow_has_one_model_call_after_code_chosen_tools(self):
        seen=[]
        def handler(r):
            seen.append(json.loads(r.content));payload=json.loads(seen[-1]['messages'][-1]['content'])
            return httpx.Response(200,json=completion(json.dumps(report_for(payload))))
        with contextlib.redirect_stdout(io.StringIO()):result=agent.run_workflow('normal',client=self.client(handler),request_options=OPTIONS)
        self.assertEqual(len(seen),1);self.assertEqual(result['model_calls'],1);self.assertNotIn('tools',seen[0])

    def test_seminar_records_real_response_separately_from_mutation(self):
        seen=[]
        def handler(r):
            seen.append(json.loads(r.content));payload=json.loads(seen[-1]['messages'][-1]['content'])
            return httpx.Response(200,json=completion(json.dumps(report_for(payload))))
        with contextlib.redirect_stdout(io.StringIO()):demos.run_seminar(self.args(self.client(handler)))
        self.assertEqual(len(seen),5)
        rows=json.loads(next(self.output.glob('seminar_2*.json')).read_text(encoding='utf-8'))['cases']
        self.assertEqual(rows[-1]['origin'],'teacher_mutation_of_actual_response')
        self.assertIsInstance(json.loads(rows[-1]['actual_model_output'])['observations'],list)
        self.assertIsInstance(json.loads(rows[-1]['displayed_output'])['observations'],str)

    def test_format_repair_is_a_second_api_request(self):
        seen=[]
        def handler(r):
            seen.append(json.loads(r.content));payload=json.loads(seen[-1]['messages'][-1]['content'])
            return httpx.Response(200,json=completion(json.dumps(report_for(payload))))
        with contextlib.redirect_stdout(io.StringIO()):demos.run_failures(self.args(self.client(handler)))
        self.assertEqual(len(seen),2)
        self.assertIn('invalid_output',json.loads(seen[1]['messages'][-1]['content']))

    def test_all_ten_runners_use_api_transport(self):
        expected={'api':1,'prompt':2,'sampling':2,'reasoning':1,'context':3,'memory':1,'rag':1,'validation':1,'failures':2,'seminar':5}
        for name,runner in demos.RUNNERS.items():
            with self.subTest(mode=name):
                seen=[]
                def handler(r):
                    body=json.loads(r.content);seen.append(body)
                    if 'response_format' in body:
                        output=json.dumps(report_for(json.loads(body['messages'][-1]['content'])))
                    else: output='HTTP TEST DOUBLE FOR TRANSPORT VERIFICATION ONLY'
                    return httpx.Response(200,json=completion(output))
                with contextlib.redirect_stdout(io.StringIO()):runner(self.args(self.client(handler)))
                self.assertEqual(len(seen),expected[name])
                self.assertTrue(all(body['thinking']['type']=='disabled' for body in seen))

if __name__=='__main__':unittest.main()
