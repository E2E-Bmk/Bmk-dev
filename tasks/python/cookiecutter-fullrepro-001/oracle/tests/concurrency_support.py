from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import os
from queue import SimpleQueue
import threading
import time
from typing import Any


WORKER_DEADLINE_SECONDS = 3.0


@dataclass(frozen=True)
class WorkerFailure:
    name: str
    exception: BaseException


def synchronized_workers(operations: Mapping[str, Callable[[], Any]]) -> dict[str, Any]:
    """Run named operations from one evaluator-owned start line and finish gate.

    Deadlines are validity guards, not behavioral observations: no assertion uses
    relative speed or completion order.  A control-only stalled worker is released
    in ``finally`` so the evaluator can prove that an incomplete implementation
    becomes a bounded call-phase failure rather than a scorer timeout.
    """

    if len(operations) < 2 or len(set(operations)) != len(operations):
        raise AssertionError("concurrency roots require distinct named operations")

    start = threading.Barrier(len(operations) + 1)
    finish = threading.Barrier(len(operations) + 1)
    stalled_worker_release = threading.Event()
    results: SimpleQueue[tuple[str, Any]] = SimpleQueue()
    failures: SimpleQueue[WorkerFailure] = SimpleQueue()
    threads: list[threading.Thread] = []
    deadlines: dict[str, float] = {}
    timed_out = False
    control = os.environ.get("COOKIECUTTER_EVALUATOR_CONCURRENCY_CONTROL", "")
    stalled_name = next(iter(operations)) if control == "stall-first-worker" else None

    def worker(name: str, operation: Callable[[], Any]) -> None:
        try:
            start.wait(timeout=WORKER_DEADLINE_SECONDS)
            if name == stalled_name:
                stalled_worker_release.wait()
            results.put((name, operation()))
        except BaseException as exc:
            failures.put(WorkerFailure(name, exc))
        finally:
            try:
                finish.wait(timeout=WORKER_DEADLINE_SECONDS)
            except threading.BrokenBarrierError:
                pass

    for name, operation in operations.items():
        thread = threading.Thread(
            target=worker,
            args=(name, operation),
            name=f"evaluator-{name}",
            daemon=True,
        )
        threads.append(thread)
        thread.start()

    try:
        start.wait(timeout=WORKER_DEADLINE_SECONDS)
        released = time.monotonic()
        deadlines = {thread.name: released + WORKER_DEADLINE_SECONDS for thread in threads}
        try:
            finish.wait(timeout=WORKER_DEADLINE_SECONDS)
        except threading.BrokenBarrierError:
            timed_out = True
    except threading.BrokenBarrierError:
        timed_out = True
    finally:
        stalled_worker_release.set()
        start.abort()
        finish.abort()
        fallback = time.monotonic() + WORKER_DEADLINE_SECONDS
        for thread in threads:
            remaining = max(0.0, deadlines.get(thread.name, fallback) - time.monotonic())
            thread.join(timeout=remaining)

    live = [thread.name for thread in threads if thread.is_alive()]
    captured_failures: list[WorkerFailure] = []
    while not failures.empty():
        captured_failures.append(failures.get())
    captured_results: dict[str, Any] = {}
    while not results.empty():
        name, value = results.get()
        captured_results[name] = value

    if timed_out or live:
        raise AssertionError(f"workers did not complete at the evaluator finish gate: {live}")
    if captured_failures:
        summary = ", ".join(
            f"{failure.name}:{type(failure.exception).__name__}"
            for failure in captured_failures
        )
        raise AssertionError(f"worker operations failed: {summary}") from captured_failures[0].exception
    if set(captured_results) != set(operations):
        raise AssertionError("worker completion set is incomplete")
    return captured_results
