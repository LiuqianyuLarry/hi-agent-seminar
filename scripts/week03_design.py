"""Explicit teaching paths for the approved Week 3 revision. English learner content."""
import copy


def ref(pack, file, symbol, slice_start=0, max_lines=12):
    return dict(pack=pack, file=file, symbol=symbol, slice_start=slice_start, max_lines=max_lines)


def step(id, title, logic, explanation, example, refs=(), slides=()):
    return dict(id=id, title=title, logic=logic, explanation=explanation,
                worked_example=example, code_refs=list(refs), slides=list(slides))


def question(prompt, options, correct, feedback):
    return dict(id='q1', type='mcq', prompt=prompt, options=dict(zip('ABCD', options)), correct=correct, feedback=feedback)


OPENING=step('t01.monitoring','Why an engineering assistant needs tools',
    'Condition monitoring means using evidence to assess how equipment is operating. Engineers may compare sensor readings, maintenance history and registered specifications before deciding what to inspect next.',
    'These records are stored outside the language model. Today we build the tool-use part of a CONV-3 assistant: DeepSeek proposes a request; our application checks it, calls a function and returns evidence. Later we use MCP to connect a tool through a shared interface. This week permits one tool per turn. We are not yet building an autonomous multi-step diagnosis system.',
    'A registered reference of 85 C tells us the classroom reference limit, not the present sensor reading. A maintenance event tells us what was recorded, not what caused a later temperature change. The assistant must obtain the relevant records before discussing them.',
    slides=[2,3,4,7])

