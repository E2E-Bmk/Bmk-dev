"""Atomic tests for httpcore-transport-fullrepro-001.

Each test exercises ONE public API entry point with ONE behavior assertion.
If only the tested API were correctly implemented (all others stubbed),
the test should pass.
"""
from __future__ import annotations

import ssl

import pytest

import httpcore


# =============================================================================
# URL parsing and components
# =============================================================================


def test_url_from_string_parses_scheme_host_target():
    url = httpcore.URL("http://example.com/items?q=1")
    assert url.scheme == b"http"
    assert url.host == b"example.com"
    assert url.target == b"/items?q=1"


def test_url_default_http_port_is_80():
    url = httpcore.URL("http://example.com/path")
    assert url.port is None
    assert url.origin == httpcore.Origin(b"http", b"example.com", 80)


def test_url_default_https_port_is_443():
    url = httpcore.URL("https://secure.test/api")
    assert url.origin == httpcore.Origin(b"https", b"secure.test", 443)


def test_url_explicit_components_round_trips_to_bytes():
    url = httpcore.URL(scheme=b"http", host=b"node.test", port=9090, target=b"/health")
    assert bytes(url) == b"http://node.test:9090/health"


def test_url_missing_path_produces_slash_target():
    url = httpcore.URL("http://bare.test")
    assert url.target == b"/"


def test_url_rejects_non_ascii_string():
    with pytest.raises(TypeError):
        httpcore.URL("http://example.com/caf\u00e9")


# =============================================================================
# Origin identity
# =============================================================================


def test_origin_equality_requires_all_three_fields():
    a = httpcore.Origin(b"http", b"example.com", 80)
    b = httpcore.Origin(b"http", b"example.com", 80)
    c = httpcore.Origin(b"https", b"example.com", 443)
    assert a == b
    assert a != c


def test_origin_stores_byte_scheme_and_host_with_int_port():
    o = httpcore.Origin(b"http", b"api.test", 8080)
    assert o.scheme == b"http"
    assert o.host == b"api.test"
    assert o.port == 8080


# =============================================================================
# Request model
# =============================================================================


def test_request_stores_method_as_bytes():
    req = httpcore.Request("POST", "http://example.com/")
    assert req.method == b"POST"


def test_request_url_is_parsed_url_object():
    req = httpcore.Request("GET", "http://example.com/page?k=v")
    assert isinstance(req.url, httpcore.URL)
    assert req.url.target == b"/page?k=v"


def test_request_headers_normalized_to_byte_pairs():
    req = httpcore.Request("GET", "http://example.com/", headers={"X-Id": "42"})
    assert req.headers == [(b"X-Id", b"42")]


def test_request_target_extension_overrides_url_target():
    req = httpcore.Request(
        "GET", "http://example.com/original", extensions={"target": b"/replaced"}
    )
    assert bytes(req.url) == b"http://example.com/replaced"


def test_request_rejects_non_ascii_method():
    with pytest.raises(TypeError):
        httpcore.Request("G\u00c9T", "http://example.com/")


def test_request_rejects_non_ascii_header_values():
    with pytest.raises(TypeError):
        httpcore.Request("GET", "http://example.com/", headers={"X-Val": "caf\u00e9"})


# =============================================================================
# Response model
# =============================================================================


def test_response_stores_status_and_headers():
    resp = httpcore.Response(201, headers={"Content-Type": "application/json"})
    assert resp.status == 201
    assert resp.headers == [(b"Content-Type", b"application/json")]


def test_response_read_caches_content_for_repeated_access():
    resp = httpcore.Response(200, content=iter([b"alpha", b"beta"]))
    assert resp.read() == b"alphabeta"
    assert resp.read() == b"alphabeta"
    assert resp.content == b"alphabeta"


def test_response_iter_stream_yields_chunks_once():
    resp = httpcore.Response(200, content=iter([b"x", b"y"]))
    assert list(resp.iter_stream()) == [b"x", b"y"]
    with pytest.raises(RuntimeError):
        list(resp.iter_stream())


def test_response_content_before_read_on_streaming_raises():
    resp = httpcore.Response(200, content=iter([b"data"]))
    with pytest.raises(RuntimeError):
        _ = resp.content


def test_response_close_calls_body_close_when_available():
    class ClosableBody:
        closed = False
        def __iter__(self):
            yield b"ok"
        def close(self):
            self.closed = True

    body = ClosableBody()
    resp = httpcore.Response(200, content=body)
    resp.close()
    assert body.closed is True


# =============================================================================
# Proxy model
# =============================================================================


def test_proxy_stores_url_as_parsed_url():
    proxy = httpcore.Proxy("http://proxy.test:3128")
    assert proxy.url.origin == httpcore.Origin(b"http", b"proxy.test", 3128)


def test_proxy_auth_generates_basic_authorization_header():
    proxy = httpcore.Proxy("http://gw.test:8080", auth=("admin", "secret"))
    assert proxy.headers[0] == (b"Proxy-Authorization", b"Basic YWRtaW46c2VjcmV0")


def test_proxy_custom_headers_follow_auth_header():
    proxy = httpcore.Proxy(
        "http://gw.test:8080",
        auth=("u", "p"),
        headers={"X-Via": "custom"},
    )
    assert len(proxy.headers) == 2
    assert proxy.headers[0][0] == b"Proxy-Authorization"
    assert proxy.headers[1] == (b"X-Via", b"custom")


def test_proxy_stores_ssl_context_when_provided():
    ctx = ssl.create_default_context()
    proxy = httpcore.Proxy("https://secure-gw.test:443", ssl_context=ctx)
    assert proxy.ssl_context is ctx


# =============================================================================
# MockStream / MockBackend
# =============================================================================


def test_mock_stream_returns_chunks_then_empty():
    stream = httpcore.MockStream([b"one", b"two"])
    assert stream.read(1024) == b"one"
    assert stream.read(1024) == b"two"
    assert stream.read(1024) == b""


def test_mock_stream_start_tls_returns_itself():
    stream = httpcore.MockStream([b""])
    ctx = ssl.create_default_context()
    assert stream.start_tls(ctx, server_hostname="node.test") is stream


# =============================================================================
# Exception hierarchy
# =============================================================================
