from __future__ import annotations

from .models import QueueItem


class InMemoryBroker:
    """Public broker abstraction for deterministic queue and redelivery behavior."""

    def enqueue(self, item: QueueItem) -> None:
        raise NotImplementedError

    def claim(self, *, now: int, worker_id: str | None = None) -> QueueItem | None:
        raise NotImplementedError

    def ack(self, task_id: str) -> None:
        raise NotImplementedError

    def requeue(self, item: QueueItem) -> None:
        raise NotImplementedError

    def snapshot(self) -> dict:
        raise NotImplementedError
