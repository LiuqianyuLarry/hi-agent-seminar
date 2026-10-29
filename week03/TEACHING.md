# Week 3 teaching script

Both modes contain 2 x 50 minutes of core learning and use logic then detailed code. No required mathematics segment. Explain one concept and a 5-12-line excerpt at a time: inputs, variables, branches, return values and why each check exists. Never just read code aloud.
Use the selected path below. Review first shows and explains the actual PPT page, its diagram and a concrete example, then connects the idea to lecture code and seminar practice. Practice starts from the seminar task and teaches its necessary concepts. Both include the complete MCP introduction with four short checks between explanations.
Offer foundations: I understand - continue / Explain briefly / Show an example. Record the choice. MCP_GUIDE.md is required in BOTH modes before task t08 practice.
Use one question at a time. Give two gradual hints with attempts between. If still stuck, ask whether to continue hints or explain the answer. After an explanation, require the learner's own words before continuing. Save that actual answer, not the model answer.
Use a compact title, short paragraphs, a fenced code excerpt and one next action. Use real choice cards when supported; otherwise show numbered choices. Keep helper JSON, instructor rubrics and long command listings out of learner messages.
Every message ends with the exact saved core percentage. Pause does not change progress. Explain task and purpose before execution; inspect actual results before explaining the schema. Label output as Expected example, Scripted replay or Observed result, as appropriate.

## Choose your learning mode

- **Review lecture + code**: Look back at the actual PPT slides, explain their diagrams and examples in plain English, then walk through the matching lecture code and apply it in the seminar.
- **Start seminar practice**: Start the CONV-3 temperature-tool exercises. Learn the concepts and code needed for each task as you go.

Both paths take two 50-minute sessions and include detailed code explanations, optional foundations, the full MCP lesson before practice, and the same core learning checks.

## t01 - Why CONV-3 needs a tool-using assistant

Purpose: Connect condition monitoring to the model-to-tool workflow.

Core time: review 10 minutes; practice 5 minutes.

### Review path

#### t01.slide_access - The missing connection in the lecture

Logic: A model can discuss the question without being able to retrieve the record needed to answer it.

Explanation: Condition monitoring means checking how equipment is operating using available evidence. An engineer may consult measurements, maintenance history and registered specifications. The lecture starts with one manageable part: finding a maintenance record. Think of an assistant who can write clearly but has not been given the filing-cabinet key. Better wording cannot open that cabinet. Our application must provide a controlled way to request and read the record.

PPT page 2: A new request exposes a missing data connection
Show the original image: slides/slide-02.png

Guide attention through the slide:
- Start at the request about CONV-3's last maintenance. Ask what evidence a planner would need: a dated record of work performed.
- Follow the existing connection from ASSISTANT APP to LLM SERVICE. It carries text and model replies.
- Now point at the MAINTENANCE DB and the label no path. The missing connection is between our program and that data source.
- Use the contrast with the earlier weeks: reliable output and faster computation help only after the required information reaches the program.

Plain-language explanation: Condition monitoring means checking how equipment is operating using available evidence. An engineer may consult measurements, maintenance history and registered specifications. The lecture starts with one manageable part: finding a maintenance record. Think of an assistant who can write clearly but has not been given the filing-cabinet key. Better wording cannot open that cabinet. Our application must provide a controlled way to request and read the record.
Concrete example: CONV-3 is an equipment identifier, not its maintenance history. If the question supplies only that identifier, a statement such as "the fan was replaced" needs a lookup or supplied evidence. A confident sentence alone is not proof that either happened.
Bridge to code: Next inspect lecture live.py::ask_no_tools. Identify the text sent to the model and confirm that this first example offers no database-reading tool.


#### t01.review_no_tools - What the model receives without a tool

Logic: Start with the lecture question about CONV-3's last maintenance. A question alone does not provide access to a local database.

Explanation: ask_no_tools sends system and user messages. Notice what is absent: there is no tools argument and no database-reading function call. The model may explain its limitation or produce an unsupported guess, but neither creates access. We need an explicit path from a proposed request to application code.

- Read lecture/live.py -> ask_no_tools; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

#### t01.slide_roles - Who owns each arrow?

Logic: The model, the application and the tools have different jobs. The application owns execution.

Explanation: Function calling gives a model a structured way to ask the application to use a function. It does not give the model Python execution inside its weights. Imagine a request slip at a service desk: writing the requested action is different from checking and carrying it out. Our program accepts only the tools it has registered. In this week, one turn permits at most one tool execution; a chain of dependent calls is a later topic.

PPT page 7: The model proposes; the program checks and executes
Show the original image: slides/slide-07.png

Guide attention through the slide:
- Name the three lanes before following arrows: LLM SERVICE, YOUR PYTHON APP, and TOOLS & DATA.
- Follow OFFER and PROPOSE: the app supplies a menu of capabilities; the model returns a request naming one capability and its inputs.
- Pause at CHECK & RUN in the middle lane. This is where the app validates the request and invokes the allowed function.
- Follow RETURN and ANSWER: the result goes back to the model, which turns it into an explanation that still needs checking.

Plain-language explanation: Function calling gives a model a structured way to ask the application to use a function. It does not give the model Python execution inside its weights. Imagine a request slip at a service desk: writing the requested action is different from checking and carrying it out. Our program accepts only the tools it has registered. In this week, one turn permits at most one tool execution; a chain of dependent calls is a later topic.
Concrete example: For "CONV-3's latest service", the model can propose query_maintenance with machine_id="CONV-3" and max_records=1. Only the application can check those values, run the lookup and return the record.
Bridge to code: After the no-tool example, inspect lecture registry.py::REGISTRY. Match the permitted tool names on the slide to real Python functions. This is the application-controlled bridge to execution.


#### t01.review_roles - The application owns the connection

Logic: Function calling is a structured way for a model to propose using a function. It is not Python execution inside model weights.

Explanation: The lecture registry maps permitted names to validation models and Python functions. The name is a key; the handler is callable code. This mapping belongs to the application. Later we will follow the checks before the handler is called. First verify the existing environment and classroom data without installing unrelated packages.

- Read lecture/registry.py -> REGISTRY; start at symbol offset 0, show at most 6 lines. Resolve current source lines; do not invent line numbers.

### Practice path

#### t01.monitoring - Why an engineering assistant needs tools

Logic: Condition monitoring means using evidence to assess how equipment is operating. Engineers may compare sensor readings, maintenance history and registered specifications before deciding what to inspect next.

Explanation: These records are stored outside the language model. Today we build the tool-use part of a CONV-3 assistant: DeepSeek proposes a request; our application checks it, calls a function and returns evidence. Later we use MCP to connect a tool through a shared interface. This week permits one tool per turn. We are not yet building an autonomous multi-step diagnosis system.


