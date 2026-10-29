"""Slides p9 + p10: what we attach in message 1, and the description discipline.

model_tools() returns the array sent with the FIRST API call (slide p12).
Compare GOOD_DESCRIPTIONS with the vague get_data card on slide p10.
"""
import json

DESCRIPTIONS = {
    "query_maintenance": (
        "Return maintenance history for one machine, newest first. "
        "Reads the service database only - no live sensor values."),
    "get_machine_spec": (
        "Return the registered spec sheet and its data version - "
        "limits, ratings, source file. No repair history, no sensor readings."),
    "calculate_temperature_gap": (
        "Compute the difference between two given Celsius values. "
        "Both numbers must be supplied; never invents a reference value."),
}

BAD_DESCRIPTION = {"name": "get_data", "description": "Get equipment data."}


def model_tools() -> list[dict]:
    """The tools array from message 1 (slide p8) - DeepSeek nested function schema; application validation remains mandatory."""
    definitions = [
        {
            "type": "function",
            "name": "query_maintenance",
            "description": DESCRIPTIONS["query_maintenance"],
            "parameters": {
                "type": "object",
                "properties": {
                    "machine_id": {"type": "string",
                                   "description": "equipment id, e.g. CONV-3"},
                    "max_records": {"type": "integer",
                                    "minimum": 1, "maximum": 10},
                },
                "required": ["machine_id", "max_records"],
                "additionalProperties": False,
            },
        },
        {
            "type": "function",
            "name": "get_machine_spec",
            "description": DESCRIPTIONS["get_machine_spec"],
            "parameters": {
                "type": "object",
                "properties": {"machine_id": {"type": "string"}},
                "required": ["machine_id"],
                "additionalProperties": False,
            },
        },
        {
            "type": "function",
            "name": "calculate_temperature_gap",
            "description": DESCRIPTIONS["calculate_temperature_gap"],
            "parameters": {
                "type": "object",
                "properties": {
                    "reading_c": {"type": "number"},
                    "limit_c": {"type": "number"},
                },
                "required": ["reading_c", "limit_c"],
                "additionalProperties": False,
            },
        },
    ]

    return [{"type":"function", "function":{k:t[k] for k in ("name","description","parameters")}} for t in definitions]

if __name__ == "__main__":
    print(json.dumps(model_tools()[0], indent=2))
