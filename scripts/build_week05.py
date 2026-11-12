"""Build the Week 5 lesson and its matching teaching guide."""

import json
from pathlib import Path
import sys


WEEK = Path(__file__).resolve().parents[1] / 'week05'
DECK = 'EEEE4149_Week5_Lecture_State_Machines_v3.pptx'
sys.path.insert(0, str(WEEK.parent))


def source(file, symbol, lines=8, offset=0, *, note=None):
    ref = dict(pack='seminar', file=file, symbol=symbol, max_lines=lines, slice_start=offset)
    if note:
        ref['note'] = note
    return ref


def step(task, suffix, title, script, *, action, refs=(), slides=(), phase='before_run', fields=()):
    result = dict(id=f'{task}.{suffix}', title=title, phase=phase,
                  logic=script[0], explanation='\n\n'.join(script), student_script=list(script),
                  one_next_action=action, code_refs=list(refs), slides=list(slides),
                  evidence_fields=list(fields))
    if refs:
        result['code_notes'] = [ref.get('note', '') for ref in refs]
    if slides:
        result['slide_review'] = dict(source_deck=DECK, primary_slide=slides[0],
                                      related_slides=list(slides[1:]), title=title,
                                      focus=script[0], explanation='\n\n'.join(script),
                                      code_bridge=refs[0].get('note') if refs else None)
        image = f'slides/slide-{slides[0]:02d}.png'
        if (WEEK / image).is_file():
            result['slide_review']['image'] = image
    return result


def paths(task, title, review, practice, observed, predict, interpret, *, slides, refs, fields, closing):
    result = {}
    for mode, preparation in [('review', review), ('practice', practice)]:
        show_slides = slides[0] if mode == 'review' else ()
        show_results = slides[1] if mode == 'review' else ()
        current = step(task, mode + '_prepare', title, preparation, action=predict, refs=refs, slides=show_slides)
        result[mode] = [current]
        if observed:
            result[mode].append(step(task, mode + '_evidence', 'Read the actual result', observed,
                                     action=interpret, slides=show_results, phase='after_run',
                                     fields=fields))
        result[mode][-1]['closing_line'] = closing
    return result


def question(prompt, rubric, hint1, hint2, answer):
    return dict(id='q1', type='open', prompt=prompt, rubric=rubric,
                hint1=hint1, hint2=hint2, worked_answer=answer)


def task(id, title, minutes, purpose, review, practice, observed, predict, interpret, check,
         *, closing, slides=((), ()), refs=(), fields=(), concepts=(), target=None):
    return dict(id=id, title=title, minutes=minutes, practice_minutes=minutes, weight=minutes,
                purpose=purpose, logic=review[0], questions=[check], code_refs=list(refs),
                concepts=list(concepts), code_target=target, requires_teaching=True,
                requires_prediction=bool(observed), requires_setup=bool(observed),
                commands=[['seminar_step.py', '--task', id]] if observed else [], planned_calls=0,
                paths=paths(id, title, review, practice, observed, predict, interpret,
                            slides=slides, refs=refs, fields=fields, closing=closing))


INSTRUCTOR_OPENING = (
    'Hi everyone. By the time you open this plugin, I’ll probably be on my way to a meeting. '
    'I had a bit of brain fog in yesterday’s lecture, and some of my explanations came out in bits and pieces.',
    'I went back over the material afterward and put it in a clearer order for this seminar. '
    'By the end, I hope you’ll have picked up a few of my moves and can use them on your own. '
    'All right. Time to pass on a little kung fu.',
)

OPENING_STORY = (
    'Think back to where we started. In Week 1, we got Python to call a language model and learned how to check its answers. '
    'In Week 2, we built a small model to see how it makes predictions. In Week 3, we gave the model tools. '
    'Last week, we put those tools in a loop so the agent could take several actions, check what happened and decide when to stop.',
    'Now give that agent a bigger job. Find me a flight, use its dates to look for a hotel, ask me to approve the plan, '
    'make the bookings and send a confirmation. Each step uses something the previous step found or decided.',
    'Suppose the agent finds a 9 a.m. flight and is about to look for a hotel when Python crashes. '
    'If we used last week’s loop for this job, the selected flight and the next step would live in that Python process’s memory. '
    'When the process closes, those values are gone. Even with the original request, the new process has to start the search again.',
    'This week, we’ll give the workflow a set of named steps and save its progress to disk. '
    'A state machine organizes the steps and the routes between them. After each completed step in our workflow, '
    'we’ll save what the program knows and where it should continue. That saved record is called a checkpoint. '
    'If Python stops again, the next process can load the selected flight from disk and go straight to looking for a hotel.',
)

OVERVIEW = [
    '**State: what do we know?** The workflow keeps the flight, dates and any reply in its state. When the flight search returns a flight, the workflow adds it to that record. Without the dates, the hotel search cannot pick the right nights.',
    '**Node: who does the work?** The flight search is one node. It takes what it needs from state and returns an update, such as the selected flight. If it returns an empty update after a successful search, the hotel step cannot see what it found.',
    '**Edge: where do we go?** The graph follows an edge to the next node. A routing function can send a sold-out flight back to search. A fixed edge to payment would send a rejected request there too.',
    '**Checkpoint: what survives a crash?** The checkpointer saves the state and the pending step together. In the second session it writes to SQLite. If we reopen that file for the same workflow, the new process can use the saved flight and `next` step. Without that save, the new process cannot recover them.',
    '**Interrupt: where do we wait for a person?** The approval node asks for a decision and pauses at that request. The saved workflow stays there until a reply arrives. If we leave out the pause, the program may carry on before anyone has approved the booking.',
    'There is one more problem. A crash can happen after the provider charges you but before our checkpoint advances. The saved position tells the workflow which step to try again. The provider needs a stable request number so it can find the old receipt and avoid a second charge.',
    '```text\nFind a flight -> Look up a hotel -> Wait for approval (interrupt)\n                                   | approved -> Book -> Send confirmation\n                                   | rejected -> Finish\n\nForgot the flight?      State stores it.\nNeed a different step?  A routing function chooses an edge.\nPython closed?         A checkpoint stores the flight and the next step.\nNo decision yet?       The interrupt keeps the workflow waiting.\nAlready charged?       The provider checks the same request number before charging.\n```',
]

