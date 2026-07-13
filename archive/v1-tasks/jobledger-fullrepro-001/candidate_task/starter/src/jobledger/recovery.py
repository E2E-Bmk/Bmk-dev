from __future__ import annotations


def classify_marker(marker: dict[str, object]) -> str:
    """Return rollback, roll-forward, or clean for a recovery marker."""
    raise NotImplementedError


def recovery_report(markers: list[dict[str, object]]) -> dict[str, object]:
    """Return a public recovery report."""
    raise NotImplementedError
