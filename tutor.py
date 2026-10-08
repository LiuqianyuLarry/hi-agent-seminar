"""Local, dependency-free seminar progress and supervised experiment runner."""
from __future__ import annotations

import argparse
import ast
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parent
SCHEMA = 2
# Permanent storage namespace, NOT the plugin release number. Never bump on update.
PROGRESS_NAMESPACE = "v2"
REVIEW_QUESTIONS = {
    "r1": "Explain one main idea from this seminar in your own words. Use a result from a recorded task.",
    "r2": "What surprised you in an experiment, and what did the actual output show?",
    "r3": "What is still unclear, and what would you try or ask next?",
}
EXCLUDED = {".git", ".venv", "node_modules", "__pycache__", "outputs", "tests"}


def english_display(value):
    text = str(value)
    if re.search(r"[\u3400-\u9fff]", text):
        return "[Learner text is saved in the local record and is not repeated in this English report.]"
    return redact(text)


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resource_files(root):
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED and not d.startswith(".")
                         and Path(base, d).resolve().is_relative_to(root.resolve())
                         and not Path(base, d).is_symlink())
        for name in sorted(files):
            path = Path(base, name)
            if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
                continue
            if name.lower().startswith(".env") or name.lower() in {"reference.md", "lesson.json", "progress.json", "credentials.json", "secrets.json"}:
                continue
            if path.suffix.lower() in {".py", ".md", ".txt", ".json"}:
                yield path


def catalog(workspace, root=ROOT):
    courses = []
    weeks = {p.parent.name for p in Path(root).glob("week[0-9][0-9]/lesson.json")}
    weeks.update(p.parent.name for p in (Path(workspace) / ".hi-agent-seminar" / PROGRESS_NAMESPACE).glob("week[0-9][0-9]/progress.json"))
    weeks.update(p.parent.name for p in (Path(workspace) / ".hi-agent-seminar").glob("week[0-9][0-9]/progress.json"))
    for week in sorted(weeks):
        try:
            seminar = Seminar(workspace, week, root=root)
        except ValueError as exc:
            courses.append({"id":week, "title":week, "started":False,
                            "core_percent":None, "updated_at":"", "error":str(exc),
                            "optional_practice_ready":False, "optional_topics":[]})
            continue
        lesson = seminar.lesson
        entry = {"id":lesson["id"], "title":lesson["title"], "minutes":sum(t["minutes"] for t in lesson["tasks"]),
                 "started":False, "core_percent":0, "updated_at":"",
                 "optional_practice_ready":False, "optional_topics":[]}
        state = None
        if seminar.path.is_file():
            try:
                state = seminar.load()
                summary = seminar.status(state)
                entry.update(started=True, core_percent=summary["core_percent"],
                             current_task=summary["current_task"], updated_at=state["updated_at"])
            except ValueError as exc:
                state = None
                entry["error"] = str(exc)
        elif seminar.legacy_path.is_file():
            entry["error"] = "Older learning records exist. They were preserved; request a compatible migration before starting."
            entry["core_percent"] = None
        if state is not None:
            env = state["environment"]
            entry["optional_practice_ready"] = bool(
                env.get("status") == "ready" and env.get("key_configured")
                and Path(env.get("python", "")).is_file())
        for topic in lesson.get("extensions", []):
            record = state["extensions"].get(topic["id"], {}) if state is not None else {}
            runs = record.get("runs", [])
            latest = runs[-1] if runs else None
            discussed = bool(latest and any(e.get("run_id") == latest["id"]
                                           for e in record.get("explanations", [])))
            status = "Not started"
            if "error" in entry:
                status = "Progress unavailable"
            elif latest:
                status = {"running":"Run pending", "failed":"Run failed",
                          "interrupted":"Run interrupted"}.get(latest["status"], "Inspect saved run")
                if latest["status"] == "success":
                    status = "Discussed" if discussed else "Awaiting explanation"
            entry["optional_topics"].append({
                "id":topic["id"], "title":topic["title"], "purpose":topic["purpose"],
                "planned_calls":topic["planned_calls"], "learning_status":status,
                "latest_run_id":latest["id"] if latest else None,
                "run_count":len(runs), "core_progress_unchanged":True})
        courses.append(entry)
    started = sorted((c for c in courses if c["started"]), key=lambda c:c["updated_at"], reverse=True)
    current = next((c for c in started if c["core_percent"] < 100), started[0] if started else None)
    return {"courses":courses, "active_week":current["id"] if current else None}


def now():
    return datetime.now(timezone.utc).isoformat()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def child(root, *parts):
    result = root.joinpath(*parts).resolve()
    require(result.is_relative_to(root.resolve()), "Path leaves its expected directory.")
    return result


def clean_text(value):
    value = str(value).strip()
    require(0 < len(value) <= 20000, "Provide 1-20000 characters of non-secret text.")
    require(not re.search(r"sk-[A-Za-z0-9_-]{12,}|(?:API_KEY|api_key)\s*[=:]\s*\S+", value),
            "Possible API key rejected. Keep credentials out of learning records.")
    return value


