from __future__ import annotations

from .models import QueueReport
from .store import Store


def queue_report(store: Store) -> QueueReport:
    return store.queue_report()


def metrics_snapshot(store: Store) -> dict[str, int]:
    report = store.queue_report()
    return {
        "jobs.queued": report.queued,
        "jobs.picked": report.picked,
        "jobs.terminal": report.terminal,
        "jobs.total": report.queued + report.picked + report.terminal,
        **{f"entrypoint.{name}": count for name, count in sorted(report.by_entrypoint.items())},
    }
