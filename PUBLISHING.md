# Publishing updates

Repository: https://github.com/LiuqianyuLarry/hi-agent-seminar

Keep .claude-plugin/marketplace.json at the repository root. The plugin source
is ./, so the plugin manifest, commands and weekly folders share that same root.
Do not upload only a ZIP or wrap the files in another hi-agent-seminar directory.

## Release checklist

1. Edit plugin/course files and update English documentation.
   For Week 2, edit scripts/build-week02.py and run it to rebuild lesson.json and
   transformer-map.html. The supplied original Transformer PNG is an explicitly
   reviewed binary asset with a pinned hash and attribution in week02/SOURCES.md.
2. Increment .claude-plugin/plugin.json version for each distributed change.
   Keep the plugin name and marketplace name stable.
3. Keep PROGRESS_NAMESPACE and existing record formats backward-compatible.
   Existing learners use saved lesson snapshots and student code. Test upgrades;
   never publish a change that resets progress or overwrites student work.
4. Run the tests and manifest checks below. No live API requests are needed.
5. Run `python -B scripts/prepare-release.py` to audit files and refresh SHA256SUMS.json.
   Run `python -B verify-package.py` and review `git diff` and `git status`.
6. Present the local changes and validation results to the instructor. Wait for
   explicit approval to publish this update to GitHub. Approval to edit or test
   does not authorize publication. After approval, commit the changes, including
   the refreshed inventory, and push to main.
   Do not force-push over another author's work. A release tag is optional.
7. Test an installation from GitHub before announcing the version to students.

```text
python -B -m unittest discover -s tests -v
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .claude-plugin/marketplace.json
python -B scripts/prepare-release.py
python -B verify-package.py
git status --short
git diff --stat
```

For real Week 2 CPU integration, prepare a dedicated interpreter using
week02/resources/requirements-cpu.txt. Set WEEK02_TEST_PYTHON to its absolute
Python path and run the same unittest discovery command. Without that variable,
the real-PyTorch integration test is explicitly skipped; mock workflow tests alone
do not prove that training works. Validate CUDA separately on actual lab hardware.
Never publish local validation workspaces, environments or completed student copies.

The release script ignores Git metadata, Python bytecode caches and Claude Code's
root .in_use runtime-marker directory. It rejects
known private/generated paths, symlinks and common secret patterns rather than
silently publishing them. This is a guardrail, not a guarantee: inspect the proposed
Git commit for private content before pushing. Never distribute real .env files,
student records, API keys, local virtual environments or generated experiment data.
An empty .env.example is intended for distribution.

The inventory detects accidental file changes; it is not a cryptographic signature
from a separate trusted party. .gitattributes prevents Git from changing line
endings, so a fresh Windows or Unix checkout can match the same file hashes.
Git metadata, Python bytecode caches and Claude Code's root .in_use runtime markers
are excluded from verification; those markers are not plugin source files.

Students update with:

```text
claude plugin marketplace update hi-agent-seminar-marketplace
claude plugin update hi-agent-seminar@hi-agent-seminar-marketplace
```

They restart Claude Code and keep using the same student workspace. Third-party
marketplace auto-update is opt-in. Publishing here does not upload student records.

Official references:

- https://code.claude.com/docs/en/plugins/host-marketplace
- https://code.claude.com/docs/en/discover-plugins
