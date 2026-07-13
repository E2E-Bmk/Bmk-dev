from __future__ import annotations

from dataclasses import asdict, dataclass, field
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
    raw: dict[str, Any] = field(default_factory=dict)


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
    delay_seconds: int = 0
    retry_scheduled_at: int | None = None


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
    run: str | None = None
    var: str | None = None
    if_expr: str | None = None
    retry_limit: int = 0
    retry_delay_seconds: int = 0
    timeout_seconds: int | None = None
    depends_on: list[str] = field(default_factory=list)
    index: int = 0
    kind: str = "task"
    metadata: dict[str, Any] = field(default_factory=dict)


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


def to_dict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: to_dict(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [to_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: to_dict(item) for key, item in value.items()}
    return value


def retry_policy_from_dict(data: dict[str, Any] | None) -> RetryPolicy | None:
    if data is None:
        return None
    return RetryPolicy(limit=int(data.get("limit", 0)), delay_seconds=int(data.get("delay_seconds", data.get("delay", 0))))


def task_spec_from_dict(data: dict[str, Any]) -> TaskSpec:
    retry = data.get("retry")
    if isinstance(retry, int):
        retry_policy = RetryPolicy(limit=retry)
    elif isinstance(retry, dict):
        retry_policy = retry_policy_from_dict(retry)
    else:
        retry_policy = None
    return TaskSpec(
        name=str(data["name"]),
        run=data.get("run"),
        var=data.get("var"),
        if_expr=data.get("if_expr"),
        retry=retry_policy,
        timeout_seconds=data.get("timeout_seconds"),
        parallel=[task_spec_from_dict(item) for item in data.get("parallel", [])],
        each=data.get("each"),
        subjob=data.get("subjob"),
        pre=[task_spec_from_dict(item) for item in data.get("pre", [])],
        post=[task_spec_from_dict(item) for item in data.get("post", [])],
        raw=dict(data.get("raw", {})),
    )


def job_spec_from_dict(data: dict[str, Any]) -> JobSpec:
    return JobSpec(
        name=str(data["name"]),
        tasks=[task_spec_from_dict(item) for item in data.get("tasks", [])],
        inputs=dict(data.get("inputs", {})),
        secrets=dict(data.get("secrets", {})),
        output=data.get("output"),
        schedule=data.get("schedule"),
    )


def attempt_from_dict(data: dict[str, Any]) -> AttemptRecord:
    return AttemptRecord(**data)


def task_record_from_dict(data: dict[str, Any]) -> TaskRecord:
    data = dict(data)
    data["attempts"] = [attempt_from_dict(item) for item in data.get("attempts", [])]
    return TaskRecord(**data)


def job_record_from_dict(data: dict[str, Any]) -> JobRecord:
    return JobRecord(**data)


def schedule_from_dict(data: dict[str, Any]) -> ScheduleRecord:
    data = dict(data)
    data["spec"] = job_spec_from_dict(data["spec"])
    return ScheduleRecord(**data)


def queue_item_from_dict(data: dict[str, Any]) -> QueueItem:
    return QueueItem(**data)
