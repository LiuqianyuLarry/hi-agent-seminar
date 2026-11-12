# Week 5 teaching script

Use the current installed OUTPUT.md, persona.md and MENTOR.md. Share the instructor’s note first, then read the travel story in order before introducing the terms. Keep the student-facing teaching and code in English except for the two exact bilingual Redo cues. Deliver both cues in the student reply in either mode. The music link is optional.

Offer Review lecture + code and Start seminar practice. Give the current step, show the actual code in the reply, and wait for the learner to predict, write code or interpret a run. In Review use the listed v3 slide before the matching source excerpt if it is visible. Always explain the concept in complete English sentences so the learner can follow without the figure. In Practice start with the current problem. Both routes include the four-minute opening map before any source excerpt. Use the source windows returned by the current helper response. Extra excerpts are for questions.

Use the three concept choices before the relevant exercise. Give two progressively clearer hints with real attempts between them, then offer more hints or an explanation. Ask for an own-words explanation before continuing after an answer has been explained.

Read the actual result for the current run before explaining it or asking its interpretation. Save the evidence explanation and learner answer. Use the helper's saved core_percent. Questions, translations and revisits do not advance the current step.

Use a verified Python environment. Run the Crash, Decide and Redo comparisons locally. In each comparison preserve the listed settings and change the designated strategy or policy. Use genuine LangGraph and SQLite for the workflow. Start, inspect and continue from separate processes. The seminar progress file tracks learning and is separate from the workflow checkpoint.

In the first session a rule simulates planning so that everyone can repeat the experiment. In the second session the CONV-3 workflow runs the actual local graph and SQLite checkpointer.

## Session 1 (50 minutes)

### t01 Crash and checkpoint (11 minutes)

Compare starting again with restoring state and the next step.

#### Review

**Pick up the booking after a restart**

Hi everyone. By the time you open this plugin, I’ll probably be on my way to a meeting. I had a bit of brain fog in yesterday’s lecture, and some of my explanations came out in bits and pieces.

I went back over the material afterward and put it in a clearer order for this seminar. By the end, I hope you’ll have picked up a few of my moves and can use them on your own. All right. Time to pass on a little kung fu.

Think back to where we started. In Week 1, we got Python to call a language model and learned how to check its answers. In Week 2, we built a small model to see how it makes predictions. In Week 3, we gave the model tools. Last week, we put those tools in a loop so the agent could take several actions, check what happened and decide when to stop.

Now give that agent a bigger job. Find me a flight, use its dates to look for a hotel, ask me to approve the plan, make the bookings and send a confirmation. Each step uses something the previous step found or decided.

Suppose the agent finds a 9 a.m. flight and is about to look for a hotel when Python crashes. If we used last week’s loop for this job, the selected flight and the next step would live in that Python process’s memory. When the process closes, those values are gone. Even with the original request, the new process has to start the search again.

This week, we’ll give the workflow a set of named steps and save its progress to disk. A state machine organizes the steps and the routes between them. After each completed step in our workflow, we’ll save what the program knows and where it should continue. That saved record is called a checkpoint. If Python stops again, the next process can load the selected flight from disk and go straight to looking for a hotel.

**State: what do we know?** The workflow keeps the flight, dates and any reply in its state. When the flight search returns a flight, the workflow adds it to that record. Without the dates, the hotel search cannot pick the right nights.

**Node: who does the work?** The flight search is one node. It takes what it needs from state and returns an update, such as the selected flight. If it returns an empty update after a successful search, the hotel step cannot see what it found.

**Edge: where do we go?** The graph follows an edge to the next node. A routing function can send a sold-out flight back to search. A fixed edge to payment would send a rejected request there too.

**Checkpoint: what survives a crash?** The checkpointer saves the state and the pending step together. In the second session it writes to SQLite. If we reopen that file for the same workflow, the new process can use the saved flight and `next` step. Without that save, the new process cannot recover them.

**Interrupt: where do we wait for a person?** The approval node asks for a decision and pauses at that request. The saved workflow stays there until a reply arrives. If we leave out the pause, the program may carry on before anyone has approved the booking.

There is one more problem. A crash can happen after the provider charges you but before our checkpoint advances. The saved position tells the workflow which step to try again. The provider needs a stable request number so it can find the old receipt and avoid a second charge.

```text
Find a flight -> Look up a hotel -> Wait for approval (interrupt)
                                   | approved -> Book -> Send confirmation
                                   | rejected -> Finish

Forgot the flight?      State stores it.
Need a different step?  A routing function chooses an edge.
Python closed?         A checkpoint stores the flight and the next step.
No decision yet?       The interrupt keeps the workflow waiting.
Already charged?       The provider checks the same request number before charging.
```

The workflow found a flight and then Python closed. Which part gives the new process the saved flight and the pending step?

**Crash and checkpoint**

Related lecture slides: 6, 5, 8.

The while loop keeps its position in a local variable and starts at the first step after a failure. The graph reads the pending step from the saved `next` field. A simulated failure can occur before an action or just after it, before `next` is saved.

**Question.** How much work does restarting repeat? Can the workflow still pay twice after it has saved a checkpoint?

**Setup.** Run 2,000 trips with seed 7 and the same nine-step booking task and 10 percent failure chance. The fixed settings make the comparison repeatable, and many trips give us an average across failures at different steps. This experiment stores checkpoints inside the simulation. We will close a real Python process and reopen SQLite later.

**Results to read.** `mean_steps` and `mean_restarts` show the cost of redoing work. `extra_charges` shows what was charged again at the provider.

`experiments/crash.py` · `agent_loop`

```python
def agent_loop(world, trip, checkpoints):
    state, position = {"request": REQUEST}, 0
    while position < len(ORDER):
        state.update(step(world, ORDER[position], trip, state))
        position += 1
    return state
```

The local position starts at zero every time the function is entered. An exception ends that attempt before the position is returned.

`experiments/crash.py` · `agent_graph`

```python
def agent_graph(world, trip, checkpoints):
    if trip in checkpoints:
        state = json.loads(checkpoints[trip])
    else:
        state = {"request": REQUEST, "next": ORDER[0]}
    while state["next"] != "END":
        node = state["next"]
        state.update(step(world, node, trip, state))
        state["next"] = EDGES[node]
        checkpoints[trip] = json.dumps(state)
    return state
```

The next node comes from the saved dictionary. The code saves the new state and advances next only after the call returns.

Additional source on request.

`experiments/crash.py` · `step`

```python
def step(world, node, trip, state):
    world.steps += 1
    draw = world.rng.random()
    if draw < FAILURE_RATE / 2:
        raise Crash("before action")
    update = NODES[node](world, trip, state)
    if draw < FAILURE_RATE:
        raise Crash("after action, before checkpoint")
    return update
```

A simulated exception can happen on either side of the action. When it happens after the action, the outside effect can already exist.

Predict which strategy will execute more steps and whether a saved checkpoint can still leave a repeated booking.

**Read the actual result**

Related lecture slides: 7, 8.

Compare the two rows using `mean_steps`, `mean_restarts` and `extra_charges`. Explain how one row can have fewer repeated steps and still have extra charges.

With an independent 10 percent chance of failure, each step succeeds with probability 0.9. The checkpoint version needs about 9 / 0.9 = 10 attempts. Starting over needs a run of nine successes and takes about 15.8 attempts. Compare these estimates with your own run.

A checkpoint can save repeated work. A booking may still have happened before the latest save.

How did saving state and next change the rerun cost? Why can a repeated booking remain?

#### Practice

**Pick up the booking after a restart**

Hi everyone. By the time you open this plugin, I’ll probably be on my way to a meeting. I had a bit of brain fog in yesterday’s lecture, and some of my explanations came out in bits and pieces.

I went back over the material afterward and put it in a clearer order for this seminar. By the end, I hope you’ll have picked up a few of my moves and can use them on your own. All right. Time to pass on a little kung fu.

Think back to where we started. In Week 1, we got Python to call a language model and learned how to check its answers. In Week 2, we built a small model to see how it makes predictions. In Week 3, we gave the model tools. Last week, we put those tools in a loop so the agent could take several actions, check what happened and decide when to stop.

Now give that agent a bigger job. Find me a flight, use its dates to look for a hotel, ask me to approve the plan, make the bookings and send a confirmation. Each step uses something the previous step found or decided.

Suppose the agent finds a 9 a.m. flight and is about to look for a hotel when Python crashes. If we used last week’s loop for this job, the selected flight and the next step would live in that Python process’s memory. When the process closes, those values are gone. Even with the original request, the new process has to start the search again.

This week, we’ll give the workflow a set of named steps and save its progress to disk. A state machine organizes the steps and the routes between them. After each completed step in our workflow, we’ll save what the program knows and where it should continue. That saved record is called a checkpoint. If Python stops again, the next process can load the selected flight from disk and go straight to looking for a hotel.

