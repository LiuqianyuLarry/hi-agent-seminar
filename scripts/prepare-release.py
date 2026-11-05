"""Audit release files and refresh the inventory; never pushes or reads credentials."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("package_check", ROOT / "verify-package.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)
files = sorted(check.package_files(ROOT))
blocked = {".venv", "node_modules", "outputs", "traces", ".hi-agent-seminar", ".hi-agent-seminar-preview", ".hi-agent-seminar-instructor", "hi-agent-seminar-work", ".archive"}
instructor_only = {"teacher_preview.py", "week03_preview.py", "TEACHER_PREVIEW.md",
                   "TEACHER_PREVIEW_VERIFICATION.md", "INSTRUCTOR_EDITION.json",
                   "tests/test_teacher_preview.py", "week04/PREVIEW.md"}
errors = []
approved_binary = {"week02/resources/assets/transformer-original.png":
                   "6d82cf140193daf9e1c95baab59017754e36c2f9548cfec9db86b2bd8d7d27ed"}
approved_binary.update({'week03/slides/slide-02.png': '53839781f8fa443a790e142566be9bbd50e149593b3f3496dac3d185bc00cc73', 'week03/slides/slide-07.png': '70a33fe18a4b273a91bb78d11d287fa7948188549fd8e194f8559d2017d44d8c', 'week03/slides/slide-09.png': '7cf7c284910927df55f4313e00d00cbdab75d839a13af9eb8ccd0e12cfff7e30', 'week03/slides/slide-16.png': '3b26f495f3e3badbf9023250992fed3853e69740e944455a47c0f3cd87ce2dc8', 'week03/slides/slide-15.png': '4e56dfcbe1af0e8f71c8ed5e90d1c8259c9cf944ce6f0ddd54fa69672b7197f6', 'week03/slides/slide-08.png': 'bbe8bbf691b068eeb6fc1b6478d4e157996e093c32db00f958ddb35bd95e9316', 'week03/slides/slide-20.png': '579793f54516e6a4a7cc84003faeba37d566da2e30b2e456a9908d951c28796c', 'week03/slides/slide-31.png': '860c0de92cbb5b0fb7233e2c6dcccb866aa6b6202a48fa98d949454423762f85', 'week03/slides/slide-37.png': '4d4facb0af01ae65bf015214a8f944c64c2cf5607409d6f4c85ad7f48e2e1b9b'})
# Original Week 4 PDF pages, rendered and visually reviewed.
approved_binary.update({'week04/slides/slide-02.png': '59003897d3101cb11d879901447fbeaba1ffc488ad0d97c70ec308776e64d804', 'week04/slides/slide-03.png': '5f41a4ead7960e42c9c257d7aed7b8d0ffe8049178f3e4fa37b5d4608b543a2f', 'week04/slides/slide-04.png': 'c1e62a0e05c22117a306b4f799313a170aa2809fbaf85d454de48a4874cbdbc8', 'week04/slides/slide-06.png': '4b697612104d8f5e253ed9e5c468b2b2491f619ca7757537be90ced05871aa40', 'week04/slides/slide-08.png': 'fb3f99bb5fe7c6d1e2746d6bb6b9b4faa19c61831f7c880733c822a8108aeef7', 'week04/slides/slide-09.png': 'a82686690c967c9d047247e94164d2c8f8d18945eacf7cb4f4b5be7b96fe4001', 'week04/slides/slide-14.png': '97cbc2c88ded5095bdc76c5563eb7bbfd29ec152978a33c6d0686ab99e7a3e9d', 'week04/slides/slide-15.png': '65c6d972c82374af7481942c2fbdb60451143ae21f38df68fc42970641d72688', 'week04/slides/slide-17.png': 'daef91b53ff71c5e48f835879604a7d24e8b2c96542302f7ea1b465762902a63', 'week04/slides/slide-18.png': '76156e1f1c93b564c359147fe2cc8183435876398e9f47ac5530ef9cdcb7f68e', 'week04/slides/slide-22.png': 'a9c985a38f2d640e6dd2ee480b423e4dd8fdef5918c49710034b60c65b215bd3', 'week04/slides/slide-23.png': '20c6c13469a80c988133c901d485d333c6ed3b79f2c0ad41ef4e22e30e3bebe6', 'week04/slides/slide-24.png': 'b73d0395774553cd3c7b36978e942c496c3846587be9ee6bcbc32a48fd86aedf', 'week04/slides/slide-25.png': '0e082c8ac037425abbfb3cb0888eb76fa737e5a36eae19a4aa26b31852b86126', 'week04/slides/slide-26.png': '027aa5bb587c5028db24cda71e3c6c9861f254d108b7e75dbfa628908cad0f99', 'week04/slides/slide-27.png': '25205efc90bea101b58750aceff861de98811b1aa9b4be5f5e060c243ac47311', 'week04/slides/slide-28.png': 'e6edf01006ea1ad763278f112000560f5d136d369ff1d4509fd67caa9ea84051', 'week04/slides/slide-29.png': 'ed3b00b826d03b1add4a60e7cf769883c58b129ad749be36f189aef6bb84b029', 'week04/slides/slide-31.png': 'af720780ef91e5ae894a3476580867b656f783608b353957fc6c60beabe607b1', 'week04/slides/slide-33.png': '0d6d29cf8f00a71bbd9b85498a64b11b7e222c0eff983895fbba6c90459f39a1', 'week04/slides/slide-34.png': 'd8b1a951741c0510222a0f263c05c48ee98f5314b20813e9bef3a36d049f1371', 'week04/slides/slide-35.png': '00a9f81b3e3658f1f6186d5485f8fb9269d541c4d1959dac08f7aa9f7f5676bd', 'week04/slides/slide-36.png': '8c056712fe59e953a5e0211767d263eb961421203d7575f59a25f76cdb1a6480', 'week04/slides/slide-38.png': '8381edd8470e470dede41c8bc460832fdddf28319f8a0ba2962f882c0cd22c6e', 'week04/slides/slide-39.png': '3dfed915b7ff2c08b27504fbd8f7f140cf0a1d15f47279fe6beef8e5caa23460'})
for path in files:
    relative = path.relative_to(ROOT)
    if relative.as_posix() in instructor_only:
        errors.append(f"Instructor-only preview file: {relative}")
        continue
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
    if (relative.parts[0] == "commands" and re.search(
            r"teacher_preview\.py|week03_preview\.py|TEACHER_PREVIEW\.md|"
            r"/hi-agent-seminar:start[^\r\n]*\bpreview\b", text, re.IGNORECASE)):
        errors.append(f"Instructor preview route in student command: {relative}")
    if path.suffix == ".py":
        ast.parse(text, filename=str(relative))
    elif path.suffix == ".json":
        json.loads(text)
if {p.name for p in (ROOT / "commands").glob("*.md")} != check.COMMANDS:
    errors.append("The release must contain exactly five commands.")
# A package hash is not enough: keep the internal course data and source hashes valid.
for manifest_name in ('week04/resources/data/manifest.json',
                      'week04/lecture_demo/data/manifest.json',
                      'week04/teacher-data/SOURCE.json',
                      'week04/slides/SOURCE.json'):
    manifest = ROOT / manifest_name
    if not manifest.is_file():
        errors.append('Missing Week 4 source manifest: ' + manifest_name)
        continue
    record = json.loads(manifest.read_text(encoding='utf-8'))
    for name, expected in record['files'].items():
        supplied = (manifest.parent / name).resolve()
        if (not supplied.is_relative_to(manifest.parent.resolve())
                or not supplied.is_file() or supplied.is_symlink()
                or hashlib.sha256(supplied.read_bytes()).hexdigest() != expected):
            errors.append('Internal source hash mismatch: ' + manifest_name + ' -> ' + name)
if errors:
    raise SystemExit("\n".join(errors))
if "--check-only" in sys.argv:
    print(f"PASS: read-only audit of {len(files)} student files; inventory unchanged.")
    raise SystemExit(0)
version = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
inventory = {"version":version, "files":{
    p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(ROOT / "SHA256SUMS.json").write_text(json.dumps(inventory, indent=2)+"\n", encoding="utf-8", newline="\n")
problems = check.verify(ROOT)
if problems:
    raise SystemExit("\n".join(problems))
print(f"PASS: audited {len(files)} files for release {version}; refreshed SHA256SUMS.json.")
