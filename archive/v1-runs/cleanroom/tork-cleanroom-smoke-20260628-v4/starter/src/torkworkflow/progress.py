from __future__ import annotations

from .models import JobRecord, TaskRecord


def task_progress(task: TaskRecord) -> float:
    raise NotImplementedError


def job_progress(job: JobRecord, tasks: list[TaskRecord]) -> float:
    raise NotImplementedError