**State: what do we know?** The workflow keeps the flight, dates and any reply in its state. When the flight search returns a flight, the workflow adds it to that record. Without the dates, the hotel search cannot pick the right nights.

**Node: who does the work?** The flight search is one node. It takes what it needs from state and returns an update, such as the selected flight. If it returns an empty update after a successful search, the hotel step cannot see what it found.

**Edge: where do we go?** The graph follows an edge to the next node. A routing function can send a sold-out flight back to search. A fixed edge to payment would send a rejected request there too.

**Checkpoint: what survives a crash?** The checkpointer saves the state and the pending step together. In the second session it writes to SQLite. If we reopen that file for the same workflow, the new process can use the saved flight and `next` step. Without that save, the new process cannot recover them.

**Interrupt: where do we wait for a person?** The approval node asks for a decision and pauses at that request. The saved workflow stays there until a reply arrives. If we leave out the pause, the program may carry on before anyone has approved the booking.

There is one more problem. A crash can happen after the provider charges you but before our checkpoint advances. The saved position tells the workflow which step to try again. The provider needs a stable request number so it can find the old receipt and avoid a second charge.

```text
Find a flight -> Look up a hotel -> Wait for approval (interrupt)
                                   | approved -> Book -> Send confirmation
                                   | rejected -> Finish

Forgot the flight?      State stores it.
Need a different step?  A routing function chooses an edge.
Python closed?         A checkpoint stores the flight and the next step.
No decision yet?       The interrupt keeps the workflow waiting.
Already charged?       The provider checks the same request number before charging.
```

The workflow found a flight and then Python closed. Which part gives the new process the saved flight and the pending step?

**Crash and checkpoint**

The booking program crashed. One version restarts from the first step. The other retrieves the saved task and runs its saved `next` step. Compare what they repeat.

**Question.** How much work does restarting repeat? Can the workflow still pay twice after it has saved a checkpoint?

**Setup.** Run 2,000 trips with seed 7 and the same nine-step booking task and 10 percent failure chance. The fixed settings make the comparison repeatable, and many trips give us an average across failures at different steps. This experiment stores checkpoints inside the simulation. We will close a real Python process and reopen SQLite later.

**Results to read.** `mean_steps` and `mean_restarts` show the cost of redoing work. `extra_charges` shows what was charged again at the provider.

`experiments/crash.py` · `agent_loop`

```python
def agent_loop(world, trip, checkpoints):
    state, position = {"request": REQUEST}, 0
    while position < len(ORDER):
        state.update(step(world, ORDER[position], trip, state))
        position += 1
    return state
```

The local position starts at zero every time the function is entered. An exception ends that attempt before the position is returned.

`experiments/crash.py` · `agent_graph`

```python
def agent_graph(world, trip, checkpoints):
    if trip in checkpoints:
        state = json.loads(checkpoints[trip])
    else:
        state = {"request": REQUEST, "next": ORDER[0]}
    while state["next"] != "END":
        node = state["next"]
        state.update(step(world, node, trip, state))
        state["next"] = EDGES[node]
        checkpoints[trip] = json.dumps(state)
    return state
```

The next node comes from the saved dictionary. The code saves the new state and advances next only after the call returns.

Additional source on request.

`experiments/crash.py` · `step`

```python
def step(world, node, trip, state):
    world.steps += 1
    draw = world.rng.random()
    if draw < FAILURE_RATE / 2:
        raise Crash("before action")
    update = NODES[node](world, trip, state)
    if draw < FAILURE_RATE:
        raise Crash("after action, before checkpoint")
    return update
```

A simulated exception can happen on either side of the action. When it happens after the action, the outside effect can already exist.

Predict which strategy will execute more steps and whether a saved checkpoint can still leave a repeated booking.

**Read the actual result**

Compare the two rows using `mean_steps`, `mean_restarts` and `extra_charges`. Explain how one row can have fewer repeated steps and still have extra charges.

With an independent 10 percent chance of failure, each step succeeds with probability 0.9. The checkpoint version needs about 9 / 0.9 = 10 attempts. Starting over needs a run of nine successes and takes about 15.8 attempts. Compare these estimates with your own run.

A checkpoint can save repeated work. A booking may still have happened before the latest save.

How did saving state and next change the rerun cost? Why can a repeated booking remain?

How did saving state and next change the rerun cost? Why can a repeated booking remain?

### t02 Decide who chooses the next action (7 minutes)

Compare the planning trade-offs on the same 30 tasks.

#### Review

**Decide who chooses the next action**

Related lecture slides: 11, 12, 14.

**Question.** We can pick up where we stopped, but what if the flight sells out before we can book it? The same next step now returns an error. Can the agent change its plan?

Reflex asks for one action and stops after running it. ReAct sees each tool result before choosing again. Plan-execute gets a list up front and can ask for a revised list if it hits an error and has replans left.

**Setup.** Run all three on the same 30 tasks with seed 7, first with normal availability and then with sold-out flights or hotels. Compare zero and one replan for plan-execute. The same tasks, seed and fixed decision rules let us repeat the comparison and see what changed when we allowed one replan.

**Results to read.** `completed` counts finished trips, `planning_calls` counts decisions, and `failed_with_bookings` counts unfinished trips that still booked something. Open `sample.tool_log` to see where a sold-out trip changed course.

`experiments/decide.py` · `reflex`

```python
def reflex(task, world, metrics):
    choice = ask(metrics, {"request": task["text"]}, find_flights(task))
    world.call(choice["tool"], choice["args"])
```

The policy asks for a single choice and makes one search. It has no loop for the next booking step.

`experiments/decide.py` · `react`

```python
def react(task, world, metrics):
    history = []
    for _ in range(12):
        prompt = {"request": task["text"], "history": history}
        choice = ask(metrics, prompt, rule(task, history))
        if choice["tool"] == "finish":
            return
        tool, arguments = choice["tool"], choice["args"]
        history.append((tool, arguments, world.call(tool, arguments)))
```

Each choice uses the current history. The tool result is appended, so the next choice can see whether it succeeded.

`experiments/decide.py` · `planexec`

```python
        if replans == 0:
            return
        replans -= 1
        prompt = {"request": task["text"], "history": history}
        steps = ask(metrics, prompt, replan(task, history))
```

Zero remaining replans means stop. With one left, spend it and ask for another plan using the recorded results.

Additional source on request.

`experiments/decide.py` · `planexec`

```python
def planexec(task, world, metrics, replans=0):
    history = []
    steps = ask(metrics, {"request": task["text"]}, plan(task))
    while True:
        for step in steps:
            tool = step["tool"]
            arguments = {key: resolve_argument(value, history) for key, value in step["args"].items()}
            result = world.call(tool, arguments)
            history.append((tool, arguments, result))
            if "error" in result:
                break
```

The planner supplies steps once. Before running a tool, resolve any argument that refers to earlier results. Stop the inner loop on an error.

What do you expect one replan to change when the first flight sells out?

**Read the actual result**

Related lecture slides: 15, 16.

Compare `completed`, `planning_calls` and `failed_with_bookings` for normal and sold-out trips. Use `sample.tool_log` to follow a trip where the first flight and the first hotel both sold out. See when ReAct sees each error and when plan-execute uses its one replan.

A plan saves decision calls when its assumptions hold. Replanning gives it another chance when they change.

Compare the zero and one replan rows. What changed in completed trips and why can a trip remain unfinished?

#### Practice

**Decide who chooses the next action**

**Question.** We can pick up where we stopped, but what if the flight sells out before we can book it? The same next step now returns an error. Can the agent change its plan?

Reflex asks for one action and stops after running it. ReAct sees each tool result before choosing again. Plan-execute gets a list up front and can ask for a revised list if it hits an error and has replans left.

**Setup.** Run all three on the same 30 tasks with seed 7, first with normal availability and then with sold-out flights or hotels. Compare zero and one replan for plan-execute. The same tasks, seed and fixed decision rules let us repeat the comparison and see what changed when we allowed one replan.

**Results to read.** `completed` counts finished trips, `planning_calls` counts decisions, and `failed_with_bookings` counts unfinished trips that still booked something. Open `sample.tool_log` to see where a sold-out trip changed course.

`experiments/decide.py` · `reflex`

```python
def reflex(task, world, metrics):
    choice = ask(metrics, {"request": task["text"]}, find_flights(task))
    world.call(choice["tool"], choice["args"])
```

The policy asks for a single choice and makes one search. It has no loop for the next booking step.

`experiments/decide.py` · `react`

```python
def react(task, world, metrics):
    history = []
    for _ in range(12):
        prompt = {"request": task["text"], "history": history}
        choice = ask(metrics, prompt, rule(task, history))
        if choice["tool"] == "finish":
            return
        tool, arguments = choice["tool"], choice["args"]
        history.append((tool, arguments, world.call(tool, arguments)))
```

