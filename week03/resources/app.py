"""DeepSeek or explicit scripted replay; local or MCP tool routing."""
import argparse
import asyncio
import json
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from executor import Executor
from replay_api import ScriptedCompletions
from tool_definitions import model_tools
from workflow import run_turn
from provider import load_environment
ROOT=Path(__file__).resolve().parent


@asynccontextmanager
async def routes(route):
    if route=='local':yield None,None
    else:
        from mcp_backend import MCPBackend,check_sdk
        check_sdk()
        async with MCPBackend() as backend:yield backend.call_spec,await backend.definition()


async def execute(a):
    load_environment()
    cases=json.loads((ROOT/'cases/tasks.json').read_text(encoding='utf-8'))
    case=next((c for c in cases if c['id']==a.case),None) if a.case else None
    client=None
    if a.mode=='replay':
        if case is None or a.question:raise ValueError('Replay needs a known --case and no --question.')
        api=ScriptedCompletions(case);model='SCRIPTED_REPLAY';question=case['question']
    else:
        question=a.question or (case['question'] if case else None)
        if not question:raise ValueError('Live mode needs --question or --case.')
        key=os.getenv('DEEPSEEK_API_KEY')
        if not key:raise ValueError('Configure DEEPSEEK_API_KEY privately before live calls.')
        model=os.getenv('DEEPSEEK_MODEL','deepseek-flash')
        from openai import OpenAI
        client=OpenAI(api_key=key,base_url='https://api.deepseek.com',timeout=30,max_retries=0)
        api=client.chat.completions
    trace={'mode':a.mode,'route':a.route,'question':question,'status':'not_started'}
    try:
        async with routes(a.route) as (remote,definition):
            definitions=model_tools()
            if definition:definitions=[definition if t['function']['name']=='get_machine_spec' else t for t in definitions]
            trace=await run_turn(api,model,question,Executor(remote_spec=remote),mode=a.mode,tools=definitions)
            trace['route']=a.route
            if a.case:trace['case_id']=a.case
    except Exception as exc:
        trace.update(status='connection_or_setup_error',error_type=type(exc).__name__,
                     answer='Connection or setup failed. No local or replay fallback occurred.')
    finally:
        if client is not None:client.close()
    out=Path(a.out) if a.out else ROOT/'traces'/f'{a.mode}_{a.route}_{uuid.uuid4().hex}.json'
    if out.exists():raise ValueError('Trace already exists; do not overwrite evidence.')
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(trace,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    print(trace.get('answer','No answer'));print('Trace:',out)
    return trace


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['live','replay'],required=True)
    p.add_argument('--route',choices=['local','mcp'],default='local');p.add_argument('--case');p.add_argument('--question');p.add_argument('--out')
    try:trace=asyncio.run(execute(p.parse_args()))
    except (ValueError,ImportError) as exc:p.exit(2,str(exc)+'\n')
    raise SystemExit(0 if trace['status'] in {'completed','no_tool'} else 2)
