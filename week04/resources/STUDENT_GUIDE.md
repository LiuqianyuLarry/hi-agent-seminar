# Work through the four exercises

Before each exercise, explain what you think will happen. Write your small code attempt in chat if that is easier; the mentor can save your exact text. Run the test for this exercise, read the result, and explain what it shows before moving on.

## W4.1: keep a record

`State.record` receives the tool name, the arguments, the result and a flag saying whether a result was reused. Build an Observation, append it to the state, and log the event. Use a separate copy for nested inputs and results so later edits cannot change old evidence.

Check with `python check_tests.py -q tests/test_state.py`.

Explain what an observation ID lets you check. Then change the original dictionary and inspect the stored observation. What stayed the same?

## W4.2: check the goal and the calculation inputs

This is one 15-minute exercise with two short code parts. Page 9 asks what evidence finishes the task. Page 14 asks whether a calculation actually used that evidence. Both checks matter.

### W4.2A: choose what this goal needs

Complete `verify`. A spec task needs a specification. A readings task needs the query result, even if it is empty. A report needs a specification, nonempty readings and matching statistics. Record what is missing and return a Check. No readings does not mean that zero percent exceeded the limit.

`matching_sources` finds the recorded specification and readings. `matching_stats` keeps the numerical checks already supplied, but its input check still needs your W4.2B function. Do not remove those other checks to make a test pass.

### W4.2B: check where the numbers came from

Complete `statistics_inputs_match`. It receives an observation, the temperature values from the saved query, and the limit from the saved specification. Compare the observation's complete argument dictionary with those two observed inputs. Return False when they differ and True when they match. Do not replace this check with a comparison of list lengths or counts.

Here is the difficult case: the recorded readings are `[82, 87, 91, 94, 97]`, but a calculation uses `[82, 88, 90, 94, 97]`. Both lists have five values. They also have the same mean, maximum and share above 85. Correct output statistics alone cannot tell you which list was used.

Before running, predict the decision for matching inputs, a two-value list, the different five-value list, and the wrong limit. Explain which comparison your code needs to make.

Check both parts with `python check_tests.py -q tests/test_verification.py`. The mentor then runs the local comparison and explains `comparison_rows`: `arguments` are the inputs actually supplied, `tool_statistics` are the returned numbers, `inputs_match` is your new check, and `check.ready` is the overall task decision.

Find the row where `same_summary_as_correct` is True but `inputs_match` and `check.ready` are False. Explain why rejecting that row is correct. Then compare an empty readings goal with an empty report goal.

## W4.3: stop an unfinished run

Use `stop_reason` to inspect the run time, decision count, reported-token threshold and repeated lack of progress. Return a reason or None. Do not turn a limit into a success status. The runner separately limits actual attempts and individual tool timeouts.

Check with `python check_tests.py -q tests/test_controls.py`.

Explain the difference between decision steps, actual tool attempts and repeated rounds without new evidence.

## W4.4: connect one tool step

Read `request_action`, the start of `run_agent`, and the error branches. Complete only `complete_tool_step`. It receives the existing state, action, planner, runner and configuration. Run the tool through the runner, return the actual result to that same planner, update the check and return the observation and check.

Check with `python check_tests.py -q tests/test_runtime.py`.

Explain why completion is checked before asking for another action. Then run the normal task and locate the first event that shows enough evidence has been collected.

## Read what happened

The normal scripted path should use the three domain tools. That is a result to check, not a fixed requirement for every possible goal. A spec-only task can finish after one useful tool result.

Use `python app.py --mode scripted --out outputs/normal` only after the exercises are complete. The plugin normally runs this in a separate experiment folder and reads the report with you.

For the comparison, use `python demos.py --case compare --out outputs/comparison`. This keeps finite limits. Never remove every stop mechanism or run an unlimited live loop.

If a test times out, the external watchdog stopped it. That does not prove your loop implemented its own stop correctly.

## When you get stuck

Ask for a hint. You will get a small hint, a chance to try, then a clearer hint if needed. After two hints you can choose more help or an explanation of the answer. If you choose the explanation, explain the idea in your own words before continuing.

Use the reflection command for three short reflections and a saved code snapshot. A break, a translation request or a look at an earlier task does not count as completing a new learning step.
