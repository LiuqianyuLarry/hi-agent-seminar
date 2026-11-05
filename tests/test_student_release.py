"""The student distribution has no instructor shortcut or preview entry point."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tutor import ROOT,seminar_for


class StudentReleaseTests(unittest.TestCase):
    def test_removed_cli_mode_never_creates_or_changes_learning_records(self):
        with tempfile.TemporaryDirectory(prefix='student-only-release-') as directory:
            base=Path(directory)
            fresh=base/'fresh';fresh.mkdir()
            old=base/'returning';old.mkdir()
            for week in ('week01','week02','week03'):
                seminar_for(old,week).start()
            historical=old/'.hi-agent-seminar-preview/week03/active.json'
            historical.parent.mkdir(parents=True)
            historical.write_text(json.dumps({'cursor':5,'format_version':1})+'\n',encoding='utf-8')
            for workspace in (fresh,old):
                with self.subTest(workspace=workspace.name):
                    before={p.relative_to(workspace):p.read_bytes() for p in workspace.rglob('*') if p.is_file()}
                    run=subprocess.run([sys.executable,str(ROOT/'tutor.py'),'preview',
                        '--workspace',str(workspace),'--name','start'],cwd=ROOT,
                        capture_output=True,text=True,encoding='utf-8',timeout=30)
                    self.assertNotEqual(run.returncode,0)
                    self.assertIn('invalid choice',run.stderr)
                    after={p.relative_to(workspace):p.read_bytes() for p in workspace.rglob('*') if p.is_file()}
                    self.assertEqual(after,before)

    def test_student_entry_points_have_no_preview_implementation(self):
        self.assertFalse((ROOT/'week03_preview.py').exists())
        self.assertFalse((ROOT/'teacher_preview.py').exists())
        self.assertFalse((ROOT/'TEACHER_PREVIEW.md').exists())
        self.assertFalse((ROOT/'INSTRUCTOR_EDITION.json').exists())
        self.assertNotIn('week03_preview',(ROOT/'tutor.py').read_text(encoding='utf-8'))
        help_result=subprocess.run([sys.executable,str(ROOT/'tutor.py'),'--help'],cwd=ROOT,
            capture_output=True,text=True,encoding='utf-8',timeout=30)
        self.assertEqual(help_result.returncode,0,help_result.stderr)
        self.assertNotRegex(help_result.stdout,r'\bpreview\b')
        self.assertIn('lesson-answer',help_result.stdout)
        self.assertIn('lesson-next',help_result.stdout)

    def test_release_audit_rejects_teacher_files_state_and_command_routes(self):
        with tempfile.TemporaryDirectory(prefix='student-package-audit-') as directory:
            base=Path(directory).resolve(); package=base/'plugin'
            self.assertTrue(package.resolve().is_relative_to(base))
            shutil.copytree(ROOT,package,ignore=shutil.ignore_patterns('.git','__pycache__','.in_use'))
            inventory=(package/'SHA256SUMS.json').read_bytes()
            def audit():
                result=subprocess.run([sys.executable,'-B',str(package/'scripts/prepare-release.py'),'--check-only'],
                    cwd=package,capture_output=True,text=True,encoding='utf-8',timeout=30)
                self.assertEqual((package/'SHA256SUMS.json').read_bytes(),inventory)
                return result
            clean=audit()
            self.assertEqual(clean.returncode,0,clean.stdout+clean.stderr)
            # This Week 1 source is an ordinary course example, not a teacher shortcut.
            self.assertTrue((package/'week01/resources/preview_agent.py').is_file())
            for name,text,reason in [
                    ('teacher_preview.py','# An instructor-only helper.\n','Instructor-only preview file'),
                    ('.hi-agent-seminar-instructor/week04/preview.json','{}\n','Private/generated file')]:
                with self.subTest(file=name):
                    path=package/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
                    result=audit()
                    self.assertNotEqual(result.returncode,0)
                    self.assertIn(reason,result.stderr)
                    self.assertTrue(path.resolve().is_relative_to(package.resolve()))
                    path.unlink()
            command=package/'commands/start.md'
            command.write_text(command.read_text(encoding='utf-8')+'\nUse /hi-agent-seminar:start week04 preview.\n',encoding='utf-8')
            result=audit()
            self.assertNotEqual(result.returncode,0)
            self.assertIn('Instructor preview route in student command',result.stderr)

    def test_next_cannot_complete_or_skip_a_normal_student_task(self):
        with tempfile.TemporaryDirectory(prefix='student-next-is-not-an-answer-') as directory:
            course=seminar_for(Path(directory),'week04')
            course.start();course.study_mode('review')
            before={p.relative_to(directory):p.read_bytes() for p in Path(directory).rglob('*') if p.is_file()}
            with self.assertRaises(ValueError):
                course.mutate('complete','NEXT')
            after={p.relative_to(directory):p.read_bytes() for p in Path(directory).rglob('*') if p.is_file()}
            self.assertEqual(after,before)
            self.assertEqual(course.status()['core_percent'],0)


if __name__=='__main__':unittest.main()
