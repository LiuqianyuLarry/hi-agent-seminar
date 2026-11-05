"""Build the approved Week 4 teaching paths. This script never runs an API call."""
import ast
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'week04'
DECK = 'EEEE4149_Week4_Lecture_Building_an_Agent_from_First_Principles.pdf'
CASE = ('Check CONV-3\'s temperature readings for 2 March 2026, 10:00 to 10:25 '
        '(UTC+08:00). Read its reference limit, calculate the share of readings '
        'above that limit, and give a summary we can check.')


def ref(pack, file, symbol, slice_start=0, max_lines=10):
    return dict(pack=pack, file=file, symbol=symbol, slice_start=slice_start, max_lines=max_lines)


def focused_ref(pack, file, symbol, anchor, max_lines=10):
    """Select a real source window instead of always showing a function's setup lines."""
    folder = 'lecture_demo' if pack == 'lecture' else 'resources'
    path = ROOT / folder / file
    source = path.read_text(encoding='utf-8')
    scope = ast.parse(source).body
    for name in symbol.split('.'):
        found = next(n for n in scope if getattr(n, 'name', None) == name)
        scope = getattr(found, 'body', [])
    lines = source.splitlines()
    first = next(i for i in range(found.lineno - 1, found.end_lineno) if anchor in lines[i])
    return ref(pack, file, symbol, slice_start=first + 1 - found.lineno, max_lines=max_lines)


def check(prompt, options, correct, explanation, hint1, hint2):
    return dict(type='mcq', prompt=prompt, options=dict(zip('ABCD', options)),
                correct=correct, explanation=explanation, hint1=hint1, hint2=hint2,
                required=True, estimated_seconds=45)


def node(id, title, script, refs=(), phase='before_run', question=None,
         code_notes=(), action=None, evidence_fields=()):
    result = dict(id=id, title=title, phase=phase, logic=script[0],
                  explanation='\n\n'.join(script), student_script=list(script),
                  code_refs=list(refs), code_walkthrough=list(code_notes), slides=[],
                  one_next_action=action, evidence_fields=list(evidence_fields))
    if question:
        result['check'] = dict(question, id=id + '.check')
    return result


def slide(id, title, number, script, pointers, bridge, related=(), question=None,
          phase='before_run', correction=None):
    result = node(id, title, script, phase=phase, question=question)
    result['slides'] = [number, *related]
    result['slide_review'] = dict(source_deck=DECK, primary_slide=number,
        title=title, image=f'slides/slide-{number:02d}.png', related_slides=list(related),
        focus=script[0], visual_walkthrough=list(pointers), explanation='\n\n'.join(script),
        code_bridge=bridge,
        case_note='The original slides call this synthetic teaching machine M12. Our exercises use CONV-3. Explain this once, then use CONV-3 consistently.')
    if correction:
        result['slide_review']['clarification'] = correction
    return result


def oq(id, prompt, rubric, hint1, hint2, answer):
    return dict(id=id, type='open', prompt=prompt, rubric=rubric,
                hint1=hint1, hint2=hint2, worked_answer=answer)


FOUNDATIONS = {
    'messages': dict(id='messages', title='Requests, responses and conversation history',
        brief='A request is information our program sends to a service. A response is what comes back. A tool request inside that response asks our program to do something; it is not the result of doing it.',
        example='The model asks for get_machine_spec with CONV-3. Python runs that function. The returned record becomes a tool message with the matching tool_call_id. The next model request includes this exchange.'),
    'functions': dict(id='functions', title='Functions, inputs and returned results',
        brief='A function is a named piece of code. Arguments are the inputs given to it. return gives a result back to the caller. Printing a value only puts it on the screen.',
        example='get_machine_spec("CONV-3") receives one identifier and returns a dictionary. The calling program can read that dictionary before choosing another step.'),
    'records': dict(id='records', title='Dictionaries and small Python classes',
        brief='A dictionary stores named values, such as status and data. A class groups related values and operations. A dataclass helps define a small record without writing all the setup code yourself.',
        example='An Observation keeps id, tool, arguments and result together. obs.result["status"] reads one named field; it does not decide whether the entire task is finished.'),
    'copies': dict(id='copies', title='Why a saved record needs its own copy',
        brief='Two variables can refer to the same mutable object. If we save only another reference, a later change can also change what appears to be our history. A deep copy gives nested dictionaries and lists their own stored values.',
        example='Save a result containing a list, then change that original list. The observation should still show what the tool returned at the time we saved it.'),
    'conditions': dict(id='conditions', title='Conditions, loops and return',
        brief='An if statement chooses a branch. A while loop repeats its body. return leaves the current function. None can mean that a function has no stopping reason to report yet.',
        example='If steps is already at max_steps, stop_reason returns "max_steps". If no limit has been reached, it returns None and the caller may continue.'),
    'validation': dict(id='validation', title='Valid data and the right data',
        brief='Validation checks whether data follows the rules we specified. Some rules check its shape and types. Others check whether it belongs to this particular task. Passing one kind of check does not automatically pass the other.',
        example='CONV-7 can be a correctly written machine identifier while still being wrong for a task about CONV-3.'),
    'time': dict(id='time', title='Timeouts and elapsed time',
        brief='A timeout limits how long we wait for one operation. A whole-run budget limits how long the overall attempt should continue. We need both because a loop counter cannot interrupt an operation that never returns.',
        example='A limit of six decisions does not help if the first tool call hangs. The local tool subprocess also needs a timeout.'),
}

OPENING = [
    'In Week 1, we connected an LLM to a local Python program. You can think of this as giving the program a brain: it could understand a request and produce a response.',
    'In Week 3, we gave it hands. The model could request a tool, and our Python program could run that tool.',
    'But having a brain and hands does not automatically mean the program can finish a whole task.',
    'Here is the task we will work on today: ' + CASE,
    'Before we run anything, think about what we would need to check the final answer. Temperature readings are one part. We also need the reference limit and a calculation that really uses those inputs.',
]

DEPENDENCY_CHECK = check(
    'We have the five temperature readings but have not read the reference file. What can we say at this point?',
    ['The full report is finished because the query worked.',
     'We have one part of the evidence; the reference and checked calculation are still missing.',
     'The program must guess the reference so that it can finish.'], 'B',
    'The query gives readings. It does not supply the registered reference or prove that a calculation used the correct inputs.',
    'Read the original request again. Which parts are not answered by a list of temperatures?',
    'The calculation has two inputs: readings and a limit. We have only the readings so far.')

PATHS = {}
PATHS['t01'] = {
 'review': [
    slide('t01.opening', 'We have a brain and hands. What is missing?', 2, OPENING,
        ['Read the request first, before naming any software modules.',
         'Point to FETCH, REFERENCE and COMPUTE. These describe three jobs done by the supplied tools.',
         'Point to JUSTIFY. This asks us to show where the answer came from; it is not automatically a fourth tool.'],
        'Later, Task stores the confirmed machine, window and goal. Do not begin this opening by reading its class definition.', related=[3,4],
        correction='Week 3 used a one-round teaching program. Function calling itself is not limited to one call. The Week 2 miniGPT is not the live tool-calling model used here; DeepSeek supplies the live planner.'),
    slide('t01.dependencies', 'Follow the two inputs to the calculation', 6,
        ['Follow the two arrows into temperature_stats. One brings the readings; the other brings the reference limit.',
         'We can read the reference before or after querying the temperatures. But we cannot use the actual values in the calculation until both results are available.',
         'For this task we have three domain tools. The checked summary can be made by Python from their verified fields. A separate model request to write prose would not be a fourth tool call.'],
        ['Trace query_temperature to VALUES, then get_machine_spec to LIMIT.',
         'Pause where the arrows meet. Ask what would be missing if either source had not returned.',
         'Follow the final arrow to SUMMARY and explain that its numbers must point back to the records.'],
        'Task.goal names what we are trying to finish; verify will later express the required evidence in Python.',
        question=DEPENDENCY_CHECK),
 ],
 'practice': [
    node('t01.practice_opening', 'What would finish this request?', OPENING[:3] +
        ['Today we will use that connection to work on a longer request: ' + CASE,
         'List what you would need before signing off the answer. Then we will inspect a single API request and see which pieces it actually supplies.'],
        question=DEPENDENCY_CHECK),
    node('t01.practice_task', 'Keep the task fixed while you investigate',
        ['The task names a machine, a time window and a goal. Keep those fields fixed while checking each result.',
         'The time window includes 10:00 and excludes 10:25. A result for another machine or another window does not answer this request, even if the data looks sensible.',
         'You can look at the task file before running anything. You do not need to rewrite the three tools from Week 3.'],
        [ref('seminar','state.py','Task',max_lines=8)],
        code_notes=['Read goal, machine_id, start and end as the confirmed request fields.',
                    'The class describes the task; defining it does not query any records.']),
 ]}

