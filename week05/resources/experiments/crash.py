"""Compare restart-from-beginning and checkpoint recovery with simulated failures."""

import json
import random
import re
from collections import Counter

REQUEST = "London -> Paris, 3 nights, budget 700 EUR"
FLIGHTS = [("AF1381", 189, "11:40"), ("BA0304", 142, "21:15"), ("U28411", 98, "07:05")]
HOTELS = [("Hotel Lumiere", 4.6, 210), ("Canal Loft", 4.1, 120), ("Gare Hostel", 3.2, 45)]
FAILURE_RATE = 0.10


class Crash(Exception):
    """End the current simulated attempt."""


class World:
    """Track simulated actions that survive a task restart."""

    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.steps = 0
        self.calls = 0
        self.charges = Counter()
        self.mails = Counter()

    def ask(self, task, state):
        self.calls += 1
        if task == "parse":
            nights, budget = re.findall(r"\d+", state["request"])
            return {"nights": int(nights), "budget": int(budget)}
        if task == "pick_flight":
            eligible = (flight for flight in state["flights"] if flight[2] < "20:00")
            return {"flight": min(eligible, key=lambda flight: flight[1])}
        if task == "pick_hotel":
            nightly_budget = (state["budget"] - state["flight"][1]) / state["nights"]
            eligible = (hotel for hotel in state["hotels"] if hotel[2] <= nightly_budget)
            return {"hotel": max(eligible, key=lambda hotel: hotel[1])}
        if task == "write":
            cost = state["flight"][1] + state["hotel"][2] * state["nights"]
            return {"letter": f"{state['flight'][0]} + {state['hotel'][0]}, total {cost} EUR"}
        raise ValueError(f"Unknown planning task: {task}")

    def charge(self, trip, item):
        self.charges[trip, item] += 1
        return {}

    def send(self, trip):
        self.mails[trip] += 1
        return {}


NODES = {
    "parse": lambda world, trip, state: world.ask("parse", state),
    "search_flights": lambda world, trip, state: {"flights": FLIGHTS},
    "pick_flight": lambda world, trip, state: world.ask("pick_flight", state),
    "book_flight": lambda world, trip, state: world.charge(trip, "flight"),
    "search_hotels": lambda world, trip, state: {"hotels": HOTELS},
    "pick_hotel": lambda world, trip, state: world.ask("pick_hotel", state),
    "book_hotel": lambda world, trip, state: world.charge(trip, "hotel"),
    "write": lambda world, trip, state: world.ask("write", state),
    "send": lambda world, trip, state: world.send(trip),
}
ORDER = list(NODES)
EDGES = dict(zip(ORDER, ORDER[1:] + ["END"]))


def step(world, node, trip, state):
    world.steps += 1
    draw = world.rng.random()
    if draw < FAILURE_RATE / 2:
        raise Crash("before action")
    update = NODES[node](world, trip, state)
    if draw < FAILURE_RATE:
        raise Crash("after action, before checkpoint")
    return update


def agent_loop(world, trip, checkpoints):
    state, position = {"request": REQUEST}, 0
    while position < len(ORDER):
        state.update(step(world, ORDER[position], trip, state))
        position += 1
    return state


def agent_graph(world, trip, checkpoints):
    if trip in checkpoints:
        state = json.loads(checkpoints[trip])
    else:
        state = {"request": REQUEST, "next": ORDER[0]}
    while state["next"] != "END":
        node = state["next"]
        state.update(step(world, node, trip, state))
        state["next"] = EDGES[node]
        checkpoints[trip] = json.dumps(state)
    return state


def run(strategy, seed, trips):
    agent = {"while": agent_loop, "graph": agent_graph}[strategy]
    world = World(seed)
    checkpoints = {}
    restarts = 0
    for trip in range(trips):
        while True:
            try:
                result = agent(world, trip, checkpoints)
            except Crash:
                restarts += 1
            else:
                break
        if result["letter"] != "U28411 + Canal Loft, total 458 EUR":
            raise RuntimeError("The simulated trip ended with an unexpected itinerary.")

    return {
        "strategy": strategy,
        "mean_steps": round(world.steps / trips, 4),
        "mean_planning_calls": round(world.calls / trips, 4),
        "mean_restarts": round(restarts / trips, 4),
        "extra_charges": sum(count - 1 for count in world.charges.values()),
        "trips_with_extra_charges": len({trip for (trip, item), count in world.charges.items() if count > 1}),
        "extra_emails": sum(count - 1 for count in world.mails.values()),
    }


def compare(strategy, seed, trips):
    success_rate = 1 - FAILURE_RATE
    attempts = len(ORDER)
    variants = ("while", "graph") if strategy == "both" else (strategy,)
    return {
        "experiment": "crash",
        "seed": seed,
        "trips": trips,
        "failure_rate": FAILURE_RATE,
        "expected_steps": {
            "while": (success_rate ** -attempts - 1) / FAILURE_RATE,
            "graph": attempts / success_rate,
        },
        "results": [run(variant, seed, trips) for variant in variants],
    }
