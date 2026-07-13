"""Workflow spec loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import WorkflowSpec


def load_spec(data: dict[str, Any] | str | Path) -> WorkflowSpec:
    """Load and normalize a workflow spec from a mapping, JSON/YAML text, or path."""
    raise NotImplementedError


def validate_spec(spec: WorkflowSpec) -> None:
    """Validate a spec without writing durable state."""
    raise NotImplementedError


def spec_to_dict(spec: WorkflowSpec) -> dict[str, Any]:
    """Return a deterministic JSON-compatible public spec."""
    raise NotImplementedError
