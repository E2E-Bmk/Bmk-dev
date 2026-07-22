"""Atomic public-API behavioral tests for anyio.

Each test exercises a single public API entry point and a single behavior.
"""
from __future__ import annotations

import math
import os
import subprocess
import sys
from contextvars import ContextVar

import pytest

import anyio
from anyio import (
    BrokenResourceError,
    BusyResourceError,
    CapacityLimiter,
    ClosedResourceError,
    Condition,
    EndOfStream,
    Event,
    IncompleteRead,
    Lock,
    NoEventLoopError,
    ResourceGuard,
    Semaphore,
    WouldBlock,
    create_memory_object_stream,
    create_task_group,
    current_effective_deadline,
    current_time,
    fail_after,
    move_on_after,
    open_file,
    run,
    sleep,
    sleep_until,
    to_thread,
    wait_all_tasks_blocked,
    wrap_file,
)
from anyio.abc import TaskStatus
from anyio.functools import cache, lru_cache, reduce
from anyio.lowlevel import RunVar, checkpoint, current_token
from anyio.streams.buffered import BufferedByteReceiveStream
from anyio.streams.text import TextReceiveStream, TextSendStream
from anyio import Path as AsyncPath

pytestmark = pytest.mark.anyio

# ── Event-loop entry ──────────────────────────────────────────────

def test_run_invokes_coroutine_and_returns_value():
    async def add(a: int, b: int) -> int:
        return a + b

    assert run(add, 2, 5, backend="asyncio") == 7


def test_run_rejects_unknown_backend():
    async def noop() -> None:
        return None

    with pytest.raises(LookupError):
        run(noop, backend="missing-backend")


def test_all_backends_public_tuple():
    assert anyio.get_all_backends() == ("asyncio", "trio")


def test_available_backend_projection_contains_asyncio():
    assert "asyncio" in anyio.get_available_backends()
    assert set(anyio.get_available_backends()).issubset(set(anyio.get_all_backends()))


# ── Timing and sleep ─────────────────────────────────────────────

async def test_current_time_available_inside_event_loop():
    now = current_time()
    assert isinstance(now, float)
    assert now >= 0
    assert now == now  # not NaN


async def test_current_time_advances_across_sleep():
    before = current_time()
    await sleep(0.01)
    assert current_time() > before


async def test_sleep_until_past_deadline_returns_promptly():
    before = current_time()
    await sleep_until(before - 1)
    assert current_time() >= before


async def test_sleep_forever_lasts_until_cancellation():
    with move_on_after(0.02) as scope:
        await anyio.sleep_forever()
    assert scope.cancelled_caught is True


def test_current_time_requires_event_loop():
    with pytest.raises(NoEventLoopError):
        current_time()


def test_cancelled_class_requires_event_loop():
    with pytest.raises(NoEventLoopError):
        anyio.get_cancelled_exc_class()


# ── Cancellation scopes ──────────────────────────────────────────

async def test_move_on_after_suppresses_own_timeout():
    with move_on_after(0.01) as scope:
        await sleep(1)
    assert scope.cancelled_caught is True


async def test_fail_after_raises_timeout_error():
    with pytest.raises(TimeoutError):
        with fail_after(0.01):
            await sleep(1)


async def test_current_effective_deadline_reports_inf_and_minus_inf():
    assert current_effective_deadline() == float("inf")
    with anyio.CancelScope() as scope:
        scope.cancel()
        assert current_effective_deadline() == float("-inf")


# ── Task groups and task handles ──────────────────────────────────

async def test_start_soon_handle_returns_result_after_completion():
    async def produce() -> int:
        return 5

    async with create_task_group() as tg:
        handle = tg.start_soon(produce)
        assert await handle == 5
        assert handle.return_value == 5
        assert handle.exception is None


# ── Memory object streams ────────────────────────────────────────

def test_memory_stream_invalid_float_buffer_raises():
    with pytest.raises(ValueError):
        create_memory_object_stream(1.0)


def test_memory_stream_negative_buffer_raises():
    with pytest.raises(ValueError):
        create_memory_object_stream(-1)


async def test_memory_stream_send_receive_one_item():
    send, receive = create_memory_object_stream[str](1)
    await send.send("payload")
    assert await receive.receive() == "payload"
    send.close()
    receive.close()


async def test_memory_stream_nowait_operations():
    send, receive = create_memory_object_stream[str](2)
    send.send_nowait("hello")
    send.send_nowait("anyio")
    assert receive.receive_nowait() == "hello"
    assert receive.receive_nowait() == "anyio"
    send.close()
    receive.close()


