"""Choose the next node from the current state."""

TERMINAL = {"completed", "rejected", "failed", "stopped", "needs_input"}


def route_planner(s):
    return "Finish" if s["status"] in TERMINAL else "Execute"


def route_verify(s):
    """Prioritize terminal status, verified evidence, then retryable errors."""
    # TODO W5.1: Return Finish, PrepareApproval, Retry, or Planner.
    raise NotImplementedError("Complete W5.1 in workflow/routing.py.")


def route_retry(s):
    return "Finish" if s["status"] in TERMINAL else "Execute"


def route_approval(s):
    if s["status"] == "approved" and (s.get("approval") or {}).get("approved") is True:
        return "ApplyAction"
    return "Finish"
