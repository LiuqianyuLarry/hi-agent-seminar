"""Direct MCP integration check, without any LLM request."""
import argparse,asyncio,json
from mcp_backend import MCPBackend,check_sdk

async def main(a):
    check_sdk()
    async with MCPBackend(a.server) as backend:
        definition=await backend.definition()
        # Demonstrate raw error flag as well as structured content.
        raw=await asyncio.wait_for(backend.client.call_tool('get_machine_spec',{'machine_id':a.machine}),15)
        report={'mode':'direct_mcp_no_llm','tool':definition,'is_error':raw.is_error,
                'structured_content':raw.structured_content,
                'text_blocks':[block.text for block in raw.content if getattr(block,'type','')=='text']}
        if a.read_resource:
            contents=await backend.client.read_resource('manual://CONV-3/temperature')
            report['resource_text']=[item.text for item in contents.contents if hasattr(item,'text')]
        print(json.dumps(report,ensure_ascii=False,indent=2))
        return 2 if raw.is_error else 0
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--machine',default='CONV-3');p.add_argument('--server')
    p.add_argument('--read-resource',action='store_true');a=p.parse_args()
    raise SystemExit(asyncio.run(main(a)))
