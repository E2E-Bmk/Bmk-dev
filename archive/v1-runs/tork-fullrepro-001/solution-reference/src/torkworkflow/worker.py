from __future__ import annotations

from .broker import InMemoryBroker
from .clock import FakeClock
from .datastore import WorkflowStore
from .logs import LogStore
from .models import AttemptRecord, QueueItem
from .retry import next_retry_item, should_retry
from .runtime import LocalRuntime


class Worker:
    def __init__(self, store: WorkflowStore, broker: InMemoryBroker, runtime: LocalRuntime, logs: LogStore, clock: FakeClock) -> None:
        self.store = store
        self.broker = broker
        self.runtime = runtime
        self.logs = logs
        self.clock = clock

    def run_one(self, *, worker_id: str = "worker-1") -> dict | None:
        item = self.broker.claim(now=self.clock.now(), worker_id=worker_id)
        if item is None:
            return None
        self.store.remove_queue_item(item.task_id)
        task = self.store.get_task(item.task_id)
        job = self.store.get_job(item.job_id)
        if job.state == "CANCELED" or task.state in {"COMPLETED", "FAILED", "CANCELED", "SKIPPED"}:
            self.broker.ack(item.task_id)
            return {"task_id": item.task_id, "job_id": item.job_id, "state": task.state, "ignored": True}

        now = self.clock.now()
        task.state = "RUNNING"
        task.progress = max(task.progress, 0.01)
        job.state = "RUNNING"
        job.updated_at = now
        attempt = AttemptRecord(attempt=item.attempt, state="RUNNING", started_at=now)
        task.attempts.append(attempt)
        self.store.save_task(task)
        self.store.save_job(job)

        context = {
            "inputs": job.metadata.get("inputs", {}),
            "outputs": job.metadata.get("outputs", {}),
            "vars": job.metadata.get("outputs", {}),
            "item": task.metadata.get("item", {}),
        }
        result = self.runtime.run(task, context)
        finished = self.clock.now()
        if task.timeout_seconds is not None and result.duration_seconds > task.timeout_seconds:
            result.exit_code = 1
            result.stderr = f"timeout after {task.timeout_seconds} seconds"

        if result.stdout:
            self.logs.append(task.id, result.stdout, stream="stdout", ts=finished)
        if result.stderr:
            self.logs.append(task.id, result.stderr, stream="stderr", ts=finished)

        attempt.finished_at = finished
        if result.exit_code == 0:
            task.state = "COMPLETED"
            task.output = result.stdout
            task.progress = float(result.progress) / 100.0 if result.progress is not None else 1.0
            attempt.state = "COMPLETED"
            attempt.output = task.output
        else:
            attempt.error = result.stderr
            if should_retry(task, max_attempts=task.retry_limit):
                retry_item = next_retry_item(task, now=finished, delay_seconds=task.retry_delay_seconds)
                task.state = "QUEUED"
                task.progress = max(task.progress, 0.01)
                attempt.state = "FAILED"
                attempt.delay_seconds = task.retry_delay_seconds
                attempt.retry_scheduled_at = retry_item.available_at
                self.store.append_queue(retry_item)
                self.broker.enqueue(retry_item)
            else:
                task.state = "FAILED"
                attempt.state = "FAILED"
                task.progress = max(task.progress, 0.01)

        job.updated_at = self.clock.now()
        self.store.save_task(task)
        self.store.save_job(job)
        self.store.save_clock(self.clock.now())
        self.broker.ack(item.task_id)
        return {"task_id": task.id, "job_id": job.id, "state": task.state, "attempt": item.attempt}

    def run_until_idle(self, *, worker_id: str = "worker-1", limit: int = 100) -> list[dict]:
        events: list[dict] = []
        for _ in range(limit):
            event = self.run_one(worker_id=worker_id)
            if event is None:
                queue = self.store.list_queue()
                future = [item.available_at for item in queue if item.available_at > self.clock.now()]
                if not future:
                    break
                self.clock.advance(min(future) - self.clock.now())
                self.store.save_clock(self.clock.now())
                continue
            events.append(event)
        return events
