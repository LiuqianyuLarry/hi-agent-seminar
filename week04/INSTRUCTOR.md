# Week 4 Mentor implementation notes

This guide describes the Week 4 student course. Read the current OUTPUT.md,
persona.md and MENTOR.md before using the saved Week 4 guide. Existing learning records must remain intact.

## Entry and time

Present Continue saved progress, Start again from the beginning, and earlier
sessions through the existing entry behaviour. A new session gets independent
progress and exercise files; it does not reset a previous session.

For a new Week 4 experience, begin with the brain-and-hands story and the concrete
task. Explain Review lecture + code versus Start seminar practice in the actual
choice card. Do not begin with installation commands. Reuse an existing Python
environment and prepare the local data before the first experiment needs it.

| Task | Minutes | Main purpose |
| --- | ---: | --- |
| t01 | 8 | Understand why a complete task needs more than an isolated tool request. |
| t02 | 8 | Inspect a real one-request DeepSeek experiment or its genuine teacher record. |
| t03 | 10 | Observe a minimal loop, repeated work and unsupported completion. |
| t04 | 9 | Check a proposal before execution. |
| t05 | 15 | Implement and test observation recording. |
| t06 | 15 | Implement both the goal checklist and the statistics-input comparison. |
| t07 | 10 | Implement and test stopping limits. |
| t08 | 13 | Connect execution, feedback and a new check. |
| t09 | 8 | Rerun the cases and read actual evidence. |
| t10 | 4 | Explain the loop and save a brief reflection. |

The first five tasks total 50 minutes and the last five total 50 minutes in either
mode. These are planning targets, not a timer that advances unfinished work. Allow
the learner to continue later when extra explanation is needed. Do not award
completion to meet a clock target. Longer reflections use the existing review
command; optional experiments are outside the core time.

## W4.2: two small implementations

Page 9 and page 14 address different decisions. W4.2A asks which evidence the goal
needs. W4.2B asks whether a statistics observation used the actual readings and
limit from those sources. Keep both required code targets in t06: `verify` and
`stats_inputs` (`statistics_inputs_match`). Do not let the supplied matcher hide
the second decision from the learner.

Use the existing 15 minutes: roughly 3 for explanation, 4 for W4.2A, 3 for W4.2B,
3 for tests and output, and 2 for the understanding checks. Teach the preparation
steps, then ask for one code body at a time. Save each actual submission under its
own target. Both bodies must be saved before running t06. Give the usual gradual
hints separately for whichever subpart the learner is working on.

The important counterexample has five different inputs but exactly the same
summary: `[82, 87, 91, 94, 97]` and `[82, 88, 90, 94, 97]` both give count 5, mean
90.2, maximum 97 and fraction 0.8 above 85. Treat these numbers as a teaching
example before the run. Afterwards use the actual `comparison_rows` to show why
matching the input dictionary matters. Do not settle for the easier `[1, 2]` case,
which a learner could reject just by comparing counts.

In the code walkthrough, trace `values` to the matching query and `limit` to the
specification. The learner compares those with `obs.arguments`. The caller skips
an observation when the helper returns False, then independently checks the
returned arithmetic for matching inputs. Explain both checks. The helper is not
a replacement for numerical validation or the task-goal checklist.

After running, require the original empty-data explanation and the new q2
explanation of the same-summary wrong-input case. Use an answer already given in
the current conversation if it actually meets a requirement; do not ask for it
again just to fill a field.

## Step delivery and experiment order

Use `lesson-step` to obtain one source-grounded step. Show or link the actual
slide in Review, explain it, then show the relevant source excerpt. Open another
code window only when needed. Do not dump `lesson.json` or this guide to students.

Every step states `before_run` or `after_run`. Present all applicable before-run
teaching and record the student's prediction or code before running. An after-run
step is not available until there is an actual completed run to inspect. Test
failures need explanation and another learner attempt; do not replace them with
reference outputs.

Save a previous formally delivered explanation at the next natural learner turn
when OUTPUT.md requires that order. Use `lesson-next` only after actual delivery
and a continuation or required answer. A request for clarification, a translation,
source inspection or a pause is not a continuation.

