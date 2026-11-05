"""Bounded execution. Successful identical reads may be reused within a frozen-data run."""
import json, subprocess, sys, time
from pathlib import Path
from pydantic import ValidationError
from controls import Config, remaining_seconds
from schemas import ToolResult, fail
from tool_definitions import ARG_TYPES
from state import State, Decision

class StopRun(Exception):
    def __init__(self, reason):
        self.reason=reason

class ToolRunner:
    def __init__(self, fault='none'):
        self.fault=fault
        self.seen_attempts={}
        self.cache={}

    def execute(self, state: State, action: Decision, cfg: Config):
        name=action.name
        if name not in ARG_TYPES:
            return state.record(name, action.arguments, fail('UNKNOWN_TOOL','The tool is not registered and was not executed.'))
        try:
            # Limit the request even in scripted tests.
            if len(json.dumps(action.arguments,allow_nan=False))>32768:
                raise ValueError('Oversize request')
            args=ARG_TYPES[name].model_validate(action.arguments).model_dump()
        except (ValidationError, ValueError, TypeError):
            return state.record(name, action.arguments,
                                fail('INVALID_ARGUMENT','The arguments have invalid types, times or ranges. The tool was not executed.'))
        # Task scope is user-confirmed input, not guessed from the model's intent.
        if 'machine_id' in args and args['machine_id']!=state.task.machine_id:
            return state.record(name,args,fail('TASK_MISMATCH','The machine differs from the confirmed task. The tool was not executed.'))
        if name=='query_temperature' and (args['start'],args['end'])!=(state.task.start,state.task.end):
            return state.record(name,args,fail('TASK_MISMATCH','The time window differs from the confirmed task. The tool was not executed.'))
        key=json.dumps([state.run_id,name,args],sort_keys=True,ensure_ascii=False)
        if key in self.cache:
            state.log('reuse', tool=name, note='The same normalized request already succeeded in this run with frozen classroom data. No new tool execution.')
            return state.record(name,args,self.cache[key],reused=True)
        for attempt in range(cfg.retry_limit+1):
            remaining=remaining_seconds(state,cfg)
            if remaining<=0:
                raise StopRun('deadline')
            if state.tool_attempts >= cfg.max_tool_attempts:
                raise StopRun('max_tool_attempts')
            state.tool_attempts+=1
            self.seen_attempts[name]=self.seen_attempts.get(name,0)+1
            state.log('tool_attempt', tool=name, attempt=attempt+1,
                      total_attempts=state.tool_attempts)
            if name=='query_temperature' and (self.fault=='persistent' or
                    (self.fault=='transient_once' and self.seen_attempts[name]==1)):
                result=fail('TEMPORARY_UNAVAILABLE','Injected classroom fault: the query is temporarily unavailable.')
                state.log('fault_injection', kind=self.fault, tool=name)
            else:
                req={'name':name,'arguments':args,
                     'teaching_delay_s':2.0 if self.fault=='timeout' and name=='query_temperature' else 0}
                try:
                    proc=subprocess.run([sys.executable,str(Path(__file__).with_name('worker.py'))],
                        input=json.dumps(req),capture_output=True,text=True,encoding='utf-8',
                        timeout=min(cfg.tool_timeout,remaining),check=False)
                    if proc.returncode:
                        result=fail('WORKER_FAILURE','The tool process failed. No new data was confirmed.')
                    else:
                        result=ToolResult.model_validate_json(proc.stdout).model_dump()
                except subprocess.TimeoutExpired:
                    result=fail('TOOL_TIMEOUT','The local tool timed out. Its process was terminated and joined.')
                except (OSError, ValueError):
                    result=fail('INVALID_RESULT','The result could not be read, or the execution environment was unavailable.')
            observation=state.record(name,args,result)
            if result['status']=='ok':
                self.cache[key]=result
                return observation
            code=result['error']['code']
            if code not in {'TEMPORARY_UNAVAILABLE','TOOL_TIMEOUT'} or attempt>=cfg.retry_limit:
                return observation
            # Only these classroom tools, all read-only / pure, are retried.
            state.log('retry', tool=name, retry_number=attempt+1, code=code)
            delay=min(cfg.retry_backoff*(2**attempt),remaining_seconds(state,cfg))
            if delay>0:
                time.sleep(delay)
        raise AssertionError('unreachable')
