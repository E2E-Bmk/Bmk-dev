from __future__ import annotations

from datetime import timedelta

import pytest

import dramatiq
from dramatiq import Message, Middleware, Worker, group, pipeline
from dramatiq.errors import QueueNotFound, Retry
from dramatiq.encoder import PickleEncoder
from dramatiq.middleware import GroupCallbacks, SkipMessage
from dramatiq.rate_limits import Barrier, ConcurrentRateLimiter
from dramatiq.rate_limits.backends import StubBackend as RateLimitStubBackend
from dramatiq.results import ResultFailure, ResultMissing, Results
from dramatiq.results.backends import StubBackend as ResultStubBackend


@pytest.mark.depends_on("test_actor_message_contains_positional_and_keyword_arguments")
def test_stub_broker_send_consume_and_ack_preserves_message_fields(stub_broker):
    @dramatiq.actor
    def work(value):
        return value

    sent = work.send("payload")
    consumer = stub_broker.consume("default")
    received = next(consumer)
    consumer.ack(received)
    consumer.close()

    assert received.message_id == sent.message_id
    assert received.args == ("payload",)
    assert received.actor_name == "work"


@pytest.mark.depends_on("test_message_proxy_forwards_fields_and_can_be_marked_failed")
def test_stub_broker_nack_moves_message_to_dead_letters(stub_broker):
    @dramatiq.actor
    def work():
        return None

    work.send()
    consumer = stub_broker.consume("default")
    received = next(consumer)
    consumer.nack(received)
    consumer.close()

    assert len(stub_broker.dead_letters) == 1
    assert stub_broker.dead_letters[0].actor_name == "work"


@pytest.mark.depends_on("test_actor_direct_call_returns_underlying_result")
def test_worker_processes_positional_and_keyword_actor_messages(stub_broker, stub_worker):
    results = []

    @dramatiq.actor
    def add(left, right):
        results.append(left + right)

    add.send(2, 5)
    add.send(left=7, right=4)
    stub_broker.join(add.queue_name)
    stub_worker.join()

    assert results == [7, 11]


@pytest.mark.depends_on("test_actor_metadata_options_are_public")
def test_worker_processes_actor_on_custom_queue(stub_broker, stub_worker):
    results = []

    @dramatiq.actor(queue_name="custom_jobs")
    def work(value):
        results.append(value)

    work.send("queued")
    stub_broker.join("custom_jobs")
    stub_worker.join()

    assert results == ["queued"]


@pytest.mark.depends_on("test_stub_broker_declares_normal_and_delay_queues")
def test_stub_broker_flush_removes_queued_messages_and_dead_letters(stub_broker):
    @dramatiq.actor
    def work():
        return None

    work.send()
    consumer = stub_broker.consume("default")
    received = next(consumer)
    consumer.nack(received)
    consumer.close()
    work.send()

    stub_broker.flush_all()

    assert stub_broker.dead_letters == []
    assert stub_broker.queues["default"].unfinished_tasks == 0
    assert stub_broker.queues["default"].qsize() == 0


@pytest.mark.depends_on("test_message_with_options_converts_callback_actor_to_name")
@pytest.mark.suppress_logs("dramatiq.worker.WorkerThread")
def test_success_callback_receives_original_message_and_result(stub_broker, stub_worker):
    calls = []

    @dramatiq.actor
    def callback(message_data, result):
        calls.append((message_data["actor_name"], result))

    @dramatiq.actor(on_success=callback.actor_name)
    def work():
        return "complete"

    work.send()
    stub_broker.join(work.queue_name)
    stub_broker.join(callback.queue_name)
    stub_worker.join()

    assert calls == [("work", "complete")]


@pytest.mark.depends_on('test_message_with_options_converts_callback_actor_to_name')
@pytest.mark.suppress_logs("dramatiq.worker.WorkerThread", "dramatiq.middleware.retries.Retries")
def test_failure_callback_receives_exception_metadata(stub_broker, stub_worker):
    failures = []

    @dramatiq.actor
    def callback(message_data, error_data):
        failures.append((message_data["actor_name"], error_data["type"]))

    @dramatiq.actor(max_retries=0, on_failure=callback.actor_name)
    def work():
        raise ValueError("bad value")

    work.send()
    stub_broker.join(work.queue_name, fail_fast=False)
    stub_worker.join()

    assert failures == [("work", "ValueError")]