async def test_memory_stream_nowait_would_block_when_empty():
    send, receive = create_memory_object_stream[str](1)
    with pytest.raises(WouldBlock):
        receive.receive_nowait()
    send.close()
    receive.close()


async def test_closed_send_stream_errors():
    send, receive = create_memory_object_stream[None]()
    await send.aclose()
    with pytest.raises(EndOfStream):
        receive.receive_nowait()
    with pytest.raises(ClosedResourceError):
        await send.send(None)
    receive.close()


async def test_closed_receive_stream_errors():
    send, receive = create_memory_object_stream[None]()
    await receive.aclose()
    with pytest.raises(ClosedResourceError):
        receive.receive_nowait()
    with pytest.raises(BrokenResourceError):
        await send.send(None)
    send.close()


async def test_memory_nowait_closed_same_end_raises_closed():
    send, receive = create_memory_object_stream[str](1)
    receive.close()
    with pytest.raises(ClosedResourceError):
        receive.receive_nowait()
    send.close()


async def test_memory_stream_send_clone_delivers_item_to_receiver():
    send, receive = create_memory_object_stream[str](1)
    clone = send.clone()
    clone.send_nowait("via-clone")
    assert receive.receive_nowait() == "via-clone"
    send.close()
    clone.close()
    receive.close()


async def test_memory_stream_inf_buffer_accepted():
    send, receive = create_memory_object_stream[int](math.inf)
    send.send_nowait(1)
    send.send_nowait(2)
    assert receive.receive_nowait() == 1
    send.close()
    receive.close()


async def test_memory_stream_item_type_deprecation_warning():
    with pytest.warns(DeprecationWarning):
        create_memory_object_stream(1, item_type=str)


# ── Buffered byte streams ────────────────────────────────────────

async def test_buffered_receive_exactly_reads_across_chunks():
    send, receive = create_memory_object_stream[bytes](2)
    buffered = BufferedByteReceiveStream(receive)
    await send.send(b"ab")
    await send.send(b"cd")
    assert await buffered.receive_exactly(4) == b"abcd"
    send.close()
    receive.close()


async def test_buffered_receive_exactly_incomplete_raises():
    send, receive = create_memory_object_stream[bytes](1)
    buffered = BufferedByteReceiveStream(receive)
    await send.send(b"ab")
    await send.aclose()
    with pytest.raises(IncompleteRead):
        await buffered.receive_exactly(3)
    receive.close()


async def test_buffered_receive_until_returns_before_delimiter():
    send, receive = create_memory_object_stream[bytes](1)
    buffered = BufferedByteReceiveStream(receive)
    await send.send(b"abc:def")
    assert await buffered.receive_until(b":", 10) == b"abc"
    send.close()
    receive.close()


# ── Text streams ──────────────────────────────────────────────────

async def test_text_send_stream_encodes_to_bytes():
    send, receive = create_memory_object_stream[bytes](1)
    text = TextSendStream(send, encoding="utf-8")
    await text.send("hi")
    assert await receive.receive() == b"hi"
    await text.aclose()
    receive.close()


async def test_text_receive_stream_decodes_bytes():
    send, receive = create_memory_object_stream[bytes](1)
    text = TextReceiveStream(receive, encoding="utf-8")
    await send.send("hi".encode())
    assert await text.receive() == "hi"
    send.close()
    await text.aclose()


# ── Files and paths ───────────────────────────────────────────────

async def test_open_file_writes_and_reads_text(tmp_path):
    path = tmp_path / "data.txt"
    async with await open_file(path, "w+") as afp:
        await afp.write("hello")
        await afp.seek(0)
        assert await afp.read() == "hello"


async def test_async_path_read_write_roundtrip(tmp_path):
    path = AsyncPath(tmp_path / "p.txt")
    await path.write_text("abc")
    assert await path.read_text() == "abc"


async def test_async_path_iterdir_yields_created_entries(tmp_path):
    await AsyncPath(tmp_path / "first.txt").write_text("1")
    await AsyncPath(tmp_path / "second.txt").write_text("2")
    entries = [entry async for entry in AsyncPath(tmp_path).iterdir()]
    assert {entry.name for entry in entries} == {"first.txt", "second.txt"}
    assert all(isinstance(entry, AsyncPath) for entry in entries)


# ── Process execution ─────────────────────────────────────────────

async def test_run_process_check_raises_called_process_error():
    with pytest.raises(subprocess.CalledProcessError):
        await anyio.run_process([sys.executable, "-c", "import sys; sys.exit(3)"])


# ── Synchronization primitives ────────────────────────────────────

async def test_lock_released_by_non_owner_raises():
    lock = Lock()
    with pytest.raises(RuntimeError):
        lock.release()


