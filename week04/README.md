# Week 4: build an agent loop

In Week 1, the local program learned to exchange messages with an LLM. In Week 3,
it learned how to check and run a tool request. This week we connect those actions
into a task that needs several pieces of evidence.

The example is CONV-3's temperature report. We need the readings, the registered
reference and a calculation using both. Then we need to check whether the task
is complete and whether another attempt is allowed.

## Choose how to begin

- **Review lecture + code:** follow the problem from the lecture, see how a small
  loop can repeat or finish too soon, explain the diagrams and actual code, then
  complete the exercises.
- **Start seminar practice:** begin with the same experiments and small coding
  tasks. Ask for a short explanation or an example when you need one.

Both paths have two 50-minute sessions. The break is outside those 100 minutes.
Before a foundation explanation you can choose **I understand - continue**,
**Explain briefly** or **Show an example**. Skipping a refresher does not skip the
exercise or its understanding check.

## What you will build

You work through four exercise groups. W4.2 contains two short function bodies:

| Task | What your code does |
| --- | --- |
| W4.1 `State.record` | Keeps an observation with an ID and independent copies of its inputs and result. |
| W4.2A `verify` | Checks which evidence this task requires and what is still missing. |
| W4.2B `statistics_inputs_match` | Checks that the calculation used the saved readings and their registered limit. |
| W4.3 `stop_reason` | Reports a limit that prevents another attempt. |
| W4.4 `complete_tool_step` | Connects tool execution, feedback and a new evidence check. |

W4.2 keeps its 15-minute slot. Page 9 supplies the task checklist; page 14 asks
whether a calculation really used the required inputs. You write both checks,
then test a case in which different values produce the same summary. Counting
readings or checking the mean alone cannot establish which inputs were used.

The existing runtime keeps the surrounding error branches and checks. You do not
need to write an agent framework, retrain a model, or set up another MCP server.

The starter intentionally contains TODOs. Some initial tests will fail because
those exercises are unfinished. That is different from a broken Python setup.
We test each part after you save your own attempt.

## What the experiments show

The opening experiment inspects one real DeepSeek request, either live or from a
saved teacher exchange. A response can propose zero, one or several tool calls.
The application still has to execute local tools and return their results before
a later model decision can use them. Three domain tools plus a checked report do
not necessarily mean four function calls.

The repeated-action and early-finish demonstrations use deliberately scripted
faults. Their local tools really execute, but the next actions are supplied by a
rule program. These experiments test the controls, not an LLM's accuracy or its
usual error rate. An outside limit contains every teaching experiment.

After the exercises, your own saved code runs the normal task and the stopping
comparisons. Read the actual `status`, `reason`, decision count, tool-attempt
count and evidence IDs. A successful test process does not make every simulated
task ending a success.

## What you need

Use an existing compatible Python environment when possible. The core local work
needs no GPU. A genuine saved teacher API exchange lets you complete the opening
analysis without a personal API key. A live run needs your explicit choice and a
privately configured DeepSeek key. A failed live request is not silently replaced
with scripted output.

The reference demonstrations use a separate completed copy. Your starter files
keep their TODOs until you write them. Generated databases and experiment outputs
belong in the learning workspace, not in the plugin distribution.

## Keep or revisit your work

The seminar saves your location, answers, hints, code and experiment records.
Continue in the same learning folder when you return. Starting again creates a
separate session; it keeps the earlier records and code. A saved older Week 4
lesson continues with its own snapshot. Choose a new session to try the revised
two-part W4.2 exercise. You can revisit an earlier
step without being pushed back to the next unfinished task.

This seminar save feature is separate from the agent's execution State. The small
agent in this week's exercise does not resume a half-executed run after its process
closes. Week 5 covers execution checkpoints and recovery.

Optional topics are in the course menu: a live DeepSeek loop, retries, tool
timeouts, human handoff, a fixed workflow comparison and extra boundary tests.
They do not change your core completion percentage. The existing review command
can save three longer reflections and a code snapshot after the lesson.
