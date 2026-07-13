from __future__ import annotations

from .models import QueueItem


class InMemoryBroker:
    """Public broker abstraction for deterministic queue and redelivery behavior."""

    def __init__(self, items: list[QueueItem] | None = None) -> None:
        self._ready: list[QueueItem] = []
        self._in_flight: dict[str, dict] = {}
        for item in items or []:
            self.enqueue(item)

    def enqueue(self, item: QueueItem) -> None:
        self._ready = [queued for queued in self._ready if queued.task_id != item.task_id]
        self._ready.append(item)
        self._ready.sort(key=lambda queued: (queued.available_at, queued.job_id, queued.task_id, queued.attempt))

    def claim(self, *, now: int, worker_id: str | None = None) -> QueueItem | None:
        for idx, item in enumerate(self._ready):
            if item.available_at <= now:
                claimed = self._ready.pop(idx)
                self._in_flight[claimed.task_id] = {"item": claimed, "worker_id": worker_id or "worker-1", "claimed_at": now}
                return claimed
        return None

    def ack(self, task_id: str) -> None:
        self._in_flight.pop(task_id, None)

    def requeue(self, item: QueueItem) -> None:
        self.ack(item.task_id)
        self.enqueue(item)

    def snapshot(self) -> dict:
        return {
            "ready": [
                {"task_id": item.task_id, "job_id": item.job_id, "available_at": item.available_at, "attempt": item.attempt}
                for item in self._ready
            ],
            "in_flight": [
                {
                    "task_id": item["item"].task_id,
                    "job_id": item["item"].job_id,
                    "available_at": item["item"].available_at,
                    "attempt": item["item"].attempt,
                    "worker_id": item["worker_id"],
                    "claimed_at": item["claimed_at"],
                }
                for item in self._in_flight.values()
            ],
            "ready_count": len(self._ready),
            "in_flight_count": len(self._in_flight),
        }
