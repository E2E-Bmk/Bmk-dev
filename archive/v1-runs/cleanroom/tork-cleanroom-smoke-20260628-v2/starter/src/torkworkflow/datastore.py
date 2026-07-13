from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .models import JobRecord, QueueItem, ScheduleRecord, TaskRecord


class WorkflowStore:
    """Public persistence boundary used by API, worker, scheduler, and recovery."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else None

    def create_job(self, job: JobRecord, tasks: Iterable[TaskRecord]) -> None:
        raise NotImplementedError

    def get_job(self, job_id: str) -> JobRecord:
        raise NotImplementedError

    def list_jobs(self) -> list[JobRecord]:
        raise NotImplementedError

    def save_job(self, job: JobRecord) -> None:
        raise NotImplementedError

    def get_task(self, task_id: str) -> TaskRecord:
        raise NotImplementedError

    def list_tasks(self, job_id: str | None = None) -> list[TaskRecord]:
        raise NotImplementedError

    def save_task(self, task: TaskRecord) -> None:
        raise NotImplementedError

    def append_queue(self, item: QueueItem) -> None:
        raise NotImplementedError

    def list_queue(self) -> list[QueueItem]:
        raise NotImplementedError

    def remove_queue_item(self, task_id: str) -> None:
        raise NotImplementedError

    def save_schedule(self, schedule: ScheduleRecord) -> None:
        raise NotImplementedError

    def list_schedules(self) -> list[ScheduleRecord]:
        raise NotImplementedError

    def reopen(self) -> "WorkflowStore":
        raise NotImplementedError
