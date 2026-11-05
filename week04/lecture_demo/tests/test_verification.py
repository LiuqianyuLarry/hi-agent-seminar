import copy,pytest
from state import State,Decision
from verification import verify,build_report,statistics_inputs_match
from gateway import ToolRunner
from tools.calculation import temperature_stats
from types import SimpleNamespace

def add_stats(state,config,values=None,limit=85.0):
    return ToolRunner().execute(state,Decision('tool','temperature_stats',{
        'values_c':values or [82.,87.,91.,94.,97.],'limit_c':limit}),config)

def test_empty_is_not_complete(task):
    check=verify(State(task,'scripted'))
    assert not check.ready and set(check.missing)=={'spec','readings','stats'}

def test_sources_are_not_yet_report(source_state):
    check=verify(source_state)
    assert not check.ready and check.missing==['stats']

def test_full_evidence(source_state,config):
    add_stats(source_state,config)
    check=verify(source_state);report=build_report(source_state,check)
    assert check.ready
    assert report['facts']['stats']['above_fraction']==0.8
    assert report['facts']['stats']['mean_c']==pytest.approx(90.2)
    assert len(report['evidence'])==3

def test_valid_shape_but_wrong_stat_inputs(source_state,config):
    add_stats(source_state,config,values=[1.,2.])
    assert not verify(source_state).ready

def test_wrong_threshold(source_state,config):
    add_stats(source_state,config,limit=100.)
    assert not verify(source_state).ready

def test_tampered_numeric_output(source_state,config):
    obs=add_stats(source_state,config)
    obs.result['data']['mean_c']=20.0
    assert not verify(source_state).ready

def test_wrong_query_window(source_state,config):
    add_stats(source_state,config)
    source_state.observations[0].arguments['end']='2026-03-02T10:30:00+08:00'
    assert not verify(source_state).ready

def test_wrong_device_in_result(source_state,config):
    add_stats(source_state,config)
    source_state.observations[0].result['data']['machine_id']='CONV-7'
    assert not verify(source_state).ready

def test_out_of_window_reading(source_state,config):
    add_stats(source_state,config)
    source_state.observations[0].result['data']['records'][0]['ts']='2026-03-03T10:00:00+08:00'
    assert not verify(source_state).ready

def test_missing_source_is_not_evidence(source_state,config):
    add_stats(source_state,config)
    source_state.observations[1].result['source']=None
    assert not verify(source_state).ready

def test_cannot_render_incomplete(source_state):
    with pytest.raises(ValueError):build_report(source_state,verify(source_state))

def test_spec_only_does_not_require_all_tools(source_state):
    source_state.task=source_state.task.model_copy(update={'goal':'spec'})
    check=verify(source_state)
    assert check.ready and check.progress==('spec',)

# W4.2B: these contracts distinguish source inputs from output shape or counts.
@pytest.mark.parametrize('arguments,expected', [
    ({'values_c': [82.,87.,91.,94.,97.], 'limit_c': 85.}, True),
    ({'values_c': [82.,88.,90.,94.,97.], 'limit_c': 85.}, False),
    ({'values_c': [82.,87.,91.,94.,97.], 'limit_c': 100.}, False),
    ({'values_c': [82.,87.,91.,94.,97.]}, False),
])
def test_statistics_input_contract(arguments, expected):
    observation = SimpleNamespace(arguments=arguments)
    assert statistics_inputs_match(observation, [82.,87.,91.,94.,97.], 85.) is expected


def test_same_count_and_same_summary_do_not_prove_matching_inputs(source_state, config):
    wrong_values = [82.,88.,90.,94.,97.]
    observation = add_stats(source_state, config, values=wrong_values)
    correct_summary = temperature_stats([82.,87.,91.,94.,97.], 85.)['data']
    # All returned statistics match. Only the recorded input list reveals the gap.
    assert observation.result['data'] == correct_summary
    check = verify(source_state)
    assert not check.ready and 'stats' in check.missing


def test_wrong_recorded_limit_is_rejected_even_if_output_claims_correct_numbers(source_state, config):
    observation = add_stats(source_state, config)
    # Deliberate inconsistent-record injection: do not trust the output alone.
    observation.arguments['limit_c'] = 100.
    assert observation.result['data'] == temperature_stats([82.,87.,91.,94.,97.], 85.)['data']
    assert not verify(source_state).ready
