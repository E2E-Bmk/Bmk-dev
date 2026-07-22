"""Integration tests for httpcore-transport-fullrepro-001.

Each test exercises ≥2 public API boundaries working together.
These tests verify composition seams: state consistency across components,
protocol handoff (Request→serializer→stream), error propagation,
configuration interaction, and lifecycle transitions.
"""
from __future__ import annotations

import ssl

import pytest

import httpcore
from conftest import (
    RecordingBackend,
    RecordingStream,
    assert_header,
    header_block,
    http11_response,
    pool_with,
    written_bytes,
)


# =============================================================================
# Request serialization through pool (Request model → HTTP/1.1 wire)
# Seam: protocol handoff — Request attributes → serialized wire bytes
# =============================================================================


@pytest.mark.depends_on("test_request_stores_method_as_bytes", "test_request_url_is_parsed_url_object")
def test_request_line_uses_method_path_and_query_on_wire():
    """Seam: protocol handoff — Request method, path, and query serialized to HTTP/1.1 wire line."""
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request("POST", "http://node.test/search?q=red&page=2")
    assert written_bytes(backend.streams[0]).startswith(
        b"POST /search?q=red&page=2 HTTP/1.1\r\n"
    )


@pytest.mark.depends_on("test_url_missing_path_produces_slash_target")
def test_empty_url_path_serializes_as_slash():
    """Seam: protocol handoff — bare URL path defaults to slash on the wire."""
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request("GET", "http://bare.test")
    assert written_bytes(backend.streams[0]).startswith(b"GET / HTTP/1.1\r\n")


@pytest.mark.depends_on("test_request_target_extension_overrides_url_target")
def test_target_extension_overrides_url_target_on_wire():
    """Seam: protocol handoff — target extension overrides parsed URL target on wire."""
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request(
        "GET",
        "http://node.test/original",
        extensions={"target": b"/override?x=1"},
    )
    assert written_bytes(backend.streams[0]).startswith(
        b"GET /override?x=1 HTTP/1.1\r\n"
    )


@pytest.mark.depends_on("test_request_target_extension_overrides_url_target")
def test_options_star_target_is_sent_unchanged():
    """Seam: protocol handoff — OPTIONS * target sent unchanged through pool."""
    pool, backend = pool_with(http11_response(body=b"ok"))
    url = httpcore.URL(scheme=b"http", host=b"node.test", target=b"*")
    pool.request("OPTIONS", url)
    assert written_bytes(backend.streams[0]).startswith(b"OPTIONS * HTTP/1.1\r\n")


# =============================================================================
# Host header generation (URL → header serialization)
# Seam: protocol handoff — URL port logic → Host header value
# =============================================================================


@pytest.mark.depends_on("test_url_default_http_port_is_80")
def test_default_http_port_omitted_from_host_header():
    """Seam: protocol handoff — default HTTP port omitted from Host header."""
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request("GET", "http://node.test:80/")
    assert_header(backend.streams[0], b"Host", b"node.test")


def test_non_default_port_included_in_host_header():
    """Seam: protocol handoff — non-default port included in Host header value."""
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request("GET", "http://node.test:9090/")
    assert_header(backend.streams[0], b"Host", b"node.test:9090")


def test_caller_supplied_host_header_is_preserved():
    """Seam: protocol handoff — caller-supplied Host header preserved over auto-generated value."""
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request("GET", "http://node.test/", headers={"Host": "override.test"})
    block = header_block(backend.streams[0])
    assert b"Host: override.test" in block.split(b"\r\n")
    assert b"Host: node.test" not in block.split(b"\r\n")


# =============================================================================
# Body framing (content → Content-Length / chunked serialization)
# Seam: protocol handoff — body type → framing header + wire body
# =============================================================================


def test_bytes_content_adds_content_length_and_serializes_body():
    """Seam: protocol handoff — bytes body adds Content-Length and serializes payload."""
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request("POST", "http://node.test/upload", content=b"payload")
    wire = written_bytes(backend.streams[0])
    assert b"\r\nContent-Length: 7\r\n" in wire
    assert wire.endswith(b"\r\n\r\npayload")


def test_empty_bytes_body_adds_zero_content_length():
    """Seam: protocol handoff — empty bytes body framed with Content-Length: 0."""
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request("PUT", "http://node.test/empty", content=b"")
    assert_header(backend.streams[0], b"Content-Length", b"0")


