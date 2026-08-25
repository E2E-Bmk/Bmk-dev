"""Atomic tests for rq-fullrepro-001.

Each test verifies ONE public API entry point, ONE behavior.
If only the tested API is correctly implemented, the test passes.
"""

from __future__ import annotations

import pytest

from conftest import (
    QUEUE_ALPHA,
    format_greeting,
    multiply,
)
from rq import Queue, RateLimit, Repeat, Retry, requeue_job
from rq.command import send_stop_job_command
from rq.exceptions import InvalidJobOperation, NoSuchGroupError, NoSuchJobError
from rq.group import Group
from rq.job import Dependency, Job, JobStatus
from rq.serializers import JSONSerializer


# --- Queue construction and ready-queue views ---


def test_queue_requires_connection():
    with pytest.raises(TypeError):
        Queue(QUEUE_ALPHA)


def test_queue_default_name_is_default(connection):
    assert Queue(connection=connection).name == "default"


def test_empty_queue_length_is_zero(queue):
    assert len(queue) == 0


def test_queue_count_matches_len(queue):
    queue.enqueue(format_greeting, "counted", job_id="count-one")

    assert queue.count == 1
    assert queue.count == len(queue)


def test_get_job_ids_returns_empty_for_new_queue(queue):
    assert queue.get_job_ids() == []


def test_get_job_ids_honors_offset_and_length(queue):
    queue.enqueue(format_greeting, "north", job_id="slice-a")
    queue.enqueue(format_greeting, "south", job_id="slice-b")
    queue.enqueue(format_greeting, "east", job_id="slice-c")

    assert queue.get_job_ids(offset=1, length=1) == ["slice-b"]


def test_get_jobs_matches_job_ids_order(queue):
    first = queue.enqueue(format_greeting, "alpha", job_id="order-alpha")
    second = queue.enqueue(format_greeting, "beta", job_id="order-beta")

    assert [job.id for job in queue.get_jobs()] == [first.id, second.id]
    assert [job.id for job in queue.jobs] == queue.get_job_ids()


def test_queue_remove_clears_ready_membership(queue):
    job = queue.enqueue(format_greeting, "removed", job_id="remove-target")
    queue.remove(job)

    assert queue.get_job_ids() == []


def test_get_job_position_is_none_after_remove(queue):
    job = queue.enqueue(format_greeting, "gone", job_id="position-gone")
    queue.remove(job)

    assert queue.get_job_position(job) is None


def test_fetch_job_returns_none_for_missing_id(queue):
    assert queue.fetch_job("missing-oracle-id") is None


# --- Job construction, fetch, and pre-execution views ---


def test_job_requires_connection():
    with pytest.raises(TypeError):
        Job()


def test_job_create_rejects_non_string_id(connection):
    with pytest.raises(TypeError):
        Job.create(multiply, args=(3, 4), connection=connection, id=9001)


def test_job_create_rejects_invalid_id_characters(connection):
    with pytest.raises(ValueError):
        Job.create(multiply, args=(3, 4), connection=connection, id="bad/id")


def test_job_exists_is_false_before_persistence(connection):
    assert Job.exists("fresh-id", connection) is False


def test_job_fetch_raises_no_such_job_error(connection):
    with pytest.raises(NoSuchJobError):
        Job.fetch("absent-id", connection=connection)


def test_requeue_job_missing_raises_no_such_job_error(connection):
    with pytest.raises(NoSuchJobError):
        requeue_job("absent-requeue-id", connection=connection)


def test_job_fetch_many_aligns_missing_entries_with_none(connection, queue):
    job = queue.enqueue(format_greeting, "found", job_id="found-id")
    fetched = Job.fetch_many(["missing-slot", job.id], connection=connection)

    assert fetched == [None, job]
    assert fetched[1].id == "found-id"


def test_return_value_is_none_before_execution(queue):
    job = queue.enqueue(multiply, 11, 13)

    assert job.return_value() is None
    assert job.latest_result(timeout=0) is None


def test_latest_result_returns_none_with_zero_timeout(queue):
    job = queue.enqueue(multiply, 5, 7)

    assert job.latest_result(timeout=0) is None


def test_job_status_queued_value():
    assert JobStatus.QUEUED.value == "queued"


# --- Dependency, retry, repeat, and rate-limit configuration ---


def test_dependency_empty_list_raises_value_error():
    with pytest.raises(ValueError):
        Dependency([])


def test_dependency_rejects_unsupported_values():
    with pytest.raises(ValueError):
        Dependency([object()])


def test_repeat_rejects_non_positive_times():
    with pytest.raises(ValueError):
        Repeat(times=0)


def test_repeat_exposes_times_and_intervals():
    repeat = Repeat(times=4, interval=[2, 8])

    assert repeat.times == 4
    assert repeat.intervals == [2, 8]


def test_retry_exposes_max_intervals_and_enqueue_at_front():
    retry = Retry(max=2, interval=[0, 15], enqueue_at_front=True)

    assert retry.max == 2
    assert retry.intervals == [0, 15]
    assert retry.enqueue_at_front is True


def test_rate_limit_rejects_empty_key():
    with pytest.raises(ValueError):
        RateLimit("", 2)


def test_rate_limit_rejects_concurrency_below_one():
    with pytest.raises(ValueError):
        RateLimit("cap-key", 0)


def test_rate_limit_stores_key_and_concurrency():
    limit = RateLimit("shared-cap", 3)

    assert limit.key == "shared-cap"
    assert limit.concurrency == 3


# --- Serializer, group, and command helpers ---


def test_json_serializer_round_trips_compatible_payload():
    payload = {"values": [4, 8, 15], "enabled": True}

    assert JSONSerializer.loads(JSONSerializer.dumps(payload)) == payload


def test_group_fetch_missing_raises_no_such_group_error(connection):
    with pytest.raises(NoSuchGroupError):
        Group.fetch("missing-group", connection=connection)


def test_send_stop_job_command_raises_for_idle_job(connection, queue):
    queue.enqueue(format_greeting, "idle", job_id="idle-stop")

    with pytest.raises(InvalidJobOperation):
        send_stop_job_command(connection, "idle-stop")
