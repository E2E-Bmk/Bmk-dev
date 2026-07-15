from __future__ import annotations

import pytest

from anyio import (
    BrokenResourceError,
    ClosedResourceError,
    EndOfStream,
    IncompleteRead,
    WouldBlock,
    create_memory_object_stream,
    create_task_group,
    fail_after,
    wait_all_tasks_blocked,
)
from anyio.streams.buffered import BufferedByteReceiveStream

pytestmark = pytest.mark.anyio


def test_upstream_invalid_max_buffer() -> None:
    with pytest.raises(ValueError):
        create_memory_object_stream(1.0)


def test_upstream_negative_max_buffer() -> None:
    with pytest.raises(ValueError):
        create_memory_object_stream(-1)


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


async def test_upstream_send_nowait_then_receive_nowait() -> None:
    send, receive = create_memory_object_stream[str](2)
    send.send_nowait("hello")
    send.send_nowait("anyio")
    assert receive.receive_nowait() == "hello"
    assert receive.receive_nowait() == "anyio"
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
