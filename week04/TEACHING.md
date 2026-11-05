# Week 4 teaching script

Apply the current installed OUTPUT.md, persona.md and MENTOR.md. This saved guide supplies the curriculum, not permission to skip the final student-visible reply.

## Start with the problem

Begin with the brain-and-hands story, then the complete CONV-3 request. Do not begin a fresh course with installation commands or a list of Python filenames. Setup comes when the first experiment needs it. Use the learner's chosen resume or new-session route.

## Keep the interaction natural

Teach one manageable idea, then wait for an actual answer or action. Use the student_script paragraphs as natural speaking notes, not labels to recite. Connect each explanation to what the learner just saw. Define a new word before relying on it. Do not say "the application disposes", "evidence-backed orchestration" or other slogans in place of an explanation.

Offer foundation choices before the related exercise: I understand - continue / Explain briefly / Show an example. Respect the choice while keeping the actual exercise and understanding requirements. Use native choice cards where the host supports them, with the delivery sequence in OUTPUT.md.

Give two gradually clearer hints with a real learner response between them. Then offer more hints or an answer explanation. After explaining an answer, ask for the learner's own explanation and assess that new response before continuing. A test passing or a copied answer is not that explanation.

## A lesson step and an experiment are different

before_run steps explain the problem, relevant code and prediction. Save the learner's real choice or code before running. after_run steps must wait for the actual report. Read the observed values, explain their structure and compare them with the prediction. Do not replace an observation with the expected answer printed on a slide.

Use lesson-next only after the explanation has actually appeared in the formal reply and the learner continues or completes the required check. Questions, translation, pauses and source inspection do not advance a step. Acknowledge an already delivered explanation at the next natural turn when needed, as OUTPUT.md describes.

Do not ask the same question twice just because it appears in both discussion and a task requirement. If an actual learner response already answers the current requirement, save that response with the relevant helper and evaluate it.

## Sources and evidence labels

Show the original PDF page in review mode, talk through its diagram, and then open the related actual code. The PDF calls the same synthetic example M12; the current course calls it CONV-3. Explain this once. Use each slide card's clarification where the old slide simplifies or overstates the implementation.

A teacher capture is a saved real DeepSeek exchange, not a new student call. A scripted planner is a rule program, not an LLM replay. Fault injections are deliberate tests, not measurements of the model's error rate. A tool test executes real local code but does not validate a model's planning ability.

Inspect actual output before speaking about a result. Use the saved status, reason, counters and evidence IDs. Never label a timeout from the outside watchdog as a correctly implemented inner stopping rule. No true unbounded loop is executed.

## Course scope and saved work

Core timing is 2 x 50 minutes, with the break outside those 100 minutes. The four exercise groups use small function bodies. W4.2 has two required subparts: the goal checklist and the statistics-input comparison, within the same 15 minutes. Keep the supplied validation and error branches. Extra live runs, retries, timeouts and handoffs are optional topics in the menu.

The seminar helper saves learning progress, answers, code and experiment records. The classroom agent uses in-memory execution state and does not yet support cross-process checkpoint recovery. A readable trace is not a resume button for that agent. Week 5 covers that separate problem.

## Learning modes

- **Review lecture + code**: Follow the brain-and-hands story, see where a simple loop fails, revisit the slide diagrams, and build the missing checks with small code exercises.
- **Start seminar practice**: Start the same experiments and four coding groups, including two short parts in W4.2. Get short concept explanations when you need them, with the same understanding checks.

## t01 - Why we need a loop

Core time: 8 minutes. Completion weight: 8%.

Purpose: Connect the earlier weeks to a task with dependent tool actions.

### Follow the lecture story, inspect experiments, explain the code, then build each part.

#### We have a brain and hands. What is missing?

Phase: before_run.

In Week 1, we connected an LLM to a local Python program. You can think of this as giving the program a brain: it could understand a request and produce a response.

In Week 3, we gave it hands. The model could request a tool, and our Python program could run that tool.

But having a brain and hands does not automatically mean the program can finish a whole task.

Here is the task we will work on today: Check CONV-3's temperature readings for 2 March 2026, 10:00 to 10:25 (UTC+08:00). Read its reference limit, calculate the share of readings above that limit, and give a summary we can check.

Before we run anything, think about what we would need to check the final answer. Temperature readings are one part. We also need the reference limit and a calculation that really uses those inputs.

PDF page 2: slides/slide-02.png

- Read the request first, before naming any software modules.
- Point to FETCH, REFERENCE and COMPUTE. These describe three jobs done by the supplied tools.
- Point to JUSTIFY. This asks us to show where the answer came from; it is not automatically a fourth tool.

Code connection: Later, Task stores the confirmed machine, window and goal. Do not begin this opening by reading its class definition.

Clarification: Week 3 used a one-round teaching program. Function calling itself is not limited to one call. The Week 2 miniGPT is not the live tool-calling model used here; DeepSeek supplies the live planner.

#### Follow the two inputs to the calculation

Phase: before_run.

Follow the two arrows into temperature_stats. One brings the readings; the other brings the reference limit.

We can read the reference before or after querying the temperatures. But we cannot use the actual values in the calculation until both results are available.

For this task we have three domain tools. The checked summary can be made by Python from their verified fields. A separate model request to write prose would not be a fourth tool call.

PDF page 6: slides/slide-06.png

