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

TERMINAL_STATES = {"completed", "cancelled", "discarded"}
CLAIMABLE_STATES = {"available", "scheduled", "retryable"}
UNIQUE_ACTIVE_STATES = {"available", "scheduled", "executing", "retryable"}


class JobLedgerError(Exception):
    """Public exception for invalid JobLedger operations."""


def to_epoch(value: str | int | None) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        raise JobLedgerError("time must be an integer epoch second")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value)
    raise JobLedgerError("time must be an integer epoch second")


def validate_name(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value or any(ch.isspace() for ch in value):
        raise JobLedgerError(f"invalid {field_name}")
    return value


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

    @classmethod
    def from_value(cls, value: "UniquePolicy | dict[str, Any] | None") -> "UniquePolicy | None":
        if value is None:
            return None
        if isinstance(value, UniquePolicy):
            return value
        if not isinstance(value, dict):
            raise JobLedgerError("unique must be a policy object")
        fields = tuple(value.get("fields", ("kind", "queue", "args")))
        allowed_fields = {"kind", "queue", "args"}
        if not fields or any(field not in allowed_fields for field in fields):
            raise JobLedgerError("invalid unique fields")
        period = int(value.get("period_seconds", 3600))
        if period <= 0:
            raise JobLedgerError("invalid unique period")
        states = tuple(value.get("states", ("available", "scheduled", "executing", "retryable")))
        if any(state not in UNIQUE_ACTIVE_STATES for state in states):
            raise JobLedgerError("invalid unique states")
        conflict = value.get("on_conflict", "reject")
        if conflict not in {"reject", "replace"}:
            raise JobLedgerError("invalid unique conflict policy")
        return cls(fields=fields, period_seconds=period, states=states, on_conflict=conflict)  # type: ignore[arg-type]

    def to_dict(self) -> dict[str, Any]:
        return {
            "fields": list(self.fields),
            "period_seconds": self.period_seconds,
            "states": list(self.states),
            "on_conflict": self.on_conflict,
        }


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

    def __post_init__(self) -> None:
        validate_name(self.queue, "queue")
        validate_name(self.kind, "kind")
        if not isinstance(self.args, dict):
            raise JobLedgerError("args must be an object")
        if not isinstance(self.priority, int):
            raise JobLedgerError("priority must be an integer")
        if not isinstance(self.max_attempts, int) or self.max_attempts < 1:
            raise JobLedgerError("max_attempts must be positive")
        if self.state not in {
            "available",
            "scheduled",
            "executing",
            "retryable",
            "completed",
            "cancelled",
            "discarded",
        }:
            raise JobLedgerError("invalid state")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "queue": self.queue,
            "kind": self.kind,
            "args": self.args,
            "state": self.state,
            "priority": self.priority,
            "max_attempts": self.max_attempts,
            "attempt": self.attempt,
            "scheduled_at": self.scheduled_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "unique": self.unique.to_dict() if self.unique else None,
            "last_error": self.last_error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JobRecord":
        data = dict(data)
        data["unique"] = UniquePolicy.from_value(data.get("unique"))
        return cls(**data)


@dataclass(frozen=True)
class AttemptRecord:
    job_id: str
    attempt: int
    at: str
    error: str

    def to_dict(self) -> dict[str, Any]:
        return {"job_id": self.job_id, "attempt": self.attempt, "at": self.at, "error": self.error}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AttemptRecord":
        return cls(job_id=str(data["job_id"]), attempt=int(data["attempt"]), at=str(data["at"]), error=str(data["error"]))


@dataclass(frozen=True)
class EventRecord:
    seq: int
    at: str
    type: str
    job_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"seq": self.seq, "at": self.at, "type": self.type, "job_id": self.job_id, "data": self.data}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EventRecord":
        return cls(seq=int(data["seq"]), at=str(data["at"]), type=str(data["type"]), job_id=data.get("job_id"), data=dict(data.get("data") or {}))


@dataclass(frozen=True)
class CronEntry:
    name: str
    every_seconds: int
    kind: str
    args: dict[str, Any] = field(default_factory=dict)
    queue: str = "default"
    unique: UniquePolicy | None = None
    last_slot: int | None = None

    def __post_init__(self) -> None:
        validate_name(self.name, "cron name")
        validate_name(self.kind, "kind")
        validate_name(self.queue, "queue")
        if self.every_seconds <= 0:
            raise JobLedgerError("every_seconds must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "every_seconds": self.every_seconds,
            "kind": self.kind,
            "args": self.args,
            "queue": self.queue,
            "unique": self.unique.to_dict() if self.unique else None,
            "last_slot": self.last_slot,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CronEntry":
        return cls(
            name=str(data["name"]),
            every_seconds=int(data["every_seconds"]),
            kind=str(data["kind"]),
            args=dict(data.get("args") or {}),
            queue=str(data.get("queue") or "default"),
            unique=UniquePolicy.from_value(data.get("unique")),
            last_slot=data.get("last_slot"),
        )


def transition_allowed(old: JobState, new: JobState) -> bool:
    allowed = {
        "available": {"executing", "cancelled"},
        "scheduled": {"executing", "cancelled"},
        "retryable": {"executing", "cancelled"},
        "executing": {"completed", "retryable", "discarded", "cancelled"},
        "completed": set(),
        "cancelled": set(),
        "discarded": set(),
    }
    return new in allowed[old]
