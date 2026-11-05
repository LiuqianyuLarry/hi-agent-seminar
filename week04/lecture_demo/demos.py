"""Small, bounded demonstrations. Each result states whether a model really ran."""
import argparse
import copy
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from controls import Config
from gateway import ToolRunner
from live_planner import make_api, parse_response, parse_arguments, get
from planner import ScriptedPlanner, LivePlanner
from prompts import RULES
from state import Task, State, Decision
from schemas import fail
from tool_definitions import model_tools
from verification import verify, matching_sources
from runtime import run_agent
from app import save_outputs

ROOT = Path(__file__).resolve().parent


def default_task(name='normal'):
    return Task.model_validate_json((ROOT / 'tasks' / (name + '.json')).read_text(encoding='utf-8')).normalized()


def source_hashes():
    files = [ROOT / 'data/sensor_readings.csv', ROOT / 'data/machine_specs.json']
    files.extend(sorted(ROOT.glob('*.py')))
    files.extend(sorted((ROOT / 'tools').glob('*.py')))
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def single_round_request(task, api=None, model=None):
    """Make exactly one request, inspect all proposals, run allowed tools, and do not ask again."""
    injected_api = api is not None
    client = None
    if api is None:
        client, api = make_api()
    model = model or os.getenv('DEEPSEEK_MODEL', 'deepseek-flash')
    # Unlike the full teaching loop, this opening experiment does not ask for one action only.
    instructions = ('Use the listed local classroom tools to answer the confirmed task. '
        'Do not invent values, limits or dates. A calculation must use observed readings and their reference limit. '
        'You may request independent tools together. The Python application executes them. '
        'Do not provide a private reasoning trace.')
    messages = [{'role': 'system', 'content': instructions},
                {'role': 'user', 'content': json.dumps(task.model_dump())}]
    request = {'model': model, 'messages': messages, 'tools': model_tools(), 'tool_choice': 'auto',
               'max_tokens': 1024, 'extra_body': {'thinking': {'type': 'disabled'}}, 'timeout': 15.0}
    state = State(task, 'live' if not injected_api else 'contract_test')
    state.log('start', task=task.model_dump(), mode=state.mode)
    before = asdict(verify(state))
    try:
        response = api.create(**copy.deepcopy(request))
    finally:
        if client is not None:
            client.close()
    message, calls, tokens, finish = parse_response(response)
    state.steps = 1
    state.usage_tokens = tokens
    state.log('model_response', requested_tool_calls=len(calls), finish_reason=finish)
    runner = ToolRunner()
    cfg = Config(max_steps=1, max_tool_attempts=4, retry_limit=0, total_seconds=40, tool_timeout=5)
    feedback = []
    for call in calls:
        name = call['function']['name']
        try:
            arguments = parse_arguments(call)
        except (ValueError, TypeError):
            observation = state.record(name, {}, fail('INVALID_ARGUMENT', 'The model did not return a JSON argument object. No tool ran.'))
        else:
            if finish not in {'tool_calls', 'stop'}:
                observation = state.record(name, arguments, fail('INCOMPLETE_RESPONSE', 'The response was incomplete. No tool ran.'))
            elif state.tool_attempts >= cfg.max_tool_attempts:
                observation = state.record(name, arguments, fail('DEMO_ATTEMPT_LIMIT', 'The opening experiment allows at most four local tool attempts. This request did not run.'))
            else:
                observation = runner.execute(state, Decision('tool', name, arguments), cfg)
        feedback.append({'role': 'tool', 'tool_call_id': call['id'], 'content': json.dumps(observation.result)})
    after = asdict(verify(state))
    state.log('verify', **after)
    state.status = 'completed' if after['ready'] else 'stopped'
    state.reason = 'verified_in_single_round' if after['ready'] else 'single_round_demo_ended'
    return {'case': 'one-shot', 'evidence_kind': 'contract_test' if injected_api else 'live_deepseek',
        'provider': 'Fake API for an offline contract test' if injected_api else 'DeepSeek',
        'captured_at': datetime.now(timezone.utc).isoformat(), 'request': request,
        'response': {'id': get(response, 'id'), 'model': get(response, 'model', model),
                     'message': message, 'finish_reason': finish, 'usage': {'total_tokens': tokens}},
        'actual_requests': 1, 'follow_up_requests': 0, 'requested_tool_calls': len(calls),
        'tool_attempts': state.tool_attempts, 'before': before, 'after': after,
        'observations': [asdict(o) for o in state.observations],
        'next_messages_not_sent': messages + [message] + feedback,
        'source_hashes': source_hashes(), 'trace': state.trace,
        'summary': 'One response was inspected. Allowed local tool requests ran, but their results were not sent in a second model request. Read the actual missing-evidence list; the API is not limited to one proposed tool call.'}


