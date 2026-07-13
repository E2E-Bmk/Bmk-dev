from __future__ import annotations

from dataclasses import replace

from .completion import CompletionWatcher
from .entrypoints import EntrypointRegistry, Handler
from .metrics import metrics_snapshot
from .models import Job, QueueReport, Schedule
from .recovery import RecoveryReport, recover_stale_jobs
from .scheduler import Scheduler
from .store import FileStore, InMemoryStore, Store
from .worker import Worker


class QueueLedger:
    def __init__(self, store: Store) -> None:
        self.store = store
        self.entrypoints = EntrypointRegistry()
        self._counter = len(store.list_jobs())

    @classmethod
    def in_memory(cls) -> "QueueLedger":
        return cls(InMemoryStore())

    @classmethod
    def file(cls, root: str) -> "QueueLedger":
        return cls(FileStore(root))

    def enqueue(self, entrypoint: str, payload: bytes, *, now: float, priority: int = 0, execute_after: float | None = None, max_attempts: int = 3, retry_delay: float = 1.0) -> Job:
        self._counter += 1
        job = Job(
            id=f"job-{self._counter}",
            entrypoint=entrypoint,
            payload=payload,
            priority=priority,
            execute_after=now if execute_after is None else execute_after,
            max_attempts=max_attempts,
            retry_delay=retry_delay,
            created_at=now,
            updated_at=now,
        )
        return self.store.put_job(job)

    def transaction(self) -> "QueueTransaction":
        return QueueTransaction(self)

    def register_entrypoint(self, name: str, handler: Handler, *, concurrency_limit: int = 0) -> None:
        self.entrypoints.register(name, handler, concurrency_limit=concurrency_limit)

    def register_schedule(self, schedule: Schedule) -> Schedule:
        return self.scheduler().register(schedule)

    def tick(self, now: float) -> list[Job]:
        return self.scheduler().tick(now)

    def list_jobs(self) -> list[Job]:
        return self.store.list_jobs()

    def scheduler(self) -> Scheduler:
        return Scheduler(self.store)

    def worker(self, worker_id: str, *, global_concurrency_limit: int = 0) -> Worker:
        return Worker(self.store, worker_id=worker_id, registry=self.entrypoints, global_concurrency_limit=global_concurrency_limit)

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
    def __init__(self, ledger: QueueLedger) -> None:
        self.ledger = ledger
        self._jobs = ledger.store.list_jobs()
        self._pending: list[Job] = []
        self._closed = False

    def enqueue(self, entrypoint: str, payload: bytes, *, now: float, priority: int = 0, execute_after: float | None = None, max_attempts: int = 3, retry_delay: float = 1.0) -> Job:
        if self._closed:
            raise RuntimeError("transaction is closed")
        self.ledger._counter += 1
        job = Job(
            id=f"job-{self.ledger._counter}",
            entrypoint=entrypoint,
            payload=payload,
            priority=priority,
            execute_after=now if execute_after is None else execute_after,
            max_attempts=max_attempts,
            retry_delay=retry_delay,
            created_at=now,
            updated_at=now,
        )
        self._pending.append(job)
        return job

    def commit(self) -> None:
        if self._closed:
            return
        for job in self._pending:
            self.ledger.store.put_job(job)
        self._closed = True

    def rollback(self) -> None:
        if self._closed:
            return
        self.ledger.store.replace_jobs(self._jobs)
        self._closed = True