#### t01.practice_map - The three capabilities we will connect

Logic: Our temperature assistant needs three narrow capabilities: summarise supplied values, read a registered reference, and query historical measurements.

Explanation: HANDLERS maps each public tool name to an existing Python function. The starter functions still contain TODOs. We will complete them and then test the application boundary around them. Setup first checks the chosen interpreter and builds synthetic data; it does not download a model or assume an API key is available.

- Read seminar/executor.py -> HANDLERS; start at symbol offset 0, show at most 3 lines. Resolve current source lines; do not invent line numbers.

### Exercise, run and check

Before execution: explain the task and purpose, then ask what the learner expects. Save student code from chat. Obtain approval for live requests within the stated limit.
After execution: open the current run report, distinguish expected values from observed results, explain fields and errors, then ask each understanding question separately.
If an answer has been shown, ask: "Please explain that in your own words before we continue."

## t02 - Turn a calculation function into a callable tool

Purpose: Connect a Python function to a model-visible interface and an application-controlled result.

Core time: review 10 minutes; practice 12 minutes.

### Review path

#### t02.slide_contract - Read the tool form before the function

Logic: A tool definition is a form the model can fill in. The form describes a capability; it does not perform it.

Explanation: A schema is a description of an allowed data structure. Validation means checking one actual request against that description. A function is the code that does the work after those checks. These three ideas are related but not interchangeable. The model needs a clear name, useful description and parameter rules. The application also needs the real function, a registered binding and runtime checks. A returned result then gives the application evidence to inspect.

PPT page 9: The schema: the contract attached to message 1
Show the original image: slides/slide-09.png

Guide attention through the slide:
- Locate name, description and parameters. Read them as the service name, the job it offers, and the inputs a request must provide.
- Within parameters, point to properties and required. They describe the named blanks and which blanks may not be omitted.
- Point to max_records and its bounds. A request can use an integer within the accepted range; a persuasive sentence cannot remove that limit.
- Use the description examples on slide 10 to separate maintenance history, registered specifications and live measurements. A precise menu helps selection; validation remains a separate job.

Plain-language explanation: A schema is a description of an allowed data structure. Validation means checking one actual request against that description. A function is the code that does the work after those checks. These three ideas are related but not interchangeable. The model needs a clear name, useful description and parameter rules. The application also needs the real function, a registered binding and runtime checks. A returned result then gives the application evidence to inspect.
Concrete example: For the supplied values 97 C and 85 C, the calculator can return a difference of 12 C. The name and schema tell the model how to request that calculation; they do not calculate 12. The seminar follows the same pattern for a temperature-summary function.
Bridge to code: Read lecture tools.py::calculate_temperature_gap, then tool_definitions.py::model_tools. Separate the implementation from its offered interface. Finally locate the seminar StatsArgs validation model and its generated JSON schema.

API mapping note: This slide shows a Responses-style tool entry with strict=true. The current course code uses DeepSeek Chat Completions and nests name, description and parameters under function. Do not copy the slide entry as a runnable DeepSeek request or assume its strict flag is supported here; local validation remains required.


#### t02.review_function - Begin with the lecture calculator

Logic: The lecture calculator has one narrow job: subtract two supplied Celsius values. It does not find a missing reference or read a sensor.

Explanation: Read the function signature first: two named arguments enter. GapArgs checks them. The body performs the calculation, and ok returns a dictionary containing data and source. Calling this Python function directly needs no language model. To let a model request it, we must describe the callable interface and connect it to a handler.

- Read lecture/tools.py -> calculate_temperature_gap; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

#### t02.review_contract - A tool description is not a function body

Logic: The model must know which capability fits the question and what input fields it may supply.

Explanation: The first excerpt is an internal definition draft: name identifies the capability, description explains its job, properties names input fields, and required lists fields the caller must supply. Then inspect the final return line: it nests name, description and parameters under function for the DeepSeek request. Do not send the internal flat draft as though it were the final API object. No Python function body is sent as executable code.

- Read lecture/tool_definitions.py -> model_tools; start at symbol offset 4, show at most 12 lines. Resolve current source lines; do not invent line numbers.
- Read lecture/tool_definitions.py -> model_tools; start at symbol offset 46, show at most 1 lines. Resolve current source lines; do not invent line numbers.

#### t02.interface - Apply the same pattern to temperature statistics

Logic: The seminar calculation is different, but its tool interface follows the same pattern.

Explanation: ARG_TYPES connects a tool name to StatsArgs. model_json_schema converts that validation model into the parameter description offered to DeepSeek. At execution time StatsArgs validates actual values. Your function computes a small summary and returns success with the course envelope. The count rule uses >; treat that as one implementation detail, not the purpose of function calling.

- Read seminar/tool_definitions.py -> model_tools; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

### Practice path

#### t02.practice_interface - What the model sees and what Python runs

Logic: Your task is to complete a calculation tool that the application can safely offer to DeepSeek.

Explanation: Read model_tools: it builds the model-visible name, description and parameters from ARG_TYPES. Then locate the temperature_stats starter. StatsArgs checks real arguments; success wraps the returned data with source and status. These are separate jobs. A function on disk is not callable by the model until the host offers and dispatches it.

- Read seminar/tool_definitions.py -> model_tools; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

#### t02.practice_body - Write the small function behind the interface

Logic: We already have the readings and reference. This function should calculate, not retrieve or invent inputs.

Explanation: Follow the validated args object. Count values, add them for the mean, select the maximum, and count values above the supplied reference. Return named fields inside success so the caller can inspect them. Explain return versus print if needed. Keep empty-list and equal-to-reference checks as short tests of the promised contract.

- Read seminar/tools/calculation.py -> temperature_stats; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

### Exercise, run and check

Before execution: explain the task and purpose, then ask what the learner expects. Save student code from chat. Obtain approval for live requests within the stated limit.
After execution: open the current run report, distinguish expected values from observed results, explain fields and errors, then ask each understanding question separately.
If an answer has been shown, ask: "Please explain that in your own words before we continue."

## t03 - Read the registered specification

Purpose: Choose the right data tool and return its provenance through a clear interface.

Core time: review 8 minutes; practice 10 minutes.

### Review path

#### t03.slide_evidence - A reference value is not a sensor reading

Logic: The meaning and source of a number matter as much as its numeric value.

Explanation: A registered specification is a filed reference, like a value in a machine handbook. A sensor reading is an observation at a time. A calculation is a new value obtained from supplied inputs. The fact that all three may contain temperature numbers does not make them interchangeable. Keeping the lookup and calculator separate also makes each function easier to test and prevents the calculator from inventing missing inputs.

PPT page 16: The calculator gets its inputs from a separate tool
Show the original image: slides/slide-16.png

