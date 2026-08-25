"""Integration tests for anyio.

Each test exercises ≥2 public API boundaries or validates cross-view invariants.
"""
from __future__ import annotations

import os
import subprocess
import sys
from contextvars import ContextVar

import pytest

import anyio
from anyio import (
    BrokenResourceError,
    CapacityLimiter,
    ClosedResourceError,
    EndOfStream,
    Event,
    Lock,
    TaskCancelled,
    WouldBlock,
    create_memory_object_stream,
    create_task_group,
    current_effective_deadline,
    current_time,
    move_on_after,
    open_file,
    run,
    sleep,
    to_thread,
    wait_all_tasks_blocked,
    wrap_file,
)
from anyio.abc import TaskStatus
from anyio.lowlevel import current_token
from anyio.streams.buffered import BufferedByteReceiveStream
from anyio.streams.stapled import StapledObjectStream
from anyio.streams.text import TextReceiveStream, TextSendStream
from anyio import Path as AsyncPath

pytestmark = pytest.mark.anyio

# ── State consistency: send → receive across task group ───────────

@pytest.mark.depends_on("test_memory_stream_send_receive_one_item")
async def test_send_receive_across_task_group_unbuffered():
    """Seam: state consistency — send across task group matches receive order."""
    async def receiver():
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


@pytest.mark.depends_on("test_memory_stream_send_receive_one_item")
async def test_iterate_memory_stream_closes_after_send_end():
    """Seam: lifecycle crossing — async iteration completes after send end."""
    async def receiver():
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


# ── Protocol handoff: cancel → nowait state ───────────────────────

@pytest.mark.depends_on("test_memory_stream_nowait_would_block_when_empty")
async def test_cancel_receive_restores_nowait_state():
    """Seam: protocol handoff — cancelled receive restores nowait send state."""
    send, receive = create_memory_object_stream[str]()
    async with create_task_group() as tg:
        tg.start_soon(receive.receive)
        await wait_all_tasks_blocked()
        tg.cancel_scope.cancel()
    with pytest.raises(WouldBlock):
        send.send_nowait("hello")
    send.close()
    receive.close()


# ── Lifecycle: clone keeps stream open ────────────────────────────

@pytest.mark.depends_on("test_memory_stream_send_clone_delivers_item_to_receiver")
async def test_clone_keeps_other_ends_open():
    """Seam: lifecycle crossing — closing one clone leaves sibling ends usable."""
    send1, receive1 = create_memory_object_stream[str](1)
    send2 = send1.clone()
    receive2 = receive1.clone()
    await send1.aclose()
    await receive1.aclose()
    send2.send_nowait("hello")
    assert receive2.receive_nowait() == "hello"
    send2.close()
    receive2.close()


# ── Configuration interaction: timeout ↔ deadline ─────────────────

@pytest.mark.depends_on("test_current_effective_deadline_reports_inf_and_minus_inf")
async def test_effective_deadline_reflects_timeout_scope():
    """Seam: config interaction — timeout scope updates effective deadline."""
    with move_on_after(5):
        assert current_effective_deadline() < float("inf")


# ── State consistency: task group waits for children ──────────────

@pytest.mark.depends_on("test_start_soon_handle_returns_result_after_completion")
async def test_task_group_waits_for_child_result_side_effect():
    """Seam: state consistency — task group exit waits for child side effects."""
    seen: list[str] = []

    async def child() -> None:
        await sleep(0)
        seen.append("done")

    async with create_task_group() as tg:
        tg.start_soon(child)
    assert seen == ["done"]


# ── Protocol handoff: start → started value ──────────────────────

@pytest.mark.depends_on("test_start_soon_handle_returns_result_after_completion")
async def test_task_group_start_returns_started_value():
    """Seam: protocol handoff — task group start returns started value."""
    async def child(*, task_status: TaskStatus[str]) -> None:
        task_status.started("ready")
        await sleep(0)

    async with create_task_group() as tg:
        assert await tg.start(child) == "ready"


# ── Cross-view: task handle projection matches start and return ──

@pytest.mark.depends_on("test_start_soon_handle_returns_result_after_completion")
async def test_task_handle_projection_matches_started_and_returned_values():
    """CVI-N: task handle projection matches start and return values."""
    async def child(*, task_status: TaskStatus[str]) -> str:
        task_status.started("ready")
        await sleep(0)
        return "done"

    async with create_task_group() as tg:
        handle = await tg.start(child, return_handle=True)
        assert handle.start_value == "ready"
        assert await handle == "done"
        assert handle.return_value == "done"


# ── Error propagation: all receive clones closed → broken send ───

@pytest.mark.depends_on("test_closed_receive_stream_errors")
async def test_memory_stream_close_all_receive_clones_breaks_send():
    """Seam: error propagation — closing all receive clones breaks send."""
    send, receive = create_memory_object_stream[str](1)
    clone = receive.clone()
    receive.close()
    clone.close()
    with pytest.raises(BrokenResourceError):
        await send.send("x")
    send.close()


# ── Lifecycle: async iteration after send close ──────────────────

