"""Serializable state and the append reducer used by the graph."""

from __future__ import annotations

import hashlib
import json
import operator
from pathlib import Path
import re
from typing import Annotated, TypedDict

VERSION = 1
DATA = Path(__file__).resolve().parent / "data"
MACHINE = "CONV-3"
START_TIME = "2026-03-02T10:00:00+08:00"
END_TIME = "2026-03-02T10:25:00+08:00"


class AgentState(TypedDict, total=False):
    schema_version: int
    data_fingerprint: str
    thread_id: str
    task: dict
    create_ticket: bool
    scenario: str
    status: str
    reason: str
    decision: str
    last_error: dict
    check: dict
    report: dict | None
    pending_action: dict | None
    approval: dict | None
    ticket: dict | None
    tool_attempts: int
    retry_total: int
    observations: list[dict]
    trace: Annotated[list[dict], operator.add]


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def data_fingerprint():
    names = ("sensor_readings.csv", "machine_specs.json")
    return digest({name: hashlib.sha256((DATA / name).read_bytes()).hexdigest() for name in names})


def validate_thread_id(thread_id):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", thread_id):
        raise ValueError("Use a thread ID of 1-64 letters, digits, underscores, or hyphens.")


def initial_state(thread_id, *, create_ticket=True, scenario="normal"):
    validate_thread_id(thread_id)
    return AgentState(
        schema_version=VERSION,
        data_fingerprint=data_fingerprint(),
        thread_id=thread_id,
        task={"machine_id": MACHINE, "start": START_TIME, "end": END_TIME},
        create_ticket=create_ticket,
        scenario=scenario,
        status="running",
        check={"ready": False},
        last_error={},
        observations=[],
        trace=[],
        tool_attempts=0,
        retry_total=0,
    )


def assert_compatible(state, thread_id):
    if not state:
        raise ValueError("No saved checkpoint for this thread.")
    if state.get("thread_id") != thread_id or state.get("schema_version") != VERSION:
        raise ValueError("Checkpoint thread or state version does not match.")
    if state.get("data_fingerprint") != data_fingerprint():
        raise ValueError("The teaching data changed. Review it in a new thread.")


def event(node, kind, **details):
    return {"node": node, "kind": kind, **details}
