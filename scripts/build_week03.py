"""Build the Week 3 lesson and instructor reference from the approved teaching design."""
import json
from pathlib import Path
from week03_design import apply_design
from week03_checkpoints import apply_checkpoints

ROOT=Path(__file__).resolve().parents[1]/'week03'

def concept(id,title,brief,example):
    return dict(id=id,title=title,brief=brief,example=example)

FOUNDATIONS={
 'functions':concept('functions','Functions, arguments and return values','A function is a named piece of code. Arguments are the values we give it. A return value is the result we get back. A list holds several values in order.','temperature_stats([82, 97], 85) passes a list and one reference value. The function returns a dictionary, not a printed sentence.'),
 'records':concept('records','JSON, dictionaries and registered values','A dictionary connects keys to values. JSON is text used to send a similar structure between programs. A registered limit describes a reference, not the current temperature.','{"machine_id":"CONV-3"} is JSON text. json.loads turns it into a Python dictionary. 85 C in the register does not mean the sensor reads 85 C.'),
 'sql':concept('sql','Tables, queries and time windows','A table stores rows with named columns. SELECT reads chosen rows. A filter narrows the result. Our start time is included and our end time is excluded.','A reading at 10:00 belongs in [10:00,10:25); a reading exactly at 10:25 does not. This avoids counting a boundary twice in adjacent windows.'),
 'contracts':concept('contracts','Schemas and validation','A schema describes the allowed structure of data. Validation checks a particular input against that structure. It does not read the user\'s mind.','A valid ID for CONV-7 can pass all type checks even when the user asked about CONV-3. Compare the actual arguments with the question.'),
 'processes':concept('processes','Programs, processes and messages','A process is a running program. Two programs can exchange messages instead of importing each other\'s functions. Our MCP server runs locally in a separate process.','The client starts Python with mcp_server.py, writes protocol messages to its input, and reads replies from its output. No cloud server or GPU is needed.'),
}

SOLUTIONS={
'stats':'''args = StatsArgs.model_validate({'values_c': values_c, 'limit_c': limit_c})
count = len(args.values_c)
above = sum(value > args.limit_c for value in args.values_c)
return success({'count': count, 'mean_c': math.fsum(args.values_c) / count,
                'max_c': max(args.values_c), 'limit_c': args.limit_c,
                'above_count': above, 'above_fraction': above / count,
                'comparison': 'strictly_greater_than'}, 'provided_readings')''',
'spec':'''args = SpecArgs.model_validate({'machine_id': machine_id})
try:
    document = json.loads(SPEC_PATH.read_text(encoding='utf-8'))
except (OSError, ValueError) as exc:
    raise ToolFailure('DATA_UNAVAILABLE', 'Equipment register is unavailable.') from exc
if args.machine_id not in document['machines']:
    raise ToolFailure('NOT_FOUND', 'No registered specification for this machine.')
data = SpecData.model_validate({'machine_id': args.machine_id, **document['machines'][args.machine_id]})
return success(data.model_dump(), 'machine_specs.json', document['version'])''',
'query':'''args = QueryArgs.model_validate({'machine_id': machine_id, 'start': start, 'end': end})
parameters = (args.machine_id, int(datetime.fromisoformat(args.start).timestamp()),
              int(datetime.fromisoformat(args.end).timestamp()))
try:
    with closing(sqlite3.connect(DB_PATH.resolve().as_uri() + '?mode=ro', uri=True)) as connection:
        connection.execute('PRAGMA query_only=ON')
        rows = connection.execute(SQL, parameters).fetchall()
except sqlite3.Error as exc:
    raise ToolFailure('DATA_UNAVAILABLE', 'Temperature database is unavailable.') from exc
if len(rows) > 100:
    raise ToolFailure('RESULT_LIMIT', 'Narrow the time window: more than 100 rows matched.')
records = [{'ts': stamp, 'temperature_c': value} for stamp, value in rows]
return success({'machine_id': args.machine_id, 'start': args.start, 'end': args.end,
                'interval': '[start,end)', 'count': len(records), 'records': records,
                'unit': 'C'}, 'engineering.sqlite')''',
'mcp':'''try:
    args = SpecArgs.model_validate({'machine_id': machine_id})
    return read_spec(args.machine_id)
except (ValidationError, ToolFailure) as exc:
    message = exc.safe_message if isinstance(exc, ToolFailure) else 'Invalid machine ID.'
    raise ToolError(message) from exc''',
'description':'Read the registered temperature reference limit for a supplied machine ID. Return its source and version. Do not use this tool for measured temperatures or maintenance records.',
}
TARGETS={'stats':['tools/calculation.py','temperature_stats'], 'spec':['tools/engineering.py','get_machine_spec'],
         'query':['tools/sql_query.py','query_temperature'], 'mcp':['mcp_server.py','get_machine_spec']}