- Trace query_temperature to VALUES, then get_machine_spec to LIMIT.
- Pause where the arrows meet. Ask what would be missing if either source had not returned.
- Follow the final arrow to SUMMARY and explain that its numbers must point back to the records.

Code connection: Task.goal names what we are trying to finish; verify will later express the required evidence in Python.

Checkpoint: We have the five temperature readings but have not read the reference file. What can we say at this point?

- A: The full report is finished because the query worked.
- B: We have one part of the evidence; the reference and checked calculation are still missing.
- C: The program must guess the reference so that it can finish.

Wait for the actual response. Keep the answer and hints private until the support rules allow them.


### Start from the exercises with the explanations and checks needed for each task.

#### What would finish this request?

Phase: before_run.

In Week 1, we connected an LLM to a local Python program. You can think of this as giving the program a brain: it could understand a request and produce a response.

In Week 3, we gave it hands. The model could request a tool, and our Python program could run that tool.

But having a brain and hands does not automatically mean the program can finish a whole task.

Today we will use that connection to work on a longer request: Check CONV-3's temperature readings for 2 March 2026, 10:00 to 10:25 (UTC+08:00). Read its reference limit, calculate the share of readings above that limit, and give a summary we can check.

List what you would need before signing off the answer. Then we will inspect a single API request and see which pieces it actually supplies.

Checkpoint: We have the five temperature readings but have not read the reference file. What can we say at this point?

- A: The full report is finished because the query worked.
- B: We have one part of the evidence; the reference and checked calculation are still missing.
- C: The program must guess the reference so that it can finish.

Wait for the actual response. Keep the answer and hints private until the support rules allow them.

#### Keep the task fixed while you investigate

Phase: before_run.

The task names a machine, a time window and a goal. Keep those fields fixed while checking each result.

The time window includes 10:00 and excludes 10:25. A result for another machine or another window does not answer this request, even if the data looks sensible.

You can look at the task file before running anything. You do not need to rewrite the three tools from Week 3.

Source: seminar/state.py :: Task. Show at most 8 lines at a time.

- Read goal, machine_id, start and end as the confirmed request fields.
- The class describes the task; defining it does not query any records.

### After the actual output explanation


- Which parts of the CONV-3 task are still missing after a temperature query alone?

## t02 - Inspect one real API request

Core time: 8 minutes. Completion weight: 8%.

Purpose: Separate a model proposal from local execution and later feedback.

### Follow the lecture story, inspect experiments, explain the code, then build each part.

#### What comes back from one API request?

Phase: before_run.

Last week our teaching program stopped after one round of tool use. This was a choice in the program, not a limit of function calling.

Now we will inspect one DeepSeek request. We will pause when the response arrives, then inspect what our local tool execution adds. We will not ask the model for another step in this experiment.

The response may contain no tool request, one request or several. We will read what actually came back instead of trying to make the model fit a prepared story.

PDF page 4: slides/slide-04.png

- Locate the point where the Week 3 program asks for prose and stops continuing the task.
- Compare the checklist on the right with the information obtained so far.
- Ask who would have to start the next request: our Python application, or a function definition sitting in a prompt?

Code connection: demos.single_round_request sends one request, records the proposed calls, and shows what the application executed.

Clarification: The original slide uses a single-tool teaching cut. A response can propose multiple tools. A tool proposal is still not the same as a returned local tool result.

#### Read the request and the two pause points

Phase: before_run.

The program sends the task and the available tool definitions. The model response names what it wants the application to do.

The application still checks and executes local functions. It must send their results back in another model request if the next decision needs those results.

Choose a recorded teacher request or one live request with your own configured key. A teacher record is a saved real exchange. It is not a new call from your computer, and it is not a scripted model reply.

Source: lecture/demos.py :: single_round_request. Show at most 10 lines at a time.

Source: lecture/demos.py :: single_round_request. Show at most 12 lines at a time.

- Find the API request before reading the handling of tool_calls.
- Find the local execution after the response. Count proposed requests and actual executions separately.
- This experiment does not send the execution results to a second model request.

Next learner action: Predict what information the first response can contain and what still needs local execution.

#### What did this particular request do?

Phase: after_run.

Read the actual report with me. First locate the evidence label: a live run or a saved teacher API exchange.

Now count the proposed tool calls and inspect their names and arguments. Do not assume the count is one. Next look at which calls were actually executed and what they returned.

Compare the evidence now available with the task checklist. We are studying the missing execution and feedback steps, not claiming that every model response has the same number of calls.

If you selected the bundled teacher record, point to its two requests: get_machine_spec and query_temperature. After Python ran both, the saved check still listed stats as missing. The record contains no second model request. For a new live run, explain its actual calls and missing list instead.


Next learner action: Explain one difference between the API response and the result of running a local function.


### Start from the exercises with the explanations and checks needed for each task.

#### Inspect one request before adding a loop

Phase: before_run.

We will send one DeepSeek request, or read a saved real teacher request, and inspect it in two stages: the model response and the local tool results.

Look for tool_calls in the code. These entries ask the application to run functions. They are not temperature measurements.

There is no follow-up model request in this experiment. Predict what information cannot reach a later model decision until we add that step.

Source: seminar/demos.py :: single_round_request. Show at most 10 lines at a time.


Next learner action: Choose teacher-record or live mode, then predict the missing feedback step.

#### Read your request report

Phase: after_run.

