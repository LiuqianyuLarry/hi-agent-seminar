"""Bind a decision to the exact verified action."""

import copy

from .graph_state import digest


class ApprovalError(ValueError):
    """An approval is absent, malformed, or tied to different evidence."""


def make_action(s):
    if not s.get("report") or s.get("check", {}).get("ready") is not True:
        raise ApprovalError("The report has not been verified.")
    payload = {
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


def checked_action(s):
    pending = s.get("pending_action")
    if pending != make_action(s):
        raise ApprovalError("The pending action no longer matches the verified report.")
    return pending


def approval_prompt(s):
    return {
        **checked_action(s),
        "question": "Approve one simulated review ticket for this verified report?",
    }


def validate_decision(s, reply):
    """Return a normalized decision after checking its type and action binding."""
    # TODO W5.3: Check the Boolean, action ID, payload hash, and reviewer label.
    raise NotImplementedError("Complete W5.3 in workflow/approval.py.")
