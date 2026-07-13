from __future__ import annotations


def validate_export(data: dict[str, object]) -> None:
    """Validate public export/import payload shape."""
    raise NotImplementedError


def canonical_export(data: dict[str, object]) -> dict[str, object]:
    """Return deterministic public export payload."""
    raise NotImplementedError
