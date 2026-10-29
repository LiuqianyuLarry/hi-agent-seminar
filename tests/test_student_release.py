"""The student distribution has no instructor shortcut or preview entry point."""
import json
from pathlib import Path
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
        self.assertNotIn('week03_preview',(ROOT/'tutor.py').read_text(encoding='utf-8'))
        help_result=subprocess.run([sys.executable,str(ROOT/'tutor.py'),'--help'],cwd=ROOT,
            capture_output=True,text=True,encoding='utf-8',timeout=30)
        self.assertEqual(help_result.returncode,0,help_result.stderr)
        self.assertNotRegex(help_result.stdout,r'\bpreview\b')
        self.assertIn('lesson-answer',help_result.stdout)
        self.assertIn('lesson-next',help_result.stdout)


if __name__=='__main__':unittest.main()