Each choice uses the current history. The tool result is appended, so the next choice can see whether it succeeded.

`experiments/decide.py` · `planexec`

```python
        if replans == 0:
            return
        replans -= 1
        prompt = {"request": task["text"], "history": history}
        steps = ask(metrics, prompt, replan(task, history))
```

Zero remaining replans means stop. With one left, spend it and ask for another plan using the recorded results.

Additional source on request.

`experiments/decide.py` · `planexec`

```python
def planexec(task, world, metrics, replans=0):
    history = []
    steps = ask(metrics, {"request": task["text"]}, plan(task))
    while True:
        for step in steps:
            tool = step["tool"]
            arguments = {key: resolve_argument(value, history) for key, value in step["args"].items()}
            result = world.call(tool, arguments)
            history.append((tool, arguments, result))
            if "error" in result:
                break
```

The planner supplies steps once. Before running a tool, resolve any argument that refers to earlier results. Stop the inner loop on an error.

What do you expect one replan to change when the first flight sells out?

**Read the actual result**

Compare `completed`, `planning_calls` and `failed_with_bookings` for normal and sold-out trips. Use `sample.tool_log` to follow a trip where the first flight and the first hotel both sold out. See when ReAct sees each error and when plan-execute uses its one replan.

A plan saves decision calls when its assumptions hold. Replanning gives it another chance when they change.

Compare the zero and one replan rows. What changed in completed trips and why can a trip remain unfinished?

Compare the zero and one replan rows. What changed in completed trips and why can a trip remain unfinished?

### t03 W5.1 Write the Verify router (12 minutes)

Route from terminal, verified, retryable or unfinished state.

#### Review

**W5.1 Write the Verify router**

Related lecture slides: 17.

Let’s make the next-step decision ourselves in our Week 4 CONV-3 agent. The run has failed, but `ready=True` is still there from an earlier check. Write `route_verify` so it reads the current state and returns one destination. Also try a temporary error with no retries yet, shown by `retry_total=0`.

If the workflow check reports that LangGraph is missing, use Python 3.11 or newer. From the seminar resources folder, run `python -m pip install -r workflow/requirements.txt` with the same Python interpreter you will use to run the checks.

`workflow/routing.py` · `route_verify`

```python
def route_verify(s):
    """Prioritize terminal status, verified evidence, then retryable errors."""
    # TODO W5.1: Return Finish, PrepareApproval, Retry, or Planner.
    raise NotImplementedError("Complete W5.1 in workflow/routing.py.")
```

This is the function to complete. It receives a state dictionary and returns the name of exactly one next node.

`workflow/routing.py` · `route_planner`

```python
def route_planner(s):
    return "Finish" if s["status"] in TERMINAL else "Execute"
```

This smaller router demonstrates how returning a node name selects a route.

Additional source on request.

`workflow/nodes.py` · `Nodes.retry`

```python
    def retry(self, s):
        if s["retry_total"] >= MAX_RETRIES:
            return {"status": "failed", "reason": "retry_exhausted", "trace": [event("Retry", "exhausted")]}
        return {
            "retry_total": s["retry_total"] + 1,
            "trace": [event("Retry", "retry", retry_total=s["retry_total"] + 1)],
        }
```

Retry owns the budget. Look at where it increments the count, and where it returns a terminal failure instead.

Where should the failed run with the old ready flag go?

**Read the actual result**

Use `exercise.cases` to compare your predictions with the destinations the router returned. Check which condition won when a failed run still carried `ready=True`, and where the first temporary error was sent.

The router chooses a destination. The Retry node owns the retry budget.

Why must a terminal check come before the ready check, and which node decides if a retry fits the budget?

#### Practice

**W5.1 Write the Verify router**

The CONV-3 run has failed, but `ready=True` is still there from an earlier check. Decide where it should go and write `route_verify`, a function that returns one destination from the current state. Then try a temporary error with no retries yet, shown by `retry_total=0`.

If the workflow check reports that LangGraph is missing, use Python 3.11 or newer. From the seminar resources folder, run `python -m pip install -r workflow/requirements.txt` with the same Python interpreter you will use to run the checks.

`workflow/routing.py` · `route_verify`

```python
def route_verify(s):
    """Prioritize terminal status, verified evidence, then retryable errors."""
    # TODO W5.1: Return Finish, PrepareApproval, Retry, or Planner.
    raise NotImplementedError("Complete W5.1 in workflow/routing.py.")
```

This is the function to complete. It receives a state dictionary and returns the name of exactly one next node.

`workflow/routing.py` · `route_planner`

```python
def route_planner(s):
    return "Finish" if s["status"] in TERMINAL else "Execute"
```

This smaller router demonstrates how returning a node name selects a route.

Additional source on request.

`workflow/nodes.py` · `Nodes.retry`

```python
    def retry(self, s):
        if s["retry_total"] >= MAX_RETRIES:
            return {"status": "failed", "reason": "retry_exhausted", "trace": [event("Retry", "exhausted")]}
        return {
            "retry_total": s["retry_total"] + 1,
            "trace": [event("Retry", "retry", retry_total=s["retry_total"] + 1)],
        }
```

Retry owns the budget. Look at where it increments the count, and where it returns a terminal failure instead.

Where should the failed run with the old ready flag go?

**Read the actual result**

Use `exercise.cases` to compare your predictions with the destinations the router returned. Check which condition won when a failed run still carried `ready=True`, and where the first temporary error was sent.

The router chooses a destination. The Retry node owns the retry budget.

Why must a terminal check come before the ready check, and which node decides if a retry fits the budget?

After saving the prediction, ask the learner for the body of `route_verify` in `workflow/routing.py`.

Why must a terminal check come before the ready check, and which node decides if a retry fits the budget?

### t04 W5.2 Connect the workflow graph (11 minutes)

Connect the Verify and HumanApproval branches in the graph builder.

#### Review

**W5.2 Connect the workflow graph**

Related lecture slides: 28, 32.

Your router returns a node name. Now connect it to the graph so LangGraph knows which destination to run. Imagine the tutor rejects the CONV-3 report. If we added a fixed edge from `HumanApproval` to `ApplyAction`, the graph would still call the ticket writer. A conditional edge chooses a destination using the router. Connect the two missing branches for `Verify` and `HumanApproval`.

If the workflow check reports that LangGraph is missing, use Python 3.11 or newer. From the seminar resources folder, run `python -m pip install -r workflow/requirements.txt` with the same Python interpreter you will use to run the checks. Then use that interpreter for `python -m workflow check edges`.

`workflow/graph_app.py` · `connect_conditional_edges`

```python
def connect_conditional_edges(builder):
    """Connect Verify and HumanApproval to their named possible successors."""
    # TODO W5.2: Add the two conditional edges with their allowed destination lists.
    raise NotImplementedError("Complete W5.2 in workflow/graph_app.py.")
```

Add two conditional branches to the existing builder.

`workflow/graph_app.py` · `build_graph`

```python
        builder.add_node(name, action)
    builder.add_edge(START, "Planner")
    builder.add_conditional_edges("Planner", route_planner, ["Finish", "Execute"])
    builder.add_edge("Execute", "Verify")
    builder.add_conditional_edges("Retry", route_retry, ["Finish", "Execute"])
    builder.add_edge("PrepareApproval", "HumanApproval")
    builder.add_edge("ApplyAction", "Finish")
    builder.add_edge("Finish", END)
    connect_conditional_edges(builder)
    return builder.compile(checkpointer=checkpointer)
```

add_edge sets one destination. add_conditional_edges attaches a router and lists its possible destinations.

Additional source on request.

`workflow/routing.py` · `route_approval`

```python
def route_approval(s):
    if s["status"] == "approved" and (s.get("approval") or {}).get("approved") is True:
        return "ApplyAction"
    return "Finish"
```

The current status and the exact Boolean decision control the two outcomes.

What would go wrong if the approval step always went to the ticket writer?

**Read the actual result**

Use `exercise.edges` to find the conditional connections you just added. Trace `HumanApproval` on a rejection and check whether the ticket writer is on that path.

A conditional edge gives each decision one next node. A rejection finishes before the ticket writer.

Which node waits, which one writes a ticket, and how do your edges keep rejection from writing?

#### Practice

**W5.2 Connect the workflow graph**

The tutor rejects the CONV-3 report. What would the graph do if `HumanApproval` had a fixed edge to `ApplyAction`? Use the two router functions to connect the missing conditional edges so the decision controls the next node.

If the workflow check reports that LangGraph is missing, use Python 3.11 or newer. From the seminar resources folder, run `python -m pip install -r workflow/requirements.txt` with the same Python interpreter you will use to run the checks. Then use that interpreter for `python -m workflow check edges`.

`workflow/graph_app.py` · `connect_conditional_edges`

