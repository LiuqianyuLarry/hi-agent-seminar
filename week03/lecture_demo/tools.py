"""The three tools from slide p5 - one narrow job each.

  calculate_temperature_gap : pure Python arithmetic (p16) - never invents an 85
  query_maintenance         : read-only SQL (p15) - fixed template, bound values
  get_machine_spec          : registered spec file (p16) - registrations, not sensors

Unknown machine is a BUSINESS error (p16 red line) - never a default 85.
"""
import json
import sqlite3
from pathlib import Path

from schemas import MaintenanceArgs, SpecArgs, GapArgs, ok, fail

DATA = Path(__file__).resolve().parent / "data"
DB_PATH = DATA / "teaching_db_v1.sqlite"
SPEC_PATH = DATA / "machine_specs.json"


class UnknownMachine(Exception):
    """Slide p29: mapped to ToolError by the MCP server."""


def calculate_temperature_gap(reading_c: float, limit_c: float) -> dict:
    GapArgs.model_validate({"reading_c": reading_c, "limit_c": limit_c})
    return ok({"reading_c": reading_c, "limit_c": limit_c,
               "difference_c": round(reading_c - limit_c, 2)},
              source="python")


def query_maintenance(machine_id: str, max_records: int) -> dict:
    args = MaintenanceArgs.model_validate(
        {"machine_id": machine_id, "max_records": max_records})
    SQL = (
        "SELECT record_id, machine_id, service_date, action "
        "FROM maintenance_event WHERE machine_id = ? "
        "ORDER BY service_date DESC, record_id DESC LIMIT ?"
    )                                                    # slide p15: our SQL, two blanks
    uri = f"file:{DB_PATH}?mode=ro"                     # read-only connection
    conn = sqlite3.connect(uri, uri=True)
    try:
        rows = conn.execute(SQL, (args.machine_id, args.max_records)).fetchall()
    finally:
        conn.close()
    records = [{"record_id": r[0], "machine_id": r[1],
                "service_date": r[2], "action": r[3]} for r in rows]
    return ok({"machine_id": args.machine_id, "records": records},
              source="teaching_db_v1")


def get_machine_spec(machine_id: str) -> dict:
    args = SpecArgs.model_validate({"machine_id": machine_id})
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    machine = spec["machines"].get(args.machine_id)
    if machine is None:                                  # CONV-99 -> business error
        raise UnknownMachine(f"no registered spec for {args.machine_id}")
    return ok({"machine_id": args.machine_id,
               "temperature_limit_c": machine["temperature_limit_c"],
               "spec_version": spec["version"],
               "source": SPEC_PATH.name},
              source=SPEC_PATH.name)
