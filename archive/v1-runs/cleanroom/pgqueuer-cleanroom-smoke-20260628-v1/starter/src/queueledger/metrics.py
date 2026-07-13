from __future__ import annotations

from .models import QueueReport
from .store import Store


def queue_report(store: Store) -> QueueReport:
    raise NotImplementedError


def metrics_snapshot(store: Store) -> dict[str, int]:
    raise NotImplementedError