OVERVIEW_CHECK = dict(
    type='mcq', required=True,
    prompt='The workflow found a flight and then Python closed. Which part gives the new process the saved flight and the pending step?',
    options={'A': 'The checkpoint', 'B': 'The conditional edge alone', 'C': 'The booking node alone', 'D': 'The approval question alone'},
    correct='A', explanation='The checkpoint saves the workflow state and where it needs to continue.',
    hint1='Which part outlives the Python process?',
    hint2='The graph can describe the route even before there is a particular flight. Look for the part that saves this run’s values.',
)

CRASH_EXPERIMENT = [
    '**Question.** How much work does restarting repeat? Can the workflow still pay twice after it has saved a checkpoint?',
    '**Setup.** Run 2,000 trips with seed 7 and the same nine-step booking task and 10 percent failure chance. The fixed settings make the comparison repeatable, and many trips give us an average across failures at different steps. This experiment stores checkpoints inside the simulation. We will close a real Python process and reopen SQLite later.',
    '**Results to read.** `mean_steps` and `mean_restarts` show the cost of redoing work. `extra_charges` shows what was charged again at the provider.',
]

DECIDE_EXPERIMENT = [
    '**Question.** We can pick up where we stopped, but what if the flight sells out before we can book it? '
    'The same next step now returns an error. Can the agent change its plan?',
    'Reflex asks for one action and stops after running it. ReAct sees each tool result before choosing again. '
    'Plan-execute gets a list up front and can ask for a revised list if it hits an error and has replans left.',
    '**Setup.** Run all three on the same 30 tasks with seed 7, first with normal availability and then with sold-out flights or hotels. '
    'Compare zero and one replan for plan-execute. The same tasks, seed and fixed decision rules let us repeat the comparison and see what changed when we allowed one replan.',
    '**Results to read.** `completed` counts finished trips, `planning_calls` counts decisions, and `failed_with_bookings` counts unfinished trips that still booked something. Open `sample.tool_log` to see where a sold-out trip changed course.',
]

REDO_EXPERIMENT = [
    '**Question.** Can we fix our saved totals and still charge a customer twice? Which change fixes each problem?',
    '**Setup.** Run the same 2,000 trips with seed 7. First compare `in_place` and `update` with no key to isolate the save method. '
    'Then keep `update` fixed and compare no key, a new key on each attempt and a stable key. Now the request number is the only change.',
    '**Results to read.** `wrong_final_states` and `replay_matches` describe our saved record. `repeated_actions` and `blocked_requests` describe the provider. `counterexamples` shows what breaks when we change one rule on purpose.',
]

REDO_CHECK = question(
    'The trace already contains `requested`, and the node produces `report ready`. Using both result tables, '
    'show what update you would save and what request IDs you would use for a retry and for a different ticket.',
    'Provide a trace update containing only report ready, reuse one stable ID for the retry, give a different ID to the distinct action, '
    'and cite actual results from both comparisons.',
    'Separate the existing trace from what the current node adds.',
    'A retry repeats the same logical action. A new booking is a distinct action even on the same trip.',
    'The update contains only report ready. Keep the same ID for retrying one ticket and use a different ID for the second ticket. '
    'The state comparison shows which save style leaves the correct state. The key comparison shows whether the provider recognizes a repeated request.',
)

REDO_OPEN = (
    'Rules stand first — only then does the workflow stop hurting.',
    '**（规矩立住了，流程才不烧心）**',
)
REDO_BRIDGE = (
    'Rules stand first — only then does the workflow stop hurting. Our ledger is quiet now; theirs is not.',
    '**（规矩立住了，流程才不烧心——我们这本安静了，他们那本还没有。）**',
)
REDO_RULES = [
    dict(rule='1. Return an update.',
         why='Return just what this node adds.',
         counterfactual='Appending `["verified", "prepared"]` to a saved log that already contains `"verified"` repeats that first entry.',
         evidence='`whole_log_as_update` compares that replay with appending just `["prepared"]`.',
         code_map='Look for `return {…}` in `select_ticket`: it returns only the selected ticket. The same rule applies to a log update.'),
    dict(rule='2. Merge computes the new state.',
         why='Add costs to `spent`, append events to `log`, and replace `next` with the new step name.',
         counterfactual='Adding `next` to `ADD` joins two step names. Removing `spent` from `ADD` lets the workshop cost replace the pass cost.',
         evidence='The replay records an invalid next step in one case and an incorrect receipt in the other.',
         code_map='`merge` adds fields in `ADD` and replaces the others.'),
    dict(rule='3. Commit once.',
         why='Save the new state and `next` together.',
         counterfactual='If the crash hits after the total changes but before `next` advances, the same step can add its cost again.',
         evidence='`partial_commit` forces a stop at that point and records both saved states.',
         code_map='In `run_trip`, lines 110–113 build the new state and set `next` before publishing the combined in-memory checkpoint.'),
]

REDO_TWO_LEDGERS = dict(
    example='Trip 17 has just paid $960 for four conference passes. The payment goes through, then the workflow crashes before it saves that the workshop booking is next.',
    why_two_ledgers='The booking provider has a receipt for $960. Our workflow’s saved state still says to pay for the passes. Each system saves its own record. The provider can finish charging before our workflow records that the payment is done.',
    analogy='Picture a booking counter. On the first visit, the clerk takes $960 and files the receipt under your request number. The receipt never reaches you. You come back with the same number. The clerk checks the register before reaching for the card reader, finds the old receipt and hands it back. If the number is missing from the register, the clerk processes the payment and files a receipt under that number.',
    mechanism_steps=(
        '1. Build the request number from the saved trip and step. This payment always uses `17:pay_for_ticket`.\n'
        '2. Look for that number in the provider’s register before charging.\n'
        '3. If the number is there, return the saved result. The provider does not charge again.\n'
        '4. If the number is missing, process the payment, save the result under that number and return it.\n\n'
        'Build the number from the restored workflow, so a retry can rebuild it. A fresh number makes the clerk charge again. A number for the whole trip alone is too broad: the clerk might return the pass receipt when you meant to book the workshop.'
    ),
)

