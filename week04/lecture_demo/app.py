"""CLI. Scripted mode never claims to measure model accuracy. Live never falls back."""
import argparse,json,sys
from dataclasses import asdict
from pathlib import Path
from state import Task
from planner import ScriptedPlanner, LivePlanner, PlannerError
from gateway import ToolRunner
from runtime import run_agent
from controls import Config

SCENARIOS=['normal','repeat','after_complete','early_finish','invalid','wrong_object',
           'wrong_stats','human','transient_once','persistent','timeout']

def save_outputs(state,out,cfg):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    data=state.export();data['config']=asdict(cfg)
    (out/'run.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    with (out/'trace.jsonl').open('w',encoding='utf-8') as f:
        for event in state.trace:f.write(json.dumps(event,ensure_ascii=False)+'\n')
    lines=[f'# Run {state.run_id}',f'Mode: **{state.mode}**',f'Status: **{state.status}** / {state.reason}',
           data['warning'],'','| Event | Decision step | Type | Details |','|---:|---:|---|---|']
    for e in state.trace:
        details={k:v for k,v in e.items() if k not in {'event_id','step','event','elapsed_s'}}
        text=json.dumps(details,ensure_ascii=False).replace('|','\\|').replace('\n',' ')
        lines.append(f"| {e['event_id']} | {e['step']} | {e['event']} | {text} |")
    (out/'trace.md').write_text('\n'.join(lines),encoding='utf-8')
    (out/'report.json').write_text(json.dumps(state.report,ensure_ascii=False,indent=2),encoding='utf-8')
    report=state.report['summary'] if state.report else f'Not completed: {state.status} / {state.reason}. Read the trace and available evidence. A stopped run is not necessarily a successful task.'
    limitations='\n'.join('- '+item for item in state.report.get('limitations',[])) if state.report else ''
    (out/'report.md').write_text('# Task result\n\n'+report+'\n\n'+limitations+'\n\n'+data['warning']+'\n',encoding='utf-8')
    if state.status!='needs_human':
        (out/'handoff.json').unlink(missing_ok=True)
    if state.status=='needs_human':
        handoff={'run_id':state.run_id,'task':state.task.model_dump(),
                 'questions':[e['question'] for e in state.trace if e['event']=='human_request'],
                 'instructions':'Ask the user to confirm the task fields, update the task JSON and start a new run. This example has no cross-process checkpoint resume.'}
        (out/'handoff.json').write_text(json.dumps(handoff,ensure_ascii=False,indent=2),encoding='utf-8')
    return data

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=['scripted','live'],default='scripted')
    p.add_argument('--scenario',choices=SCENARIOS,default='normal')
    p.add_argument('--task',default='tasks/normal.json')
    p.add_argument('--out',default='outputs/run')
    p.add_argument('--max-steps',type=int,default=6)
    p.add_argument('--max-no-progress',type=int,default=2)
    p.add_argument('--max-tool-attempts',type=int,default=8)
    p.add_argument('--retry-limit',type=int,default=1)
    p.add_argument('--tool-timeout',type=float,default=3.0)
    p.add_argument('--total-seconds',type=float,default=60.0)
    a=p.parse_args()
    if a.mode=='live' and a.scenario!='normal':
        p.error('Fault scenarios are scripted-only; live will not pretend they are model failures.')
    try:
        task=Task.model_validate_json(Path(a.task).read_text(encoding='utf-8')).normalized()
        cfg=Config(max_steps=a.max_steps,max_no_progress=a.max_no_progress,
                   max_tool_attempts=a.max_tool_attempts,retry_limit=a.retry_limit,
                   tool_timeout=a.tool_timeout,total_seconds=a.total_seconds)
        planner=LivePlanner(task) if a.mode=='live' else ScriptedPlanner(a.scenario)
        runner=ToolRunner(a.scenario if a.scenario in {'transient_once','persistent','timeout'} else 'none')
        state=run_agent(task,planner,cfg,runner)
        save_outputs(state,a.out,cfg)
    except Exception as exc:
        print(f'Startup or code error: {type(exc).__name__}: {exc}',file=sys.stderr)
        return 2
    print(f'{state.mode} | {state.status} | {state.reason} | steps={state.steps} | attempts={state.tool_attempts}')
    if state.report:print(state.report['summary'])
    print('Evidence folder: '+str(Path(a.out).resolve()))
    return 0 if state.status=='completed' else 1

if __name__=='__main__':
    raise SystemExit(main())