Read the actual `lesson_result.json`, its linked demo report or test output, and
the corresponding trace before explaining the result. Preserve the evidence
label and show the important fields in the formal reply. After a real response
to that explanation, save the relevant acknowledgement and answer. Do not say
only Saved after a tool call.

## Support and assessment

For a required multiple-choice step, use the existing lesson answer, hint,
solution and own-words assessment actions. A wrong response cannot advance it.

For code or a final open question, use Week 4's support actions with the target
`code:record`, `code:verify`, `code:stats_inputs`, `code:guards`, `code:loop`,
`question:q1` or the t06 `question:q2`:

1. Save the actual attempt, including a clear statement that the learner is stuck.
2. Give the first hint, then wait for an actual response or attempt.
3. Give the second hint, then wait again and offer more hints or an explanation.
4. Only after the learner chooses an explanation, read the relevant answer and
   explain how it works. Code reference answers are in the saved solutions file.
5. Save the learner's own-word response and assess it before allowing continuation.

Hints and reference explanations live in `lesson.json` for Mentor use. They are
not displayed in normal task views. Do not present a full assessed function body
as the pre-exercise walkthrough. Use existing helpers, data structures and small
adjacent examples so the learner still makes the key decision.

If a student has already supplied a response that answers a requirement, save and
assess that actual response rather than asking the identical question again.
Passing tests does not replace an understanding response. Mentor text is never
saved as a student response.

## Opening API evidence

The default no-key route reads a genuine saved teacher exchange. It must contain
the real request, response, matching local observations and provenance. If it is
missing, say that the route is unavailable until the record is supplied. Do not
fill the gap with a fabricated response or a scripted planner result.

A live selection authorizes only the described bounded experiment, not unrelated
calls. The one-request demonstration inspects all returned proposals without
claiming that every API response contains one tool. It makes no follow-up model
request. Later live-loop practice is a separate optional selection with a stated
budget. Do not print or save the API key.

The one-request demonstration uses a separate completed reference runtime because
the student's exercise functions are still unfinished. The copied reference is not
written over the learner's source files. Later core tests and the final comparison
run the learner's actual saved code.

## Correct the old slide simplifications

- M12 on the original PDF is the same synthetic classroom case now named CONV-3.
- Three domain tools plus a report do not imply four function calls.
- A response can propose several calls. Local execution and later feedback still
  require application code.
- A fixed workflow may include conditions and can be the simpler choice.
- The Week 2 miniGPT is not the live DeepSeek planner.
- Use dataclass default factories in executable code, not shared mutable defaults.
- The execution gate checks names, argument structure and task scope. The later
  statistics matcher checks that numbers use the collected source evidence.
- Observe preserves results, including errors; it does not judge task completion.
- Gate A is the combined control decision. Gate B checks a proposed tool action.
  These are teaching labels, not extra models or new callable tools.
- The scripted planner reads State directly. A missing observe call cannot be
  used as a fake demonstration of model amnesia. Inspect live protocol pairing.

## Preservation and Week 5 boundary

Keep schema and progress namespace compatible. Week 1-3 records and snapshots are
not rewritten when Week 4 starts. Existing Week 4 version-1 snapshots also remain
unchanged; only a new version-2 session requires the extra W4.2B body and question. A new session is independent; a revisit does
not move the current cursor or force the student back to it.

The learning helper saves seminar progress and artifacts. The example agent does
not resume a half-executed run across process restarts. A corrected human-handoff
task starts a new agent run here. Week 5 will introduce execution checkpoints.

## Verification and delivery

Check source references, English text, the two paths, the 50+50 timing, original
slide mappings, code-attempt gates, two-hint support, real-output explanations,
saved progress and independent restart. Run the offline exercise and integration
tests in disposable workspaces. An automated test does not prove how a host UI
renders the formal reply; report that limit honestly. Follow PUBLISHING.md for
distribution checks and the publication approval applicable to the release.
