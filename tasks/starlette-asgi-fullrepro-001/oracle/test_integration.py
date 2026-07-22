"""Integration tests for starlette-asgi-fullrepro-001.

Each test exercises ≥2 public API boundaries working together.
Seams: routing → request → response, middleware → endpoint,
lifespan → state → request, TestClient → ASGI app, etc.
"""
from __future__ import annotations

import json
import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

import pytest

from starlette.applications import Starlette
from starlette.background import BackgroundTask, BackgroundTasks
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
    Response,
    StreamingResponse,
)
from starlette.routing import Host, Mount, NoMatchFound, Route, Router, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.testclient import TestClient
from starlette.websockets import WebSocket, WebSocketDisconnect


# =============================================================================
# CVI-1: Route → TestClient response matches endpoint
# Seam: routing → dispatch → response
# =============================================================================


def test_route_returns_correct_response_through_test_client():
    """CVI-1: Seam: protocol handoff — route dispatch ↔ TestClient JSON response."""
    async def homepage(request):
        return JSONResponse({"path": request.url.path})

    app = Starlette(routes=[Route("/home", homepage)])
    with TestClient(app) as client:
        resp = client.get("/home")
    assert resp.status_code == 200
    assert resp.json() == {"path": "/home"}


def test_unmatched_route_returns_404():
    """CVI-1: Seam: error propagation — unmatched route ↔ 404 response."""
    app = Starlette(routes=[Route("/exists", lambda r: PlainTextResponse("ok"))])
    with TestClient(app) as client:
        assert client.get("/missing").status_code == 404


def test_wrong_method_returns_405_with_allow_header():
    """CVI-1: Seam: error propagation — wrong HTTP method ↔ 405 with Allow header."""
    app = Starlette(routes=[Route("/item", lambda r: PlainTextResponse("ok"), methods=["POST"])])
    with TestClient(app) as client:
        resp = client.get("/item")
    assert resp.status_code == 405
    assert "POST" in resp.headers["allow"]


def test_get_implies_head():
    """CVI-1: Seam: protocol handoff — GET route registration ↔ HEAD request empty-body response."""
    app = Starlette(routes=[Route("/page", lambda r: PlainTextResponse("body"), methods=["GET"])])
    with TestClient(app) as client:
        resp = client.head("/page")
    assert resp.status_code == 200
    assert resp.content == b""


# =============================================================================
# CVI-2: Path parameters converted and visible in request
# Seam: routing convertor → request.path_params
# =============================================================================


def test_int_convertor_passes_integer():
    """CVI-2: Seam: state consistency — int path convertor ↔ integer path_params value."""
    async def handler(request):
        return JSONResponse({"id": request.path_params["id"], "type": type(request.path_params["id"]).__name__})

    app = Starlette(routes=[Route("/items/{id:int}", handler)])
    with TestClient(app) as client:
        resp = client.get("/items/42")
    assert resp.json() == {"id": 42, "type": "int"}


def test_int_convertor_rejects_non_integer():
    """CVI-2: Seam: error propagation — non-integer path segment ↔ 404 no match."""
    app = Starlette(routes=[Route("/items/{id:int}", lambda r: PlainTextResponse("ok"))])
    with TestClient(app) as client:
        assert client.get("/items/abc").status_code == 404


def test_path_convertor_includes_slashes():
    """CVI-2: Seam: state consistency — path convertor ↔ slash-containing path param capture."""
    async def handler(request):
        return PlainTextResponse(request.path_params["rest"])

    app = Starlette(routes=[Route("/files/{rest:path}", handler)])
    with TestClient(app) as client:
        resp = client.get("/files/a/b/c.txt")
    assert resp.text == "a/b/c.txt"


# =============================================================================
# CVI-3: Response visible through TestClient matches ASGI messages
# Seam: endpoint response → ASGI send → TestClient
# =============================================================================


def test_custom_headers_and_status_visible_through_client():
    """CVI-3: Seam: state consistency — Response status/headers ↔ TestClient visibility."""
    async def handler(request):
        return Response(content="custom", status_code=201, headers={"X-Custom": "val"})

    app = Starlette(routes=[Route("/", handler)])
    with TestClient(app) as client:
        resp = client.get("/")
    assert resp.status_code == 201
    assert resp.headers["x-custom"] == "val"
    assert resp.text == "custom"


