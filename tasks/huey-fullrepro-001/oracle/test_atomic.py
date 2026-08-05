from __future__ import annotations

import datetime

import pytest

from huey import CancelExecution, Error, MemoryHuey, RetryTask, crontab
from huey.exceptions import (
    RateLimitExceeded,
    TaskLockedException,
    TaskException,
)
from huey.serializer import Serializer, SignedSerializer, constant_time_compare
from huey.storage import MemoryStorage

from conftest import FIXED_ETA


def test_immediate_memory_huey_uses_memory_storage(immediate_huey):
    assert isinstance(immediate_huey.storage, MemoryStorage)
    assert immediate_huey.immediate is True
    assert immediate_huey.name


def test_huey_immediate_property_can_toggle_execution_mode(huey):
    assert huey.immediate is False
    huey.immediate = True
    assert huey.immediate is True
    huey.immediate = False
    assert huey.immediate is False


def test_empty_huey_exposes_zero_queue_schedule_and_result_counts(huey):
    assert len(huey) == 0
    assert huey.pending_count() == 0
    assert huey.scheduled_count() == 0
    assert huey.result_count() == 0


def test_task_wrapper_call_local_returns_function_value(immediate_huey):
    @immediate_huey.task()
    def add(left, right):
        return left + right

    assert add.call_local(4, 9) == 13


def test_task_wrapper_s_exposes_task_arguments_and_keywords(immediate_huey):
    @immediate_huey.task(name="named-add")
    def add(left, right=0):
        return left + right

    task = add.s(6, right=8)
    assert task.args == (6,)
    assert task.kwargs == {"right": 8}
    assert task.data == ((6,), {"right": 8})
    assert task.name == "named-add"


def test_task_wrapper_schedule_requires_eta_or_delay(immediate_huey):
    @immediate_huey.task()
    def identity(value):
        return value

    with pytest.raises(ValueError):
        identity.schedule((3,))


def test_immediate_task_call_returns_ready_result(immediate_huey):
    @immediate_huey.task()
    def multiply(left, right):
        return left * right

    result = multiply(7, 6)
    assert result.id
    assert result.is_ready() is True
    assert result.get() == 42


def test_result_preserve_and_reset_control_result_consumption(huey):
    @huey.task()
    def identity(value):
        return value

    result = identity("kept")
    huey.execute(huey.dequeue())
    assert result.get(preserve=True) == "kept"
    result.reset()
    assert result.get() == "kept"
    assert huey.result_count() == 0


def test_task_then_returns_original_task_and_adds_completion(immediate_huey):
    @immediate_huey.task()
    def add(left, right):
        return left + right

    task = add.s(1, 2)
    chained = task.then(add, 5)
    assert chained is task
    assert task.on_complete is not None


def test_task_error_returns_original_task_and_adds_error_handler(immediate_huey):
    @immediate_huey.task()
    def primary():
        return 1

    @immediate_huey.task()
    def handle_error(error):
        return error

    task = primary.s()
    assert task.error(handle_error) is task
    assert task.on_error is not None


def test_crontab_wildcard_matches_fixed_timestamp():
    matcher = crontab()
    assert matcher(datetime.datetime(2030, 1, 2, 12, 0)) is True


def test_crontab_interval_matches_only_selected_minutes():
    matcher = crontab(minute="*/15")
    assert matcher(datetime.datetime(2030, 1, 2, 12, 30)) is True
    assert matcher(datetime.datetime(2030, 1, 2, 12, 31)) is False


def test_crontab_range_and_list_match_selected_hours():
    matcher = crontab(hour="9-11,16-18")
    assert matcher(datetime.datetime(2030, 1, 2, 10, 0)) is True
    assert matcher(datetime.datetime(2030, 1, 2, 14, 0)) is False


def test_crontab_strict_rejects_unsupported_input():
    with pytest.raises(ValueError):
        crontab(minute="invalid", strict=True)


def test_crontab_daily_and_hourly_shortcuts_match_expected_times():
    daily = crontab.daily()
    hourly = crontab.hourly()
    assert daily(datetime.datetime(2030, 1, 2, 0, 0)) is True
    assert daily(datetime.datetime(2030, 1, 2, 0, 1)) is False
    assert hourly(datetime.datetime(2030, 1, 2, 12, 0)) is True
    assert hourly(datetime.datetime(2030, 1, 2, 12, 1)) is False


def test_serializer_round_trips_nested_python_values():
    serializer = Serializer()
    value = {"items": [1, 2, {"ok": True}], "empty": None}
    assert serializer.deserialize(serializer.serialize(value)) == value


def test_serializer_gzip_round_trip_preserves_bytes():
    serializer = Serializer(compression=True)
    value = b"payload-" * 20
    assert serializer.deserialize(serializer.serialize(value)) == value


def test_serializer_zlib_round_trip_preserves_mapping():
    serializer = Serializer(compression=True, use_zlib=True)
    value = {"compression": "zlib", "count": 4}
    assert serializer.deserialize(serializer.serialize(value)) == value


def test_signed_serializer_round_trips_payload():
    serializer = SignedSerializer(secret="s2r-secret", salt="s2r-salt")
    value = {"signed": True, "number": 17}
    assert serializer.deserialize(serializer.serialize(value)) == value


