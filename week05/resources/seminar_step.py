"""Run a Week 5 lesson task and save evidence from its actual local execution."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys


SIMULATIONS = {'t01': 'crash', 't02': 'decide', 't05': 'redo'}
EXERCISES = {'t03': 'route', 't04': 'edges', 't06': 'approval'}
THREADS = ('week05-approve', 'week05-reject', 'week05-recovery')


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')


def require(condition, message):
    if not condition:
        raise ValueError(message)


class LocalRun:
    def __init__(self, output):
        self.output = output
        self.steps = []
        self.workspace = output / 'workflow'

    def invoke(self, label, args, expected=0):
        command = [sys.executable, '-B', '-X', 'utf8', *args]
        child = subprocess.run(command, cwd=Path(__file__).resolve().parent,
                               capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=25)
        log = self.output / f'{label}.log'
        log.write_text(child.stdout + child.stderr, encoding='utf-8')
        record = {'step': label, 'arguments': args, 'returncode': child.returncode, 'log': log.name}
        self.steps.append(record)
        require(child.returncode == expected,
                f'{label} exited with {child.returncode}; expected {expected}. See {log.name}. '
                + (child.stdout or child.stderr).strip()[-1000:])
        result = json.loads(child.stdout)
        require(isinstance(result, dict), f'{label} did not produce an experiment record.')
        evidence = self.output / f'{label}.json'
        save_json(evidence, result)
        record['evidence'] = evidence.name
        return result

    def workflow(self, label, thread, action, *, decision=None, crash=False, expected=0):
        args = ['-m', 'workflow', '--workspace', str(self.workspace), '--thread', thread]
        if crash:
            args += ['--crash-at', 'after_write']
        args.append(action)
        if decision is not None:
            path = self.output / f'{label}-input.json'
            save_json(path, decision)
            args += ['--decision-file', str(path)]
        return self.invoke(label, args, expected)

    def clone_waiting(self, source):
        require(source.is_dir(), 'The saved waiting workflow directory is missing.')
        shutil.copytree(source, self.workspace)


def distinct_processes(first, second):
    require(type(first.get('pid')) is int and type(second.get('pid')) is int and first['pid'] != second['pid'],
            'Expected two independent process IDs.')


def same_report(first, second):
    require(first.get('thread_id') == second.get('thread_id'), 'The workflow thread changed.')
    require(first.get('tool_attempts') == second.get('tool_attempts') == 3,
            'The original three tool attempts were not preserved.')
    require(isinstance(first.get('observations'), list) and len(first['observations']) == 3 and
            first['observations'] == second.get('observations'), 'The saved tool observations changed.')
    require(first.get('report') and first['report'] == second.get('report'), 'The verified report changed.')
    first_tools = [event for event in first['trace'] if event.get('node') == 'Execute']
    second_tools = [event for event in second['trace'] if event.get('node') == 'Execute']
    require(len(first_tools) == 3 and first_tools == second_tools, 'The workflow repeated a tool node.')


def waiting(result, thread):
    require(result.get('thread_id') == thread and result.get('status') == 'awaiting_approval' and
            result.get('next') == ['HumanApproval'] and result.get('interrupts') and result.get('ticket_count') == 0,
            f'{thread} did not pause at HumanApproval with an empty ticket table.')
    action = result.get('pending_action')
    require(isinstance(action, dict) and action.get('action_id') and action.get('payload_hash'),
            'The waiting workflow did not expose its pending action.')
    return action


def finished(result, status, count):
    require(result.get('status') == status and result.get('ticket_count') == count and result.get('next') == [],
            f'Expected {status} with {count} ticket rows and no next node.')


def summary(result):
    fields = ('pid', 'thread_id', 'checkpoint_id', 'status', 'next', 'ticket_count',
              'action_id', 'payload_hash', 'tool_attempts', 'reused', 'ticket', 'tickets', 'error')
    return {key: result[key] for key in fields if key in result}


def waiting_summary(result):
    return dict(summary(result), observation_count=len(result['observations']),
                interrupt_count=len(result['interrupts']),
                executed_nodes=[event['node'] for event in result['trace']])


def prepare(run):
    requests = {}
    records = {}
    for thread in THREADS:
        start = run.workflow(f'{thread}-start', thread, 'start')
        inspect = run.workflow(f'{thread}-inspect', thread, 'inspect')
        distinct_processes(start, inspect)
        same_report(start, inspect)
        require(waiting(start, thread) == waiting(inspect, thread), 'The pending action changed after exit.')
        require(start.get('checkpoint_id') and start['checkpoint_id'] == inspect.get('checkpoint_id'),
                'Inspect did not find the checkpoint written by start.')
        requests[thread] = waiting(inspect, thread)
        records[thread] = {'start': waiting_summary(start), 'inspect': waiting_summary(inspect)}
    return {'processes': records, 'decision_requests': requests, 'report': inspect['report']}


def verify_decisions(run, decision):
    approve, reject = THREADS[:2]
    before_approve = run.workflow('approve-before', approve, 'inspect')
    before_reject = run.workflow('reject-before', reject, 'inspect')
    waiting(before_approve, approve)
    expected_reject = waiting(before_reject, reject)
    invalid = dict(decision['reject'], approved='false')
    error = run.workflow('invalid-decision', reject, 'decide', decision=invalid, expected=2)
    require(error.get('error'), 'The malformed approval did not produce an error.')
    after_invalid = run.workflow('invalid-after', reject, 'inspect')
    distinct_processes(error, after_invalid)
    same_report(before_reject, after_invalid)
    require(waiting(after_invalid, reject) == expected_reject,
            'The malformed approval changed the original pending action.')
    require(before_reject['checkpoint_id'] == after_invalid['checkpoint_id'] and
            before_reject['trace'] == after_invalid['trace'], 'The malformed approval advanced the saved task.')
    approved = run.workflow('approve', approve, 'decide', decision=decision['approve'])
    rejected = run.workflow('reject', reject, 'decide', decision=decision['reject'])
    for before, result, status, count in ((before_approve, approved, 'completed', 1),
                                           (before_reject, rejected, 'rejected', 0)):
        distinct_processes(before, result)
        same_report(before, result)
        finished(result, status, count)
    require(all(event.get('node') != 'ApplyAction' for event in rejected['trace']),
            'The rejection executed ApplyAction.')
    require(all(approved['tickets'][0][key] == decision['approve'][key]
                for key in ('action_id', 'payload_hash')),
            'The ticket does not match the action the learner approved.')
    return {'approval': summary(approved), 'rejection': summary(rejected),
            'invalid_reply': {'error': error, 'before': waiting_summary(before_reject),
                              'after': waiting_summary(after_invalid)}}


def verify_recovery(run, decision):
    thread = THREADS[2]
    before = run.workflow('recovery-before', thread, 'inspect')
    action = waiting(before, thread)
    fault = run.workflow('after-write-fault', thread, 'decide', decision=decision, crash=True, expected=3)
    interrupted = run.workflow('after-fault-inspect', thread, 'inspect')
    distinct_processes(fault, interrupted)
    same_report(before, interrupted)
    require(interrupted.get('next') == ['ApplyAction'] and interrupted.get('ticket_count') == 1,
            'Expected a committed ticket with ApplyAction still pending.')
    resumed = run.workflow('recovery-continue', thread, 'continue')
    distinct_processes(interrupted, resumed)
    distinct_processes(fault, resumed)
    same_report(interrupted, resumed)
    finished(resumed, 'completed', 1)
    require(interrupted.get('action_id') == resumed.get('action_id') == action['action_id'],
            'The action ID changed during recovery.')
    require(resumed.get('reused') is True and interrupted.get('tickets') == resumed.get('tickets') and
            resumed['tickets'][0]['action_id'] == action['action_id'],
            'Recovery must reuse the exact durable ticket row.')
    return {'fault': fault, 'after_fault': summary(interrupted), 'after_continue': summary(resumed)}


def redo_counterexamples(run):
    evidence = run.invoke('redo-counterexamples', ['-m', 'experiments.redo_counterexamples'])
    next_case = evidence['next_in_add']
    spent_case = evidence['spent_not_in_add']
    require(next_case['error'] == 'KeyError' and next_case['merged_next'] == 'read_requestsearch_tickets',
            'Adding next to ADD should attempt to run an unknown node.')
    require(spent_case['expected_total_usd'] == 1140 and spent_case['observed_total_usd'] == 180
            and spent_case['wrong_spent'] == 0,
            'The amount should be overwritten while the simulation reports no inconsistency.')
    return evidence


def observe_interrupt_replay(run):
    evidence = run.invoke('interrupt-demo', ['-m', 'workflow.mechanism_demos', 'interrupt'])
    require(evidence['events'] == ['before interrupt', 'before interrupt', 'after interrupt'],
            'Expected code before interrupt to execute twice and code after it to execute once.')
    return evidence


def observe_payload_collision(run):
    evidence = run.invoke('payload-collision', ['-m', 'workflow.mechanism_demos', 'payload-collision'])
    require(evidence['error'] == 'ApprovalError'
            and evidence['message'] == 'This action ID already has a different payload.'
            and evidence['ticket_count_before'] == evidence['ticket_count_after'] == 1
            and evidence['row_unchanged'] is True,
            'Expected the ticket store to reject a changed payload without changing its existing row.')
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', required=True, choices=[*SIMULATIONS, *EXERCISES, 't07', 't08', 't09'])
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--prepared-workspace', type=Path)
    parser.add_argument('--decision-json')
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    run = LocalRun(output)
    result = {'task': args.task, 'success': False, 'steps': run.steps}
    try:
        if args.task in SIMULATIONS:
            name = SIMULATIONS[args.task]
            result['evidence_kind'] = 'local_simulation'
            result['experiment'] = run.invoke(name, ['-m', 'experiments', name, '--json'])
            if name == 'redo':
                result['counterexamples'] = redo_counterexamples(run)
        elif args.task in EXERCISES:
            check = EXERCISES[args.task]
            result['evidence_kind'] = 'local_exercise_check'
            result['exercise'] = run.invoke(check, ['-m', 'workflow', 'check', check])
        else:
            result['evidence_kind'] = 'langgraph_sqlite_processes'
            if args.task == 't07':
                result['exercise'] = run.invoke('resume-check', ['-m', 'workflow', 'check', 'resume'])
                result.update(prepare(run))
            else:
                require(args.prepared_workspace and args.decision_json, 'A waiting workspace and learner decision are required.')
                run.clone_waiting(args.prepared_workspace)
                decision = json.loads(args.decision_json)
                if args.task == 't08':
                    result['interrupt_demo'] = observe_interrupt_replay(run)
                    result.update(verify_decisions(run, decision))
                else:
                    result.update(verify_recovery(run, decision))
                    result['payload_collision'] = observe_payload_collision(run)
        result['success'] = True
    except (ValueError, OSError, KeyError, subprocess.TimeoutExpired) as exc:
        result['error'] = str(exc)
    save_json(output / 'lesson_result.json', result)
    print(json.dumps({'task': args.task, 'success': result['success'], 'error': result.get('error')}, ensure_ascii=True))
    return 0 if result['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
