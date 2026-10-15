"""Local MiniGPT course support; Week 1 remains on its original runner."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import uuid

from tutor import child, clean_text, fingerprint, now, require, redact, atomic_json, english_display


def atomic_text(path, text):
    fd, temporary = tempfile.mkstemp(prefix=".code-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def checked_process(command, cwd, timeout=600):
    try:
        result = subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False)
        return result.returncode, redact(result.stdout or "")
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        return 124, redact(output + "\nTime limit reached. No success was assumed.")


class Week2Mixin:
    def status(self, state=None):
        state = state or self.load()
        result = super().status(state)
        current = self.current(state)
        runs = state["tasks"][current["id"]]["runs"] if current else []
        if runs and runs[-1]["status"] == "awaiting_gpu":
            result["next"] = "Obtain an actual CUDA measurement for the pending equal-work device comparison; keep the saved CPU evidence."
        result["foundation_choices"] = {key:history[-1]["choice"] for key,history in state.get("concept_choices", {}).items() if history}
        return result

    def concepts(self):
        state = self.load()
        task = self.current(state)
        require(task is not None, "The core is complete; browse optional topics.")
        saved = state.get("concept_choices", {})
        return {"task":task["id"], "concepts":[
            {**c, "saved_choice":saved.get(c["id"], [])[-1] if saved.get(c["id"]) else None}
            for c in task.get("concepts", [])],
            "choices":{"understand":"I understand - continue", "brief":"Explain briefly",
                       "example":"Show an example"},
            "instruction":"Offer each concept or small related group with genuine choice cards before explaining it. Skipping a refresher does not skip task checks."}

    def concept_choice(self, name, choice):
        require(choice in {"understand", "brief", "example"}, "Choose understand, brief or example.")
        with self.lock():
            state = self.load()
            task = self.current(state)
            require(task and name in {c["id"] for c in task.get("concepts", [])}, "Choose a concept from the current task.")
            state.setdefault("concept_choices", {}).setdefault(name, []).append(
                {"at":now(), "task":task["id"], "choice":choice})
            self.save(state)
        return {"saved_choice":choice, "concept":name, "core_percent":self.status(state)["core_percent"],
                "instruction":"Follow the student's requested depth. Save teaching only after presenting the required logic, mathematics and code. Checks still apply."}

    def diagram(self):
        state = self.load()
        task = self.current(state)
        selected = set(task.get("module_ids", [])) if task else set()
        return {"figure":str(child(self.resources, "assets", "transformer-original.png")),
                "browser_guide":str(child(self.resources, "transformer-map.html")),
                "mini_gpt_route":"IDs [B,T] -> token + position vectors [B,T,d] -> (Pre-LN masked attention + residual -> Pre-LN FFN + residual) x L -> final LayerNorm -> vocabulary logits [B,T,V]",
                "modules":[m for m in self.lesson["transformer_modules"] if not selected or m["id"] in selected],
                "caption":"Vaswani et al. (2017), Attention Is All You Need, Figure 1. Original encoder-decoder architecture.",
                "instruction":"Locate the labelled box in the original figure, explain its purpose, then map the MiniGPT difference and actual source symbol. Our model has no encoder or cross-attention and uses Pre-LN and learned positions. If images cannot display, link the local browser guide and use the text map."}

    def mutate(self, action, text="", question=None, verdict=None, run_id=None, name=None):
        if action == "teach":
            state = self.load()
            task = self.current(state)
            choices = state.get("concept_choices", {})
            require(task and all(choices.get(c["id"]) for c in task.get("concepts", [])),
                    "Offer the foundation concept cards before teaching; record the student's choice for each concept.")
        if action == "key-ready":
            raise ValueError("Week 2 runs locally and needs no API key.")
        return super().mutate(action, text, question, verdict, run_id, name)

    def missing(self, task, record):
        gaps = super().missing(task, record)
        state = self.load()
        if task.get("requires_setup"):
            gaps = [g for g in gaps if g != "student configures the key in their own terminal"]
        for module in task.get("code_targets", []):
            if not record.get("code_drafts", {}).get(module):
                gaps.append("save the student's " + module + " implementation")
        if task.get("bind_model") and record["runs"]:
            if record["runs"][-1].get("model_sha256") != fingerprint(child(self.resources, "model.py")):
                gaps.append("rerun this check with the current model.py")
        if task.get("evidence_task"):
            source = state["tasks"][task["evidence_task"]]
            if not source["runs"] or source["runs"][-1]["status"] != "success":
                gaps.append("a successful saved benchmark for output interpretation")
        return gaps

    def write_code(self, name, text):
        text = clean_text(text)
        body = textwrap.dedent(text).strip()
        require(not any("\u3400" <= c <= "\u9fff" for c in body), "Write the exercise code and comments in English.")
        require("TODO" not in body and "NotImplementedError" not in body, "Replace the exercise placeholder with your implementation.")
        candidate_body = ast.parse("def exercise(self, x):\n" + textwrap.indent(body, "    ")).body[0].body
        require(any(isinstance(n, ast.Return) for n in ast.walk(ast.Module(body=candidate_body, type_ignores=[]))), "Include the output return statement.")
        require(not any(isinstance(n, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal, ast.ClassDef, ast.FunctionDef))
                        for node in candidate_body for n in ast.walk(node)), "Submit only this forward method's tensor operations, without imports or new definitions.")
        with self.lock():
            state = self.load()
            task = self.current(state)
            require(task and name in task.get("code_targets", []), "This code exercise does not belong to the current task.")
            record = state["tasks"][task["id"]]
            require(record["teaching"], "Explain the logic, mathematics, diagram and numbered code before asking for an implementation.")
            require(not any(r["status"] == "running" for t in [*state["tasks"].values(), *state["extensions"].values()] for r in t["runs"]), "Wait for the active run before editing code.")
            path = child(self.resources, "model.py")
            previous = path.read_text(encoding="utf-8")
            tree = ast.parse(previous)
            class_name = self.lesson["code_targets"][name]
            classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name]
            require(len(classes) == 1, "Expected model class was not found; preserve and inspect the student file.")
            methods = [n for n in classes[0].body if isinstance(n, ast.FunctionDef) and n.name == "forward"]
            require(len(methods) == 1, "The target forward method is missing or duplicated; preserve and inspect the student file.")
            method = methods[0]
            lines = previous.splitlines(keepends=True)
            indent = " " * (method.col_offset + 4)
            replacement = textwrap.indent(body, indent) + "\n"
            updated = "".join(lines[:method.lineno]) + replacement + "".join(lines[method.end_lineno:])
            ast.parse(updated)
            draft_id = uuid.uuid4().hex
            history = child(self.base, "code_history", draft_id)
            history.mkdir(parents=True)
            atomic_text(child(history, "model.before.py"), previous)
            # Save the student's exact submitted text and the recoverable target before editing.
            draft = {"id":draft_id, "at":now(), "origin":"student_chat", "submitted_text":text,
                     "class":class_name, "backup":str(history / "model.before.py"),
                     "sha256":hashlib.sha256(updated.encode("utf-8")).hexdigest()}
            atomic_json(child(history, "draft.json"), draft)
            atomic_text(path, updated)
            record.setdefault("code_drafts", {}).setdefault(name, []).append(draft)
            self.save(state)
        return {"saved_file":str(path), "module":name, "saved_text":body, "status":self.status(state),
                "next":"Ask for a prediction, then run the real test. Saving code does not prove it is correct."}

    def setup(self, interpreter=sys.executable, install=None):
        interpreter = str(Path(interpreter).expanduser().absolute())
        require(Path(interpreter).is_file(), "Python interpreter was not found.")
        if install == "cpu":
            require(not child(self.resources, ".venv").exists(), "A course environment already exists. Inspect/repair it; do not overwrite a CUDA environment with CPU packages.")
        with self.lock():
            state = self.load()
            task = self.current(state)
            require(task and task.get("requires_setup"), "Environment preparation belongs to the setup task.")
            require(state["tasks"][task["id"]]["teaching"], "Explain the local experiment and setup purpose first.")
            require(state["environment"].get("status") != "running", "Environment setup is already running.")
            run_id = uuid.uuid4().hex
            folder = child(self.base, "setup", run_id)
            folder.mkdir(parents=True)
            env = {"id":run_id, "status":"running", "started_at":now(), "helper_pid":os.getpid(),
                   "python":interpreter, "steps":[], "requires_api_key":False}
            state["environment"] = env
            self.save(state)
        commands = []
        if install == "cpu":
            venv = child(self.resources, ".venv")
            require(not venv.exists(), "A course environment already exists. Inspect/repair it; do not overwrite a CUDA environment with CPU packages.")
            python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            commands = [("Create Week 2 environment", [interpreter, "-m", "venv", str(venv)]),
                        ("Install supplied CPU dependencies", [str(python), "-m", "pip", "install", "--disable-pip-version-check", "-r", str(child(self.resources, "requirements-cpu.txt"))])]
            interpreter = str(python)
        commands.append(("Check actual environment and starter data", [interpreter, "-X", "utf8", str(child(self.resources, "seminar_step.py")), "--action", "preflight", "--output-dir", str(folder / "check")]))
        try:
            for i, (label, command) in enumerate(commands, 1):
                code, output = checked_process(command, self.resources, timeout=900)
                log = child(folder, f"step{i}.txt")
                atomic_text(log, output)
                env["steps"].append({"step":label, "returncode":code, "log":str(log), "summary":output[-2500:]})
                if code:
                    break
            report_path = folder / "check" / "week02_result.json"
            report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.is_file() else {}
            env.update(status="ready" if len(env["steps"]) == len(commands) and all(s["returncode"] == 0 for s in env["steps"]) and report.get("status") == "ok" else "failed",
                       python=interpreter, report=report, finished_at=now())
        except (OSError, ValueError) as exc:
            env.update(status="failed", error=redact(str(exc)), finished_at=now())
        with self.lock():
            state = self.load()
            require(state["environment"].get("id") == run_id and state["environment"].get("status") == "running", "Setup state changed; inspect before continuing.")
            state["environment"] = env
            self.save(state)
        return {"environment":env, "status":self.status(state),
                "next_instruction":"Explain the actual JSON fields. This week needs no model API key. Install dependencies before class; never replace a working CUDA environment blindly."}

    def run(self, interpreter, intro, name=None, prediction=None):
        intro = clean_text(intro)
        with self.lock():
            state = self.load()
            env = state["environment"]
            require(env.get("status") == "ready", "Verify the Week 2 Python environment first.")
            interpreter = str(Path(interpreter or env["python"]).expanduser().absolute())
            require(interpreter == env["python"] and Path(interpreter).is_file(), "Use the verified Week 2 interpreter.")
            task = self.extension(name) if name else self.current(state)
            require(task is not None and task["commands"], "This is a discussion task; no experiment is needed.")
            if name:
                if name in {"repeat3", "batch"}:
                    require(state["tasks"]["w207"]["complete"], "Complete the four code exercises and full model checks before optional training experiments.")
                prediction = clean_text(prediction or "")
                record = state["extensions"].setdefault(name, {"runs":[], "explanations":[]})
            else:
                record = state["tasks"][task["id"]]
                require(record["teaching"] and record["predictions"], "Explain the logic, mathematics and code, then record the student's prediction first.")
                prediction = record["predictions"][-1]["text"]
                require(all(record.get("code_drafts", {}).get(n) for n in task.get("code_targets", [])), "Save the student's code attempt before testing.")
            require(not any(r["status"] == "running" for t in [*state["tasks"].values(), *state["extensions"].values()] for r in t["runs"]), "A run is pending; inspect/recover before retrying.")
            run_id = uuid.uuid4().hex
            folder = child(self.base, "runs", run_id)
            folder.mkdir(parents=True)
            run = {"id":run_id, "task":task["id"], "status":"running", "started_at":now(), "helper_pid":os.getpid(),
                   "intro":intro, "prediction":prediction, "planned_calls":0, "commands":[], "folder":str(folder),
                   "model_sha256":fingerprint(child(self.resources, "model.py"))}
            record["runs"].append(run)
            self.save(state)
        try:
            for i, arguments in enumerate(task["commands"], 1):
                require(len(arguments) == 3 and arguments[:2] == ["seminar_step.py", "--action"] and arguments[2] in {
                    "data", "attention_math", "head", "multihead", "blocks", "full_tests", "benchmark", "failures", "repeat3", "batch", "context_math", "kv_concept", "architecture"}, "Unapproved Week 2 command.")
                out = child(folder, f"command{i:02d}")
                out.mkdir()
                code, output = checked_process([interpreter, "-X", "utf8", str(child(self.resources, "seminar_step.py")), *arguments[1:], "--output-dir", str(out)], self.resources, timeout=600)
                atomic_text(out / "stdout.txt", output)
                artifacts = sorted(str(p) for p in out.rglob("*") if p.is_file() and p.suffix.lower() in {".json", ".csv", ".txt", ".png", ".xml"})
                summary_path = out / "week02_result.json"
                summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.is_file() else {}
                run["commands"].append({"arguments":arguments, "returncode":code, "stdout":str(out / "stdout.txt"), "artifacts":artifacts, "summary":summary})
                if code:
                    break
            run["status"] = "success" if len(run["commands"]) == len(task["commands"]) and all(c["returncode"] == 0 and c["summary"].get("status") == "ok" for c in run["commands"]) else "failed"
            if any(c["summary"].get("status") == "awaiting_gpu" for c in run["commands"]):
                run["status"] = "awaiting_gpu"
        except Exception as exc:
            run.update(status="failed", error=redact(f"{type(exc).__name__}: {exc}"))
        run["finished_at"] = now()
        atomic_json(folder / "receipt.json", run)
        with self.lock():
            state = self.load()
            record = state["extensions"][name] if name else state["tasks"][task["id"]]
            index = next(i for i, r in enumerate(record["runs"]) if r["id"] == run_id)
            require(record["runs"][index]["status"] == "running", "The run was recovered while active; inspect its receipt.")
            record["runs"][index] = run
            self.save(state)
        return {"run":run, "status":self.status(state),
                "next_instruction":"Read results and actual artifacts; explain fields before checking understanding. Awaiting GPU is not a completed CPU/GPU comparison."}

    def results(self, name=None, task_id=None):
        state = self.load()
        current = self.current(state)
        if name:
            self.extension(name)
            record = state["extensions"].get(name, {})
        else:
            if task_id is None and current:
                task_id = current.get("evidence_task", current["id"])
            require(task_id in state["tasks"], "Choose an existing Week 2 task ID.")
            record = state["tasks"][task_id]
        require(record.get("runs"), "No recorded experiment exists for this task/topic.")
        run = record["runs"][-1]
        return {"task":run["task"], "run_id":run["id"], "status":run["status"],
                "model_sha256":run.get("model_sha256"), "commands":run["commands"],
                "instruction":"Use these recorded values and listed artifacts. Explain the schema and units; do not invent device values or reuse a different learner's run."}

    def export(self):
        result = super().export()
        state = self.load()
        lines = ["", "## Foundation refresher choices", ""]
        for concept, history in state.get("concept_choices", {}).items():
            lines.append(f"- {concept}: {history[-1]['choice']} ({len(history)} saved choices)")
        lines += ["", "## Student code attempts", ""]
        for task, record in state["tasks"].items():
            for module, drafts in record.get("code_drafts", {}).items():
                for draft in drafts:
                    lines += [f"### {task}: {module}", "", f"Saved model SHA256: {draft['sha256']}",
                              "", "Submitted code:", "", "```python", english_display(draft["submitted_text"]), "```", "",
                              "Before-file: " + draft["backup"], ""]
        path = Path(result["report"])
        atomic_text(path, path.read_text(encoding="utf-8") + "\n".join(lines) + "\n")
        return result
