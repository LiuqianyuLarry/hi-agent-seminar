import asyncio,json,sqlite3
from contextlib import closing
from pathlib import Path
import pytest
from schemas import QueryArgs,ToolResult
from executor import Executor,AccessPolicy
from tools import engineering,sql_query

ARGS={'machine_id':'CONV-3','start':'2026-03-02T10:00:00+08:00','end':'2026-03-02T10:25:00+08:00'}
def execute(name,args,ex=None):
    ex=ex or Executor()
    return asyncio.run(ex.execute(name,json.dumps(args)))

def test_stats_expected():
    r=execute('temperature_stats',{'values_c':[82,87,91,94,97],'limit_c':85})
    assert r['status']=='ok';d=r['data']
    assert d['mean_c']==pytest.approx(90.2)
    assert d['max_c']==97 and d['above_count']==4 and d['above_fraction']==pytest.approx(0.8)

@pytest.mark.parametrize('values,expected', [([85],0),([86],1),([84,85,86],1/3)])
def test_strictly_greater(values,expected):
    assert execute('temperature_stats',{'values_c':values,'limit_c':85})['data']['above_fraction']==pytest.approx(expected)

@pytest.mark.parametrize('values',[[],['97'],[True],[float('nan')],[float('inf')],list(range(1001))])
def test_bad_values_blocked(values):
    ex=Executor();r=execute('temperature_stats',{'values_c':values,'limit_c':85},ex)
    assert r['status']=='error' and ex.invocations==0

def test_stats_rejects_extra():
    assert execute('temperature_stats',{'values_c':[97],'limit_c':85,'code':'print(1)'})['status']=='error'

def test_spec_known_and_source():
    r=execute('get_machine_spec',{'machine_id':'CONV-3'})
    assert r['data']['temperature_limit_c']==85 and r['source']=='machine_specs.json'

def test_spec_unknown():
    r=execute('get_machine_spec',{'machine_id':'CONV-99'})
    assert r['error']['code']=='NOT_FOUND'

def test_spec_wrong_type():
    ex=Executor();r=execute('get_machine_spec',{'machine_id':['CONV-3']},ex)
    assert r['error']['code']=='INVALID_ARGUMENT' and ex.invocations==0

def test_no_model_supplied_path_or_admin():
    for field in ['path','admin']:
        r=execute('get_machine_spec',{'machine_id':'CONV-3',field:True})
        assert r['status']=='error'

def test_query_exact_interval():
    r=execute('query_temperature',ARGS)
    assert r['status']=='ok' and r['data']['count']==5
    assert [row['temperature_c'] for row in r['data']['records']]==[82,87,91,94,97]

def test_timezone_normalization():
    r=execute('query_temperature',{**ARGS,'start':'2026-03-02T02:00:00+00:00','end':'2026-03-02T02:25:00+00:00'})
    assert r['data']['count']==5 and r['data']['start'].endswith('+08:00')

@pytest.mark.parametrize('start,end',[
    ('2026-03-02T10:00:00','2026-03-02T10:25:00'),
    ('2026-03-02T11:00:00+08:00','2026-03-02T10:00:00+08:00'),
    ('2026-03-02T10:00:00+08:00','2026-03-04T10:00:00+08:00')])
def test_bad_time(start,end):
    ex=Executor();r=execute('query_temperature',{**ARGS,'start':start,'end':end},ex)
    assert r['status']=='error' and ex.invocations==0

def test_empty_is_success_not_fake_zero():
    r=execute('query_temperature',{**ARGS,'machine_id':'CONV-99'})
    assert r['status']=='ok' and r['data']['records']==[] and r['data']['count']==0

def test_too_many_rows_not_truncated():
    r=execute('query_temperature',{**ARGS,'start':'2026-03-03T10:00:00+08:00','end':'2026-03-03T12:00:00+08:00'})
    assert r['error']['code']=='RESULT_LIMIT' and r['data'] is None

def test_parameterized_query_and_read_only():
    with closing(sqlite3.connect(sql_query.DB_PATH.resolve().as_uri()+'?mode=ro',uri=True)) as conn:
        assert conn.execute(sql_query.SQL,("CONV-3' OR 1=1--",0,9999999999)).fetchall()==[]
        with pytest.raises(sqlite3.OperationalError):conn.execute('DELETE FROM sensor_reading')

def test_unknown_tool_never_executes():
    ex=Executor();r=execute('delete_records',{'machine_id':'CONV-3'},ex)
    assert r['error']['code']=='UNKNOWN_TOOL' and ex.invocations==0

def test_permissions_not_from_arguments():
    ex=Executor(policy=AccessPolicy(allowed_machines=frozenset({'CONV-3'})))
    r=execute('get_machine_spec',{'machine_id':'CONV-7'},ex)
    assert r['error']['code']=='PERMISSION_DENIED' and ex.invocations==0

def test_injected_exception():
    def broken(**kwargs):raise RuntimeError('secret/path should not leak')
    ex=Executor(handlers={'get_machine_spec':broken})
    r=execute('get_machine_spec',{'machine_id':'CONV-3'},ex)
    assert r['error']['code']=='TOOL_EXCEPTION' and 'secret' not in json.dumps(r)

def test_missing_database(monkeypatch,tmp_path):
    monkeypatch.setattr(sql_query,'DB_PATH',tmp_path/'missing.sqlite')
    r=execute('query_temperature',ARGS)
    assert r['error']['code']=='DATA_UNAVAILABLE' and not (tmp_path/'missing.sqlite').exists()

def test_missing_spec(monkeypatch,tmp_path):
    monkeypatch.setattr(engineering,'SPEC_PATH',tmp_path/'missing.json')
    assert execute('get_machine_spec',{'machine_id':'CONV-3'})['error']['code']=='DATA_UNAVAILABLE'

def test_valid_wrong_machine_is_not_semantic_guard():
    # Explicitly document the limit: valid CONV-7 is not rejected simply because a user meant CONV-3.
    assert execute('get_machine_spec',{'machine_id':'CONV-7'})['status']=='ok'

def test_oversized_arguments():
    ex=Executor();r=asyncio.run(ex.execute('get_machine_spec',' '*33000))
    assert r['status']=='error' and ex.invocations==0

def test_invalid_output_is_rejected():
    def broken(**kwargs):return {'status':'ok','data':{'machine_id':'CONV-3'}}
    ex=Executor(handlers={'get_machine_spec':broken})
    assert execute('get_machine_spec',{'machine_id':'CONV-3'},ex)['error']['code']=='INVALID_RESULT'
