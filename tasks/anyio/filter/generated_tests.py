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
    ConnectionFailed,
    EndOfStream,
    Event,
    IncompleteRead,
    Lock,
    NoEventLoopError,
    ResourceGuard,
    RunFinishedError,
    Semaphore,
    TypedAttributeLookupError,
    TypedAttributeProvider,
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
    wrap_file,
)
from anyio.abc import SocketAttribute, TaskStatus
from anyio.functools import cache, lru_cache, reduce
from anyio.lowlevel import RunVar, checkpoint, current_token
from anyio.streams.buffered import BufferedByteReceiveStream
from anyio.streams.stapled import StapledObjectStream
from anyio.streams.text import TextReceiveStream, TextSendStream
from anyio import Path as AsyncPath

pytestmark = pytest.mark.anyio


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


def test_current_time_requires_event_loop() -> None:
    with pytest.raises(NoEventLoopError):
        current_time()


def test_cancelled_class_requires_event_loop() -> None:
    with pytest.raises(NoEventLoopError):
        anyio.get_cancelled_exc_class()


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


async def test_effective_deadline_reflects_timeout_scope() -> None:
    with move_on_after(5):
        assert current_effective_deadline() < float("inf")


async def test_task_group_waits_for_child_result_side_effect() -> None:
    seen: list[str] = []

    async def child() -> None:
        await sleep(0)
        seen.append("done")

    async with create_task_group() as tg:
        tg.start_soon(child)
    assert seen == ["done"]


async def test_task_group_start_returns_started_value() -> None:
    async def child(*, task_status: TaskStatus[str]) -> None:
        task_status.started("ready")
        await sleep(0)

    async with create_task_group() as tg:
        assert await tg.start(child) == "ready"


async def test_task_handle_projection_matches_started_and_returned_values() -> None:
    async def child(*, task_status: TaskStatus[str]) -> str:
        task_status.started("ready")
        await sleep(0)
        return "done"

    async with create_task_group() as tg:
        handle = await tg.start(child, return_handle=True)
        assert handle.start_value == "ready"
        assert await handle == "done"
        assert handle.return_value == "done"


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


async def test_memory_stream_close_all_receive_clones_breaks_send() -> None:
    send, receive = create_memory_object_stream[str](1)
    clone = receive.clone()
    receive.close(); clone.close()
    with pytest.raises(BrokenResourceError):
        await send.send("x")
    send.close()


async def test_memory_stream_async_iteration_finishes_after_send_close() -> None:
    send, receive = create_memory_object_stream[int](1)
    await send.send(1)
    await send.aclose()
    assert [item async for item in receive] == [1]
    receive.close()


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


async def test_stapled_object_stream_closes_both_halves() -> None:
    send, receive = create_memory_object_stream[str](1)
    stapled = StapledObjectStream(send, receive)
    await stapled.aclose()
    with pytest.raises(ClosedResourceError):
        send.send_nowait("x")
    with pytest.raises(ClosedResourceError):
        receive.receive_nowait()


async def test_open_file_writes_and_reads_text(tmp_path) -> None:
    path = tmp_path / "data.txt"
    async with await open_file(path, "w+") as afp:
        await afp.write("hello")
        await afp.seek(0)
        assert await afp.read() == "hello"


async def test_wrap_file_closes_underlying_file(tmp_path) -> None:
    path = tmp_path / "wrapped.txt"
    raw = path.open("w+")
    wrapped = wrap_file(raw)
    await wrapped.write("x")
    await wrapped.aclose()
    assert raw.closed


async def test_async_path_read_write_roundtrip(tmp_path) -> None:
    path = AsyncPath(tmp_path / "p.txt")
    await path.write_text("abc")
    assert await path.read_text() == "abc"


async def test_temporary_directory_context_removes_path() -> None:
    async with anyio.TemporaryDirectory() as path:
        assert os.path.isdir(path)
    assert not os.path.exists(path)


