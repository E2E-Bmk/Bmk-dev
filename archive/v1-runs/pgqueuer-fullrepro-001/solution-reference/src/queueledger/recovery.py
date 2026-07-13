from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace

from .models import JobStatus
from .store import Store


@dataclass(frozen=True)
class RecoveryReport:
    recovered: list[str]
    untouched: list[str]


def recover_stale_jobs(store: Store, *, now: float, heartbeat_timeout: float) -> RecoveryReport:
    recovered: list[str] = []
    untouched: list[str] = []
    updated = []
    for job in store.list_jobs():
        if job.status == JobStatus.PICKED and job.heartbeat is not None and now - job.heartbeat >= heartbeat_timeout:
            updated.append(replace(job, status=JobStatus.QUEUED, heartbeat=None, updated_at=now))
            recovered.append(job.id)
        else:
            updated.append(job)
            untouched.append(job.id)
    store.replace_jobs(updated)
    return RecoveryReport(recovered=recovered, untouched=untouched)
