from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class JobStatus(StrEnum):
    QUEUED = "queued"
    PICKED = "picked"
    SUCCESSFUL = "successful"
    EXCEPTION = "exception"
    FAILED = "failed"
    CANCELED = "canceled"
    DELETED = "deleted"


@dataclass(frozen=True)
class Job:
    id: str
    entrypoint: str
    payload: bytes
    priority: int = 0
    status: JobStatus = JobStatus.QUEUED
    attempts: int = 0
    execute_after: float = 0.0
    heartbeat: float | None = None
    max_attempts: int = 3
    retry_delay: float = 1.0
    created_at: float = 0.0
    updated_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Schedule:
    id: str
    entrypoint: str
    every_seconds: int
    payload: bytes = b""
    last_run_at: float | None = None
    heartbeat: float | None = None
    enabled: bool = True


@dataclass(frozen=True)
class QueueReport:
    queued: int
    picked: int
    terminal: int
    by_entrypoint: dict[str, int]


@dataclass(frozen=True)
class CompletionEvent:
    job_id: str
    status: JobStatus
    observed_at: float
