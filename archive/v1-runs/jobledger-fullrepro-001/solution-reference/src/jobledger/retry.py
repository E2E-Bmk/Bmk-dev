from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetryDecision:
    state: str
    delay_seconds: int | None


def retry_delay_seconds(attempt: int) -> int:
    if attempt < 1:
        raise ValueError("attempt must be positive")
    return 10 * (2 ** (attempt - 1))


def decide_retry(attempt: int, max_attempts: int) -> RetryDecision:
    if attempt < max_attempts:
        return RetryDecision("retryable", retry_delay_seconds(attempt))
    return RetryDecision("discarded", None)
