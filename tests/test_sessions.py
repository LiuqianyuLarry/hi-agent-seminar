"""Independent repeat learning preserves old work and routes resumed actions."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tutor import seminar_for, catalog, compact_output


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.workspace = Path(self.tmp.name)

    def test_both_weeks_repeat_and_return_preserve_original_bytes(self):
        for week in ("week01", "week02"):
            old = seminar_for(self.workspace, week)
            old.start()
            state = old.load()
            state["tasks"][old.lesson["tasks"][0]["id"]]["complete"] = True
            old.save(state)
            before = {p:p.read_bytes() for p in old.base.rglob("*") if p.is_file()}
            student = old.resources / "student-note.txt"
            student.write_text("My old code notes")
            result = old.select_session(fresh=True)
            self.assertEqual(result["core_percent"], 0)
            replay = seminar_for(self.workspace, week)
            self.assertNotEqual(replay.session, "original")
            self.assertNotEqual(replay.resources, old.resources)
            self.assertFalse((replay.resources / student.name).exists())
            self.assertEqual(replay.load()["environment"], {})
            self.assertEqual(replay.start()["session"], replay.session)
            replay.mutate("save", "Replay pause")
            self.assertEqual(len(replay.sessions()["sessions"]), 2)
            replay.select_session("original")
            self.assertEqual(seminar_for(self.workspace, week).session, "original")
            for p, data in before.items():
                self.assertEqual(p.read_bytes(), data)
            self.assertEqual(student.read_text(), "My old code notes")

    def test_pending_experiment_blocks_restart(self):
        course = seminar_for(self.workspace)
        course.start()
        state = course.load()
        state["tasks"][course.lesson["tasks"][0]["id"]]["runs"].append({"status":"running"})
        course.save(state)
        with self.assertRaisesRegex(ValueError, "pending"):
            course.select_session(fresh=True)
        self.assertFalse(course.session_pointer.exists())

    def test_corrupt_record_blocks_restart(self):
        course = seminar_for(self.workspace)
        course.start()
        course.path.write_text("broken")
        with self.assertRaises(ValueError):
            course.select_session(fresh=True)
        self.assertEqual(course.path.read_text(), "broken")

    def test_invalid_session_does_not_change_selection(self):
        course = seminar_for(self.workspace)
        course.start()
        with self.assertRaises(ValueError):
            course.select_session("../../escape")
        self.assertFalse(course.session_pointer.exists())

    def test_catalog_does_not_compute_task_requirements(self):
        course = seminar_for(self.workspace)
        course.start()
        with patch.object(type(course), "status", side_effect=AssertionError("Expensive status")):
            self.assertEqual(catalog(self.workspace)["active_week"], "week01")

    def test_compact_status_does_not_expand_history(self):
        course = seminar_for(self.workspace)
        course.start()
        status = course.status()
        status["extensions"] = {"demo":{"runs":[{"large":"x" * 10000}] * 100,
                                         "explanations":[]}}
        result = compact_output(status)
        self.assertEqual(result["extensions"]["demo"]["run_count"], 100)
        self.assertLess(len(json.dumps(result)), 6000)
        self.assertEqual(len(status["extensions"]["demo"]["runs"]), 100)


if __name__ == "__main__":
    unittest.main()
