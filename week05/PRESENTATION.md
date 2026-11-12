# Week 5 delivery notes

Read the installed `OUTPUT.md` and use the active Week 5 session. Give the task,
its purpose, the short code excerpt, the result explanation and the saved
percentage in the formal student-visible reply. Wait after the current question
or request for an action. Use ordinary English. In the revised lesson, deliver
the two exact bilingual cues from the saved t05 steps. Outside those cues, use
English unless the learner explicitly requests a Chinese translation.

## Open with the travel problem

If the saved first step includes `instructor_opening`, quote the instructor's
note at the start of the formal reply. For a step with `opening_story`, read
that story straight after the note, in its saved order. Begin with what learners
built in Weeks 1–4, give them the full booking job, then show what disappears
when Python stops. Introduce the state machine and the saved checkpoint once
the learner knows what needs to survive. Explain the rest of the overview
through the same booking before showing the map and asking the checkpoint
question. Allow about four minutes for this opening. Then begin the Crash
comparison. Introduce the CONV-3 review ticket in Session 2.

Show the two study choices and their descriptions from the lesson. In **Review
lecture + code**, state the main idea in complete sentences. Show the supplied
slide as a visual aid, then show the matching Python. Make the explanation
understandable on its own. Save numerical comparisons for the observed-result
step. In **Start seminar practice**, open the first task, give
the same opening overview, and explain the relevant code. In both routes offer
the concept choices before the relevant task. Accept “I understand,” offer a
short explanation or work through the example, then ask for the prediction.

Use the returned `snippets` with their line notes. Each step supplies its
key code windows in one response. Fetch a specific `--code-index` only for
a learner question. The complete script in `TEACHING.md` is available as a
reference. Use the code from the active session's saved resource directory.

Use `study-mode --next-step`, `run --next-step`, and `complete --next-step`
when taking those actions. Their replies already contain the next teaching
step. `lesson-next --step-id ID` also returns it. On resume, use `lesson-step`
without a step ID if no current step is in context. For an exact read-only
lookup in Review, use `lesson-step --step-id t02.review_prepare --week week05`.
Use the saved step ID for the active mode. For a short multiple-choice check,
save the actual letter the learner picked using `lesson-answer --step-id ID
--text LETTER`. A task's final question is `one_next_action` on its evidence
step. Record that same answer under its `task_question_id` after saving the
delivered step. Use the supplied `foundation_options` instead of fetching
the concept cards again.

## Run the three comparisons

Before each experiment, explain the question, which settings are fixed and
why, and which fields answer it. Record the learner's prediction. Use the
seminar `run` command to save results with the current learning session. For a
manual repetition, run these commands from that session's resources directory.

```text
python -m experiments crash --strategy both --seed 7 --trips 2000
python -m experiments decide --scenario both --strategy all --seed 7
python -m experiments redo --write-as both --keys all --seed 7 --trips 2000
```

Each command runs the paired cases or complete table shown in the lesson. In
the formal reply read the actual result under `experiment.results`. A student
can reproduce a row by choosing one strategy and leaving the seed and workload
the same. When answering a question about the two-store recovery workflow, use
that workflow’s evidence instead of the simulation results.

| Experiment | Question and fixed settings | Fields to show after the run |
| --- | --- | --- |
| Crash | How much work does saving the position avoid? Compare strategies with the same seed, 2,000 trips and failure probability. | `mean_steps`, `mean_restarts`, `mean_planning_calls`, `extra_charges` |
| Decide | Who notices a sold-out option, and how much does one replan recover? Use the same 30 tasks and seed for each policy in each scenario. | `scenario`, `strategy`, `replans`, `completed`, `planning_calls`, `failed_with_bookings`, `sample.tool_log` |
| Redo | Which change repairs saved state, and which avoids duplicate payments? Compare state writes first, then vary the key with the update style fixed. Use the same seed and 2,000 trials. | `write_as`, `keys`, `wrong_final_states`, `repeated_actions`, `blocked_requests`, `replay_matches` |

