from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetryDecision:
    state: str
    delay_seconds: int | None


def retry_delay_seconds(attempt: int) -> int:
    """Return public deterministic retry delay for a failed attempt."""
    raise NotImplementedError


def decide_retry(attempt: int, max_attempts: int) -> RetryDecision:
    """Return retryable/discarded decision for the next state."""
    raise NotImplementedError
