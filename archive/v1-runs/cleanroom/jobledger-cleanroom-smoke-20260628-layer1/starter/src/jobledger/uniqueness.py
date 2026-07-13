from __future__ import annotations

from collections.abc import Iterable

from .models import JobRecord, UniquePolicy


def uniqueness_key(job: JobRecord, policy: UniquePolicy) -> str:
    """Build a stable public uniqueness key from policy-selected fields."""
    raise NotImplementedError


def find_conflict(
    candidate: JobRecord,
    existing: Iterable[JobRecord],
    now: str | int | None = None,
) -> JobRecord | None:
    """Return the conflicting job, if the candidate's unique policy blocks it."""
    raise NotImplementedError