MCP_STEPS=[
 step('t08.mcp_need','Why not just call the Python function?',
    'For one small application with a few local functions, direct function calling can be enough. MCP is optional; adding it does not make a model smarter.',
    'Our local tool list is prepared in tool_definitions.py. A second application could reuse that Python package, but another language or process needs an agreed interface. MCP, the Model Context Protocol, standardizes messages for discovering and using capabilities. This can reduce separate connection code across applications. The function still performs the same narrow job.',
    'Keep the local route when it is the simplest fit. Consider MCP when a tool provider should be independently connected, discovered and reused by compatible applications. These are design benefits, not proof that every project needs MCP.',
    [ref('seminar','tool_definitions.py','model_tools')],[21,22,23,35]),
 step('t08.mcp_roles','Three roles, two different connections',
    'Function calling links the model to its application. MCP links an application client to a tool server. They describe different connections in the same workflow.',
    'The Host is the whole assistant application. Its Client speaks MCP to a Server that offers a function. In app.py, routes chooses either a local function or an MCPBackend. async with opens the connection for this block and closes it afterward. DeepSeek receives model API requests; it does not connect directly to the local server. A client can test the server with no model present.',
    'Student -> host -> DeepSeek proposal -> host validation -> MCP client -> server function -> result -> host -> DeepSeek explanation. On the local route, the middle client/server connection becomes an ordinary function call.',
    [ref('seminar','app.py','routes')],[24,27]),
 step('t08.mcp_process','Local messages and a deliberately limited environment',
    'A process is a running program. Our client starts a separate Python program for the server and exchanges messages through its input and output streams. This transport is called stdio.',
    'server_parameters selects the same Python interpreter and the server script. Its environment allowlist does not intentionally pass DEEPSEEK_API_KEY. The specification reader has no need for that key. This reduces unnecessary credential exposure, but a separate process under the same user is not an automatic file-permission sandbox. Keep stdout for protocol messages and send diagnostic logs to stderr. No HTTP port or GPU is required here.',
    'The model client needs the DeepSeek key; the local register-reading server does not. These responsibilities can be separated without claiming that MCP itself grants or enforces all permissions.',
    [ref('seminar','mcp_backend.py','server_parameters')],[28,34]),
 step('t08.mcp_discovery','Discover a tool before requesting its result',
    'A catalogue describes what can be requested. It is not the requested equipment data. Discovering tools does not execute all of them.',
    'Read the lecture client: list_tools asks for names, descriptions and argument schemas. call_tool names one function and supplies an argument dictionary. await means wait for that operation to finish before using its result. The known machine should return a structured record; an unknown machine should produce an explicit error. This independent check separates connection problems from model-selection problems.',
    'list_tools can tell us that get_machine_spec accepts machine_id. Only call_tool("get_machine_spec", {"machine_id":"CONV-3"}) asks the server to read CONV-3.',
    [ref('lecture','check_server.py','main')],[25,30]),
 step('t08.mcp_wrapper','Wrap the tested function instead of rewriting it',
    'The server is an interface around a function we already trust enough to test. Its wrapper should not create a second source of specification data.',
    'MCPServer creates the server object. @server.tool registers the following function; it does not run it immediately. The return annotation dict[str, Any] and structured_output=True request structured output. The alias read_spec refers to the existing reader, avoiding an accidental call back to the wrapper itself. Known business failures become ToolError rather than successful-looking text. Use the lecture implementation to understand the pattern, then complete the seminar wrapper yourself.',
    'A CONV-3 request reaches read_spec and returns its source and reference value. A nonexistent machine reaches the error path. Both paths tell the client what actually happened.',
    [ref('lecture','mcp_server.py','get_machine_spec',max_lines=12)],[29]),
 step('t08.mcp_results','Structured results and honest failure signals',
    'A string that looks like JSON is still text. A structured result lets the application inspect fields without guessing from a sentence.',
    'unpack_result first checks is_error. If it is true, the course raises a tool failure instead of treating the message as data. Next it requires a structured_content dictionary and validates our ToolResult envelope. status, data, source, version and error are this seminar\'s field names, not mandatory fields for every MCP server. The lecture uses an ok-based envelope, so do not interchange their keys.',
    'Connection failure, unsupported protocol/schema, tool failure and an incorrect final model answer are different problems. A correct structured tool result is evidence to check the answer against, not a guarantee that the answer is correct.',
    [ref('seminar','mcp_backend.py','unpack_result')],[17,33]),
 step('t08.mcp_bridge','Discovered metadata still needs an application decision',
    'The model does not automatically see every tool advertised by a server. The host decides which definitions to offer and which requests to allow.',
    'adapt_spec_tool accepts only our expected specification tool and simple machine_id schema. It rejects unsupported schema shapes instead of silently dropping constraints. It then forms the nested function definition used by DeepSeek. This is a deliberately narrow teaching adapter, not a universal schema converter. Local validation and permission checks remain in the executor after discovery.',
    'Function calling proposes the action; MCP carries the app-to-provider request. Comparing local and MCP routes should compare the actual offered definitions too: their descriptions or schema details may differ unless deliberately normalized.',
    [ref('seminar','mcp_backend.py','adapt_spec_tool',max_lines=9),ref('seminar','mcp_backend.py','adapt_spec_tool',slice_start=9,max_lines=6)],[31,34]),
 step('t08.mcp_resource','Reading a resource does not put it in model context',
    'A tool is invoked with arguments. A resource is content read through a resource interface. The difference is not simply whether data changes: our specification tool only reads.',
    'The lecture resource returns a short CONV-3 reference note. Reading that URI obtains content for the host. The host still has to select it and include it in a model request if it should affect the answer. That explicit selection is also why merely adding a resource is not a complete RAG system. We can now build and test the seminar wrapper before reconnecting DeepSeek.',
    'A resource can be present on a server while the model never receives it. A client-only resource test confirms retrieval, not a model explanation or an autonomous agent loop.',
    [ref('lecture','mcp_server.py','conv3_spec_note')],[26,32]),
]