Guide attention through the slide:
- Read the temperature scale: 85 is the registered reference and 97 is the supplied reading. The marked gap is the calculated difference, 12 C.
- Move to the specification result. machine_id identifies the equipment; temperature_limit_c names what the number means; spec_version and source identify where it came from.
- Point to the unknown-machine case. The lookup reports that no record is available instead of assuming every machine has the same reference.
- Connect to the result envelope on slide 17: status, data and provenance allow an answer to be checked against a concrete returned record.

Plain-language explanation: A registered specification is a filed reference, like a value in a machine handbook. A sensor reading is an observation at a time. A calculation is a new value obtained from supplied inputs. The fact that all three may contain temperature numbers does not make them interchangeable. Keeping the lookup and calculator separate also makes each function easier to test and prevents the calculator from inventing missing inputs.
Concrete example: get_machine_spec("CONV-3") can establish the classroom registered limit of 85 C and its source. It cannot establish CONV-3's current measured temperature. For CONV-99, an explicit missing-record error is more informative than an invented 85 C.
Bridge to code: Trace lecture tools.py::get_machine_spec from the fixed register to its selected entry and return value, then complete the seminar reader while preserving source and version.

API mapping note: The lecture uses an ok/data/error envelope, while the seminar uses status/data/source/version/error. These are course conventions, not universal MCP or Function Calling fields. Explain the actual keys in each code pack. Fetching a missing specification and then calculating requires separate calls; this week does not automate that chain.


#### t03.review_spec - Read the lecture specification lookup

Logic: The lecture uses a separate specification tool because maintenance history and reference limits have different meanings.

Explanation: The function validates machine_id, reads the fixed JSON register and selects the requested machine. If there is no entry, it raises a business error rather than inventing a default value. On success, the returned fields include the reference, version and source. Trace CONV-3 through those operations before moving to the seminar starter.

- Read lecture/tools.py -> get_machine_spec; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

#### t03.interface - Return evidence with its source

Logic: A registered reference and a measured temperature can both be numbers, but they answer different questions.

Explanation: The seminar reader has a fixed SPEC_PATH, so the model cannot choose an arbitrary file. SpecArgs validates the supplied ID. Parse the document, check whether the machine exists, and preserve its source and version when returning success. Unknown machine and unreadable source are different errors. The model needs these distinctions to explain the result honestly.

- Read seminar/tools/engineering.py -> get_machine_spec; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

### Practice path

#### t03.interface - Return evidence with its source

Logic: A registered reference and a measured temperature can both be numbers, but they answer different questions.

Explanation: The seminar reader has a fixed SPEC_PATH, so the model cannot choose an arbitrary file. SpecArgs validates the supplied ID. Parse the document, check whether the machine exists, and preserve its source and version when returning success. Unknown machine and unreadable source are different errors. The model needs these distinctions to explain the result honestly.

- Read seminar/tools/engineering.py -> get_machine_spec; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

### Exercise, run and check

Before execution: explain the task and purpose, then ask what the learner expects. Save student code from chat. Obtain approval for live requests within the stated limit.
After execution: open the current run report, distinguish expected values from observed results, explain fields and errors, then ask each understanding question separately.
If an answer has been shown, ask: "Please explain that in your own words before we continue."

## t04 - Query a precise temperature window

Purpose: Keep SQL under application control while allowing the model to supply validated query arguments.

Core time: review 12 minutes; practice 13 minutes.

### Review path

#### t04.slide_query - Use the table to explain the lookup

Logic: The model supplies bounded values to a defined lookup. The application keeps control of the query itself.

Explanation: A query is a request for selected rows from a table. The developer writes the query structure, while the caller supplies only the allowed values. Binding means sending those values separately from the SQL text so they are treated as data. Before execution, argument checks reject invalid types or excessive limits; the registry chooses the allowed function. A read-only connection provides another concrete restriction. None of these checks alone can prove that the requested machine matches the user's intent.

PPT page 15: The model fills two blanks; the SQL stays ours
Show the original image: slides/slide-15.png

Guide attention through the slide:
- Read the table before the SQL: each row is one service record with a machine, date and action.
- For CONV-3's last service, first keep only CONV-3 rows. The newer CONV-7 row is irrelevant to this question.
- Then order the remaining dates newest first and keep one row. This gives EV-104, dated 2026-03-18, with the recorded cooling-fan replacement.
- Now match those operations to WHERE, ORDER BY and LIMIT. The two question marks are value slots, not places for arbitrary SQL commands.

Plain-language explanation: A query is a request for selected rows from a table. The developer writes the query structure, while the caller supplies only the allowed values. Binding means sending those values separately from the SQL text so they are treated as data. Before execution, argument checks reject invalid types or excessive limits; the registry chooses the allowed function. A read-only connection provides another concrete restriction. None of these checks alone can prove that the requested machine matches the user's intent.
Concrete example: With machine_id="CONV-3" and max_records=1, the maintenance lookup selects CONV-3's latest stored service, not the newest service anywhere in the table. The seminar transfers this idea to a machine ID and a temperature time window; its query remains fixed as well.
Bridge to code: Read lecture tools.py::query_maintenance and match the table operations to its fixed SELECT and bound values. Then inspect the seminar SQL and QueryArgs before writing the temperature reader.


#### t04.review_sql - The lecture model fills blanks, not SQL

Logic: Maintenance retrieval shows how a narrow tool can expose useful database access without accepting arbitrary code.

Explanation: Read the fixed SELECT in query_maintenance. It selects known columns, filters machine_id, sorts newest first and limits the number of records. The model supplies machine_id and max_records through a validated contract. Parameter binding inserts their values without giving the caller control of the query structure. The application then turns returned rows into named fields.

- Read lecture/tools.py -> query_maintenance; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.
- Read lecture/tools.py -> query_maintenance; start at symbol offset 12, show at most 8 lines. Resolve current source lines; do not invent line numbers.

#### t04.interface - Keep the query fixed and bind the arguments

Logic: The model should request a defined lookup, not invent arbitrary database commands.

Explanation: QueryArgs checks machine and timezone-aware start/end inputs. SQL contains question marks for values; binding parameters keeps the SQL structure fixed. mode=ro and query_only prevent writes in this classroom reader. The interval includes start and excludes end. More than 100 matching rows is reported as a limit error rather than a silently incomplete answer.

- Read seminar/tools/sql_query.py -> SQL; start at symbol offset 0, show at most 7 lines. Resolve current source lines; do not invent line numbers.
- Read seminar/tools/sql_query.py -> query_temperature; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

### Practice path

#### t04.interface - Keep the query fixed and bind the arguments

Logic: The model should request a defined lookup, not invent arbitrary database commands.

