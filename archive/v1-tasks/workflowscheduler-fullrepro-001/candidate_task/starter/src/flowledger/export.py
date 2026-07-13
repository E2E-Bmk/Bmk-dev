"""Export/import public snapshots."""

from __future__ import annotations


def export_snapshot(store) -> dict:
    """Return a JSON-compatible public snapshot."""
    raise NotImplementedError


def import_snapshot(store, snapshot: dict) -> dict:
    """Import into an empty ledger atomically."""
    raise NotImplementedError
