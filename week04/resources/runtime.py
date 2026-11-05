"""Explicit Plan–Act–Observe–Verify loop. No Agent framework or graph abstraction."""
import time
from controls import Config, stop_reason, remaining_seconds
from gateway import ToolRunner, StopRun
from planner import PlannerError
from schemas import fail
from state import State, Task
from verification import verify, build_report


def _update_check(state):
    check=verify(state)
    state.no_progress=0 if check.progress!=state.last_progress else state.no_progress+1
    state.last_progress=check.progress
    state.log('verify', ready=check.ready, missing=check.missing,
              progress=list(check.progress), evidence_ids=check.evidence_ids,
              no_progress=state.no_progress)
    return check


def _end(state,status,reason,check=None):
    state.status=status;state.reason=reason
    if status=='completed':
        state.report=build_report(state,check)
    state.log('stop',status=status,reason=reason,tool_attempts=state.tool_attempts)
    return state


def complete_tool_step(state, action, planner, runner, cfg):
    """Run one allowed tool action, return its result to the planner, and update the check."""
    # W4.4: use the runner, return the result, update the check, then return both.
    raise NotImplementedError('Complete W4.4 in complete_tool_step')


def request_action(state, planner, cfg):
    """Count every proposed decision, including a wrong or premature one."""
    state.steps += 1
    state.log('decision_requested', remaining_s=round(remaining_seconds(state, cfg), 3))
    return planner.next(state, min(cfg.request_timeout, remaining_seconds(state, cfg)))


def run_agent(task: Task, planner, cfg=None, runner=None) -> State:
    cfg=cfg or Config();runner=runner or ToolRunner()
    task=task.normalized()
    state=State(task,planner.mode)
    state.log('start',task=task.model_dump(),mode=planner.mode)
    missing=task.missing_fields()
    if missing:
        state.log('human_request',question='Please confirm these task fields: '+', '.join(missing))
        return _end(state,'needs_human','missing_task_fields')
    # BEGIN_SOLUTION W4.4
    while True:
        check=verify(state)
        if check.ready:
            return _end(state,'completed','verified',check)
        reason=stop_reason(state,cfg)
        if reason:
            return _end(state,'stopped',reason)
        try:
            action = request_action(state, planner, cfg)
        except PlannerError as exc:
            state.log('provider_error',message=str(exc))
            return _end(state,'failed','model_error')
        state.usage_tokens+=action.usage_tokens or 0
        state.log('decision',kind=action.kind,tool=action.name,arguments=action.arguments,
                  action_label=action.note,usage_tokens=action.usage_tokens)
        if remaining_seconds(state,cfg)<=0:
            return _end(state,'stopped','deadline')
        if state.mode=='live' and state.usage_tokens>=cfg.token_stop:
            return _end(state,'stopped','reported_token_limit')
        if action.kind=='human':
            state.log('human_request',question=action.question)
            return _end(state,'needs_human','planner_requested_human')
        if action.kind in {'invalid','finish'}:
            planner.observe(fail('INCOMPLETE_EVIDENCE','Still missing: '+', '.join(check.missing)))
            _update_check(state)
            continue
        if action.kind!='tool':
            planner.observe(fail('INVALID_ACTION','Unknown action type.'))
            _update_check(state)
            continue
        try:
            obs, check = complete_tool_step(state, action, planner, runner, cfg)
        except StopRun as exc:
            return _end(state,'stopped',exc.reason)
        if remaining_seconds(state,cfg)<=0:
            return _end(state,'stopped','deadline')
        if check.ready:
            return _end(state,'completed','verified',check)
        if obs.result['status']=='error':
            code=obs.result['error']['code']
            if code in {'NOT_FOUND','DATA_UNAVAILABLE'}:
                state.log('human_request',question=obs.result['error']['message'])
                return _end(state,'needs_human',code.lower())
            if code in {'TEMPORARY_UNAVAILABLE','TOOL_TIMEOUT'}:
                return _end(state,'failed','retry_exhausted')
            if code in {'WORKER_FAILURE','INVALID_RESULT','TOOL_EXCEPTION','NOT_IMPLEMENTED'}:
                return _end(state,'failed',code.lower())
        if (obs.tool=='query_temperature' and obs.result['status']=='ok'
                and obs.result['data']['count']==0 and task.goal=='report'):
            state.log('human_request',question='There are no readings in this window. Please confirm the range. An empty dataset is not a 0% over-limit result.')
            return _end(state,'needs_human','no_readings')
    # END_SOLUTION W4.4