In Decide, explain that a planning call in the output is a call to a rule in
this simulation. For the sold-out sample, walk through one failed tool result
and the next decision. In Redo, ask the learner to write the one-event trace
update and identify which repeated request gets the same key.

## Teach the two Redo comparisons in order

Begin both modes with the example where payment succeeds and the process then
crashes. Offer the supplied [optional
15-second music link](https://www.bilibili.com/video/BV1min86QEHN/) in the reply.
Invite the learner to open it in a new tab. Continue the lesson with the first
bilingual cue whether the learner plays the music or skips it. Allow about one
minute for this opening, including the optional clip. The audio stays external
for copyright reasons.

Present the three state rules in their stated order. For each rule, explain
why it exists, show the relevant lines, and describe an observable failure.

| Rule | Source and counterexample |
| --- | --- |
| Return an update | A node returns only its new values or events. Returning the old log together with the new event makes the merge append the old events a second time. |
| Merge computes the new state | `merge` uses `ADD` for fields that accumulate. Adding `next` to `ADD` produces `read_requestsearch_tickets` and an unknown node error. Removing `spent` from `ADD` overwrites USD 960 with USD 180. Adding the two legitimate charges gives USD 1,140. |
| Commit once | Save the new state and its next node together. If the log or total has changed while `next` still points to that same step, recovery can apply the update twice. Use the two write strategies in the actual table to check the result. |

Use `counterexamples.whole_log_as_update`, `next_in_add`, `spent_not_in_add`
and `partial_commit` after the revised t05 run. Show the repeated event, the
actual exception, the two totals and the state before and after recovery.
Explain that the simulation computes its expectation with the same merge
rule, which is why `wrong_spent` can be zero when the receipt is wrong. The
USD 1,140 check comes from adding the underlying charges independently. For
a separate manual replay, use `python -m experiments.redo_counterexamples`.

After the second bilingual cue, use the five parts of `t05.*_two_ledgers` in
order. Tell the story of trip 17 and the $960 charge, then compare the saved
workflow position with the provider's receipt. Walk the learner through the
booking counter twice so they can see the same number being checked before the
clerk charges anything. Explain both outcomes of the lookup and give the four
numbered operations. Then show the supplied `World.act` excerpt and use each
line of `code_walkthrough` to connect the code to what the clerk did. Ask the
step's one prediction before moving to the replay comparison. Session 2 uses
the same idea with the approval action and the local `tickets` table.

## Save code and use the actual workflow evidence

For W5.1 through W5.4, ask for the learner’s function body in chat after the
prediction. Save it with `write-code`, then run the task. On failure, explain
the smallest relevant test case and ask the learner what to change. Follow the
two-hint rule and confirm an own-words explanation after a worked solution.
The calculations run with Python 3.11 or later and its standard library.
Prepare the workflow interpreter before W5.1 (`t03`) so it is also ready for
the graph check in W5.2. Create a virtual environment in the learner workspace,
outside the saved resources directory. From the active session's saved
resources directory, use its Python to install the lab packages. Explain the
current task and save that explanation before using the seminar setup command.
Use the same interpreter path for installation and setup.

```text
<venv-python> -m pip install -r workflow/requirements.txt
<helper-python> <plugin-root>/tutor.py setup --week week05 --workspace <learner-folder> --python <venv-python>
```

Quote any paths that contain spaces.

Use the resulting `workflow_ready` status before running a workflow exercise.
For a manual isolated check, run these commands from the saved resources
directory, replacing `<venv-python>` with the same executable path.

```text
<venv-python> -m workflow check route
<venv-python> -m workflow check edges
<venv-python> -m workflow check approval
<venv-python> -m workflow check resume
```

If `check edges` reports `ModuleNotFoundError` for `langgraph`, check which
interpreter ran the command. Use the interpreter whose installation and
seminar setup passed.

In t06, introduce `action_id` as the request number and `payload_hash` as a
fingerprint of the approved content. A regenerated sensor report can describe
different readings for the same request. The approver needs to review those
new details before authorizing the action.

W5.4 first uses a stand-in graph to check the learner’s resume call. Read
`exercise` for that check. Fix the function if it fails before starting the
workflow trials. A passing check confirms the call shape. The following
`processes` records come from starting and inspecting three waiting threads.
A new PID shows a fresh process. The matching `thread_id`,
`checkpoint_id` and pending `HumanApproval` identify the state it reopened.
The tool counts and observations show what was carried over. For an individual
event or the exact observation, open the corresponding `steps[].evidence` file
in the saved run folder.

In t07, explain that the thread identifies the whole workflow record and each
checkpoint identifies one saved version of it. `sync` waits for a save before
the next graph step. `async` can write while execution continues. `exit` saves
at a run boundary such as completion or an interrupt. A process that closes
unexpectedly may lose work after the last durable checkpoint. Point to the
lab's SQLite checkpointer and `durability="sync"` when showing the code.

Before collecting decisions in t08 or t09, use the t07 run result already in
the conversation. If it is missing, use `results --week week05 --task-id t07`.
Read each requested thread’s
`decision_requests` entry, including the proposed action and report. Ask the
learner to decide for the named pending action and give a short reviewer label.
Ask for one decision at a time. Save the actual learner decisions to a JSON
file in the current learning workspace, then pass its path with
`run --decision-file PATH --next-step`. Both `action_id` and `payload_hash` come from the
saved request for that exact thread.

The shape for t08 is shown below. Replace the placeholders using the real
waiting tasks and the learner’s reply.

```json
{
  "approve": {
    "approved": true,
    "action_id": "APPROVE_ACTION_ID",
    "payload_hash": "APPROVE_PAYLOAD_HASH",
    "reviewer": "REVIEWER_LABEL"
  },
  "reject": {
    "approved": false,
    "action_id": "REJECT_ACTION_ID",
    "payload_hash": "REJECT_PAYLOAD_HASH",
    "reviewer": "REVIEWER_LABEL"
  }
}
```

For t09 use one approval object with the same four keys for `week05-recovery`.
Each task starts from a separate copy of the three closed waiting workflows
from t07. Every process within a task opens the same copied databases.
The test driver creates its own malformed fixture in t08. Compare the
`invalid_reply.before` and `invalid_reply.after` checkpoints, then compare the
actual `approval` and `rejection` results. After the outcomes, use
`interrupt_demo.before_pause` and `interrupt_demo.after_resume` to explain the
restart. A separate demonstration graph records calls on both sides of the interrupt.
The count before the wait increases again on resume because LangGraph restarts
the node at the beginning. In CONV-3, `HumanApproval` waits and `ApplyAction`
writes only after the learner approves. In t09 the interrupted step is the
approved `ApplyAction` itself, after its ticket has committed.

For t09, connect the Redo receipt register to the actual `tickets` table. Compare
`fault`, `after_fault` and `after_continue` using the pending node, PIDs, ticket
counts, `action_id`, and `reused`. The same action ID and payload identify the
one durable row. In the revised lesson, show the independent `payload_collision`
case. The conflicting payload raises an error and leaves the existing row
unchanged. The collision case uses a separate exercise database.

The revised t08 and t09 demonstrations can also run separately from the saved
resources directory with the workflow interpreter. The collision demonstration
uses the completed approval validator.

```text
<venv-python> -m workflow.mechanism_demos interrupt
<venv-python> -m workflow.mechanism_demos payload-collision
```

Have the learner assemble the five acceptance rows in t10 using the saved
results. Use the active session’s saved `core_percent` after each response.
An optional rerun, a question, a translation or a revisit leaves that progress
where it was.
