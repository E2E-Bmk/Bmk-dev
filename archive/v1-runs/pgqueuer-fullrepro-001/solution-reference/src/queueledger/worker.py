from __future__ import annotations

from dataclasses import replace

from .models import Job, JobStatus
from .store import Store


class Worker:
    def __init__(self, store: Store, *, worker_id: str, registry=None, global_concurrency_limit: int = 0) -> None:
        self.store = store
        self.worker_id = worker_id
        self.registry = registry
        self.global_concurrency_limit = global_concurrency_limit

    def claim(self, entrypoints: list[str], *, now: float, limit: int = 1) -> list[Job]:
        wanted = set(entrypoints)
        candidates = [
            job
            for job in self.store.list_jobs()
            if job.status == JobStatus.QUEUED
            and job.entrypoint in wanted
            and job.execute_after <= now
        ]
        active = [job for job in self.store.list_jobs() if job.status == JobStatus.PICKED]
        if self.global_concurrency_limit > 0:
            limit = min(limit, max(0, self.global_concurrency_limit - len(active)))
        if self.registry is not None:
            filtered = []
            for job in candidates:
                entry_limit = self.registry.concurrency_limit(job.entrypoint)
                if entry_limit <= 0:
                    filtered.append(job)
                    continue
                active_for_entry = sum(1 for item in active if item.entrypoint == job.entrypoint)
                already_selected = sum(1 for item in filtered if item.entrypoint == job.entrypoint)
                if active_for_entry + already_selected < entry_limit:
                    filtered.append(job)
            candidates = filtered
        candidates.sort(key=lambda job: (-job.priority, job.created_at, job.id))
        claimed = [replace(job, status=JobStatus.PICKED, heartbeat=now, updated_at=now, metadata={**job.metadata, "worker_id": self.worker_id}) for job in candidates[:limit]]
        by_id = {job.id: job for job in claimed}
        self.store.replace_jobs([by_id.get(job.id, job) for job in self.store.list_jobs()])
        return claimed

    def heartbeat(self, job_ids: list[str], *, now: float) -> None:
        ids = set(job_ids)
        self.store.replace_jobs([
            replace(job, heartbeat=now, updated_at=now) if job.id in ids and job.status == JobStatus.PICKED else job
            for job in self.store.list_jobs()
        ])

    def complete(self, job_id: str, *, now: float) -> Job:
        return self._transition(job_id, JobStatus.SUCCESSFUL, now)

    def fail(self, job_id: str, error: str, *, now: float) -> Job:
        job = self.store.get_job(job_id)
        if job is None:
            raise KeyError(job_id)
        attempts = job.attempts + 1
        if attempts < job.max_attempts:
            updated = replace(job, status=JobStatus.QUEUED, attempts=attempts, heartbeat=None, execute_after=now + job.retry_delay, updated_at=now, metadata={**job.metadata, "last_error": error})
        else:
            updated = replace(job, status=JobStatus.FAILED, attempts=attempts, heartbeat=None, updated_at=now, metadata={**job.metadata, "last_error": error})
        self._put_transition(updated)
        return updated

    def cancel(self, job_id: str, *, now: float) -> Job:
        return self._transition(job_id, JobStatus.CANCELED, now)

    def _transition(self, job_id: str, status: JobStatus, now: float) -> Job:
        job = self.store.get_job(job_id)
        if job is None:
            raise KeyError(job_id)
        updated = replace(job, status=status, heartbeat=None, updated_at=now)
        self._put_transition(updated)
        return updated

    def _put_transition(self, updated: Job) -> None:
        self.store.replace_jobs([updated if job.id == updated.id else job for job in self.store.list_jobs()])
        if updated.status in {JobStatus.SUCCESSFUL, JobStatus.EXCEPTION, JobStatus.FAILED, JobStatus.CANCELED, JobStatus.DELETED}:
            self.store.put_job(updated)
