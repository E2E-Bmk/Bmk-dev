"""Integration tests for apscheduler-jobs-fullrepro-001.

Each test crosses ≥2 public API boundaries and verifies the "seam" between
cooperating components (state consistency, protocol handoff, error
propagation, configuration interaction, or lifecycle crossing).
"""
from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta, timezone
from queue import Queue

import anyio
import pytest

from apscheduler import (
    AsyncScheduler,
    JobAcquired,
    JobAdded,
    JobLookupError,
    JobOutcome,
    JobReleased,
    JobResult,
    RunState,
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
    TaskUpdated,
)
from apscheduler.datastores.memory import MemoryDataStore
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from conftest import (
    add_values,
    async_context_identity,
    async_return_thread_id,
    current_job_id,
    current_scheduler_identity,
    raise_value_error,
    return_value,
)


# ── Context Variables ───────────────────────────────────────────────────


@pytest.mark.depends_on("test_scheduler_defaults_memory_store_local_broker_both_role")
def test_sync_scheduler_context_variable_is_set_inside_context():
    """Seam: protocol handoff — integration path for sync scheduler context variable is set inside context across cooperating public APIs."""
    from apscheduler import current_scheduler

    with Scheduler(identity="sync-ctx-test") as sched:
        assert current_scheduler.get() is sched


# ── Task → Event ────────────────────────────────────────────────────────


@pytest.mark.depends_on("test_configure_task_creates_task_with_default_executor")
def test_configure_task_creates_task_and_emits_task_added_event():
    """Seam: config interaction — integration path for configure task creates task and emits task added event across cooperating public APIs."""
    with Scheduler() as sched:
        queue: Queue = Queue()
        sched.subscribe(queue.put_nowait)
        t = sched.configure_task(
            "alpha-task", func=return_value, metadata={"a": 1},
        )
        assert t.id == "alpha-task"
        assert t.func.endswith(":return_value")
        assert t.metadata == {"a": 1}
        assert sched.get_tasks()[0].id == "alpha-task"
        event = queue.get(timeout=1)
        assert isinstance(event, TaskAdded)
        assert event.task_id == "alpha-task"


@pytest.mark.depends_on("test_configure_task_creates_task_with_default_executor")
def test_configure_task_updates_existing_and_emits_task_updated_event():
    """Seam: config interaction — integration path for configure task updates existing and emits task updated event across cooperating public APIs."""
    with Scheduler() as sched:
        queue: Queue = Queue()
        sched.subscribe(queue.put_nowait)
        sched.configure_task("alpha-task", func=return_value)
        sched.configure_task("alpha-task", misfire_grace_time=2)
        events = [queue.get(timeout=1), queue.get(timeout=1)]
        assert isinstance(events[0], TaskAdded)
        assert isinstance(events[1], TaskUpdated)
        t = sched.get_tasks()[0]
        assert t.misfire_grace_time == timedelta(seconds=2)


# ── Schedule → Event + State ───────────────────────────────────────────


@pytest.mark.depends_on("test_add_schedule_returns_explicit_id_and_preserves_args")
def test_add_schedule_stores_with_correct_task_reference():
    """Seam: protocol handoff — integration path for add schedule stores with correct task reference across cooperating public APIs."""
    run_time = datetime.now(timezone.utc) + timedelta(hours=2)
    with Scheduler() as sched:
        sid = sched.add_schedule(
            return_value, DateTrigger(run_time), id="ref-sched",
        )
        s = sched.get_schedule(sid)
        assert sid == "ref-sched"
        assert s.id == "ref-sched"
        assert s.next_fire_time == run_time
        assert s.task_id.endswith(":return_value")


@pytest.mark.depends_on("test_add_schedule_returns_explicit_id_and_preserves_args")
def test_schedule_added_event_contains_identity_and_fire_time():
    """Seam: protocol handoff — integration path for schedule added event contains identity and fire time across cooperating public APIs."""
    run_time = datetime.now(timezone.utc) + timedelta(hours=2)
    with Scheduler() as sched:
        queue: Queue = Queue()
        sched.subscribe(queue.put_nowait)
        sched.add_schedule(
            return_value, DateTrigger(run_time), id="evt-sched",
        )
        events = [queue.get(timeout=1), queue.get(timeout=1)]
        assert isinstance(events[0], TaskAdded)
        assert isinstance(events[1], ScheduleAdded)
        assert events[1].schedule_id == "evt-sched"
        assert events[1].next_fire_time == run_time