PATHS['t02'] = {
 'review': [
    slide('t02.one_round', 'What comes back from one API request?', 4,
        ['Last week our teaching program stopped after one round of tool use. This was a choice in the program, not a limit of function calling.',
         'Now we will inspect one DeepSeek request. We will pause when the response arrives, then inspect what our local tool execution adds. We will not ask the model for another step in this experiment.',
         'The response may contain no tool request, one request or several. We will read what actually came back instead of trying to make the model fit a prepared story.'],
        ['Locate the point where the Week 3 program asks for prose and stops continuing the task.',
         'Compare the checklist on the right with the information obtained so far.',
         'Ask who would have to start the next request: our Python application, or a function definition sitting in a prompt?'],
        'demos.single_round_request sends one request, records the proposed calls, and shows what the application executed.',
        correction='The original slide uses a single-tool teaching cut. A response can propose multiple tools. A tool proposal is still not the same as a returned local tool result.'),
    node('t02.read_request', 'Read the request and the two pause points',
        ['The program sends the task and the available tool definitions. The model response names what it wants the application to do.',
         'The application still checks and executes local functions. It must send their results back in another model request if the next decision needs those results.',
         'Choose a recorded teacher request or one live request with your own configured key. A teacher record is a saved real exchange. It is not a new call from your computer, and it is not a scripted model reply.'],
        [ref('lecture','demos.py','single_round_request')],
        code_notes=['Find the API request before reading the handling of tool_calls.',
                    'Find the local execution after the response. Count proposed requests and actual executions separately.',
                    'This experiment does not send the execution results to a second model request.'],
        action='Predict what information the first response can contain and what still needs local execution.'),
    node('t02.actual_response', 'What did this particular request do?',
        ['Read the actual report with me. First locate the evidence label: a live run or a saved teacher API exchange.',
         'Now count the proposed tool calls and inspect their names and arguments. Do not assume the count is one. Next look at which calls were actually executed and what they returned.',
         'Compare the evidence now available with the task checklist. We are studying the missing execution and feedback steps, not claiming that every model response has the same number of calls.',
         'If you selected the bundled teacher record, point to its two requests: get_machine_spec and query_temperature. After Python ran both, the saved check still listed stats as missing. The record contains no second model request. For a new live run, explain its actual calls and missing list instead.'],
        phase='after_run', evidence_fields=['evidence label','model request count','proposed calls','executed calls','tool results','missing evidence'],
        action='Explain one difference between the API response and the result of running a local function.'),
 ],
 'practice': [
    node('t02.practice_request', 'Inspect one request before adding a loop',
        ['We will send one DeepSeek request, or read a saved real teacher request, and inspect it in two stages: the model response and the local tool results.',
         'Look for tool_calls in the code. These entries ask the application to run functions. They are not temperature measurements.',
         'There is no follow-up model request in this experiment. Predict what information cannot reach a later model decision until we add that step.'],
        [ref('seminar','demos.py','single_round_request')],
        action='Choose teacher-record or live mode, then predict the missing feedback step.'),
    node('t02.practice_observed', 'Read your request report',
        ['Check whether this is a live exchange or an inspected teacher record. Keep that label in your explanation.',
         'Find the proposed calls, the real local results, and any missing evidence. If the model proposed two calls, say two. If it returned text instead, report that too.',
         'Which information would we need to include when asking the model what to do next?'],
        phase='after_run', evidence_fields=['evidence label','proposed calls','executed calls','missing evidence']),
 ]}

PATHS['t03'] = {
 'review': [
    slide('t03.small_loop', 'Try the smallest loop first', 8,
        ['The simplest idea is to repeat four actions: ask for a next step, run it, read the result, and ask again.',
         'Keep the same conversation history. That means keeping the original task, the model request and its matching tool result, rather than starting over with only the first question.',
         'A fixed workflow can also have conditions. For a small task it may be the simpler solution. Today we are learning to control a loop whose next action is proposed while it runs.'],
        ['Start at PLAN and follow one trip around the circle.',
         'At OBSERVE, point back toward the next PLAN. The return value changes what can sensibly happen next.',
         'The Verify and stop rules on this teaching diagram are what we are about to build, not features that appear merely because we wrote while.'],
        'demos.bare_loop lets us inspect a small loop with deliberately weak completion logic.',
        related=[17], correction='The four named stages are this course\'s explanation of the loop. ReAct does not mean that we should save or display private model reasoning.'),
    node('t03.predict_failures', 'What could go wrong with that loop?',
        ['We will try two deliberately difficult planners. One keeps asking for the same file. The other asks to finish before collecting the evidence.',
         'These are scripted fault injections so that everyone can inspect the same control problems. They do not measure how often a real model makes these mistakes.',
         'An outside step and time limit will end the demonstration. We will never leave an unbounded loop running against a paid API.'],
        [ref('lecture','demos.py','bare_loop')],
        action='Predict what is missing in each case: a completion check, a limit on continued work, or both.'),
    node('t03.inspect_failures', 'One loop repeats; the other stops too soon',
        ['Read the two actual traces. In the repeat case, identify what useful evidence was added and what was only repeated.',
         'In the early-finish case, compare the claimed ending with the evidence still missing. A request to finish is not proof that the task is finished.',
         'The outside limit stopped our demonstration safely. That is different from the learner\'s loop correctly deciding when to stop. We need to add those checks inside the application.'],
        phase='after_run', evidence_fields=['scenario','events','claimed ending','missing evidence','outer limit'],
        question=check('Which pair of additions addresses the two demonstrated problems?',
            ['A longer prompt and a more confident final sentence.',
             'An evidence check for completion, and limits on unproductive or excessive work.',
             'Always stop after the first successful tool call.'], 'B',
            'An evidence check prevents unsupported success. Progress and resource limits prevent the run from continuing without a useful reason.',
            'Treat stopping too early and continuing too long as two separate problems.',
            'One check asks whether the task is done. Another asks whether we may keep trying.')),
 ],
 'practice': [
    node('t03.practice_loop', 'Test two bad next-step proposals',
        ['Read the small loop, then predict what it will do with a planner that repeats one request and a planner that asks to finish too soon.',
         'We use known scripted proposals to test the program. The demonstration has an outside limit even though its own teaching logic is deliberately incomplete.'],
        [ref('seminar','demos.py','bare_loop')], action='Predict the two failure modes before running the bounded demonstration.'),
    node('t03.practice_failures', 'Locate the missing check in each trace',
        ['Find the first repeated action with no useful new evidence. Then inspect the other run\'s finish request and list the evidence it did not collect.',
         'Explain which part of the program should decide whether that finish request is accepted. The outside demonstration limit is not evidence that the internal loop works.'],
        phase='after_run', evidence_fields=['scenario','events','missing evidence','outer limit']),
 ]}

