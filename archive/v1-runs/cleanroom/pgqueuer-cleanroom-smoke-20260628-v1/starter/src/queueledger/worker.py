from __future__ import annotations

from .models import Job
from .store import Store


class Worker:
    def __init__(self, store: Store, *, worker_id: str) -> None:
        self.store = store
        self.worker_id = worker_id

    def claim(self, entrypoints: list[str], *, now: float, limit: int = 1) -> list[Job]:
        raise NotImplementedError

    def heartbeat(self, job_ids: list[str], *, now: float) -> None:
        raise NotImplementedError

    def complete(self, job_id: str, *, now: float) -> Job:
        raise NotImplementedError

    def fail(self, job_id: str, error: str, *, now: float) -> Job:
        raise NotImplementedError

    def cancel(self, job_id: str, *, now: float) -> Job:
        raise NotImplementedError