# =============================================================================
# CVI-4: Middleware header appended visible in TestClient
# Seam: middleware → endpoint → response
# =============================================================================


def test_middleware_appends_header_to_response():
    """CVI-4: Seam: protocol handoff — middleware dispatch ↔ appended response header."""
    class AddHeader(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["X-Middle"] = "added"
            return response

    app = Starlette(
        routes=[Route("/", lambda r: PlainTextResponse("ok"))],
        middleware=[Middleware(AddHeader)],
    )
    with TestClient(app) as client:
        resp = client.get("/")
    assert resp.headers["x-middle"] == "added"


# =============================================================================
# CVI-5: Lifespan state visible in request handlers
# Seam: lifespan → state → request.state
# =============================================================================


def test_lifespan_state_shared_with_requests():
    """CVI-5: Seam: lifecycle crossing — lifespan state ↔ request.state across requests."""
    @asynccontextmanager
    async def lifespan(app):
        yield {"counter": [0]}

    async def handler(request):
        request.state["counter"][0] += 1
        return JSONResponse({"count": request.state["counter"][0]})

    app = Starlette(routes=[Route("/inc", handler)], lifespan=lifespan)
    with TestClient(app) as client:
        assert client.get("/inc").json()["count"] == 1
        assert client.get("/inc").json()["count"] == 2


def test_lifespan_state_key_rebinding_does_not_affect_later_requests():
    """CVI-5: Seam: state consistency — per-request state mutation ↔ later request isolation."""
    @asynccontextmanager
    async def lifespan(app):
        yield {"val": "original"}

    async def mutate(request):
        request.state["val"] = "mutated"
        return PlainTextResponse("ok")

    async def read(request):
        return PlainTextResponse(request.state["val"])

    app = Starlette(routes=[Route("/mutate", mutate), Route("/read", read)], lifespan=lifespan)
    with TestClient(app) as client:
        client.get("/mutate")
        assert client.get("/read").text == "original"


# =============================================================================
# CVI-6: StaticFiles mount serves file bytes
# Seam: mount → static files → file response
# =============================================================================


def test_static_files_serves_existing_file(tmp_path):
    """CVI-6: Seam: protocol handoff — StaticFiles mount ↔ file bytes response."""
    (tmp_path / "hello.txt").write_text("static content")
    app = Starlette(routes=[Mount("/static", StaticFiles(directory=str(tmp_path)), name="static")])
    with TestClient(app) as client:
        resp = client.get("/static/hello.txt")
    assert resp.status_code == 200
    assert resp.text == "static content"


def test_static_files_returns_404_for_missing(tmp_path):
    """CVI-6: Seam: error propagation — missing static file ↔ 404 response."""
    (tmp_path / "exists.txt").write_text("x")
    app = Starlette(routes=[Mount("/static", StaticFiles(directory=str(tmp_path)))])
    with TestClient(app) as client:
        assert client.get("/static/missing.txt").status_code == 404


def test_static_files_method_enforcement(tmp_path):
    """CVI-6: Seam: error propagation — POST on static file ↔ 405 response."""
    (tmp_path / "f.txt").write_text("x")
    app = Starlette(routes=[Mount("/s", StaticFiles(directory=str(tmp_path)))])
    with TestClient(app) as client:
        assert client.post("/s/f.txt").status_code == 405


# =============================================================================
# CVI-7: WebSocket lifecycle
# Seam: route → websocket accept → send/receive → close
# =============================================================================


def test_websocket_json_exchange():
    """CVI-7: Seam: protocol handoff — WebSocket accept/send ↔ client JSON receive."""
    async def ws_handler(websocket):
        await websocket.accept()
        await websocket.send_json({"msg": "hello"})
        await websocket.close()

    app = Starlette(routes=[WebSocketRoute("/ws", ws_handler)])
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            data = ws.receive_json()
    assert data == {"msg": "hello"}


def test_websocket_disconnect_raises_on_receive():
    """CVI-7: Seam: error propagation — WebSocket close ↔ WebSocketDisconnect on receive."""
    async def ws_handler(websocket):
        await websocket.accept()
        await websocket.send_text("hi")
        await websocket.close()

    app = Starlette(routes=[WebSocketRoute("/ws", ws_handler)])
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            ws.receive_text()
            with pytest.raises(WebSocketDisconnect):
                ws.receive_text()


# =============================================================================
# CVI-8: Background tasks run after response body sent
# Seam: response → background task → state mutation
# =============================================================================


def test_background_task_runs_after_response():
    """CVI-8: Seam: lifecycle crossing — response delivery ↔ background task execution."""
    results = []

    async def handler(request):
        task = BackgroundTask(lambda: results.append("done"))
        return PlainTextResponse("ok", background=task)

    app = Starlette(routes=[Route("/bg", handler)])
    with TestClient(app) as client:
        resp = client.get("/bg")
    assert resp.text == "ok"
    assert results == ["done"]


def test_background_tasks_run_in_order():
    """CVI-8: Seam: lifecycle crossing — BackgroundTasks queue ↔ ordered post-response execution."""
    order = []

    async def handler(request):
        tasks = BackgroundTasks()
        tasks.add_task(lambda: order.append("first"))
        tasks.add_task(lambda: order.append("second"))
        return PlainTextResponse("ok", background=tasks)

    app = Starlette(routes=[Route("/bg", handler)])
    with TestClient(app) as client:
        client.get("/bg")
    assert order == ["first", "second"]


# =============================================================================
# Middleware behaviors
# =============================================================================


def test_gzip_middleware_compresses_large_responses():
    """Seam: protocol handoff — GZipMiddleware ↔ gzip content-encoding on large body."""
    async def handler(request):
        return PlainTextResponse("x" * 500)

    app = Starlette(
        routes=[Route("/", handler)],
        middleware=[Middleware(GZipMiddleware, minimum_size=100)],
    )
    with TestClient(app) as client:
        resp = client.get("/", headers={"Accept-Encoding": "gzip"})
    assert resp.headers["content-encoding"] == "gzip"
    assert len(resp.content) < 500


def test_gzip_middleware_skips_small_responses():
    """Seam: config interaction — minimum_size threshold ↔ uncompressed small response."""
    async def handler(request):
        return PlainTextResponse("small")

    app = Starlette(
        routes=[Route("/", handler)],
        middleware=[Middleware(GZipMiddleware, minimum_size=100)],
    )
    with TestClient(app) as client:
        resp = client.get("/", headers={"Accept-Encoding": "gzip"})
    assert "content-encoding" not in resp.headers


def test_https_redirect_middleware():
    """Seam: protocol handoff — HTTP request ↔ HTTPS 307 redirect response."""
    app = Starlette(
        routes=[Route("/", lambda r: PlainTextResponse("ok"))],
        middleware=[Middleware(HTTPSRedirectMiddleware)],
    )
    client = TestClient(app, base_url="http://testserver", follow_redirects=False)
    with client:
        resp = client.get("/")
    assert resp.status_code == 307
    assert resp.headers["location"].startswith("https://")


def test_trusted_host_middleware_rejects_invalid_host():
    """Seam: error propagation — invalid Host header ↔ 400 response."""
    app = Starlette(
        routes=[Route("/", lambda r: PlainTextResponse("ok"))],
        middleware=[Middleware(TrustedHostMiddleware, allowed_hosts=["good.test"])],
    )
    with TestClient(app, base_url="http://evil.test") as client:
        resp = client.get("/")
    assert resp.status_code == 400


def test_cors_preflight_returns_200_for_allowed_origin():
    """Seam: config interaction — CORS allow_origins ↔ successful preflight response."""
    app = Starlette(
        routes=[Route("/api", lambda r: PlainTextResponse("ok"))],
        middleware=[Middleware(CORSMiddleware, allow_origins=["https://allowed.test"], allow_methods=["GET", "POST"])],
    )
    with TestClient(app) as client:
        resp = client.options(
            "/api",
            headers={
                "Origin": "https://allowed.test",
                "Access-Control-Request-Method": "POST",
            },
        )
    assert resp.status_code == 200
    assert "https://allowed.test" in resp.headers["access-control-allow-origin"]


def test_cors_disallowed_origin_returns_400():
    """Seam: error propagation — disallowed CORS origin ↔ 400 preflight response."""
    app = Starlette(
        routes=[Route("/api", lambda r: PlainTextResponse("ok"))],
        middleware=[Middleware(CORSMiddleware, allow_origins=["https://allowed.test"])],
    )
    with TestClient(app) as client:
        resp = client.options(
            "/api",
            headers={
                "Origin": "https://evil.test",
                "Access-Control-Request-Method": "GET",
            },
        )
    assert resp.status_code == 400


# =============================================================================
# Reverse URL generation
# =============================================================================


def test_url_for_generates_absolute_url():
    """Seam: state consistency — named route ↔ url_for absolute URL in handler."""
    async def handler(request):
        url = request.url_for("item", id=7)
        return PlainTextResponse(str(url))

    app = Starlette(routes=[Route("/items/{id:int}", handler, name="item")])
    with TestClient(app) as client:
        resp = client.get("/items/7")
    assert "/items/7" in resp.text


def test_url_path_for_raises_no_match():
    """Seam: error propagation — unknown route name ↔ NoMatchFound exception."""
    app = Starlette(routes=[Route("/x", lambda r: PlainTextResponse("ok"), name="x")])
    with pytest.raises(NoMatchFound):
        app.url_path_for("nonexistent")


# =============================================================================
# Exception handling
# =============================================================================


def test_http_exception_becomes_error_response():
    """Seam: error propagation — HTTPException in handler ↔ error response status."""
    async def handler(request):
        raise HTTPException(status_code=403, detail="denied")

    app = Starlette(routes=[Route("/secret", handler)])
    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.get("/secret")
    assert resp.status_code == 403


def test_custom_exception_handler():
    """Seam: error propagation — registered exception handler ↔ custom JSON error response."""
    async def handler(request):
        raise HTTPException(status_code=418)

    async def custom_handler(request, exc):
        return JSONResponse({"tea": True}, status_code=exc.status_code)

    app = Starlette(routes=[Route("/tea", handler)], exception_handlers={418: custom_handler})
    with TestClient(app) as client:
        resp = client.get("/tea")
    assert resp.status_code == 418
    assert resp.json() == {"tea": True}


# =============================================================================
# Mount and nested routing
# =============================================================================


def test_mount_strips_prefix_for_child_routes():
    """Seam: protocol handoff — Mount prefix stripping ↔ child route dispatch."""
    sub = Router(routes=[Route("/detail", lambda r: PlainTextResponse("detail"))])
    app = Starlette(routes=[Mount("/api", sub)])
    with TestClient(app) as client:
        assert client.get("/api/detail").text == "detail"


# =============================================================================
# Middleware stack locking
# =============================================================================


def test_add_middleware_after_first_request_raises():
    """Seam: lifecycle crossing — first request ↔ middleware stack lock RuntimeError."""
    app = Starlette(routes=[Route("/", lambda r: PlainTextResponse("ok"))])
    with TestClient(app) as client:
        client.get("/")
        with pytest.raises(RuntimeError):
            app.add_middleware(GZipMiddleware)


# =============================================================================
# Streaming response
# =============================================================================


def test_streaming_response_sends_chunks():
    """Seam: protocol handoff — StreamingResponse generator ↔ concatenated response body."""
    async def gen():
        yield b"chunk1"
        yield b"chunk2"

    async def handler(request):
        return StreamingResponse(gen())

    app = Starlette(routes=[Route("/stream", handler)])
    with TestClient(app) as client:
        resp = client.get("/stream")
    assert resp.content == b"chunk1chunk2"


# =============================================================================
# Request body consumption
# =============================================================================


def test_request_body_cached_after_first_read():
    """Seam: state consistency — repeated request.body() ↔ cached byte identity."""
    async def handler(request):
        first = await request.body()
        second = await request.body()
        return JSONResponse({"same": first == second, "body": first.decode()})

    app = Starlette(routes=[Route("/body", handler, methods=["POST"])])
    with TestClient(app) as client:
        resp = client.post("/body", content=b"data")
    assert resp.json() == {"same": True, "body": "data"}


def test_request_json_parses_body():
    """Seam: state consistency — JSON request body ↔ request.json() parsed dict."""
    async def handler(request):
        data = await request.json()
        return JSONResponse(data)

    app = Starlette(routes=[Route("/json", handler, methods=["POST"])])
    with TestClient(app) as client:
        resp = client.post("/json", json={"key": "val"})
    assert resp.json() == {"key": "val"}