Explanation: QueryArgs checks machine and timezone-aware start/end inputs. SQL contains question marks for values; binding parameters keeps the SQL structure fixed. mode=ro and query_only prevent writes in this classroom reader. The interval includes start and excludes end. More than 100 matching rows is reported as a limit error rather than a silently incomplete answer.

- Read seminar/tools/sql_query.py -> SQL; start at symbol offset 0, show at most 7 lines. Resolve current source lines; do not invent line numbers.
- Read seminar/tools/sql_query.py -> query_temperature; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

### Exercise, run and check

Before execution: explain the task and purpose, then ask what the learner expects. Save student code from chat. Obtain approval for live requests within the stated limit.
After execution: open the current run report, distinguish expected values from observed results, explain fields and errors, then ask each understanding question separately.
If an answer has been shown, ask: "Please explain that in your own words before we continue."

## t05 - Follow a DeepSeek tool call

Purpose: Understand every hand-off from user question to final answer.

Core time: review 10 minutes; practice 10 minutes.

### Review path

#### t05.slide_messages - Follow the request slip and its receipt

Logic: The returned result must be linked to the exact request that caused it.

Explanation: The request identifier works like a receipt number. The application keeps the model's original request and attaches the result to that same request. Otherwise a model could receive a number without a reliable connection to the operation that produced it. The final answer is another generated message, so we compare it with the returned evidence rather than trusting its tone.

PPT page 8: A function call is three messages and one shared id
Show the original image: slides/slide-08.png

Guide attention through the slide:
- Start at message 1: the application sends a task and a catalogue of tools. The model does not discover arbitrary Python files.
- Read message 2 as a call slip: a name, arguments and an identifier. It contains the requested inputs, not a retrieved maintenance record.
- Pause at the small validation, registry and execution box between messages 2 and 3. This work belongs to the application even though it is drawn between two model messages.
- Match the identifier in message 3 to the call slip, then follow the final plain-text answer. Use slide 18 to reinforce that the real result is sent back before asking for that answer.

Plain-language explanation: The request identifier works like a receipt number. The application keeps the model's original request and attaches the result to that same request. Otherwise a model could receive a number without a reliable connection to the operation that produced it. The final answer is another generated message, so we compare it with the returned evidence rather than trusting its tone.
Concrete example: If one slip requests CONV-3 maintenance, its paired result should contain that lookup's record. A result for another machine does not become correct merely because the JSON is well formed or the request identifier matches.
Bridge to code: Trace lecture first_call, run_tool and complete_trip in that order. In the seminar, find the same responsibilities in run_turn and Executor.execute.

API mapping note: Slides 8 and 18 illustrate Responses-style call_id and function_call_output. Current DeepSeek Chat Completions uses message.tool_calls entries with id, followed by a role="tool" message with the matching tool_call_id. Teach the shared pairing idea, then use the actual current syntax.


#### t05.review_proposal - First call: a proposal, not execution

Logic: The application sends a question and a list of available tools. DeepSeek may select a tool, ask for missing inputs, or answer without one.

Explanation: In first_call, tools attaches the definitions and tool_choice="auto" allows selection. message.tool_calls contains proposed requests. Each has an ID, function name and arguments string. Turning those fields into a slip is only parsing. No database function has been called yet. The one-call guard rejects multiple proposals in this week's bounded workflow.

- Read lecture/live.py -> first_call; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

#### t05.review_dispatch - Only the application can dispatch the request

Logic: A model-generated name is data until the application chooses an allowed implementation.

Explanation: run_tool looks up the name in REGISTRY. If no entry exists it returns UNKNOWN_TOOL. The registered argument model validates the JSON string. Only after those checks does handler(**args.model_dump()) call Python, using the validated fields as named arguments. A correct type or range still cannot prove that the model chose the machine the user intended.

- Read lecture/registry.py -> run_tool; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.
- Read lecture/registry.py -> run_tool; start at symbol offset 12, show at most 10 lines. Resolve current source lines; do not invent line numbers.

#### t05.review_return - Return the result with the matching ID

Logic: The model needs the real tool result to explain what happened. The request ID connects that result to the earlier call.

Explanation: complete_trip preserves the assistant call message, then appends a role="tool" message. tool_call_id matches the requested call; content contains serialized result data. The second model request uses tool_choice="none", so this turn ends with an explanation instead of another tool. Check the explanation against the recorded data: wording can be wrong even after correct execution.

- Read lecture/live.py -> complete_trip; start at symbol offset 11, show at most 12 lines. Resolve current source lines; do not invent line numbers.

#### t05.transfer - Find the same responsibilities in the seminar

Logic: The temperature assistant implements the same message sequence with different tool capabilities.

Explanation: Locate executor.execute, the assistant tool_calls message, the role="tool" result and the second request in run_turn. Match each line to its role in the lecture chain. The upcoming replay runs your tools but scripts the model choices and final text. It checks the application path without establishing live model reliability.

- Read seminar/workflow.py -> run_turn; start at symbol offset 32, show at most 12 lines. Resolve current source lines; do not invent line numbers.

### Practice path

#### t05.practice_proposal - Read the model-to-application boundary

Logic: The first DeepSeek request asks what to do; it does not run a function.

Explanation: run_turn prepares model, tools and messages, then requests tool_choice="auto". The returned choices contain the assistant message and any tool_calls. Check completion before using a response. The app rejects multiple calls and malformed requests before invoking its executor. Explain JSON text versus a Python dictionary if needed.

- Read seminar/workflow.py -> run_turn; start at symbol offset 0, show at most 9 lines. Resolve current source lines; do not invent line numbers.
- Read seminar/workflow.py -> run_turn; start at symbol offset 12, show at most 12 lines. Resolve current source lines; do not invent line numbers.

#### t05.practice_dispatch - Validate and execute only registered code

Logic: The application controls which functions run and which arguments reach them.

Explanation: Executor checks the name against handlers and ARG_TYPES, checks policy, parses JSON and validates the argument model. It then invokes a local handler or the selected MCP route. The returned envelope and data fields are validated too. These checks establish a contract, not whether a natural-language request was understood correctly.

- Read seminar/executor.py -> Executor.execute; start at symbol offset 7, show at most 12 lines. Resolve current source lines; do not invent line numbers.
- Read seminar/executor.py -> Executor.execute; start at symbol offset 24, show at most 12 lines. Resolve current source lines; do not invent line numbers.

#### t05.practice_return - Send evidence back before asking for an answer

Logic: A tool result must be connected to the call that requested it.

Explanation: The assistant message is kept, then the result is added with role="tool" and the matching tool_call_id. JSON content carries the actual course envelope. The second request uses tool_choice="none". The final answer is checked separately from the result, and tool failure cannot be rewritten as success. Replay has the same shape but scripted model behaviour.