```python
def connect_conditional_edges(builder):
    """Connect Verify and HumanApproval to their named possible successors."""
    # TODO W5.2: Add the two conditional edges with their allowed destination lists.
    raise NotImplementedError("Complete W5.2 in workflow/graph_app.py.")
```

Add two conditional branches to the existing builder.

`workflow/graph_app.py` · `build_graph`

```python
        builder.add_node(name, action)
    builder.add_edge(START, "Planner")
    builder.add_conditional_edges("Planner", route_planner, ["Finish", "Execute"])
    builder.add_edge("Execute", "Verify")
    builder.add_conditional_edges("Retry", route_retry, ["Finish", "Execute"])
    builder.add_edge("PrepareApproval", "HumanApproval")
    builder.add_edge("ApplyAction", "Finish")
    builder.add_edge("Finish", END)
    connect_conditional_edges(builder)
    return builder.compile(checkpointer=checkpointer)
```

add_edge sets one destination. add_conditional_edges attaches a router and lists its possible destinations.

Additional source on request.

`workflow/routing.py` · `route_approval`

```python
def route_approval(s):
    if s["status"] == "approved" and (s.get("approval") or {}).get("approved") is True:
        return "ApplyAction"
    return "Finish"
```

The current status and the exact Boolean decision control the two outcomes.

What would go wrong if the approval step always went to the ticket writer?

**Read the actual result**

Use `exercise.edges` to find the conditional connections you just added. Trace `HumanApproval` on a rejection and check whether the ticket writer is on that path.

A conditional edge gives each decision one next node. A rejection finishes before the ticket writer.

Which node waits, which one writes a ticket, and how do your edges keep rejection from writing?

After saving the prediction, ask the learner for the body of `connect_conditional_edges` in `workflow/graph_app.py`.

Which node waits, which one writes a ticket, and how do your edges keep rejection from writing?

### t05 Redo state and external actions (9 minutes)

Separate repeated state updates from repeated external effects.

#### Review

**Three rules for saving workflow state**

Related lecture slides: 20.

In our next simulation, the booking provider charges 960 USD for four conference passes on trip 17. We simulate a crash before the workflow records that the workshop booking is next. The provider has recorded the charge, but our saved record still points to the pass purchase. Start with what we can fix in our own record.

