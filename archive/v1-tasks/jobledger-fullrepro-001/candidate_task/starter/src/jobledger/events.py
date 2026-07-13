from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .models import EventRecord


def make_event(
    seq: int,
    event_type: str,
    *,
    at: str,
    job_id: str | None = None,
    data: dict[str, Any] | None = None,
) -> EventRecord:
    """Create a validated public event record."""
    raise NotImplementedError


def event_totals(events: Iterable[EventRecord]) -> dict[str, int]:
    """Return counts by public event type."""
    raise NotImplementedError
