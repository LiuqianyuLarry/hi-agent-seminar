"""Fixed classroom data path; no model-supplied filename or credentials."""
import json
from pathlib import Path
from schemas import SpecArgs,SpecData,ToolFailure,success
SPEC_PATH=Path(__file__).resolve().parents[1]/'data'/'machine_specs.json'

def get_machine_spec(machine_id:str)->dict:
    args=SpecArgs.model_validate({'machine_id':machine_id})
    # TODO W3.2: Read fixed SPEC_PATH; unknown device is NOT_FOUND; preserve version
    raise NotImplementedError("TODO W3.2: complete this step before full tests")