"""Week 4 preserves older work and requires visible, checked learning steps.

These checks use disposable learner workspaces. They do not claim that a host UI
rendered a reply or that a paid model request was made.
"""
import ast
import copy
import hashlib
import json
import os
import zipfile
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tutor import ROOT, PROGRESS_NAMESPACE, SCHEMA, atomic_json, catalog, seminar_for
from week03_flow import excerpt, steps_for


PRIVATE_KEYS = {'correct', 'rubric', 'feedback', 'worked_answer', 'worked_example',
                'solutions', 'answer_guidance', 'hint1', 'hint2'}


class Week4Case(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='week04-learning-')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.workspace = self.directory / 'learner'
        self.workspace.mkdir()

    def files(self, folder=None):
        folder = folder or self.workspace
        return {p.relative_to(folder).as_posix(): p.read_bytes()
                for p in folder.rglob('*') if p.is_file()}

    def course(self, mode='review', task_id='t01', root=ROOT):
        course = seminar_for(self.workspace, 'week04', root=root)
        course.start()
        course.study_mode(mode)
        state = course.load()
        for task in course.lesson['tasks']:
            if task['id'] == task_id:
                break
            state['tasks'][task['id']]['complete'] = True
        course.save(state)
        return course

    def step_definition(self, course, name):
        state = course.load()
        task = course.current(state)
        return next(step for step in steps_for(task, state['study_mode'])
                    if step['id'] == name)

    def advance_before_run(self, course, stop_at_check=False):
        for _ in range(100):
            shown = course.lesson_step()
            if shown.get('needs_run') or shown.get('preparation_complete'):
                return shown
            self.assertIn('step', shown)
            step = self.step_definition(course, shown['step_id'])
            if step.get('check'):
                if stop_at_check:
                    return step
                course.lesson_answer(step['id'], step['check']['correct'])
            course.lesson_next(step['id'],
                'The explanation was shown in the final reply and the learner continued.')
        self.fail('Teaching steps did not reach a run boundary or a checkpoint.')

    def assert_no_answers(self, value):
        if isinstance(value, dict):
            self.assertFalse(PRIVATE_KEYS.intersection(value))
            for child in value.values():
                self.assert_no_answers(child)
        elif isinstance(value, list):
            for child in value:
                self.assert_no_answers(child)

    def cli(self, action, *arguments, expected=0):
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'tutor.py'), action,
            '--workspace', str(self.workspace), '--week', 'week04', *arguments],
            cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads(result.stdout) if result.stdout.strip() else {}


class Week4CurriculumTests(Week4Case):
    def test_catalog_is_read_only_and_both_modes_fit_two_fifty_minute_sessions(self):
        before = self.files()
        result = catalog(self.workspace)
        self.assertEqual([item['id'] for item in result['courses']],
                         ['week01', 'week02', 'week03', 'week04'])
        self.assertEqual(self.files(), before)
        lesson = seminar_for(self.workspace, 'week04').lesson
        self.assertEqual(sum(t['weight'] for t in lesson['tasks']), 100)
        self.assertEqual(len(lesson['tasks']), 10)
        for field in ('minutes', 'practice_minutes'):
            self.assertEqual(sum(t[field] for t in lesson['tasks'][:5]), 50)
            self.assertEqual(sum(t[field] for t in lesson['tasks'][5:]), 50)
        self.assertEqual(set(lesson['code_targets']), {'record', 'verify', 'stats_inputs', 'guards', 'loop'})
        self.assertIn('complete_tool_step', str(lesson['code_targets']['loop']))
        self.assertNotRegex(json.dumps(lesson, ensure_ascii=False), '[\u3400-\u9fff]')

    def test_review_explains_slides_and_actual_code_while_practice_has_its_own_path(self):
        lesson = seminar_for(self.workspace, 'week04').lesson
        packs = {'lecture': ROOT / 'week04/lecture_demo',
                 'seminar': ROOT / 'week04/resources'}
        slides = []
        sources = set()
        for task in lesson['tasks']:
            review = steps_for(task, 'review')
            practice = steps_for(task, 'practice')
            self.assertTrue(review)
            self.assertTrue(practice)
            self.assertNotEqual(review, practice)
            for mode in ('review', 'practice'):
                for step in steps_for(task, mode):
                    self.assertIn(step['phase'], ('before_run', 'after_run'))
                    card = step.get('slide_review')
                    if mode == 'review' and card:
                        self.assertTrue(card['visual_walkthrough'])
                        self.assertTrue(card['code_bridge'])
                        self.assertGreater(len(card['explanation'].split()), 25)
                        self.assertTrue((ROOT / 'week04' / card['image']).is_file())
                        slides.append(card['primary_slide'])
                    for ref in step.get('code_refs', []):
                        with self.subTest(task=task['id'], mode=mode, source=ref):
                            snippet = excerpt(ref, packs)
                            self.assertTrue(snippet['numbered_code'])
                            self.assertLessEqual(len(snippet['numbered_code'].splitlines()), 12)
                            sources.add((mode, ref['pack']))
        self.assertIn(6, slides)
        self.assertIn(25, slides)
        self.assertIn(27, slides)
        self.assertIn(('review', 'lecture'), sources)
        self.assertIn(('practice', 'seminar'), sources)


