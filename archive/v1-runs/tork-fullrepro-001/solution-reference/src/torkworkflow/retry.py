from __future__ import annotations

from .models import QueueItem, TaskRecord


def should_retry(task: TaskRecord, *, max_attempts: int) -> bool:
    return len(task.attempts) <= max_attempts


def next_retry_item(task: TaskRecord, *, now: int, delay_seconds: int) -> QueueItem:
    return QueueItem(task_id=task.id, job_id=task.job_id, available_at=now + delay_seconds, attempt=len(task.attempts) + 1)
