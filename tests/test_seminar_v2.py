"""Meaningful v2 workflow regressions. All installations and API calls are mocked."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tutor import ROOT, Seminar, REVIEW_QUESTIONS, atomic_json, catalog, resource_files


class SeminarV2Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="seminar-v2-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.plugin = self.base / "plugin"
        self.workspace = self.base / "student"
        self.workspace.mkdir()
        self.lesson = json.loads((ROOT / "week01" / "lesson.json").read_text(encoding="utf-8"))
        atomic_json(self.plugin / "week01" / "lesson.json", self.lesson)
        assets = ROOT / "week01" / "resources"
        for path in resource_files(assets):
            target = self.plugin / "week01" / "resources" / path.relative_to(assets)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        self.s = Seminar(self.workspace, root=self.plugin)
        self.s.start()

    def mock_process(self, command, **kwargs):
        if "venv" in command:
            venv = Path(command[-1])
            python = venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
            python.parent.mkdir(parents=True, exist_ok=True)
            python.write_text("TEST ONLY. No executable code.", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "Venv test fixture", "")
        if "--output-dir" not in command:
            return subprocess.CompletedProcess(command, 0, "Imports OK\nTEST ONLY", "")
        out = Path(command[command.index("--output-dir")+1])
        mode = command[command.index("--demo")+1] if "--demo" in command else "agent"
        if mode == "prompt":
            atomic_json(out / "prompt_fixture.json", {"runs":[
                {"label":"original", "metadata":{"usage":{"prompt_tokens":100,"completion_tokens":20,"total_tokens":120},"elapsed_seconds":0.1}},
                {"label":"changed", "metadata":{"usage":{"prompt_tokens":120,"completion_tokens":50,"total_tokens":170},"elapsed_seconds":0.2}}]})
        elif mode == "validation":
            atomic_json(out / "validation_fixture.json", {"checks":{
                "actual_baseline":{"valid_format":True,"evidence_check_passed":True},
                "unsupported_claim":{"valid_format":True,"evidence_check_passed":False}}})
        elif mode == "seminar":
            case = command[command.index("--case")+1]
            unknown = ["cause"] if case == "complete" else ["cause", "alarm record"]
            atomic_json(out / "seminar_case_fixture.json", {"case":case,"displayed_output":json.dumps({"missing_information":unknown,"diagnosis":None}),
                        "origin":"actual_model_response","checks":{"valid_format":True,"evidence_check_passed":True}})
        else:
            atomic_json(out / (mode + "_fixture.json"), {"test_only":True})
        return subprocess.CompletedProcess(command, 0, "EXPLICIT TEST FIXTURE OUTPUT", "")

    def teach(self):
        self.s.mutate("teach", "Explained task purpose, terms and numbered code before questioning.")

    def prepare_setup(self):
        self.teach()
        with patch("tutor.subprocess.run", side_effect=self.mock_process) as mock:
            result = self.s.setup(sys.executable)
        self.assertEqual(result["environment"]["status"], "ready")
        (self.s.resources / ".env").write_text("TEST ONLY", encoding="utf-8")
        self.s.mutate("key-ready", "Student confirmed private setup is done.")
        return mock

    def prepare_task(self):
        task = self.s.current(self.s.load())
        if task.get("requires_setup"):
            self.prepare_setup()
        else:
            self.teach()
            if task.get("requires_prompt"):
                self.s.write_prompt("Use only the supplied log. Return two known facts and one item to confirm. Do not invent a cause.")
            self.s.mutate("predict", "Student prediction based on the explained code.")
            if task["commands"]:
                with patch("tutor.subprocess.run", side_effect=self.mock_process):
                    self.s.run(None, "Task and purpose explained before the fixture run.")
        self.s.mutate("explain", "Explained actual fixture output fields and limitations.")

    def answer_all(self):
        for q in self.s.current(self.s.load())["questions"]:
            self.s.mutate("answer", q.get("correct", "Student fixture explanation"), question=q["id"])
            if q["type"] == "open":
                self.s.mutate("assess", "Fixture rubric assessment", question=q["id"], verdict="pass")

    def finish(self):
        self.prepare_task()
        self.answer_all()
        self.s.mutate("complete")

    def advance(self, target):
        while self.s.status()["current_task"] != target:
            self.finish()

    def test_fresh_edition_ignores_legacy_records(self):
        atomic_json(self.workspace / ".hi-agent-seminar" / "week01" / "progress.json", {"old_complete":True})
        self.assertEqual(self.s.start()["core_percent"], 0)
        self.assertIn("v2", self.s.path.parts)

    def test_empty_leftover_directories_do_not_block_start(self):
        other = self.base / "empty-workspace"
        (other / "hi-agent-seminar-work" / "v2" / "week01" / "resources" / "student").mkdir(parents=True)
        s = Seminar(other, root=self.plugin)
        self.assertEqual(s.start()["core_percent"], 0)
        self.assertTrue((s.resources / "week1_demo.py").is_file())

    def test_nonempty_orphan_is_not_overwritten(self):
        other = self.base / "orphan"
        existing = other / "hi-agent-seminar-work" / "v2" / "week01" / "resources"
        existing.mkdir(parents=True)
        (existing / "work.txt").write_text("Student work")
        with self.assertRaisesRegex(ValueError, "not overwritten"):
            Seminar(other, root=self.plugin).start()
        self.assertEqual((existing / "work.txt").read_text(), "Student work")

    def test_setup_has_no_prediction_or_quiz(self):
        task = self.s.task()["task"]
        self.assertEqual(task["questions"], [])
        self.assertIsNone(task["prediction"])
        with self.assertRaisesRegex(ValueError, "no prediction"):
            self.s.mutate("predict", "Unneeded response")
        mock = self.prepare_setup()
        command = mock.call_args_list[1].args[0]
        self.assertIn(".venv", command[0])
        self.assertEqual(command[1:4], ["-m", "pip", "install"])
        self.s.mutate("explain", "Venv installation and imports succeeded. Key remains local.")
        self.s.mutate("complete")
        self.assertEqual(self.s.status()["core_percent"], 8)

    def test_setup_failure_blocks_completion(self):
        self.teach()
        with patch("tutor.subprocess.run", return_value=subprocess.CompletedProcess([], 1, "", "fixture install error")):
            self.assertEqual(self.s.setup(sys.executable)["environment"]["status"], "failed")
        self.s.mutate("explain", "The actual setup fixture failed.")
        with self.assertRaisesRegex(ValueError, "venv"):
            self.s.mutate("complete")

    def test_key_handoff_checks_presence_without_reading(self):
        self.teach()
        with patch("tutor.subprocess.run", side_effect=self.mock_process):
            self.s.setup(sys.executable)
        with self.assertRaisesRegex(ValueError, "does not exist"):
            self.s.mutate("key-ready", "Done")
        (self.s.resources / ".env").write_bytes(b"\xffPRIVATE TEST DATA")
        self.s.mutate("key-ready", "Done in local terminal")
        self.assertTrue(self.s.load()["environment"]["key_configured"])

    def test_explain_before_prediction_is_required(self):
        self.advance("t02")
        with self.assertRaisesRegex(ValueError, "Explain"):
            self.s.mutate("predict", "My prediction")

    def test_numbered_source_matches_actual_lines(self):
        self.advance("t03")
        snippets = self.s.code()["snippets"]
        public = next(s for s in snippets if "public_response" in s["numbered_code"])
        lines = Path(public["absolute_path"]).read_text(encoding="utf-8").splitlines()
        self.assertTrue(public["numbered_code"].startswith(f"{public['start_line']}: " + lines[public["start_line"]-1]))
        self.assertIn("c.message.content", public["numbered_code"])

    def test_prompt_saved_exactly_from_chat(self):
        self.advance("t04")
        self.teach()
        text = "Use only the log.\nReturn two facts and one item to confirm."
        self.s.write_prompt(text)
        self.assertEqual((self.s.resources / "student" / "instructions.txt").read_text(encoding="utf-8"), text+"\n")
        self.assertEqual(self.s.load()["tasks"]["t04"]["prompt_drafts"][-1]["origin"], "student_chat")

    def test_prompt_scaffold_cannot_be_used_as_student_work(self):
        self.advance("t04")
        self.teach()
        with self.assertRaisesRegex(ValueError, "placeholders"):
            self.s.write_prompt("[STUDENT_TASK] [EVIDENCE_RULE] [OUTPUT_STRUCTURE]")
        with self.assertRaisesRegex(ValueError, "Save"):
            self.s.mutate("predict", "A short result")

    def test_global_python_is_rejected_for_experiments(self):
        self.advance("t03")
        self.teach()
        self.s.mutate("predict", "A response")
        with self.assertRaisesRegex(ValueError, "venv"):
            self.s.run(sys.executable, "Task and purpose explained")

    def test_changed_prompt_requires_new_recorded_run(self):
        self.advance("t04")
        self.prepare_task()
        self.answer_all()
        self.s.write_prompt("Use the log only. Give two short facts and one unknown. No invented cause.")
        with self.assertRaisesRegex(ValueError, "current saved prompt"):
            self.s.mutate("complete")

    def test_token_table_preserves_an_unexpected_result(self):
        self.advance("t04")
        self.prepare_task()
        table = self.s.results()["token_table"]
        self.assertEqual([r["completion_tokens"] for r in table], [20, 50])
        self.assertGreater(table[1]["completion_tokens"], table[0]["completion_tokens"])

    def test_schema_table_keeps_origin_and_two_checks(self):
        self.advance("t06")
        self.prepare_task()
        table = self.s.results()["checks_table"]
        self.assertEqual(table[0]["origin"], "actual model response")
        self.assertTrue(table[1]["valid_format"])
        self.assertFalse(table[1]["evidence_check_passed"])

    def test_both_cases_may_be_honest_drafts(self):
        self.advance("t08")
        self.prepare_task()
        table = self.s.results()["case_table"]
        self.assertEqual([r["missing_count"] for r in table], [1, 2])
        self.assertTrue(all(r["Outcome"] == "draft_for_review" and r["diagnosis"] is None for r in table))

    def test_wrong_mcq_and_open_retry_preserve_attempts(self):
        self.advance("t02")
        self.prepare_task()
        self.s.mutate("answer", "A", question="evidence")
        with self.assertRaises(ValueError):
            self.s.mutate("complete")
        self.s.mutate("answer", "B", question="evidence")
        self.s.mutate("complete")
        self.prepare_task()
        self.s.mutate("answer", "Not enough detail", question="trace")
        self.s.mutate("assess", "Please point to a field", question="trace", verdict="retry")
        with self.assertRaises(ValueError):
            self.s.mutate("complete")
        self.assertEqual(len(self.s.load()["tasks"]["t02"]["answers"]["evidence"]), 2)

    def test_task_output_hides_keys_and_rubrics(self):
        self.advance("t02")
        self.assertNotIn("correct", self.s.task()["task"]["questions"][0])
        self.advance("t03")
        self.assertNotIn("rubric", self.s.task()["task"]["questions"][0])

    def test_full_core_reaches_100_and_resumes(self):
        percents = []
        for _ in self.lesson["tasks"]:
            self.finish()
            percents.append(self.s.status()["core_percent"])
        self.assertEqual(percents, [8,15,30,40,50,62,74,86,93,100])
        resumed = Seminar(self.workspace, root=self.plugin)
        self.assertEqual(resumed.start()["core_percent"], 100)
        self.assertTrue(Path(resumed.export()["report"]).is_file())

    def test_extensions_are_saved_without_changing_core(self):
        self.finish()
        before = self.s.status()["core_percent"]
        with patch("tutor.subprocess.run", side_effect=self.mock_process):
            self.s.run(None, "Sampling task explained", name="sampling", prediction="They may match")
        self.s.mutate("explain-extension", "Explained the actual fixture fields", name="sampling")
        self.assertEqual(self.s.status()["core_percent"], before)
        self.assertTrue(self.s.status()["extensions"]["sampling"]["explanations"])

    def test_reviews_resume_draft_and_exclude_private_files(self):
        self.s.mutate("review-answer", "My own reflection", question="r1")
        resumed = Seminar(self.workspace, root=self.plugin)
        self.assertEqual(resumed.review_questions()["questions"][0]["saved_answer"]["answer"], "My own reflection")
        with self.assertRaisesRegex(ValueError, "three"):
            resumed.review()
        (self.s.resources / ".env").write_text("SHOULD NEVER APPEAR")
        (self.s.resources / "reference.md").write_text("HIDDEN CHECKPOINT")
        for directory in (".venv", "node_modules", "outputs", "tests"):
            folder = self.s.resources / directory
            folder.mkdir(exist_ok=True)
            (folder / "private.txt").write_text("SHOULD NEVER APPEAR")
        for key in ("r2", "r3"):
            resumed.mutate("review-answer", "Another student reflection", question=key)
        result = resumed.review()
        text = Path(result["report"]).read_text(encoding="utf-8")
        self.assertIn("My own reflection", text)
        self.assertNotIn("SHOULD NEVER APPEAR", text)
        self.assertNotIn("HIDDEN CHECKPOINT", text)
        self.assertEqual(resumed.status()["core_percent"], 0)
        self.assertEqual(resumed.load()["review_draft"], {})

    def test_snapshot_size_is_bounded(self):
        for i in range(8):
            (self.s.resources / f"a{i}.py").write_text("# " + "x"*40000)
        for key in REVIEW_QUESTIONS:
            self.s.mutate("review-answer", "Typed student reflection", question=key)
        result = self.s.review()
        payload = json.loads(Path(result["report"]).with_suffix(".json").read_text(encoding="utf-8"))
        sizes = [len(item["text"].encode("utf-8")) for item in payload["code_snapshot"]]
        self.assertLessEqual(max(sizes), 20000)
        self.assertLessEqual(sum(sizes), 100000)

    def test_catalog_lists_current_progress_and_not_placeholder(self):
        (self.plugin / "week02").mkdir()
        self.finish()
        info = catalog(self.workspace, self.plugin)
        self.assertEqual([x["id"] for x in info["courses"]], ["week01"])
        self.assertEqual(info["active_week"], "week01")
        self.assertEqual(info["courses"][0]["core_percent"], 8)

    def test_five_commands_and_reflection_review(self):
        commands = ROOT / "commands"
        self.assertEqual({p.name for p in commands.glob("*.md")},
                         {"menu.md", "start.md", "status.md", "review.md", "help.md"})
        review = (commands / "review.md").read_text(encoding="utf-8")
        self.assertIn("review-questions", review)
        self.assertIn("review-answer", review)
        menu = (commands / "menu.md").read_text(encoding="utf-8")
        for word in ("optional_topics", "optional_practice_ready", "run-extension", "explain-extension"):
            self.assertIn(word, menu)
        manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertRegex(manifest["version"], r"^\d+\.\d+\.\d+$")

    def test_catalog_browsing_does_not_start_or_write_progress(self):
        workspace = self.base / "never-started"
        workspace.mkdir()
        info = catalog(workspace, self.plugin)
        course = info["courses"][0]
        self.assertEqual(list(workspace.iterdir()), [])
        self.assertFalse(course["started"])
        self.assertFalse(course["optional_practice_ready"])
        self.assertEqual({x["id"] for x in course["optional_topics"]},
                         {"sampling", "reasoning", "memory", "rag", "agent", "cases"})
        self.assertTrue(all(x["learning_status"] == "Not started" for x in course["optional_topics"]))
        before = self.s.path.read_bytes()
        catalog(self.workspace, self.plugin)
        self.assertEqual(before, self.s.path.read_bytes())

    def test_menu_optional_topic_status_resumes_without_core_change(self):
        self.finish()
        before = self.s.status()["core_percent"]
        def topic():
            course = catalog(self.workspace, self.plugin)["courses"][0]
            self.assertTrue(course["optional_practice_ready"])
            self.assertEqual(course["core_percent"], before)
            return next(t for t in course["optional_topics"] if t["id"] == "sampling")
        with patch("tutor.subprocess.run", side_effect=self.mock_process):
            self.s.run(None, "Sampling purpose explained", name="sampling", prediction="They may match")
        self.assertEqual(topic()["learning_status"], "Awaiting explanation")
        self.s.mutate("explain-extension", "Explained the actual output structure", name="sampling")
        self.assertEqual(topic()["learning_status"], "Discussed")
        with patch("tutor.subprocess.run", side_effect=self.mock_process):
            self.s.run(None, "Approved another sampling run", name="sampling", prediction="It may differ")
        self.assertEqual(topic()["learning_status"], "Awaiting explanation")
        self.assertEqual(topic()["run_count"], 2)

    def test_menu_never_marks_failed_or_pending_topic_as_discussed(self):
        self.finish()
        with patch("tutor.subprocess.run", return_value=subprocess.CompletedProcess([], 1, "fixture failure", "")):
            self.s.run(None, "Sampling purpose explained", name="sampling", prediction="It may fail")
        self.s.mutate("explain-extension", "Explained the actual failure", name="sampling")
        def label():
            return next(x for x in catalog(self.workspace, self.plugin)["courses"][0]["optional_topics"]
                        if x["id"] == "sampling")["learning_status"]
        self.assertEqual(label(), "Run failed")
        state = self.s.load()
        state["extensions"]["sampling"]["runs"][-1]["status"] = "running"
        self.s.save(state)
        self.assertEqual(label(), "Run pending")
        state["extensions"]["sampling"]["runs"][-1]["status"] = "interrupted"
        self.s.save(state)
        self.assertEqual(label(), "Run interrupted")

    def test_menu_reports_corrupt_state_without_resetting_it(self):
        self.s.path.write_text("{broken")
        course = catalog(self.workspace, self.plugin)["courses"][0]
        self.assertIn("error", course)
        self.assertFalse(course["optional_practice_ready"])
        self.assertTrue(all(t["learning_status"] == "Progress unavailable" for t in course["optional_topics"]))
        self.assertEqual(self.s.path.read_text(), "{broken")

    def test_menu_uses_selected_week_and_detects_missing_interpreter(self):
        lesson2 = copy.deepcopy(self.lesson)
        lesson2["id"] = "week02"
        lesson2["extensions"] = [dict(lesson2["extensions"][0], id="week02-only")]
        atomic_json(self.plugin / "week02" / "lesson.json", lesson2)
        courses = catalog(self.workspace, self.plugin)["courses"]
        self.assertEqual([t["id"] for t in courses[1]["optional_topics"]], ["week02-only"])
        self.assertNotIn("week02-only", [t["id"] for t in courses[0]["optional_topics"]])
        self.finish()
        Path(self.s.load()["environment"]["python"]).unlink()
        self.assertFalse(catalog(self.workspace, self.plugin)["courses"][0]["optional_practice_ready"])

    def test_plugin_update_preserves_all_learning_files(self):
        self.advance("t04")
        self.prepare_task()
        self.s.mutate("review-answer", "Reflection before update", question="r1")
        self.s.mutate("save", "Continue the prompt task next time.")
        before = {str(p.relative_to(self.workspace)): p.read_bytes()
                  for p in self.workspace.rglob("*") if p.is_file()}
        upgraded = self.base / "plugin-9.0.0"
        shutil.copytree(self.plugin, upgraded)
        atomic_json(upgraded / ".claude-plugin" / "plugin.json", {"version":"9.0.0"})
        (upgraded / "week01" / "resources" / "student" / "instructions.txt").write_text("NEW DISTRIBUTED SCAFFOLD")
        resumed = Seminar(self.workspace, root=upgraded)
        self.assertEqual(resumed.start()["core_percent"], self.s.status()["core_percent"])
        self.assertEqual(before, {str(p.relative_to(self.workspace)): p.read_bytes()
                                  for p in self.workspace.rglob("*") if p.is_file()})
        self.assertIn("Reflection before update", str(resumed.review_questions()))

    def test_new_curriculum_keeps_started_course_snapshot_and_guide(self):
        guide = self.plugin / "week01" / "TEACHING.md"
        guide.write_text("Original teaching guide", encoding="utf-8")
        self.s.start()
        self.finish()
        changed = copy.deepcopy(self.lesson)
        changed["version"] = 99
        changed["tasks"][0]["id"] = "new-task"
        changed["extensions"] = []
        atomic_json(self.plugin / "week01" / "lesson.json", changed)
        guide.write_text("Updated teaching guide", encoding="utf-8")
        resumed = Seminar(self.workspace, root=self.plugin)
        self.assertEqual(resumed.start()["core_percent"], 8)
        self.assertEqual(resumed.lesson, self.lesson)
        self.assertEqual(Path(resumed.status()["teaching_guide"]).read_text(), "Original teaching guide")
        self.assertEqual(len(catalog(self.workspace, self.plugin)["courses"][0]["optional_topics"]), 6)
        fresh = self.base / "new-learner"
        fresh.mkdir()
        self.assertEqual(Seminar(fresh, root=self.plugin).lesson["version"], 99)

    def test_existing_201_progress_gains_snapshot_without_rewriting_records(self):
        self.finish()
        self.s.snapshot.unlink()
        before = self.s.path.read_bytes()
        resumed = Seminar(self.workspace, root=self.plugin)
        self.assertEqual(resumed.start()["core_percent"], 8)
        self.assertTrue(resumed.snapshot.is_file())
        self.assertEqual(resumed.path.read_bytes(), before)

    def test_removed_course_stays_in_catalog_when_snapshot_exists(self):
        (self.plugin / "week01").rename(self.plugin / "retired-week01")
        courses = catalog(self.workspace, self.plugin)["courses"]
        self.assertEqual([c["id"] for c in courses], ["week01"])
        self.assertTrue(courses[0]["started"])
        self.assertEqual(Seminar(self.workspace, root=self.plugin).start()["core_percent"], 0)

    def test_legacy_only_progress_is_not_silently_replaced(self):
        workspace = self.base / "legacy-only"
        old = workspace / ".hi-agent-seminar" / "week01" / "progress.json"
        atomic_json(old, {"old_complete":True})
        before = old.read_bytes()
        course = catalog(workspace, self.plugin)["courses"][0]
        self.assertIn("error", course)
        self.assertIsNone(course["core_percent"])
        s = Seminar(workspace, root=self.plugin)
        with self.assertRaisesRegex(ValueError, "Older learning records"):
            s.start()
        self.assertFalse(s.path.exists())
        self.assertEqual(old.read_bytes(), before)

    def test_incompatible_schema_and_unpinned_lesson_keep_original_records(self):
        state = self.s.load()
        state["schema_version"] = 999
        atomic_json(self.s.path, state)
        before = self.s.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "NOT reset"):
            self.s.start()
        self.assertEqual(self.s.path.read_bytes(), before)
        state["schema_version"] = 2
        atomic_json(self.s.path, state)
        self.s.snapshot.unlink()
        changed = copy.deepcopy(self.lesson)
        changed["version"] = 999
        atomic_json(self.plugin / "week01" / "lesson.json", changed)
        before = self.s.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "NOT reset"):
            Seminar(self.workspace, root=self.plugin).start()
        self.assertEqual(self.s.path.read_bytes(), before)

    def test_corrupt_snapshot_does_not_fall_back_to_new_lesson(self):
        self.s.snapshot.write_text("{broken")
        before = self.s.path.read_bytes()
        self.assertIn("error", catalog(self.workspace, self.plugin)["courses"][0])
        with self.assertRaisesRegex(ValueError, "snapshot"):
            Seminar(self.workspace, root=self.plugin)
        self.assertEqual(self.s.path.read_bytes(), before)

    def test_optional_results_and_review_survive_course_update(self):
        self.finish()
        with patch("tutor.subprocess.run", side_effect=self.mock_process):
            self.s.run(None, "Sampling task explained", name="sampling", prediction="They may match")
        self.s.mutate("explain-extension", "Explained actual fixture fields", name="sampling")
        for key in REVIEW_QUESTIONS:
            self.s.mutate("review-answer", "A saved reflection", question=key)
        report = self.s.review()["report"]
        before = self.s.load()
        report_bytes = Path(report).read_bytes()
        changed = copy.deepcopy(self.lesson)
        changed["version"] = 100
        atomic_json(self.plugin / "week01" / "lesson.json", changed)
        resumed = Seminar(self.workspace, root=self.plugin)
        self.assertEqual(resumed.start()["core_percent"], 8)
        self.assertEqual(resumed.load(), before)
        self.assertEqual(Path(report).read_bytes(), report_bytes)
        self.assertEqual(resumed.status()["review_count"], 1)
        topic = next(t for t in catalog(self.workspace, self.plugin)["courses"][0]["optional_topics"] if t["id"] == "sampling")
        self.assertEqual(topic["learning_status"], "Discussed")

    def test_corrupt_state_is_not_reset(self):
        self.s.path.write_text("{broken")
        with self.assertRaisesRegex(ValueError, "NOT reset"):
            self.s.start()
        self.assertEqual(self.s.path.read_text(), "{broken")

    def test_timing_calls_and_english_assets(self):
        for session in (1,2):
            self.assertEqual(sum(t["minutes"] for t in self.lesson["tasks"] if t["session"]==session), 50)
        self.assertEqual(sum(t["planned_calls"] for t in self.lesson["tasks"]), 11)
        self.assertEqual(sum(t["weight"] for t in self.lesson["tasks"]), 100)
        for name in ("persona.md", "MENTOR.md", "week01/TEACHING.md", "week01/lesson.json"):
            self.assertFalse(any("\u3400" <= c <= "\u9fff" for c in (ROOT/name).read_text(encoding="utf-8")), name)


if __name__ == "__main__":
    unittest.main()
