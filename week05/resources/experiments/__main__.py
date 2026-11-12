"""Run the Week 5 simulations with Python's standard library."""

import argparse
import json

from . import crash, decide, redo


def positive_int(text):
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("The number of trips must be positive.")
    return value


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    experiments = parser.add_subparsers(dest="experiment", required=True)

    crash_parser = experiments.add_parser("crash", help="Compare two ways of recovering from a crash.")
    crash_parser.add_argument("--strategy", choices=("while", "graph", "both"), default="both")
    crash_parser.add_argument("--trips", type=positive_int, default=2000)

    decide_parser = experiments.add_parser("decide", help="Compare planning strategies against simulated inventory.")
    decide_parser.add_argument("--scenario", choices=("baseline", "sold-out", "both"), default="both")
    decide_parser.add_argument("--strategy", choices=("reflex", "react", "planexec", "all"), default="all")
    decide_parser.add_argument("--replans", type=int, choices=(0, 1, 2), help="Override the planexec replan budget.")

    redo_parser = experiments.add_parser("redo", help="Compare state commits and request keys.")
    redo_parser.add_argument("--write-as", choices=("in_place", "update", "both"), default="both")
    redo_parser.add_argument("--keys", choices=("none", "random", "stable", "all"), default="all")
    redo_parser.add_argument("--trips", type=positive_int, default=2000)

    for experiment in (crash_parser, decide_parser, redo_parser):
        experiment.add_argument("--seed", type=int, default=7)
        experiment.add_argument("--json", action="store_true", help="Print the full results as JSON.")

    args = parser.parse_args(argv)
    if args.experiment == "decide" and args.replans is not None and args.strategy in {"reflex", "react"}:
        decide_parser.error("--replans applies to planexec.")
    return args


def print_table(headers, rows):
    values = [["-" if value is None else str(value) for value in row] for row in rows]
    widths = [max(len(label), *(len(row[index]) for row in values)) for index, label in enumerate(headers)]

    def line(row):
        return "  ".join(value.ljust(width) for value, width in zip(row, widths)).rstrip()

    print(line(headers))
    print(line(["-" * width for width in widths]))
    for row in values:
        print(line(row))


def print_crash(result):
    print(f"Crash simulation. Seed {result['seed']}, {result['trips']} trips, nine steps per trip.")
    print(f"Failure probability per attempt: {result['failure_rate']:.0%}.")
    expected = result["expected_steps"]
    print(f"Expected attempts per completed trip: while {expected['while']:.2f}, graph {expected['graph']:.2f}.")
    print_table(
        ["Strategy", "Mean attempts", "Mean plan calls", "Mean restarts", "Extra charges", "Extra emails"],
        [
            [row[key] for key in ("strategy", "mean_steps", "mean_planning_calls", "mean_restarts", "extra_charges", "extra_emails")]
            for row in result["results"]
        ],
    )


def print_decide(result):
    print(f"Decide simulation. Seed {result['seed']}, {result['tasks']} tasks per row.")
    print("Planning calls count fixed-rule decisions.")
    print_table(
        ["Scenario", "Strategy", "Replans allowed", "Completed", "Plan calls", "Failed with bookings"],
        [
            [row[key] for key in ("scenario", "strategy", "replans", "completed", "planning_calls", "failed_with_bookings")]
            for row in result["results"]
        ],
    )
    for row in result["results"]:
        sample = row["sample"]
        if row["scenario"] != "sold-out" or sample is None:
            continue
        label = row["strategy"] if row["replans"] is None else f"{row['strategy']} ({row['replans']} replans)"
        print(f"\n{label}: {sample['task']}. Sold out: {', '.join(sample['sold_out'])}.")
        print(f"Planning calls: {sample['planning_calls']}. Completed: {'yes' if sample['completed'] else 'no'}.")
        for tool, arguments, output in sample["tool_log"]:
            print(f"  {tool} {arguments} -> {output}")


def print_redo(result):
    print(f"Redo simulation. Seed {result['seed']}, {result['trips']} trips, seven steps per trip.")
    print(f"Failure probability per attempt: {result['failure_rate']:.0%}.")
    print_table(
        ["Write mode", "Keys", "Wrong final states", "Repeated actions", "Extra charges", "Extra emails", "Blocked repeats"],
        [
            [row[key] for key in ("write_as", "keys", "wrong_final_states", "repeated_actions", "repeated_charges", "repeated_emails", "blocked_requests")]
            for row in result["results"]
        ],
    )


def main(argv=None):
    args = parse_args(argv)
    if args.experiment == "crash":
        result = crash.compare(args.strategy, args.seed, args.trips)
        display = print_crash
    elif args.experiment == "decide":
        result = decide.compare(args.scenario, args.strategy, args.seed, args.replans)
        display = print_decide
    else:
        result = redo.compare(args.write_as, args.keys, args.seed, args.trips)
        display = print_redo
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        display(result)


if __name__ == "__main__":
    main()
