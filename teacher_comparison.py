"""Validate supplied teacher measurements; never manufacture device results."""
import math
import re
from tutor import require

QUESTION = ("Using the teacher's CPU and CUDA times, calculate CPU time / CUDA time. "
            "Explain why their work is comparable. Which measurements are from your "
            "computer and which are teacher reference data? Why can you not use your "
            "CPU time divided by the teacher's CUDA time as your computer's speedup? "
            "Give one limitation of one run per device and distinguish CPU RSS from "
            "CUDA allocated memory.")
RUBRIC = ("Check arithmetic against the teacher pair; same initialization, batches, "
          "configuration and timing scope; explicit local/reference attribution; "
          "no cross-machine speedup claim; n=1 does not establish stable performance; "
          "process RSS and PyTorch allocated CUDA bytes have different scopes.")


def validate_pair(cpu, cuda):
    equal = ("config", "batch_size", "steps", "warmup_updates", "seed", "threads",
             "learning_rate", "precision", "timing_scope", "source_implementation", "environment",
             "initial_weights_sha256", "training_batches_sha256", "train_sha256", "val_sha256")
    for key in equal:
        require(key in cpu and key in cuda and cpu[key] == cuda[key],
                "Teacher CPU/CUDA workload mismatch or missing field: " + key)
    require(cpu["steps"] == 200 and cpu["warmup_updates"] == 10 and cpu["batch_size"] == 16,
            "Teacher data must use the core 200-step, 10-warmup, B=16 configuration.")
    config = cpu["config"]
    require(isinstance(config, dict) and all(config.get(k) == v for k,v in {"vocab_size":96, "block_size":64, "embed_dim":128,
            "num_heads":4, "num_layers":2}.items()), "Teacher model differs from the core model.")
    require(cpu["precision"] == "FP32, TF32 disabled" and cpu["learning_rate"] == 0.0003,
            "Teacher precision or learning rate differs from the core experiment.")
    for m, device in ((cpu, "cpu"), (cuda, "cuda")):
        require(m.get("status") == "ok" and m.get("device") == device,
                "Provide successful real CPU and CUDA metrics, not unavailable or failed runs.")
        require(not any(m.get(k) for k in ("fixture", "explicit_test_fixture", "simulated")),
                "Labelled fixtures or simulated measurements are not teacher evidence.")
        require(isinstance(m.get("environment"), dict) and m["environment"], "Missing hardware/software environment.")
        for key in ("initial_weights_sha256", "training_batches_sha256", "train_sha256", "val_sha256"):
            require(bool(re.fullmatch(r"[a-f0-9]{64}", str(m[key]))), "Invalid measurement hash: " + key)
        for key in ("elapsed_seconds", "tokens_per_second"):
            require(isinstance(m.get(key), (int, float)) and math.isfinite(m[key]) and m[key] > 0,
                    "Missing or invalid measurement: " + key)
        require(m.get("measured_tokens") == 204800 and math.isclose(
            m["tokens_per_second"], 204800 / m["elapsed_seconds"], rel_tol=1e-5),
            "Teacher throughput does not match the recorded workload and time.")
        require(isinstance(m.get("process_rss_sampled_peak_bytes"), (int, float))
                and m["process_rss_sampled_peak_bytes"] > 0 and m.get("rss_scope"), "Missing RSS measurement/scope.")
        if device == "cuda":
            require(isinstance(m.get("gpu_peak_allocated_bytes"), (int, float))
                    and m["gpu_peak_allocated_bytes"] > 0 and m.get("gpu_scope"), "Missing CUDA memory measurement/scope.")
    return {"teacher_cpu_seconds":cpu["elapsed_seconds"], "teacher_cuda_seconds":cuda["elapsed_seconds"],
            "teacher_pair_speedup":cpu["elapsed_seconds"] / cuda["elapsed_seconds"],
            "origin":"teacher_reference_not_student_hardware",
            "limitation":"One measurement per device; no universal or cross-machine speedup claim."}
