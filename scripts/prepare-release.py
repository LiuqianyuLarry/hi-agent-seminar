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
blocked = {".venv", "node_modules", "outputs", "traces", ".hi-agent-seminar", ".hi-agent-seminar-preview", "hi-agent-seminar-work", ".archive"}
errors = []
approved_binary = {"week02/resources/assets/transformer-original.png":
                   "6d82cf140193daf9e1c95baab59017754e36c2f9548cfec9db86b2bd8d7d27ed"}
approved_binary.update({'week03/slides/slide-02.png': '53839781f8fa443a790e142566be9bbd50e149593b3f3496dac3d185bc00cc73', 'week03/slides/slide-07.png': '70a33fe18a4b273a91bb78d11d287fa7948188549fd8e194f8559d2017d44d8c', 'week03/slides/slide-09.png': '7cf7c284910927df55f4313e00d00cbdab75d839a13af9eb8ccd0e12cfff7e30', 'week03/slides/slide-16.png': '3b26f495f3e3badbf9023250992fed3853e69740e944455a47c0f3cd87ce2dc8', 'week03/slides/slide-15.png': '4e56dfcbe1af0e8f71c8ed5e90d1c8259c9cf944ce6f0ddd54fa69672b7197f6', 'week03/slides/slide-08.png': 'bbe8bbf691b068eeb6fc1b6478d4e157996e093c32db00f958ddb35bd95e9316', 'week03/slides/slide-20.png': '579793f54516e6a4a7cc84003faeba37d566da2e30b2e456a9908d951c28796c', 'week03/slides/slide-31.png': '860c0de92cbb5b0fb7233e2c6dcccb866aa6b6202a48fa98d949454423762f85', 'week03/slides/slide-37.png': '4d4facb0af01ae65bf015214a8f944c64c2cf5607409d6f4c85ad7f48e2e1b9b'})
for path in files:
    relative = path.relative_to(ROOT)
    if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
        errors.append(f"Linked file: {relative}")
        continue
    if any(part in blocked for part in relative.parts) or (path.name.startswith(".env") and path.name != ".env.example") or path.name.lower() in {"credentials.json", "secrets.json"}:
        errors.append(f"Private/generated file: {relative}")
        continue
    if relative.as_posix() in approved_binary:
        if hashlib.sha256(path.read_bytes()).hexdigest() != approved_binary[relative.as_posix()]:
            errors.append(f"Supplied figure differs from reviewed source: {relative}")
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
(ROOT / "SHA256SUMS.json").write_text(json.dumps(inventory, indent=2)+"\n", encoding="utf-8", newline="\n")
problems = check.verify(ROOT)
if problems:
    raise SystemExit("\n".join(problems))
print(f"PASS: audited {len(files)} files for release {version}; refreshed SHA256SUMS.json.")