PATHS['t04'] = {
 'review': [
    slide('t04.execution_gate', 'Should this proposed action be allowed to run?', 26,
        ['Before we fix the whole loop, there is a smaller question: is this particular action allowed to run?',
         'The program accepts only registered tool names. It checks the argument types and values, then checks that the requested machine and window match the task the user confirmed.',
         'A correctly written request about another machine is still the wrong request for this task. A rejection should be recorded and returned as feedback; it must not execute the tool.'],
        ['Read the three allowed tool names. There is no route here for arbitrary Python text.',
         'Follow the wrong-machine example and stop before execution.',
         'Separate these execution checks from the later check that statistics use the collected readings.'],
        'ToolRunner.execute performs the execution checks before starting a local worker.',
        correction='In this implementation, matching_stats checks the statistics\' link to collected evidence after execution. Do not claim the input-provenance check already happened at the execution gate.'),
    node('t04.gate_code', 'Find the check before the worker starts',
        ['Read the beginning of ToolRunner.execute. The name is checked against the allowed set, and the argument model validates the proposed values.',
         'Next inspect the task checks. They compare the requested machine and time window with the confirmed task.',
         'Predict what the actual tool-attempt counter will do for a rejected request, then run the small gate demonstration.'],
        [ref('lecture','gateway.py','ToolRunner.execute',max_lines=12)],
        action='Choose one invalid request and predict whether any tool code will run.'),
    node('t04.gate_result', 'A refused request is still useful feedback',
        ['Read the rejection code and message in the actual output. Check the number of real tool attempts rather than guessing from the number of requests.',
         'The program can explain why it refused a request. Recording that refusal does not turn it into successful equipment data.'],
        phase='after_run', evidence_fields=['validation result','error code','tool attempts'],
        question=check('A proposed request uses the wrong machine and is rejected before execution. What should happen?',
            ['Record the rejection and return feedback, without counting a tool execution that never happened.',
             'Run it anyway because the machine identifier has the correct type.',
             'Treat the error message as the requested machine specification.'], 'A',
            'The refusal is a real event worth recording. It is not a tool execution and it does not supply the requested equipment evidence.',
            'Separate a proposed action from code that actually ran.',
            'The gate rejected the request before the worker started. What can the attempt counter honestly count?')),
 ],
 'practice': [
    node('t04.practice_gate', 'Will this request reach a tool?',
        ['Inspect the execution checks, then classify the supplied unknown-tool, wrong-argument and wrong-machine requests.',
         'For each one, predict whether the worker should start. We will check the actual attempt counter after running the gate demonstration.'],
        [ref('seminar','gateway.py','ToolRunner.execute')],
        action='Predict one rejection and explain which condition should cause it.'),
    node('t04.practice_result', 'Check whether your predicted rejection happened',
        ['Compare the real rejection message and attempt count with your prediction.',
         'If a request is well formed but belongs to another task, identify the task-scope check. A type check alone is not enough.'],
        phase='after_run', evidence_fields=['validation result','error code','tool attempts']),
 ]}

PATHS['t05'] = {
 'review': [
    slide('t05.state', 'Where do we keep what happened?', 23,
        ['We can now decide whether a request may run. After it runs, we need to keep what actually happened.',
         'Think of State as the program\'s notebook. It contains the confirmed task, the observations and the counters that control the run.',
         'An Observation is one entry in that notebook. Context is the part of the notebook we choose to show the planner. These are related, but they are not the same object.'],
        ['Read the State column as information owned by Python.',
         'Follow context() across the diagram. It selects and copies information for the next decision.',
         'Point out that a claim in a model message cannot directly change the runtime\'s status or counters.'],
        'Observation defines one record; State.context selects information for the planner.', related=[22,24],
        correction='Use field(default_factory=list) for separate lists in the executable dataclass. The slide\'s shortened default-value display is not code to copy unchanged.'),
    slide('t05.two_routes', 'The result has two places to go', 25,
        ['Follow the upper arrow first. The result goes into the program\'s record so that the verifier and a human can inspect it later.',
         'Now follow the lower arrow. The result also goes back to the planner so that its next decision can use it.',
         'Observe keeps the result, including an error or refusal. It does not decide that the task is complete. We will write that separate decision next.'],
        ['Trace the result into the ledger. Name the observation ID, inputs and returned value.',
         'Trace the other route into the conversation. A tool message must match the original tool-call ID.',
         'Ask what each route is for before introducing any new class syntax.'],
        'State.record saves the observation; planner.observe returns feedback. State.context also supplies a selected view of evidence.',
        correction='The scripted planner can read State directly. Removing observe from it does not prove model amnesia. Check actual message pairing when examining the live interface.'),
    node('t05.record_code', 'Save a small record without changing its history',
        ['Look at Observation. Its fields tell us which tool was requested, which inputs were used, and what came back.',
         'When we save arguments and results, we need our own copies. Otherwise a later edit to a nested dictionary or list could also change what looks like an old observation.',
         'Complete State.record in three small steps: give the observation an ID, store separate copies, and add the record and its event. Keep the provided function signature.'],
        [ref('seminar','state.py','Observation',max_lines=8),ref('seminar','state.py','State.log',max_lines=6)],
        code_notes=['Observation describes the fields, not the decision about completion.',
                    'State.log already shows how copy.deepcopy protects event fields.',
                    'Use the existing fields and log method; do not replace the whole State class.'],
        action='Write the body of State.record in chat, then predict what should happen if the original dictionary changes.'),
    node('t05.record_output', 'Did the saved observation keep its own values?',
        ['Read the state-test results and the saved observation example. Locate the ID, tool, arguments, result and reused fields.',
         'Inspect the result of changing the original nested object after it was recorded. Explain why the saved observation should keep the earlier values.',
         'A new log entry only tells us that something was recorded. Whether it adds useful evidence is a later check.'],
        phase='after_run', evidence_fields=['test results','observation ID','arguments','result','copy check','reused']),
 ],
 'practice': [
    node('t05.practice_record', 'Keep the tool result so that we can check it later',
        ['Your first code task is State.record. It receives a tool name, arguments, a result and a reused flag.',
         'Read Observation and the existing log method. Use them to give the result an ID, keep separate copies, and append a record and event.',
         'Before coding, choose whether you want a short explanation of dictionaries, dataclasses or deep copies.'],
        [ref('seminar','state.py','Observation',max_lines=8),ref('seminar','state.py','State.log',max_lines=6)],
        action='Write a small function body, then predict the saved value after the original object is changed.'),
    node('t05.practice_result', 'Inspect the copy test and one saved observation',
        ['Check which tests passed and which still need work. Use the actual observation fields to explain where the tool inputs and outputs are kept.',
         'Then explain the copy test. Do not just report that it is green: tell me what could have gone wrong if two variables referred to the same nested object.'],
        phase='after_run', evidence_fields=['test results','observation ID','copy check']),
 ]}

