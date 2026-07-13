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


def test_in_memory_factory_wires_public_managers_and_queries():
    pgq = PgQueuer.in_memory(resources={"name": "shared"})
    assert isinstance(pgq.connection, InMemoryDriver)
    assert isinstance(pgq.queries, InMemoryQueries)
    assert pgq.qm.queries is pgq.queries
    assert pgq.sm.queries is pgq.queries
    assert pgq.qm.resources["name"] == "shared"
    assert pgq.sm.resources["name"] == "shared"


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


def test_enqueue_batch_preserves_order_and_payloads():
    async def scenario():
        seen = []
        pgq = PgQueuer.in_memory()

        for entrypoint in ["a", "b", "c"]:

            @pgq.entrypoint(entrypoint)
            async def work(job: Job) -> None:
                seen.append((job.entrypoint, job.payload, job.priority))

        ids = await pgq.qm.queries.enqueue(["a", "b", "c"], [b"one", None, b"three"], [0, 5, 2])
        assert ids == [JobId(1), JobId(2), JobId(3)]
        await pgq.qm.run(
            batch_size=10,
            mode=QueueExecutionMode.drain,
            max_concurrent_tasks=20,
            dequeue_timeout=timedelta(seconds=0.01),
        )
        assert seen == [
            ("b", None, 5),
            ("c", b"three", 2),
            ("a", b"one", 0),
        ]

    run(scenario())


def test_dequeue_raises_for_zero_batch_size():
    async def scenario():
        queries = await make_queries()
        with pytest.raises(ValueError):
            await queries.dequeue(0, {}, uuid.uuid4(), None, timedelta(seconds=30))

    run(scenario())


def test_dequeue_empty_entrypoints_returns_empty():
    async def scenario():
        queries = await make_queries()
        await queries.enqueue("a", b"x")
        assert await queries.dequeue(10, {}, uuid.uuid4(), None, timedelta(seconds=30)) == []

    run(scenario())


def test_dequeue_filters_by_registered_entrypoints():
    async def scenario():
        seen = []
        pgq = PgQueuer.in_memory()

        @pgq.entrypoint("b")
        async def only_b(job: Job) -> None:
            seen.append(job.entrypoint)

        await pgq.qm.queries.enqueue(["a", "b"], [b"a", b"b"], [0, 0])
        await pgq.qm.run(
            batch_size=10,
            mode=QueueExecutionMode.drain,
            max_concurrent_tasks=20,
            dequeue_timeout=timedelta(seconds=0.01),
        )
        assert seen == ["b"]
        sizes = await pgq.qm.queries.queue_size()
        assert [(row.entrypoint, row.status, row.count) for row in sizes] == [("a", "queued", 1)]

    run(scenario())


def test_dequeue_orders_by_priority_then_id():
    async def scenario():
        seen = []
        pgq = PgQueuer.in_memory()

        for entrypoint in ["low", "high1", "high2"]:

            @pgq.entrypoint(entrypoint)
            async def work(job: Job) -> None:
                seen.append((job.entrypoint, int(job.id)))

        await pgq.qm.queries.enqueue(["low", "high1", "high2"], [b"l", b"h1", b"h2"], [0, 9, 9])
        await pgq.qm.run(
            batch_size=3,
            mode=QueueExecutionMode.drain,
            max_concurrent_tasks=6,
            dequeue_timeout=timedelta(seconds=0.01),
        )
        assert seen == [
            ("high1", 2),
            ("high2", 3),
            ("low", 1),
        ]

    run(scenario())


def test_dequeue_marks_jobs_picked_and_job_status_reflects_latest():
    async def scenario():
        seen_statuses = []
        pgq = PgQueuer.in_memory()

        @pgq.entrypoint("alpha")
        async def alpha(job: Job) -> None:
            seen_statuses.append(job.status)
            seen_statuses.append(latest_status(await pgq.qm.queries.job_status([job.id]), job.id))

        ids = await pgq.qm.queries.enqueue("alpha", b"x")
        await pgq.qm.run(
            batch_size=1,
            mode=QueueExecutionMode.drain,
            max_concurrent_tasks=2,
            dequeue_timeout=timedelta(seconds=0.01),
        )
        assert seen_statuses == ["picked", "picked"]
        assert latest_status(await pgq.qm.queries.job_status(ids), ids[0]) == "successful"

    run(scenario())


