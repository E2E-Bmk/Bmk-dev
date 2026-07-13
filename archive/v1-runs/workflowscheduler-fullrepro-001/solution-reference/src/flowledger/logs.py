"""Public log and event records."""

from __future__ import annotations

from .models import utc
from .store import next_sequence, save_if_possible, state_of


def _public(record: dict) -> dict:
    return dict(record)


def _ordered(records: list[dict]) -> list[dict]:
    return sorted((dict(r) for r in records), key=lambda r: (r.get("recorded_at", ""), int(r.get("sequence", 0))))

def append_event(store, event: dict) -> dict:
    """Append and return a public event record."""
    data = state_of(store)
    record = dict(event)
    record["recorded_at"] = utc(record.get("recorded_at") or record.get("now") or "")
    record.pop("now", None)
    record["sequence"] = next_sequence(store)
    record.setdefault("type", "event")
    data["events"].append(record)
    save_if_possible(store)
    return _public(record)


def append_log(store, log: dict) -> dict:
    """Append and return a public log record."""
    data = state_of(store)
    record = dict(log)
    record["recorded_at"] = utc(record.get("recorded_at") or record.get("now") or "")
    record.pop("now", None)
    record["sequence"] = next_sequence(store)
    record.setdefault("message", "")
    data["logs"].append(record)
    save_if_possible(store)
    return _public(record)


def event_stream(store, run_id: str | None = None) -> list[dict]:
    """Return deterministic public events."""
    data = state_of(store)
    records = data["events"]
    if run_id is not None:
        records = [r for r in records if r.get("run_id") == run_id]
    return _ordered(records)


def log_stream(store, run_id: str | None = None) -> list[dict]:
    """Return deterministic public logs."""
    data = state_of(store)
    records = data["logs"]
    if run_id is not None:
        records = [r for r in records if r.get("run_id") == run_id]
    return _ordered(records)