class Week4PreservationTests(Week4Case):
    def test_starting_week_four_preserves_all_old_week_records_sources_and_snapshots(self):
        self.assertEqual((SCHEMA, PROGRESS_NAMESPACE), (2, 'v2'))
        for week in ('week01', 'week02', 'week03'):
            old = seminar_for(self.workspace, week)
            old.start()
            state = old.load()
            state['tasks'][old.lesson['tasks'][0]['id']]['complete'] = True
            old.save(state)
            learner_source = next(old.resources.rglob('*.py'))
            learner_source.write_bytes(learner_source.read_bytes() + b'\n# My saved course work.\n')
            guide = old.base / 'TEACHING.snapshot.md'
            guide.write_bytes(guide.read_bytes() + b'\nHistorical teaching notes remain pinned.\n')
        before = self.files()
        current = self.course()
        current.lesson_step()
        current.select_session(fresh=True)
        current = seminar_for(self.workspace, 'week04')
        current.start()
        catalog(self.workspace)
        for name, data in before.items():
            self.assertEqual((self.workspace / name).read_bytes(), data, name)
        for week in ('week01', 'week02', 'week03'):
            old = seminar_for(self.workspace, week)
            old.start()
            self.assertGreater(old.status()['core_percent'], 0)
        for name, data in before.items():
            self.assertEqual((self.workspace / name).read_bytes(), data, name)

    def test_replay_keeps_prior_answers_and_code_and_starts_separate_progress(self):
        original = self.course()
        original.mutate('save', 'Pause before trying the next idea.')
        source = original.resources / 'state.py'
        source.write_bytes(source.read_bytes() + b'\n# My first attempt.\n')
        before = {p: p.read_bytes() for p in original.base.rglob('*') if p.is_file()}
        before[source] = source.read_bytes()
        original.select_session(fresh=True)
        replay = seminar_for(self.workspace, 'week04')
        self.assertNotEqual(replay.session, 'original')
        self.assertEqual(replay.status()['core_percent'], 0)
        self.assertEqual(replay.load()['notes'], [])
        self.assertNotEqual(replay.resources, original.resources)
        self.assertNotIn('My first attempt', (replay.resources / 'state.py').read_text())
        for path, data in before.items():
            self.assertEqual(path.read_bytes(), data)
        replay.select_session('original')
        restored = seminar_for(self.workspace, 'week04')
        self.assertEqual(restored.resources, original.resources)
        self.assertEqual(restored.load()['notes'][-1]['text'], 'Pause before trying the next idea.')

    def test_new_installed_sources_do_not_replace_saved_curriculum_or_learner_code(self):
        local_root = self.directory / 'updated-plugin'
        local_root.mkdir()
        shutil.copytree(ROOT / 'week04', local_root / 'week04',
                        ignore=shutil.ignore_patterns('__pycache__', '.venv', '.env'))
        course = self.course(root=local_root)
        original = {p: p.read_bytes() for p in course.base.rglob('*') if p.is_file()}
        source = course.resources / 'state.py'
        source.write_bytes(source.read_bytes() + b'\n# A learner change.\n')
        original[source] = source.read_bytes()
        (local_root / 'week04/resources/state.py').write_text('# Revised starter\n', encoding='utf-8')
        new_lesson = copy.deepcopy(course.lesson)
        new_lesson['version'] += 1
        atomic_json(local_root / 'week04/lesson.json', new_lesson)
        resumed = seminar_for(self.workspace, 'week04', root=local_root)
        resumed.start()
        self.assertEqual(resumed.lesson['version'], course.lesson['version'])
        self.assertTrue(resumed.status()['new_script_available'])
        for path, data in original.items():
            self.assertEqual(path.read_bytes(), data)


