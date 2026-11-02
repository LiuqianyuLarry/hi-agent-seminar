# Week 3 mentor teaching workflow

Read the installed OUTPUT.md before this workflow or any saved teaching guide.
The shared formal final-response policy applies to both routes and older saved
lessons without replacing their snapshots or learning records. It controls
delivery order; it does not change the curriculum or completion gates.

Keep the five seminar commands and guide the learner through real attempts,
observed results and understanding checks. Follow the saved course and preserve
previous progress, source files and learning sessions.

## Choose a learning route with useful option descriptions

Show these native choice cards after the learner selects a normal learning
session. Use the card descriptions as well as the labels:

| ID | Label | Description |
|---|---|---|
| review | Review lecture + code | Look back at the actual PPT slides, explain their diagrams and examples in plain English, then walk through the matching lecture code and apply it in the seminar. |
| practice | Start seminar practice | Start the CONV-3 temperature-tool exercises. Learn the concepts and code needed for each task as you go. |

Common caption: "Both paths take two 50-minute sessions. Both include detailed
code explanations, optional foundation explanations, and the full MCP lesson
before practice."

The paths must differ in their actual steps. Review uses the selected PPT
concepts and lecture_demo source functions before transferring the same idea to
the seminar tools. Practice uses the seminar source directly with the necessary
concept explanations. Both fully teach MCP before the wrapper exercise. Do not
return the same walkthrough with a different mode label.

Begin with condition monitoring: engineers combine measurements, maintenance
history and equipment references to assess operation. Those records are outside
the model. This week builds the tool-use part of an engineering assistant:
DeepSeek proposes a request; the application validates, runs a function and
returns evidence. Each turn permits at most one tool. Do not promise autonomous
multi-tool diagnosis or imply that three classroom records prove a fault cause.

## Teaching and saved lesson fragments

Continue/restart/session choices remain unchanged. Continue respects the saved
lesson snapshot and student files. Restart makes a separate session. Do not reset
Week 1, Week 2 or an existing Week 3 record on update. Existing Week 3 version-1/2
sessions retain their original course; offer a fresh session to study version 3,
without losing or silently remapping earlier answers and percentages.

After selecting a session, record the chosen route with study-mode. Read the
saved teaching guides and PRESENTATION.md; load only the current fragment.
Before explaining unfamiliar basics, offer the current task's foundation cards
through concepts and concept-choice: I understand / Explain briefly / Show an
example. Honour that choice, then return to the selected teaching fragment.

```text
python tutor.py study-mode --workspace PROJECT --week week03 --study-mode review
python tutor.py lesson-step --workspace PROJECT --week week03
python tutor.py lesson-step --workspace PROJECT --week week03 --name STEP_ID
python tutor.py lesson-step --workspace PROJECT --week week03 --name STEP_ID --code-offset 12
python tutor.py lesson-next --workspace PROJECT --week week03 --name STEP_ID --text ACTUAL_EXPLANATION
```

Deliver the complete returned fragment in a formal reply first. At the next
learner continuation or eligible attempt, record lesson-next with what was
actually delivered, not simply "done". Do not advance it for a clarification,
translation or request to inspect code. Keep the node ID and mode aligned with
the helper. Do not mark a source as explained merely because it was opened.
Use the helper's actual source excerpts and line numbers; source packs are
lecture demo or student seminar, not interchangeable. Continue from the saved
fragment after a pause. Show the code in groups of at most 12 lines.
Use the returned next_code_offset for another window of the same function;
reading that window must not record lesson-next or count as task completion.
For another source in code_sources, use --code-index INDEX with offset 0. Each
source has its own windows; explain the relevant sources before advancing.

For phase=slide, show slide_image and follow slide_review: point to the important
parts of the actual page, explain the concept, work through its example and make
the code bridge. Do this before source-code walkthroughs. Setup scripts remain
setup; they cannot substitute for the slide discussion. Only load the current
image. Images, source code and the lesson are preserved in each new session.

## Four short MCP checkpoints inside 28 minutes

Teach two short concepts, then stop for the saved check: roles, discovery, failed
results, and resource context. Allocate 14 minutes to explanations, 4 minutes to
these checks, 7 minutes to the wrapper/tests/output, and 3 minutes to the final
two questions. These are planning targets; do not skip a failed check to meet a
timer. Both study routes include the same checks before the MCP exercise.

