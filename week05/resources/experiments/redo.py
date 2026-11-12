"""Compare state commits and request keys in the simulated booking workflow."""

import json
import random
from collections import Counter

from .crash import Crash, FAILURE_RATE

TICKETS = [["Talks", 180, False], ["Full", 240, True], ["Full+Party", 310, True]]
ADD = {"spent", "log"}


class World:
    """Simulate a provider that can recognize repeated requests."""

    def __init__(self, seed, keys, failure_rate=FAILURE_RATE):
        self.rng = random.Random(seed)
        # Use a separate stream so changing keys cannot change the failure draws.
        self.key_rng = random.Random(seed + 99)
        self.keys = keys
        self.failure_rate = failure_rate
        self.done = Counter()
        self.receipts = {}
        self.blocked = 0

    def act(self, kind, trip, node, update):
        key = None
        if self.keys == "random":
            key = f"k{self.key_rng.getrandbits(40):x}"
        elif self.keys == "stable":
            key = f"{trip}:{node}"
        if key is not None and key in self.receipts:
            self.blocked += 1
            return self.receipts[key]
        self.done[trip, kind] += 1
        if key is not None:
            self.receipts[key] = update
        return update


def select_ticket(world, trip, state):
    eligible = (ticket[:2] for ticket in state["tickets"] if ticket[2])
    return {"ticket": min(eligible, key=lambda ticket: ticket[1])}


def pay_for_ticket(world, trip, state):
    update = {"spent": state["people"] * state["ticket"][1], "log": ["ticket paid"]}
    return world.act("ticket", trip, "pay_for_ticket", update)


def book_workshop(world, trip, state):
    update = {"spent": state["people"] * 45, "log": ["workshop booked"]}
    return world.act("seat", trip, "book_workshop", update)


def write_receipt(world, trip, state):
    ticket = state["ticket"][0]
    return {"receipt": f"{ticket} x{state['people']} + workshop, total {state['spent']} USD"}


NODES = {
    "read_request": lambda world, trip, state: {"people": 4},
    "search_tickets": lambda world, trip, state: {"tickets": TICKETS},
    "select_ticket": select_ticket,
    "pay_for_ticket": pay_for_ticket,
    "book_workshop": book_workshop,
    "write_receipt": write_receipt,
    "send_receipt": lambda world, trip, state: world.act("mail", trip, "send_receipt", {"log": ["receipt sent"]}),
}
ORDER = list(NODES)
EDGES = dict(zip(ORDER, ORDER[1:] + ["END"]))


def initial_state():
    return {"next": ORDER[0], "spent": 0, "log": []}


def merge(state, update):
    merged = dict(state)
    for key, value in update.items():
        merged[key] = state[key] + value if key in ADD else value
    return merged


def run_trip(world, trip, checkpoints, write_as):
    if write_as == "in_place":
        state = checkpoints.setdefault(trip, initial_state())
        history = None
    elif trip in checkpoints:
        saved = json.loads(checkpoints[trip])
        state, history = saved["state"], saved["history"]
    else:
        state, history = initial_state(), []

    while state["next"] != "END":
        node = state["next"]
        draw = world.rng.random()
        if draw < world.failure_rate / 2:
            raise Crash("before action")

        update = NODES[node](world, trip, state)
        if write_as == "in_place":
            state.update(merge(state, update))
        if draw < world.failure_rate:
            raise Crash("after action, before advancing next")

        if write_as == "in_place":
            state["next"] = EDGES[node]
        else:
            update = {**update, "next": EDGES[node]}
            state = merge(state, update)
            history.append(update)
            checkpoints[trip] = json.dumps({"state": state, "history": history})
    return state, history


def run(write_as, keys, seed, trips):
    expected, _ = run_trip(World(0, "none", failure_rate=0), 0, {}, "update")
    world = World(seed, keys)
    checkpoints = {}
    restarts = 0
    wrong = Counter()
    replay_matches = 0
    for trip in range(trips):
        while True:
            try:
                state, history = run_trip(world, trip, checkpoints, write_as)
            except Crash:
                restarts += 1
            else:
                break
        wrong["state"] += state != expected
        for field in ("spent", "log", "receipt"):
            wrong[field] += state[field] != expected[field]
        if history is not None:
            replayed = initial_state()
            for update in history:
                replayed = merge(replayed, update)
            replay_matches += replayed == state

    repeated_charges = sum(count - 1 for (_, kind), count in world.done.items() if kind != "mail")
    repeated_emails = sum(count - 1 for (_, kind), count in world.done.items() if kind == "mail")
    return {
        "write_as": write_as,
        "keys": keys,
        "mean_restarts": round(restarts / trips, 4),
        "wrong_final_states": wrong["state"],
        "wrong_spent": wrong["spent"],
        "wrong_log": wrong["log"],
        "wrong_receipt": wrong["receipt"],
        "repeated_actions": repeated_charges + repeated_emails,
        "repeated_charges": repeated_charges,
        "repeated_emails": repeated_emails,
        "blocked_requests": world.blocked,
        "replay_matches": replay_matches if write_as == "update" else None,
    }


def compare(write_as, keys, seed, trips):
    modes = ("in_place", "update") if write_as == "both" else (write_as,)
    rows = []
    for mode in modes:
        if keys != "all":
            policies = (keys,)
        elif mode == "in_place" and write_as == "both":
            policies = ("none",)
        else:
            policies = ("none", "random", "stable")
        rows.extend(run(mode, policy, seed, trips) for policy in policies)
    return {"experiment": "redo", "seed": seed, "trips": trips, "failure_rate": FAILURE_RATE, "results": rows}