@pytest.mark.depends_on("test_remove_schedule_removes_only_matching_entry")
def test_remove_schedule_removes_view_and_emits_schedule_removed():
    """Seam: lifecycle crossing — integration path for remove schedule removes view and emits schedule removed across cooperating public APIs."""
    run_time = datetime.now(timezone.utc) + timedelta(hours=2)
    with Scheduler() as sched:
        queue: Queue = Queue()
        sched.subscribe(queue.put_nowait)
        sched.add_schedule(
            return_value, DateTrigger(run_time), id="rm-sched",
        )
        sched.remove_schedule("rm-sched")
        assert sched.get_schedules() == []
        events = [queue.get(timeout=1), queue.get(timeout=1), queue.get(timeout=1)]
        assert isinstance(events[-1], ScheduleRemoved)
        assert events[-1].schedule_id == "rm-sched"
        assert events[-1].finished is False


@pytest.mark.depends_on("test_pause_and_unpause_schedule_round_trip")
def test_pause_and_unpause_schedule_update_state_and_emit_events():
    """Seam: lifecycle crossing — integration path for pause and unpause schedule update state and emit events across cooperating public APIs."""
    run_time = datetime.now(timezone.utc) + timedelta(hours=2)
    with Scheduler() as sched:
        queue: Queue = Queue()
        sched.subscribe(queue.put_nowait, {ScheduleUpdated})
        sched.add_schedule(
            return_value, DateTrigger(run_time), id="toggle-evt",
        )
        sched.pause_schedule("toggle-evt")
        assert sched.get_schedule("toggle-evt").paused is True
        sched.unpause_schedule("toggle-evt")
        assert sched.get_schedule("toggle-evt").paused is False
        events = [queue.get(timeout=1), queue.get(timeout=1)]
        assert all(isinstance(e, ScheduleUpdated) for e in events)


# ── Unpause with resume_from ───────────────────────────────────────────


@pytest.mark.depends_on("test_interval_trigger_steps_from_start_through_end")
def test_unpause_resume_from_advances_interval_schedule():
    """Seam: lifecycle crossing — integration path for unpause resume from advances interval schedule across cooperating public APIs."""
    start = datetime.now(timezone.utc) - timedelta(minutes=5)
    resume_from = datetime.now(timezone.utc) + timedelta(minutes=1)
    with Scheduler() as sched:
        sched.add_schedule(
            return_value,
            IntervalTrigger(minutes=1, start_time=start),
            id="interval-resume",
            paused=True,
        )
        sched.unpause_schedule("interval-resume", resume_from=resume_from)
        assert sched.get_schedule("interval-resume").next_fire_time >= resume_from


# ── Paused Schedule Behavior ───────────────────────────────────────────


@pytest.mark.depends_on("test_schedule_paused_defaults_to_false")
def test_paused_schedule_does_not_create_job_until_unpaused():
    """Seam: lifecycle crossing — integration path for paused schedule does not create job until unpaused across cooperating public APIs."""
    flag = threading.Event()
    with Scheduler(role=SchedulerRole.both) as sched:
        sched.add_schedule(
            flag.set, DateTrigger(datetime.now(timezone.utc)),
            id="paused-sched", paused=True,
        )
        sched.start_in_background()
        assert not flag.wait(0.2)
        sched.unpause_schedule("paused-sched")
        assert flag.wait(3)


# ── Scheduler Roles ─────────────────────────────────────────────────────


@pytest.mark.depends_on("test_scheduler_role_enum_has_documented_members")
def test_scheduler_role_scheduler_processes_schedule_without_executing():
    """Seam: lifecycle crossing — integration path for scheduler role scheduler processes schedule without executing across cooperating public APIs."""
    flag = threading.Event()
    with Scheduler(role=SchedulerRole.scheduler) as sched:
        sched.add_schedule(
            flag.set, DateTrigger(datetime.now(timezone.utc)),
            id="sched-only",
        )
        sched.start_in_background()
        time.sleep(0.4)
        assert sched.get_jobs()
        assert not flag.is_set()


