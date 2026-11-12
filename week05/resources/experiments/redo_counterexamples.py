"""Run small changes to Redo in this process and report what breaks."""

import json
from itertools import chain, repeat
from types import SimpleNamespace
from unittest.mock import patch

from . import redo


def whole_log_as_update():
    """Pass the previous events back to an append reducer and observe the duplicate."""
    state = {"log": ["verified"]}
    old_and_new = {"log": ["verified", "prepared"]}
    new_only = {"log": ["prepared"]}
    return {
        "change": "Return both the saved and new event instead of just the new event.",
        "old_log": state["log"],
        "wrong_update": old_and_new["log"],
        "wrong_result": redo.merge(state, old_and_new)["log"],
        "correct_update": new_only["log"],
        "correct_result": redo.merge(state, new_only)["log"],
    }


def next_in_add():
    """Add next instead of replacing it, then try to run the graph."""
    checkpoints = {}
    world = redo.World(0, "none", failure_rate=0)
    with patch.object(redo, "ADD", redo.ADD | {"next"}):
        try:
            redo.run_trip(world, 0, checkpoints, "update")
        except KeyError as error:
            merged_next = json.loads(checkpoints[0])["state"]["next"]
            if error.args != (merged_next,):
                raise
            return {
                "change": 'Add "next" to ADD.',
                "merged_next": merged_next,
                "error": type(error).__name__,
                "message": str(error),
            }
    raise AssertionError("Adding next to ADD should produce an unknown node name.")


def spent_not_in_add():
    """Remove spent from ADD and compare with a total calculated separately."""
    # The example buys four $240 tickets and four $45 workshop seats.
    ticket_cost = 4 * 240
    workshop_cost = 4 * 45
    expected = ticket_cost + workshop_cost
    trips = 2000
    baseline, _ = redo.run_trip(redo.World(0, "none", failure_rate=0), 0, {}, "update")
    if baseline["spent"] != expected:
        raise AssertionError("The original booking no longer matches the example total.")
    with patch.object(redo, "ADD", redo.ADD - {"spent"}):
        observed, _ = redo.run_trip(redo.World(0, "none", failure_rate=0), 0, {}, "update")
        result = redo.run("update", "none", seed=7, trips=trips)
    return {
        "change": 'Remove "spent" from ADD.',
        "ticket_cost_usd": ticket_cost,
        "workshop_cost_usd": workshop_cost,
        "expected_total_usd": expected,
        "observed_total_usd": observed["spent"],
        "receipt": observed["receipt"],
        "trips": trips,
        "wrong_spent": result["wrong_spent"],
    }


def interrupted_trip(write_as):
    """Stop just after the ticket charge, then restart the same simulated trip."""
    trip = 17
    world = redo.World(7, "none")
    checkpoints = {}
    draws = chain((0.99, 0.99, 0.99, 0.075), repeat(0.99))
    world.rng = SimpleNamespace(random=draws.__next__)
    try:
        redo.run_trip(world, trip, checkpoints, write_as)
    except redo.Crash as error:
        if str(error) != "after action, before advancing next":
            raise
    else:
        raise AssertionError("Expected an interruption after the ticket charge.")
    saved = checkpoints[trip]
    state = json.loads(saved)["state"] if write_as == "update" else saved
    after_crash = {
        "next": state["next"],
        "spent_usd": state["spent"],
        "ticket_charges": world.done[trip, "ticket"],
    }
    final, _ = redo.run_trip(world, trip, checkpoints, write_as)
    return {
        "after_crash": after_crash,
        "after_resume": {"next": final["next"], "spent_usd": final["spent"],
                         "ticket_charges": world.done[trip, "ticket"]},
    }


def main():
    print(json.dumps({
        "whole_log_as_update": whole_log_as_update(),
        "next_in_add": next_in_add(),
        "spent_not_in_add": spent_not_in_add(),
        "partial_commit": {
            "trip": 17,
            "change": "Stop after the first ticket charge, before advancing next.",
            "in_place": interrupted_trip("in_place"),
            "update": interrupted_trip("update"),
        },
    }))


if __name__ == "__main__":
    main()