def bare_loop(scenario, max_decisions=4):
    """Expose missing completion controls, while an outer demo cap and tool timeouts remain."""
    task = default_task()
    state = State(task, 'scripted_fault_injection')
    runner = ToolRunner()
    cfg = Config(max_steps=max_decisions, retry_limit=0, total_seconds=20, tool_timeout=5)
    naive_status = 'running'
    planner = ScriptedPlanner('normal')
    for index in range(max_decisions):
        state.steps += 1
        if scenario == 'minimal-loop':
            action = planner.next(state, 1.0)
            if action.kind == 'finish':
                naive_status = 'completed'
                ending = 'naive_finish_accepted'
                break
        if scenario == 'bare-finish' and index == 1:
            state.log('decision', kind='finish', note='Injected request: finish after only the readings.')
            naive_status = 'completed'
            ending = 'naive_finish_accepted'
            break
        action = action if scenario == 'minimal-loop' else (Decision('tool', 'get_machine_spec', {'machine_id': task.machine_id})
                  if scenario == 'bare-repeat' else Decision('tool', 'query_temperature', {
                      'machine_id': task.machine_id, 'start': task.start, 'end': task.end}))
        state.log('decision', kind=action.kind, tool=action.name, arguments=action.arguments)
        obs = runner.execute(state, action, cfg)
        planner.observe(obs.result)
        state.log('feedback', observation_id=obs.id, result=obs.result)
    else:
        ending = 'external_demo_cap'
    # This check is an outside observer: the deliberately weak loop did not use it.
    diagnostic = asdict(verify(state))
    return {'case': scenario, 'evidence_kind': 'scripted_local_execution' if scenario == 'minimal-loop' else 'scripted_fault_injection',
        'planner_is_live': False, 'actual_local_tools': True, 'decisions': state.steps,
        'tool_attempts': state.tool_attempts, 'naive_status': naive_status,
        'ending': ending, 'external_demo_cap': max_decisions, 'internal_completion_checks': False,
        'diagnostic_check': diagnostic, 'observations': [asdict(o) for o in state.observations],
        'trace': state.trace, 'summary': ('The outside demo limit stopped repeated requests; the loop itself had no progress check.'
        if scenario == 'bare-repeat' else 'The simple loop progressed through the task; now test how it behaves with a bad proposal.' if scenario == 'minimal-loop' else 'The weak loop accepted finish with missing evidence. Its claimed success is not a verified result.')}


def check_gate():
    task = default_task()
    cases = [Decision('tool', 'unknown_tool', {}),
             Decision('tool', 'get_machine_spec', {'machine_id': [task.machine_id]}),
             Decision('tool', 'get_machine_spec', {'machine_id': 'CONV-7'}),
             Decision('tool', 'get_machine_spec', {'machine_id': task.machine_id})]
    rows = []
    for action in cases:
        state = State(task, 'scripted_gate_test')
        obs = ToolRunner().execute(state, action, Config(total_seconds=20, tool_timeout=5))
        rows.append({'tool': action.name, 'arguments': action.arguments, 'tool_attempts': state.tool_attempts,
                     'status': obs.result['status'], 'result': obs.result})
    return {'case': 'gate', 'evidence_kind': 'scripted_fault_injection', 'rows': rows,
            'summary': 'Compare the rejected requests with the allowed one. A rejection records feedback without executing that tool.'}


def wrong_stats():
    task = default_task()
    state = State(task, 'scripted_fault_injection')
    runner = ToolRunner()
    cfg = Config(total_seconds=30, tool_timeout=5)
    runner.execute(state, Decision('tool', 'query_temperature', {
        'machine_id': task.machine_id, 'start': task.start, 'end': task.end}), cfg)
    runner.execute(state, Decision('tool', 'get_machine_spec', {'machine_id': task.machine_id}), cfg)
    spec, query = matching_sources(state)
    obs = runner.execute(state, Decision('tool', 'temperature_stats', {
        'values_c': [1.0, 2.0], 'limit_c': spec[1].temperature_limit_c}), cfg)
    check = asdict(verify(state))
    return {'case': 'wrong-stats', 'evidence_kind': 'scripted_fault_injection',
            'actual_local_tools': True, 'wrong_observation': asdict(obs), 'check': check,
            'observed_values': [r.temperature_c for r in query[1].records],
            'summary': 'The calculation used valid numbers, but they were not the readings in this task. Tool success did not make the report complete.'}


