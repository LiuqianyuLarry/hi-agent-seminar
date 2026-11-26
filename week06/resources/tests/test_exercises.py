"""Run one check after its exercise: python -m unittest discover -s tests -k packet."""
from pathlib import Path
import tempfile
import unittest

from common import ROOT, load
from context import packet_size, select_context
from documents import eligible, load_chunks
from retrieval import rrf
from seed import seed_db
from seminar_step import sql_lab


class ExerciseChecks(unittest.TestCase):
    def test_packet_keeps_whole_items_and_only_preferences(self):
        task = {'question': 'Check these readings.'}
        facts = {'id': 'rows', 'type': 'sql', 'payload': [82, 87]}
        passage = {'id': 'manual', 'type': 'document', 'payload': 'Temperature in °C'}
        pref = {'kind': 'preference', 'key': 'report_order', 'value': 'summary_first'}
        old = {'kind': 'episode', 'key': 'old-cause', 'value': 'fan repair'}
        full, dropped = select_context(task, [passage, facts, passage], [old, pref])
        self.assertEqual(full['preferences'], [pref])
        self.assertEqual(full['evidence'], [facts, passage])
        self.assertEqual(dropped, [])
        exact = packet_size(full)
        for limit, expected in [(exact, [facts, passage]), (exact - 1, [facts])]:
            packet, excluded = select_context(task, [passage, facts], [old, pref], budget_bytes=limit)
            self.assertEqual(packet['evidence'], expected)
            self.assertEqual(excluded, [] if limit == exact else [{'id': 'manual', 'reason': 'context_budget'}])
        with self.assertRaises(ValueError):
            select_context(task, [facts], [pref], budget_bytes=1)

    def test_query_uses_both_time_bounds(self):
        with tempfile.TemporaryDirectory() as folder:
            result = sql_lab(seed_db(Path(folder)/'check.sqlite'), load(ROOT/'tasks/combined.json'))
            self.assertEqual(result['correct_query']['payload']['row_ids'],
                             ['R0002', 'R0003', 'R0004', 'R0005', 'R0006'])
            self.assertIsNone(result['fault_record']['root_cause'])

    def test_scope_checks_date_model_machine_and_role(self):
        old = next(c for c in load_chunks() if c['doc_id'] == 'manual_conv3_v1')
        criteria = dict(machine_id='CONV-3', model_code='MX-A', as_of=old['valid_from'], role='student')
        self.assertTrue(eligible(old, **criteria))
        for update in ({'model_code': 'MX-B'}, {'machine_id': 'CONV-7'}, {'as_of': old['valid_to']}):
            self.assertFalse(eligible(old, **dict(criteria, **update)))
        self.assertFalse(eligible(dict(old, access='restricted'), **criteria))

    def test_fusion_counts_duplicates_once_per_list(self):
        self.assertEqual(rrf([['A', 'B', 'C'], ['B', 'D', 'A']]), ['B', 'A', 'D', 'C'])
        self.assertEqual(rrf([['B', 'B'], ['A']]), ['A', 'B'])
        self.assertEqual(rrf([[], []]), [])
        with self.assertRaises(ValueError):
            rrf([['A']], k=0)

