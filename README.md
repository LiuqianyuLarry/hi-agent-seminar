# hi-agent-seminar 2.0.3

An English EEEE4149 teaching plugin for Claude Code. Mentor Liu explains the code
and terms before asking questions, runs the prepared experiments, and helps students
interpret the actual output. Students write their own answers and prompts in chat.
Chinese appears only when a student explicitly requests a Chinese translation.

## Install from GitHub

Install Git, Python 3.11+ and Claude Code, and make sure you can sign in to Claude
Code and access GitHub. The classroom experiments use a separate DeepSeek API key
and may incur API charges. Never put your key in chat, this repository or a GitHub issue.

Run these commands in your terminal (PowerShell on Windows), not in Claude chat:

```text
claude plugin marketplace add LiuqianyuLarry/hi-agent-seminar
claude plugin install hi-agent-seminar@hi-agent-seminar-marketplace
claude plugin list
```

Restart Claude Code if prompted. Create or open your own student work folder
outside the plugin/repository, launch Claude Code there, and enter this in chat:

```text
/hi-agent-seminar:menu
```

The menu offers core lessons and optional topics. Only Week 1 is currently
published; Week 2 is a placeholder. Use the same student folder every time to resume.

## Update from GitHub

Run in your terminal:

```text
claude plugin marketplace update hi-agent-seminar-marketplace
claude plugin update hi-agent-seminar@hi-agent-seminar-marketplace
claude plugin list
```

Restart Claude Code, reopen the same student folder and use
`/hi-agent-seminar:start`. Updating the plugin does not replace learning records.
For automatic updates, open `/plugin` in Claude Code, select Marketplaces, choose
hi-agent-seminar-marketplace, then Enable auto-update. Third-party marketplaces
do not have auto-update enabled by default.

If an update says you already have the latest version, check
`claude plugin marketplace list`: the source must be this GitHub repository,
not an old local folder. Do not delete learning records or edit the installed
manifest version to work around an update problem.

## Switch from the old local-folder installation

Back up your student workspace first. Use `claude plugin marketplace list` to
confirm that hi-agent-seminar-marketplace currently points at the old local folder.
The following removes that marketplace registration AND its installed plugins,
then reinstalls this plugin from GitHub. Do not do this if the named marketplace
contains other plugins you need without planning to reinstall those as well.
It does not delete this seminar's records kept outside the plugin in your student folder.

```text
claude plugin marketplace remove hi-agent-seminar-marketplace
claude plugin marketplace add LiuqianyuLarry/hi-agent-seminar
claude plugin install hi-agent-seminar@hi-agent-seminar-marketplace
```

Restart Claude Code and continue from the same student workspace.

## Start or resume a seminar

Use a student work folder outside this plugin. You need Claude Code and Python
3.11 or newer. The teaching conversation uses the model configured in Claude Code;
the classroom examples use your own DeepSeek API account.

From a terminal in your student folder, load the plugin (replace the path):

```text
claude --plugin-dir "/absolute/path/to/hi-agent-seminar"
```

In Claude Code, open the course chooser:

```text
/hi-agent-seminar:menu
```

Or start Week 1 directly:

```text
/hi-agent-seminar:start week01
```

Mentor Liu prepares a local virtual environment, installs its packages and checks
imports. You enter your API key yourself in the terminal command it provides.
Do not put a key in chat. Setup has no graded questions. During Task 4, write your
prompt in chat; Mentor Liu saves your wording to instructions.txt before running.

## Alternative: install from an extracted local package

The package includes both `.claude-plugin/plugin.json` and a local marketplace.
With the extracted plugin at its permanent location, run these terminal commands:

```text
claude plugin marketplace add "/absolute/path/to/hi-agent-seminar"
claude plugin install hi-agent-seminar@hi-agent-seminar-marketplace
```

If the marketplace is already registered to this same source folder, update:

```text
claude plugin update hi-agent-seminar@hi-agent-seminar-marketplace
```

If it points to another folder, inspect `claude plugin marketplace list` and update
that source or use the explicit --plugin-dir loading method above. Do not assume
editing source files changes an already installed cache. Restart the Claude Code
session after an update. Confirm version 2.0.3 with `claude plugin list`.

Replace the whole plugin source folder with the extracted release folder, including
the hidden .claude-plugin directory. Do not merge it into an old commands folder:
old command files would remain visible. The correct commands folder contains
exactly menu.md, start.md, status.md, review.md and help.md. Keep an old folder as
a backup outside the active plugin path. Do not nest hi-agent-seminar inside itself.
The ZIP includes its own SHA256SUMS.json; verify-package.py checks the packaged
file set and hashes to detect missing, extra or modified files after extraction.

On Windows, if PowerShell cannot find claude but it was installed through npm, use:

```powershell
& "$env:APPDATA\npm\claude.cmd" --version
& "$env:APPDATA\npm\claude.cmd" plugin update "hi-agent-seminar@hi-agent-seminar-marketplace"
```

