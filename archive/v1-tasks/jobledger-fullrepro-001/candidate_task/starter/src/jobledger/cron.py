from __future__ import annotations

from .models import CronEntry


def next_slot(entry: CronEntry, after: str | int) -> int:
    """Return the next epoch-second slot strictly after the given time."""
    raise NotImplementedError


def due_slots(entry: CronEntry, last_slot: int | None, now: str | int) -> list[int]:
    """Return schedule slots that should be materialized up to now."""
    raise NotImplementedError