def test_dequeue_respects_per_entrypoint_concurrency_limit():
    async def scenario():
        running = 0
        max_seen = 0
        pgq = PgQueuer.in_memory()

        @pgq.entrypoint("alpha", concurrency_limit=1)
        async def alpha(job: Job) -> None:
            nonlocal running, max_seen
            running += 1
            max_seen = max(max_seen, running)
            await asyncio.sleep(0.01)
            running -= 1

        await pgq.qm.queries.enqueue(["alpha", "alpha", "alpha"], [b"1", b"2", b"3"], [0, 0, 0])
        await pgq.qm.run(
            batch_size=3,
            mode=QueueExecutionMode.drain,
            max_concurrent_tasks=6,
            dequeue_timeout=timedelta(seconds=0.01),
        )
        assert max_seen == 1

    run(scenario())


def test_dequeue_respects_global_concurrency_limit():
    async def scenario():
        running = 0
        max_seen = 0
        pgq = PgQueuer.in_memory()

        for entrypoint in ["a", "b", "c"]:

            @pgq.entrypoint(entrypoint)
            async def work(job: Job) -> None:
                nonlocal running, max_seen
                running += 1
                max_seen = max(max_seen, running)
                await asyncio.sleep(0.01)
                running -= 1

        await pgq.qm.queries.enqueue(["a", "b", "c"], [b"a", b"b", b"c"], [0, 0, 0])
        await pgq.qm.run(
            batch_size=1,
            mode=QueueExecutionMode.drain,
            max_concurrent_tasks=2,
            dequeue_timeout=timedelta(seconds=0.01),
        )
        assert max_seen <= 2

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


def test_entrypoint_rejects_non_boolean_accepts_context():
    pgq = PgQueuer.in_memory()
    with pytest.raises(ValueError):
        pgq.entrypoint("bad", accepts_context="yes")


def test_entrypoint_rejects_unknown_failure_policy():
    pgq = PgQueuer.in_memory()
    with pytest.raises(ValueError):
        pgq.entrypoint("bad", on_failure="retry")


def test_queue_manager_run_drain_processes_priority_order_and_success_logs():
    async def scenario():
        seen = []
        pgq = PgQueuer.in_memory(resources={"seen": seen})

        @pgq.entrypoint("work", accepts_context=True)
        async def work(job: Job, ctx: Context) -> None:
            ctx.resources["seen"].append(job.payload)

        ids = await pgq.qm.queries.enqueue(["work", "work"], [b"low", b"high"], [0, 10])
        await pgq.qm.run(
            batch_size=2,
            mode=QueueExecutionMode.drain,
            max_concurrent_tasks=4,
            dequeue_timeout=timedelta(seconds=0.01),
        )
        assert seen == [b"high", b"low"]
        assert latest_statuses(await pgq.qm.queries.job_status(ids), ids) == {
            1: "successful",
            2: "successful",
        }
        assert await pgq.qm.queries.queue_size() == []

    run(scenario())


def test_context_auto_detects_context_annotation():
    async def scenario():
        pgq = PgQueuer.in_memory(resources={"count": 0})

        @pgq.entrypoint("ctx")
        async def ctx_job(job: Job, ctx: Context) -> None:
            ctx.resources["count"] += 1

        await pgq.qm.queries.enqueue("ctx", b"x")
        await pgq.qm.run(
            batch_size=1,
            mode=QueueExecutionMode.drain,
            max_concurrent_tasks=2,
            dequeue_timeout=timedelta(seconds=0.01),
        )
        assert pgq.resources["count"] == 1

    run(scenario())