Check whether this is a live exchange or an inspected teacher record. Keep that label in your explanation.

Find the proposed calls, the real local results, and any missing evidence. If the model proposed two calls, say two. If it returned text instead, report that too.

Which information would we need to include when asking the model what to do next?


### After the actual output explanation

- `lesson_result.json: evidence_kind`: Whether this was a new live exchange or inspection of a saved teacher exchange.
- `teacher route: observation.requests_made_now`: How many API requests this student action made; reading a record makes none.
- `single-round record: requested_tool_calls and response.message.tool_calls`: How many calls the actual response proposed, and their names and arguments.
- `single-round record: tool_attempts and observations`: What local tool code actually ran and the results or refusals that were saved.
- `single-round record: after.ready and after.missing`: What the verifier can conclude after those results, and which evidence is still absent.
- `single-round record: next_messages_not_sent`: The prepared continuation was not sent in this one-request experiment.

- Using the actual request report, explain what the model proposed, what Python executed, and what would need another round.

## t03 - Find two problems in a small loop

Core time: 10 minutes. Completion weight: 10%.

Purpose: Observe repeated work and unsupported completion in bounded fault demonstrations.

### Follow the lecture story, inspect experiments, explain the code, then build each part.

#### Try the smallest loop first

Phase: before_run.

The simplest idea is to repeat four actions: ask for a next step, run it, read the result, and ask again.

Keep the same conversation history. That means keeping the original task, the model request and its matching tool result, rather than starting over with only the first question.

A fixed workflow can also have conditions. For a small task it may be the simpler solution. Today we are learning to control a loop whose next action is proposed while it runs.

PDF page 8: slides/slide-08.png

- Start at PLAN and follow one trip around the circle.
- At OBSERVE, point back toward the next PLAN. The return value changes what can sensibly happen next.
- The Verify and stop rules on this teaching diagram are what we are about to build, not features that appear merely because we wrote while.

Code connection: demos.bare_loop lets us inspect a small loop with deliberately weak completion logic.

Clarification: The four named stages are this course's explanation of the loop. ReAct does not mean that we should save or display private model reasoning.

#### What could go wrong with that loop?

Phase: before_run.

We will try two deliberately difficult planners. One keeps asking for the same file. The other asks to finish before collecting the evidence.

These are scripted fault injections so that everyone can inspect the same control problems. They do not measure how often a real model makes these mistakes.

An outside step and time limit will end the demonstration. We will never leave an unbounded loop running against a paid API.

Source: lecture/demos.py :: bare_loop. Show at most 12 lines at a time.

Source: lecture/demos.py :: bare_loop. Show at most 4 lines at a time.


Next learner action: Predict what is missing in each case: a completion check, a limit on continued work, or both.

#### One loop repeats; the other stops too soon

Phase: after_run.

Read the two actual traces. In the repeat case, identify what useful evidence was added and what was only repeated.

In the early-finish case, compare the claimed ending with the evidence still missing. A request to finish is not proof that the task is finished.

The outside limit stopped our demonstration safely. That is different from the learner's loop correctly deciding when to stop. We need to add those checks inside the application.

Checkpoint: Which pair of additions addresses the two demonstrated problems?

- A: A longer prompt and a more confident final sentence.
- B: An evidence check for completion, and limits on unproductive or excessive work.
- C: Always stop after the first successful tool call.

Wait for the actual response. Keep the answer and hints private until the support rules allow them.


### Start from the exercises with the explanations and checks needed for each task.

#### Test two bad next-step proposals

Phase: before_run.

Read the small loop, then predict what it will do with a planner that repeats one request and a planner that asks to finish too soon.

We use known scripted proposals to test the program. The demonstration has an outside limit even though its own teaching logic is deliberately incomplete.

Source: seminar/demos.py :: bare_loop. Show at most 12 lines at a time.


Next learner action: Predict the two failure modes before running the bounded demonstration.

#### Locate the missing check in each trace

Phase: after_run.

Find the first repeated action with no useful new evidence. Then inspect the other run's finish request and list the evidence it did not collect.

Explain which part of the program should decide whether that finish request is accepted. The outside demonstration limit is not evidence that the internal loop works.


### After the actual output explanation

- `demo.json: case and evidence_kind`: Which deliberately scripted test this is; it is not a live model failure.
- `decisions and tool_attempts`: Separate requests for a next step from actual local executions.
- `naive_status and diagnostic_check`: Compare what the weak loop claimed with what the outside evidence check found.
- `ending and external_demo_cap`: Identify the outside limit that contained a repeated loop. It does not repair the inner logic.

- What was missing from each deliberately weak loop, and what did the outside limit prove?

## t04 - Check a proposal before it runs

Core time: 9 minutes. Completion weight: 9%.

Purpose: Inspect the execution checks and their effect on real tool attempts.

### Follow the lecture story, inspect experiments, explain the code, then build each part.

#### Should this proposed action be allowed to run?

Phase: before_run.

Before we fix the whole loop, there is a smaller question: is this particular action allowed to run?

The program accepts only registered tool names. It checks the argument types and values, then checks that the requested machine and window match the task the user confirmed.

A correctly written request about another machine is still the wrong request for this task. A rejection should be recorded and returned as feedback; it must not execute the tool.

PDF page 26: slides/slide-26.png

