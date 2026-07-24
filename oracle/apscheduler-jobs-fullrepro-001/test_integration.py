# Spec2Repo oracle - integration tests for apscheduler-jobs-fullrepro-001
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

def test_sync_scheduler_context_variable_is_set_inside_context():
    with Scheduler(identity="sync-context") as scheduler:
        assert current_scheduler.get() is scheduler

def test_configure_task_creates_task_and_task_added_event():
    with Scheduler() as scheduler:
        queue: Queue = Queue()
        scheduler.subscribe(queue.put_nowait)
        task_obj = scheduler.configure_task("alpha", func=return_value, metadata={"a": 1})
        assert task_obj.id == "alpha"
        assert task_obj.func.endswith(":return_value")
        assert task_obj.metadata == {"a": 1}
        assert scheduler.get_tasks()[0].id == "alpha"
        event = queue.get(timeout=1)
        assert isinstance(event, TaskAdded)
        assert event.task_id == "alpha"

def test_configure_task_updates_existing_task_and_emits_update():
    with Scheduler() as scheduler:
        queue: Queue = Queue()
        scheduler.subscribe(queue.put_nowait)
        scheduler.configure_task("alpha", func=return_value)
        scheduler.configure_task("alpha", misfire_grace_time=2)
        events = [queue.get(timeout=1), queue.get(timeout=1)]
        assert isinstance(events[0], TaskAdded)
        assert isinstance(events[1], TaskUpdated)
        task_obj = scheduler.get_tasks()[0]
        assert task_obj.misfire_grace_time == timedelta(seconds=2)

def test_add_schedule_returns_supplied_id_and_stores_schedule():
    run_time = datetime.now(timezone.utc) + timedelta(hours=1)
    with Scheduler() as scheduler:
        schedule_id = scheduler.add_schedule(return_value, DateTrigger(run_time), id="once")
        schedule = scheduler.get_schedule(schedule_id)
        assert schedule_id == "once"
        assert schedule.id == "once"
        assert schedule.next_fire_time == run_time
        assert schedule.task_id.endswith(":return_value")

def test_schedule_added_event_contains_schedule_and_task_identity():
    run_time = datetime.now(timezone.utc) + timedelta(hours=1)
    with Scheduler() as scheduler:
        queue: Queue = Queue()
        scheduler.subscribe(queue.put_nowait)
        scheduler.add_schedule(return_value, DateTrigger(run_time), id="once")
        events = [queue.get(timeout=1), queue.get(timeout=1)]
        assert isinstance(events[0], TaskAdded)
        assert isinstance(events[1], ScheduleAdded)
        assert events[1].schedule_id == "once"
        assert events[1].next_fire_time == run_time

def test_remove_schedule_removes_view_and_emits_event():
    run_time = datetime.now(timezone.utc) + timedelta(hours=1)
    with Scheduler() as scheduler:
        queue: Queue = Queue()
        scheduler.subscribe(queue.put_nowait)
        scheduler.add_schedule(return_value, DateTrigger(run_time), id="once")
        scheduler.remove_schedule("once")
        assert scheduler.get_schedules() == []
        events = [queue.get(timeout=1), queue.get(timeout=1), queue.get(timeout=1)]
        assert isinstance(events[-1], ScheduleRemoved)
        assert events[-1].schedule_id == "once"
        assert events[-1].finished is False

def test_pause_and_unpause_schedule_change_public_state_and_events():
    run_time = datetime.now(timezone.utc) + timedelta(hours=1)
    with Scheduler() as scheduler:
        queue: Queue = Queue()
        scheduler.subscribe(queue.put_nowait, {ScheduleUpdated})
        scheduler.add_schedule(return_value, DateTrigger(run_time), id="once")
        scheduler.pause_schedule("once")
        assert scheduler.get_schedule("once").paused is True
        scheduler.unpause_schedule("once")
        assert scheduler.get_schedule("once").paused is False
        events = [queue.get(timeout=1), queue.get(timeout=1)]
        assert all(isinstance(event, ScheduleUpdated) for event in events)

