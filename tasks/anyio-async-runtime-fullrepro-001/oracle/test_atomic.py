from __future__ import annotations

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
from anyio.streams.stapled import StapledObjectStream
from anyio.streams.text import TextReceiveStream, TextSendStream
from anyio import Path as AsyncPath

pytestmark = pytest.mark.anyio

def test_upstream_invalid_max_buffer() -> None:
    with pytest.raises(ValueError):
        create_memory_object_stream(1.0)


def test_upstream_negative_max_buffer() -> None:
    with pytest.raises(ValueError):
        create_memory_object_stream(-1)


async def test_upstream_send_nowait_then_receive_nowait() -> None:
    send, receive = create_memory_object_stream[str](2)
    send.send_nowait("hello")
    send.send_nowait("anyio")
    assert receive.receive_nowait() == "hello"
    assert receive.receive_nowait() == "anyio"
    send.close()
    receive.close()


async def test_upstream_closed_send_stream_errors() -> None:
    send, receive = create_memory_object_stream[None]()
    await send.aclose()
    with pytest.raises(EndOfStream):
        receive.receive_nowait()
    with pytest.raises(ClosedResourceError):
        await send.send(None)
    receive.close()


async def test_upstream_closed_receive_stream_errors() -> None:
    send, receive = create_memory_object_stream[None]()
    await receive.aclose()
    with pytest.raises(ClosedResourceError):
        receive.receive_nowait()
    with pytest.raises(BrokenResourceError):
        await send.send(None)
    send.close()


async def test_upstream_buffered_receive_exactly() -> None:
    send_stream, receive_stream = create_memory_object_stream[bytes](2)
    buffered_stream = BufferedByteReceiveStream(receive_stream)
    await send_stream.send(b"abcd")
    await send_stream.send(b"efgh")
    assert await buffered_stream.receive_exactly(8) == b"abcdefgh"
    send_stream.close()
    receive_stream.close()


async def test_upstream_buffered_receive_exactly_incomplete() -> None:
    send_stream, receive_stream = create_memory_object_stream[bytes](1)
    buffered_stream = BufferedByteReceiveStream(receive_stream)
    await send_stream.send(b"abcd")
    await send_stream.aclose()
    with pytest.raises(IncompleteRead):
        await buffered_stream.receive_exactly(8)
    receive_stream.close()


async def test_upstream_buffered_receive_until() -> None:
    send_stream, receive_stream = create_memory_object_stream[bytes](2)
    buffered_stream = BufferedByteReceiveStream(receive_stream)
    await send_stream.send(b"abcd")
    await send_stream.send(b"efgh")
    assert await buffered_stream.receive_until(b"de", 10) == b"abc"
    assert await buffered_stream.receive_until(b"h", 10) == b"fg"
    send_stream.close()
    receive_stream.close()


def test_deprecated_worker_interpreter_alias_warns() -> None:
    with pytest.warns(DeprecationWarning):
        assert anyio.BrokenWorkerIntepreter is anyio.BrokenWorkerInterpreter


def test_stream_file_public_classes_are_importable() -> None:
    from anyio.streams.file import FileReadStream, FileStreamAttribute, FileWriteStream

    assert FileReadStream is not FileWriteStream
    assert FileStreamAttribute.file is not None


def test_abc_public_resource_and_task_types_are_importable() -> None:
    from anyio.abc import AsyncResource, TaskGroup

    assert AsyncResource is not TaskGroup


def test_available_backend_projection_contains_asyncio() -> None:
    assert "asyncio" in anyio.get_available_backends()
    assert set(anyio.get_available_backends()).issubset(set(anyio.get_all_backends()))


def test_all_backends_public_tuple() -> None:
    assert anyio.get_all_backends() == ("asyncio", "trio")


def test_run_invokes_coroutine_and_returns_value() -> None:
    async def add(a: int, b: int) -> int:
        return a + b

    assert run(add, 2, 5, backend="asyncio") == 7


def test_run_rejects_unknown_backend() -> None:
    async def noop() -> None:
        return None

    with pytest.raises(LookupError):
        run(noop, backend="missing-backend")


async def test_current_time_available_inside_event_loop() -> None:
    assert isinstance(current_time(), float)


async def test_sleep_until_past_deadline_returns_promptly() -> None:
    before = current_time()
    await sleep_until(before - 1)
    assert current_time() >= before


async def test_move_on_after_suppresses_own_timeout() -> None:
    with move_on_after(0.01) as scope:
        await sleep(1)
    assert scope.cancelled_caught is True


async def test_fail_after_raises_timeout_error() -> None:
    with pytest.raises(TimeoutError):
        with fail_after(0.01):
            await sleep(1)


async def test_memory_stream_send_receive_one_item() -> None:
    send, receive = create_memory_object_stream[str](1)
    await send.send("payload")
    assert await receive.receive() == "payload"
    send.close(); receive.close()


