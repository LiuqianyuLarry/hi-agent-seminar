# MCP: from a working local tool to a shared connection

Required in BOTH Review and Practice modes before t08 coding. Use this as a
reference, not a single message to paste into chat. Teach the saved small lesson
nodes one at a time. Allow about 14 minutes for the introduction and 14 minutes
for the wrapper and real client/server test. Follow PRESENTATION.md: logic first,
then the relevant actual source excerpt, then one concrete example or question.

## 1. Start with a working application: do we need MCP yet?

Our application already has a Python function that reads CONV-3's registered
reference value. DeepSeek can propose that function through function calling,
and Executor can run it directly. This is a valid design.

Say clearly: "For one small application with a few local functions, direct
function calling may be enough. You do not have to use MCP."

Now add a second assistant application that needs the same tool. Without a
shared interface, both applications may need their own connection code and
copies of names, argument rules and error handling. As these copies change,
they can disagree. MCP offers a common interface through which an application
can discover and request capabilities provided by another program.

MCP stands for Model Context Protocol. A protocol is an agreed format and
sequence for messages. MCP is not a model, training method or database. It does
not make a function more intelligent or eliminate the need to implement it.

Show the repository connection: resources/tool_definitions.py currently builds
a local catalogue. MCPBackend.definition instead asks a connected provider for
its available tool metadata. This example still deliberately accepts only the
specification tool; discovery is not permission to execute every returned name.

Check with a card: "One script imports two local functions. Must it use MCP?"
The useful explanation is no: add MCP when sharing and a common connection are
worth the additional server/client machinery.

## 2. Separate model requests from application-to-tool messages

Function calling and MCP cover different connections:

| Connection | What is happening? | Our code |
|---|---|---|
| Application to DeepSeek | Send the question and tool descriptions | workflow.run_turn |
| DeepSeek to application | Propose a function name and JSON arguments | message.tool_calls |
| Application to tool provider | Discover or call a tool through MCP | MCPBackend |
| Application to DeepSeek | Return the actual tool result with its call ID | role=tool message |

The same logic can use a local function or an MCP server:

```text
User question -> DeepSeek proposes a tool call
             -> Application validates the request
             -> Local Python function OR MCP client -> MCP server -> Python function
             -> Actual result returns to the application
             -> Application returns it to DeepSeek
             -> DeepSeek explains it; the user checks the evidence
```

First point to the model/application boundary, then the application/tool boundary.
Do not introduce all arrows at once. Function calling does not run Python in the
model. MCP does not choose the user's next action. Our application connects those
parts and retains responsibility for validation, permissions and final checking.

A plain MCP client can test the server without any model. Equally, the application
can use function calling without MCP by invoking local Python. These are practical
reasons to test the parts separately, not competing standards to choose between.

## 3. Host, Client and Server: three roles, one laptop

A Host is the whole assistant application. It handles the user, calls DeepSeek,
chooses which tool definitions to offer, and applies its access rules. In our
seminar, app.py is the host entry and Executor performs the controlled dispatch.

A Client is the part that speaks MCP to one server. MCPBackend owns an SDK Client.
It opens the connection, lists tools and sends a request for get_machine_spec.

A Server is a running program that offers capabilities through MCP. Our
mcp_server.py wraps the existing specification reader. The server can be local;
"server" does not mean a cloud machine. DeepSeek's model API is a separate remote
service. This exercise needs no GPU.

If process or async syntax is unfamiliar, offer the processes foundation card.
Explain only what is needed: a process is a running program; await waits for a
reply; async with opens the connection for a block and closes it afterward.

Our transport is stdio: the client starts a local server process and exchanges
protocol messages through its input/output streams. No HTTP port is required.
The server reserves stdout for protocol messages. Send diagnostic messages to
stderr. A server launched alone may wait quietly because no client has asked it
anything yet; waiting is not evidence that a tool call succeeded.

Show server_parameters(): it passes a small environment-variable allowlist and
does not deliberately forward DEEPSEEK_API_KEY. This reduces credential exposure.
Do not teach "independent process = independent permissions". A process launched
as the same user may still access the same files. Stronger isolation requires
separate operating-system controls. This environment control is our application
choice, not an automatic MCP guarantee or an ability unique to MCP.

## 4. Discover first, then adapt and offer the tool to the model

Show the actual code from resources/mcp_backend.py's MCPBackend.definition and
lecture_demo/check_server.py in small fragments. list_tools asks "What capabilities
do you offer?" Its reply contains
names, descriptions and input schemas. It does not execute every tool or return
all sensor data.

call_tool asks to run one named capability with one argument object. Trace
get_machine_spec and {"machine_id":"CONV-3"} through that request. The name
identifies the registered operation; the dictionary supplies its input value.

