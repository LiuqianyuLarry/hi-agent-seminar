"""DeepSeek Chat Completions: one decision, at most one tool, one final answer."""
import copy
import json
from tool_definitions import RULES, model_tools


def get(obj, name, default=None):
    return obj.get(name, default) if isinstance(obj, dict) else getattr(obj, name, default)


def payload(item):
    return item.model_dump(exclude_none=True) if hasattr(item, 'model_dump') else copy.deepcopy(item)


async def run_turn(completions_api, model, question, executor, *, mode='live', tools=None):
    # The OpenAI Python SDK is an HTTP client here; the service is DeepSeek.
    request = dict(model=model, tools=tools or model_tools(), max_tokens=2048,
                   extra_body={'thinking': {'type': 'disabled'}})
    messages = [{'role': 'system', 'content': RULES}, {'role': 'user', 'content': question}]
    trace = dict(mode=mode, question=question, model=model if mode == 'live' else 'NO_MODEL_SCRIPTED_REPLAY',
                 provider='DeepSeek' if mode == 'live' else 'SCRIPTED_REPLAY', status='pending',
                 calls=[], events=executor.events, api_requests=0,
                 tool_definitions=copy.deepcopy(request['tools']),
                 warning='Inspect arguments and facts manually.' if mode == 'live' else
                 'Scripted choices and final text; real local tools. Not model-selection evidence.')
    try:
        trace['api_requests'] += 1
        first = completions_api.create(**request, messages=copy.deepcopy(messages), tool_choice='auto')
        choices = get(first, 'choices', [])
        if len(choices) != 1 or get(choices[0], 'finish_reason') not in {'stop', 'tool_calls'}:
            trace.update(status='incomplete_response', answer='Incomplete model response. No tool executed.')
            return trace
        message = get(choices[0], 'message')
        calls = get(message, 'tool_calls', []) or []
        trace['calls'] = [dict(name=get(get(c, 'function'), 'name'),
                               arguments=get(get(c, 'function'), 'arguments'), call_id=get(c, 'id')) for c in calls]
        if len(calls) > 1:
            trace.update(status='rejected_multiple_calls', answer='This week allows one tool per turn. None executed.')
            return trace
        if not calls:
            trace.update(status='no_tool', answer=get(message, 'content') or 'No usable answer received.')
            return trace
        call = trace['calls'][0]
        if get(calls[0], 'type') != 'function' or not all(isinstance(v, str) and v for v in call.values()):
            trace.update(status='invalid_call', answer='Invalid tool request. Nothing executed.')
            return trace
        result = await executor.execute(call['name'], call['arguments'])
        trace['tool_result'] = result
        messages.append({'role': 'assistant', 'content': get(message, 'content'),
                         'tool_calls': [payload(c) for c in calls]})
        messages.append({'role': 'tool', 'tool_call_id': call['call_id'],
                         'content': json.dumps(result, ensure_ascii=False, allow_nan=False)})
        trace['api_requests'] += 1
        final = completions_api.create(**request, messages=messages, tool_choice='none')
        choices = get(final, 'choices', [])
        if len(choices) != 1 or get(choices[0], 'finish_reason') != 'stop' or get(get(choices[0], 'message'), 'tool_calls'):
            trace.update(status='invalid_final_response', answer='Tool result saved; final response is incomplete or asks for another tool.')
            return trace
        text = get(get(choices[0], 'message'), 'content') or ''
        if result['status'] == 'error':
            trace.update(status='tool_error', untrusted_model_draft=text,
                         answer='Tool failed: ' + result['error']['message'])
        elif not text.strip():
            trace.update(status='invalid_final_response', answer='Tool result saved; final answer was empty.')
        else:
            trace.update(status='completed', answer=text)
        if get(final, 'usage') is not None:
            trace['final_usage'] = payload(get(final, 'usage'))
    except Exception as exc:
        trace.update(status='api_or_pipeline_error', error_type=type(exc).__name__,
                     answer='Request failed. Check dependencies, network and DeepSeek configuration. No replay fallback occurred.')
    return trace
