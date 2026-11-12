"""Week 5 local experiments and student decisions, stored in the existing v2 layout."""
import json
from pathlib import Path
import subprocess
import sys

from week04_support import Week4Mixin
from week03_flow import excerpt, public, render_step, steps_for


WORKFLOW_PREFLIGHT = """\
from importlib.metadata import version
from pathlib import Path
import sys
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph

for requirement in Path(sys.argv[1]).read_text(encoding='utf-8').splitlines():
    if requirement.strip() and not requirement.lstrip().startswith('#'):
        name, expected = requirement.strip().split('==', 1)
        actual = version(name)
        if actual != expected:
            raise SystemExit(f'{name} is {actual}; this lab uses {expected}.')
        print(f'{name} {actual}')
JsonPlusSerializer(allowed_msgpack_modules=[])
print('Workflow imports and versions passed.')
"""


class Week5Mixin(Week4Mixin):
    def lesson_step(self, name=None, code_offset=0, code_index=None, *, step_id=None):
        primary = code_index is None and code_offset == 0
        index = 0 if code_index is None else code_index
        if step_id is None:
            result = super().lesson_step(name, code_offset, index)
            self.add_current_step_context(result)
        else:
            result = self.show_lesson_step(step_id, code_offset, index)
        self.refresh_student_step(result, code_offset, index)
        return self.student_step_delivery(result, primary=primary)

    def revisit(self, task_id, step_id=None, code_offset=0, code_index=0):
        result = super().revisit(task_id, step_id, code_offset, code_index)
        self.refresh_student_step(result, code_offset, code_index)
        return self.student_step_delivery(result, primary=code_offset == 0 and code_index == 0)

    def revised_lesson(self):
        # These snapshots have the same step IDs, exercises and evidence as version 7.
        # Only replace the delivery at read time. No saved lesson or student work is written.
        if 3 <= self.lesson['version'] < 7:
            path = self.root / self.week / 'lesson.json'
            if path.is_file():
                current = json.loads(path.read_text(encoding='utf-8'))
                if current['version'] == 7:
                    return current
        return self.lesson

    def refresh_student_step(self, result, code_offset, code_index):
        shown = result.get('step')
        if not shown:
            return
        lesson = self.revised_lesson()
        if lesson is self.lesson:
            return
        for task in lesson['tasks']:
            for path in task['paths'].values():
                for step in path:
                    if step['id'] == shown['id'] and step['phase'] == shown['phase']:
                        result['step'] = render_step(step, self.teaching_packs(), code_offset, code_index=code_index)
                        return

    def mutate(self, action, text='', question=None, verdict=None, run_id=None, name=None):
        result = super().mutate(action, text, question, verdict, run_id, name)
        if action == 'complete':
            status = result['status']
            task_id = status['completed_tasks'][-1]
            task = next(task for task in self.revised_lesson()['tasks'] if task['id'] == task_id)
            steps = steps_for(task, status.get('study_mode'))
            if steps and steps[-1].get('closing_line'):
                result['closing_line'] = steps[-1]['closing_line']
        return result

    def add_current_step_context(self, result):
        task_id = result.get('status', {}).get('current_task')
        task = next((item for item in self.lesson['tasks'] if item['id'] == task_id), None)
        if not task:
            return
        if result.get('preparation_complete'):
            result['task_question'] = public(task['questions'][0])
            return
        if result.get('needs_run'):
            result['code_targets'] = self.required_code_targets(task)
        elif result.get('step', {}).get('phase') != 'before_run':
            return
        if result.get('step_id', '').endswith('_overview') or not task.get('concepts'):
            return
        choices = self.load().get('concept_choices', {})
        foundations = [self.lesson['foundations'][key] for key in task['concepts'] if key not in choices]
        if foundations:
            result['foundation_options'] = {'concepts': foundations, 'choices': ['understand', 'brief', 'example']}

    def compact_step(self, step, primary):
        refs = step.pop('code_refs', [])
        shown = step['snippets']
        indices = [step['code_index']] if shown else []
        preferred = step.pop('primary_code_indices', None)
        if primary and refs and preferred:
            indices = preferred
            already_rendered = shown[0]
            packs = self.teaching_packs()
            shown = [already_rendered if index == step['code_index'] else excerpt(refs[index], packs)
                     for index in indices]
            step['snippets'] = shown
            step['code_index'] = indices[0]
        for source in step['code_sources']:
            source['shown'] = source['index'] in indices
        for index, snippet in zip(indices, shown):
            snippet['index'] = index
            if refs[index].get('note'):
                snippet['note'] = refs[index]['note']
        for key in ('code_notes', 'rules', 'mechanism'):
            step.pop(key, None)
        if 'student_script' not in step:
            return
        script = step['student_script']
        if step.get('logic') in script:
            step.pop('logic')
        joined = '\n\n'.join(script)
        if step.get('explanation') == joined:
            step.pop('explanation')
        slide = step.get('slide_review', {})
        if slide.get('explanation') == joined:
            slide.pop('explanation')
        if slide.get('focus') in script:
            slide.pop('focus')
        if any(snippet.get('note') == slide.get('code_bridge') for snippet in shown):
            slide.pop('code_bridge', None)
        opening = step.get('instructor_opening', []) + step.get('opening_story', [])
        if opening and script[:len(opening)] == opening:
            step['student_script'] = script[len(opening):]

    def student_step_delivery(self, result, *, primary=False):
        step = result.get('step')
        if step:
            self.compact_step(step, primary)
        if step and self.lesson['version'] >= 2:
            if step['id'].endswith('_two_ledgers') and step.get('code_walkthrough'):
                step['presentation'] = (
                    'In the formal reply, copy the two required_student_text lines verbatim first. Then deliver the remaining '
                    'student_script in order: the $960 crash, the two records, both outcomes at the counter, and the '
                    'four numbered operations. Keep those parts distinct. A slide may support the example after the '
                    'counter story. Show the supplied World.act source after the four operations and explain each '
                    'item in code_walkthrough in order. Finish with the single next action and saved progress.'
                )
                return result
            if step.get('opening_story'):
                step['presentation'] = (
                    'Open the formal reply with instructor_opening verbatim as a note from the instructor. '
                    'Then deliver opening_story verbatim and in order, with no heading or question in between. '
                    'After the story, teach every role in the remaining student_script in order using the booking example. '
                    'Show the map after the explanation. End with the single checkpoint question and the saved progress.'
                )
                return result
            opening = 'In the formal reply, explain student_script in words that stand on their own. '
            if step.get('instructor_opening'):
                opening = ('Open the formal reply with instructor_opening verbatim as a note from the instructor. '
                           'Then teach the remaining student_script in words that stand on their own. ')
            step['presentation'] = (
                opening + 'Teach every student_script paragraph in order before showing the supplied source. Keep the '
                'example, analogy, mechanism and any failure case together; do not reduce them to a definition. '
                'In Review, show or link the supplied slide and explain its main idea in words. Include actual observations for an evidence step. '
                'Copy required_student_text verbatim when present, with each line in its own paragraph. '
                'Then give one next action and the saved progress.'
            )
        return result

    def setup(self, interpreter=sys.executable):
        from tutor import now, redact, require

        python = str(Path(interpreter).expanduser().resolve())
        require(Path(python).is_file(), 'Choose an existing Python interpreter.')
        state = self.load()
        task = self.current(state)
        require(task and state['tasks'][task['id']]['teaching'],
                'Explain the current task before checking the environment.')
        checks = []
        for label, code, arguments in (
            ('Python', "import sys; assert sys.version_info >= (3,11), 'Python 3.11 or newer is required.'; print(sys.version.split()[0])", []),
            ('LangGraph and SQLite checkpointer', WORKFLOW_PREFLIGHT, [str(self.resources / 'workflow/requirements.txt')]),
        ):
            try:
                result = subprocess.run([python, '-X', 'utf8', '-c', code, *arguments],
                                        capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)
                checks.append({'check': label, 'returncode': result.returncode,
                               'output': redact(result.stdout + result.stderr)})
            except (OSError, subprocess.TimeoutExpired) as exc:
                checks.append({'check': label, 'returncode': 1, 'output': redact(str(exc))})
            if label == 'Python' and checks[-1]['returncode']:
                break
        workflow_ready = len(checks) == 2 and checks[1]['returncode'] == 0
        with self.lock():
            state = self.load()
            state['environment'] = {
                'status': 'ready' if checks[0]['returncode'] == 0 else 'failed',
                'workflow_ready': workflow_ready, 'python': python, 'checked_at': now(),
                'steps': checks, 'key_configured': False,
                'note': ('Python and the workflow dependencies are ready.' if workflow_ready else
                         'The simulations use Python alone. Install workflow/requirements.txt in an isolated environment before the workflow exercises, then check setup again.'),
            }
            self.save(state)
        return {'checks': checks, 'status': self.status()}

    def results(self, name=None, task_id=None):
        if task_id is None:
            return super().results(name)
        from tutor import require

        state = self.load()
        require(name is None and task_id in state['tasks'], 'Choose a saved Week 5 core task.')
        runs = state['tasks'][task_id]['runs']
        require(runs and runs[-1]['status'] == 'success', 'No successful experiment is saved for this task.')
        run = runs[-1]
        return {'run': run, 'observed_result': self.read_result(run), 'status': self.status(state)}

    @staticmethod
    def checked_decision(value, approved, pending):
        from tutor import clean_text, require

        require(isinstance(value, dict) and set(value) == {'approved', 'action_id', 'payload_hash', 'reviewer'},
                'Include approved, action_id, payload_hash and reviewer for each decision.')
        require(value['approved'] is approved, 'Record the learner decision as the requested JSON Boolean.')
        for key in ('action_id', 'payload_hash'):
            require(value[key] == pending[key], 'Use the action ID and hash from the actual waiting task.')
        reviewer = value['reviewer']
        require(isinstance(reviewer, str) and 0 < len(reviewer.strip()) <= 80,
                'Enter a short reviewer name.')
        clean_text(reviewer)

    def experiment_arguments(self, task, folder, state, name, live, decision_file):
        from tutor import child, require

        require(not live, 'Week 5 uses local experiments.')
        task_id = task['id']
        if task_id in {'t03', 't04', 't06', 't07', 't08', 't09'}:
            require(state['environment'].get('workflow_ready'),
                    'Check setup with an interpreter that has workflow/requirements.txt installed.')
        args = ['seminar_step.py', '--task', task_id, '--output-dir', str(folder)]
        if task_id not in {'t08', 't09'}:
            require(decision_file is None, 'Approval files belong to the decision and recovery tasks.')
            return args
        require(decision_file is not None, 'Ask the learner for the decision and save it in a JSON file first.')
        path = Path(decision_file).resolve()
        require(path.suffix.lower() == '.json' and path.is_relative_to(self.workspace) and
                path.is_file() and path.stat().st_size <= 8192,
                'Use a JSON decision file under this learning workspace (up to 8 KiB).')
        decision = json.loads(path.read_text(encoding='utf-8-sig'))
        preparation = state['tasks']['t07']
        require(self.usable_run(preparation),
                'The saved waiting tasks require the same source as the successful t07 run. Restore that source or use a new learning session.')
        previous = preparation['runs'][-1]
        pending = self.read_result(previous)['decision_requests']
        if task_id == 't08':
            require(isinstance(decision, dict) and set(decision) == {'approve', 'reject'},
                    'Provide an approve object and a reject object for the two waiting tasks.')
            self.checked_decision(decision['approve'], True, pending['week05-approve'])
            self.checked_decision(decision['reject'], False, pending['week05-reject'])
        else:
            self.checked_decision(decision, True, pending['week05-recovery'])
        source = child(self.base, 'runs', previous['id'], 'workflow')
        return args + ['--prepared-workspace', str(source), '--decision-json', json.dumps(decision, ensure_ascii=True)]
