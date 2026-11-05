# Set up the existing environment

Use Python 3.11 or later. Reuse an environment that already has Pydantic 2 and pytest. The mentor checks it first; nothing downloads automatically.

If those packages are missing, use a suitable local environment and install requirements.txt after reviewing what is needed. The OpenAI Python SDK is only a client library for the optional DeepSeek requests; this course uses the DeepSeek endpoint.

Run these from the resource folder:

```text
python build_data.py
python preflight.py
```

The first command creates a local SQLite database from the supplied CSV. It checks the supplied data hashes and does not replace an existing database with a different source version. The second checks required imports and data. It does not require unfinished student tests to pass.

On Windows, you can use the full path to an existing environment's python.exe. There is no need to change PowerShell policy just to activate it.

## Optional live requests

Use requirements-live.txt only if the SDK is missing. Store your key privately using `python provider.py`, or set DEEPSEEK_API_KEY in your local environment. Do not paste a key into chat, source files or a report. DEEPSEEK_MODEL chooses the model; the supplied default is deepseek-flash.

The client disables hidden SDK retries. Each request has a timeout; the full loop also checks decisions, attempts, elapsed time and reported token usage. A response can cross the token threshold before its usage is known, so that threshold is not a prepaid spending cap.

The teacher-record route makes no API request. Check the record's response ID, capture time, model and original request before describing it as a saved real experiment.
