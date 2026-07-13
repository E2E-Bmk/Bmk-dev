from __future__ import annotations

from .models import JobRecord, TaskRecord


def task_progress(task: TaskRecord) -> float:
    if task.state in {"COMPLETED", "SKIPPED"}:
        return 1.0
    if task.state in {"FAILED", "CANCELED"}:
        return _ratio(task.progress)
    return _ratio(task.progress)


def job_progress(job: JobRecord, tasks: list[TaskRecord]) -> float:
    owned = [task for task in tasks if task.job_id == job.id]
    if not owned:
        return 0.0
    return round(sum(task_progress(task) for task in owned) / len(owned), 4)


def _ratio(value: float) -> float:
    value = float(value)
    if value > 1.0:
        value = value / 100.0
    return max(0.0, min(1.0, value))
