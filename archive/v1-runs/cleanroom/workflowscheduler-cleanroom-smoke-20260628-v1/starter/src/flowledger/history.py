"""Public history and status projections."""

from __future__ import annotations


def status_report(store, workflow: str | None = None, run_id: str | None = None) -> dict:
    """Return status projection."""
    raise NotImplementedError


def history_report(store, workflow: str | None = None) -> dict:
    """Return run and attempt history."""
    raise NotImplementedError


def next_runs_report(store, now: str) -> dict:
    """Return next-run projection for known schedules."""
    raise NotImplementedError
