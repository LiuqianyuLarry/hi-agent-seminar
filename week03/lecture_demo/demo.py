"""Classroom scene runner - one command per slide.

    python demo.py            list scenes
    python demo.py p3         no-tools demo (select --mode live or --mode replay)
    python demo.py p15        run the scene for slide 15
    python demo.py p37        full traced trip (select --mode explicitly)
"""
import json
import sys

from schemas import show
from registry import run_tool, REGISTRY
from tools import (query_maintenance, get_machine_spec,
                   calculate_temperature_gap, DB_PATH)
from tool_definitions import model_tools, DESCRIPTIONS, BAD_DESCRIPTION
import flow
import live
MODE = "replay"


def hdr(title: str) -> None:
    print("\n" + "=" * 62 + f"\n{title}\n" + "=" * 62)


def _live_note() -> str | None:
    cfg = live.provider()
    return None if cfg is None else f"{cfg['name']} / {cfg['model']}"


def p3():
    hdr("PAGE 3 - NO TOOLS CONFIGURED")
    print(flow.TASK)
    if MODE == 'live':
        print('[LIVE DeepSeek]', live.ask_no_tools(flow.TASK))
    else:
        print('[SCRIPTED REPLAY] I cannot access the maintenance database without a connected tool.')
    print('Model speed does not grant database access.')


def p5():
    hdr("PAGE 5 - THREE TOOLS, ONE NARROW JOB EACH")
    for name in REGISTRY:
        print(f"  {name}")
    print("\n  sample calls:")
    print(" ", calculate_temperature_gap(97, 85)["data"])
    print(" ", get_machine_spec("CONV-3")["data"])
    print(" ", query_maintenance("CONV-3", 1)["data"]["records"][0])


def p9():
    hdr("PAGE 9 - THE SCHEMA ATTACHED IN MESSAGE 1")
    print(json.dumps(model_tools()[0], indent=2))
    print("\nfield -> consequence (right rail of the slide):")
    print("  name        must match the registry exactly (see p14)")
    print("  description the only text the model reads when choosing")
    print("  parameters  blanks the model fills + rules we enforce")
    print("  validation  Pydantic rejects extra arguments; no beta strict-generation flag is used")


def p10():
    hdr("PAGE 10 - DESCRIPTIONS WIN SELECTION")
    print("BAD:", json.dumps(BAD_DESCRIPTION))
    print("  -> both questions match it; selection becomes a coin toss\n")
    for name, text in DESCRIPTIONS.items():
        print(f"GOOD {name}:\n  {text}\n")


def p12():
    hdr("PAGE 12 - FIRST CALL PROPOSES A TOOL")
    if MODE == 'live':
        slips, message = live.first_call(flow.TASK)
        print('[LIVE DeepSeek]')
        print(json.dumps([c.model_dump(exclude_none=True) for c in message.tool_calls or []], indent=2))
        if not slips: print('No tool requested: auto allows this. Inspect whether it answers the task.')
    else:
        print('[SCRIPTED REPLAY]')
        call = flow.CANNED_CALL
        print(json.dumps({'id':call['call_id'],'type':'function','function':{'name':call['name'],'arguments':call['arguments']}},indent=2))
    print('arguments is JSON text. No Python function has executed yet.')


def p13():
    hdr("PAGE 13 - THREE GATES: TYPE, RANGE, INTENT")
    cases = [
        ('query_maintenance', '{"machine_id": "CONV-3", "max_records": "three"}', "type"),
        ('query_maintenance', '{"machine_id": "CONV-3", "max_records": 1000}', "range"),
        ('query_maintenance', '{"machine_id": "CONV-7", "max_records": 1}', "intent"),
    ]
    for name, args, gate in cases:
        r = run_tool(name, args)
        verdict = "PASSES structure (gate 3 is yours, not Pydantic's)" \
            if r["ok"] else r["error"]["message"]
        print(f"[{gate:6s}] {args}\n         -> {verdict}\n")


def p14():
    hdr("PAGE 14 - ONLY REGISTERED FUNCTIONS EVER RUN")
    for name in ('delete_records', 'exec', 'run_shell'):
        print(f"  {name!r:18s} ->", run_tool(name, "{}")["error"])


def p15():
    hdr("PAGE 15 - THE MODEL FILLS TWO BLANKS; THE SQL STAYS OURS")
    print(f"  database : {DB_PATH.name} (read-only URI, mode=ro)")
    print("  template : SELECT ... WHERE machine_id = ? ... LIMIT ?   (two blanks)")
    print("  result   :")
    print(show(query_maintenance("CONV-3", 3)))
    print("\n  CONV-7 has a row too - keep an eye on it for page 20:")
    print(show(query_maintenance("CONV-7", 1)))


def p16():
    hdr("PAGE 16 - CALCULATOR COMPUTES; SPEC TOOL SUPPLIES")
    print("  gap(97, 85)      ->", calculate_temperature_gap(97, 85)["data"])
    print("  spec('CONV-3')   ->", get_machine_spec("CONV-3")["data"])
    print("  spec('CONV-99')  ->", run_tool("get_machine_spec",
                                            '{"machine_id": "CONV-99"}')["error"])