@pytest.mark.depends_on("test_memory_stream_send_receive_one_item")
async def test_memory_stream_async_iteration_finishes_after_send_close():
    """Seam: lifecycle crossing — async iteration finishes after send close."""
    send, receive = create_memory_object_stream[int](1)
    await send.send(1)
    await send.aclose()
    assert [item async for item in receive] == [1]
    receive.close()


# ── Lifecycle: stapled stream closes both halves ─────────────────

@pytest.mark.depends_on("test_closed_send_stream_errors", "test_closed_receive_stream_errors")
async def test_stapled_object_stream_closes_both_halves():
    """Seam: lifecycle crossing — stapled stream close closes both halves."""
    send, receive = create_memory_object_stream[str](1)
    stapled = StapledObjectStream(send, receive)
    await stapled.aclose()
    with pytest.raises(ClosedResourceError):
        send.send_nowait("x")
    with pytest.raises(ClosedResourceError):
        receive.receive_nowait()


# ── Lifecycle: wrap_file closes underlying file ──────────────────

@pytest.mark.depends_on("test_open_file_writes_and_reads_text")
async def test_wrap_file_closes_underlying_file(tmp_path):
    """Seam: lifecycle crossing — wrapped async file close closes underlying file."""
    path = tmp_path / "wrapped.txt"
    raw = path.open("w+")
    wrapped = wrap_file(raw)
    await wrapped.write("x")
    await wrapped.aclose()
    assert raw.closed


# ── Lifecycle: temporary directory removed on exit ────────────────

async def test_temporary_directory_context_removes_path():
    """Seam: lifecycle crossing — temporary directory removed on context exit."""
    async with anyio.TemporaryDirectory() as path:
        assert os.path.isdir(path)
    assert not os.path.exists(path)


# ── State consistency: process output capture ─────────────────────

async def test_run_process_captures_stdout():
    """Seam: state consistency — run_process stdout matches child print output."""
    result = await anyio.run_process([sys.executable, "-c", "print('ok')"])
    assert result.returncode == 0
    assert result.stdout.strip() == b"ok"


# ── Cross-view: context vars copied to thread, not back-propagated

@pytest.mark.depends_on("test_to_thread_run_sync_returns_callable_result")
async def test_to_thread_copies_contextvars_without_back_propagation():
    """CVI-N: to_thread copies contextvars without back-propagation."""
    var: ContextVar[str] = ContextVar("generated_var", default="unset")
    var.set("caller")

    def worker() -> str:
        seen = var.get()
        var.set("worker")
        return seen

    assert await to_thread.run_sync(worker) == "caller"
    assert var.get() == "caller"


# ── Cross-view: from_thread uses originating event loop ──────────

@pytest.mark.depends_on("test_to_thread_run_sync_returns_callable_result")
async def test_from_thread_run_sync_uses_originating_loop():
    """CVI-N: from_thread run_sync uses originating event loop."""
    def worker() -> float:
        return anyio.from_thread.run_sync(current_time)

    assert isinstance(await to_thread.run_sync(worker), float)


# ── State consistency: event wakes waiter in task group ───────────

@pytest.mark.depends_on("test_event_set_wakes_all_counted_waiters")
async def test_event_wakes_waiter():
    """Seam: state consistency — event set wakes blocked waiter in task group."""
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


# ── Representative workflow: memory + timeout ─────────────────────

@pytest.mark.depends_on("test_memory_stream_send_receive_one_item", "test_move_on_after_suppresses_own_timeout")
async def test_representative_memory_timeout_workflow():
    """Seam: lifecycle crossing — memory stream receive within timeout scope."""
    send, receive = create_memory_object_stream[bytes](1)
    await send.send(b"abc")
    with move_on_after(1) as scope:
        assert await receive.receive() == b"abc"
    assert scope.cancelled_caught is False
    send.close()
    receive.close()


# ── Representative workflow: task start and cancel ────────────────

@pytest.mark.depends_on("test_start_soon_handle_returns_result_after_completion")
async def test_representative_task_start_and_cancel_workflow():
    """Seam: lifecycle crossing — task start then cancel scope termination."""
    async def worker(*, task_status: TaskStatus[str]) -> None:
        task_status.started("started")
        await sleep(10)

    async with create_task_group() as tg:
        assert await tg.start(worker) == "started"
        tg.cancel_scope.cancel()


# ── Representative workflow: task + memory + file ─────────────────

@pytest.mark.depends_on("test_memory_stream_send_receive_one_item", "test_open_file_writes_and_reads_text")
async def test_representative_task_memory_file_workflow(tmp_path):
    """Seam: lifecycle crossing — task start writes file and sends on stream."""
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


# ── Cross-view: buffered stream ↔ memory stream ──────────────────

@pytest.mark.depends_on("test_buffered_receive_exactly_reads_across_chunks")
async def test_buffered_stream_combines_multi_chunk_reads():
    """CVI-N: buffered stream receive_exactly spans memory stream chunks."""
    send, receive = create_memory_object_stream[bytes](2)
    buffered = BufferedByteReceiveStream(receive)
    await send.send(b"abcd")
    await send.send(b"efgh")
    assert await buffered.receive_exactly(8) == b"abcdefgh"
    await send.send(b"xy!")
    assert await buffered.receive_until(b"!", 10) == b"xy"
    send.close()
    receive.close()