def openq(id,prompt,rubric):return dict(id=id,type='open',prompt=prompt,rubric=rubric)
def mcq(id,prompt,options,correct,feedback):return dict(id=id,type='mcq',prompt=prompt,options=dict(zip('ABCD',options)),correct=correct,feedback=feedback)
def task(id,title,minutes,practice,purpose,logic,walkthrough,answer,questions,refs=(),concepts=(),target=None,run=False,calls=0):
    return dict(id=id,title=title,minutes=minutes,practice_minutes=practice,weight=10,purpose=purpose,
                logic=logic,code_walkthrough=walkthrough,worked_answer=answer,questions=questions,
                code_refs=list(refs),concepts=list(concepts),code_target=target,requires_teaching=True,
                requires_prediction=run,commands=[['seminar_step.py','--task',id]] if run else [],
                planned_calls=calls,output_fields='Read the actual report and source-specific envelope. Never invent a run.',
                hint1='Describe what information goes in and what must come out.',
                hint2='Trace one concrete input through the relevant lines before choosing an answer.')

tasks=[
task('t01','Meet CONV-3 and choose your learning path',10,5,'Separate model reasoning from access to equipment data.',
 'CONV-3 is the same classroom conveyor in the lecture and seminar. Maintenance history, temperature readings and registered limits are different records about it. A faster model cannot read a database that the application has not connected.',
 ['Read preflight.py: package versions and key presence are printed, never the key itself.',
  'Read build_data.py: it creates synthetic classroom records; an existing database is not overwritten.',
  'Review mode: connect lecture pages 3, 5 and 7-8 to the task map. Practice mode: use a short task map, then start the code.'],
 'The model proposes a request. The application validates and executes it. The tool returns data. The model explains that data; its explanation still needs checking.',
 [mcq('q1','Which part actually runs the Python function?',['The application','The model weights','The JSON schema'],'A','The application runs the function after validation.')],
 [('preflight.py',None),('build_data.py','build')],['contracts']),
task('t02','Build a temperature summary tool',10,12,'Turn a clear counting rule into a tested function.',
 'We already have the readings and reference value. No database or model is needed for the calculation. Compare each reading with the reference; equal is not above.',
 ['StatsArgs.model_validate checks the input before any calculation; an empty list is rejected so we never divide by zero.',
  'len counts readings. math.fsum adds them; dividing by count gives the mean. max selects the largest reading.',
  'value > limit produces True or False; sum counts True values. Use > rather than >=.',
  'success wraps the data with status, source, version and an empty error field. return passes this object to the caller; print would only display it.'],
 'For 82,87,91,94,97 at reference 85: count=5, mean_c=90.2, max_c=97, above_count=4, above_fraction=0.8. These are expected example values until a real test is run. The ratio describes sampled readings, not time.',
 [openq('q1','Why does 85 not count as above 85, and why does 0.8 not prove 80% of the time was above the limit?','Explain strict comparison and that sampled readings do not establish duration.')],
 [TARGETS['stats']],['functions'],target='stats',run=True),
task('t03','Read the registered specification',8,10,'Read a fixed data source and preserve its meaning and provenance.',
 'The registered 85 C reference is not a sensor reading. Use the supplied machine ID, never invent one or accept a user-controlled file path.',
 ['SPEC_PATH fixes which register the tool can read.', 'read_text reads the file; json.loads parses its contents into dictionaries.',
  'Check membership before indexing machines. Unknown IDs produce NOT_FOUND; missing files produce DATA_UNAVAILABLE.',
  'SpecData validates output fields. Preserve the source filename and document version in success.'],
 'CONV-3 returns temperature_limit_c=85, unit=C and source=machine_specs.json. CONV-99 has no registered record. CONV-7 is a valid different machine and is not an answer to a CONV-3 question.',
 [openq('q1','The user asked for CONV-3 but the tool returned a valid CONV-7 record. What must you check?','Distinguish tool success from matching the requested machine; registered values are not measurements.')],
 [TARGETS['spec']],['records'],target='spec',run=True),
task('t04','Query a precise temperature window',12,13,'Read the right records without allowing arbitrary SQL or writes.',
 'A query filters rows for one device and time window. Include the start, exclude the end. A successful query can return zero rows.',
 ['QueryArgs normalizes timezone-aware timestamps and checks start < end and a maximum 24-hour window.',
  'Convert the validated times to epoch seconds. Bind values into the fixed SQL question marks; never concatenate user text into SQL.',
  'mode=ro opens a read-only connection; query_only adds another guard. closing releases the database handle even on failure.',
  'ORDER BY gives chronological order. LIMIT 101 lets us detect more than 100 rows and report RESULT_LIMIT instead of silently truncating.',
  'Turn each returned tuple into a dictionary. count equals len(records); an empty list means no matching records, not a temperature of zero.'],
 'The interval 2026-03-02 10:00 to 10:25 (+08:00), end excluded, contains five readings: 82,87,91,94,97. Database failure and zero matches have different status values.',
 [openq('q1','Explain why 10:25 is excluded and why no rows is different from a database failure.','Explain adjacent half-open windows and ok/count=0/records=[] versus error/data=null.')],
 [TARGETS['query'],('schemas.py','QueryArgs')],['sql'],target='query',run=True),
task('t05','Follow a DeepSeek tool call',10,10,'Understand every hand-off from user question to final answer.',
 'Function calling lets the model propose a named function and JSON arguments. The model does not execute Python. Our application accepts at most one call per turn.',
 ['model_tools builds DeepSeek objects with type=function and a nested function containing name, description and parameters.',
  'run_turn builds system/user messages and makes the first chat.completions request with tool_choice=auto.',
  'Read choices[0].message.tool_calls. Each call has id and function.name / function.arguments. arguments is JSON text, not executable Python.',
  'Reject more than one call before execution. Executor checks JSON, Pydantic types, access policy, handler name and returned fields.',
  'Append the assistant call message, then a role=tool message with the same tool_call_id and JSON result.',
  'The second request uses tool_choice=none, asking for an explanation. It is still possible for that explanation to be wrong.',
  'Replay uses the same message shape but scripted choices and final text. It can test plumbing, not model selection.'],
 'The normal trace has two requests and one execution. Tool call id and tool_call_id match. The standard DeepSeek endpoint is used without beta strict generation; local validation remains mandatory.',
 [openq('q1','Who checks and runs the call, and what connects a tool result to the original request?','Application validates/executes; matching call ID connects result; model only proposes and explains.')],
 [('workflow.py','run_turn'),('executor.py','Executor'),('tool_definitions.py','model_tools')],['contracts'],run=True),
task('t06','Let DeepSeek choose the tool',6,6,'Compare real model choices with the meaning of the question.',
 'Run the spec, query and stats questions separately. Each provides all required inputs. A question about a concept can be answered without a tool.',
 ['app.py uses DEEPSEEK_API_KEY and the DeepSeek endpoint. The OpenAI SDK is only the client library.',
  'Inspect calls, validated_arguments, events, tool_result and answer. Check the machine, time interval, units and provenance.',
  'A no-tool response may be valid for a concept question but does not satisfy a requested data lookup. Never replace a live failure with replay.'],
 'Expected selections are get_machine_spec, query_temperature and temperature_stats. Actual choices and wording can vary; inspect the recorded output rather than assuming the expected result.',
 [openq('q1','Use one real trace to explain whether the chosen tool, arguments and final answer match the question.','Reference actual run, verify input intent and result/answer consistency; acknowledge any failure.')],
 [('app.py','execute'),('workflow.py','run_turn')],run=True,calls=6),
task('t07','Find failures and improve one description',8,8,'Locate errors instead of trusting fluent answers.',
 'Controlled injected failures test the application. They are not evidence that DeepSeek made those errors. A useful tool description states purpose, inputs, outputs and boundaries.',
 ['failure_demo injects bad types, an unknown tool, a reversed time window, an exception and a valid wrong machine.',
  'Read validation, permission, invoked and result in each event. Locate where the call stopped.',
  'Write an improved get_machine_spec description in chat; Mentor saves it to student_description.txt, read by model_tools.',
  'Compare task 6 baseline with two new live questions after the edit, including a paraphrase. A clearer description does not guarantee correct selection.'],
 'A type error should stop before invocation. A function exception happens after invocation. A successful CONV-7 response still fails the CONV-3 intent. Explain the evidence even if the edited description does not improve the model.',
 [openq('q1','Which injected case can pass validation and still fail the task? What did your description change achieve?','Valid wrong machine is a semantic mismatch; compare real before/after traces without claiming guaranteed improvement.')],
 [('failure_demo.py','main'),('tool_definitions.py','model_tools')],target='description',run=True,calls=4),
task('t08','Understand MCP, then build and test a server',28,28,'Expose the tested specification tool through a shared protocol.',
 'Both study modes must complete the full MCP introduction before coding. Explain what MCP is, why it is useful, function calling versus MCP, Host/Client/Server, discovery versus execution, and local stdio. Optional Python/process explanations remain selectable.',
 ['Read MCP_GUIDE.md one section at a time before the TODO. Pause after each small explanation; do not skip this block in practice mode.',
  'MCPServer creates the server; @server.tool registers a callable with a name, description and input schema.',
  'The wrapper validates the ID and calls the existing read_spec. It does not create a second specification database.',
  'Translate known business failures into ToolError so the client sees an error, not a successful-looking message.',
  'Client starts the local server with a restricted environment. list_tools discovers metadata. call_tool requests execution.',
  'Inspect is_error and structured_content. Test CONV-3 success and CONV-99 error before attaching any model.',
  'read_resource fetches text separately. The host must deliberately put selected content into model context; it does not happen automatically.'],
 'Function calling is how the model proposes a request to its application. MCP is how that application discovers and calls a tool provider. They can work together; neither guarantees permissions or factual correctness. A real local client/server test requires no model API or GPU.',
 [openq('q1','Explain MCP to a classmate: why use it, how is it different from function calling, and how do they work together?','Shared tool interface across apps; model proposes via function calling; host/client invokes server via MCP; identify all three roles.'),
  mcq('q2','What does tools/list do?',['Run every tool','Return available tool descriptions and input schemas','Send all resources to the model'],'B','Discovery returns metadata. tools/call requests execution; resources need explicit selection.')],
 [TARGETS['mcp'],('mcp_backend.py','MCPBackend'),('mcp_client.py','main')],['processes'],target='mcp',run=True),
task('t09','Connect MCP to the DeepSeek assistant',5,5,'See the two interfaces working together in one trace.',
 'Use the same CONV-3 specification question as the local run. Only the tool route changes; DeepSeek still uses function calling.',
 ['MCPBackend.definition discovers the specification tool and adapts input_schema into the nested DeepSeek function.parameters.',
  'The host offers that definition to the model. Discovery alone does not give the model access.',
  'Executor routes only get_machine_spec to the MCP backend. Other tools remain local.',
  'Compare events.route, source, version and data with task 6. Connection, tool and answer errors are different layers. No silent local fallback.'],
 'A correct run shows provider=DeepSeek, route=mcp and the same CONV-3 registered reference. The model does not connect directly to stdio. The application owns the MCP client and returns the tool result to the model.',
 [openq('q1','What changed from the local run, and what stayed the same? Use the actual trace.','Tool transport changed to MCP; model function calling and validated data contract remain; reference recorded route and source.')],
 [('mcp_backend.py','adapt_spec_tool'),('app.py','routes')],run=True,calls=2),
task('t10','Explain the complete chain and save your work',3,3,'Connect the ideas and choose what to practise next.',
 'Review model proposal, application validation, execution, tool output and checked explanation. MCP changes the app-to-tool connection, not responsibility for verification.',
 ['Use the saved reports and your own code as evidence.', 'Return to any completed task through revisit; its discussion can be replayed without resetting completion.',
  'Use a new learning session for fresh code exercises. Finish with one short explanation now; the three-question reflection command remains available after class.'],
 'A trustworthy workflow checks intent, arguments, permissions, execution status, provenance and the final answer. Passing a schema does not prove the user received the right answer.',
 [openq('q1','Describe the full CONV-3 request path, one failure you would check for, and one thing you want to practise next.','Include model/app/tool responsibilities, MCP placement, a concrete failure check and a next learning step.')]),
]