def p17():
    hdr("PAGE 17 - DATA AND ITS PROVENANCE, ONE ENVELOPE")
    print(show(query_maintenance("CONV-3", 1)))
    print("\n  every field diffable against the slide's database row EV-104")


def p18():
    hdr("PAGE 18 - RESULT RETURNS UNDER THE SAME call_id")
    r = flow.replay()
    print("message 3:")
    print(json.dumps(r["output_message"], indent=2, ensure_ascii=False))


def p19():
    hdr("PAGE 19 - ZERO ROWS / QUERY FAILED / BAD ARGS / REFUSED")
    print("[ok, zero rows ]", run_tool("query_maintenance",
          '{"machine_id": "CONV-05", "max_records": 1}')["data"]["records"])
    print("[invalid args  ]", run_tool("query_maintenance",
          '{"machine_id": "CONV-3", "max_records": 1000}')["error"])
    print("[not registered]", run_tool("delete_records", "{}")["error"])
    print("\n  zero rows = a fact you may report;")
    print("  a failed query = unknown - NEVER 'no maintenance ever happened'.")


def p20():
    hdr("PAGE 20 - EXECUTED PERFECTLY, ON THE WRONG MACHINE")
    user_task = "CONV-3"
    slip = '{"machine_id": "CONV-7", "max_records": 1}'
    r = run_tool("query_maintenance", slip)
    rec = r["data"]["records"][0]
    print(f"  user asked      : {user_task}")
    print(f"  slip requested  : {slip}")
    print(f"  every gate      : passed (valid, registered, executed)")
    print(f"  returned record : {rec['record_id']} {rec['machine_id']} "
          f"{rec['service_date']} - {rec['action']}")
    print(f"\n  FUNCTION: executed   TASK: "
          f"{'MISMATCH - ' + rec['machine_id'] + ' is not ' + user_task}")
    print("  verdict comes from task-vs-trace, not from the absence of errors")


def p29():
    hdr("PAGE 29 - THE MINIMAL SERVER (code on this slide = mcp_server.py)")
    print("  open mcp_server.py next to the slide - ~12 new lines around read_spec")
    print("  business exception UnknownMachine -> ToolError (real failure, not fake success)")
    print("  run it:  python mcp_server.py        (stdio; it waits - that is normal)")


def p30():
    hdr("PAGE 30 - TEST THE SERVER WITH NO LLM")
    try:
        import mcp  # noqa: F401
    except ImportError:
        print('  pip install "mcp==2.2.0"  then:  python check_server.py')
        print("  expected output (slide p30):")
        print("    ['get_machine_spec']")
        print("    False {'machine_id': 'CONV-3', 'temperature_limit_c': 85.0, ...}")
        return
    import asyncio
    import check_server
    asyncio.run(check_server.main())


def p37():
    hdr("PAGE 37 - THE ANSWER TRACES BACK TO ITS RECORD")
    result = live.complete_trip(flow.TASK) if MODE == 'live' else flow.replay()
    print('[LIVE DeepSeek]' if MODE == 'live' else '[SCRIPTED REPLAY: final text is scripted]')
    for step in result['trace']: print(step['step'], ':', step['detail'])
    print(result['answer'])


SCENES = {name[1:]: fn for name, fn in list(globals().items())
          if name.startswith("p") and name[1:].isdigit() and callable(fn)}


def check():
    hdr("LIVE-MODE SELF CHECK")
    import os
    from pathlib import Path
    here = Path(__file__).resolve().parent
    for name in (".env", ".env.txt"):
        print(f"  {name:10s} exists = {(here / name).exists()}")
    key = os.environ.get("DEEPSEEK_API_KEY")
    print("  env DEEPSEEK_API_KEY :", "set" if key else "NOT set")
    try:
        import openai
        print("  openai installed     :", openai.__version__)
    except ImportError:
        print("  openai installed     : NO  ->  pip install openai")
    cfg = live.provider()
    print("  live.provider()      :",
          f"{cfg['name']} / {cfg['model']}" if cfg else "offline (replay only)")
    for hint in live.setup_help():
        print("  ->", hint)


def main():
    global MODE
    import argparse
    parser=argparse.ArgumentParser(description='CONV-3 lecture scenes using DeepSeek or explicit replay.')
    parser.add_argument('scene',nargs='?')
    parser.add_argument('--mode',choices=['live','replay'])
    args=parser.parse_args()
    if args.scene=='check':check();return
    if not args.scene or args.scene.removeprefix('p') not in SCENES:
        print('Scenes:', ' '.join('p'+s for s in sorted(SCENES)));return
    if args.scene in {'p3','p12','p37'} and not args.mode:
        parser.error('Select --mode live or --mode replay. No automatic fallback.')
    MODE=args.mode or 'replay'
    try:SCENES[args.scene.removeprefix('p')]()
    except Exception as exc:
        print('Scene failed:',type(exc).__name__,'. Check configuration; no replay fallback occurred.')
        raise SystemExit(2)


if __name__ == "__main__":
    main()
