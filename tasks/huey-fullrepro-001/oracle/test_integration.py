from __future__ import annotations

import contextlib
import datetime

import pytest

from huey import MemoryHuey, chord, crontab, group
from huey.exceptions import RateLimitExceeded, TaskException
from huey.serializer import Serializer
from huey.signals import (
    SIGNAL_COMPLETE,
    SIGNAL_ENQUEUED,
    SIGNAL_ERROR,
    SIGNAL_EXECUTING,
    SIGNAL_EXPIRED,
    SIGNAL_LOCKED,
    SIGNAL_REVOKED,
)

from conftest import FIXED_ETA


@pytest.mark.depends_on("test_immediate_task_call_returns_ready_result")
def test_enqueue_dequeue_execute_and_result_get_share_task_state(huey):
    @huey.task()
    def add(left, right):
        return left + right

    result = add(8, 9)
    assert result.is_ready() is False
    assert huey.pending_count() == 1
    task = huey.dequeue()
    assert task.id == result.id
    assert huey.execute(task) == 17
    assert result.get() == 17
    assert huey.pending_count() == 0


@pytest.mark.depends_on("test_task_wrapper_s_exposes_task_arguments_and_keywords")
def test_serialized_task_round_trip_preserves_public_task_data(huey):
    @huey.task(name="round-trip")
    def add(left, right=0):
        return left + right

    original = add.s(5, right=7)
    restored = huey.deserialize_task(huey.serialize_task(original))
    assert restored.id == original.id
    assert restored.name == original.name
    assert restored.args == original.args
    assert restored.kwargs == original.kwargs


@pytest.mark.depends_on('test_immediate_task_call_returns_ready_result')
def test_pending_returns_deserialized_tasks_and_honors_limit(huey):
    @huey.task()
    def identity(value):
        return value

    first = identity("first")
    second = identity("second")
    pending = huey.pending(limit=1)
    assert len(pending) == 1
    assert pending[0].id == first.id
    assert huey.pending()[1].id == second.id


@pytest.mark.depends_on("test_task_then_returns_original_task_and_adds_completion")
def test_tuple_pipeline_passes_returned_tuple_as_next_arguments(immediate_huey):
    @immediate_huey.task()
    def split(value):
        return value, value + 1

    @immediate_huey.task()
    def add(left, right):
        return left + right

    results = immediate_huey.enqueue(split.s(4).then(add))
    assert results.get() == [((4, 5)), 9]


@pytest.mark.depends_on("test_task_then_returns_original_task_and_adds_completion")
def test_dict_pipeline_passes_returned_mapping_as_next_keywords(immediate_huey):
    @immediate_huey.task()
    def make_values():
        return {"left": 6, "right": 7}

    @immediate_huey.task()
    def add(left, right):
        return left + right

    results = immediate_huey.enqueue(make_values.s().then(add))
    assert results.get() == [{"left": 6, "right": 7}, 13]


@pytest.mark.depends_on("test_immediate_task_call_returns_ready_result")
def test_task_map_returns_result_group_in_input_order(immediate_huey):
    @immediate_huey.task()
    def square(value):
        return value * value

    results = square.map([2, 3, 5])
    assert len(results) == 3
    assert results.get() == [4, 9, 25]


@pytest.mark.depends_on("test_memory_storage_enqueued_items_preserve_fifo_order")
def test_group_enqueues_distinct_tasks_and_collects_results(immediate_huey):
    @immediate_huey.task()
    def identity(value):
        return value

    results = immediate_huey.enqueue(group([identity.s("a"), identity.s("b")]))
    assert results.get() == ["a", "b"]
    assert len(results) == 2


