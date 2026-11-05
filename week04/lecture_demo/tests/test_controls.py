import time,pytest
from state import State
from controls import Config,stop_reason

@pytest.mark.parametrize('field,value,reason',[
    ('steps',6,'max_steps'),('no_progress',2,'no_progress')])
def test_step_and_progress_limits(task,field,value,reason):
    state=State(task,'scripted');setattr(state,field,value)
    assert stop_reason(state,Config())==reason

def test_deadline(task):
    s=State(task,'scripted');s.started-=100
    assert stop_reason(s,Config())=='deadline'

def test_reported_token_circuit_breaker(task):
    s=State(task,'live');s.usage_tokens=16000
    assert stop_reason(s,Config())=='reported_token_limit'

def test_progress_check_can_be_disabled_but_step_cap_remains(task):
    s=State(task,'scripted');s.no_progress=100
    cfg=Config(max_no_progress=0)
    assert stop_reason(s,cfg) is None
    s.steps=6;assert stop_reason(s,cfg)=='max_steps'

@pytest.mark.parametrize('kw',[{'max_steps':0},{'max_steps':True},{'retry_limit':-1},
                                {'tool_timeout':0},{'total_seconds':float('inf')}])
def test_invalid_config(kw):
    with pytest.raises(ValueError):Config(**kw)
