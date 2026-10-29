"""PPT-first review cards grounded in the supplied Week 3 lecture deck.

Slide numbers refer to presentation order, not the slide XML filename. The
original deck is a reading source; these cards do not alter it or claim that its
older API snippets match the current DeepSeek teaching implementation.
"""
import copy


DECK = 'EEEE4149_Week3_Lecture_Tools_FunctionCalling_MCP_v3.pptx'


def slide_step(id, title, number, slide_title, focus, walkthrough, explanation,
               example, bridge, related=(), provider_note=None):
    review = {
        'source_deck': DECK,
        'primary_slide': number,
        'title': slide_title,
        'image': f'slides/slide-{number:02d}.png',
        'related_slides': [{'number': n, 'title': label} for n, label in related],
        'focus': focus,
        'visual_walkthrough': list(walkthrough),
        'explanation': explanation,
        'example': example,
        'code_bridge': bridge,
    }
    if provider_note:
        review['provider_note'] = provider_note
    return {
        'id': id, 'title': title, 'phase': 'slide',
        'logic': focus, 'explanation': explanation,
        'worked_example': example, 'code_refs': [],
        'slides': [number, *[n for n, _ in related]], 'slide_review': review,
        'presentation': 'Show the original slide image first. Explain the visible idea in plain English, trace the example, and only then introduce the named code bridge. Do not begin this step with a source file.',
    }


