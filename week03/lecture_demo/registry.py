"""Slide p14: only registered functions ever run.

The registry is the app's configuration, not the model's opinion.
No eval(), no exec(): model text never becomes code.
"""
from pydantic import ValidationError

from schemas import MaintenanceArgs, SpecArgs, GapArgs, fail
from tools import query_maintenance, get_machine_spec, calculate_temperature_gap

REGISTRY = {
    "query_maintenance": (MaintenanceArgs, query_maintenance),
    "get_machine_spec": (SpecArgs, get_machine_spec),
    "calculate_temperature_gap": (GapArgs, calculate_temperature_gap),
}

KNOWN_BUSINESS_ERRORS = {  # handler signals that are results, not crashes
    "UnknownMachine": "NOT_FOUND",
}


def run_tool(name: str, arguments_json: str) -> dict:
    entry = REGISTRY.get(name)
    if entry is None:                                     # gate 1: registered?
        return fail("UNKNOWN_TOOL", f"{name!r} is not in the registry")
    args_model, handler = entry
    try:                                                  # gate 2: arguments valid?
        args = args_model.model_validate_json(arguments_json)
    except ValidationError as exc:
        first = exc.errors()[0]
        return fail("INVALID_ARGUMENT",
                    f"{first['loc'][0]}: {first['msg']}")
    try:                                                  # gate 3: run the handler
        return handler(**args.model_dump())
    except Exception as exc:                              # business error -> envelope
        code = KNOWN_BUSINESS_ERRORS.get(type(exc).__name__, "TOOL_ERROR")
        return fail(code, str(exc))
