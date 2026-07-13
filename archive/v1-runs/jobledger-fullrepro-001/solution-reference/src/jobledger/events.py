from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .models import EventRecord, JobLedgerError

ALLOWED_EVENTS = {
    "enqueued",
    "claimed",
    "completed",
    "failed",
    "retry_scheduled",
    "discarded",
    "cancelled",
    "cron_configured",
    "cron_tick",
    "unique_conflict",
    "pruned",
    "recovered",
}


def make_event(
    seq: int,
    event_type: str,
    *,
    at: str,
    job_id: str | None = None,
    data: dict[str, Any] | None = None,
) -> EventRecord:
    if seq < 1:
        raise JobLedgerError("event sequence must be positive")
    if event_type not in ALLOWED_EVENTS:
        raise JobLedgerError("invalid event type")
    if event_type not in {"cron_configured", "recovered"} and job_id is None:
        raise JobLedgerError("job_id required for job event")
    return EventRecord(seq=seq, at=str(at), type=event_type, job_id=job_id, data=dict(data or {}))


def event_totals(events: Iterable[EventRecord]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for event in events:
        totals[event.type] = totals.get(event.type, 0) + 1
    return totals
