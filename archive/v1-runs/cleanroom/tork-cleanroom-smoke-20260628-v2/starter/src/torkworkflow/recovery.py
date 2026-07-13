from __future__ import annotations

from .datastore import WorkflowStore


def recover(store: WorkflowStore, *, now: int) -> dict:
    """Rebuild queue/projections from durable state and return a public report."""
    raise NotImplementedError