def test_accepts_context_false_suppresses_annotation_injection():
    async def scenario():
        pgq = PgQueuer.in_memory(resources={"called": False})

        @pgq.entrypoint("plain", accepts_context=False)
        async def plain(job: Job) -> None:
            pgq.resources["called"] = True

        await pgq.qm.queries.enqueue("plain", b"x")
        await pgq.qm.run(
            batch_size=1,
            mode=QueueExecutionMode.drain,
            max_concurrent_tasks=2,
            dequeue_timeout=timedelta(seconds=0.01),
        )
        assert pgq.resources["called"] is True

    run(scenario())


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


def test_retry_requested_requeues_same_job_and_increments_attempts():
    async def scenario():
        pgq = PgQueuer.in_memory()
        calls = []

        @pgq.entrypoint("flaky")
        async def flaky(job: Job) -> None:
            calls.append((int(job.id), job.attempts))
            if job.attempts == 0:
                raise RetryRequested(reason="again")

        ids = await pgq.qm.queries.enqueue("flaky", b"payload")
        await pgq.qm.run(
            batch_size=1,
            mode=QueueExecutionMode.drain,
            max_concurrent_tasks=2,
            dequeue_timeout=timedelta(seconds=0.01),
        )
        assert calls == [(1, 0), (1, 1)]
        assert latest_status(await pgq.qm.queries.job_status(ids), ids[0]) == "successful"

    run(scenario())


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


def test_unhandled_exception_delete_policy_logs_exception_and_removes_job():
    async def scenario():
        pgq = PgQueuer.in_memory()

        @pgq.entrypoint("boom")
        async def boom(job: Job) -> None:
            raise RuntimeError("bad")

        ids = await pgq.qm.queries.enqueue("boom", b"x")
        await pgq.qm.run(
            batch_size=1,
            mode=QueueExecutionMode.drain,
            max_concurrent_tasks=2,
            dequeue_timeout=timedelta(seconds=0.01),
        )
        assert latest_status(await pgq.qm.queries.job_status(ids), ids[0]) == "exception"
        assert await pgq.qm.queries.queue_size() == []

    run(scenario())


def test_unhandled_exception_hold_policy_keeps_failed_job_visible():
    async def scenario():
        pgq = PgQueuer.in_memory()

        @pgq.entrypoint("hold", on_failure="hold")
        async def hold(job: Job) -> None:
            raise RuntimeError("bad")

        ids = await pgq.qm.queries.enqueue("hold", b"x")
        await pgq.qm.run(
            batch_size=1,
            mode=QueueExecutionMode.drain,
            max_concurrent_tasks=2,
            dequeue_timeout=timedelta(seconds=0.01),
        )
        failed = await pgq.qm.queries.list_failed_jobs()
        assert [(int(job.id), job.status, job.payload) for job in failed] == [(1, "failed", b"x")]
        assert latest_status(await pgq.qm.queries.job_status(ids), ids[0]) == "failed"

    run(scenario())


def test_requeue_jobs_restores_failed_job_and_resets_attempts():
    async def scenario():
        pgq = PgQueuer.in_memory()

        @pgq.entrypoint("hold", on_failure="hold")
        async def hold(job: Job) -> None:
            raise RuntimeError("bad")

        ids = await pgq.qm.queries.enqueue("hold", b"x")
        await pgq.qm.run(
            batch_size=1,
            mode=QueueExecutionMode.drain,
            max_concurrent_tasks=2,
            dequeue_timeout=timedelta(seconds=0.01),
        )
        await pgq.qm.queries.requeue_jobs(ids)
        assert await pgq.qm.queries.list_failed_jobs() == []
        assert latest_status(await pgq.qm.queries.job_status(ids), ids[0]) == "queued"

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


def test_clear_queue_without_filter_removes_jobs_without_delete_logs():
    async def scenario():
        queries = await make_queries()
        ids = await queries.enqueue(["a", "b"], [b"a", b"b"], [0, 0])
        await queries.clear_queue()
        assert await queries.queue_size() == []
        assert latest_statuses(await queries.job_status(ids), ids) == {1: "queued", 2: "queued"}

    run(scenario())


