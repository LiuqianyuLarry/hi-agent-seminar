"""Open a fresh graph and SQLite connection on each command."""

from contextlib import closing, contextmanager
import os
import sqlite3

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from .approval import validate_decision
from .effects import EffectStore
from .graph_app import build_graph
from .graph_state import assert_compatible, initial_state, validate_thread_id


def config(thread_id):
    validate_thread_id(thread_id)
    return {"configurable": {"thread_id": thread_id}, "recursion_limit": 60}


def interrupts_of(snapshot):
    return [item for task in snapshot.tasks for item in task.interrupts]


@contextmanager
def session(workspace, *, crash_at=None):
    workspace.mkdir(parents=True, exist_ok=True)
    effects = EffectStore(workspace / "effects.sqlite")
    with closing(sqlite3.connect(workspace / "checkpoints.sqlite", check_same_thread=False)) as conn:
        serializer = JsonPlusSerializer(allowed_msgpack_modules=[])
        saver = SqliteSaver(conn, serde=serializer)
        yield build_graph(saver, effects, crash_at=crash_at), effects


def start(graph, thread_id, *, create_ticket=True, scenario="normal"):
    cfg = config(thread_id)
    if graph.get_state(cfg).values:
        raise ValueError("This thread already exists. Inspect it or choose a fresh thread ID.")
    graph.invoke(initial_state(thread_id, create_ticket=create_ticket, scenario=scenario), cfg, durability="sync")
    return graph.get_state(cfg)


def inspect(graph, thread_id):
    snapshot = graph.get_state(config(thread_id))
    assert_compatible(snapshot.values, thread_id)
    return snapshot


def resume_approval(graph, config, decision):
    """Send the validated decision to the suspended node using the saved config."""
    # TODO W5.4: Invoke the graph with Command(resume=...), using synchronous durability.
    raise NotImplementedError("Complete W5.4 in workflow/service.py.")


def decide(graph, thread_id, reply):
    cfg = config(thread_id)
    snapshot = inspect(graph, thread_id)
    if not interrupts_of(snapshot) or "HumanApproval" not in snapshot.next:
        raise ValueError("This thread is not waiting for approval.")
    decision = validate_decision(snapshot.values, reply)
    resume_approval(graph, cfg, decision)
    return graph.get_state(cfg)


def continue_run(graph, thread_id):
    cfg = config(thread_id)
    snapshot = inspect(graph, thread_id)
    if interrupts_of(snapshot):
        raise ValueError("A human decision is still pending. Use decide.")
    if not snapshot.next:
        raise ValueError("There is no pending node to continue.")
    graph.invoke(None, cfg, durability="sync")
    return graph.get_state(cfg)


def public_snapshot(snapshot, effects):
    state = snapshot.values
    action = state.get("pending_action")
    tickets = effects.rows(state["thread_id"])
    return {
        "pid": os.getpid(),
        "status": state["status"],
        "reason": state.get("reason"),
        "thread_id": state["thread_id"],
        "checkpoint_id": snapshot.config["configurable"]["checkpoint_id"],
        "next": list(snapshot.next),
        "interrupts": [{"id": item.id, "value": item.value} for item in interrupts_of(snapshot)],
        "pending_action": action,
        "action_id": action["action_id"] if action else None,
        "payload_hash": action["payload_hash"] if action else None,
        "approval": state.get("approval"),
        "report": state.get("report"),
        "tool_attempts": state["tool_attempts"],
        "retry_total": state["retry_total"],
        "observations": state["observations"],
        "trace": state["trace"],
        "ticket_count": len(tickets),
        "tickets": tickets,
        "ticket": state.get("ticket"),
        "reused": (state.get("ticket") or {}).get("reused"),
    }
