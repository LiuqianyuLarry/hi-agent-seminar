"""Slide p30: test the MCP server with no LLM in the loop at all.

Run:      python check_server.py
Install:  pip install "mcp>=2"
"""
import asyncio
import sys
from pathlib import Path

try:
    from mcp import Client, StdioServerParameters
except ImportError:                                   # pragma: no cover
    raise SystemExit('pip install "mcp>=2"  then re-run this script')

SERVER = Path(__file__).resolve().parent / "mcp_server.py"

params = StdioServerParameters(
    command=sys.executable,
    args=[str(SERVER)],
)


async def main() -> None:
    async with Client(params) as client:
        tools = await client.list_tools()
        print([t.name for t in tools.tools])          # terminal 1, slide p30

        result = await client.call_tool(
            "get_machine_spec", {"machine_id": "CONV-3"})
        print(result.is_error, result.structured_content)   # terminal 2


if __name__ == "__main__":
    asyncio.run(main())