def run_case(scenario, out, **settings):
    task_name = settings.pop('task_name', 'normal')
    cfg = Config(total_seconds=30, tool_timeout=settings.pop('tool_timeout', 5), **settings)
    fault = scenario if scenario in {'transient_once', 'persistent', 'timeout'} else 'none'
    state = run_agent(default_task(task_name), ScriptedPlanner(scenario), cfg, ToolRunner(fault))
    data = save_outputs(state, out, cfg)
    check = verify(state)
    return {'condition': scenario, 'task': task_name, 'status': data['status'], 'reason': data['reason'],
            'decisions': data['steps'], 'tool_attempts': data['tool_attempts'],
            'evidence_ids': check.evidence_ids, 'missing': check.missing,
            'observation_ids': [o.id for o in state.observations], 'run_json': str(Path(out) / 'run.json')}


def compare_runs(out):
    cases = [('normal', 'normal', 2), ('step_cap_only', 'repeat', 0),
             ('progress_guard', 'repeat', 2), ('early_finish', 'early_finish', 2),
             ('stop_when_complete', 'after_complete', 2)]
    rows = []
    for label, scenario, guard in cases:
        row = run_case(scenario, Path(out) / label, max_no_progress=guard)
        row['condition'] = label
        rows.append(row)
    path = Path(out) / 'comparison.csv'
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    expected = [('completed', 'verified', 3, 3), ('stopped', 'max_steps', 6, 1),
                ('stopped', 'no_progress', 3, 1), ('stopped', 'no_progress', 2, 0),
                ('completed', 'verified', 3, 3)]
    checks = [{'condition': row['condition'], 'passed': (
        row['status'], row['reason'], row['decisions'], row['tool_attempts']) == exp}
        for row, exp in zip(rows, expected)]
    return {'case': 'compare', 'evidence_kind': 'scripted_local_execution', 'rows': rows,
            'checks': checks, 'success': all(c['passed'] for c in checks),
            'summary': 'Read the real status, reason and counts for each run. A stopped run is not a completed task.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', required=True, choices=['one-shot', 'minimal-loop', 'bare-repeat', 'bare-finish', 'gate', 'wrong-stats',
        'normal', 'compare', 'retry', 'timeout', 'handoff', 'live-loop'])
    parser.add_argument('--mode', choices=['scripted', 'live'], default='scripted')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.case == 'one-shot':
        if args.mode != 'live':
            parser.error('The one-shot capture needs --mode live. A scripted response must not be labelled as a real API capture.')
        result = single_round_request(default_task())
    elif args.case.startswith('bare-') or args.case == 'minimal-loop':
        result = bare_loop(args.case)
    elif args.case == 'gate':
        result = check_gate()
    elif args.case == 'wrong-stats':
        result = wrong_stats()
    elif args.case == 'compare':
        result = compare_runs(out)
    elif args.case == 'live-loop':
        if args.mode != 'live':
            parser.error('Use --mode live for a real DeepSeek loop.')
        task = default_task()
        cfg = Config(total_seconds=60, tool_timeout=5)
        state = run_agent(task, LivePlanner(task), cfg)
        result = {'case': args.case, 'evidence_kind': 'live_deepseek', 'run': save_outputs(state, out, cfg),
                  'success': state.status == 'completed', 'summary': 'Real model choices with the same program checks. Inspect the recorded evidence.'}
    else:
        if args.case == 'retry':
            rows = [run_case(s, out / s) for s in ['transient_once', 'persistent']]
        elif args.case == 'timeout':
            rows = [run_case('timeout', out / 'timeout', tool_timeout=0.15, retry_limit=0)]
        elif args.case == 'handoff':
            rows = [run_case('normal', out / t, task_name=t) for t in ['ambiguous', 'no_data', 'missing_spec']]
        else:
            rows = [run_case('normal', out / 'normal')]
        result = {'case': args.case, 'evidence_kind': 'scripted_local_execution', 'rows': rows,
                  'summary': 'These are actual local runs. Faults, where present, were inserted by the classroom script.'}
    result.setdefault('success', True)
    (out / 'demo.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 0 if result['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
