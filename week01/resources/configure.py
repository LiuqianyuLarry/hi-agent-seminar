"""Save one required DeepSeek key locally. No API request is made here."""
import getpass
import json
import re
import sys
import warnings
from pathlib import Path
from lesson_core import ROOT, LessonError

def save_key(key: str, path: Path) -> None:
    key = key.strip()
    if not key or any(ch.isspace() for ch in key):
        raise LessonError("Enter a non-empty key without spaces or line breaks.")
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    line = "DEEPSEEK_API_KEY=" + json.dumps(key) + "\n"
    if re.search(r"^DEEPSEEK_API_KEY=", existing, flags=re.M):
        updated = re.sub(r"^DEEPSEEK_API_KEY=.*(?:\n|$)", lambda m: line, existing, flags=re.M)
    else:
        updated = existing.rstrip() + ("\n" if existing.strip() else "") + line
    path.write_text(updated, encoding="utf-8")

def main() -> int:
    if not sys.stdin.isatty():
        print("Use an interactive terminal for hidden input, or fill DEEPSEEK_API_KEY in a local .env file.", file=sys.stderr)
        return 1
    print("Your key will be saved locally in .env. Do not submit that file.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            key = getpass.getpass("DeepSeek API key (hidden): ")
        save_key(key, ROOT / ".env")
    except (LessonError, OSError, getpass.GetPassWarning, EOFError) as exc:
        print("Configuration stopped; use a terminal with hidden input or edit .env locally.", file=sys.stderr)
        return 1
    print("Key saved. Model and API address are already configured.")
    print("Next: python first_call.py")
    return 0

if __name__ == "__main__": raise SystemExit(main())
