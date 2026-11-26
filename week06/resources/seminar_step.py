"""Small, repeatable experiments on the same classroom case."""
import argparse
import subprocess
import sys
from pathlib import Path

from answers import check_citations, template_answer
from common import ROOT, load, save, utc
from context import evidence_hash, packet_size, select_context
from database import query_engineering, readonly
from documents import eligible, load_chunks, public_evidence
from evaluate import measures
from memory import MemoryStore
from pipeline import run_task
from retrieval import Retriever, rrf
from seed import seed_db


def raw_window(db, task):
    """Read the fixed exhibit before the student repairs the reporting query."""
    params = (task['machine_id'], utc(task['start']), utc(task['end']))
    with readonly(db) as conn:
        rows = conn.execute('SELECT reading_id,temperature_c FROM sensor_reading '
                            'WHERE machine_id=? AND ts>=? AND ts<? ORDER BY ts', params)
        return [dict(row) for row in rows]


def governing_passage(chunks):
    return next(c for c in chunks if c['doc_id'] == 'manual_conv3_review_2026'
                and c['section'].startswith('4.2 '))


def reopen(db, task, chunks):
    return {'checkpoint_example': {'task': 201, 'next': 'Verify'},
            'current_request': task['question'], 'reading_rows': raw_window(db, task),
            'shelf': [c['doc_id'] for c in chunks if c['word_offset'] == 0 and c['section']
                      in ('Archived reference', '4.2 Temperature review and evidence')],
            'draft_for_review': 'Four out of five readings were high. The bearing has failed.'}


def budget(db, task, chunks):
    rows = raw_window(db, task)
    with readonly(db) as conn:
        spec = dict(conn.execute('SELECT * FROM machine WHERE machine_id=?', (task['machine_id'],)).fetchone())
    return {'window_tokens': 12000, 'reserved_tokens': {'instructions_and_tools': 2000, 'reply': 2000, 'buffer': 1000},
            'available_tokens': 12000 - 2000 - 2000 - 1000, 'rows': rows, 'reference': spec,
            'window': [task['start'], task['end']], 'edition': governing_passage(chunks)['version'],
            'strictly_above': sum(row['temperature_c'] > spec['reference_c'] for row in rows),
            'unreviewed_summary': '80% anomalous.'}


def share_checklist(episode):
    return {'past_task': episode['task_id'], 'checklist': list(episode['checklist'])}


def remember(folder, task, chunks):
    memory = MemoryStore(folder / 'preferences.sqlite')
    episode = {'task_id': 183, 'machine': 'CONV-7', 'summary': 'Fan repair recorded.',
               'evidence_ids': ['old-service-note'], 'checklist': ['Check calibration', 'Ask for the load log']}
    memory.put('engineer-a', 'episode183', episode, kind='episode', confirmed=True)
    current = {'rules': 'Use evidence from the current case.', 'task': task,
               'evidence': [{'id': 'fixture:measurement', 'type': 'sql', 'payload': {'count': 5}},
                            public_evidence(governing_passage(chunks))]}
    profiles = {}
    for owner, order in [('engineer-a', 'summary_first'), ('engineer-b', 'evidence_first')]:
        memory.put(owner, 'report_order', order, confirmed=True)
        records = MemoryStore(folder / 'preferences.sqlite').get(owner, now=task['as_of'])
        packet = dict(current, preferences=[r for r in records if r['kind'] == 'preference'])
        answer = template_answer(packet)
        profiles[owner] = {'first_kind': answer['claims'][0]['kind'], 'stored': packet['preferences'],
                           'evidence_hash': evidence_hash(packet)}
    saved = next(r['value'] for r in memory.get('engineer-a', now=task['as_of']) if r['kind'] == 'episode')
    carry = share_checklist(saved)
    assert 'summary' not in carry and len({p['evidence_hash'] for p in profiles.values()}) == 1
    return {'old_episode': saved, 'shared_with_task_202': carry, 'profiles': profiles}


