from __future__ import annotations

from .models import JobSpec, ScheduleRecord


class Scheduler:
    def register(self, name: str, spec: JobSpec, *, interval_seconds: int, now: int) -> ScheduleRecord:
        raise NotImplementedError

    def due(self, *, now: int) -> list[ScheduleRecord]:
        raise NotImplementedError

    def mark_run(self, schedule_id: str, *, now: int) -> None:
        raise NotImplementedError
