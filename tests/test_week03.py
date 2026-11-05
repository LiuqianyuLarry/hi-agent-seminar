"""Week 3 integration and preservation of older learning records."""
import json
import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tutor import seminar_for, catalog, ROOT


class Week3Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.workspace=Path(self.temp.name)

    def teach_path(self, course):
        """Acknowledge each actual node, without awarding task completion."""
        result=course.lesson_step()
        while result.get('step_id'):
            task=course.current(course.load())
            current=next(step for step in task['paths'][course.load()['study_mode']]
                         if step['id']==result['step_id'])
            if current.get('check'):
                course.lesson_answer(current['id'],current['check']['correct'])
            result=course.lesson_next(result['step_id'],
                'Explained the logic, source inputs and outputs; checked the learner response.')
        self.assertTrue(result.get('preparation_complete'))

    def test_catalog_and_timing(self):
        courses=catalog(self.workspace)['courses']
        self.assertEqual([c['id'] for c in courses],['week01','week02','week03','week04'])
        course=seminar_for(self.workspace,'week03')
        for key in ['minutes','practice_minutes']:
            self.assertEqual(sum(t[key] for t in course.lesson['tasks'][:5]),50)
            self.assertEqual(sum(t[key] for t in course.lesson['tasks'][5:]),50)



    def test_starter_has_todos_tests_and_csv_but_no_answers(self):
        s=seminar_for(self.workspace,'week03');s.start()
        self.assertIn('NotImplementedError',(s.resources/'tools/calculation.py').read_text())
        self.assertTrue((s.resources/'tests/test_mcp_integration.py').exists())
        self.assertTrue((s.resources/'data/sensor_readings.csv').exists())
        self.assertFalse((s.resources/'instructor').exists())
        self.assertNotIn('worked_answer',s.task()['task'])

    def test_modes_concepts_and_revisit_preserve_progress(self):
        s=seminar_for(self.workspace,'week03');s.start()
        s.study_mode('practice');s.concept_choice('contracts','brief')
        before=s.path.read_bytes();view=s.revisit('t02')
        self.assertEqual(view['task']['id'],'t02');self.assertEqual(s.path.read_bytes(),before)
        self.assertNotIn('worked_answer',view['task'])

    def test_mcp_introduction_required_in_both_modes(self):
        for mode in ['review','practice']:
            s=seminar_for(self.workspace,'week03');s.start();s.study_mode(mode)
            state=s.load()
            for t in s.lesson['tasks'][:7]:state['tasks'][t['id']]['complete']=True
            s.save(state)
            self.assertIn('teach the full MCP introduction in either study mode',s.status()['remaining_requirements'])
            with self.assertRaisesRegex(ValueError,'MCP teaching steps'):
                s.mcp_intro('Premature claim that the complete introduction was taught.')
            self.teach_path(s)
            s.mcp_intro('Explained purpose, roles, function calling, transport, discovery and boundaries.')
            self.assertNotIn('teach the full MCP introduction in either study mode',s.status()['remaining_requirements'])
            s.select_session(fresh=True)

    def test_code_is_saved_exactly_and_old_file_is_backed_up(self):
        s=seminar_for(self.workspace,'week03');s.start();s.study_mode('review')
        state=s.load();state['tasks']['t01']['complete']=True;s.save(state)
        s.mutate('teach','Explained logic and the function body.')
        original=(s.resources/'tools/calculation.py').read_bytes()
        body="raise NotImplementedError('My unfinished attempt')"
        with self.assertRaisesRegex(ValueError,'path'):
            s.write_code('stats',body)
        self.assertEqual((s.resources/'tools/calculation.py').read_bytes(),original)
        self.teach_path(s)
        result=s.write_code('stats',body)
        record=s.load()['tasks']['t02']['code_drafts'][-1]
        self.assertEqual(record['student_text'],body)
        self.assertEqual(Path(record['previous']).read_bytes(),original)
        self.assertIn('My unfinished attempt',Path(result['saved']).read_text())

    def test_new_week_keeps_both_old_weeks_byte_for_byte(self):
        for week in ['week01','week02']:seminar_for(self.workspace,week).start()
        before={p:p.read_bytes() for p in self.workspace.rglob('*') if p.is_file()}
        s=seminar_for(self.workspace,'week03');s.start();s.study_mode('practice');s.select_session(fresh=True)
        for p,data in before.items():self.assertEqual(p.read_bytes(),data)

    def test_old_lesson_snapshot_remains_usable_and_preserved(self):
        s=seminar_for(self.workspace,'week03');s.start();s.study_mode('review')
        lesson=copy.deepcopy(s.lesson);lesson['version']=1
        for task in lesson['tasks']:task.pop('paths',None)
        state=s.load();state['lesson_version']=1
        state['tasks']['t01']['complete']=True
        s.snapshot.write_text(json.dumps(lesson,indent=3)+'\n',encoding='utf-8')
        s.path.write_text(json.dumps(state,indent=3)+'\n',encoding='utf-8')
        original={p:p.read_bytes() for p in (s.path,s.snapshot,s.resources/'tools/calculation.py')}
        resumed=seminar_for(self.workspace,'week03')
        self.assertEqual(resumed.status()['core_percent'],10)
        self.assertTrue(resumed.status()['new_script_available'])
        self.assertTrue(resumed.lesson_step()['legacy_lesson'])
        self.assertEqual(resumed.task()['task']['id'],'t02')
        resumed.start()
        for path,data in original.items():self.assertEqual(path.read_bytes(),data)
        resumed.select_session(fresh=True)
        fresh=seminar_for(self.workspace,'week03')
        self.assertEqual(fresh.lesson['version'],3)
        self.assertEqual(fresh.status()['core_percent'],0)
        for path,data in original.items():self.assertEqual(path.read_bytes(),data)


if __name__=='__main__':unittest.main()
