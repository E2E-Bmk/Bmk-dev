"""Atomic tests for apscheduler-jobs-fullrepro-001.

Each test validates ONE public API entry point with ONE behavior point.
If only the API under test is correctly implemented (everything else is a
stub), the test must still pass.
"""
from __future__ import annotations

import pickle
from datetime import datetime, timedelta, timezone

import anyio
import pytest

from apscheduler import (
    AsyncScheduler,
    CoalescePolicy,
    ConflictPolicy,
    ConflictingIdError,
    JobLookupError,
    JobOutcome,
    JobResult,
    JobResultNotReady,
    RunState,
    ScheduleLookupError,
    Scheduler,
    SchedulerRole,
    TaskDefaults,
    TaskLookupError,
    task,
)
from apscheduler.datastores.memory import MemoryDataStore
from apscheduler.eventbrokers.local import LocalEventBroker
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from conftest import add_values, decorated_callable, return_value


# ── Task Decorator ──────────────────────────────────────────────────────


def test_task_decorator_rejects_non_callable_argument():
    with pytest.raises(ValueError):
        task()(42)


def test_task_decorator_rejects_double_decoration_attempt():
    def fn():
        return None

    decorated = task()(fn)
    with pytest.raises(ValueError):
        task()(decorated)


def test_task_decorator_does_not_wrap_or_replace_function():
    def original():
        return "hello"

    result = task()(original)
    assert result is original


# ── configure_task ──────────────────────────────────────────────────────


def test_configure_task_rejects_invalid_argument_type():
    with Scheduler() as sched:
        with pytest.raises(TypeError):
            sched.configure_task(None)


def test_configure_task_creates_task_with_default_executor():
    with Scheduler() as sched:
        t = sched.configure_task("plain-task", func=return_value)
        assert t.id == "plain-task"
        assert t.job_executor == "threadpool"
        assert t.running_jobs == 0
        assert t.metadata == {}


def test_configure_task_uses_module_qualname_as_task_id():
    with Scheduler() as sched:
        t = sched.configure_task(add_values)
        expected = f"{add_values.__module__}:{add_values.__qualname__}"
        assert t.id == expected


def test_configure_task_merges_defaults_decorator_and_direct_metadata():
    defaults = TaskDefaults(
        metadata={"base": 1, "shared": "base"}, misfire_grace_time=5,
    )
    with Scheduler(task_defaults=defaults) as sched:
        t = sched.configure_task(
            decorated_callable, metadata={"direct": 3, "shared": "direct"},
        )
        assert t.id == "decorated-task"
        assert t.job_executor == "threadpool"
        assert t.max_running_jobs == 3
        assert t.misfire_grace_time == timedelta(seconds=6)
        assert t.metadata == {
            "base": 1,
            "decorated": True,
            "direct": 3,
            "shared": "direct",
        }


# ── Task Object Attributes ─────────────────────────────────────────────


def test_task_running_jobs_is_zero_for_new_task():
    with Scheduler() as sched:
        t = sched.configure_task("fresh-task", func=return_value)
        assert t.running_jobs == 0


def test_task_metadata_defaults_to_empty_dict():
    with Scheduler() as sched:
        t = sched.configure_task("bare-task", func=return_value)
        assert t.metadata == {}


def test_task_equality_and_hash_determined_by_id():
    with Scheduler() as sched:
        t1 = sched.configure_task("same-id", func=return_value)
        t2 = sched.configure_task("different-id", func=return_value)
        fetched = [x for x in sched.get_tasks() if x.id == "same-id"][0]
        assert t1 == fetched
        assert hash(t1) == hash(fetched)
        assert t1 != t2


# ── get_tasks ───────────────────────────────────────────────────────────


def test_get_tasks_returns_results_sorted_by_id():
    with Scheduler() as sched:
        sched.configure_task("zeta", func=return_value)
        sched.configure_task("alpha", func=return_value)
        ids = [t.id for t in sched.get_tasks()]
        assert ids == ["alpha", "zeta"]


