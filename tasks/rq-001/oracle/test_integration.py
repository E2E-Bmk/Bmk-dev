# Generated behavioral oracle tests for rq-001.

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import subprocess
import sys

import pytest
from fakeredis import FakeRedis

from rq import Queue, Repeat, Retry, SimpleWorker, Worker, cancel_job, get_current_job, requeue_job
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


def add(x, y):
    return x + y


def echo_args(*args, **kwargs):
    return args, kwargs


def greet(name="Stranger"):
    return f"Hi there, {name}!"


def fail_with_value_error():
    raise ValueError("generated failure")


def current_job_id():
    return get_current_job().id


def current_job_meta_value(key):
    return get_current_job().meta[key]


def return_retry_once():
    return Retry(max=1)


def make_connection():
    return FakeRedis()


def make_queue(name="default", **kwargs):
    return Queue(name, connection=make_connection(), **kwargs)


def work_one_queue(queue, connection):
    return SimpleWorker([queue], connection=connection).work(burst=True, logging_level="WARNING")


def test_queue_all_lists_known_queue_after_enqueue():
    connection = make_connection()
    queue = Queue("alpha", connection=connection)
    queue.enqueue(add, 1, 2)
    assert [q.name for q in Queue.all(connection=connection)] == ["alpha"]


def test_enqueue_persists_job_status_origin_and_arguments():
    queue = make_queue("critical")
    job = queue.enqueue(add, 2, 5, job_id="add_2_5")
    assert job.id == "add_2_5"
    assert job.origin == "critical"
    assert job.get_status() == JobStatus.QUEUED
    assert queue.fetch_job(job.id).args == (2, 5)


def test_enqueue_at_front_changes_ready_order():
    queue = make_queue()
    first = queue.enqueue(greet, "first", job_id="first")
    second = queue.enqueue(greet, "second", job_id="second", at_front=True)
    assert queue.get_job_ids() == [second.id, first.id]
    assert queue.get_job_position(second) == 0


def test_successful_simple_worker_execution_records_finished_result():
    connection = make_connection()
    queue = Queue(connection=connection)
    job = queue.enqueue(add, 2, 3, job_id="success-job")
    assert work_one_queue(queue, connection) is True
    job.refresh()
    assert job.get_status() == JobStatus.FINISHED
    assert job.return_value() == 5
    assert job in FinishedJobRegistry(queue=queue)
    assert job.latest_result().type == Result.Type.SUCCESSFUL


def test_failed_simple_worker_execution_records_failed_registry_and_exception_info():
    connection = make_connection()
    queue = Queue(connection=connection)
    job = queue.enqueue(fail_with_value_error, job_id="failed-job")
    assert work_one_queue(queue, connection) is True
    job.refresh()
    assert job.get_status() == JobStatus.FAILED
    assert job in FailedJobRegistry(queue=queue)
    assert "ValueError" in job.exc_info
    assert job.latest_result().type == Result.Type.FAILED


def test_finished_job_return_value_survives_refetch():
    connection = make_connection()
    queue = Queue(connection=connection)
    job = queue.enqueue(add, 7, 8, job_id="refetch-result")
    work_one_queue(queue, connection)
    fetched = Job.fetch(job.id, connection=connection)
    assert fetched.return_value() == 15
    assert fetched.result == 15


def test_failed_registry_requeue_moves_job_back_to_ready_queue():
    connection = make_connection()
    queue = Queue(connection=connection)
    job = queue.enqueue(fail_with_value_error, job_id="requeue-failed")
    work_one_queue(queue, connection)
    requeued = FailedJobRegistry(queue=queue).requeue(job.id)
    assert requeued.id == job.id
    assert job.id in queue.get_job_ids()
    assert job not in FailedJobRegistry(queue=queue)


def test_job_requeue_returns_failed_job_to_origin_queue():
    connection = make_connection()
    queue = Queue(connection=connection)
    job = queue.enqueue(fail_with_value_error, job_id="job-requeue")
    work_one_queue(queue, connection)
    requeued = Job.fetch(job.id, connection=connection).requeue()
    assert requeued.id == job.id
    assert queue.get_job_ids() == [job.id]


def test_requeue_job_helper_returns_failed_job_to_queue():
    connection = make_connection()
    queue = Queue(connection=connection)
    job = queue.enqueue(fail_with_value_error, job_id="helper-requeue")
    work_one_queue(queue, connection)
    requeued = requeue_job(job.id, connection=connection)
    assert requeued.id == job.id
    assert job.id in queue.get_job_ids()


def test_cancel_queued_job_moves_to_canceled_registry():
    queue = make_queue()
    job = queue.enqueue(greet, "cancel", job_id="cancel-job")
    job.cancel()
    job.refresh()
    assert job.get_status() == JobStatus.CANCELED
    assert job.id not in queue.get_job_ids()
    assert job in CanceledJobRegistry(queue=queue)