PATHS['t06'] = {
 'review': [
    slide('t06.acceptance', 'W4.2A: what would let us accept the report?', 9,
        ['We can store results now. But a pile of records does not tell us whether the task is complete.',
         'Read the checklist with me. We need the right readings, the registered reference, a calculation using those inputs, and a report whose numbers point back to those records.',
         'Your first small function, verify, will decide which pieces this goal requires and name any gaps. A readings query can finish with an empty list; a percentage report cannot turn no readings into 0%.'],
        ['Read each row as a question we can ask about the collected observations.',
         'Point to the observation-ID slots. They link a fact to the record that supports it.',
         'Separate the checklist from the next question: did the calculation actually use those records?'],
        'W4.2A completes verify and returns Check. W4.2B will supply the input comparison used by matching_stats.'),
    slide('t06.wrong_numbers', 'W4.2B: the same answer can come from different inputs', 14,
        ['The slide uses [1, 2] as an obvious example of wrong inputs. Now try a harder case: our saved readings are [82, 87, 91, 94, 97], but the calculation used [82, 88, 90, 94, 97].',
         'Both lists have five readings. Both give a mean of 90.2, a maximum of 97, and four readings above 85. Even all of those matching results would not prove that the calculation used our saved readings.',
         'The arguments record what the tool was given. Compare that whole record with the saved list of values and the saved limit. This is the small check you will write in statistics_inputs_match.'],
        ['Compare the observed readings with the arguments passed to the calculation.',
         'Locate the slide\'s if obs.arguments != {...} check. It asks whether the input record matches, not whether the list lengths match.',
         'Then follow the numerical checks. We still need them: correct inputs do not excuse an incorrect output.'],
        'matching_stats calls the new statistics_inputs_match before checking the returned numbers. You implement the input guard as well as the goal checklist.',
        question=check('The count, mean, maximum and above-limit fraction all match, but two input values differ from the saved readings. What should we do?',
            ['Accept the report because every displayed statistic matches.',
             'Reject this statistics record because its inputs differ from the saved readings.',
             'Accept it if the model says the differences are unimportant.'], 'B',
            'The same summary can describe different inputs. The argument record must match the observed values and registered limit before this calculation counts as evidence.',
            'Compare the two lists position by position, rather than comparing their length or mean.',
            'Which record tells us what was sent into the calculation: its arguments, or its summary output?')),
    node('t06.verify_code', 'Prepare the two short function bodies',
        ['Look at Check first. ready says whether the required evidence is present. missing names the gaps. evidence_ids links the accepted facts to their observations.',
         'For W4.2A, use matching_sources and matching_stats in verify, then choose the required pieces from the goal. The report goal also needs nonempty readings.',
         'For W4.2B, statistics_inputs_match receives an observation, the values taken from the matching query, and the limit taken from the specification. Its job is to return True only when the observation arguments match both inputs.',
         'A dictionary holds named values; a list holds the ordered readings. Comparing the dictionaries checks their fields and the list contents. A length comparison cannot do that job.',
         'The caller skips a statistics observation when this helper returns False, then continues looking for suitable evidence. It still checks the numerical output after a True result.'],
        [ref('seminar','verification.py','Check',max_lines=8),
         ref('seminar','verification.py','matching_stats',max_lines=12),
         ref('seminar','verification.py','statistics_inputs_match',max_lines=8)],
        code_notes=['Follow values back to query records and limit back to the specification.',
                    'Read obs.arguments as what this particular tool call received, not as a remembered expected answer.',
                    'The supplied caller handles searching and numerical checks; do not remove them.',
                    'Check.progress tracks evidence types, not the seminar percentage.'],
        action='After these preparation steps, write your verify body first. Mentor saves it and then asks separately for statistics_inputs_match. Both are required before the t06 tests run.'),
    node('t06.verify_output', 'Read the two checks separately',
        ['Read the actual comparison_rows. Start with the correct-input case and identify its arguments, inputs_match and check.ready.',
         'Next find same_count_same_summary_wrong_values. Compare its tool_statistics with the correct case. Then read same_summary_as_correct, inputs_match and check.missing. Use the observed values; do not merely repeat the expected answer.',
         'The wrong-limit case checks the other input. The empty-data cases check the goal checklist. These are different reasons for refusing a report.',
         'Now read your saved statistics_inputs_match and follow its return value into matching_stats. Explain why the input comparison and numerical checks are both needed.'],
        [ref('seminar','verification.py','statistics_inputs_match',max_lines=10),
         ref('seminar','verification.py','matching_stats',max_lines=12)],
        phase='after_run', evidence_fields=['comparison_rows','inputs_match','same_summary_as_correct','ready','missing','evidence_ids','facts']),
 ],
 'practice': [
    node('t06.practice_verify', 'W4.2A: choose what this goal needs',
        ['We will complete two short functions in this task. First, verify chooses what evidence the current goal needs. Second, statistics_inputs_match checks which values and limit went into a calculation.',
         'Read Check to see what verify must return. A specification lookup needs its matching specification; a readings query needs its matching query result; a report needs both sources and matching statistics.',
         'An empty query can answer a readings request. A percentage report still needs actual readings to count. We will test that difference after saving both functions.'],
        [ref('seminar','verification.py','Check',max_lines=8)],
        action='Explain which evidence the report goal needs before looking at the input comparison.'),
    node('t06.practice_inputs', 'W4.2B: check what the calculation received',
        ['Our query returned [82, 87, 91, 94, 97]. A different call used [82, 88, 90, 94, 97], with the same limit of 85. Both have count 5, mean 90.2, maximum 97 and above-limit fraction 0.8.',
         'That is why checking the count, or even checking every summary value, is not enough. Compare obs.arguments with the complete expected argument record built from values and limit.',
         'A dictionary comparison checks the named fields and the values they hold. The list inside it must contain the saved readings. The limit must also match the specification.',
         'Read how matching_stats uses the Boolean returned by statistics_inputs_match. False skips this record; True allows the separate numerical checks to follow.'],
        [ref('seminar','verification.py','statistics_inputs_match',max_lines=8),
         ref('seminar','verification.py','matching_stats',max_lines=12)],
        question=check('Five readings produced the same summary as our saved readings. Which check is still necessary?',
            ['Check only that the tool response has status ok.',
             'Compare the full calculation arguments with the observed values and reference limit.',
             'Check the number of readings one more time.'], 'B',
            'Equal summaries can hide different input values. Match the argument record before using the statistics as evidence.',
            'Look at the two lists: which values changed while their summaries stayed the same?',
            'The input dictionary names values_c and limit_c. Both must come from the saved sources.'),
        action='After preparation, write your verify body first. Mentor then asks separately for statistics_inputs_match and a prediction before running the tests.'),
    node('t06.practice_result', 'Explain why each record was accepted or rejected',
        ['Read the actual comparison_rows and find the case whose summary matches despite different inputs. Explain its inputs_match and check.missing fields.',
         'Then compare the wrong-limit case and the two empty-data goals. Identify which small function checks each issue.',
         'Use your saved guard to explain why correct arithmetic alone cannot show that a result answers this task.'],
        [ref('seminar','verification.py','statistics_inputs_match',max_lines=10)],
        phase='after_run', evidence_fields=['comparison_rows','inputs_match','same_summary_as_correct','ready','missing','evidence_ids','facts']),
 ]}

PATHS['t07'] = {
 'review': [
    slide('t07.endings', 'Not finished, but not allowed to run forever', 28,
        ['The verifier stops us from declaring success too early. It does not give us permission to keep trying forever.',
         'Read the four endings. Completed means the evidence passed. Stopped means a limit ended the run. Failed means an operation could not be completed. Needs_human means someone must clarify or supply something.',
         'These endings ask for different follow-up work. The word stopped by itself does not tell us that we have a usable report.'],
        ['Compare completed with stopped before reading the other two boxes.',
         'For each example, point to both the status and the reason.',
         'Ask what the user would need to do next for a missing machine identifier.'],
        'stop_reason returns a limit reason or None. The runtime chooses an honest ending.', related=[29,36]),
    slide('t07.no_progress', 'More requests do not always mean more progress', 31,
        ['The program reads the same frozen specification again. What useful evidence did the second request add?',
         'A repeated request can increase the decision count while the real execution count stays the same because a saved result was reused.',
         'Keep steps, tool_attempts and no_progress separate. They answer different questions: how many choices, how many executions, and how many rounds without useful new evidence.'],
        ['Follow the first specification read and its new evidence.',
         'Compare the next two observations with the first one. New IDs do not make the same information new evidence.',
         'Read the no-progress count beside each round.'],
        'Config sets the limits; stop_reason checks the current state; the runner separately bounds individual attempts and timeouts.', related=[34,35]),
    node('t07.guard_code', 'Write a stop reason, not a success message',
        ['Read Config first. Its limits are ordinary values the program can compare with the current run.',
         'Complete stop_reason so it returns the appropriate limit reason, or None if the run may continue. Follow the provided order when more than one limit has been reached.',
         'The loop needs its whole-run limit, and each operation needs a timeout too. A counter cannot interrupt the first tool if that tool never returns. Token usage is reported after a response, so its threshold cannot guarantee a prepaid spending cap.'],
        [ref('seminar','controls.py','Config',max_lines=12),ref('seminar','controls.py','remaining_seconds',max_lines=4)],
        action='Write the guard conditions and predict what happens at exactly max_steps, not just above it.'),
    node('t07.guard_output', 'Which limit stopped this case?',
        ['Read the actual boundary tests. Notice the equal-to-limit case and the difference between a disabled no-progress check and the step limit that remains active.',
         'A returned limit reason says why we must stop trying. It does not supply any missing readings or make a report complete.'],
        phase='after_run', evidence_fields=['test results','configured limits','stop reason']),
 ],
 'practice': [
    node('t07.practice_guards', 'Stop a run that cannot usefully continue',
        ['The task may still be incomplete when a step or time limit is reached. Complete stop_reason without changing that situation into success.',
         'Use Config and remaining_seconds to read the existing limits. Keep the limit comparisons in the documented order.',
         'Predict the boundary at steps equal to max_steps, then run the guard tests after saving your code.'],
        [ref('seminar','controls.py','Config',max_lines=12),ref('seminar','controls.py','remaining_seconds',max_lines=4)],
        action='Write the stopping conditions and explain what None means to their caller.'),
    node('t07.practice_results', 'Read the boundary cases',
        ['Find the actual result for each tested limit and explain one boundary in your own words.',
         'Explain why reaching that limit is a stopped run rather than a completed report.'],
        phase='after_run', evidence_fields=['test results','configured limits','stop reason']),
 ]}

