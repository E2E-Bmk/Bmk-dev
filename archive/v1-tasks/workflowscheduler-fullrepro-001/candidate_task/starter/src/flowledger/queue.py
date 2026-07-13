"""Durable queue and lease primitives."""

from __future__ import annotations


def enqueue(store, item: dict) -> dict:
    """Add a queue item and return its public record."""
    raise NotImplementedError


def claim(store, queue: str, worker_id: str, now: str, lease_seconds: int) -> dict | None:
    """Claim the next visible item for a worker."""
    raise NotImplementedError


def ack(store, item_id: str, worker_id: str, now: str) -> dict:
    """Acknowledge a leased item by its owning worker."""
    raise NotImplementedError


def expire_leases(store, now: str) -> list[dict]:
    """Mark expired leases and return public timeout records."""
    raise NotImplementedError


def queue_report(store) -> dict:
    """Return the public queue projection."""
    raise NotImplementedError
