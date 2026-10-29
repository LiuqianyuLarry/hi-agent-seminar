"""Slide p13 (three gates) and p17 (result envelope).

Strict Pydantic models: no silent casts, no extra keys.
The envelope ok/data/error is OUR course convention (slide p17) - not an API standard.
"""
import json
from pydantic import BaseModel, ConfigDict, Field

MACHINE_PATTERN = r"^(CONV|M)-\d{1,2}$"   # slide p13


class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class MaintenanceArgs(StrictModel):
    """Slide p13: strict=True + extra='forbid' + pattern + range."""
    machine_id: str = Field(pattern=MACHINE_PATTERN)
    max_records: int = Field(ge=1, le=10)


class SpecArgs(StrictModel):
    machine_id: str = Field(pattern=MACHINE_PATTERN)


class GapArgs(StrictModel):
    reading_c: float = Field(ge=-273.15, le=1000)
    limit_c: float = Field(ge=-273.15, le=1000)


def ok(data: dict, source: str) -> dict:
    """Slide p17: the envelope that makes mutated answers catchable."""
    return {"ok": True, "data": data, "source": source, "error": None}


def fail(code: str, message: str) -> dict:
    """Slide p19: stable error codes, honest wording."""
    return {"ok": False, "data": None, "source": None,
            "error": {"code": code, "message": message}}


def show(envelope: dict) -> str:
    return json.dumps(envelope, ensure_ascii=False, indent=2)
