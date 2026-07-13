from __future__ import annotations

from pathlib import Path
from typing import Any

from .broker import InMemoryBroker
from .clock import FakeClock
from .datastore import WorkflowStore
from .logs import LogStore
from .models import JobSpec, QueueItem, TaskRecord, job_spec_from_dict, to_dict
from .parser import normalize_job_spec, parse_job_spec
from .planner import build_records, rollup_job_state, runnable_tasks
from .progress import job_progress, task_progress
from .recovery import recover as recover_store
from .runtime import LocalRuntime
from .scheduler import Scheduler
from .worker import Worker


class WorkflowEngine:
    """Main public API used by hidden integration and system tests."""

    def __init__(self, store_path: str | Path | None = None, *, clock: FakeClock | None = None) -> None:
        self.store = WorkflowStore(store_path)
        self.clock = clock or FakeClock(self.store.clock())
        self.store.save_clock(self.clock.now())
        self.broker = InMemoryBroker(self.store.list_queue())
        self.logs = LogStore(self.store)
        self.runtime = LocalRuntime(self.clock)
        self.worker = Worker(self.store, self.broker, self.runtime, self.logs, self.clock)
        self.scheduler = Scheduler(self.store)

    def submit(self, spec: JobSpec | dict | str, *, fmt: str | None = None) -> dict:
        job_spec = self._coerce_spec(spec, fmt=fmt)
        job_id = self._next_job_id()
        job, tasks = build_records(job_spec, job_id=job_id, now=self.clock.now())
        job.metadata["spec"] = to_dict(job_spec)
        self.store.create_job(job, tasks)
        self._refresh_job(job_id)
        return self.get_job(job_id)

    def run_until_idle(self, *, limit: int = 100) -> list[dict]:
        events: list[dict] = []
        for _ in range(limit):
            for job in self.store.list_jobs():
                self._refresh_job(job.id)
            event = self.worker.run_one()
            if event is None:
                future = [item.available_at for item in self.store.list_queue() if item.available_at > self.clock.now()]
                if not future:
                    break
                self.clock.advance(min(future) - self.clock.now())
                self.store.save_clock(self.clock.now())
                continue
            events.append(event)
            self._refresh_job(event["job_id"])
        return events

    def get_job(self, job_id: str) -> dict:
        self._refresh_job(job_id)
        job = self.store.get_job(job_id)
        tasks = self.store.list_tasks(job_id)
        return self._job_view(job, tasks, detail=True)

    def list_jobs(self) -> list[dict]:
        return [self._job_view(job, self.store.list_tasks(job.id), detail=False) for job in sorted(self.store.list_jobs(), key=lambda item: item.created_at)]

    def get_task(self, task_id: str) -> dict:
        task = self.store.get_task(task_id)
        return self._task_view(task, self.store.list_tasks(task.job_id))

    def queue_status(self) -> dict:
        durable = [to_dict(item) for item in self.store.list_queue()]
        broker = self.broker.snapshot()
        return {
            "now": self.clock.now(),
            "durable": durable,
            "durable_count": len(durable),
            "queued": len(durable),
            "scheduled": len([item for item in durable if item.get("available_at", 0) > self.clock.now()]),
            "broker": broker,
            "ready_count": broker["ready_count"],
            "in_flight_count": broker["in_flight_count"],
        }

    def log_page(self, *, job_id: str | None = None, task_id: str | None = None, contains: str | None = None) -> list[dict]:
        logs = self.logs.page(task_id=task_id, contains=contains)
        if job_id is not None:
            task_ids = {task.id for task in self.store.list_tasks(job_id)}
            logs = [entry for entry in logs if entry["task_id"] in task_ids]
        return logs

    def progress(self, job_id: str) -> dict:
        job = self.store.get_job(job_id)
        tasks = self.store.list_tasks(job_id)
        return {
            "job_id": job_id,
            "state": job.state,
            "progress": job_progress(job, tasks),
            "percent": round(job_progress(job, tasks) * 100),
            "tasks": {task.id: {"name": task.name, "state": task.state, "progress": task_progress(task), "percent": round(task_progress(task) * 100)} for task in tasks},
        }

    def cancel(self, job_id: str) -> dict:
        job = self.store.get_job(job_id)
        if job.state in {"COMPLETED", "FAILED", "CANCELED"}:
            return {"job_id": job_id, "state": job.state, "changed": False}
        job.state = "CANCELED"
        job.updated_at = self.clock.now()
        for task in self.store.list_tasks(job_id):
            if task.state in {"PENDING", "QUEUED", "RUNNING"}:
                task.state = "CANCELED"
                self.store.remove_queue_item(task.id)
                self.store.save_task(task)
        self.store.save_job(job)
        self.broker = InMemoryBroker(self.store.list_queue())
        self.worker.broker = self.broker
        return {"job_id": job_id, "state": "CANCELED", "changed": True}

    def restart(self, job_id: str) -> dict:
        job = self.store.get_job(job_id)
        spec_data = job.metadata.get("spec")
        if not spec_data:
            raise ValueError("job was not created with a restartable spec")
        restarted = self.submit(job_spec_from_dict(spec_data))
        restarted_job = self.store.get_job(restarted["id"])
        restarted_job.metadata["restarted_from"] = job_id
        self.store.save_job(restarted_job)
        return {"id": restarted["id"], "old_job_id": job_id, "new_job_id": restarted["id"], "state": restarted["state"]}

    def register_schedule(self, name: str, spec: JobSpec | dict | str, *, interval_seconds: int, fmt: str | None = None) -> dict:
        schedule = self.scheduler.register(name, self._coerce_spec(spec, fmt=fmt), interval_seconds=interval_seconds, now=self.clock.now())
        return self._schedule_view(schedule)

    def tick(self, *, seconds: int = 0) -> list[dict]:
        self.clock.advance(seconds)
        self.store.save_clock(self.clock.now())
        runs = []
        for schedule in self.scheduler.due(now=self.clock.now()):
            self.scheduler.mark_run(schedule.id, now=self.clock.now())
            view = self.submit(schedule.spec)
            job = self.store.get_job(view["id"])
            job.metadata["schedule_id"] = schedule.id
            job.metadata["scheduled_at"] = self.clock.now()
            self.store.save_job(job)
            runs.append(self.get_job(job.id))
        return runs

    def schedules(self) -> list[dict]:
        return [self._schedule_view(schedule) for schedule in self.store.list_schedules()]

    def recover(self) -> dict:
        report = recover_store(self.store, now=self.clock.now())
        self.broker = InMemoryBroker(self.store.list_queue())
        self.worker.broker = self.broker
        return report

    def reopen(self) -> "WorkflowEngine":
        if self.store.path is None:
            reopened = WorkflowEngine(None, clock=FakeClock(self.clock.now()))
            reopened.store = self.store
            reopened.broker = InMemoryBroker(self.store.list_queue())
            reopened.logs = LogStore(self.store)
            reopened.runtime = LocalRuntime(reopened.clock)
            reopened.worker = Worker(reopened.store, reopened.broker, reopened.runtime, reopened.logs, reopened.clock)
            reopened.scheduler = Scheduler(reopened.store)
            return reopened
        return WorkflowEngine(self.store.path)

    def _coerce_spec(self, spec: JobSpec | dict | str, *, fmt: str | None) -> JobSpec:
        if isinstance(spec, JobSpec):
            return spec
        if isinstance(spec, dict):
            return normalize_job_spec(spec)
        path = Path(spec)
        if "\n" not in spec and path.exists():
            return parse_job_spec(path.read_text(encoding="utf-8"), fmt=fmt)
        return parse_job_spec(spec, fmt=fmt)

    def _next_job_id(self) -> str:
        return f"job-{len(self.store.list_jobs()) + 1:06d}"

    def _refresh_job(self, job_id: str) -> None:
        job = self.store.get_job(job_id)
        tasks = self.store.list_tasks(job_id)
        if job.state == "CANCELED":
            return
        changed = True
        while changed:
            changed = False
            by_id = {task.id: task for task in self.store.list_tasks(job_id)}
            for task in list(by_id.values()):
                original = task.state
                if task.state == "PENDING" and not self._condition_true(task, job):
                    task.state = "SKIPPED"
                    task.progress = 1.0
                elif task.kind == "group" and task.state in {"PENDING", "RUNNING"}:
                    deps_ok = all(by_id[dep].state in {"COMPLETED", "SKIPPED"} for dep in task.depends_on if dep in by_id)
                    deps_failed = any(by_id[dep].state in {"FAILED", "CANCELED"} for dep in task.depends_on if dep in by_id)
                    children = [by_id[child] for child in task.children if child in by_id]
                    if deps_failed:
                        task.state = "SKIPPED"
                        task.progress = 1.0
                    elif children and all(child.state in {"COMPLETED", "FAILED", "SKIPPED", "CANCELED"} for child in children):
                        if any(child.state == "FAILED" for child in children):
                            task.state = "FAILED"
                        elif any(child.state == "CANCELED" for child in children):
                            task.state = "CANCELED"
                        else:
                            task.state = "COMPLETED"
                        task.progress = sum(task_progress(child) for child in children) / len(children)
                        outputs = {child.name: child.output for child in children if child.output is not None}
                        wanted = task.metadata.get("output")
                        if wanted:
                            task.output = self._resolve_output_expr(wanted, outputs, task.output)
                        elif outputs:
                            task.output = next(reversed(outputs.values()))
                    elif deps_ok:
                        task.state = "RUNNING"
                        task.progress = max(task.progress, 0.01)
                if task.state != original:
                    self.store.save_task(task)
                    changed = True

        job = self.store.get_job(job_id)
        tasks = self.store.list_tasks(job_id)
        for task in runnable_tasks(job, tasks):
            task.state = "QUEUED"
            task.progress = max(task.progress, 0.01)
            self.store.save_task(task)
            item = QueueItem(task_id=task.id, job_id=job.id, available_at=self.clock.now(), attempt=len(task.attempts) + 1)
            self.store.append_queue(item)
            self.broker.enqueue(item)

        job = rollup_job_state(self.store.get_job(job_id), self.store.list_tasks(job_id))
        if job.state == "FAILED":
            for task in self.store.list_tasks(job_id):
                if task.state in {"PENDING", "QUEUED"}:
                    task.state = "SKIPPED"
                    task.progress = 1.0
                    self.store.remove_queue_item(task.id)
                    self.store.save_task(task)
            self.broker = InMemoryBroker(self.store.list_queue())
            self.worker.broker = self.broker
        job.updated_at = self.clock.now()
        self.store.save_job(job)

    def _condition_true(self, task: TaskRecord, job) -> bool:
        expr = task.if_expr
        if expr is None:
            return True
        if isinstance(expr, bool):
            return expr
        text = str(expr).strip()
        low = text.lower()
        if low in {"", "false", "0", "no", "off", "none", "null"}:
            return False
        if low in {"true", "1", "yes", "on"}:
            return True
        values: dict[str, Any] = {}
        values.update(job.metadata.get("inputs", {}))
        values.update(job.metadata.get("outputs", {}))
        values.update(task.metadata.get("item", {}))
        if text.startswith("!"):
            return not bool(values.get(text[1:], False))
        if "==" in text:
            left, right = [part.strip().strip("'\"") for part in text.split("==", 1)]
            return str(values.get(left, left)) == right
        return bool(values.get(text, False))

    def _job_view(self, job, tasks: list[TaskRecord], *, detail: bool) -> dict:
        base = {
            "id": job.id,
            "name": job.name,
            "state": job.state,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "output": job.output,
            "progress": job_progress(job, tasks),
            "percent": round(job_progress(job, tasks) * 100),
            "task_count": len(tasks),
        }
        if detail:
            base["metadata"] = job.metadata
            base["tasks"] = [self._task_view(task, tasks) for task in tasks]
            base["task_tree"] = [self._task_tree(task, tasks) for task in tasks if task.parent_id is None]
        return base

    def _task_view(self, task: TaskRecord, tasks: list[TaskRecord]) -> dict:
        return {
            "id": task.id,
            "job_id": task.job_id,
            "name": task.name,
            "state": task.state,
            "parent_id": task.parent_id,
            "children": list(task.children),
            "depends_on": list(task.depends_on),
            "run": task.run,
            "var": task.var,
            "output": task.output,
            "progress": task_progress(task),
            "percent": round(task_progress(task) * 100),
            "attempts": [to_dict(attempt) for attempt in task.attempts],
            "history": [to_dict(attempt) for attempt in task.attempts],
            "metadata": task.metadata,
        }

    def _task_tree(self, task: TaskRecord, tasks: list[TaskRecord]) -> dict:
        view = self._task_view(task, tasks)
        by_parent = [candidate for candidate in tasks if candidate.parent_id == task.id]
        view["children"] = [self._task_tree(child, tasks) for child in by_parent]
        return view

    def _schedule_view(self, schedule) -> dict:
        return {
            "id": schedule.id,
            "name": schedule.name,
            "interval_seconds": schedule.interval_seconds,
            "next_due_at": schedule.next_due_at,
            "last_run_at": schedule.last_run_at,
            "paused": schedule.paused,
        }

    def _resolve_output_expr(self, expr: str, outputs: dict, default=None):
        text = str(expr).strip()
        if text.startswith("{{") and text.endswith("}}"):
            text = text[2:-2].strip()
        if text.startswith("tasks."):
            text = text.split(".", 1)[1]
        if text.startswith("outputs."):
            text = text.split(".", 1)[1]
        return outputs.get(text, default)
