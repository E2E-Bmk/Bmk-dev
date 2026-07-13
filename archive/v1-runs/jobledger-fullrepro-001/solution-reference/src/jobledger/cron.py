from __future__ import annotations

from .models import CronEntry, JobLedgerError, to_epoch


def next_slot(entry: CronEntry, after: str | int) -> int:
    epoch = to_epoch(after)
    return ((epoch // entry.every_seconds) + 1) * entry.every_seconds


def due_slots(entry: CronEntry, last_slot: int | None, now: str | int) -> list[int]:
    current = to_epoch(now)
    start = entry.every_seconds if last_slot is None else last_slot + entry.every_seconds
    if start <= 0:
        raise JobLedgerError("invalid cron start")
    slots: list[int] = []
    slot = start
    while slot <= current:
        slots.append(slot)
        slot += entry.every_seconds
    return slots