def apply_design(lesson):
    lesson['version']=2
    lesson['mode_cards']=[
        {'id':'review','label':'Review lecture + code','description':'Revisit key slides, walk through the CONV-3 maintenance demo, then apply the ideas in the seminar exercises.'},
        {'id':'practice','label':'Start seminar practice','description':'Start the CONV-3 temperature-tool exercises. Learn the concepts and code needed for each task as you go.'},
    ]
    lesson['mode_common_note']='Both paths take two 50-minute sessions and include detailed code explanations, optional foundations, the full MCP lesson before practice, and the same core learning checks.'
    lesson['presentation']={'title_max_words':9,'code_lines_per_excerpt':12,'one_active_question':True,
        'concept_before_code':True,'choices':'Use real host choice cards whenever supported; never render fake buttons. Use an honest numbered fallback only if cards are unavailable.',
        'sequence':['short title','task and purpose when starting a task','one concept','one source excerpt','explain the relevant lines','one next action','exact progress footer'],
        'output_labels':['Observed result','Expected example','Scripted replay','Instructor walkthrough'],
        'avoid':['full-file dumps','duplicated question gates','internal rubric text','repeating the entire course plan','exposing helper JSON directly']}
    tasks={t['id']:t for t in lesson['tasks']}
    t=tasks['t01'];t.update(title='Why CONV-3 needs a tool-using assistant',purpose='Connect condition monitoring to the model-to-tool workflow.',logic=OPENING['logic']+' '+OPENING['explanation'])
    t['worked_answer']=OPENING['worked_example']+' The model proposes; the application checks and executes; tools return evidence for a checked explanation.'
    t['paths']={'review':[copy.deepcopy(OPENING),
        step('t01.review_no_tools','What the model receives without a tool',
            'Start with the lecture question about CONV-3\'s last maintenance. A question alone does not provide access to a local database.',
            'ask_no_tools sends system and user messages. Notice what is absent: there is no tools argument and no database-reading function call. The model may explain its limitation or produce an unsupported guess, but neither creates access. We need an explicit path from a proposed request to application code.',
            'The question "What was done at CONV-3\'s last maintenance?" requires a record lookup. A plausible answer is not evidence of that lookup.',
            [ref('lecture','live.py','ask_no_tools')],[3,7]),
        step('t01.review_roles','The application owns the connection',
            'Function calling is a structured way for a model to propose using a function. It is not Python execution inside model weights.',
            'The lecture registry maps permitted names to validation models and Python functions. The name is a key; the handler is callable code. This mapping belongs to the application. Later we will follow the checks before the handler is called. First verify the existing environment and classroom data without installing unrelated packages.',
            'query_maintenance is a name offered to the model and a registered Python handler. Both sides must agree on that name for dispatch to succeed.',
            [ref('lecture','registry.py','REGISTRY',max_lines=6)],[5,7,8])],
        'practice':[copy.deepcopy(OPENING),
        step('t01.practice_map','The three capabilities we will connect',
            'Our temperature assistant needs three narrow capabilities: summarise supplied values, read a registered reference, and query historical measurements.',
            'HANDLERS maps each public tool name to an existing Python function. The starter functions still contain TODOs. We will complete them and then test the application boundary around them. Setup first checks the chosen interpreter and builds synthetic data; it does not download a model or assume an API key is available.',
            'For a registered limit, use get_machine_spec. For measured temperatures, use query_temperature. For a supplied list, use temperature_stats.',
            [ref('seminar','executor.py','HANDLERS',max_lines=3)])]}

    t=tasks['t02'];t.update(title='Turn a calculation function into a callable tool',purpose='Connect a Python function to a model-visible interface and an application-controlled result.',
        logic='A useful Python function is not automatically available to a language model. We need a name and description, an argument contract, a real application binding, and a returned result the application can inspect.')
    t['questions']=[question('The calculation function exists on disk. Which step makes it usable in this tool-calling assistant?',
        ['Let the model guess the Python filename','Offer its name, description and parameter schema; let the application validate, dispatch and return its result','Print its source code and assume the model has executed it'],
        'B','The model sees the interface; the application runs the registered implementation and returns a result. A schema does not execute a function.')]
    t['hint1']='Separate what the model needs to know from what the application must actually run.'
    t['hint2']='Look for model_tools, StatsArgs validation, HANDLERS and success. Each has a different responsibility.'
    t['code_walkthrough']=[
        'Start with the model-visible name, description and parameters. The model sees this interface, not an executable Python body.',
        'Connect the offered name to HANDLERS and StatsArgs. Runtime validation checks actual arguments before the function computes.',
        'Complete the temperature summary from validated inputs and return the course success envelope so its caller can inspect named fields.',
        'Use empty and equal-to-reference samples as short implementation checks; the central learning question is how a function becomes a callable tool.']
    t['paths']={'review':[
        step('t02.review_function','Begin with the lecture calculator',
            'The lecture calculator has one narrow job: subtract two supplied Celsius values. It does not find a missing reference or read a sensor.',
            'Read the function signature first: two named arguments enter. GapArgs checks them. The body performs the calculation, and ok returns a dictionary containing data and source. Calling this Python function directly needs no language model. To let a model request it, we must describe the callable interface and connect it to a handler.',
            'For supplied values 97 and 85, the expected difference is 12 C. That result says nothing by itself about a fault cause.',
            [ref('lecture','tools.py','calculate_temperature_gap')],[5,16,17]),
        step('t02.review_contract','A tool description is not a function body',
            'The model must know which capability fits the question and what input fields it may supply.',
            'The first excerpt is an internal definition draft: name identifies the capability, description explains its job, properties names input fields, and required lists fields the caller must supply. Then inspect the final return line: it nests name, description and parameters under function for the DeepSeek request. Do not send the internal flat draft as though it were the final API object. No Python function body is sent as executable code.',
            'A request for repair history should select query_maintenance, not a calculator. Both may mention CONV-3, but their capabilities are different.',
            [ref('lecture','tool_definitions.py','model_tools',slice_start=4,max_lines=12),ref('lecture','tool_definitions.py','model_tools',slice_start=46,max_lines=1)],[9,10]),
        step('t02.interface','Apply the same pattern to temperature statistics',
            'The seminar calculation is different, but its tool interface follows the same pattern.',
            'ARG_TYPES connects a tool name to StatsArgs. model_json_schema converts that validation model into the parameter description offered to DeepSeek. At execution time StatsArgs validates actual values. Your function computes a small summary and returns success with the course envelope. The count rule uses >; treat that as one implementation detail, not the purpose of function calling.',
            'For the existing five readings, the expected summary includes mean_c=90.2, max_c=97 and above_fraction=0.8. The fraction describes samples, not duration. We still need the function, registry and runtime validation beyond these interface fields.',
            [ref('seminar','tool_definitions.py','model_tools')])],
        'practice':[
        step('t02.practice_interface','What the model sees and what Python runs',
            'Your task is to complete a calculation tool that the application can safely offer to DeepSeek.',
            'Read model_tools: it builds the model-visible name, description and parameters from ARG_TYPES. Then locate the temperature_stats starter. StatsArgs checks real arguments; success wraps the returned data with source and status. These are separate jobs. A function on disk is not callable by the model until the host offers and dispatches it.',
            'The model proposes temperature_stats with JSON arguments. The application checks those arguments and calls your function. Python computes the values, then the result returns to the model.',
            [ref('seminar','tool_definitions.py','model_tools')]),
        step('t02.practice_body','Write the small function behind the interface',
            'We already have the readings and reference. This function should calculate, not retrieve or invent inputs.',
            'Follow the validated args object. Count values, add them for the mean, select the maximum, and count values above the supplied reference. Return named fields inside success so the caller can inspect them. Explain return versus print if needed. Keep empty-list and equal-to-reference checks as short tests of the promised contract.',
            'The expected five-reading summary is count=5, mean_c=90.2 and above_fraction=0.8. This is an expected example until your saved function is actually tested.',
            [ref('seminar','tools/calculation.py','temperature_stats')]) ]}

    t=tasks['t03'];t['purpose']='Choose the right data tool and return its provenance through a clear interface.'
    t['questions']=[question('A user asks for CONV-3\'s current temperature. Should the assistant use only get_machine_spec?',
        ['Yes: any temperature number answers the question','No: that tool returns a registered reference, not a measured temperature','Yes: the model can rename the reference field to current_temperature'],
        'B','Match the tool capability to the question. A successful specification lookup does not provide a live measurement.')]
    spec_step=step('t03.interface','Return evidence with its source',
        'A registered reference and a measured temperature can both be numbers, but they answer different questions.',
        'The seminar reader has a fixed SPEC_PATH, so the model cannot choose an arbitrary file. SpecArgs validates the supplied ID. Parse the document, check whether the machine exists, and preserve its source and version when returning success. Unknown machine and unreadable source are different errors. The model needs these distinctions to explain the result honestly.',
        'CONV-3 has a classroom registered reference of 85 C. CONV-99 is format-valid but absent. Neither case tells us the present sensor value.',
        [ref('seminar','tools/engineering.py','get_machine_spec')])
    t['paths']={'review':[
        step('t03.review_spec','Read the lecture specification lookup',
            'The lecture uses a separate specification tool because maintenance history and reference limits have different meanings.',
            'The function validates machine_id, reads the fixed JSON register and selects the requested machine. If there is no entry, it raises a business error rather than inventing a default value. On success, the returned fields include the reference, version and source. Trace CONV-3 through those operations before moving to the seminar starter.',
            'A correct source and version make a result traceable. They do not turn a registered limit into a sensor measurement.',
            [ref('lecture','tools.py','get_machine_spec')],[16,17]),copy.deepcopy(spec_step)],'practice':[copy.deepcopy(spec_step)]}

    t=tasks['t04'];t['purpose']='Keep SQL under application control while allowing the model to supply validated query arguments.'
    t['questions']=[question('What should the model supply to the temperature-query tool?',
        ['Any SQL string it writes','A machine ID and start/end arguments; the application keeps the SQL template','A Python expression that the application evaluates'],
        'B','The model supplies constrained arguments. The application owns the query, binds values and reads the result.')]
    query_step=step('t04.interface','Keep the query fixed and bind the arguments',
        'The model should request a defined lookup, not invent arbitrary database commands.',
        'QueryArgs checks machine and timezone-aware start/end inputs. SQL contains question marks for values; binding parameters keeps the SQL structure fixed. mode=ro and query_only prevent writes in this classroom reader. The interval includes start and excludes end. More than 100 matching rows is reported as a limit error rather than a silently incomplete answer.',
        'The expected CONV-3 window returns five records. An empty successful query returns an empty list; a failed database access returns an error. The model must not turn either into a made-up temperature.',
        [ref('seminar','tools/sql_query.py','SQL',max_lines=7),ref('seminar','tools/sql_query.py','query_temperature')])
    t['paths']={'review':[
        step('t04.review_sql','The lecture model fills blanks, not SQL',
            'Maintenance retrieval shows how a narrow tool can expose useful database access without accepting arbitrary code.',
            'Read the fixed SELECT in query_maintenance. It selects known columns, filters machine_id, sorts newest first and limits the number of records. The model supplies machine_id and max_records through a validated contract. Parameter binding inserts their values without giving the caller control of the query structure. The application then turns returned rows into named fields.',
            'For CONV-3 with max_records=1, the teaching database\'s expected latest record is EV-104, replaced cooling fan. That is a recorded maintenance action, not a temperature measurement.',
            [ref('lecture','tools.py','query_maintenance',max_lines=12),ref('lecture','tools.py','query_maintenance',slice_start=12,max_lines=8)],[13,14,15]),copy.deepcopy(query_step)],'practice':[copy.deepcopy(query_step)]}

    t=tasks['t05'];t['paths']={'review':[
        step('t05.review_proposal','First call: a proposal, not execution',
            'The application sends a question and a list of available tools. DeepSeek may select a tool, ask for missing inputs, or answer without one.',
            'In first_call, tools attaches the definitions and tool_choice="auto" allows selection. message.tool_calls contains proposed requests. Each has an ID, function name and arguments string. Turning those fields into a slip is only parsing. No database function has been called yet. The one-call guard rejects multiple proposals in this week\'s bounded workflow.',
            'A call named query_maintenance with CONV-3 and max_records=1 tells the app what is requested. It is not itself the maintenance record.',
            [ref('lecture','live.py','first_call')],[11,12]),
        step('t05.review_dispatch','Only the application can dispatch the request',
            'A model-generated name is data until the application chooses an allowed implementation.',
            'run_tool looks up the name in REGISTRY. If no entry exists it returns UNKNOWN_TOOL. The registered argument model validates the JSON string. Only after those checks does handler(**args.model_dump()) call Python, using the validated fields as named arguments. A correct type or range still cannot prove that the model chose the machine the user intended.',
            'A nonexistent tool never runs. A valid CONV-7 request can run successfully and still fail a user request for CONV-3. Inspect intent separately from validation.',
            [ref('lecture','registry.py','run_tool',max_lines=12),ref('lecture','registry.py','run_tool',slice_start=12,max_lines=10)],[13,14,20]),
        step('t05.review_return','Return the result with the matching ID',
            'The model needs the real tool result to explain what happened. The request ID connects that result to the earlier call.',
            'complete_trip preserves the assistant call message, then appends a role="tool" message. tool_call_id matches the requested call; content contains serialized result data. The second model request uses tool_choice="none", so this turn ends with an explanation instead of another tool. Check the explanation against the recorded data: wording can be wrong even after correct execution.',
            'The completed chain is proposal -> validated Python call -> returned evidence -> checked explanation. Lecture ok/data/error and seminar status/data/source/version/error are different course envelopes.',
            [ref('lecture','live.py','complete_trip',slice_start=11,max_lines=12)],[17,18,37]),
        step('t05.transfer','Find the same responsibilities in the seminar',
            'The temperature assistant implements the same message sequence with different tool capabilities.',
            'Locate executor.execute, the assistant tool_calls message, the role="tool" result and the second request in run_turn. Match each line to its role in the lecture chain. The upcoming replay runs your tools but scripts the model choices and final text. It checks the application path without establishing live model reliability.',
            'The expected replay contains one tool execution and two scripted requests with a matching ID. Treat it as a plumbing check, then test real selection in t06.',
            [ref('seminar','workflow.py','run_turn',slice_start=32,max_lines=12)])],
        'practice':[
        step('t05.practice_proposal','Read the model-to-application boundary',
            'The first DeepSeek request asks what to do; it does not run a function.',
            'run_turn prepares model, tools and messages, then requests tool_choice="auto". The returned choices contain the assistant message and any tool_calls. Check completion before using a response. The app rejects multiple calls and malformed requests before invoking its executor. Explain JSON text versus a Python dictionary if needed.',
            'A function name and argument string are a request. A separate application action is required to obtain data.',
            [ref('seminar','workflow.py','run_turn',max_lines=9),ref('seminar','workflow.py','run_turn',slice_start=12,max_lines=12)]),
        step('t05.practice_dispatch','Validate and execute only registered code',
            'The application controls which functions run and which arguments reach them.',
            'Executor checks the name against handlers and ARG_TYPES, checks policy, parses JSON and validates the argument model. It then invokes a local handler or the selected MCP route. The returned envelope and data fields are validated too. These checks establish a contract, not whether a natural-language request was understood correctly.',
            'A wrong type is blocked before invocation. A valid wrong machine may pass; compare the arguments with the user\'s question.',
            [ref('seminar','executor.py','Executor.execute',slice_start=7,max_lines=12),ref('seminar','executor.py','Executor.execute',slice_start=24,max_lines=12)]),
        step('t05.practice_return','Send evidence back before asking for an answer',
            'A tool result must be connected to the call that requested it.',
            'The assistant message is kept, then the result is added with role="tool" and the matching tool_call_id. JSON content carries the actual course envelope. The second request uses tool_choice="none". The final answer is checked separately from the result, and tool failure cannot be rewritten as success. Replay has the same shape but scripted model behaviour.',
            'A successful replay is local workflow evidence. Live DeepSeek selection is a separate task.',
            [ref('seminar','workflow.py','run_turn',slice_start=32,max_lines=12)])]}

    common_live=step('t06.live_evidence','Separate a real model decision from a replay',
        'Now DeepSeek must choose among the three tools from the wording of each question.',
        'app.py selects ScriptedCompletions only when replay was explicitly requested. Live mode creates the DeepSeek client using a private key. Each data question can make up to two API requests, so these three cases have a six-request budget. Inspect chosen name, arguments, validation events, returned data and final answer. No silent fallback is allowed.',
        'The expected selections are spec -> get_machine_spec, query -> query_temperature, and stats -> temperature_stats. Record what actually happened, even if it differs.',
        [ref('seminar','app.py','execute',slice_start=4,max_lines=12)])
    tasks['t06']['paths']={'review':[copy.deepcopy(common_live)],'practice':[copy.deepcopy(common_live)]}

    failure=step('t07.failure_layers','Find the failed responsibility',
        'A fluent answer does not tell us whether selection, validation or execution was correct.',
        'The injected cases deliberately request a wrong type, unknown tool, reversed time window, execution exception and valid wrong machine. Follow each event\'s validation, permission, invoked and result fields. These are application tests, not naturally observed model errors. Then improve the specification description and compare a real baseline with the same question and a paraphrase.',
        'CONV-7 is the useful counterexample: validation can pass while intent fails. Better descriptions can help selection, but the before/after traces determine what the change actually achieved.',
        [ref('seminar','failure_demo.py','main',slice_start=1,max_lines=12)])
    tasks['t07']['paths']={'review':[
        step('t07.review_description','A description helps the model choose a capability',
            'Several tools can mention equipment and temperature. A vague description does not separate their jobs.',
            'Compare the lecture DESCRIPTIONS. query_maintenance states that it reads service history; get_machine_spec names registered limits; the calculator requires supplied values. The exclusions matter because they prevent a plausible but irrelevant selection. The application still validates inputs and checks evidence after selection.',
            'A request for maintenance history should not be satisfied with the specification merely because both tools accept machine_id.',
            [ref('lecture','tool_definitions.py','DESCRIPTIONS',max_lines=12)],[10,19,20]),copy.deepcopy(failure)],'practice':[copy.deepcopy(failure)]}

    tasks['t08']['paths']={'review':copy.deepcopy(MCP_STEPS),'practice':copy.deepcopy(MCP_STEPS)}
    tasks['t08']['code_walkthrough'][1]='MCPServer creates the server; @server.tool(structured_output=True) and dict[str, Any] declare a structured tool result. The decorator registers, rather than immediately runs, the function.'
    tasks['t08']['worked_answer']='Direct function calling is enough for a small local app. MCP offers a shared app-to-provider interface for discovery and execution. The host owns its client and permissions; DeepSeek still proposes via function calling. Separate processes and environment filtering do not automatically sandbox file permissions. Validate the real client/server result before connecting the model.'

    bridge=step('t09.offered_definitions','Check the interface before comparing routes',
        'A fair comparison changes the tool connection while keeping the requested business capability clear.',
        'Read routes: the MCP backend returns a callable and a discovered definition. execute replaces the local get_machine_spec definition before sending tools to DeepSeek. The other tools stay local. The trace saves tool_definitions, the actual list offered to the model. The task also saves tool_interfaces.json with local_definition_now, mcp_definition_sent and comparison flags. Check the local snapshot against the earlier local trace if its description has since been edited. Compare names, descriptions and parameter schemas; do not claim identical model input without checking.',
        'Different transport does not imply different intelligence. A changed description can affect selection, so record it when interpreting the comparison.',
        [ref('seminar','app.py','execute',slice_start=19,max_lines=7)],[31])
    comparison=step('t09.trace_route','Follow the result through the new connection',
        'MCP should change how the application reaches the specification function, not the meaning of its result.',
        'Executor selects remote_spec for the registered specification tool when that route is configured. MCPBackend.call_spec checks the ID, calls the server and validates the structured result. Inspect events.route, source, version and machine_id beside the previous local trace. A connection error must remain an error; it must not silently run a local substitute.',
        'For the same CONV-3 reference request, compare the observed business data and final explanation. The real trace, not the route name alone, establishes what ran.',
        [ref('seminar','mcp_backend.py','MCPBackend.call_spec')],[33,34,37])
    tasks['t09']['paths']={'review':[copy.deepcopy(bridge),copy.deepcopy(comparison)],'practice':[copy.deepcopy(bridge),copy.deepcopy(comparison)]}
    tasks['t09']['logic']='Use the same CONV-3 specification question on local and MCP routes. Compare the offered definitions as well as the execution route; do not assume their descriptions and schemas are identical.'
    tasks['t09']['questions'][0]['rubric']='Reference the actual route, source and result. Explain that function calling still proposes the tool while MCP changes the app-to-tool connection. Compare offered definitions instead of asserting identical model input.'
    recap=step('t10.recap','Explain the chain in your own words',
        'The main achievement is connecting a model proposal to inspected engineering evidence.',
        'Use one saved trace to tell the story: the host offers definitions, the model proposes a call, the application validates and dispatches it, a function returns data, and the model explains it. Locate MCP in that story if the remote route was used. Name one check that a schema cannot perform. Save a short next-learning goal, then choose whether to revisit a task or explore an optional topic.',
        'A valid response about the wrong machine is still the wrong answer. MCP standardizes a connection; it does not replace intent checks, permissions or result review.',slides=[37,38,39,40])
    tasks['t10']['paths']={'review':[copy.deepcopy(recap)],'practice':[copy.deepcopy(recap)]}
    for t in lesson['tasks']:
        t['output_fields']='Inspect the actual report: distinguish tool-call arguments, execution events, tool envelope and final model explanation. Label expected examples and scripted replay explicitly.'
        for mode,path in t['paths'].items():
            assert path and len({s['id'] for s in path})==len(path)
            for s in path:
                assert s['logic'] and s['explanation'] and s['worked_example']
                assert all(1<=r['max_lines']<=12 for r in s['code_refs'])
    from week03_slides import apply_slide_review
    return apply_slide_review(lesson)