for t in tasks:
    if t['id']=='t01':t['requires_setup']=True
    if t['id']=='t08':t['mandatory_mcp']=True
lesson=dict(id='week03',version=1,title='CONV-3: tools, DeepSeek function calling and MCP',requires_api_key=True,
            language='English; Chinese translation only on explicit request',teaching_order=['logic','code','attempt','run','explain output','check understanding'],
            modes={'review':'Review the lecture with detailed code explanations','practice':'Start the seminar exercises; keep the full MCP introduction'},
            foundations=FOUNDATIONS,code_targets=TARGETS,tasks=tasks,extensions=[])
for id,title,purpose,command,calls in [
 ('cases','Complete seven-case evaluation','Check missing inputs, concepts, denied writes and unknown devices.',['evaluate.py','--mode','live','--route','local'],14),
 ('boundaries','More boundary tests','Inspect timezones, row limits, permissions and output validation.',['-m','pytest','tests/test_tools.py','-q'],0),
 ('resources','MCP resources and context','Read the manual explicitly and explain why it is not automatically in model context.',['mcp_client.py','--read-resource'],0)]:
    lesson['extensions'].append(dict(id=id,title=title,purpose=purpose,planned_calls=calls,commands=[command],code_refs=[],guide='Explain the purpose, predict, run, inspect actual outputs and discuss limitations. Optional work never changes core completion.'))