- Read seminar/workflow.py -> run_turn; start at symbol offset 32, show at most 12 lines. Resolve current source lines; do not invent line numbers.

### Exercise, run and check

Before execution: explain the task and purpose, then ask what the learner expects. Save student code from chat. Obtain approval for live requests within the stated limit.
After execution: open the current run report, distinguish expected values from observed results, explain fields and errors, then ask each understanding question separately.
If an answer has been shown, ask: "Please explain that in your own words before we continue."

## t06 - Let DeepSeek choose the tool

Purpose: Compare real model choices with the meaning of the question.

Core time: review 6 minutes; practice 6 minutes.

### Review path

#### t06.live_evidence - Separate a real model decision from a replay

Logic: Now DeepSeek must choose among the three tools from the wording of each question.

Explanation: app.py selects ScriptedCompletions only when replay was explicitly requested. Live mode creates the DeepSeek client using a private key. Each data question can make up to two API requests, so these three cases have a six-request budget. Inspect chosen name, arguments, validation events, returned data and final answer. No silent fallback is allowed.

- Read seminar/app.py -> execute; start at symbol offset 4, show at most 12 lines. Resolve current source lines; do not invent line numbers.

### Practice path

#### t06.live_evidence - Separate a real model decision from a replay

Logic: Now DeepSeek must choose among the three tools from the wording of each question.

Explanation: app.py selects ScriptedCompletions only when replay was explicitly requested. Live mode creates the DeepSeek client using a private key. Each data question can make up to two API requests, so these three cases have a six-request budget. Inspect chosen name, arguments, validation events, returned data and final answer. No silent fallback is allowed.

- Read seminar/app.py -> execute; start at symbol offset 4, show at most 12 lines. Resolve current source lines; do not invent line numbers.

### Exercise, run and check

Before execution: explain the task and purpose, then ask what the learner expects. Save student code from chat. Obtain approval for live requests within the stated limit.
After execution: open the current run report, distinguish expected values from observed results, explain fields and errors, then ask each understanding question separately.
If an answer has been shown, ask: "Please explain that in your own words before we continue."

## t07 - Find failures and improve one description

Purpose: Locate errors instead of trusting fluent answers.

Core time: review 8 minutes; practice 8 minutes.

### Review path

#### t07.slide_success - A successful function can answer the wrong question

Logic: Execution success and task success are separate judgments.

Explanation: A schema checks an input's structure and allowed values; it cannot infer every detail of a user's intended task. This is why an assistant needs checks at several points: useful descriptions before selection, validation before execution, and a comparison between request, trace and answer afterward. A better description can reduce mistakes, but the actual traces show whether it helped.

PPT page 20: The call succeeded perfectly — on the wrong machine
Show the original image: slides/slide-20.png

Guide attention through the slide:
- Compare the two machine labels: the request is for CONV-3 but the lookup targets CONV-7.
- Read the two scores separately. FUNCTION executed means the call ran; TASK remains unverified until its arguments and result are compared with the request.
- Identify what the existing checks could establish: the ID had an acceptable form, the tool existed and the function returned a result.
- Name what is still missing: evidence that this was the machine and information the user actually asked for.

Plain-language explanation: A schema checks an input's structure and allowed values; it cannot infer every detail of a user's intended task. This is why an assistant needs checks at several points: useful descriptions before selection, validation before execution, and a comparison between request, trace and answer afterward. A better description can reduce mistakes, but the actual traces show whether it helped.
Concrete example: A correct CONV-7 specification is still an incorrect response to a CONV-3 specification question. In contrast, a wrong argument type should be stopped before the handler runs. These failures occur at different places in the chain.
Bridge to code: Compare lecture tool descriptions, then inspect the seminar failure_demo events. Identify the first failed responsibility before editing one description and testing the real before/after evidence.


#### t07.review_description - A description helps the model choose a capability

Logic: Several tools can mention equipment and temperature. A vague description does not separate their jobs.

Explanation: Compare the lecture DESCRIPTIONS. query_maintenance states that it reads service history; get_machine_spec names registered limits; the calculator requires supplied values. The exclusions matter because they prevent a plausible but irrelevant selection. The application still validates inputs and checks evidence after selection.

- Read lecture/tool_definitions.py -> DESCRIPTIONS; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

#### t07.failure_layers - Find the failed responsibility

Logic: A fluent answer does not tell us whether selection, validation or execution was correct.

Explanation: The injected cases deliberately request a wrong type, unknown tool, reversed time window, execution exception and valid wrong machine. Follow each event's validation, permission, invoked and result fields. These are application tests, not naturally observed model errors. Then improve the specification description and compare a real baseline with the same question and a paraphrase.

- Read seminar/failure_demo.py -> main; start at symbol offset 1, show at most 12 lines. Resolve current source lines; do not invent line numbers.

### Practice path

#### t07.failure_layers - Find the failed responsibility

Logic: A fluent answer does not tell us whether selection, validation or execution was correct.

Explanation: The injected cases deliberately request a wrong type, unknown tool, reversed time window, execution exception and valid wrong machine. Follow each event's validation, permission, invoked and result fields. These are application tests, not naturally observed model errors. Then improve the specification description and compare a real baseline with the same question and a paraphrase.

- Read seminar/failure_demo.py -> main; start at symbol offset 1, show at most 12 lines. Resolve current source lines; do not invent line numbers.

### Exercise, run and check

Before execution: explain the task and purpose, then ask what the learner expects. Save student code from chat. Obtain approval for live requests within the stated limit.
After execution: open the current run report, distinguish expected values from observed results, explain fields and errors, then ask each understanding question separately.
If an answer has been shown, ask: "Please explain that in your own words before we continue."

## t08 - Understand MCP, then build and test a server

Purpose: Expose the tested specification tool through a shared protocol.

Core time: review 28 minutes; practice 28 minutes.

### Review path

#### t08.mcp_need - Why not just call the Python function?

Logic: For one small application with a few local functions, direct function calling can be enough. MCP is optional; adding it does not make a model smarter.

Explanation: Our local tool list is prepared in tool_definitions.py. A second application could reuse that Python package, but another language or process needs an agreed interface. MCP, the Model Context Protocol, standardizes messages for discovering and using capabilities. This can reduce separate connection code across applications. The function still performs the same narrow job.

- Read seminar/tool_definitions.py -> model_tools; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

#### t08.mcp_roles - Three roles, two different connections

Logic: Function calling links the model to its application. MCP links an application client to a tool server. They describe different connections in the same workflow.

Explanation: The Host is the whole assistant application. Its Client speaks MCP to a Server that offers a function. In app.py, routes chooses either a local function or an MCPBackend. async with opens the connection for this block and closes it afterward. DeepSeek receives model API requests; it does not connect directly to the local server. A client can test the server with no model present.