class Week4LearningGates(Week4Case):
    def test_chat_code_targets_the_method_and_keeps_an_exact_recoverable_attempt(self):
        course = self.course(task_id='t05')
        path = course.resources / 'state.py'
        original = path.read_bytes()
        attempt = "raise NotImplementedError('My own incomplete attempt')"
        with self.assertRaises(ValueError):
            course.write_code('record', attempt)
        self.assertEqual(path.read_bytes(), original)
        self.advance_before_run(course)
        course.write_code('record', attempt)
        changed = path.read_text(encoding='utf-8')
        tree = ast.parse(changed)
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'State')
        record = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == 'record')
        self.assertEqual(ast.unparse(record.body[-1]), attempt)
        self.assertTrue(any(isinstance(node, ast.FunctionDef) and node.name == 'context' for node in cls.body))
        drafts = course.load()['tasks']['t05']['code_drafts']
        self.assertEqual(drafts[-1]['student_text'], attempt)
        self.assertEqual(Path(drafts[-1]['previous']).read_bytes(), original)
        before = self.files()
        with self.assertRaises((ValueError, SyntaxError)):
            course.write_code('record', 'if this is not Python:')
        self.assertEqual(self.files(), before)
        with self.assertRaises(ValueError):
            course.write_code('loop', attempt)

    def test_code_help_requires_attempts_between_hints_then_a_new_own_words_response(self):
        course = self.course(task_id='t05')
        self.advance_before_run(course)
        name = 'code:record'
        course.support('attempt', name, 'I do not know how to keep a separate copy of this dictionary.')
        course.support('hint', name, 'Please help me find the first step.')
        with self.assertRaises(ValueError):
            course.support('hint', name, 'Give the second hint without another attempt.')
        with self.assertRaises(ValueError):
            course.support('solution', name, 'Please give me the answer before the second hint.')
        course.support('attempt', name, 'I would assign the result dictionary, but I am unsure if that makes a copy.')
        course.support('hint', name, 'Please explain what copying changes.')
        with self.assertRaises(ValueError):
            course.support('solution', name, 'Skip my response to the second hint.')
        course.support('attempt', name, 'I still need help to turn this into the code.')
        course.support('solution', name, 'Please explain the answer now rather than give another hint.')
        with self.assertRaises(ValueError):
            course.support('assess', name, 'There was no learner explanation.', 'pass')
        course.support('answer', name, 'The record needs a separate copy so a later change does not alter the saved evidence.')
        course.support('assess', name, 'Add how this applies to nested data.', 'retry')
        with self.assertRaises(ValueError):
            course.support('assess', name, 'Regrade the same response without new work.', 'pass')
        course.support('answer', name, 'A deep copy also copies the nested result objects, so later changes cannot rewrite what the tool returned.')
        course.support('assess', name, 'The explanation connects the copied data to reliable historical evidence.', 'pass')
        self.assertFalse(course.load()['tasks']['t05']['complete'])

    def test_unrun_observations_and_checks_are_not_shown_or_accepted(self):
        for mode in ('review', 'practice'):
            with self.subTest(mode=mode):
                if mode == 'practice':
                    seminar_for(self.workspace, 'week04').select_session(fresh=True)
                course = self.course(mode, 't03')
                boundary = self.advance_before_run(course)
                self.assertTrue(boundary.get('needs_run'))
                self.assertEqual(boundary['phase'], 'after_run')
                self.assertNotIn('step', boundary)
                self.assertNotIn('snippets', boundary)
                before = self.files()
                with self.assertRaises(ValueError):
                    course.lesson_next(boundary['step_id'], 'Pretend the experiment already happened.')
                definition = self.step_definition(course, boundary['step_id'])
                if definition.get('check'):
                    with self.assertRaises(ValueError):
                        course.lesson_answer(boundary['step_id'], definition['check']['correct'])
                self.assertEqual(self.files(), before)

    def test_pending_teaching_blocks_running_and_awarding_completion(self):
        course = self.course(task_id='t03')
        state = course.load()
        state['environment'] = {'status': 'ready', 'python': sys.executable}
        record = state['tasks']['t03']
        record['teaching'].append({'text': 'A generic introduction is insufficient.'})
        record['predictions'].append({'text': 'I think this loop repeats the same request.'})
        course.save(state)
        with patch('subprocess.run', side_effect=AssertionError('No subprocess before teaching.')):
            with self.assertRaises(ValueError):
                course.run(None, 'Inspect the repeated action and the early finish request.')
        with self.assertRaises(ValueError):
            course.mutate('complete')
        self.assertFalse(course.load()['tasks']['t03']['runs'])

    def test_checkpoint_needs_interleaved_attempts_and_own_words_after_answer_explanation(self):
        course = self.course()
        step = self.advance_before_run(course, stop_at_check=True)
        self.assertIn('check', step)
        name = step['id']
        check = step['check']
        wrong = next(key for key in check['options'] if key != check['correct'])
        before = course.status()['core_percent']
        with self.assertRaises(ValueError):
            course.lesson_next(name, 'Move on without asking the learner.')
        self.assert_no_answers(course.lesson_step()['step'])
        course.lesson_answer(name, wrong)
        course.lesson_hint(name, 'Please give me a first clue.')
        with self.assertRaises(ValueError):
            course.lesson_hint(name, 'Give both hints without another learner attempt.')
        course.lesson_answer(name, wrong)
        course.lesson_hint(name, 'I tried again; please give me a clearer clue.')
        with self.assertRaises(ValueError):
            course.lesson_solution(name, 'Explain immediately without letting me try the second hint.')
        course.lesson_answer(name, wrong)
        course.lesson_solution(name, 'I would like you to explain the answer now.')
        with self.assertRaises(ValueError):
            course.lesson_next(name, 'The mentor explanation is enough.')
        with self.assertRaises(ValueError):
            course.lesson_answer(name, check['correct'])
        with self.assertRaises(ValueError):
            course.lesson_answer(name, 'SHOWCASE')
        course.lesson_answer(name, 'The program must check the actual tool results against the task before claiming that it is finished.')
        course.lesson_assess(name, 'Explain which part belongs to the program.', 'retry')
        with self.assertRaises(ValueError):
            course.lesson_assess(name, 'Change the grade without a new explanation.', 'pass')
        course.lesson_answer(name, 'The model proposes an action, and the Python program executes it, records its result, and checks whether the task is complete.')
        course.lesson_assess(name, 'You separated the proposed action from the completed task.', 'pass')
        course.lesson_next(name, 'Confirmed this learner explanation after showing the full teaching reply.')
        self.assertEqual(course.status()['core_percent'], before)

    def test_current_step_and_completed_checkpoint_resume_without_mode_transfer(self):
        course = self.course()
        step = self.advance_before_run(course, stop_at_check=True)
        course.lesson_answer(step['id'], step['check']['correct'])
        before = self.files()
        resumed = seminar_for(self.workspace, 'week04')
        self.assertEqual(resumed.lesson_step()['step_id'], step['id'])
        self.assertTrue(resumed.lesson_step()['checkpoint_passed'])
        self.assertEqual(self.files(), before)
        resumed.study_mode('practice')
        practice = self.advance_before_run(resumed, stop_at_check=True)
        with self.assertRaises(ValueError):
            resumed.lesson_next(practice['id'], 'The answer in the other mode also counts here.')
        resumed.study_mode('review')
        self.assertTrue(resumed.lesson_step()['checkpoint_passed'])

    def test_cli_formal_reply_contract_and_read_only_revisit_preserve_the_current_position(self):
        course = self.course(task_id='t05')
        before = self.files()
        shown = self.cli('lesson-step')
        self.assertTrue(shown['response_contract']['final_reply_required'])
        self.assertEqual(shown['response_contract']['progress'],
                         {'week': 'week04', 'core_percent': course.status()['core_percent']})
        old = course.revisit('t01')
        self.assertEqual(old['task']['id'], 't01')
        self.assertTrue(old['core_progress_unchanged'])
        self.assertEqual(course.status()['current_task'], 't05')
        self.assert_no_answers(old)
        self.assertEqual(self.files(), before)

    def test_repeated_teaching_acknowledgement_is_idempotent(self):
        course = self.course()
        shown = course.lesson_step()
        step = self.step_definition(course, shown['step_id'])
        if step.get('check'):
            course.lesson_answer(step['id'], step['check']['correct'])
        course.lesson_next(step['id'], 'The learner has seen this explanation and is ready to continue.')
        before = self.files()
        result = course.lesson_next(step['id'], 'The same acknowledgement was delivered a second time.')
        self.assertTrue(result['duplicate_ignored'])
        self.assertEqual(self.files(), before)

    def test_an_explained_code_answer_blocks_running_and_advancing_until_own_words_pass(self):
        course = self.course(task_id='t05')
        boundary = self.advance_before_run(course)
        state = course.load()
        state['environment'] = {'status': 'ready', 'python': sys.executable}
        course.save(state)
        name = 'code:record'
        course.support('attempt', name, 'I am not sure how to copy the result.')
        course.support('hint', name, 'Please point me to the first step.')
        course.support('attempt', name, 'I would save the dictionary, but I cannot explain the copying.')
        course.support('hint', name, 'Please give me the next clue.')
        course.support('attempt', name, 'I still need the code explained.')
        course.support('solution', name, 'Please explain this answer now.')
        solution = json.loads((ROOT / 'week04/instructor/solutions.json').read_text())['record']
        course.write_code('record', solution)
        before = self.files()
        with patch('subprocess.run', side_effect=AssertionError('No execution before the own-words check.')):
            with self.assertRaisesRegex(ValueError, "learner's own explanation"):
                course.run(None, 'Try to test the answer before checking understanding.')
            with self.assertRaisesRegex(ValueError, "learner's own explanation"):
                course.run(None, 'Try optional work while the explanation is unfinished.', name='workflow',
                           prediction='I expect the fixed workflow to need the same evidence.')
        with self.assertRaisesRegex(ValueError, "learner's own explanation"):
            course.lesson_next(boundary['step_id'], 'Try to move past the pending explanation.')
        self.assertEqual(self.files(), before)
        last_done = course.load()['tasks']['t05']['path_teaching']['review'][-1]['id']
        self.assertTrue(course.lesson_next(last_done, 'A duplicate acknowledgement does not advance learning.')['duplicate_ignored'])
        course.support('answer', name, 'The copied observation keeps the returned nested data separate from the objects edited later.')
        course.support('assess', name, 'You explained how the stored evidence stays independent.', 'pass')
        self.assertNotIn('explain code:record in your own words and check understanding', course.status()['remaining_requirements'])

    def test_extension_prediction_survives_failed_execution_and_reload(self):
        course = self.course()
        state = course.load()
        state['environment'] = {'status': 'ready', 'python': sys.executable}
        course.save(state)
        prediction = 'I expect the fixed workflow to collect the same readings and reference before calculating the share.'
        percent = course.status()['core_percent']
        with patch('subprocess.run', side_effect=OSError('The test deliberately makes this local launch unavailable.')):
            result = course.run(None, 'Compare the explained fixed workflow with the loop.', name='workflow', prediction=prediction)
        self.assertEqual(result['run']['status'], 'failed')
        self.assertEqual(result['run']['prediction'], prediction)
        receipt = json.loads((Path(result['run']['folder']) / 'receipt.json').read_text())
        self.assertEqual(receipt['prediction'], prediction)
        resumed = seminar_for(self.workspace, 'week04')
        self.assertEqual(resumed.load()['extensions']['workflow']['runs'][-1]['prediction'], prediction)
        self.assertEqual(resumed.results('workflow')['run']['prediction'], prediction)
        self.assertEqual(resumed.status()['core_percent'], percent)


