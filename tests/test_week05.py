"""Run the Week 5 teaching paths and their local experiments in disposable workspaces."""

from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tutor import ROOT, seminar_for
from week03_flow import steps_for


VISIBLE_CONTENT = {
    't01_overview': ('**State:', '**Node:', '**Edge:', '**Checkpoint:', '**Interrupt:', 'Already charged?'),
    't01_prepare': ('**Question.**', '**Setup.**', '**Results to read.**', 'mean_restarts'),
    't02_prepare': ('**Question.**', '**Setup.**', '**Results to read.**', 'failed_with_bookings'),
    't04_prepare': ('python -m pip install -r workflow/requirements.txt', 'python -m workflow check edges'),
    't05_rules': ('Qiu Long', 'new tab', 'QQ Music', '1. Return an update.', '2. Merge computes', '3. Commit once.'),
    't05_prepare': ('**Question.**', '**Setup.**', '**Results to read.**', 'blocked_requests'),
    't05_evidence': ('281', 'read_requestsearch_tickets', '1,140 USD', 'wrong_spent=0'),
    't06_prepare': ('Monday', 'waiting request', 'wax seal', 'data_fingerprint', 'digest(payload)'),
    't07_prepare': ('tomorrow', 'ticket database', 'medical folder', 'checkpoints.sqlite', 'Command(resume=decision)'),
    't07_evidence': ('`sync`', '`async`', '`exit`'),
    't08_prepare': ('writing a ticket before it asks', 'ticket table', 'from the top', 'unprotected insert', 'find the call to `suspend`'),
    't08_evidence': ('before_interrupt', 'once on resume', 'writer pending'),
    't09_prepare': ('rerunning the writer', 'two separate saves', '315 repeated requests', 'different `payload_hash`', '`EffectStore.apply`'),
    't09_evidence': ('process IDs', 'reused', 'payload_collision'),
}