def test_unpause_resume_from_advances_interval_schedule():
    start = datetime.now(timezone.utc) - timedelta(minutes=5)
    resume_from = datetime.now(timezone.utc) + timedelta(minutes=1)
    with Scheduler() as scheduler:
        scheduler.add_schedule(
            return_value,
            IntervalTrigger(minutes=1, start_time=start),
            id="interval",
            paused=True,
        )
        scheduler.unpause_schedule("interval", resume_from=resume_from)
        assert scheduler.get_schedule("interval").next_fire_time >= resume_from

def test_paused_due_schedule_does_not_create_job_until_unpaused():
    event = threading.Event()
    with Scheduler(role=SchedulerRole.both) as scheduler:
        scheduler.add_schedule(event.set, DateTrigger(datetime.now(timezone.utc)), id="once", paused=True)
        scheduler.start_in_background()
        assert not event.wait(0.2)
        scheduler.unpause_schedule("once")
        assert event.wait(3)

def test_scheduler_role_scheduler_processes_schedule_without_running_job():
    event = threading.Event()
    with Scheduler(role=SchedulerRole.scheduler) as scheduler:
        scheduler.add_schedule(event.set, DateTrigger(datetime.now(timezone.utc)), id="once")
        scheduler.start_in_background()
        time.sleep(0.4)
        assert scheduler.get_jobs()
        assert not event.is_set()

def test_scheduler_role_worker_runs_existing_direct_job():
    with Scheduler(role=SchedulerRole.worker) as scheduler:
        job_id = scheduler.add_job(return_value, args=["done"], result_expiration_time=10)
        scheduler.start_in_background()
        result = scheduler.get_job_result(job_id)
        assert result.return_value == "done"

def test_add_job_publishes_job_added_event():
    with Scheduler() as scheduler:
        queue: Queue = Queue()
        scheduler.subscribe(queue.put_nowait, {JobAdded})
        job_id = scheduler.add_job(return_value)
        event = queue.get(timeout=1)
        assert event.job_id == job_id
        assert event.schedule_id is None

def test_run_job_returns_callable_value():
    with Scheduler() as scheduler:
        scheduler.start_in_background()
        assert scheduler.run_job(add_values, args=[2, 5]) == 7

def test_run_job_reraises_callable_exception():
    with Scheduler() as scheduler:
        scheduler.start_in_background()
        with pytest.raises(ValueError):
            scheduler.run_job(raise_value_error)

def test_successful_job_result_is_consumed_after_retrieval():
    with Scheduler() as scheduler:
        job_id = scheduler.add_job(return_value, args=["stored"], result_expiration_time=10)
        scheduler.start_in_background()
        result = scheduler.get_job_result(job_id)
        assert result.return_value == "stored"
        with pytest.raises(JobLookupError):
            scheduler.get_job_result(job_id, wait=False)

def test_job_events_are_emitted_in_lifecycle_order():
    with Scheduler() as scheduler:
        queue: Queue = Queue()
        scheduler.subscribe(queue.put_nowait, {JobAdded, JobAcquired, JobReleased})
        job_id = scheduler.add_job(return_value, result_expiration_time=10)
        scheduler.start_in_background()
        result = scheduler.get_job_result(job_id)
        events = [queue.get(timeout=1), queue.get(timeout=1), queue.get(timeout=1)]
        assert [type(event) for event in events] == [JobAdded, JobAcquired, JobReleased]
        assert events[0].job_id == events[1].job_id == events[2].job_id == result.job_id
        assert events[2].outcome is JobOutcome.success

def test_current_job_context_variable_identifies_running_job():
    with Scheduler() as scheduler:
        job_id = scheduler.add_job(current_job_id, result_expiration_time=10)
        scheduler.start_in_background()
        result = scheduler.get_job_result(job_id)
        assert result.return_value == job_id

def test_current_scheduler_context_variable_visible_to_sync_job():
    with Scheduler(identity="ctx-sync") as scheduler:
        job_id = scheduler.add_job(current_scheduler_identity, result_expiration_time=10)
        scheduler.start_in_background()
        assert scheduler.get_job_result(job_id).return_value == "ctx-sync"