- Read seminar/app.py -> routes; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

Required short check: DeepSeek proposes get_machine_spec for CONV-3. On the MCP route, which sequence reaches the Python function?
- A: DeepSeek connects directly to the server through stdio.
- B: The host checks the request, then its MCP client calls the server tool.
- C: The parameter schema runs the function as soon as the model reads it.
Save the actual response with lesson-answer. Resolve an incorrect answer with the two-hint policy before lesson-next. Do not reveal the answer immediately.

#### t08.mcp_process - Local messages and a deliberately limited environment

Logic: A process is a running program. Our client starts a separate Python program for the server and exchanges messages through its input and output streams. This transport is called stdio.

Explanation: server_parameters selects the same Python interpreter and the server script. Its environment allowlist does not intentionally pass DEEPSEEK_API_KEY. The specification reader has no need for that key. This reduces unnecessary credential exposure, but a separate process under the same user is not an automatic file-permission sandbox. Keep stdout for protocol messages and send diagnostic logs to stderr. No HTTP port or GPU is required here.

- Read seminar/mcp_backend.py -> server_parameters; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

#### t08.mcp_discovery - Discover a tool before requesting its result

Logic: A catalogue describes what can be requested. It is not the requested equipment data. Discovering tools does not execute all of them.

Explanation: Read the lecture client: list_tools asks for names, descriptions and argument schemas. call_tool names one function and supplies an argument dictionary. await means wait for that operation to finish before using its result. The known machine should return a structured record; an unknown machine should produce an explicit error. This independent check separates connection problems from model-selection problems.

- Read lecture/check_server.py -> main; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

Required short check: The client has completed only await client.list_tools(). It sees get_machine_spec and its machine_id input. What has it obtained so far?
- A: The tool interface; it still needs call_tool with CONV-3 to request the registered value.
- B: The CONV-3 registered value, because listing a tool also runs it.
- C: Every machine record, because discovery loads all tool data.
Save the actual response with lesson-answer. Resolve an incorrect answer with the two-hint policy before lesson-next. Do not reveal the answer immediately.

#### t08.mcp_wrapper - Wrap the tested function instead of rewriting it

Logic: The server is an interface around a function we already trust enough to test. Its wrapper should not create a second source of specification data.

Explanation: MCPServer creates the server object. @server.tool registers the following function; it does not run it immediately. The return annotation dict[str, Any] and structured_output=True request structured output. The alias read_spec refers to the existing reader, avoiding an accidental call back to the wrapper itself. Known business failures become ToolError rather than successful-looking text. Use the lecture implementation to understand the pattern, then complete the seminar wrapper yourself.

- Read lecture/mcp_server.py -> get_machine_spec; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

#### t08.mcp_results - Structured results and honest failure signals

Logic: A string that looks like JSON is still text. A structured result lets the application inspect fields without guessing from a sentence.

Explanation: unpack_result first checks is_error. If it is true, the course raises a tool failure instead of treating the message as data. Next it requires a structured_content dictionary and validates our ToolResult envelope. status, data, source, version and error are this seminar's field names, not mandatory fields for every MCP server. The lecture uses an ok-based envelope, so do not interchange their keys.

- Read seminar/mcp_backend.py -> unpack_result; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

Required short check: An MCP reply has is_error=True. Its text mentions "85 C", but no valid structured result was confirmed. What should our client do?
- A: Extract 85 and report a successful specification lookup.
- B: Ask the model to guess whether the number is probably correct.
- C: Keep the failure and report that no specification value was confirmed.
Save the actual response with lesson-answer. Resolve an incorrect answer with the two-hint policy before lesson-next. Do not reveal the answer immediately.

#### t08.mcp_bridge - Discovered metadata still needs an application decision

Logic: The model does not automatically see every tool advertised by a server. The host decides which definitions to offer and which requests to allow.

Explanation: adapt_spec_tool accepts only our expected specification tool and simple machine_id schema. It rejects unsupported schema shapes instead of silently dropping constraints. It then forms the nested function definition used by DeepSeek. This is a deliberately narrow teaching adapter, not a universal schema converter. Local validation and permission checks remain in the executor after discovery.

- Read seminar/mcp_backend.py -> adapt_spec_tool; start at symbol offset 0, show at most 9 lines. Resolve current source lines; do not invent line numbers.
- Read seminar/mcp_backend.py -> adapt_spec_tool; start at symbol offset 9, show at most 6 lines. Resolve current source lines; do not invent line numbers.

#### t08.mcp_resource - Reading a resource does not put it in model context

Logic: A tool is invoked with arguments. A resource is content read through a resource interface. The difference is not simply whether data changes: our specification tool only reads.

Explanation: The lecture resource returns a short CONV-3 reference note. Reading that URI obtains content for the host. The host still has to select it and include it in a model request if it should affect the answer. That explicit selection is also why merely adding a resource is not a complete RAG system. We can now build and test the seminar wrapper before reconnecting DeepSeek.

- Read lecture/mcp_server.py -> conv3_spec_note; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

Required short check: The host reads the CONV-3 reference-note resource successfully, but sends DeepSeek only the original user question. Why can the model still lack the note?
- A: Reading any resource automatically updates the model weights.
- B: The host must select the relevant content and include it in a model request.
- C: The server must rename the resource as a tool before any model can use its text.
Save the actual response with lesson-answer. Resolve an incorrect answer with the two-hint policy before lesson-next. Do not reveal the answer immediately.

### Practice path

#### t08.mcp_need - Why not just call the Python function?

Logic: For one small application with a few local functions, direct function calling can be enough. MCP is optional; adding it does not make a model smarter.

Explanation: Our local tool list is prepared in tool_definitions.py. A second application could reuse that Python package, but another language or process needs an agreed interface. MCP, the Model Context Protocol, standardizes messages for discovering and using capabilities. This can reduce separate connection code across applications. The function still performs the same narrow job.

- Read seminar/tool_definitions.py -> model_tools; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

#### t08.mcp_roles - Three roles, two different connections

Logic: Function calling links the model to its application. MCP links an application client to a tool server. They describe different connections in the same workflow.

Explanation: The Host is the whole assistant application. Its Client speaks MCP to a Server that offers a function. In app.py, routes chooses either a local function or an MCPBackend. async with opens the connection for this block and closes it afterward. DeepSeek receives model API requests; it does not connect directly to the local server. A client can test the server with no model present.

- Read seminar/app.py -> routes; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

Required short check: DeepSeek proposes get_machine_spec for CONV-3. On the MCP route, which sequence reaches the Python function?
- A: DeepSeek connects directly to the server through stdio.
- B: The host checks the request, then its MCP client calls the server tool.
- C: The parameter schema runs the function as soon as the model reads it.
Save the actual response with lesson-answer. Resolve an incorrect answer with the two-hint policy before lesson-next. Do not reveal the answer immediately.

