"""Week 4 teaching, bounded experiments and saved learner work.

The shared v2 storage format is unchanged. New fields belong only to Week 4.
"""
import ast
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import textwrap
import uuid

from week03_support import Week3Mixin
from week03_flow import public, steps_for, render_step


class Week4Mixin(Week3Mixin):
    @staticmethod
    def required_code_targets(task):
        # Read the saved task, so older lesson snapshots keep their own requirements.
        return list(task.get('required_code_targets',
                             [task['code_target']] if task.get('code_target') else []))

    def pending_code_targets(self, task, record):
        saved = {draft.get('target') for draft in record.get('code_drafts', [])}
        return [name for name in self.required_code_targets(task) if name not in saved]

    def source_hashes(self):
        from tutor import fingerprint
        ignored = {'.venv', '__pycache__', 'outputs', '.git'}
        return {p.relative_to(self.resources).as_posix(): fingerprint(p)
                for p in sorted(self.resources.rglob('*'))
                if p.is_file() and not p.is_symlink() and p.suffix in {'.py', '.csv', '.json'}
                and not ignored.intersection(p.relative_to(self.resources).parts)}

    def preserve_course(self):
        from tutor import Seminar
        Seminar.preserve_course(self)
        for name, saved in [('instructor/solutions.json', 'solutions.snapshot.json'),
                            ('PRESENTATION.md', 'PRESENTATION.snapshot.md')]:
            source = self.root / self.week / name
            target = self.base / saved
            if not target.exists() and source.is_file():
                target.write_bytes(source.read_bytes())
        for name, saved in [('lecture_demo', 'lecture.snapshot'),
                            ('slides', 'slides.snapshot'),
                            ('teacher-data', 'teacher-data.snapshot')]:
            source = self.root / self.week / name
            target = self.base / saved
            if not target.exists() and source.is_dir():
                shutil.copytree(source, target, ignore=shutil.ignore_patterns(
                    '__pycache__', '.env', '.venv', 'outputs', '*.pyc'))

    def before_steps(self, task, record, mode):
        return [s for s in self.pending_steps(task, record, mode)
                if s.get('phase', 'before_run') == 'before_run']

    def usable_run(self, record):
        return bool(record.get('runs') and record['runs'][-1]['status'] == 'success'
                    and record['runs'][-1].get('source_hashes') == self.source_hashes())

    @staticmethod
    def require_own_words(record):
        from tutor import require
        pending = [name for name, support in record.get('support', {}).items()
                   if support.get('answer_explained') and not support.get('passed')]
        require(not pending, 'Check the learner\'s own explanation before continuing: ' + ', '.join(pending))

    def missing(self, task, record):
        result = super().missing(task, record)
        result.extend('save the learner code for ' + name
                      for name in self.pending_code_targets(task, record))
        for target, support in record.get('support', {}).items():
            if support.get('answer_explained') and not support.get('passed'):
                result.append('explain ' + target + ' in your own words and check understanding')
        return result

    def task(self):
        value = super().task()
        value.pop('mcp_guide', None)
        if 'task' in value:
            value['task'] = public(value['task'])
            value['task'].pop('code_walkthrough', None)
            value['task']['next_instruction'] = 'Use lesson-step. Teach the current part before asking the learner to work on it.'
            state = self.load()
            task = self.current(state)
            if task:
                value['pending_code_targets'] = self.pending_code_targets(task, state['tasks'][task['id']])
        return value

    def lesson_step(self, name=None, code_offset=0, code_index=0):
        from tutor import require
        state = self.load(); task = self.current(state); mode = state.get('study_mode')
        require(task and mode in {'review', 'practice'}, 'Choose a task and learning mode first.')
        record = state['tasks'][task['id']]
        steps = steps_for(task, mode)
        pending = self.pending_steps(task, record, mode)
        step = next((s for s in steps if s['id'] == name), None) if name else next(iter(pending), None)
        if step is None:
            require(name is None, 'Choose a listed lesson step.')
            return {'preparation_complete': True, 'status': self.status(),
                    'next': 'Check the actual result, answer the task question, then complete this task.'}
        if step.get('phase') == 'after_run' and not self.usable_run(record):
            return {'needs_run': True, 'step_id': step['id'], 'title': step['title'],
                    'phase': 'after_run', 'task': task['id'], 'status': self.status(),
                    'run_hint': 'Save the learner prediction and any required code. Run this task and inspect its result before teaching this part.'}
        result = super().lesson_step(name, code_offset, code_index)
        if step.get('phase') == 'after_run':
            result['observed_result'] = self.read_result(record['runs'][-1])
            result['run_id'] = record['runs'][-1]['id']
        return result

    def require_current_phase(self, name):
        from tutor import require
        state = self.load(); task = self.current(state)
        require(task, 'Choose a current task.')
        record = state['tasks'][task['id']]
        pending = self.pending_steps(task, record, state.get('study_mode'))
        require(pending and pending[0]['id'] == name, 'Use the current lesson step.')
        if pending[0].get('phase') == 'after_run':
            require(self.usable_run(record), 'Run the task successfully with the current code before discussing its observed result.')
        return pending[0]

    def lesson_next(self, name, text):
        state = self.load(); task = self.current(state)
        if task:
            done = state['tasks'][task['id']].get('path_teaching', {}).get(state.get('study_mode'), [])
            if any(item['id'] == name for item in done):
                return {'duplicate_ignored': True, 'status': self.status(state)}
            self.require_own_words(state['tasks'][task['id']])
        self.require_current_phase(name)
        return super().lesson_next(name, text)

    def lesson_answer(self, name, text):
        return self.checkpoint('answer', name, text)

    def lesson_hint(self, name, text):
        return self.checkpoint('hint', name, text)

    def lesson_solution(self, name, text):
        return self.checkpoint('solution', name, text)

    def lesson_assess(self, name, text, verdict):
        return self.checkpoint('assess', name, text, verdict)

    @staticmethod
    def support_action(saved, action, text, info, verdict=None):
        from tutor import require, now
        require(text.strip().upper() != 'SHOWCASE', 'There is no answer shortcut. Try the question or ask for help.')
        if action in {'attempt', 'answer'}:
            if saved.get('answer_explained'):
                require(len(text.split()) >= 4 and text.strip().upper() not in info.get('options', {}),
                        'Explain the idea in a short sentence of your own.')
                saved['own_words'].append({'at': now(), 'text': text})
                saved['passed'] = False; saved.pop('assessment', None)
                return {'passed': False, 'needs_assessment': True, 'next': 'Read this explanation and check what the learner understands.'}
            passed = bool(info.get('correct') and text.strip().upper() == info['correct'])
            saved['attempts'].append({'at': now(), 'text': text, 'passed': passed})
            saved['passed'] = passed
            return {'passed': passed, 'feedback': info.get('explanation', '') if passed else
                    'Not yet. Try explaining what you know so far, or ask for a hint.'}
        if action == 'hint':
            require(not saved['passed'], 'This check has passed. Continue, or ask a clarification question.')
            if saved['hints']:
                require(len(saved['attempts']) > saved['hints'][-1]['attempt_count'],
                        'Let the learner try after the previous hint before giving another.')
            count = len(saved['hints'])
            hint = info.get('hint' + str(count + 1)) if count < 2 else None
            hint = hint or 'Use one example from the task. Say what goes in, what changes, and what comes out. We can work through that part together.'
            saved['hints'].append({'at': now(), 'request': text, 'text': hint,
                                   'attempt_count': len(saved['attempts'])})
            result = {'hint_number': count + 1, 'hint': hint, 'passed': False,
                      'next': 'Wait for the learner to try. A reply saying they are still unsure is also an attempt.'}
            if count >= 1:
                result['next'] += ' If they are still stuck, offer more hints or an answer explanation.'
            return result
        if action == 'solution':
            require(not saved.get('answer_explained'), 'The answer was already explained. Work with the learner\'s own explanation now.')
            require(len(saved['hints']) >= 2, 'Give two gradual hints with learner attempts first.')
            require(len(saved['attempts']) > saved['hints'][-1]['attempt_count'],
                    'Wait for the learner response after the second hint before offering an answer explanation.')
            require(not saved['passed'], 'The learner already passed this check.')
            saved['answer_explained'] = {'at': now(), 'learner_request': text}
            saved['passed'] = False; saved['own_words'] = []; saved.pop('assessment', None)
            return {'passed': False, 'explanation': info.get('explanation', info.get('worked_answer', '')),
                    'worked_answer': info.get('worked_answer'), 'correct': info.get('correct'),
                    'next': 'Explain this answer in a formal reply. Then ask for the learner\'s explanation in their own words; do not advance yet.'}
        if action == 'assess':
            require(verdict in {'pass', 'retry'}, 'Choose pass or retry.')
            require(saved.get('answer_explained') and saved['own_words'], 'Save the learner\'s own explanation before assessing it.')
            index = len(saved['own_words']) - 1
            require(saved.get('assessment', {}).get('response_index') != index,
                    'This response was already assessed. Wait for a new learner response.')
            saved['assessment'] = {'at': now(), 'response_index': index, 'verdict': verdict, 'feedback': text}
            saved['passed'] = verdict == 'pass'
            return {'passed': saved['passed'], 'feedback': text}
        raise ValueError('Unknown support action.')

    def checkpoint(self, action, name, text, verdict=None):
        from tutor import clean_text
        from week03_checks import current_check
        text = clean_text(text)
        self.require_current_phase(name)
        with self.lock():
            state = self.load(); check, saved = current_check(self, state, name)
            result = self.support_action(saved, action, text, check, verdict)
            self.save(state)
        return {**result, 'step_id': name, 'progress_unchanged': True, 'status': self.status()}

    def support(self, action, name, text, verdict=None):
        from tutor import require, clean_text
        text = clean_text(text)
        with self.lock():
            state = self.load(); task = self.current(state)
            require(task, 'Select a current task.')
            record = state['tasks'][task['id']]
            require(record['teaching'] and not self.before_steps(task, record, state.get('study_mode')),
                    'Teach the preparation steps before working on the exercise.')
            if name and name.startswith('code:'):
                target = name.split(':', 1)[1]
                require(target in self.required_code_targets(task), 'Choose a code exercise required by the current saved task.')
                info = dict(self.lesson.get('code_support', {}).get(target, {}))
                if action == 'solution':
                    solutions = json.loads((self.base / 'solutions.snapshot.json').read_text(encoding='utf-8'))
                    solution = solutions[target]
                    info['worked_answer'] = solution.get('body', solution.get('code')) if isinstance(solution, dict) else solution
            else:
                require(name and name.startswith('question:'), 'Choose code:TARGET or question:ID.')
                info = dict(self.question(task, name.split(':', 1)[1]))
                require(record['explanations'], 'Explain the result before checking this question.')
            saved = record.setdefault('support', {}).setdefault(name,
                    {'attempts': [], 'hints': [], 'own_words': [], 'passed': False})
            result = self.support_action(saved, action, text, info, verdict)
            self.save(state)
        return {**result, 'target': name, 'progress_unchanged': True, 'status': self.status()}

    def setup(self, interpreter=sys.executable):
        from tutor import require, redact, now
        interpreter = str(Path(interpreter).expanduser().absolute())
        require(Path(interpreter).is_file(), 'Choose an existing Python interpreter.')
        state = self.load(); task = self.current(state)
        require(task and state['tasks'][task['id']]['teaching'], 'Explain the current task before checking the environment.')
        check = "import sys,importlib.metadata as m; assert sys.version_info >= (3,11); import pydantic,pytest; assert int(m.version('pydantic').split('.')[0])>=2; print('Python, Pydantic and pytest are ready. The optional live client is checked only when needed.')"
        logs = []
        for args in (['-c', check], ['build_data.py'], ['preflight.py']):
            try:
                result = subprocess.run([interpreter, '-X', 'utf8', *args], cwd=self.resources,
                    capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
                logs.append({'arguments': args, 'returncode': result.returncode, 'output': redact(result.stdout + result.stderr)})
            except (subprocess.TimeoutExpired, OSError) as exc:
                logs.append({'arguments': args, 'returncode': 124, 'output': redact(str(exc))})
            if logs[-1]['returncode']:
                break
        with self.lock():
            state = self.load()
            state['environment'] = {'status': 'ready' if all(x['returncode'] == 0 for x in logs) else 'failed',
                'python': interpreter, 'checked_at': now(), 'steps': logs, 'key_configured': False,
                'note': 'Existing environment checked. No installation, GPU or API key is required for core practice.'}
            self.save(state)
        return {'status': self.status(), 'checks': logs}

    def write_code(self, name, text):
        from tutor import require, clean_text, child, now, fingerprint
        original = clean_text(text); body = textwrap.dedent(original).strip()
        require(not any('\u3400' <= c <= '\u9fff' for c in body), 'Write the code and comments in English.')
        ast.parse('def exercise():\n' + textwrap.indent(body, '    '))
        with self.lock():
            state = self.load(); task = self.current(state)
            require(task and name in self.required_code_targets(task), 'Choose a code target required by the current saved task.')
            record = state['tasks'][task['id']]
            require(record['teaching'] and not self.before_steps(task, record, state.get('study_mode')),
                    'Teach the selected path before the code attempt.')
            require(not any(r['status'] == 'running' for r in record['runs']), 'Wait for the running experiment.')
            filename, symbol = self.lesson['code_targets'][name]
            path = child(self.resources, filename); source = path.read_text(encoding='utf-8')
            nodes = ast.parse(source).body
            for part in symbol.split('.'):
                node = next((n for n in nodes if getattr(n, 'name', None) == part), None)
                require(node is not None, 'Exercise function was not found. Preserve the code and inspect it.')
                nodes = getattr(node, 'body', [])
            require(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)), 'The code target must be a function.')
            first = node.body[1] if ast.get_docstring(node) and len(node.body) > 1 else node.body[0]
            lines = source.splitlines(keepends=True)
            new = ''.join(lines[:first.lineno-1]) + textwrap.indent(body, ' ' * (node.col_offset + 4)) + '\n' + ''.join(lines[node.end_lineno:])
            ast.parse(new)
            backup = child(self.base, 'code-history', uuid.uuid4().hex + '.txt'); backup.parent.mkdir(exist_ok=True)
            backup.write_bytes(path.read_bytes()); path.write_text(new, encoding='utf-8', newline='\n')
            record.setdefault('code_drafts', []).append({'at': now(), 'target': name, 'student_text': original,
                'sha256': fingerprint(path), 'previous': str(backup)})
            support = record.get('support', {}).get('code:' + name)
            if support is not None and not support.get('answer_explained'):
                support['attempts'].append({'at': now(), 'text': original, 'kind': 'code'})
            self.save(state)
        return {'saved': str(path), 'status': self.status()}

    def read_result(self, run):
        from tutor import child, require
        folder = child(self.base, 'runs', run['id'])
        path = folder / 'lesson_result.json'
        require(path.is_file(), 'The experiment result is missing. Inspect the saved run; do not invent its output.')
        return json.loads(path.read_text(encoding='utf-8'))

    def run(self, interpreter, intro, name=None, prediction=None, live=False):
        from tutor import require, clean_text, now, child, atomic_json, redact
        intro = clean_text(intro)
        with self.lock():
            state = self.load(); env = state['environment']
            require(env.get('status') == 'ready', 'Check the existing Python environment first.')
            python = interpreter or env['python']
            require(Path(python).resolve() == Path(env['python']).resolve(), 'Use the verified Python interpreter.')
            active = self.current(state)
            if active:
                self.require_own_words(state['tasks'][active['id']])
            task = self.extension(name) if name else self.current(state)
            require(task and task['commands'], 'This step is a discussion; it has no experiment to run.')
            record = state['extensions'].setdefault(name, {'runs': [], 'explanations': []}) if name else state['tasks'][task['id']]
            if name:
                clean_text(prediction or '')
            else:
                require(record['teaching'] and record['predictions'], 'Teach the task and record the learner prediction before running.')
                require(not self.before_steps(task, record, state.get('study_mode')), 'Finish the before_run teaching steps first.')
                pending_code = self.pending_code_targets(task, record)
                require(not pending_code, 'Save the learner code before testing: ' + ', '.join(pending_code))
                for concept in task.get('concepts', []):
                    require(concept in state.get('concept_choices', {}), 'Offer the foundation choice before running: ' + concept)
            require(not any(r['status'] == 'running' for item in [*state['tasks'].values(), *state['extensions'].values()] for r in item['runs']),
                    'A run is still pending. Inspect it before starting another.')
            is_live = bool(live or task.get('planned_calls', 0))
            require(not live or (not name and task['id'] == 't02'), 'The live switch is available only for the single-round experiment.')
            if is_live:
                require('approv' in intro.lower() or 'consent' in intro.lower(), 'Record the learner approval for this live API call in the introduction.')
            run_id = uuid.uuid4().hex; folder = child(self.base, 'runs', run_id); folder.mkdir(parents=True)
            run = {'id': run_id, 'task': task['id'], 'status': 'running', 'started_at': now(), 'intro': intro,
                'prediction': prediction if name else copy.deepcopy(record['predictions'][-1]),
                'planned_calls': 1 if live else task.get('planned_calls', 0), 'folder': str(folder),
                'commands': [], 'source_hashes': self.source_hashes()}
            if not name and record['runs']:
                archive = {'run_id': record['runs'][-1]['id'], 'path_teaching': {}, 'path_checks': {}}
                for mode in ('review', 'practice'):
                    after = {s['id'] for s in steps_for(task, mode) if s.get('phase') == 'after_run'}
                    taught = record.get('path_teaching', {}).get(mode, [])
                    checks = record.get('path_checks', {}).get(mode, {})
                    archive['path_teaching'][mode] = [s for s in taught if s['id'] in after]
                    archive['path_checks'][mode] = {k: v for k, v in checks.items() if k in after}
                    if mode in record.get('path_teaching', {}):
                        record['path_teaching'][mode] = [s for s in taught if s['id'] not in after]
                    if mode in record.get('path_checks', {}):
                        record['path_checks'][mode] = {k: v for k, v in checks.items() if k not in after}
                record.setdefault('path_run_history', []).append(archive)
            record['runs'].append(run); self.save(state)
        args = list(task['commands'][0]) if name else ['seminar_step.py', '--task', task['id']]
        args += ['--output-dir', str(folder), '--reference-dir', str(self.base / 'lecture.snapshot')]
        if not name and task['id'] == 't02':
            args += ['--mode', 'live' if live else 'teacher', '--teacher-record', str(self.base / 'teacher-data.snapshot' / 'single_round.json')]
        try:
            result = subprocess.run([python, '-X', 'utf8', *args], cwd=self.resources, capture_output=True,
                text=True, encoding='utf-8', errors='replace', timeout=240)
            output = redact(result.stdout + result.stderr); code = result.returncode
        except subprocess.TimeoutExpired:
            output = 'The experiment timed out. Inspect the saved files before trying again.'; code = 124
        except OSError as exc:
            output = redact(str(exc)); code = 1
        path = folder / 'lesson_result.json'
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            valid = isinstance(data, dict) and data.get('success') is True
            if valid and not name and task['id'] == 't02':
                valid = data.get('evidence_kind') == ('live_deepseek' if live else 'recorded_live')
        except (OSError, ValueError):
            data = None; valid = False
        log = folder / 'stdout.txt'; log.write_text(output, encoding='utf-8')
        artifacts = [str(p) for p in folder.rglob('*') if p.is_file() and p.suffix in {'.json', '.csv', '.md', '.html'}]
        run.update(status='success' if code == 0 and valid else 'failed', finished_at=now(),
            evidence_kind=data.get('evidence_kind') if isinstance(data, dict) else None,
            commands=[{'arguments': args, 'returncode': code, 'stdout': str(log), 'artifacts': artifacts}])
        atomic_json(folder / 'receipt.json', run)
        with self.lock():
            state = self.load(); record = state['extensions'][name] if name else state['tasks'][task['id']]
            saved = next(r for r in record['runs'] if r['id'] == run_id)
            require(saved['status'] == 'running', 'This run was recovered separately. Inspect its receipt before continuing.')
            saved.update(run)
            if is_live and run['status'] == 'success':
                state['environment']['key_configured'] = True
            self.save(state)
        return {'run': run, 'observed_result': data, 'status': self.status(),
                'next': 'Read the actual result. Use lesson-step for its explanation and next question, then save the explanation at the next learner reply.'}

    def results(self, name=None):
        result = super().results(name)
        if (Path(result['run']['folder']) / 'lesson_result.json').is_file():
            result['observed_result'] = self.read_result(result['run'])
        return result

    def mutate(self, action, text='', question=None, verdict=None, run_id=None, name=None):
        from tutor import require
        if action in {'answer', 'assess', 'complete'}:
            state = self.load(); task = self.current(state)
            if task:
                record = state['tasks'][task['id']]
                require(not self.pending_steps(task, record, state.get('study_mode')),
                        'Finish the current before_run and after_run teaching steps first.')
        return super().mutate(action, text, question, verdict, run_id, name)
