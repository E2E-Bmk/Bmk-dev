"""Public records and errors for FlowLedger."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


class FlowLedgerError(Exception):
    """Public structured error."""

    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {"error": self.code, "message": self.message, "details": self.details}


@dataclass
class StepSpec:
    id: str
    action: str
    depends: list[str] = field(default_factory=list)
    with_args: dict[str, Any] = field(default_factory=dict)
    retry: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowSpec:
    name: str
    mode: str = "graph"
    params: dict[str, Any] = field(default_factory=dict)
    queue: str = "default"
    max_active_runs: int = 1
    schedule: dict[str, Any] | None = None
    steps: list[StepSpec] = field(default_factory=list)


@dataclass
class RunRecord:
    id: str
    workflow: str
    status: str
    created_at: str
    updated_at: str


@dataclass
class StepAttempt:
    run_id: str
    step_id: str
    attempt: int
    status: str
    started_at: str | None = None
    finished_at: str | None = None
    output: Any = None
    error: dict[str, Any] | None = None


def utc(value: str) -> str:
    """Validate and normalize a public UTC timestamp string."""
    if not isinstance(value, str) or not value.strip():
        raise FlowLedgerError("invalid_time", "timestamp must be a non-empty string")
    raw = value.strip()
    candidate = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise FlowLedgerError("invalid_time", f"invalid UTC timestamp: {value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    parsed = parsed.astimezone(timezone.utc)
    if parsed.microsecond:
        text = parsed.isoformat(timespec="microseconds")
    else:
        text = parsed.isoformat(timespec="seconds")
    return text.replace("+00:00", "Z")
