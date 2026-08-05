from __future__ import annotations

from datetime import datetime, timezone

import pytest

import dramatiq
from dramatiq import Message, Middleware
from dramatiq.brokers.stub import StubBroker
from dramatiq.encoder import JSONEncoder, PickleEncoder
from dramatiq.errors import ActorNotFound, DecodeError, QueueNotFound, Retry
from dramatiq.middleware import SkipMessage
from dramatiq.rate_limits import Barrier
from dramatiq.rate_limits.backends import StubBackend as RateLimitStubBackend
from dramatiq.results import Missing, ResultFailure, ResultMissing
from dramatiq.results.backends import StubBackend as ResultStubBackend


def test_actor_decorator_returns_actor_and_registers_name(stub_broker):
    @dramatiq.actor
    def add(left, right):
        return left + right

    assert isinstance(add, dramatiq.Actor)
    assert add.actor_name == "add"
    assert add.actor_name in stub_broker.get_declared_actors()


def test_actor_direct_call_returns_underlying_result(stub_broker):
    @dramatiq.actor
    def multiply(left, right):
        return left * right

    assert multiply(6, 7) == 42


def test_actor_metadata_options_are_public(stub_broker):
    @dramatiq.actor(actor_name="named", queue_name="jobs", priority=4, max_retries=3)
    def work():
        return None

    assert work.actor_name == "named"
    assert work.queue_name == "jobs"
    assert work.priority == 4
    assert work.options["max_retries"] == 3
    assert work.broker is stub_broker


def test_actor_custom_actor_class_is_used(stub_broker):
    class ChildActor(dramatiq.Actor):
        pass

    @dramatiq.actor(actor_class=ChildActor)
    def work():
        return "done"

    assert isinstance(work, ChildActor)


def test_invalid_queue_name_raises_value_error(stub_broker):
    with pytest.raises(ValueError):

        @dramatiq.actor(queue_name="bad queue")
        def work():
            return None


def test_unsupported_actor_option_raises_value_error(stub_broker):
    with pytest.raises(ValueError):

        @dramatiq.actor(unsupported_option=True)
        def work():
            return None


def test_actor_message_contains_positional_and_keyword_arguments(stub_broker):
    @dramatiq.actor
    def work(left, right):
        return left + right

    message = work.message(2, right=5)

    assert message.actor_name == "work"
    assert message.queue_name == "default"
    assert message.args == (2,)
    assert message.kwargs == {"right": 5}
    assert message.options == {}


def test_message_with_options_converts_callback_actor_to_name(stub_broker):
    @dramatiq.actor
    def callback(message_data, result):
        return None

    @dramatiq.actor
    def work():
        return "done"

    message = work.message_with_options(on_success=callback, pipe_ignore=True)

    assert message.options["on_success"] == "callback"
    assert message.options["pipe_ignore"] is True


def test_message_with_options_rejects_non_actor_callback(stub_broker):
    @dramatiq.actor
    def work():
        return None

    with pytest.raises(TypeError):
        work.message_with_options(on_success=object())


def test_message_args_are_normalized_to_tuple():
    message = Message("jobs", "work", ["x", "y"], {}, {})

    assert message.args == ("x", "y")


def test_message_asdict_exposes_serializable_public_fields():
    message = Message("jobs", "work", ("x",), {"flag": True}, {"priority": 2}, message_id="m-1", message_timestamp=17)

    data = message.asdict()

    assert data["queue_name"] == "jobs"
    assert data["actor_name"] == "work"
    assert data["args"] == ("x",)
    assert data["kwargs"] == {"flag": True}
    assert data["options"] == {"priority": 2}
    assert data["message_id"] == "m-1"
    assert data["message_timestamp"] == 17


def test_message_copy_replaces_fields_and_merges_options():
    message = Message("jobs", "work", (), {}, {"first": 1})

    copied = message.copy(actor_name="other", options={"second": 2})

    assert copied.actor_name == "other"
    assert copied.options == {"first": 1, "second": 2}
    assert copied.message_id == message.message_id


def test_message_encode_decode_roundtrip():
    message = Message("jobs", "work", (1, "two"), {"enabled": True}, {"tag": "x"}, message_id="stable")

    decoded = Message.decode(message.encode())

    assert decoded == message
    assert decoded.args == (1, "two")


def test_invalid_message_bytes_raise_decode_error():
    with pytest.raises(DecodeError):
        Message.decode(b"not-json")


def test_message_datetime_uses_utc_and_millisecond_timestamp():
    message = Message("jobs", "work", (), {}, {}, message_timestamp=1_702_000_123_456)

    assert message.message_datetime.tzinfo is timezone.utc
    assert message.message_datetime == datetime.fromtimestamp(1_702_000_123.456, tz=timezone.utc)


def test_json_encoder_roundtrips_message_data():
    encoder = JSONEncoder()
    data = {"args": [1, "two"], "kwargs": {"ok": True}}

    assert encoder.decode(encoder.encode(data)) == data


def test_pickle_encoder_roundtrips_non_json_value():
    encoder = PickleEncoder()
    data = {"values": {1, 2, 3}}

    assert encoder.decode(encoder.encode(data)) == data


def test_global_encoder_can_be_replaced_and_restored():
    previous = dramatiq.get_encoder()
    replacement = PickleEncoder()
    try:
        dramatiq.set_encoder(replacement)
        assert dramatiq.get_encoder() is replacement
    finally:
        dramatiq.set_encoder(previous)


def test_stub_broker_declares_normal_and_delay_queues():
    broker = StubBroker(middleware=[])

    broker.declare_queue("jobs")

    assert "jobs" in broker.get_declared_queues()
    assert "jobs.DQ" in broker.get_declared_delay_queues()


