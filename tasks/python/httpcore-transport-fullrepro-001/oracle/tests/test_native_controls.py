from __future__ import annotations

import asyncio
import ssl
from pathlib import Path

import pytest

import httpcore

from .native_support import (
    ClosingAsyncBody,
    ClosingSyncBody,
    RecordingAsyncBackend,
    RecordingSyncBackend,
    async_wire,
    flatten,
    h2_response_frames,
    http11_response,
    wire,
)


def test_a01(tmp_path: Path) -> None:
    url = httpcore.URL("https://example.test:443/items?q=1")
    assert (url.scheme, url.host, url.port, url.target) == (b"https", b"example.test", 443, b"/items?q=1")
    assert bytes(url) == b"https://example.test:443/items?q=1"
    assert url.origin == httpcore.Origin(b"https", b"example.test", 443)
    assert httpcore.URL(b"http://example.test").target == b"/"


def test_a02(tmp_path: Path) -> None:
    marker = object()
    request = httpcore.Request(
        "POST",
        "https://example.test:8443/original",
        headers=[("X-Id", "1"), (b"X-Id", b"2")],
        content=iter([b"a", b"bc"]),
        extensions={"target": b"*", "opaque": marker},
    )
    assert request.method == b"POST" and request.headers == [(b"X-Id", b"1"), (b"X-Id", b"2")]
    assert request.url.target == b"*" and request.url.origin == httpcore.Origin(b"https", b"example.test", 8443)
    assert request.extensions["opaque"] is marker and list(request.stream) == [b"a", b"bc"]


def test_a03(tmp_path: Path) -> None:
    body = ClosingSyncBody([b"ab", b"cd"])
    response = httpcore.Response(200, headers=[(b"X", b"1"), (b"X", b"2")], content=body)
    assert response.read() == b"abcd" and response.content == b"abcd"
    body.chunks[:] = [b"changed"]
    assert response.read() == b"abcd" and response.headers == [(b"X", b"1"), (b"X", b"2")]
    response.close(); assert body.close_calls == 1


def test_a04(tmp_path: Path) -> None:
    async def scenario() -> None:
        body = ClosingAsyncBody([b"ab", b"cd"])
        response = httpcore.Response(201, content=body)
        assert await response.aread() == b"abcd" and response.content == b"abcd"
        body.chunks[:] = [b"changed"]
        assert await response.aread() == b"abcd"
        await response.aclose(); assert body.close_calls == 1
    asyncio.run(scenario())


def test_a05(tmp_path: Path) -> None:
    hierarchy = {
        "ConnectError": httpcore.NetworkError,
        "ConnectTimeout": httpcore.TimeoutException,
        "PoolTimeout": httpcore.TimeoutException,
        "ReadTimeout": httpcore.TimeoutException,
        "WriteTimeout": httpcore.TimeoutException,
        "LocalProtocolError": httpcore.ProtocolError,
        "RemoteProtocolError": httpcore.ProtocolError,
    }
    for name, parent in hierarchy.items():
        cls = getattr(httpcore, name)
        assert issubclass(cls, parent) and cls("detail", 17).args == ("detail", 17)


def test_a06(tmp_path: Path) -> None:
    context = ssl.create_default_context()
    proxy = httpcore.Proxy(
        "https://proxy.test:8443",
        auth=("user", "pass"),
        headers=[("X-Proxy", "one"), (b"X-Proxy", b"two")],
        ssl_context=context,
    )
    assert proxy.url == httpcore.URL("https://proxy.test:8443") and proxy.auth == (b"user", b"pass")
    assert proxy.headers == [(b"Proxy-Authorization", b"Basic dXNlcjpwYXNz"), (b"X-Proxy", b"one"), (b"X-Proxy", b"two")]
    assert proxy.ssl_context is context


def test_a07(tmp_path: Path) -> None:
    stream = httpcore.MockStream([b"a", b"bc"])
    assert stream.read(10) == b"a" and stream.read(10) == b"bc" and stream.read(10) == b""
    assert stream.start_tls(ssl.create_default_context()) is stream


def test_a08(tmp_path: Path) -> None:
    async def scenario() -> None:
        stream = httpcore.AsyncMockStream([b"a", b"bc"])
        assert await stream.read(10) == b"a" and await stream.read(10) == b"bc" and await stream.read(10) == b""
        assert await stream.start_tls(ssl.create_default_context()) is stream
    asyncio.run(scenario())


def test_i01(tmp_path: Path) -> None:
    timeout = {"timeout": {"pool": 0}}
    backend = RecordingSyncBackend([flatten(http11_response(b"one"), http11_response(b"two"))])
    with httpcore.ConnectionPool(network_backend=backend, max_connections=1) as pool:
        with pool.stream("GET", "http://same.test/one", extensions=timeout) as held:
            with pytest.raises(httpcore.PoolTimeout):
                pool.request("GET", "http://same.test/two", extensions=timeout)
            assert held.read() == b"one"
        assert pool.request("GET", "http://same.test/two", extensions=timeout).content == b"two"
    assert len(backend.connect_calls) == 1 and b"/one" in wire(backend.streams[0]) and b"/two" in wire(backend.streams[0])