SLIDE_STEPS = {
    't01': [
        slide_step('t01.slide_access', 'The missing connection in the lecture', 2,
            'A new request exposes a missing data connection',
            'A model can discuss the question without being able to retrieve the record needed to answer it.',
            [
                'Start at the request about CONV-3\'s last maintenance. Ask what evidence a planner would need: a dated record of work performed.',
                'Follow the existing connection from ASSISTANT APP to LLM SERVICE. It carries text and model replies.',
                'Now point at the MAINTENANCE DB and the label no path. The missing connection is between our program and that data source.',
                'Use the contrast with the earlier weeks: reliable output and faster computation help only after the required information reaches the program.',
            ],
            'Condition monitoring means checking how equipment is operating using available evidence. An engineer may consult measurements, maintenance history and registered specifications. The lecture starts with one manageable part: finding a maintenance record. Think of an assistant who can write clearly but has not been given the filing-cabinet key. Better wording cannot open that cabinet. Our application must provide a controlled way to request and read the record.',
            'CONV-3 is an equipment identifier, not its maintenance history. If the question supplies only that identifier, a statement such as "the fan was replaced" needs a lookup or supplied evidence. A confident sentence alone is not proof that either happened.',
            'Next inspect lecture live.py::ask_no_tools. Identify the text sent to the model and confirm that this first example offers no database-reading tool.',
            related=[(3, 'The model cannot return records it never received')]),
        slide_step('t01.slide_roles', 'Who owns each arrow?', 7,
            'The model proposes; the program checks and executes',
            'The model, the application and the tools have different jobs. The application owns execution.',
            [
                'Name the three lanes before following arrows: LLM SERVICE, YOUR PYTHON APP, and TOOLS & DATA.',
                'Follow OFFER and PROPOSE: the app supplies a menu of capabilities; the model returns a request naming one capability and its inputs.',
                'Pause at CHECK & RUN in the middle lane. This is where the app validates the request and invokes the allowed function.',
                'Follow RETURN and ANSWER: the result goes back to the model, which turns it into an explanation that still needs checking.',
            ],
            'Function calling gives a model a structured way to ask the application to use a function. It does not give the model Python execution inside its weights. Imagine a request slip at a service desk: writing the requested action is different from checking and carrying it out. Our program accepts only the tools it has registered. In this week, one turn permits at most one tool execution; a chain of dependent calls is a later topic.',
            'For "CONV-3\'s latest service", the model can propose query_maintenance with machine_id="CONV-3" and max_records=1. Only the application can check those values, run the lookup and return the record.',
            'After the no-tool example, inspect lecture registry.py::REGISTRY. Match the permitted tool names on the slide to real Python functions. This is the application-controlled bridge to execution.'),
    ],
    't02': [
        slide_step('t02.slide_contract', 'Read the tool form before the function', 9,
            'The schema: the contract attached to message 1',
            'A tool definition is a form the model can fill in. The form describes a capability; it does not perform it.',
            [
                'Locate name, description and parameters. Read them as the service name, the job it offers, and the inputs a request must provide.',
                'Within parameters, point to properties and required. They describe the named blanks and which blanks may not be omitted.',
                'Point to max_records and its bounds. A request can use an integer within the accepted range; a persuasive sentence cannot remove that limit.',
                'Use the description examples on slide 10 to separate maintenance history, registered specifications and live measurements. A precise menu helps selection; validation remains a separate job.',
            ],
            'A schema is a description of an allowed data structure. Validation means checking one actual request against that description. A function is the code that does the work after those checks. These three ideas are related but not interchangeable. The model needs a clear name, useful description and parameter rules. The application also needs the real function, a registered binding and runtime checks. A returned result then gives the application evidence to inspect.',
            'For the supplied values 97 C and 85 C, the calculator can return a difference of 12 C. The name and schema tell the model how to request that calculation; they do not calculate 12. The seminar follows the same pattern for a temperature-summary function.',
            'Read lecture tools.py::calculate_temperature_gap, then tool_definitions.py::model_tools. Separate the implementation from its offered interface. Finally locate the seminar StatsArgs validation model and its generated JSON schema.',
            related=[(10, 'The description decides whether this tool gets chosen')],
            provider_note='This slide shows a Responses-style tool entry with strict=true. The current course code uses DeepSeek Chat Completions and nests name, description and parameters under function. Do not copy the slide entry as a runnable DeepSeek request or assume its strict flag is supported here; local validation remains required.'),
    ],
    't03': [
        slide_step('t03.slide_evidence', 'A reference value is not a sensor reading', 16,
            'The calculator gets its inputs from a separate tool',
            'The meaning and source of a number matter as much as its numeric value.',
            [
                'Read the temperature scale: 85 is the registered reference and 97 is the supplied reading. The marked gap is the calculated difference, 12 C.',
                'Move to the specification result. machine_id identifies the equipment; temperature_limit_c names what the number means; spec_version and source identify where it came from.',
                'Point to the unknown-machine case. The lookup reports that no record is available instead of assuming every machine has the same reference.',
                'Connect to the result envelope on slide 17: status, data and provenance allow an answer to be checked against a concrete returned record.',
            ],
            'A registered specification is a filed reference, like a value in a machine handbook. A sensor reading is an observation at a time. A calculation is a new value obtained from supplied inputs. The fact that all three may contain temperature numbers does not make them interchangeable. Keeping the lookup and calculator separate also makes each function easier to test and prevents the calculator from inventing missing inputs.',
            'get_machine_spec("CONV-3") can establish the classroom registered limit of 85 C and its source. It cannot establish CONV-3\'s current measured temperature. For CONV-99, an explicit missing-record error is more informative than an invented 85 C.',
            'Trace lecture tools.py::get_machine_spec from the fixed register to its selected entry and return value, then complete the seminar reader while preserving source and version.',
            related=[(17, 'Every tool result carries its data and its provenance')],
            provider_note='The lecture uses an ok/data/error envelope, while the seminar uses status/data/source/version/error. These are course conventions, not universal MCP or Function Calling fields. Explain the actual keys in each code pack. Fetching a missing specification and then calculating requires separate calls; this week does not automate that chain.'),
    ],
    't04': [
        slide_step('t04.slide_query', 'Use the table to explain the lookup', 15,
            'The model fills two blanks; the SQL stays ours',
            'The model supplies bounded values to a defined lookup. The application keeps control of the query itself.',
            [
                'Read the table before the SQL: each row is one service record with a machine, date and action.',
                'For CONV-3\'s last service, first keep only CONV-3 rows. The newer CONV-7 row is irrelevant to this question.',
                'Then order the remaining dates newest first and keep one row. This gives EV-104, dated 2026-03-18, with the recorded cooling-fan replacement.',
                'Now match those operations to WHERE, ORDER BY and LIMIT. The two question marks are value slots, not places for arbitrary SQL commands.',
            ],
            'A query is a request for selected rows from a table. The developer writes the query structure, while the caller supplies only the allowed values. Binding means sending those values separately from the SQL text so they are treated as data. Before execution, argument checks reject invalid types or excessive limits; the registry chooses the allowed function. A read-only connection provides another concrete restriction. None of these checks alone can prove that the requested machine matches the user\'s intent.',
            'With machine_id="CONV-3" and max_records=1, the maintenance lookup selects CONV-3\'s latest stored service, not the newest service anywhere in the table. The seminar transfers this idea to a machine ID and a temperature time window; its query remains fixed as well.',
            'Read lecture tools.py::query_maintenance and match the table operations to its fixed SELECT and bound values. Then inspect the seminar SQL and QueryArgs before writing the temperature reader.',
            related=[(13, 'Arguments must pass three gates: type, range, intent'),
                     (14, 'Only functions the app registered can ever execute')]),
    ],
    't05': [
        slide_step('t05.slide_messages', 'Follow the request slip and its receipt', 8,
            'A function call is three messages and one shared id',
            'The returned result must be linked to the exact request that caused it.',
            [
                'Start at message 1: the application sends a task and a catalogue of tools. The model does not discover arbitrary Python files.',
                'Read message 2 as a call slip: a name, arguments and an identifier. It contains the requested inputs, not a retrieved maintenance record.',
                'Pause at the small validation, registry and execution box between messages 2 and 3. This work belongs to the application even though it is drawn between two model messages.',
                'Match the identifier in message 3 to the call slip, then follow the final plain-text answer. Use slide 18 to reinforce that the real result is sent back before asking for that answer.',
            ],
            'The request identifier works like a receipt number. The application keeps the model\'s original request and attaches the result to that same request. Otherwise a model could receive a number without a reliable connection to the operation that produced it. The final answer is another generated message, so we compare it with the returned evidence rather than trusting its tone.',
            'If one slip requests CONV-3 maintenance, its paired result should contain that lookup\'s record. A result for another machine does not become correct merely because the JSON is well formed or the request identifier matches.',
            'Trace lecture first_call, run_tool and complete_trip in that order. In the seminar, find the same responsibilities in run_turn and Executor.execute.',
            related=[(18, 'Results return to the model, matched by call_id')],
            provider_note='Slides 8 and 18 illustrate Responses-style call_id and function_call_output. Current DeepSeek Chat Completions uses message.tool_calls entries with id, followed by a role="tool" message with the matching tool_call_id. Teach the shared pairing idea, then use the actual current syntax.'),
    ],
    't07': [
        slide_step('t07.slide_success', 'A successful function can answer the wrong question', 20,
            'The call succeeded perfectly — on the wrong machine',
            'Execution success and task success are separate judgments.',
            [
                'Compare the two machine labels: the request is for CONV-3 but the lookup targets CONV-7.',
                'Read the two scores separately. FUNCTION executed means the call ran; TASK remains unverified until its arguments and result are compared with the request.',
                'Identify what the existing checks could establish: the ID had an acceptable form, the tool existed and the function returned a result.',
                'Name what is still missing: evidence that this was the machine and information the user actually asked for.',
            ],
            'A schema checks an input\'s structure and allowed values; it cannot infer every detail of a user\'s intended task. This is why an assistant needs checks at several points: useful descriptions before selection, validation before execution, and a comparison between request, trace and answer afterward. A better description can reduce mistakes, but the actual traces show whether it helped.',
            'A correct CONV-7 specification is still an incorrect response to a CONV-3 specification question. In contrast, a wrong argument type should be stopped before the handler runs. These failures occur at different places in the chain.',
            'Compare lecture tool descriptions, then inspect the seminar failure_demo events. Identify the first failed responsibility before editing one description and testing the real before/after evidence.',
            related=[(19, 'Zero rows, a failed query, a refusal — three answers')]),
    ],
    't09': [
        slide_step('t09.slide_bridge', 'Discovery is followed by an application decision', 31,
            'A discovered tool is not yet visible to the model',
            'The application decides what reaches the model and where an accepted request is routed.',
            [
                'Follow the five numbered actions: fetch the catalogue, filter it, convert allowed definitions, receive a model request, then route it to the right client.',
                'Use the mapping table to connect name and description directly, and inputSchema to the model API\'s parameters field.',
                'Notice that the owning server is kept inside the application for routing. It is not a magic instruction that lets the model connect itself.',
                'Read the route table: the specification tool can use an MCP client while the maintenance lookup remains a local function.',
            ],
            'MCP discovery gives the host information about capabilities. The host still chooses which capabilities to offer to the model and how to adapt their schemas. Once the model proposes a request through Function Calling, the host checks it and uses its route table to reach the right implementation. This keeps responsibility in the application and allows local and MCP tools to work together.',
            'Offering get_machine_spec through MCP can preserve its business purpose while changing its connection. Its discovered description or schema may differ from the local definition. We must inspect the actual offered interfaces before interpreting the comparison.',
            'Inspect app.py::execute where the discovered definition replaces the local specification entry, then follow MCPBackend.call_spec. Compare the saved tool_interfaces.json and actual traces.',
            provider_note='The slide gives conceptual field mapping. The current adapter builds a nested DeepSeek function object and rejects unsupported schema shapes; it is not a universal converter.'),
    ],
    't10': [
        slide_step('t10.slide_trace', 'Read the evidence chain back to front', 37,
            'The answer now traces back to the record it came from',
            'A useful engineering answer lets us trace each claim to a result and the request that produced it.',
            [
                'Start with the quoted answer about the cooling fan. Locate its record ID, service date and named source.',
                'Move backward through the trace table: returned record, execution site, validation, model choice and original user request.',
                'Check that every row refers to the same machine and purpose. A broken link tells us what must be investigated.',
                'Read the scope note: latest in the teaching database is a narrower claim than latest in a real plant. Then use slide 38 to identify the missing loop for a multi-call request.',
            ],
            'Traceability means being able to follow a claim back to the evidence that supports it. It is not the same as a long log: the important links must agree. Our course uses synthetic records, so our conclusions inherit that scope. Function Calling and MCP make particular operations possible; they do not prove a complete diagnosis or plan and execute an unlimited sequence of actions.',
            'The slide\'s example points to EV-104 and the recorded cooling-fan replacement in teaching_db_v1. For your own work, use a result from your actual saved run, name its source and explain one check that could still fail.',
            'Return to the saved seminar trace and your own functions. Explain the full request path, then state one next learning goal. A multi-step dependency belongs to the Week 4 loop.',
            related=[(38, 'Multi-step tasks need the Agent Loop of Week 4')]),
    ],
}


