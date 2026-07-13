from __future__ import annotations

from .models import JobSpec, ScheduleRecord
from .datastore import WorkflowStore


class Scheduler:
    def __init__(self, store: WorkflowStore | None = None) -> None:
        self.store = store or WorkflowStore(None)

    def register(self, name: str, spec: JobSpec, *, interval_seconds: int, now: int) -> ScheduleRecord:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        schedule = ScheduleRecord(
            id=f"schedule-{name}",
            name=name,
            spec=spec,
            interval_seconds=int(interval_seconds),
            next_due_at=now + int(interval_seconds),
        )
        self.store.save_schedule(schedule)
        return schedule

    def due(self, *, now: int) -> list[ScheduleRecord]:
        return [schedule for schedule in self.store.list_schedules() if not schedule.paused and schedule.next_due_at <= now]

    def mark_run(self, schedule_id: str, *, now: int) -> None:
        for schedule in self.store.list_schedules():
            if schedule.id == schedule_id:
                schedule.last_run_at = now
                while schedule.next_due_at <= now:
                    schedule.next_due_at += schedule.interval_seconds
                self.store.save_schedule(schedule)
                return
        raise KeyError(schedule_id)
