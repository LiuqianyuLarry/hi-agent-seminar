# CONV-3 classroom demonstrations using DeepSeek

Install requirements.txt in the selected environment. Generate synthetic data
with `python data/build_data.py`. This rebuilds only the bundled classroom
maintenance database. The register already contains CONV-3 and CONV-7.

```text
python demo.py
python demo.py p5
python demo.py p9
python demo.py p12 --mode replay
python demo.py p12 --mode live
python demo.py p37 --mode replay
python demo.py p37 --mode live
python check_server.py
```

p3, p12 and p37 require an explicit execution mode. Live calls use only DeepSeek,
configured privately through DEEPSEEK_API_KEY and optional DEEPSEEK_MODEL. The
default model is deepseek-flash; thinking is disabled. No live failure triggers
a replay fallback. The OpenAI SDK is a compatible HTTP client, not the provider.

The wire format is Chat Completions: nested function definitions, assistant
tool_calls and role=tool results with a matching tool_call_id. The application
rejects multiple calls before execution. Local Pydantic checks remain mandatory;
this standard endpoint configuration does not enable beta strict generation.

The supplied PPT may show a provider-neutral or Responses-style call diagram.
Explain the conceptual correspondence and use these source files for the actual
DeepSeek field names. The existing PPT file itself has not been rewritten.

Lecture maintenance records and seminar temperatures describe the same CONV-3,
but remain separate datasets. No causal link between maintenance and temperature
is established by these synthetic examples. The lecture envelope uses ok/data/error;
the seminar envelope uses status/data/source/version/error. Neither is a universal
MCP or model-provider standard.

MCP is the official Python SDK 2.2.0. The server uses an explicit structured return
type. check_server.py tests a real local subprocess without requesting a model.
Keep stdout for protocol traffic and use stderr for server diagnostics.
