"""Slides p8, p12, p18, p37: the two-call flow with call_id pairing.

REPLAY mode (default, no API key): the model's reply is the canned call slip
from slide p8 - everything downstream (validate, registry, execute, envelope,
tool result) runs for real; message 4 is scripted, not a model answer.

LIVE mode: see live.py - DeepSeek by default (DEEPSEEK_API_KEY or .env),
used by demo scenes p3 / p12 / p37; fails explicitly when unavailable; replay is selected separately.
"""
import json

from registry import run_tool
from tool_definitions import model_tools

TASK = "What was done at CONV-3's last maintenance?"

CANNED_CALL = {                                    # slide p8, message 2
    "type": "function_call",
    "name": "query_maintenance",
    "arguments": '{"machine_id": "CONV-3", "max_records": 1}',
    "call_id": "call_01",
}

FINAL_ANSWER = ("In teaching_db_v1, CONV-3's latest recorded service is "
                "dated 2026-03-18: the cooling fan was replaced - record EV-104.")


def replay() -> dict:
    """The full trip from slide p37, executable without a model."""
    trace = [{"step": "user request", "detail": TASK}]
    trace.append({"step": "message 1 sent",
                  "detail": "task + %d tool schemas" % len(model_tools())})
    trace.append({"step": "message 2 received",
                  "detail": "%s(%s) call_id=%s" % (
                      CANNED_CALL["name"], CANNED_CALL["arguments"],
                      CANNED_CALL["call_id"])})
    result = run_tool(CANNED_CALL["name"], CANNED_CALL["arguments"])
    trace.append({"step": "step 3 executed",
                  "detail": "registry hit -> read-only SQLite -> envelope"})
    output_msg = {                                   # slide p8, message 3
        "role": "tool",
        "tool_call_id": CANNED_CALL["call_id"],
        "content": json.dumps(result, ensure_ascii=False),
    }
    trace.append({"step": "message 3 sent", "detail": "same call_id=%s"
                  % output_msg["tool_call_id"]})
    trace.append({"step": "message 4", "detail": FINAL_ANSWER})
    return {"trace": trace, "result": result,
            "output_message": output_msg, "answer": FINAL_ANSWER}


def live_available() -> bool:
    """True if a provider key is configured (see live.py for the setup)."""
    import live
    return live.provider() is not None
