"""Durable queue and lease primitives."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .models import FlowLedgerError, utc
from .store import next_id, save_if_possible, state_of


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(utc(value).replace("Z", "+00:00")).astimezone(timezone.utc)


def _ts(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _deadline(item: dict) -> str | None:
    if item.get("status") != "leased" or not item.get("leased_at"):
        return None
    return _ts(_dt(item["leased_at"]) + timedelta(seconds=int(item.get("lease_seconds", 0))))


def _public(item: dict) -> dict:
    record = dict(item)
    record["lease_deadline"] = _deadline(item)
    return record

def enqueue(store, item: dict) -> dict:
    """Add a queue item and return its public record."""
    data = state_of(store)
    record = dict(item)
    record.setdefault("id", next_id(store, "item"))
    record.setdefault("status", "queued")
    record.setdefault("queue", "default")
    record["created_at"] = utc(record.get("created_at") or record.get("visible_at") or record.get("now") or "")
    record["visible_at"] = utc(record.get("visible_at") or record["created_at"])
    record.pop("now", None)
    record.setdefault("worker_id", None)
    record.setdefault("leased_at", None)
    record.setdefault("lease_seconds", None)
    record.setdefault("acked_at", None)
    record.setdefault("cancelled_at", None)
    record.setdefault("timed_out_at", None)
    data["queue"].append(record)
    save_if_possible(store)
    return _public(record)


def claim(store, queue: str, worker_id: str, now: str, lease_seconds: int) -> dict | None:
    """Claim the next visible item for a worker."""
    data = state_of(store)
    now = utc(now)
    if lease_seconds <= 0:
        raise FlowLedgerError("invalid_lease", "lease_seconds must be positive")
    candidates = [
        item
        for item in data["queue"]
        if item.get("queue") == queue and item.get("status") == "queued" and utc(item.get("visible_at", item.get("created_at"))) <= now
    ]
    candidates.sort(key=lambda item: (item.get("visible_at", ""), item.get("created_at", ""), item.get("id", "")))
    if not candidates:
        return None
    item = candidates[0]
    item["status"] = "leased"
    item["worker_id"] = worker_id
    item["leased_at"] = now
    item["lease_seconds"] = lease_seconds
    save_if_possible(store)
    return _public(item)


def ack(store, item_id: str, worker_id: str, now: str) -> dict:
    """Acknowledge a leased item by its owning worker."""
    data = state_of(store)
    for item in data["queue"]:
        if item.get("id") == item_id:
            if item.get("status") != "leased":
                raise FlowLedgerError("invalid_queue_state", "queue item is not leased", {"item_id": item_id, "status": item.get("status")})
            if item.get("worker_id") != worker_id:
                raise FlowLedgerError("lease_owner_mismatch", "queue item is leased by another worker", {"item_id": item_id})
            item["status"] = "acked"
            item["acked_at"] = utc(now)
            save_if_possible(store)
            return _public(item)
    raise FlowLedgerError("not_found", "queue item not found", {"item_id": item_id})


def expire_leases(store, now: str) -> list[dict]:
    """Mark expired leases and return public timeout records."""
    data = state_of(store)
    now = utc(now)
    expired: list[dict] = []
    for item in data["queue"]:
        deadline = _deadline(item)
        if deadline and deadline <= now:
            item["status"] = "timed_out"
            item["timed_out_at"] = now
            expired.append(_public(item))
    if expired:
        save_if_possible(store)
    return expired


def queue_report(store) -> dict:
    """Return the public queue projection."""
    data = state_of(store)
    items = sorted((_public(item) for item in data["queue"]), key=lambda item: (item.get("created_at", ""), item.get("id", "")))
    counts: dict[str, int] = {}
    by_queue: dict[str, dict[str, int]] = {}
    for item in items:
        status = item.get("status", "unknown")
        name = item.get("queue", "default")
        counts[status] = counts.get(status, 0) + 1
        by_queue.setdefault(name, {})
        by_queue[name][status] = by_queue[name].get(status, 0) + 1
    return {"items": items, "counts": counts, "by_queue": by_queue}
