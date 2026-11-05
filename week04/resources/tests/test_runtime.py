import json,time,pytest
from pathlib import Path
from state import State,Task,Decision
from controls import Config
from gateway import ToolRunner
from planner import ScriptedPlanner,PlannerError
from runtime import run_agent

@pytest.mark.parametrize('goal,expected_steps',[('report',3),('spec',1),('readings',1)])
def test_normal_completion(task,config,goal,expected_steps):
    planner=ScriptedPlanner()
    state=run_agent(task.model_copy(update={'goal':goal}),planner,config)
    assert state.status=='completed'
    assert state.steps==expected_steps and state.tool_attempts==expected_steps
    assert len(planner.feedback)==expected_steps
    assert state.trace[-1]['event']=='stop'

def test_repeat_stops_without_reexecuting_same_read(task,config):
    p=ScriptedPlanner('repeat');s=run_agent(task,p,config)
    assert (s.status,s.reason,s.steps,s.tool_attempts)==('stopped','no_progress',3,1)

def test_max_steps_contains_nonterminating_script(task):
    s=run_agent(task,ScriptedPlanner('repeat'),Config(max_no_progress=0,max_steps=6))
    assert (s.reason,s.steps,s.tool_attempts)==('max_steps',6,1)

def test_no_model_or_tool_after_completion(task,config):
    p=ScriptedPlanner('after_complete');s=run_agent(task,p,config)
    assert s.status=='completed' and p.calls==3 and s.tool_attempts==3
    # If a bug asked again, this scripted policy WOULD request another tool.
    assert p.next(s,5).kind=='tool'

@pytest.mark.parametrize('scenario',['invalid','wrong_object','early_finish'])
def test_bad_requests_cost_steps_not_tool_execution(task,config,scenario):
    s=run_agent(task,ScriptedPlanner(scenario),config)
    assert s.status=='stopped' and s.steps==2 and s.tool_attempts==0 and s.report is None

def test_made_up_stats_do_not_complete(task,config):
    s=run_agent(task,ScriptedPlanner('wrong_stats'),config)
    assert s.status=='stopped' and s.reason=='no_progress'
    assert s.report is None

def test_transient_failure_one_retry(task,config):
    s=run_agent(task,ScriptedPlanner(),config,ToolRunner('transient_once'))
    assert s.status=='completed' and s.tool_attempts==4 and s.steps==3
    assert len([x for x in s.trace if x['event']=='retry'])==1

def test_retry_exhaustion(task,config):
    s=run_agent(task,ScriptedPlanner(),config,ToolRunner('persistent'))
    assert s.status=='failed' and s.reason=='retry_exhausted'
    assert s.steps==1 and s.tool_attempts==2 and s.report is None

def test_retry_cannot_bypass_total_attempt_budget(task):
    s=run_agent(task,ScriptedPlanner(),Config(max_tool_attempts=1),ToolRunner('persistent'))
    assert s.status=='stopped' and s.reason=='max_tool_attempts' and s.tool_attempts==1

def test_timeout_really_bounds_child_process(task):
    start=time.monotonic()
    s=run_agent(task,ScriptedPlanner(),Config(tool_timeout=.15,retry_limit=0),ToolRunner('timeout'))
    assert time.monotonic()-start<3
    assert s.status=='failed' and s.reason=='retry_exhausted'
    assert any(o.result['error']['code']=='TOOL_TIMEOUT' for o in s.observations)

@pytest.mark.parametrize('case,reason',[('ambiguous','missing_task_fields'),('no_data','no_readings'),
                                       ('missing_spec','not_found')])
def test_handoff(case,reason,config):
    task=Task.model_validate_json(Path(f'tasks/{case}.json').read_text(encoding='utf-8'))
    s=run_agent(task,ScriptedPlanner(),config)
    assert (s.status,s.reason)==('needs_human',reason)
    assert any(e['event']=='human_request' for e in s.trace)
    assert s.report is None

def test_empty_readings_goal_is_success(task,config):
    t=Task.model_validate_json(Path('tasks/no_data.json').read_text(encoding='utf-8'))
    s=run_agent(t.model_copy(update={'goal':'readings'}),ScriptedPlanner(),config)
    assert s.status=='completed' and s.report['facts']['readings']['count']==0

def test_model_error_never_falls_back(task,config):
    class Broken(ScriptedPlanner):
        mode='live'
        def next(self,*a,**k):raise PlannerError('test only')
    s=run_agent(task,Broken(),config)
    assert s.status=='failed' and s.reason=='model_error' and s.steps==1 and s.tool_attempts==0

def test_unknown_tool_not_executed(task,config):
    s=State(task,'scripted')
    obs=ToolRunner().execute(s,Decision('tool','delete_records',{}),config)
    assert obs.result['error']['code']=='UNKNOWN_TOOL' and s.tool_attempts==0

def test_run_cache_not_shared_as_evidence(task,config):
    runner=ToolRunner()
    one=State(task,'scripted');two=State(task,'scripted')
    d=Decision('tool','get_machine_spec',{'machine_id':'CONV-3'})
    runner.execute(one,d,config);runner.execute(two,d,config)
    assert one.tool_attempts==two.tool_attempts==1
    assert not two.observations[0].reused
