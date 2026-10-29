# CONV-3 student starter

Read SETUP.md, then let the seminar mentor guide one task at a time. Four TODOs:
tools/calculation.py, tools/engineering.py, tools/sql_query.py and mcp_server.py.
Write the requested function body in chat; the mentor saves your words as code.
Do not paste credentials into chat. Every interaction is in English unless you
explicitly request a translation.

The three tools respectively summarise supplied readings, read a registered
reference value and query historical measurements. They have different purposes.
Their common envelope is status, data, source, version and error. Read each
tool's data fields separately. Measurements and registered limits are not equal
concepts, even when their numeric values happen to match.

After coding, use `python -m pytest tests/test_tools.py -q` for local tests.
`tests/test_workflow.py` tests the DeepSeek message contract using scripted
responses. `tests/test_mcp_integration.py` starts a real subprocess; it explicitly
skips when the required SDK is absent. The seminar runner checks the SDK first
so a skipped integration test cannot earn task completion.

Keep this workspace when updating the plugin. Use Continue saved progress,
Start again in a separate session, or revisit an earlier task. Restart never
overwrites earlier code. Optional seven-case evaluation and boundary tests do
not change core progress. There is no external submission service.
