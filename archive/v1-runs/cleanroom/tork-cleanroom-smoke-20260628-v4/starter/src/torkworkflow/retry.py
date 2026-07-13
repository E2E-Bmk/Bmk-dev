from __future__ import annotations

from .models import QueueItem, TaskRecord


def should_retry(task: TaskRecord, *, max_attempts: int) -> bool:
    raise NotImplementedError


def next_retry_item(task: TaskRecord, *, now: int, delay_seconds: int) -> QueueItem:
    raise NotImplementedError
