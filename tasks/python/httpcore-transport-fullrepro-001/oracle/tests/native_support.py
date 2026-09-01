from __future__ import annotations

import ssl
from collections.abc import AsyncIterator, Iterable, Iterator
from typing import Any

import hpack
import httpcore
import hyperframe.frame


def http11_response(
    body: bytes = b"ok",
    *,
    status: int = 200,
    reason: bytes = b"OK",
    headers: Iterable[tuple[bytes, bytes]] = (),
    body_chunks: Iterable[bytes] | None = None,
) -> list[bytes]:
    items = list(headers)
    lower = {name.lower() for name, _ in items}
    if b"content-length" not in lower and b"transfer-encoding" not in lower:
        items.append((b"Content-Length", str(len(body)).encode("ascii")))
    head = [b"HTTP/1.1 %d %s\r\n" % (status, reason)]
    head.extend(name + b": " + value + b"\r\n" for name, value in items)
    head.append(b"\r\n")
    chunks = list(body_chunks) if body_chunks is not None else ([body] if body else [])
    return [b"".join(head), *chunks]


def flatten(*scripts: Iterable[bytes]) -> list[bytes]:
    return [part for script in scripts for part in script]


class TLSInfo:
    def __init__(self, protocol: str = "http/1.1") -> None:
        self.protocol = protocol

    def selected_alpn_protocol(self) -> str:
        return self.protocol


class RecordingSyncStream(httpcore.NetworkStream):
    def __init__(
        self,
        chunks: Iterable[bytes],
        *,
        http2: bool = False,
        readable: bool = False,
    ) -> None:
        self.chunks = list(chunks)
        self.http2 = http2
        self.readable = readable
        self.read_calls: list[tuple[int, float | None]] = []
        self.write_calls: list[tuple[bytes, float | None]] = []
        self.tls_calls: list[tuple[ssl.SSLContext, str | None, float | None]] = []
        self.close_calls = 0

    def read(self, max_bytes: int, timeout: float | None = None) -> bytes:
        self.read_calls.append((max_bytes, timeout))
        return self.chunks.pop(0) if self.chunks else b""

    def write(self, buffer: bytes, timeout: float | None = None) -> None:
        self.write_calls.append((bytes(buffer), timeout))

    def close(self) -> None:
        self.close_calls += 1

    def start_tls(
        self,
        ssl_context: ssl.SSLContext,
        server_hostname: str | None = None,
        timeout: float | None = None,
    ) -> httpcore.NetworkStream:
        self.tls_calls.append((ssl_context, server_hostname, timeout))
        return self

    def get_extra_info(self, info: str) -> Any:
        if info == "ssl_object":
            return TLSInfo("h2" if self.http2 else "http/1.1")
        if info == "is_readable":
            return self.readable
        return None


class RecordingSyncBackend(httpcore.NetworkBackend):
    def __init__(
        self,
        scripts: Iterable[Iterable[bytes] | BaseException],
        *,
        http2: bool = False,
        readable: Iterable[bool] | None = None,
    ) -> None:
        self.scripts = list(scripts)
        self.http2 = http2
        self.readable = list(readable or [])
        self.connect_calls: list[dict[str, Any]] = []
        self.unix_calls: list[dict[str, Any]] = []
        self.sleep_calls: list[float] = []
        self.streams: list[RecordingSyncStream] = []

    def _next(self) -> RecordingSyncStream:
        script = self.scripts.pop(0)
        if isinstance(script, BaseException):
            raise script
        flag = self.readable.pop(0) if self.readable else False
        stream = RecordingSyncStream(script, http2=self.http2, readable=flag)
        self.streams.append(stream)
        return stream

    def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options: Iterable[tuple[Any, ...]] | None = None,
    ) -> httpcore.NetworkStream:
        self.connect_calls.append(
            {
                "host": host,
                "port": port,
                "timeout": timeout,
                "local_address": local_address,
                "socket_options": socket_options,
            }
        )
        return self._next()

    def connect_unix_socket(
        self,
        path: str,
        timeout: float | None = None,
        socket_options: Iterable[tuple[Any, ...]] | None = None,
    ) -> httpcore.NetworkStream:
        self.unix_calls.append(
            {"path": path, "timeout": timeout, "socket_options": socket_options}
        )
        return self._next()

    def sleep(self, seconds: float) -> None:
        self.sleep_calls.append(seconds)


