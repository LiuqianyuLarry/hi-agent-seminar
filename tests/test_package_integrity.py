"""Distribution verification works with Git metadata but detects missing commands."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("package_check", ROOT / "verify-package.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


class PackageIntegrityTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="seminar-integrity-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "commands").mkdir()
        for name in check.COMMANDS:
            (self.root / "commands" / name).write_text("English fixture\n", encoding="utf-8")
        (self.root / ".claude-plugin").mkdir()
        (self.root / ".claude-plugin/plugin.json").write_text('{"version":"2.0.3"}', encoding="utf-8")
        inventory = {"version":"2.0.3", "files":{
            p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in check.package_files(self.root)}}
        (self.root / "SHA256SUMS.json").write_text(json.dumps(inventory), encoding="utf-8")

    def test_git_directory_does_not_break_verification(self):
        (self.root / ".git").mkdir()
        (self.root / ".git/config").write_text("Git metadata fixture")
        self.assertEqual(check.verify(self.root), [])

    def test_claude_runtime_markers_do_not_break_verification(self):
        (self.root / ".in_use").mkdir()
        (self.root / ".in_use/12345").write_text("Host runtime marker")
        self.assertEqual(check.verify(self.root), [])

    def test_worktree_git_file_does_not_break_verification(self):
        (self.root / ".git").write_text("gitdir: fixture")
        self.assertEqual(check.verify(self.root), [])

    def test_missing_command_is_reported(self):
        (self.root / "commands/menu.md").unlink()
        errors = check.verify(self.root)
        self.assertIn("Missing: commands/menu.md", errors)
        self.assertTrue(any("five commands" in e for e in errors))

    def test_changed_command_is_reported(self):
        (self.root / "commands/menu.md").write_text("Changed fixture")
        self.assertIn("Changed: commands/menu.md", check.verify(self.root))

    def test_extra_command_is_reported(self):
        (self.root / "commands/old.md").write_text("Old fixture")
        self.assertIn("Unexpected: commands/old.md", check.verify(self.root))


if __name__ == "__main__":
    unittest.main()
