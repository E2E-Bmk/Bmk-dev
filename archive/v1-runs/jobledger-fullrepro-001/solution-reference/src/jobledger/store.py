from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from .models import AttemptRecord, CronEntry, EventRecord, JobRecord, JobLedgerError
from .windows import WindowRecord


class Store(Protocol):
    def load_jobs(self) -> list[JobRecord]: ...
    def save_jobs(self, jobs: list[JobRecord]) -> None: ...
    def load_attempts(self) -> list[AttemptRecord]: ...
    def save_attempts(self, attempts: list[AttemptRecord]) -> None: ...
    def append_attempt(self, attempt: AttemptRecord) -> None: ...
    def load_events(self) -> list[EventRecord]: ...
    def append_event(self, event: EventRecord) -> None: ...
    def load_cron(self) -> list[CronEntry]: ...
    def save_cron(self, entries: list[CronEntry]) -> None: ...
    def load_windows(self) -> list[WindowRecord]: ...
    def save_windows(self, windows: list[WindowRecord]) -> None: ...
    def load_recovery_markers(self) -> list[dict[str, object]]: ...
    def save_recovery_markers(self, markers: list[dict[str, object]]) -> None: ...


class JsonStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.file = self.path / "jobledger.json"
        if not self.file.exists():
            self._write({"jobs": [], "attempts": [], "events": [], "cron": [], "uniqueness_windows": [], "recovery_markers": []})

    def _read(self) -> dict[str, object]:
        try:
            return json.loads(self.file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise JobLedgerError("corrupt store") from exc

    def _write(self, data: dict[str, object]) -> None:
        tmp = self.file.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, sort_keys=True, indent=2), encoding="utf-8")
        if self.file.exists():
            self.file.unlink()
        tmp.rename(self.file)

    def load_jobs(self) -> list[JobRecord]:
        return [JobRecord.from_dict(item) for item in self._read().get("jobs", [])]  # type: ignore[arg-type]

    def save_jobs(self, jobs: list[JobRecord]) -> None:
        data = self._read()
        data["jobs"] = [job.to_dict() for job in jobs]
        self._write(data)

    def load_attempts(self) -> list[AttemptRecord]:
        return [AttemptRecord.from_dict(item) for item in self._read().get("attempts", [])]  # type: ignore[arg-type]

    def save_attempts(self, attempts: list[AttemptRecord]) -> None:
        data = self._read()
        data["attempts"] = [attempt.to_dict() for attempt in attempts]
        self._write(data)

    def append_attempt(self, attempt: AttemptRecord) -> None:
        attempts = self.load_attempts()
        attempts.append(attempt)
        self.save_attempts(attempts)

    def load_events(self) -> list[EventRecord]:
        return [EventRecord.from_dict(item) for item in self._read().get("events", [])]  # type: ignore[arg-type]

    def append_event(self, event: EventRecord) -> None:
        data = self._read()
        events = list(data.get("events", []))
        events.append(event.to_dict())
        data["events"] = events
        self._write(data)

    def load_cron(self) -> list[CronEntry]:
        return [CronEntry.from_dict(item) for item in self._read().get("cron", [])]  # type: ignore[arg-type]

    def save_cron(self, entries: list[CronEntry]) -> None:
        data = self._read()
        data["cron"] = [entry.to_dict() for entry in entries]
        self._write(data)

    def load_windows(self) -> list[WindowRecord]:
        return [WindowRecord.from_dict(item) for item in self._read().get("uniqueness_windows", [])]  # type: ignore[arg-type]

    def save_windows(self, windows: list[WindowRecord]) -> None:
        data = self._read()
        data["uniqueness_windows"] = [window.to_dict() for window in windows]
        self._write(data)

    def load_recovery_markers(self) -> list[dict[str, object]]:
        return [dict(item) for item in self._read().get("recovery_markers", [])]  # type: ignore[arg-type]

    def save_recovery_markers(self, markers: list[dict[str, object]]) -> None:
        data = self._read()
        data["recovery_markers"] = markers
        self._write(data)


def open_store(path: str | Path) -> Store:
    """Open or create the durable public store at path."""
    return JsonStore(path)
