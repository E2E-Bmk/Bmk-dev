from __future__ import annotations

import asyncio
import io
import logging
import subprocess
import sys
from collections.abc import Callable

import pytest

from hypercorn.asyncio import serve as asyncio_serve
from hypercorn.config import Config
from hypercorn.logging import Logger
from hypercorn.middleware import (
    AsyncioWSGIMiddleware,
    DispatcherMiddleware,
    HTTPToHTTPSRedirectMiddleware,
    ProxyFixMiddleware,
)


def make_http_scope(**overrides: object) -> dict:
    scope = {
        "type": "http",
        "asgi": {},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
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


async def run_asyncio_wsgi(app: AsyncioWSGIMiddleware, scope: dict, body: bytes = b"") -> list[dict]:
    queue: asyncio.Queue = asyncio.Queue()
    await queue.put({"type": "http.request", "body": body, "more_body": False})
    messages = []

    async def send(message: dict) -> None:
        messages.append(message)

    await app(scope, queue.get, send)
    return messages


def test_config_documented_defaults_are_visible() -> None:
    config = Config()

    assert config.bind == ["127.0.0.1:8000"]
    assert config.insecure_bind == []
    assert config.quic_bind == []
    assert config.worker_class == "asyncio"
    assert config.workers == 1
    assert config.keep_alive_timeout == 5
    assert config.websocket_max_message_size == 16777216


def test_config_bind_groups_accept_single_string_assignments() -> None:
    config = Config()

    config.bind = "127.0.0.1:9000"
    config.insecure_bind = "0.0.0.0:8080"
    config.quic_bind = "0.0.0.0:4433"

    assert config.bind == ["127.0.0.1:9000"]
    assert config.insecure_bind == ["0.0.0.0:8080"]
    assert config.quic_bind == ["0.0.0.0:4433"]


def test_config_root_path_assignment_removes_trailing_slashes() -> None:
    config = Config()

    config.root_path = "/api/v1///"

    assert config.root_path == "/api/v1"


def test_config_from_mapping_applies_keyword_arguments_last() -> None:
    config = Config.from_mapping(
        {"bind": "127.0.0.1:5000", "workers": 1, "root_path": "/from_mapping/"},
        bind=["127.0.0.1:9000"],
        workers=3,
        root_path="/from_kwargs/",
    )

    assert config.bind == ["127.0.0.1:9000"]
    assert config.workers == 3
    assert config.root_path == "/from_kwargs"


def test_config_from_mapping_accepts_keyword_only_configuration() -> None:
    config = Config.from_mapping(access_log_format="custom", h2_max_concurrent_streams=12)

    assert config.access_log_format == "custom"
    assert config.h2_max_concurrent_streams == 12


def test_config_from_object_resolves_dotted_object(tmp_path, monkeypatch) -> None:
    module_file = tmp_path / "object_config.py"
    module_file.write_text(
        "class Settings:\n"
        "    bind = '127.0.0.1:7777'\n"
        "    workers = 4\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    config = Config.from_object("object_config.Settings")

    assert config.bind == ["127.0.0.1:7777"]
    assert config.workers == 4


def test_config_from_pyfile_propagates_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        Config.from_pyfile("/path/that/does/not/exist.py")


def test_config_from_pyfile_propagates_execution_failure(tmp_path) -> None:
    config_file = tmp_path / "bad_config.py"
    config_file.write_text("raise RuntimeError('configuration failed')\n", encoding="utf-8")

    with pytest.raises(RuntimeError):
        Config.from_pyfile(str(config_file))


def test_config_from_toml_propagates_parse_failure(tmp_path) -> None:
    config_file = tmp_path / "bad.toml"
    config_file.write_text("bind = [unterminated\n", encoding="utf-8")

    with pytest.raises(Exception):
        Config.from_toml(str(config_file))


def test_config_ssl_enabled_reflects_certificate_and_key_presence() -> None:
    config = Config()

    assert config.ssl_enabled is False

    config.certfile = "cert.pem"
    assert config.ssl_enabled is False

    config.keyfile = "key.pem"
    assert config.ssl_enabled is True


def test_config_response_headers_include_each_alt_svc_value() -> None:
    config = Config()
    config.include_date_header = False
    config.include_server_header = False
    config.alt_svc_headers = ['h3=":443"', 'h2=":8443"']

    assert config.response_headers("h2") == [
        (b"alt-svc", b'h3=":443"'),
        (b"alt-svc", b'h2=":8443"'),
    ]


def test_config_statsd_logger_class_requires_statsd_host() -> None:
    class CustomLogger(Logger):
        pass

    config = Config()
    config.set_statsd_logger_class(CustomLogger)

    assert config.logger_class is Logger


def test_config_statsd_logger_class_replaces_default_when_statsd_is_enabled() -> None:
    class CustomLogger(Logger):
        pass

    config = Config()
    config.statsd_host = "localhost:8125"
    config.set_statsd_logger_class(CustomLogger)

    assert config.logger_class is CustomLogger


@pytest.mark.asyncio
async def test_redirect_without_constructor_or_request_host_raises_value_error() -> None:
    middleware = HTTPToHTTPSRedirectMiddleware(lambda scope, receive, send: None, None)

    async def send(message: dict) -> None:
        raise AssertionError("redirect should fail before sending")

    with pytest.raises(ValueError):
        await middleware(make_http_scope(headers=[]), None, send)


@pytest.mark.asyncio
async def test_redirect_location_includes_root_path_before_raw_path() -> None:
    middleware = HTTPToHTTPSRedirectMiddleware(lambda scope, receive, send: None, "example.com")
    sent_events = []

    async def send(message: dict) -> None:
        sent_events.append(message)

    await middleware(
        make_http_scope(root_path="/prefix", raw_path=b"/encoded%2Fpath", query_string=b"x=1"),
        None,
        send,
    )

    assert sent_events[0]["headers"] == [
        (b"location", b"https://example.com/prefix/encoded%2Fpath?x=1")
    ]


@pytest.mark.asyncio
async def test_redirect_passes_secure_websocket_to_wrapped_application() -> None:
    seen_scopes = []

    async def app(scope: dict, receive: Callable | None, send: Callable | None) -> None:
        seen_scopes.append(scope)
        assert send is not None
        await send({"type": "websocket.accept"})

    middleware = HTTPToHTTPSRedirectMiddleware(app, "example.com")
    sent_events = []

    async def send(message: dict) -> None:
        sent_events.append(message)

    scope = make_websocket_scope(scheme="wss")
    await middleware(scope, None, send)

    assert seen_scopes == [scope]
    assert sent_events == [{"type": "websocket.accept"}]


@pytest.mark.asyncio
async def test_redirect_passes_non_http_scope_without_requiring_host() -> None:
    seen_scopes = []

    async def app(scope: dict, receive: Callable | None, send: Callable | None) -> None:
        seen_scopes.append(scope)

    middleware = HTTPToHTTPSRedirectMiddleware(app, None)
    scope = {"type": "lifespan", "asgi": {"version": "3.0"}, "state": {}}

    await middleware(scope, None, None)

    assert seen_scopes == [scope]


@pytest.mark.asyncio
async def test_proxy_fix_without_forwarded_headers_preserves_scope_values() -> None:
    seen_scopes = []

    async def app(scope: dict, receive: Callable | None, send: Callable | None) -> None:
        seen_scopes.append(scope)

    scope = make_http_scope(scheme="http", client=("10.0.0.1", 123), headers=[])
    await ProxyFixMiddleware(app)(scope, None, None)

    assert seen_scopes[0]["scheme"] == "http"
    assert seen_scopes[0]["client"] == ("10.0.0.1", 123)
    assert seen_scopes[0]["headers"] == []
    assert seen_scopes[0] is not scope


@pytest.mark.asyncio
async def test_proxy_fix_trusted_hops_selects_value_from_the_right() -> None:
    seen_scopes = []

    async def app(scope: dict, receive: Callable | None, send: Callable | None) -> None:
        seen_scopes.append(scope)

    middleware = ProxyFixMiddleware(app, trusted_hops=2)
    await middleware(
        make_http_scope(
            headers=[
                (b"x-forwarded-for", b"client, proxy1, proxy2"),
                (b"x-forwarded-proto", b"http, https, http"),
                (b"x-forwarded-host", b"client.example, proxy.example"),
            ],
            client=("10.0.0.1", 123),
        ),
        None,
        None,
    )

    scope = seen_scopes[0]
    assert scope["client"] == ("proxy1", 0)
    assert scope["scheme"] == "https"
    assert [h for h in scope["headers"] if h[0] == b"host"] == [
        (b"host", b"client.example")
    ]


@pytest.mark.asyncio
async def test_proxy_fix_modern_mode_falls_back_to_legacy_headers() -> None:
    seen_scopes = []

    async def app(scope: dict, receive: Callable | None, send: Callable | None) -> None:
        seen_scopes.append(scope)

    await ProxyFixMiddleware(app, mode="modern")(
        make_http_scope(
            headers=[
                (b"x-forwarded-for", b"203.0.113.10"),
                (b"x-forwarded-proto", b"https"),
                (b"x-forwarded-host", b"fallback.example"),
            ]
        ),
        None,
        None,
    )

    scope = seen_scopes[0]
    assert scope["client"] == ("203.0.113.10", 0)
    assert scope["scheme"] == "https"
    assert [h for h in scope["headers"] if h[0] == b"host"] == [
        (b"host", b"fallback.example")
    ]


@pytest.mark.asyncio
async def test_proxy_fix_non_http_scope_is_passed_without_copying() -> None:
    seen_scopes = []

    async def app(scope: dict, receive: Callable | None, send: Callable | None) -> None:
        seen_scopes.append(scope)

    scope = {"type": "lifespan", "asgi": {"version": "3.0"}, "state": {}}
    await ProxyFixMiddleware(app)(scope, None, None)

    assert seen_scopes == [scope]


@pytest.mark.asyncio
async def test_dispatcher_uses_first_matching_mount_even_when_later_mount_is_longer() -> None:
    async def first(scope: dict, receive: Callable | None, send: Callable) -> None:
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"first"})

    async def second(scope: dict, receive: Callable | None, send: Callable) -> None:
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"second"})

    middleware = DispatcherMiddleware({"/api": first, "/api/specific": second})
    sent_events = []

    async def send(message: dict) -> None:
        sent_events.append(message)

    await middleware(make_http_scope(path="/api/specific/item"), None, send)

    assert [event.get("body") for event in sent_events if event["type"] == "http.response.body"] == [
        b"first"
    ]


