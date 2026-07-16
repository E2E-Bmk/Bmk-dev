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


def test_top_level_installable_surface_exports_core_names():
    from rq import Callback, RateLimit, SpawnWorker, Webhook

    assert Queue is not None
    assert Worker is not None
    assert SimpleWorker is not None
    assert SpawnWorker is not None
    assert Retry is not None
    assert Repeat is not None
    assert Callback is not None
    assert RateLimit is not None
    assert Webhook is not None
    assert cancel_job is not None
    assert requeue_job is not None
    assert get_current_job is not None


def test_documented_public_modules_export_scoped_classes():
    from rq.decorators import job
    from rq.worker import RandomWorker, RoundRobinWorker, WorkerStatus

    assert Job is not None
    assert Dependency is not None
    assert JobStatus.QUEUED.value == "queued"
    assert FinishedJobRegistry is not None
    assert Result is not None
    assert Group is not None
    assert JSONSerializer is not None
    assert job is not None
    assert WorkerStatus is not None
    assert RoundRobinWorker is not None
    assert RandomWorker is not None


def test_queue_requires_connection():
    with pytest.raises(TypeError):
        Queue("missing-connection")


def test_queue_default_name_and_empty_count():
    queue = make_queue()
    assert queue.name == "default"
    assert len(queue) == 0
    assert queue.count == 0
    assert queue.get_job_ids() == []


def test_get_jobs_matches_job_ids_order():
    queue = make_queue()
    first = queue.enqueue(greet, "one", job_id="one")
    second = queue.enqueue(greet, "two", job_id="two")
    assert [job.id for job in queue.get_jobs()] == [first.id, second.id]
    assert [job.id for job in queue.jobs] == queue.get_job_ids()


def test_queue_remove_removes_one_ready_job():
    queue = make_queue()
    job = queue.enqueue(greet, "remove-me", job_id="remove-me")
    queue.remove(job)
    assert queue.get_job_ids() == []
    assert queue.get_job_position(job) is None


def test_get_job_ids_supports_offset_and_length_window():
    queue = make_queue()
    queue.enqueue(greet, "a", job_id="window-a")
    queue.enqueue(greet, "b", job_id="window-b")
    queue.enqueue(greet, "c", job_id="window-c")
    assert queue.get_job_ids(offset=1, length=1) == ["window-b"]


def test_job_requires_connection():
    with pytest.raises(TypeError):
        Job()


def test_job_create_rejects_non_string_id():
    with pytest.raises(TypeError):
        Job.create(add, args=(1, 2), connection=make_connection(), id=123)


def test_job_create_rejects_id_with_invalid_characters():
    with pytest.raises(ValueError):
        Job.create(add, args=(1, 2), connection=make_connection(), id="bad/id")


def test_job_exists_tracks_persisted_job():
    connection = make_connection()
    queue = Queue(connection=connection)
    assert Job.exists("exists-job", connection) is False
    job = queue.enqueue(greet, "exists", job_id="exists-job")
    assert Job.exists(job.id, connection) is True


def test_job_fetch_missing_raises_named_error():
    with pytest.raises(Exception) as excinfo:
        Job.fetch("missing-job", connection=make_connection())
    assert excinfo.type.__name__ == "NoSuchJobError"


def test_job_fetch_many_preserves_requested_order_and_missing_slots():
    connection = make_connection()
    queue = Queue(connection=connection)
    job = queue.enqueue(greet, "many", job_id="many-job")
    fetched = Job.fetch_many(["missing", job.id], connection=connection)
    assert fetched[0] is None
    assert fetched[1].id == job.id


def test_job_metadata_round_trips_through_save_meta_and_get_meta():
    connection = make_connection()
    queue = Queue(connection=connection)
    job = queue.enqueue(current_job_meta_value, "color", meta={"color": "blue"}, job_id="meta-job")
    job.meta["color"] = "red"
    job.save_meta()
    fetched = Job.fetch(job.id, connection=connection)
    assert fetched.get_meta() == {"color": "red"}


def test_return_value_is_none_before_successful_execution():
    queue = make_queue()
    job = queue.enqueue(add, 1, 2)
    assert job.return_value() is None
    assert job.latest_result(timeout=0) is None


def test_dependency_empty_list_is_rejected():
    with pytest.raises(ValueError):
        Dependency([])


def test_dependency_rejects_unsupported_values():
    with pytest.raises(ValueError):
        Dependency([object()])


def test_repeat_rejects_non_positive_times():
    with pytest.raises(ValueError):
        Repeat(times=0)


def test_repeat_keeps_times_and_interval_configuration():
    repeat = Repeat(times=3, interval=[1, 5])
    assert repeat.times == 3
    assert repeat.intervals == [1, 5]


def test_retry_keeps_max_interval_and_front_configuration():
    retry = Retry(max=3, interval=[0, 2], enqueue_at_front=True)
    assert retry.max == 3
    assert retry.intervals == [0, 2]
    assert retry.enqueue_at_front is True


def test_json_serializer_round_trips_json_compatible_values():
    payload = {"answer": [1, 2, 3], "ok": True}
    assert JSONSerializer.loads(JSONSerializer.dumps(payload)) == payload


def test_group_fetch_missing_group_raises_named_error():
    connection = make_connection()
    with pytest.raises(Exception) as excinfo:
        Group.fetch("missing-group", connection=connection)
    assert excinfo.type.__name__ == "NoSuchGroupError"


def test_send_stop_job_command_rejects_non_executing_job_id():
    from rq.command import send_stop_job_command

    connection = make_connection()
    queue = Queue(connection=connection)
    queue.enqueue(greet, "idle", job_id="idle-job")
    with pytest.raises(Exception):
        send_stop_job_command(connection, "idle-job")

