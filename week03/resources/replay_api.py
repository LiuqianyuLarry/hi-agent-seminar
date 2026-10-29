"""Deterministic Chat Completions-shaped replay. NOT a model."""
import copy


class ScriptedCompletions:
    def __init__(self, case):
        self.case = case
        self.requests = []

    def create(self, **kwargs):
        self.requests.append(copy.deepcopy(kwargs))
        message = {'role': 'assistant', 'content': None}
        reason = 'stop'
        if len(self.requests) == 1:
            call = self.case.get('call')
            if call:
                reason = 'tool_calls'
                message['tool_calls'] = [{'id': 'replay_call_01', 'type': 'function', 'function': copy.deepcopy(call)}]
            else:
                message['content'] = self.case.get('direct_text', 'REPLAY: Please supply the missing information.')
        else:
            result = next(m for m in reversed(kwargs['messages']) if m['role'] == 'tool')
            message['content'] = '[SCRIPTED REPLAY, NOT AN LLM ANSWER]\n' + result['content']
        return {'choices': [{'finish_reason': reason, 'message': message}]}
