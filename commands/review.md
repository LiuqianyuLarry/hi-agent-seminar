---
description: Answer three reflection questions and save a local code snapshot
argument-hint: "[week01|week02|week03|week04]"
---

Read `${CLAUDE_PLUGIN_ROOT}/OUTPUT.md` before persona, lesson or saved-guide
instructions. Its formal final-response delivery rules apply to every week and
existing session. Keep tool preambles to brief operation status; place the complete
student-facing explanation, relevant code/results, one next question or action,
and exact saved progress in the formal reply. A helper record or tool log is not
that reply. Follow OUTPUT.md when sequencing blocking native choice tools.

Read `${CLAUDE_PLUGIN_ROOT}/persona.md` and `${CLAUDE_PLUGIN_ROOT}/MENTOR.md`.
Use `${CLAUDE_PLUGIN_ROOT}/tutor.py` with an available Python 3.11+ interpreter,
the student's current project directory as --workspace, and the selected --week.
All student-facing content is English; Chinese is allowed only for an explicitly
requested translation. Follow the persona's presentation and progress footer rules.

Select the supplied week $ARGUMENTS or the active week returned by list. If none has started, invite the student to begin a seminar. Call review-questions. Ask its three open questions in ordinary chat one at a time, skipping already saved draft answers. Let the student write their own reflections; do not use multiple-choice cards or fill in answers. Save each with review-answer --question r1/r2/r3 --text STUDENT_WORDS, preserving their words. After all three, call review. It saves a local report and code snapshot with size and privacy limits. Link the report and show unchanged core progress. No external submission or Feishu is used.
