"""Local stdio server; logs must not pollute stdout. Optional resource illustrates context."""
from typing import Annotated, Any
from pydantic import Field,ValidationError
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from schemas import SpecArgs,ToolFailure
from tools.engineering import get_machine_spec as read_spec

server=MCPServer('EngineeringTools')

@server.tool(structured_output=True)
def get_machine_spec(machine_id:Annotated[str,Field(pattern=r'^CONV-[0-9]{1,3}$')])->dict[str, Any]:
    """Read the registered temperature reference, source and version; not live sensors."""
    # TODO W3.4: Validate and call read_spec; map known business failures to ToolError
    raise NotImplementedError("TODO W3.4: complete this step before full tests")
@server.resource('manual://CONV-3/temperature')
def temperature_note()->str:
    return ('Synthetic classroom register: CONV-3 temperature reference is 85 C, version classroom-v1.'
            'This is not a live measurement or evidence of a fault cause.')

if __name__=='__main__':server.run(transport='stdio')
