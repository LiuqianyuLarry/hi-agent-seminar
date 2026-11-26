import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tutor import attach_next_step, catalog, seminar_for


class WeekSixTeaching(unittest.TestCase):
    def test_both_routes_and_session_history(self):
        solutions = json.loads((ROOT/'week06/instructor/solutions.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            earlier = seminar_for(workspace, 'week05')
            earlier.start()
            earlier.study_mode('practice')
            earlier_record = earlier.path.read_bytes()
            self.assertIn('week06', [c['id'] for c in catalog(workspace)['courses']])
            for mode in ('review', 'practice'):
                course = seminar_for(workspace, 'week06')
                if mode == 'review':
                    course.start()
                    first_path = course.path
                else:
                    course.select_session(fresh=True)
                    course = seminar_for(workspace, "week06")
                    self.assertNotEqual(first_path, course.path)
                course.study_mode(mode)
                for index, task in enumerate(course.lesson['tasks'], 1):
                    with self.subTest(mode=mode, task=task['id']):
                        concept = task['concepts'][0]
                        course.concept_choice(concept, 'example' if mode == 'review' else 'understand')
                        ran_task = False
                        for step in task['paths'][mode]:
                            if step['phase'] == 'after_run' and not ran_task:
                                ran_task = True
                                gate = course.lesson_step()
                                self.assertTrue(gate.get('needs_run'), gate)
                                if index == 1:
                                    self.assertEqual(course.setup(sys.executable)['checks'][0]['returncode'], 0)
                                course.mutate('predict', 'I will check the source and compare the two outputs.')
                                for target in course.required_code_targets(task):
                                    if mode == 'review' and target == 'query':
                                        course.write_code(target, solutions[target]['body'].replace('r.ts<?', 'r.ts<=?'))
                                        failed = course.run(None, task['purpose'])
                                        self.assertEqual(failed['run']['status'], 'failed')
                                        self.assertIn('10:25', failed['observed_result']['error'])
                                    course.write_code(target, solutions[target]['body'])
                                run = course.run(None, task['purpose'])
                                self.assertEqual(run['run']['status'], 'success', run['observed_result'])
                                transition = attach_next_step(course, run, 'run')
                                self.assertEqual(transition['next_step']['step_id'], step['id'])
                                data = run['observed_result']
                                if index == 5:
                                    self.assertEqual(data['correct_query']['payload']['statistics']['mean_c'], 90.2)
                                if index == 8:
                                    self.assertTrue(data['id_check']['citations_resolve'])
                                    self.assertIn('4.2', data['rule']['payload']['section'])
                                    self.assertIn('cannot confirm', data['rule']['payload']['text'])
                                    self.assertIn('retrieval', data['routes']['combined'])
                            live = course.lesson_step()
                            self.assertEqual(live['step_id'], step['id'])
                            if step['phase'] == 'before_run' and mode == 'review' and step.get('slide_review'):
                                self.assertTrue(Path(live['step']['slide_image']).is_file())
                            if step.get('check'):
                                check = step['check']
                                if index == 1 and mode == 'review':
                                    wrong = next(k for k in check['options'] if k != check['correct'])
                                    for _ in range(2):
                                        course.lesson_answer(step['id'], wrong)
                                        course.lesson_hint(step['id'], 'I would like a hint.')
                                    course.lesson_answer(step['id'], wrong)
                                    course.lesson_solution(step['id'], 'Please explain the answer.')
                                    course.lesson_answer(step['id'], 'I would open the manual edition applicable to this machine.')
                                    course.lesson_assess(step['id'], 'That locates the right procedure.', 'pass')
                                else:
                                    self.assertTrue(course.lesson_answer(step['id'], check['correct'])['passed'])
                            course.lesson_next(step['id'], 'We discussed the example and checked the source.')
                        course.mutate('explain', task['questions'][0]['worked_answer'])
                        question = task['questions'][0]
                        answer = question['worked_answer']
                        if index == 8:
                            source = data['rule']['payload']
                            answer = (data['measurement']['text'] + ' [' + data['measurement']['evidence_ids'][0] +
                                      ']. Retain the raw readings and obtain the calibration record and load log. ' +
                                      source['source_ref'] + ' edition ' + source['version'] +
                                      '. The temperature records alone cannot confirm a bearing failure.')
                        course.mutate('answer', answer, question=question['id'])
                        course.mutate('assess', 'The learner explained the result with the relevant evidence.',
                                      question=question['id'], verdict='pass')
                        status = course.mutate('complete')['status']
                        if index == 4:
                            self.assertEqual(status['core_percent'], 50)
                            saved = course.path.read_bytes()
                            reopened = seminar_for(workspace, 'week06')
                            self.assertEqual(reopened.status()['current_task'], 't05')
                            previous = reopened.revisit('t01', f't01.{mode}_inspect')
                            self.assertTrue(previous['core_progress_unchanged'])
                            self.assertEqual(len(previous['observed_result']['reading_rows']), 5)
                            self.assertEqual(saved, reopened.path.read_bytes())
                            course = reopened
                self.assertEqual(course.status()['core_percent'], 100)
                bench = course.run(None, 'Compare the labelled questions.', name='bench', prediction='Scope should affect ranks.')
                self.assertEqual(bench['run']['status'], 'success', bench)
                self.assertEqual(bench['observed_result']['trials'], 42)
                if mode == 'review':
                    first_record = first_path.read_bytes()
            self.assertEqual(first_path.read_bytes(), first_record)
            self.assertEqual(earlier.path.read_bytes(), earlier_record)


if __name__ == '__main__':
    unittest.main()

