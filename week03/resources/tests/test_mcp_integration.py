"""Real subprocess/stdio test. Explicitly skipped if the pinned optional SDK is absent."""
import asyncio,importlib.metadata
import pytest
try:VERSION=importlib.metadata.version('mcp')
except importlib.metadata.PackageNotFoundError:VERSION=None
pytestmark=pytest.mark.skipif(VERSION!='2.2.0',reason='Real MCP requires optional mcp==2.2.0; not exercised by mocks')

def test_real_stdio_discovery_result_error_and_resource():
    from mcp_backend import MCPBackend
    async def run():
        async with MCPBackend() as backend:
            definition=await backend.definition();assert definition['function']['name']=='get_machine_spec'
            result=await backend.call_spec('CONV-3');assert result['data']['temperature_limit_c']==85
            bad=await backend.client.call_tool('get_machine_spec',{'machine_id':'CONV-99'})
            assert bad.is_error
            wrong=await backend.client.call_tool('get_machine_spec',{'machine_id':['CONV-3']})
            assert wrong.is_error
            note=await backend.client.read_resource('manual://CONV-3/temperature')
            assert any('85' in getattr(x,'text','') for x in note.contents)
    asyncio.run(asyncio.wait_for(run(),timeout=30))