REDO_CODE_WALKTHROUGH = (
    '`key = f"{trip}:{node}"` rebuilds the same request number from trip 17 and the payment step.',
    '`if key is not None and key in self.receipts` checks the register before any payment.',
    '`return self.receipts[key]` hands back the saved result and exits before the charge. `self.blocked` counts that avoided repeat.',
    '`self.done[trip, kind] += 1` records that the simulated provider has carried out the action.',
    '`self.receipts[key] = update` files the result under that number. The last `return update` sends back the new result.',
)

APPROVAL_MECHANISM = dict(
    example='A tutor opens the CONV-3 report on Monday. On Tuesday a corrected temperature reading is included and the data file is regenerated. The ticket request can still have the same number. Should Monday’s approval create a ticket for Tuesday’s report?',
    why_two_ledgers='The tutor’s reply records what they saw. The workflow’s waiting request records what it is about to submit. A new version can keep the same request number, so we also check the contents.',
    analogy='Think of the request number on an envelope and a wax seal made from its contents. The request number (`action_id`) tells us which envelope it is. When the corrected report goes inside, it gets a different seal (`payload_hash`). The tutor’s reply carries the seal they saw, so we can spot a reply for the earlier version.',
    mechanism_steps='When preparing a request, include the data file’s fingerprint (`data_fingerprint`) and the report in the payload, then compute the seal. When reading a reply, compare its ID and hash with the waiting request. Require a real JSON Boolean and a nonempty reviewer name. Try JSON `false` for the current report, text `"false"` for that report, and JSON `true` for the old report.',
    code_map='In `make_action`, look at what goes into `payload`, how the ID comes from the thread, and how `digest(payload)` makes the seal. Then add the reply checks to `validate_decision`.',
)

CHECKPOINT_MECHANISM = dict(
    example='The tutor will reply tomorrow. Today, Python closes with the CONV-3 report still waiting. How will tomorrow’s process find this report instead of starting the tools again?',
    why_two_ledgers='The checkpoint holds the report and the pending step. The separate ticket database records tickets that have actually been written. A waiting report has a checkpoint even though it has no ticket.',
    analogy='Think of a patient’s medical folder. `thread_id` is the folder label. Each visit adds a page: one may say “report verified” and a later one “waiting for approval.” Each saved page has its own `checkpoint_id`. Start and inspect should open the same latest page. A different workflow would have a different folder.',
    mechanism_steps='Close the first process and open the same `checkpoints.sqlite` file with the same thread ID. The checkpointer finds the latest page. Use synchronous durability for this lab so a step’s checkpoint is saved before the next step starts.',
    code_map='`config` supplies the thread ID. Write `resume_approval` to use that same config, pass the reply in `Command(resume=decision)` and return the result of invoking the graph with `durability="sync"`. Then start and inspect the three waiting reports in separate processes.',
)

INTERRUPT_MECHANISM = dict(
    example='Two CONV-3 requests are waiting. We will approve `week05-approve` and reject `week05-reject`, then check a malformed reply. Before we run that test, picture the waiting step writing a ticket before it asks the question.',
    why_two_ledgers='The checkpoint records where the workflow is waiting. The ticket table records what was actually written. Restoring a waiting page cannot undo a ticket that was already inserted.',
    analogy='Think of a clerk reopening the medical folder and starting the instructions on the waiting page from the top. When the clerk reaches the approval question again, the answer is now in the folder. Anything the clerk did above that question can happen again.',
    mechanism_steps='LangGraph starts the interrupted node again from the top when `Command(resume=decision)` resumes it. At `interrupt()`, the saved reply now comes back as the return value. Keep ticket writes out of the waiting node. If an unprotected insert ran before `interrupt()`, it would run before the pause and again on resume and could create two tickets. The counter test demonstrates those two executions without writing duplicate tickets.',
    code_map='In `human_approval`, find the call to `suspend` (our name for LangGraph’s `interrupt`) and the line that reads the reply. In `decide`, check where the reply is validated. In `route_approval`, trace where a valid approval goes and why rejection never reaches `ApplyAction`. Use the saved ID and hash for each request.',
)

RECOVERY_MECHANISM = dict(
    example='This time you will approve `week05-recovery`. The CONV-3 ticket is written, but Python stops before the workflow saves that the write finished. The next process retries `ApplyAction`. Here we are rerunning the writer after a crash, rather than rerunning the waiting node when the tutor replies.',
    why_two_ledgers='`checkpoints.sqlite` still says the writer is pending. `effects.sqlite` already contains the ticket. The workflow’s checkpoint and the ticket insert are two separate saves.',
    analogy='Remember `blocked_requests` in Redo? With seed 7, the stable key blocked 315 repeated requests. Here the SQLite `tickets` table is the booking clerk’s register. The `action_id` is the stable request number. A result of `reused=True` means the clerk found the original ticket and handed it back.',
    mechanism_steps='Look up the same `action_id` before inserting. If the hash matches, return that existing ticket. If the same number arrives with a different `payload_hash`, refuse it with an error. This is how we avoid treating a changed request as one we have already done. Insert only if there is no row for that ID.',
    code_map='In `apply_action`, find where the controlled stop happens after the write. In `EffectStore.apply`, follow the lookup, the conflicting-hash check and the `reused` return. Then continue from another process and use the saved records to see whether a second row appeared.',
)

FOUNDATIONS = {
    'checkpoint': dict(id='checkpoint', title='State and checkpoints',
        brief='State is what the workflow currently knows. A checkpoint stores the state and the position needed to continue.',
        example='A saved booking record can hold the chosen flight and the next action, book the flight.'),
    'routing': dict(id='routing', title='Nodes and conditional edges',
        brief='A node performs one part of the task. A conditional edge chooses where to go by reading a result or state field.',
        example='After verifying a report, a rule can choose to prepare approval, retry, or finish.'),
    'effects': dict(id='effects', title='State changes and external actions',
        brief='A state update changes what the workflow knows. An external action changes another system, such as adding a ticket.',
        example='Appending a log event and creating a booking are two separate changes, so they need separate checks.'),
    'approval': dict(id='approval', title='Approval binds a decision to an action',
        brief='An approval identifies the proposed action and its exact payload. The decision itself must be a JSON boolean.',
        example='JSON false is a valid rejection. The string "false" is rejected as invalid input.'),
    'thread': dict(id='thread', title='Workflow thread and checkpoint',
        brief='A thread ID identifies a workflow instance. A checkpoint ID identifies one saved state in that thread.',
        example='Open the same SQLite database and use the same thread ID after the first Python process closes.'),
}

