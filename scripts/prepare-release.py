"""Audit release files and refresh the inventory; never pushes or reads credentials."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("package_check", ROOT / "verify-package.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)
files = sorted(check.package_files(ROOT))
blocked = {".venv", "node_modules", "outputs", ".hi-agent-seminar", "hi-agent-seminar-work", ".archive"}
errors = []
for path in files:
    relative = path.relative_to(ROOT)
    if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
        errors.append(f"Linked file: {relative}")
        continue
    if any(part in blocked for part in relative.parts) or (path.name.startswith(".env") and path.name != ".env.example") or path.name.lower() in {"credentials.json", "secrets.json"}:
        errors.append(f"Private/generated file: {relative}")
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeError, OSError):
        errors.append(f"Review non-text file before release: {relative}")
        continue
    if any("\u3400" <= c <= "\u9fff" for c in text):
        errors.append(f"Non-English presentation text: {relative}")
    if re.search(r"(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)", text):
        errors.append(f"Possible secret: {relative}")
    if path.suffix == ".py":
        ast.parse(text, filename=str(relative))
    elif path.suffix == ".json":
        json.loads(text)
if {p.name for p in (ROOT / "commands").glob("*.md")} != check.COMMANDS:
    errors.append("The release must contain exactly five commands.")
if errors:
    raise SystemExit("\n".join(errors))
version = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
inventory = {"version":version, "files":{
    p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(ROOT / "SHA256SUMS.json").write_text(json.dumps(inventory, indent=2)+"\n", encoding="utf-8")
problems = check.verify(ROOT)
if problems:
    raise SystemExit("\n".join(problems))
print(f"PASS: audited {len(files)} files for release {version}; refreshed SHA256SUMS.json.")
