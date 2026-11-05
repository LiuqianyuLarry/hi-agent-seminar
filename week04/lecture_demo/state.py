"""Application-owned state; model content cannot mutate counters or evidence directly."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal
import copy, time, uuid
from pydantic import BaseModel, ConfigDict
from schemas import QueryArgs, SpecArgs

class Task(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')
    question: str
    goal: Literal['report', 'spec', 'readings'] = 'report'
    machine_id: str | None = None
    start: str | None = None
    end: str | None = None

    def missing_fields(self) -> list[str]:
        missing = []
        if not self.machine_id:
            missing.append('machine_id')
        if self.goal != 'spec':
            missing += [key for key in ('start', 'end') if not getattr(self, key)]
        return missing

    def normalized(self) -> 'Task':
        if self.missing_fields():
            return self
        values = self.model_dump()
        if self.goal == 'spec':
            SpecArgs(machine_id=self.machine_id)
        else:
            args = QueryArgs(machine_id=self.machine_id, start=self.start, end=self.end)
            values.update(args.model_dump())
        return Task.model_validate(values)

@dataclass
class Decision:
    kind: str  # tool, finish, human, invalid
    name: str = ''
    arguments: dict[str, Any] = field(default_factory=dict)
    question: str = ''
    # This is a brief action label, NOT private chain-of-thought.
    note: str = ''
    usage_tokens: int | None = None

@dataclass
class Observation:
    id: str
    tool: str
    arguments: dict
    result: dict
    reused: bool = False

@dataclass
class State:
    task: Task
    mode: str
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    started: float = field(default_factory=time.monotonic)
    steps: int = 0
    tool_attempts: int = 0
    no_progress: int = 0
    usage_tokens: int = 0
    status: str = 'running'
    reason: str = ''
    observations: list[Observation] = field(default_factory=list)
    trace: list[dict] = field(default_factory=list)
    last_progress: tuple = ()
    report: dict | None = None

    def log(self, event: str, **fields) -> None:
        self.trace.append({'event_id': len(self.trace)+1, 'step': self.steps,
                           'event': event, 'elapsed_s': round(time.monotonic()-self.started, 6),
                           **copy.deepcopy(fields)})

    def record(self, tool: str, arguments: dict, result: dict, reused: bool = False) -> Observation:
        # BEGIN_SOLUTION W4.1
        observation = Observation(f'obs_{len(self.observations)+1:03d}', tool,
                                  copy.deepcopy(arguments), copy.deepcopy(result), reused)
        self.observations.append(observation)
        self.log('observation', observation_id=observation.id, tool=tool,
                 arguments=arguments, result=result, reused=reused)
        return observation
        # END_SOLUTION W4.1

    def context(self) -> dict:
        """Small bounded lab context. No key, raw traceback, or hidden model items."""
        return copy.deepcopy({'task': self.task.model_dump(), 'steps_used': self.steps,
                'latest_check': next((event for event in reversed(self.trace)
                                      if event['event']=='verify'), None),
                'observations': [dict(id=o.id, tool=o.tool, arguments=o.arguments,
                                      result=o.result, reused=o.reused)
                                 for o in self.observations]})

    def export(self) -> dict:
        return {'run_id': self.run_id, 'mode': self.mode, 'task': self.task.model_dump(),
                'status': self.status, 'reason': self.reason, 'steps': self.steps,
                'tool_attempts': self.tool_attempts, 'no_progress': self.no_progress,
                'reported_api_tokens': self.usage_tokens if self.mode=='live' else None,
                'elapsed_s': round(time.monotonic()-self.started, 6),
                'report': self.report, 'trace': self.trace,
                'warning': ('Scripted controller, actual local tool execution; NOT LLM accuracy.'
                            if self.mode!='live' else
                            'Real model choices; verify facts. Reported tokens are not a prepaid hard cost cap.')}