@pytest.mark.depends_on("test_scheduler_role_enum_has_documented_members")
def test_scheduler_role_worker_runs_queued_direct_job():
    """Seam: lifecycle crossing — integration path for scheduler role worker runs queued direct job across cooperating public APIs."""
    with Scheduler(role=SchedulerRole.worker) as sched:
        jid = sched.add_job(
            return_value, args=["done"], result_expiration_time=15,
        )
        sched.start_in_background()
        result = sched.get_job_result(jid)
        assert result.return_value == "done"


# ── Job Events ──────────────────────────────────────────────────────────


@pytest.mark.depends_on("test_add_job_returns_uuid_and_visible_before_processing")
def test_add_job_publishes_job_added_with_null_schedule_id():
    """Seam: protocol handoff — integration path for add job publishes job added with null schedule id across cooperating public APIs."""
    with Scheduler() as sched:
        queue: Queue = Queue()
        sched.subscribe(queue.put_nowait, {JobAdded})
        jid = sched.add_job(return_value)
        event = queue.get(timeout=1)
        assert event.job_id == jid
        assert event.schedule_id is None


@pytest.mark.depends_on("test_job_outcome_enum_has_documented_members")
def test_job_events_emitted_in_lifecycle_order():
    """Seam: lifecycle crossing — integration path for job events emitted in lifecycle order across cooperating public APIs."""
    with Scheduler() as sched:
        queue: Queue = Queue()
        sched.subscribe(queue.put_nowait, {JobAdded, JobAcquired, JobReleased})
        jid = sched.add_job(return_value, result_expiration_time=15)
        sched.start_in_background()
        result = sched.get_job_result(jid)
        events = [queue.get(timeout=1), queue.get(timeout=1), queue.get(timeout=1)]
        assert [type(e) for e in events] == [JobAdded, JobAcquired, JobReleased]
        assert events[0].job_id == events[1].job_id == events[2].job_id == result.job_id
        assert events[2].outcome is JobOutcome.success


# ── run_job ─────────────────────────────────────────────────────────────


@pytest.mark.depends_on("test_job_attributes_args_kwargs_executor_expiration")
def test_run_job_returns_callable_return_value():
    """Seam: lifecycle crossing — integration path for run job returns callable return value across cooperating public APIs."""
    with Scheduler() as sched:
        sched.start_in_background()
        assert sched.run_job(add_values, args=[4, 9]) == 13


@pytest.mark.depends_on("test_job_attributes_args_kwargs_executor_expiration")
def test_run_job_reraises_callable_exception():
    """Seam: error propagation — integration path for run job reraises callable exception across cooperating public APIs."""
    with Scheduler() as sched:
        sched.start_in_background()
        with pytest.raises(ValueError):
            sched.run_job(raise_value_error)


# ── Job Result Consumption ──────────────────────────────────────────────


@pytest.mark.depends_on("test_job_result_from_job_sets_id_and_expiration")
def test_successful_job_result_consumed_on_second_retrieval():
    """Seam: error propagation — integration path for successful job result consumed on second retrieval across cooperating public APIs."""
    with Scheduler() as sched:
        jid = sched.add_job(
            return_value, args=["stored"], result_expiration_time=15,
        )
        sched.start_in_background()
        result = sched.get_job_result(jid)
        assert result.return_value == "stored"
        with pytest.raises(JobLookupError):
            sched.get_job_result(jid, wait=False)


@pytest.mark.depends_on("test_job_result_from_job_sets_id_and_expiration")
def test_error_job_result_reraises_original_exception():
    """Seam: error propagation — integration path for error job result reraises original exception across cooperating public APIs."""
    with Scheduler() as sched:
        jid = sched.add_job(raise_value_error, result_expiration_time=15)
        sched.start_in_background()
        with pytest.raises(ValueError):
            sched.get_job_result(jid)


# ── Context Variables Inside Jobs ───────────────────────────────────────