PATHS['t08'] = {
 'review': [
    slide('t08.join_loop', 'Put the checks in the right places', 27,
        ['We now have the pieces. Let us follow one round and decide where each belongs.',
         'At Gate A, the program checks the evidence, limits and run status. It may continue, complete the task, stop at a limit, report a failure, or ask for help.',
         'If it continues, the planner proposes an action. Gate B checks whether a proposed tool request may run. The tool returns a result; Observe records and returns it; Verify checks what the new result proves. Then we return to Gate A.'],
        ['Begin at the completion check before the next planner request.',
         'Follow the loop to the runner, then follow the result into observe and the next verification.',
         'Return to the top. Ask where a fourth unnecessary action would be prevented.'],
        'run_agent keeps the control branches. complete_tool_step joins execution, feedback and the updated check.',
        correction='Gate A and Gate B are teaching names for the control decision and execution checks. They are not two extra models. finish and human are control requests, not ordinary tools.'),
    node('t08.loop_code', 'Connect the result to the next check',
        ['Read _update_check. It compares the kinds of evidence now available with the previous check, updates no_progress and records what the verifier found.',
         'The provided run_agent handles completion, limits and error endings. Your small helper needs to run the allowed action, return its result to the same planner, and get a fresh check.',
         'Use the new check after execution. A check made before the action cannot describe evidence that has only just arrived.'],
        [ref('seminar','runtime.py','_update_check',max_lines=10),ref('seminar','runtime.py','complete_tool_step',max_lines=10)],
        action='Write complete_tool_step in chat. Predict why using the old check after execution could cause an unnecessary next round.'),
    node('t08.loop_results', 'Did every result reach the next decision?',
        ['Read the runtime test results. Find the checks for a normal completion, a refused early finish and no extra action after completion.',
         'Explain where the result is recorded and where feedback reaches the planner. In a live exchange, the tool message must match the model request it answers.',
         'The scripted planner can inspect State directly, so a fake memory experiment that merely deletes observe would be misleading. Use the actual protocol tests to check the live message connection.'],
        phase='after_run', evidence_fields=['test results','runtime events','feedback','completion check']),
 ],
 'practice': [
    node('t08.practice_connect', 'Connect execution, feedback and the new check',
        ['Complete the small helper inside the existing runtime. The surrounding branches for completion, errors and limits stay in place.',
         'Follow an action through runner.execute, planner.observe and _update_check. Return the observation and updated check in the form used by the caller.',
         'Predict what could go wrong if the caller used a check made before the tool ran.'],
        [ref('seminar','runtime.py','complete_tool_step',max_lines=10),ref('seminar','runtime.py','_update_check',max_lines=10)],
        action='Save your helper body, then run the runtime tests.'),
    node('t08.practice_result', 'Explain a runtime test using the actual calls',
        ['Inspect the actual runtime test output and choose a case that checks feedback or completion.',
         'Point to the operation that gives the next check its new evidence. Explain why a finish request still needs verification.'],
        phase='after_run', evidence_fields=['test results','runtime events','feedback']),
 ]}

PATHS['t09'] = {
 'review': [
    slide('t09.rerun', 'Try the original cases with the completed loop', 38,
        ['Return to the cases we used before adding the controls. This time your saved code will run them.',
         'Predict the normal task, the repeating planner and the planner that asks to finish too early. We will compare their actual evidence and ending reasons.',
         'Read the slide as a reference design, not as a result from your computer. The exact counts we discuss must come from your run. Keep the outside test limit in place.'],
        ['Read the scenario column before looking at the reference outcome.',
         'Keep decisions and actual attempts in separate columns.',
         'Ask which check should end each scenario and what evidence would justify that ending.'],
        'The comparison driver runs the student loop and writes the counts and ending reasons for inspection.', related=[18,17]),
    node('t09.trace', 'Find the event that explains the ending',
        ['Read the actual normal run first. Follow a decision to its tool result, then to the verifier event that records what is still missing.',
         'Now read the bounded failure comparisons. For a refused early finish, locate the missing evidence and the feedback. For a repeat, distinguish another request from another real tool execution.',
         'Find the first event that explains the ending, not just the last line. If an outside watchdog ended a test, report that as a failed internal control, not as successful stopping logic.'],
        phase='after_run', evidence_fields=['status','reason','steps','tool_attempts','no_progress','evidence IDs','report facts','outside watchdog'],
        action='Use one actual trace to explain why this run ended where it did.'),
 ],
 'practice': [
    node('t09.practice_compare', 'Predict and run the complete comparison',
        ['Your four code changes are now in place. Predict the result of the normal request, a repeated request and an unsupported finish request.',
         'Use the same supplied tools and data. We want to see what the controls changed, not change the task to make the result look better.'],
        action='Make a short prediction for the scenarios, then run the bounded comparison.'),
    node('t09.practice_trace', 'Explain what your program actually did',
        ['Read the actual comparison rows and open the relevant trace when a row needs explanation.',
         'Explain a status, its reason, the decision count and the actual execution count. Point to the evidence behind a completed report or to the missing evidence behind an unfinished run.'],
        phase='after_run', evidence_fields=['status','reason','steps','tool_attempts','evidence IDs','outside watchdog']),
 ]}

PATHS['t10'] = {
 'review': [
    slide('t10.return_to_request', 'What did we add to the brain and hands?', 39,
        ['Return to the request we started with. At first, our program could ask a model and run a tool. Now it can keep results, check what they prove, and decide whether another action is needed and allowed.',
         'Explain the loop to a classmate using this CONV-3 example. Name where an action is checked, where its result is saved and returned, and where completion is decided.',
         'Your seminar progress, code and answers are saved. The small agent you built is a different program: it does not yet resume a partly executed run after the process closes. We will study that problem in Week 5.'],
        ['Follow the three evidence records back to the original task.',
         'Point to the ending and ask what made completed justified.',
         'Use the next-week note to separate learning progress from agent execution checkpoints.'],
        'Save the current work and use the existing review command for a longer reflection when you want one.', related=[36]),
 ],
 'practice': [
    node('t10.practice_recap', 'Explain your loop using the experiment you just ran',
        ['Use your own trace to explain how a tool result changed the next decision or the ending.',
         'Name one check that prevents false completion and one that stops a run from continuing too long.',
         'Your learning session is saved. Resuming this seminar is separate from resuming a half-executed agent run; the latter is a Week 5 topic.']),
 ]}

