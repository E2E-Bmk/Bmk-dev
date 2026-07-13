from __future__ import annotations

from .models import Job, Schedule
from .store import Store


class Scheduler:
    def __init__(self, store: Store) -> None:
        self.store = store

    def register(self, schedule: Schedule) -> Schedule:
        raise NotImplementedError

    def tick(self, now: float) -> list[Job]:
        raise NotImplementedError
