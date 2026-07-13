from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from .models import CLAIMABLE_STATES, TERMINAL_STATES, EventRecord, JobRecord, to_epoch
from .scheduler import is_due


def state_counts(jobs: Iterable[JobRecord]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for job in jobs:
        counts[job.state] = counts.get(job.state, 0) + 1
    return dict(sorted(counts.items()))


def queue_state_matrix(jobs: Iterable[JobRecord]) -> dict[str, dict[str, int]]:
    matrix: dict[str, dict[str, int]] = {}
    for job in jobs:
        matrix.setdefault(job.queue, {})
        matrix[job.queue][job.state] = matrix[job.queue].get(job.state, 0) + 1
    return {queue: dict(sorted(states.items())) for queue, states in sorted(matrix.items())}


def claimable_counts(jobs: Iterable[JobRecord], now: str | int | None = None) -> dict[str, int]:
    counts: dict[str, int] = {}
    for job in jobs:
        if job.state in CLAIMABLE_STATES and is_due(job, now):
            counts[job.queue] = counts.get(job.queue, 0) + 1
    return dict(sorted(counts.items()))


def terminal_counts(jobs: Iterable[JobRecord]) -> dict[str, int]:
    counts = {state: 0 for state in sorted(TERMINAL_STATES)}
    for job in jobs:
        if job.state in TERMINAL_STATES:
            counts[job.state] += 1
    return counts


def queue_report_from_jobs(jobs: Iterable[JobRecord], now: str | int | None = None) -> dict[str, Any]:
    materialized = list(jobs)
    return {
        "claimable": claimable_counts(materialized, now),
        "by_state": state_counts(materialized),
        "by_queue": queue_state_matrix(materialized),
        "terminal": terminal_counts(materialized),
        "total": len(materialized),
    }


def conflict_report_from_events(events: Iterable[EventRecord]) -> dict[str, Any]:
    conflicts = [event.to_dict() for event in events if event.type == "unique_conflict"]
    by_queue: dict[str, int] = {}
    for event in conflicts:
        queue = str(event.get("data", {}).get("queue", "default"))
        by_queue[queue] = by_queue.get(queue, 0) + 1
    return {
        "conflicts": conflicts,
        "count": len(conflicts),
        "by_queue": dict(sorted(by_queue.items())),
    }


def event_timeline(events: Iterable[EventRecord]) -> list[dict[str, Any]]:
    return [event.to_dict() for event in sorted(events, key=lambda item: item.seq)]


def event_type_matrix(events: Iterable[EventRecord]) -> dict[str, dict[str, int]]:
    matrix: dict[str, dict[str, int]] = defaultdict(dict)
    for event in events:
        queue = str(event.data.get("queue", "default"))
        matrix[queue][event.type] = matrix[queue].get(event.type, 0) + 1
    return {queue: dict(sorted(types.items())) for queue, types in sorted(matrix.items())}


def job_age_buckets(jobs: Iterable[JobRecord], now: str | int) -> dict[str, int]:
    current = to_epoch(now)
    buckets = {"lt_60": 0, "lt_3600": 0, "gte_3600": 0}
    for job in jobs:
        age = current - to_epoch(job.created_at)
        if age < 60:
            buckets["lt_60"] += 1
        elif age < 3600:
            buckets["lt_3600"] += 1
        else:
            buckets["gte_3600"] += 1
    return buckets


def history_report(job: JobRecord, attempts: list[dict[str, Any]], events: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "job": job.to_dict(),
        "attempts": attempts,
        "events": sorted(events, key=lambda item: item["seq"]),
        "terminal": job.state in TERMINAL_STATES,
    }


def public_projection(
    *,
    jobs: Iterable[JobRecord],
    events: Iterable[EventRecord],
    metrics: dict[str, Any],
    now: str | int | None = None,
) -> dict[str, Any]:
    materialized_jobs = list(jobs)
    materialized_events = list(events)
    return {
        "jobs": [job.to_dict() for job in sorted(materialized_jobs, key=lambda item: item.id)],
        "queue_report": queue_report_from_jobs(materialized_jobs, now),
        "events": event_timeline(materialized_events),
        "event_matrix": event_type_matrix(materialized_events),
        "metrics": metrics,
    }