- Read the three allowed tool names. There is no route here for arbitrary Python text.
- Follow the wrong-machine example and stop before execution.
- Separate these execution checks from the later check that statistics use the collected readings.

Code connection: ToolRunner.execute performs the execution checks before starting a local worker.

Clarification: In this implementation, matching_stats checks the statistics' link to collected evidence after execution. Do not claim the input-provenance check already happened at the execution gate.

#### Find the check before the worker starts

Phase: before_run.

Read the beginning of ToolRunner.execute. The name is checked against the allowed set, and the argument model validates the proposed values.

Next inspect the task checks. They compare the requested machine and time window with the confirmed task.

Predict what the actual tool-attempt counter will do for a rejected request, then run the small gate demonstration.

Source: lecture/gateway.py :: ToolRunner.execute. Show at most 11 lines at a time.

Source: lecture/gateway.py :: ToolRunner.execute. Show at most 7 lines at a time.


Next learner action: Choose one invalid request and predict whether any tool code will run.

#### A refused request is still useful feedback

Phase: after_run.

Read the rejection code and message in the actual output. Check the number of real tool attempts rather than guessing from the number of requests.

The program can explain why it refused a request. Recording that refusal does not turn it into successful equipment data.

Checkpoint: A proposed request uses the wrong machine and is rejected before execution. What should happen?

- A: Record the rejection and return feedback, without counting a tool execution that never happened.
- B: Run it anyway because the machine identifier has the correct type.
- C: Treat the error message as the requested machine specification.

Wait for the actual response. Keep the answer and hints private until the support rules allow them.


### Start from the exercises with the explanations and checks needed for each task.

#### Will this request reach a tool?

Phase: before_run.

Inspect the execution checks, then classify the supplied unknown-tool, wrong-argument and wrong-machine requests.

For each one, predict whether the worker should start. We will check the actual attempt counter after running the gate demonstration.

Source: seminar/gateway.py :: ToolRunner.execute. Show at most 11 lines at a time.

Source: seminar/gateway.py :: ToolRunner.execute. Show at most 7 lines at a time.


Next learner action: Predict one rejection and explain which condition should cause it.

#### Check whether your predicted rejection happened

Phase: after_run.

Compare the real rejection message and attempt count with your prediction.

If a request is well formed but belongs to another task, identify the task-scope check. A type check alone is not enough.


### After the actual output explanation

- `demo.json: rows[].arguments`: The actual proposed inputs for each gate test.
- `rows[].result.status and rows[].result.error`: Whether the request was refused and the stated reason.
- `rows[].tool_attempts`: Whether any local tool execution occurred. A recorded refusal need not be an execution.

- Use one rejected request to explain why the tool did not run and how you can tell from the output.

## t05 - Keep the result in a reliable record

Core time: 15 minutes. Completion weight: 15%.

Purpose: Write State.record and check that later edits cannot alter the saved observation.

### Follow the lecture story, inspect experiments, explain the code, then build each part.

#### Where do we keep what happened?

Phase: before_run.

We can now decide whether a request may run. After it runs, we need to keep what actually happened.

Think of State as the program's notebook. It contains the confirmed task, the observations and the counters that control the run.

An Observation is one entry in that notebook. Context is the part of the notebook we choose to show the planner. These are related, but they are not the same object.

PDF page 23: slides/slide-23.png

- Read the State column as information owned by Python.
- Follow context() across the diagram. It selects and copies information for the next decision.
- Point out that a claim in a model message cannot directly change the runtime's status or counters.

Code connection: Observation defines one record; State.context selects information for the planner.

Clarification: Use field(default_factory=list) for separate lists in the executable dataclass. The slide's shortened default-value display is not code to copy unchanged.

#### The result has two places to go

Phase: before_run.

Follow the upper arrow first. The result goes into the program's record so that the verifier and a human can inspect it later.

Now follow the lower arrow. The result also goes back to the planner so that its next decision can use it.

Observe keeps the result, including an error or refusal. It does not decide that the task is complete. We will write that separate decision next.

PDF page 25: slides/slide-25.png

- Trace the result into the ledger. Name the observation ID, inputs and returned value.
- Trace the other route into the conversation. A tool message must match the original tool-call ID.
- Ask what each route is for before introducing any new class syntax.

Code connection: State.record saves the observation; planner.observe returns feedback. State.context also supplies a selected view of evidence.

Clarification: The scripted planner can read State directly. Removing observe from it does not prove model amnesia. Check actual message pairing when examining the live interface.

#### Save a small record without changing its history

Phase: before_run.

Look at Observation. Its fields tell us which tool was requested, which inputs were used, and what came back.

When we save arguments and results, we need our own copies. Otherwise a later edit to a nested dictionary or list could also change what looks like an old observation.

Complete State.record in three small steps: give the observation an ID, store separate copies, and add the record and its event. Keep the provided function signature.

Source: seminar/state.py :: Observation. Show at most 8 lines at a time.

Source: seminar/state.py :: State.log. Show at most 6 lines at a time.

- Observation describes the fields, not the decision about completion.
- State.log already shows how copy.deepcopy protects event fields.
- Use the existing fields and log method; do not replace the whole State class.

Next learner action: Write the body of State.record in chat, then predict what should happen if the original dictionary changes.

#### Did the saved observation keep its own values?

Phase: after_run.

Read the state-test results and the saved observation example. Locate the ID, tool, arguments, result and reused fields.

