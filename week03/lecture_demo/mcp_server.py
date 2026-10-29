"""Slide p29: a minimal MCP server - reuse, don't rewrite.

Run:      python mcp_server.py            (stdio; it waits for a client - that is normal)
Install:  pip install "mcp>=2"
"""
try:
    from mcp.server import MCPServer
    from mcp.server.mcpserver.exceptions import ToolError
except ImportError:                                   # pragma: no cover
    raise SystemExit('pip install "mcp>=2"  (pinned SDK, as slide p28 notes)')

from tools import get_machine_spec as read_spec, UnknownMachine
from typing import Any

server = MCPServer("EngineeringTools")


@server.tool(structured_output=True)
def get_machine_spec(machine_id: str) -> dict[str, Any]:
    """Read the registered spec for one machine; no live sensor values."""
    try:
        envelope = read_spec(machine_id)
    except UnknownMachine as exc:                     # business error -> ToolError
        raise ToolError(f"machine not found: {exc}") from exc
    return envelope                                   # reuse, zero rewrite


@server.resource("machine://CONV-3/spec")
def conv3_spec_note() -> str:
    """Slide p32: a resource is read, selected, then included - never automatic."""
    return ("CONV-3 registered temperature limit 85.0 C, version class-v1, "
            "source machine_specs.json. Registration, not measurement.")


if __name__ == "__main__":
    server.run(transport="stdio")
