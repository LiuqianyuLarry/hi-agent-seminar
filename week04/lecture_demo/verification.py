"""A task-specific verifier, NOT a general factual verifier for arbitrary questions."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
import math
from schemas import ToolResult, SpecData, QueryData, StatsData
from state import State, Observation

@dataclass
class Check:
    ready: bool
    missing: list[str]
    progress: tuple[str, ...]
    evidence_ids: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)


def _valid_result(obs: Observation, cls):
    try:
        result = ToolResult.model_validate(obs.result)
        if result.status != 'ok' or not result.source or not result.version:
            return None
        return cls.model_validate(result.data)
    except (ValueError, TypeError):
        return None


def matching_sources(state: State):
    task = state.task
    spec = query = None
    for obs in state.observations:
        if obs.reused:
            continue
        if obs.tool == 'get_machine_spec':
            data = _valid_result(obs, SpecData)
            if (data and obs.arguments == {'machine_id': task.machine_id}
                    and data.machine_id == task.machine_id):
                spec = (obs, data)
        if obs.tool == 'query_temperature':
            data = _valid_result(obs, QueryData)
            expected = {'machine_id': task.machine_id, 'start': task.start, 'end': task.end}
            if not data or obs.arguments != expected:
                continue
            if (data.machine_id, data.start, data.end) != (task.machine_id, task.start, task.end):
                continue
            try:
                timestamps = [datetime.fromisoformat(row.ts) for row in data.records]
                start, end = datetime.fromisoformat(task.start), datetime.fromisoformat(task.end)
                if timestamps != sorted(timestamps) or len(set(timestamps)) != len(timestamps):
                    continue
                if any(not start <= value < end for value in timestamps):
                    continue
            except (TypeError, ValueError):
                continue
            query = (obs, data)
    return spec, query


def statistics_inputs_match(obs: Observation, values: list[float], limit: float) -> bool:
    """Check that this calculation used the saved readings and reference limit."""
    if obs.arguments != {'values_c': values, 'limit_c': limit}:
        return False
    return True


def matching_stats(state: State, spec, query):
    if not spec or not query or query[1].count == 0:
        return None
    limit = spec[1].temperature_limit_c
    values = [row.temperature_c for row in query[1].records]
    count = len(values)
    above = sum(value > limit for value in values)
    for obs in reversed(state.observations):
        if obs.reused or obs.tool != 'temperature_stats':
            continue
        # Input matching is separate from checking the calculated numbers below.
        if not statistics_inputs_match(obs, values, limit):
            continue
        data = _valid_result(obs, StatsData)
        if not data or data.count != count or data.above_count != above:
            continue
        expected = [limit, math.fsum(values)/count, max(values), above/count]
        actual = [data.limit_c, data.mean_c, data.max_c, data.above_fraction]
        if all(math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9) for a,b in zip(actual,expected)):
            return obs, data
    return None


def verify(state: State) -> Check:
    spec, query = matching_sources(state)
    stats = matching_stats(state, spec, query)
    # BEGIN_SOLUTION W4.2A
    found = {'spec': spec, 'readings': query, 'stats': stats}
    required = {'spec': ['spec'], 'readings': ['readings'],
                'report': ['spec', 'readings', 'stats']}[state.task.goal]
    missing = [name for name in required if not found[name]]
    if state.task.goal=='report' and query and query[1].count==0:
        missing.append('nonempty_readings')
    progress = tuple(name for name in required if found[name])
    evidence_ids = [found[name][0].id for name in required if found[name]]
    facts = {name: found[name][1].model_dump() for name in required if found[name]}
    return Check(not missing, missing, progress, evidence_ids, facts)
    # END_SOLUTION W4.2A


def build_report(state: State, check: Check) -> dict:
    if not check.ready:
        raise ValueError('Do not render a success report from incomplete evidence')
    facts = check.facts
    if state.task.goal == 'report':
        s = facts['stats']
        summary = (f"{state.task.machine_id}: {s['count']} readings in the confirmed window. "
                   f"Mean {s['mean_c']:.2f} C; maximum {s['max_c']:.2f} C. "
                   f"{s['above_count']}/{s['count']} readings ({s['above_fraction']:.1%}) "
                   f"were strictly above the registered limit of {s['limit_c']:.2f} C.")
    elif state.task.goal == 'spec':
        summary = f"{state.task.machine_id}: registered classroom temperature limit {facts['spec']['temperature_limit_c']} C."
    else:
        summary = f"The query completed with {facts['readings']['count']} readings in the confirmed window."
    sources = [{'id': o.id, 'tool': o.tool, 'source': o.result.get('source'),
                'version': o.result.get('version')} for o in state.observations if o.id in check.evidence_ids]
    return {'summary': summary, 'facts': facts, 'evidence': sources,
            'limitations': ['Synthetic classroom data, not a real equipment diagnosis.',
                            'A share of readings is not a duration or proof of a cause.',
                            'Verification checks the data links and numbers for this task, not the truth of the external source.']}