Inspect the result of changing the original nested object after it was recorded. Explain why the saved observation should keep the earlier values.

A new log entry only tells us that something was recorded. Whether it adds useful evidence is a later check.


### Start from the exercises with the explanations and checks needed for each task.

#### Keep the tool result so that we can check it later

Phase: before_run.

Your first code task is State.record. It receives a tool name, arguments, a result and a reused flag.

Read Observation and the existing log method. Use them to give the result an ID, keep separate copies, and append a record and event.

Before coding, choose whether you want a short explanation of dictionaries, dataclasses or deep copies.

Source: seminar/state.py :: Observation. Show at most 8 lines at a time.

Source: seminar/state.py :: State.log. Show at most 6 lines at a time.


Next learner action: Write a small function body, then predict the saved value after the original object is changed.

#### Inspect the copy test and one saved observation

Phase: after_run.

Check which tests passed and which still need work. Use the actual observation fields to explain where the tool inputs and outputs are kept.

Then explain the copy test. Do not just report that it is green: tell me what could have gone wrong if two variables referred to the same nested object.


### After the actual output explanation

- `lesson_result.json: checks[].passed and checks[].log`: The test outcome and where to read a failed assertion.
- `student_observation.json: observation`: The ID, tool, arguments and result saved by the learner's own function.
- `original_arguments_after_edit and original_result_after_edit`: Compare the changed original objects with the unchanged saved values.
- `input_is_teaching_example`: This small mutation check uses deliberate teaching inputs; it is not a sensor measurement.

- Why did the saved observation need its own copy, and why is recording a result different from verifying it?

## t06 - Check the task and the calculation inputs

Core time: 15 minutes. Completion weight: 15%.

Purpose: Write the goal checklist and the exact statistics-input comparison as two short subparts.

Required code subparts (save one learner body at a time):

- W4.2A / verify: Write the goal checklist in verify and return the required evidence, gaps, IDs and facts.
- W4.2B / stats_inputs: Write statistics_inputs_match so it compares the calculation argument record with the saved values and registered limit.

Time within this 15-minute task: 3 minutes explanation, 4 minutes W4.2A, 3 minutes W4.2B, 3 minutes tests/output and 2 minutes understanding. Both code bodies are required before running the task.

### Follow the lecture story, inspect experiments, explain the code, then build each part.

#### W4.2A: what would let us accept the report?

Phase: before_run.

We can store results now. But a pile of records does not tell us whether the task is complete.

Read the checklist with me. We need the right readings, the registered reference, a calculation using those inputs, and a report whose numbers point back to those records.

Your first small function, verify, will decide which pieces this goal requires and name any gaps. A readings query can finish with an empty list; a percentage report cannot turn no readings into 0%.

PDF page 9: slides/slide-09.png

- Read each row as a question we can ask about the collected observations.
- Point to the observation-ID slots. They link a fact to the record that supports it.
- Separate the checklist from the next question: did the calculation actually use those records?

Code connection: W4.2A completes verify and returns Check. W4.2B will supply the input comparison used by matching_stats.

#### W4.2B: the same answer can come from different inputs

Phase: before_run.

The slide uses [1, 2] as an obvious example of wrong inputs. Now try a harder case: our saved readings are [82, 87, 91, 94, 97], but the calculation used [82, 88, 90, 94, 97].

Both lists have five readings. Both give a mean of 90.2, a maximum of 97, and four readings above 85. Even all of those matching results would not prove that the calculation used our saved readings.

The arguments record what the tool was given. Compare that whole record with the saved list of values and the saved limit. This is the small check you will write in statistics_inputs_match.

PDF page 14: slides/slide-14.png

- Compare the observed readings with the arguments passed to the calculation.
- Locate the slide's if obs.arguments != {...} check. It asks whether the input record matches, not whether the list lengths match.
- Then follow the numerical checks. We still need them: correct inputs do not excuse an incorrect output.

Code connection: matching_stats calls the new statistics_inputs_match before checking the returned numbers. You implement the input guard as well as the goal checklist.

Checkpoint: The count, mean, maximum and above-limit fraction all match, but two input values differ from the saved readings. What should we do?

- A: Accept the report because every displayed statistic matches.
- B: Reject this statistics record because its inputs differ from the saved readings.
- C: Accept it if the model says the differences are unimportant.

Wait for the actual response. Keep the answer and hints private until the support rules allow them.

#### Prepare the two short function bodies

Phase: before_run.

Look at Check first. ready says whether the required evidence is present. missing names the gaps. evidence_ids links the accepted facts to their observations.

For W4.2A, use matching_sources and matching_stats in verify, then choose the required pieces from the goal. The report goal also needs nonempty readings.

For W4.2B, statistics_inputs_match receives an observation, the values taken from the matching query, and the limit taken from the specification. Its job is to return True only when the observation arguments match both inputs.

A dictionary holds named values; a list holds the ordered readings. Comparing the dictionaries checks their fields and the list contents. A length comparison cannot do that job.

The caller skips a statistics observation when this helper returns False, then continues looking for suitable evidence. It still checks the numerical output after a True result.

Source: seminar/verification.py :: Check. Show at most 8 lines at a time.

Source: seminar/verification.py :: matching_stats. Show at most 12 lines at a time.

Source: seminar/verification.py :: statistics_inputs_match. Show at most 8 lines at a time.

