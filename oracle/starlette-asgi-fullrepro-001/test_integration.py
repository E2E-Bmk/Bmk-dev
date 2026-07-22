# Spec2Repo oracle - integration tests for starlette-asgi-fullrepro-001
from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

import pytest

from starlette.applications import Starlette
from starlette.background import BackgroundTask, BackgroundTasks
from starlette.datastructures import Headers, MutableHeaders, QueryParams
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.responses import (
    FileResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)
from starlette.routing import Host, Mount, NoMatchFound, Route, Router, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.testclient import TestClient
from starlette.websockets import WebSocket, WebSocketDisconnect


def _run_asgi(app, scope, incoming=None):
    sent = []
    messages = list(incoming or [{"type": "http.request", "body": b"", "more_body": False}])

    async def receive():
        return messages.pop(0) if messages else {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    asyncio.run(app(scope, receive, send))
    return sent


def _http_scope(path="/", method="GET", headers=None, query_string=b""):
    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.4"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": query_string,
        "root_path": "",
        "headers": headers or [(b"host", b"testserver")],
        "client": ("127.0.0.1", 1234),
        "server": ("testserver", 80),
    }


# Application and lifespan rewrites from tests/test_applications.py and
# tests/test_testclient.py.


def test_application_route_is_visible_through_testclient():
    async def homepage(request):
        return PlainTextResponse("home")

    app = Starlette(routes=[Route("/", homepage)])
    response = TestClient(app).get("/")
    assert (response.status_code, response.text) == (200, "home")


def test_application_places_itself_on_request_scope():
    app = Starlette()

    async def homepage(request):
        return JSONResponse({"same": request.app is app})

    app.routes.append(Route("/", homepage))
    assert TestClient(app).get("/").json() == {"same": True}


def test_testclient_context_runs_lifespan_startup_and_shutdown():
    events = []

    @asynccontextmanager
    async def lifespan(app):
        events.append("startup")
        yield
        events.append("shutdown")

    app = Starlette(routes=[Route("/", lambda request: PlainTextResponse("ok"))], lifespan=lifespan)
    with TestClient(app) as client:
        assert events == ["startup"]
        assert client.get("/").status_code == 200
    assert events == ["startup", "shutdown"]


def test_testclient_construction_alone_does_not_run_lifespan():
    events = []

    @asynccontextmanager
    async def lifespan(app):
        events.append("startup")
        yield

    TestClient(Starlette(lifespan=lifespan))
    assert events == []


def test_lifespan_state_is_shallow_copied_between_requests():
    @asynccontextmanager
    async def lifespan(app):
        yield {"items": [], "label": "initial"}

    async def endpoint(request):
        request.state.items.append(request.url.path)
        old_label = request.state.label
        request.state.label = "changed"
        return JSONResponse({"old_label": old_label, "items": request.state.items})

    app = Starlette(routes=[Route("/{name}", endpoint)], lifespan=lifespan)
    with TestClient(app) as client:
        assert client.get("/one").json() == {"old_label": "initial", "items": ["/one"]}
        assert client.get("/two").json() == {"old_label": "initial", "items": ["/one", "/two"]}


# Routing rewrites from tests/test_routing.py and tests/test_convertors.py.


def test_routing_uses_first_matching_route():
    async def first(request):
        return PlainTextResponse("first")

    async def second(request):
        return PlainTextResponse("second")

    app = Starlette(routes=[Route("/{value}", first), Route("/fixed", second)])
    assert TestClient(app).get("/fixed").text == "first"


def test_routing_converts_integer_path_parameter():
    async def endpoint(request):
        return JSONResponse({"value": request.path_params["value"], "type": type(request.path_params["value"]).__name__})

    response = TestClient(Starlette(routes=[Route("/{value:int}", endpoint)])).get("/12")
    assert response.json() == {"value": 12, "type": "int"}


