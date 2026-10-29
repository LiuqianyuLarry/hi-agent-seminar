# Prepare the existing environment first

Python 3.11+ is required. No GPU, CUDA or PyTorch is needed. Inspect an existing
environment with `python preflight.py` before installing anything. Do not alter
an unrelated environment just to make this exercise run.

If a new environment is needed, create it in your student workspace:

```text
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-live.txt -r requirements-mcp.txt
```

On macOS/Linux use `.venv/bin/python` in place of `.venv/Scripts/python.exe`.
Tell the mentor which interpreter to verify with the setup helper. Then run:

```text
python build_data.py
python preflight.py
```

These commands generate 109 synthetic rows and inspect package versions. An
existing database is preserved unless --force is explicitly selected. The
four TODO functions are intentionally incomplete; full tests will fail until
you complete them. Do not treat that initial failure as an installation error.

For live exercises, privately run `python provider.py` in your own terminal.
It uses hidden input to save DEEPSEEK_API_KEY locally in .env. Never paste the
key into chat, a notebook cell, a report or a repository. An existing .env is
not overwritten. You can also use a private environment variable.

The service is https://api.deepseek.com. The OpenAI Python SDK is used only as
the compatible client; no OpenAI account or OPENAI_API_KEY is used. The default
model is deepseek-flash, configurable with DEEPSEEK_MODEL. Thinking is disabled
for this small teaching flow. Model availability and usage depend on your account.

```text
python app.py --mode replay --case spec
python app.py --mode live --case spec
python app.py --mode live --route mcp --case spec
```

Replay is explicit, with scripted model decisions and final text. It runs real
local tools, but does not count as a real DeepSeek call. A live failure never
falls back to replay. The standard endpoint uses no beta strict-generation flag;
the executor validates input types, ranges and permissions before execution.

MCP is pinned to the official Python SDK 2.2.0. Do not mix v1 and v2 examples.
After the wrapper is complete, `python mcp_client.py --read-resource` starts a
real local server subprocess. It does not call a model or open an HTTP port.
