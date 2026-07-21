from __future__ import annotations

import asyncio
from collections.abc import Callable

import pytest

from hypercorn.config import Config
from hypercorn.middleware import (
    AsyncioWSGIMiddleware,
    DispatcherMiddleware,
    HTTPToHTTPSRedirectMiddleware,
    ProxyFixMiddleware,
    TrioWSGIMiddleware,
)


def make_http_scope(**overrides: object) -> dict:
    scope = {
        "type": "http",
        "asgi": {},
        "http_version": "2",
        "method": "GET",
        "scheme": "https",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "root_path": "",
        "headers": [],
        "client": ("127.0.0.1", 80),
        "server": None,
        "extensions": {},
        "state": {},
    }
    scope.update(overrides)
    return scope


def make_websocket_scope(**overrides: object) -> dict:
    scope = {
        "type": "websocket",
        "asgi": {},
        "http_version": "1.1",
        "scheme": "ws",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "root_path": "",
        "headers": [],
        "client": None,
        "server": None,
        "subprotocols": [],
        "extensions": {},
        "state": {},
    }
    scope.update(overrides)
    return scope


async def empty_app(scope: dict, receive: Callable | None, send: Callable | None) -> None:
    return None


async def collect_app(scope: dict, receive: Callable | None, send: Callable | None) -> None:
    assert send is not None
    body = f"{scope['root_path']}|{scope['path']}".encode()
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": body})


def test_config_from_pyfile_loads_public_attributes(tmp_path) -> None:
    config_file = tmp_path / "hypercorn_config.py"
    config_file.write_text(
        'access_log_format = "bob"\n'
        'bind = "127.0.0.1:5555"\n'
        "h11_max_incomplete_size = 4\n",
        encoding="utf-8",
    )

    config = Config.from_pyfile(str(config_file))

    assert config.access_log_format == "bob"
    assert config.h11_max_incomplete_size == 4
    assert config.bind == ["127.0.0.1:5555"]


def test_config_from_toml_loads_public_attributes(tmp_path) -> None:
    config_file = tmp_path / "hypercorn.toml"
    config_file.write_text(
        'access_log_format = "bob"\n'
        'bind = "127.0.0.1:5555"\n'
        "h11_max_incomplete_size = 4\n",
        encoding="utf-8",
    )

    config = Config.from_toml(str(config_file))

    assert config.access_log_format == "bob"
    assert config.h11_max_incomplete_size == 4
    assert config.bind == ["127.0.0.1:5555"]


