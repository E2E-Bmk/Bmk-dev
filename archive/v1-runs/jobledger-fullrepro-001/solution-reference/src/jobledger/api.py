from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from .cron import due_slots
from .events import make_event
from .export import canonical_export, validate_export
from .metrics import metrics_from_events, queue_counts
from .models import (
    CLAIMABLE_STATES,
    AttemptRecord,
    TERMINAL_STATES,
    CronEntry,
    EventRecord,
    JobLedgerError,
    JobRecord,
    UniquePolicy,
    to_epoch,
    transition_allowed,
)
from .recovery import recovery_report
from .reports import conflict_report_from_events, history_report, queue_report_from_jobs
from .retention import plan_prune, prune_report
from .retry import decide_retry
from .scheduler import claim_order, is_due
from .store import Store, open_store
from .windows import build_window, find_window_conflict, replace_window, window_report


class JobLedger:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.store: Store = open_store(self.path)

    def _now(self, now: str | int | None) -> str:
        return str(to_epoch(now))

    def _next_seq(self) -> int:
        events = self.store.load_events()
        return (events[-1].seq if events else 0) + 1

    def _emit(self, event_type: str, *, at: str, job_id: str | None = None, data: dict[str, Any] | None = None) -> None:
        self.store.append_event(make_event(self._next_seq(), event_type, at=at, job_id=job_id, data=data))

    def _save_job(self, job: JobRecord) -> None:
        jobs = self.store.load_jobs()
        replaced = False
        for index, old in enumerate(jobs):
            if old.id == job.id:
                jobs[index] = job
                replaced = True
                break
        if not replaced:
            jobs.append(job)
        self.store.save_jobs(jobs)

    def _get_job(self, job_id: str) -> JobRecord:
        for job in self.store.load_jobs():
            if job.id == job_id:
                return job
        raise JobLedgerError("unknown job")

    def enqueue(
        self,
        kind: str,
        args: dict[str, Any] | None = None,
        *,
        queue: str = "default",
        priority: int = 0,
        max_attempts: int = 3,
        scheduled_at: str | int | None = None,
        unique: UniquePolicy | dict[str, Any] | None = None,
        now: str | int | None = None,
    ) -> dict[str, Any]:
        at = self._now(now)
        state = "scheduled" if scheduled_at is not None and to_epoch(scheduled_at) > to_epoch(now) else "available"
        policy = UniquePolicy.from_value(unique)
        job = JobRecord(
            id=f"job-{uuid4().hex[:12]}",
            queue=queue,
            kind=kind,
            args=dict(args or {}),
            state=state,  # type: ignore[arg-type]
            priority=priority,
            max_attempts=max_attempts,
            scheduled_at=str(to_epoch(scheduled_at)) if scheduled_at is not None else None,
            created_at=at,
            updated_at=at,
            unique=policy,
        )
        jobs = self.store.load_jobs()
        windows = self.store.load_windows()
        conflict = find_window_conflict(job, windows, jobs, now=now)
        if conflict is not None and policy is not None:
            self._emit("unique_conflict", at=at, job_id=conflict.job_id, data={"queue": conflict.queue, "candidate": job.to_dict(), "window_key": conflict.key})
            if policy.on_conflict == "reject":
                raise JobLedgerError("uniqueness conflict")
            old_job = self._get_job(conflict.job_id)
            old_job.state = "cancelled"
            old_job.updated_at = at
            self._save_job(old_job)
            windows = replace_window(windows, old_job.id, job.id)
            self._emit("cancelled", at=at, job_id=old_job.id, data={"queue": old_job.queue, "reason": "unique replace"})
            jobs = self.store.load_jobs()
        jobs.append(job)
        self.store.save_jobs(jobs)
        if policy is not None:
            windows.append(build_window(job, policy, now=now))
            self.store.save_windows(windows)
        self._emit("enqueued", at=at, job_id=job.id, data={"queue": queue, "kind": kind})
        return job.to_dict()

    def claim(
        self,
        queue: str = "default",
        *,
        worker: str = "worker",
        limit: int = 1,
        now: str | int | None = None,
    ) -> list[dict[str, Any]]:
        if limit < 1:
            raise JobLedgerError("limit must be positive")
        at = self._now(now)
        jobs = self.store.load_jobs()
        candidates = [job for job in jobs if job.queue == queue and job.state in CLAIMABLE_STATES and is_due(job, now)]
        claimed: list[JobRecord] = []
        for job in claim_order(candidates)[:limit]:
            job.state = "executing"
            job.updated_at = at
            claimed.append(job)
            self._emit("claimed", at=at, job_id=job.id, data={"queue": queue, "worker": worker})
        if claimed:
            by_id = {job.id: job for job in claimed}
            self.store.save_jobs([by_id.get(job.id, job) for job in jobs])
        return [job.to_dict() for job in claimed]

    def complete(self, job_id: str, result: dict[str, Any] | None = None, *, now: str | int | None = None) -> dict[str, Any]:
        job = self._get_job(job_id)
        if job.state != "executing" or not transition_allowed(job.state, "completed"):
            raise JobLedgerError("job is not executing")
        at = self._now(now)
        job.state = "completed"
        job.updated_at = at
        self._save_job(job)
        self._emit("completed", at=at, job_id=job.id, data={"queue": job.queue, "result": dict(result or {})})
        return job.to_dict()

    def fail(self, job_id: str, error: str, *, now: str | int | None = None) -> dict[str, Any]:
        job = self._get_job(job_id)
        if job.state != "executing":
            raise JobLedgerError("job is not executing")
        at = self._now(now)
        job.attempt += 1
        job.last_error = error
        self.store.append_attempt(AttemptRecord(job_id=job.id, attempt=job.attempt, at=at, error=error))
        self._emit("failed", at=at, job_id=job.id, data={"queue": job.queue, "attempt": job.attempt, "error": error})
        decision = decide_retry(job.attempt, job.max_attempts)
        job.state = decision.state  # type: ignore[assignment]
        job.updated_at = at
        if decision.delay_seconds is not None:
            job.scheduled_at = str(to_epoch(now) + decision.delay_seconds)
            self._emit("retry_scheduled", at=at, job_id=job.id, data={"queue": job.queue, "scheduled_at": job.scheduled_at})
        else:
            self._emit("discarded", at=at, job_id=job.id, data={"queue": job.queue})
        self._save_job(job)
        return job.to_dict()

    def cancel(self, job_id: str, reason: str | None = None, *, now: str | int | None = None) -> dict[str, Any]:
        job = self._get_job(job_id)
        if job.state in TERMINAL_STATES:
            raise JobLedgerError("terminal job cannot be cancelled")
        at = self._now(now)
        job.state = "cancelled"
        job.updated_at = at
        self._save_job(job)
        self._emit("cancelled", at=at, job_id=job.id, data={"queue": job.queue, "reason": reason})
        return job.to_dict()

    def configure_cron(self, name: str, every_seconds: int, kind: str, args: dict[str, Any] | None = None, *, queue: str = "default", unique: UniquePolicy | dict[str, Any] | None = None) -> dict[str, Any]:
        entry = CronEntry(name=name, every_seconds=every_seconds, kind=kind, args=dict(args or {}), queue=queue, unique=UniquePolicy.from_value(unique))
        entries = [old for old in self.store.load_cron() if old.name != name]
        entries.append(entry)
        self.store.save_cron(entries)
        self._emit("cron_configured", at="0", data={"name": name, "queue": queue})
        return entry.to_dict()

    def tick(self, now: str | int) -> list[dict[str, Any]]:
        created: list[dict[str, Any]] = []
        updated: list[CronEntry] = []
        for entry in self.store.load_cron():
            slots = due_slots(entry, entry.last_slot, now)
            last_slot = entry.last_slot
            for slot in slots:
                job = self.enqueue(entry.kind, entry.args, queue=entry.queue, scheduled_at=slot, unique=entry.unique, now=slot)
                self._emit("cron_tick", at=str(slot), job_id=job["id"], data={"queue": entry.queue, "cron": entry.name, "slot": slot})
                created.append(job)
                last_slot = slot
            updated.append(CronEntry(entry.name, entry.every_seconds, entry.kind, entry.args, entry.queue, entry.unique, last_slot))
        self.store.save_cron(updated)
        return created

    def jobs(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        filters = dict(filters or {})
        result = self.store.load_jobs()
        for key, value in filters.items():
            result = [job for job in result if getattr(job, key) == value]
        return [job.to_dict() for job in sorted(result, key=lambda job: job.id)]

    def history(self, job_id: str) -> dict[str, Any]:
        job = self._get_job(job_id)
        events = [event.to_dict() for event in self.store.load_events() if event.job_id == job_id]
        attempts = [attempt.to_dict() for attempt in self.store.load_attempts() if attempt.job_id == job_id]
        return history_report(job, attempts, events)

    def queue_report(self) -> dict[str, Any]:
        return queue_report_from_jobs(self.store.load_jobs())

    def conflict_report(self) -> dict[str, Any]:
        report = conflict_report_from_events(self.store.load_events())
        report["uniqueness"] = window_report(self.store.load_windows(), self.store.load_jobs())
        return report

    def metrics(self) -> dict[str, Any]:
        return metrics_from_events(self.store.load_events())

    def events(self, after: int | None = None) -> list[dict[str, Any]]:
        events = self.store.load_events()
        if after is not None:
            events = [event for event in events if event.seq > after]
        return [event.to_dict() for event in events]

    def prune(self, retain_seconds: int, *, now: str | int | None = None) -> dict[str, Any]:
        jobs = self.store.load_jobs()
        decision = plan_prune(jobs, retain_seconds, now=now)
        self.store.save_jobs(decision.keep)
        report = prune_report(jobs, decision, self.metrics())
        self._emit("pruned", at=self._now(now), data=report)
        return report

    def recover(self) -> dict[str, Any]:
        markers = self.store.load_recovery_markers()
        report = recovery_report(markers)
        self.store.save_recovery_markers([])
        self._emit("recovered", at="0", data=report)
        return report

    def export_state(self) -> dict[str, Any]:
        data = {
            "jobs": [job.to_dict() for job in self.store.load_jobs()],
            "attempts": [attempt.to_dict() for attempt in self.store.load_attempts()],
            "events": [event.to_dict() for event in self.store.load_events()],
            "cron": [entry.to_dict() for entry in self.store.load_cron()],
            "uniqueness_windows": [window.to_dict() for window in self.store.load_windows()],
            "recovery_markers": self.store.load_recovery_markers(),
        }
        return canonical_export(data)

    @classmethod
    def import_state(cls, path: str | Path, data: dict[str, Any]) -> "JobLedger":
        validate_export(data)
        ledger = cls(path)
        ledger.store.save_jobs([JobRecord.from_dict(item) for item in data["jobs"]])  # type: ignore[arg-type]
        ledger.store.save_attempts([AttemptRecord.from_dict(item) for item in data["attempts"]])  # type: ignore[arg-type]
        for event in data["events"]:  # type: ignore[union-attr]
            ledger.store.append_event(EventRecord.from_dict(event))
        ledger.store.save_cron([CronEntry.from_dict(item) for item in data["cron"]])  # type: ignore[arg-type]
        ledger.store.save_windows([__import__("jobledger.windows", fromlist=["WindowRecord"]).WindowRecord.from_dict(item) for item in data["uniqueness_windows"]])  # type: ignore[arg-type]
        ledger.store.save_recovery_markers([dict(item) for item in data["recovery_markers"]])  # type: ignore[arg-type]
        return ledger
