# Week 1: explain before asking

Use these notes with the task returned by tutor.py. They are teaching material,
not a script to dump in one response. The code action reads the student's actual
source and gives current line numbers. Paste the relevant short excerpt and name
the file and line span before discussing it. Do not rely on hardcoded line numbers
after student edits. Teach enough context for the next question, then pause.

## Task01: setup with Mentor Liu

Say: "Our Python program runs here. It sends a request to a model service. I will
prepare the Python environment and its libraries. You will enter your API key in
your own terminal, where it is hidden."

Explain a virtual environment as a course-specific Python folder. Run setup and
show the actual outcome in an observations block: the environment path, successful
package installation and Imports OK, or the real error. Show the exact configure
command returned by setup. Wait for the student's practical 'Done' before key-ready.
There is no quiz about version numbers, package installation or key handling.
After explaining the results, complete the task and begin the evidence discussion.

## Task02: readings versus causes

Explain the supplied CONV-3 facts before asking about them: the temperature rose
from 68 to 97 degrees C; the stated limit is below 85; current rose about 18%;
the fan was running and no abnormal vibration was reported. A reading describes
what was observed. A cause explains why it happened and needs supporting evidence.
Briefly distinguish a model, an application and an agent using this report task.
The result of this task is a fact/unknown summary. No model call is needed.

## Task03: follow the request and response

First define an object as a set of named values and a list as an ordered collection.
`choices` is a list; `[0]` means its first item. Attribute access on the SDK response
uses dots. Parsed JSON uses dictionary keys and list indexes.

Show this SDK structure before the prediction:

```text
response                     SDK response object
|-- id                       request identifier
|-- model                    model name
|-- choices                  list of possible replies
|   `-- [0]                  first reply
|       |-- finish_reason    why generation ended
|       `-- message
|           `-- content      reply text
`-- usage                    token counts
```

The SDK access is `response.choices[0].message.content`. The teaching script then
copies selected fields into a simpler dictionary. Read the public_response return
dictionary together; its shape is visible in the source BEFORE calling the model.

```text
saved api_exchange JSON
|-- request
|   `-- messages             list of system/user messages
|-- response
|   `-- choices
|       `-- [0]
|           `-- content      copied reply text; no message layer here
`-- metadata
    |-- request_id
    |-- usage
    `-- elapsed_seconds
```

Use this small JSON as an explicitly labelled STRUCTURE EXAMPLE, not a live result:

```json
{"response":{"choices":[{"content":"Example reply text","finish_reason":"stop"}]}}
```

The saved-file path is `response.choices[0].content` (JSON-path notation), or
`record["response"]["choices"][0]["content"]` in Python. Show run_api and
request_text to locate the engineering log and the system/user messages. Define
engineering evidence as supplied readings, logs and manuals. Metadata describes
the request: token counts do not describe the motor's temperature or condition.
Now ask the code-reading prediction, explicitly saying no execution is needed yet.

After the approved call, replace the illustration with a short fragment from the
ACTUAL api_exchange JSON. Point out request messages, the saved response content,
and one metadata value. Also show the api record's instructions/input/output fields.
Then ask trace. Do not require the learner to find the file unaided.

## Task04: student writes the prompt in chat

Show the actual current instructions.txt contents, including its placeholders.
Explain that they mark the parts the student will supply, not a finished prompt.
Show run_prompt, including its shared input, two instructions and two API calls.

Ask for a short English prompt with three ingredients:

- The task: organise the CONV-3 log for review.
- The evidence rule: use the supplied facts and do not make up a cause or reading.
- The output structure: two known facts followed by one item to confirm.

A partial scaffold is enough: "Read the supplied log and [state the task]. Use
[state the evidence rule]. Return [state the structure]." Explain what each blank
means. Do not present a polished complete answer for the student to copy.

Say: "Write your prompt here in the chat. I will save your wording into the file."
After the student responds, save it with write-prompt and show the saved text.
If the requirement is missing, point to that part and let them revise it themselves.
Define prompt_tokens and completion_tokens before predicting the difference.
The prompt comparison shares evidence and model settings, but its requested report
formats differ. It is a teaching comparison, not a controlled claim of prompt quality.

After one approved run (two planned calls), show short actual output excerpts and
the results token_table. Include input, output and total tokens, plus elapsed time.
Ask what actually changed. Do not assert that clear prompts always save tokens,
that vague prompts always cost more, or that larger requests always produce longer
replies. Length/structure constraints are useful controls, but actual counts vary.
Token counts and money are not interchangeable; rates and provider rules determine
the bill. No price calculation is required. Ask the structure/token check after
this explanation. Editing the prompt is a change to this request, not model training.