def test_iterable_body_uses_chunked_transfer_encoding():
    """Seam: protocol handoff — iterable body uses chunked transfer encoding on wire."""
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request("POST", "http://node.test/stream", content=iter([b"ab", b"cde"]))
    wire = written_bytes(backend.streams[0])
    assert b"\r\nTransfer-Encoding: chunked\r\n" in wire
    assert b"2\r\nab\r\n3\r\ncde\r\n0\r\n\r\n" in wire


def test_explicit_content_length_header_is_preserved():
    """Seam: protocol handoff — explicit Content-Length header preserved without duplication."""
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request(
        "POST", "http://node.test/", headers={"Content-Length": "4"}, content=b"data"
    )
    lines = header_block(backend.streams[0]).split(b"\r\n")
    assert lines.count(b"Content-Length: 4") == 1


def test_explicit_transfer_encoding_prevents_auto_content_length():
    """Seam: protocol handoff — explicit Transfer-Encoding prevents auto Content-Length."""
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request(
        "POST",
        "http://node.test/",
        headers={"Transfer-Encoding": "chunked"},
        content=b"abc",
    )
    block = header_block(backend.streams[0])
    assert b"Transfer-Encoding: chunked" in block.split(b"\r\n")
    assert all(not line.startswith(b"Content-Length:") for line in block.split(b"\r\n"))


# =============================================================================
# Response parsing (wire bytes → Response model)
# Seam: protocol handoff — network bytes → Response status/headers/body/extensions
# =============================================================================


def test_pool_request_returns_status_headers_content_and_extensions():
    """Seam: protocol handoff — wire bytes parsed into Response status, headers, content, and extensions."""
    pool, backend = pool_with(
        http11_response(201, b"Created", [(b"X-Id", b"99")], b"done")
    )
    response = pool.request("GET", "http://node.test/resource")
    assert response.status == 201
    assert (b"X-Id", b"99") in response.headers
    assert response.content == b"done"
    assert response.extensions["http_version"] == b"HTTP/1.1"
    assert response.extensions["reason_phrase"] == b"Created"


def test_duplicate_response_headers_are_preserved():
    """Seam: state consistency — duplicate response headers preserved across parse boundary."""
    pool, _ = pool_with(
        http11_response(200, headers=[(b"Set-Cookie", b"a=1"), (b"Set-Cookie", b"b=2")], body=b"ok")
    )
    response = pool.request("GET", "http://node.test/")
    cookies = [v for n, v in response.headers if n == b"Set-Cookie"]
    assert cookies == [b"a=1", b"b=2"]


# =============================================================================
# Streaming lifecycle (pool → stream → iter/read → close)
# Seam: lifecycle crossing — stream state transitions
# =============================================================================


def test_stream_response_does_not_preload_body():
    """Seam: lifecycle crossing — stream mode defers body read until iter_stream."""
    pool, _ = pool_with(
        http11_response(headers=[(b"Content-Length", b"5")], body=b"hello")
    )
    with pool.stream("GET", "http://node.test/") as response:
        with pytest.raises(RuntimeError):
            _ = response.content
        assert list(response.iter_stream()) == [b"hello"]


def test_stream_read_makes_content_available():
    """Seam: lifecycle crossing — stream read populates content for later access."""
    pool, _ = pool_with(
        http11_response(headers=[(b"Content-Length", b"6")], body=b"abc") + [b"def"]
    )
    with pool.stream("GET", "http://node.test/") as response:
        assert response.read() == b"abcdef"
        assert response.content == b"abcdef"


# =============================================================================
# Connection reuse (pool state → connection lifecycle)
# Seam: state consistency — pool tracks idle/active connections
# =============================================================================


def test_same_origin_reuses_connection_after_body_consumed():
    """Seam: state consistency — pool reuses connection after body consumed for same origin."""
    backend = RecordingBackend(
        [http11_response(body=b"first") + http11_response(body=b"second")]
    )
    pool = httpcore.ConnectionPool(network_backend=backend)
    assert pool.request("GET", "http://node.test/one").content == b"first"
    assert pool.request("GET", "http://node.test/two").content == b"second"
    assert len(backend.tcp_calls) == 1


