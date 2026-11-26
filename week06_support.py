"""Run the Week 6 lab in the student's own session."""
from pathlib import Path
import subprocess
import sys

from week05_support import Week5Mixin


class Week6Mixin(Week5Mixin):
    def revised_lesson(self):
        return self.lesson

    def code(self, name=None):
        from tutor import require
        from week03_flow import excerpt
        state = self.load()
        task = self.extension(name) if name else self.current(state)
        require(task, 'Choose a current task or an optional experiment.')
        return {'snippets': [excerpt(ref, self.teaching_packs()) for ref in task['code_refs']],
                'status': self.status(state)}

    def student_step_delivery(self, result, *, primary=False):
        step = result.get('step')
        if step:
            self.compact_step(step, primary)
            step['presentation'] = ('Teach the case in natural prose in the formal reply. In Review, explain the '
                'relevant slide idea directly from student_script (do not open slide PNGs unless the learner asks) '
                'before showing the matching source snippet. Use actual values for the output, ask one clear '
                'question, and show the saved percentage.')
        return result

    def revisit(self, task_id, step_id=None, code_offset=0, code_index=0):
        view = super().revisit(task_id, step_id, code_offset, code_index)
        if view.get('step', {}).get('phase') == 'after_run':
            read = self.show_lesson_step(view['step']['id'], code_offset, code_index)
            if read.get('needs_run'):
                view.pop('step')
                view.update(needs_run=True, run_hint=read['run_hint'])
            else:
                view.update(observed_result=read['observed_result'], run_id=read['run_id'])
        return view

    def setup(self, interpreter=sys.executable):
        from tutor import now, require
        python = str(Path(interpreter).resolve())
        state = self.load()
        task = self.current(state)
        require(task and state['tasks'][task['id']]['teaching'], 'Meet the task before checking your Python installation.')
        check = subprocess.run([python, '-X', 'utf8', '-c',
            "import sys, sqlite3; assert sys.version_info >= (3, 11); print(sys.version.split()[0], 'SQLite', sqlite3.sqlite_version)"],
            capture_output=True, text=True, timeout=30)
        item = {'check': 'Python and SQLite', 'returncode': check.returncode,
                'output': (check.stdout + check.stderr).strip()}
        with self.lock():
            state = self.load()
            state['environment'] = {'status': 'failed' if check.returncode else 'ready',
                                    'python': python, 'checked_at': now(), 'steps': [item], 'key_configured': False}
            self.save(state)
        return {'checks': [item], 'status': self.status()}

    def source_hashes(self):
        from tutor import fingerprint
        result = super().source_hashes()
        for pattern in ('data/documents/*.md', '*.sql'):
            result.update({p.relative_to(self.resources).as_posix(): fingerprint(p)
                           for p in sorted(self.resources.glob(pattern))})
        return result

    def experiment_arguments(self, task, folder, state, name, live, decision_file):
        from tutor import require
        require(not live and decision_file is None, 'The core experiments use local classroom data.')
        return ['optional_lab.py' if name else 'seminar_step.py', '--task', name or task['id'], '--output-dir', str(folder)]