# ── add_schedule ────────────────────────────────────────────────────────


def test_add_schedule_generates_string_id_when_omitted():
    t = datetime.now(timezone.utc) + timedelta(hours=2)
    with Scheduler() as sched:
        sid = sched.add_schedule(return_value, DateTrigger(t))
        assert isinstance(sid, str)
        assert sched.get_schedule(sid).id == sid


def test_add_schedule_returns_explicit_id_and_preserves_args():
    t = datetime.now(timezone.utc) + timedelta(hours=2)
    with Scheduler() as sched:
        sid = sched.add_schedule(
            add_values, DateTrigger(t), id="explicit-sched", args=(7, 8),
        )
        assert sid == "explicit-sched"
        s = sched.get_schedule("explicit-sched")
        assert s.id == "explicit-sched"
        assert tuple(s.args) == (7, 8)
        assert s.next_fire_time == t


def test_add_schedule_preserves_kwargs_metadata_jitter_and_expiration():
    t = datetime.now(timezone.utc) + timedelta(hours=2)
    with Scheduler() as sched:
        sched.add_schedule(
            return_value,
            DateTrigger(t),
            id="rich-sched",
            kwargs={"value": "x"},
            metadata={"env": "test"},
            max_jitter=timedelta(seconds=7),
            job_result_expiration_time=20,
        )
        s = sched.get_schedule("rich-sched")
        assert dict(s.kwargs) == {"value": "x"}
        assert s.metadata == {"env": "test"}
        assert s.max_jitter == timedelta(seconds=7)
        assert s.job_result_expiration_time == timedelta(seconds=20)


# ── Schedule Attributes ────────────────────────────────────────────────


def test_schedule_coalesce_defaults_to_latest():
    t = datetime.now(timezone.utc) + timedelta(hours=2)
    with Scheduler() as sched:
        sched.add_schedule(return_value, DateTrigger(t), id="coal-check")
        assert sched.get_schedule("coal-check").coalesce == CoalescePolicy.latest


def test_schedule_paused_defaults_to_false():
    t = datetime.now(timezone.utc) + timedelta(hours=2)
    with Scheduler() as sched:
        sched.add_schedule(return_value, DateTrigger(t), id="paused-check")
        assert sched.get_schedule("paused-check").paused is False


# ── get_schedule / get_schedules ────────────────────────────────────────


def test_get_schedule_raises_lookup_error_for_missing_id():
    with Scheduler() as sched:
        with pytest.raises(ScheduleLookupError):
            sched.get_schedule("nonexistent-id")


def test_get_schedules_ordered_by_next_fire_time():
    base = datetime.now(timezone.utc) + timedelta(hours=2)
    with Scheduler() as sched:
        sched.add_schedule(
            return_value, DateTrigger(base + timedelta(hours=2)), id="later",
        )
        sched.add_schedule(return_value, DateTrigger(base), id="earlier")
        schedules = sched.get_schedules()
        assert schedules[0].id == "earlier"
        assert schedules[1].id == "later"


# ── remove_schedule ─────────────────────────────────────────────────────


def test_remove_schedule_noop_for_absent_id():
    with Scheduler() as sched:
        sched.remove_schedule("ghost-schedule")
        assert sched.get_schedules() == []


def test_remove_schedule_removes_only_matching_entry():
    t = datetime.now(timezone.utc) + timedelta(hours=2)
    with Scheduler() as sched:
        sched.add_schedule(return_value, DateTrigger(t), id="keep-this")
        sched.add_schedule(return_value, DateTrigger(t), id="drop-this")
        sched.remove_schedule("drop-this")
        assert [s.id for s in sched.get_schedules()] == ["keep-this"]


# ── ConflictPolicy ──────────────────────────────────────────────────────


