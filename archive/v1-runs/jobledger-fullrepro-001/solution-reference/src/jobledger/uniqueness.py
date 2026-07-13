from __future__ import annotations

import json
from collections.abc import Iterable

from .models import JobRecord, UniquePolicy, to_epoch


def uniqueness_key(job: JobRecord, policy: UniquePolicy) -> str:
    parts: list[object] = []
    for field in policy.fields:
        if field == "kind":
            parts.append(job.kind)
        elif field == "queue":
            parts.append(job.queue)
        elif field == "args":
            parts.append(job.args)
    return json.dumps(parts, sort_keys=True, separators=(",", ":"))


def find_conflict(
    candidate: JobRecord,
    existing: Iterable[JobRecord],
    now: str | int | None = None,
) -> JobRecord | None:
    if candidate.unique is None:
        return None
    policy = candidate.unique
    key = uniqueness_key(candidate, policy)
    current = to_epoch(now)
    for job in existing:
        if job.id == candidate.id or job.unique is None:
            continue
        if job.state not in policy.states:
            continue
        if uniqueness_key(job, policy) != key:
            continue
        created = to_epoch(job.created_at)
        if current and current - created >= policy.period_seconds:
            continue
        return job
    return None
