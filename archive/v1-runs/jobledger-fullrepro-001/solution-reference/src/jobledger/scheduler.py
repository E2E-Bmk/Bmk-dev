from __future__ import annotations

from collections.abc import Iterable

from .models import JobRecord, to_epoch


def is_due(job: JobRecord, now: str | int | None) -> bool:
    if job.state == "available":
        return True
    if job.state not in {"scheduled", "retryable"}:
        return False
    return to_epoch(job.scheduled_at) <= to_epoch(now)


def claim_order(jobs: Iterable[JobRecord]) -> list[JobRecord]:
    def sort_key(job: JobRecord) -> tuple[int, int, str]:
        ready_at = to_epoch(job.scheduled_at) if job.scheduled_at is not None else to_epoch(job.created_at)
        return (job.priority, ready_at, job.id)

    return sorted(jobs, key=sort_key)
