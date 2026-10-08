---
description: Explain the five seminar commands and how to resume
---

Read `${CLAUDE_PLUGIN_ROOT}/persona.md` and `${CLAUDE_PLUGIN_ROOT}/MENTOR.md`.
Use `${CLAUDE_PLUGIN_ROOT}/tutor.py` with Python 3.11+ and the student's current
project directory as --workspace. All presentation is English unless the student
explicitly requests a Chinese translation. Follow the persona and progress footer.

Show exactly these five commands and their uses:

| Command | Purpose |
| --- | --- |
| /hi-agent-seminar:menu | Browse weeks, saved progress and optional topics |
| /hi-agent-seminar:start [week01] | Start or resume the selected week |
| /hi-agent-seminar:status [week01] | Show saved progress and the next step |
| /hi-agent-seminar:review [week01] | Answer three reflections and save a local code snapshot |
| /hi-agent-seminar:help | Show this guide |

Optional sampling, reasoning, Memory, RAG, workflow/Agent comparison and extra
cases are inside menu, under the selected week. No separate extension command is
needed. These topics do not change the core percentage. Explain that confirmed
learning steps save automatically; students can ask in chat to save a pause note
and resume by reopening the same workspace and using start or menu. Review means
new/resumed typed reflections, not just exporting old records. If a learner asks
for an existing learning report in chat, the mentor can use the export helper.
Run list read-only to find progress for the footer, or use 'Seminar · Choose a week'
when no course has started. Do not create progress just to show help.