@pytest.mark.depends_on("test_result_backend_stores_and_retrieves_result")
def test_results_middleware_stores_actor_result_for_message(stub_broker, stub_worker, result_backend):
    stub_broker.add_middleware(Results(backend=result_backend))

    @dramatiq.actor(store_results=True)
    def work():
        return {"value": 12}

    message = work.send()
    stub_broker.join(work.queue_name)
    stub_worker.join()

    assert message.get_result(backend=result_backend) == {"value": 12}
    assert stub_broker.get_results_backend() is result_backend


@pytest.mark.depends_on("test_result_backend_stored_exception_raises_result_failure")
@pytest.mark.suppress_logs("dramatiq.worker.WorkerThread", "dramatiq.middleware.retries.Retries")
def test_results_middleware_projects_actor_failure_as_result_failure(stub_broker, stub_worker, result_backend):
    stub_broker.add_middleware(Results(backend=result_backend))

    @dramatiq.actor(store_results=True, max_retries=0)
    def work():
        raise LookupError("missing record")

    message = work.send()
    stub_broker.join(work.queue_name, fail_fast=False)
    stub_worker.join()

    with pytest.raises(ResultFailure) as error:
        message.get_result(backend=result_backend)

    assert error.value.orig_exc_type == "LookupError"


@pytest.mark.depends_on("test_result_backend_missing_result_raises_result_missing")
@pytest.mark.suppress_logs("dramatiq.worker.WorkerThread")
def test_actor_without_results_option_has_no_retrievable_result(stub_broker, stub_worker):
    @dramatiq.actor
    def work():
        return "discarded"

    message = work.send()
    stub_broker.join(work.queue_name)
    stub_worker.join()

    with pytest.raises(RuntimeError):
        message.get_result()


@pytest.mark.depends_on("test_message_copy_replaces_fields_and_merges_options")
def test_message_get_result_can_infer_backend_from_global_broker(stub_broker, stub_worker, result_backend):
    stub_broker.add_middleware(Results(backend=result_backend))

    @dramatiq.actor(store_results=True)
    def work():
        return 27

    message = work.send()
    stub_broker.join(work.queue_name)
    stub_worker.join()

    assert message.get_result(block=True) == 27


@pytest.mark.depends_on("test_message_with_options_converts_callback_actor_to_name")
def test_pipeline_runs_messages_in_order_and_exposes_each_result(stub_broker, stub_worker, result_backend):
    stub_broker.add_middleware(Results(backend=result_backend))

    @dramatiq.actor(store_results=True)
    def add(left, right):
        return left + right

    pipe = add.message(1, 2) | add.message(3) | add.message(4)
    assert pipe.run() is pipe
    stub_broker.join(add.queue_name)
    stub_worker.join()

    assert list(pipe.get_results()) == [3, 6, 10]
    assert pipe.get_result() == 10
    assert pipe.completed is True
    assert pipe.completed_count == 3


@pytest.mark.depends_on('test_message_with_options_converts_callback_actor_to_name')
def test_pipeline_flattens_nested_pipeline_before_running(stub_broker, stub_worker, result_backend):
    stub_broker.add_middleware(Results(backend=result_backend))

    @dramatiq.actor(store_results=True)
    def add(*values):
        return sum(values)

    inner = add.message(2, 3) | add.message(4)
    outer = pipeline([add.message(1, 1), inner, add.message(5)])

    assert len(outer) == 4
    outer.run()
    stub_broker.join(add.queue_name)
    stub_worker.join()

    assert list(outer.get_results()) == [2, 7, 11, 16]


@pytest.mark.depends_on('test_message_with_options_converts_callback_actor_to_name')
def test_pipeline_pipe_ignore_uses_receiving_message_arguments(stub_broker, stub_worker, result_backend):
    stub_broker.add_middleware(Results(backend=result_backend))

    @dramatiq.actor(store_results=True)
    def collect(*values):
        return list(values)

    pipe = collect.message("first") | collect.message_with_options(pipe_ignore=True, args=("second",)) | collect.message(
        "third"
    )
    pipe.run()
    stub_broker.join(collect.queue_name)
    stub_worker.join()

    assert list(pipe.get_results()) == [["first"], ["second"], ["third", ["second"]]]


@pytest.mark.depends_on('test_message_with_options_converts_callback_actor_to_name')
def test_incomplete_pipeline_reports_missing_completion_without_worker(stub_broker, result_backend):
    stub_broker.add_middleware(Results(backend=result_backend))

    @dramatiq.actor(store_results=True)
    def work():
        return "later"

    pipe = work.message() | work.message()
    pipe.run()

    assert pipe.completed is False
    with pytest.raises(ResultMissing):
        pipe.get_result()