def apply_slide_review(lesson):
    """Add genuine slide teaching before source inspection, within existing times."""
    lesson['version'] = 3
    tasks = {task['id']: task for task in lesson['tasks']}
    for task_id, introductions in SLIDE_STEPS.items():
        task = tasks[task_id]
        path = task['paths']['review']
        if task_id == 't01':
            # The dedicated slide opening now performs the old overview's job.
            path = [node for node in path if node['id'] != 't01.monitoring']
        for node in path:
            node['phase'] = 'code' if node.get('code_refs') else 'application'
        if task_id=='t01':
            task['paths']['review']=[copy.deepcopy(introductions[0]),path[0],copy.deepcopy(introductions[1]),path[1]]
        else:task['paths']['review'] = copy.deepcopy(introductions) + path
    # This is a subdivision of each existing task budget, not extra lecture time.
    for task_id, split in {
        't01': (3, 2, 5), 't02': (3, 3, 4), 't03': (2, 2, 4),
        't04': (3, 3, 6), 't05': (3, 3, 4), 't07': (2, 2, 4),
        't09': (1, 1, 3), 't10': (1, 0, 2),
    }.items():
        task = tasks[task_id]
        assert sum(split) == task['minutes']
        task['review_time_plan'] = dict(zip(
            ['slides_and_concepts', 'code_explanation', 'practice_and_checks'], split))
    tasks['t01']['code_walkthrough'] = [
        'In Review, show slide 2 and explain the missing database path, then slide 7 and the responsibilities of model, application and tools.',
        'Connect those ideas to lecture ask_no_tools and REGISTRY. In Practice, start with the temperature-tool map and explain the needed concepts.',
        'Environment preflight and synthetic data building are setup actions after the task and purpose have been explained; they are not the PPT review.',
    ]
    for task_id, primary, bridge in [
        ('t02', 9, 'Separate the calculator body, its offered definition, runtime validation and returned result.'),
        ('t03', 16, 'Trace the fixed specification reader and preserve its source and version.'),
        ('t04', 15, 'Match filtering, sorting and row limits to the fixed query before transferring to temperature data.'),
    ]:
        tasks[task_id]['code_walkthrough'].insert(0,
            f'In Review, first explain the actual concept and visual on slide {primary}; then connect it to code. In Practice, introduce the concept at the exercise. {bridge}')
    lesson['mode_cards'][0]['description'] = 'Look back at the actual PPT slides, explain their diagrams and examples in plain English, then walk through the matching lecture code and apply it in the seminar.'
    lesson['slide_source'] = {
        'file': DECK,
        'numbering': 'Presentation order, starting at 1.',
        'primary_slides': [2, 7, 9, 16, 15, 8, 20, 31, 37],
        'note': 'Original slide excerpts support review. Current DeepSeek API and MCP code are the runnable implementation; provider/version differences are explained at the relevant bridge.',
    }
    return lesson
