# Spec2Repo oracle - atomic tests for pgqueuer-fullrepro-001
from __future__ import annotations

import asyncio
import uuid
from collections.abc import Mapping
from datetime import timedelta

import pytest

from pgqueuer import InMemoryDriver, InMemoryQueries, Job, PgQueuer, RetryRequested
from pgqueuer.models import Context, ScheduleContext
from pgqueuer.types import JobId, QueueExecutionMode


def run(coro):
    return asyncio.run(coro)


def latest_status(rows, job_id):
    requested = int(job_id)
    if isinstance(rows, Mapping):
        for key in (job_id, requested, str(requested)):
            if key in rows:
                return rows[key]
        raise AssertionError(f"job id {requested} missing from job_status result")

    for row in rows:
        if isinstance(row, Mapping):
            key = row.get("job_id", row.get("id"))
            status = row.get("status")
        elif hasattr(row, "job_id") and hasattr(row, "status"):
            key = row.job_id
            status = row.status
        elif hasattr(row, "id") and hasattr(row, "status"):
            key = row.id
            status = row.status
        else:
            key, status = row
        if int(key) == requested:
            return status
    raise AssertionError(f"job id {requested} missing from job_status result")


def latest_statuses(rows, ids):
    return {int(job_id): latest_status(rows, job_id) for job_id in ids}


async def make_queries() -> InMemoryQueries:
    pgq = PgQueuer.in_memory()
    return pgq.qm.queries


def test_top_level_public_imports_available():
    assert PgQueuer is not None
    assert InMemoryDriver is not None
    assert InMemoryQueries is not None
    assert Job is not None
    assert JobId(7) == 7


def test_install_upgrade_and_schema_checks_are_noops():
    async def scenario():
        queries = await make_queries()
        await queries.install()
        await queries.upgrade()
        assert await queries.has_table("anything")
        assert await queries.table_has_column("anything", "column")
        assert await queries.table_has_index("anything", "index")
        assert await queries.has_user_defined_enum("queued", "enum")
        assert await queries.has_function("fn")
        assert await queries.has_trigger("trig")

    run(scenario())


def test_enqueue_single_returns_monotonic_job_id_and_log():
    async def scenario():
        queries = await make_queries()
        ids = await queries.enqueue("alpha", b"payload", priority=3)
        assert ids == [JobId(1)]
        log = await queries.queue_log()
        assert [(int(row.job_id), row.entrypoint, row.status, row.priority) for row in log] == [
            (1, "alpha", "queued", 3)
        ]

    run(scenario())


def test_deferred_job_is_hidden_until_eligible():
    async def scenario():
        queries = await make_queries()
        await queries.enqueue("later", b"x", execute_after=timedelta(seconds=60))
        eta = await queries.next_deferred_eta(["later"])
        sizes = await queries.queue_size()
        assert [(row.entrypoint, row.status, row.count) for row in sizes] == [("later", "queued", 1)]
        assert eta is not None and eta > timedelta(seconds=0)

    run(scenario())


def test_next_deferred_eta_none_when_no_matching_deferred_work():
    async def scenario():
        queries = await make_queries()
        assert await queries.next_deferred_eta(["missing"]) is None
        await queries.enqueue("ready", b"x")
        assert await queries.next_deferred_eta(["ready"]) is None

    run(scenario())


def test_entrypoint_decorator_registers_and_returns_function():
    pgq = PgQueuer.in_memory()

    async def work(job: Job) -> None:
        return None

    assert pgq.entrypoint("work")(work) is work


def test_entrypoint_duplicate_name_raises_runtime_error():
    pgq = PgQueuer.in_memory()

    @pgq.entrypoint("same")
    async def first(job: Job) -> None:
        return None

    with pytest.raises(RuntimeError):

        @pgq.entrypoint("same")
        async def second(job: Job) -> None:
            return None


@pytest.mark.parametrize("value", ["1", 1.5, object()])
def test_entrypoint_rejects_non_integer_concurrency_limit(value):
    pgq = PgQueuer.in_memory()
    with pytest.raises(ValueError):
        pgq.entrypoint("bad", concurrency_limit=value)


def test_entrypoint_rejects_negative_concurrency_limit():
    pgq = PgQueuer.in_memory()
    with pytest.raises(ValueError):
        pgq.entrypoint("bad", concurrency_limit=-1)


def test_entrypoint_rejects_unknown_failure_policy():
    pgq = PgQueuer.in_memory()
    with pytest.raises(ValueError):
        pgq.entrypoint("bad", on_failure="retry")


def test_run_rejects_too_low_max_concurrent_tasks():
    async def scenario():
        pgq = PgQueuer.in_memory()
        with pytest.raises(RuntimeError):
            await pgq.qm.run(
                batch_size=2,
                max_concurrent_tasks=3,
                mode=QueueExecutionMode.drain,
                dequeue_timeout=timedelta(seconds=0.01),
            )

    run(scenario())


def test_retry_requested_defaults_and_reason_attributes():
    default = RetryRequested()
    custom = RetryRequested(timedelta(seconds=5), reason="later")
    assert default.delay == timedelta(0)
    assert default.reason is None
    assert str(default) == "Retry requested"
    assert custom.delay == timedelta(seconds=5)
    assert custom.reason == "later"
    assert str(custom) == "later"