@pytest.mark.depends_on('test_memory_storage_enqueued_items_preserve_fifo_order')
def test_chord_collects_member_results_before_callback(immediate_huey):
    @immediate_huey.task()
    def multiply(value):
        return value * 2

    @immediate_huey.task()
    def total(values):
        return sum(values)

    result = immediate_huey.enqueue(
        chord([multiply.s(2), multiply.s(4), multiply.s(5)], total)
    )
    assert result.get() == 22
    assert result.results.get() == [4, 8, 10]
    assert result.callback.get() == 22


@pytest.mark.depends_on('test_memory_storage_enqueued_items_preserve_fifo_order')
def test_chord_pipeline_exposes_callback_pipeline_results(immediate_huey):
    @immediate_huey.task()
    def identity(value):
        return value

    @immediate_huey.task()
    def collect(values):
        return values

    result = immediate_huey.enqueue(
        chord([identity.s("x"), identity.s("y")], collect)
        .then(identity)
        .then(identity)
    )
    assert result.get() == ["x", "y"]
    assert result.pipeline_results.get() == [["x", "y"], ["x", "y"], ["x", "y"]]


@pytest.mark.depends_on('test_immediate_task_call_returns_ready_result')
@pytest.mark.suppress_logs("huey")
def test_failed_task_surfaces_public_task_exception(huey):
    @huey.task()
    def fail():
        raise ValueError("failure")

    result = fail()
    huey.execute(huey.dequeue())
    with pytest.raises(TaskException) as caught:
        result.get()
    assert isinstance(caught.value.metadata, dict)
    assert "task_id" in caught.value.metadata


@pytest.mark.depends_on('test_immediate_task_call_returns_ready_result')
@pytest.mark.suppress_logs("huey")
def test_retrying_task_requeues_then_stores_success(huey):
    attempts = []

    @huey.task(retries=1)
    def flaky():
        attempts.append(len(attempts))
        if len(attempts) == 1:
            raise ValueError("retry")
        return "ok"

    result = flaky()
    assert huey.execute(huey.dequeue()) is None
    assert huey.pending_count() == 1
    result.reset()
    assert huey.execute(huey.dequeue()) == "ok"
    assert result.get() == "ok"
    assert attempts == [0, 1]


@pytest.mark.depends_on('test_immediate_task_call_returns_ready_result')
def test_pre_and_post_execute_hooks_observe_task_lifecycle(huey):
    events = []

    @huey.pre_execute()
    def before(task):
        events.append(("before", task.name))

    @huey.post_execute()
    def after(task, value, exception):
        events.append(("after", value, exception is None))

    @huey.task()
    def identity(value):
        return value

    result = identity(23)
    huey.execute(huey.dequeue())
    assert result.get() == 23
    assert events == [("before", "identity"), ("after", 23, True)]


@pytest.mark.depends_on('test_immediate_task_call_returns_ready_result')
def test_signal_handler_receives_enqueue_execute_and_complete(huey):
    events = []

    @huey.signal()
    def receiver(signal, task, *args):
        events.append(signal)

    @huey.task()
    def identity(value):
        return value

    result = identity(31)
    huey.execute(huey.dequeue())
    assert result.get() == 31
    assert events == [SIGNAL_ENQUEUED, SIGNAL_EXECUTING, SIGNAL_COMPLETE]


@pytest.mark.depends_on('test_immediate_task_call_returns_ready_result')
def test_disconnect_signal_stops_selected_signal_delivery(huey):
    events = []

    @huey.signal(SIGNAL_EXECUTING, SIGNAL_COMPLETE)
    def receiver(signal, task):
        events.append(signal)

    @huey.task()
    def identity(value):
        return value

    first = identity(1)
    huey.execute(huey.dequeue())
    assert first.get() == 1
    huey.disconnect_signal(receiver, SIGNAL_COMPLETE)
    second = identity(2)
    huey.execute(huey.dequeue())
    assert second.get() == 2
    assert events == [
        SIGNAL_EXECUTING,
        SIGNAL_COMPLETE,
        SIGNAL_EXECUTING,
    ]


