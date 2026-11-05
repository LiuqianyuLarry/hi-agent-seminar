# Week 4: build a loop you can check and stop

This folder contains the completed lecture reference. The seminar makes a separate copy for opening demonstrations, so these demonstrations can run before students finish the exercises. Student work belongs in the resources workspace.

The task is to read CONV-3 temperatures, read its reference limit, calculate the share of readings above that limit, and explain the result using saved evidence. These are synthetic classroom readings, not a diagnosis of real equipment.

## Start here

Use the seminar plugin to work through one step at a time. It explains each task before running it and helps you read the actual result afterwards. The Review route starts with the lecture figures and the problem each part of the loop solves. Practice starts with the exercise and supplies the explanation you need.

Do not run every command at once. The four exercise groups below are complete in this reference. They begin unfinished in the student workspace, where a `NotImplementedError` marks an exercise.

| Exercise | Function | Your part |
| --- | --- | --- |
| W4.1 | `state.py: State.record` | Give each observation an ID and save a separate copy of its inputs and result. |
| W4.2A / W4.2B | `verification.py: verify` and `statistics_inputs_match` | Choose the required evidence, then check that the calculation used its actual values and limit. |
| W4.3 | `controls.py: stop_reason` | Return the reason why an unfinished run must stop. |
| W4.4 | `runtime.py: complete_tool_step` | Execute one tool action, send the result back, and update the evidence check. |

The existing `run_agent` keeps the error and handoff branches. Read them with your mentor; you do not need to rewrite the whole function to connect the three operations in W4.4.

W4.2 has two small function bodies in the same 15-minute slot. Its comparison includes a different input list with identical returned statistics, so checking only counts or summary numbers cannot pass.

## What runs locally

Core coding uses a scripted planner and real local tools. It tests your program, not LLM planning accuracy. The first API experiment can use a saved real teacher capture. The plugin labels that route `recorded_live`: the request happened earlier, not on your computer now. A scripted response is never substituted for that record.

A live experiment needs a private DeepSeek key and an explicit live choice. It does not fall back to a script if the API fails. The full live loop accepts one action per round as a teaching rule; the API itself can propose multiple tool calls. The opening one-shot experiment inspects every returned call.

No GPU, MCP server or agent framework is required. Read SETUP.md before preparing the environment.

## Results worth keeping

`run.json` contains the status, reason, counts and trace. `report.json` contains checked facts and their evidence IDs. `trace.jsonl` is the event sequence. `comparison.csv` lets you compare stopped and completed runs. `handoff.json` names the missing information when a person needs to help.

A recorded observation is not automatically valid evidence. Read `ready` and `missing` in the verifier result. A `status: ok` tool response does not prove that it used the right numbers for this task.

Your seminar progress, answers, code and run files can be saved and resumed by the plugin. The small agent inside this exercise does not yet have cross-process checkpoint recovery. After a handoff, confirm the task and start a new agent run; Week 5 studies resuming an interrupted execution.
