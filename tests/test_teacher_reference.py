"""Synthetic unit fixtures only; these numbers are never distributed as teacher data."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import test_week02 as base
from tutor import atomic_json, fingerprint, Week2Seminar
from teacher_comparison import validate_pair


class TeacherReferenceTests(unittest.TestCase):
    setUp = base.Week2Tests.setUp
    teach = base.Week2Tests.teach
    ready = base.Week2Tests.ready
    finish = base.Week2Tests.finish
    advance = base.Week2Tests.advance
    fixture_process = base.Week2Tests.fixture_process

    def prepare(self):
        self.advance("w208")
        self.teach()
        self.s.mutate("predict", "Synthetic test prediction")
        with patch("week02_support.checked_process", side_effect=self.fixture_process):
            self.s.run(None, "Unit test CPU evidence")
        state = self.s.load()
        run = state["tasks"]["w208"]["runs"][-1]
        run["status"] = "awaiting_gpu"
        run["commands"][0]["summary"] = {"status":"awaiting_gpu", "plot_returncode":0,
             "equal_work_hashes_match":True, "measurements":[{"device":"cpu", "status":"ok", "elapsed_seconds":2}]}
        self.s.save(state)
        self.dataset = self.base / "unit-only-reference"
        metric = {"status":"ok", "device":"cpu", "config":{"vocab_size":96,"block_size":64,"embed_dim":128,"num_heads":4,"num_layers":2},
                  "batch_size":16, "steps":200, "warmup_updates":10, "seed":4149,"threads":2,
                  "learning_rate":0.0003,"precision":"FP32, TF32 disabled", "timing_scope":"unit test scope", "source_implementation":"unit test",
                  "environment":{"test_context":"synthetic unit fixture"},"measured_tokens":204800,
                  "elapsed_seconds":2,"tokens_per_second":102400,"process_rss_sampled_peak_bytes":100,
                  "rss_scope":"test scope","gpu_peak_allocated_bytes":200,"gpu_scope":"test scope"}
        for key in ("initial_weights_sha256","training_batches_sha256","train_sha256","val_sha256"):
            metric[key] = "a" * 64
        for device in ("cpu", "cuda"):
            metric["device"] = device
            atomic_json(self.dataset / (device + "_r1") / "metrics.json", metric)
        return run["id"]

    def attach(self):
        return self.s.reference_data(self.dataset, "Synthetic unit test, never classroom evidence")

    def answer(self):
        self.s.mutate("explain", "Explained local and reference evidence separately")
        self.s.reference_answer("Student unit-test answer distinguishing devices, timing and evidence")
        self.s.reference_answer("Mentor unit-test assessment", "pass")
        self.s.mutate("answer", "C", question="fairness")

    def test_no_gpu_path_reaches_100_without_relabelling_run(self):
        ident = self.prepare()
        original_snapshot = self.s.snapshot.read_bytes()
        self.attach()
        with self.assertRaises(ValueError):
            self.s.reference_answer("Answer before explanation")
        self.answer()
        self.assertEqual(self.s.mutate("complete")["status"]["core_percent"], 80)
        while self.s.current(self.s.load()):
            self.finish()
        self.assertEqual(self.s.status()["core_percent"], 100)
        run = self.s.load()["tasks"]["w208"]["runs"][-1]
        self.assertEqual((run["id"],run["status"]), (ident,"awaiting_gpu"))
        self.assertEqual(self.s.snapshot.read_bytes(), original_snapshot)
        report = Path(self.s.export()["report"]).read_text(encoding="utf-8")
        self.assertIn("no student GPU measurement", report)

    def test_reference_without_pass_cannot_complete(self):
        self.prepare()
        self.attach()
        self.s.mutate("explain", "Explained teacher pair and local CPU")
        self.s.mutate("answer", "C", question="fairness")
        self.s.reference_answer("Student pending answer")
        with self.assertRaises(ValueError):
            self.s.mutate("complete")
        self.s.reference_answer("Need a better explanation", "retry")
        with self.assertRaises(ValueError):
            self.s.mutate("complete")

    def test_invalid_or_missing_teacher_gpu_rejected(self):
        self.prepare()
        path = self.dataset / "cuda_r1/metrics.json"
        metrics = json.loads(path.read_text())
        for key,value in (("status","unavailable"),("steps",20),("tokens_per_second",1),("explicit_test_fixture",True)):
            changed = dict(metrics, **{key:value})
            atomic_json(path, changed)
            with self.assertRaises(ValueError):
                self.attach()
        self.assertNotIn("teacher_reference", self.s.load()["tasks"]["w208"])

    def test_model_or_reference_change_invalidates_binding(self):
        self.prepare()
        self.attach()
        self.answer()
        ref = self.s.load()["tasks"]["w208"]["teacher_reference"]
        path = Path(ref["file"])
        content = path.read_bytes()
        path.write_bytes(content + b" ")
        self.assertFalse(self.s.reference_ready(self.s.load()))
        with self.assertRaises(ValueError):
            self.s.mutate("complete")
        path.write_bytes(content)
        model = self.s.resources / "model.py"
        model.write_text(model.read_text() + "\n# Changed model\n")
        self.assertFalse(self.s.reference_ready(self.s.load()))

    def test_resume_preserves_reference_and_old_answers(self):
        self.prepare()
        self.attach()
        self.answer()
        self.s = Week2Seminar(self.workspace, "week02")
        self.assertTrue(self.s.reference_ready(self.s.load()))
        self.attach()
        record = self.s.load()["tasks"]["w208"]
        self.assertEqual(record["teacher_reference_history"][-1]["answers"][-1]["verdict"], "pass")
        self.assertEqual(record["teacher_reference"]["answers"], [])
        with self.assertRaises(ValueError):
            self.s.mutate("complete")

    def test_failed_cpu_cannot_use_reference(self):
        self.prepare()
        state = self.s.load()
        state["tasks"]["w208"]["runs"][-1]["status"] = "failed"
        self.s.save(state)
        with self.assertRaises(ValueError):
            self.attach()

    def test_new_cpu_run_requires_new_binding_and_analysis(self):
        self.prepare()
        self.attach()
        self.answer()
        state = self.s.load()
        runs = state["tasks"]["w208"]["runs"]
        repeated = copy.deepcopy(runs[-1])
        repeated["id"] = "new-test-run"
        runs.append(repeated)
        self.s.save(state)
        self.assertFalse(self.s.reference_ready(self.s.load()))
        with self.assertRaises(ValueError):
            self.s.mutate("complete")