def test_threadpool_executor_runs_sync_job_off_calling_thread():
    with Scheduler() as scheduler:
        scheduler.start_in_background()
        worker_thread_id = scheduler.run_job(threading.get_ident, job_executor="threadpool")
        assert worker_thread_id != threading.get_ident()

def test_async_scheduler_async_executor_runs_on_event_loop(anyio_backend):
    async def main():
        async with AsyncScheduler() as scheduler:
            await scheduler.start_in_background()
            event_loop_thread = threading.get_ident()
            returned_thread = await scheduler.run_job(async_return_thread_id, job_executor="async")
            assert returned_thread == event_loop_thread

    import anyio

    anyio.run(main)

def test_async_scheduler_context_variable_visible_to_async_job(anyio_backend):
    async def main():
        async with AsyncScheduler(identity="async-job-context") as scheduler:
            await scheduler.start_in_background()
            assert await scheduler.run_job(async_context_identity, job_executor="async") == "async-job-context"

    import anyio

    anyio.run(main)

def test_scheduler_start_and_stop_publish_lifecycle_events():
    with Scheduler() as scheduler:
        queue: Queue = Queue()
        scheduler.subscribe(queue.put_nowait, {SchedulerStarted, SchedulerStopped})
        scheduler.start_in_background()
        scheduler.stop()
        scheduler.wait_until_stopped()
        events = [queue.get(timeout=1), queue.get(timeout=1)]
        assert isinstance(events[0], SchedulerStarted)
        assert isinstance(events[1], SchedulerStopped)

def test_wait_until_stopped_returns_after_stop_job():
    with Scheduler() as scheduler:
        scheduler.configure_task("stop", func=scheduler.stop)
        scheduler.add_job("stop")
        scheduler.start_in_background()
        scheduler.wait_until_stopped()
        assert True

def test_finished_schedule_removed_by_cleanup():
    event = threading.Event()
    with Scheduler(cleanup_interval=None) as scheduler:
        scheduler.add_schedule(event.set, DateTrigger(datetime.now(timezone.utc)), id="once")
        scheduler.start_in_background()
        assert event.wait(3)
        deadline = time.time() + 3
        while time.time() < deadline:
            if scheduler.get_schedule("once").next_fire_time is None and not scheduler.get_jobs():
                break
            time.sleep(0.05)
        scheduler.cleanup()
        with pytest.raises(ScheduleLookupError):
            scheduler.get_schedule("once")

def test_job_result_expiration_cleanup_removes_result():
    with Scheduler(cleanup_interval=None) as scheduler:
        job_id = scheduler.add_job(return_value, result_expiration_time=0.1)
        scheduler.start_in_background()
        result = scheduler.get_job_result(job_id)
        assert result.outcome is JobOutcome.success
        time.sleep(0.2)
        scheduler.cleanup()
        with pytest.raises(JobLookupError):
            scheduler.get_job_result(job_id, wait=False)

def test_memory_datastore_get_next_schedule_run_time_tracks_earliest():
    first = datetime.now(timezone.utc) + timedelta(hours=1)
    second = first + timedelta(hours=1)
    with Scheduler() as scheduler:
        scheduler.add_schedule(return_value, DateTrigger(second), id="second")
        scheduler.add_schedule(return_value, DateTrigger(first), id="first")
        assert scheduler.data_store
        assert scheduler.get_schedules()[0].id == "first"

def test_job_original_scheduled_time_subtracts_jitter():
    run_time = datetime.now(timezone.utc)
    with Scheduler(role=SchedulerRole.scheduler) as scheduler:
        scheduler.add_schedule(return_value, DateTrigger(run_time), id="once", max_jitter=0)
        scheduler.start_in_background()
        deadline = time.time() + 3
        while time.time() < deadline and not scheduler.get_jobs():
            time.sleep(0.05)
        job = scheduler.get_jobs()[0]
        assert job.original_scheduled_time == job.scheduled_fire_time - job.jitter