def redact(value):
    text = re.sub(r"sk-[A-Za-z0-9_-]{12,}", "[REDACTED_KEY]", str(value))
    text = re.sub(r"(https?://)[^\s/@]+:[^\s/@]+@", r"\1[REDACTED]@", text)
    text = re.sub(r"(?i)(Bearer\s+)\S+", r"\1[REDACTED]", text)
    text = re.sub(r"-----BEGIN [^-]*PRIVATE KEY-----[\s\S]*?-----END [^-]*PRIVATE KEY-----", "[REDACTED_PRIVATE_KEY]", text)
    return re.sub(r'''(?im)((?:api[_-]?key|token|password|secret)\s*[=:]\s*)["']([^"'\r\n]{8,})["']''', r'\1"[REDACTED]"', text)


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".save-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class Seminar:
    def __init__(self, workspace, week="week01", root=ROOT):
        require(re.fullmatch(r"week\d{2}", week), "Use a week ID such as week01.")
        self.root = Path(root).resolve()
        self.workspace = Path(workspace).expanduser().resolve()
        require(self.workspace.is_dir(), "The student workspace must already exist.")
        require(not self.workspace.is_relative_to(self.root), "Choose a student workspace outside the plugin.")
        self.week = week
        self.base = child(self.workspace, ".hi-agent-seminar", PROGRESS_NAMESPACE, week)
        self.path = child(self.base, "progress.json")
        self.legacy_path = child(self.workspace, ".hi-agent-seminar", week, "progress.json")
        self.snapshot = child(self.base, "lesson.snapshot.json")
        self.resources = child(self.workspace, "hi-agent-seminar-work", PROGRESS_NAMESPACE, week, "resources")
        lesson_path = child(self.root, week, "lesson.json")
        if self.path.is_file() and self.snapshot.is_file():
            lesson_path = self.snapshot
        require(lesson_path.is_file(), f"{week} is not available yet. No progress was changed.")
        try:
            self.lesson = json.loads(lesson_path.read_text(encoding="utf-8"))
            require(isinstance(self.lesson, dict) and isinstance(self.lesson.get("tasks"), list)
                    and all(isinstance(t, dict) and "id" in t and isinstance(t.get("weight"), (int, float))
                            for t in self.lesson["tasks"]) and "version" in self.lesson and "id" in self.lesson,
                    "Invalid lesson snapshot or course definition. No progress was reset.")
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("Lesson snapshot or course definition is unreadable. Preserve it for recovery; no progress was reset.") from exc
        require(self.lesson["id"] == week, "Lesson ID mismatch.")
        tasks = self.lesson["tasks"]
        require(sum(t["weight"] for t in tasks) == 100, "Core weights must sum to 100.")
        require(len({t["id"] for t in tasks}) == len(tasks), "Duplicate task IDs.")

    def preserve_course(self):
        # Called under the progress lock. Existing snapshots and student code stay intact.
        if not self.snapshot.exists():
            atomic_json(self.snapshot, self.lesson)
        guide = child(self.base, "TEACHING.snapshot.md")
        source = child(self.root, self.week, "TEACHING.md")
        definition = child(self.root, self.week, "lesson.json")
        if not guide.exists() and source.is_file() and definition.is_file():
            try:
                matches = json.loads(definition.read_text(encoding="utf-8")) == self.lesson
            except (OSError, ValueError):
                matches = False
            if matches:
                shutil.copy2(source, guide)

    def teaching_guide(self):
        saved = child(self.base, "TEACHING.snapshot.md")
        return str(saved) if saved.is_file() else None

    @contextmanager
    def lock(self):
        self.base.mkdir(parents=True, exist_ok=True)
        lockpath = child(self.base, "progress.lock")
        try:
            fd = os.open(lockpath, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            raise ValueError("Progress is locked. Wait for the other helper. If it crashed, confirm it stopped before removing only progress.lock.")
        try:
            with os.fdopen(fd, "w") as stream:
                stream.write(str(os.getpid()))
            yield
        finally:
            lockpath.unlink(missing_ok=True)

    def load(self):
        require(self.path.is_file(), "No saved progress. Use start first.")
        try:
            state = json.loads(self.path.read_text(encoding="utf-8"))
            require(state["schema_version"] == SCHEMA and state["lesson_version"] == self.lesson["version"],
                    "Saved record format or lesson version is incompatible. Records were NOT reset. Restore the matching lesson snapshot or request a migration; do not create replacement progress.")
            require(state["week"] == self.week and set(state["tasks"]) == {t["id"] for t in self.lesson["tasks"]},
                    "Saved task list differs from this lesson.")
            require(all(isinstance(s["complete"], bool) and isinstance(s["answers"], dict)
                        and isinstance(s["runs"], list) for s in state["tasks"].values()), "Invalid saved tasks.")
            require(isinstance(state["extensions"], dict) and isinstance(state["notes"], list), "Invalid saved records.")
            return state
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ValueError("Saved progress is unreadable. It was NOT reset. Preserve progress.json and progress.backup.json for recovery.") from exc

    def save(self, state):
        # Validate/read before taking a backup: never replace a corrupt file silently.
        if self.path.exists():
            previous = self.load()
            atomic_json(child(self.base, "progress.backup.json"), previous)
        state["updated_at"] = now()
        atomic_json(self.path, state)

    def start(self):
        with self.lock():
            if self.path.exists():
                state = self.load()
                require(self.resources.is_dir(), "Progress exists but resources are missing. Restore the student workspace; do not reset progress.")
                self.preserve_course()
                return self.status(state)
            require(not self.legacy_path.is_file(),
                    "Older learning records exist. They were NOT reset or replaced. Request a compatible migration before starting.")
            require(not self.snapshot.exists(),
                    "A course snapshot exists without progress. Preserve the workspace and recover its records; do not start over.")
            require(not self.resources.exists() or (self.resources.is_dir() and not any(p.is_file() or p.is_symlink() for p in self.resources.rglob("*"))),
                    "Student files exist without progress. Use a new workspace; these files were not overwritten.")
            source = child(self.root, self.week, "resources")
            require(source.is_dir(), "This lesson has no resource pack.")
            files = list(resource_files(source))
            require(files, "Resource pack is empty.")
            self.resources.parent.mkdir(parents=True, exist_ok=True)
            ignore = child(self.base, ".gitignore")
            if not ignore.exists():
                ignore.write_text("*\n", encoding="utf-8")
            self.resources.mkdir(parents=True, exist_ok=True)
            for source_file in files:
                target = child(self.resources, str(source_file.relative_to(source)))
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, target)
            child(self.resources, ".gitignore").write_text(".env\n.venv/\n__pycache__/\noutputs/\n", encoding="utf-8")
            state = {"schema_version": SCHEMA, "lesson_version": self.lesson["version"], "week": self.week,
                     "started_at": now(), "tasks": {}, "extensions": {}, "notes": [],
                     "environment": {}, "review_draft": {}, "reviews": []}
            for task in self.lesson["tasks"]:
                state["tasks"][task["id"]] = {"complete": False, "predictions": [], "runs": [],
                                               "explanations": [], "answers": {}, "teaching":[], "prompt_drafts":[]}
            self.preserve_course()
            self.save(state)
            return self.status(state)

    def current(self, state):
        return next((t for t in self.lesson["tasks"] if not state["tasks"][t["id"]]["complete"]), None)

    def missing(self, task, record):
        result = []
        if task.get("requires_teaching") and not record["teaching"]:
            result.append("explain the terms and code before questioning")
        if task.get("requires_setup"):
            env = self.load()["environment"]
            if env.get("status") != "ready":
                result.append("Mentor prepares and verifies the local venv")
            if not env.get("key_configured"):
                result.append("student configures the key in their own terminal")
        if task.get("requires_prediction", True) and not record["predictions"]:
            result.append("student prediction")
        if task.get("requires_prompt"):
            prompt = child(self.resources, "student", "instructions.txt")
            drafts = record["prompt_drafts"]
            if not drafts or not prompt.is_file() or drafts[-1]["sha256"] != fingerprint(prompt):
                result.append("save the student's chat prompt")
            elif record["runs"] and record["runs"][-1].get("prompt_sha256") != drafts[-1]["sha256"]:
                result.append("run the comparison with the current saved prompt")
        if task["commands"]:
            if not record["runs"] or record["runs"][-1]["status"] != "success":
                result.append("successful experiment execution (not a claim that its report is true)")
        latest_id = record["runs"][-1]["id"] if record["runs"] else None
        if not record["explanations"] or record["explanations"][-1]["run_id"] != latest_id:
            result.append("explanation of actual output structure")
        for q in task["questions"]:
            attempts = record["answers"].get(q["id"], [])
            if not attempts or attempts[-1].get("verdict") != "pass" or attempts[-1].get("run_id") != latest_id:
                result.append("understanding check: " + q["id"])
        return result

    def status(self, state=None):
        state = state or self.load()
        current = self.current(state)
        percent = sum(t["weight"] for t in self.lesson["tasks"] if state["tasks"][t["id"]]["complete"])
        all_runs = [r for t in state["tasks"].values() for r in t["runs"]]
        all_runs += [r for t in state["extensions"].values() for r in t["runs"]]
        missing = self.missing(current, state["tasks"][current["id"]]) if current else []
        return {"week": self.week, "title": self.lesson["title"], "core_percent": percent,
                "current_task": current["id"] if current else None,
                "task_number": self.lesson["tasks"].index(current) + 1 if current else len(self.lesson["tasks"]),
                "total_tasks": len(self.lesson["tasks"]), "next": missing[0] if missing else ("complete task" if current else "export review or choose an extension"),
                "remaining_requirements": missing, "completed_tasks": [k for k,v in state["tasks"].items() if v["complete"]],
                "running": [r for r in all_runs if r["status"] == "running"],
                "recent_runs": sorted(all_runs, key=lambda r: r["started_at"])[-3:],
                "extensions": state["extensions"], "last_note": state["notes"][-1] if state["notes"] else None,
                "environment":state["environment"], "review_count":len(state["reviews"]),
                "progress_file": str(self.path), "resource_directory": str(self.resources),
                "lesson_version":self.lesson["version"], "lesson_snapshot":str(self.snapshot),
                "teaching_guide":self.teaching_guide()}

    def task(self):
        state = self.load()
        task = self.current(state)
        if task is None:
            return self.status(state)
        public = json.loads(json.dumps(task))
        for question in public["questions"]:
            for key in ("correct", "rubric", "feedback"):
                question.pop(key, None)
        return {"status": self.status(state), "task": public, "saved_task": state["tasks"][task["id"]]}

    def question(self, task, qid):
        found = next((q for q in task["questions"] if q["id"] == qid), None)
        require(found is not None, "Question does not belong to the current task.")
        return found

    def code(self, name=None):
        state = self.load()
        task = self.extension(name) if name else self.current(state)
        require(task is not None, "Core complete. Select an optional topic.")
        snippets = []
        for filename, symbol in task.get("code_refs", []):
            path = child(self.resources, filename)
            require(path.is_file(), "Teaching source is missing: " + filename)
            lines = path.read_text(encoding="utf-8").splitlines()
            start, end = 1, len(lines)
            if symbol:
                nodes = [n for n in ast.parse("\n".join(lines)).body if getattr(n, "name", None) == symbol]
                require(nodes, f"Source symbol {symbol} was not found in {filename}. Read the edited file before teaching it.")
                start, end = nodes[0].lineno, nodes[0].end_lineno
            # Keep full source location, while limiting a single displayed excerpt.
            shown_end = min(end, start + 54)
            snippets.append({"file":filename, "absolute_path":str(path), "start_line":start,
                             "end_line":shown_end, "symbol_end_line":end,
                             "numbered_code":"\n".join(f"{n}: {lines[n-1]}" for n in range(start, shown_end+1))})
        return {"task":task["id"], "terms":task.get("terms", {}), "snippets":snippets,
                "note":"Read this code before running it. Show the relevant numbered snippets and define terms before asking the prediction."}

    def setup(self, interpreter=sys.executable):
        interpreter = str(Path(interpreter).resolve())
        require(Path(interpreter).is_file(), "Python interpreter was not found.")
        with self.lock():
            state = self.load()
            task = self.current(state)
            require(task and task.get("requires_setup"), "Setup belongs to the current setup task.")
            require(state["tasks"][task["id"]]["teaching"], "Explain the setup purpose first.")
            require(state["environment"].get("status") != "running", "Setup is already running; wait or inspect the interrupted process.")
            venv = child(self.resources, ".venv")
            python = child(venv, "Scripts", "python.exe") if os.name == "nt" else child(venv, "bin") / "python"
            # POSIX venv executables are normally symlinks: use the lexical path for execution.
            if os.name != "nt":
                python = venv / "bin" / "python"
            existing = state["environment"]
            if existing.get("status") == "ready" and python.is_file():
                return {"environment":existing, "status":self.status(state)}
            run_id = uuid.uuid4().hex
            folder = child(self.base, "setup", run_id)
            folder.mkdir(parents=True)
            env = {"status":"running", "started_at":now(), "helper_pid":os.getpid(), "id":run_id,
                   "python":str(python), "key_configured":False, "steps":[]}
            state["environment"] = env
            self.save(state)
        check = ("import sys,json,openai,pydantic,dotenv; "
                 "assert sys.version_info >= (3,11); assert sys.prefix != sys.base_prefix; "
                 "print('Imports OK'); print(json.dumps({'python':sys.executable,'prefix':sys.prefix,'version':sys.version.split()[0]}))")
        commands = [("Create virtual environment", [interpreter, "-m", "venv", str(venv)]),
                    ("Install course packages", [str(python), "-m", "pip", "install", "--disable-pip-version-check", "-r", str(child(self.resources, "requirements.txt"))]),
                    ("Check imports in the course environment", [str(python), "-X", "utf8", "-c", check])]
        try:
            for number, (label, command) in enumerate(commands, 1):
                result = subprocess.run(command, cwd=self.resources, capture_output=True, text=True,
                                        encoding="utf-8", errors="replace", timeout=300, check=False)
                output = redact(result.stdout + result.stderr)
                log = child(folder, f"step{number}.txt")
                log.write_text(output, encoding="utf-8")
                env["steps"].append({"step":label, "returncode":result.returncode, "log":str(log), "summary":output[-2500:]})
                if result.returncode:
                    break
            env["status"] = "ready" if len(env["steps"]) == 3 and all(s["returncode"] == 0 for s in env["steps"]) else "failed"
        except (OSError, subprocess.TimeoutExpired) as exc:
            env.update(status="failed", error=redact(str(exc)))
        env["finished_at"] = now()
        env["configure_command"] = ("& " if os.name == "nt" else "") + f'"{python}" "{child(self.resources, "configure.py")}"'
        with self.lock():
            state = self.load()
            require(state["environment"].get("id") == run_id and state["environment"].get("status") == "running", "Setup state changed while the process was active.")
            state["environment"] = env
            self.save(state)
        return {"environment":env, "status":self.status(state)}

    def write_prompt(self, text):
        text = clean_text(text)
        require(not re.search(r"[\u3400-\u9fff]", text), "Please write the experiment prompt in English. Ask Mentor Liu for a hint if needed.")
        require(not any(marker in text for marker in ("[STUDENT_TASK", "[EVIDENCE_RULE", "[OUTPUT_STRUCTURE", "TODO")),
                "Replace the scaffold placeholders with the student's own prompt first.")
        with self.lock():
            state = self.load()
            task = self.current(state)
            require(task and task.get("requires_prompt"), "Chat prompt saving belongs to the prompt task.")
            record = state["tasks"][task["id"]]
            require(record["teaching"], "Explain the prompt task and show the current file before asking the student to write it.")
            require(not any(r["status"] == "running" for t in [*state["tasks"].values(), *state["extensions"].values()] for r in t["runs"]), "Wait for the active run before changing the prompt.")
            path = child(self.resources, "student", "instructions.txt")
            path.parent.mkdir(parents=True, exist_ok=True)
            draft = {"at":now(), "text":text, "origin":"student_chat", "previous_text":path.read_text(encoding="utf-8") if path.exists() else ""}
            path.write_text(text + "\n", encoding="utf-8")
            draft["sha256"] = fingerprint(path)
            record["prompt_drafts"].append(draft)
            self.save(state)
            return {"saved_file":str(path), "saved_text":text, "status":self.status(state)}

    def review_questions(self):
        state = self.load()
        return {"questions":[{"id":key, "prompt":value, "saved_answer":state["review_draft"].get(key)} for key,value in REVIEW_QUESTIONS.items()],
                "instruction":"Ask in ordinary chat, one at a time. Let the student type their own reflection.", "status":self.status(state)}

    def review(self):
        with self.lock():
            state = self.load()
            require(all(key in state["review_draft"] for key in REVIEW_QUESTIONS), "Collect the three student reflections before saving the review.")
            snapshot, remaining = [], 100000
            for path in resource_files(self.resources):
                if remaining <= 0:
                    break
                if path.suffix not in (".py", ".txt", ".json", ".md"):
                    continue
                relative = path.relative_to(self.resources).as_posix()
                with path.open("rb") as stream:
                    raw = stream.read(min(20000, remaining) + 1)
                limit = min(20000, remaining)
                shortened = len(raw) > limit
                safe = redact(raw[:limit].decode("utf-8", errors="replace"))
                snapshot.append({"file":relative, "text":safe, "truncated":shortened})
                remaining -= min(len(raw), limit)
            review_id = uuid.uuid4().hex
            folder = child(self.base, "reviews", review_id)
            folder.mkdir(parents=True)
            payload = {"id":review_id, "at":now(), "week":self.week,
                       "core_percent":self.status(state)["core_percent"], "reflections":state["review_draft"], "code_snapshot":snapshot}
            atomic_json(child(folder, "review.json"), payload)
            lines = [f"# Seminar {self.week}: reflection and code review", "", f"Core completion: {payload['core_percent']}%", "", "Saved locally. No submission service was contacted.", ""]
            for key, question in REVIEW_QUESTIONS.items():
                lines += ["## " + question, "", english_display(state["review_draft"][key]["answer"]), ""]
            lines += ["## Source snapshot", "", "At most 20 KB per file and 100 KB of source in total. Credentials, environments, tests and generated output are excluded.", ""]
            for item in snapshot:
                text = english_display(item["text"])
                fence = "`" * max(3, max((len(m.group(0))+1 for m in re.finditer(r"`+", text)), default=3))
                lines += ["### " + item["file"], "", fence, text, fence, "", "[Truncated]" if item["truncated"] else ""]
            target = child(folder, "review.md")
            target.write_text("\n".join(lines), encoding="utf-8")
            state["reviews"].append({"id":review_id, "at":payload["at"], "report":str(target)})
            state["review_draft"] = {}
            self.save(state)
            return {"report":str(target), "snapshot_files":len(snapshot), "status":self.status(state)}

    def mutate(self, action, text="", question=None, verdict=None, run_id=None, name=None):
        text = clean_text(text) if action != "complete" else ""
        with self.lock():
            state = self.load()
            task = self.current(state)
            extra = {}
            if action == "save":
                state["notes"].append({"at": now(), "text": text})
            elif action == "key-ready":
                require(task and task.get("requires_setup"), "Key setup belongs to Task01.")
                require(state["environment"].get("status") == "ready", "Finish the venv setup and import check first.")
                require(child(self.resources, ".env").is_file(), "The local .env file does not exist yet. Run configure.py in your own terminal.")
                state["environment"].update(key_configured=True, key_confirmed_at=now(), key_note=text)
            elif action == "review-answer":
                require(question in REVIEW_QUESTIONS, "Choose reflection r1, r2 or r3.")
                state["review_draft"][question] = {"question":REVIEW_QUESTIONS[question], "answer":text, "at":now()}
            elif action == "recover":
                if state["environment"].get("id") == run_id and state["environment"].get("status") == "running":
                    state["environment"].update(status="interrupted", finished_at=now(), recovery_note=text)
                    self.save(state)
                    return {"status":self.status(state)}
                runs = [r for v in [*state["tasks"].values(), *state["extensions"].values()] for r in v["runs"]]
                run = next((r for r in runs if r["id"] == run_id), None)
                require(run and run["status"] == "running", "No such pending run.")
                run.update(status="interrupted", finished_at=now(), recovery_note=text)
            elif action == "explain-extension":
                record = state["extensions"].get(name)
                require(record and record["runs"] and record["runs"][-1]["status"] != "running", "Run this extension first; wait if still running.")
                record["explanations"].append({"at":now(), "run_id":record["runs"][-1]["id"], "text":text})
            else:
                require(task is not None, "Core is already complete. Use an optional extension.")
                record = state["tasks"][task["id"]]
                latest_id = record["runs"][-1]["id"] if record["runs"] else None
                if action == "teach":
                    record["teaching"].append({"at":now(), "text":text})
                elif action == "predict":
                    require(task.get("requires_prediction", True), "This setup task has no prediction question.")
                    require(record["teaching"], "Explain the terms and code before asking a prediction.")
                    require(not task.get("requires_prompt") or record["prompt_drafts"], "Save the student's chat prompt before asking this task's prediction.")
                    record["predictions"].append({"at": now(), "text": text})
                elif action == "explain":
                    require(record["teaching"], "Present the task preparation first.")
                    require(not task.get("requires_prediction", True) or record["predictions"], "Record the student's prediction first.")
                    require(not task["commands"] or (record["runs"] and record["runs"][-1]["status"] != "running"), "Run the task first, then inspect and explain its actual output.")
                    record["explanations"].append({"at":now(), "run_id":latest_id, "text":text})
                elif action == "answer":
                    require(record["explanations"] and record["explanations"][-1]["run_id"] == latest_id,
                            "Explain the current task output before checking understanding.")
                    q = self.question(task, question)
                    attempt = {"at":now(), "student_answer":text, "run_id":latest_id}
                    if q["type"] == "mcq":
                        choice = text.upper().strip()
                        require(choice in q["options"], "Submit one listed option letter.")
                        attempt.update(verdict="pass" if choice == q["correct"] else "retry", feedback=q["feedback"], assessor="deterministic-choice-check")
                        extra["feedback"] = attempt["feedback"]
                    else:
                        attempt.update(verdict="pending", assessor="mentor-pending")
                        extra["mentor_rubric"] = q["rubric"]
                    record["answers"].setdefault(question, []).append(attempt)
                    extra["attempt"] = attempt
                elif action == "assess":
                    q = self.question(task, question)
                    require(q["type"] == "open", "Multiple-choice answers are checked automatically.")
                    attempts = record["answers"].get(question, [])
                    require(attempts and attempts[-1]["verdict"] == "pending" and attempts[-1]["run_id"] == latest_id,
                            "Submit a new student answer before mentor assessment.")
                    require(verdict in ("pass", "retry"), "Use pass or retry.")
                    attempts[-1].update(verdict=verdict, feedback=text, assessor="mentor-rubric-review", assessed_at=now())
                elif action == "complete":
                    gaps = self.missing(task, record)
                    require(not gaps, "Cannot complete: " + "; ".join(gaps))
                    record.update(complete=True, completed_at=now())
                else:
                    raise ValueError("Unknown state action.")
            self.save(state)
            return {"status":self.status(state), **extra}

    def extension(self, name=None):
        choices = self.lesson.get("extensions", [])
        if name is None:
            return {"extensions": choices, "core_progress_unchanged": True}
        item = next((e for e in choices if e["id"] == name), None)
        require(item is not None, "Unknown extension. List extensions first.")
        return item

    def run(self, interpreter, intro, name=None, prediction=None):
        intro = clean_text(intro)
        with self.lock():
            state = self.load()
            env = state["environment"]
            require(env.get("status") == "ready" and env.get("key_configured"), "Complete the local environment and private key setup first.")
            interpreter = str(Path(interpreter or env["python"]).expanduser().absolute())
            require(Path(interpreter) == Path(env["python"]), "Use the verified course venv interpreter, not global Python.")
            require(Path(interpreter).is_file(), "The saved venv interpreter is missing. Restore the environment before running.")
            if name:
                task = self.extension(name)
                prediction = clean_text(prediction or "")
                record = state["extensions"].setdefault(name, {"runs":[], "explanations":[]})
            else:
                task = self.current(state)
                require(task is not None, "Core is complete.")
                record = state["tasks"][task["id"]]
                require(record["teaching"], "Explain the terms and code before the experiment.")
                require(record["predictions"], "Ask for and record the student's prediction before running.")
                prediction = record["predictions"][-1]["text"]
                if task.get("requires_prompt"):
                    drafts = record["prompt_drafts"]
                    prompt = child(self.resources, "student", "instructions.txt")
                    require(drafts and prompt.is_file() and fingerprint(prompt) == drafts[-1]["sha256"], "Save the student's chat prompt with write-prompt before running.")
            require(task["commands"], "This is a discussion/setup task. No experiment is needed.")
            require(not any(r["status"] == "running" for s in [*state["tasks"].values(), *state["extensions"].values()] for r in s["runs"]),
                    "A run is pending. Inspect it before starting another.")
            run_id = uuid.uuid4().hex
            folder = child(self.base, "runs", run_id)
            folder.mkdir(parents=True)
            run = {"id":run_id, "task":task["id"], "status":"running", "started_at":now(), "helper_pid":os.getpid(),
                   "intro":intro, "prediction":prediction, "planned_calls":task["planned_calls"], "commands":[], "folder":str(folder)}
            if task.get("requires_prompt"):
                run["prompt_sha256"] = record["prompt_drafts"][-1]["sha256"]
                run["student_prompt"] = record["prompt_drafts"][-1]["text"]
            record["runs"].append(run)
            self.save(state)
        try:
            for index, arguments in enumerate(task["commands"], 1):
                script = child(self.resources, arguments[0])
                require(script.name in ("week1_demo.py", "preview_agent.py") and script.is_file(), "Unapproved experiment script.")
                out = child(folder, f"command{index:02d}")
                out.mkdir()
                command = [interpreter, "-X", "utf8", str(script), *arguments[1:], "--output-dir", str(out)]
                try:
                    result = subprocess.run(command, cwd=self.resources, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                            text=True, encoding="utf-8", errors="replace", timeout=360, check=False)
                    code, output = result.returncode, result.stdout
                except subprocess.TimeoutExpired as exc:
                    code, output = 124, exc.stdout or ""
                    if isinstance(output, bytes):
                        output = output.decode("utf-8", errors="replace")
                    output += "\nStopped: the 360-second command limit was reached. No success was assumed."
                log = child(out, "stdout.txt")
                log.write_text(redact(output), encoding="utf-8")
                artifacts = sorted(str(p) for p in out.rglob("*") if p.is_file() and p.suffix in (".json", ".csv"))
                run["commands"].append({"arguments":arguments, "returncode":code, "stdout":str(log), "artifacts":artifacts})
                if code != 0:
                    break
            run["status"] = "success" if len(run["commands"]) == len(task["commands"]) and all(c["returncode"] == 0 for c in run["commands"]) else "failed"
        except Exception as exc:
            run.update(status="failed", error=redact(f"{type(exc).__name__}: {exc}"))
        run["finished_at"] = now()
        atomic_json(child(folder, "receipt.json"), run)
        with self.lock():
            state = self.load()
            record = state["extensions"][name] if name else state["tasks"][task["id"]]
            index = next(i for i,r in enumerate(record["runs"]) if r["id"] == run_id)
            require(record["runs"][index]["status"] == "running", "Run was recovered while still active. Inspect its receipt before continuing.")
            record["runs"][index] = run
            self.save(state)
        return {"run":run, "status":self.status(state), "next_instruction":"Read the actual artifacts, explain their structure, then record explain (or explain-extension)."}

    def results(self, name=None):
        state = self.load()
        task = self.extension(name) if name else self.current(state)
        require(task is not None, "Select an active task or optional topic.")
        record = state["extensions"].get(name) if name else state["tasks"][task["id"]]
        require(record and record["runs"], "This task has no recorded experiment yet.")
        run = record["runs"][-1]
        result = {"task":task["id"], "run_id":run["id"], "status":run["status"], "artifacts":[], "token_table":[], "checks_table":[], "case_table":[]}
        for command in run["commands"]:
            result["artifacts"].append({"stdout":command["stdout"], "files":command["artifacts"]})
            for filename in command["artifacts"]:
                path = child(self.base, str(Path(filename).relative_to(self.base)))
                if path.suffix != ".json" or path.stat().st_size > 1000000:
                    continue
                data = json.loads(path.read_text(encoding="utf-8"))
                if path.name.startswith("prompt_"):
                    for item in data.get("runs", []):
                        meta = item.get("metadata", {})
                        usage = meta.get("usage") or {}
                        result["token_table"].append({"label":item["label"], **{k:usage.get(k) for k in ("prompt_tokens", "completion_tokens", "total_tokens")}, "elapsed_seconds":meta.get("elapsed_seconds"), "file":filename})
                if path.name.startswith("validation_"):
                    for label, checks in data.get("checks", {}).items():
                        result["checks_table"].append({"sample":label, "origin":"actual model response" if label == "actual_baseline" else "deliberately altered teaching sample", **checks})
                if path.name.startswith("failures_"):
                    result["repair_summary"] = {key:data.get(key) for key in ("mutation_origin", "damaged_output", "actual_repair", "repair_check", "unsupported_mutation_check")}
                if path.name.startswith("seminar_case_"):
                    try:
                        parsed = json.loads(data["displayed_output"])
                    except (ValueError, TypeError):
                        parsed = None
                    checks = data["checks"]
                    outcome = "needs_format_repair" if not checks["valid_format"] else ("draft_for_review" if checks["evidence_check_passed"] else "needs_source_review")
                    missing = parsed.get("missing_information") if isinstance(parsed, dict) else None
                    result["case_table"].append({"case":data["case"], "missing_information":missing,
                                                "missing_count":len(missing) if isinstance(missing, list) else None,
                                                "diagnosis":parsed.get("diagnosis") if isinstance(parsed, dict) else "Unparseable report",
                                                "valid_format":checks["valid_format"], "source_checks":checks["evidence_check_passed"],
                                                "Outcome":outcome, "origin":data["origin"], "file":filename})
        return result

    def export(self):
        state = self.load()
        status = self.status(state)
        lines = [f"# {self.lesson['title']}", "", f"Core completion: {status['core_percent']}%", "",
                 "Local learning record. No online submission. Mentor assessments are not automatic grading.", ""]
        for task in self.lesson["tasks"]:
            record = state["tasks"][task["id"]]
            lines += [f"## {task['id']}: {task['title']}", "", f"Complete: {record['complete']}", ""]
            for p in record["predictions"]:
                lines += ["Prediction: " + english_display(p["text"]), ""]
            for r in record["runs"]:
                lines += [f"Run {r['id']}: {r['status']} | {r['folder']}", ""]
            for e in record["explanations"]:
                lines += ["Output discussion: " + english_display(e["text"]), ""]
            for q in task["questions"]:
                lines += [q["prompt"], ""]
                for attempt in record["answers"].get(q["id"], []):
                    lines += ["Student: " + english_display(attempt["student_answer"]), "",
                              "Assessment: " + attempt["verdict"] + ". " + english_display(attempt.get("feedback", "Awaiting mentor review.")), ""]
        lines += ["## Optional extensions", ""]
        for name, record in state["extensions"].items():
            lines += [f"### {name}", ""]
            for run in record["runs"]:
                lines += [f"Run {run['id']}: {run['status']} | {run['folder']}", ""]
            for item in record["explanations"]:
                lines += [english_display(item["text"]), ""]
        lines += ["## Resume", "", "Next: " + status["next"], ""]
        if state["notes"]:
            lines += [english_display(state["notes"][-1]["text"]), ""]
        target = child(self.base, "exports", f"review-{uuid.uuid4().hex[:10]}.md")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(lines), encoding="utf-8")
        return {"report":str(target), "status":status}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["list", "start", "status", "task", "code", "teach", "predict", "setup", "key-ready", "write-prompt", "run", "results", "explain", "answer", "assess", "complete", "save", "recover", "export", "review-questions", "review-answer", "review", "extension", "run-extension", "explain-extension"])
    parser.add_argument("--workspace", default=str(Path.cwd()))
    parser.add_argument("--week")
    parser.add_argument("--text", default="")
    parser.add_argument("--input-file", type=Path)
    parser.add_argument("--question")
    parser.add_argument("--verdict", choices=["pass", "retry"])
    parser.add_argument("--run-id")
    parser.add_argument("--name")
    parser.add_argument("--intro", default="")
    parser.add_argument("--prediction", default="")
    parser.add_argument("--python")
    args = parser.parse_args()
    try:
        if args.action == "list":
            result = catalog(args.workspace)
        else:
            week = args.week or catalog(args.workspace)["active_week"] or "week01"
            seminar = Seminar(args.workspace, week)
            if args.input_file:
                require(args.input_file.suffix.lower() in (".txt", ".md") and not args.input_file.name.startswith(".env"),
                        "Use a response-only .txt or .md file, not a credential or state file.")
                require(args.input_file.stat().st_size <= 80000, "Response file is too large.")
                args.text = args.input_file.read_text(encoding="utf-8")
            if args.action in ("start", "status", "task", "export", "review"):
                result = getattr(seminar, args.action)()
            elif args.action == "review-questions":
                result = seminar.review_questions()
            elif args.action == "write-prompt":
                result = seminar.write_prompt(args.text)
            elif args.action == "setup":
                result = seminar.setup(args.python or sys.executable)
            elif args.action in ("code", "results"):
                result = getattr(seminar, args.action)(args.name)
            elif args.action == "extension":
                result = seminar.extension(args.name)
            elif args.action in ("run", "run-extension"):
                require(args.action != "run-extension" or args.name, "Choose an extension name.")
                result = seminar.run(args.python, args.intro, args.name if args.action == "run-extension" else None, args.prediction)
            else:
                result = seminar.mutate(args.action, args.text, args.question, args.verdict, args.run_id, args.name)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"error":redact(str(exc)), "progress_not_reset":True}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
