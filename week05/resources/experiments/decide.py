"""Compare three planning strategies against the same simulated inventory."""

import random
from collections import Counter

CITIES = "NRT ICN LIS BER NBO CAI LIM BOG SYD AKL BOM DXB YYZ SEA OSL FCO DEL HAN UIO ACC".split()
LOOK, BOOK, BOTH = "search only", "book flight", "book flight and hotel"


def tasks():
    for origin, destination in zip(CITIES[::2], CITIES[1::2]):
        for kind in (LOOK, BOOK, BOTH):
            yield {
                "kind": kind,
                "origin": origin,
                "destination": destination,
                "text": f"{kind}: {origin} -> {destination}",
            }


def flights(origin, destination):
    return [{"id": f"{origin}{destination}{index}"} for index in range(3)]


def hotels(city):
    return [{"id": f"{city}-H{index}"} for index in range(3)]


class World:
    """Expose simulated tools and retain their observable results."""

    def __init__(self, sold_out):
        self.sold_out = sold_out
        self.log = []

    def call(self, tool, arguments):
        if tool == "flights":
            result = flights(arguments["origin"], arguments["destination"])
        elif tool == "hotels":
            result = hotels(arguments["city"])
        elif arguments.get("id") in self.sold_out:
            result = {"error": "sold_out"}
        else:
            result = {"ok": True}
        self.log.append((tool, arguments, result))
        return result


def ask(metrics, prompt, answer):
    """Count one planning call and return an answer produced by fixed rules."""
    metrics["planning_calls"] += 1
    metrics["input_characters"] += len(str(prompt))
    metrics["output_characters"] += len(str(answer))
    return answer


def action(tool, **arguments):
    return {"tool": tool, "args": arguments}


def find_flights(task):
    return action("flights", origin=task["origin"], destination=task["destination"])


def reflex(task, world, metrics):
    choice = ask(metrics, {"request": task["text"]}, find_flights(task))
    world.call(choice["tool"], choice["args"])


def next_option(history, search_tool, booking_tool):
    tried = {arguments["id"] for tool, arguments, _ in history if tool == booking_tool}
    options = next(result for tool, _, result in reversed(history) if tool == search_tool)
    return next(option["id"] for option in options if option["id"] not in tried)


def rule(task, history):
    if not history:
        return find_flights(task)
    tool, _, result = history[-1]
    if tool == "flights":
        if task["kind"] == LOOK:
            return action("finish")
        return action("book_flight", id=result[0]["id"])
    if tool == "book_flight":
        if "error" in result:
            return action("book_flight", id=next_option(history, "flights", tool))
        if task["kind"] == BOOK:
            return action("mail")
        return action("hotels", city=task["destination"])
    if tool == "hotels":
        return action("book_hotel", id=result[0]["id"])
    if tool == "book_hotel" and "error" in result:
        return action("book_hotel", id=next_option(history, "hotels", tool))
    if tool == "mail":
        return action("finish")
    return action("mail")


def react(task, world, metrics):
    history = []
    for _ in range(12):
        prompt = {"request": task["text"], "history": history}
        choice = ask(metrics, prompt, rule(task, history))
        if choice["tool"] == "finish":
            return
        tool, arguments = choice["tool"], choice["args"]
        history.append((tool, arguments, world.call(tool, arguments)))


def booking_steps(task, flight_id):
    steps = [action("book_flight", id=flight_id)]
    if task["kind"] == BOTH:
        steps += [
            action("hotels", city=task["destination"]),
            action("book_hotel", id=["hotels", 0, "id"]),
        ]
    return steps + [action("mail")]


def plan(task):
    steps = [find_flights(task)]
    if task["kind"] != LOOK:
        steps += booking_steps(task, ["flights", 0, "id"])
    return steps


def replan(task, history):
    failed_tool = history[-1][0]
    if failed_tool == "book_flight":
        return booking_steps(task, next_option(history, "flights", failed_tool))
    hotel_id = next_option(history, "hotels", failed_tool)
    return [action("book_hotel", id=hotel_id), action("mail")]


def resolve_argument(value, history):
    if not isinstance(value, list):
        return value
    result = {tool: result for tool, _, result in history}
    for key in value:
        result = result[key]
    return result


def planexec(task, world, metrics, replans=0):
    history = []
    steps = ask(metrics, {"request": task["text"]}, plan(task))
    while True:
        for step in steps:
            tool = step["tool"]
            arguments = {key: resolve_argument(value, history) for key, value in step["args"].items()}
            result = world.call(tool, arguments)
            history.append((tool, arguments, result))
            if "error" in result:
                break
        else:
            return
        if replans == 0:
            return
        replans -= 1
        prompt = {"request": task["text"], "history": history}
        steps = ask(metrics, prompt, replan(task, history))


def bookings(log):
    return [arguments["id"] for tool, arguments, result in log if tool.startswith("book_") and "ok" in result]


def completed(task, world):
    if task["kind"] == LOOK:
        return bool(world.log) and world.log[0][0] == "flights"
    options = [flights(task["origin"], task["destination"])]
    if task["kind"] == BOTH:
        options.append(hotels(task["destination"]))
    wanted = [next(option["id"] for option in choices if option["id"] not in world.sold_out) for choices in options]
    mail_count = sum(tool == "mail" for tool, _, _ in world.log)
    return bookings(world.log) == wanted and mail_count == 1


def inventory(scenario, seed):
    rng = random.Random(seed)
    for task in tasks():
        sold_out = set()
        if scenario == "sold-out" and task["kind"] != LOOK:
            if rng.random() < 0.5:
                sold_out.add(flights(task["origin"], task["destination"])[0]["id"])
            if task["kind"] == BOTH and rng.random() < 0.5:
                sold_out.add(hotels(task["destination"])[0]["id"])
        yield task, sold_out


def run(scenario, strategy, seed, replans):
    metrics = Counter()
    sample = None
    for task, sold_out in inventory(scenario, seed):
        world = World(sold_out)
        calls_before = metrics["planning_calls"]
        if strategy == "planexec":
            planexec(task, world, metrics, replans)
        else:
            {"reflex": reflex, "react": react}[strategy](task, world, metrics)
        success = completed(task, world)
        metrics["completed"] += success
        metrics["failed_with_bookings"] += not success and bool(bookings(world.log))
        # Choose a single common task to inspect across all strategies.
        sample_match = scenario == "baseline" or len(sold_out) == 2
        if sample is None and task["kind"] == BOTH and sample_match:
            sample = {
                "task": task["text"],
                "sold_out": sorted(sold_out),
                "completed": success,
                "planning_calls": metrics["planning_calls"] - calls_before,
                "tool_log": world.log,
            }
    return {"scenario": scenario, "strategy": strategy, "replans": replans, **metrics, "sample": sample}


def compare(scenario, strategy, seed, replans):
    scenarios = ("baseline", "sold-out") if scenario == "both" else (scenario,)
    strategies = ("reflex", "react", "planexec") if strategy == "all" else (strategy,)
    rows = []
    for condition in scenarios:
        for variant in strategies:
            if variant != "planexec":
                budgets = (None,)
            elif replans is not None:
                budgets = (replans,)
            else:
                budgets = (0, 1) if condition == "sold-out" else (0,)
            for budget in budgets:
                rows.append(run(condition, variant, seed, budget))
    return {"experiment": "decide", "seed": seed, "tasks": sum(1 for _ in tasks()), "results": rows}
