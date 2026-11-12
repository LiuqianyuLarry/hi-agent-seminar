"""Run one Week 5 workflow command in this Python process."""

import argparse
import json
import os
from pathlib import Path
import sqlite3


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, help="Folder for checkpoints.sqlite and effects.sqlite")
    parser.add_argument("--thread", help="Thread ID within that workspace")
    parser.add_argument("--crash-at", choices=("after_write",), help="Stop at the recovery exercise's crash point")
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("start", help="Create a fresh thread")
    start.add_argument("--report-only", action="store_true", help="Finish with a report and skip ticket approval")
    start.add_argument("--scenario", choices=("normal", "transient_once", "persistent"), default="normal")
    commands.add_parser("inspect", help="Read a thread's saved state")
    decide = commands.add_parser("decide", help="Resume a human approval with a JSON decision")
    decide.add_argument("--decision-file", type=Path, required=True)
    commands.add_parser("continue", help="Retry the saved node after an interrupted action")
    check = commands.add_parser("check", help="Test one exercise in isolation")
    check.add_argument("exercise", choices=("route", "edges", "approval", "resume"))
    return parser.parse_args()


def run(args):
    if args.command == "check":
        from .checks import check_exercise

        return check_exercise(args.exercise)

    from . import service

    if args.workspace is None or args.thread is None:
        raise ValueError("Provide both --workspace and --thread before the command.")
    if args.crash_at and args.command != "decide":
        raise ValueError("Use --crash-at only when testing an approval decision.")
    if args.command == "decide":
        reply = json.loads(args.decision_file.read_text(encoding="utf-8-sig"))
    with service.session(args.workspace, crash_at=args.crash_at) as (graph, effects):
        if args.command == "start":
            snapshot = service.start(graph, args.thread, create_ticket=not args.report_only, scenario=args.scenario)
        elif args.command == "inspect":
            snapshot = service.inspect(graph, args.thread)
        elif args.command == "decide":
            snapshot = service.decide(graph, args.thread, reply)
        else:
            snapshot = service.continue_run(graph, args.thread)
        return service.public_snapshot(snapshot, effects)


def main():
    from .nodes import SimulatedCrash

    args = arguments()
    try:
        # The lab runs locally with deterministic inputs and no tracing service.
        os.environ["LANGSMITH_TRACING"] = "false"
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        output = run(args)
        code = 0
    except SimulatedCrash as exc:
        output = {"error": type(exc).__name__, "message": str(exc), "pid": os.getpid()}
        code = 3
    except (ValueError, TypeError, OSError, ImportError, sqlite3.Error, AssertionError, NotImplementedError) as exc:
        output = {"error": type(exc).__name__, "message": str(exc), "pid": os.getpid()}
        code = 2
    print(json.dumps(output, allow_nan=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