def test_routing_path_convertor_captures_slashes():
    async def endpoint(request):
        return PlainTextResponse(request.path_params["rest"])

    assert TestClient(Starlette(routes=[Route("/files/{rest:path}", endpoint)])).get("/files/a/b.txt").text == "a/b.txt"


def test_route_get_implies_head_and_method_error_has_allow_header():
    async def endpoint(request):
        return PlainTextResponse("body")

    client = TestClient(Starlette(routes=[Route("/", endpoint, methods=["GET"])]))
    assert client.head("/").status_code == 200
    response = client.post("/")
    assert response.status_code == 405
    assert set(response.headers["allow"].split(", ")) == {"GET", "HEAD"}


def test_host_route_ignores_port_when_matching():
    async def endpoint(request):
        return PlainTextResponse("hosted")

    app = Starlette(routes=[Host("api.example.com", app=Router(routes=[Route("/", endpoint)]))])
    assert TestClient(app, base_url="http://api.example.com:8080").get("/").text == "hosted"


# Request rewrites from tests/test_requests.py and public form behavior.


def test_background_tasks_execute_in_insertion_order():
    events = []
    tasks = BackgroundTasks()
    tasks.add_task(events.append, "first")
    tasks.add_task(events.append, "second")
    _run_asgi(Response("ok", background=tasks), _http_scope())
    assert events == ["first", "second"]


def test_streaming_response_streams_sync_iterable():
    sent = _run_asgi(StreamingResponse(iter([b"a", b"b"])), _http_scope())
    bodies = [message.get("body", b"") for message in sent if message["type"] == "http.response.body"]
    assert b"".join(bodies) == b"ab"


