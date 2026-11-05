---
description: Explain the five seminar commands and how to resume
---

Read `${CLAUDE_PLUGIN_ROOT}/OUTPUT.md` before persona, lesson or saved-guide
instructions. Its formal final-response delivery rules apply to every week and
existing session. Keep tool preambles to brief operation status; place the complete
student-facing explanation, relevant code/results, one next question or action,
and exact saved progress in the formal reply. A helper record or tool log is not
that reply. Follow OUTPUT.md when sequencing blocking native choice tools.

Read `${CLAUDE_PLUGIN_ROOT}/persona.md`; this command does not need the full MENTOR.md.
Use `${CLAUDE_PLUGIN_ROOT}/tutor.py` with Python 3.11+ and the student's current
project directory as --workspace. All presentation is English unless the student
explicitly requests a Chinese translation. Follow the persona and progress footer.

Explain that menu/start offers Continue saved progress, Start again from the
beginning, and Choose an earlier learning session. Starting again creates separate
progress and fresh exercises, preserving earlier records and code. Each session
has its own setup and percentage. Show exactly these five commands and their uses:

| Command | Purpose |
| --- | --- |
| /hi-agent-seminar:menu | Browse weeks, saved progress and optional topics |
| /hi-agent-seminar:start [week01, week02, week03 or week04] | Start or resume the selected week |
| /hi-agent-seminar:status [week01, week02, week03 or week04] | Show saved progress and the next step |
| /hi-agent-seminar:review [week01, week02, week03 or week04] | Answer three reflections and save a local code snapshot |
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
one run per CPU/CUDA device. Without CUDA, complete a local CPU experiment and
analyse the supplied real teacher CPU/CUDA data, then pass the understanding check
to continue to 100%. Three repeats and full Batch scanning are optional
inside Week 2's menu. Week 2 needs no API key. Week 1 records remain separate.


Week 3 offers two distinct paths in the same 2 x 50-minute format:

- Review lecture + code: original PPT pages explained through their diagrams and examples, then
  actual CONV-3 maintenance-demo code and
  the related temperature-tool exercises.
- Start seminar practice: temperature-tool exercises with the necessary concept
  and detailed code explanations as students need them.

Both paths include the full MCP introduction before practice, optional foundation
cards, and the same core learning checks. Native cards show these differences
before students choose. Earlier records are preserved; a new session is needed
to use a revised lesson when the saved session still uses an older snapshot.

The four MCP mini-checks require actual learner responses before continuing.
The mentor saves answers, hints and explanations so students can pause and resume
without losing their place.

Week 4 builds an agent loop in two 50-minute sessions. Review follows the lecture story and demonstrations before the coding exercises; practice starts from the exercises. Four coding groups cover observations, verification, stopping and connecting the loop. W4.2 has two short required parts: the goal checklist and exact source-input matching. Students can complete the core using the teacher's genuine recorded API experiment and real local tools, with no GPU or private key. Live DeepSeek practice is optional and requires approval. Earlier progress is preserved.
