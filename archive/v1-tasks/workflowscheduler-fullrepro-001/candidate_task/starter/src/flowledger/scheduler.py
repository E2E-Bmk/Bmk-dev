"""Virtual-clock scheduling and overlap decisions."""

from __future__ import annotations

from .models import WorkflowSpec


def due_slots(spec: WorkflowSpec, last_slot: str | None, now: str) -> list[str]:
    """Return schedule slots due at `now` under the public catch-up policy."""
    raise NotImplementedError


def apply_overlap(policy: str, active_run_ids: list[str], queued_run_ids: list[str], new_slots: list[str]) -> dict:
    """Return enqueue/cancel decisions for the public overlap policy."""
    raise NotImplementedError


def next_run(spec: WorkflowSpec, last_slot: str | None, now: str) -> dict:
    """Return the public next-run projection."""
    raise NotImplementedError
