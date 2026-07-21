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

async def test_upstream_receive_then_send() -> None:
    async def receiver() -> None:
        received_objects.append(await receive.receive())
        received_objects.append(await receive.receive())

    send, receive = create_memory_object_stream[str](0)
    received_objects: list[str] = []
    async with create_task_group() as tg:
        tg.start_soon(receiver)
        await wait_all_tasks_blocked()
        await send.send("hello")
        await send.send("anyio")

    assert received_objects == ["hello", "anyio"]
    send.close()
    receive.close()


async def test_upstream_iterate_memory_stream() -> None:
    async def receiver() -> None:
        received_objects.extend([item async for item in receive])

    send, receive = create_memory_object_stream[str]()
    received_objects: list[str] = []
    async with create_task_group() as tg:
        tg.start_soon(receiver)
        await send.send("hello")
        await send.send("anyio")
        await send.aclose()

    assert received_objects == ["hello", "anyio"]
    receive.close()


async def test_upstream_cancel_receive_restores_nowait_state() -> None:
    send, receive = create_memory_object_stream[str]()
    async with create_task_group() as tg:
        tg.start_soon(receive.receive)
        await wait_all_tasks_blocked()
        tg.cancel_scope.cancel()
    with pytest.raises(WouldBlock):
        send.send_nowait("hello")
    send.close()
    receive.close()


async def test_upstream_clone_keeps_other_ends_open() -> None:
    send1, receive1 = create_memory_object_stream[str](1)
    send2 = send1.clone()
    receive2 = receive1.clone()
    await send1.aclose()
    await receive1.aclose()
    send2.send_nowait("hello")
    assert receive2.receive_nowait() == "hello"
    send2.close()
    receive2.close()


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


async def test_stapled_object_stream_closes_both_halves() -> None:
    send, receive = create_memory_object_stream[str](1)
    stapled = StapledObjectStream(send, receive)
    await stapled.aclose()
    with pytest.raises(ClosedResourceError):
        send.send_nowait("x")
    with pytest.raises(ClosedResourceError):
        receive.receive_nowait()


async def test_wrap_file_closes_underlying_file(tmp_path) -> None:
    path = tmp_path / "wrapped.txt"
    raw = path.open("w+")
    wrapped = wrap_file(raw)
    await wrapped.write("x")
    await wrapped.aclose()
    assert raw.closed


async def test_temporary_directory_context_removes_path() -> None:
    async with anyio.TemporaryDirectory() as path:
        assert os.path.isdir(path)
    assert not os.path.exists(path)


async def test_run_process_captures_stdout() -> None:
    result = await anyio.run_process([sys.executable, "-c", "print('ok')"])
    assert result.returncode == 0
    assert result.stdout.strip() == b"ok"


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