async def test_lock_statistics_report_locked_state():
    lock = Lock()
    await lock.acquire()
    statistics = lock.statistics()
    assert statistics.locked is True
    assert statistics.tasks_waiting == 0
    lock.release()
    assert lock.statistics().locked is False


async def test_condition_notify_requires_lock():
    condition = Condition()
    with pytest.raises(RuntimeError):
        condition.notify()


def test_semaphore_rejects_invalid_initial_value():
    with pytest.raises(ValueError):
        Semaphore(-1)


async def test_semaphore_value_tracks_acquire_and_release():
    semaphore = Semaphore(2)
    await semaphore.acquire()
    assert semaphore.value == 1
    semaphore.release()
    assert semaphore.value == 2


async def test_capacity_limiter_rejects_double_borrow():
    limiter = CapacityLimiter(1)
    await limiter.acquire()
    with pytest.raises(RuntimeError):
        await limiter.acquire()
    limiter.release()


async def test_capacity_limiter_statistics_track_borrowed_tokens():
    limiter = CapacityLimiter(3)
    assert limiter.total_tokens == 3
    await limiter.acquire()
    statistics = limiter.statistics()
    assert statistics.borrowed_tokens == 1
    assert statistics.tasks_waiting == 0
    limiter.release()
    assert limiter.statistics().borrowed_tokens == 0


async def test_event_set_wakes_all_counted_waiters():
    event = Event()
    woken: list[str] = []

    async def waiter() -> None:
        await event.wait()
        woken.append("woken")

    async with create_task_group() as tg:
        tg.start_soon(waiter)
        tg.start_soon(waiter)
        await wait_all_tasks_blocked()
        assert event.statistics().tasks_waiting == 2
        event.set()
    assert woken == ["woken", "woken"]


def test_resource_guard_rejects_concurrent_entry():
    guard = ResourceGuard("using resource")
    with guard:
        with pytest.raises(BusyResourceError):
            with guard:
                pass


# ── Thread workers ────────────────────────────────────────────────

async def test_default_thread_limiter_reports_forty_total_tokens():
    assert to_thread.current_default_thread_limiter().total_tokens == 40


async def test_to_thread_run_sync_returns_callable_result():
    assert await to_thread.run_sync(len, "abcd") == 4
    assert await to_thread.run_sync(min, 9, 4, 7) == 4


def test_from_thread_run_sync_foreign_thread_requires_token():
    with pytest.raises(NoEventLoopError):
        anyio.from_thread.run_sync(lambda: None)


# ── Low-level primitives ─────────────────────────────────────────

async def test_runvar_set_get_reset_within_run():
    var = RunVar("generated_runvar", default="default")
    assert var.get() == "default"
    token = var.set("value")
    assert var.get() == "value"
    var.reset(token)
    assert var.get() == "default"


async def test_lowlevel_checkpoint_allows_progress():
    before = current_time()
    await checkpoint()
    assert current_time() >= before


async def test_current_token_available_inside_run():
    token = current_token()
    assert token is not None
    assert current_token() is token


def test_current_token_requires_event_loop():
    with pytest.raises(NoEventLoopError):
        current_token()


# ── Async functools ───────────────────────────────────────────────

async def test_functools_reduce_consumes_async_iterable():
    async def values():
        for item in [1, 2, 3]:
            yield item

    async def add(left: int, right: int) -> int:
        return left + right

    assert await reduce(add, values(), 0) == 6


async def test_functools_cache_reuses_coroutine_result():
    calls = 0

    @cache
    async def value() -> int:
        nonlocal calls
        calls += 1
        return 5

    assert await value() == 5
    assert await value() == 5
    assert calls == 1


async def test_functools_lru_cache_honors_arguments():
    calls = 0

    @lru_cache(maxsize=2)
    async def add_one(value: int) -> int:
        nonlocal calls
        calls += 1
        return value + 1

    assert await add_one(1) == 2
    assert await add_one(1) == 2
    assert await add_one(2) == 3
    assert calls == 2


# ── Deprecation and import surface ────────────────────────────────

def test_deprecated_worker_interpreter_alias_warns():
    with pytest.warns(DeprecationWarning):
        assert anyio.BrokenWorkerIntepreter is anyio.BrokenWorkerInterpreter


def test_stream_file_public_classes_are_importable():
    from anyio.streams.file import FileReadStream, FileStreamAttribute, FileWriteStream

    assert FileReadStream is not FileWriteStream
    assert FileStreamAttribute.file is not None


def test_abc_public_resource_and_task_types_are_importable():
    from anyio.abc import AsyncResource, TaskGroup

    assert AsyncResource is not TaskGroup
