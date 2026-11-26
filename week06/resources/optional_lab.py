"""Opt-in comparisons; core sessions do not call external services."""
import argparse
import os
from pathlib import Path

from common import ROOT, load, save
from evaluate import evaluate
from pipeline import run_task
from seed import seed_db


def compare(name, folder):
    if name == 'bench':
        rows = evaluate(out=folder)
        return {'trials': len(rows), 'sample': rows[:3], 'details': 'retrieval_results.csv'}
    db = seed_db(folder/'engineering.sqlite')
    options = {}
    if name == 'semantic':
        options = {'encoder': 'local-sentence', 'model_path': os.environ['W6_MODEL_PATH']}
        if os.getenv('W6_RERANKER_PATH'):
            options.update(reranker='cross-encoder', reranker_path=os.environ['W6_RERANKER_PATH'])
    elif name == 'postgres':
        options = {'backend': 'postgres', 'encoder': 'local-sentence', 'model_path': os.environ['W6_MODEL_PATH']}
    elif name == 'deepseek':
        options = {'generation': 'live', 'model': os.environ['DEEPSEEK_MODEL']}
    else:
        raise ValueError('Choose a listed optional experiment.')
    result = run_task(load(ROOT/'tasks/combined.json'), db=db, memory_db=folder/'preferences.sqlite', **options)
    save(folder/'report.json', result)
    return {'backend': result['backend'], 'encoder': result['encoder'], 'generation': result['generation'],
            'trace': result['trace'], 'claims': result['answer']['claims'], 'citation_check': result['citation_check']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--task', required=True)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    try:
        evidence = compare(args.task, args.output_dir)
    except Exception as exc:
        # External drivers may include connection details. Keep the saved error credential-free.
        save(args.output_dir/'lesson_result.json', {'success': False, 'task': args.task,
             'error': type(exc).__name__, 'next': 'Check OPTIONAL.md for this experiment and inspect the local prerequisites.'})
        raise SystemExit(1)
    save(args.output_dir/'lesson_result.json', {'success': True, 'evidence_kind': 'optional_experiment', **evidence})