def test_cancel_job_helper_cancels_by_id():
    connection = make_connection()
    queue = Queue(connection=connection)
    job = queue.enqueue(greet, "cancel-helper", job_id="cancel-helper")
    cancel_job(job.id, connection=connection)
    fetched = Job.fetch(job.id, connection=connection)
    assert fetched.get_status() == JobStatus.CANCELED
    assert fetched in CanceledJobRegistry(queue=queue)


def test_delete_job_removes_queue_and_registry_membership():
    queue = make_queue()
    job = queue.enqueue(greet, "delete-job", job_id="delete-record")
    job.cancel()
    job.delete()
    assert queue.fetch_job(job.id) is None
    assert job not in CanceledJobRegistry(queue=queue)


def test_enqueue_in_creates_scheduled_job_not_ready_job():
    queue = make_queue()
    job = queue.enqueue_in(timedelta(minutes=5), greet, "later", job_id="later-job")
    assert job.get_status() == JobStatus.SCHEDULED
    assert job.id not in queue.get_job_ids()
    assert job in ScheduledJobRegistry(queue=queue)


def test_enqueue_at_records_scheduled_time():
    queue = make_queue()
    scheduled_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    job = queue.enqueue_at(scheduled_at, greet, "at-time", job_id="at-time-job")
    recorded = ScheduledJobRegistry(queue=queue).get_scheduled_time(job)
    assert recorded.replace(microsecond=0) == scheduled_at.replace(microsecond=0)


def test_sync_queue_executes_success_immediately():
    queue = Queue("sync", connection=make_connection(), is_async=False)
    job = queue.enqueue(add, 20, 22, job_id="sync-success")
    assert job.get_status() == JobStatus.FINISHED
    assert job.return_value() == 42
    assert len(queue) == 0


def test_sync_queue_records_failed_state_on_exception():
    queue = Queue("sync", connection=make_connection(), is_async=False)
    job = queue.enqueue(fail_with_value_error, job_id="sync-failure")
    assert job.get_status() == JobStatus.FAILED
    assert job in FailedJobRegistry(queue=queue)


def test_dependency_places_dependent_job_in_deferred_registry():
    queue = make_queue()
    parent = queue.enqueue(add, 1, 1, job_id="parent")
    child = queue.enqueue(greet, "child", depends_on=parent, job_id="child")
    assert child.get_status() == JobStatus.DEFERRED
    assert child.id not in queue.get_job_ids()
    assert child in DeferredJobRegistry(queue=queue)


def test_finished_dependency_enqueues_dependent_after_worker_run():
    connection = make_connection()
    queue = Queue(connection=connection)
    parent = queue.enqueue(add, 1, 2, job_id="parent-finish")
    child = queue.enqueue(greet, "child", depends_on=parent, job_id="child-finish")
    work_one_queue(queue, connection)
    fetched = Job.fetch(child.id, connection=connection)
    assert fetched.get_status() == JobStatus.FINISHED
    assert fetched.return_value() == "Hi there, child!"
    assert fetched not in DeferredJobRegistry(queue=queue)


def test_dependency_allow_failure_enqueues_dependent_after_failed_parent():
    connection = make_connection()
    queue = Queue(connection=connection)
    parent = queue.enqueue(fail_with_value_error, job_id="parent-fail")
    child = queue.enqueue(greet, "child", depends_on=Dependency(parent, allow_failure=True), job_id="child-after-fail")
    work_one_queue(queue, connection)
    fetched = Job.fetch(child.id, connection=connection)
    assert fetched.get_status() == JobStatus.FINISHED
    assert fetched.return_value() == "Hi there, child!"


def test_enqueue_many_with_prepared_data_returns_jobs_in_order():
    queue = make_queue()
    data = [
        queue.prepare_data(add, args=(1, 2), job_id="many-one"),
        queue.prepare_data(add, args=(3, 4), job_id="many-two"),
    ]
    jobs = queue.enqueue_many(data)
    assert [job.id for job in jobs] == ["many-one", "many-two"]
    assert queue.get_job_ids() == ["many-one", "many-two"]


def test_group_enqueue_many_attaches_jobs_to_group():
    connection = make_connection()
    queue = Queue(connection=connection)
    group = Group.create(connection=connection, name="batch")
    data = [
        queue.prepare_data(greet, args=("a",), job_id="batch-a"),
        queue.prepare_data(greet, args=("b",), job_id="batch-b"),
    ]
    jobs = group.enqueue_many(queue, data)
    assert {job.id for job in group.get_jobs()} == {job.id for job in jobs}


