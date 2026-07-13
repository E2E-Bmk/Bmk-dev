from __future__ import annotations

from .broker import InMemoryBroker
from .clock import FakeClock
from .datastore import WorkflowStore
from .logs import LogStore
from .runtime import LocalRuntime


class Worker:
    def __init__(self, store: WorkflowStore, broker: InMemoryBroker, runtime: LocalRuntime, logs: LogStore, clock: FakeClock) -> None:
        self.store = store
        self.broker = broker
        self.runtime = runtime
        self.logs = logs
        self.clock = clock

    def run_one(self, *, worker_id: str = "worker-1") -> dict | None:
        raise NotImplementedError

    def run_until_idle(self, *, worker_id: str = "worker-1", limit: int = 100) -> list[dict]:
        raise NotImplementedError