- Follow values back to query records and limit back to the specification.
- Read obs.arguments as what this particular tool call received, not as a remembered expected answer.
- The supplied caller handles searching and numerical checks; do not remove them.
- Check.progress tracks evidence types, not the seminar percentage.

Next learner action: After these preparation steps, write your verify body first. Mentor saves it and then asks separately for statistics_inputs_match. Both are required before the t06 tests run.

#### Read the two checks separately

Phase: after_run.

Read the actual comparison_rows. Start with the correct-input case and identify its arguments, inputs_match and check.ready.

Next find same_count_same_summary_wrong_values. Compare its tool_statistics with the correct case. Then read same_summary_as_correct, inputs_match and check.missing. Use the observed values; do not merely repeat the expected answer.

The wrong-limit case checks the other input. The empty-data cases check the goal checklist. These are different reasons for refusing a report.

Now read your saved statistics_inputs_match and follow its return value into matching_stats. Explain why the input comparison and numerical checks are both needed.

Source: seminar/verification.py :: statistics_inputs_match. Show at most 10 lines at a time.

Source: seminar/verification.py :: matching_stats. Show at most 12 lines at a time.


### Start from the exercises with the explanations and checks needed for each task.

#### W4.2A: choose what this goal needs

Phase: before_run.

We will complete two short functions in this task. First, verify chooses what evidence the current goal needs. Second, statistics_inputs_match checks which values and limit went into a calculation.

Read Check to see what verify must return. A specification lookup needs its matching specification; a readings query needs its matching query result; a report needs both sources and matching statistics.

An empty query can answer a readings request. A percentage report still needs actual readings to count. We will test that difference after saving both functions.

Source: seminar/verification.py :: Check. Show at most 8 lines at a time.


Next learner action: Explain which evidence the report goal needs before looking at the input comparison.

#### W4.2B: check what the calculation received

Phase: before_run.

Our query returned [82, 87, 91, 94, 97]. A different call used [82, 88, 90, 94, 97], with the same limit of 85. Both have count 5, mean 90.2, maximum 97 and above-limit fraction 0.8.

That is why checking the count, or even checking every summary value, is not enough. Compare obs.arguments with the complete expected argument record built from values and limit.

A dictionary comparison checks the named fields and the values they hold. The list inside it must contain the saved readings. The limit must also match the specification.

Read how matching_stats uses the Boolean returned by statistics_inputs_match. False skips this record; True allows the separate numerical checks to follow.

Source: seminar/verification.py :: statistics_inputs_match. Show at most 8 lines at a time.

Source: seminar/verification.py :: matching_stats. Show at most 12 lines at a time.


Next learner action: After preparation, write your verify body first. Mentor then asks separately for statistics_inputs_match and a prediction before running the tests.

Checkpoint: Five readings produced the same summary as our saved readings. Which check is still necessary?

- A: Check only that the tool response has status ok.
- B: Compare the full calculation arguments with the observed values and reference limit.
- C: Check the number of readings one more time.

Wait for the actual response. Keep the answer and hints private until the support rules allow them.

#### Explain why each record was accepted or rejected

Phase: after_run.

Read the actual comparison_rows and find the case whose summary matches despite different inputs. Explain its inputs_match and check.missing fields.

Then compare the wrong-limit case and the two empty-data goals. Identify which small function checks each issue.

Use your saved guard to explain why correct arithmetic alone cannot show that a result answers this task.

Source: seminar/verification.py :: statistics_inputs_match. Show at most 10 lines at a time.


### After the actual output explanation

- `student_observation.json: stages[].check`: Watch ready, missing, progress, evidence_ids and facts change as actual tool results are added.
- `comparison_rows[].arguments and tool_statistics`: Compare what each call received with the summary it returned. These cases are deliberate local teaching inputs.
- `comparison_rows[].inputs_match and same_summary_as_correct`: Separate the input comparison from an equal-looking summary. The same-summary wrong-input case makes this difference visible.
- `comparison_rows[].check.ready and check.missing`: Read whether that case supplies acceptable evidence for the report.
- `observations`: The actual local results used for the checks.
- `empty_report_goal_check and empty_readings_goal_check`: Compare the completion decisions for the same empty query under two different goals.

- Explain why an empty query can finish a readings task but cannot finish the requested percentage report.
- In the same_count_same_summary_wrong_values case, why must we reject the statistics even though its count, mean, maximum and above-limit fraction match? Explain which inputs your guard compares.

## t07 - Set limits on continued work

Core time: 10 minutes. Completion weight: 10%.

Purpose: Write the stopping checks without confusing a limit with success.

### Follow the lecture story, inspect experiments, explain the code, then build each part.

#### Not finished, but not allowed to run forever

Phase: before_run.

The verifier stops us from declaring success too early. It does not give us permission to keep trying forever.

Read the four endings. Completed means the evidence passed. Stopped means a limit ended the run. Failed means an operation could not be completed. Needs_human means someone must clarify or supply something.

These endings ask for different follow-up work. The word stopped by itself does not tell us that we have a usable report.

PDF page 28: slides/slide-28.png

- Compare completed with stopped before reading the other two boxes.
- For each example, point to both the status and the reason.
- Ask what the user would need to do next for a missing machine identifier.

Code connection: stop_reason returns a limit reason or None. The runtime chooses an honest ending.

#### More requests do not always mean more progress

Phase: before_run.

