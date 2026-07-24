"""Integration tests for rq-fullrepro-001.

Each test crosses ≥2 public API boundaries.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from conftest import (
    QUEUE_ALPHA,
    QUEUE_BETA,
    capture_running_job_id,
    capture_worker_registration,
    echo_payload,
    format_greeting,
    make_queue,
    multiply,
    raise_runtime_failure,
    request_function_retry,
    run_cli,
    started_registry_snapshot,
    work_burst,
)
from rq import Queue, Retry, SimpleWorker, Worker, cancel_job, requeue_job
from rq.exceptions import InvalidJobOperation
from rq.group import Group
from rq.job import Dependency, Job, JobStatus
from rq.registry import (
    CanceledJobRegistry,
    DeferredJobRegistry,
    FailedJobRegistry,
    FinishedJobRegistry,
    ScheduledJobRegistry,
    StartedJobRegistry,
)
from rq.results import Result
from rq.serializers import JSONSerializer


# --- Cross-view invariants ---


def test_enqueue_job_is_fetchable(connection, queue):
    """CVI-1: enqueue projection must match Job.fetch view."""
    job = queue.enqueue(multiply, 11, 13, job_id="fetch-oracle")

    fetched = Job.fetch(job.id, connection=connection)

    assert fetched.id == "fetch-oracle"
    assert fetched.args == (11, 13)


def test_get_jobs_aligns_with_get_job_ids(queue):
    """CVI-2: ready id list and Job list must stay aligned."""
    first = queue.enqueue(format_greeting, "one", job_id="align-one")
    second = queue.enqueue(format_greeting, "two", job_id="align-two")

    assert [job.id for job in queue.get_jobs()] == queue.get_job_ids()
    assert queue.get_jobs()[0].id == first.id
    assert queue.get_jobs()[1].id == second.id


def test_at_front_job_runs_before_earlier_ready_job(connection):
    """CVI-3: at_front enqueue order must control worker dequeue order."""
    queue = make_queue(connection, QUEUE_BETA)
    first = queue.enqueue(format_greeting, "first", job_id="front-first")
    front = queue.enqueue(format_greeting, "jump", job_id="front-jump", at_front=True)

    SimpleWorker([queue], connection=connection).work(burst=True, max_jobs=1, logging_level="WARNING")

    assert Job.fetch(front.id, connection=connection).is_finished is True
    assert Job.fetch(first.id, connection=connection).get_status() == JobStatus.QUEUED


def test_enqueue_in_keeps_job_in_scheduled_registry(queue):
    """CVI-4: delayed jobs must live in scheduled registry, not ready queue."""
    job = queue.enqueue_in(timedelta(minutes=12), format_greeting, "later", job_id="later-oracle")

    assert job.get_status() == JobStatus.SCHEDULED
    assert job.id not in queue.get_job_ids()
    assert job in ScheduledJobRegistry(queue=queue)


def test_running_job_reports_started_registry_membership(connection, queue):
    """CVI-5: executing jobs must appear in StartedJobRegistry."""
    job = queue.enqueue(started_registry_snapshot, job_id="started-view")
    work_burst(queue, connection)
    snapshot = job.return_value()

    assert snapshot == {"status": "started", "in_started": True}


def test_successful_execution_updates_finished_registry_and_return_value(connection, queue):
    """CVI-6: success must finish the job and expose the return value."""
    job = queue.enqueue(multiply, 6, 7, job_id="success-oracle")
    work_burst(queue, connection)
    job.refresh()

    assert job.get_status() == JobStatus.FINISHED
    assert job.return_value() == 42
    assert job in FinishedJobRegistry(queue=queue)
    assert job not in StartedJobRegistry(queue=queue)


def test_failed_execution_updates_failed_registry_and_result(connection, queue):
    """CVI-7: terminal failure must land in FailedJobRegistry with result metadata."""
    job = queue.enqueue(raise_runtime_failure, job_id="fail-oracle")
    work_burst(queue, connection)
    job.refresh()

    assert job.get_status() == JobStatus.FAILED
    assert job in FailedJobRegistry(queue=queue)
    assert job.latest_result().type == Result.Type.FAILED
    assert "RuntimeError" in job.latest_result().exc_string


def test_cancel_moves_job_to_canceled_registry(queue):
    """CVI-8: cancel must remove ready membership and add canceled registry entry."""
    job = queue.enqueue(format_greeting, "cancel-me", job_id="cancel-oracle")
    job.cancel()
    job.refresh()

    assert job.get_status() == JobStatus.CANCELED
    assert job.id not in queue.get_job_ids()
    assert job in CanceledJobRegistry(queue=queue)


def test_failed_registry_requeue_restores_ready_queue(connection, queue):
    """CVI-9: failed registry requeue must restore ready queue membership."""
    job = queue.enqueue(raise_runtime_failure, job_id="requeue-oracle")
    work_burst(queue, connection)
    requeued = FailedJobRegistry(queue=queue).requeue(job.id)

    assert requeued.id == job.id
    assert job.id in queue.get_job_ids()
    assert job not in FailedJobRegistry(queue=queue)


def test_worker_registration_visible_during_and_cleared_after_burst(connection, queue):
    """CVI-11: a processing worker must be discoverable through Worker.all and
    Worker.count (monitoring projection) while it runs, and must deregister after
    a graceful burst exit."""
    job = queue.enqueue(capture_worker_registration, job_id="worker-view")
    SimpleWorker([queue], name="oracle-registry-worker", connection=connection).work(
        burst=True,
        logging_level="WARNING",
    )
    snapshot = job.return_value()

    assert snapshot["count"] == 1
    assert "oracle-registry-worker" in snapshot["names"]
    assert Worker.count(connection=connection) == 0
    assert Worker.all(connection=connection) == []


def test_json_serializer_queue_worker_round_trip(connection):
    """CVI-12: serializer choice must stay consistent across queue and worker."""
    queue = Queue("json-lane", connection=connection, serializer=JSONSerializer)
    job = queue.enqueue(echo_payload, 9, label="payload", job_id="json-oracle")
    work_burst(queue, connection, serializer=JSONSerializer)

    fetched = Job.fetch(job.id, connection=connection, serializer=JSONSerializer)

    assert fetched.return_value() == [[9], {"label": "payload"}]


# --- State consistency seams ---


def test_enqueue_persists_origin_status_and_arguments(queue):
    """Seam: state consistency between Queue.enqueue and Job status fields."""
    job = queue.enqueue(multiply, 17, 19, job_id="persist-oracle")

    assert job.origin == QUEUE_ALPHA
    assert job.get_status() == JobStatus.QUEUED
    assert queue.fetch_job(job.id).kwargs == {}


def test_finished_return_value_survives_job_fetch(connection, queue):
    """Seam: state consistency between worker result and Job.fetch return_value."""
    job = queue.enqueue(multiply, 8, 9, job_id="refetch-oracle")
    work_burst(queue, connection)

    fetched = Job.fetch(job.id, connection=connection)

    assert fetched.return_value() == 72


def test_enqueue_at_records_scheduled_time(queue):
    """Seam: state consistency between enqueue_at and ScheduledJobRegistry time."""
    scheduled_at = datetime.now(timezone.utc) + timedelta(minutes=20)
    job = queue.enqueue_at(scheduled_at, format_greeting, "timed", job_id="at-oracle")
    recorded = ScheduledJobRegistry(queue=queue).get_scheduled_time(job)

    assert recorded.replace(microsecond=0) == scheduled_at.replace(microsecond=0)


def test_result_history_records_successful_return_value(connection, queue):
    """Seam: state consistency between return_value and results history."""
    job = queue.enqueue(multiply, 10, 11, job_id="history-oracle")
    work_burst(queue, connection)
    fetched = Job.fetch(job.id, connection=connection)

    results = fetched.results()

    assert len(results) == 1
    assert results[0].return_value == 110
    assert results[0].job_id == job.id


def test_queue_all_lists_queue_after_enqueue(connection):
    """Seam: state consistency between Queue.all and enqueue side effects."""
    queue = make_queue(connection, "listed-queue")
    queue.enqueue(format_greeting, "listed", job_id="listed-job")

    assert [item.name for item in Queue.all(connection=connection)] == ["listed-queue"]


def test_group_enqueue_many_links_jobs_to_group(connection, queue):
    """Seam: state consistency between Group.enqueue_many and group.get_jobs."""
    group = Group.create(connection=connection, name="batch-oracle")
    data = [
        queue.prepare_data(format_greeting, args=("batch-a",), job_id="batch-a"),
        queue.prepare_data(format_greeting, args=("batch-b",), job_id="batch-b"),
    ]
    jobs = group.enqueue_many(queue, data)

    assert {job.id for job in group.get_jobs()} == {job.id for job in jobs}


def test_get_current_job_matches_executed_job_id(connection, queue):
    """Seam: state consistency between worker execution and get_current_job."""
    job = queue.enqueue(capture_running_job_id, job_id="current-oracle")
    work_burst(queue, connection)

    assert job.return_value() == "current-oracle"


# --- Lifecycle crossing seams ---


def test_job_requeue_helper_restores_ready_queue(connection, queue):
    """Seam: lifecycle crossing from failed registry back to ready queue via Job.requeue."""
    job = queue.enqueue(raise_runtime_failure, job_id="job-requeue-oracle")
    work_burst(queue, connection)
    requeued = Job.fetch(job.id, connection=connection).requeue()

    assert requeued.id == job.id
    assert queue.get_job_ids() == [job.id]


def test_requeue_job_function_restores_ready_queue(connection, queue):
    """Seam: lifecycle crossing through requeue_job helper."""
    job = queue.enqueue(raise_runtime_failure, job_id="helper-requeue-oracle")
    work_burst(queue, connection)
    requeued = requeue_job(job.id, connection=connection)

    assert requeued.id == job.id
    assert job.id in queue.get_job_ids()


def test_cancel_job_helper_updates_status_and_registry(connection, queue):
    """Seam: lifecycle crossing through cancel_job helper and registry views."""
    job = queue.enqueue(format_greeting, "helper-cancel", job_id="helper-cancel-oracle")
    cancel_job(job.id, connection=connection)
    fetched = Job.fetch(job.id, connection=connection)

    assert fetched.get_status() == JobStatus.CANCELED
    assert fetched in CanceledJobRegistry(queue=queue)


def test_delete_removes_job_from_registry_views(queue):
    """Seam: lifecycle crossing through cancel then delete cleanup."""
    job = queue.enqueue(format_greeting, "delete-me", job_id="delete-oracle")
    job.cancel()
    job.delete()

    assert queue.fetch_job(job.id) is None
    assert job not in CanceledJobRegistry(queue=queue)


def test_worker_burst_drains_all_ready_jobs(connection, queue):
    """Seam: lifecycle crossing from queued through worker burst to finished."""
    first = queue.enqueue(multiply, 2, 3, job_id="burst-a")
    second = queue.enqueue(multiply, 4, 5, job_id="burst-b")
    assert work_burst(queue, connection) is True

    assert Job.fetch(first.id, connection=connection).return_value() == 6
    assert Job.fetch(second.id, connection=connection).return_value() == 20
    assert len(queue) == 0


def test_dependency_defers_until_parent_completes(connection, queue):
    """Seam: lifecycle crossing from deferred registry to finished dependent."""
    parent = queue.enqueue(multiply, 2, 2, job_id="dep-parent")
    child = queue.enqueue(format_greeting, "dependent", depends_on=parent, job_id="dep-child")

    assert child.get_status() == JobStatus.DEFERRED
    assert child in DeferredJobRegistry(queue=queue)
    work_burst(queue, connection)
    fetched = Job.fetch(child.id, connection=connection)

    assert fetched.get_status() == JobStatus.FINISHED
    assert fetched.return_value() == "Hello, dependent!"
    assert fetched not in DeferredJobRegistry(queue=queue)


# --- Config interaction seams ---


def test_sync_queue_executes_success_immediately(connection):
    """Seam: config interaction between is_async=False and finished state."""
    sync_queue = Queue("sync-lane", connection=connection, is_async=False)
    job = sync_queue.enqueue(multiply, 6, 7, job_id="sync-success")

    assert job.get_status() == JobStatus.FINISHED
    assert job.return_value() == 42
    assert len(sync_queue) == 0


def test_sync_queue_records_failure_in_failed_registry(connection):
    """Seam: config interaction between is_async=False and failure registries."""
    sync_queue = Queue("sync-fail", connection=connection, is_async=False)
    job = sync_queue.enqueue(raise_runtime_failure, job_id="sync-fail")

    assert job.get_status() == JobStatus.FAILED
    assert job in FailedJobRegistry(queue=sync_queue)


def test_dependency_allow_failure_enqueues_after_failed_parent(connection, queue):
    """Seam: config interaction between Dependency.allow_failure and enqueue policy."""
    parent = queue.enqueue(raise_runtime_failure, job_id="allow-parent")
    child = queue.enqueue(
        format_greeting,
        "after-fail",
        depends_on=Dependency(parent, allow_failure=True),
        job_id="allow-child",
    )
    work_burst(queue, connection)
    fetched = Job.fetch(child.id, connection=connection)

    assert fetched.get_status() == JobStatus.FINISHED
    assert fetched.return_value() == "Hello, after-fail!"


def test_worker_prefers_first_non_empty_queue(connection):
    """Seam: config interaction between queue order and worker dequeue strategy."""
    high = make_queue(connection, "priority-high")
    low = make_queue(connection, "priority-low")
    low_job = low.enqueue(format_greeting, "low", job_id="prio-low")
    high_job = high.enqueue(format_greeting, "high", job_id="prio-high")

    SimpleWorker([high, low], connection=connection).work(
        burst=True,
        max_jobs=1,
        logging_level="WARNING",
    )

    assert Job.fetch(high_job.id, connection=connection).is_finished is True
    assert Job.fetch(low_job.id, connection=connection).get_status() == JobStatus.QUEUED


def test_worker_max_jobs_limits_processed_count(connection, queue):
    """Seam: config interaction between max_jobs and remaining ready queue."""
    first = queue.enqueue(multiply, 3, 3, job_id="max-a")
    second = queue.enqueue(multiply, 4, 4, job_id="max-b")

    SimpleWorker([queue], connection=connection).work(
        burst=True,
        max_jobs=1,
        logging_level="WARNING",
    )

    assert Job.fetch(first.id, connection=connection).get_status() == JobStatus.FINISHED
    assert Job.fetch(second.id, connection=connection).get_status() == JobStatus.QUEUED


def test_enqueue_many_preserves_batch_order(queue):
    """Seam: protocol handoff between prepare_data and enqueue_many."""
    data = [
        queue.prepare_data(multiply, args=(2, 3), job_id="many-a"),
        queue.prepare_data(multiply, args=(5, 6), job_id="many-b"),
    ]
    jobs = queue.enqueue_many(data)

    assert [job.id for job in jobs] == ["many-a", "many-b"]
    assert queue.get_job_ids() == ["many-a", "many-b"]


# --- Error propagation seams ---


def test_exception_retry_exhaustion_leaves_terminal_failed_status(connection, queue):
    """Seam: error propagation from Retry configuration to terminal failed status."""
    job = queue.enqueue(
        raise_runtime_failure,
        retry=Retry(max=1, interval=0),
        job_id="retry-oracle",
    )
    work_burst(queue, connection)
    fetched = Job.fetch(job.id, connection=connection)

    assert fetched.get_status() == JobStatus.FAILED
    assert [result.type for result in fetched.results()] == [Result.Type.FAILED]


def test_return_based_retry_records_max_retries_exceeded(connection, queue):
    """Seam: error propagation from return-based Retry to result history."""
    job = queue.enqueue(request_function_retry, job_id="return-retry-oracle")
    work_burst(queue, connection)
    fetched = Job.fetch(job.id, connection=connection)

    assert fetched.get_status() == JobStatus.FAILED
    assert fetched.results()[0].type == Result.Type.MAX_RETRIES_EXCEEDED


def test_requeue_non_failed_job_raises_invalid_job_operation(connection, queue):
    """Seam: error propagation when requeue targets a non-failed job."""
    job = queue.enqueue(format_greeting, "still-queued", job_id="invalid-requeue")

    with pytest.raises(InvalidJobOperation):
        Job.fetch(job.id, connection=connection).requeue()


def test_cli_invalid_command_exits_two():
    """Seam: error propagation from invalid CLI invocation to exit code 2."""
    completed = run_cli("not-a-real-command")

    assert completed.returncode == 2


# --- CLI protocol handoff ---


def test_cli_help_exits_zero():
    """CVI-10: the operator CLI must be wired to the same library command group as
    python -m rq.cli, exposing info/worker/enqueue and exiting 0 for help."""
    completed = run_cli("--help")

    assert completed.returncode == 0
    assert "worker" in completed.stdout
    assert "enqueue" in completed.stdout
    assert "info" in completed.stdout


def test_cli_worker_help_exits_zero():
    """Seam: protocol handoff from worker subcommand help to exit status 0."""
    completed = run_cli("worker", "--help")

    assert completed.returncode == 0
    assert "burst" in completed.stdout