def test_broker_declares_actor_and_can_lookup_it(stub_broker):
    @dramatiq.actor
    def work():
        return None

    assert stub_broker.get_actor("work") is work
    assert stub_broker.get_declared_actors() == {"work"}


def test_broker_unknown_actor_raises_actor_not_found(stub_broker):
    with pytest.raises(ActorNotFound):
        stub_broker.get_actor("missing")


def test_stub_broker_consume_unknown_queue_raises_queue_not_found():
    broker = StubBroker(middleware=[])

    with pytest.raises(QueueNotFound):
        broker.consume("missing")


def test_stub_broker_enqueue_unknown_queue_raises_queue_not_found():
    broker = StubBroker(middleware=[])
    message = Message("missing", "work", (), {}, {})

    with pytest.raises(QueueNotFound):
        broker.enqueue(message)


def test_stub_broker_join_unknown_queue_raises_queue_not_found():
    broker = StubBroker(middleware=[])

    with pytest.raises(QueueNotFound):
        broker.join("missing")


def test_message_proxy_forwards_fields_and_can_be_marked_failed():
    message = Message("jobs", "work", (), {}, {}, message_id="proxy-id")
    proxy = dramatiq.MessageProxy(message)

    proxy.fail()

    assert proxy.message_id == "proxy-id"
    assert proxy.actor_name == "work"
    assert proxy.failed is True


def test_message_proxy_exception_state_can_be_stuffed_and_cleared():
    message = Message("jobs", "work", (), {}, {})
    proxy = dramatiq.MessageProxy(message)
    error = RuntimeError("failure")

    proxy.stuff_exception(error)
    proxy.clear_exception()

    assert proxy.failed is False


def test_broker_add_middleware_exposes_actor_options(stub_broker):
    class ExtraMiddleware(Middleware):
        pass

    middleware = ExtraMiddleware()
    stub_broker.add_middleware(middleware)

    assert middleware in stub_broker.middleware
    assert isinstance(middleware.actor_options, set)


def test_broker_middleware_missing_anchor_raises_value_error(stub_broker):
    class ExtraMiddleware(Middleware):
        pass

    with pytest.raises(ValueError):
        stub_broker.add_middleware(
            ExtraMiddleware(), before=type("MissingMiddleware", (Middleware,), {})
        )


def test_base_middleware_has_empty_public_defaults():
    middleware = Middleware()

    assert middleware.actor_options == set()
    assert middleware.forks == []


def test_stub_result_backend_builds_readable_namespace_key():
    backend = ResultStubBackend(namespace="reports", use_namespace_prefix_keys=True)
    message = Message("jobs", "work", (), {}, {}, message_id="result-id")

    key = backend.build_message_key(message)

    assert key == "reports:jobs:work:result-id"


def test_stub_result_backend_builds_legacy_hash_key():
    backend = ResultStubBackend(namespace="reports")
    message = Message("jobs", "work", (), {}, {}, message_id="result-id")

    key = backend.build_message_key(message)

    assert len(key) == 32
    assert all(character in "0123456789abcdef" for character in key)


def test_missing_result_marker_is_distinct_from_none():
    assert Missing is not None
    assert Missing is not object()


def test_result_backend_missing_result_raises_result_missing():
    backend = ResultStubBackend()
    message = Message("jobs", "work", (), {}, {})

    with pytest.raises(ResultMissing):
        backend.get_result(message)


def test_result_backend_stores_and_retrieves_result():
    backend = ResultStubBackend()
    message = Message("jobs", "work", (), {}, {})

    backend.store_result(message, {"answer": 42}, 5000)

    assert backend.get_result(message) == {"answer": 42}


def test_result_backend_stored_exception_raises_result_failure():
    backend = ResultStubBackend()
    message = Message("jobs", "work", (), {}, {})

    backend.store_exception(message, ValueError("bad input"), 5000)

    with pytest.raises(ResultFailure) as error:
        backend.get_result(message)

    assert error.value.orig_exc_type == "ValueError"


def test_retry_exposes_requested_delay():
    error = Retry("retry later", delay=17)

    assert error.delay == 17
    assert isinstance(error, dramatiq.DramatiqError)


def test_barrier_requires_positive_party_count(rate_limiter_backend):
    barrier = Barrier(rate_limiter_backend, "single-barrier")

    with pytest.raises(AssertionError):
        barrier.create(0)


def test_generic_actor_subclass_is_callable(stub_broker):
    class Add(dramatiq.GenericActor):
        def perform(self, left, right):
            return left + right

    assert isinstance(Add.__actor__, dramatiq.Actor)
    assert Add(4, 5) == 9


def test_generic_actor_meta_options_are_forwarded(stub_broker):
    class Task(dramatiq.GenericActor):
        class Meta:
            queue_name = "tasks"
            max_retries = 2

        def perform(self):
            return "done"

    assert Task.queue_name == "tasks"
    assert Task.options["max_retries"] == 2


def test_generic_actor_abstract_base_is_not_registered_as_actor(stub_broker):
    class BaseTask(dramatiq.GenericActor):
        class Meta:
            abstract = True

        def perform(self):
            raise NotImplementedError

    assert not isinstance(BaseTask, dramatiq.Actor)


def test_generic_actor_missing_perform_raises_not_implemented(stub_broker):
    class EmptyTask(dramatiq.GenericActor):
        pass

    with pytest.raises(NotImplementedError):
        EmptyTask()


def test_skip_message_is_a_middleware_error():
    assert issubclass(SkipMessage, Exception)


def test_retry_default_delay_can_be_none():
    error = Retry()

    assert error.delay is None