def test_retry_preserves_payload_priority_and_job_id():
    async def scenario():
        pgq = PgQueuer.in_memory()
        observed = []

        @pgq.entrypoint("flaky")
        async def flaky(job: Job) -> None:
            observed.append((int(job.id), job.payload, job.priority, job.attempts))
            if job.attempts == 0:
                raise RetryRequested()

        await pgq.qm.queries.enqueue("flaky", b"keep", priority=8)
        await pgq.qm.run(
            batch_size=1,
            mode=QueueExecutionMode.drain,
            max_concurrent_tasks=2,
            dequeue_timeout=timedelta(seconds=0.01),
        )
        assert observed == [(1, b"keep", 8, 0), (1, b"keep", 8, 1)]

    run(scenario())


def test_requeue_jobs_ignores_non_failed_and_missing_ids():
    async def scenario():
        queries = await make_queries()
        ids = await queries.enqueue("a", b"x")
        await queries.requeue_jobs([ids[0], JobId(999)])
        assert latest_status(await queries.job_status(ids), ids[0]) == "queued"

    run(scenario())


def test_mark_job_as_cancelled_removes_active_job_and_logs_status():
    async def scenario():
        queries = await make_queries()
        ids = await queries.enqueue("a", b"x")
        await queries.mark_job_as_cancelled(ids)
        assert await queries.queue_size() == []
        assert latest_status(await queries.job_status(ids), ids[0]) == "canceled"

    run(scenario())


def test_mark_job_as_cancelled_ignores_missing_ids():
    async def scenario():
        queries = await make_queries()
        await queries.mark_job_as_cancelled([JobId(1234)])
        assert await queries.queue_log() == []

    run(scenario())


def test_dedupe_key_rejects_duplicate_active_job():
    async def scenario():
        queries = await make_queries()
        await queries.enqueue("a", b"x", dedupe_key="same")
        with pytest.raises(Exception):
            await queries.enqueue("a", b"y", dedupe_key="same")

    run(scenario())


def test_queue_size_groups_by_entrypoint_priority_and_status():
    async def scenario():
        queries = await make_queries()
        await queries.enqueue(["a", "a", "b"], [b"1", b"2", b"3"], [0, 0, 5])
        sizes = await queries.queue_size()
        assert sorted((row.entrypoint, row.priority, row.status, row.count) for row in sizes) == [
            ("a", 0, "queued", 2),
            ("b", 5, "queued", 1),
        ]

    run(scenario())


def test_queue_size_counts_active_jobs_by_entrypoint():
    async def scenario():
        queries = await make_queries()
        await queries.enqueue(["a", "b", "b"], [b"1", b"2", b"3"], [0, 0, 0])
        sizes = await queries.queue_size()
        assert sorted((row.entrypoint, row.status, row.count) for row in sizes) == [
            ("a", "queued", 1),
            ("b", "queued", 2),
        ]

    run(scenario())


def test_uninstall_clears_jobs_logs_statistics_schedules_and_dedupe():
    async def scenario():
        queries = await make_queries()
        await queries.enqueue("a", b"x", dedupe_key="same")
        await queries.log_statistics(limit=10)
        await queries.uninstall()
        ids = await queries.enqueue("a", b"y", dedupe_key="same")
        assert ids == [JobId(2)]
        assert [(row.entrypoint, row.status) for row in await queries.queue_log()] == [("a", "queued")]

    run(scenario())


def test_schedule_decorator_registers_and_returns_function():
    pgq = PgQueuer.in_memory()

    async def tick(schedule):
        return None

    assert pgq.schedule("tick", "* * * * *")(tick) is tick


def test_schedule_invalid_cron_raises_value_error():
    pgq = PgQueuer.in_memory()
    with pytest.raises(ValueError):
        pgq.schedule("bad", "not a cron")


def test_schedule_duplicate_normalized_pair_raises_runtime_error():
    pgq = PgQueuer.in_memory()

    @pgq.schedule("tick", "* * * * *")
    async def first(schedule):
        return None

    with pytest.raises(RuntimeError):

        @pgq.schedule("tick", "* * * * *")
        async def second(schedule):
            return None


def test_schedule_six_field_trailing_seconds_is_registered():
    async def scenario():
        pgq = PgQueuer.in_memory()

        @pgq.schedule("heartbeat", "* * * * * */1")
        async def heartbeat(schedule):
            pgq.shutdown.set()

        await asyncio.wait_for(pgq.sm.run(), timeout=3)
        schedules = await pgq.sm.queries.peek_schedule()
        assert [(row.entrypoint, row.status) for row in schedules] == [("heartbeat", "queued")]

    run(scenario())


def test_update_schedule_heartbeat_changes_heartbeat_without_status_change():
    async def scenario():
        pgq = PgQueuer.in_memory()

        @pgq.schedule("tick", "* * * * * */1")
        async def tick(schedule):
            pgq.shutdown.set()

        await asyncio.wait_for(pgq.sm.run(), timeout=3)
        before = (await pgq.sm.queries.peek_schedule())[0]
        await pgq.sm.queries.update_schedule_heartbeat({before.id})
        after = (await pgq.sm.queries.peek_schedule())[0]
        assert after.id == before.id
        assert after.status == "queued"
        assert after.heartbeat >= before.heartbeat

    run(scenario())