The program reads the same frozen specification again. What useful evidence did the second request add?

A repeated request can increase the decision count while the real execution count stays the same because a saved result was reused.

Keep steps, tool_attempts and no_progress separate. They answer different questions: how many choices, how many executions, and how many rounds without useful new evidence.

PDF page 31: slides/slide-31.png

- Follow the first specification read and its new evidence.
- Compare the next two observations with the first one. New IDs do not make the same information new evidence.
- Read the no-progress count beside each round.

Code connection: Config sets the limits; stop_reason checks the current state; the runner separately bounds individual attempts and timeouts.

#### Write a stop reason, not a success message

Phase: before_run.

Read Config first. Its limits are ordinary values the program can compare with the current run.

Complete stop_reason so it returns the appropriate limit reason, or None if the run may continue. Follow the provided order when more than one limit has been reached.

The loop needs its whole-run limit, and each operation needs a timeout too. A counter cannot interrupt the first tool if that tool never returns. Token usage is reported after a response, so its threshold cannot guarantee a prepaid spending cap.

Source: seminar/controls.py :: Config. Show at most 12 lines at a time.

Source: seminar/controls.py :: remaining_seconds. Show at most 4 lines at a time.


Next learner action: Write the guard conditions and predict what happens at exactly max_steps, not just above it.

#### Which limit stopped this case?

Phase: after_run.

Read the actual boundary tests. Notice the equal-to-limit case and the difference between a disabled no-progress check and the step limit that remains active.

A returned limit reason says why we must stop trying. It does not supply any missing readings or make a report complete.


### Start from the exercises with the explanations and checks needed for each task.

#### Stop a run that cannot usefully continue

Phase: before_run.

The task may still be incomplete when a step or time limit is reached. Complete stop_reason without changing that situation into success.

Use Config and remaining_seconds to read the existing limits. Keep the limit comparisons in the documented order.

Predict the boundary at steps equal to max_steps, then run the guard tests after saving your code.

Source: seminar/controls.py :: Config. Show at most 12 lines at a time.

Source: seminar/controls.py :: remaining_seconds. Show at most 4 lines at a time.


Next learner action: Write the stopping conditions and explain what None means to their caller.

#### Read the boundary cases

Phase: after_run.

Find the actual result for each tested limit and explain one boundary in your own words.

Explain why reaching that limit is a stopped run rather than a completed report.


### After the actual output explanation

- `student_observation.json: config`: The limits used in this boundary demonstration.
- `rows[].steps, no_progress and elapsed_at_least_seconds`: The deliberately constructed boundary values.
- `rows[].returned_stop_reason`: What the learner's function returned for that case.
- `inputs_are_boundary_examples`: These are test situations, not measurements of a long real run.

- Explain one tested limit and why it ends an attempt without proving that the task succeeded.

## t08 - Connect the pieces inside the loop

Core time: 13 minutes. Completion weight: 13%.

Purpose: Connect execution, feedback and a fresh check in the provided runtime.

### Follow the lecture story, inspect experiments, explain the code, then build each part.

#### Put the checks in the right places

Phase: before_run.

We now have the pieces. Let us follow one round and decide where each belongs.

At Gate A, the program checks the evidence, limits and run status. It may continue, complete the task, stop at a limit, report a failure, or ask for help.

If it continues, the planner proposes an action. Gate B checks whether a proposed tool request may run. The tool returns a result; Observe records and returns it; Verify checks what the new result proves. Then we return to Gate A.

PDF page 27: slides/slide-27.png

- Begin at the completion check before the next planner request.
- Follow the loop to the runner, then follow the result into observe and the next verification.
- Return to the top. Ask where a fourth unnecessary action would be prevented.

Code connection: run_agent keeps the control branches. complete_tool_step joins execution, feedback and the updated check.

Clarification: Gate A and Gate B are teaching names for the control decision and execution checks. They are not two extra models. finish and human are control requests, not ordinary tools.

#### Connect the result to the next check

Phase: before_run.

Read _update_check. It compares the kinds of evidence now available with the previous check, updates no_progress and records what the verifier found.

The provided run_agent handles completion, limits and error endings. Your small helper needs to run the allowed action, return its result to the same planner, and get a fresh check.

Use the new check after execution. A check made before the action cannot describe evidence that has only just arrived.

Source: seminar/runtime.py :: _update_check. Show at most 10 lines at a time.

Source: seminar/runtime.py :: complete_tool_step. Show at most 10 lines at a time.


Next learner action: Write complete_tool_step in chat. Predict why using the old check after execution could cause an unnecessary next round.

#### Did every result reach the next decision?

Phase: after_run.

Read the runtime test results. Find the checks for a normal completion, a refused early finish and no extra action after completion.

Explain where the result is recorded and where feedback reaches the planner. In a live exchange, the tool message must match the model request it answers.

The scripted planner can inspect State directly, so a fake memory experiment that merely deletes observe would be misleading. Use the actual protocol tests to check the live message connection.


### Start from the exercises with the explanations and checks needed for each task.

#### Connect execution, feedback and the new check

Phase: before_run.

Complete the small helper inside the existing runtime. The surrounding branches for completion, errors and limits stay in place.

Follow an action through runner.execute, planner.observe and _update_check. Return the observation and updated check in the form used by the caller.

Predict what could go wrong if the caller used a check made before the tool ran.