# ── Cross-view: buffered delimiter across chunks ──────────────────

@pytest.mark.depends_on("test_buffered_receive_until_returns_before_delimiter")
async def test_buffered_receive_until_across_chunks():
    """CVI-N: buffered receive_until delimiter search spans chunks."""
    send, receive = create_memory_object_stream[bytes](2)
    buffered = BufferedByteReceiveStream(receive)
    await send.send(b"abcd")
    await send.send(b"efgh")
    assert await buffered.receive_until(b"de", 10) == b"abc"
    assert await buffered.receive_until(b"h", 10) == b"fg"
    send.close()
    receive.close()


# ── CVI-2: cancel scope → TaskHandle cancelled state ─────────────

@pytest.mark.depends_on("test_start_soon_handle_returns_result_after_completion")
async def test_cancel_scope_moves_task_handle_to_cancelled():
    """CVI-2: cancel_scope.cancel moves unfinished TaskHandle to cancelled.
    Seam: state consistency — cancel scope and task handle status agree."""
    async def long_task():
        await sleep(999)

    async with create_task_group() as tg:
        handle = tg.start_soon(long_task)
        await wait_all_tasks_blocked()
        tg.cancel_scope.cancel()

    with pytest.raises(TaskCancelled):
        handle.return_value


# ── State consistency: Lock mutual exclusion in task group ────────

@pytest.mark.depends_on("test_lock_statistics_report_locked_state")
async def test_lock_enforces_mutual_exclusion_across_tasks():
    """Seam: state consistency — Lock enforces mutual exclusion in task group.
    Seam: lifecycle crossing — Lock acquire/release spans task lifecycle."""
    lock = Lock()
    concurrent_count = 0
    max_concurrent = 0

    async def worker():
        nonlocal concurrent_count, max_concurrent
        await lock.acquire()
        try:
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await sleep(0.01)
            concurrent_count -= 1
        finally:
            lock.release()

    async with create_task_group() as tg:
        for _ in range(3):
            tg.start_soon(worker)

    assert max_concurrent == 1


# ── State consistency: CapacityLimiter limits task group concurrency

@pytest.mark.depends_on("test_capacity_limiter_statistics_track_borrowed_tokens")
async def test_capacity_limiter_limits_concurrency_in_task_group():
    """Seam: state consistency — CapacityLimiter limits concurrent borrows.
    Seam: lifecycle crossing — limiter acquire/release across task lifecycle."""
    limiter = CapacityLimiter(2)
    max_concurrent = 0
    concurrent_count = 0

    async def worker():
        nonlocal concurrent_count, max_concurrent
        async with limiter:
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await sleep(0.01)
            concurrent_count -= 1

    async with create_task_group() as tg:
        for _ in range(5):
            tg.start_soon(worker)

    assert max_concurrent <= 2


# ── Cross-view: text stream encode/decode across task group ───────

@pytest.mark.depends_on("test_text_send_stream_encodes_to_bytes", "test_text_receive_stream_decodes_bytes")
async def test_text_stream_roundtrip_across_task_group():
    """CVI-N: text stream encode/decode roundtrip across task group boundary."""
    send_bytes, receive_bytes = create_memory_object_stream[bytes](1)
    text_send = TextSendStream(send_bytes, encoding="utf-8")
    text_receive = TextReceiveStream(receive_bytes, encoding="utf-8")
    received: list[str] = []

    async def consumer():
        received.append(await text_receive.receive())

    async with create_task_group() as tg:
        tg.start_soon(consumer)
        await wait_all_tasks_blocked()
        await text_send.send("hello-text")

    assert received == ["hello-text"]
    await text_send.aclose()
    await text_receive.aclose()


# ── State consistency: async path writes match real filesystem ────

@pytest.mark.depends_on("test_async_path_read_write_roundtrip")
async def test_async_path_operations_match_real_filesystem(tmp_path):
    """Seam: state consistency — async path operations match real filesystem state."""
    apath = AsyncPath(tmp_path / "sub" / "deep")
    await apath.mkdir(parents=True)
    assert (tmp_path / "sub" / "deep").is_dir()
    target = apath / "data.txt"
    await target.write_text("content")
    assert await target.exists()
    assert await target.read_text() == "content"
    entries = [e async for e in apath.iterdir()]
    assert [e.name for e in entries] == ["data.txt"]


# ── State consistency: lock serializes concurrent task group access

@pytest.mark.depends_on("test_lock_statistics_report_locked_state")
async def test_lock_serializes_concurrent_task_group_access():
    """Seam: state consistency — lock serializes concurrent task group access."""
    lock = Lock()
    counter = [0]
    max_concurrent = [0]

    async def worker():
        async with lock:
            counter[0] += 1
            if counter[0] > max_concurrent[0]:
                max_concurrent[0] = counter[0]
            await sleep(0)
            counter[0] -= 1

    async with create_task_group() as tg:
        for _ in range(5):
            tg.start_soon(worker)

    assert max_concurrent[0] == 1