#### t08.mcp_process - Local messages and a deliberately limited environment

Logic: A process is a running program. Our client starts a separate Python program for the server and exchanges messages through its input and output streams. This transport is called stdio.

Explanation: server_parameters selects the same Python interpreter and the server script. Its environment allowlist does not intentionally pass DEEPSEEK_API_KEY. The specification reader has no need for that key. This reduces unnecessary credential exposure, but a separate process under the same user is not an automatic file-permission sandbox. Keep stdout for protocol messages and send diagnostic logs to stderr. No HTTP port or GPU is required here.

- Read seminar/mcp_backend.py -> server_parameters; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

#### t08.mcp_discovery - Discover a tool before requesting its result

Logic: A catalogue describes what can be requested. It is not the requested equipment data. Discovering tools does not execute all of them.

Explanation: Read the lecture client: list_tools asks for names, descriptions and argument schemas. call_tool names one function and supplies an argument dictionary. await means wait for that operation to finish before using its result. The known machine should return a structured record; an unknown machine should produce an explicit error. This independent check separates connection problems from model-selection problems.

- Read lecture/check_server.py -> main; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

Required short check: The client has completed only await client.list_tools(). It sees get_machine_spec and its machine_id input. What has it obtained so far?
- A: The tool interface; it still needs call_tool with CONV-3 to request the registered value.
- B: The CONV-3 registered value, because listing a tool also runs it.
- C: Every machine record, because discovery loads all tool data.
Save the actual response with lesson-answer. Resolve an incorrect answer with the two-hint policy before lesson-next. Do not reveal the answer immediately.

#### t08.mcp_wrapper - Wrap the tested function instead of rewriting it

Logic: The server is an interface around a function we already trust enough to test. Its wrapper should not create a second source of specification data.

Explanation: MCPServer creates the server object. @server.tool registers the following function; it does not run it immediately. The return annotation dict[str, Any] and structured_output=True request structured output. The alias read_spec refers to the existing reader, avoiding an accidental call back to the wrapper itself. Known business failures become ToolError rather than successful-looking text. Use the lecture implementation to understand the pattern, then complete the seminar wrapper yourself.

- Read lecture/mcp_server.py -> get_machine_spec; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

#### t08.mcp_results - Structured results and honest failure signals

Logic: A string that looks like JSON is still text. A structured result lets the application inspect fields without guessing from a sentence.

Explanation: unpack_result first checks is_error. If it is true, the course raises a tool failure instead of treating the message as data. Next it requires a structured_content dictionary and validates our ToolResult envelope. status, data, source, version and error are this seminar's field names, not mandatory fields for every MCP server. The lecture uses an ok-based envelope, so do not interchange their keys.

- Read seminar/mcp_backend.py -> unpack_result; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

Required short check: An MCP reply has is_error=True. Its text mentions "85 C", but no valid structured result was confirmed. What should our client do?
- A: Extract 85 and report a successful specification lookup.
- B: Ask the model to guess whether the number is probably correct.
- C: Keep the failure and report that no specification value was confirmed.
Save the actual response with lesson-answer. Resolve an incorrect answer with the two-hint policy before lesson-next. Do not reveal the answer immediately.

#### t08.mcp_bridge - Discovered metadata still needs an application decision

Logic: The model does not automatically see every tool advertised by a server. The host decides which definitions to offer and which requests to allow.

Explanation: adapt_spec_tool accepts only our expected specification tool and simple machine_id schema. It rejects unsupported schema shapes instead of silently dropping constraints. It then forms the nested function definition used by DeepSeek. This is a deliberately narrow teaching adapter, not a universal schema converter. Local validation and permission checks remain in the executor after discovery.

- Read seminar/mcp_backend.py -> adapt_spec_tool; start at symbol offset 0, show at most 9 lines. Resolve current source lines; do not invent line numbers.
- Read seminar/mcp_backend.py -> adapt_spec_tool; start at symbol offset 9, show at most 6 lines. Resolve current source lines; do not invent line numbers.

#### t08.mcp_resource - Reading a resource does not put it in model context

Logic: A tool is invoked with arguments. A resource is content read through a resource interface. The difference is not simply whether data changes: our specification tool only reads.

Explanation: The lecture resource returns a short CONV-3 reference note. Reading that URI obtains content for the host. The host still has to select it and include it in a model request if it should affect the answer. That explicit selection is also why merely adding a resource is not a complete RAG system. We can now build and test the seminar wrapper before reconnecting DeepSeek.

- Read lecture/mcp_server.py -> conv3_spec_note; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

Required short check: The host reads the CONV-3 reference-note resource successfully, but sends DeepSeek only the original user question. Why can the model still lack the note?
- A: Reading any resource automatically updates the model weights.
- B: The host must select the relevant content and include it in a model request.
- C: The server must rename the resource as a tool before any model can use its text.
Save the actual response with lesson-answer. Resolve an incorrect answer with the two-hint policy before lesson-next. Do not reveal the answer immediately.

### Timing inside this task

- 3 min: Why MCP and who connects to whom
- 1 min: Trace the next hand-off
- 4 min: Local messages and tool discovery
- 1 min: Predict what discovery returns
- 4 min: The server wrapper and result checks
- 1 min: Inspect a failure response
- 3 min: Select interfaces and resource context
- 1 min: Find the missing context connection
- 7 min: Complete the wrapper, run tests and read the output
- 3 min: Explain the full chain and check an unsupported conclusion

### Exercise, run and check

Before execution: explain the task and purpose, then ask what the learner expects. Save student code from chat. Obtain approval for live requests within the stated limit.
After execution: open the current run report, distinguish expected values from observed results, explain fields and errors, then ask each understanding question separately.
If an answer has been shown, ask: "Please explain that in your own words before we continue."

## t09 - Connect MCP to the DeepSeek assistant

Purpose: See the two interfaces working together in one trace.

Core time: review 5 minutes; practice 5 minutes.

### Review path

#### t09.slide_bridge - Discovery is followed by an application decision

Logic: The application decides what reaches the model and where an accepted request is routed.

Explanation: MCP discovery gives the host information about capabilities. The host still chooses which capabilities to offer to the model and how to adapt their schemas. Once the model proposes a request through Function Calling, the host checks it and uses its route table to reach the right implementation. This keeps responsibility in the application and allows local and MCP tools to work together.

PPT page 31: A discovered tool is not yet visible to the model
Show the original image: slides/slide-31.png

Guide attention through the slide:
- Follow the five numbered actions: fetch the catalogue, filter it, convert allowed definitions, receive a model request, then route it to the right client.
- Use the mapping table to connect name and description directly, and inputSchema to the model API's parameters field.
- Notice that the owning server is kept inside the application for routing. It is not a magic instruction that lets the model connect itself.
- Read the route table: the specification tool can use an MCP client while the maintenance lookup remains a local function.

