"""Budgets and progress checks are controlled by Python, not by the prompt."""
from dataclasses import dataclass
import math, time
from state import State

@dataclass(frozen=True)
class Config:
    max_steps: int = 6
    max_tool_attempts: int = 8
    max_no_progress: int = 2  # 0 disables this check for a bounded classroom comparison.
    total_seconds: float = 60.0
    tool_timeout: float = 3.0
    request_timeout: float = 15.0
    retry_limit: int = 1  # additional attempts per decision, not total attempts.
    retry_backoff: float = 0.05
    token_stop: int = 16000  # post-response circuit breaker, NOT guaranteed spend limit.

    def __post_init__(self):
        for name in ('max_steps','max_tool_attempts','token_stop'):
            if type(getattr(self,name)) is not int or getattr(self,name)<1:
                raise ValueError(f'{name} must be a positive integer')
        for name in ('max_no_progress','retry_limit'):
            if type(getattr(self,name)) is not int or getattr(self,name)<0:
                raise ValueError(f'{name} must be a nonnegative integer')
        for name in ('total_seconds','tool_timeout','request_timeout','retry_backoff'):
            value=getattr(self,name)
            if not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:
                raise ValueError(f'{name} must be finite and positive')


def stop_reason(state: State, cfg: Config) -> str | None:
    # BEGIN_SOLUTION W4.3
    if time.monotonic()-state.started >= cfg.total_seconds:
        return 'deadline'
    if state.steps >= cfg.max_steps:
        return 'max_steps'
    if state.mode=='live' and state.usage_tokens >= cfg.token_stop:
        return 'reported_token_limit'
    if cfg.max_no_progress and state.no_progress >= cfg.max_no_progress:
        return 'no_progress'
    return None
    # END_SOLUTION W4.3


def remaining_seconds(state: State, cfg: Config) -> float:
    return max(0.0, cfg.total_seconds - (time.monotonic()-state.started))