apply_design(lesson)
apply_checkpoints(lesson)
ROOT.mkdir(exist_ok=True)
(ROOT/'lesson.json').write_text(json.dumps(lesson,indent=2)+'\n',encoding='utf-8')
(ROOT/'instructor').mkdir(exist_ok=True)
(ROOT/'instructor/solutions.json').write_text(json.dumps(SOLUTIONS,indent=2)+'\n',encoding='utf-8')
guide=['# Week 3 teaching script','',
       'Both modes contain 2 x 50 minutes of core learning and use logic then detailed code. No required mathematics segment. Explain one concept and a 5-12-line excerpt at a time: inputs, variables, branches, return values and why each check exists. Never just read code aloud.',
       'Use the selected path below. Review first shows and explains the actual PPT page, its diagram and a concrete example, then connects the idea to lecture code and seminar practice. Practice starts from the seminar task and teaches its necessary concepts. Both include the complete MCP introduction with four short checks between explanations.',
       'Offer foundations: I understand - continue / Explain briefly / Show an example. Record the choice. MCP_GUIDE.md is required in BOTH modes before task t08 practice.',
       'Use one question at a time. Give two gradual hints with attempts between. If still stuck, ask whether to continue hints or explain the answer. After an explanation, require the learner\'s own words before continuing. Save that actual answer, not the model answer.',
       'Use a compact title, short paragraphs, a fenced code excerpt and one next action. Use real choice cards when supported; otherwise show numbered choices. Keep helper JSON, instructor rubrics and long command listings out of learner messages.',
       'Every message ends with the exact saved core percentage. Pause does not change progress. Explain task and purpose before execution; inspect actual results before explaining the schema. Label output as Expected example, Scripted replay or Observed result, as appropriate.', '',
       '## Choose your learning mode','']
