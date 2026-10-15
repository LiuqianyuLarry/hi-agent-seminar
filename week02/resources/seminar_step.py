"""Recorded local teaching experiments. No model API calls or completed TODOs."""
import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent


def process(arguments, out, label, timeout=480):
    result = subprocess.run([sys.executable, "-X", "utf8", *arguments], cwd=ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                            encoding="utf-8", errors="replace", timeout=timeout, check=False)
    (out / (label + ".txt")).write_text(result.stdout, encoding="utf-8")
    return result.returncode


def tests(out, selection=None):
    xml = out / "tests.xml"
    arguments = ["-m", "pytest", "-q", "tests/test_model.py", "-o", "pythonpath=.", "--junitxml", str(xml)]
    if selection:
        arguments += ["-k", selection]
    code = process(arguments, out, "pytest")
    cases = list(ET.parse(xml).getroot().iter("testcase")) if xml.exists() else []
    failed = [c.attrib.get("name") for c in cases if c.find("failure") is not None or c.find("error") is not None]
    skipped = [c.attrib.get("name") for c in cases if c.find("skipped") is not None]
    return {"status":"ok" if code == 0 and cases and not skipped else "failed", "returncode":code,
            "collected":len(cases), "passed":len(cases)-len(failed)-len(skipped), "failed":failed,
            "skipped":skipped, "tests_xml":str(xml), "stdout":str(out / "pytest.txt")}


def environment(out):
    import preflight
    info = preflight.report()
    required = ["torch", "numpy", "matplotlib", "pytest", "psutil"]
    check = tests(out, "vocabulary or data_disjoint or config")
    ready = info["data_present"] and all(info["packages"].get(p) != "NOT INSTALLED" for p in required)
    return {"status":"ok" if ready and check["status"] == "ok" else "failed", "environment":info,
            "starter_checks":check, "api_calls":0, "note":"CUDA=False means unavailable hardware, not failed CPU setup. Full model tests wait until the four TODOs are written."}


def data_example():
    from data import ALPHABET, encode, decode, load_tokens, make_batches
    x, y = make_batches(load_tokens("train"), 1, 16, 1, 4149)[0]
    return {"status":"ok", "vocabulary_size":len(ALPHABET), "example_text":"M12 ",
            "actual_ids":encode("M12 ").tolist(), "x_ids":x[0].tolist(), "y_ids":y[0].tolist(),
            "x_text":decode(x[0]), "y_text":decode(y[0]), "shape":list(x.shape),
            "shift_matches":bool((x[:,1:] == y[:,:-1]).all()),
            "note":"IDs are lookup labels from data.py, not ASCII code values or physical measurements."}


def attention_math():
    import torch
    q = torch.tensor([[1., 0.]])
    k = torch.tensor([[1., 0.], [0., 1.], [1., 1.]])
    v = torch.tensor([[2., 0.], [0., 2.], [2., 2.]])
    scores = q @ k.T / 2**0.5
    weights = scores.softmax(-1)
    return {"status":"ok", "kind":"illustrative numeric calculation, not trained model weights",
            "q":q.tolist(), "keys":k.tolist(), "values":v.tolist(), "scaled_scores":scores.tolist(),
            "weights":weights.tolist(), "row_sum":weights.sum(-1).tolist(), "output":(weights @ v).tolist(),
            "pooled_tensor":"Value", "head_width":2}


