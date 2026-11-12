"""Read the teaching data and return small updates from each graph node."""

from __future__ import annotations

import csv
import json
from math import fsum

from .approval import approval_prompt, make_action, validate_decision
from .graph_state import DATA, event

TOOLS = ("query_temperature", "get_machine_spec", "temperature_stats")
MAX_RETRIES = 1
MAX_TOOL_ATTEMPTS = 8


class SimulatedCrash(RuntimeError):
    """Stop a classroom process after its local side effect commits."""


def successful_observations(s):
    return {item["tool"]: item for item in s["observations"] if item["status"] == "ok"}


def query_temperature(task):
    with (DATA / "sensor_readings.csv").open(encoding="utf-8", newline="") as source:
        return [
            {"ts": row["ts"], "temperature_c": float(row["temperature_c"])}
            for row in csv.DictReader(source)
            if row["machine_id"] == task["machine_id"]
            and task["start"] <= row["ts"] < task["end"]
        ]


def get_machine_spec(machine_id):
    specs = json.loads((DATA / "machine_specs.json").read_text(encoding="utf-8"))
    return specs["machines"][machine_id]


def temperature_stats(values, limit):
    count = len(values)
    above_count = sum(value > limit for value in values)
    return {
        "count": count,
        "limit_c": limit,
        "above_count": above_count,
        "above_fraction": above_count / count,
        "mean_c": fsum(values) / count,
        "max_c": max(values),
    }


def statistics_arguments(observed):
    return {
        "values": [row["temperature_c"] for row in observed["query_temperature"]["result"]],
        "limit": observed["get_machine_spec"]["result"]["temperature_limit_c"],
    }


class Nodes:
    def __init__(self, effects, *, suspend, crash_at=None):
        self.effects = effects
        self.suspend = suspend
        self.crash_at = crash_at

    def planner(self, s):
        observed = successful_observations(s)
        decision = next(name for name in TOOLS if name not in observed)
        return {
            "decision": decision,
            "trace": [event("Planner", "decision", tool=decision)],
        }

    def execute(self, s):
        if s["tool_attempts"] >= MAX_TOOL_ATTEMPTS:
            return {"status": "stopped", "reason": "tool_attempt_limit"}
        name = s["decision"]
        task = s["task"]
        attempt = s["tool_attempts"] + 1
        retryable = name == "query_temperature" and (
            s["scenario"] == "persistent"
            or s["scenario"] == "transient_once" and s["retry_total"] == 0
        )
        if retryable:
            arguments = dict(task)
            result = {"code": "TEMPORARY_UNAVAILABLE"}
        elif name == "query_temperature":
            arguments = dict(task)
            result = query_temperature(task)
        elif name == "get_machine_spec":
            arguments = {"machine_id": task["machine_id"]}
            result = get_machine_spec(**arguments)
        else:
            arguments = statistics_arguments(successful_observations(s))
            result = temperature_stats(**arguments)
        observation = {
            "id": f"obs-{attempt}",
            "tool": name,
            "arguments": arguments,
            "result": result,
            "status": "error" if retryable else "ok",
        }
        return {
            "tool_attempts": attempt,
            "observations": [*s["observations"], observation],
            "last_error": {"retryable": retryable},
            "trace": [event("Execute", "observation", observation_id=observation["id"], tool=name)],
        }

    def verify(self, s):
        observed = successful_observations(s)
        missing = [name for name in TOOLS if name not in observed]
        check = {"ready": False, "missing": missing}
        update = {"check": check, "trace": [event("Verify", "check", check=check)]}
        if "query_temperature" in observed and not observed["query_temperature"]["result"]:
            update.update(status="needs_input", reason="no_readings")
        elif not missing:
            arguments = statistics_arguments(observed)
            stats = observed["temperature_stats"]
            correct = (
                observed["query_temperature"]["arguments"] == s["task"]
                and observed["get_machine_spec"]["arguments"] == {"machine_id": s["task"]["machine_id"]}
                and stats["arguments"] == arguments
                and stats["result"] == temperature_stats(**arguments)
            )
            check["ready"] = correct
            if correct:
                update["report"] = {
                    "machine_id": s["task"]["machine_id"],
                    "statistics": stats["result"],
                    "evidence_ids": [observed[name]["id"] for name in TOOLS],
                }
                update["status"] = "ready_for_approval" if s["create_ticket"] else "completed"
            else:
                update.update(status="failed", reason="evidence_mismatch")
        return update

    def retry(self, s):
        if s["retry_total"] >= MAX_RETRIES:
            return {"status": "failed", "reason": "retry_exhausted", "trace": [event("Retry", "exhausted")]}
        return {
            "retry_total": s["retry_total"] + 1,
            "trace": [event("Retry", "retry", retry_total=s["retry_total"] + 1)],
        }

    def prepare_approval(self, s):
        action = make_action(s)
        return {
            "pending_action": action,
            "status": "awaiting_approval",
            "trace": [event("PrepareApproval", "prepared", action_id=action["action_id"])],
        }

    def human_approval(self, s):
        reply = self.suspend(approval_prompt(s))
        grant = validate_decision(s, reply)
        return {
            "approval": grant,
            "status": "approved" if grant["approved"] is True else "rejected",
            "trace": [event("HumanApproval", "decision", approved=grant["approved"])],
        }

    def apply_action(self, s):
        ticket = self.effects.apply(s)
        if self.crash_at == "after_write":
            raise SimulatedCrash("Stopped after ticket commit and before the graph saved the node result.")
        return {
            "ticket": ticket,
            "status": "completed",
            "trace": [event("ApplyAction", "ticket", **ticket)],
        }

    def finish(self, s):
        return {"trace": [event("Finish", "finished", status=s["status"])]}