def test_conflict_policy_do_nothing_preserves_existing():
    t1 = datetime.now(timezone.utc) + timedelta(hours=2)
    t2 = t1 + timedelta(hours=1)
    with Scheduler() as sched:
        sched.add_schedule(return_value, DateTrigger(t1), id="conflict-dn")
        ret = sched.add_schedule(
            add_values, DateTrigger(t2), id="conflict-dn",
            conflict_policy=ConflictPolicy.do_nothing,
        )
        assert ret == "conflict-dn"
        assert sched.get_schedule("conflict-dn").next_fire_time == t1


def test_conflict_policy_replace_updates_existing():
    t1 = datetime.now(timezone.utc) + timedelta(hours=2)
    t2 = t1 + timedelta(hours=1)
    with Scheduler() as sched:
        sched.add_schedule(return_value, DateTrigger(t1), id="conflict-rp")
        sched.add_schedule(
            add_values, DateTrigger(t2), id="conflict-rp",
            conflict_policy=ConflictPolicy.replace,
        )
        assert sched.get_schedule("conflict-rp").next_fire_time == t2


def test_conflict_policy_exception_raises_conflicting_id_error():
    t = datetime.now(timezone.utc) + timedelta(hours=2)
    with Scheduler() as sched:
        sched.add_schedule(return_value, DateTrigger(t), id="conflict-ex")
        with pytest.raises(ConflictingIdError):
            sched.add_schedule(
                return_value, DateTrigger(t), id="conflict-ex",
                conflict_policy=ConflictPolicy.exception,
            )


# ── pause_schedule / unpause_schedule ──────────────────────────────────


def test_pause_and_unpause_schedule_round_trip():
    t = datetime.now(timezone.utc) + timedelta(hours=2)
    with Scheduler() as sched:
        sched.add_schedule(return_value, DateTrigger(t), id="toggle-sched")
        sched.pause_schedule("toggle-sched")
        assert sched.get_schedule("toggle-sched").paused is True
        sched.unpause_schedule("toggle-sched")
        s = sched.get_schedule("toggle-sched")
        assert s.paused is False
        assert s.next_fire_time == t


# ── add_job ─────────────────────────────────────────────────────────────


def test_add_job_returns_uuid_and_visible_before_processing():
    with Scheduler() as sched:
        jid = sched.add_job(return_value, result_expiration_time=15)
        jobs = sched.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == jid
        assert jobs[0].schedule_id is None


# ── Job Attributes ──────────────────────────────────────────────────────


def test_job_attributes_args_kwargs_executor_expiration():
    with Scheduler() as sched:
        jid = sched.add_job(
            add_values, args=(7, 8), kwargs={"k": 2},
            result_expiration_time=45,
        )
        job = sched.get_jobs()[0]
        assert job.id == jid
        assert tuple(job.args) == (7, 8)
        assert dict(job.kwargs) == {"k": 2}
        assert job.executor == "threadpool"
        assert job.result_expiration_time == timedelta(seconds=45)
        assert job.scheduled_fire_time is None
        assert job.original_scheduled_time is None


# ── get_job_result ──────────────────────────────────────────────────────


def test_get_job_result_wait_false_raises_job_lookup_error():
    with Scheduler() as sched:
        jid = sched.add_job(return_value, result_expiration_time=15)
        with pytest.raises(JobLookupError):
            sched.get_job_result(jid, wait=False)


# ── JobResult.from_job ──────────────────────────────────────────────────


def test_job_result_from_job_sets_id_and_expiration():
    with Scheduler() as sched:
        jid = sched.add_job(return_value, result_expiration_time=15)
        job = sched.get_jobs()[0]
        finished = datetime.now(timezone.utc)
        result = JobResult.from_job(
            job, JobOutcome.success, finished_at=finished, return_value="val",
        )
        assert result.job_id == jid
        assert result.expires_at == finished + timedelta(seconds=15)
        assert result.return_value == "val"


# ── JobResultNotReady ───────────────────────────────────────────────────


