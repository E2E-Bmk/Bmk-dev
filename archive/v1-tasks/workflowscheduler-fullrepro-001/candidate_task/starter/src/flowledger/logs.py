"""Public log and event records."""

from __future__ import annotations


def append_event(store, event: dict) -> dict:
    """Append and return a public event record."""
    raise NotImplementedError


def append_log(store, log: dict) -> dict:
    """Append and return a public log record."""
    raise NotImplementedError


def event_stream(store, run_id: str | None = None) -> list[dict]:
    """Return deterministic public events."""
    raise NotImplementedError


def log_stream(store, run_id: str | None = None) -> list[dict]:
    """Return deterministic public logs."""
    raise NotImplementedError