def test_local_event_broker_delivers_one_shot_only_once():
    with Scheduler() as scheduler:
        queue: Queue = Queue()
        scheduler.subscribe(queue.put_nowait, {TaskAdded}, one_shot=True)
        scheduler.configure_task("a", func=return_value)
        assert queue.get(timeout=1).task_id == "a"
        scheduler.configure_task("b", func=return_value)
        time.sleep(0.1)
        assert queue.empty()

def test_local_event_broker_filters_event_types():
    with Scheduler() as scheduler:
        queue: Queue = Queue()
        scheduler.subscribe(queue.put_nowait, {ScheduleAdded}, one_shot=True)
        scheduler.configure_task("a", func=return_value)
        scheduler.add_schedule("a", DateTrigger(datetime.now(timezone.utc) + timedelta(hours=1)), id="once")
        assert isinstance(queue.get(timeout=1), ScheduleAdded)

def test_get_next_event_returns_matching_event():
    with Scheduler() as scheduler:
        scheduler.configure_task("stop", func=scheduler.stop)
        scheduler.add_job("stop")
        scheduler.start_in_background()
        event = scheduler.get_next_event(SchedulerStopped)
        assert isinstance(event, SchedulerStopped)

def test_schedule_metadata_inherits_task_metadata_and_overrides_top_level():
    defaults = TaskDefaults(metadata={"base": "default", "shared": "default"})
    with Scheduler(task_defaults=defaults) as scheduler:
        scheduler.configure_task("meta", func=return_value, metadata={"task": "value", "shared": "task"})
        scheduler.add_schedule(
            "meta",
            DateTrigger(datetime.now(timezone.utc) + timedelta(hours=1)),
            id="meta-schedule",
            metadata={"schedule": "value", "shared": "schedule"},
        )
        schedule = scheduler.get_schedule("meta-schedule")
        assert schedule.metadata == {
            "base": "default",
            "task": "value",
            "schedule": "value",
            "shared": "schedule",
        }

def test_direct_job_metadata_inherits_task_metadata_and_overrides_top_level():
    defaults = TaskDefaults(metadata={"base": "default", "shared": "default"})
    with Scheduler(task_defaults=defaults) as scheduler:
        scheduler.configure_task("meta", func=return_value, metadata={"task": "value", "shared": "task"})
        scheduler.add_job("meta", metadata={"job": "value", "shared": "job"})
        job = scheduler.get_jobs()[0]
        assert job.metadata == {
            "base": "default",
            "task": "value",
            "job": "value",
            "shared": "job",
        }

def test_max_running_jobs_limits_second_acquisition_until_release(anyio_backend):
    async def main():
        store = MemoryDataStore()
        async with AsyncScheduler(data_store=store) as scheduler:
            await scheduler.configure_task("limited", func=return_value, max_running_jobs=1)
            await scheduler.add_job("limited")
            await scheduler.add_job("limited")
            first = await store.acquire_jobs("worker", timedelta(seconds=30), limit=2)
            assert len(first) == 1
            result = JobResult.from_job(first[0], JobOutcome.success)
            await store.release_job("worker", first[0], result)
            second = await store.acquire_jobs("worker", timedelta(seconds=30), limit=2)
            assert len(second) == 1

    import anyio

    anyio.run(main)

def test_state_model_views_agree_for_task_schedule_and_job():
    run_time = datetime.now(timezone.utc) + timedelta(hours=1)
    with Scheduler(role=SchedulerRole.scheduler) as scheduler:
        queue: Queue = Queue()
        scheduler.subscribe(queue.put_nowait)
        scheduler.configure_task("model", func=return_value, metadata={"scope": "state"})
        scheduler.add_schedule("model", DateTrigger(run_time), id="model-schedule")
        scheduler.add_job("model")
        assert scheduler.get_tasks()[0].id == "model"
        assert scheduler.get_schedule("model-schedule").task_id == "model"
        assert scheduler.get_jobs()[0].task_id == "model"
        event_names = [queue.get(timeout=1).__class__.__name__ for _ in range(3)]
        assert event_names == ["TaskAdded", "ScheduleAdded", "JobAdded"]

