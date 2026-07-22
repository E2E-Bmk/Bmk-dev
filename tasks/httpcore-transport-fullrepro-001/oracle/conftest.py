"""Shared fixtures, helpers, and constants for httpcore oracle tests."""
from __future__ import annotations

import ssl
from typing import List, Sequence

import pytest

import httpcore


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TEST_URL = "http://example.com/"
TEST_HTTPS_URL = "https://example.com/"
TEST_BODY = b"Hello"


# ---------------------------------------------------------------------------
# Helper: build raw HTTP/1.1 response byte chunks
# ---------------------------------------------------------------------------


def http11_response(
    status: int = 200,
    reason: bytes = b"OK",
    headers: Sequence[tuple[bytes, bytes]] = (),
    body: bytes = b"Hello",
) -> list[bytes]:
    header_items = list(headers)
    lower_names = {name.lower() for name, _ in header_items}
    if b"content-length" not in lower_names:
        header_items.append((b"Content-Length", str(len(body)).encode("ascii")))
    lines: list[bytes] = [b"HTTP/1.1 %d %s\r\n" % (status, reason)]
    lines += [name + b": " + value + b"\r\n" for name, value in header_items]
    lines.append(b"\r\n")
    if body:
        lines.append(body)
    return lines


# ---------------------------------------------------------------------------
# Recording stream and backend for verifying wire bytes and backend calls
# ---------------------------------------------------------------------------


class TLSInfo:
    def selected_alpn_protocol(self):
        return "http/1.1"


class RecordingStream(httpcore.NetworkStream):
    def __init__(self, chunks: list[bytes]):
        self.chunks = list(chunks)
        self.writes: list[bytes] = []
        self.read_calls: list[tuple] = []
        self.close_calls = 0
        self.tls_calls: list[tuple] = []
        self.write_timeout = None

    def read(self, max_bytes, timeout=None):
        self.read_calls.append((max_bytes, timeout))
        if not self.chunks:
            return b""
        return self.chunks.pop(0)

    def write(self, buffer, timeout=None):
        self.writes.append(bytes(buffer))
        self.write_timeout = timeout

    def close(self):
        self.close_calls += 1

    def start_tls(self, ssl_context, server_hostname=None, timeout=None):
        assert isinstance(ssl_context, ssl.SSLContext)
        self.tls_calls.append((server_hostname, timeout))
        return self

    def get_extra_info(self, info):
        if info == "ssl_object":
            return TLSInfo()
        return None


class RecordingBackend(httpcore.NetworkBackend):
    def __init__(self, scripts: list):
        self.scripts = list(scripts)
        self.tcp_calls: list[dict] = []
        self.uds_calls: list[dict] = []
        self.sleep_calls: list[float] = []
        self.streams: list[RecordingStream] = []

    def _next_stream(self):
        script = self.scripts.pop(0)
        if isinstance(script, BaseException):
            raise script
        stream = RecordingStream(script)
        self.streams.append(stream)
        return stream

    def connect_tcp(
        self, host, port, timeout=None, local_address=None, socket_options=None
    ):
        self.tcp_calls.append(
            {
                "host": host,
                "port": port,
                "timeout": timeout,
                "local_address": local_address,
                "socket_options": socket_options,
            }
        )
        return self._next_stream()

    def connect_unix_socket(self, path, timeout=None, socket_options=None):
        self.uds_calls.append(
            {"path": path, "timeout": timeout, "socket_options": socket_options}
        )
        return self._next_stream()

    def sleep(self, seconds):
        self.sleep_calls.append(seconds)


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------


def pool_with(script, **kwargs) -> tuple[httpcore.ConnectionPool, RecordingBackend]:
    backend = RecordingBackend([script])
    pool = httpcore.ConnectionPool(network_backend=backend, **kwargs)
    return pool, backend


def written_bytes(stream: RecordingStream) -> bytes:
    return b"".join(stream.writes)


def header_block(stream: RecordingStream) -> bytes:
    return written_bytes(stream).split(b"\r\n\r\n", 1)[0]


def assert_header(stream: RecordingStream, name: bytes, value: bytes):
    lines = header_block(stream).split(b"\r\n")[1:]
    assert name + b": " + value in lines