def pack(db, task, chunks):
    # A small, labelled SQL exhibit lets us study packing before writing SQL.
    facts = {'id': 'exhibit:rows', 'type': 'sql', 'payload': raw_window(db, task)}
    doc = public_evidence(governing_passage(chunks))
    second = public_evidence(next(c for c in chunks if c['section'] == 'Interpretation limits'))
    entries = [doc, facts, doc, second]
    full, excluded = select_context(task, entries, [])
    assert [e['id'] for e in full['evidence']] == [facts['id'], doc['id'], second['id']] and not excluded
    smaller = packet_size(dict(full, evidence=[facts, doc]))
    tight, skipped = select_context(task, entries, [], budget_bytes=smaller)
    assert tight['evidence'] == [facts, doc] and skipped == [{'id': second['id'], 'reason': 'context_budget'}]
    try:
        select_context(task, entries, [], budget_bytes=packet_size(dict(full, evidence=[])))
    except ValueError as exc:
        failure = str(exc)
    else:
        raise AssertionError('What happens when the mandatory readings do not fit?')
    return {'input_ids': [e['id'] for e in entries], 'full_bytes': packet_size(full), 'limit_bytes': smaller,
            'kept_ids': [e['id'] for e in tight['evidence']], 'excluded': skipped,
            'required_sql_failure': failure, 'packet': tight}


def sql_lab(db, task):
    evidence = query_engineering(db, task)
    payload = evidence['payload']
    with readonly(db) as conn:
        joined = conn.execute('SELECT COUNT(*) FROM sensor_reading r JOIN maintenance_event e USING(machine_id) '
                              'WHERE r.machine_id=? AND r.ts>=? AND r.ts<?', payload['provenance']['bound_parameters']).fetchone()[0]
        boundary = dict(conn.execute('SELECT * FROM sensor_reading WHERE machine_id=? AND ts=?',
                                     (task['machine_id'], utc(task['end']))).fetchone())
        fault = dict(conn.execute('SELECT confirmation_status,root_cause FROM fault_record WHERE machine_id=?',
                                  (task['machine_id'],)).fetchone())
    assert payload['count'] == 5 and boundary['reading_id'] not in payload['row_ids'], 'The row at 10:25 belongs to the next window.'
    assert joined == 10 and payload['statistics']['exceed_count'] == 4
    assert not query_engineering(db, load(ROOT/'tasks/empty.json'))['payload']['row_ids']
    return {'joined_row_count': joined, 'correct_query': evidence, 'next_window_row': boundary, 'fault_record': fault}


def scope_lab(task, chunks):
    search = Retriever(chunks)
    settings = dict(machine_id=task['machine_id'], model_code='MX-A', as_of=task['as_of'])
    comparison = {}
    for filtered in (False, True):
        docs, trace = search.search('temperature reference threshold', method='keyword', filter_scope=filtered, **settings)
        comparison['with_scope' if filtered else 'without_scope'] = {
            'candidates': trace['candidate_count'], 'ranked_sources': [d['payload']['doc_id'] for d in docs],
            'ids': trace['returned_ids']}
    old = next(c for c in chunks if c['doc_id'] == 'manual_conv3_v1')
    assert not eligible(old, **dict(settings, as_of=old['valid_to'])), 'At valid_to, the old edition has expired.'
    for c in chunks:
        if c['machine_id'] != 'CONV-3' or c['access'] != 'public' or c['doc_id'].endswith('_future'):
            assert not eligible(c, **settings), 'Check machine, date and access before ranking.'
    rule = governing_passage(chunks)
    return dict(comparison, expiry_probe=old['valid_to'], indexed_passage=public_evidence(rule),
                eligible_now=eligible(rule, **settings))