SPECS = [
 ('t01','Why we need a loop',8,'Connect the earlier weeks to a task with dependent tool actions.',[],None,False,
  oq('q1','Which parts of the CONV-3 task are still missing after a temperature query alone?',
     'Identify the registered reference, matching calculation and checked report; do not require a fourth domain tool.',
     'Read the verbs in the request.', 'The query supplies readings, but not the reference or a statistics result.',
     'We still need the registered reference and a calculation using it with the queried readings. The report must cite those observations.')),
 ('t02','Inspect one real API request',8,'Separate a model proposal from local execution and later feedback.',['messages'],None,True,
  oq('q1','Using the actual request report, explain what the model proposed, what Python executed, and what would need another round.',
     'Use the real evidence label and counts. Separate model requests, tool proposals, executions and feedback. Do not claim one call per response.',
     'Read the model response and local results as two different stages.', 'Point to one proposed tool name and then to its execution result or rejection.',
     'The model response contains requests or text. Python performs the allowed local actions. A later model decision needs their results in the conversation. Use the actual report to supply the counts.')),
 ('t03','Find two problems in a small loop',10,'Observe repeated work and unsupported completion in bounded fault demonstrations.',['conditions'],None,True,
  oq('q1','What was missing from each deliberately weak loop, and what did the outside limit prove?',
     'Distinguish evidence-based completion from progress/budget limits. Label scripted fault injection and external containment honestly.',
     'One case continued too long; the other accepted completion too soon.', 'The outside harness ended the demonstration. It did not repair the inner loop.',
     'The repeating case needs progress and resource limits; the early-finish case needs an evidence check. The outside limit only bounded the experiment.')),
 ('t04','Check a proposal before it runs',9,'Inspect the execution checks and their effect on real tool attempts.',['validation'],None,True,
  oq('q1','Use one rejected request to explain why the tool did not run and how you can tell from the output.',
     'Name the specific name/argument/task-scope check and cite actual rejection plus attempt evidence.',
     'Look for the error code and the real execution count.', 'A request may be recorded before any worker starts. Which condition rejected this one?',
     'The allowed-tool, argument or task-scope check refused the request before execution. The report must show that refusal and no invented tool attempt.')),
 ('t05','Keep the result in a reliable record',15,'Write State.record and check that later edits cannot alter the saved observation.',['records','copies'],'record',True,
  oq('q1','Why did the saved observation need its own copy, and why is recording a result different from verifying it?',
     'Explain mutable-object independence and separate record keeping from task-completion judgement using the actual test.',
     'Think about two names referring to one nested dictionary.', 'The copied record preserves what was returned; a later checker decides whether it answers this task.',
     'A deep copy keeps later changes to the original object from changing the saved history. Recording preserves the event; verification decides what that event proves for this task.')),
 ('t06','Check the task and the calculation inputs',15,'Write the goal checklist and the exact statistics-input comparison as two short subparts.',['validation'],'verify',True,
  oq('q1','Explain why an empty query can finish a readings task but cannot finish the requested percentage report.',
     'Relate evidence requirements to goal; empty query is a valid query outcome but does not provide denominator for report. Do not invent 0%.',
     'Compare what the two task goals ask for.', 'A list can be empty. A percentage requires actual readings to count.',
     'The readings task asks for the matching records, so an empty list can answer it. The report needs nonempty readings and matching statistics, so no data cannot be presented as 0% above the reference.')),
 ('t07','Set limits on continued work',10,'Write the stopping checks without confusing a limit with success.',['conditions','time'],'guards',True,
  oq('q1','Explain one tested limit and why it ends an attempt without proving that the task succeeded.',
     'Use an actual tested boundary and distinguish stop reason from verified task completion.',
     'Find the configuration value and the current value in that test.', 'Does hitting this limit supply the missing evidence, or only end further attempts?',
     'A limit ends continued attempts when the configured boundary is reached. It does not supply missing observations. Only the task verifier can establish completion.')),
 ('t08','Connect the pieces inside the loop',13,'Connect execution, feedback and a fresh check in the provided runtime.',['functions'],'loop',True,
  oq('q1','Where does the new result enter the next check, and what stops an unnecessary action after completion?',
     'Trace execute, record, feedback and fresh verification. Explain the completion decision before another planner request.',
     'Follow the observation returned by the runner.', 'Compare a check made before the action with the new check after it.',
     'The runner records the result, feedback returns to the planner, and _update_check verifies the updated State. The runtime checks completion before requesting another action.')),
 ('t09','Rerun the cases and read the evidence',8,'Use actual traces to compare a complete task with stopped or rejected attempts.',[],None,True,
  oq('q1','Choose one actual comparison run. Explain its ending, its decision and execution counts, and the event that caused that ending.',
     'Use observed values rather than reference counts; distinguish completed/stopped/failed/needs_human and outside watchdog; connect cause to trace.',
     'Start with status and reason, then look earlier in the trace.', 'Find the first event that explains the missing evidence or stopping condition.',
     'Use the recorded status, reason and counters for the chosen run. Trace them to a verified result, repeated lack of progress, a limit, an error or a request for human input. Do not label an outside watchdog termination as successful internal control.')),
 ('t10','Explain what your loop now does',4,'Return to the original task and save a brief learning reflection.',[],None,False,
  oq('q1','In a few sentences: what does the loop add, which check mattered in your experiment, and what would you like to practise next?',
     'Connect actions to recorded feedback, evidence verification and bounded continuation; name an actual example and a next topic. Separate seminar save from agent checkpoint.',
     'Start with the original multi-step request.', 'Describe what happens after one tool returns, then name the check that decides whether to continue.',
     'The loop connects each proposed action to real results, keeps them available, checks whether the task is complete and limits further work. Use your own experiment and choose a next topic such as live planning, handoff or retries.')),
]

WALKTHROUGHS = {
 't01':['Use the concrete request before any source file. Locate the two inputs of the statistics tool on the slide.'],
 't02':['Read the single-request function, distinguish the model response from local execution, then inspect the actual report.'],
 't03':['Read the small bounded demonstration, predict repeat and early-finish behaviour, then locate the missing internal checks.'],
 't04':['Find allowed names, argument validation and task-scope checks before the worker starts.'],
 't05':['Explain Observation and the supplied log method, then let the learner write record and test independent copies.'],
 't06':['Connect page 9 to the verify checklist and page 14 to statistics_inputs_match. Let the learner write both short bodies, then compare actual cases with matching summaries but different inputs.'],
 't07':['Read Config and remaining_seconds, then let the learner write the limit comparisons and test exact boundaries.'],
 't08':['Read the surrounding loop and _update_check, then let the learner connect the small tool-step helper.'],
 't09':['Use current student code to rerun the original cases; explain actual ending reasons and counts.'],
 't10':['Use the saved trace to explain the full path and select a next topic.'],
}

CODE_REFS = {
 't01': [], 't02': [('demos.py','single_round_request')],
 't03': [('demos.py','bare_loop')], 't04': [('gateway.py','ToolRunner.execute')],
 't05': [('state.py','Observation'),('state.py','State.log')],
 't06': [('verification.py','Check'),('verification.py','matching_stats'),('verification.py','statistics_inputs_match')],
 't07': [('controls.py','Config'),('controls.py','remaining_seconds')],
 't08': [('runtime.py','_update_check'),('runtime.py','complete_tool_step')],
 't09': [], 't10': [],
}

CODE_SUPPORT = {
 'record': dict(hint1='Look at the fields in Observation and the existing State.log method. Which inputs must the new record keep?',
     hint2='Make an ID from the next position, deep-copy arguments and result, append the Observation, log the event and return the Observation.',
     explanation='record stores what happened. Its deep copies protect the record from later changes. The ID lets a report refer back to one observation. It does not decide whether that observation completes the task.',
     rubric='Explain why the inputs and result are copied, where the Observation is appended, and why recording is separate from verification.'),
 'verify': dict(hint1='Which evidence does each goal require? The matching helpers will supply suitable observations once you also complete the small input guard.',
     hint2='Build a mapping of found evidence, choose the required names from the goal, and list missing names. A report with zero query rows also needs nonempty readings. Return the associated IDs and facts.',
     explanation='verify expresses the task checklist. It uses matched observations rather than model confidence. Different goals need different evidence, and an empty query cannot support a percentage report.',
     rubric='Explain the required evidence for report versus readings, how missing controls ready, and why evidence IDs identify actual matched observations.'),
 'stats_inputs': dict(hint1='Read obs.arguments. Which two named inputs should come from the saved query and specification?',
     hint2='Build the expected argument dictionary from values and limit. Compare the whole dictionary, including every list value; a count or summary comparison is not enough.',
     explanation='statistics_inputs_match connects a calculation to the values and limit collected for this task. Different lists can produce identical summaries. The caller rejects a mismatched input record before checking the returned arithmetic.',
     rubric='Explain where values and limit come from, why the full argument dictionary is compared, and why a False return skips this observation even when its summary looks correct.'),
 'guards': dict(hint1='Read Config and compare its limits with the counters and elapsed time in State.',
     hint2='Check the total deadline, step count, reported live-token threshold and enabled no-progress limit in the provided order. Reaching the boundary is enough; return None only if none applies.',
     explanation='stop_reason reports why another attempt is no longer allowed. It does not claim success. Individual tool attempts and operation timeouts are also bounded by the existing runner.',
     rubric='Explain an exact boundary, the None return, the special disabled no-progress value and why a stop reason is not verified completion.'),
 'loop': dict(hint1='Trace the action through the runner and ask who needs to see its returned observation next.',
     hint2='Use runner.execute to obtain obs, give obs.result to the same planner, call _update_check on the updated State, and return what the caller expects.',
     explanation='The helper connects execution to feedback and fresh verification. The runner records the result; the same planner receives feedback; the new check sees the evidence just collected.',
     rubric='Explain the order execute, observe, update check; distinguish a stored observation from planner feedback and describe why an old check is insufficient.'),
}