class Week42ExerciseGates(Week4Case):
    def test_t06_needs_both_code_attempts_and_keeps_each_submission(self):
        course = self.course(task_id='t06')
        self.advance_before_run(course)
        for concept in course.current(course.load()).get('concepts', []):
            course.concept_choice(concept, 'brief')
        state = course.load()
        state['environment'] = {'status': 'ready', 'python': sys.executable}
        course.save(state)
        course.mutate('predict', 'Equal summary numbers can hide different input readings.')
        solutions = json.loads((ROOT / 'week04/instructor/solutions.json').read_text(encoding='utf-8'))
        course.write_code('verify', solutions['verify'])
        self.assertEqual(course.task()['pending_code_targets'], ['stats_inputs'])
        self.assertIn('save the learner code for stats_inputs', course.status()['remaining_requirements'])
        before = self.files()
        with patch('week04_support.subprocess.run', side_effect=AssertionError('Do not run before both attempts.')):
            with self.assertRaisesRegex(ValueError, 'stats_inputs'):
                course.run(None, 'Test the two parts of the verifier.')
        self.assertEqual(self.files(), before)
        course.write_code('stats_inputs', solutions['stats_inputs'])
        self.assertEqual(course.task()['pending_code_targets'], [])
        drafts = course.load()['tasks']['t06']['code_drafts']
        self.assertEqual([draft['target'] for draft in drafts], ['verify', 'stats_inputs'])
        self.assertEqual(drafts[-1]['student_text'], solutions['stats_inputs'])
        self.assertTrue(all(Path(draft['previous']).is_file() for draft in drafts))
        self.assertFalse(course.load()['tasks']['t06']['complete'])

    def test_old_saved_task_contract_does_not_acquire_new_requirements(self):
        course = self.course(task_id='t06')
        legacy_task = copy.deepcopy(course.current(course.load()))
        legacy_task.pop('required_code_targets', None)
        self.assertEqual(course.required_code_targets(legacy_task), ['verify'])
        self.assertEqual(course.pending_code_targets(legacy_task, {'code_drafts': [{'target': 'verify'}]}), [])
        self.assertEqual(course.required_code_targets({'id': 'discussion'}), [])

    @unittest.skipUnless(os.environ.get('WEEK04_LEGACY_ARCHIVE'), 'Set WEEK04_LEGACY_ARCHIVE to test a real v1 distribution upgrade.')
    def test_actual_v1_session_resumes_without_new_exercise_or_changed_snapshots(self):
        old_root = self.directory / 'legacy-plugin'
        old_root.mkdir()
        with zipfile.ZipFile(os.environ['WEEK04_LEGACY_ARCHIVE']) as archive:
            for name in archive.namelist():
                self.assertTrue((old_root / name).resolve().is_relative_to(old_root.resolve()))
            archive.extractall(old_root)
        course = self.course(task_id='t06', root=old_root)
        self.assertEqual(course.lesson['version'], 1)
        self.advance_before_run(course)
        solution = json.loads((old_root / 'week04/instructor/solutions.json').read_text(encoding='utf-8'))['verify']
        course.write_code('verify', solution)
        before = self.files()
        current = seminar_for(self.workspace, 'week04', root=ROOT)
        task = current.current(current.load())
        self.assertEqual(current.lesson['version'], 1)
        self.assertEqual(current.required_code_targets(task), ['verify'])
        self.assertEqual(current.task()['pending_code_targets'], [])
        self.assertNotIn('stats_inputs', current.lesson['code_targets'])
        with self.assertRaises(ValueError):
            current.write_code('stats_inputs', 'return True')
        self.assertEqual(self.files(), before)
        current.select_session(fresh=True)
        renewed = seminar_for(self.workspace, 'week04', root=ROOT)
        self.assertEqual(renewed.lesson['version'], 2)
        task = next(t for t in renewed.lesson['tasks'] if t['id'] == 't06')
        self.assertEqual(renewed.required_code_targets(task), ['verify', 'stats_inputs'])
        for name, data in before.items():
            if name.endswith('active-session.json'):
                continue
            self.assertEqual((self.workspace / name).read_bytes(), data, name)