@pytest.mark.depends_on("test_add_job_returns_uuid_and_visible_before_processing")
def test_current_job_context_variable_identifies_running_job():
    """Seam: lifecycle crossing — integration path for current job context variable identifies running job across cooperating public APIs."""
    with Scheduler() as sched:
        jid = sched.add_job(current_job_id, result_expiration_time=15)
        sched.start_in_background()
        result = sched.get_job_result(jid)
        assert result.return_value == jid


@pytest.mark.depends_on("test_scheduler_defaults_memory_store_local_broker_both_role")
def test_current_scheduler_context_variable_visible_to_sync_job():
    """Seam: lifecycle crossing — integration path for current scheduler context variable visible to sync job across cooperating public APIs."""
    with Scheduler(identity="ctx-sync-id") as sched:
        jid = sched.add_job(
            current_scheduler_identity, result_expiration_time=15,
        )
        sched.start_in_background()
        assert sched.get_job_result(jid).return_value == "ctx-sync-id"


# ── Executors ───────────────────────────────────────────────────────────


def test_threadpool_executor_runs_job_on_separate_thread():
    """Seam: lifecycle crossing — integration path for threadpool executor runs job on separate thread across cooperating public APIs."""
    with Scheduler() as sched:
        sched.start_in_background()
        worker_tid = sched.run_job(
            threading.get_ident, job_executor="threadpool",
        )
        assert worker_tid != threading.get_ident()


def test_async_executor_runs_on_event_loop_thread():
    """Seam: lifecycle crossing — integration path for async executor runs on event loop thread across cooperating public APIs."""
    async def _run():
        async with AsyncScheduler() as sched:
            await sched.start_in_background()
            loop_thread = threading.get_ident()
            returned = await sched.run_job(
                async_return_thread_id, job_executor="async",
            )
            assert returned == loop_thread

    anyio.run(_run)


def test_async_scheduler_context_variable_visible_to_async_job():
    """Seam: lifecycle crossing — integration path for async scheduler context variable visible to async job across cooperating public APIs."""
    async def _run():
        async with AsyncScheduler(identity="async-ctx-id") as sched:
            await sched.start_in_background()
            result = await sched.run_job(
                async_context_identity, job_executor="async",
            )
            assert result == "async-ctx-id"

    anyio.run(_run)


# ── Scheduler Lifecycle ─────────────────────────────────────────────────


@pytest.mark.depends_on("test_run_state_enum_has_documented_members")
def test_scheduler_start_and_stop_publish_lifecycle_events():
    """Seam: lifecycle crossing — integration path for scheduler start and stop publish lifecycle events across cooperating public APIs."""
    with Scheduler() as sched:
        queue: Queue = Queue()
        sched.subscribe(queue.put_nowait, {SchedulerStarted, SchedulerStopped})
        sched.start_in_background()
        sched.stop()
        sched.wait_until_stopped()
        events = [queue.get(timeout=1), queue.get(timeout=1)]
        assert isinstance(events[0], SchedulerStarted)
        assert isinstance(events[1], SchedulerStopped)
        assert sched.state is RunState.stopped


@pytest.mark.depends_on("test_run_state_enum_has_documented_members")
def test_wait_until_stopped_reaches_stopped_state():
    """Seam: config interaction — integration path for wait until stopped reaches stopped state across cooperating public APIs."""
    with Scheduler() as sched:
        sched.configure_task("stopper", func=sched.stop)
        sched.add_job("stopper")
        sched.start_in_background()
        sched.wait_until_stopped()
        assert sched.state is RunState.stopped


# ── Cleanup ─────────────────────────────────────────────────────────────


@pytest.mark.depends_on("test_date_trigger_fires_once_then_exhausts")
def test_finished_schedule_removed_by_cleanup():
    """Seam: error propagation — integration path for finished schedule removed by cleanup across cooperating public APIs."""
    flag = threading.Event()
    with Scheduler(cleanup_interval=None) as sched:
        sched.add_schedule(
            flag.set, DateTrigger(datetime.now(timezone.utc)),
            id="cleanup-sched",
        )
        sched.start_in_background()
        assert flag.wait(3)
        deadline = time.time() + 3
        while time.time() < deadline:
            try:
                s = sched.get_schedule("cleanup-sched")
                if s.next_fire_time is None and not sched.get_jobs():
                    break
            except Exception:
                break
            time.sleep(0.05)
        sched.cleanup()
        with pytest.raises(ScheduleLookupError):
            sched.get_schedule("cleanup-sched")