class Week5IntegrationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='week05-learning-')
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name) / 'learner'
        self.workspace.mkdir()
        source = ROOT / 'week05' / 'instructor' / 'solutions.json'
        self.solutions = json.loads(source.read_text(encoding='utf-8'))

    def cli(self, action, *args):
        return subprocess.run([sys.executable, '-B', str(ROOT / 'tutor.py'), action,
                               '--workspace', str(self.workspace), '--week', 'week05', *args],
                              capture_output=True, text=True, encoding='utf-8', timeout=30)

    def test_exact_step_read_is_independent_of_the_cursor_and_gates_after_run(self):
        course = seminar_for(self.workspace, 'week05')
        course.start()
        course.study_mode('review')
        before = course.path.read_bytes()
        default = json.loads(self.cli('lesson-step').stdout)
        self.assertEqual(default['step_id'], 't01.review_overview')

        exact = self.cli('lesson-step', '--step-id', 't02.review_prepare')
        self.assertEqual(exact.returncode, 0, exact.stderr)
        displayed = json.loads(exact.stdout)
        self.assertEqual(displayed['step_id'], 't02.review_prepare')
        self.assertEqual(displayed['step']['id'], displayed['step_id'])
        self.assertEqual(displayed['step']['snippets'][0]['symbol'], 'reflex')
        self.assertIs(displayed['read_only'], True)

        single = self.cli('lesson-step', '--step-id', 't02.review_prepare', '--code-index', '1')
        self.assertEqual(single.returncode, 0, single.stderr)
        self.assertEqual(len(json.loads(single.stdout)['step']['snippets']), 1)

        for step_id in ('t02.missing', 't02.practice_prepare'):
            invalid = self.cli('lesson-step', '--step-id', step_id)
            self.assertEqual(invalid.returncode, 1)
            self.assertIn(step_id, json.loads(invalid.stderr)['error'])

        unrun = self.cli('lesson-step', '--step-id', 't02.review_evidence')
        self.assertEqual(unrun.returncode, 0, unrun.stderr)
        waiting = json.loads(unrun.stdout)
        self.assertIs(waiting['needs_run'], True)
        self.assertNotIn('step', waiting)
        self.assertNotIn('observed_result', waiting)
        self.assertEqual(course.path.read_bytes(), before)

    def test_step_id_response_and_entry_reuse_next_step_without_an_extra_read(self):
        course = seminar_for(self.workspace, 'week05')
        course.start()
        entered = self.cli('study-mode', '--study-mode', 'review', '--next-step')
        self.assertEqual(entered.returncode, 0, entered.stderr)
        entry = json.loads(entered.stdout)
        current = entry['next_step']['step_id']
        self.assertEqual(current, 't01.review_overview')
        self.assertEqual(entry['core_percent'], 0)
        self.assertNotIn('status', entry['next_step'])
        before = course.path.read_bytes()

        for action, options in (
            ('lesson-answer', ('--step-id', current, '--name', 't02.review_prepare', '--text', 'A')),
            ('lesson-answer', ('--step-id', current, '--text', 'A', '--next-step')),
            ('study-mode', ('--week', 'week04', '--study-mode', 'review', '--next-step')),
            ('list', ('--next-step',)),
        ):
            rejected = self.cli(action, *options)
            self.assertEqual(rejected.returncode, 1, rejected.stdout)
            self.assertEqual(course.path.read_bytes(), before)

        answer = self.cli('lesson-answer', '--step-id', current, '--text', 'A')
        self.assertEqual(answer.returncode, 0, answer.stderr)
        self.assertTrue(json.loads(answer.stdout)['passed'])
        advanced = self.cli('lesson-next', '--step-id', current, '--name', current,
                            '--text', 'I can explain why the saved checkpoint is needed.')
        self.assertEqual(advanced.returncode, 0, advanced.stderr)
        self.assertEqual(json.loads(advanced.stdout)['step_id'], 't01.review_prepare')

    def test_both_routes_return_the_two_approved_student_cues(self):
        open_line = 'Rules stand first \u2014 only then does the workflow stop hurting.'
        expected = {
            'rules': [open_line, '**\uff08\u89c4\u77e9\u7acb\u4f4f\u4e86\uff0c\u6d41\u7a0b\u624d\u4e0d\u70e7\u5fc3\uff09**'],
            'two_ledgers': [open_line + ' Our ledger is quiet now; theirs is not.', '**\uff08\u89c4\u77e9\u7acb\u4f4f\u4e86\uff0c\u6d41\u7a0b\u624d\u4e0d\u70e7\u5fc3\u2014\u2014\u6211\u4eec\u8fd9\u672c\u5b89\u9759\u4e86\uff0c\u4ed6\u4eec\u90a3\u672c\u8fd8\u6ca1\u6709\u3002\uff09**'],
        }
        original = seminar_for(self.workspace, 'week05')
        original.start()
        for mode in ('review', 'practice'):
            if mode == 'practice':
                original.select_session(fresh=True)
            course = seminar_for(self.workspace, 'week05')
            course.study_mode(mode)
            weights = [task['minutes'] for task in course.lesson['tasks']]
            self.assertEqual(weights, [11, 7, 12, 11, 9, 12, 12, 12, 9, 5])
            opening = course.lesson_step()['step']
            saved_opening = steps_for(course.lesson['tasks'][0], mode)[0]
            story = opening['opening_story']
            opening_prefix = opening['instructor_opening'] + story
            self.assertEqual(saved_opening['student_script'][:len(opening_prefix)], opening_prefix)
            self.assertEqual(opening['student_script'], saved_opening['student_script'][len(opening_prefix):])
            for paragraph, cue in zip(story, ('Week 1', 'bigger job', 'process’s memory', 'state machine'), strict=True):
                self.assertIn(cue, paragraph)
            self.assertIn('no heading or question in between', opening['presentation'])
            for suffix, lines in expected.items():
                with self.subTest(mode=mode, suffix=suffix):
                    result = self.cli('lesson-step', '--step-id', f't05.{mode}_{suffix}')
                    self.assertEqual(result.returncode, 0, result.stderr)
                    step = json.loads(result.stdout)['step']
                    self.assertEqual(step['required_student_text'], lines)
                    index = step['student_script'].index(lines[0])
                    self.assertEqual(step['student_script'][index:index + 2], lines)
                    self.assertIn('verbatim', step['presentation'])
                    link = 'https://www.bilibili.com/video/BV1min86QEHN/'
                    self.assertEqual(link in json.dumps(step), suffix == 'rules')
                    if suffix == 'two_ledgers':
                        crash, records, counter, operations = step['student_script'][index + 2:]
                        self.assertIn('$960', crash)
                        self.assertIn('Trip 17', crash)
                        self.assertIn('saved state still says to pay', records)
                        self.assertIn('same number', counter)
                        self.assertIn('old receipt', counter)
                        self.assertIn('missing from the register', counter)
                        self.assertEqual([line[:2] for line in operations.splitlines()[:4]], ['1.', '2.', '3.', '4.'])
                        self.assertIn('restored workflow', operations)
                        self.assertEqual([snippet['symbol'] for snippet in step['snippets']], ['World.act'])
                        for code in ('key = f"{trip}:{node}"', 'key in self.receipts', 'return self.receipts[key]',
                                     'self.done[trip, kind] += 1', 'self.receipts[key] = update'):
                            self.assertIn(code, step['snippets'][0]['numbered_code'])
                            self.assertIn(code, '\n'.join(step['code_walkthrough']))
                        self.assertIn('Show the supplied World.act source after the four operations', step['presentation'])
            self.assertEqual(course.status()['core_percent'], 0)

    @unittest.skipUnless(os.environ.get('WEEK05_LEGACY_ARCHIVE'), 'Set WEEK05_LEGACY_ARCHIVE to test the previous Week 5 package.')
    def test_previous_week05_session_keeps_its_snapshot_records_and_code(self):
        legacy = self.workspace.parent / 'previous-package'
        with ZipFile(os.environ['WEEK05_LEGACY_ARCHIVE']) as archive:
            archive.extractall(legacy)
        original = seminar_for(self.workspace, 'week05', legacy)
        original.start()
        original.study_mode('review')
        original.mutate('save', 'My earlier Week 5 note.')
        original.lesson_next('t01.review_prepare', 'I have compared both crash strategies.')
        student_source = original.resources / 'workflow' / 'routing.py'
        student_source.write_bytes(student_source.read_bytes() + b'\n# My earlier source edit.\n')
        saved = {path: path.read_bytes() for base in (original.base, original.resources)
                 for path in base.rglob('*') if path.is_file()}

        current = seminar_for(self.workspace, 'week05')
        status = current.start()
        self.assertEqual(status['lesson_version'], 1)
        self.assertIs(status['new_script_available'], True)
        exact = self.cli('lesson-step', '--step-id', 't02.review_prepare')
        self.assertEqual(exact.returncode, 0, exact.stderr)
        self.assertEqual(json.loads(exact.stdout)['step_id'], 't02.review_prepare')
        fresh = current.select_session(fresh=True)
        self.assertEqual((fresh['lesson_version'], fresh['core_percent']), (7, 0))
        self.assertEqual({path: path.read_bytes() for path in saved}, saved)

    @unittest.skipUnless(os.environ.get('WEEK05_RECENT_ARCHIVE'), 'Set WEEK05_RECENT_ARCHIVE to test an existing compatible session.')
    def test_saved_session_displays_revisions_without_changing_work(self):
        legacy = self.workspace.parent / 'recent-package'
        with ZipFile(os.environ['WEEK05_RECENT_ARCHIVE']) as archive:
            archive.extractall(legacy)
        original = seminar_for(self.workspace, 'week05', legacy)
        original.start()
        original.study_mode('practice')
        original.mutate('save', 'Keep my learning notes.')
        self.assertLess(original.lesson['version'], 7)
        saved = {path: path.read_bytes() for base in (original.base, original.resources)
                 for path in base.rglob('*') if path.is_file()}
        current = seminar_for(self.workspace, 'week05')
        self.assertIn('Already charged?', current.lesson_step()['step']['student_script'][-1])
        old_approval = current.lesson_step(step_id='t06.practice_prepare')['step']
        self.assertIn('wax seal', '\n'.join(old_approval['student_script']))
        self.assertEqual({path: path.read_bytes() for path in saved}, saved)
        self.assertEqual(current.status()['lesson_version'], original.lesson['version'])

    def teach_until_boundary(self, course, task, mode):
        by_id = {step['id']: step for step in steps_for(task, mode)}
        for _ in range(len(by_id) + 1):
            shown = course.lesson_step()
            if shown.get('needs_run') or shown.get('preparation_complete'):
                return shown
            step = by_id[shown['step_id']]
            task_id, suffix = step['id'].split('.')
            phrases = VISIBLE_CONTENT.get(task_id + '_' + suffix.split('_', 1)[1], ())
            if phrases:
                live = shown['step']
                script = '\n'.join(live['student_script'])
                for phrase in phrases:
                    self.assertIn(phrase, script, step['id'])
                if step['phase'] == 'after_run':
                    self.assertTrue(shown['observed_result']['success'])
                if step['id'].endswith('_prepare'):
                    code = '\n'.join(item['numbered_code'] for item in live['snippets'])
                    for fragment in {'t06': ('digest(payload)', 'validate_decision'),
                                     't08': ('self.suspend', 'resume_approval', 'def route_approval'),
                                     't09': ('SELECT payload_hash', 'different payload', '"reused"')}.get(task_id, ()):
                        self.assertIn(fragment, code, step['id'])
            if step.get('check'):
                checked = course.lesson_answer(step['id'], step['check']['correct'])
                self.assertTrue(checked['passed'], checked)
            course.lesson_next(step['id'], 'I have read the explanation and I am ready to continue.')
        self.fail('The lesson did not reach a run boundary or finish its teaching steps.')

    def decision_file(self, course, task_id):
        pending = course.results(task_id='t07')['observed_result']['decision_requests']

        def reply(thread, approved):
            request = pending[thread]
            return {'approved': approved, 'reviewer': 'Test tutor', 'action_id': request['action_id'],
                    'payload_hash': request['payload_hash']}

        path = self.workspace / f'{task_id}-test-decision.json'
        decision = ({'approve': reply('week05-approve', True), 'reject': reply('week05-reject', False)}
                    if task_id == 't08' else reply('week05-recovery', True))
        path.write_text(json.dumps(decision), encoding='utf-8')
        return path, decision

    def run_experiment(self, course, task):
        intro = 'I expect the saved evidence to show which steps run and which effects occur.'
        task_id = task['id']
        path = None
        if task_id in {'t08', 't09'}:
            path, decision = self.decision_file(course, task_id)
            if task_id == 't08':
                malformed = {**decision, 'approve': {**decision['approve'], 'action_id': 'another-action'}}
                path.write_text(json.dumps(malformed), encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'actual waiting task'):
                    course.run(None, intro, decision_file=path)
                self.assertEqual(course.load()['tasks'][task_id]['runs'], [])
                path.write_text(json.dumps(decision), encoding='utf-8')
        decision_arg = ('--decision-file', str(path)) if path else ()
        observed = self.cli('run', '--intro', intro, '--next-step', *decision_arg)
        self.assertEqual(observed.returncode, 0, observed.stderr)
        execution = json.loads(observed.stdout)
        mode = course.load()['study_mode']
        next_step = execution['next_step']
        self.assertEqual(next_step['step_id'], f'{task_id}.{mode}_evidence')
        self.assertNotIn('observed_result', next_step)
        self.assertNotIn('status', next_step)
        self.assertTrue(execution['response_contract']['final_reply_required'])
        for phrase in VISIBLE_CONTENT.get(task_id + '_evidence', ()):
            self.assertIn(phrase, '\n'.join(next_step['step']['student_script']))
        self.assertEqual(execution['run']['status'], 'success', execution)
        self.assertEqual(execution['run']['planned_calls'], 0)
        evidence = execution['observed_result']
        self.assertTrue(evidence['success'], evidence)
        self.assertEqual(course.results(task_id=task_id)['observed_result'], evidence)
        self.check_experiment(task_id, evidence, Path(execution['run']['folder']))

    def check_experiment(self, task_id, evidence, folder):
        if task_id in {'t01', 't02', 't05'}:
            self.assertEqual(evidence['evidence_kind'], 'local_simulation')
            result = evidence['experiment']
            self.assertEqual(result['seed'], 7)
            rows = result['results']
            if task_id == 't01':
                self.assertEqual(result['trips'], 2000)
                self.assertEqual([(r['strategy'], r['mean_steps'], r['extra_charges']) for r in rows],
                                 [('while', 15.842, 2183), ('graph', 9.974, 217)])
                self.assertAlmostEqual(result['expected_steps']['graph'], 10)
            elif task_id == 't02':
                self.assertEqual(result['tasks'], 30)
                by_case = {(r['scenario'], r['strategy'], r['replans']):
                           (r['completed'], r['planning_calls'], r['failed_with_bookings']) for r in rows}
                self.assertEqual(by_case, {
                    ('baseline', 'reflex', None): (10, 30, 0),
                    ('baseline', 'react', None): (30, 120, 0),
                    ('baseline', 'planexec', 0): (30, 30, 0),
                    ('sold-out', 'reflex', None): (10, 30, 0),
                    ('sold-out', 'react', None): (30, 139, 0),
                    ('sold-out', 'planexec', 0): (13, 30, 4),
                    ('sold-out', 'planexec', 1): (28, 47, 2),
                })
            else:
                self.assertEqual(result['trips'], 2000)
                self.assertEqual([(r['write_as'], r['keys'], r['wrong_final_states'],
                                   r['repeated_actions'], r['blocked_requests']) for r in rows], [
                    ('in_place', 'none', 281, 315, 0), ('update', 'none', 0, 315, 0),
                    ('update', 'random', 0, 315, 0), ('update', 'stable', 0, 0, 315),
                ])
                examples = evidence['counterexamples']
                wrong_next = examples['next_in_add']
                self.assertEqual((wrong_next['error'], wrong_next['merged_next']),
                                 ('KeyError', 'read_requestsearch_tickets'))
                spent = examples['spent_not_in_add']
                self.assertEqual((spent['expected_total_usd'], spent['observed_total_usd'],
                                  spent['wrong_spent']), (1140, 180, 0))
                log = examples['whole_log_as_update']
                self.assertEqual(log['wrong_result'], ['verified', 'verified', 'prepared'])
                self.assertEqual(log['correct_result'], ['verified', 'prepared'])
                partial = examples['partial_commit']
                self.assertEqual(partial['in_place']['after_crash']['spent_usd'], 960)
                self.assertEqual(partial['update']['after_crash']['spent_usd'], 0)
        elif task_id in {'t03', 't04', 't06'}:
            self.assertEqual(evidence['evidence_kind'], 'local_exercise_check')
            self.assertTrue(evidence['exercise']['passed'])
        else:
            self.assertEqual(evidence['evidence_kind'], 'langgraph_sqlite_processes')
            self.check_workflow(task_id, evidence, folder)

    def check_workflow(self, task_id, evidence, folder):
        if task_id == 't07':
            self.assertEqual(set(evidence['processes']), {'week05-approve', 'week05-reject', 'week05-recovery'})
            for thread, snapshots in evidence['processes'].items():
                start, inspected = snapshots['start'], snapshots['inspect']
                self.assertNotEqual(start['pid'], inspected['pid'])
                self.assertEqual(inspected['thread_id'], thread)
                self.assertEqual(start['checkpoint_id'], inspected['checkpoint_id'])
                self.assertEqual(inspected['next'], ['HumanApproval'])
                self.assertEqual(inspected['ticket_count'], 0)
                self.assertEqual(inspected['tool_attempts'], 3)
            return
        if task_id == 't08':
            demo = evidence['interrupt_demo']
            self.assertEqual(demo['before_pause'], {'before_interrupt': 1, 'after_interrupt': 0})
            self.assertEqual(demo['after_resume'], {'before_interrupt': 2, 'after_interrupt': 1})
            approved = evidence['approval']
            self.assertEqual((approved['status'], approved['ticket_count']), ('completed', 1))
            rejected = evidence['rejection']
            self.assertEqual((rejected['status'], rejected['ticket_count']), ('rejected', 0))
            invalid = evidence['invalid_reply']
            self.assertEqual(invalid['error']['error'], 'ApprovalError')
            self.assertEqual(invalid['before']['checkpoint_id'], invalid['after']['checkpoint_id'])
            self.assertEqual(invalid['after']['next'], ['HumanApproval'])
            self.assertEqual(invalid['after']['ticket_count'], 0)
            self.assertNotEqual(invalid['error']['pid'], invalid['after']['pid'])
            final = approved
        else:
            fault, interrupted, resumed = (evidence[key] for key in ('fault', 'after_fault', 'after_continue'))
            self.assertEqual(fault['error'], 'SimulatedCrash')
            self.assertEqual(len({fault['pid'], interrupted['pid'], resumed['pid']}), 3)
            self.assertEqual(interrupted['next'], ['ApplyAction'])
            self.assertEqual((resumed['status'], resumed['next']), ('completed', []))
            self.assertEqual(interrupted['tool_attempts'], 3)
            self.assertEqual(interrupted['tool_attempts'], resumed['tool_attempts'])
            self.assertEqual((interrupted['ticket_count'], resumed['ticket_count']), (1, 1))
            self.assertEqual(interrupted['tickets'], resumed['tickets'])
            self.assertIs(resumed['reused'], True)
            collision = evidence['payload_collision']
            self.assertEqual(collision['error'], 'ApprovalError')
            self.assertNotEqual(collision['original_payload_hash'], collision['different_payload_hash'])
            self.assertIs(collision['row_unchanged'], True)
            self.assertEqual((collision['ticket_count_before'], collision['ticket_count_after']), (1, 1))
            final = resumed
        database = folder / 'workflow' / 'effects.sqlite'
        with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as connection:
            self.assertEqual(connection.execute('SELECT action_id, thread_id, payload_hash FROM tickets').fetchall(),
                             [(final['action_id'], final['thread_id'], final['payload_hash'])])

    def complete_path(self, course, mode):
        course.study_mode(mode)
        self.assertEqual(course.status()['core_percent'], 0)
        for number in range(1, 11):
            task_id = f't{number:02}'
            with self.subTest(mode=mode, task=task_id):
                state = course.load()
                task = course.current(state)
                self.assertEqual(task['id'], task_id)
                for concept in task.get('concepts', []):
                    course.concept_choice(concept, 'brief' if mode == 'review' else 'understand')
                boundary = self.teach_until_boundary(course, task, mode)
                if task['commands']:
                    self.assertTrue(boundary.get('needs_run'))
                    if number == 1:
                        setup = course.setup(sys.executable)
                        self.assertTrue(setup['status']['environment']['workflow_ready'], setup)
                    course.mutate('predict', 'I expect the result to record both the outcome and how the run got there.')
                    if task_id == 't07' and mode == 'review':
                        course.write_code('resume', 'return None')
                        failure = self.cli('run', '--next-step', '--intro',
                                           'Check whether the saved code can send a decision to the workflow.')
                        self.assertEqual(failure.returncode, 0, failure.stderr)
                        failed = json.loads(failure.stdout)
                        self.assertEqual(failed['run']['status'], 'failed', failed)
                        self.assertFalse(failed['observed_result']['success'])
                        self.assertIn('resume', failed['observed_result']['error'].lower())
                        self.assertNotIn('next_step', failed)
                        self.assertEqual(course.status()['current_task'], 't07')
                    for target in course.required_code_targets(task):
                        course.write_code(target, self.solutions[target]['body'])
                    self.run_experiment(course, task)
                    self.assertTrue(self.teach_until_boundary(course, task, mode).get('preparation_complete'))
                course.mutate('explain', 'I reviewed the evidence fields and compared them with the expected result.')
                for question in task['questions']:
                    answer = question['worked_answer'] if question['type'] == 'open' else question['correct']
                    course.mutate('answer', answer, question=question['id'])
                    if question['type'] == 'open':
                        course.mutate('assess', 'The explanation addresses the task evidence.',
                                      question=question['id'], verdict='pass')
                if number in {1, 10}:
                    transition = self.cli('complete', '--next-step')
                    self.assertEqual(transition.returncode, 0, transition.stderr)
                    completed = json.loads(transition.stdout)
                    self.assertEqual(completed['closing_line'], steps_for(task, mode)[-1]['closing_line'])
                    if number == 1:
                        self.assertEqual(completed['next_step']['task'], 't02')
                        self.assertNotIn('status', completed['next_step'])
                    else:
                        self.assertEqual(completed['status']['core_percent'], 100)
                        self.assertNotIn('next_step', completed)
                else:
                    completed = course.mutate('complete')
                    self.assertEqual(completed['closing_line'], steps_for(task, mode)[-1]['closing_line'])
                course = seminar_for(self.workspace, 'week05')
                self.assertEqual(course.status()['core_percent'], sum(t['weight'] for t in course.lesson['tasks'][:number]))
        self.assertEqual(course.status()['core_percent'], 100)
        self.assertIsNone(course.status()['current_task'])
        saved_redo = course.lesson_step(step_id=f't05.{mode}_evidence')
        self.assertIs(saved_redo['read_only'], True)
        self.assertEqual(saved_redo['observed_result']['counterexamples']['spent_not_in_add']['observed_total_usd'], 180)

    def test_both_modes_run_real_experiments_and_preserve_earlier_work(self):
        try:
            import langgraph.checkpoint.sqlite
        except ModuleNotFoundError as exc:
            if exc.name not in {'langgraph', 'langgraph.checkpoint', 'langgraph.checkpoint.sqlite'}:
                raise
            self.skipTest('Use an interpreter with week05/resources/workflow/requirements.txt installed.')

        earlier = []
        for week in ('week01', 'week02', 'week03', 'week04'):
            old = seminar_for(self.workspace, week)
            old.start()
            old.mutate('save', f'My existing {week} learning note.')
            (old.resources / 'my-notes.txt').write_text(f'My earlier work for {week}.', encoding='utf-8')
            earlier.extend(path for directory in (old.base, old.resources) for path in directory.rglob('*') if path.is_file())
        previous_bytes = {path: path.read_bytes() for path in earlier}

        original = seminar_for(self.workspace, 'week05')
        original.start()
        self.complete_path(original, 'review')
        review_record = original.path.read_bytes()
        original.select_session(fresh=True)
        self.complete_path(seminar_for(self.workspace, 'week05'), 'practice')

        self.assertEqual(original.path.read_bytes(), review_record)
        self.assertEqual({path: path.read_bytes() for path in earlier}, previous_bytes)
        sessions = seminar_for(self.workspace, 'week05').sessions()['sessions']
        self.assertEqual([session['core_percent'] for session in sessions], [100, 100])


if __name__ == '__main__':
    unittest.main()