def test_clear_queue_with_entrypoint_logs_deleted_for_matching_jobs():
    async def scenario():
        queries = await make_queries()
        ids = await queries.enqueue(["a", "b"], [b"a", b"b"], [0, 0])
        await queries.clear_queue("a")
        assert latest_statuses(await queries.job_status(ids), ids) == {1: "deleted", 2: "queued"}
        sizes = await queries.queue_size()
        assert [(row.entrypoint, row.count) for row in sizes] == [("b", 1)]

    run(scenario())


def test_clear_queue_with_entrypoint_list_filters_any_match():
    async def scenario():
        queries = await make_queries()
        ids = await queries.enqueue(["a", "b", "c"], [b"a", b"b", b"c"], [0, 0, 0])
        await queries.clear_queue(["a", "c"])
        assert latest_statuses(await queries.job_status(ids), ids) == {
            1: "deleted",
            2: "queued",
            3: "deleted",
        }

    run(scenario())


def test_dedupe_key_rejects_duplicate_active_job():
    async def scenario():
        queries = await make_queries()
        await queries.enqueue("a", b"x", dedupe_key="same")
        with pytest.raises(Exception):
            await queries.enqueue("a", b"y", dedupe_key="same")

    run(scenario())


def test_dedupe_key_released_after_successful_log():
    async def scenario():
        pgq = PgQueuer.in_memory()

        @pgq.entrypoint("a")
        async def a(job: Job) -> None:
            return None

        ids = await pgq.qm.queries.enqueue("a", b"x", dedupe_key="same")
        await pgq.qm.run(
            batch_size=1,
            mode=QueueExecutionMode.drain,
            max_concurrent_tasks=2,
            dequeue_timeout=timedelta(seconds=0.01),
        )
        new_ids = await pgq.qm.queries.enqueue("a", b"y", dedupe_key="same")
        assert ids == [JobId(1)]
        assert new_ids == [JobId(2)]

    run(scenario())


def test_dedupe_key_released_after_failed_hold():
    async def scenario():
        pgq = PgQueuer.in_memory()

        @pgq.entrypoint("hold", on_failure="hold")
        async def hold(job: Job) -> None:
            raise RuntimeError("bad")

        await pgq.qm.queries.enqueue("hold", b"x", dedupe_key="same")
        await pgq.qm.run(
            batch_size=1,
            mode=QueueExecutionMode.drain,
            max_concurrent_tasks=2,
            dequeue_timeout=timedelta(seconds=0.01),
        )
        ids = await pgq.qm.queries.enqueue("hold", b"y", dedupe_key="same")
        assert ids == [JobId(2)]

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


def test_queue_log_is_append_ordered_across_transitions():
    async def scenario():
        pgq = PgQueuer.in_memory()

        @pgq.entrypoint("a")
        async def a(job: Job) -> None:
            return None

        ids = await pgq.qm.queries.enqueue("a", b"x")
        await pgq.qm.run(
            batch_size=1,
            mode=QueueExecutionMode.drain,
            max_concurrent_tasks=2,
            dequeue_timeout=timedelta(seconds=0.01),
        )
        assert [(int(row.job_id), row.status) for row in await pgq.qm.queries.queue_log()] == [
            (1, "queued"),
            (1, "picked"),
            (1, "successful"),
        ]
        assert latest_status(await pgq.qm.queries.job_status(ids), ids[0]) == "successful"

    run(scenario())


def test_log_statistics_aggregates_once_and_respects_limit():
    async def scenario():
        queries = await make_queries()
        await queries.enqueue(["a", "a", "b"], [b"1", b"2", b"3"], [0, 0, 1])
        first = await queries.log_statistics(limit=10)
        second = await queries.log_statistics(limit=10)
        limited = await queries.log_statistics(limit=1)
        assert sorted((row.entrypoint, row.priority, row.status, row.count) for row in first) == [
            ("a", 0, "queued", 2),
            ("b", 1, "queued", 1),
        ]
        assert [(row.entrypoint, row.priority, row.status, row.count) for row in second] == [
            (row.entrypoint, row.priority, row.status, row.count) for row in first
        ]
        assert len(limited) == 1

    run(scenario())