@pytest.mark.asyncio
async def test_dispatcher_extends_existing_root_path_for_selected_mount() -> None:
    seen_scopes = []

    async def app(scope: dict, receive: Callable | None, send: Callable) -> None:
        seen_scopes.append(scope)
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    middleware = DispatcherMiddleware({"/api": app})

    async def send(message: dict) -> None:
        return None

    await middleware(make_http_scope(path="/api/items", root_path="/base"), None, send)

    assert seen_scopes[0]["root_path"] == "/base/api"
    assert seen_scopes[0]["path"] == "/api/items"


@pytest.mark.asyncio
async def test_wsgi_environment_contains_root_path_path_info_query_and_headers() -> None:
    captured = {}

    def app(environ: dict, start_response: Callable) -> list[bytes]:
        captured.update(environ)
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"ok"]

    messages = await run_asyncio_wsgi(
        AsyncioWSGIMiddleware(app, 2**16),
        make_http_scope(
            method="POST",
            path="/api/items",
            root_path="/api",
            raw_path=b"/api/items",
            query_string=b"a=b",
            headers=[
                (b"content-type", b"text/plain"),
                (b"content-length", b"3"),
                (b"x-example", b"one"),
                (b"x-example", b"two"),
            ],
        ),
        b"abc",
    )

    assert messages[0]["status"] == 200
    assert captured["REQUEST_METHOD"] == "POST"
    assert captured["SCRIPT_NAME"] == "/api"
    assert captured["PATH_INFO"] == "/items"
    assert captured["QUERY_STRING"] == "a=b"
    assert captured["CONTENT_TYPE"] == "text/plain"
    assert captured["CONTENT_LENGTH"] == "3"
    assert captured["HTTP_X_EXAMPLE"] == "one,two"
    assert captured["wsgi.input"].read() == b"abc"


