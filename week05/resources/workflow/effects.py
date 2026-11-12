"""Write one local ticket per approved action."""

from contextlib import closing
import sqlite3

from .approval import ApprovalError, checked_action, validate_decision
from .graph_state import canonical


class EffectStore:
    def __init__(self, path):
        self.path = path
        with closing(sqlite3.connect(path)) as database, database:
            database.execute(
                """CREATE TABLE IF NOT EXISTS tickets (
                    action_id TEXT PRIMARY KEY,
                    thread_id TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    reviewer TEXT NOT NULL
                )"""
            )

    def apply(self, state):
        grant = validate_decision(state, state.get("approval"))
        if grant["approved"] is not True or state["status"] != "approved":
            raise ApprovalError("The action has no valid approval.")
        action = checked_action(state)
        with closing(sqlite3.connect(self.path, timeout=5)) as database, database:
            database.execute("BEGIN IMMEDIATE")
            existing = database.execute(
                "SELECT payload_hash FROM tickets WHERE action_id = ?",
                (action["action_id"],),
            ).fetchone()
            if existing is None:
                database.execute(
                    "INSERT INTO tickets VALUES (?, ?, ?, ?, ?)",
                    (action["action_id"], state["thread_id"], action["payload_hash"],
                     canonical(action["payload"]), grant["reviewer"]),
                )
            elif existing[0] != action["payload_hash"]:
                raise ApprovalError("This action ID already has a different payload.")
        return {
            "action_id": action["action_id"],
            "payload_hash": action["payload_hash"],
            "reused": existing is not None,
        }

    def rows(self, thread_id):
        with closing(sqlite3.connect(self.path)) as database:
            database.row_factory = sqlite3.Row
            rows = database.execute(
                "SELECT action_id, payload_hash, reviewer FROM tickets WHERE thread_id = ?",
                (thread_id,),
            )
            return [dict(row) for row in rows]
