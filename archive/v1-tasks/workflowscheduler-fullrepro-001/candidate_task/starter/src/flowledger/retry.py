"""Retry policy primitives."""

from __future__ import annotations


def retry_decision(policy: dict, failure_count: int, failed_at: str) -> dict:
    """Return retry_wait or exhausted decision for a failed step."""
    raise NotImplementedError


def due_retries(store, now: str) -> list[dict]:
    """Return retry records due at `now`."""
    raise NotImplementedError