def test_direct_job_representative_workflow_events_and_result():
    with Scheduler() as scheduler:
        queue: Queue = Queue()
        scheduler.subscribe(queue.put_nowait, {JobAdded, JobAcquired, JobReleased})
        job_id = scheduler.add_job(add_values, args=[4, 6], result_expiration_time=10)
        assert scheduler.get_jobs()[0].id == job_id
        scheduler.start_in_background()
        result = scheduler.get_job_result(job_id)
        assert result.return_value == 10
        events = [queue.get(timeout=1), queue.get(timeout=1), queue.get(timeout=1)]
        assert [type(event) for event in events] == [JobAdded, JobAcquired, JobReleased]

def test_date_schedule_representative_workflow_pause_unpause_remove():
    run_time = datetime.now(timezone.utc) + timedelta(hours=1)
    with Scheduler() as scheduler:
        schedule_id = scheduler.add_schedule(return_value, DateTrigger(run_time), id="workflow-once")
        scheduler.pause_schedule(schedule_id)
        assert scheduler.get_schedule(schedule_id).paused is True
        scheduler.unpause_schedule(schedule_id)
        assert scheduler.get_schedule(schedule_id).paused is False
        scheduler.remove_schedule(schedule_id)
        assert scheduler.get_schedules() == []

def test_cross_view_schedule_event_matches_stored_schedule():
    run_time = datetime.now(timezone.utc) + timedelta(hours=1)
    with Scheduler() as scheduler:
        queue: Queue = Queue()
        scheduler.subscribe(queue.put_nowait, {ScheduleAdded})
        scheduler.add_schedule(return_value, DateTrigger(run_time), id="cross-view")
        event = queue.get(timeout=1)
        schedule = scheduler.get_schedule("cross-view")
        assert event.schedule_id == schedule.id
        assert event.task_id == schedule.task_id
        assert event.next_fire_time == schedule.next_fire_time


def test_cross_view_task_event_matches_configured_task():
    with Scheduler() as scheduler:
        queue: Queue = Queue()
        scheduler.subscribe(queue.put_nowait, {TaskAdded})
        task_obj = scheduler.configure_task("cross-task", func=return_value, metadata={"owner": "ops"})
        event = queue.get(timeout=1)
        stored = scheduler.get_tasks()[0]

        assert event.task_id == task_obj.id == stored.id
        assert stored.metadata == {"owner": "ops"}


def test_direct_job_workflow_is_visible_in_job_event_and_result_views():
    with Scheduler() as scheduler:
        queue: Queue = Queue()
        scheduler.subscribe(queue.put_nowait, {JobAdded, JobAcquired, JobReleased})
        job_id = scheduler.add_job(return_value, result_expiration_time=10)
        scheduler.start_in_background()
        result = scheduler.get_job_result(job_id)
        events = [queue.get(timeout=1), queue.get(timeout=1), queue.get(timeout=1)]

        assert result.return_value == "result"
        assert [type(event) for event in events] == [JobAdded, JobAcquired, JobReleased]
        assert events[-1].outcome is JobOutcome.success


def test_schedule_lifecycle_workflow_keeps_lookup_and_event_views_aligned():
    run_time = datetime.now(timezone.utc) + timedelta(hours=1)
    with Scheduler() as scheduler:
        queue: Queue = Queue()
        scheduler.subscribe(queue.put_nowait, {ScheduleAdded, ScheduleUpdated, ScheduleRemoved})
        scheduler.add_schedule(return_value, DateTrigger(run_time), id="workflow-schedule")
        scheduler.pause_schedule("workflow-schedule")
        assert scheduler.get_schedule("workflow-schedule").paused is True
        scheduler.unpause_schedule("workflow-schedule")
        assert scheduler.get_schedule("workflow-schedule").paused is False
        scheduler.remove_schedule("workflow-schedule")
        events = [queue.get(timeout=1) for _ in range(4)]

        assert [type(event) for event in events] == [
            ScheduleAdded,
            ScheduleUpdated,
            ScheduleUpdated,
            ScheduleRemoved,
        ]
