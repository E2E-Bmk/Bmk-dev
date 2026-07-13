from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    delay_seconds: float = 1.0
    backoff: float = 2.0


def next_retry_delay(policy: RetryPolicy, attempts: int) -> float | None:
    if attempts >= policy.max_attempts:
        return None
    return policy.delay_seconds * (policy.backoff ** max(0, attempts - 1))