That mishap has the right soundtrack: *Qiu Long* by Beizhou, nicknamed the heartbreak tune from short dramas. [Optional: open it on Bilibili in a new tab and listen for 15 seconds](https://www.bilibili.com/video/BV1min86QEHN/). The recording stays on the external platform for copyright reasons. If the link is blocked, search for the song on QQ Music or NetEase Cloud Music, or skip it and keep going.

Rules stand first — only then does the workflow stop hurting.

**（规矩立住了，流程才不烧心）**

**1. Return an update.** Return just what this node adds. Appending `["verified", "prepared"]` to a saved log that already contains `"verified"` repeats that first entry. Look for `return {…}` in `select_ticket`: it returns only the selected ticket. The same rule applies to a log update.

**2. Merge computes the new state.** Add costs to `spent`, append events to `log`, and replace `next` with the new step name. Adding `next` to `ADD` joins two step names. Removing `spent` from `ADD` lets the workshop cost replace the pass cost. `merge` adds fields in `ADD` and replaces the others.

**3. Commit once.** Save the new state and `next` together. If the crash hits after the total changes but before `next` advances, the same step can add its cost again. In `run_trip`, lines 110–113 build the new state and set `next` before publishing the combined in-memory checkpoint.

`experiments/redo.py` · `select_ticket`

```python
def select_ticket(world, trip, state):
    eligible = (ticket[:2] for ticket in state["tickets"] if ticket[2])
    return {"ticket": min(eligible, key=lambda ticket: ticket[1])}
```

Return the selected ticket as a small update.

`experiments/redo.py` · `merge`

```python
def merge(state, update):
    merged = dict(state)
    for key, value in update.items():
        merged[key] = state[key] + value if key in ADD else value
    return merged
```

Fields in ADD are added. Other fields take the new value.

`experiments/redo.py` · `run_trip`

```python
        if write_as == "in_place":
            state.update(merge(state, update))
        if draw < world.failure_rate:
            raise Crash("after action, before advancing next")

        if write_as == "in_place":
            state["next"] = EDGES[node]
        else:
            update = {**update, "next": EDGES[node]}
            state = merge(state, update)
            history.append(update)
            checkpoints[trip] = json.dumps({"state": state, "history": history})
```

The simulated crash can interrupt an in-place write before next advances. The update branch saves them together.

Continue to the provider’s record.

**A stable number for the same request**

Related lecture slides: 23.

Rules stand first — only then does the workflow stop hurting. Our ledger is quiet now; theirs is not.

**（规矩立住了，流程才不烧心——我们这本安静了，他们那本还没有。）**

Trip 17 has just paid $960 for four conference passes. The payment goes through, then the workflow crashes before it saves that the workshop booking is next.

The booking provider has a receipt for $960. Our workflow’s saved state still says to pay for the passes. Each system saves its own record. The provider can finish charging before our workflow records that the payment is done.

Picture a booking counter. On the first visit, the clerk takes $960 and files the receipt under your request number. The receipt never reaches you. You come back with the same number. The clerk checks the register before reaching for the card reader, finds the old receipt and hands it back. If the number is missing from the register, the clerk processes the payment and files a receipt under that number.

1. Build the request number from the saved trip and step. This payment always uses `17:pay_for_ticket`.
2. Look for that number in the provider’s register before charging.
3. If the number is there, return the saved result. The provider does not charge again.
4. If the number is missing, process the payment, save the result under that number and return it.

Build the number from the restored workflow, so a retry can rebuild it. A fresh number makes the clerk charge again. A number for the whole trip alone is too broad: the clerk might return the pass receipt when you meant to book the workshop.

`experiments/redo.py` · `World.act`

```python
        key = None
        if self.keys == "random":
            key = f"k{self.key_rng.getrandbits(40):x}"
        elif self.keys == "stable":
            key = f"{trip}:{node}"
        if key is not None and key in self.receipts:
            self.blocked += 1
            return self.receipts[key]
        self.done[trip, kind] += 1
        if key is not None:
            self.receipts[key] = update
        return update
```

`key = f"{trip}:{node}"` rebuilds the same request number from trip 17 and the payment step.

`if key is not None and key in self.receipts` checks the register before any payment.

`return self.receipts[key]` hands back the saved result and exits before the charge. `self.blocked` counts that avoided repeat.

`self.done[trip, kind] += 1` records that the simulated provider has carried out the action.

`self.receipts[key] = update` files the result under that number. The last `return update` sends back the new result.

What would the clerk do if this retry arrived with a different number?

**Redo state and external actions**

**Question.** Can we fix our saved totals and still charge a customer twice? Which change fixes each problem?

**Setup.** Run the same 2,000 trips with seed 7. First compare `in_place` and `update` with no key to isolate the save method. Then keep `update` fixed and compare no key, a new key on each attempt and a stable key. Now the request number is the only change.

**Results to read.** `wrong_final_states` and `replay_matches` describe our saved record. `repeated_actions` and `blocked_requests` describe the provider. `counterexamples` shows what breaks when we change one rule on purpose.

Predict which state update will reduce bad final states and which key will reduce repeated actions.

**Read the actual result**

Related lecture slides: 21, 24.

Read `wrong_final_states` for our saved record, then `repeated_actions` and `blocked_requests` for the provider. Use `replay_matches` to check whether the saved updates rebuild the same final state. In the seed 7 comparison, mutating state in place left 281 trips with wrong final states; returning an update removed those errors.

Verify the examples in `counterexamples`. `whole_log_as_update` shows the duplicate entry. `next_in_add` records `KeyError: 'read_requestsearch_tickets'`. `spent_not_in_add` gives 180 USD instead of the independent total of 1,140 USD. The simulation can still report `wrong_spent=0` because it uses the same wrong merge for its reference.

In `partial_commit`, compare the saved `next`, `spent_usd` and `ticket_charges` across the stop and restart. Saving state and `next` together gives 1,140 USD instead of 2,100 USD in our record. Without a key, the provider still charges twice.

Commit the workflow’s update together. Give the provider a stable key for each action.

The trace already contains `requested`, and the node produces `report ready`. Using both result tables, show what update you would save and what request IDs you would use for a retry and for a different ticket.

#### Practice

**Three rules for saving workflow state**

In our next simulation, the booking provider charges 960 USD for four conference passes on trip 17. We simulate a crash before the workflow records that the workshop booking is next. The provider has recorded the charge, but our saved record still points to the pass purchase. Start with what we can fix in our own record.

That mishap has the right soundtrack: *Qiu Long* by Beizhou, nicknamed the heartbreak tune from short dramas. [Optional: open it on Bilibili in a new tab and listen for 15 seconds](https://www.bilibili.com/video/BV1min86QEHN/). The recording stays on the external platform for copyright reasons. If the link is blocked, search for the song on QQ Music or NetEase Cloud Music, or skip it and keep going.

Rules stand first — only then does the workflow stop hurting.

**（规矩立住了，流程才不烧心）**

**1. Return an update.** Return just what this node adds. Appending `["verified", "prepared"]` to a saved log that already contains `"verified"` repeats that first entry. Look for `return {…}` in `select_ticket`: it returns only the selected ticket. The same rule applies to a log update.

**2. Merge computes the new state.** Add costs to `spent`, append events to `log`, and replace `next` with the new step name. Adding `next` to `ADD` joins two step names. Removing `spent` from `ADD` lets the workshop cost replace the pass cost. `merge` adds fields in `ADD` and replaces the others.

**3. Commit once.** Save the new state and `next` together. If the crash hits after the total changes but before `next` advances, the same step can add its cost again. In `run_trip`, lines 110–113 build the new state and set `next` before publishing the combined in-memory checkpoint.

`experiments/redo.py` · `select_ticket`

```python
def select_ticket(world, trip, state):
    eligible = (ticket[:2] for ticket in state["tickets"] if ticket[2])
    return {"ticket": min(eligible, key=lambda ticket: ticket[1])}
```

Return the selected ticket as a small update.

`experiments/redo.py` · `merge`

```python
def merge(state, update):
    merged = dict(state)
    for key, value in update.items():
        merged[key] = state[key] + value if key in ADD else value
    return merged
```

Fields in ADD are added. Other fields take the new value.

`experiments/redo.py` · `run_trip`

```python
        if write_as == "in_place":
            state.update(merge(state, update))
        if draw < world.failure_rate:
            raise Crash("after action, before advancing next")

        if write_as == "in_place":
            state["next"] = EDGES[node]
        else:
            update = {**update, "next": EDGES[node]}
            state = merge(state, update)
            history.append(update)
            checkpoints[trip] = json.dumps({"state": state, "history": history})
```

The simulated crash can interrupt an in-place write before next advances. The update branch saves them together.

Continue to the provider’s record.

**A stable number for the same request**

Rules stand first — only then does the workflow stop hurting. Our ledger is quiet now; theirs is not.

**（规矩立住了，流程才不烧心——我们这本安静了，他们那本还没有。）**

Trip 17 has just paid $960 for four conference passes. The payment goes through, then the workflow crashes before it saves that the workshop booking is next.

The booking provider has a receipt for $960. Our workflow’s saved state still says to pay for the passes. Each system saves its own record. The provider can finish charging before our workflow records that the payment is done.

Picture a booking counter. On the first visit, the clerk takes $960 and files the receipt under your request number. The receipt never reaches you. You come back with the same number. The clerk checks the register before reaching for the card reader, finds the old receipt and hands it back. If the number is missing from the register, the clerk processes the payment and files a receipt under that number.

1. Build the request number from the saved trip and step. This payment always uses `17:pay_for_ticket`.
2. Look for that number in the provider’s register before charging.
3. If the number is there, return the saved result. The provider does not charge again.
4. If the number is missing, process the payment, save the result under that number and return it.

Build the number from the restored workflow, so a retry can rebuild it. A fresh number makes the clerk charge again. A number for the whole trip alone is too broad: the clerk might return the pass receipt when you meant to book the workshop.

`experiments/redo.py` · `World.act`

```python
        key = None
        if self.keys == "random":
            key = f"k{self.key_rng.getrandbits(40):x}"
        elif self.keys == "stable":
            key = f"{trip}:{node}"
        if key is not None and key in self.receipts:
            self.blocked += 1
            return self.receipts[key]
        self.done[trip, kind] += 1
        if key is not None:
            self.receipts[key] = update
        return update
```

`key = f"{trip}:{node}"` rebuilds the same request number from trip 17 and the payment step.

`if key is not None and key in self.receipts` checks the register before any payment.

`return self.receipts[key]` hands back the saved result and exits before the charge. `self.blocked` counts that avoided repeat.

`self.done[trip, kind] += 1` records that the simulated provider has carried out the action.

`self.receipts[key] = update` files the result under that number. The last `return update` sends back the new result.

What would the clerk do if this retry arrived with a different number?

**Redo state and external actions**

**Question.** Can we fix our saved totals and still charge a customer twice? Which change fixes each problem?

**Setup.** Run the same 2,000 trips with seed 7. First compare `in_place` and `update` with no key to isolate the save method. Then keep `update` fixed and compare no key, a new key on each attempt and a stable key. Now the request number is the only change.

**Results to read.** `wrong_final_states` and `replay_matches` describe our saved record. `repeated_actions` and `blocked_requests` describe the provider. `counterexamples` shows what breaks when we change one rule on purpose.

Predict which state update will reduce bad final states and which key will reduce repeated actions.

**Read the actual result**

Read `wrong_final_states` for our saved record, then `repeated_actions` and `blocked_requests` for the provider. Use `replay_matches` to check whether the saved updates rebuild the same final state. In the seed 7 comparison, mutating state in place left 281 trips with wrong final states; returning an update removed those errors.

Verify the examples in `counterexamples`. `whole_log_as_update` shows the duplicate entry. `next_in_add` records `KeyError: 'read_requestsearch_tickets'`. `spent_not_in_add` gives 180 USD instead of the independent total of 1,140 USD. The simulation can still report `wrong_spent=0` because it uses the same wrong merge for its reference.

In `partial_commit`, compare the saved `next`, `spent_usd` and `ticket_charges` across the stop and restart. Saving state and `next` together gives 1,140 USD instead of 2,100 USD in our record. Without a key, the provider still charges twice.

Commit the workflow’s update together. Give the provider a stable key for each action.

The trace already contains `requested`, and the node produces `report ready`. Using both result tables, show what update you would save and what request IDs you would use for a retry and for a different ticket.

The trace already contains `requested`, and the node produces `report ready`. Using both result tables, show what update you would save and what request IDs you would use for a retry and for a different ticket.

## Session 2 (50 minutes)

### t06 W5.3 Validate an approval (12 minutes)

Bind a boolean decision to the exact pending CONV-3 review action.

#### Review

**W5.3 Validate an approval**

Related lecture slides: 27, 29, 30.

A tutor opens the CONV-3 report on Monday. On Tuesday a corrected temperature reading is included and the data file is regenerated. The ticket request can still have the same number. Should Monday’s approval create a ticket for Tuesday’s report?

The tutor’s reply records what they saw. The workflow’s waiting request records what it is about to submit. A new version can keep the same request number, so we also check the contents.

Think of the request number on an envelope and a wax seal made from its contents. The request number (`action_id`) tells us which envelope it is. When the corrected report goes inside, it gets a different seal (`payload_hash`). The tutor’s reply carries the seal they saw, so we can spot a reply for the earlier version.

When preparing a request, include the data file’s fingerprint (`data_fingerprint`) and the report in the payload, then compute the seal. When reading a reply, compare its ID and hash with the waiting request. Require a real JSON Boolean and a nonempty reviewer name. Try JSON `false` for the current report, text `"false"` for that report, and JSON `true` for the old report.

In `make_action`, look at what goes into `payload`, how the ID comes from the thread, and how `digest(payload)` makes the seal. Then add the reply checks to `validate_decision`.

`workflow/approval.py` · `make_action`

```python
        "kind": "create_simulated_review_ticket",
        "thread_id": s["thread_id"],
        "machine_id": s["task"]["machine_id"],
        "window": {"start": s["task"]["start"], "end": s["task"]["end"]},
        "report": copy.deepcopy(s["report"]),
        "data_fingerprint": s["data_fingerprint"],
    }
    return {
        "action_id": f"{s['thread_id']}-review-1",
        "payload": payload,
        "payload_hash": digest(payload),
    }
```

The payload contains the data fingerprint and report. The ID comes from the thread, while the hash comes from the payload.

`workflow/approval.py` · `validate_decision`

```python
def validate_decision(s, reply):
    """Return a normalized decision after checking its type and action binding."""
    # TODO W5.3: Check the Boolean, action ID, payload hash, and reviewer label.
    raise NotImplementedError("Complete W5.3 in workflow/approval.py.")
```

The function you write returns a normalized reply after checking its type, action binding and reviewer label.

Additional source on request.

`workflow/approval.py` · `checked_action`

```python
def checked_action(s):
    pending = s.get("pending_action")
    if pending != make_action(s):
        raise ApprovalError("The pending action no longer matches the verified report.")
    return pending
```

Before using the waiting action, compare it with one derived again from the verified report.

Of those three replies, which should your validator accept?

**Read the actual result**

Use `exercise.cases` to compare `accepted` and `reason` for the Boolean and string replies.

Then find “a changed report needs a new approval.” Compare `old_payload_hash`, `new_payload_hash` and `original_decision_rejected`. The fresh decision covers the new report.

A valid approval covers one specific action and the exact contents the reviewer saw.

Why is JSON false a valid rejection but the string "false" invalid? What is the purpose of checking the action ID and payload hash?

#### Practice

**W5.3 Validate an approval**

A tutor opens the CONV-3 report on Monday. On Tuesday a corrected temperature reading is included and the data file is regenerated. The ticket request can still have the same number. Should Monday’s approval create a ticket for Tuesday’s report?

The tutor’s reply records what they saw. The workflow’s waiting request records what it is about to submit. A new version can keep the same request number, so we also check the contents.

Think of the request number on an envelope and a wax seal made from its contents. The request number (`action_id`) tells us which envelope it is. When the corrected report goes inside, it gets a different seal (`payload_hash`). The tutor’s reply carries the seal they saw, so we can spot a reply for the earlier version.

When preparing a request, include the data file’s fingerprint (`data_fingerprint`) and the report in the payload, then compute the seal. When reading a reply, compare its ID and hash with the waiting request. Require a real JSON Boolean and a nonempty reviewer name. Try JSON `false` for the current report, text `"false"` for that report, and JSON `true` for the old report.

In `make_action`, look at what goes into `payload`, how the ID comes from the thread, and how `digest(payload)` makes the seal. Then add the reply checks to `validate_decision`.

`workflow/approval.py` · `make_action`

```python
        "kind": "create_simulated_review_ticket",
        "thread_id": s["thread_id"],
        "machine_id": s["task"]["machine_id"],
        "window": {"start": s["task"]["start"], "end": s["task"]["end"]},
        "report": copy.deepcopy(s["report"]),
        "data_fingerprint": s["data_fingerprint"],
    }
    return {
        "action_id": f"{s['thread_id']}-review-1",
        "payload": payload,
        "payload_hash": digest(payload),
    }
```

The payload contains the data fingerprint and report. The ID comes from the thread, while the hash comes from the payload.

`workflow/approval.py` · `validate_decision`

```python
def validate_decision(s, reply):
    """Return a normalized decision after checking its type and action binding."""
    # TODO W5.3: Check the Boolean, action ID, payload hash, and reviewer label.
    raise NotImplementedError("Complete W5.3 in workflow/approval.py.")
```

The function you write returns a normalized reply after checking its type, action binding and reviewer label.

Additional source on request.

`workflow/approval.py` · `checked_action`

```python
def checked_action(s):
    pending = s.get("pending_action")
    if pending != make_action(s):
        raise ApprovalError("The pending action no longer matches the verified report.")
    return pending
```

Before using the waiting action, compare it with one derived again from the verified report.

Of those three replies, which should your validator accept?

**Read the actual result**

Use `exercise.cases` to compare `accepted` and `reason` for the Boolean and string replies.

Then find “a changed report needs a new approval.” Compare `old_payload_hash`, `new_payload_hash` and `original_decision_rejected`. The fresh decision covers the new report.

A valid approval covers one specific action and the exact contents the reviewer saw.

Why is JSON false a valid rejection but the string "false" invalid? What is the purpose of checking the action ID and payload hash?

After saving the prediction, ask the learner for the body of `validate_decision` in `workflow/approval.py`.

Why is JSON false a valid rejection but the string "false" invalid? What is the purpose of checking the action ID and payload hash?

### t07 W5.4 Find the same workflow in a new process (12 minutes)

Use LangGraph and SQLite to save a waiting workflow and inspect it from a separate process.

#### Review

**W5.4 Find the same workflow in a new process**

Related lecture slides: 31, 32, 33.

The tutor will reply tomorrow. Today, Python closes with the CONV-3 report still waiting. How will tomorrow’s process find this report instead of starting the tools again?

The checkpoint holds the report and the pending step. The separate ticket database records tickets that have actually been written. A waiting report has a checkpoint even though it has no ticket.

Think of a patient’s medical folder. `thread_id` is the folder label. Each visit adds a page: one may say “report verified” and a later one “waiting for approval.” Each saved page has its own `checkpoint_id`. Start and inspect should open the same latest page. A different workflow would have a different folder.

Close the first process and open the same `checkpoints.sqlite` file with the same thread ID. The checkpointer finds the latest page. Use synchronous durability for this lab so a step’s checkpoint is saved before the next step starts.

`config` supplies the thread ID. Write `resume_approval` to use that same config, pass the reply in `Command(resume=decision)` and return the result of invoking the graph with `durability="sync"`. Then start and inspect the three waiting reports in separate processes.

`workflow/service.py` · `config`

```python
def config(thread_id):
    validate_thread_id(thread_id)
    return {"configurable": {"thread_id": thread_id}, "recursion_limit": 60}
```

The configured thread_id lets the checkpointer find the history of a particular workflow.

`workflow/service.py` · `resume_approval`

```python
def resume_approval(graph, config, decision):
    """Send the validated decision to the suspended node using the saved config."""
    # TODO W5.4: Invoke the graph with Command(resume=...), using synchronous durability.
    raise NotImplementedError("Complete W5.4 in workflow/service.py.")
```

Invoke the existing graph with the current config, the validated decision and synchronous durability. Return the invocation result.

Additional source on request.

`workflow/service.py` · `start`

```python
def start(graph, thread_id, *, create_ticket=True, scenario="normal"):
    cfg = config(thread_id)
    if graph.get_state(cfg).values:
        raise ValueError("This thread already exists. Inspect it or choose a fresh thread ID.")
    graph.invoke(initial_state(thread_id, create_ticket=create_ticket, scenario=scenario), cfg, durability="sync")
    return graph.get_state(cfg)
```

Starting a new thread passes an initial state to invoke. Your resume call passes a decision to the existing interrupt.

Additional source on request.

`workflow/service.py` · `session`

```python
@contextmanager
def session(workspace, *, crash_at=None):
    workspace.mkdir(parents=True, exist_ok=True)
    effects = EffectStore(workspace / "effects.sqlite")
    with closing(sqlite3.connect(workspace / "checkpoints.sqlite", check_same_thread=False)) as conn:
        serializer = JsonPlusSerializer(allowed_msgpack_modules=[])
        saver = SqliteSaver(conn, serde=serializer)
        yield build_graph(saver, effects, crash_at=crash_at), effects
```

Each process opens the same two local files. The checkpointer stores the graph state. The effect database holds the tickets.

Which fields would you compare to tell whether the new process found the same waiting report?

**Read the actual result**

The resume check uses a stand-in graph to test the function call. In the real `processes` results, compare the start and inspect records for one thread. Check the process, thread and checkpoint IDs, the pending step and the tool evidence.

This is the third Redo rule in a real workflow: the step’s state and next position are saved together. With `sync`, the save finishes before the next step starts. With `async`, the next step can start while the save is still in flight, so a hard crash can lose that latest save. With `exit`, the graph saves at an exit such as a normal finish or a pause; a hard crash before that point can lose work since the last saved run.

The saved `decision_requests` contain the action IDs and hashes for the next two tasks.

A new process can use the same thread and database to recover the pending step.

Which fields show that the new process opened the same waiting task? How do you know that it did not run the original tools again?

#### Practice

**W5.4 Find the same workflow in a new process**

The tutor will reply tomorrow. Today, Python closes with the CONV-3 report still waiting. How will tomorrow’s process find this report instead of starting the tools again?

The checkpoint holds the report and the pending step. The separate ticket database records tickets that have actually been written. A waiting report has a checkpoint even though it has no ticket.

Think of a patient’s medical folder. `thread_id` is the folder label. Each visit adds a page: one may say “report verified” and a later one “waiting for approval.” Each saved page has its own `checkpoint_id`. Start and inspect should open the same latest page. A different workflow would have a different folder.

Close the first process and open the same `checkpoints.sqlite` file with the same thread ID. The checkpointer finds the latest page. Use synchronous durability for this lab so a step’s checkpoint is saved before the next step starts.

`config` supplies the thread ID. Write `resume_approval` to use that same config, pass the reply in `Command(resume=decision)` and return the result of invoking the graph with `durability="sync"`. Then start and inspect the three waiting reports in separate processes.

`workflow/service.py` · `config`

```python
def config(thread_id):
    validate_thread_id(thread_id)
    return {"configurable": {"thread_id": thread_id}, "recursion_limit": 60}
```

The configured thread_id lets the checkpointer find the history of a particular workflow.

`workflow/service.py` · `resume_approval`

```python
def resume_approval(graph, config, decision):
    """Send the validated decision to the suspended node using the saved config."""
    # TODO W5.4: Invoke the graph with Command(resume=...), using synchronous durability.
    raise NotImplementedError("Complete W5.4 in workflow/service.py.")
```

Invoke the existing graph with the current config, the validated decision and synchronous durability. Return the invocation result.

Additional source on request.

`workflow/service.py` · `start`

```python
def start(graph, thread_id, *, create_ticket=True, scenario="normal"):
    cfg = config(thread_id)
    if graph.get_state(cfg).values:
        raise ValueError("This thread already exists. Inspect it or choose a fresh thread ID.")
    graph.invoke(initial_state(thread_id, create_ticket=create_ticket, scenario=scenario), cfg, durability="sync")
    return graph.get_state(cfg)
```

Starting a new thread passes an initial state to invoke. Your resume call passes a decision to the existing interrupt.

Additional source on request.

`workflow/service.py` · `session`

```python
@contextmanager
def session(workspace, *, crash_at=None):
    workspace.mkdir(parents=True, exist_ok=True)
    effects = EffectStore(workspace / "effects.sqlite")
    with closing(sqlite3.connect(workspace / "checkpoints.sqlite", check_same_thread=False)) as conn:
        serializer = JsonPlusSerializer(allowed_msgpack_modules=[])
        saver = SqliteSaver(conn, serde=serializer)
        yield build_graph(saver, effects, crash_at=crash_at), effects
```

Each process opens the same two local files. The checkpointer stores the graph state. The effect database holds the tickets.

Which fields would you compare to tell whether the new process found the same waiting report?

**Read the actual result**

The resume check uses a stand-in graph to test the function call. In the real `processes` results, compare the start and inspect records for one thread. Check the process, thread and checkpoint IDs, the pending step and the tool evidence.

This is the third Redo rule in a real workflow: the step’s state and next position are saved together. With `sync`, the save finishes before the next step starts. With `async`, the next step can start while the save is still in flight, so a hard crash can lose that latest save. With `exit`, the graph saves at an exit such as a normal finish or a pause; a hard crash before that point can lose work since the last saved run.

The saved `decision_requests` contain the action IDs and hashes for the next two tasks.

A new process can use the same thread and database to recover the pending step.

Which fields show that the new process opened the same waiting task? How do you know that it did not run the original tools again?

After saving the prediction, ask the learner for the body of `resume_approval` in `workflow/service.py`.

Which fields show that the new process opened the same waiting task? How do you know that it did not run the original tools again?

### t08 Run approval, rejection and invalid input (12 minutes)

Submit decisions bound to two different waiting tasks and read their actual outcomes.

#### Review

**Run approval, rejection and invalid input**

Related lecture slides: 28, 30, 32.

Two CONV-3 requests are waiting. We will approve `week05-approve` and reject `week05-reject`, then check a malformed reply. Before we run that test, picture the waiting step writing a ticket before it asks the question.

The checkpoint records where the workflow is waiting. The ticket table records what was actually written. Restoring a waiting page cannot undo a ticket that was already inserted.

Think of a clerk reopening the medical folder and starting the instructions on the waiting page from the top. When the clerk reaches the approval question again, the answer is now in the folder. Anything the clerk did above that question can happen again.

LangGraph starts the interrupted node again from the top when `Command(resume=decision)` resumes it. At `interrupt()`, the saved reply now comes back as the return value. Keep ticket writes out of the waiting node. If an unprotected insert ran before `interrupt()`, it would run before the pause and again on resume and could create two tickets. The counter test demonstrates those two executions without writing duplicate tickets.

In `human_approval`, find the call to `suspend` (our name for LangGraph’s `interrupt`) and the line that reads the reply. In `decide`, check where the reply is validated. In `route_approval`, trace where a valid approval goes and why rejection never reaches `ApplyAction`. Use the saved ID and hash for each request.

`workflow/nodes.py` · `Nodes.human_approval`

```python
    def human_approval(self, s):
        reply = self.suspend(approval_prompt(s))
        grant = validate_decision(s, reply)
        return {
            "approval": grant,
            "status": "approved" if grant["approved"] is True else "rejected",
            "trace": [event("HumanApproval", "decision", approved=grant["approved"])],
        }
```

The interrupt gives the learner the pending action. After resuming, the submitted reply becomes the value returned by suspend.

`workflow/service.py` · `decide`

```python
def decide(graph, thread_id, reply):
    cfg = config(thread_id)
    snapshot = inspect(graph, thread_id)
    if not interrupts_of(snapshot) or "HumanApproval" not in snapshot.next:
        raise ValueError("This thread is not waiting for approval.")
    decision = validate_decision(snapshot.values, reply)
    resume_approval(graph, cfg, decision)
    return graph.get_state(cfg)
```

The service checks that HumanApproval is waiting and validates the reply before invoking resume.

`workflow/routing.py` · `route_approval`

```python
def route_approval(s):
    if s["status"] == "approved" and (s.get("approval") or {}).get("approved") is True:
        return "ApplyAction"
    return "Finish"
```

Only an approved state with the Boolean true enters ApplyAction.

Predict the workflow status and ticket count after each of the three replies.

**Read the actual result**

Related lecture slides: 35.

Compare `status`, `ticket_count` and the trace for approval and rejection. For the malformed reply, read the error and compare the waiting checkpoint before and after it.

Then read `interrupt_demo.before_pause` and `interrupt_demo.after_resume`. Compare `before_interrupt` and follow `events`: the line before the pause ran once on the way in and once on resume. The counter stands in for a write. The real approval node does not write a ticket; a later node, `ApplyAction`, does.

Next you will see a different repeat: a crash leaves the writer pending after its ticket was already committed. That is where the saved request number protects the ticket table.

Keep the approval wait free of ticket writes. A valid approval can then route to the separate writer.

Which output proves that each branch behaved as intended? Include the invalid input and the pending state after it.

#### Practice

**Run approval, rejection and invalid input**

Two CONV-3 requests are waiting. We will approve `week05-approve` and reject `week05-reject`, then check a malformed reply. Before we run that test, picture the waiting step writing a ticket before it asks the question.

The checkpoint records where the workflow is waiting. The ticket table records what was actually written. Restoring a waiting page cannot undo a ticket that was already inserted.

Think of a clerk reopening the medical folder and starting the instructions on the waiting page from the top. When the clerk reaches the approval question again, the answer is now in the folder. Anything the clerk did above that question can happen again.

LangGraph starts the interrupted node again from the top when `Command(resume=decision)` resumes it. At `interrupt()`, the saved reply now comes back as the return value. Keep ticket writes out of the waiting node. If an unprotected insert ran before `interrupt()`, it would run before the pause and again on resume and could create two tickets. The counter test demonstrates those two executions without writing duplicate tickets.

In `human_approval`, find the call to `suspend` (our name for LangGraph’s `interrupt`) and the line that reads the reply. In `decide`, check where the reply is validated. In `route_approval`, trace where a valid approval goes and why rejection never reaches `ApplyAction`. Use the saved ID and hash for each request.

`workflow/nodes.py` · `Nodes.human_approval`

```python
    def human_approval(self, s):
        reply = self.suspend(approval_prompt(s))
        grant = validate_decision(s, reply)
        return {
            "approval": grant,
            "status": "approved" if grant["approved"] is True else "rejected",
            "trace": [event("HumanApproval", "decision", approved=grant["approved"])],
        }
```

The interrupt gives the learner the pending action. After resuming, the submitted reply becomes the value returned by suspend.

`workflow/service.py` · `decide`

```python
def decide(graph, thread_id, reply):
    cfg = config(thread_id)
    snapshot = inspect(graph, thread_id)
    if not interrupts_of(snapshot) or "HumanApproval" not in snapshot.next:
        raise ValueError("This thread is not waiting for approval.")
    decision = validate_decision(snapshot.values, reply)
    resume_approval(graph, cfg, decision)
    return graph.get_state(cfg)
```

The service checks that HumanApproval is waiting and validates the reply before invoking resume.

`workflow/routing.py` · `route_approval`

```python
def route_approval(s):
    if s["status"] == "approved" and (s.get("approval") or {}).get("approved") is True:
        return "ApplyAction"
    return "Finish"
```

Only an approved state with the Boolean true enters ApplyAction.

Predict the workflow status and ticket count after each of the three replies.

**Read the actual result**

Compare `status`, `ticket_count` and the trace for approval and rejection. For the malformed reply, read the error and compare the waiting checkpoint before and after it.

Then read `interrupt_demo.before_pause` and `interrupt_demo.after_resume`. Compare `before_interrupt` and follow `events`: the line before the pause ran once on the way in and once on resume. The counter stands in for a write. The real approval node does not write a ticket; a later node, `ApplyAction`, does.

Next you will see a different repeat: a crash leaves the writer pending after its ticket was already committed. That is where the saved request number protects the ticket table.

Keep the approval wait free of ticket writes. A valid approval can then route to the separate writer.

Which output proves that each branch behaved as intended? Include the invalid input and the pending state after it.

After saving the prediction, get the pending action from the actual t07 result and ask for the learner’s explicit decision for the named thread. Prepare the decision file from the learner reply. Follow the example in PRESENTATION.md.

Which output proves that each branch behaved as intended? Include the invalid input and the pending state after it.

### t09 Recover after the ticket write (9 minutes)

Verify that retrying a committed action creates no duplicate local ticket.

#### Review

**Recover after the ticket write**

Related lecture slides: 23, 24, 34.

This time you will approve `week05-recovery`. The CONV-3 ticket is written, but Python stops before the workflow saves that the write finished. The next process retries `ApplyAction`. Here we are rerunning the writer after a crash, rather than rerunning the waiting node when the tutor replies.

`checkpoints.sqlite` still says the writer is pending. `effects.sqlite` already contains the ticket. The workflow’s checkpoint and the ticket insert are two separate saves.

Remember `blocked_requests` in Redo? With seed 7, the stable key blocked 315 repeated requests. Here the SQLite `tickets` table is the booking clerk’s register. The `action_id` is the stable request number. A result of `reused=True` means the clerk found the original ticket and handed it back.

Look up the same `action_id` before inserting. If the hash matches, return that existing ticket. If the same number arrives with a different `payload_hash`, refuse it with an error. This is how we avoid treating a changed request as one we have already done. Insert only if there is no row for that ID.

In `apply_action`, find where the controlled stop happens after the write. In `EffectStore.apply`, follow the lookup, the conflicting-hash check and the `reused` return. Then continue from another process and use the saved records to see whether a second row appeared.

`workflow/nodes.py` · `Nodes.apply_action`

```python
    def apply_action(self, s):
        ticket = self.effects.apply(s)
        if self.crash_at == "after_write":
            raise SimulatedCrash("Stopped after ticket commit and before the graph saved the node result.")
        return {
            "ticket": ticket,
            "status": "completed",
            "trace": [event("ApplyAction", "ticket", **ticket)],
        }
```

The SQLite write completes before the simulated exception. The node returns completed and an event only when it can finish.

`workflow/effects.py` · `EffectStore.apply`

```python
            existing = database.execute(
                "SELECT payload_hash FROM tickets WHERE action_id = ?",
                (action["action_id"],),
            ).fetchone()
            if existing is None:
                database.execute(
                    "INSERT INTO tickets VALUES (?, ?, ?, ?, ?)",
                    (action["action_id"], state["thread_id"], action["payload_hash"],
                     canonical(action["payload"]), grant["reviewer"]),
                )
            elif existing[0] != action["payload_hash"]:
                raise ApprovalError("This action ID already has a different payload.")
```

The code looks up the logical action ID before inserting. A matching row can be reused. A conflicting payload for that ID is rejected.

`workflow/effects.py` · `EffectStore.apply`

```python
            elif existing[0] != action["payload_hash"]:
                raise ApprovalError("This action ID already has a different payload.")
        return {
            "action_id": action["action_id"],
            "payload_hash": action["payload_hash"],
            "reused": existing is not None,
        }
```

An existing row with a different hash raises an error. The return value marks a matching existing row as reused.

Additional source on request.

`workflow/service.py` · `continue_run`

```python
def continue_run(graph, thread_id):
    cfg = config(thread_id)
    snapshot = inspect(graph, thread_id)
    if interrupts_of(snapshot):
        raise ValueError("A human decision is still pending. Use decide.")
    if not snapshot.next:
        raise ValueError("There is no pending node to continue.")
    graph.invoke(None, cfg, durability="sync")
    return graph.get_state(cfg)
```

Continue uses the same thread and passes no new task input. A waiting human interrupt must use decide instead.

Predict the pending step after the stop and the ticket count after recovery.

**Read the actual result**

Related lecture slides: 35.

Compare the controlled fault, the inspection and the fresh continue result. Use the process IDs, pending step, action ID and ticket row count. Then check `reused` and the tool attempt count.

For the separate collision example, read `payload_collision`. The hashes differ for one ID. Check the refusal and whether the saved row stayed the same.

Recovery reruns the pending node. The same action ID lets it reuse the existing ticket.

How does the recovery output establish that the action was not duplicated after the controlled exception?

#### Practice

**Recover after the ticket write**

This time you will approve `week05-recovery`. The CONV-3 ticket is written, but Python stops before the workflow saves that the write finished. The next process retries `ApplyAction`. Here we are rerunning the writer after a crash, rather than rerunning the waiting node when the tutor replies.

`checkpoints.sqlite` still says the writer is pending. `effects.sqlite` already contains the ticket. The workflow’s checkpoint and the ticket insert are two separate saves.

Remember `blocked_requests` in Redo? With seed 7, the stable key blocked 315 repeated requests. Here the SQLite `tickets` table is the booking clerk’s register. The `action_id` is the stable request number. A result of `reused=True` means the clerk found the original ticket and handed it back.

Look up the same `action_id` before inserting. If the hash matches, return that existing ticket. If the same number arrives with a different `payload_hash`, refuse it with an error. This is how we avoid treating a changed request as one we have already done. Insert only if there is no row for that ID.

In `apply_action`, find where the controlled stop happens after the write. In `EffectStore.apply`, follow the lookup, the conflicting-hash check and the `reused` return. Then continue from another process and use the saved records to see whether a second row appeared.

`workflow/nodes.py` · `Nodes.apply_action`

```python
    def apply_action(self, s):
        ticket = self.effects.apply(s)
        if self.crash_at == "after_write":
            raise SimulatedCrash("Stopped after ticket commit and before the graph saved the node result.")
        return {
            "ticket": ticket,
            "status": "completed",
            "trace": [event("ApplyAction", "ticket", **ticket)],
        }
```

The SQLite write completes before the simulated exception. The node returns completed and an event only when it can finish.

`workflow/effects.py` · `EffectStore.apply`

```python
            existing = database.execute(
                "SELECT payload_hash FROM tickets WHERE action_id = ?",
                (action["action_id"],),
            ).fetchone()
            if existing is None:
                database.execute(
                    "INSERT INTO tickets VALUES (?, ?, ?, ?, ?)",
                    (action["action_id"], state["thread_id"], action["payload_hash"],
                     canonical(action["payload"]), grant["reviewer"]),
                )
            elif existing[0] != action["payload_hash"]:
                raise ApprovalError("This action ID already has a different payload.")
```

The code looks up the logical action ID before inserting. A matching row can be reused. A conflicting payload for that ID is rejected.

`workflow/effects.py` · `EffectStore.apply`

```python
            elif existing[0] != action["payload_hash"]:
                raise ApprovalError("This action ID already has a different payload.")
        return {
            "action_id": action["action_id"],
            "payload_hash": action["payload_hash"],
            "reused": existing is not None,
        }
```

An existing row with a different hash raises an error. The return value marks a matching existing row as reused.

Additional source on request.

`workflow/service.py` · `continue_run`

```python
def continue_run(graph, thread_id):
    cfg = config(thread_id)
    snapshot = inspect(graph, thread_id)
    if interrupts_of(snapshot):
        raise ValueError("A human decision is still pending. Use decide.")
    if not snapshot.next:
        raise ValueError("There is no pending node to continue.")
    graph.invoke(None, cfg, durability="sync")
    return graph.get_state(cfg)
```

Continue uses the same thread and passes no new task input. A waiting human interrupt must use decide instead.

Predict the pending step after the stop and the ticket count after recovery.

**Read the actual result**

Compare the controlled fault, the inspection and the fresh continue result. Use the process IDs, pending step, action ID and ticket row count. Then check `reused` and the tool attempt count.

For the separate collision example, read `payload_collision`. The hashes differ for one ID. Check the refusal and whether the saved row stayed the same.

Recovery reruns the pending node. The same action ID lets it reuse the existing ticket.

How does the recovery output establish that the action was not duplicated after the controlled exception?

After saving the prediction, get the pending action from the actual t07 result and ask for the learner’s explicit decision for the named thread. Prepare the decision file from the learner reply. Follow the example in PRESENTATION.md.

How does the recovery output establish that the action was not duplicated after the controlled exception?

### t10 Build an acceptance record (5 minutes)

Connect each completion claim to the actual saved evidence.

#### Review

**Build an acceptance record**

Related lecture slides: 35, 36.

You have run five checks: reopen a waiting task, approve, reject, refuse invalid input, and recover after a ticket write. Each claim needs a row drawn from your saved outputs.

Use the saved process, checkpoint and ticket records to show what the workflow actually did.

Fill the five rows from your runs. For each row, identify a thread, a state or next value, and a ticket count or evidence field.

#### Practice

**Build an acceptance record**

Open your saved workflow results for reopening, approval, rejection, invalid input and recovery. Use those runs to fill the five rows.

Use the saved process, checkpoint and ticket records to show what the workflow actually did.

Fill the five rows from your runs. For each row, identify a thread, a state or next value, and a ticket count or evidence field.

Fill five rows from your saved runs. For each case, name the thread, observed status or next node, and the ticket count or other evidence. Which field helped you diagnose the invalid reply or the stop after the write?

