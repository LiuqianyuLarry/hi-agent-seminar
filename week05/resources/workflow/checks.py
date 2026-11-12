"""Check the small exercise functions without running the full workflow."""

from .approval import ApprovalError, make_action, validate_decision
from .graph_app import build_graph
from .graph_state import initial_state
from .routing import route_verify


def require(condition, description):
    if not condition:
        raise AssertionError(description)


def check_route():
    base = {"status": "running", "create_ticket": True}
    cases = (
        ("Terminal status takes priority", {**base, "status": "failed", "check": {"ready": True},
                                          "last_error": {"retryable": True}}, "Finish"),
        ("Verified evidence takes priority over a stale retry flag",
         {**base, "check": {"ready": True}, "last_error": {"retryable": True}}, "PrepareApproval"),
        ("A verified report needs no approval for a report-only task",
         {**base, "check": {"ready": True}, "create_ticket": False}, "Finish"),
        ("A retryable error takes the Retry edge", {**base, "last_error": {"retryable": True}}, "Retry"),
        ("Missing evidence sends the workflow back to Planner", base, "Planner"),
    )
    rows = []
    for label, state, expected in cases:
        actual = route_verify(state)
        require(actual == expected, f"{label}. Expected {expected}, got {actual}.")
        rows.append({"case": label, "state": state, "expected": expected, "actual": actual})
    return {"checks": [row["case"] for row in rows], "cases": rows}


def check_edges():
    edges = build_graph(None, None).get_graph().edges
    expected = {
        "Verify": {"Finish", "PrepareApproval", "Retry", "Planner"},
        "HumanApproval": {"ApplyAction", "Finish"},
    }
    rows = []
    for source, targets in expected.items():
        outgoing = [edge for edge in edges if edge.source == source]
        require({edge.target for edge in outgoing} == targets, f"{source} has the wrong destinations.")
        require(all(edge.conditional for edge in outgoing), f"{source} needs conditional edges.")
        for edge in sorted(outgoing, key=lambda edge: edge.target):
            rows.append({"source": edge.source, "target": edge.target, "conditional": edge.conditional})
    return {"checks": list(expected), "edges": rows}


def check_approval():
    state = initial_state("approval-check")
    state["report"] = {"machine_id": "CONV-3", "statistics": {"above_fraction": 0.8}}
    state["check"] = {"ready": True}
    pending = state["pending_action"] = make_action(state)
    base = {"action_id": pending["action_id"], "payload_hash": pending["payload_hash"], "reviewer": "Tutor"}
    rows = []
    for approved in (True, False):
        decision = validate_decision(state, {**base, "approved": approved})
        require(decision == {**base, "approved": approved} and decision["approved"] is approved,
                "A valid decision should keep its Boolean, reviewer and action binding.")
        rows.append({"case": "approve" if approved else "reject", "approved": approved, "accepted": True})

    invalid = {
        "string false": {"approved": "false"},
        "integer one": {"approved": 1},
        "wrong action ID": {"action_id": "another-action"},
        "wrong payload hash": {"payload_hash": "0" * 64},
        "blank reviewer": {"reviewer": "   "},
    }
    for label, fields in invalid.items():
        try:
            validate_decision(state, {**base, "approved": True, **fields})
        except ApprovalError as exc:
            rows.append({"case": label, "input": fields, "accepted": False, "reason": str(exc)})
        else:
            raise AssertionError(f"The validator accepted {label}.")

    changed = dict(state, report={"machine_id": "CONV-3", "statistics": {"above_fraction": 0.2}})
    changed_pending = changed["pending_action"] = make_action(changed)
    require(changed_pending["action_id"] == pending["action_id"], "The example must keep the same action ID.")
    require(changed_pending["payload_hash"] != pending["payload_hash"], "The changed report must have a new hash.")
    try:
        validate_decision(changed, {**base, "approved": True})
    except ApprovalError as exc:
        old_reason = str(exc)
    else:
        raise AssertionError("The validator reused an approval for a different report.")
    fresh_reply = {**base, "approved": True, "payload_hash": changed_pending["payload_hash"]}
    require(validate_decision(changed, fresh_reply) == fresh_reply,
            "A newly bound approval should be valid for the changed report.")
    rows.append({"case": "a changed report needs a new approval", "accepted": True,
                 "old_payload_hash": pending["payload_hash"], "new_payload_hash": changed_pending["payload_hash"],
                 "original_decision_rejected": True, "original_decision_reason": old_reason})
    return {"checks": [row["case"] for row in rows], "cases": rows}


def check_resume():
    from langgraph.types import Command

    from .service import config, resume_approval

    # This test double records one call. It does not open SQLite or submit an approval.
    calls = []
    returned = object()

    class SpyGraph:
        def invoke(self, input, config=None, *, durability=None):
            calls.append((input, config, durability))
            return returned

    saved_config = config("resume-unit-check")
    fixture = {
        "approved": False,
        "action_id": "unit-test-action",
        "payload_hash": "0" * 64,
        "reviewer": "Unit test",
    }
    expected_command = Command(resume=dict(fixture))
    result = resume_approval(SpyGraph(), saved_config, fixture)
    require(len(calls) == 1, "Resume should invoke the existing graph exactly once.")
    command, passed_config, durability = calls[0]
    require(command == expected_command, "Pass a Command with the validated decision as resume.")
    require(passed_config == config("resume-unit-check"), "Pass the same thread configuration to the graph.")
    require(durability == "sync", "Use synchronous durability for the resumed run.")
    require(result is returned, "Return the graph invocation result.")
    return {"checks": ["isolated invocation check", "Command with the decision", "same thread configuration",
                       "synchronous durability", "returns the invocation result"]}


def check_exercise(exercise):
    check = {"route": check_route, "edges": check_edges, "approval": check_approval, "resume": check_resume}[exercise]
    return {"exercise": exercise, "passed": True, **check()}