Source: seminar/runtime.py :: complete_tool_step. Show at most 10 lines at a time.

Source: seminar/runtime.py :: _update_check. Show at most 10 lines at a time.


Next learner action: Save your helper body, then run the runtime tests.

#### Explain a runtime test using the actual calls

Phase: after_run.

Inspect the actual runtime test output and choose a case that checks feedback or completion.

Point to the operation that gives the next check its new evidence. Explain why a finish request still needs verification.


### After the actual output explanation

- `student_observation.json: run.status and run.reason`: How the local run ended and why.
- `run.steps, run.tool_attempts and run.trace`: Follow proposals, actual executions, feedback and fresh checks.
- `run.report and planner_kind`: Read the checked report while retaining the scripted-planner label.

- Where does the new result enter the next check, and what stops an unnecessary action after completion?

## t09 - Rerun the cases and read the evidence

Core time: 8 minutes. Completion weight: 8%.

Purpose: Use actual traces to compare a complete task with stopped or rejected attempts.

### Follow the lecture story, inspect experiments, explain the code, then build each part.

#### Try the original cases with the completed loop

Phase: before_run.

Return to the cases we used before adding the controls. This time your saved code will run them.

Predict the normal task, the repeating planner and the planner that asks to finish too early. We will compare their actual evidence and ending reasons.

Read the slide as a reference design, not as a result from your computer. The exact counts we discuss must come from your run. Keep the outside test limit in place.

PDF page 38: slides/slide-38.png

- Read the scenario column before looking at the reference outcome.
- Keep decisions and actual attempts in separate columns.
- Ask which check should end each scenario and what evidence would justify that ending.

Code connection: The comparison driver runs the student loop and writes the counts and ending reasons for inspection.

#### Find the event that explains the ending

Phase: after_run.

Read the actual normal run first. Follow a decision to its tool result, then to the verifier event that records what is still missing.

Now read the bounded failure comparisons. For a refused early finish, locate the missing evidence and the feedback. For a repeat, distinguish another request from another real tool execution.

Find the first event that explains the ending, not just the last line. If an outside watchdog ended a test, report that as a failed internal control, not as successful stopping logic.


Next learner action: Use one actual trace to explain why this run ended where it did.


### Start from the exercises with the explanations and checks needed for each task.

#### Predict and run the complete comparison

Phase: before_run.

Your four code changes are now in place. Predict the result of the normal request, a repeated request and an unsupported finish request.

Use the same supplied tools and data. We want to see what the controls changed, not change the task to make the result look better.


Next learner action: Make a short prediction for the scenarios, then run the bounded comparison.

#### Explain what your program actually did

Phase: after_run.

Read the actual comparison rows and open the relevant trace when a row needs explanation.

Explain a status, its reason, the decision count and the actual execution count. Point to the evidence behind a completed report or to the missing evidence behind an unfinished run.


### After the actual output explanation

- `demo.json: rows[].condition`: The test situation used for this comparison.
- `rows[].status and rows[].reason`: The actual ending, not a generic success message.
- `rows[].decisions and rows[].tool_attempts`: Compare requests for a next step with actual tool executions.
- `linked run.json: trace and report.evidence`: Find the event that explains the ending and the source IDs used in any report.

- Choose one actual comparison run. Explain its ending, its decision and execution counts, and the event that caused that ending.

## t10 - Explain what your loop now does

Core time: 4 minutes. Completion weight: 4%.

Purpose: Return to the original task and save a brief learning reflection.

### Follow the lecture story, inspect experiments, explain the code, then build each part.

#### What did we add to the brain and hands?

Phase: before_run.

Return to the request we started with. At first, our program could ask a model and run a tool. Now it can keep results, check what they prove, and decide whether another action is needed and allowed.

Explain the loop to a classmate using this CONV-3 example. Name where an action is checked, where its result is saved and returned, and where completion is decided.

Your seminar progress, code and answers are saved. The small agent you built is a different program: it does not yet resume a partly executed run after the process closes. We will study that problem in Week 5.

PDF page 39: slides/slide-39.png

- Follow the three evidence records back to the original task.
- Point to the ending and ask what made completed justified.
- Use the next-week note to separate learning progress from agent execution checkpoints.

Code connection: Save the current work and use the existing review command for a longer reflection when you want one.


### Start from the exercises with the explanations and checks needed for each task.

#### Explain your loop using the experiment you just ran

Phase: before_run.

Use your own trace to explain how a tool result changed the next decision or the ending.

Name one check that prevents false completion and one that stops a run from continuing too long.

Your learning session is saved. Resuming this seminar is separate from resuming a half-executed agent run; the latter is a Week 5 topic.


### After the actual output explanation


- In a few sentences: what does the loop add, which check mattered in your experiment, and what would you like to practise next?

## Optional topics

- **Try your loop with DeepSeek**: Use a real model to propose actions while keeping the tested runtime, verifier and limits.
- **Compare a temporary and a lasting error**: Inspect what changes after one bounded retry and count the actual attempts.
- **End a tool call that takes too long**: Inspect a local subprocess timeout and distinguish it from a whole-run limit.
- **Ask for missing information**: Inspect empty data or missing task fields, then read the specific handoff question.
- **Compare with a fixed workflow**: Compare the same task with a straightforward fixed Python workflow, which can also have conditions.
- **Try more boundary tests**: Inspect additional cases without removing the outside test limits.