def test_config_from_object_loads_public_attributes(tmp_path, monkeypatch) -> None:
    module_file = tmp_path / "sample_hypercorn_config.py"
    module_file.write_text(
        'access_log_format = "bob"\n'
        'bind = "127.0.0.1:5555"\n'
        "h11_max_incomplete_size = 4\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    config = Config.from_object("sample_hypercorn_config")

    assert config.access_log_format == "bob"
    assert config.h11_max_incomplete_size == 4
    assert config.bind == ["127.0.0.1:5555"]


def test_config_response_headers_follow_metadata_flags() -> None:
    config = Config()
    config.include_date_header = False
    assert config.response_headers("test") == [(b"server", b"hypercorn-test")]

    config.include_server_header = False
    assert config.response_headers("test") == []


@pytest.mark.asyncio
@pytest.mark.parametrize("raw_path", [b"/abc", b"/abc%3C"])
async def test_http_to_https_redirect_preserves_http_raw_path_and_query(raw_path: bytes) -> None:
    app = HTTPToHTTPSRedirectMiddleware(empty_app, "localhost")
    sent_events = []

    async def send(message: dict) -> None:
        sent_events.append(message)

    await app(
        make_http_scope(
            scheme="http",
            path=raw_path.decode(),
            raw_path=raw_path,
            query_string=b"a=b",
        ),
        None,
        send,
    )

    assert sent_events[0] == {
        "type": "http.response.start",
        "status": 307,
        "headers": [(b"location", b"https://localhost%s?a=b" % raw_path)],
    }
    assert sent_events[1]["type"] == "http.response.body"
    assert sent_events[1].get("body", b"") == b""


@pytest.mark.asyncio
@pytest.mark.parametrize("raw_path", [b"/abc", b"/abc%3C"])
async def test_http_to_https_redirect_preserves_websocket_raw_path_and_query(
    raw_path: bytes,
) -> None:
    app = HTTPToHTTPSRedirectMiddleware(empty_app, "localhost")
    sent_events = []

    async def send(message: dict) -> None:
        sent_events.append(message)

    await app(
        make_websocket_scope(
            http_version="1.1",
            raw_path=raw_path,
            path=raw_path.decode(),
            query_string=b"a=b",
            extensions={"websocket.http.response": {}},
        ),
        None,
        send,
    )

    assert sent_events[0] == {
        "type": "websocket.http.response.start",
        "status": 307,
        "headers": [(b"location", b"wss://localhost%s?a=b" % raw_path)],
    }
    assert sent_events[1]["type"] == "websocket.http.response.body"
    assert sent_events[1].get("body", b"") == b""


@pytest.mark.asyncio
async def test_http_to_https_redirect_uses_https_scheme_for_http2_websocket() -> None:
    app = HTTPToHTTPSRedirectMiddleware(empty_app, "localhost")
    sent_events = []

    async def send(message: dict) -> None:
        sent_events.append(message)

    await app(
        make_websocket_scope(
            http_version="2",
            raw_path=b"/abc",
            path="/abc",
            query_string=b"a=b",
            extensions={"websocket.http.response": {}},
        ),
        None,
        send,
    )

    assert sent_events[0] == {
        "type": "websocket.http.response.start",
        "status": 307,
        "headers": [(b"location", b"https://localhost/abc?a=b")],
    }
    assert sent_events[1]["type"] == "websocket.http.response.body"
    assert sent_events[1].get("body", b"") == b""


@pytest.mark.asyncio
async def test_http_to_https_redirect_closes_websocket_without_denial_extension() -> None:
    app = HTTPToHTTPSRedirectMiddleware(empty_app, "localhost")
    sent_events = []

    async def send(message: dict) -> None:
        sent_events.append(message)

    await app(make_websocket_scope(path="/abc", raw_path=b"/abc"), None, send)

    assert sent_events == [{"type": "websocket.close"}]


@pytest.mark.asyncio
async def test_http_to_https_redirect_uses_request_host_when_constructor_host_is_none() -> None:
    app = HTTPToHTTPSRedirectMiddleware(empty_app, None)
    sent_events = []

    async def send(message: dict) -> None:
        sent_events.append(message)

    await app(
        make_http_scope(scheme="http", headers=[(b"host", b"example.com")]),
        None,
        send,
    )

    assert sent_events[0]["headers"] == [(b"location", b"https://example.com/")]


@pytest.mark.asyncio
async def test_proxy_fix_legacy_restores_trusted_client_scheme_and_host() -> None:
    seen_scopes = []

    async def app(scope: dict, receive: Callable | None, send: Callable | None) -> None:
        seen_scopes.append(scope)

    middleware = ProxyFixMiddleware(app)
    original_scope = make_http_scope(
        scheme="http",
        headers=[
            (b"x-forwarded-for", b"127.0.0.1"),
            (b"x-forwarded-for", b"127.0.0.2"),
            (b"x-forwarded-proto", b"http,https"),
            (b"x-forwarded-host", b"example.com"),
        ],
        client=("127.0.0.3", 80),
    )

    await middleware(original_scope, None, None)
    scope = seen_scopes[0]

    assert scope["client"] == ("127.0.0.2", 0)
    assert scope["scheme"] == "https"
    assert [h for h in scope["headers"] if h[0].lower() == b"host"] == [
        (b"host", b"example.com")
    ]
    assert original_scope["client"] == ("127.0.0.3", 80)
    assert original_scope["scheme"] == "http"


@pytest.mark.asyncio
async def test_proxy_fix_modern_restores_trusted_client_scheme_and_host() -> None:
    seen_scopes = []

    async def app(scope: dict, receive: Callable | None, send: Callable | None) -> None:
        seen_scopes.append(scope)

    middleware = ProxyFixMiddleware(app, mode="modern")

    await middleware(
        make_http_scope(
            scheme="http",
            headers=[
                (
                    b"forwarded",
                    b"for=127.0.0.1;proto=http,for=127.0.0.2;proto=https;host=example.com",
                )
            ],
            client=("127.0.0.3", 80),
        ),
        None,
        None,
    )

    scope = seen_scopes[0]
    assert scope["client"] == ("127.0.0.2", 0)
    assert scope["scheme"] == "https"
    assert [h for h in scope["headers"] if h[0].lower() == b"host"] == [
        (b"host", b"example.com")
    ]


@pytest.mark.asyncio
async def test_dispatcher_routes_by_insertion_order_and_updates_root_path() -> None:
    app = DispatcherMiddleware({"/api/x": collect_app, "/api": collect_app})
    sent_events = []

    async def send(message: dict) -> None:
        sent_events.append(message)

    await app(make_http_scope(path="/api/x/b"), None, send)
    await app(make_http_scope(path="/api/b"), None, send)

    bodies = [message["body"] for message in sent_events if message["type"] == "http.response.body"]
    assert bodies == [b"/api/x|/api/x/b", b"/api|/api/b"]


@pytest.mark.asyncio
async def test_dispatcher_returns_404_when_no_mount_matches() -> None:
    app = DispatcherMiddleware({"/api": collect_app})
    sent_events = []

    async def send(message: dict) -> None:
        sent_events.append(message)

    await app(make_http_scope(path="/other"), None, send)

    assert sent_events[0]["type"] == "http.response.start"
    assert sent_events[0]["status"] == 404
    assert sent_events[1]["type"] == "http.response.body"
    assert sent_events[1].get("body", b"") == b""


@pytest.mark.asyncio
async def test_dispatcher_broadcasts_lifespan_to_mounted_applications() -> None:
    calls = []

    async def mounted(scope: dict, receive: Callable, send: Callable) -> None:
        calls.append(scope["type"])
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return

    app = DispatcherMiddleware({"/one": mounted, "/two": mounted})
    sent_events = []

    async def send(message: dict) -> None:
        sent_events.append(message)

    received = iter([{"type": "lifespan.startup"}, {"type": "lifespan.shutdown"}])

    async def receive() -> dict:
        return next(received)

    await app({"type": "lifespan", "asgi": {"version": "3.0"}, "state": {}}, receive, send)

    assert calls == ["lifespan", "lifespan"]
    assert sent_events == [
        {"type": "lifespan.startup.complete"},
        {"type": "lifespan.shutdown.complete"},
    ]


def echo_wsgi_body(environ: dict, start_response: Callable) -> list[bytes]:
    body = environ["wsgi.input"].read()
    start_response(
        "200 OK",
        [("Content-Type", "text/plain; charset=utf-8"), ("Content-Length", str(len(body)))],
    )
    return [body]


async def run_asyncio_wsgi(app: AsyncioWSGIMiddleware, scope: dict, body: bytes = b"") -> list[dict]:
    queue: asyncio.Queue = asyncio.Queue()
    await queue.put({"type": "http.request", "body": body, "more_body": False})
    messages = []

    async def send(message: dict) -> None:
        messages.append(message)

    await app(scope, queue.get, send)
    return messages


@pytest.mark.asyncio
async def test_asyncio_wsgi_middleware_emits_wsgi_response_body() -> None:
    app = AsyncioWSGIMiddleware(echo_wsgi_body, 2**16)

    messages = await run_asyncio_wsgi(app, make_http_scope(http_version="1.1"), b"hello")

    assert messages[0]["type"] == "http.response.start"
    assert messages[0]["status"] == 200
    assert b"hello" == b"".join(message.get("body", b"") for message in messages[1:])


@pytest.mark.asyncio
async def test_asyncio_wsgi_middleware_returns_400_when_body_exceeds_limit() -> None:
    called = False

    def app(environ: dict, start_response: Callable) -> list[bytes]:
        nonlocal called
        called = True
        start_response("200 OK", [])
        return [b""]

    messages = await run_asyncio_wsgi(
        AsyncioWSGIMiddleware(app, 4),
        make_http_scope(http_version="1.1"),
        b"abcde",
    )

    assert messages[0]["type"] == "http.response.start"
    assert messages[0]["status"] == 400
    assert messages[0]["headers"] == []
    assert messages[1]["type"] == "http.response.body"
    assert messages[1].get("body", b"") == b""
    assert messages[1].get("more_body", False) is False
    assert called is False


@pytest.mark.asyncio
async def test_asyncio_wsgi_middleware_requires_start_response_before_body() -> None:
    def app(environ: dict, start_response: Callable) -> list[bytes]:
        return [b"result"]

    with pytest.raises(RuntimeError):
        await run_asyncio_wsgi(
            AsyncioWSGIMiddleware(app, 2**16),
            make_http_scope(http_version="1.1"),
        )


@pytest.mark.trio
async def test_trio_wsgi_middleware_emits_wsgi_response_body() -> None:
    app = TrioWSGIMiddleware(echo_wsgi_body, 2**16)
    events = [{"type": "http.request", "body": b"hello", "more_body": False}]
    messages = []

    async def receive() -> dict:
        return events.pop(0)

    async def send(message: dict) -> None:
        messages.append(message)

    await app(make_http_scope(http_version="1.1"), receive, send)

    assert messages[0]["type"] == "http.response.start"
    assert messages[0]["status"] == 200
    assert b"hello" == b"".join(message.get("body", b"") for message in messages[1:])