OUTPUT_WALKTHROUGHS = {
 't02': [
    ['lesson_result.json: evidence_kind', 'Whether this was a new live exchange or inspection of a saved teacher exchange.'],
    ['teacher route: observation.requests_made_now', 'How many API requests this student action made; reading a record makes none.'],
    ['single-round record: requested_tool_calls and response.message.tool_calls', 'How many calls the actual response proposed, and their names and arguments.'],
    ['single-round record: tool_attempts and observations', 'What local tool code actually ran and the results or refusals that were saved.'],
    ['single-round record: after.ready and after.missing', 'What the verifier can conclude after those results, and which evidence is still absent.'],
    ['single-round record: next_messages_not_sent', 'The prepared continuation was not sent in this one-request experiment.'],
 ],
 't03': [
    ['demo.json: case and evidence_kind', 'Which deliberately scripted test this is; it is not a live model failure.'],
    ['decisions and tool_attempts', 'Separate requests for a next step from actual local executions.'],
    ['naive_status and diagnostic_check', 'Compare what the weak loop claimed with what the outside evidence check found.'],
    ['ending and external_demo_cap', 'Identify the outside limit that contained a repeated loop. It does not repair the inner logic.'],
 ],
 't04': [
    ['demo.json: rows[].arguments', 'The actual proposed inputs for each gate test.'],
    ['rows[].result.status and rows[].result.error', 'Whether the request was refused and the stated reason.'],
    ['rows[].tool_attempts', 'Whether any local tool execution occurred. A recorded refusal need not be an execution.'],
 ],
 't05': [
    ['lesson_result.json: checks[].passed and checks[].log', 'The test outcome and where to read a failed assertion.'],
    ['student_observation.json: observation', 'The ID, tool, arguments and result saved by the learner\'s own function.'],
    ['original_arguments_after_edit and original_result_after_edit', 'Compare the changed original objects with the unchanged saved values.'],
    ['input_is_teaching_example', 'This small mutation check uses deliberate teaching inputs; it is not a sensor measurement.'],
 ],
 't06': [
    ['student_observation.json: stages[].check', 'Watch ready, missing, progress, evidence_ids and facts change as actual tool results are added.'],
    ['comparison_rows[].arguments and tool_statistics', 'Compare what each call received with the summary it returned. These cases are deliberate local teaching inputs.'],
    ['comparison_rows[].inputs_match and same_summary_as_correct', 'Separate the input comparison from an equal-looking summary. The same-summary wrong-input case makes this difference visible.'],
    ['comparison_rows[].check.ready and check.missing', 'Read whether that case supplies acceptable evidence for the report.'],
    ['observations', 'The actual local results used for the checks.'],
    ['empty_report_goal_check and empty_readings_goal_check', 'Compare the completion decisions for the same empty query under two different goals.'],
 ],
 't07': [
    ['student_observation.json: config', 'The limits used in this boundary demonstration.'],
    ['rows[].steps, no_progress and elapsed_at_least_seconds', 'The deliberately constructed boundary values.'],
    ['rows[].returned_stop_reason', 'What the learner\'s function returned for that case.'],
    ['inputs_are_boundary_examples', 'These are test situations, not measurements of a long real run.'],
 ],
 't08': [
    ['student_observation.json: run.status and run.reason', 'How the local run ended and why.'],
    ['run.steps, run.tool_attempts and run.trace', 'Follow proposals, actual executions, feedback and fresh checks.'],
    ['run.report and planner_kind', 'Read the checked report while retaining the scripted-planner label.'],
 ],
 't09': [
    ['demo.json: rows[].condition', 'The test situation used for this comparison.'],
    ['rows[].status and rows[].reason', 'The actual ending, not a generic success message.'],
    ['rows[].decisions and rows[].tool_attempts', 'Compare requests for a next step with actual tool executions.'],
    ['linked run.json: trace and report.evidence', 'Find the event that explains the ending and the source IDs used in any report.'],
 ],
}


def build():
    # Follow the actual executable sources. These excerpts do not contain complete
    # answers to the assessed function bodies, including both W4.2 subparts.
    focused = {
        't02.read_request': [('lecture','demos.py','single_round_request','request =',10),
                            ('lecture','demos.py','single_round_request','for call in calls:',12)],
        't02.practice_request': [('seminar','demos.py','single_round_request','request =',10)],
        't03.predict_failures': [('lecture','demos.py','bare_loop','for index in range',12),
                                ('lecture','demos.py','bare_loop','obs = runner.execute',4)],
        't03.practice_loop': [('seminar','demos.py','bare_loop','for index in range',12)],
        't04.gate_code': [('lecture','gateway.py','ToolRunner.execute','name=action.name',11),
                         ('lecture','gateway.py','ToolRunner.execute',"if 'machine_id'",7)],
        't04.practice_gate': [('seminar','gateway.py','ToolRunner.execute','name=action.name',11),
                             ('seminar','gateway.py','ToolRunner.execute',"if 'machine_id'",7)],
    }
    for modes in PATHS.values():
        for steps in modes.values():
            for step in steps:
                if step['id'] in focused:
                    step['code_refs'] = [focused_ref(*values) for values in focused[step['id']]]
    tasks=[]
    for id,title,minutes,purpose,concepts,target,run,q in SPECS:
        tasks.append(dict(id=id,title=title,minutes=minutes,practice_minutes=minutes,weight=minutes,
            purpose=purpose,logic=PATHS[id]['review'][0]['explanation'],
            code_walkthrough=WALKTHROUGHS[id],worked_answer=q['worked_answer'],questions=[q],
            code_refs=CODE_REFS[id],concepts=concepts,code_target=target,
            requires_teaching=True,requires_prediction=run,requires_setup=run,
            commands=[['seminar_step.py','--task',id]] if run else [],planned_calls=0,
            paths=PATHS[id],output_fields='Read the actual task report, evidence label, relevant results and any failed check. Show the important fields in the formal reply.',
            output_walkthrough=OUTPUT_WALKTHROUGHS.get(id,[]),
            hint1=q['hint1'],hint2=q['hint2']))
    verification_task = next(task for task in tasks if task['id'] == 't06')
    verification_task['required_code_targets'] = ['verify', 'stats_inputs']
    verification_task['code_exercises'] = [
        dict(id='W4.2A', target='verify', prompt='Write the goal checklist in verify and return the required evidence, gaps, IDs and facts.'),
        dict(id='W4.2B', target='stats_inputs', prompt='Write statistics_inputs_match so it compares the calculation argument record with the saved values and registered limit.')]
    verification_task['time_plan_minutes'] = {'explanation': 3, 'W4.2A': 4, 'W4.2B': 3, 'tests_and_output': 3, 'understanding': 2}
    verification_task['questions'].append(oq('q2',
        'In the same_count_same_summary_wrong_values case, why must we reject the statistics even though its count, mean, maximum and above-limit fraction match? Explain which inputs your guard compares.',
        'Use the actual comparison row, explain that identical summaries can come from different values, and identify both the observed values and registered limit as required arguments. Distinguish input matching from numerical validation.',
        'Look for the changed values in arguments, then compare inputs_match with same_summary_as_correct.',
        'The returned summary describes the supplied arguments. Does it establish that those arguments came from the saved task observations?',
        'The call used different values from the saved readings. Equal summaries do not prove equal inputs. My guard compares the complete argument record with values from the matching query and the limit from the matching specification. The numerical checks still verify the returned arithmetic after the inputs match.'))
    tasks[1].update(default_route='teacher',available_routes=['teacher','live'],live_planned_calls=1,
        teacher_data_required=True,teacher_data_file='teacher-data/single_round.json',teacher_data_manifest='teacher-data/SOURCE.json',
        evidence_rule='A teacher route must read a saved real API exchange and retain its provenance. It must not substitute a scripted reply when real evidence is missing. A live route requires explicit selection and privately configured credentials.')
    lesson=dict(id='week04',version=2,title='Build an agent loop that can finish a task and stop',
        language='English; Chinese translation only on explicit request',requires_api_key=False,
        teaching_order=['problem','prediction','observed evidence','plain explanation','actual code','learner attempt','test','explain output'],
        modes={'review':'Follow the lecture story, inspect experiments, explain the code, then build each part.',
               'practice':'Start from the exercises with the explanations and checks needed for each task.'},
        mode_cards=[dict(id='review',label='Review lecture + code',description='Follow the brain-and-hands story, see where a simple loop fails, revisit the slide diagrams, and build the missing checks with small code exercises.'),
                    dict(id='practice',label='Start seminar practice',description='Start the same experiments and four coding groups, including two short parts in W4.2. Get short concept explanations when you need them, with the same understanding checks.')],
        mode_common_note='Both paths take two 50-minute sessions and use the same completion requirements. Core study needs no GPU or personal API key when the genuine teacher capture is available. Optional live runs are labelled and require your choice.',
        foundations=FOUNDATIONS,code_targets={'record':['state.py','State.record'],
            'verify':['verification.py','verify'],
            'stats_inputs':['verification.py','statistics_inputs_match'],'guards':['controls.py','stop_reason'],
            'loop':['runtime.py','complete_tool_step']},code_support=CODE_SUPPORT,tasks=tasks,
        presentation=dict(one_active_question=True,code_lines_per_excerpt=12,
            final_reply_required=True,read_slide_before_code_in_review=True,
            student_style='Use ordinary words and connected sentences. Explain what just happened and why the next step helps. Avoid slogans, compressed labels, unexplained jargon and repeated confirmation questions.'),
        progress_policy='Use the helper\'s saved core_percent for the active week and session. Teaching steps, tool calls and optional work do not by themselves award task completion.',
        source_deck=DECK,extensions=[])
    for id,title,case,purpose,calls in [
        ('live_loop','Try your loop with DeepSeek','live-loop','Use a real model to propose actions while keeping the tested runtime, verifier and limits.',6),
        ('retry','Compare a temporary and a lasting error','retry','Inspect what changes after one bounded retry and count the actual attempts.',0),
        ('timeout','End a tool call that takes too long','timeout','Inspect a local subprocess timeout and distinguish it from a whole-run limit.',0),
        ('handoff','Ask for missing information','handoff','Inspect empty data or missing task fields, then read the specific handoff question.',0),
        ('workflow','Compare with a fixed workflow','workflow','Compare the same task with a straightforward fixed Python workflow, which can also have conditions.',0),
        ('boundaries','Try more boundary tests','boundaries','Inspect additional cases without removing the outside test limits.',0),
    ]:
        command=['seminar_step.py','--case',case]
        if calls:command += ['--mode','live']
        lesson['extensions'].append(dict(id=id,title=title,purpose=purpose,planned_calls=calls,
            commands=[command],code_refs=[],
            guide='Explain the task and purpose, save a prediction, run only the selected extension, read the actual evidence and explain the output. Optional work never changes core completion.',
            requires_live_approval=bool(calls)))
    assert sum(t['minutes'] for t in tasks[:5]) == 50
    assert sum(t['minutes'] for t in tasks[5:]) == 50
    assert sum(t['weight'] for t in tasks) == 100
    ROOT.mkdir(exist_ok=True)
    (ROOT/'lesson.json').write_text(json.dumps(lesson,indent=2)+'\n',encoding='utf-8',newline='\n')
    write_guide(lesson)
    return lesson


