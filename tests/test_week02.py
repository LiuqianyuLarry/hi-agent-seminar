"""Week 2 course gates, upgrade isolation, and optional real CPU integration."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tutor import ROOT, Seminar, Week2Seminar, atomic_json, catalog, resource_files, seminar_for
from week02_fixture import METHODS


class Week2Tests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="seminar-week02-")
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.workspace = self.base / "learner"
        self.workspace.mkdir()
        self.s = Week2Seminar(self.workspace, "week02")
        self.s.start()

    def teach(self):
        for c in self.s.concepts()["concepts"]:
            self.s.concept_choice(c["id"], "understand")
        self.s.mutate("teach", "Presented the selected refresher depth, diagram, logic, mathematics and code.")

    def ready(self, python=sys.executable):
        state = self.s.load()
        state["environment"] = {"status":"ready", "python":python, "requires_api_key":False,
                                "fixture":True}
        self.s.save(state)

    def fixture_process(self, command, cwd, timeout=600):
        folder = Path(command[command.index("--output-dir")+1])
        folder.mkdir(parents=True, exist_ok=True)
        action = command[command.index("--action")+1]
        atomic_json(folder / "week02_result.json", {"status":"ok", "action":action,
                    "explicit_test_fixture":True, "api_calls":0})
        return 0, "EXPLICIT TEST FIXTURE; NOT A MEASURED DEVICE RESULT"

    def finish(self):
        self.teach()
        task = self.s.current(self.s.load())
        if task["requires_setup"]:
            self.ready()
        else:
            for module in task["code_targets"]:
                self.s.write_code(module, METHODS[module])
            self.s.mutate("predict", "Student test-fixture prediction.")
            if task["commands"]:
                with patch("week02_support.checked_process", side_effect=self.fixture_process):
                    self.s.run(None, "Explained this explicit fixture task and its purpose.")
        self.s.mutate("explain", "Explained actual fixture field names, status and limitations.")
        for q in task["questions"]:
            self.s.mutate("answer", q.get("correct", "Student test-fixture explanation"), question=q["id"])
            if q["type"] == "open":
                self.s.mutate("assess", "Assessed the test fixture", question=q["id"], verdict="pass")
        return self.s.mutate("complete")["status"]["core_percent"]

    def advance(self, task_id):
        while self.s.status()["current_task"] != task_id:
            self.finish()

    def test_course_budget_and_menu(self):
        lesson = self.s.lesson
        self.assertEqual([sum(t["minutes"] for t in lesson["tasks"] if t["session"] == x) for x in [1,2]], [50,50])
        self.assertEqual(sum(t["weight"] for t in lesson["tasks"]), 100)
        self.assertFalse(lesson["requires_api_key"])
        self.assertTrue(all(t["planned_calls"] == 0 for t in lesson["tasks"]))
        self.assertIsInstance(seminar_for(self.workspace, "week02"), Week2Seminar)
        self.assertEqual({c["id"] for c in catalog(self.workspace)["courses"]}, {"week01", "week02"})

    def test_concept_choice_precedes_teaching_and_resumes_without_progress(self):
        before = self.s.status()["core_percent"]
        with self.assertRaisesRegex(ValueError, "cards"):
            self.s.mutate("teach", "Premature explanation")
        self.s.concept_choice("parameters", "example")
        resumed = Week2Seminar(self.workspace, "week02")
        self.assertEqual(resumed.concepts()["concepts"][0]["saved_choice"]["choice"], "example")
        self.assertEqual(resumed.status()["core_percent"], before)
        resumed.concept_choice("parameters", "understand")
        resumed.mutate("teach", "Selected depth followed")
        with self.assertRaises(ValueError):
            resumed.mutate("complete")

    def test_week1_records_and_student_files_are_byte_preserved(self):
        week1 = Seminar(self.workspace)
        week1.start()
        week1.mutate("save", "Continue Week 1 later")
        prompt = week1.resources / "student" / "instructions.txt"
        prompt.write_text("Existing Week 1 student text", encoding="utf-8")
        before = {str(p):p.read_bytes() for folder in [week1.base, week1.resources] for p in folder.rglob("*") if p.is_file()}
        self.finish()
        self.s.start()
        catalog(self.workspace)
        self.assertEqual(before, {str(p):p.read_bytes() for folder in [week1.base, week1.resources] for p in folder.rglob("*") if p.is_file()})
        self.assertEqual(week1.status()["last_note"]["text"], "Continue Week 1 later")

    def test_full_core_mocked_workflow_reaches_100_and_saves_review(self):
        self.assertEqual([self.finish() for _ in self.s.lesson["tasks"]], [5,13,23,40,50,60,68,80,86,94,100])
        resumed = Week2Seminar(self.workspace, "week02")
        self.assertEqual(resumed.start()["core_percent"], 100)
        self.assertTrue(Path(resumed.export()["report"]).is_file())
        for q in ["r1", "r2", "r3"]:
            resumed.mutate("review-answer", "Typed reflection fixture", question=q)
        self.assertTrue(Path(resumed.review()["report"]).is_file())

    def test_student_code_is_saved_only_to_the_requested_method(self):
        self.advance("w204")
        self.teach()
        original = (self.s.resources / "model.py").read_text()
        self.s.write_code("head", METHODS["head"])
        state = self.s.load()
        draft = state["tasks"]["w204"]["code_drafts"]["head"][-1]
        self.assertEqual(draft["submitted_text"], METHODS["head"])
        self.assertEqual(Path(draft["backup"]).read_text(), original)
        edited = (self.s.resources / "model.py").read_text()
        self.assertNotIn("TODO W2.1", edited)
        self.assertIn("TODO W2.2", edited)
        self.assertIn("TODO W2.3", edited)
        with self.assertRaises(ValueError):
            self.s.write_code("block", METHODS["block"])
        self.assertIn("TODO W2.1", (ROOT / "week02/resources/model.py").read_text())

    def test_changed_model_requires_new_test_and_output_explanation(self):
        self.advance("w204")
        self.teach()
        self.s.write_code("head", METHODS["head"])
        self.s.mutate("predict", "It should preserve the source-axis weights")
        with patch("week02_support.checked_process", side_effect=self.fixture_process):
            self.s.run(None, "Test the head and its purpose")
        self.s.mutate("explain", "Explained fixture fields")
        self.s.mutate("answer", "C", question="mask_order")
        self.s.write_code("head", METHODS["head"] + "\n# A new student edit")
        with self.assertRaisesRegex(ValueError, "current model"):
            self.s.mutate("complete")

    def test_missing_cuda_cannot_complete_the_comparison(self):
        self.advance("w208")
        self.teach()
        self.s.mutate("predict", "GPU timing may differ")
        def unavailable(command, cwd, timeout=600):
            out = Path(command[-1])
            atomic_json(out / "week02_result.json", {"status":"awaiting_gpu", "fixture":True})
            return 3, "EXPLICIT UNAVAILABLE FIXTURE"
        with patch("week02_support.checked_process", side_effect=unavailable):
            result = self.s.run(None, "Measure device comparison")
        self.assertEqual(result["run"]["status"], "awaiting_gpu")
        self.s.mutate("explain", "The real comparison is still pending in this fixture.")
        self.s.mutate("answer", "C", question="fairness")
        with self.assertRaises(ValueError):
            self.s.mutate("complete")
        self.assertEqual(self.s.status()["core_percent"], 68)

        self.assertIn("actual CUDA", self.s.status()["next"])

    def test_visual_and_tests_are_installed_without_teacher_fixture(self):
        self.assertTrue((self.s.resources / "assets/transformer-original.png").is_file())
        self.assertTrue((self.s.resources / "transformer-map.html").is_file())
        self.assertTrue((self.s.resources / "tests/test_model.py").is_file())
        self.assertFalse((self.s.resources / "tests/week02_fixture.py").exists())
        self.assertIn("Pre-LN", str(self.s.diagram()))

    def test_existing_cuda_environment_is_not_overwritten(self):
        (self.s.resources / ".venv").mkdir()
        self.teach()
        before = self.s.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "environment already exists"):
            self.s.setup(sys.executable, install="cpu")
        self.assertEqual(self.s.path.read_bytes(), before)

    def test_optional_practice_needs_no_api_key_and_keeps_core_percentage(self):
        self.finish()
        percent = self.s.status()["core_percent"]
        entry = next(c for c in catalog(self.workspace)["courses"] if c["id"] == "week02")
        self.assertTrue(entry["optional_practice_ready"])
        with patch("week02_support.checked_process", side_effect=self.fixture_process):
            self.s.run(None, "Explain the optional context calculation", "context", "The matrix should quadruple")
        self.s.mutate("explain-extension", "Explained the calculated fixture", name="context")
        self.assertEqual(self.s.status()["core_percent"], percent)

    def test_failed_code_cannot_skip_tests_or_understanding_checks(self):
        self.advance("w204")
        self.teach()
        self.s.write_code("head", "return x")
        self.s.mutate("predict", "This wrong output should fail the test")
        def failed(command, cwd, timeout=600):
            atomic_json(Path(command[-1]) / "week02_result.json", {"status":"failed", "fixture":True})
            return 1, "EXPLICIT FAILED TEST FIXTURE"
        with patch("week02_support.checked_process", side_effect=failed):
            self.s.run(None, "Check the wrong shape")
        self.s.mutate("explain", "Explained actual fixture failure")
        with self.assertRaises(ValueError):
            self.s.mutate("complete")

    def test_week2_update_preserves_concept_choices_code_and_snapshot(self):
        self.advance("w204")
        self.teach()
        self.s.write_code("head", METHODS["head"])
        before = {str(p.relative_to(self.workspace)):p.read_bytes() for p in self.workspace.rglob("*") if p.is_file()}
        plugin = self.base / "updated-plugin"
        shutil.copytree(ROOT / "week02", plugin / "week02")
        changed = copy.deepcopy(self.s.lesson)
        changed["version"] = 999
        changed["title"] = "A future course for new students"
        atomic_json(plugin / "week02/lesson.json", changed)
        resumed = Week2Seminar(self.workspace, "week02", root=plugin)
        self.assertEqual(resumed.start()["core_percent"], 23)
        self.assertEqual(resumed.lesson["version"], 1)
        self.assertEqual(before, {str(p.relative_to(self.workspace)):p.read_bytes() for p in self.workspace.rglob("*") if p.is_file()})

    def test_optional_training_waits_for_completed_model_checks(self):
        self.finish()
        with self.assertRaisesRegex(ValueError, "full model checks"):
            self.s.run(None, "Three-repeat training fixture", "repeat3", "Times may vary")

    def test_output_reader_uses_saved_benchmark_without_rerunning(self):
        self.advance("w209")
        state_before = self.s.path.read_bytes()
        results = self.s.results()
        self.assertEqual(results["task"], "w208")
        self.assertEqual(self.s.path.read_bytes(), state_before)

    def test_setup_failures_keep_actual_receipts_and_zero_progress(self):
        self.teach()
        with patch("week02_support.checked_process", return_value=(1, "EXPLICIT MISSING DEPENDENCY FIXTURE")):
            result = self.s.setup(sys.executable)
        self.assertEqual(result["environment"]["status"], "failed")
        self.assertTrue(Path(result["environment"]["steps"][0]["log"]).is_file())
        self.assertEqual(self.s.status()["core_percent"], 0)
        with self.assertRaises(ValueError):
            self.s.mutate("complete")

    @unittest.skipUnless(os.environ.get("WEEK02_TEST_PYTHON"), "Set WEEK02_TEST_PYTHON for real local PyTorch integration")
    def test_real_cpu_starter_tests_student_code_and_training_gate(self):
        python = str(Path(os.environ["WEEK02_TEST_PYTHON"]).absolute())
        self.teach()
        result = self.s.setup(python)
        self.assertEqual(result["environment"]["status"], "ready")
        self.s.mutate("explain", "Explained actual environment and three starter tests")
        self.s.mutate("complete")
        for task_id in ["w202", "w203", "w204", "w205", "w206", "w207"]:
            self.assertEqual(self.s.status()["current_task"], task_id)
            self.teach()
            task = self.s.current(self.s.load())
            for module in task["code_targets"]:
                self.s.write_code(module, METHODS[module])
            self.s.mutate("predict", "Prediction for a real CPU validation run")
            run = self.s.run(None, "Run the actual local task and inspect its real outputs")
            self.assertEqual(run["run"]["status"], "success", run)
            summary = self.s.results()["commands"][0]["summary"]
            if task_id == "w207":
                self.assertEqual(summary["passed"], 11)
                self.assertLess(summary["small_batch_probe"]["final_loss"], summary["small_batch_probe"]["initial_loss"])
            self.s.mutate("explain", "Explained the actual local JSON, tests and shapes")
            for q in task["questions"]:
                self.s.mutate("answer", q.get("correct", "Actual integration answer fixture"), question=q["id"])
                if q["type"] == "open":
                    self.s.mutate("assess", "Integration fixture assessment", question=q["id"], verdict="pass")
            self.s.mutate("complete")
        self.assertEqual(self.s.status()["core_percent"], 68)
        self.s.run(python, "Run real controlled failures", "architecture", "The core has no encoder")
        self.assertEqual(self.s.status()["core_percent"], 68)


if __name__ == "__main__":
    unittest.main()