def test_expired_job_result_removed_by_cleanup():
    """Seam: error propagation — integration path for expired job result removed by cleanup across cooperating public APIs."""
    with Scheduler(cleanup_interval=None) as sched:
        jid = sched.add_job(return_value, result_expiration_time=0.1)
        sched.start_in_background()
        result = sched.get_job_result(jid)
        assert result.outcome is JobOutcome.success
        time.sleep(0.2)
        sched.cleanup()
        with pytest.raises(JobLookupError):
            sched.get_job_result(jid, wait=False)


# ── Schedule Ordering ──────────────────────────────────────────────────


def test_get_schedules_ordering_tracks_earliest_fire_time():
    """Seam: protocol handoff — integration path for get schedules ordering tracks earliest fire time across cooperating public APIs."""
    first = datetime.now(timezone.utc) + timedelta(hours=2)
    second = first + timedelta(hours=1)
    with Scheduler() as sched:
        sched.add_schedule(
            return_value, DateTrigger(second), id="second-sched",
        )
        sched.add_schedule(
            return_value, DateTrigger(first), id="first-sched",
        )
        assert sched.get_schedules()[0].id == "first-sched"


# ── Job Original Scheduled Time ────────────────────────────────────────


def test_job_original_scheduled_time_equals_fire_time_minus_jitter():
    """Seam: lifecycle crossing — integration path for job original scheduled time equals fire time minus jitter across cooperating public APIs."""
    run_time = datetime.now(timezone.utc)
    with Scheduler(role=SchedulerRole.scheduler) as sched:
        sched.add_schedule(
            return_value, DateTrigger(run_time),
            id="jitter-sched", max_jitter=0,
        )
        sched.start_in_background()
        deadline = time.time() + 3
        while time.time() < deadline and not sched.get_jobs():
            time.sleep(0.05)
        job = sched.get_jobs()[0]
        assert job.original_scheduled_time == job.scheduled_fire_time - job.jitter


# ── Subscription Behavior ──────────────────────────────────────────────


def test_one_shot_subscription_delivers_only_first_event():
    """Seam: config interaction — integration path for one shot subscription delivers only first event across cooperating public APIs."""
    with Scheduler() as sched:
        queue: Queue = Queue()
        sched.subscribe(queue.put_nowait, {TaskAdded}, one_shot=True)
        sched.configure_task("first-os", func=return_value)
        assert queue.get(timeout=1).task_id == "first-os"
        sched.configure_task("second-os", func=return_value)
        time.sleep(0.1)
        assert queue.empty()


def test_event_type_filter_limits_delivery():
    """Seam: config interaction — integration path for event type filter limits delivery across cooperating public APIs."""
    with Scheduler() as sched:
        queue: Queue = Queue()
        sched.subscribe(queue.put_nowait, {ScheduleAdded}, one_shot=True)
        sched.configure_task("filter-task", func=return_value)
        sched.add_schedule(
            "filter-task",
            DateTrigger(datetime.now(timezone.utc) + timedelta(hours=2)),
            id="filter-sched",
        )
        event = queue.get(timeout=1)
        assert isinstance(event, ScheduleAdded)
        assert event.schedule_id == "filter-sched"


def test_subscription_unsubscribe_stops_further_delivery():
    """Seam: config interaction — integration path for subscription unsubscribe stops further delivery across cooperating public APIs."""
    with Scheduler() as sched:
        events = []
        sub = sched.subscribe(events.append, {TaskAdded})
        sched.configure_task("before-unsub", func=return_value)
        time.sleep(0.05)
        sub.unsubscribe()
        sched.configure_task("after-unsub", func=return_value)
        time.sleep(0.1)
        task_ids = [e.task_id for e in events if isinstance(e, TaskAdded)]
        assert "before-unsub" in task_ids
        assert "after-unsub" not in task_ids


# ── Metadata Inheritance ───────────────────────────────────────────────


