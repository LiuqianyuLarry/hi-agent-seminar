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
| /hi-agent-seminar:start [week01 or week02] | Start or resume the selected week |
| /hi-agent-seminar:status [week01 or week02] | Show saved progress and the next step |
| /hi-agent-seminar:review [week01 or week02] | Answer three reflections and save a local code snapshot |
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

Week 2 is available with beginner concept choices, the original Transformer figure,
four student coding exercises and local PyTorch experiments. Students may choose
I understand - continue, Explain briefly, or Show an example before foundation
explanations. The teaching order is logic, mathematics and actual code. Core uses
one run per CPU/CUDA device; three repeats and full Batch scanning are optional
inside Week 2's menu. Week 2 needs no API key. Week 1 records remain separate.
