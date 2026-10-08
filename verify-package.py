"""Read-only integrity check for an extracted seminar distribution."""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
COMMANDS = {"menu.md", "start.md", "status.md", "review.md", "help.md"}


def package_files(root):
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in {".git", "__pycache__"})
        if Path(base) == root:
            dirs[:] = [d for d in dirs if d != ".in_use"]
        for name in sorted(files):
            path = Path(base, name)
            if path == root / "SHA256SUMS.json" or path == root / ".git":
                continue
            yield path


def verify(root=ROOT):
    inventory = json.loads((root / "SHA256SUMS.json").read_text(encoding="utf-8"))
    expected = inventory["files"]
    actual = {p.relative_to(root).as_posix(): p for p in package_files(root)}
    errors = []
    for name in sorted(set(expected) - set(actual)):
        errors.append("Missing: " + name)
    for name in sorted(set(actual) - set(expected)):
        errors.append("Unexpected: " + name)
    for name in sorted(set(actual) & set(expected)):
        if actual[name].is_symlink() or hashlib.sha256(actual[name].read_bytes()).hexdigest() != expected[name]:
            errors.append("Changed: " + name)
    if {p.name for p in (root / "commands").glob("*.md")} != COMMANDS:
        errors.append("Expected exactly five commands: menu, start, status, review, help.")
    manifest = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    if manifest.get("version") != inventory["version"]:
        errors.append("Plugin version differs from the inventory.")
    return errors


if __name__ == "__main__":
    try:
        problems = verify()
    except (OSError, ValueError, KeyError) as exc:
        problems = ["Cannot verify this package: " + str(exc)]
    for problem in problems:
        print(problem)
    print("FAIL: package is incomplete or changed." if problems else
          "PASS: all package hashes, manifests and five commands are intact.")
    sys.exit(1 if problems else 0)