def test_schedule_metadata_inherits_and_overrides_task_metadata():
    """Seam: config interaction — integration path for schedule metadata inherits and overrides task metadata across cooperating public APIs."""
    defaults = TaskDefaults(
        metadata={"base": "default", "shared": "default"},
    )
    with Scheduler(task_defaults=defaults) as sched:
        sched.configure_task(
            "meta-task", func=return_value,
            metadata={"task": "value", "shared": "task"},
        )
        sched.add_schedule(
            "meta-task",
            DateTrigger(datetime.now(timezone.utc) + timedelta(hours=2)),
            id="meta-schedule",
            metadata={"schedule": "value", "shared": "schedule"},
        )
        s = sched.get_schedule("meta-schedule")
        assert s.metadata == {
            "base": "default",
            "task": "value",
            "schedule": "value",
            "shared": "schedule",
        }


def test_direct_job_metadata_inherits_and_overrides_task_metadata():
    """Seam: config interaction — integration path for direct job metadata inherits and overrides task metadata across cooperating public APIs."""
    defaults = TaskDefaults(
        metadata={"base": "default", "shared": "default"},
    )
    with Scheduler(task_defaults=defaults) as sched:
        sched.configure_task(
            "meta-task", func=return_value,
            metadata={"task": "value", "shared": "task"},
        )
        sched.add_job(
            "meta-task", metadata={"job": "value", "shared": "job"},
        )
        job = sched.get_jobs()[0]
        assert job.metadata == {
            "base": "default",
            "task": "value",
            "job": "value",
            "shared": "job",
        }


# ── Max Running Jobs ───────────────────────────────────────────────────


def test_max_running_jobs_limits_concurrent_acquisition():
    """Seam: config interaction — integration path for max running jobs limits concurrent acquisition across cooperating public APIs."""
    async def _run():
        store = MemoryDataStore()
        async with AsyncScheduler(data_store=store) as sched:
            await sched.configure_task(
                "limited", func=return_value, max_running_jobs=1,
            )
            await sched.add_job("limited")
            await sched.add_job("limited")
            first = await store.acquire_jobs(
                "worker", timedelta(seconds=30), limit=2,
            )
            assert len(first) == 1
            result = JobResult.from_job(first[0], JobOutcome.success)
            await store.release_job("worker", first[0], result)
            second = await store.acquire_jobs(
                "worker", timedelta(seconds=30), limit=2,
            )
            assert len(second) == 1

    anyio.run(_run)


# ── Cross-View Invariants ──────────────────────────────────────────────


def test_state_model_views_agree_for_task_schedule_job():
    """Seam: config interaction — integration path for state model views agree for task schedule job across cooperating public APIs."""
    run_time = datetime.now(timezone.utc) + timedelta(hours=2)
    with Scheduler(role=SchedulerRole.scheduler) as sched:
        queue: Queue = Queue()
        sched.subscribe(queue.put_nowait)
        sched.configure_task(
            "model-task", func=return_value, metadata={"scope": "state"},
        )
        sched.add_schedule(
            "model-task", DateTrigger(run_time), id="model-schedule",
        )
        sched.add_job("model-task")
        assert sched.get_tasks()[0].id == "model-task"
        assert sched.get_schedule("model-schedule").task_id == "model-task"
        assert sched.get_jobs()[0].task_id == "model-task"
        event_types = [type(queue.get(timeout=1)) for _ in range(3)]
        assert event_types == [TaskAdded, ScheduleAdded, JobAdded]


def test_cross_view_schedule_event_matches_stored_schedule():
    """CVI-N: ScheduleAdded event fields match the stored schedule projection."""
    run_time = datetime.now(timezone.utc) + timedelta(hours=2)
    with Scheduler() as sched:
        queue: Queue = Queue()
        sched.subscribe(queue.put_nowait, {ScheduleAdded})
        sched.add_schedule(
            return_value, DateTrigger(run_time), id="cross-view-s",
        )
        event = queue.get(timeout=1)
        s = sched.get_schedule("cross-view-s")
        assert event.schedule_id == s.id
        assert event.task_id == s.task_id
        assert event.next_fire_time == s.next_fire_time


def test_cross_view_task_event_matches_configured_task():
    """CVI-N: TaskAdded event fields match the configured task projection."""
    with Scheduler() as sched:
        queue: Queue = Queue()
        sched.subscribe(queue.put_nowait, {TaskAdded})
        t = sched.configure_task(
            "cross-view-t", func=return_value, metadata={"owner": "ops"},
        )
        event = queue.get(timeout=1)
        stored = sched.get_tasks()[0]
        assert event.task_id == t.id == stored.id
        assert stored.metadata == {"owner": "ops"}