def test_job_result_not_ready_is_constructible():
    with Scheduler() as sched:
        jid = sched.add_job(return_value)
        exc = JobResultNotReady(jid)
        assert isinstance(exc, Exception)
        assert exc.job_id == jid


# ── DateTrigger ─────────────────────────────────────────────────────────


def test_date_trigger_fires_once_then_exhausts():
    t = datetime(2026, 8, 15, 10, 0, tzinfo=timezone.utc)
    trigger = DateTrigger(t)
    assert trigger.next() == t
    assert trigger.next() is None


def test_date_trigger_converts_naive_to_timezone_aware():
    naive = datetime(2026, 6, 10, 14, 45)
    trigger = DateTrigger(naive)
    fired = trigger.next()
    assert fired.tzinfo is not None
    assert fired == naive.astimezone()


def test_date_trigger_pickle_preserves_fired_state():
    t = datetime(2026, 4, 20, tzinfo=timezone.utc)
    fresh = pickle.loads(pickle.dumps(DateTrigger(t)))
    assert fresh.next() == t

    already_fired = DateTrigger(t)
    already_fired.next()
    restored = pickle.loads(pickle.dumps(already_fired))
    assert restored.next() is None


# ── IntervalTrigger ─────────────────────────────────────────────────────


def test_interval_trigger_rejects_zero_interval():
    with pytest.raises(ValueError):
        IntervalTrigger()


def test_interval_trigger_rejects_end_before_start():
    s = datetime(2026, 3, 10, tzinfo=timezone.utc)
    e = datetime(2026, 3, 9, tzinfo=timezone.utc)
    with pytest.raises(ValueError):
        IntervalTrigger(days=1, start_time=s, end_time=e)


def test_interval_trigger_steps_from_start_through_end():
    s = datetime(2026, 2, 1, tzinfo=timezone.utc)
    trigger = IntervalTrigger(
        minutes=15, start_time=s,
        end_time=s + timedelta(minutes=30),
    )
    assert trigger.next() == s
    assert trigger.next() == s + timedelta(minutes=15)
    assert trigger.next() == s + timedelta(minutes=30)
    assert trigger.next() is None


def test_interval_trigger_pickle_preserves_progress():
    s = datetime(2026, 2, 1, tzinfo=timezone.utc)
    trigger = IntervalTrigger(
        minutes=15, start_time=s,
        end_time=s + timedelta(minutes=30),
    )
    assert trigger.next() == s
    restored = pickle.loads(pickle.dumps(trigger))
    assert restored.next() == s + timedelta(minutes=15)
    assert restored.next() == s + timedelta(minutes=30)
    assert restored.next() is None


# ── Documented Enums ────────────────────────────────────────────────────


def test_job_outcome_enum_has_documented_members():
    assert {m.name for m in JobOutcome} == {
        "success", "error", "missed_start_deadline",
        "deserialization_failed", "cancelled", "abandoned",
    }


def test_run_state_enum_has_documented_members():
    assert {m.name for m in RunState} == {
        "starting", "started", "stopping", "stopped",
    }


def test_scheduler_role_enum_has_documented_members():
    assert {m.name for m in SchedulerRole} == {
        "scheduler", "worker", "both",
    }


# ── Scheduler Defaults ─────────────────────────────────────────────────


def test_scheduler_defaults_memory_store_local_broker_both_role():
    with Scheduler() as sched:
        assert isinstance(sched.data_store, MemoryDataStore)
        assert isinstance(sched.event_broker, LocalEventBroker)
        assert sched.role is SchedulerRole.both
        assert sched.max_concurrent_jobs == 100
        assert isinstance(sched.identity, str)
        assert sched.identity


# ── MemoryDataStore ─────────────────────────────────────────────────────


def test_memory_datastore_raises_task_lookup_error_for_missing():
    async def _run():
        store = MemoryDataStore()
        async with AsyncScheduler(data_store=store):
            with pytest.raises(TaskLookupError):
                await store.get_task("nonexistent-task")

    anyio.run(_run)
