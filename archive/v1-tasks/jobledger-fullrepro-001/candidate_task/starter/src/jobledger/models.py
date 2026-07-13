from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

JobState = Literal[
    "available",
    "scheduled",
    "executing",
    "retryable",
    "completed",
    "cancelled",
    "discarded",
]


class JobLedgerError(Exception):
    """Public exception for invalid JobLedger operations."""


@dataclass(frozen=True)
class UniquePolicy:
    fields: tuple[str, ...] = ("kind", "queue", "args")
    period_seconds: int = 3600
    states: tuple[JobState, ...] = (
        "available",
        "scheduled",
        "executing",
        "retryable",
    )
    on_conflict: Literal["reject", "replace"] = "reject"


@dataclass
class JobRecord:
    id: str
    queue: str
    kind: str
    args: dict[str, Any] = field(default_factory=dict)
    state: JobState = "available"
    priority: int = 0
    max_attempts: int = 3
    attempt: int = 0
    scheduled_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    unique: UniquePolicy | None = None
    last_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        raise NotImplementedError


@dataclass(frozen=True)
class AttemptRecord:
    job_id: str
    attempt: int
    at: str
    error: str


@dataclass(frozen=True)
class EventRecord:
    seq: int
    at: str
    type: str
    job_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CronEntry:
    name: str
    every_seconds: int
    kind: str
    args: dict[str, Any] = field(default_factory=dict)
    queue: str = "default"
    unique: UniquePolicy | None = None