async def test_memory_stream_nowait_would_block_when_empty() -> None:
    send, receive = create_memory_object_stream[str](1)
    with pytest.raises(WouldBlock):
        receive.receive_nowait()
    send.close(); receive.close()


async def test_buffered_receive_exactly_reads_across_chunks() -> None:
    send, receive = create_memory_object_stream[bytes](2)
    buffered = BufferedByteReceiveStream(receive)
    await send.send(b"ab")
    await send.send(b"cd")
    assert await buffered.receive_exactly(4) == b"abcd"
    send.close(); receive.close()


async def test_buffered_receive_until_returns_before_delimiter() -> None:
    send, receive = create_memory_object_stream[bytes](1)
    buffered = BufferedByteReceiveStream(receive)
    await send.send(b"abc:def")
    assert await buffered.receive_until(b":", 10) == b"abc"
    send.close(); receive.close()


async def test_buffered_receive_exactly_incomplete_raises() -> None:
    send, receive = create_memory_object_stream[bytes](1)
    buffered = BufferedByteReceiveStream(receive)
    await send.send(b"ab")
    await send.aclose()
    with pytest.raises(IncompleteRead):
        await buffered.receive_exactly(3)
    receive.close()


async def test_text_send_stream_encodes_to_bytes() -> None:
    send, receive = create_memory_object_stream[bytes](1)
    text = TextSendStream(send, encoding="utf-8")
    await text.send("hi")
    assert await receive.receive() == b"hi"
    await text.aclose(); receive.close()


async def test_text_receive_stream_decodes_bytes() -> None:
    send, receive = create_memory_object_stream[bytes](1)
    text = TextReceiveStream(receive, encoding="utf-8")
    await send.send("hi".encode())
    assert await text.receive() == "hi"
    send.close(); await text.aclose()


async def test_open_file_writes_and_reads_text(tmp_path) -> None:
    path = tmp_path / "data.txt"
    async with await open_file(path, "w+") as afp:
        await afp.write("hello")
        await afp.seek(0)
        assert await afp.read() == "hello"


async def test_async_path_read_write_roundtrip(tmp_path) -> None:
    path = AsyncPath(tmp_path / "p.txt")
    await path.write_text("abc")
    assert await path.read_text() == "abc"


async def test_run_process_check_raises_called_process_error() -> None:
    with pytest.raises(subprocess.CalledProcessError):
        await anyio.run_process([sys.executable, "-c", "import sys; sys.exit(3)"])


async def test_lock_released_by_non_owner_raises() -> None:
    lock = Lock()
    with pytest.raises(RuntimeError):
        lock.release()


async def test_condition_notify_requires_lock() -> None:
    condition = Condition()
    with pytest.raises(RuntimeError):
        condition.notify()


async def test_capacity_limiter_rejects_double_borrow() -> None:
    limiter = CapacityLimiter(1)
    await limiter.acquire()
    with pytest.raises(RuntimeError):
        await limiter.acquire()
    limiter.release()


async def test_runvar_set_get_reset_within_run() -> None:
    var = RunVar("generated_runvar", default="default")
    assert var.get() == "default"
    token = var.set("value")
    assert var.get() == "value"
    var.reset(token)
    assert var.get() == "default"


async def test_functools_reduce_consumes_async_iterable() -> None:
    async def values():
        for item in [1, 2, 3]:
            yield item

    async def add(left: int, right: int) -> int:
        return left + right

    assert await reduce(add, values(), 0) == 6


async def test_functools_cache_reuses_coroutine_result() -> None:
    calls = 0

    @cache
    async def value() -> int:
        nonlocal calls
        calls += 1
        return 5

    assert await value() == 5
    assert await value() == 5
    assert calls == 1


async def test_functools_lru_cache_honors_arguments() -> None:
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


async def test_lowlevel_checkpoint_allows_progress() -> None:
    before = current_time()
    await checkpoint()
    assert current_time() >= before


async def test_current_token_available_inside_run() -> None:
    assert current_token() is not None


async def test_memory_nowait_closed_same_end_raises_closed() -> None:
    send, receive = create_memory_object_stream[str](1)
    receive.close()
    with pytest.raises(ClosedResourceError):
        receive.receive_nowait()
    send.close()


def test_current_time_requires_event_loop() -> None:
    with pytest.raises(NoEventLoopError):
        current_time()


def test_cancelled_class_requires_event_loop() -> None:
    with pytest.raises(NoEventLoopError):
        anyio.get_cancelled_exc_class()


def test_from_thread_run_sync_foreign_thread_requires_token() -> None:
    with pytest.raises(NoEventLoopError):
        anyio.from_thread.run_sync(lambda: None)


def test_semaphore_rejects_invalid_initial_value() -> None:
    with pytest.raises(ValueError):
        Semaphore(-1)


def test_resource_guard_rejects_concurrent_entry() -> None:
    guard = ResourceGuard("using resource")
    with guard:
        with pytest.raises(BusyResourceError):
            with guard:
                pass


def test_current_token_requires_event_loop() -> None:
    with pytest.raises(NoEventLoopError):
        current_token()
