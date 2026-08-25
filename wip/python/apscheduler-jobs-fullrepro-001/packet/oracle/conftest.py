"""Shared fixtures, helpers, and constants for apscheduler oracle tests."""
from __future__ import annotations

import threading
from datetime import timedelta
from queue import Queue

from apscheduler import (
    Scheduler,
    current_async_scheduler,
    current_job,
    current_scheduler,
    task,
)


# ---------------------------------------------------------------------------
# Callable helpers used as job / schedule targets
# ---------------------------------------------------------------------------

def return_value(value="result"):
    return value


def add_values(x, y):
    return x + y


def raise_value_error():
    raise ValueError("boom")


def current_job_id():
    return current_job.get().id


def current_scheduler_identity():
    return current_scheduler.get().identity


async def async_return_thread_id():
    return threading.get_ident()


async def async_context_identity():
    return current_async_scheduler.get().identity


@task(
    id="decorated-task",
    job_executor="threadpool",
    max_running_jobs=3,
    misfire_grace_time=timedelta(seconds=6),
    metadata={"decorated": True, "shared": "decorator"},
)
def decorated_callable():
    return "decorated"


# ---------------------------------------------------------------------------
# Event / scheduler utilities
# ---------------------------------------------------------------------------

def collect_events(queue: Queue, event_types=None):
    """Drain a queue and return events, optionally filtered by type."""
    return [
        ev for ev in list(queue.queue)
        if event_types is None or isinstance(ev, event_types)
    ]


def make_queue_scheduler(**kwargs):
    """Create a Scheduler with a Queue subscribed to all events."""
    queue: Queue = Queue()
    sched = Scheduler(**kwargs)
    sched.subscribe(queue.put_nowait)
    return sched, queue
