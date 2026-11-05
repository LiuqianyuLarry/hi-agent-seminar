"""Offline DeepSeek Chat Completions contracts; no network or paid model call."""
import copy
import json

import pytest

from controls import Config
from live_planner import LivePlanner, PlannerError
from runtime import run_agent
from schemas import fail
from state import State


class FakeCompletions:
    def __init__(self, replies):
        self.replies = list(replies)
        self.requests = []

    def create(self, **kwargs):
        self.requests.append(copy.deepcopy(kwargs))
        return self.replies.pop(0)


def call(name, arguments, identifier):
    return {'id': identifier, 'type': 'function',
            'function': {'name': name, 'arguments': json.dumps(arguments)}}


def reply(calls=(), content=None, finish=None, tokens=100):
    return {'id': 'offline-test-response', 'model': 'offline-test-model',
            'usage': {'total_tokens': tokens},
            'choices': [{'finish_reason': finish or ('tool_calls' if calls else 'stop'),
                         'message': {'role': 'assistant', 'content': content,
                                     'reasoning_content': 'PRIVATE_TEST_REASONING_MUST_NOT_APPEAR',
                                     'tool_calls': list(calls)}}]}


def spec_call(identifier='c1'):
    return call('get_machine_spec', {'machine_id': 'CONV-3'}, identifier)


def test_results_return_to_the_same_conversation_with_matching_call_ids(task, config):
    api = FakeCompletions([
        reply([spec_call()]),
        reply([call('query_temperature', {'machine_id': task.machine_id,
            'start': task.start, 'end': task.end}, 'c2')]),
        reply([call('temperature_stats', {'values_c': [82., 87., 91., 94., 97.],
            'limit_c': 85.}, 'c3')])])
    planner = LivePlanner(task, api=api, model='offline-test-model')
    state = run_agent(task, planner, config)
    assert state.status == 'completed'
    assert len(api.requests) == 3
    assert state.usage_tokens == 300
    assert state.tool_attempts == 3
    second = api.requests[1]['messages']
    assert any(message.get('role') == 'assistant' and
               message.get('tool_calls', [{}])[0].get('id') == 'c1'
               for message in second)
    results = [message for message in second if message.get('role') == 'tool']
    assert [message['tool_call_id'] for message in results] == ['c1']
    assert json.loads(results[0]['content'])['status'] == 'ok'
    assert any(message['role'] == 'user' and task.question in message['content']
               for message in second)
    assert 'PRIVATE_TEST_REASONING_MUST_NOT_APPEAR' not in json.dumps(planner.messages)
    assert 'PRIVATE_TEST_REASONING_MUST_NOT_APPEAR' not in json.dumps(state.export())
    assert api.requests[0]['extra_body']['thinking']['type'] == 'disabled'


def test_an_unreturned_tool_result_blocks_the_next_model_request(task):
    api = FakeCompletions([reply([spec_call()])])
    planner = LivePlanner(task, api=api, model='offline-test-model')
    state = State(task, 'live')
    decision = planner.next(state, 2)
    assert decision.kind == 'tool'
    with pytest.raises(PlannerError, match='pending tool result'):
        planner.next(state, 2)
    assert len(api.requests) == 1
    planner.observe(fail('TEST_FAILURE', 'The offline test did not run the tool.'))
    assert planner.messages[-1]['tool_call_id'] == 'c1'
    assert planner.pending_call is None


def test_free_text_is_a_finish_request_not_automatic_success(task, config):
    api = FakeCompletions([reply(content='Everything is complete.') for _ in range(2)])
    state = run_agent(task, LivePlanner(task, api=api, model='offline-test-model'), config)
    assert state.status == 'stopped'
    assert state.reason == 'no_progress'
    assert state.report is None
    assert state.tool_attempts == 0


def test_reported_token_limit_prevents_another_tool_execution(task):
    api = FakeCompletions([reply([spec_call()])])
    state = run_agent(task, LivePlanner(task, api=api, model='offline-test-model'),
                      Config(token_stop=50))
    assert state.reason == 'reported_token_limit'
    assert state.tool_attempts == 0
    assert state.usage_tokens == 100


