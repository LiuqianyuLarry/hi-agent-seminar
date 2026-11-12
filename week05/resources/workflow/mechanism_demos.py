"""Run isolated examples of interrupt replay and duplicate-ticket checks."""

import argparse
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from .approval import ApprovalError, make_action
from .effects import EffectStore
from .graph_state import initial_state


class DemoState(TypedDict):
    accepted: bool


def interrupt_demo():
    """Observe which lines rerun when LangGraph resumes the paused node."""
    events = []

    def wait_for_answer(state):
        events.append("before interrupt")
        answer = interrupt("Continue the demonstration?")
        events.append("after interrupt")
        return {"accepted": answer}

    def counts():
        return {
            "before_interrupt": events.count("before interrupt"),
            "after_interrupt": events.count("after interrupt"),
        }

    builder = StateGraph(DemoState)
    builder.add_node("WaitForAnswer", wait_for_answer)
    builder.add_edge(START, "WaitForAnswer")
    builder.add_edge("WaitForAnswer", END)
    graph = builder.compile(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "interrupt-demonstration"}}
    graph.invoke({"accepted": False}, config, durability="sync")
    paused = graph.get_state(config)
    if paused.next != ("WaitForAnswer",) or not any(task.interrupts for task in paused.tasks):
        raise AssertionError("The demonstration did not pause at its interrupt.")
    before_pause = counts()
    result = graph.invoke(Command(resume=True), config, durability="sync")
    if result.get("accepted") is not True or graph.get_state(config).next:
        raise AssertionError("The demonstration did not finish after resuming.")
    return {"before_pause": before_pause, "after_resume": counts(), "events": events}


def approved_fixture(thread_id, above_fraction):
    """Build a simulated approval for a specific report in the test store."""
    state = initial_state(thread_id)
    state["status"] = "approved"
    state["report"] = {"machine_id": "CONV-3", "statistics": {"above_fraction": above_fraction}}
    state["check"] = {"ready": True}
    pending = state["pending_action"] = make_action(state)
    state["approval"] = {
        "approved": True,
        "action_id": pending["action_id"],
        "payload_hash": pending["payload_hash"],
        "reviewer": "Demo fixture",
    }
    return state


def payload_collision():
    """Try to write changed report contents under an existing action ID."""
    thread_id = "payload-collision-demo"
    original = approved_fixture(thread_id, 0.8)
    changed = approved_fixture(thread_id, 0.2)
    first = original["pending_action"]
    second = changed["pending_action"]
    if first["action_id"] != second["action_id"] or first["payload_hash"] == second["payload_hash"]:
        raise AssertionError("Expected one action ID and two different payload hashes.")
    with TemporaryDirectory(prefix="week05-payload-demo-") as directory:
        store = EffectStore(Path(directory) / "effects.sqlite")
        store.apply(original)
        before = store.rows(thread_id)
        try:
            store.apply(changed)
        except ApprovalError as error:
            after = store.rows(thread_id)
            return {
                "action_id": first["action_id"],
                "original_payload_hash": first["payload_hash"],
                "different_payload_hash": second["payload_hash"],
                "ticket_count_before": len(before),
                "ticket_count_after": len(after),
                "row_unchanged": before == after,
                "error": type(error).__name__,
                "message": str(error),
            }
    raise AssertionError("Expected the ticket store to reject the changed payload.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("demo", choices=("interrupt", "payload-collision"))
    args = parser.parse_args()
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    result = interrupt_demo() if args.demo == "interrupt" else payload_collision()
    print(json.dumps(result, allow_nan=False))


if __name__ == "__main__":
    main()
