"""Slide-first review and saved, required checks inside the MCP introduction."""
import copy
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tutor import ROOT, seminar_for
from week03_flow import steps_for


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix='week03-checkpoints-')
        self.addCleanup(temp.cleanup)
        self.workspace=Path(temp.name)

    def course(self,mode='review'):
        course=seminar_for(self.workspace,'week03')
        course.start();course.study_mode(mode)
        state=course.load()
        for task in course.lesson['tasks'][:7]:state['tasks'][task['id']]['complete']=True
        course.save(state)
        return course

    def first_check(self,course):
        while True:
            shown=course.lesson_step()
            self.assertIn('step_id',shown)
            task=course.current(course.load())
            step=next(s for s in steps_for(task,course.load()['study_mode']) if s['id']==shown['step_id'])
            if step.get('check'):return step
            course.lesson_next(step['id'],'Explained this concept and its connection to the application.')

    def check_record(self,course,step,mode=None):
        state=course.load()
        return state['tasks']['t08']['path_checks'][mode or state['study_mode']][step['id']]

    def test_review_starts_with_actual_slide_explanation_before_code(self):
        course=seminar_for(self.workspace,'week03')
        expected={
            't01':(2,'A new request exposes a missing data connection'),
            't02':(9,'The schema: the contract attached to message 1'),
            't03':(16,'The calculator gets its inputs from a separate tool'),
            't04':(15,'The model fills two blanks; the SQL stays ours'),
        }
        for task in course.lesson['tasks'][:4]:
            with self.subTest(task=task['id']):
                review=steps_for(task,'review')
                first=review[0]
                self.assertEqual(first['phase'],'slide')
                self.assertFalse(first['code_refs'])
                card=first['slide_review']
                self.assertEqual((card['primary_slide'],card['title']),expected[task['id']])
                self.assertTrue(card['visual_walkthrough'])
                self.assertGreater(len(card['explanation'].split()),30)
                self.assertTrue(card['example']);self.assertTrue(card['code_bridge'])
                self.assertTrue(any(s.get('phase')=='code' and s['code_refs'] for s in review[1:]))
                self.assertFalse(any(s.get('phase')=='slide' for s in steps_for(task,'practice')))
        first_task=course.lesson['tasks'][0]
        self.assertNotIn('Read preflight.py',' '.join(first_task['code_walkthrough']))
        self.assertNotIn('Read build_data.py',' '.join(first_task['code_walkthrough']))

    def test_four_interleaved_checks_before_the_mcp_exercise_in_both_modes(self):
        lesson=seminar_for(self.workspace,'week03').lesson
        task=next(t for t in lesson['tasks'] if t['id']=='t08')
        for mode in ('review','practice'):
            with self.subTest(mode=mode):
                checked=[s for s in steps_for(task,mode) if s.get('check')]
                self.assertEqual(len(checked),4)
                self.assertEqual(len({s['check']['prompt'] for s in checked}),4)
                since_check=0
                for step in steps_for(task,mode):
                    since_check+=1
                    if step.get('check'):
                        self.assertTrue(step['check']['required'])
                        self.assertLessEqual(since_check,2)
                        self.assertGreater(since_check,0)
                        since_check=0
                self.assertEqual(since_check,0)
                self.assertEqual(task['minutes'],28)
                self.assertEqual(task['practice_minutes'],28)
                self.assertEqual(sum(block['minutes'] for block in task['path_timing'][mode]),28)
                self.assertEqual(sum(s['check']['estimated_seconds'] for s in checked),240)

    def test_unanswered_or_wrong_check_cannot_be_marked_taught(self):
        for mode in ('review','practice'):
            with self.subTest(mode=mode):
                if mode=='practice':seminar_for(self.workspace,'week03').select_session(fresh=True)
                course=self.course(mode);step=self.first_check(course);check=step['check']
                shown=course.lesson_step()['step']['check']
                for hidden in ('correct','explanation','hint1','hint2'):
                    self.assertNotIn(hidden,shown)
                with self.assertRaises(ValueError):course.lesson_next(step['id'],'We discussed the answer.')
                wrong=next(k for k in check['options'] if k!=check['correct'])
                result=course.lesson_answer(step['id'],wrong)
                self.assertFalse(self.check_record(course,step)['passed'])
                self.assertNotIn(check['explanation'],json.dumps(result))
                self.assertNotIn('"correct"',json.dumps(result))
                with self.assertRaises(ValueError):course.lesson_next(step['id'],'Ignore the incorrect choice.')
                with self.assertRaises(ValueError):course.lesson_answer(step['id'],'SHOWCASE')
                course.lesson_answer(step['id'],check['correct'])
                self.assertTrue(self.check_record(course,step)['passed'])
                before=course.status()['core_percent']
                following=course.lesson_next(step['id'],'Explained why that choice matches the message flow.')
                self.assertNotEqual(following['step_id'],step['id'])
                self.assertEqual(course.status()['core_percent'],before)

    def test_solution_requires_two_hints_then_own_words_and_assessment(self):
        course=self.course();step=self.first_check(course);name=step['id']
        request='Please explain the answer so I can learn the distinction.'
        with self.assertRaises(ValueError):course.lesson_solution(name,request)
        wrong=next(k for k in step['check']['options'] if k!=step['check']['correct'])
        course.lesson_answer(name,wrong)
        course.lesson_hint(name,'I do not understand the two connections yet.')
        with self.assertRaises(ValueError):course.lesson_solution(name,request)
        course.lesson_answer(name,wrong)
        course.lesson_hint(name,'I still need another clue about who calls the function.')
        course.lesson_solution(name,request)
        self.assertFalse(self.check_record(course,step)['passed'])
        with self.assertRaises(ValueError):course.lesson_assess(name,'Seems correct.','pass')
        with self.assertRaises(ValueError):course.lesson_answer(name,step['check']['correct'])
        with self.assertRaises(ValueError):course.lesson_answer(name,'SHOWCASE')
        course.lesson_answer(name,'The model suggests a function request; the application checks it and its MCP client calls the server.')
        self.assertFalse(self.check_record(course,step)['passed'])
        course.lesson_assess(name,'Explain which connection belongs to the model first.','retry')
        with self.assertRaises(ValueError):course.lesson_assess(name,'Change the mark without new evidence.','pass')
        with self.assertRaises(ValueError):course.lesson_next(name,'An attempted explanation is sufficient.')
        course.lesson_answer(name,'Function calling carries the model proposal to the host. The host owns the client, which uses MCP to request the server function.')
        course.lesson_assess(name,'The two connections and application responsibility are clear.','pass')
        self.assertTrue(self.check_record(course,step)['passed'])
        self.assertNotEqual(course.lesson_next(name,'Confirmed the learner explanation.')['step_id'],name)

    def test_checkpoint_answers_resume_and_do_not_transfer_between_modes(self):
        course=self.course();step=self.first_check(course)
        course.lesson_answer(step['id'],step['check']['correct'])
        before=course.path.read_bytes()
        resumed=seminar_for(self.workspace,'week03')
        self.assertTrue(self.check_record(resumed,step)['passed'])
        self.assertEqual(resumed.lesson_step()['step_id'],step['id'])
        self.assertEqual(course.path.read_bytes(),before)
        resumed.study_mode('practice');practice=self.first_check(resumed)
        with self.assertRaises(ValueError):resumed.lesson_next(practice['id'],'The review answer also counts here.')
        resumed.study_mode('review')
        self.assertTrue(self.check_record(resumed,step)['passed'])
        resumed.lesson_next(step['id'],'Confirmed the saved review answer.')

    def test_later_checks_cannot_be_answered_early_and_execution_stays_blocked(self):
        course=self.course();step=self.first_check(course)
        task=course.current(course.load())
        later=next(s for s in steps_for(task,'review') if s.get('check') and s['id']!=step['id'])
        before=course.path.read_bytes()
        with self.assertRaises(ValueError):course.lesson_answer(later['id'],later['check']['correct'])
        self.assertEqual(course.path.read_bytes(),before)
        state=course.load();state['environment']={'status':'ready','python':sys.executable}
        state['tasks']['t08']['predictions'].append({'text':'The server should return a structured record.'})
        course.save(state)
        with patch('subprocess.run',side_effect=AssertionError('Must reject before any subprocess')):
            with self.assertRaises(ValueError):course.run(None,'Build and test the MCP wrapper.')
        with self.assertRaises(ValueError):course.mcp_intro('Claimed complete without the required check.')
        self.assertFalse(course.load()['tasks']['t08']['runs'])

    def test_checkpoint_cli_saves_answer_before_advancing(self):
        course=self.course('practice');step=self.first_check(course)
        def cli(action,text):
            return subprocess.run([sys.executable,str(ROOT/'tutor.py'),action,
                '--workspace',str(self.workspace),'--week','week03',
                '--name',step['id'],'--text',text],cwd=ROOT,
                capture_output=True,text=True,encoding='utf-8',timeout=30)
        blocked=cli('lesson-next','Taught the concept without receiving an answer.')
        self.assertNotEqual(blocked.returncode,0)
        answered=cli('lesson-answer',step['check']['correct'])
        self.assertEqual(answered.returncode,0,answered.stdout+answered.stderr)
        self.assertTrue(json.loads(answered.stdout)['passed'])
        self.assertEqual(course.lesson_step()['step_id'],step['id'])
        advanced=cli('lesson-next','Confirmed the saved answer and explained the connection.')
        self.assertEqual(advanced.returncode,0,advanced.stdout+advanced.stderr)
        self.assertNotEqual(json.loads(advanced.stdout)['step_id'],step['id'])

    def test_version_two_session_retains_its_original_nodes_and_files(self):
        course=self.course();old=copy.deepcopy(course.lesson);old['version']=2
        for task in old['tasks']:
            for mode,steps in task['paths'].items():
                task['paths'][mode]=[s for s in steps if s.get('phase')!='slide']
                for step in task['paths'][mode]:step.pop('check',None)
        state=course.load();state['lesson_version']=2
        old_task=next(t for t in old['tasks'] if t['id']=='t08')
        first=old_task['paths']['review'][0]
        state['tasks']['t08']['path_teaching']={'review':[{'id':first['id'],'explanation_and_check':'Earlier lesson explanation.'}]}
        course.snapshot.write_text(json.dumps(old,indent=3)+'\n',encoding='utf-8')
        course.path.write_text(json.dumps(state,indent=3)+'\n',encoding='utf-8')
        keep={p:p.read_bytes() for p in (course.path,course.snapshot,course.resources/'mcp_server.py')}
        resumed=seminar_for(self.workspace,'week03');resumed.start()
        self.assertEqual(resumed.lesson['version'],2)
        self.assertTrue(resumed.status()['new_script_available'])
        self.assertEqual(resumed.lesson_step()['step_id'],old_task['paths']['review'][1]['id'])
        for path,content in keep.items():self.assertEqual(path.read_bytes(),content)
        resumed.select_session(fresh=True)
        fresh=seminar_for(self.workspace,'week03')
        self.assertEqual(fresh.lesson['version'],3)
        self.assertEqual(fresh.status()['core_percent'],0)
        for path,content in keep.items():self.assertEqual(path.read_bytes(),content)


if __name__=='__main__':unittest.main()