def test_different_origins_open_separate_connections():
    """Seam: state consistency — different origins open separate TCP connections."""
    backend = RecordingBackend(
        [http11_response(body=b"a"), http11_response(body=b"b")]
    )
    pool = httpcore.ConnectionPool(network_backend=backend)
    pool.request("GET", "http://alpha.test/")
    pool.request("GET", "http://beta.test/")
    assert [c["host"] for c in backend.tcp_calls] == ["alpha.test", "beta.test"]


def test_zero_keepalive_closes_connection_after_response():
    """Seam: lifecycle crossing — zero keepalive closes connection after response."""
    pool, backend = pool_with(http11_response(body=b"ok"), max_keepalive_connections=0)
    pool.request("GET", "http://node.test/")
    assert backend.streams[0].close_calls == 1


def test_pool_close_closes_idle_connections():
    """Seam: lifecycle crossing — pool.close closes idle underlying streams."""
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request("GET", "http://node.test/")
    pool.close()
    assert backend.streams[0].close_calls == 1


def test_pool_context_manager_closes_on_exit():
    """Seam: lifecycle crossing — pool context manager closes connections on exit."""
    backend = RecordingBackend([http11_response(body=b"ok")])
    with httpcore.ConnectionPool(network_backend=backend) as pool:
        pool.request("GET", "http://node.test/")
    assert backend.streams[0].close_calls == 1


def test_pool_connections_returns_list_snapshot():
    """Seam: state consistency — pool.connections returns independent list snapshot."""
    pool, _ = pool_with(http11_response(body=b"ok"))
    assert pool.connections == []
    pool.request("GET", "http://node.test/")
    snapshot = pool.connections
    snapshot.clear()
    assert len(pool.connections) == 1


# =============================================================================
# Direct HTTPConnection (single-origin connection lifecycle)
# Seam: state consistency — connection state reflects body consumption
# =============================================================================


def test_http_connection_returns_response_for_configured_origin():
    """Seam: protocol handoff — HTTPConnection serves configured origin requests."""
    backend = RecordingBackend([http11_response(202, b"Accepted", body=b"queued")])
    origin = httpcore.Origin(b"http", b"node.test", 80)
    conn = httpcore.HTTPConnection(origin, network_backend=backend)
    req = httpcore.Request("GET", "http://node.test/job")
    response = conn.handle_request(req)
    assert response.read() == b"queued"
    assert response.status == 202


def test_http_connection_rejects_different_origin():
    """Seam: error propagation — HTTPConnection rejects requests to different origin."""
    backend = RecordingBackend([http11_response(body=b"unused")])
    origin = httpcore.Origin(b"http", b"node.test", 80)
    conn = httpcore.HTTPConnection(origin, network_backend=backend)
    with pytest.raises(RuntimeError):
        conn.handle_request(httpcore.Request("GET", "http://other.test/"))
    assert backend.tcp_calls == []


def test_http_connection_becomes_idle_after_response_consumed():
    """Seam: lifecycle crossing — HTTPConnection idle after response consumed enables reuse."""
    backend = RecordingBackend(
        [http11_response(body=b"one") + http11_response(body=b"two")]
    )
    origin = httpcore.Origin(b"http", b"node.test", 80)
    conn = httpcore.HTTPConnection(origin, network_backend=backend)
    first = conn.handle_request(httpcore.Request("GET", "http://node.test/1"))
    first.read()
    first.close()
    assert conn.is_idle() is True
    second = conn.handle_request(httpcore.Request("GET", "http://node.test/2"))
    assert second.read() == b"two"
    assert len(backend.tcp_calls) == 1


def test_http_connection_close_closes_underlying_stream():
    """Seam: lifecycle crossing — HTTPConnection.close closes underlying network stream."""
    backend = RecordingBackend([http11_response(body=b"ok")])
    origin = httpcore.Origin(b"http", b"node.test", 80)
    conn = httpcore.HTTPConnection(origin, network_backend=backend)
    conn.handle_request(httpcore.Request("GET", "http://node.test/")).read()
    conn.close()
    assert conn.is_closed() is True
    assert backend.streams[0].close_calls == 1


# =============================================================================
# TLS (pool → backend → stream TLS upgrade)
# Seam: configuration interaction — SSL context + hostname flow
# =============================================================================