def test_signed_serializer_rejects_tampered_payload():
    serializer = SignedSerializer(secret="s2r-secret", salt="s2r-salt")
    encoded = serializer.serialize({"signed": True})
    tampered = encoded[:-1] + bytes([encoded[-1] ^ 1])
    with pytest.raises(ValueError):
        serializer.deserialize(tampered)


def test_constant_time_compare_reports_equal_and_unequal_bytes():
    assert constant_time_compare(b"alpha", b"alpha") is True
    assert constant_time_compare(b"alpha", b"omega") is False


def test_memory_storage_empty_dequeue_returns_none():
    storage = MemoryStorage("atomic-empty")
    assert storage.dequeue() is None
    assert storage.queue_size() == 0


def test_memory_storage_enqueued_items_preserve_fifo_order():
    storage = MemoryStorage("atomic-fifo")
    storage.enqueue(b"first")
    storage.enqueue(b"second")
    assert storage.enqueued_items() == [b"first", b"second"]
    assert storage.dequeue() == b"first"
    assert storage.dequeue() == b"second"


def test_memory_storage_prioritizes_higher_priority_items():
    storage = MemoryStorage("atomic-priority")
    storage.enqueue(b"low", priority=1)
    storage.enqueue(b"high", priority=8)
    assert storage.dequeue() == b"high"
    assert storage.dequeue() == b"low"


def test_memory_storage_reads_only_schedule_items_due_by_timestamp():
    storage = MemoryStorage("atomic-schedule")
    storage.add_to_schedule(b"early", FIXED_ETA - datetime.timedelta(minutes=1))
    storage.add_to_schedule(b"late", FIXED_ETA + datetime.timedelta(minutes=1))
    assert storage.read_schedule(FIXED_ETA) == [b"early"]
    assert storage.schedule_size() == 1
    assert storage.scheduled_items() == [b"late"]


def test_memory_storage_peek_and_pop_data_have_distinct_lifecycles():
    storage = MemoryStorage("atomic-data")
    storage.put_data("key", b"value")
    assert storage.peek_data("key") == b"value"
    assert storage.has_data_for_key("key") is True
    assert storage.pop_data("key") == b"value"
    assert storage.has_data_for_key("key") is False


def test_memory_storage_put_if_empty_is_idempotent():
    storage = MemoryStorage("atomic-if-empty")
    assert storage.put_if_empty("key", "first") is True
    assert storage.put_if_empty("key", "second") is False
    assert storage.peek_data("key") == "first"


def test_memory_storage_counter_increment_and_delete_are_publicly_observable():
    storage = MemoryStorage("atomic-counter")
    assert storage.incr("counter") == 1
    assert storage.incr("counter", 3) == 4
    storage.delete_counter("counter")
    assert storage.incr("counter", 0) == 0


def test_memory_storage_result_items_and_flush_results():
    storage = MemoryStorage("atomic-results")
    storage.put_data("one", 1, is_result=True)
    storage.put_data("two", 2, is_result=True)
    assert storage.result_items() == {"one": 1, "two": 2}
    assert storage.result_store_size() == 2
    storage.flush_results()
    assert storage.result_items() == {}
    assert storage.result_store_size() == 0


def test_memory_storage_flush_queue_and_schedule_clear_both_views():
    storage = MemoryStorage("atomic-flush")
    storage.enqueue(b"queued")
    storage.add_to_schedule(b"scheduled", FIXED_ETA)
    storage.flush_queue()
    storage.flush_schedule()
    assert storage.queue_size() == 0
    assert storage.schedule_size() == 0


def test_error_named_tuple_exposes_metadata():
    error = Error({"kind": "failure"})
    assert error.metadata == {"kind": "failure"}


def test_cancel_execution_preserves_retry_option():
    exception = CancelExecution(retry=True)
    assert exception.retry is True


def test_retry_task_preserves_eta_and_delay_options():
    exception = RetryTask(eta=FIXED_ETA, delay=4)
    assert exception.eta == FIXED_ETA
    assert exception.delay == 4


def test_rate_limit_usage_can_be_read_and_reset(huey):
    rate_limit = huey.rate_limit("atomic-rate", limit=3, per=100000, retry=False)
    assert rate_limit.current_usage() == 0
    rate_limit.acquire()
    assert rate_limit.current_usage() == 1
    rate_limit.reset()
    assert rate_limit.current_usage() == 0


def test_task_lock_acquire_reports_state_and_release_clears_it(huey):
    lock = huey.lock_task("atomic-lock")
    assert lock.is_locked() is False
    assert lock.acquire() is True
    assert lock.is_locked() is True
    assert lock.release() is True
    assert lock.is_locked() is False


def test_huey_put_get_and_delete_expose_serialized_data(huey):
    huey.put("atomic-key", {"value": 12})
    assert huey.get("atomic-key", peek=True) == {"value": 12}
    assert huey.delete("atomic-key") is True
    assert huey.get("atomic-key") is None


def test_memory_huey_results_false_omits_result_handle():
    huey = MemoryHuey("atomic-no-results", results=False, immediate=True, utc=False)

    @huey.task()
    def identity(value):
        return value

    assert identity("value") is None
    assert huey.result_count() == 0


def test_memory_huey_store_none_preserves_none_result():
    huey = MemoryHuey("atomic-store-none", store_none=True, immediate=True, utc=False)

    @huey.task()
    def returns_none():
        return None

    result = returns_none()
    assert result.is_ready() is True
    assert result.get() is None