Discovery alone does not make a tool visible to DeepSeek. The host takes the MCP
input_schema and adapts it into DeepSeek's nested function.parameters structure,
then attaches that definition to a model request. This is the role of
adapt_spec_tool(). Read its checks before its return statement:

- Accept only the supported name and the expected machine_id property.
- Require the supported simple string schema; stop on unsupported references,
  alternative schemas or default argument values rather than guessing a conversion.
- Preserve the supported constraints and use the local executor for actual
  argument validation, even after the schema has been offered to the model.

A schema describes structure. It does not prove that the user meant CONV-3 rather
than CONV-7. The application and student must still compare the request with intent.
Do not describe this small adapter as a universal security audit for every MCP
schema; it intentionally supports a limited teaching case.

Check: "We have listed a tool. Can DeepSeek use it automatically now?"
The missing step is the host adapting and including an approved tool definition
in the model request. The host must also connect that name to an execution route.

## 5. Read the server wrapper before writing one

First show the completed lecture example, or the equivalent selected fragment
from the seminar starter in Practice. Keep registration and function body in
separate small excerpts. The current seminar source uses:

```python
@server.tool(structured_output=True)
def get_machine_spec(machine_id:Annotated[str,Field(pattern=r'^CONV-[0-9]{1,3}$')])->dict[str, Any]:
```

The decorator registers a capability; it does not execute it immediately.
structured_output=True requests structured output from the SDK. The return type
dict[str, Any] describes a dictionary with string keys and values of different
types. In this pinned SDK, it helps generate the structured result contract.
Do not substitute the older bare dict example: that example produced text-only
output in our previous test and did not satisfy the client's contract.

Explain the argument annotation separately. machine_id is the input name, str is
its basic type, and Field(pattern=...) states the accepted ID format. The full
code also validates actual arguments with SpecArgs. Ask for a foundation example
if the notation is unfamiliar; do not turn it into an annotation-syntax quiz.

The import alias `get_machine_spec as read_spec` gives the existing reader a new
local name. The wrapper then calls read_spec instead of accidentally calling
itself. We keep one function responsible for the register; the MCP wrapper adds
a connection, not another copy of the business logic.

Known business errors become ToolError so the client receives an explicit tool
error. A successful-looking result containing the word "error" is not equivalent.
The student completes this small wrapper after the explanation, not an entire
server framework.

## 6. Explain the returned object, not just the printed text

Inspect a real direct client result before using a model:

| Field | Meaning |
|---|---|
| is_error | The SDK's tool-error flag |
| structured_content | The structured object returned by the tool |
| status, data | Our course envelope says whether usable business data exists |
| source, version, error | Provenance or structured error details in our envelope |

A text block containing JSON characters is still text; it does not prove that
structured_content is populated. The host checks the field it actually requires.
Do not teach our envelope as a universal MCP format. The lecture uses ok/data/error
with source information; the seminar uses status/data/source/version/error.
Explain this mapping when transferring from the lecture demo.

Test a known machine and an unknown machine. Separate a connection failure,
a protocol/schema failure, a tool/business failure and a wrong final answer.
An error at one layer should not be disguised as success at another. External
tool content is evidence, not authority to override host instructions.

## 7. Tools, resources and context

A tool is an operation invoked with arguments through tools/call. A resource is
content read through the resource interface. The distinction is not "tools write,
resources read": our specification tool is read-only.

Read manual://CONV-3/temperature explicitly to illustrate a resource. The client
receiving that text does not automatically put it into DeepSeek's context. The
host must select and include it. Resource reading alone is not a complete RAG
system. Keep this explanation brief in core; further resource work is optional.

## 8. Compare local and MCP routes without overstating the experiment

Use the same CONV-3 specification question through --route local and --route mcp.
Inspect the tool name, argument schema and description offered to the model, then
inspect the executor route and returned data. Expected business capability and
results should agree; the application-to-tool connection is different.

Do not claim the model sees identical inputs merely because the question matches.
The local description/schema and the discovered, adapted definition can differ.
Show those differences. If a later controlled comparison needs identical tool
metadata, normalize the approved definitions first and verify structural equality.
Likewise, model answer wording can vary even for the same data.

The learning conclusion is that MCP provides a common connection to an existing
capability. It does not supply intelligence, grant permissions, guarantee correct
arguments or prove a final answer true. Its benefit must justify its integration
cost for the particular application.

## 9. Begin the wrapper exercise

Restate the task: "Wrap the function you already tested, connect a real client,
and check a known and an unknown machine. We do not need a model call yet."
Record the completed introduction only after presenting its lesson nodes in the
selected route. Save the student's wrapper body from chat, obtain a prediction,
run t08, read the report and explain the observed fields before the final check.

The four short MCP checks must be resolved before the wrapper exercise. Give
two gradual hints when needed; if the learner requests an answer explanation,
ask for their own explanation and confirm understanding before proceeding.
