"""Small real outputs after the matching student tests pass. No model calls."""
from dataclasses import asdict
import copy
import json
from pathlib import Path
import time
from controls import Config, stop_reason
from demos import default_task
from gateway import ToolRunner
from planner import ScriptedPlanner
from state import State, Decision
from verification import verify, matching_sources, statistics_inputs_match
from runtime import run_agent
from app import save_outputs


def record_example():
    state = State(default_task(), 'student_code_example')
    arguments = {'machine_id': state.task.machine_id}
    result = {'status': 'ok', 'data': {'temperature_limit_c': 85.0},
              'source': 'small_copy_example', 'version': 'example-v1'}
    observation = state.record('get_machine_spec', arguments, result)
    arguments['machine_id'] = 'CONV-7'
    result['data']['temperature_limit_c'] = 99.0
    return {'case': 'state', 'evidence_kind': 'student_code_execution',
            'input_is_teaching_example': True, 'observation': asdict(observation),
            'original_arguments_after_edit': arguments, 'original_result_after_edit': result,
            'trace': state.trace, 'summary': 'Your record function saved this example. Compare its stored values with the edited original dictionaries.'}


def verification_example():
    task = default_task()
    state = State(task, 'student_code_execution')
    runner = ToolRunner()
    cfg = Config(total_seconds=40, tool_timeout=5)
    snapshots = [{'stage': 'before_tools', 'check': asdict(verify(state))}]
    runner.execute(state, Decision('tool', 'query_temperature', {
        'machine_id': task.machine_id, 'start': task.start, 'end': task.end}), cfg)
    snapshots.append({'stage': 'after_readings', 'check': asdict(verify(state))})
    runner.execute(state, Decision('tool', 'get_machine_spec', {'machine_id': task.machine_id}), cfg)
    spec, query = matching_sources(state)
    values = [row.temperature_c for row in query[1].records]
    limit = spec[1].temperature_limit_c
    rows = []
    case_states = {}
    # Each case starts from the same saved sources, with no earlier statistics.
    for label, supplied_values, supplied_limit in [
            ('correct', values, limit),
            ('wrong_count', [1.0, 2.0], limit),
            ('same_count_same_summary_wrong_values', [82.0, 88.0, 90.0, 94.0, 97.0], limit),
            ('wrong_limit', values, 100.0)]:
        case_state = copy.deepcopy(state)
        observation = runner.execute(case_state, Decision('tool', 'temperature_stats', {
            'values_c': supplied_values, 'limit_c': supplied_limit}), cfg)
        check = verify(case_state)
        rows.append({'case': label, 'arguments': observation.arguments,
                     'tool_statistics': observation.result['data'],
                     'inputs_match': statistics_inputs_match(observation, values, limit),
                     'check': asdict(check), 'observation': asdict(observation)})
        case_states[label] = case_state
    correct_summary = rows[0]['tool_statistics']
    for row in rows:
        row['same_summary_as_correct'] = row['tool_statistics'] == correct_summary
    snapshots.append({'stage': 'after_wrong_statistics', 'check': rows[1]['check']})
    snapshots.append({'stage': 'after_matching_statistics', 'check': rows[0]['check']})
    empty_task = default_task('no_data')
    empty = State(empty_task, 'student_code_execution')
    ToolRunner().execute(empty, Decision('tool', 'query_temperature', {
        'machine_id': empty_task.machine_id, 'start': empty_task.start, 'end': empty_task.end}), cfg)
    empty_report = asdict(verify(empty))
    empty.task = empty.task.model_copy(update={'goal': 'readings'})
    empty_readings = asdict(verify(empty))
    return {'case': 'verify', 'evidence_kind': 'student_code_execution', 'actual_local_tools': True,
            'stages': snapshots, 'observations': [asdict(o) for o in case_states['correct'].observations],
            'comparison_rows': rows, 'cases_are_independent': True,
            'observed_inputs': {'values_c': values, 'limit_c': limit},
            'case_note': 'These inputs were selected for this comparison. The local tools actually ran; no model was called. Observation IDs belong to each separate case.',
            'empty_result': empty.observations[0].result,
            'empty_report_goal_check': empty_report, 'empty_readings_goal_check': empty_readings,
            'summary': 'Your two verifier functions checked actual local results. Compare the input lists even when every returned statistic matches. Then compare the two goals for the same empty query.'}


def guard_example():
    cfg = Config(max_steps=3, max_no_progress=2, total_seconds=60)
    state = State(default_task(), 'student_code_example')
    rows = []
    for label, steps, no_progress, age in [('room_to_continue', 2, 0, 0),
            ('decision_limit', 3, 0, 0), ('no_new_evidence', 0, 2, 0), ('time_limit', 0, 0, 61)]:
        state.steps = steps
        state.no_progress = no_progress
        state.started = time.monotonic() - age
        reason = stop_reason(state, cfg)
        rows.append({'case': label, 'steps': state.steps, 'no_progress': state.no_progress,
                     'elapsed_at_least_seconds': age, 'returned_stop_reason': reason})
    return {'case': 'guards', 'evidence_kind': 'student_code_execution',
            'inputs_are_boundary_examples': True, 'config': asdict(cfg), 'rows': rows,
            'summary': 'Your stop function ran on four supplied boundary examples. These counters were set for this check; they are not a live model trace.'}


def loop_example(out):
    cfg = Config(total_seconds=30, tool_timeout=5)
    state = run_agent(default_task(), ScriptedPlanner('normal'), cfg)
    data = save_outputs(state, Path(out) / 'normal_run', cfg)
    return {'case': 'loop', 'evidence_kind': 'student_code_execution',
            'planner_kind': 'scripted', 'actual_local_tools': True, 'run': data,
            'summary': 'Your connected loop ran the actual local tools. Find the observations, final check and stop event.'}


def save_example(case, out):
    value = {'state': record_example, 'verify': verification_example, 'guards': guard_example}.get(case)
    result = value() if value else loop_example(out)
    path = Path(out) / 'student_observation.json'
    path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return path, result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', required=True, choices=['state', 'verify', 'guards', 'loop'])
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    Path(args.out).mkdir(parents=True, exist_ok=True)
    _, data = save_example(args.case, args.out)
    print(json.dumps(data, indent=2))