def ranked_lab(task, chunks):
    rankings = [['A', 'B', 'C'], ['B', 'D', 'A']]
    fused = rrf(rankings)
    assert fused == ['B', 'A', 'D', 'C'], 'Rank positions start at one. Add contributions across lists.'
    assert rrf([['B', 'B'], ['A']]) == ['A', 'B'], 'Count a repeated ID once per list; break ties by ID.'
    ret = Retriever(chunks)
    settings = dict(machine_id=task['machine_id'], model_code='MX-A', as_of=task['as_of'])
    question = task['question']
    docs, trace = ret.search(question, **settings)
    reranked, second = ret.search(question, reranker='heuristic', **settings)
    return {'example_lists': rankings, 'fused': fused, 'trace': trace, 'reranker': second['reranker'],
            'after_rerank': [d['id'] for d in reranked], 'source_lines': [d['payload']['source_ref'] for d in docs]}


def sign_off(folder, db, chunks):
    reports = {}
    for route in ('sql', 'rag', 'combined', 'unknown_topic'):
        request = load(ROOT/'tasks'/f'{route}.json')
        report = run_task(request, db=db, memory_db=folder/'memory.sqlite', chunks=chunks)
        save(folder/f'{route}.json', report)
        reports[route] = report
    report = reports['combined']
    evidence = report['context']['evidence']
    rule_id = governing_passage(chunks)['chunk_id']
    rule = next(item for item in evidence if item['id'] == rule_id)
    claim = {'text': 'Bearing failure is confirmed.', 'evidence_ids': [rule_id]}
    evaluation = load(ROOT/'evaluation/queries.json')
    q = next(row for row in evaluation if row['id'] == 'review')
    found, trace = Retriever(chunks).search(q['question'], machine_id=q['machine_id'], model_code=q['model_code'], as_of=q['as_of'])
    return {'routes': {key: [s['stage'] for s in val['trace']] for key, val in reports.items()},
            'run_files': [f'{key}.json' for key in reports],
            'measurement': next(c for c in report['answer']['claims'] if c['kind'] == 'measurement'),
            'rule': rule, 'constructed_claim': claim,
            'id_check': check_citations({'claims': [claim]}, report['context']),
            'retrieval_metrics': measures(found, q['relevant_units'], 3),
            'scope_comparison': scope_lab(report['task'], chunks),
            'torque_status': reports['unknown_topic']['status'],
            'torque_passages': [e['payload']['text'] for e in reports['unknown_topic']['context']['evidence'] if e['type']=='document']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--task', required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    folder = args.output_dir
    folder.mkdir(parents=True, exist_ok=True)
    task = load(ROOT/'tasks/combined.json')
    try:
        chunks = load_chunks()
        db = seed_db(folder/'engineering.sqlite')
        experiments = {'t01': lambda: reopen(db, task, chunks), 't02': lambda: budget(db, task, chunks),
                       't03': lambda: remember(folder, task, chunks), 't04': lambda: pack(db, task, chunks),
                       't05': lambda: sql_lab(db, task), 't06': lambda: scope_lab(task, chunks),
                       't07': lambda: ranked_lab(task, chunks), 't08': lambda: sign_off(folder, db, chunks)}
        result = experiments[args.task]()
        target = {'t04': 'packet', 't05': 'query', 't06': 'scope', 't07': 'fusion'}.get(args.task)
        if target:
            check = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-k', target],
                                   cwd=ROOT, capture_output=True, text=True, timeout=30)
            if check.returncode or 'Ran 1 test' not in check.stderr:
                raise AssertionError(check.stderr.strip() or 'The exercise check did not run.')
            result['exercise_check'] = {'target': target, 'passed': True, 'output': check.stderr.strip()}
    except Exception as exc:
        save(folder/'lesson_result.json', {'success': False, 'task': args.task, 'error': f'{type(exc).__name__}: {exc}'})
        raise
    save(folder/'lesson_result.json', {'success': True, 'task': args.task, 'evidence_kind': 'local_experiment', **result})
    print('Open lesson_result.json for the observations from this run.')


if __name__ == '__main__':
    main()

