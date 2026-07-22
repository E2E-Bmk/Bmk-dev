# Spec2Repo oracle - atomic tests for apscheduler-jobs-fullrepro-001
from __future__ import annotations

import os

import threading

import time

from datetime import datetime, timedelta, timezone

from queue import Queue

import pytest

from apscheduler import (
    AsyncScheduler,
    CoalescePolicy,
    ConflictPolicy,
    ConflictingIdError,
    JobAcquired,
    JobAdded,
    JobDeadlineMissed,
    JobLookupError,
    JobOutcome,
    JobReleased,
    JobResult,
    JobResultNotReady,
    ScheduleAdded,
    ScheduleLookupError,
    ScheduleRemoved,
    ScheduleUpdated,
    Scheduler,
    SchedulerRole,
    SchedulerStarted,
    SchedulerStopped,
    TaskAdded,
    TaskDefaults,
    TaskLookupError,
    TaskUpdated,
    current_async_scheduler,
    current_job,
    current_scheduler,
    task,
)

from apscheduler.datastores.memory import MemoryDataStore

from apscheduler.eventbrokers.local import LocalEventBroker

from apscheduler.executors.async_ import AsyncJobExecutor

from apscheduler.executors.thread import ThreadPoolJobExecutor

from apscheduler.triggers.date import DateTrigger

from apscheduler.triggers.interval import IntervalTrigger

def return_value(value="result"):
    return value

def add_values(x, y):
    return x + y

def raise_value_error():
    raise ValueError("boom")

def current_job_id():
    return current_job.get().id

def current_scheduler_identity():
    scheduler = current_scheduler.get()
    return scheduler.identity

async def async_return_thread_id():
    return threading.get_ident()

async def async_context_identity():
    scheduler = current_async_scheduler.get()
    return scheduler.identity

@task(
    id="decorated-task",
    job_executor="threadpool",
    max_running_jobs=3,
    misfire_grace_time=timedelta(seconds=6),
    metadata={"decorated": True, "shared": "decorator"},
)
def decorated_callable():
    return "decorated"

def collect_events(queue: Queue, event_types=None):
    return [event for event in list(queue.queue) if event_types is None or isinstance(event, event_types)]

def make_queue_scheduler(**kwargs):
    queue: Queue = Queue()
    scheduler = Scheduler(**kwargs)
    scheduler.subscribe(queue.put_nowait)
    return scheduler, queue

def test_default_sync_scheduler_components_and_state():
    with Scheduler() as scheduler:
        assert isinstance(scheduler.data_store, MemoryDataStore)
        assert isinstance(scheduler.event_broker, LocalEventBroker)
        assert scheduler.role is SchedulerRole.both
        assert scheduler.max_concurrent_jobs == 100
        assert isinstance(scheduler.identity, str)
        assert scheduler.identity

def test_configure_task_merges_defaults_decorator_and_direct_metadata():
    defaults = TaskDefaults(metadata={"base": 1, "shared": "base"}, misfire_grace_time=5)
    with Scheduler(task_defaults=defaults) as scheduler:
        task_obj = scheduler.configure_task(
            decorated_callable, metadata={"direct": 3, "shared": "direct"}
        )
        assert task_obj.id == "decorated-task"
        assert task_obj.job_executor == "threadpool"
        assert task_obj.max_running_jobs == 3
        assert task_obj.misfire_grace_time == timedelta(seconds=6)
        assert task_obj.metadata == {"base": 1, "decorated": True, "direct": 3, "shared": "direct"}

def test_task_decorator_rejects_non_callable():
    with pytest.raises(ValueError):
        task()(42)

def test_task_decorator_rejects_double_decoration():
    def func():
        return None

    decorated = task()(func)
    with pytest.raises(ValueError):
        task()(decorated)

def test_configure_task_rejects_invalid_identifier_type():
    with Scheduler() as scheduler:
        with pytest.raises(TypeError):
            scheduler.configure_task(None)

def test_get_tasks_returns_sorted_by_id():
    with Scheduler() as scheduler:
        scheduler.configure_task("b", func=return_value)
        scheduler.configure_task("a", func=return_value)
        assert [task.id for task in scheduler.get_tasks()] == ["a", "b"]

def test_add_schedule_without_id_generates_string_identifier():
    run_time = datetime.now(timezone.utc) + timedelta(hours=1)
    with Scheduler() as scheduler:
        schedule_id = scheduler.add_schedule(return_value, DateTrigger(run_time))
        assert isinstance(schedule_id, str)
        assert scheduler.get_schedule(schedule_id).id == schedule_id