def write_guide(lesson):
    lines=['# Week 4 teaching script','',
        'Apply the current installed OUTPUT.md, persona.md and MENTOR.md. This saved guide supplies the curriculum, not permission to skip the final student-visible reply.',
        '', '## Start with the problem','',
        'Begin with the brain-and-hands story, then the complete CONV-3 request. Do not begin a fresh course with installation commands or a list of Python filenames. Setup comes when the first experiment needs it. Use the learner\'s chosen resume or new-session route.',
        '', '## Keep the interaction natural','',
        'Teach one manageable idea, then wait for an actual answer or action. Use the student_script paragraphs as natural speaking notes, not labels to recite. Connect each explanation to what the learner just saw. Define a new word before relying on it. Do not say "the application disposes", "evidence-backed orchestration" or other slogans in place of an explanation.',
        '', 'Offer foundation choices before the related exercise: I understand - continue / Explain briefly / Show an example. Respect the choice while keeping the actual exercise and understanding requirements. Use native choice cards where the host supports them, with the delivery sequence in OUTPUT.md.',
        '', 'Give two gradually clearer hints with a real learner response between them. Then offer more hints or an answer explanation. After explaining an answer, ask for the learner\'s own explanation and assess that new response before continuing. A test passing or a copied answer is not that explanation.',
        '', '## A lesson step and an experiment are different','',
        'before_run steps explain the problem, relevant code and prediction. Save the learner\'s real choice or code before running. after_run steps must wait for the actual report. Read the observed values, explain their structure and compare them with the prediction. Do not replace an observation with the expected answer printed on a slide.',
        '', 'Use lesson-next only after the explanation has actually appeared in the formal reply and the learner continues or completes the required check. Questions, translation, pauses and source inspection do not advance a step. Acknowledge an already delivered explanation at the next natural turn when needed, as OUTPUT.md describes.',
        '', 'Do not ask the same question twice just because it appears in both discussion and a task requirement. If an actual learner response already answers the current requirement, save that response with the relevant helper and evaluate it.',
        '', '## Sources and evidence labels','',
        'Show the original PDF page in review mode, talk through its diagram, and then open the related actual code. The PDF calls the same synthetic example M12; the current course calls it CONV-3. Explain this once. Use each slide card\'s clarification where the old slide simplifies or overstates the implementation.',
        '', 'A teacher capture is a saved real DeepSeek exchange, not a new student call. A scripted planner is a rule program, not an LLM replay. Fault injections are deliberate tests, not measurements of the model\'s error rate. A tool test executes real local code but does not validate a model\'s planning ability.',
        '', 'Inspect actual output before speaking about a result. Use the saved status, reason, counters and evidence IDs. Never label a timeout from the outside watchdog as a correctly implemented inner stopping rule. No true unbounded loop is executed.',
        '', '## Course scope and saved work','',
        'Core timing is 2 x 50 minutes, with the break outside those 100 minutes. The four exercise groups use small function bodies. W4.2 has two required subparts: the goal checklist and the statistics-input comparison, within the same 15 minutes. Keep the supplied validation and error branches. Extra live runs, retries, timeouts and handoffs are optional topics in the menu.',
        '', 'The seminar helper saves learning progress, answers, code and experiment records. The classroom agent uses in-memory execution state and does not yet support cross-process checkpoint recovery. A readable trace is not a resume button for that agent. Week 5 covers that separate problem.',
        '', '## Learning modes','']
    for card in lesson['mode_cards']:
        lines += ['- **'+card['label']+'**: '+card['description']]
    for task in lesson['tasks']:
        lines += ['', '## '+task['id']+' - '+task['title'], '',
                  f"Core time: {task['minutes']} minutes. Completion weight: {task['weight']}%.",
                  '', 'Purpose: '+task['purpose']]
        if task.get('code_exercises'):
            lines += ['', 'Required code subparts (save one learner body at a time):', '']
            lines += ['- '+part['id']+' / '+part['target']+': '+part['prompt'] for part in task['code_exercises']]
            lines += ['', 'Time within this 15-minute task: 3 minutes explanation, 4 minutes W4.2A, 3 minutes W4.2B, 3 minutes tests/output and 2 minutes understanding. Both code bodies are required before running the task.']
        for mode in ('review','practice'):
            lines += ['', '### '+lesson['modes'][mode], '']
            for step in task['paths'][mode]:
                lines += ['#### '+step['title'], '', 'Phase: '+step['phase']+'.', '',step['explanation'],'']
                if 'slide_review' in step:
                    s=step['slide_review']
                    lines += [f"PDF page {s['primary_slide']}: {s['image']}", '']
                    lines += ['- '+x for x in s['visual_walkthrough']]
                    lines += ['', 'Code connection: '+s['code_bridge'],'']
                    if s.get('clarification'):lines += ['Clarification: '+s['clarification'],'']
                for r in step['code_refs']:
                    lines += [f"Source: {r['pack']}/{r['file']} :: {r['symbol']}. Show at most {r['max_lines']} lines at a time.",'']
                lines += ['- '+x for x in step['code_walkthrough']]
                if step.get('one_next_action'):lines += ['', 'Next learner action: '+step['one_next_action'],'']
                if step.get('check'):
                    c=step['check'];lines += ['Checkpoint: '+c['prompt'],'']
                    lines += ['- '+key+': '+value for key,value in c['options'].items()]
                    lines += ['', 'Wait for the actual response. Keep the answer and hints private until the support rules allow them.','']
        lines += ['', '### After the actual output explanation','']
        for field,meaning in task.get('output_walkthrough',[]):
            lines += ['- `'+field+'`: '+meaning]
        lines += ['']
        lines += ['- '+q['prompt'] for q in task['questions']]
    lines += ['', '## Optional topics','']
    lines += ['- **'+x['title']+'**: '+x['purpose'] for x in lesson['extensions']]
    (ROOT/'TEACHING.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':
    built=build()
    print('Built Week 4 lesson version '+str(built['version'])+' with two 50-minute paths.')