def test_get_current_job_inside_execution_returns_running_job_id():
    connection = make_connection()
    queue = Queue(connection=connection)
    job = queue.enqueue(current_job_id, job_id="current-job")
    work_one_queue(queue, connection)
    assert job.return_value() == "current-job"


def test_worker_default_queue_priority_processes_first_non_empty_queue():
    connection = make_connection()
    high = Queue("high", connection=connection)
    low = Queue("low", connection=connection)
    low_job = low.enqueue(greet, "low", job_id="low-job")
    high_job = high.enqueue(greet, "high", job_id="high-job")
    SimpleWorker([high, low], connection=connection).work(burst=True, max_jobs=1, logging_level="WARNING")
    assert Job.fetch(high_job.id, connection=connection).get_status() == JobStatus.FINISHED
    assert Job.fetch(low_job.id, connection=connection).get_status() == JobStatus.QUEUED


def test_worker_burst_processes_all_available_jobs_and_returns_true():
    connection = make_connection()
    queue = Queue(connection=connection)
    first = queue.enqueue(add, 1, 1, job_id="burst-one")
    second = queue.enqueue(add, 2, 2, job_id="burst-two")
    result = SimpleWorker([queue], connection=connection).work(burst=True, logging_level="WARNING")
    assert result is True
    assert Job.fetch(first.id, connection=connection).return_value() == 2
    assert Job.fetch(second.id, connection=connection).return_value() == 4
    assert len(queue) == 0


def test_worker_all_and_count_are_empty_after_graceful_burst_exit():
    connection = make_connection()
    queue = Queue(connection=connection)
    Worker([queue], name="done-worker", connection=connection).work(burst=True, logging_level="WARNING")
    assert Worker.count(connection=connection) == 0
    assert Worker.all(connection=connection) == []


def test_worker_max_jobs_limits_burst_processing():
    connection = make_connection()
    queue = Queue(connection=connection)
    first = queue.enqueue(add, 1, 3, job_id="max-one")
    second = queue.enqueue(add, 5, 8, job_id="max-two")
    SimpleWorker([queue], connection=connection).work(burst=True, max_jobs=1, logging_level="WARNING")
    assert Job.fetch(first.id, connection=connection).get_status() == JobStatus.FINISHED
    assert Job.fetch(second.id, connection=connection).get_status() == JobStatus.QUEUED


def test_result_history_records_newest_result_for_success():
    connection = make_connection()
    queue = Queue(connection=connection)
    job = queue.enqueue(add, 9, 1, job_id="result-history")
    work_one_queue(queue, connection)
    results = Job.fetch(job.id, connection=connection).results()
    assert len(results) == 1
    assert results[0].return_value == 10
    assert results[0].job_id == job.id


def test_exception_retry_with_zero_interval_requeues_then_fails_terminally():
    connection = make_connection()
    queue = Queue(connection=connection)
    job = queue.enqueue(fail_with_value_error, retry=Retry(max=1, interval=0), job_id="retry-zero")
    work_one_queue(queue, connection)
    fetched = Job.fetch(job.id, connection=connection)
    assert fetched.get_status() == JobStatus.FAILED
    assert [result.type for result in fetched.results()] == [Result.Type.FAILED]


def test_return_based_retry_records_retried_result():
    connection = make_connection()
    queue = Queue(connection=connection)
    job = queue.enqueue(return_retry_once, job_id="return-retry")
    work_one_queue(queue, connection)
    fetched = Job.fetch(job.id, connection=connection)
    assert fetched.get_status() == JobStatus.FAILED
    assert fetched.results()[0].type == Result.Type.MAX_RETRIES_EXCEEDED


def test_json_serializer_queue_and_worker_preserve_arguments_and_result():
    connection = make_connection()
    queue = Queue("json", connection=connection, serializer=JSONSerializer)
    job = queue.enqueue(echo_args, 1, keyword="value", job_id="json-job")
    SimpleWorker([queue], connection=connection, serializer=JSONSerializer).work(burst=True, logging_level="WARNING")
    assert Job.fetch(job.id, connection=connection, serializer=JSONSerializer).return_value() == [[1], {"keyword": "value"}]


def test_cli_help_exits_zero_and_lists_core_commands():
    completed = subprocess.run(
        [sys.executable, "-m", "rq.cli", "--help"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0
    assert "worker" in completed.stdout
    assert "enqueue" in completed.stdout
    assert "info" in completed.stdout


def test_cli_invalid_command_exits_nonzero():
    completed = subprocess.run(
        [sys.executable, "-m", "rq.cli", "not-a-command"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 2


def test_cli_worker_help_exits_zero():
    completed = subprocess.run(
        [sys.executable, "-m", "rq.cli", "worker", "--help"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0
    assert "burst" in completed.stdout
    assert "queue" in completed.stdout.lower()