def fixed_batch_probe(out):
    import torch
    from torch.nn import functional as F
    from model import ModelConfig, MiniGPT
    torch.set_num_threads(1)
    torch.manual_seed(7)
    config = ModelConfig(block_size=12, embed_dim=32, num_heads=4, num_layers=1)
    model = MiniGPT(config)
    x = torch.randint(96, (2,12))
    y = torch.randint(96, (2,12))
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.01)
    losses = []
    for step in range(31):
        optimizer.zero_grad(set_to_none=True)
        logits = model(x)
        loss = F.cross_entropy(logits.reshape(-1,96), y.reshape(-1))
        losses.append(float(loss.detach()))
        if step < 30:
            loss.backward()
            optimizer.step()
    with (out / "fixed_batch_loss.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["updates", "fixed_batch_loss"])
        writer.writerows(enumerate(losses))
    return {"updates":30, "initial_loss":losses[0], "final_loss":losses[-1],
            "logits_shape":list(logits.shape), "finite":all(torch.isfinite(torch.tensor(losses)).tolist()),
            "purpose":"Implementation check using one repeated batch; not held-out generalization.",
            "formal_run_uses_fresh_model":True}


def benchmark(out, repeats=1):
    folder = out / "compare"
    code = process(["benchmark.py", "--devices", "cpu", "cuda", "--repeats", str(repeats),
                    "--steps", "200", "--warmup", "10", "--out", str(folder)], out, "benchmark")
    if code:
        return {"status":"failed", "returncode":code, "stdout":str(out / "benchmark.txt")}
    with (folder / "benchmark_results.csv").open(encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    metrics = [json.loads((folder / row["metrics_path"]).read_text(encoding="utf-8")) for row in rows]
    plotting = process(["plot_results.py", str(folder)], out, "plotting")
    successful = [m for m in metrics if m["status"] == "ok"]
    available = {m["device"] for m in successful}
    equal = all(len({m[f] for m in successful}) <= 1 for f in ["initial_weights_sha256", "training_batches_sha256"])
    return {"status":("failed" if plotting or not equal else "ok" if available == {"cpu", "cuda"} else "awaiting_gpu"),
            "repeats_per_device":repeats, "measured_steps":200, "warmup_updates":10,
            "equal_work_hashes_match":equal, "measurements":metrics,
            "csv":str(folder / "benchmark_results.csv"), "plot_returncode":plotting,
            "note":"Training token positions/s is not text-generation speed. Missing CUDA is retained as unavailable; obtain a real GPU run before completing the device comparison."}


def failures(out):
    records = []
    for case in ["no_causal_mask", "no_optimizer_step"]:
        path = out / (case + ".json")
        code = process(["failure_demo.py", "--case", case, "--out", str(path)], out, case)
        if code:
            return {"status":"failed", "returncode":code, "case":case}
        records.append(json.loads(path.read_text(encoding="utf-8")))
    return {"status":"ok" if all(r["fault_detected"] for r in records) else "failed", "injected":True,
            "cases":records, "note":"These failures are deliberate teaching changes in temporary model instances; the student's model.py is not edited."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", required=True, choices=["preflight", "data", "attention_math", "head", "multihead", "blocks", "full_tests", "benchmark", "failures", "repeat3", "batch", "context_math", "kv_concept", "architecture"])
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    target = out / "week02_result.json"
    if target.exists():
        parser.error("This output already has a result. Choose a fresh directory; do not overwrite evidence.")
    try:
        if args.action == "preflight":
            result = environment(out)
        elif args.action == "data":
            result = data_example()
        elif args.action == "attention_math":
            result = attention_math()
        elif args.action in {"head", "multihead", "blocks", "full_tests"}:
            selection = {"head":"head_matches", "multihead":"multihead", "blocks":"feedforward or residual", "full_tests":None}[args.action]
            result = tests(out, selection)
            if args.action == "full_tests" and result["status"] == "ok":
                result["small_batch_probe"] = fixed_batch_probe(out)
        elif args.action in {"benchmark", "repeat3"}:
            result = benchmark(out, repeats=1 if args.action == "benchmark" else 3)
        elif args.action == "failures":
            result = failures(out)
        elif args.action == "batch":
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            code = process(["batch_sweep.py", "--device", device, "--steps", "50", "--out", str(out / "batch")], out, "batch_sweep")
            metrics = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((out / "batch").glob("B*/*/metrics.json"))]
            result = {"status":"ok" if code == 0 and len(metrics) == 3 else "failed", "device":device,
                      "measurements":metrics, "note":"B=1,8,16; different token budgets. Compare throughput/memory, not learning quality by final loss."}
        elif args.action == "context_math":
            result = {"status":"ok", "kind":"calculated matrix size, not measured total memory", "B":16, "heads":4,
                      "rows":[{"T":t, "one_attention_matrix_MiB":16*4*t*t*4/1024**2} for t in [64,128,256]]}
        elif args.action == "kv_concept":
            result = {"status":"ok", "kind":"concept recap only; no KV-cache implementation", "saved":"past keys and values at inference",
                      "benefit":"less repeated computation", "cost":"growing memory", "not_user_memory":True}
        else:
            result = {"status":"ok", "kind":"architecture recap; no encoder or cross-attention implemented",
                      "mini_gpt_route":["token IDs", "token + position embeddings", "Pre-LN masked attention + residual", "Pre-LN FFN + residual", "final LayerNorm", "vocabulary logits"],
                      "original_figure":"assets/transformer-original.png"}
    except Exception as exc:
        result = {"status":"failed", "error_type":type(exc).__name__, "message":str(exc)}
    result.update(action=args.action, api_calls=0)
    target.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "ok" else 3 if result["status"] == "awaiting_gpu" else 1


if __name__ == "__main__":
    raise SystemExit(main())
