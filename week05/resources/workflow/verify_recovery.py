"""Exercise real cross-process recovery in a disposable SQLite workspace."""

import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from .checks import require


def invoke(workspace, thread, *command, expected_code=0, crash_at=None):
    args = [sys.executable, "-m", "workflow", "--workspace", str(workspace), "--thread", thread]
    if crash_at:
        args.extend(("--crash-at", crash_at))
    result = subprocess.run(
        [*args, *command], capture_output=True, text=True, encoding="utf-8", timeout=30, check=False,
    )
    require(result.returncode == expected_code,
            f"{thread} {command[0]} exited {result.returncode}: {result.stdout or result.stderr}")
    return json.loads(result.stdout)


def decision_file(workspace, saved, approved):
    path = workspace / "decision.json"
    reply = {
        "approved": approved,
        "action_id": saved["action_id"],
        "payload_hash": saved["payload_hash"],
        "reviewer": "Recovery test",
    }
    path.write_text(json.dumps(reply), encoding="utf-8")
    return ("decide", "--decision-file", str(path))


def evidence_unchanged(first, second):
    for key in ("thread_id", "report", "observations", "tool_attempts", "action_id", "payload_hash"):
        require(first[key] == second[key], f"{key} changed across the checkpoint.")


def start_and_inspect(workspace, thread):
    first = invoke(workspace, thread, "start")
    saved = invoke(workspace, thread, "inspect")
    evidence_unchanged(first, saved)
    require(first["pid"] != saved["pid"], "Inspect should run in a new process.")
    require(first["checkpoint_id"] == saved["checkpoint_id"], "Inspect changed the checkpoint.")
    require(saved["status"] == "awaiting_approval" and saved["next"] == ["HumanApproval"],
            "The thread should be waiting at HumanApproval.")
    require(len(saved["interrupts"]) == 1 and saved["ticket_count"] == 0,
            "The approval request should be present with an empty ticket table.")
    return first, saved


def verify(workspace):
    start, pending = start_and_inspect(workspace, "approve")
    require(pending["tool_attempts"] == 3, "Three observations should be saved before approval.")
    require(pending["report"]["statistics"]["above_fraction"] == 0.8, "CONV-3 evidence differs from the lab data.")
    paused = {
        "start_pid": start["pid"],
        "inspect_pid": pending["pid"],
        "checkpoint_id": pending["checkpoint_id"],
        "observations": len(pending["observations"]),
    }

    approved = invoke(workspace, "approve", *decision_file(workspace, pending, True))
    evidence_unchanged(pending, approved)
    require(approved["status"] == "completed" and not approved["next"], "Approval should finish the workflow.")
    require(approved["ticket_count"] == 1 and approved["reused"] is False,
            "The approved action should create one ticket.")
    require(approved["tickets"][0]["action_id"] == pending["action_id"], "The ticket's action ID changed.")

    _, pending = start_and_inspect(workspace, "reject")
    rejected = invoke(workspace, "reject", *decision_file(workspace, pending, False))
    evidence_unchanged(pending, rejected)
    require(rejected["status"] == "rejected" and rejected["ticket_count"] == 0 and not rejected["next"],
            "Rejection should finish with an empty ticket table.")
    require(all(event["node"] != "ApplyAction" for event in rejected["trace"]),
            "The rejected action reached ApplyAction.")

    _, pending = start_and_inspect(workspace, "invalid")
    error = invoke(workspace, "invalid", *decision_file(workspace, pending, "false"), expected_code=2)
    require(error["error"] == "ApprovalError", "A string decision should fail validation.")
    invalid = invoke(workspace, "invalid", "inspect")
    evidence_unchanged(pending, invalid)
    require(invalid["checkpoint_id"] == pending["checkpoint_id"]
            and invalid["status"] == "awaiting_approval" and invalid["ticket_count"] == 0,
            "An invalid decision changed the pending thread.")

    _, pending = start_and_inspect(workspace, "recover")
    crash = invoke(workspace, "recover", *decision_file(workspace, pending, True),
                   expected_code=3, crash_at="after_write")
    require(crash["error"] == "SimulatedCrash", "The injected crash did not run.")
    interrupted = invoke(workspace, "recover", "inspect")
    evidence_unchanged(pending, interrupted)
    require(interrupted["next"] == ["ApplyAction"] and interrupted["ticket_count"] == 1,
            "The local ticket should be committed while ApplyAction is still pending.")
    resumed = invoke(workspace, "recover", "continue")
    evidence_unchanged(interrupted, resumed)
    require(resumed["pid"] != crash["pid"] and resumed["status"] == "completed" and not resumed["next"],
            "A fresh process should finish the saved action.")
    require(resumed["ticket_count"] == 1 and resumed["reused"] is True,
            "Retry should reuse the existing row.")
    require(resumed["tickets"] == interrupted["tickets"], "The durable ticket changed on retry.")

    return {
        "saved_approval": paused,
        "approved": {"pid": approved["pid"], "status": approved["status"], "ticket_count": approved["ticket_count"]},
        "rejected": {"pid": rejected["pid"], "status": rejected["status"], "ticket_count": rejected["ticket_count"]},
        "invalid": {"status": invalid["status"], "checkpoint_unchanged": True, "ticket_count": invalid["ticket_count"]},
        "crash_and_continue": {
            "crash_pid": crash["pid"],
            "inspect_pid": interrupted["pid"],
            "continue_pid": resumed["pid"],
            "ticket_count_before": interrupted["ticket_count"],
            "ticket_count_after": resumed["ticket_count"],
            "action_id": resumed["action_id"],
            "reused": resumed["reused"],
            "tool_attempts": resumed["tool_attempts"],
        },
    }


if __name__ == "__main__":
    with TemporaryDirectory(prefix="week05-recovery-") as directory:
        print(json.dumps(verify(Path(directory)), indent=2))