@pytest.mark.depends_on('test_result_backend_stores_and_retrieves_result')
def test_group_runs_children_and_returns_results(stub_broker, stub_worker, result_backend):
    stub_broker.add_middleware(Results(backend=result_backend))

    @dramatiq.actor(store_results=True)
    def square(value):
        return value * value

    jobs = group([square.message(2), square.message(4), square.message(5)])
    assert jobs.run() is jobs
    stub_broker.join(square.queue_name)
    stub_worker.join()

    assert list(jobs.get_results()) == [4, 16, 25]
    assert jobs.completed_count == 3
    assert jobs.completed is True


@pytest.mark.depends_on('test_result_backend_stores_and_retrieves_result')
def test_nested_group_returns_nested_result_lists(stub_broker, stub_worker, result_backend):
    stub_broker.add_middleware(Results(backend=result_backend))

    @dramatiq.actor(store_results=True)
    def identify(value):
        return value

    jobs = group([group([identify.message("a"), identify.message("b")]), group([identify.message("c")])])
    jobs.run()
    stub_broker.join(identify.queue_name)
    stub_worker.join()

    assert list(jobs.get_results()) == [["a", "b"], ["c"]]


@pytest.mark.depends_on('test_result_backend_stores_and_retrieves_result')
def test_group_wait_completes_after_worker_finishes(stub_broker, stub_worker, result_backend):
    stub_broker.add_middleware(Results(backend=result_backend))

    @dramatiq.actor(store_results=True)
    def work(value):
        return value

    jobs = group([work.message(8), work.message(9)])
    jobs.run()
    jobs.wait()

    assert jobs.completed is True


@pytest.mark.depends_on('test_result_backend_stores_and_retrieves_result')
def test_group_completion_callback_runs_after_all_children(stub_broker, stub_worker, rate_limiter_backend):
    calls = []
    stub_broker.add_middleware(GroupCallbacks(rate_limiter_backend, barrier_ttl=5000))

    @dramatiq.actor
    def callback():
        calls.append("callback")

    @dramatiq.actor
    def work():
        return None

    jobs = group([work.message(), work.message()])
    jobs.add_completion_callback(callback.message())
    jobs.run()
    stub_broker.join(work.queue_name)
    stub_broker.join(callback.queue_name)
    stub_worker.join()

    assert calls == ["callback"]


@pytest.mark.depends_on('test_result_backend_stores_and_retrieves_result')
def test_group_callback_requires_group_callbacks_middleware(stub_broker):
    @dramatiq.actor
    def callback():
        return None

    @dramatiq.actor
    def work():
        return None

    jobs = group([work.message()])
    jobs.add_completion_callback(callback.message())

    with pytest.raises(RuntimeError):
        jobs.run()


@pytest.mark.depends_on('test_result_backend_stores_and_retrieves_result')
def test_group_of_pipelines_returns_pipeline_results(stub_broker, stub_worker, result_backend):
    stub_broker.add_middleware(Results(backend=result_backend))

    @dramatiq.actor(store_results=True)
    def add(left, right):
        return left + right

    first = add.message(1, 1) | add.message(2)
    second = add.message(3, 4) | add.message(5)
    jobs = group([first, second])
    jobs.run()
    stub_broker.join(add.queue_name)
    stub_worker.join()

    assert list(jobs.get_results()) == [4, 12]


@pytest.mark.depends_on("test_broker_add_middleware_exposes_actor_options")
@pytest.mark.suppress_logs("dramatiq.worker.WorkerThread")
def test_custom_middleware_receives_declaration_and_processing_hooks(stub_broker, stub_worker):
    events = []

    class Recorder(Middleware):
        @property
        def actor_options(self):
            return {"record_tag"}

        def after_declare_actor(self, broker, actor):
            events.append(("declare", actor.actor_name))

        def before_process_message(self, broker, message):
            events.append(("before", message.actor_name))

        def after_process_message(self, broker, message, *, result=None, exception=None):
            events.append(("after", result, exception is None))

    recorder = Recorder()
    stub_broker.add_middleware(recorder)

    @dramatiq.actor(record_tag="sample")
    def work():
        return "done"

    work.send()
    stub_broker.join(work.queue_name)
    stub_worker.join()

    assert ("declare", "work") in events
    assert ("before", "work") in events
    assert ("after", "done", True) in events


@pytest.mark.depends_on('test_broker_add_middleware_exposes_actor_options')
@pytest.mark.suppress_logs("dramatiq.worker.WorkerThread")
def test_skip_message_hook_acknowledges_without_running_actor(stub_broker, stub_worker):
    events = []

    class Skipper(Middleware):
        def before_process_message(self, broker, message):
            raise SkipMessage()

        def after_skip_message(self, broker, message):
            events.append(message.actor_name)

    stub_broker.add_middleware(Skipper())

    @dramatiq.actor
    def work():
        events.append("ran")

    work.send()
    stub_broker.join(work.queue_name)
    stub_worker.join()

    assert events == ["work"]


