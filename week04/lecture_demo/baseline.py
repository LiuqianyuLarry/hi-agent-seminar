"""A fixed workflow baseline: no model and no dynamic planner."""
import argparse,json
from pathlib import Path
from state import Task,State,Decision
from controls import Config
from gateway import ToolRunner,StopRun
from verification import verify,matching_sources,build_report
from app import save_outputs

def main():
    p=argparse.ArgumentParser();p.add_argument('--task',default='tasks/normal.json')
    p.add_argument('--out',default='outputs/fixed_workflow');a=p.parse_args()
    t=Task.model_validate_json(Path(a.task).read_text(encoding='utf-8')).normalized()
    s=State(t,'fixed_workflow');cfg=Config();runner=ToolRunner()
    s.log('start',mode='fixed_workflow',note='Fixed workflow; no model requests.')
    if t.missing_fields():
        s.status='needs_human';s.reason='missing_task_fields'
    else:
        try:
            if t.goal in {'report','readings'}:
                runner.execute(s,Decision('tool','query_temperature',
                    {'machine_id':t.machine_id,'start':t.start,'end':t.end}),cfg)
            if t.goal in {'report','spec'}:
                runner.execute(s,Decision('tool','get_machine_spec',{'machine_id':t.machine_id}),cfg)
            spec,query=matching_sources(s)
            if t.goal=='report' and spec and query and query[1].count>0:
                runner.execute(s,Decision('tool','temperature_stats',{
                    'values_c':[r.temperature_c for r in query[1].records],
                    'limit_c':spec[1].temperature_limit_c}),cfg)
            check=verify(s)
            s.status='completed' if check.ready else 'needs_human'
            s.reason='verified' if check.ready else 'incomplete_evidence'
            if check.ready:s.report=build_report(s,check)
        except StopRun as exc:s.status='stopped';s.reason=exc.reason
    s.log('stop',status=s.status,reason=s.reason)
    save_outputs(s,a.out,cfg)
    print(f'{s.mode}: {s.status}; tool_attempts={s.tool_attempts}; LLM calls=0')
if __name__=='__main__':main()
