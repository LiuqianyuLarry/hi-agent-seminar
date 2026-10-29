"""DeepSeek Chat Completions-shaped contract tests; no external model calls."""
import asyncio
import json
from pathlib import Path
from executor import Executor
from replay_api import ScriptedCompletions
from workflow import run_turn
from tool_definitions import model_tools

CASES=json.loads((Path(__file__).resolve().parents[1]/'cases/tasks.json').read_text(encoding='utf-8'))
def case(name):return next(c for c in CASES if c['id']==name)
def run(api,ex=None,mode='replay'):
    return asyncio.run(run_turn(api,'NO_MODEL','Question',ex or Executor(),mode=mode))


def test_two_calls_matching_id_and_deepseek_format():
    api=ScriptedCompletions(case('spec'));ex=Executor();trace=run(api,ex)
    assert trace['status']=='completed' and len(api.requests)==2 and ex.invocations==1
    messages=api.requests[1]['messages']
    call=next(m for m in messages if m.get('tool_calls'))['tool_calls'][0]
    result=next(m for m in messages if m['role']=='tool')
    assert call['id']==result['tool_call_id']
    assert api.requests[1]['tool_choice']=='none'
    assert api.requests[0]['extra_body']['thinking']['type']=='disabled'
    assert 'input' not in api.requests[0] and 'instructions' not in api.requests[0]
    assert trace['tool_definitions']==api.requests[0]['tools']
    # Evidence must keep the interface actually sent, even if later code edits change it.
    api.requests[0]['tools'][0]['function']['description']='Changed after the request'
    assert trace['tool_definitions']!=api.requests[0]['tools']


def test_no_call_never_executes():
    api=ScriptedCompletions(case('clarify'));ex=Executor()
    assert run(api,ex)['status']=='no_tool' and ex.invocations==0 and len(api.requests)==1


def test_error_not_rewritten_as_success():
    class Liar(ScriptedCompletions):
        def create(self,**kwargs):
            result=super().create(**kwargs)
            if len(self.requests)>1:result['choices'][0]['message']['content']='Success! The reference is 85.'
            return result
    result=run(Liar(case('unknown_machine')))
    assert result['status']=='tool_error' and 'Success!' not in result['answer']
    assert 'Success!' in result['untrusted_model_draft']


def test_multiple_calls_blocked_before_execution():
    class Multiple(ScriptedCompletions):
        def create(self,**kwargs):
            result=super().create(**kwargs)
            calls=result['choices'][0]['message']['tool_calls'];calls.append({**calls[0],'id':'second'})
            return result
    ex=Executor();result=run(Multiple(case('spec')),ex)
    assert result['status']=='rejected_multiple_calls' and ex.invocations==0


def test_incomplete_response_blocks_execution():
    class Incomplete:
        def create(self,**kwargs):return {'choices':[{'finish_reason':'length','message':{}}]}
    ex=Executor();assert run(Incomplete(),ex)['status']=='incomplete_response' and ex.invocations==0


def test_live_error_never_replays():
    class Broken:
        def create(self,**kwargs):raise ConnectionError('do not expose raw details')
    ex=Executor();result=run(Broken(),ex,mode='live')
    assert result['status']=='api_or_pipeline_error' and result['mode']=='live' and ex.invocations==0
    assert 'raw details' not in json.dumps(result)


def test_nested_tools_and_no_beta_strict_claim():
    definitions=model_tools();assert len(definitions)==3
    for entry in definitions:
        assert entry['type']=='function'
        f=entry['function'];schema=f['parameters']
        assert 'strict' not in f and schema['additionalProperties'] is False
        assert set(schema['required'])==set(schema['properties'])


def test_hidden_reasoning_not_saved_in_trace():
    class Extra(ScriptedCompletions):
        def create(self,**kwargs):
            result=super().create(**kwargs)
            result['choices'][0]['message']['reasoning_content']='PRIVATE_REASONING_SENTINEL'
            return result
    api=Extra(case('spec'));result=run(api)
    assert 'PRIVATE_REASONING_SENTINEL' not in json.dumps(result)
    assert 'PRIVATE_REASONING_SENTINEL' not in json.dumps(api.requests)


def test_second_request_cannot_execute_more_tools():
    class Again(ScriptedCompletions):
        def create(self,**kwargs):
            result=super().create(**kwargs)
            if len(self.requests)>1:result['choices'][0]['message']['tool_calls']=[{'id':'bad'}]
            return result
    ex=Executor();result=run(Again(case('spec')),ex)
    assert result['status']=='invalid_final_response' and ex.invocations==1
