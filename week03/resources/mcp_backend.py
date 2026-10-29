"""Official MCP Python SDK v2.2.0 adapter. Optional dependency; no silent local fallback."""
import asyncio,copy,importlib.metadata,os,sys
from pathlib import Path
from schemas import ToolResult,SpecArgs,ToolFailure
ROOT=Path(__file__).resolve().parent

def check_sdk():
    try: version=importlib.metadata.version('mcp')
    except importlib.metadata.PackageNotFoundError as exc:
        raise RuntimeError('Install requirements-mcp.txt in this environment first.') from exc
    if version!='2.2.0':
        raise RuntimeError(f'This lab targets mcp==2.2.0, installed={version}. Do not mix v1/v2 examples.')

def server_parameters(server_path=None):
    check_sdk()
    from mcp import StdioServerParameters
    # Do not pass API keys to the classroom server subprocess.
    keys=['PATH','SYSTEMROOT','WINDIR','HOME','USERPROFILE','TEMP','TMP','PYTHONPATH','VIRTUAL_ENV']
    safe_env={k:os.environ[k] for k in keys if k in os.environ}
    safe_env['PYTHONIOENCODING']='utf-8'
    return StdioServerParameters(command=sys.executable,
            args=[str(Path(server_path or ROOT/'mcp_server.py').resolve())],env=safe_env)

def unpack_result(result):
    if result.is_error:
        raise ToolFailure('MCP_TOOL_ERROR','MCP reported a tool failure. No specification data was confirmed.')
    if not isinstance(result.structured_content,dict):
        raise ToolFailure('INVALID_RESULT','MCP did not return the required structured object.')
    return ToolResult.model_validate(result.structured_content).model_dump()

def adapt_spec_tool(tool):
    """Only adapt the one scalar-argument tool this lab explicitly supports."""
    if tool.name!='get_machine_spec':raise ValueError('Unsupported MCP tool')
    schema=copy.deepcopy(tool.input_schema)
    if schema.get('type')!='object' or set(schema.get('properties',{}))!={'machine_id'}:
        raise ValueError('Unexpected MCP argument schema; review rather than silently discard constraints')
    prop=schema['properties']['machine_id']
    if prop.get('type')!='string' or any(k in schema or k in prop for k in ['$ref','$defs','oneOf','anyOf']):
        raise ValueError('This teaching adapter supports a simple string only')
    schema.pop('title',None);prop.pop('title',None)
    if 'default' in prop:raise ValueError('Optional/default MCP arguments need a deliberate adaptation')
    schema['required']=['machine_id'];schema['additionalProperties']=False
    # Local stricter validation remains in the executor; it is not removed by this conversion.
    return {'type':'function','function':{'name':tool.name,'description':tool.description or 'Read the classroom equipment register.',
            'parameters':schema}}

class MCPBackend:
    def __init__(self,server_path=None):self.server_path=server_path;self.client=None
    async def __aenter__(self):
        from mcp import Client
        self.client=Client(server_parameters(self.server_path))
        # Enter and exit in the same task: MCP transports may own task-local cancel scopes.
        async with asyncio.timeout(15):
            await self.client.__aenter__()
        return self
    async def __aexit__(self,*args):
        return await self.client.__aexit__(*args)
    async def definition(self):
        cursor=None
        while True:
            page=await asyncio.wait_for(self.client.list_tools(cursor=cursor),timeout=15)
            for tool in page.tools:
                if tool.name=='get_machine_spec':return adapt_spec_tool(tool)
            cursor=page.next_cursor
            if cursor is None:raise ToolFailure('UNKNOWN_TOOL','The MCP server did not register the specification tool.')
    async def call_spec(self,machine_id):
        SpecArgs.model_validate({'machine_id':machine_id})
        result=await asyncio.wait_for(self.client.call_tool('get_machine_spec',{'machine_id':machine_id}),timeout=15)
        return unpack_result(result)