class RecordingAsyncStream(httpcore.AsyncNetworkStream):
    def __init__(
        self,
        chunks: Iterable[bytes],
        *,
        http2: bool = False,
        readable: bool = False,
    ) -> None:
        self.chunks = list(chunks)
        self.http2 = http2
        self.readable = readable
        self.read_calls: list[tuple[int, float | None]] = []
        self.write_calls: list[tuple[bytes, float | None]] = []
        self.tls_calls: list[tuple[ssl.SSLContext, str | None, float | None]] = []
        self.close_calls = 0

    async def read(self, max_bytes: int, timeout: float | None = None) -> bytes:
        self.read_calls.append((max_bytes, timeout))
        return self.chunks.pop(0) if self.chunks else b""

    async def write(self, buffer: bytes, timeout: float | None = None) -> None:
        self.write_calls.append((bytes(buffer), timeout))

    async def aclose(self) -> None:
        self.close_calls += 1

    async def start_tls(
        self,
        ssl_context: ssl.SSLContext,
        server_hostname: str | None = None,
        timeout: float | None = None,
    ) -> httpcore.AsyncNetworkStream:
        self.tls_calls.append((ssl_context, server_hostname, timeout))
        return self

    def get_extra_info(self, info: str) -> Any:
        if info == "ssl_object":
            return TLSInfo("h2" if self.http2 else "http/1.1")
        if info == "is_readable":
            return self.readable
        return None


class RecordingAsyncBackend(httpcore.AsyncNetworkBackend):
    def __init__(
        self,
        scripts: Iterable[Iterable[bytes] | BaseException],
        *,
        http2: bool = False,
        readable: Iterable[bool] | None = None,
    ) -> None:
        self.scripts = list(scripts)
        self.http2 = http2
        self.readable = list(readable or [])
        self.connect_calls: list[dict[str, Any]] = []
        self.unix_calls: list[dict[str, Any]] = []
        self.sleep_calls: list[float] = []
        self.streams: list[RecordingAsyncStream] = []

    def _next(self) -> RecordingAsyncStream:
        script = self.scripts.pop(0)
        if isinstance(script, BaseException):
            raise script
        flag = self.readable.pop(0) if self.readable else False
        stream = RecordingAsyncStream(script, http2=self.http2, readable=flag)
        self.streams.append(stream)
        return stream

    async def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options: Iterable[tuple[Any, ...]] | None = None,
    ) -> httpcore.AsyncNetworkStream:
        self.connect_calls.append(
            {
                "host": host,
                "port": port,
                "timeout": timeout,
                "local_address": local_address,
                "socket_options": socket_options,
            }
        )
        return self._next()

    async def connect_unix_socket(
        self,
        path: str,
        timeout: float | None = None,
        socket_options: Iterable[tuple[Any, ...]] | None = None,
    ) -> httpcore.AsyncNetworkStream:
        self.unix_calls.append(
            {"path": path, "timeout": timeout, "socket_options": socket_options}
        )
        return self._next()

    async def sleep(self, seconds: float) -> None:
        self.sleep_calls.append(seconds)


class ClosingSyncBody:
    def __init__(self, chunks: Iterable[bytes]) -> None:
        self.chunks = list(chunks)
        self.close_calls = 0

    def __iter__(self) -> Iterator[bytes]:
        yield from self.chunks

    def close(self) -> None:
        self.close_calls += 1


class ClosingAsyncBody:
    def __init__(self, chunks: Iterable[bytes]) -> None:
        self.chunks = list(chunks)
        self.close_calls = 0

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for chunk in self.chunks:
            yield chunk

    async def aclose(self) -> None:
        self.close_calls += 1


def wire(stream: RecordingSyncStream) -> bytes:
    return b"".join(buffer for buffer, _ in stream.write_calls)


def async_wire(stream: RecordingAsyncStream) -> bytes:
    return b"".join(buffer for buffer, _ in stream.write_calls)


def h2_response_frames(
    responses: Iterable[tuple[int, bytes]], *, goaway_after: int | None = None
) -> list[bytes]:
    frames: list[bytes] = [hyperframe.frame.SettingsFrame().serialize()]
    encoder = hpack.Encoder()
    for index, (stream_id, body) in enumerate(responses, start=1):
        frames.append(
            hyperframe.frame.HeadersFrame(
                stream_id=stream_id,
                data=encoder.encode(
                    [(b":status", b"200"), (b"content-type", b"text/plain")]
                ),
                flags=["END_HEADERS"],
            ).serialize()
        )
        frames.append(
            hyperframe.frame.DataFrame(
                stream_id=stream_id, data=body, flags=["END_STREAM"]
            ).serialize()
        )
        if goaway_after == index:
            frames.append(
                hyperframe.frame.GoAwayFrame(
                    stream_id=0, error_code=0, last_stream_id=stream_id
                ).serialize()
            )
            frames.append(b"")
    return frames