def test_clear_statistics_log_removes_selected_entrypoint_only():
    async def scenario():
        queries = await make_queries()
        await queries.enqueue(["a", "b"], [b"1", b"2"], [0, 0])
        await queries.log_statistics(limit=10)
        await queries.clear_statistics_log("a")
        remaining = await queries.log_statistics(limit=10)
        assert [(row.entrypoint, row.count) for row in remaining] == [("b", 1)]

    run(scenario())


def test_clear_queue_log_removes_selected_entrypoint_only():
    async def scenario():
        queries = await make_queries()
        await queries.enqueue(["a", "b"], [b"1", b"2"], [0, 0])
        await queries.clear_queue_log("a")
        assert [(row.entrypoint, row.status) for row in await queries.queue_log()] == [("b", "queued")]

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


def test_scheduler_run_populates_peek_schedule_with_registered_schedule():
    async def scenario():
        pgq = PgQueuer.in_memory()

        @pgq.schedule("tick", "* * * * * */1")
        async def tick(schedule):
            pgq.shutdown.set()

        await asyncio.wait_for(pgq.sm.run(), timeout=3)
        schedules = await pgq.sm.queries.peek_schedule()
        assert len(schedules) == 1
        assert schedules[0].entrypoint == "tick"
        assert schedules[0].status == "queued"

    run(scenario())


def test_scheduler_run_skips_duplicate_entrypoint_expression():
    async def scenario():
        pgq = PgQueuer.in_memory()

        @pgq.schedule("tick", "* * * * * */1")
        async def tick(schedule):
            pgq.shutdown.set()

        await asyncio.wait_for(pgq.sm.run(), timeout=3)
        await asyncio.wait_for(pgq.sm.run(), timeout=1)
        assert len(await pgq.sm.queries.peek_schedule()) == 1

    run(scenario())


def test_scheduler_run_marks_due_schedule_picked_and_restores_queued():
    async def scenario():
        seen = []
        pgq = PgQueuer.in_memory()

        @pgq.schedule("tick", "* * * * * */1")
        async def tick(schedule):
            seen.append(schedule.status)
            pgq.shutdown.set()

        await asyncio.wait_for(pgq.sm.run(), timeout=3)
        schedules = await pgq.sm.queries.peek_schedule()
        assert seen == ["picked"]
        assert schedules[0].status == "queued"
        assert schedules[0].last_run is not None

    run(scenario())


def test_delete_schedule_by_entrypoint_removes_matching_schedules():
    async def scenario():
        pgq = PgQueuer.in_memory()

        @pgq.schedule("a", "* * * * * */1")
        async def a(schedule):
            pgq.shutdown.set()

        @pgq.schedule("b", "* * * * * */1")
        async def b(schedule):
            pgq.shutdown.set()

        await asyncio.wait_for(pgq.sm.run(), timeout=3)
        await pgq.sm.queries.delete_schedule(set(), {"a"})
        assert [(row.entrypoint, row.status) for row in await pgq.sm.queries.peek_schedule()] == [
            ("b", "queued")
        ]

    run(scenario())


def test_clear_schedule_removes_all_schedules():
    async def scenario():
        pgq = PgQueuer.in_memory()

        @pgq.schedule("a", "* * * * * */1")
        async def a(schedule):
            pgq.shutdown.set()

        await asyncio.wait_for(pgq.sm.run(), timeout=3)
        await pgq.sm.queries.clear_schedule()
        assert await pgq.sm.queries.peek_schedule() == []

    run(scenario())


def test_schedule_dispatch_injects_schedule_context_resources_and_requeues():
    async def scenario():
        pgq = PgQueuer.in_memory(resources={"seen": []})

        @pgq.schedule("tick", "* * * * * */1")
        async def tick(schedule, ctx: ScheduleContext):
            ctx.resources["seen"].append(schedule.entrypoint)
            pgq.shutdown.set()

        await asyncio.wait_for(pgq.sm.run(), timeout=3)
        assert pgq.resources["seen"] == ["tick"]
        assert (await pgq.sm.queries.peek_schedule())[0].status == "queued"

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