def test_file_response_headers_and_body(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_bytes(b"abcdef")
    response = TestClient(Starlette(routes=[Route("/file", lambda request: FileResponse(path))])).get("/file")
    assert response.content == b"abcdef"
    for name in ("content-length", "last-modified", "etag", "accept-ranges"):
        assert name in response.headers


def test_file_response_supports_byte_range_and_head(tmp_path):
    path = tmp_path / "sample.bin"
    path.write_bytes(b"0123456789")
    app = Starlette(routes=[Route("/file", lambda request: FileResponse(path))])
    client = TestClient(app)
    ranged = client.get("/file", headers={"Range": "bytes=2-5"})
    assert (ranged.status_code, ranged.content, ranged.headers["content-range"]) == (206, b"2345", "bytes 2-5/10")
    head = client.head("/file")
    assert head.status_code == 200 and head.content == b""


# WebSocket rewrites from tests/test_websockets.py.


def test_websocket_text_round_trip():
    async def endpoint(websocket):
        await websocket.accept()
        await websocket.send_text(await websocket.receive_text())

    with TestClient(Starlette(routes=[WebSocketRoute("/ws", endpoint)])).websocket_connect("/ws") as session:
        session.send_text("hello")
        assert session.receive_text() == "hello"


def test_websocket_json_text_and_binary_modes():
    async def endpoint(websocket):
        await websocket.accept()
        await websocket.send_json({"mode": "text"})
        await websocket.send_json({"mode": "binary"}, mode="binary")

    with TestClient(Starlette(routes=[WebSocketRoute("/ws", endpoint)])).websocket_connect("/ws") as session:
        assert session.receive_json() == {"mode": "text"}
        assert session.receive_json(mode="binary") == {"mode": "binary"}


def test_websocket_disconnect_preserves_code_and_reason():
    async def endpoint(websocket):
        await websocket.accept()
        await websocket.close(code=4001, reason="done")

    with TestClient(Starlette(routes=[WebSocketRoute("/ws", endpoint)])).websocket_connect("/ws") as session:
        with pytest.raises(WebSocketDisconnect) as exc:
            session.receive_text()
    assert (exc.value.code, exc.value.reason) == (4001, "done")


def test_websocket_close_before_accept_disconnects_client():
    async def endpoint(websocket):
        await websocket.close()

    client = TestClient(Starlette(routes=[WebSocketRoute("/ws", endpoint)]))
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws"):
            pass
    assert exc.value.code == 1000


def test_websocket_accept_selects_subprotocol():
    async def endpoint(websocket):
        await websocket.accept("chat")
        await websocket.close()

    with TestClient(Starlette(routes=[WebSocketRoute("/ws", endpoint)])).websocket_connect(
        "/ws", subprotocols=["chat"]
    ) as session:
        assert session.accepted_subprotocol == "chat"


def test_websocket_path_params_and_query_are_public_views():
    async def endpoint(websocket):
        await websocket.accept()
        await websocket.send_json({"room": websocket.path_params["room"], "q": websocket.query_params["q"]})

    app = Starlette(routes=[WebSocketRoute("/rooms/{room:int}", endpoint)])
    with TestClient(app).websocket_connect("/rooms/7?q=x") as session:
        assert session.receive_json() == {"room": 7, "q": "x"}


# StaticFiles rewrites from tests/test_staticfiles.py.


def test_staticfiles_serves_file_bytes(tmp_path):
    (tmp_path / "hello.txt").write_text("hello", encoding="utf-8")
    app = Starlette(routes=[Mount("/static", StaticFiles(directory=tmp_path), name="static")])
    assert TestClient(app).get("/static/hello.txt").content == b"hello"


def test_staticfiles_head_returns_headers_without_body(tmp_path):
    (tmp_path / "hello.txt").write_text("hello", encoding="utf-8")
    response = TestClient(Starlette(routes=[Mount("/", StaticFiles(directory=tmp_path))])).head("/hello.txt")
    assert response.status_code == 200
    assert response.headers["content-length"] == "5"
    assert response.content == b""


def test_staticfiles_rejects_post_method(tmp_path):
    (tmp_path / "hello.txt").write_text("hello", encoding="utf-8")
    response = TestClient(Starlette(routes=[Mount("/", StaticFiles(directory=tmp_path))])).post("/hello.txt")
    assert response.status_code == 405


def test_staticfiles_html_directory_redirects_and_serves_index(tmp_path):
    directory = tmp_path / "docs"
    directory.mkdir()
    (directory / "index.html").write_text("index", encoding="utf-8")
    client = TestClient(Starlette(routes=[Mount("/", StaticFiles(directory=tmp_path, html=True))]), follow_redirects=False)
    redirect = client.get("/docs")
    assert redirect.status_code in {301, 307}
    assert redirect.headers["location"].endswith("/docs/")
    assert client.get("/docs/").text == "index"


def test_staticfiles_html_custom_404(tmp_path):
    (tmp_path / "404.html").write_text("custom missing", encoding="utf-8")
    response = TestClient(Starlette(routes=[Mount("/", StaticFiles(directory=tmp_path, html=True))])).get("/missing")
    assert (response.status_code, response.text) == (404, "custom missing")


def test_staticfiles_conditional_request_returns_304(tmp_path):
    (tmp_path / "hello.txt").write_text("hello", encoding="utf-8")
    client = TestClient(Starlette(routes=[Mount("/", StaticFiles(directory=tmp_path))]))
    initial = client.get("/hello.txt")
    conditional = client.get("/hello.txt", headers={"If-None-Match": initial.headers["etag"]})
    assert conditional.status_code == 304
    assert conditional.content == b""


# Middleware rewrites from the middleware upstream modules.


def test_https_redirect_preserves_path_and_query():
    app = Starlette(
        routes=[Route("/items", lambda request: PlainTextResponse("ok"))],
        middleware=[Middleware(HTTPSRedirectMiddleware)],
    )
    response = TestClient(app, follow_redirects=False).get("http://testserver/items?q=1")
    assert response.status_code == 307
    assert response.headers["location"] == "https://testserver/items?q=1"


def test_trusted_host_rejects_unknown_host():
    app = Starlette(
        routes=[Route("/", lambda request: PlainTextResponse("ok"))],
        middleware=[Middleware(TrustedHostMiddleware, allowed_hosts=["example.com"])],
    )
    assert TestClient(app, base_url="http://invalid.test").get("/").status_code == 400


def test_gzip_compresses_large_response_and_skips_small_response():
    async def endpoint(request):
        return PlainTextResponse("x" * int(request.path_params["size"]))

    app = Starlette(
        routes=[Route("/{size:int}", endpoint)],
        middleware=[Middleware(GZipMiddleware, minimum_size=20)],
    )
    client = TestClient(app)
    assert client.get("/100", headers={"Accept-Encoding": "gzip"}).headers["content-encoding"] == "gzip"
    assert "content-encoding" not in client.get("/5", headers={"Accept-Encoding": "gzip"}).headers


def test_cors_preflight_allows_configured_origin_and_method():
    app = CORSMiddleware(
        Starlette(), allow_origins=["https://example.com"], allow_methods=["POST"], allow_headers=["x-token"]
    )
    response = TestClient(app).options(
        "/",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "x-token",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://example.com"


def test_cors_simple_response_echoes_origin_with_credentials():
    app = CORSMiddleware(
        Starlette(routes=[Route("/", lambda request: PlainTextResponse("ok"))]),
        allow_origins=["*"],
        allow_credentials=True,
    )
    response = TestClient(app).get("/", headers={"Origin": "https://example.com", "Cookie": "session=x"})
    assert response.headers["access-control-allow-origin"] == "https://example.com"
    assert response.headers["access-control-allow-credentials"] == "true"


# Error-semantics rewrites from tests/test_exceptions.py and applications tests.


def test_http_exception_default_handler_preserves_status_detail_and_headers():
    async def endpoint(request):
        raise HTTPException(418, detail="teapot", headers={"x-error": "yes"})

    response = TestClient(Starlette(routes=[Route("/", endpoint)])).get("/")
    assert (response.status_code, response.text, response.headers["x-error"]) == (418, "teapot", "yes")


def test_custom_status_exception_handler_is_used():
    async def endpoint(request):
        raise HTTPException(404)

    async def handler(request, exc):
        return JSONResponse({"handled": exc.status_code}, status_code=exc.status_code)

    app = Starlette(routes=[Route("/", endpoint)], exception_handlers={404: handler})
    assert TestClient(app).get("/").json() == {"handled": 404}


def test_unhandled_error_uses_registered_500_handler():
    async def endpoint(request):
        raise RuntimeError("boom")

    async def handler(request, exc):
        return PlainTextResponse("handled", status_code=500)

    app = Starlette(routes=[Route("/", endpoint)], exception_handlers={500: handler})
    response = TestClient(app, raise_server_exceptions=False).get("/")
    assert (response.status_code, response.text) == (500, "handled")


def test_cross_view_response_matches_raw_asgi_and_client():
    response = JSONResponse({"ok": True}, headers={"x-view": "same"})
    raw = _run_asgi(response, _http_scope())
    start = next(message for message in raw if message["type"] == "http.response.start")
    body = b"".join(message.get("body", b"") for message in raw if message["type"] == "http.response.body")

    async def endpoint(request):
        return JSONResponse({"ok": True}, headers={"x-view": "same"})

    client_response = TestClient(Starlette(routes=[Route("/", endpoint)])).get("/")
    assert start["status"] == client_response.status_code == 200
    assert body == client_response.content
    assert client_response.headers["x-view"] == "same"


def test_cross_view_route_parameter_matches_reverse_generation():
    async def endpoint(request):
        return JSONResponse({"value": request.path_params["value"], "reverse": str(request.url_for("item", value=7))})

    app = Starlette(routes=[Route("/items/{value:int}", endpoint, name="item")])
    assert TestClient(app).get("/items/7").json() == {"value": 7, "reverse": "http://testserver/items/7"}
    assert str(app.url_path_for("item", value=7)) == "/items/7"


def test_cross_view_lifespan_state_visible_to_http_and_websocket():
    @asynccontextmanager
    async def lifespan(app):
        yield {"token": "ready"}

    async def http_endpoint(request):
        return PlainTextResponse(request.state.token)

    async def websocket_endpoint(websocket):
        await websocket.accept()
        await websocket.send_text(websocket.state.token)

    app = Starlette(
        routes=[Route("/", http_endpoint), WebSocketRoute("/ws", websocket_endpoint)], lifespan=lifespan
    )
    with TestClient(app) as client:
        assert client.get("/").text == "ready"
        with client.websocket_connect("/ws") as session:
            assert session.receive_text() == "ready"


def test_cross_view_static_reverse_url_serves_same_file(tmp_path):
    (tmp_path / "asset.txt").write_text("asset", encoding="utf-8")

    async def link(request):
        return PlainTextResponse(str(request.url_for("static", path="asset.txt")))

    app = Starlette(
        routes=[Route("/link", link), Mount("/assets", StaticFiles(directory=tmp_path), name="static")]
    )
    client = TestClient(app)
    url = client.get("/link").text
    assert url == "http://testserver/assets/asset.txt"
    assert client.get(url).content == b"asset"


def test_cross_view_middleware_header_visible_to_client_and_raw_asgi():
    class HeaderMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["x-stage"] = "three"
            return response

    app = Starlette(
        routes=[Route("/", lambda request: PlainTextResponse("ok"))],
        middleware=[Middleware(HeaderMiddleware)],
    )
    client_response = TestClient(app).get("/")
    raw = _run_asgi(app, _http_scope())
    start = next(message for message in raw if message["type"] == "http.response.start")
    raw_headers = MutableHeaders(raw=start["headers"])
    assert client_response.headers["x-stage"] == raw_headers["x-stage"] == "three"


# Representative multi-surface workflows.


def test_workflow_route_middleware_and_reverse_url():
    class Marker(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["x-workflow"] = "yes"
            return response

    async def endpoint(request):
        return JSONResponse({"user": request.path_params["user"], "self": str(request.url_for("user", user="sam"))})

    app = Starlette(
        routes=[Route("/users/{user}", endpoint, name="user")], middleware=[Middleware(Marker)]
    )
    response = TestClient(app).get("/users/sam")
    assert response.json() == {"user": "sam", "self": "http://testserver/users/sam"}
    assert response.headers["x-workflow"] == "yes"


def test_workflow_lifespan_http_and_websocket_share_state():
    @asynccontextmanager
    async def lifespan(app):
        yield {"events": []}

    async def add_event(request):
        request.state.events.append("http")
        return JSONResponse(request.state.events)

    async def read_events(websocket):
        await websocket.accept()
        await websocket.send_json(websocket.state.events)

    app = Starlette(routes=[Route("/event", add_event), WebSocketRoute("/events", read_events)], lifespan=lifespan)
    with TestClient(app) as client:
        assert client.get("/event").json() == ["http"]
        with client.websocket_connect("/events") as session:
            assert session.receive_json() == ["http"]


def test_workflow_file_mount_link_and_conditional_fetch(tmp_path):
    (tmp_path / "data.txt").write_text("payload", encoding="utf-8")

    async def index(request):
        return JSONResponse({"url": str(request.url_for("files", path="data.txt"))})

    app = Starlette(routes=[Route("/", index), Mount("/files", StaticFiles(directory=tmp_path), name="files")])
    client = TestClient(app)
    file_url = client.get("/").json()["url"]
    first = client.get(file_url)
    second = client.get(file_url, headers={"If-None-Match": first.headers["etag"]})
    assert first.content == b"payload"
    assert second.status_code == 304
