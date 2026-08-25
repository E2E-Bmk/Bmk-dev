from __future__ import annotations

import importlib
import os
from pathlib import Path
from typing import Any, Callable

import fakeredis

from rq import Callback, Queue, RateLimit, Repeat, Retry, SimpleWorker
from rq.job import Dependency, Job, JobStatus
from rq.registry import CanceledJobRegistry, DeferredJobRegistry, FinishedJobRegistry
from rq.serializers import JSONSerializer


def expect(error: type[BaseException], function: Callable[[], Any]) -> BaseException:
    try:
        function()
    except error as exc:
        return exc
    raise AssertionError(f"expected {error.__name__}")


def connection() -> Any:
    return fakeredis.FakeRedis()


def native_case(root_id: str, tmp_path: Path) -> None:
    rq = importlib.import_module("rq")
    if root_id == "A01":
        root = Path(os.environ["SPEC2REPO_CANDIDATE_ROOT"]).resolve()
        assert rq.__version__ == "2.10.0"
        assert Path(rq.__file__).resolve().is_relative_to(root)
        assert all(isinstance(item, type) for item in (Queue, Job, SimpleWorker, Retry, Repeat, Callback, RateLimit))
    elif root_id == "A02":
        redis = connection(); default = Queue(connection=redis); named = Queue("critical", connection=redis)
        assert default.name == "default" and named.name == "critical"
        assert len(default) == len(named) == 0 and default.job_ids == named.job_ids == []
    elif root_id == "A03":
        retry = Retry(max=3, interval=(0, 2), enqueue_at_front=True)
        assert retry.max == 3 and retry.intervals == [0, 2] and retry.enqueue_at_front is True
        expect(ValueError, lambda: Retry(max=0)); expect(ValueError, lambda: Retry(max=1, interval=-1))
    elif root_id == "A04":
        callback = Callback("operator.add", timeout=5)
        assert callback.func == "operator.add" and callback.timeout == 5
        expect(ValueError, lambda: Callback(42))
    elif root_id == "A05":
        value = {"message": "héllo", "values": [1, True, None]}
        assert JSONSerializer.loads(JSONSerializer.dumps(value)) == value
        expect(TypeError, lambda: JSONSerializer.dumps({"bad": {1, 2}}))
    elif root_id == "A06":
        assert JobStatus.QUEUED.value == "queued" and JobStatus.FINISHED.value == "finished"
        assert JobStatus("failed") is JobStatus.FAILED
    elif root_id == "A07":
        dependency = Dependency(("parent-a", "parent-b"), allow_failure=True, enqueue_at_front=True)
        assert dependency.dependencies == ["parent-a", "parent-b"]
        assert dependency.allow_failure is True and dependency.enqueue_at_front is True
        expect(ValueError, lambda: Dependency(()))
    elif root_id == "A08":
        repeat = Repeat(times=2, interval=(0, 1)); limit = RateLimit("mail", 2)
        assert repeat.times == 2 and repeat.intervals == [0, 1]
        assert limit.key == "mail" and limit.concurrency == 2
        expect(ValueError, lambda: Repeat(times=0)); expect(ValueError, lambda: RateLimit("", 1))
    elif root_id == "I01":
        redis = connection(); queue = Queue("alpha", connection=redis)
        job = queue.enqueue("operator.add", 2, 3, job_id="job-one", meta={"owner": "alice"})
        fresh = Job.fetch(job.id, connection=redis)
        assert queue.job_ids == ["job-one"] and fresh.origin == "alpha"
        assert fresh.args == (2, 3) and fresh.meta == {"owner": "alice"}
    elif root_id == "I02":
        redis = connection(); queue = Queue("alpha", connection=redis)
        job = queue.enqueue("operator.add", 1, 4, job_id="job-meta")
        job.meta["attempt"] = 2; job.save_meta()
        fresh = Job.fetch(job.id, connection=redis)
        assert fresh.meta == {"attempt": 2} and queue.fetch_job(job.id).id == job.id
    elif root_id == "I03":
        redis = connection(); queue = Queue("batch", connection=redis)
        data = [queue.prepare_data("operator.add", (1, 2), job_id="a"), queue.prepare_data("operator.mul", (2, 3), job_id="b")]
        jobs = queue.enqueue_many(data)
        assert [job.id for job in jobs] == ["a", "b"] and queue.job_ids == ["a", "b"]
        assert [job.id if job else None for job in Job.fetch_many(("b", "missing", "a"), connection=redis)] == ["b", None, "a"]
    elif root_id == "I04":
        redis = connection(); queue = Queue("cancel", connection=redis)
        first = queue.enqueue("operator.add", 1, 2, job_id="first"); queue.enqueue("operator.add", 3, 4, job_id="sibling")
        first.cancel(); first.refresh()
        assert first.get_status() is JobStatus.CANCELED and queue.job_ids == ["sibling"]
        assert CanceledJobRegistry("cancel", connection=redis).get_job_ids() == ["first"]
    elif root_id == "S01":
        redis = connection(); queue = Queue("work", connection=redis)
        job = queue.enqueue("operator.add", 20, 22, job_id="sum")
        assert SimpleWorker((queue,), connection=redis).work(burst=True, logging_level="WARNING") is True
        fresh = Job.fetch(job.id, connection=redis)
        assert fresh.get_status() is JobStatus.FINISHED and fresh.return_value() == 42
        assert FinishedJobRegistry("work", connection=redis).get_job_ids() == ["sum"] and queue.job_ids == []
    elif root_id == "S02":
        redis = connection(); queue = Queue("graph", connection=redis)
        parent = queue.enqueue("operator.add", 1, 2, job_id="parent")
        child = queue.enqueue("operator.mul", 3, 4, job_id="child", depends_on=parent)
        assert queue.job_ids == ["parent"] and child.get_status() is JobStatus.DEFERRED
        assert DeferredJobRegistry("graph", connection=redis).get_job_ids() == ["child"]
        assert SimpleWorker((queue,), connection=redis).work(burst=True, logging_level="WARNING") is True
        parent.refresh(); child.refresh()
        assert parent.get_status() is JobStatus.FINISHED and child.get_status() is JobStatus.FINISHED
        assert child.return_value() == 12 and queue.job_ids == []
    else:
        raise KeyError(root_id)
