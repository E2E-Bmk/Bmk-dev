from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Iterable

from .errors import NotFoundError
from .models import (
    JobRecord,
    QueueItem,
    ScheduleRecord,
    TaskRecord,
    job_record_from_dict,
    queue_item_from_dict,
    schedule_from_dict,
    task_record_from_dict,
    to_dict,
)


class WorkflowStore:
    """Public persistence boundary used by API, worker, scheduler, and recovery."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else None
        if self.path is not None and self.path.suffix == "":
            self.path = self.path / "workflow-state.json"
        self._state = self._load()

    def _empty(self) -> dict:
        return {"jobs": {}, "tasks": {}, "queue": [], "schedules": {}, "logs": [], "meta": {"clock": 0}}

    def _load(self) -> dict:
        if self.path is None or not self.path.exists():
            return self._empty()
        with self.path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        base = self._empty()
        base.update(data)
        for key in base:
            if key not in data:
                data[key] = base[key]
        return data

    def _flush(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix=self.path.name + ".", suffix=".tmp", dir=self.path.parent)
        tmp = Path(tmp_name)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(self._state, fh, indent=2, sort_keys=True)
        for attempt in range(5):
            try:
                os.replace(tmp, self.path)
                return
            except PermissionError:
                if attempt == 4:
                    raise
                time.sleep(0.01)

    def create_job(self, job: JobRecord, tasks: Iterable[TaskRecord]) -> None:
        self._state["jobs"][job.id] = to_dict(job)
        for task in tasks:
            self._state["tasks"][task.id] = to_dict(task)
        self._flush()

    def get_job(self, job_id: str) -> JobRecord:
        try:
            return job_record_from_dict(self._state["jobs"][job_id])
        except KeyError as exc:
            raise NotFoundError(f"job not found: {job_id}") from exc

    def list_jobs(self) -> list[JobRecord]:
        return [job_record_from_dict(item) for item in self._state["jobs"].values()]

    def save_job(self, job: JobRecord) -> None:
        if job.id not in self._state["jobs"]:
            raise NotFoundError(f"job not found: {job.id}")
        self._state["jobs"][job.id] = to_dict(job)
        self._flush()

    def get_task(self, task_id: str) -> TaskRecord:
        try:
            return task_record_from_dict(self._state["tasks"][task_id])
        except KeyError as exc:
            raise NotFoundError(f"task not found: {task_id}") from exc

    def list_tasks(self, job_id: str | None = None) -> list[TaskRecord]:
        tasks = [task_record_from_dict(item) for item in self._state["tasks"].values()]
        if job_id is not None:
            tasks = [task for task in tasks if task.job_id == job_id]
        return sorted(tasks, key=lambda task: (task.job_id, task.index, task.id))

    def save_task(self, task: TaskRecord) -> None:
        if task.id not in self._state["tasks"]:
            raise NotFoundError(f"task not found: {task.id}")
        self._state["tasks"][task.id] = to_dict(task)
        self._flush()

    def append_queue(self, item: QueueItem) -> None:
        self.remove_queue_item(item.task_id, flush=False)
        self._state["queue"].append(to_dict(item))
        self._flush()

    def list_queue(self) -> list[QueueItem]:
        return [queue_item_from_dict(item) for item in self._state["queue"]]

    def remove_queue_item(self, task_id: str, *, flush: bool = True) -> None:
        self._state["queue"] = [item for item in self._state["queue"] if item["task_id"] != task_id]
        if flush:
            self._flush()

    def replace_queue(self, items: Iterable[QueueItem]) -> None:
        seen: set[str] = set()
        queue = []
        for item in items:
            if item.task_id in seen:
                continue
            seen.add(item.task_id)
            queue.append(to_dict(item))
        self._state["queue"] = queue
        self._flush()

    def save_schedule(self, schedule: ScheduleRecord) -> None:
        self._state["schedules"][schedule.id] = to_dict(schedule)
        self._flush()

    def list_schedules(self) -> list[ScheduleRecord]:
        return [schedule_from_dict(item) for item in self._state["schedules"].values()]

    def append_log(self, entry: dict) -> None:
        self._state["logs"].append(dict(entry))
        self._flush()

    def list_logs(self) -> list[dict]:
        return list(self._state["logs"])

    def clock(self) -> int:
        return int(self._state.get("meta", {}).get("clock", 0))

    def save_clock(self, now: int) -> None:
        self._state.setdefault("meta", {})["clock"] = int(now)
        self._flush()

    def reopen(self) -> "WorkflowStore":
        return WorkflowStore(self.path)
