from __future__ import annotations

from collections.abc import Iterable

from .models import CLAIMABLE_STATES, EventRecord, JobRecord, to_epoch
from .scheduler import is_due


def metrics_from_events(events: Iterable[EventRecord]) -> dict[str, object]:
    totals = {
        "enqueued": 0,
        "claimed": 0,
        "completed": 0,
        "failed": 0,
        "discarded": 0,
        "cancelled": 0,
        "retry_scheduled": 0,
        "unique_conflicts": 0,
        "cron_ticks": 0,
    }
    by_queue: dict[str, dict[str, int]] = {}
    for event in events:
        queue = str(event.data.get("queue", "default"))
        by_queue.setdefault(queue, {})
        if event.type == "unique_conflict":
            totals["unique_conflicts"] += 1
        elif event.type == "cron_tick":
            totals["cron_ticks"] += 1
        elif event.type in totals:
            totals[event.type] += 1
            by_queue[queue][event.type] = by_queue[queue].get(event.type, 0) + 1
    return {"totals": totals, "by_queue": by_queue}


def queue_counts(jobs: Iterable[JobRecord], now: str | int | None = None) -> dict[str, int]:
    counts: dict[str, int] = {}
    for job in jobs:
        if job.state in CLAIMABLE_STATES and is_due(job, to_epoch(now)):
            counts[job.queue] = counts.get(job.queue, 0) + 1
    return counts