Plain-language explanation: MCP discovery gives the host information about capabilities. The host still chooses which capabilities to offer to the model and how to adapt their schemas. Once the model proposes a request through Function Calling, the host checks it and uses its route table to reach the right implementation. This keeps responsibility in the application and allows local and MCP tools to work together.
Concrete example: Offering get_machine_spec through MCP can preserve its business purpose while changing its connection. Its discovered description or schema may differ from the local definition. We must inspect the actual offered interfaces before interpreting the comparison.
Bridge to code: Inspect app.py::execute where the discovered definition replaces the local specification entry, then follow MCPBackend.call_spec. Compare the saved tool_interfaces.json and actual traces.

API mapping note: The slide gives conceptual field mapping. The current adapter builds a nested DeepSeek function object and rejects unsupported schema shapes; it is not a universal converter.


#### t09.offered_definitions - Check the interface before comparing routes

Logic: A fair comparison changes the tool connection while keeping the requested business capability clear.

Explanation: Read routes: the MCP backend returns a callable and a discovered definition. execute replaces the local get_machine_spec definition before sending tools to DeepSeek. The other tools stay local. The trace saves tool_definitions, the actual list offered to the model. The task also saves tool_interfaces.json with local_definition_now, mcp_definition_sent and comparison flags. Check the local snapshot against the earlier local trace if its description has since been edited. Compare names, descriptions and parameter schemas; do not claim identical model input without checking.

- Read seminar/app.py -> execute; start at symbol offset 19, show at most 7 lines. Resolve current source lines; do not invent line numbers.

#### t09.trace_route - Follow the result through the new connection

Logic: MCP should change how the application reaches the specification function, not the meaning of its result.

Explanation: Executor selects remote_spec for the registered specification tool when that route is configured. MCPBackend.call_spec checks the ID, calls the server and validates the structured result. Inspect events.route, source, version and machine_id beside the previous local trace. A connection error must remain an error; it must not silently run a local substitute.

- Read seminar/mcp_backend.py -> MCPBackend.call_spec; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

### Practice path

#### t09.offered_definitions - Check the interface before comparing routes

Logic: A fair comparison changes the tool connection while keeping the requested business capability clear.

Explanation: Read routes: the MCP backend returns a callable and a discovered definition. execute replaces the local get_machine_spec definition before sending tools to DeepSeek. The other tools stay local. The trace saves tool_definitions, the actual list offered to the model. The task also saves tool_interfaces.json with local_definition_now, mcp_definition_sent and comparison flags. Check the local snapshot against the earlier local trace if its description has since been edited. Compare names, descriptions and parameter schemas; do not claim identical model input without checking.

- Read seminar/app.py -> execute; start at symbol offset 19, show at most 7 lines. Resolve current source lines; do not invent line numbers.

#### t09.trace_route - Follow the result through the new connection

Logic: MCP should change how the application reaches the specification function, not the meaning of its result.

Explanation: Executor selects remote_spec for the registered specification tool when that route is configured. MCPBackend.call_spec checks the ID, calls the server and validates the structured result. Inspect events.route, source, version and machine_id beside the previous local trace. A connection error must remain an error; it must not silently run a local substitute.

- Read seminar/mcp_backend.py -> MCPBackend.call_spec; start at symbol offset 0, show at most 12 lines. Resolve current source lines; do not invent line numbers.

### Exercise, run and check

Before execution: explain the task and purpose, then ask what the learner expects. Save student code from chat. Obtain approval for live requests within the stated limit.
After execution: open the current run report, distinguish expected values from observed results, explain fields and errors, then ask each understanding question separately.
If an answer has been shown, ask: "Please explain that in your own words before we continue."

## t10 - Explain the complete chain and save your work

Purpose: Connect the ideas and choose what to practise next.

Core time: review 3 minutes; practice 3 minutes.

### Review path

#### t10.slide_trace - Read the evidence chain back to front

Logic: A useful engineering answer lets us trace each claim to a result and the request that produced it.

Explanation: Traceability means being able to follow a claim back to the evidence that supports it. It is not the same as a long log: the important links must agree. Our course uses synthetic records, so our conclusions inherit that scope. Function Calling and MCP make particular operations possible; they do not prove a complete diagnosis or plan and execute an unlimited sequence of actions.

PPT page 37: The answer now traces back to the record it came from
Show the original image: slides/slide-37.png

Guide attention through the slide:
- Start with the quoted answer about the cooling fan. Locate its record ID, service date and named source.
- Move backward through the trace table: returned record, execution site, validation, model choice and original user request.
- Check that every row refers to the same machine and purpose. A broken link tells us what must be investigated.
- Read the scope note: latest in the teaching database is a narrower claim than latest in a real plant. Then use slide 38 to identify the missing loop for a multi-call request.

Plain-language explanation: Traceability means being able to follow a claim back to the evidence that supports it. It is not the same as a long log: the important links must agree. Our course uses synthetic records, so our conclusions inherit that scope. Function Calling and MCP make particular operations possible; they do not prove a complete diagnosis or plan and execute an unlimited sequence of actions.
Concrete example: The slide's example points to EV-104 and the recorded cooling-fan replacement in teaching_db_v1. For your own work, use a result from your actual saved run, name its source and explain one check that could still fail.
Bridge to code: Return to the saved seminar trace and your own functions. Explain the full request path, then state one next learning goal. A multi-step dependency belongs to the Week 4 loop.


#### t10.recap - Explain the chain in your own words

Logic: The main achievement is connecting a model proposal to inspected engineering evidence.

Explanation: Use one saved trace to tell the story: the host offers definitions, the model proposes a call, the application validates and dispatches it, a function returns data, and the model explains it. Locate MCP in that story if the remote route was used. Name one check that a schema cannot perform. Save a short next-learning goal, then choose whether to revisit a task or explore an optional topic.


### Practice path

#### t10.recap - Explain the chain in your own words

Logic: The main achievement is connecting a model proposal to inspected engineering evidence.

Explanation: Use one saved trace to tell the story: the host offers definitions, the model proposes a call, the application validates and dispatches it, a function returns data, and the model explains it. Locate MCP in that story if the remote route was used. Name one check that a schema cannot perform. Save a short next-learning goal, then choose whether to revisit a task or explore an optional topic.


### Exercise, run and check

Before execution: explain the task and purpose, then ask what the learner expects. Save student code from chat. Obtain approval for live requests within the stated limit.
After execution: open the current run report, distinguish expected values from observed results, explain fields and errors, then ask each understanding question separately.
If an answer has been shown, ask: "Please explain that in your own words before we continue."
