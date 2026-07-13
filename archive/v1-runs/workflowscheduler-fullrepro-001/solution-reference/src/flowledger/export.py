"""Export/import public snapshots."""

from __future__ import annotations

from copy import deepcopy

from .models import FlowLedgerError
from .store import empty_state, save_if_possible, state_of

def export_snapshot(store) -> dict:
    """Return a JSON-compatible public snapshot."""
    data = state_of(store)
    return {"format": "flowledger.snapshot.v1", "state": deepcopy(data)}


def import_snapshot(store, snapshot: dict) -> dict:
    """Import into an empty ledger atomically."""
    if not isinstance(snapshot, dict) or snapshot.get("format") != "flowledger.snapshot.v1" or not isinstance(snapshot.get("state"), dict):
        raise FlowLedgerError("invalid_snapshot", "snapshot must be a FlowLedger v1 export")
    data = state_of(store)
    empty = empty_state()
    non_empty = any(data.get(key) != empty.get(key) for key in ["specs", "schedules", "runs", "steps", "attempts", "queue", "logs", "events", "recovery_markers"])
    if non_empty:
        raise FlowLedgerError("import_not_empty", "import requires an empty ledger")
    data.clear()
    data.update(deepcopy(snapshot["state"]))
    save_if_possible(store)
    return {"imported": True, "runs": len(data.get("runs", {})), "specs": len(data.get("specs", {}))}