@pytest.mark.depends_on('test_immediate_task_call_returns_ready_result')
@pytest.mark.suppress_logs("huey")
def test_task_class_revoke_and_restore_control_execution(huey):
    @huey.task()
    def identity(value):
        return value

    identity.revoke()
    blocked = identity(7)
    assert huey.execute(huey.dequeue()) is None
    assert blocked.get() is None
    assert identity.is_revoked() is True
    assert identity.restore() is True
    allowed = identity(8)
    assert huey.execute(huey.dequeue()) == 8
    assert allowed.get() == 8


@pytest.mark.depends_on('test_immediate_task_call_returns_ready_result')
@pytest.mark.suppress_logs("huey")
def test_revoke_once_blocks_one_task_instance_then_restores(huey):
    @huey.task()
    def identity(value):
        return value

    identity.revoke(revoke_once=True)
    first = identity(1)
    second = identity(2)
    assert huey.execute(huey.dequeue()) is None
    assert first.get() is None
    assert huey.execute(huey.dequeue()) == 2
    assert second.get() == 2


@pytest.mark.depends_on('test_immediate_task_call_returns_ready_result')
def test_result_revoke_restore_can_restore_queued_task(huey):
    @huey.task()
    def identity(value):
        return value

    result = identity(11)
    result.revoke()
    assert result.is_revoked() is True
    assert result.restore() is True
    assert huey.execute(huey.dequeue()) == 11
    assert result.get() == 11


@pytest.mark.depends_on("test_memory_storage_reads_only_schedule_items_due_by_timestamp")
def test_scheduled_task_moves_from_schedule_to_execution(huey, fixed_eta):
    @huey.task()
    def add(left, right):
        return left + right

    result = add.schedule((3, 4), eta=fixed_eta)
    assert huey.pending_count() == 1
    assert huey.execute(huey.dequeue(), timestamp=datetime.datetime(2029, 1, 1)) is None
    assert huey.scheduled_count() == 1
    assert result.get() is None
    due = huey.read_schedule(fixed_eta)
    assert [task.id for task in due] == [result.id]
    assert huey.execute(due[0], timestamp=fixed_eta) == 7
    assert result.get() == 7


@pytest.mark.depends_on('test_memory_storage_reads_only_schedule_items_due_by_timestamp')
def test_scheduled_items_and_flush_remove_scheduled_tasks(huey, fixed_eta):
    @huey.task()
    def identity(value):
        return value

    identity.schedule((1,), eta=fixed_eta)
    identity.schedule((2,), eta=fixed_eta + datetime.timedelta(minutes=1))
    assert huey.pending_count() == 2
    assert huey.execute(huey.dequeue(), timestamp=datetime.datetime(2029, 1, 1)) is None
    assert huey.execute(huey.dequeue(), timestamp=datetime.datetime(2029, 1, 1)) is None
    assert len(huey.scheduled()) == 2
    huey.flush()
    assert huey.scheduled_count() == 0
    assert huey.pending_count() == 0


@pytest.mark.depends_on('test_immediate_task_call_returns_ready_result')
def test_expired_task_emits_no_result_and_public_expired_signal(huey):
    events = []

    @huey.signal(SIGNAL_EXPIRED)
    def receiver(signal, task):
        events.append((signal, task.name))

    @huey.task(expires=FIXED_ETA)
    def identity(value):
        return value

    result = identity(99)
    assert huey.execute(
        huey.dequeue(), timestamp=FIXED_ETA + datetime.timedelta(minutes=1)
    ) is None
    assert result.get() is None
    assert events == [(SIGNAL_EXPIRED, "identity")]


@pytest.mark.depends_on("test_memory_storage_prioritizes_higher_priority_items")
def test_task_priorities_control_dequeue_execution_order(huey):
    seen = []

    @huey.task(priority=1)
    def low():
        seen.append("low")
        return "low"

    @huey.task(priority=5)
    def high():
        seen.append("high")
        return "high"

    low_result = low()
    high_result = high()
    assert huey.execute(huey.dequeue()) == "high"
    assert huey.execute(huey.dequeue()) == "low"
    assert high_result.get() == "high"
    assert low_result.get() == "low"
    assert seen == ["high", "low"]