def test_https_connects_to_port_443_and_starts_tls():
    """Seam: protocol handoff — HTTPS connects on 443 and upgrades stream with TLS."""
    pool, backend = pool_with(http11_response(body=b"secure"))
    response = pool.request("GET", "https://tls.test/")
    assert response.content == b"secure"
    assert backend.tcp_calls[0]["port"] == 443
    assert backend.streams[0].tls_calls[0][0] == "tls.test"


def test_sni_hostname_extension_overrides_tls_server_name():
    """Seam: config interaction — sni_hostname extension overrides TLS server name."""
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request("GET", "https://main.test/", extensions={"sni_hostname": "alt.test"})
    assert backend.streams[0].tls_calls[0][0] == "alt.test"


def test_https_non_default_port_for_connect_and_host():
    """Seam: config interaction — HTTPS non-default port used for connect and Host header."""
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request("GET", "https://secure.test:8443/")
    assert backend.tcp_calls[0]["port"] == 8443
    assert_header(backend.streams[0], b"Host", b"secure.test:8443")


# =============================================================================
# UDS, timeouts, and configuration forwarding
# Seam: configuration interaction — pool config → backend call arguments
# =============================================================================


def test_uds_path_uses_connect_unix_socket():
    """Seam: config interaction — UDS path routes pool connect through unix socket backend."""
    pool, backend = pool_with(http11_response(body=b"ok"), uds="/var/run/app.sock")
    pool.request("GET", "http://node.test/")
    assert backend.tcp_calls == []
    assert backend.uds_calls[0]["path"] == "/var/run/app.sock"


def test_local_address_forwarded_to_backend():
    """Seam: config interaction — local_address pool config forwarded to backend TCP connect."""
    pool, backend = pool_with(http11_response(body=b"ok"), local_address="10.0.0.1")
    pool.request("GET", "http://node.test/")
    assert backend.tcp_calls[0]["local_address"] == "10.0.0.1"


def test_socket_options_forwarded_to_backend():
    """Seam: config interaction — socket_options forwarded from pool to backend connect."""
    opts = [(6, 1, 1)]
    pool, backend = pool_with(http11_response(body=b"ok"), socket_options=opts)
    pool.request("GET", "http://node.test/")
    assert backend.tcp_calls[0]["socket_options"] == opts


def test_connect_timeout_forwarded_to_backend():
    """Seam: config interaction — connect timeout extension forwarded to backend."""
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request("GET", "http://node.test/", extensions={"timeout": {"connect": 1.5}})
    assert backend.tcp_calls[0]["timeout"] == 1.5


def test_read_timeout_forwarded_to_stream():
    """Seam: config interaction — read timeout extension forwarded to network stream."""
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request("GET", "http://node.test/", extensions={"timeout": {"read": 2.5}})
    assert any(call[1] == 2.5 for call in backend.streams[0].read_calls)


def test_write_timeout_forwarded_to_stream():
    """Seam: config interaction — write timeout extension forwarded to network stream."""
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request("POST", "http://node.test/", content=b"x", extensions={"timeout": {"write": 3.5}})
    assert backend.streams[0].write_timeout == 3.5


# =============================================================================
# Retry behavior (pool → backend error → retry → success)
# Seam: error propagation + state consistency — retry logic across connect attempts
# =============================================================================


def test_connect_error_retried_once_succeeds():
    """Seam: error propagation — connect error retried once then succeeds through pool."""
    backend = RecordingBackend(
        [httpcore.ConnectError("fail"), http11_response(body=b"ok")]
    )
    pool = httpcore.ConnectionPool(network_backend=backend, retries=1)
    assert pool.request("GET", "http://node.test/").content == b"ok"
    assert len(backend.tcp_calls) == 2
    assert backend.sleep_calls == [0]


def test_connect_error_exhausts_retries_and_raises():
    """Seam: error propagation — exhausted connect retries propagate ConnectError."""
    backend = RecordingBackend([httpcore.ConnectError("boom")])
    pool = httpcore.ConnectionPool(network_backend=backend, retries=0)
    with pytest.raises(httpcore.ConnectError):
        pool.request("GET", "http://node.test/")


def test_retry_backoff_uses_exponential_sequence():
    """Seam: error propagation — retry backoff uses exponential sleep sequence."""
    backend = RecordingBackend(
        [
            httpcore.ConnectError("1"),
            httpcore.ConnectError("2"),
            http11_response(body=b"ok"),
        ]
    )
    pool = httpcore.ConnectionPool(network_backend=backend, retries=2)
    assert pool.request("GET", "http://node.test/").content == b"ok"
    assert backend.sleep_calls == [0, 0.5]


