"""Virtual-clock scheduling and overlap decisions."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .models import FlowLedgerError
from .models import WorkflowSpec


def _dt(value: str) -> datetime:
    from .models import utc

    return datetime.fromisoformat(utc(value).replace("Z", "+00:00")).astimezone(timezone.utc)


def _ts(value: datetime) -> str:
    value = value.astimezone(timezone.utc)
    text = value.isoformat(timespec="microseconds" if value.microsecond else "seconds")
    return text.replace("+00:00", "Z")


def due_slots(spec: WorkflowSpec, last_slot: str | None, now: str) -> list[str]:
    """Return schedule slots due at `now` under the public catch-up policy."""
    if not spec.schedule:
        return []
    every = int(spec.schedule.get("every_seconds", 0))
    if every <= 0:
        raise FlowLedgerError("invalid_schedule", "every_seconds must be positive")
    catchup = spec.schedule.get("catchup", "latest")
    now_dt = _dt(now)
    if last_slot is None:
        return [_ts(now_dt)]
    cursor = _dt(last_slot) + timedelta(seconds=every)
    if cursor > now_dt:
        return []
    slots: list[str] = []
    while cursor <= now_dt:
        slots.append(_ts(cursor))
        cursor += timedelta(seconds=every)
    if catchup == "all":
        return slots
    if catchup == "latest":
        return slots[-1:]
    if catchup == "skip":
        return [_ts(now_dt)]
    raise FlowLedgerError("invalid_schedule", "unknown catchup policy", {"catchup": catchup})


def apply_overlap(policy: str, active_run_ids: list[str], queued_run_ids: list[str], new_slots: list[str]) -> dict:
    """Return enqueue/cancel decisions for the public overlap policy."""
    if policy == "all":
        return {"enqueue_slots": list(new_slots), "cancel_run_ids": []}
    if policy == "skip":
        if active_run_ids:
            return {"enqueue_slots": [], "cancel_run_ids": []}
        return {"enqueue_slots": list(new_slots), "cancel_run_ids": []}
    if policy == "latest":
        if not new_slots:
            return {"enqueue_slots": [], "cancel_run_ids": []}
        return {"enqueue_slots": [new_slots[-1]], "cancel_run_ids": list(queued_run_ids)}
    raise FlowLedgerError("invalid_schedule", "unknown overlap policy", {"overlap": policy})


def next_run(spec: WorkflowSpec, last_slot: str | None, now: str) -> dict:
    """Return the public next-run projection."""
    if not spec.schedule:
        return {"workflow": spec.name, "scheduled": False, "due_slots": [], "next_slot": None, "last_slot": last_slot}
    every = int(spec.schedule["every_seconds"])
    now_dt = _dt(now)
    if last_slot is None:
        next_slot = _ts(now_dt)
    else:
        next_dt = _dt(last_slot) + timedelta(seconds=every)
        while next_dt <= now_dt:
            next_dt += timedelta(seconds=every)
        next_slot = _ts(next_dt)
    return {
        "workflow": spec.name,
        "scheduled": True,
        "last_slot": last_slot,
        "due_slots": due_slots(spec, last_slot, now),
        "next_slot": next_slot,
        "schedule": dict(spec.schedule),
    }
