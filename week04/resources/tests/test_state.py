from state import State
from schemas import fail

def test_record_is_independent_copy(task):
    s=State(task,'scripted');args={'machine_id':'CONV-3'};result=fail('X','test')
    obs=s.record('get_machine_spec',args,result)
    args['machine_id']='CONV-7';result['error']['code']='Y'
    assert obs.arguments['machine_id']=='CONV-3'
    assert obs.result['error']['code']=='X'
    assert s.trace[0]['event']=='observation'
    assert s.trace[0]['observation_id']==obs.id

def test_monotonic_ids(task):
    s=State(task,'scripted')
    a=s.record('a',{},fail('X','x'));b=s.record('a',{},fail('X','x'))
    assert (a.id,b.id)==('obs_001','obs_002')
    assert [x['event_id'] for x in s.trace]==[1,2]

def test_context_is_not_an_alias(task):
    s=State(task,'scripted');s.record('a',{},fail('X','x'))
    # context() intentionally returns a serializable view; caller transport deep-copies it.
    assert s.context()['task']['machine_id']=='CONV-3'
    assert 'OPENAI_API_KEY' not in str(s.context())

def test_missing_fields_are_not_guessed(task):
    ambiguous=task.model_copy(update={'machine_id':None,'start':None,'end':None})
    assert set(ambiguous.missing_fields())=={'machine_id','start','end'}

def test_utc_normalization(task):
    t=task.model_copy(update={'start':'2026-03-02T02:00:00Z','end':'2026-03-02T02:25:00Z'}).normalized()
    assert t.start==task.start and t.end==task.end