TARGETS = {
    'route': ['workflow/routing.py', 'route_verify'],
    'edges': ['workflow/graph_app.py', 'connect_conditional_edges'],
    'approval': ['workflow/approval.py', 'validate_decision'],
    'resume': ['workflow/service.py', 'resume_approval'],
}

SUPPORT = {
    'route': dict(hint1='Can a terminal status be reopened by an older ready flag?',
        hint2='Check terminal status first. Next decide what a verified report needs, then handle a retryable error and the remaining planning path.',
        explanation='The router gives terminal status priority, then handles readiness and retries. The Retry node owns the budget check.',
        rubric='Explain the first matching branch and why a stale ready flag cannot reopen a failed task.'),
    'edges': dict(hint1='Find the two places where the next node depends on a function result.',
        hint2='Connect Verify to its possible route results, and HumanApproval to the apply and finish outcomes.',
        explanation='The two conditional edges call the appropriate router. The approval router can direct a rejection to Finish.',
        rubric='Trace the rejection branch and identify the only node that creates a ticket.'),
    'approval': dict(hint1='What type is the value between quotation marks?',
        hint2='A nonempty string passes a truthiness check. Read the proposed action identity and payload fingerprint as well as the type.',
        explanation='Approval validates the exact action, exact payload and boolean decision before applying any change.',
        rubric='Distinguish a valid false decision from invalid input and explain why action binding matters.'),
    'resume': dict(hint1='Which identifier lets the new process find the same workflow instance?',
        hint2='Use the graph with its checkpointer, keep the thread configuration, and put the submitted decision in the resume command.',
        explanation='The resume invocation supplies the decision to the current interrupted task in the saved thread.',
        rubric='Explain how the workspace, thread and resume value each contribute to recovery.'),
}


def add_openings(tasks):
    redo_rule_refs = (
        source('experiments/redo.py', 'select_ticket', 3, note='Return the selected ticket as a small update.'),
        source('experiments/redo.py', 'merge', 5, note='Fields in ADD are added. Other fields take the new value.'),
        source('experiments/redo.py', 'run_trip', 12, 17, note='The simulated crash can interrupt an in-place write before next advances. The update branch saves them together.'),
    )
    rules_script = [
        'In our next simulation, the booking provider charges 960 USD for four conference passes on trip 17. '
        'We simulate a crash before the workflow records that the workshop booking is next. '
        'The provider has recorded the charge, but our saved record still points to the pass purchase. Start with what we can fix in our own record.',
        'That mishap has the right soundtrack: *Qiu Long* by Beizhou, nicknamed the heartbreak tune from short dramas. '
        '[Optional: open it on Bilibili in a new tab and listen for 15 seconds](https://www.bilibili.com/video/BV1min86QEHN/). '
        'The recording stays on the external platform for copyright reasons. If the link is blocked, search for the song on QQ Music or NetEase Cloud Music, or skip it and keep going.',
        *REDO_OPEN,
        *(f"**{rule['rule']}** " + ' '.join(rule[key] for key in ('why', 'counterfactual', 'code_map')) for rule in REDO_RULES),
    ]
    for mode in ('review', 'practice'):
        overview = step('t01', mode + '_overview', 'Pick up the booking after a restart',
                        [*INSTRUCTOR_OPENING, *OPENING_STORY, *OVERVIEW],
                        action=OVERVIEW_CHECK['prompt'])
        overview['logic'] = OPENING_STORY[0]
        overview['instructor_opening'] = list(INSTRUCTOR_OPENING)
        overview['opening_story'] = list(OPENING_STORY)
        overview['check'] = OVERVIEW_CHECK
        overview['teaching_minutes'] = 4
        tasks[0]['paths'][mode].insert(0, overview)

        rules = step('t05', mode + '_rules', 'Three rules for saving workflow state', rules_script,
                     action='Continue to the provider’s record.',
                     refs=redo_rule_refs, slides=(20,) if mode == 'review' else ())
        rules['required_student_text'] = list(REDO_OPEN)
        rules['rules'] = REDO_RULES
        two_ledgers = step('t05', mode + '_two_ledgers', 'A stable number for the same request',
                           [*REDO_BRIDGE, *REDO_TWO_LEDGERS.values()],
                           action='What would the clerk do if this retry arrived with a different number?',
                           refs=(source('experiments/redo.py', 'World.act', 12, 1),),
                           slides=(23,) if mode == 'review' else ())
        two_ledgers['required_student_text'] = list(REDO_BRIDGE)
        two_ledgers['code_walkthrough'] = list(REDO_CODE_WALKTHROUGH)
        tasks[4]['paths'][mode][:0] = [rules, two_ledgers]

def set_delivery_order(tasks):
    primary_counts = {'t01': 2, 't02': 3, 't03': 2, 't04': 2,
                      't05': 3, 't06': 2, 't07': 2, 't08': 3, 't09': 3}
    for task in tasks:
        check = task['questions'][0]
        for path in task['paths'].values():
            for node in path:
                count = min(len(node['code_refs']), primary_counts.get(task['id'], 1))
                if count:
                    node['primary_code_indices'] = list(range(count))
            if path[-1]['phase'] == 'after_run':
                path[-1]['one_next_action'] = check['prompt']
            path[-1]['task_question_id'] = check['id']