Local loading and manifests follow the
[Claude Code plugin guide](https://code.claude.com/docs/en/plugins) and
[manifest reference](https://code.claude.com/docs/en/plugins-reference).

## Commands

All commands begin with `/hi-agent-seminar:`.

| Command | Purpose |
| --- | --- |
| `menu` | Browse weeks, saved progress and optional topics; start or continue learning |
| `start [week01]` | Start a chosen week or resume the active week |
| `status [week01]` | Show saved percentage and next step without advancing |
| `review [week01]` | Answer three reflection questions; save answers and a code snapshot locally |
| `help` | Show these five commands and usage guidance |

In menu, choose a week, then Optional topics for sampling, reasoning, Memory, RAG,
workflow/Agent comparison and extra cases. Each topic shows its own saved status.
Browsing and short concept recaps do not start experiments or change progress.
Live practice requires environment/key setup, your prediction and approval for
API calls. Optional progress does not change the core percentage.

Confirmed learning steps save automatically. Ask Mentor Liu in chat to save a
pause note or export an existing learning report; no extra slash command is needed.
The review command always means three reflections plus a code snapshot.
Version 2.0.3 resumes existing v2 progress in the same workspace; it does not reset it.

Course selection and multiple-choice checks use genuine AskUserQuestion selectors
when available in the host. Open questions and reflections remain ordinary typed
chat. If that host lacks the selector tool, the mentor explains the limitation and
offers lettered choices. It does not present text boxes as clickable controls.

## Updates keep learning records

Plugin files and student records are separate. Update only the plugin folder;
keep the student workspace and both folders below. The v2 directory name is a
permanent storage namespace and does not change with the plugin version.

```text
.hi-agent-seminar/v2/week01/
  progress.json          Teaching steps, predictions, answers, feedback and runs
  progress.backup.json   Previous valid save
  lesson.snapshot.json  Course definition pinned for this learner
  TEACHING.snapshot.md  Teaching notes pinned for this learner, when available
  setup/                Environment setup receipts
  runs/                 Actual experiment records, stdout and CSV files
  reviews/              Reflection answers and bounded code snapshots
  exports/              Learning reports
hi-agent-seminar-work/v2/week01/resources/
                        Student copy of the examples and prompt file
```

Next time, open the same student folder and start the course again to resume v2.
Completed tasks, answers, prompt edits, run artifacts, reflections, optional topics
and pause notes remain in place. Existing compatible v2 records get a course
snapshot on their first resume in 2.0.2. New course material in later releases
applies to new learners; started courses keep their original task definitions,
weights and student code. Updating does not automatically replace learner files.
The helper preserves incompatible/corrupt records and stops for recovery or a
compatible migration instead of resetting them. Legacy v1-only records are also
detected and preserved, but require migration; they are not silently converted.
Records deleted before this release cannot be recreated by an update.
Moving to another computer requires copying the student workspace as well as the
plugin. Progress is local, not cloud-synced; the Python environment may need repair
after a move. Keep backups of the whole workspace, not just progress.json.
The footer uses saved completion, not elapsed time. Its sequence is
0, 8, 15, 30, 40, 50, 62, 74, 86, 93, 100%. Optional extensions do not change it.
Each student should use their own work folder. There is no Feishu submission or
cloud sync. You can pause midway through a task or a reflection review.

## Files for instructors

- `persona.md`: Mentor Liu's English persona and response layout.
- `MENTOR.md`: required teaching order and helper instructions.
- `week01/lesson.json`: tasks, terms, code anchors, questions and private rubrics.
- `week01/TEACHING.md`: response trees, explanations and practical teaching notes.
- `week01/INSTRUCTOR.md`: 2 x 50-minute timing and classroom guidance.
- `week01/SOURCES.md`: slide/handout/code alignment.
- `week02/README.md`: instructions for adding future weeks.
- `FEEDBACK_CHANGES.md`: mapping from the supplied test feedback to changes.
- `VERIFICATION.md`: performed checks and remaining host-interaction limits.
- `PUBLISHING.md`: release checklist, version bumps and integrity checks.

This public repository includes lesson definitions and mentor assessment criteria.
They are not secret exam material. Learner records are local and are not sent to
GitHub. Avoid attaching private logs or credentials when reporting a problem.

The helper enforces task order and stores evidence. The conversational explanation
and open-answer assessment still come from the mentor. Do not present completion
as certification that an engineering diagnosis or machine action is safe.

## Recovery

An empty leftover resources directory is reused. Existing nonempty student files
without a progress record are not overwritten. Preserve the folder and recover
its matching record instead of replacing the student's work.
For an interrupted run/setup, verify the old process stopped, then let the mentor
use recover with the recorded ID. Do not rerun a pending process blindly. A stale
lock can be removed after its helper has stopped. Do not delete progress to fix it.
API errors retain their real records. There is no fabricated successful fallback.
