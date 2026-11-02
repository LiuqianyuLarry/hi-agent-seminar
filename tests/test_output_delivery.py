"""Current output instructions apply without migrating older learner workspaces.

These tests verify helper metadata and preservation, not a host's message UI.
"""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tutor import ROOT, atomic_json, catalog, seminar_for
from output_delivery import response_output


class OutputDeliveryTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory(prefix='seminar-output-delivery-')
        self.addCleanup(directory.cleanup)
        self.workspace=Path(directory.name)

    def cli(self,action,*arguments):
        result=subprocess.run([sys.executable,'-B',str(ROOT/'tutor.py'),action,
            '--workspace',str(self.workspace),*arguments],cwd=ROOT,
            capture_output=True,text=True,encoding='utf-8',timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        return json.loads(result.stdout)

    def workspace_bytes(self):
        return {p.relative_to(self.workspace).as_posix():p.read_bytes()
                for p in self.workspace.rglob('*') if p.is_file()}

    def contract(self,result):
        contract=result['response_contract']
        self.assertTrue(contract['final_reply_required'])
        self.assertEqual(Path(contract['policy']).resolve(),(ROOT/'OUTPUT.md').resolve())
        self.assertTrue(Path(contract['policy']).is_file())
        self.assertEqual(set(contract['required_content']),
                         {'teaching','code_explanation','observed_results','saved_progress'})
        return contract

    def older_course(self,week):
        course=seminar_for(self.workspace,week)
        course.start()
        state=course.load()
        first=course.lesson['tasks'][0]
        state['tasks'][first['id']]['complete']=True
        course.save(state)
        # A pre-update lesson and its old output advice must remain pinned.
        old=copy.deepcopy(course.lesson)
        old['version']=max(1,old['version']-1)
        state=course.load();state['lesson_version']=old['version']
        atomic_json(course.snapshot,old)
        atomic_json(course.path,state)
        guide=course.base/'TEACHING.snapshot.md'
        guide.write_bytes(guide.read_bytes()+b'\nHistorical instruction preserved by update.\n')
        source=next(course.resources.rglob('*.py'))
        source.write_bytes(source.read_bytes()+b'\n# Preserved learner source edit.\n')
        return seminar_for(self.workspace,week)

    def test_fresh_catalog_requests_a_final_reply_without_starting_a_course(self):
        before=self.workspace_bytes()
        expected=catalog(self.workspace)
        shown=self.cli('list')
        contract=self.contract(shown)
        self.assertIsNone(contract['progress'])
        self.assertIsNone(shown['active_week'])
        self.assertEqual({key:value for key,value in shown.items() if key!='response_contract'},expected)
        self.assertEqual(self.workspace_bytes(),before)

    def test_current_policy_and_real_saved_progress_apply_to_all_older_weeks(self):
        courses={week:self.older_course(week) for week in ('week01','week02','week03')}
        before=self.workspace_bytes()
        for week,course in courses.items():
            with self.subTest(week=week):
                expected=course.status()['core_percent']
                shown=self.cli('status','--week',week)
                contract=self.contract(shown)
                self.assertEqual(contract['progress'],{'week':week,'core_percent':expected})
                self.assertEqual(shown['core_percent'],expected)
                self.assertEqual(Path(shown['lesson_snapshot']),course.snapshot)
                self.assertNotEqual(Path(contract['policy']).parent,course.base)
                self.assertEqual(self.workspace_bytes(),before)

    def test_catalog_progress_comes_from_the_active_saved_course(self):
        self.older_course('week01')
        active=self.older_course('week03')
        before=self.workspace_bytes()
        expected_catalog=catalog(self.workspace)
        shown=self.cli('list')
        self.assertEqual(shown['active_week'],'week03')
        expected=active.status()['core_percent']
        self.assertEqual(self.contract(shown)['progress'],{'week':'week03','core_percent':expected})
        self.assertEqual({key:value for key,value in shown.items() if key!='response_contract'},expected_catalog)
        self.assertEqual(self.workspace_bytes(),before)

    def test_lesson_read_includes_the_contract_without_advancing_the_step(self):
        course=seminar_for(self.workspace,'week03')
        course.start();course.study_mode('review')
        before=self.workspace_bytes()
        current=course.lesson_step()
        shown=self.cli('lesson-step','--week','week03')
        self.assertEqual(shown['step_id'],current['step_id'])
        self.assertEqual(self.contract(shown)['progress'],{'week':'week03','core_percent':0})
        self.assertEqual(shown['step'],current['step'])
        self.assertEqual(self.workspace_bytes(),before)

    def test_output_contract_is_not_written_into_a_saved_learning_note(self):
        course=self.older_course('week01')
        snapshot=course.snapshot.read_bytes()
        guide=(course.base/'TEACHING.snapshot.md').read_bytes()
        note='Pause here and continue with this same learning record.'
        shown=self.cli('save','--week','week01','--text',note)
        self.contract(shown)
        state=course.load()
        self.assertEqual(state['notes'][-1]['text'],note)
        self.assertNotIn('response_contract',state)
        self.assertNotIn('final_reply_required',json.dumps(state))
        self.assertEqual(course.snapshot.read_bytes(),snapshot)
        self.assertEqual((course.base/'TEACHING.snapshot.md').read_bytes(),guide)

    def test_read_only_code_output_uses_saved_status_when_payload_has_no_status(self):
        course=self.older_course('week03')
        before=self.workspace_bytes()
        shown=self.cli('code','--week','week03')
        self.assertTrue(shown['snippets'])
        self.assertEqual(self.contract(shown)['progress'],
                         {'week':'week03','core_percent':course.status()['core_percent']})
        self.assertEqual(self.workspace_bytes(),before)

    def test_metadata_wrap_preserves_evidence_and_ignores_progress_looking_run_data(self):
        evidence={'run':{'data':{'week':'week01','core_percent':99},
                         'observations':[{'temperature_c':87.0},'unchanged text']}}
        before=copy.deepcopy(evidence)
        unknown=response_output(evidence,ROOT)
        self.assertIsNone(self.contract(unknown)['progress'])
        authoritative={'week':'week03','core_percent':70}
        wrapped=response_output(evidence,ROOT,status=authoritative)
        self.assertEqual(self.contract(wrapped)['progress'],authoritative)
        self.assertEqual(wrapped['run'],before['run'])
        self.assertEqual(evidence,before)


if __name__=='__main__':unittest.main()