for card in lesson['mode_cards']:
    guide += ['- **'+card['label']+'**: '+card['description']]
guide += ['',lesson['mode_common_note'],'']
for t in tasks:
    guide += ['## '+t['id']+' - '+t['title'],'', 'Purpose: '+t['purpose'],'',
              'Core time: review '+str(t['minutes'])+' minutes; practice '+str(t['practice_minutes'])+' minutes.','']
    for mode in ('review','practice'):
        guide += ['### '+mode.title()+' path','']
        for s in t['paths'][mode]:
            guide += ['#### '+s['id']+' - '+s['title'],'', 'Logic: '+s['logic'],'', 'Explanation: '+s['explanation'],'']
            if s.get('slide_review'):
                slide=s['slide_review']
                guide += ['PPT page '+str(slide['primary_slide'])+': '+slide['title'],
                          'Show the original image: '+slide['image'], '', 'Guide attention through the slide:']
                guide += ['- '+item for item in slide['visual_walkthrough']]
                guide += ['', 'Plain-language explanation: '+slide['explanation'],
                          'Concrete example: '+slide['example'],'Bridge to code: '+slide['code_bridge'],'']
                if slide.get('provider_note'):guide += ['API mapping note: '+slide['provider_note'],'']
            for r in s['code_refs']:
                guide += ['- Read '+r['pack']+'/'+r['file']+' -> '+r['symbol']+'; start at symbol offset '+str(r['slice_start'])+', show at most '+str(r['max_lines'])+' lines. Resolve current source lines; do not invent line numbers.']
            if s.get('check'):
                q=s['check'];guide += ['', 'Required short check: '+q['prompt']]
                guide += ['- '+key+': '+value for key,value in q['options'].items()]
                guide += ['Save the actual response with lesson-answer. Resolve an incorrect answer with the two-hint policy before lesson-next. Do not reveal the answer immediately.']
            guide += ['']
    if t.get('timing_blocks'):
        guide += ['### Timing inside this task','']
        guide += ['- '+str(block['minutes'])+' min: '+block['title'] for block in t['timing_blocks']]
        guide += ['']
    guide += ['### Exercise, run and check','',
              'Before execution: explain the task and purpose, then ask what the learner expects. Save student code from chat. Obtain approval for live requests within the stated limit.',
              'After execution: open the current run report, distinguish expected values from observed results, explain fields and errors, then ask each understanding question separately.',
              'If an answer has been shown, ask: "Please explain that in your own words before we continue."','']
(ROOT/'TEACHING.md').write_text('\n'.join(guide),encoding='utf-8')
assert sum(t['minutes'] for t in tasks)==sum(t['practice_minutes'] for t in tasks)==100
assert sum(t['minutes'] for t in tasks[:5])==sum(t['practice_minutes'] for t in tasks[:5])==50
print('Built Week 3: 100 minutes, 100 percent, two study modes, four code TODOs.')
