from __future__ import annotations

from collections.abc import Iterable

from .models import EventRecord, JobRecord


def metrics_from_events(events: Iterable[EventRecord]) -> dict[str, object]:
    """Replay public event stream into metrics rollups."""
    raise NotImplementedError


def queue_counts(jobs: Iterable[JobRecord], now: str | int | None = None) -> dict[str, int]:
    """Return public claimable/pending counts by queue."""
    raise NotImplementedError