def build():
    setup = ('If the workflow check reports that LangGraph is missing, use Python 3.11 or newer. '
             'From the seminar resources folder, run `python -m pip install -r workflow/requirements.txt` '
             'with the same Python interpreter you will use to run the checks.')
    tasks = [
        task('t01', 'Crash and checkpoint', 11, 'Compare starting again with restoring state and the next step.',
            ['The while loop keeps its position in a local variable and starts at the first step after a failure. The graph reads the pending step from the saved `next` field. A simulated failure can occur before an action or just after it, before `next` is saved.', *CRASH_EXPERIMENT],
            ['The booking program crashed. One version restarts from the first step. The other retrieves the saved task and runs its saved `next` step. Compare what they repeat.', *CRASH_EXPERIMENT],
            ['Compare the two rows using `mean_steps`, `mean_restarts` and `extra_charges`. Explain how one row can have fewer repeated steps and still have extra charges.',
             'With an independent 10 percent chance of failure, each step succeeds with probability 0.9. The checkpoint version needs about 9 / 0.9 = 10 attempts. Starting over needs a run of nine successes and takes about 15.8 attempts. Compare these estimates with your own run.'],
            'Predict which strategy will execute more steps and whether a saved checkpoint can still leave a repeated booking.',
            'Use one numeric difference and the saved next field to explain your result.',
            question('How did saving state and next change the rerun cost? Why can a repeated booking remain?',
                'Use one actual numeric comparison and explain the interval between the action and checkpoint commit.',
                'Compare steps per trip in the two rows.',
                'If booking succeeds but the checkpoint still names that action, what will the restart execute?',
                'The restored version resumes the saved step and usually repeats fewer steps. A booking can still repeat if its effect happened before the next checkpoint was saved.'),
            closing='A checkpoint can save repeated work. A booking may still have happened before the latest save.',
            slides=((6, 5, 8), (7, 8)), concepts=('checkpoint',),
            refs=(source('experiments/crash.py', 'agent_loop', note='The local position starts at zero every time the function is entered. An exception ends that attempt before the position is returned.'),
                  source('experiments/crash.py', 'agent_graph', 11, note='The next node comes from the saved dictionary. The code saves the new state and advances next only after the call returns.'),
                  source('experiments/crash.py', 'step', 9, note='A simulated exception can happen on either side of the action. When it happens after the action, the outside effect can already exist.')),
            fields=('strategy', 'mean_steps', 'mean_planning_calls', 'mean_restarts', 'extra_charges')),
        task('t02', 'Decide who chooses the next action', 7, 'Compare the planning trade-offs on the same 30 tasks.',
            DECIDE_EXPERIMENT, DECIDE_EXPERIMENT,
            ['Compare `completed`, `planning_calls` and `failed_with_bookings` for normal and sold-out trips. '
             'Use `sample.tool_log` to follow a trip where the first flight and the first hotel both sold out. '
             'See when ReAct sees each error and when plan-execute uses its one replan.'],
            'What do you expect one replan to change when the first flight sells out?',
            'Compare the zero and one replan rows. What changed in completed trips and why can a trip remain unfinished?',
            question('Compare the zero and one replan rows. What changed in completed trips and why can a trip remain unfinished?',
                'Cite the two actual counts and explain a second failure after using the available replan.',
                'Look at the sold-out rows for plan execution.',
                'Imagine a flight and a hotel both fail after planning. How many revised plans does the budget permit?',
                'One replan can choose a replacement after one failure. If a later action also fails after that replan is used, the workflow may stop with part of the booking already applied.'),
            closing='A plan saves decision calls when its assumptions hold. Replanning gives it another chance when they change.',
            slides=((11, 12, 14), (15, 16)), concepts=('routing',),
            refs=(source('experiments/decide.py', 'reflex', note='The policy asks for a single choice and makes one search. It has no loop for the next booking step.'),
                  source('experiments/decide.py', 'react', 9, note='Each choice uses the current history. The tool result is appended, so the next choice can see whether it succeeded.'),
                  source('experiments/decide.py', 'planexec', 5, 13, note='Zero remaining replans means stop. With one left, spend it and ask for another plan using the recorded results.'),
                  source('experiments/decide.py', 'planexec', 11, note='The planner supplies steps once. Before running a tool, resolve any argument that refers to earlier results. Stop the inner loop on an error.')),
            fields=('scenario', 'strategy', 'replans', 'completed', 'planning_calls', 'failed_with_bookings', 'sample.tool_log')),
        task('t03', 'W5.1 Write the Verify router', 12, 'Route from terminal, verified, retryable or unfinished state.',
            ['Let’s make the next-step decision ourselves in our Week 4 CONV-3 agent. '
             'The run has failed, but `ready=True` is still there from an earlier check. '
             'Write `route_verify` so it reads the current state and returns one destination. '
             'Also try a temporary error with no retries yet, shown by `retry_total=0`.', setup],
            ['The CONV-3 run has failed, but `ready=True` is still there from an earlier check. '
             'Decide where it should go and write `route_verify`, a function that returns one destination from the current state. '
             'Then try a temporary error with no retries yet, shown by `retry_total=0`.', setup],
            ['Use `exercise.cases` to compare your predictions with the destinations the router returned. '
             'Check which condition won when a failed run still carried `ready=True`, and where the first temporary error was sent.'],
            'Where should the failed run with the old ready flag go?',
            'Why must a terminal check come before the ready check, and which node decides if a retry fits the budget?',
            question('Why must a terminal check come before the ready check, and which node decides if a retry fits the budget?',
                'Explain terminal precedence over a stale ready flag, and identify Retry as the node checking the budget.',
                'Can an old ready flag make a failed task active again?',
                'The router names a destination. Inspect the node that performs the retry check.',
                'A terminal state has priority even if ready was saved earlier. The Retry node checks whether another attempt fits the budget.'),
            closing='The router chooses a destination. The Retry node owns the retry budget.',
            slides=((17,), ()), target='route',
            refs=(source('workflow/routing.py', 'route_verify', note='This is the function to complete. It receives a state dictionary and returns the name of exactly one next node.'),
                  source('workflow/routing.py', 'route_planner', note='This smaller router demonstrates how returning a node name selects a route.'),
                  source('workflow/nodes.py', 'Nodes.retry', 7, note='Retry owns the budget. Look at where it increments the count, and where it returns a terminal failure instead.')),
            fields=('test case', 'expected route', 'observed route')),
        task('t04', 'W5.2 Connect the workflow graph', 11, 'Connect the Verify and HumanApproval branches in the graph builder.',
            ['Your router returns a node name. Now connect it to the graph so LangGraph knows which destination to run. '
             'Imagine the tutor rejects the CONV-3 report. If we added a fixed edge from `HumanApproval` to `ApplyAction`, the graph would still call the ticket writer. '
             'A conditional edge chooses a destination using the router. Connect the two missing branches for `Verify` and `HumanApproval`.',
             setup + ' Then use that interpreter for `python -m workflow check edges`.'],
            ['The tutor rejects the CONV-3 report. What would the graph do if `HumanApproval` had a fixed edge to `ApplyAction`? '
             'Use the two router functions to connect the missing conditional edges so the decision controls the next node.',
             setup + ' Then use that interpreter for `python -m workflow check edges`.'],
            ['Use `exercise.edges` to find the conditional connections you just added. '
             'Trace `HumanApproval` on a rejection and check whether the ticket writer is on that path.'],
            'What would go wrong if the approval step always went to the ticket writer?',
            'Which node waits, which one writes a ticket, and how do your edges keep rejection from writing?',
            question('Which node waits, which one writes a ticket, and how do your edges keep rejection from writing?',
                'Name HumanApproval and ApplyAction and trace rejection to Finish with no ApplyAction edge on that branch.',
                'Read the next node name returned for a rejected decision.',
                'Start with HumanApproval and follow only its rejected branch to Finish.',
                'HumanApproval waits. ApplyAction writes the ticket. The rejected result routes directly to Finish.'),
            closing='A conditional edge gives each decision one next node. A rejection finishes before the ticket writer.',
            slides=((28, 32), ()), target='edges',
            refs=(source('workflow/graph_app.py', 'connect_conditional_edges', note='Add two conditional branches to the existing builder.'),
                  source('workflow/graph_app.py', 'build_graph', 10, 16, note='add_edge sets one destination. add_conditional_edges attaches a router and lists its possible destinations.'),
                  source('workflow/routing.py', 'route_approval', note='The current status and the exact Boolean decision control the two outcomes.')),
            fields=('conditional edges', 'route checks', 'approved destination', 'rejected destination')),
        task('t05', 'Redo state and external actions', 9, 'Separate repeated state updates from repeated external effects.',
            REDO_EXPERIMENT, REDO_EXPERIMENT,
            ['Read `wrong_final_states` for our saved record, then `repeated_actions` and `blocked_requests` for the provider. '
             'Use `replay_matches` to check whether the saved updates rebuild the same final state. In the seed 7 comparison, mutating state in place left 281 trips with wrong final states; returning an update removed those errors.',
             'Verify the examples in `counterexamples`. `whole_log_as_update` shows the duplicate entry. '
             "`next_in_add` records `KeyError: 'read_requestsearch_tickets'`. `spent_not_in_add` gives 180 USD instead of the independent total of 1,140 USD. "
             'The simulation can still report `wrong_spent=0` because it uses the same wrong merge for its reference.',
             'In `partial_commit`, compare the saved `next`, `spent_usd` and `ticket_charges` across the stop and restart. '
             'Saving state and `next` together gives 1,140 USD instead of 2,100 USD in our record. Without a key, the provider still charges twice.'],
            'Predict which state update will reduce bad final states and which key will reduce repeated actions.',
            REDO_CHECK['prompt'], REDO_CHECK,
            closing='Commit the workflow’s update together. Give the provider a stable key for each action.',
            slides=((), (21, 24)), concepts=('effects',),
            fields=('wrong_final_states', 'repeated_actions', 'blocked_requests', 'replay_matches', 'counterexamples')),
        task('t06', 'W5.3 Validate an approval', 12, 'Bind a boolean decision to the exact pending CONV-3 review action.',
            list(APPROVAL_MECHANISM.values()), list(APPROVAL_MECHANISM.values()),
            ['Use `exercise.cases` to compare `accepted` and `reason` for the Boolean and string replies.',
             'Then find “a changed report needs a new approval.” Compare `old_payload_hash`, `new_payload_hash` and `original_decision_rejected`. The fresh decision covers the new report.'],
            'Of those three replies, which should your validator accept?',
            'Use the test rows to explain why a valid rejection and a malformed reply are different.',
            question('Why is JSON false a valid rejection but the string "false" invalid? What is the purpose of checking the action ID and payload hash?',
                'Explain strict boolean type and that approval binds to the specific waiting action and its content.',
                'What type is the value between the quotation marks?',
                'A nonempty string passes a truthiness test. Which exact type and which identity fields should the validator require?',
                'JSON false has boolean type and is a valid negative decision. The string is rejected. The action ID and hash ensure that the decision addresses this exact pending action and payload.'),
            closing='A valid approval covers one specific action and the exact contents the reviewer saw.',
            slides=((27, 29, 30), ()), concepts=('approval',), target='approval',
            refs=(source('workflow/approval.py', 'make_action', 12, 4, note='The payload contains the data fingerprint and report. The ID comes from the thread, while the hash comes from the payload.'),
                  source('workflow/approval.py', 'validate_decision', note='The function you write returns a normalized reply after checking its type, action binding and reviewer label.'),
                  source('workflow/approval.py', 'checked_action', note='Before using the waiting action, compare it with one derived again from the verified report.')),
            fields=('validator case', 'accept or refuse', 'reason')),
        task('t07', 'W5.4 Find the same workflow in a new process', 12, 'Use LangGraph and SQLite to save a waiting workflow and inspect it from a separate process.',
            list(CHECKPOINT_MECHANISM.values()), list(CHECKPOINT_MECHANISM.values()),
            ['The resume check uses a stand-in graph to test the function call. In the real `processes` results, compare the start and inspect records for one thread. Check the process, thread and checkpoint IDs, the pending step and the tool evidence.',
             'This is the third Redo rule in a real workflow: the step’s state and next position are saved together. With `sync`, the save finishes before the next step starts. With `async`, the next step can start while the save is still in flight, so a hard crash can lose that latest save. With `exit`, the graph saves at an exit such as a normal finish or a pause; a hard crash before that point can lose work since the last saved run.',
             'The saved `decision_requests` contain the action IDs and hashes for the next two tasks.'],
            'Which fields would you compare to tell whether the new process found the same waiting report?',
            'Use one actual start and inspect pair to explain whether the original tools ran again.',
            question('Which fields show that the new process opened the same waiting task? How do you know that it did not run the original tools again?',
                'Cite different process IDs, matching thread and checkpoint, pending HumanApproval, and unchanged tool attempts and observations or execution trace.',
                'A new process ID alone does not show which saved task was opened.',
                'Compare identity, pending step and tool evidence across start and inspect.',
                'The process IDs differ while the thread, checkpoint and pending action match. Unchanged attempts and observations show the original execution did not run again.'),
            closing='A new process can use the same thread and database to recover the pending step.',
            slides=((31, 32, 33), ()), concepts=('thread',), target='resume',
            refs=(source('workflow/service.py', 'config', note='The configured thread_id lets the checkpointer find the history of a particular workflow.'),
                  source('workflow/service.py', 'resume_approval', note='Invoke the existing graph with the current config, the validated decision and synchronous durability. Return the invocation result.'),
                  source('workflow/service.py', 'start', note='Starting a new thread passes an initial state to invoke. Your resume call passes a decision to the existing interrupt.'),
                  source('workflow/service.py', 'session', note='Each process opens the same two local files. The checkpointer stores the graph state. The effect database holds the tickets.')),
            fields=('resume call check', 'start PID', 'inspect PID', 'thread ID', 'checkpoint ID', 'next', 'interrupts', 'tool attempts', 'observations', 'pending action')),
        task('t08', 'Run approval, rejection and invalid input', 12, 'Submit decisions bound to two different waiting tasks and read their actual outcomes.',
            list(INTERRUPT_MECHANISM.values()), list(INTERRUPT_MECHANISM.values()),
            ['Compare `status`, `ticket_count` and the trace for approval and rejection. For the malformed reply, read the error and compare the waiting checkpoint before and after it.',
             'Then read `interrupt_demo.before_pause` and `interrupt_demo.after_resume`. Compare `before_interrupt` and follow `events`: the line before the pause ran once on the way in and once on resume. The counter stands in for a write. The real approval node does not write a ticket; a later node, `ApplyAction`, does.',
             'Next you will see a different repeat: a crash leaves the writer pending after its ticket was already committed. That is where the saved request number protects the ticket table.'],
            'Predict the workflow status and ticket count after each of the three replies.',
            'Use the three saved records to explain how the workflow handled each reply.',
            question('Which output proves that each branch behaved as intended? Include the invalid input and the pending state after it.',
                'Cite the actual completed and rejected statuses and row counts, and the refusal with an unchanged waiting checkpoint.',
                'Look at status and the ticket rows for both terminal tasks.',
                'Inspect the interrupt after the malformed reply and compare it with the snapshot taken before it.',
                'Approval completed with one ticket. Rejection finished with no ticket. The invalid input was refused, and the interrupted task remained waiting with no new ticket.'),
            closing='Keep the approval wait free of ticket writes. A valid approval can then route to the separate writer.',
            slides=((28, 30, 32), (35,)),
            refs=(source('workflow/nodes.py', 'Nodes.human_approval', note='The interrupt gives the learner the pending action. After resuming, the submitted reply becomes the value returned by suspend.'),
                  source('workflow/service.py', 'decide', note='The service checks that HumanApproval is waiting and validates the reply before invoking resume.'),
                  source('workflow/routing.py', 'route_approval', note='Only an approved state with the Boolean true enters ApplyAction.')),
            fields=('interrupt_demo', 'invalid_reply', 'approval', 'rejection', 'ticket_count')),
        task('t09', 'Recover after the ticket write', 9, 'Verify that retrying a committed action creates no duplicate local ticket.',
            list(RECOVERY_MECHANISM.values()), list(RECOVERY_MECHANISM.values()),
            ['Compare the controlled fault, the inspection and the fresh continue result. Use the process IDs, pending step, action ID and ticket row count. Then check `reused` and the tool attempt count.',
             'For the separate collision example, read `payload_collision`. The hashes differ for one ID. Check the refusal and whether the saved row stayed the same.'],
            'Predict the pending step after the stop and the ticket count after recovery.',
            'Use the saved records to show whether the new process reused the original ticket.',
            question('How does the recovery output establish that the action was not duplicated after the controlled exception?',
                'Cite the pending step after the exception, distinct continuation process, same action ID and one row before and after recovery.',
                'One store records pending work and another holds the committed effect.',
                'Compare the existing ticket ID and row count before continue with the final result.',
                'The checkpoint still had ApplyAction pending while one row already existed. A separate process completed the same action ID, and the table still had one row.'),
            closing='Recovery reruns the pending node. The same action ID lets it reuse the existing ticket.',
            slides=((23, 24, 34), (35,)),
            refs=(source('workflow/nodes.py', 'Nodes.apply_action', 9, note='The SQLite write completes before the simulated exception. The node returns completed and an event only when it can finish.'),
                  source('workflow/effects.py', 'EffectStore.apply', 12, 7, note='The code looks up the logical action ID before inserting. A matching row can be reused. A conflicting payload for that ID is rejected.'),
                  source('workflow/effects.py', 'EffectStore.apply', 7, 17, note='An existing row with a different hash raises an error. The return value marks a matching existing row as reused.'),
                  source('workflow/service.py', 'continue_run', 9, note='Continue uses the same thread and passes no new task input. A waiting human interrupt must use decide instead.')),
            fields=('fault', 'after_fault', 'after_continue', 'payload_collision')),
        task('t10', 'Build an acceptance record', 5, 'Connect each completion claim to the actual saved evidence.',
            ['You have run five checks: reopen a waiting task, approve, reject, refuse invalid input, and recover after a ticket write. Each claim needs a row drawn from your saved outputs.'],
            ['Open your saved workflow results for reopening, approval, rejection, invalid input and recovery. Use those runs to fill the five rows.'],
            [], 'Fill the five rows from your runs. For each row, identify a thread, a state or next value, and a ticket count or evidence field.', '',
            question('Fill five rows from your saved runs. For each case, name the thread, observed status or next node, and the ticket count or other evidence. Which field helped you diagnose the invalid reply or the stop after the write?',
                'Ground all five rows in the learner’s actual saved records. Waiting needs a different process with the same checkpoint and no ticket. Approval needs completed with one ticket. Rejection needs rejected with zero. An invalid reply needs an error and the same waiting checkpoint. Recovery needs ApplyAction pending with one row, then completed with the same row. Connect one diagnostic field to its case.',
                'Compare a pending node, the refusal error or the effect row count.',
                'Pick one field and say what you expected and what the saved result showed.',
                'Reopening finds the same checkpoint in a new process with HumanApproval pending and no ticket. Approval completes with one ticket, and rejection ends with zero. The invalid reply raises an error and leaves the waiting checkpoint unchanged. After the controlled stop, ApplyAction is pending with one row already committed. Continue completes the same action and reuses that row.'),
            closing='Use the saved process, checkpoint and ticket records to show what the workflow actually did.',
            slides=((35, 36), ())),
    ]
    add_openings(tasks)
    set_delivery_order(tasks)
    lesson = dict(id='week05', version=7, title='State machines that pause, resume and avoid repeated actions',
        language='English', requires_api_key=False, source_deck=DECK,
        teaching_order=['problem', 'concept', 'actual code', 'prediction', 'learner attempt', 'test', 'explain output'],
        modes={'review': 'Follow the diagrams and code, then predict, run and explain the result.',
               'practice': 'Start from the problem, get a short explanation as needed, then predict, run and explain.'},
        mode_cards=[dict(id='review', label='Review lecture + code',
                         description='Walk through the actual lecture slides, trace the matching Python code, then run each experiment and build the CONV-3 workflow.'),
                    dict(id='practice', label='Start seminar practice',
                         description='Start the current task straight away. Choose a short concept explanation when you need it. Run the same experiments and recovery checks.')],
        mode_common_note='Both routes take two 50-minute sessions. The calculation experiments use the Python standard library. The workflow lab uses local LangGraph and SQLite. No API key or GPU is required.',
        foundations=FOUNDATIONS, code_targets=TARGETS, code_support=SUPPORT, tasks=tasks,
        presentation=dict(one_active_question=True, code_lines_per_excerpt=12, final_reply_required=True,
                          read_slide_before_code_in_review=True),
        progress_policy='Use the saved core_percent from the active Week 5 seminar session.',
        extensions=[])
    assert sum(t['minutes'] for t in tasks[:5]) == 50
    assert sum(t['minutes'] for t in tasks[5:]) == 50
    assert sum(t['weight'] for t in tasks) == 100
    (WEEK / 'lesson.json').write_text(json.dumps(lesson, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    guide(lesson)


def guide(lesson):
    from week03_flow import excerpt

    packs = {'seminar': WEEK / 'resources'}
    lines = ['# Week 5 teaching script', '',
             'Use the current installed OUTPUT.md, persona.md and MENTOR.md. '
             'Share the instructor’s note first, then read the travel story in order before introducing the terms. '
             'Keep the student-facing teaching and code in English except for the two exact bilingual Redo cues. '
             'Deliver both cues in the student reply in either mode. The music link is optional.', '',
             'Offer Review lecture + code and Start seminar practice. Give the current step, show the actual code '
             'in the reply, and wait for the learner to predict, write code or interpret a run. In Review use the '
             'listed v3 slide before the matching source excerpt if it is visible. Always explain the concept in '
             'complete English sentences so the learner can follow without the figure. In Practice start with the '
             'current problem. Both routes include the four-minute opening map before any source excerpt. '
             'Use the source windows returned by the current helper response. Extra excerpts are for questions.', '',
             'Use the three concept choices before the relevant exercise. Give two progressively clearer hints '
             'with real attempts between them, then offer more hints or an explanation. Ask for an own-words '
             'explanation before continuing after an answer has been explained.', '',
             'Read the actual result for the current run before explaining it or asking its interpretation. '
             'Save the evidence explanation and learner answer. Use the helper\'s saved core_percent. '
             'Questions, translations and revisits do not advance the current step.', '',
             'Use a verified Python environment. Run the Crash, Decide and Redo comparisons locally. In each '
             'comparison preserve the listed settings and change the designated strategy or policy. '
             'Use genuine LangGraph and SQLite for the workflow. Start, inspect and continue from separate '
             'processes. The seminar progress file tracks learning and is separate from the workflow checkpoint.', '',
             'In the first session a rule simulates planning so that everyone can repeat the experiment. '
             'In the second session the CONV-3 workflow runs the actual local graph and SQLite checkpointer.', '']
    for index, item in enumerate(lesson['tasks']):
        if index in {0, 5}:
            lines += [f'## Session {1 if index == 0 else 2} (50 minutes)', '']
        lines += [f"### {item['id']} {item['title']} ({item['minutes']} minutes)", '', item['purpose'], '']
        for mode in ('review', 'practice'):
            lines += [f'#### {mode.title()}', '']
            for node in item['paths'][mode]:
                lines += [f"**{node['title']}**", '']
                if node['slides']:
                    lines += ['Related lecture slides: ' + ', '.join(map(str, node['slides'])) + '.', '']
                lines += [node['explanation'], '']
                for index, ref in enumerate(node['code_refs']):
                    window = excerpt(ref, packs)
                    raw = '\n'.join(line.split(': ', 1)[1] for line in window['numbered_code'].splitlines())
                    if index not in node.get('primary_code_indices', []):
                        lines += ['Additional source on request.', '']
                    lines += [f"`{ref['file']}` · `{ref['symbol']}`", '', '```python', raw, '```', '']
                    if ref.get('note'):
                        lines += [ref['note'], '']
                for explanation in node.get('code_walkthrough', []):
                    lines += [explanation, '']
                if 'closing_line' in node:
                    lines += [node['closing_line'], '']
                lines += [node['one_next_action'], '']
        if item['code_target']:
            file, symbol = lesson['code_targets'][item['code_target']]
            lines += [f'After saving the prediction, ask the learner for the body of `{symbol}` in `{file}`.', '']
        if item['id'] in {'t08', 't09'}:
            lines += ['After saving the prediction, get the pending action from the actual t07 result and ask for '
                      'the learner’s explicit decision for the named thread. Prepare the decision file from the '
                      'learner reply. Follow the example in PRESENTATION.md.', '']
        lines += [item['questions'][0]['prompt'], '']
    (WEEK / 'TEACHING.md').write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    build()