def test_one_action_loop_rejects_a_batch_and_pairs_every_request(task, config):
    api = FakeCompletions([
        reply([spec_call('c1'), spec_call('c2')]),
        reply(content='I have nothing else to add.')])
    planner = LivePlanner(task, api=api, model='offline-test-model')
    state = run_agent(task, planner, config)
    assert state.tool_attempts == 0
    assert state.status == 'stopped'
    feedback = [message for message in api.requests[1]['messages']
                if message['role'] == 'tool']
    assert [message['tool_call_id'] for message in feedback] == ['c1', 'c2']
    assert all(json.loads(message['content'])['error']['code'] == 'ROUND_NOT_EXECUTED'
               for message in feedback)
    assert all('None of these requests ran' in message['content'] for message in feedback)


def test_truncated_request_is_not_executed_and_receives_matching_feedback(task, config):
    api = FakeCompletions([
        reply([spec_call()], finish='length'),
        reply(content='Please continue.')])
    state = run_agent(task, LivePlanner(task, api=api, model='offline-test-model'), config)
    assert state.tool_attempts == 0
    assert state.status == 'stopped'
    feedback = [message for message in api.requests[1]['messages']
                if message['role'] == 'tool']
    assert len(feedback) == 1
    assert feedback[0]['tool_call_id'] == 'c1'
    assert json.loads(feedback[0]['content'])['error']['code'] == 'ROUND_NOT_EXECUTED'


@pytest.mark.parametrize('usage', [None, {}, {'total_tokens': -1},
                                    {'total_tokens': True}, {'total_tokens': '100'}])
def test_missing_or_invalid_usage_fails_before_a_tool_runs(task, config, usage):
    response = reply([spec_call()])
    response['usage'] = usage
    state = run_agent(task, LivePlanner(task,
        api=FakeCompletions([response]), model='offline-test-model'), config)
    assert state.status == 'failed'
    assert state.reason == 'model_error'
    assert state.tool_attempts == 0


@pytest.mark.parametrize('identifiers', [[None], [''], ['duplicate', 'duplicate']])
def test_invalid_or_repeated_call_ids_fail_before_execution(task, config, identifiers):
    response = reply([spec_call(identifier) for identifier in identifiers])
    state = run_agent(task, LivePlanner(task,
        api=FakeCompletions([response]), model='offline-test-model'), config)
    assert state.status == 'failed'
    assert state.reason == 'model_error'
    assert state.tool_attempts == 0


@pytest.mark.parametrize('arguments', ['[]', '{"machine_id": NaN}', '{unfinished'])
def test_bad_argument_json_is_rejected_but_the_request_is_still_paired(task, config, arguments):
    proposed = spec_call()
    proposed['function']['arguments'] = arguments
    api = FakeCompletions([reply([proposed]), reply(content='Please stop.')])
    state = run_agent(task, LivePlanner(task, api=api, model='offline-test-model'), config)
    assert state.tool_attempts == 0
    assert state.status == 'stopped'
    feedback = [message for message in api.requests[1]['messages']
                if message['role'] == 'tool']
    assert len(feedback) == 1 and feedback[0]['tool_call_id'] == 'c1'
    assert json.loads(feedback[0]['content'])['status'] == 'error'


def test_one_shot_inspects_all_proposals_with_one_request_and_honest_test_label(task):
    from demos import single_round_request
    api = FakeCompletions([reply([
        call('query_temperature', {'machine_id': task.machine_id,
            'start': task.start, 'end': task.end}, 'q1'),
        spec_call('s1')])])
    result = single_round_request(task, api=api, model='offline-test-model')
    assert len(api.requests) == 1
    assert result['actual_requests'] == 1
    assert result['follow_up_requests'] == 0
    assert result['requested_tool_calls'] == 2
    assert result['tool_attempts'] == 2
    assert result['evidence_kind'] == 'contract_test'
    assert result['provider'] != 'DeepSeek'
    assert result['after']['ready'] is False
    assert result['after']['missing'] == ['stats']
    feedback = [message for message in result['next_messages_not_sent']
                if message['role'] == 'tool']
    assert [message['tool_call_id'] for message in feedback] == ['q1', 's1']
    assert all(json.loads(message['content'])['status'] == 'ok' for message in feedback)
    assert 'PRIVATE_TEST_REASONING_MUST_NOT_APPEAR' not in json.dumps(result)