@pytest.mark.depends_on("test_huey_immediate_property_can_toggle_execution_mode")
def test_switching_immediate_mode_changes_enqueue_execution(huey):
    @huey.task()
    def identity(value):
        return value

    queued = identity(1)
    assert huey.pending_count() == 1
    huey.flush()
    huey.immediate = True
    immediate = identity(2)
    assert immediate.get() == 2
    assert huey.pending_count() == 0
    huey.immediate = False
    assert queued.get() is None


@pytest.mark.depends_on("test_task_lock_acquire_reports_state_and_release_clears_it")
@pytest.mark.suppress_logs("huey")
def test_lock_decorator_and_lock_signal_integrate_with_task_execution(huey):
    events = []

    @huey.signal(SIGNAL_LOCKED)
    def receiver(signal, task):
        events.append((signal, task.name))

    @huey.task()
    @huey.lock_task("integration-lock")
    def identity(value):
        return value

    lock = huey.lock_task("integration-lock")
    with lock:
        result = identity(4)
        assert huey.execute(huey.dequeue()) is None
    with pytest.raises(TaskException):
        result.get()
    assert events == [(SIGNAL_LOCKED, "identity")]
    success = identity(5)
    assert huey.execute(huey.dequeue()) == 5
    assert success.get() == 5


@pytest.mark.depends_on("test_rate_limit_usage_can_be_read_and_reset")
def test_rate_limit_decorator_emits_rate_limit_error_without_retry(huey):
    @huey.task()
    @huey.rate_limit("integration-rate", limit=1, per=100000, retry=False)
    def identity():
        return "ok"

    first = identity()
    second = identity()
    assert huey.execute(huey.dequeue()) == "ok"
    assert first.get() == "ok"
    assert huey.execute(huey.dequeue()) is None
    with pytest.raises(TaskException) as caught:
        second.get()
    assert "error" in caught.value.metadata


@pytest.mark.depends_on("test_task_wrapper_s_exposes_task_arguments_and_keywords")
def test_context_task_receives_public_task_object(huey):
    seen = []

    @huey.task(context=True)
    def capture(task=None):
        seen.append((task.id, task.name))
        return task.id

    result = capture()
    task = huey.dequeue()
    task_id = task.id
    assert huey.execute(task) == task_id
    assert result.get() == task_id
    assert seen == [(task_id, "capture")]


@pytest.mark.depends_on("test_crontab_interval_matches_only_selected_minutes")
def test_periodic_task_registration_and_execution_use_crontab(huey):
    seen = []

    @huey.periodic_task(crontab(minute="*/15"), name="periodic-report")
    def report():
        seen.append("ran")
        return 42

    periodic = huey.read_periodic(datetime.datetime(2030, 1, 2, 12, 30))
    assert [task.name for task in periodic] == ["periodic-report"]
    huey.enqueue(periodic[0])
    assert huey.execute(huey.dequeue()) == 42
    assert seen == ["ran"]


@pytest.mark.depends_on("test_serializer_zlib_round_trip_preserves_mapping")
def test_compressed_huey_serializer_preserves_task_result(huey):
    compressed = MemoryHuey(
        "compressed-integration",
        immediate=False,
        utc=False,
        serializer=Serializer(compression=True),
    )

    @compressed.task()
    def identity(value):
        return value

    result = identity({"compressed": True, "count": 3})
    assert compressed.execute(compressed.dequeue()) == {
        "compressed": True,
        "count": 3,
    }
    assert result.get() == {"compressed": True, "count": 3}


