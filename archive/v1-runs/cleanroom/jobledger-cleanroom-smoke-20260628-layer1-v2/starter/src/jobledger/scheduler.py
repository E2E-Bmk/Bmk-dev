from __future__ import annotations

from collections.abc import Iterable

from .models import JobRecord


def is_due(job: JobRecord, now: str | int | None) -> bool:
    """Return whether a scheduled/retryable job is claimable at now."""
    raise NotImplementedError


def claim_order(jobs: Iterable[JobRecord]) -> list[JobRecord]:
    """Sort claimable jobs by public deterministic claim ordering."""
    raise NotImplementedError
