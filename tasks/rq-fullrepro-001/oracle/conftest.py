"""Shared fixtures, helpers, and constants for rq-fullrepro-001 oracle tests."""

from __future__ import annotations

import subprocess
import sys

import pytest
from fakeredis import FakeRedis

from rq import Queue, Retry, SimpleWorker, get_current_job

QUEUE_ALPHA = "alpha-queue"
QUEUE_BETA = "beta-queue"
QUEUE_REPORTS = "reports-queue"


def multiply(a: int, b: int) -> int:
    return a * b


def format_greeting(name: str = "Guest") -> str:
    return f"Hello, {name}!"


def echo_payload(*args, **kwargs):
    return list(args), dict(kwargs)


def raise_runtime_failure() -> None:
    raise RuntimeError("oracle failure marker")


def capture_running_job_id() -> str:
    job = get_current_job()
    return job.id


def read_meta_color(key: str) -> str:
    return get_current_job().meta[key]


def request_function_retry():
    return Retry(max=1)


def started_registry_snapshot() -> dict[str, object]:
    from rq.registry import StartedJobRegistry

    job = get_current_job()
    queue = Queue(job.origin, connection=job.connection)
    return {
        "status": job.get_status().value,
        "in_started": job in StartedJobRegistry(queue=queue),
    }


def capture_worker_registration() -> dict[str, object]:
    """Return the monitoring view of workers observed from inside a running job."""
    from rq import Worker

    connection = get_current_job().connection
    return {
        "count": Worker.count(connection=connection),
        "names": [worker.name for worker in Worker.all(connection=connection)],
    }


@pytest.fixture
def connection():
    """Provide an isolated Redis-compatible connection for each test."""
    conn = FakeRedis()
    yield conn
    conn.flushdb()


@pytest.fixture
def queue(connection):
    """Default named queue bound to the test connection."""
    return Queue(QUEUE_ALPHA, connection=connection)


def make_queue(connection, name: str = QUEUE_ALPHA, **kwargs) -> Queue:
    return Queue(name, connection=connection, **kwargs)


def work_burst(queue: Queue, connection, *, max_jobs: int | None = None, serializer=None) -> bool:
    worker_kwargs = {"connection": connection}
    if serializer is not None:
        worker_kwargs["serializer"] = serializer
    worker = SimpleWorker([queue], **worker_kwargs)
    work_kwargs = {"burst": True, "logging_level": "WARNING"}
    if max_jobs is not None:
        work_kwargs["max_jobs"] = max_jobs
    return worker.work(**work_kwargs)


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "rq.cli", *args],
        check=False,
        text=True,
        capture_output=True,
    )

