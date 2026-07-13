from __future__ import annotations

from pathlib import Path

from .clock import FakeClock
from .models import JobSpec


class WorkflowEngine:
    """Main public API used by hidden integration and system tests."""

    def __init__(self, store_path: str | Path | None = None, *, clock: FakeClock | None = None) -> None:
        raise NotImplementedError

    def submit(self, spec: JobSpec | dict | str, *, fmt: str | None = None) -> dict:
        raise NotImplementedError

    def run_until_idle(self, *, limit: int = 100) -> list[dict]:
        raise NotImplementedError

    def get_job(self, job_id: str) -> dict:
        raise NotImplementedError

    def list_jobs(self) -> list[dict]:
        raise NotImplementedError

    def get_task(self, task_id: str) -> dict:
        raise NotImplementedError

    def queue_status(self) -> dict:
        raise NotImplementedError

    def log_page(self, *, job_id: str | None = None, task_id: str | None = None, contains: str | None = None) -> list[dict]:
        raise NotImplementedError

    def progress(self, job_id: str) -> dict:
        raise NotImplementedError

    def cancel(self, job_id: str) -> dict:
        raise NotImplementedError

    def restart(self, job_id: str) -> dict:
        raise NotImplementedError

    def register_schedule(self, name: str, spec: JobSpec | dict | str, *, interval_seconds: int, fmt: str | None = None) -> dict:
        raise NotImplementedError

    def tick(self, *, seconds: int = 0) -> list[dict]:
        raise NotImplementedError

    def schedules(self) -> list[dict]:
        raise NotImplementedError

    def recover(self) -> dict:
        raise NotImplementedError

    def reopen(self) -> "WorkflowEngine":
        raise NotImplementedError
