"""Run one taught experiment. This script does not answer questions or award progress."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TASK_CASES = {'t02': 'one-shot', 't03': 'bare-loop', 't04': 'gate', 't05': 'state',
              't06': 'verify', 't07': 'guards', 't08': 'loop', 't09': 'compare'}
TEST_FILES = {'state': 'test_state.py', 'verify': 'test_verification.py',
              'guards': 'test_controls.py', 'loop': 'test_runtime.py'}


def run_command(arguments, cwd, output, seconds=180):
    try:
        completed = subprocess.run([sys.executable, '-X', 'utf8', *arguments], cwd=cwd,
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=seconds)
        text = completed.stdout + completed.stderr
        code = completed.returncode
    except subprocess.TimeoutExpired:
        text, code = 'The external experiment timeout stopped this process. This is a failed check, not a successful internal stop.\n', 124
    output.write_text(text, encoding='utf-8')
    return {'arguments': arguments, 'returncode': code, 'log': str(output), 'passed': code == 0}


def reference_copy(source, output):
    if source is None:
        raise ValueError('This opening demonstration needs the saved lecture reference directory. Student exercises were not changed.')
    source = Path(source).resolve()
    if not (source / 'demos.py').is_file() or not (source / 'data/manifest.json').is_file():
        raise ValueError('The saved lecture reference is incomplete. Recover it before running this demonstration.')
    destination = output / 'reference_runtime'
    if destination.exists():
        raise ValueError('Use a new output folder for this demonstration; an earlier copy was not overwritten.')
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns('__pycache__', '.env', '*.sqlite', 'outputs'))
    step = run_command(['build_data.py'], destination, output / 'reference_setup.txt', 30)
    if not step['passed']:
        raise ValueError('The reference data could not be prepared. Read reference_setup.txt.')
    return destination


def teacher_record(path, output):
    if path is None or not Path(path).is_file():
        raise ValueError('The real teacher API record is missing. Do not replace it with a scripted response.')
    path = Path(path)
    source_file = path.with_name('SOURCE.json')
    if not source_file.is_file():
        raise ValueError('The teacher capture has no source manifest. Recover the supplied record and its SOURCE.json.')
    source = json.loads(source_file.read_text(encoding='utf-8'))
    expected = source.get('files', {}).get(path.name)
    if not isinstance(expected, str) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError('The teacher capture differs from its source manifest. It was not used as learning evidence.')
    record = json.loads(path.read_text(encoding='utf-8'))
    if (record.get('evidence_kind') != 'live_deepseek' or record.get('provider') != 'DeepSeek'
            or type(record.get('actual_requests')) is not int or record['actual_requests'] != 1
            or type(record.get('follow_up_requests')) is not int or record['follow_up_requests'] != 0
            or not isinstance(record.get('response', {}).get('id'), str) or not record['response']['id']
            or not isinstance(record.get('captured_at'), str)
            or not isinstance(record.get('request', {}).get('messages'), list)
            or not isinstance(record.get('request', {}).get('tools'), list)
            or not isinstance(record.get('response', {}).get('message'), dict)
            or type(record.get('response', {}).get('usage', {}).get('total_tokens')) is not int
            or type(record.get('requested_tool_calls')) is not int
            or type(record.get('tool_attempts')) is not int
            or not isinstance(record.get('observations'), list)
            or not isinstance(record.get('after', {}).get('missing'), list)
            or type(record.get('after', {}).get('ready')) is not bool):
        raise ValueError('This file is not a complete real one-request teacher capture.')
    saved = output / 'teacher_record.json'
    saved.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    return {'source': str(Path(path).resolve()), 'record': str(saved),
            'captured_at': record.get('captured_at'), 'response_id': record['response']['id'],
            'requested_tool_calls': record['requested_tool_calls'], 'tool_attempts': record['tool_attempts'],
            'actual_requests_in_teacher_capture': 1, 'requests_made_now': 0,
            'missing_evidence': record['after']['missing'], 'ready': record['after']['ready']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', choices=list(TASK_CASES))
    parser.add_argument('--case', choices=[*TASK_CASES.values(), 'wrong-stats', 'live-loop', 'retry', 'timeout', 'handoff', 'workflow', 'boundaries'])
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--reference-dir')
    parser.add_argument('--teacher-record')
    parser.add_argument('--mode', choices=['teacher', 'live', 'scripted'], default='teacher')
    args = parser.parse_args()
    case = args.case or TASK_CASES.get(args.task)
    if not case:
        parser.error('Choose one task or experiment case.')
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    result = {'task': args.task or case, 'case': case, 'success': False, 'checks': [], 'artifacts': [],
              'evidence_kind': 'not_executed', 'summary': '', 'observations': []}
    try:
        if args.mode == 'live':
            # A copied reference runtime receives the private key through its process
            # environment. Never copy the student's .env into an experiment artifact.
            from provider import load_environment
            load_environment()
        if case == 'one-shot' and args.mode != 'live':
            result['observation'] = teacher_record(args.teacher_record, output)
            result.update(success=True, evidence_kind='recorded_live',
                summary='This is a saved real DeepSeek experiment. No model request ran in this student session. Read the original request, response and actual local observations.')
        elif case in TEST_FILES or case == 'boundaries':
            command = ['check_tests.py', '-q', 'tests/' + TEST_FILES[case]] if case in TEST_FILES else ['check_tests.py', '-q', 'tests']
            check = run_command(command, ROOT, output / 'test_output.txt', 200)
            result['checks'].append(check)
            result.update(success=check['passed'], evidence_kind='student_code_tests',
                summary='These tests ran against your current saved code. Read a failed assertion before changing the code; an unfinished exercise can fail with NotImplementedError.')
            if check['passed'] and case in TEST_FILES:
                observation_check = run_command(['student_observations.py', '--case', case, '--out', str(output)],
                    ROOT, output / 'student_observation_console.txt', 90)
                result['checks'].append(observation_check)
                result['success'] = observation_check['passed']
                if observation_check['passed']:
                    observed = json.loads((output / 'student_observation.json').read_text(encoding='utf-8'))
                    result['observation'] = observed
                    result['evidence_kind'] = 'student_code_execution'
                    result['summary'] = observed['summary']
        elif case == 'workflow':
            check = run_command(['baseline.py', '--out', str(output / 'workflow')], ROOT, output / 'console.txt')
            result['checks'].append(check)
            result.update(success=check['passed'], evidence_kind='student_code_local_execution',
                summary='A fixed Python workflow ran without a model. Compare its branches and evidence with the agent loop.')
        else:
            # Opening demonstrations use a separate completed reference; exercises keep their TODOs.
            cwd = reference_copy(args.reference_dir, output) if case in {'one-shot', 'bare-loop', 'gate', 'wrong-stats'} else ROOT
            cases = ['minimal-loop', 'bare-repeat', 'bare-finish'] if case == 'bare-loop' else [case]
            for item in cases:
                destination = output / item
                command = ['demos.py', '--case', item, '--out', str(destination)]
                if item in {'one-shot', 'live-loop'}:
                    if args.mode != 'live':
                        raise ValueError('A live experiment needs the explicit --mode live choice.')
                    command += ['--mode', 'live']
                check = run_command(command, cwd, output / (item + '_console.txt'), 180)
                result['checks'].append(check)
                demo_path = destination / 'demo.json'
                if demo_path.is_file():
                    demo = json.loads(demo_path.read_text(encoding='utf-8'))
                    result['observations'].append({'case': item, 'report': str(demo_path),
                        'evidence_kind': demo['evidence_kind'], 'summary': demo['summary']})
                if not check['passed']:
                    break
            result['success'] = bool(result['checks']) and all(x['passed'] for x in result['checks'])
            result['evidence_kind'] = ('live_deepseek' if case in {'one-shot', 'live-loop'} else
                                      'scripted_fault_injection' if case in {'bare-loop', 'gate', 'wrong-stats'} else 'student_code_local_execution')
            result['summary'] = ('Read the actual observations and explain what the checks established. '
                'Injected faults are deliberate test inputs, not a claim about how often a model fails.')
    except Exception as exc:
        result['summary'] = 'The experiment could not finish: ' + str(exc)
        result['error_type'] = type(exc).__name__
    result['artifacts'] = [str(p) for p in output.rglob('*') if p.is_file()
                           and p.suffix in {'.json', '.jsonl', '.csv', '.txt', '.md'}
                           and 'reference_runtime' not in p.relative_to(output).parts]
    (output / 'lesson_result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 0 if result['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