```text
python tutor.py lesson-answer --workspace PROJECT --week week03 --name STEP_ID --text LETTER
python tutor.py lesson-hint --workspace PROJECT --week week03 --name STEP_ID --text STUDENT_DIFFICULTY
python tutor.py lesson-solution --workspace PROJECT --week week03 --name STEP_ID --text STUDENT_REQUEST
python tutor.py lesson-answer --workspace PROJECT --week week03 --name STEP_ID --text STUDENT_OWN_WORDS
python tutor.py lesson-assess --workspace PROJECT --week week03 --name STEP_ID --verdict pass --text ACTUAL_FEEDBACK
```

Save the learner's actual choice. On success, record lesson-next with the prior
concept explanation already delivered in a formal reply, then include a brief
confirmation and why the choice fits in the next formal reply. Follow all check
gates; never record the new feedback as though it had already been delivered.
A wrong answer does not pass and
does not reveal the full answer. Give hint 1, wait for a response, then hint 2 if
needed. After two hints, offer More hints / Explain the answer. Only invoke
lesson-solution when the learner requests the explanation. That explanation
still does not pass the checkpoint: save a new own-words response and assess it.
Use verdict retry when it is not yet understood, then wait for a new response.
A bare lesson-next acknowledgement cannot skip a checkpoint. Wrong attempts and
hints are saved so a paused learner can resume with the same support history.

## Continue the exercise after the teaching checks

After the preparation fragments, use the normal task/code and supervised exercise
flow. Foundation preferences still use concepts and concept-choice. A learner
may skip a foundation refresher but must complete the core code and checks.

- `write-code --name stats|spec|query|mcp --input-file BODY.txt` saves the student's
  function body from chat. Imports and signatures are provided. Earlier code is
  backed up. `--name description` saves the student's revised tool description.
- `predict`, `run --intro TASK_AND_PURPOSE`, `results`, `explain`, `answer`, `assess`
  and `complete` retain the supervised sequence. Explain actual output fields
  in a complete formal reply before checking understanding. At the next natural
  learner turn, record that delivered explanation before handling the answer or
  completing the task. Do not save a worked answer as student work.
- `mcp-intro --text ACTUAL_EXPLANATION` records the full MCP introduction once it
  has actually been presented. Both modes need it before t08 practice.
- `revisit --task-id t02` retrieves earlier content without redirecting to the
  latest unfinished task or changing completion. Use a fresh session when the
  learner wants clean code and new recorded runs. Never overwrite older work.
  The response contains one step and a short step list. Use `--step-id STEP_ID`
  to inspect another step, or `--code-offset OFFSET` for another code window.

For difficulty, give two gradual hints, with an attempt between them. Then offer
More hints / Explain the answer. After explaining the answer in student mode,
ask for the learner's own explanation and confirm understanding before moving
on. Do not enter the mentor's explanation as the learner's own response.

## Environment and evidence

Inspect available interpreters first. `setup --python EXISTING_PYTHON` checks
packages and builds synthetic data; it does not automatically install them.
Only prepare the small Week 3 dependencies if needed. No CUDA, PyTorch or model
download is required. Configure keys privately through resources/provider.py in
the student's terminal, never by pasting them into chat.

Core live budgets remain t06 up to 6 requests, t07 up to 4, t09 up to 2 before
approved retries. Explain the budget and obtain approval for the task. A failed
live call is not silently replaced with replay. Local work can remain saved
while live verification is pending. The three-question reflection command is
available after class; no external submission is used.

## Teaching boundaries

Keep every check tied to function calling, tools or MCP. A boundary case such
as a reading equal to a reference can illustrate testing briefly, but it must
not displace the tool-interface learning goal. Name/description, parameter schema
and result envelope describe our interface design; execution also needs the
function, validation and application dispatcher. StatsArgs is the local validation
model; model_json_schema() produces the parameter description sent to DeepSeek.

Lecture maintenance records and seminar temperatures concern the same CONV-3,
but are separate synthetic data sources, not evidence of a causal link. The
lecture ok envelope and seminar status envelope differ. Explain the actual fields;
neither is a universal function-calling or MCP standard.
