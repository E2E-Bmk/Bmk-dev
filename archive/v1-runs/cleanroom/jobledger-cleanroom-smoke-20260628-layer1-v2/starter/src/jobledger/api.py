from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import JobLedgerError, UniquePolicy


class JobLedger:
    def __init__(self, path: str | Path):
        raise NotImplementedError

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
        raise NotImplementedError

    def claim(
        self,
        queue: str = "default",
        *,
        worker: str = "worker",
        limit: int = 1,
        now: str | int | None = None,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    def complete(self, job_id: str, result: dict[str, Any] | None = None, *, now: str | int | None = None) -> dict[str, Any]:
        raise NotImplementedError

    def fail(self, job_id: str, error: str, *, now: str | int | None = None) -> dict[str, Any]:
        raise NotImplementedError

    def cancel(self, job_id: str, reason: str | None = None, *, now: str | int | None = None) -> dict[str, Any]:
        raise NotImplementedError

    def configure_cron(self, name: str, every_seconds: int, kind: str, args: dict[str, Any] | None = None, *, queue: str = "default", unique: UniquePolicy | dict[str, Any] | None = None) -> dict[str, Any]:
        raise NotImplementedError

    def tick(self, now: str | int) -> list[dict[str, Any]]:
        raise NotImplementedError

    def jobs(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError

    def history(self, job_id: str) -> dict[str, Any]:
        raise NotImplementedError

    def queue_report(self) -> dict[str, Any]:
        raise NotImplementedError

    def conflict_report(self) -> dict[str, Any]:
        raise NotImplementedError

    def metrics(self) -> dict[str, Any]:
        raise NotImplementedError

    def events(self, after: int | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError

    def prune(self, retain_seconds: int, *, now: str | int | None = None) -> dict[str, Any]:
        raise NotImplementedError

    def recover(self) -> dict[str, Any]:
        raise NotImplementedError

    def export_state(self) -> dict[str, Any]:
        raise NotImplementedError

    @classmethod
    def import_state(cls, path: str | Path, data: dict[str, Any]) -> "JobLedger":
        raise NotImplementedError