@pytest.mark.depends_on('test_immediate_task_call_returns_ready_result')
def test_huey_result_lookup_reads_result_by_task_id(huey):
    @huey.task()
    def identity(value):
        return value

    result = identity("lookup")
    huey.execute(huey.dequeue())
    assert huey.result(result.id) == "lookup"


@pytest.mark.depends_on('test_immediate_task_call_returns_ready_result')
def test_all_results_exposes_completed_task_ids_before_consumption(huey):
    @huey.task()
    def identity(value):
        return value

    first = identity("first")
    second = identity("second")
    huey.execute(huey.dequeue())
    huey.execute(huey.dequeue())
    assert set(huey.all_results()) == {first.id, second.id}


@pytest.mark.depends_on("test_huey_put_get_and_delete_expose_serialized_data")
def test_huey_flush_clears_queue_schedule_results_and_locks(huey, fixed_eta):
    @huey.task()
    def identity(value):
        return value

    result = identity("queued")
    identity.schedule((2,), eta=fixed_eta)
    lock = huey.lock_task("flush-lock")
    lock.acquire()
    assert huey.pending_count() == 2
    assert huey.scheduled_count() == 0
    huey.execute(huey.dequeue())
    assert result.is_ready() is True
    huey.flush()
    assert huey.pending_count() == 0
    assert huey.scheduled_count() == 0
    assert huey.result_count() == 0
    assert lock.is_locked() is False
    assert lock.acquire() is True
    assert huey.flush_locks("flush-lock") == {"flush-lock"}
    assert lock.is_locked() is False


@pytest.mark.depends_on("test_result_preserve_and_reset_control_result_consumption")
def test_result_group_iteration_and_indexing_resolve_member_results(immediate_huey):
    @immediate_huey.task()
    def identity(value):
        return value

    group_result = immediate_huey.enqueue(
        group([identity.s("left"), identity.s("right")])
    )
    assert [result.get() for result in group_result] == ["left", "right"]
    assert group_result[0] == "left"
    assert group_result[1] == "right"


@pytest.mark.depends_on('test_memory_storage_reads_only_schedule_items_due_by_timestamp')
def test_result_reschedule_revokes_original_and_creates_new_task(huey, fixed_eta):
    @huey.task()
    def identity(value):
        return value

    original = identity.schedule((10,), eta=fixed_eta)
    replacement = original.reschedule(eta=fixed_eta)
    assert replacement.id != original.id
    assert original.is_revoked() is True
    assert huey.pending_count() == 2
    assert huey.scheduled_count() == 0


@pytest.mark.depends_on('test_immediate_task_call_returns_ready_result')
@pytest.mark.suppress_logs("huey")
def test_error_signal_and_error_result_are_consistent(huey):
    events = []

    @huey.signal(SIGNAL_ERROR)
    def receiver(signal, task, exception):
        events.append((signal, type(exception)))

    @huey.task()
    def fail():
        raise RuntimeError("broken")

    result = fail()
    huey.execute(huey.dequeue())
    with pytest.raises(TaskException):
        result.get()
    assert events == [(SIGNAL_ERROR, RuntimeError)]


@pytest.mark.depends_on('test_immediate_task_call_returns_ready_result')
@pytest.mark.suppress_logs("huey")
def test_revoked_task_emits_public_revoked_signal(huey):
    events = []

    @huey.signal(SIGNAL_REVOKED)
    def receiver(signal, task):
        events.append(task.name)

    @huey.task()
    def identity(value):
        return value

    identity.revoke()
    result = identity(3)
    huey.execute(huey.dequeue())
    assert result.get() is None
    assert events == ["identity"]


@pytest.mark.depends_on("test_task_wrapper_call_local_returns_function_value")
def test_call_local_and_queued_execution_produce_same_value(huey):
    @huey.task()
    def add(left, right):
        return left + right

    assert add.call_local(12, 4) == 16
    result = add(12, 4)
    huey.execute(huey.dequeue())
    assert result.get() == 16
