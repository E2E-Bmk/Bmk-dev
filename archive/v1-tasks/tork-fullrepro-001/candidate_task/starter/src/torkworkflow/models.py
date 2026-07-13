from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

JobState = Literal["QUEUED", "RUNNING", "COMPLETED", "FAILED", "CANCELED"]
TaskState = Literal["PENDING", "QUEUED", "RUNNING", "COMPLETED", "FAILED", "SKIPPED", "CANCELED"]


@dataclass
class RetryPolicy:
    limit: int = 0
    delay_seconds: int = 0


@dataclass
class TaskSpec:
    name: str
    run: str | None = None
    var: str | None = None
    if_expr: str | None = None
    retry: RetryPolicy | None = None
    timeout_seconds: int | None = None
    parallel: list["TaskSpec"] = field(default_factory=list)
    each: dict[str, Any] | None = None
    subjob: dict[str, Any] | None = None
    pre: list["TaskSpec"] = field(default_factory=list)
    post: list["TaskSpec"] = field(default_factory=list)


@dataclass
class JobSpec:
    name: str
    tasks: list[TaskSpec]
    inputs: dict[str, Any] = field(default_factory=dict)
    secrets: dict[str, str] = field(default_factory=dict)
    output: str | None = None
    schedule: str | None = None


@dataclass
class AttemptRecord:
    attempt: int
    state: TaskState
    started_at: int | None = None
    finished_at: int | None = None
    output: str | None = None
    error: str | None = None


@dataclass
class TaskRecord:
    id: str
    job_id: str
    name: str
    state: TaskState = "PENDING"
    parent_id: str | None = None
    attempts: list[AttemptRecord] = field(default_factory=list)
    children: list[str] = field(default_factory=list)
    output: str | None = None
    progress: float = 0.0


@dataclass
class JobRecord:
    id: str
    name: str
    state: JobState = "QUEUED"
    created_at: int = 0
    updated_at: int = 0
    output: str | None = None
    task_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScheduleRecord:
    id: str
    name: str
    spec: JobSpec
    interval_seconds: int
    next_due_at: int
    last_run_at: int | None = None
    paused: bool = False


@dataclass
class QueueItem:
    task_id: str
    job_id: str
    available_at: int = 0
    attempt: int = 1
