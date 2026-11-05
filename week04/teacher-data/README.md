# A real one-response experiment

This is a saved DeepSeek call made for Week 4. The model requested both `get_machine_spec` and `query_temperature` in one response. The local program ran those requests. The verifier still reported `stats` as missing. The results were not sent back to the model in a second request.

This record shows why this task needs another turn. It also shows that a response can contain more than one tool call. It does not show that every task needs the same number of turns.

When students inspect this record, no API request is made. The seminar labels this as `recorded_live`. A fresh student call, chosen with their approval, is labelled `live_deepseek`. Other failure demonstrations use labelled scripted choices and real local tool execution.

`single_round.json` includes the public request, response, allowed local tool results, verifier checks and source hashes. It contains no API key or private reasoning trace. `SOURCE.json` records its SHA-256 hash. Keep these files together.
