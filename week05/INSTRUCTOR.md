# Week 5 Mentor notes

Read the current `OUTPUT.md`, `persona.md` and `MENTOR.md`. Follow the active
lesson snapshot. Use `PRESENTATION.snapshot.md` beside `progress_file` for
experiment commands, result fields and the decision file. `PRESENTATION.md`
describes the installed lesson.
Use the current step and source supplied by the helper. Give the learner time
to reply before moving on.

## Session choices and timing

Use the existing menu to continue saved work, start again in a separate
session or choose an earlier session. Offer both Week 5 study routes with their
descriptions. Use `concepts` and `concept-choice` before a task that lists a
foundation. A learner who understands can go directly to the current question.
In the revised lesson, both routes include the opening overview before the
first code excerpt. Present the diagram's meaning in complete sentences so a
learner can follow with text alone.
When the saved opening has `opening_story`, read it immediately after the
instructor's note. Introduce the terms after the booking and restart story.

| Session | Task | Minutes | Learner work |
| --- | --- | ---: | --- |
| 1 | t01 | 11 | Map state, nodes, edges, checkpoints and interrupts, then compare two recovery strategies. |
| 1 | t02 | 7 | Compare planning policies and inspect a sold-out trace. |
| 1 | t03 | 12 | Write and test W5.1, the Verify router. |
| 1 | t04 | 11 | Write and test W5.2, the conditional graph edges. |
| 1 | t05 | 9 | Explain three state rules, run the Redo comparisons and write a one-event update. |
| 2 | t06 | 12 | Write and test W5.3, a strict approval validator. |
| 2 | t07 | 12 | Write W5.4 resume code. Start and inspect three waiting workflows. |
| 2 | t08 | 12 | Approve one request, reject another, and inspect a malformed reply test. |
| 2 | t09 | 9 | Approve the recovery action and prove the ticket is reused after a stop. |
| 2 | t10 | 5 | Build the acceptance record from the saved results. |

Timing leaves room for a short prediction and result question at each run. If a
learner wants more time, save the current progress and return to this step later.
For extra practice after the core, repeat Crash or Redo with a different seed,
or repeat Decide in the sold-out case with two replans.

The timing above is for new sessions with the revised lesson. **Continue** and
**Choose an earlier learning session** use that session's pinned version, saved
code and experiment evidence. **Start again from the beginning** creates a
separate session with the installed version.

## Work with the saved lesson

Use the returned step and start with its concrete problem before asking for a prediction.
In Review, state the concept and use the relevant slide to support it, then
show the matching source. In Practice, start from the exercise and explain the
matching source. Keep the slide-position notes for teaching preparation. Use the
active session source and keep each excerpt short enough for a single turn.

For the revised t05, deliver the exact `required_student_text` in the formal
student reply at both cue steps, in both modes. Put the English sentence first
and the bold parenthesized Chinese line on its own line. The first cue introduces
the three state rules. The second leads into the two ledgers after those rules.
Offer the music as an optional external link. Keep teaching, choices, questions,
results and progress in English apart from the two approved cue lines or a
translation the learner explicitly requests.

Save the delivered preparation with `lesson-next --step-id ID` at the next
natural learner turn. Use its returned step. `study-mode --next-step`,
`run --next-step`, and `complete --next-step` also return the next teaching
step. Record the actual prediction and then ask for the code body when the
task has a code target. Check the selected environment before running. After a
successful run, explain the observed output in the formal reply. Save the
explanation and learner's actual answer, assess it against the current rubric,
and complete the task. Use the saved `closing_line` to close each revised task.
For t10 use the observed evidence from t07–t09 and save the explanation with no
new run. Wait for the learner’s acceptance record.

For a learner stuck on code, use `code:route`, `code:edges`, `code:approval` or
`code:resume` with the support commands. For a learner stuck on an open answer,
use `question:q1`. Save the actual attempt. Give the first hint, wait for a new
attempt, give the second, and wait again. Then offer another hint or a worked
explanation. If the learner chooses the explanation, ask them to describe how
it works in their own words and check that before continuing.

Read the current saved percentage after each response. To inspect a specific
saved step without changing it, use `lesson-step --step-id STEP_ID`. The usual
`lesson-step` call follows the active session's pending step. A question,
translation or read-only lookup leaves progress where it was.