@pytest.mark.asyncio
async def test_wsgi_path_outside_root_path_returns_404_without_calling_app() -> None:
    called = False

    def app(environ: dict, start_response: Callable) -> list[bytes]:
        nonlocal called
        called = True
        start_response("200 OK", [])
        return [b""]

    messages = await run_asyncio_wsgi(
        AsyncioWSGIMiddleware(app, 2**16),
        make_http_scope(path="/other", root_path="/api", raw_path=b"/other"),
    )

    assert messages[0]["type"] == "http.response.start"
    assert messages[0]["status"] == 404
    assert messages[1]["type"] == "http.response.body"
    assert messages[1].get("body", b"") == b""
    assert messages[1].get("more_body", False) is False
    assert called is False


@pytest.mark.asyncio
async def test_wsgi_websocket_scope_closes_without_calling_wsgi_app() -> None:
    called = False

    def app(environ: dict, start_response: Callable) -> list[bytes]:
        nonlocal called
        called = True
        start_response("200 OK", [])
        return [b""]

    middleware = AsyncioWSGIMiddleware(app, 2**16)
    sent_events = []

    async def receive() -> dict:
        return {"type": "websocket.connect"}

    async def send(message: dict) -> None:
        sent_events.append(message)

    await middleware(make_websocket_scope(), receive, send)

    assert sent_events == [{"type": "websocket.close"}]
    assert called is False