def test_i02(tmp_path: Path) -> None:
    async def scenario() -> None:
        timeout = {"timeout": {"pool": 0}}
        backend = RecordingAsyncBackend([flatten(http11_response(b"one"), http11_response(b"two"))])
        async with httpcore.AsyncConnectionPool(network_backend=backend, max_connections=1) as pool:
            async with pool.stream("GET", "http://same.test/one", extensions=timeout) as held:
                with pytest.raises(httpcore.PoolTimeout):
                    await pool.request("GET", "http://same.test/two", extensions=timeout)
                assert await held.aread() == b"one"
            assert (await pool.request("GET", "http://same.test/two", extensions=timeout)).content == b"two"
        assert len(backend.connect_calls) == 1 and b"/one" in async_wire(backend.streams[0]) and b"/two" in async_wire(backend.streams[0])
    asyncio.run(scenario())


def _proxy() -> httpcore.Proxy:
    return httpcore.Proxy("http://proxy.test:8080", auth=("user", "pass"), headers={"X-Proxy": "yes"})


def test_i03(tmp_path: Path) -> None:
    incomplete = [b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nxx", b""]
    direct_backend = RecordingSyncBackend([flatten(http11_response(b"d1"), http11_response(b"d2"))])
    proxy_backend = RecordingSyncBackend([incomplete, http11_response(b"p2")])
    with httpcore.ConnectionPool(network_backend=direct_backend) as direct, httpcore.ConnectionPool(network_backend=proxy_backend, proxy=_proxy()) as proxied:
        assert direct.request("GET", "http://destination.test/direct-one").content == b"d1"
        direct_connection = direct.connections[0]
        with pytest.raises(httpcore.RemoteProtocolError):
            proxied.request("GET", "http://destination.test/proxy-broken")
        assert direct.request("GET", "http://destination.test/direct-two").content == b"d2"
        assert direct.connections[0] is direct_connection
        assert proxied.request("GET", "http://destination.test/proxy-fixed").content == b"p2"
    assert [(c["host"], c["port"]) for c in proxy_backend.connect_calls] == [("proxy.test", 8080), ("proxy.test", 8080)]
    assert b"Proxy-Authorization:" not in wire(direct_backend.streams[0])
    assert b"GET http://destination.test/proxy-fixed HTTP/1.1" in wire(proxy_backend.streams[1])


def test_i04(tmp_path: Path) -> None:
    frames = h2_response_frames([(1, b"first"), (3, b"second")])
    backend = RecordingSyncBackend([frames], http2=True)
    with httpcore.ConnectionPool(network_backend=backend, http2=True) as pool:
        first = pool.request("GET", "https://h2.test/one")
        connection = pool.connections[0]
        second = pool.request("GET", "https://h2.test/two")
        assert (first.content, second.content) == (b"first", b"second")
        assert first.extensions["http_version"] == b"HTTP/2" and second.extensions["http_version"] == b"HTTP/2"
        assert pool.connections[0] is connection and connection.is_idle()
    assert len(backend.connect_calls) == 1


def test_s01(tmp_path: Path) -> None:
    beta = httpcore.Origin(b"http", b"beta.test", 80)
    incomplete = [b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nxx", b""]
    backend = RecordingSyncBackend([
        flatten(http11_response(b"b1"), http11_response(b"b2")),
        incomplete,
        http11_response(b"fixed"),
    ])
    with httpcore.ConnectionPool(network_backend=backend) as pool:
        assert pool.request("GET", "http://beta.test/one").content == b"b1"
        beta_connection = next(item for item in pool.connections if item.can_handle_request(beta))
        with pytest.raises(httpcore.RemoteProtocolError):
            pool.request("GET", "http://alpha.test/broken")
        assert pool.request("GET", "http://beta.test/two").content == b"b2"
        assert next(item for item in pool.connections if item.can_handle_request(beta)) is beta_connection
        assert pool.request("GET", "http://alpha.test/fixed").content == b"fixed"
    assert len(backend.connect_calls) == 3 and backend.streams[1].close_calls == 1


def test_s02(tmp_path: Path) -> None:
    first_frames = h2_response_frames([(1, b"completed")], goaway_after=1)
    second_frames = h2_response_frames([(1, b"replacement")])
    h2_backend = RecordingSyncBackend([first_frames, second_frames], http2=True)
    direct_backend = RecordingSyncBackend([flatten(http11_response(b"direct-one"), http11_response(b"direct-two"))])
    with httpcore.ConnectionPool(network_backend=direct_backend) as direct, httpcore.ConnectionPool(network_backend=h2_backend, http2=True) as h2_pool:
        assert direct.request("GET", "http://plain.test/one").content == b"direct-one"
        direct_connection = direct.connections[0]
        first = h2_pool.request("GET", "https://h2.test/one")
        second = h2_pool.request("GET", "https://h2.test/two")
        assert first.content == b"completed" and second.content == b"replacement"
        assert direct.request("GET", "http://plain.test/two").content == b"direct-two"
        assert direct.connections[0] is direct_connection
    assert len(h2_backend.connect_calls) == 2 and h2_backend.streams[0].close_calls == 1
    assert len(direct_backend.connect_calls) == 1
