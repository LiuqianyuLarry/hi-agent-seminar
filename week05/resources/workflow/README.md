# Week 5 workflow lab

This lab uses LangGraph and two local SQLite files. The planner follows a fixed rule so everyone gets the same CONV-3 data. The lab needs no API key.

Run these commands from your Week 5 resources folder. Use Python 3.11 or later in an active virtual environment. The lab was checked on Python 3.12. If your shell uses a different Python, replace `python` with the full path to the interpreter in your virtual environment.

```text
python -m pip install -r workflow/requirements.txt
```

Use that same interpreter for every check below. If `check edges` cannot import `langgraph`, check that it ran with the Python you used to install the requirements.

## Exercises

| Exercise | Fill in | Check it |
| --- | --- | --- |
| W5.1 | `route_verify` in `workflow/routing.py` | `python -m workflow check route` |
| W5.2 | `connect_conditional_edges` in `workflow/graph_app.py` | `python -m workflow check edges` |
| W5.3 | `validate_decision` in `workflow/approval.py` | `python -m workflow check approval` |
| W5.4 | `resume_approval` in `workflow/service.py` | `python -m workflow check resume`, then run the approval and recovery commands below |

## Check a saved approval

```text
python -m workflow --workspace lab-run --thread approval-demo start
python -m workflow --workspace lab-run --thread approval-demo inspect
```

Each command launches a Python process. Compare the two `pid` values and the shared `checkpoint_id`. The saved workflow should show `awaiting_approval`, `next` set to `["HumanApproval"]`, one interrupt, and zero ticket rows. The three observations hold the readings, the reference limit, and the computed statistics.

Create a file called `approval.json` using the action ID and payload hash from your own `pending_action`. The sample values below are placeholders.

```json
{
  "approved": true,
  "action_id": "COPY_ACTION_ID",
  "payload_hash": "COPY_PAYLOAD_HASH",
  "reviewer": "Student"
}
```

```text
python -m workflow --workspace lab-run --thread approval-demo decide --decision-file approval.json
```

For rejection, start a fresh thread and use its own action ID and payload hash with the JSON Boolean `false`. The status becomes `rejected` and its ticket table count stays at zero. The JSON string `"false"` is invalid and leaves the approval waiting.

## Recover after a ticket write

Start a fresh `recovery-demo` thread and inspect it. Save an approval for that thread in `recovery-approval.json`.

```text
python -m workflow --workspace lab-run --thread recovery-demo start
python -m workflow --workspace lab-run --thread recovery-demo inspect
python -m workflow --workspace lab-run --thread recovery-demo --crash-at after_write decide --decision-file recovery-approval.json
python -m workflow --workspace lab-run --thread recovery-demo inspect
python -m workflow --workspace lab-run --thread recovery-demo continue
```

The fault exits with code 3 after the ticket commits and before `ApplyAction` returns its state update. Inspect should show `ApplyAction` still pending and one durable ticket. Continue uses the same workspace and thread. It should show `completed`, one durable ticket, and `reused` set to `true`. Compare the action IDs and the number of tool attempts across the two snapshots.

`checkpoints.sqlite` holds graph state and the next node for each thread. `effects.sqlite` holds the simulated tickets. A transaction makes the ticket write durable. The action ID is the ticket table's primary key, so the resumed node can find the existing row.

Once all four exercises are filled in, `python -m workflow.verify_recovery` checks the five scenarios in a disposable workspace with separate Python processes.

The graph is adapted from the Week 5 teaching pack. The CONV-3 data comes from the Week 4 exercise.
