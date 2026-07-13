from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from .models import CompletionEvent, Job, JobStatus, QueueReport, Schedule


class Store(Protocol):
    def put_job(self, job: Job) -> Job: ...
    def get_job(self, job_id: str) -> Job | None: ...
    def list_jobs(self) -> list[Job]: ...
    def replace_jobs(self, jobs: list[Job]) -> None: ...
    def put_schedule(self, schedule: Schedule) -> Schedule: ...
    def list_schedules(self) -> list[Schedule]: ...
    def replace_schedules(self, schedules: list[Schedule]) -> None: ...
    def append_completion(self, event: CompletionEvent) -> None: ...
    def completions_since(self, offset: int = 0) -> list[CompletionEvent]: ...
    def queue_report(self) -> QueueReport: ...


class InMemoryStore:
    """Implement the public Store contract without durability."""

    def __init__(self) -> None:
        self.jobs: dict[str, Job] = {}
        self.schedules: dict[str, Schedule] = {}
        self.completion_events: list[CompletionEvent] = []

    def put_job(self, job: Job) -> Job:
        self.jobs[job.id] = job
        if job.status in TERMINAL_STATUSES and not any(e.job_id == job.id and e.status == job.status for e in self.completion_events):
            self.completion_events.append(CompletionEvent(job.id, job.status, job.updated_at))
        return job

    def get_job(self, job_id: str) -> Job | None:
        return self.jobs.get(job_id)

    def list_jobs(self) -> list[Job]:
        return sorted(self.jobs.values(), key=lambda job: (job.created_at, job.id))

    def replace_jobs(self, jobs: list[Job]) -> None:
        self.jobs = {job.id: job for job in jobs}

    def put_schedule(self, schedule: Schedule) -> Schedule:
        self.schedules[schedule.id] = schedule
        return schedule

    def list_schedules(self) -> list[Schedule]:
        return sorted(self.schedules.values(), key=lambda schedule: schedule.id)

    def replace_schedules(self, schedules: list[Schedule]) -> None:
        self.schedules = {schedule.id: schedule for schedule in schedules}

    def append_completion(self, event: CompletionEvent) -> None:
        self.completion_events.append(event)

    def completions_since(self, offset: int = 0) -> list[CompletionEvent]:
        return self.completion_events[offset:]

    def queue_report(self) -> QueueReport:
        by_entrypoint: dict[str, int] = {}
        queued = picked = terminal = 0
        for job in self.jobs.values():
            by_entrypoint[job.entrypoint] = by_entrypoint.get(job.entrypoint, 0) + 1
            if job.status == JobStatus.QUEUED:
                queued += 1
            elif job.status == JobStatus.PICKED:
                picked += 1
            elif job.status in TERMINAL_STATUSES:
                terminal += 1
        return QueueReport(queued=queued, picked=picked, terminal=terminal, by_entrypoint=by_entrypoint)


class FileStore:
    """Implement the public Store contract with durable local files."""

    def __init__(self, root: str) -> None:
        self.root = root
        self.path = Path(root)
        self.path.mkdir(parents=True, exist_ok=True)
        self.state_file = self.path / "queueledger-state.json"
        self._inner = InMemoryStore()
        self._load()

    def _load(self) -> None:
        if not self.state_file.exists():
            return
        raw = json.loads(self.state_file.read_text(encoding="utf-8"))
        self._inner.jobs = {item["id"]: _job_from_dict(item) for item in raw.get("jobs", [])}
        self._inner.schedules = {item["id"]: _schedule_from_dict(item) for item in raw.get("schedules", [])}
        self._inner.completion_events = [_completion_from_dict(item) for item in raw.get("completions", [])]

    def _save(self) -> None:
        raw = {
            "jobs": [_job_to_dict(job) for job in self._inner.list_jobs()],
            "schedules": [_schedule_to_dict(schedule) for schedule in self._inner.list_schedules()],
            "completions": [_completion_to_dict(event) for event in self._inner.completion_events],
        }
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(raw, sort_keys=True, indent=2), encoding="utf-8")
        tmp.replace(self.state_file)

    def put_job(self, job: Job) -> Job:
        result = self._inner.put_job(job)
        self._save()
        return result

    def get_job(self, job_id: str) -> Job | None:
        return self._inner.get_job(job_id)

    def list_jobs(self) -> list[Job]:
        return self._inner.list_jobs()

    def replace_jobs(self, jobs: list[Job]) -> None:
        self._inner.replace_jobs(jobs)
        self._save()

    def put_schedule(self, schedule: Schedule) -> Schedule:
        result = self._inner.put_schedule(schedule)
        self._save()
        return result

    def list_schedules(self) -> list[Schedule]:
        return self._inner.list_schedules()

    def replace_schedules(self, schedules: list[Schedule]) -> None:
        self._inner.replace_schedules(schedules)
        self._save()

    def append_completion(self, event: CompletionEvent) -> None:
        self._inner.append_completion(event)
        self._save()

    def completions_since(self, offset: int = 0) -> list[CompletionEvent]:
        return self._inner.completions_since(offset)

    def queue_report(self) -> QueueReport:
        return self._inner.queue_report()


TERMINAL_STATUSES = {
    JobStatus.SUCCESSFUL,
    JobStatus.EXCEPTION,
    JobStatus.FAILED,
    JobStatus.CANCELED,
    JobStatus.DELETED,
}


def _job_to_dict(job: Job) -> dict:
    return {
        "id": job.id,
        "entrypoint": job.entrypoint,
        "payload": job.payload.decode("latin1"),
        "priority": job.priority,
        "status": job.status.value,
        "attempts": job.attempts,
        "execute_after": job.execute_after,
        "heartbeat": job.heartbeat,
        "max_attempts": job.max_attempts,
        "retry_delay": job.retry_delay,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "metadata": job.metadata,
    }


def _job_from_dict(raw: dict) -> Job:
    return Job(
        id=raw["id"],
        entrypoint=raw["entrypoint"],
        payload=raw["payload"].encode("latin1"),
        priority=raw.get("priority", 0),
        status=JobStatus(raw.get("status", "queued")),
        attempts=raw.get("attempts", 0),
        execute_after=raw.get("execute_after", 0.0),
        heartbeat=raw.get("heartbeat"),
        max_attempts=raw.get("max_attempts", 3),
        retry_delay=raw.get("retry_delay", 1.0),
        created_at=raw.get("created_at", 0.0),
        updated_at=raw.get("updated_at", 0.0),
        metadata=raw.get("metadata", {}),
    )


def _schedule_to_dict(schedule: Schedule) -> dict:
    return {
        "id": schedule.id,
        "entrypoint": schedule.entrypoint,
        "every_seconds": schedule.every_seconds,
        "payload": schedule.payload.decode("latin1"),
        "last_run_at": schedule.last_run_at,
        "heartbeat": schedule.heartbeat,
        "enabled": schedule.enabled,
    }


def _schedule_from_dict(raw: dict) -> Schedule:
    return Schedule(
        id=raw["id"],
        entrypoint=raw["entrypoint"],
        every_seconds=raw["every_seconds"],
        payload=raw.get("payload", "").encode("latin1"),
        last_run_at=raw.get("last_run_at"),
        heartbeat=raw.get("heartbeat"),
        enabled=raw.get("enabled", True),
    )


def _completion_to_dict(event: CompletionEvent) -> dict:
    return {"job_id": event.job_id, "status": event.status.value, "observed_at": event.observed_at}


def _completion_from_dict(raw: dict) -> CompletionEvent:
    return CompletionEvent(raw["job_id"], JobStatus(raw["status"]), raw["observed_at"])