## Task05: context A/B/C

Show the messages created in run_context. A gives a random sample ID. B receives
only a new question. C resends the earlier messages with the question. Explain
which input contains the ID before asking the student to predict the effect.

After running, use actual A/B/C input and output values. C may fail despite having
the evidence; do not guarantee its answer. If relevant, compare prompt_tokens to
show that history is sent as input again. A shared API key alone does not send
that history. At 50%, offer the planned break and save a pause note if requested.

## Task06: structure checks and evidence checks

Introduce the terms with this table before code or questions:

| Check | What it asks | What a pass does not establish |
| --- | --- | --- |
| Schema | Are the required fields present, with the declared types and no extra fields? | That a claim is true |
| Evidence | Does the content agree with the supplied source rules? | That the sources are complete or the machine is safe |

JSON is a way of writing named data. A schema is a declared data contract. Show
FaultReport's four fields. observations and missing_information are lists of
strings; equipment_id and diagnosis can be strings or null. All four are required.
This demo performs source checks only after it can read a schema-valid report.
Its source matching is narrow; it is not a universal truth checker.

Use a clearly labelled illustration: `"diagnosis": "Confirmed bearing failure"`
has a permitted string type, but that does not supply a source confirming a failed
bearing. The schema and evidence questions can therefore have different answers.
Show check_report and the teacher mutation function, then ask the prediction.

After running, display the actual checks_table, including each sample's origin,
valid_format and evidence_check_passed. Explain that null means not checked when
format failed. Distinguish actual_model_output from deliberate_mutations. If the
actual baseline is invalid, preserve it and explain why later samples are absent.
Then ask the concrete table-reading question. Do not call teacher alterations
natural mistakes made by DeepSeek.

## Task07: one repair, then reassess

Explain a content repair as another model request prompted by a detected problem.
The repair budget here is one. A network retry is a different mechanism. Show
run_failures: baseline, wrong-type alteration if possible, one real repair, and a
later deliberately unsupported diagnosis. Ask the prediction after this walkthrough.

Show the actual mutation_origin, damaged_output, actual_repair, repair_check and
unsupported_mutation_check. The last field may be null. Ask for a short failure
note referencing these named fields. A repaired format does not create missing
evidence. A 300-500-word reflection is optional after class, not required here.

## Task08: find unknowns in the actual report

Show the selected complete and missing_evidence input cases and run_seminar.
Explain how it makes the CSV columns and outcomes. 'Complete' is the case name;
it is not a promise that all facts needed to diagnose a cause exist.

After running, show both actual report fragments and the case_table next to the
CSV. Locate missing_information; count its list items separately for each case.
Locate diagnosis and read it exactly. Read the CSV Outcome values. An honest report
can list unknowns, leave diagnosis null and pass both checks as draft_for_review.
Do not assume the missing-evidence case must fail or hardcode any list length.
If the report is invalid, explain its actual limitation instead of inventing counts.
Now ask the three concrete case questions, one small part at a time.

## Task09: short scenarios, no code

Say explicitly: "This task is a short discussion. No code needs to run."
Explain sampling, stored memory, retrieval and tool control with brief situations.
Sampling concerns possible next tokens; repeating a request can yield the same
wording. Memory is application data loaded into context. RAG supplies retrieved
sources before generation; relevance and currency still need checks. In an agent,
the model proposes an action and application code checks and executes it.

After these examples, ask the learner to describe one concrete situation for each
idea in one sentence. 'Example' here means a scenario in words, not a new experiment.
These topics will return in later seminars. Offer optional hands-on extensions later.

## Task10: short exit check

Recap the work already done: request construction, prompt changes, context,
structure/evidence checks and bounded repair. Define any term the student still
finds unclear. Ask the five exit questions separately, allowing typed responses.
Use a small hint or revisit an observed result after a wrong answer; never submit
the student's answer for them. At 100%, give a personal recap and export the record.

## Response layout example

Use this as a layout, filling it with actual content; do not display placeholders:

```text
---
Task 6: Check the report

What we are doing and why: [one or two plain-English sentences]

Code: [file and current line numbers, followed by a short snippet]

> 🔬 Experiment observations
> [actual values from this task, with named fields]

What this means: [explain the structure and its limits]

Your question: [one specific question after the explanation]

📚 [Seminar week01 · X% complete]
```

Use genuine AskUserQuestion cards for MCQs. Do not reveal which card is correct or
add a 'Recommended' label to an assessed question. Open questions stay in chat.
