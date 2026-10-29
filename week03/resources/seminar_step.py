"""Bounded task runner. A live error never falls back to replay or local MCP bypass."""
import argparse
import asyncio
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parent


def check_tests(expression, out, files=None):
    result=subprocess.run([sys.executable,'-m','pytest',*(files or ['tests/test_tools.py']),'-q','-p','no:cacheprovider','-k',expression],
                          cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90)
    log=out/'tests.txt';log.write_text(result.stdout+result.stderr,encoding='utf-8')
    print(result.stdout+result.stderr)
    return {'kind':'local_tests','passed':result.returncode==0,'returncode':result.returncode,'log':str(log)}


async def example(name,out):
    from executor import Executor
    cases=json.loads((ROOT/'cases/tasks.json').read_text(encoding='utf-8'))
    call=next(c['call'] for c in cases if c['id']==name)
    result=await Executor().execute(call['name'],call['arguments'])
    (out/'tool_result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


async def model_case(case,out,mode='live',route='local',question=None,label=None):
    from app import execute
    result=await execute(SimpleNamespace(mode=mode,route=route,case=case,question=question,out=str(out/((label or case)+'.json'))))
    calls=result.get('calls',[])
    expected={'spec':'get_machine_spec','query':'query_temperature','stats':'temperature_stats'}[case]
    good=result.get('status')=='completed' and len(calls)==1 and calls[0]['name']==expected
    return {'kind':mode,'case':case,'route':route,'passed':good,'status':result.get('status'),
            'note':'Passing the pipeline does not replace manual intent and answer checks.'}


async def run(task,out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    report_path=out/'report.json'
    if report_path.exists():raise ValueError('Do not overwrite a task report.')
    checks=[]
    if task in {'t02','t03','t04'}:
        case={'t02':'stats','t03':'spec','t04':'query'}[task]
        expression={'t02':'stats or strictly_greater or bad_values','t03':'spec or model_supplied or valid_wrong','t04':'query or time or empty or rows or database'}[task]
        checks.append(check_tests(expression,out))
        await example(case,out)
    elif task=='t05':
        checks.append(await model_case('spec',out,mode='replay'))
        checks.append(check_tests('',out,['tests/test_workflow.py']))
    elif task=='t06':
        for case in ['spec','query','stats']:
            checks.append(await model_case(case,out))
            if not checks[-1]['passed']:break
    elif task=='t07':
        from failure_demo import main
        await main(str(out/'injected_failures.json'))
        checks.append(await model_case('spec',out,label='after_edit'))
        if checks[-1]['passed']:
            checks.append(await model_case('spec',out,question='What temperature reference is registered for CONV-3? Include the source and version.',label='paraphrase'))
    elif task=='t08':
        # Explicit import/version check prevents a skipped integration test counting as a pass.
        from mcp_backend import check_sdk
        check_sdk()
        checks.append(check_tests('',out,['tests/test_mcp_contract.py','tests/test_mcp_integration.py']))
        if checks[-1]['passed']:
            from mcp_client import main
            await main(SimpleNamespace(server=None,machine='CONV-3',read_resource=True))
    elif task=='t09':
        checks.append(await model_case('spec',out,route='mcp'))
        # Compare the actual model-facing interface; equal tool names do not imply equal schemas.
        from tool_definitions import model_tools
        trace=json.loads((out/'spec.json').read_text(encoding='utf-8'))
        local=next(t for t in model_tools() if t['function']['name']=='get_machine_spec')
        remote=next((t for t in trace.get('tool_definitions',[]) if t['function']['name']=='get_machine_spec'),None)
        comparison={'local_definition_now':local,'mcp_definition_sent':remote,
                    'same_description':remote is not None and local['function']['description']==remote['function']['description'],
                    'same_parameters':remote is not None and local['function']['parameters']==remote['function']['parameters'],
                    'note':'Inspect both definitions. The executor still validates arguments. This comparison does not prove model decisions are equivalent.'}
        (out/'tool_interfaces.json').write_text(json.dumps(comparison,indent=2),encoding='utf-8')
    else:raise ValueError('This task has no experiment.')
    report={'task':task,'checks':checks,'passed':bool(checks) and all(c['passed'] for c in checks),
            'manual_answer_review_required':task in {'t06','t07','t09'}}
    report_path.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 2


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',required=True);parser.add_argument('--output-dir',required=True)
    args=parser.parse_args()
    raise SystemExit(asyncio.run(run(args.task,args.output_dir)))
