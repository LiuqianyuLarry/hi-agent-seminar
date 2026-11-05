"""DeepSeek Chat Completions adapter. Protocol tests are not live-model evidence."""
import copy
import json
import os
from provider import load_environment
from prompts import RULES, tools_for_model
from state import Decision


class PlannerError(Exception):
    pass


def get(value, name, default=None):
    return value.get(name, default) if isinstance(value, dict) else getattr(value, name, default)


def make_api():
    load_environment()
    if not os.getenv('DEEPSEEK_API_KEY'):
        raise PlannerError('Configure DEEPSEEK_API_KEY privately before a live run. No offline fallback was used.')
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise PlannerError('The optional DeepSeek client is missing. Use requirements-live.txt.') from exc
    client = OpenAI(api_key=os.environ['DEEPSEEK_API_KEY'], base_url='https://api.deepseek.com',
                    max_retries=0, timeout=15.0)
    return client, client.chat.completions


def parse_response(response):
    """Keep public tool requests; never copy private reasoning into a teaching artifact."""
    tokens = get(get(response, 'usage', {}), 'total_tokens')
    if type(tokens) is not int or tokens < 0:
        raise PlannerError('The response has no usable token count. Stop rather than continue unmetered.')
    choices = get(response, 'choices', [])
    if len(choices) != 1:
        raise PlannerError('Expected one model response choice.')
    choice = choices[0]
    message = get(choice, 'message', {})
    calls = []
    identifiers = set()
    for item in get(message, 'tool_calls', []) or []:
        call_id = get(item, 'id')
        function = get(item, 'function', {})
        name, arguments = get(function, 'name'), get(function, 'arguments')
        if (not isinstance(call_id, str) or not call_id or call_id in identifiers
                or not isinstance(name, str) or not name or not isinstance(arguments, str)):
            raise PlannerError('A tool request has an invalid or repeated ID, name or argument string. No tool ran.')
        identifiers.add(call_id)
        calls.append({'id': call_id, 'type': 'function', 'function': {'name': name, 'arguments': arguments}})
    public_message = {'role': 'assistant', 'content': get(message, 'content')}
    if calls:
        public_message['tool_calls'] = calls
    return public_message, calls, tokens, get(choice, 'finish_reason')


def parse_arguments(call):
    def reject_constant(value):
        raise ValueError('Non-finite JSON number')
    arguments = json.loads(call['function']['arguments'], parse_constant=reject_constant)
    if not isinstance(arguments, dict):
        raise ValueError('Arguments must be a JSON object')
    return arguments


class LivePlanner:
    mode = 'live'

    def __init__(self, task, api=None, model=None):
        load_environment()
        self.model = model or os.getenv('DEEPSEEK_MODEL', 'deepseek-flash')
        self.client = None
        if api is None:
            self.client, api = make_api()
        self.api = api
        self.messages = [{'role': 'system', 'content': RULES},
                         {'role': 'user', 'content': json.dumps(task.model_dump())}]
        self.pending_call = None
        self.requests = 0

    def next(self, state, timeout):
        if self.pending_call:
            raise PlannerError('Return the pending tool result before asking for another action.')
        self.messages.append({'role': 'user', 'content': 'Program state for the same task: ' + json.dumps(state.context())})
        try:
            self.requests += 1
            response = self.api.create(model=self.model, messages=copy.deepcopy(self.messages),
                tools=tools_for_model(), tool_choice='auto', max_tokens=1024,
                extra_body={'thinking': {'type': 'disabled'}}, timeout=max(0.01, min(15.0, timeout)))
        except Exception as exc:
            raise PlannerError('DeepSeek request failed (' + type(exc).__name__ + '). No offline fallback was used.') from exc
        message, calls, tokens, finish = parse_response(response)
        self.messages.append(message)
        if len(calls) > 1 or finish not in {'stop', 'tool_calls'}:
            # Pair EVERY requested call, even when none may execute in this one-action loop.
            for call in calls:
                self.messages.append({'role': 'tool', 'tool_call_id': call['id'], 'content': json.dumps({
                    'status': 'error', 'error': {'code': 'ROUND_NOT_EXECUTED',
                    'message': 'This teaching loop accepts one complete action per round. None of these requests ran.'}})})
            return Decision('invalid', note='Multiple or incomplete requests were not executed; this is an application policy.', usage_tokens=tokens)
        if not calls:
            return Decision('finish', note='Text is a request to finish, not proof of completion.', usage_tokens=tokens)
        call = calls[0]
        self.pending_call = call['id']
        try:
            arguments = parse_arguments(call)
        except (ValueError, TypeError):
            return Decision('invalid', note='Tool arguments are not a valid JSON object.', usage_tokens=tokens)
        name = call['function']['name']
        if name == 'finish_task':
            return Decision('finish', note='The model asks to finish.', usage_tokens=tokens)
        if name == 'ask_human':
            question = arguments.get('question')
            if not isinstance(question, str) or not question.strip():
                return Decision('invalid', note='The request for help has no question.', usage_tokens=tokens)
            return Decision('human', question=question[:500], usage_tokens=tokens)
        return Decision('tool', name, arguments, note='Request ' + name, usage_tokens=tokens)

    def observe(self, result):
        text = json.dumps(result, ensure_ascii=True, allow_nan=False)
        if self.pending_call:
            self.messages.append({'role': 'tool', 'tool_call_id': self.pending_call, 'content': text})
            self.pending_call = None
        else:
            self.messages.append({'role': 'user', 'content': 'Program feedback: ' + text})
