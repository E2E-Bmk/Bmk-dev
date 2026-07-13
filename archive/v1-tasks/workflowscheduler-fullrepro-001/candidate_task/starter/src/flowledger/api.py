"""Integrated FlowLedger facade."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class FlowLedger:
    """Durable local workflow scheduler facade."""

    def __init__(self, store_path: str | Path):
        raise NotImplementedError

    def init(self) -> dict[str, Any]:
        raise NotImplementedError

    def put_spec(self, spec: dict[str, Any] | str | Path) -> dict[str, Any]:
        raise NotImplementedError

    def tick(self, now: str) -> dict[str, Any]:
        raise NotImplementedError

    def start(self, workflow: str, now: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        raise NotImplementedError

    def claim(self, queue: str, worker_id: str, now: str, lease_seconds: int = 60) -> dict[str, Any] | None:
        raise NotImplementedError

    def complete(self, item_id: str, worker_id: str, now: str, output: Any = None) -> dict[str, Any]:
        raise NotImplementedError

    def fail(self, item_id: str, worker_id: str, now: str, error: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def cancel(self, run_id: str, now: str) -> dict[str, Any]:
        raise NotImplementedError

    def status(self, workflow: str | None = None, run_id: str | None = None) -> dict[str, Any]:
        raise NotImplementedError

    def history(self, workflow: str | None = None) -> dict[str, Any]:
        raise NotImplementedError

    def queue(self) -> dict[str, Any]:
        raise NotImplementedError

    def next_runs(self, now: str) -> dict[str, Any]:
        raise NotImplementedError

    def logs(self, run_id: str | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError

    def events(self, run_id: str | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError

    def recover(self, now: str) -> dict[str, Any]:
        raise NotImplementedError

    def export(self) -> dict[str, Any]:
        raise NotImplementedError

    def import_snapshot(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