def test_schedule_get_missing_raises_schedule_lookup_error():
    with Scheduler() as scheduler:
        with pytest.raises(ScheduleLookupError):
            scheduler.get_schedule("missing")

def test_remove_missing_schedule_is_noop():
    with Scheduler() as scheduler:
        scheduler.remove_schedule("missing")
        assert scheduler.get_schedules() == []

def test_conflict_policy_do_nothing_preserves_existing_schedule():
    first = datetime.now(timezone.utc) + timedelta(hours=1)
    second = first + timedelta(hours=1)
    with Scheduler() as scheduler:
        scheduler.add_schedule(return_value, DateTrigger(first), id="same")
        returned = scheduler.add_schedule(
            add_values, DateTrigger(second), id="same", conflict_policy=ConflictPolicy.do_nothing
        )
        assert returned == "same"
        assert scheduler.get_schedule("same").next_fire_time == first

def test_conflict_policy_replace_updates_schedule():
    first = datetime.now(timezone.utc) + timedelta(hours=1)
    second = first + timedelta(hours=1)
    with Scheduler() as scheduler:
        scheduler.add_schedule(return_value, DateTrigger(first), id="same")
        scheduler.add_schedule(
            add_values, DateTrigger(second), id="same", conflict_policy=ConflictPolicy.replace
        )
        assert scheduler.get_schedule("same").next_fire_time == second

def test_conflict_policy_exception_raises_conflicting_id_error():
    run_time = datetime.now(timezone.utc) + timedelta(hours=1)
    with Scheduler() as scheduler:
        scheduler.add_schedule(return_value, DateTrigger(run_time), id="same")
        with pytest.raises(ConflictingIdError):
            scheduler.add_schedule(
                return_value, DateTrigger(run_time), id="same", conflict_policy=ConflictPolicy.exception
            )

def test_add_job_returns_uuid_and_job_is_visible_before_processing():
    with Scheduler() as scheduler:
        job_id = scheduler.add_job(return_value, result_expiration_time=10)
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == job_id
        assert jobs[0].schedule_id is None

def test_get_job_result_wait_false_before_run_raises_lookup_error():
    with Scheduler() as scheduler:
        job_id = scheduler.add_job(return_value, result_expiration_time=10)
        with pytest.raises(JobLookupError):
            scheduler.get_job_result(job_id, wait=False)

def test_date_trigger_fires_once_then_exhausts():
    run_time = datetime.now(timezone.utc)
    trigger = DateTrigger(run_time)
    assert trigger.next() == run_time
    assert trigger.next() is None

def test_interval_trigger_rejects_zero_interval():
    with pytest.raises(ValueError):
        IntervalTrigger()

def test_interval_trigger_rejects_end_before_start():
    start = datetime(2026, 1, 2, tzinfo=timezone.utc)
    end = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValueError):
        IntervalTrigger(days=1, start_time=start, end_time=end)

def test_interval_trigger_returns_start_then_interval_steps_until_end():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    trigger = IntervalTrigger(minutes=10, start_time=start, end_time=start + timedelta(minutes=20))
    assert trigger.next() == start
    assert trigger.next() == start + timedelta(minutes=10)
    assert trigger.next() == start + timedelta(minutes=20)
    assert trigger.next() is None

def test_memory_datastore_task_lookup_error_for_missing_task(anyio_backend):
    async def main():
        store = MemoryDataStore()
        async with AsyncScheduler(data_store=store):
            with pytest.raises(TaskLookupError):
                await store.get_task("missing")

    import anyio

    anyio.run(main)

def test_job_result_from_job_sets_expiration_from_finish_time():
    with Scheduler() as scheduler:
        job_id = scheduler.add_job(return_value, result_expiration_time=10)
        job = scheduler.get_jobs()[0]
        finished = datetime.now(timezone.utc)
        result = JobResult.from_job(job, JobOutcome.success, finished_at=finished, return_value="x")
        assert result.job_id == job_id
        assert result.expires_at == finished + timedelta(seconds=10)
        assert result.return_value == "x"

def test_job_result_not_ready_exception_is_public_constructible():
    with Scheduler() as scheduler:
        job_id = scheduler.add_job(return_value)
        exc = JobResultNotReady(job_id)
        assert isinstance(exc, Exception)
