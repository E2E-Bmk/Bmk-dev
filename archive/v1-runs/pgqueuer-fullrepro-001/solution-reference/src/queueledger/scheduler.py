from __future__ import annotations

from dataclasses import replace

from .models import Job, Schedule
from .store import Store


class Scheduler:
    def __init__(self, store: Store) -> None:
        self.store = store

    def register(self, schedule: Schedule) -> Schedule:
        if schedule.every_seconds <= 0:
            raise ValueError("schedule interval must be positive")
        return self.store.put_schedule(schedule)

    def tick(self, now: float) -> list[Job]:
        created: list[Job] = []
        schedules = []
        existing_ids = {job.id for job in self.store.list_jobs()}
        for schedule in self.store.list_schedules():
            if not schedule.enabled:
                schedules.append(schedule)
                continue
            due = schedule.last_run_at is None or now - schedule.last_run_at >= schedule.every_seconds
            if not due:
                schedules.append(schedule)
                continue
            job_id = f"schedule-{schedule.id}-{int(now)}"
            if job_id not in existing_ids:
                job = Job(
                    id=job_id,
                    entrypoint=schedule.entrypoint,
                    payload=schedule.payload,
                    created_at=now,
                    updated_at=now,
                    execute_after=now,
                    metadata={"schedule_id": schedule.id},
                )
                self.store.put_job(job)
                created.append(job)
            schedules.append(replace(schedule, last_run_at=now, heartbeat=now))
        self.store.replace_schedules(schedules)
        return created