class Week4RealExperiments(Week4Case):
    def prepare_experiment(self, course):
        state = course.load()
        task = course.current(state)
        for concept in task.get('concepts', []):
            course.concept_choice(concept, 'brief')
        self.advance_before_run(course)
        if state['environment'].get('status') != 'ready':
            setup = course.setup(sys.executable)
            self.assertTrue(all(item['returncode'] == 0 for item in setup['checks']), setup)
        course.mutate('predict', 'I will compare the saved observations with the stated goal and check why execution ends.')

    def finish_current_task(self, course):
        self.advance_before_run(course)
        task = course.current(course.load())
        course.mutate('explain', 'The displayed result separates the experiment label, test or trace artifacts, actual observations, and the reason for the ending.')
        for question in task['questions']:
            course.mutate('answer', question.get('worked_answer', 'The observed output supports this conclusion.'), question=question['id'])
            if question['type'] == 'open':
                course.mutate('assess', 'This simulated learner answer addresses the evidence and the stated task rubric.', question=question['id'], verdict='pass')
        course.mutate('complete')

    def test_both_complete_courses_use_real_evidence_and_all_required_student_implementations(self):
        solutions = json.loads((ROOT / 'week04/instructor/solutions.json').read_text(encoding='utf-8'))
        for mode in ('review', 'practice'):
            with self.subTest(mode=mode):
                if mode == 'practice':
                    seminar_for(self.workspace, 'week04').select_session(fresh=True)
                course = self.course(mode)
                for expected_id in ('t01', 't02', 't03', 't04', 't05', 't06', 't07', 't08', 't09', 't10'):
                    with self.subTest(task=expected_id):
                        task = course.current(course.load())
                        self.assertEqual(task['id'], expected_id)
                        if task['commands']:
                            self.prepare_experiment(course)
                            for target in course.required_code_targets(task):
                                course.write_code(target, solutions[target])
                            execution = course.run(None, 'Run the explained local experiment and inspect its actual saved result.')
                            self.assertEqual(execution['run']['status'], 'success', execution)
                            self.assertTrue(execution['observed_result']['success'])
                            self.assertEqual(execution['run']['planned_calls'], 0)
                            self.assertEqual(execution['run']['prediction'], course.load()['tasks'][expected_id]['predictions'][-1])
                            observed = execution['observed_result']
                            if expected_id == 't02':
                                self.assertEqual(observed['evidence_kind'], 'recorded_live')
                                self.assertEqual(observed['observation']['requests_made_now'], 0)
                                self.assertEqual(observed['observation']['actual_requests_in_teacher_capture'], 1)
                                capture = json.loads(Path(observed['observation']['record']).read_text())
                                self.assertEqual(capture['evidence_kind'], 'live_deepseek')
                                self.assertEqual(capture['provider'], 'DeepSeek')
                                self.assertEqual(capture['actual_requests'], 1)
                                self.assertEqual(capture['follow_up_requests'], 0)
                                self.assertEqual(capture['requested_tool_calls'], len(capture['response']['message']['tool_calls']))
                                self.assertNotIn('reasoning_content', capture['response']['message'])
                            else:
                                self.assertNotIn(observed['evidence_kind'], {'live_deepseek', 'recorded_live'})
                            if task.get('code_target'):
                                self.assertEqual(observed['evidence_kind'], 'student_code_execution')
                                artifact = Path(execution['run']['folder']) / 'student_observation.json'
                                self.assertEqual(json.loads(artifact.read_text()), observed['observation'])
                            receipt = Path(execution['run']['folder']) / 'receipt.json'
                            self.assertEqual(json.loads(receipt.read_text())['id'], execution['run']['id'])
                            self.assertEqual(course.results()['observed_result'], execution['observed_result'])
                        self.finish_current_task(course)
                        course = seminar_for(self.workspace, 'week04')
                self.assertEqual(course.status()['core_percent'], 100)
                self.assertIsNone(course.status()['current_task'])

    def test_changed_code_and_data_require_a_new_run_and_new_after_run_check(self):
        course = self.course(task_id='t03')
        self.prepare_experiment(course)
        first = course.run(None, 'Observe the actual bounded failures in the reference demonstration.')
        self.assertEqual(first['run']['status'], 'success', first)
        self.advance_before_run(course)
        record = course.load()['tasks']['t03']
        self.assertTrue(course.usable_run(record))
        original_checks = copy.deepcopy(record['path_checks']['review'])
        self.assertTrue(original_checks)
        source = course.resources / 'runtime.py'
        original = source.read_bytes()
        source.write_bytes(original + b'\n# A learner changed the source after this experiment.\n')
        self.assertFalse(course.usable_run(course.load()['tasks']['t03']))
        self.assertIn('run again after the latest source change', course.status()['remaining_requirements'])
        with self.assertRaises(ValueError):
            course.mutate('complete')
        source.write_bytes(original)
        data = next((course.resources / 'data').glob('*.csv'))
        original_data = data.read_bytes()
        data.write_bytes(original_data + b'\n')
        self.assertFalse(course.usable_run(course.load()['tasks']['t03']))
        data.write_bytes(original_data)
        self.assertTrue(course.usable_run(course.load()['tasks']['t03']))
        second = course.run(None, 'Repeat the explained experiment to inspect a new result.')
        self.assertEqual(second['run']['status'], 'success', second)
        record = course.load()['tasks']['t03']
        self.assertEqual(record['path_run_history'][-1]['run_id'], first['run']['id'])
        self.assertEqual(record['path_run_history'][-1]['path_checks']['review'], original_checks)
        self.assertFalse(record['path_checks']['review'])
        self.assertNotEqual(course.lesson_step()['run_id'], first['run']['id'])
        with self.assertRaises(ValueError):
            course.mutate('complete')

    def test_teacher_analysis_rejects_fake_or_changed_capture(self):
        course = self.course(task_id='t02')
        fake = self.directory / 'offline-contract.json'
        fake.write_text(json.dumps({'evidence_kind': 'contract_test', 'provider': 'Fake API',
            'actual_requests': 1, 'follow_up_requests': 0, 'response': {'id': 'offline-id'},
            'observations': [], 'after': {'missing': ['query'], 'ready': False}}), encoding='utf-8')
        (fake.parent / 'SOURCE.json').write_text(json.dumps({'files': {
            fake.name: hashlib.sha256(fake.read_bytes()).hexdigest()}}), encoding='utf-8')
        output = self.directory / 'fake-record-output'
        result = subprocess.run([sys.executable, '-B', 'seminar_step.py', '--task', 't02',
            '--mode', 'teacher', '--teacher-record', str(fake), '--output-dir', str(output)],
            cwd=course.resources, capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        report = json.loads((output / 'lesson_result.json').read_text())
        self.assertFalse(report['success'])
        self.assertEqual(report['evidence_kind'], 'not_executed')
        self.assertIn('not a complete real one-request teacher capture', report['summary'])
        source = ROOT / 'week04/teacher-data/single_round.json'
        fake.write_bytes(source.read_bytes() + b'\n')
        (fake.parent / 'SOURCE.json').write_text(json.dumps({'files': {
            fake.name: hashlib.sha256(source.read_bytes()).hexdigest()}}), encoding='utf-8')
        changed_output = self.directory / 'changed-record-output'
        result = subprocess.run([sys.executable, '-B', 'seminar_step.py', '--task', 't02',
            '--mode', 'teacher', '--teacher-record', str(fake), '--output-dir', str(changed_output)],
            cwd=course.resources, capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        report = json.loads((changed_output / 'lesson_result.json').read_text())
        self.assertFalse(report['success'])
        self.assertEqual(report['evidence_kind'], 'not_executed')
        self.assertIn('differs from its source manifest', report['summary'])


if __name__ == '__main__':
    unittest.main()
