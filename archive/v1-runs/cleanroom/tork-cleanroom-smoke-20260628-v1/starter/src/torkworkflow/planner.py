from __future__ import annotations

from .models import JobRecord, JobSpec, TaskRecord


def build_records(spec: JobSpec, *, job_id: str, now: int) -> tuple[JobRecord, list[TaskRecord]]:
    """Create initial job and task records from a JobSpec."""
    raise NotImplementedError


def runnable_tasks(job: JobRecord, tasks: list[TaskRecord]) -> list[TaskRecord]:
    """Return tasks whose dependencies are satisfied."""
    raise NotImplementedError


def rollup_job_state(job: JobRecord, tasks: list[TaskRecord]) -> JobRecord:
    """Update job state/output/progress from task records."""
    raise NotImplementedError