async def test_run_process_captures_stdout() -> None:
    result = await anyio.run_process([sys.executable, "-c", "print('ok')"])
    assert result.returncode == 0
    assert result.stdout.strip() == b"ok"


async def test_run_process_check_raises_called_process_error() -> None:
    with pytest.raises(subprocess.CalledProcessError):
        await anyio.run_process([sys.executable, "-c", "import sys; sys.exit(3)"])


async def test_to_thread_copies_contextvars_without_back_propagation() -> None:
    var: ContextVar[str] = ContextVar("generated_var", default="unset")
    var.set("caller")

    def worker() -> str:
        seen = var.get()
        var.set("worker")
        return seen

    assert await to_thread.run_sync(worker) == "caller"
    assert var.get() == "caller"


async def test_from_thread_run_sync_uses_originating_loop() -> None:
    def worker() -> float:
        return anyio.from_thread.run_sync(current_time)

    assert isinstance(await to_thread.run_sync(worker), float)


def test_from_thread_run_sync_foreign_thread_requires_token() -> None:
    with pytest.raises(NoEventLoopError):
        anyio.from_thread.run_sync(lambda: None)


async def test_event_wakes_waiter() -> None:
    event = Event()
    seen: list[str] = []

    async def waiter() -> None:
        await event.wait()
        seen.append("set")

    async with create_task_group() as tg:
        tg.start_soon(waiter)
        await sleep(0)
        event.set()
    assert seen == ["set"]


async def test_lock_released_by_non_owner_raises() -> None:
    lock = Lock()
    with pytest.raises(RuntimeError):
        lock.release()


def test_semaphore_rejects_invalid_initial_value() -> None:
    with pytest.raises(ValueError):
        Semaphore(-1)


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


def test_resource_guard_rejects_concurrent_entry() -> None:
    guard = ResourceGuard("using resource")
    with guard:
        with pytest.raises(BusyResourceError):
            with guard:
                pass


async def test_runvar_set_get_reset_within_run() -> None:
    var = RunVar("generated_runvar", default="default")
    assert var.get() == "default"
    token = var.set("value")
    assert var.get() == "value"
    var.reset(token)
    assert var.get() == "default"


class EmptyProvider(TypedAttributeProvider):
    @property
    def extra_attributes(self):
        return {}


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


def test_current_token_requires_event_loop() -> None:
    with pytest.raises(NoEventLoopError):
        current_token()


async def test_memory_nowait_closed_same_end_raises_closed() -> None:
    send, receive = create_memory_object_stream[str](1)
    receive.close()
    with pytest.raises(ClosedResourceError):
        receive.receive_nowait()
    send.close()


async def test_representative_memory_timeout_workflow() -> None:
    send, receive = create_memory_object_stream[bytes](1)
    await send.send(b"abc")
    with move_on_after(1) as scope:
        assert await receive.receive() == b"abc"
    assert scope.cancelled_caught is False
    send.close(); receive.close()


async def test_representative_task_start_and_cancel_workflow() -> None:
    async def worker(*, task_status: TaskStatus[str]) -> None:
        task_status.started("started")
        await sleep(10)

    async with create_task_group() as tg:
        assert await tg.start(worker) == "started"
        tg.cancel_scope.cancel()


async def test_representative_task_memory_file_workflow(tmp_path) -> None:
    send, receive = create_memory_object_stream[str](1)
    path = tmp_path / "workflow.txt"

    async def producer(*, task_status: TaskStatus[str]) -> None:
        task_status.started("ready")
        async with await open_file(path, "w") as afp:
            await afp.write("abc")

        await send.send("abc")
        await send.aclose()

    async with create_task_group() as tg:
        assert await tg.start(producer) == "ready"
        with move_on_after(1) as scope:
            assert await receive.receive() == "abc"

    assert scope.cancelled_caught is False
    assert path.read_text() == "abc"
