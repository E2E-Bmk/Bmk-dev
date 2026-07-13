from __future__ import annotations

from .completion import CompletionWatcher
from .metrics import metrics_snapshot
from .models import Job, QueueReport, Schedule
from .recovery import RecoveryReport, recover_stale_jobs
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

    def enqueue(self, entrypoint: str, payload: bytes, *, now: float, priority: int = 0, execute_after: float | None = None, max_attempts: int = 3, retry_delay: float = 1.0) -> Job:
        raise NotImplementedError

    def transaction(self) -> "QueueTransaction":
        raise NotImplementedError

    def list_jobs(self) -> list[Job]:
        return self.store.list_jobs()

    def scheduler(self) -> Scheduler:
        return Scheduler(self.store)

    def worker(self, worker_id: str, *, global_concurrency_limit: int = 0) -> Worker:
        return Worker(self.store, worker_id=worker_id, registry=getattr(self, "entrypoints", None), global_concurrency_limit=global_concurrency_limit)

    def completion_watcher(self) -> CompletionWatcher:
        return CompletionWatcher(self.store)

    def queue_report(self) -> QueueReport:
        return self.store.queue_report()

    def metrics_snapshot(self) -> dict[str, int]:
        return metrics_snapshot(self.store)

    def recover(self, *, now: float, heartbeat_timeout: float) -> RecoveryReport:
        return recover_stale_jobs(self.store, now=now, heartbeat_timeout=heartbeat_timeout)

    def get_job(self, job_id: str) -> Job | None:
        return self.store.get_job(job_id)

    def list_schedules(self) -> list[Schedule]:
        return self.store.list_schedules()


class QueueTransaction:
    def enqueue(self, entrypoint: str, payload: bytes, *, now: float, priority: int = 0, execute_after: float | None = None, max_attempts: int = 3, retry_delay: float = 1.0) -> Job:
        raise NotImplementedError

    def commit(self) -> None:
        raise NotImplementedError

    def rollback(self) -> None:
        raise NotImplementedError
