"""Fixed classroom data path; no model-supplied filename or credentials."""
import json
from pathlib import Path
from schemas import SpecArgs,SpecData,ToolFailure,success
SPEC_PATH=Path(__file__).resolve().parents[1]/'data'/'machine_specs.json'

def get_machine_spec(machine_id:str)->dict:
    args=SpecArgs.model_validate({'machine_id':machine_id})
    # BEGIN_SOLUTION W3.2
    try:
        document=json.loads(SPEC_PATH.read_text(encoding='utf-8'))
    except (OSError,ValueError) as exc:
        raise ToolFailure('DATA_UNAVAILABLE','The classroom specification file could not be read.') from exc
    row=document.get('machines',{}).get(args.machine_id)
    if row is None:
        raise ToolFailure('NOT_FOUND','This machine is not in the classroom specification file. No default limit was used.')
    data=SpecData.model_validate({'machine_id':args.machine_id,**row}).model_dump()
    return success(data,source='machine_specs.json',version=document['version'])
    # END_SOLUTION W3.2