def test_remove_schedule_does_not_cancel_already_queued_jobs():
    """Seam: lifecycle crossing — integration path for remove schedule does not cancel already queued jobs across cooperating public APIs."""
    with Scheduler(role=SchedulerRole.scheduler) as sched:
        sched.add_schedule(
            return_value, DateTrigger(datetime.now(timezone.utc)),
            id="removable-sched",
        )
        sched.start_in_background()
        deadline = time.time() + 3
        while time.time() < deadline and not sched.get_jobs():
            time.sleep(0.05)
        assert len(sched.get_jobs()) >= 1
        sched.remove_schedule("removable-sched")
        assert len(sched.get_jobs()) >= 1


# ── Workflow Compositions ──────────────────────────────────────────────


def test_direct_job_workflow_events_and_result():
    """Seam: lifecycle crossing — integration path for direct job workflow events and result across cooperating public APIs."""
    with Scheduler() as sched:
        queue: Queue = Queue()
        sched.subscribe(queue.put_nowait, {JobAdded, JobAcquired, JobReleased})
        jid = sched.add_job(
            add_values, args=[4, 9], result_expiration_time=15,
        )
        assert sched.get_jobs()[0].id == jid
        sched.start_in_background()
        result = sched.get_job_result(jid)
        assert result.return_value == 13
        events = [queue.get(timeout=1), queue.get(timeout=1), queue.get(timeout=1)]
        assert [type(e) for e in events] == [JobAdded, JobAcquired, JobReleased]
        assert events[-1].outcome is JobOutcome.success


def test_schedule_lifecycle_pause_unpause_remove_workflow():
    """Seam: lifecycle crossing — integration path for schedule lifecycle pause unpause remove workflow across cooperating public APIs."""
    run_time = datetime.now(timezone.utc) + timedelta(hours=2)
    with Scheduler() as sched:
        sid = sched.add_schedule(
            return_value, DateTrigger(run_time), id="wf-lifecycle",
        )
        sched.pause_schedule(sid)
        assert sched.get_schedule(sid).paused is True
        sched.unpause_schedule(sid)
        assert sched.get_schedule(sid).paused is False
        sched.remove_schedule(sid)
        assert sched.get_schedules() == []


def test_direct_job_visible_in_event_and_result_projections():
    """Seam: lifecycle crossing — integration path for direct job visible in event and result projections across cooperating public APIs."""
    with Scheduler() as sched:
        queue: Queue = Queue()
        sched.subscribe(queue.put_nowait, {JobAdded, JobAcquired, JobReleased})
        jid = sched.add_job(return_value, result_expiration_time=15)
        sched.start_in_background()
        result = sched.get_job_result(jid)
        events = [queue.get(timeout=1), queue.get(timeout=1), queue.get(timeout=1)]
        assert result.return_value == "result"
        assert [type(e) for e in events] == [JobAdded, JobAcquired, JobReleased]
        assert events[-1].outcome is JobOutcome.success


def test_schedule_lifecycle_events_match_state_changes():
    """Seam: lifecycle crossing — integration path for schedule lifecycle events match state changes across cooperating public APIs."""
    run_time = datetime.now(timezone.utc) + timedelta(hours=2)
    with Scheduler() as sched:
        queue: Queue = Queue()
        sched.subscribe(
            queue.put_nowait,
            {ScheduleAdded, ScheduleUpdated, ScheduleRemoved},
        )
        sched.add_schedule(
            return_value, DateTrigger(run_time), id="lc-events",
        )
        sched.pause_schedule("lc-events")
        assert sched.get_schedule("lc-events").paused is True
        sched.unpause_schedule("lc-events")
        assert sched.get_schedule("lc-events").paused is False
        sched.remove_schedule("lc-events")
        events = [queue.get(timeout=1) for _ in range(4)]
        assert [type(e) for e in events] == [
            ScheduleAdded,
            ScheduleUpdated,
            ScheduleUpdated,
            ScheduleRemoved,
        ]
