from __future__ import annotations

from .completion import CompletionWatcher
from .models import Job, QueueReport, Schedule
from .scheduler import Scheduler
from .store import FileStore, InMemoryStore, Store
from .worker import Worker


class QueueLedger:
    def __init__(self, store: Store) -> None:
        self.store = store

    @classmethod
    def in_memory(cls) -> "QueueLedger":
        return cls(InMemoryStore())

    @classmethod
    def file(cls, root: str) -> "QueueLedger":
        return cls(FileStore(root))

    def enqueue(self, entrypoint: str, payload: bytes, *, now: float, priority: int = 0, execute_after: float | None = None) -> Job:
        raise NotImplementedError

    def scheduler(self) -> Scheduler:
        return Scheduler(self.store)

    def worker(self, worker_id: str) -> Worker:
        return Worker(self.store, worker_id=worker_id)

    def completion_watcher(self) -> CompletionWatcher:
        return CompletionWatcher(self.store)

    def queue_report(self) -> QueueReport:
        return self.store.queue_report()

    def get_job(self, job_id: str) -> Job | None:
        return self.store.get_job(job_id)

    def list_schedules(self) -> list[Schedule]:
        return self.store.list_schedules()