# =============================================================================
# Trace callbacks (pool → trace extension → event reporting)
# Seam: configuration interaction — trace callback receives lifecycle events
# =============================================================================


def test_trace_reports_tcp_connect_started_and_complete():
    """Seam: config interaction — trace callback receives TCP connect lifecycle events."""
    events = []
    pool, _ = pool_with(http11_response(body=b"ok"))
    pool.request("GET", "http://node.test/", extensions={"trace": lambda n, i: events.append(n)})
    assert "connection.connect_tcp.started" in events
    assert "connection.connect_tcp.complete" in events


def test_trace_reports_tcp_connect_failed_on_error():
    """Seam: error propagation — trace callback reports TCP connect failure on error."""
    events = []
    backend = RecordingBackend([httpcore.ConnectError("boom")])
    pool = httpcore.ConnectionPool(network_backend=backend)
    with pytest.raises(httpcore.ConnectError):
        pool.request("GET", "http://node.test/", extensions={"trace": lambda n, i: events.append(n)})
    assert "connection.connect_tcp.failed" in events


def test_trace_reports_tls_events_for_https():
    """Seam: protocol handoff — trace callback reports TLS start/complete for HTTPS."""
    events = []
    pool, _ = pool_with(http11_response(body=b"ok"))
    pool.request("GET", "https://tls.test/", extensions={"trace": lambda n, i: events.append(n)})
    assert "connection.start_tls.started" in events
    assert "connection.start_tls.complete" in events


# =============================================================================
# Error conditions (wire → error propagation)
# Seam: error propagation — malformed responses → documented exceptions
# =============================================================================


def test_premature_disconnect_raises_remote_protocol_error():
    """Seam: error propagation — premature disconnect raises RemoteProtocolError."""
    pool, _ = pool_with([])
    with pytest.raises(httpcore.RemoteProtocolError):
        pool.request("GET", "http://node.test/")


def test_invalid_method_bytes_raise_local_protocol_error():
    """Seam: error propagation — invalid method bytes raise LocalProtocolError."""
    pool, _ = pool_with(http11_response())
    with pytest.raises(httpcore.LocalProtocolError):
        pool.request(b"GET\n", "http://node.test/")


# =============================================================================
# CONNECT response network_stream extension
# Seam: protocol handoff — CONNECT response exposes raw stream
# =============================================================================


def test_connect_response_exposes_network_stream():
    """Seam: protocol handoff — CONNECT response exposes raw network_stream extension."""
    pool, _ = pool_with(http11_response(200, headers=[(b"Content-Length", b"0")], body=b""))
    with pool.stream("CONNECT", "http://tunnel.test:80/") as response:
        assert response.status == 200
        ns = response.extensions["network_stream"]
        assert hasattr(ns, "read")
        assert hasattr(ns, "write")
        assert hasattr(ns, "close")


# =============================================================================
# MockBackend integration with pool
# Seam: state consistency — MockBackend byte chunks → pool response
# =============================================================================


def test_mock_backend_serves_response_through_pool():
    """Seam: state consistency — MockBackend response served consistently through pool."""
    backend = httpcore.MockBackend(
        http11_response(200, headers=[(b"X-Mock", b"yes")], body=b"mocked")
    )
    with httpcore.ConnectionPool(network_backend=backend) as pool:
        response = pool.request("GET", "https://mock.test/")
    assert response.status == 200
    assert (b"X-Mock", b"yes") in response.headers
    assert response.content == b"mocked"

def test_unsupported_protocol_is_raised_for_ftp_scheme():
    """Seam: error propagation — unsupported URL scheme raises through pool.request."""
    from conftest import pool_with, http11_response

    pool, _ = pool_with(http11_response(body=b"unused"))
    with pytest.raises(httpcore.UnsupportedProtocol):
        pool.request("GET", "ftp://example.com/")

def test_unsupported_protocol_is_raised_for_missing_scheme():
    """Seam: error propagation — missing URL scheme raises through pool.request."""
    from conftest import pool_with, http11_response

    pool, _ = pool_with(http11_response(body=b"unused"))
    with pytest.raises(httpcore.UnsupportedProtocol):
        pool.request("GET", "example.com/no-scheme")