@pytest.mark.depends_on("test_retry_exposes_requested_delay")
def test_retry_middleware_requeues_retry_exception_until_success(stub_broker, stub_worker):
    attempts = []

    @dramatiq.actor(max_retries=2)
    def work():
        attempts.append(len(attempts) + 1)
        if len(attempts) == 1:
            raise Retry(delay=0)

    work.send()
    stub_broker.join(work.queue_name)
    stub_worker.join()

    assert attempts == [1, 2]
    assert stub_broker.dead_letters == []


@pytest.mark.depends_on('test_retry_exposes_requested_delay')
@pytest.mark.suppress_logs("dramatiq.worker.WorkerThread", "dramatiq.middleware.retries.Retries")
def test_max_retries_zero_moves_failed_actor_to_dead_letters(stub_broker, stub_worker):
    @dramatiq.actor(max_retries=0)
    def work():
        raise ValueError("permanent")

    work.send()
    stub_broker.join(work.queue_name, fail_fast=False)
    stub_worker.join()

    assert len(stub_broker.dead_letters) == 1
    assert stub_broker.dead_letters[0].actor_name == "work"


@pytest.mark.depends_on("test_pickle_encoder_roundtrips_non_json_value")
def test_pickle_encoder_integrates_with_broker_message_processing(stub_broker, stub_worker):
    previous = dramatiq.get_encoder()
    seen = []
    try:
        dramatiq.set_encoder(PickleEncoder())

        @dramatiq.actor
        def work(value):
            seen.append(value)

        work.send({"values": {3, 5}})
        stub_broker.join(work.queue_name)
        stub_worker.join()
    finally:
        dramatiq.set_encoder(previous)

    assert seen == [{"values": {3, 5}}]


@pytest.mark.depends_on("test_result_backend_stores_and_retrieves_result")
def test_result_backend_uses_message_identity_across_store_and_get():
    backend = ResultStubBackend(namespace="identity")
    first = Message("jobs", "work", (), {}, {}, message_id="same")
    second = Message("jobs", "work", (), {}, {}, message_id="same")

    backend.store_result(first, "value", 5000)

    assert backend.get_result(second) == "value"


@pytest.mark.depends_on("test_barrier_requires_positive_party_count")
def test_barrier_completes_after_all_parties_signal(rate_limiter_backend):
    barrier = Barrier(rate_limiter_backend, "three-party", ttl=5000)
    assert barrier.create(3) is True

    assert barrier.wait(block=False) is False
    assert barrier.wait(block=False) is False
    assert barrier.wait(block=False) is True


@pytest.mark.depends_on('test_barrier_requires_positive_party_count')
def test_concurrent_rate_limiter_releases_slot_after_context():
    limiter_backend = RateLimitStubBackend()
    limiter = ConcurrentRateLimiter(limiter_backend, "mutex", limit=1, ttl=5000)

    with limiter.acquire() as acquired:
        assert acquired is True
        with limiter.acquire(raise_on_failure=False) as nested:
            assert nested is False

    with limiter.acquire(raise_on_failure=False) as reacquired:
        assert reacquired is True


@pytest.mark.depends_on("test_actor_decorator_returns_actor_and_registers_name")
def test_global_broker_setter_connects_actor_and_composition(stub_broker):
    dramatiq.set_broker(stub_broker)

    @dramatiq.actor
    def work():
        return "ok"

    message = work.message()
    pipe = message | message

    assert pipe.broker is stub_broker
    assert pipe.messages[0].actor_name == "work"


@pytest.mark.depends_on("test_stub_broker_declares_normal_and_delay_queues")
def test_stub_broker_consumer_rejects_missing_message_queue_consistently(stub_broker):
    @dramatiq.actor(queue_name="known")
    def work():
        return None

    with pytest.raises(QueueNotFound):
        stub_broker.consume("unknown")

    assert "known" in stub_broker.get_declared_queues()


@pytest.mark.depends_on("test_actor_direct_call_returns_underlying_result")
def test_actor_send_with_timedelta_delay_encodes_delay_metadata(stub_broker):
    @dramatiq.actor
    def work():
        return None

    message = work.send_with_options(delay=timedelta(milliseconds=7))

    assert message.queue_name == "default.DQ"
    assert isinstance(message.options["eta"], int)
    assert message.options["eta"] >= message.message_timestamp