@pytest.mark.asyncio
async def test_logger_access_logfile_dash_writes_configured_access_record_to_stdout(capsys) -> None:
    logging.getLogger("hypercorn.access").handlers = []
    config = Config()
    config.accesslog = "-"
    config.access_log_format = "%(m)s %(U)s %(s)s %(b)s"
    logger = Logger(config)

    await logger.access(
        make_http_scope(path="/resource", raw_path=b"/resource", query_string=b"a=b"),
        {"status": 204, "headers": [(b"content-length", b"5")]},
        0.1,
    )

    captured = capsys.readouterr()
    assert "GET /resource 204 5" in captured.out


@pytest.mark.asyncio
async def test_logger_missing_access_atom_renders_dash(capsys) -> None:
    logging.getLogger("hypercorn.access").handlers = []
    config = Config()
    config.accesslog = "-"
    config.access_log_format = "%(not-atom)s"

    await Logger(config).access(make_http_scope(), {"status": 200, "headers": []}, 0.1)

    captured = capsys.readouterr()
    assert captured.out.rstrip().endswith("-")


@pytest.mark.asyncio
async def test_logger_errorlog_dash_writes_error_and_warning_to_stderr(capsys) -> None:
    logging.getLogger("hypercorn.error").handlers = []
    config = Config()
    config.errorlog = "-"
    config.loglevel = "INFO"
    logger = Logger(config)

    await logger.error("failed %s", "request")
    await logger.warning("slow request")

    captured = capsys.readouterr()
    assert "failed request" in captured.err
    assert "slow request" in captured.err


@pytest.mark.asyncio
async def test_asyncio_serve_warns_when_process_or_loop_settings_do_not_apply() -> None:
    async def app(scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return

    config = Config()
    config.bind = []
    config.debug = True
    config.workers = 2

    async def shutdown() -> None:
        return None

    with pytest.warns(Warning) as records:
        await asyncio_serve(app, config, shutdown_trigger=shutdown)

    messages = [str(record.message) for record in records]
    assert any("debug" in message for message in messages)
    assert any("workers" in message for message in messages)


def test_hypercorn_module_help_exposes_command_line_interface() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "hypercorn", "--help"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "usage:" in result.stdout
    assert "--bind" in result.stdout


def test_hypercorn_module_rejects_unknown_verify_mode() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "hypercorn", "--verify-mode", "CERT_UNKNOWN", "asgi:App"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "CERT_UNKNOWN" in result.stderr
    assert "verify" in result.stderr.lower()
