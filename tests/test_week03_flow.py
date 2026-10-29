"""Small-step teaching, real code windows and upgrade isolation."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tutor import ROOT, seminar_for
from week03_flow import excerpt, render_step, steps_for


ANSWER_KEYS={'correct','rubric','feedback','worked_answer','worked_example','solutions','answer_guidance'}


class FlowCase(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix='week03-flow-')
        self.addCleanup(temp.cleanup)
        self.base=Path(temp.name)
        self.workspace=self.base/'learner';self.workspace.mkdir()

    def assert_no_answers(self,value):
        if isinstance(value,dict):
            self.assertFalse(ANSWER_KEYS.intersection(value))
            for item in value.values():self.assert_no_answers(item)
        elif isinstance(value,list):
            for item in value:self.assert_no_answers(item)

    def course(self,mode='review',task='t01'):
        course=seminar_for(self.workspace,'week03');course.start();course.study_mode(mode)
        state=course.load()
        for item in course.lesson['tasks']:
            if item['id']==task:break
            state['tasks'][item['id']]['complete']=True
        course.save(state)
        return course

    def local_plugin(self):
        root=self.base/'plugin';root.mkdir()
        shutil.copytree(ROOT/'week03',root/'week03',
                        ignore=shutil.ignore_patterns('__pycache__','.venv','.env'))
        return root


class SourceWindowTests(FlowCase):
    def test_selecting_one_source_keeps_offsets_local_to_that_function(self):
        source=self.base/'sources';source.mkdir()
        (source/'sample.py').write_text('def short():\n    return 1\n\ndef long():\n'+''.join(
            f'    item_{n} = {n}\n' for n in range(25)),encoding='utf-8')
        step={'id':'two_sources','code_refs':[
            {'pack':'lecture','file':'sample.py','symbol':'short'},
            {'pack':'lecture','file':'sample.py','symbol':'long'}]}
        first=render_step(step,{'lecture':source})
        self.assertEqual(len(first['snippets']),1)
        self.assertEqual(first['snippets'][0]['symbol'],'short')
        self.assertEqual(len(first['code_sources']),2)
        later=render_step(step,{'lecture':source},offset=12,code_index=1)
        self.assertEqual(len(later['snippets']),1)
        self.assertEqual(later['snippets'][0]['symbol'],'long')
        self.assertEqual(later['snippets'][0]['start_line'],16)
        with self.assertRaises(ValueError):render_step(step,{'lecture':source},code_index=2)

    def test_windows_use_real_line_numbers_and_never_exceed_twelve_lines(self):
        source=self.base/'source';source.mkdir()
        code='\n\nclass Machine:\n    @staticmethod\n    def sample():\n'+''.join(
            f'        value_{n} = {n}\n' for n in range(25))+'        return value_24\n'
        path=source/'machine.py';path.write_text(code,encoding='utf-8')
        reference={'pack':'lecture','file':'machine.py','symbol':'Machine.sample','max_lines':99}
        offset=0;seen=[]
        while True:
            result=excerpt(reference,{'lecture':source},offset)
            self.assertLessEqual(result['end_line']-result['start_line']+1,12)
            self.assertEqual(result['path'],str(path))
            for line in result['numbered_code'].splitlines():
                number,text=line.split(': ',1);number=int(number)
                self.assertEqual(text,code.splitlines()[number-1]);seen.append(number)
            if not result['more_available']:break
            offset=result['next_code_offset']
        self.assertEqual(seen,list(range(4,32)))
        with self.assertRaises(ValueError):excerpt(reference,{'lecture':source},-1)
        with self.assertRaises(ValueError):excerpt(reference,{'lecture':source},1000)
        with self.assertRaises(ValueError):
            excerpt(dict(reference,file='../outside.py'),{'lecture':source})

    def test_all_curriculum_code_references_resolve_to_real_sources(self):
        lesson=json.loads((ROOT/'week03/lesson.json').read_text(encoding='utf-8'))
        packs={'lecture':ROOT/'week03/lecture_demo','seminar':ROOT/'week03/resources'}
        self.assertEqual(lesson['version'],3)
        self.assertNotRegex(json.dumps(lesson,ensure_ascii=False),'[\u4e00-\u9fff]')
        refs=[]
        for task in lesson['tasks']:
            for mode in ('review','practice'):
                self.assertTrue(steps_for(task,mode))
                for step in steps_for(task,mode):
                    for reference in step.get('code_refs',[]):
                        with self.subTest(mode=mode,step=step['id'],source=reference):
                            result=excerpt(reference,packs)
                            self.assertLessEqual(len(result['numbered_code'].splitlines()),12)
                            self.assertTrue(result['numbered_code'])
                            refs.append((mode,reference['pack']))
        self.assertIn(('review','lecture'),refs)
        self.assertIn(('practice','seminar'),refs)
        self.assertNotEqual([t['paths']['review'] for t in lesson['tasks']],
                            [t['paths']['practice'] for t in lesson['tasks']])

    def test_render_hides_answers_before_a_checkpoint_response(self):
        step={'id':'sample','code_refs':[],
              'worked_example':'Secret explanation',
              'check':{'prompt':'Choose','options':{'A':'One','B':'Two'},
                       'correct':'A','explanation':'A is correct','feedback':'Answer feedback'},
              'nested':[{'rubric':'Secret rubric','answer_guidance':'Private guidance'}]}
        original=copy.deepcopy(step)
        result=render_step(step,{})
        self.assert_no_answers(result)
        self.assertNotIn('explanation',result['check'])
        self.assertEqual(step,original)




class StudentFlowTests(FlowCase):
    def test_more_code_windows_and_sources_never_advance_learning(self):
        lesson=json.loads((ROOT/'week03/lesson.json').read_text(encoding='utf-8'))
        task,step=next((task,step) for task in lesson['tasks']
                      for step in steps_for(task,'review') if len(step['code_refs'])>1)
        course=self.course(task=task['id'])
        before={p:p.read_bytes() for p in course.base.rglob('*') if p.is_file()}
        current=course.lesson_step()['step_id']
        first=course.lesson_step(step['id'])
        snippet=first['step']['snippets'][0]
        self.assertTrue(snippet['more_available'])
        more=course.lesson_step(step['id'],code_offset=snippet['next_code_offset'])
        self.assertGreater(more['step']['snippets'][0]['start_line'],snippet['end_line'])
        second=course.lesson_step(step['id'],code_index=1)
        self.assertEqual(len(second['step']['snippets']),1)
        self.assertEqual(second['step']['snippets'][0]['symbol'],step['code_refs'][1]['symbol'])
        self.assertNotEqual(second['step']['snippets'][0]['start_line'],snippet['start_line'])
        self.assertEqual(course.lesson_step()['step_id'],current)
        for path,data in before.items():self.assertEqual(path.read_bytes(),data)

    def test_revisit_selects_one_earlier_step_without_mutating_progress(self):
        course=self.course(task='t06')
        before={p:p.read_bytes() for p in course.base.rglob('*') if p.is_file()}
        first=course.revisit('t02')
        self.assertTrue(first['core_progress_unchanged'])
        self.assertEqual(first['task']['id'],'t02')
        self.assertGreater(len(first['step_choices']),1)
        self.assertEqual(first['step']['id'],first['step_choices'][0]['id'])
        self.assertNotIn('teaching_steps',first)
        self.assertNotIn('paths',first['task'])
        self.assert_no_answers(first)
        other=first['step_choices'][-1]['id']
        selected=course.revisit('t02',step_id=other)
        self.assertEqual(selected['step']['id'],other)
        for snippet in selected['step']['snippets']:
            self.assertLessEqual(len(snippet['numbered_code'].splitlines()),12)
        with self.assertRaises(ValueError):course.revisit('t02',step_id='another.task.step')
        self.assertEqual(course.status()['current_task'],'t06')
        self.assertEqual(course.status()['core_percent'],50)
        for path,data in before.items():self.assertEqual(path.read_bytes(),data)

    def test_current_task_is_compact_and_does_not_reveal_answers(self):
        course=self.course()
        result=course.task()
        self.assertNotIn('paths',result['task'])
        self.assertNotIn('code_walkthrough',result['task'])
        self.assert_no_answers(result['task'])
        step=course.lesson_step()
        self.assert_no_answers(step['step'])
        self.assertEqual(step['step_id'],step['step']['id'])

    def test_teaching_acknowledgement_is_ordered_resumable_and_mode_specific(self):
        course=self.course()
        first=course.lesson_step();task=course.current(course.load())
        steps=steps_for(task,'review');self.assertGreater(len(steps),1)
        with self.assertRaises(ValueError):course.lesson_next(steps[-1]['id'],'Out of order.')
        second=course.lesson_next(first['step_id'],'Explained this concept and checked the response.')
        before=course.path.read_bytes()
        retry=course.lesson_next(first['step_id'],'Retried acknowledgement.')
        self.assertTrue(retry['duplicate_ignored'])
        self.assertEqual(course.path.read_bytes(),before)
        resumed=seminar_for(self.workspace,'week03')
        self.assertEqual(resumed.lesson_step()['step_id'],second['step_id'])
        self.assertEqual(resumed.status()['core_percent'],0)
        resumed.study_mode('practice')
        practice=resumed.lesson_step()
        self.assertEqual(practice['pending_count'],len(steps_for(task,'practice')))
        resumed.study_mode('review')
        self.assertEqual(resumed.lesson_step()['step_id'],second['step_id'])

    def test_pending_path_blocks_execution_and_completion(self):
        course=self.course(task='t02')
        state=course.load();state['environment']={'status':'ready','python':sys.executable}
        record=state['tasks']['t02']
        record['teaching'].append({'text':'Generic teaching alone is insufficient.'})
        record['predictions'].append({'text':'Expected fixture output.'})
        course.save(state)
        with patch('subprocess.run',side_effect=AssertionError('Must reject before execution')):
            with self.assertRaisesRegex(ValueError,'teaching path'):
                course.run(None,'Explained this task and its purpose.')
        with self.assertRaisesRegex(ValueError,'selected path step'):
            course.mutate('complete')
        self.assertFalse(course.load()['tasks']['t02']['runs'])

    def test_existing_student_and_lecture_sources_survive_plugin_updates(self):
        root=self.local_plugin()
        course=seminar_for(self.workspace,'week03',root=root);course.start();course.study_mode('review')
        lecture=next((course.base/'lecture.snapshot').rglob('*.py'))
        image=Path(course.lesson_step()['step']['slide_image'])
        student=course.resources/'tools/calculation.py'
        student.write_text(student.read_text(encoding='utf-8')+'\n# Student work stays here.\n',encoding='utf-8')
        before={p:p.read_bytes() for p in (lecture,image,student,course.path,course.snapshot)}
        upstream=root/'week03/lecture_demo'/lecture.relative_to(course.base/'lecture.snapshot')
        upstream.write_text('# New release\n',encoding='utf-8')
        (root/'week03/resources/tools/calculation.py').write_text('# New starter\n',encoding='utf-8')
        (root/'week03/slides'/image.name).write_bytes(b'Changed source slide after learning started.')
        resumed=seminar_for(self.workspace,'week03',root=root);resumed.start()
        for path,data in before.items():self.assertEqual(path.read_bytes(),data)
        self.assertEqual(resumed.lesson_step()['mode'],'review')
        self.assertEqual(resumed.lesson_step()['step']['slide_image'],str(image))


if __name__=='__main__':unittest.main()
