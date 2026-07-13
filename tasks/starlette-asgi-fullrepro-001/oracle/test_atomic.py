# Spec2Repo oracle - atomic tests for starlette-asgi-fullrepro-001
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


def test_application_rejects_middleware_added_after_first_call():
    app = Starlette(routes=[Route("/", lambda request: PlainTextResponse("ok"))])
    assert TestClient(app).get("/").status_code == 200
    with pytest.raises(RuntimeError):
        app.add_middleware(GZipMiddleware)


def test_route_requires_leading_slash():
    with pytest.raises(AssertionError):
        Route("missing", lambda request: Response())


def test_route_rejects_duplicate_parameter_names():
    with pytest.raises(ValueError):
        Route("/{item}/{item}", lambda request: Response())


def test_route_rejects_unknown_convertor():
    with pytest.raises(AssertionError):
        Route("/{item:missing_convertor}", lambda request: Response())


def test_router_reverse_lookup_and_missing_name():
    router = Router(routes=[Route("/users/{user:int}", lambda request: Response(), name="user")])
    assert str(router.url_path_for("user", user=4)) == "/users/4"
    with pytest.raises(NoMatchFound):
        router.url_path_for("missing")


def test_request_is_mapping_over_scope():
    scope = _http_scope("/items")
    request = Request(scope)
    assert request["path"] == "/items"
    assert len(request) == len(scope)


def test_request_url_and_query_params_follow_scope():
    request = Request(_http_scope("/items", query_string=b"a=1&a=2"))
    assert str(request.url) == "http://testserver/items?a=1&a=2"
    assert request.query_params.getlist("a") == ["1", "2"]


def test_request_headers_are_case_insensitive_and_immutable():
    request = Request(_http_scope(headers=[(b"host", b"testserver"), (b"x-token", b"abc")]))
    assert request.headers["X-Token"] == "abc"
    with pytest.raises(TypeError):
        request.headers["x-token"] = "changed"


def test_public_multidict_views_preserve_repeated_values():
    query = QueryParams("a=1&a=2&b=3")
    headers = Headers(raw=[(b"x-tag", b"one"), (b"x-tag", b"two")])
    assert query.getlist("a") == ["1", "2"]
    assert headers.getlist("x-tag") == ["one", "two"]


def test_request_body_is_cached():
    chunks = [{"type": "http.request", "body": b"hello", "more_body": False}]

    async def receive():
        return chunks.pop(0)

    async def read_twice():
        request = Request(_http_scope(method="POST"), receive)
        return await request.body(), await request.body()

    assert asyncio.run(read_twice()) == (b"hello", b"hello")


def test_request_invalid_json_raises_decoder_error():
    messages = [{"type": "http.request", "body": b"not-json", "more_body": False}]

    async def receive():
        return messages.pop(0)

    async def parse():
        return await Request(_http_scope(method="POST"), receive).json()

    with pytest.raises(json.JSONDecodeError):
        asyncio.run(parse())


def test_request_client_projection_handles_present_and_missing_client():
    assert Request(_http_scope()).client.host == "127.0.0.1"
    scope = _http_scope()
    scope["client"] = None
    assert Request(scope).client is None


# Response rewrites from tests/test_responses.py and tests/test_background.py.


def test_response_none_renders_empty_body():
    response = Response(None)
    assert response.body == b""


def test_response_adds_content_length_and_text_charset():
    response = PlainTextResponse("hello")
    assert response.headers["content-length"] == "5"
    assert response.headers["content-type"] == "text/plain; charset=utf-8"


def test_response_204_omits_content_length():
    assert "content-length" not in Response(b"ignored", status_code=204).headers


def test_response_preserves_caller_content_headers():
    response = Response("abc", headers={"content-length": "9", "content-type": "application/custom"})
    assert response.headers["content-length"] == "9"
    assert response.headers["content-type"] == "application/custom"


def test_json_response_is_compact_utf8_and_preserves_unicode():
    response = JSONResponse({"message": "olá"})
    assert response.body == '{"message":"olá"}'.encode()


def test_json_response_rejects_non_finite_numbers():
    with pytest.raises(ValueError):
        JSONResponse({"value": float("nan")})


def test_redirect_response_quotes_location():
    response = RedirectResponse("https://example.com/a path?q=hello world")
    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/a%20path?q=hello%20world"


def test_response_cookie_set_and_delete_are_observable():
    response = Response()
    response.set_cookie("session", "abc", httponly=True, samesite="strict")
    response.delete_cookie("old")
    cookies = response.headers.getlist("set-cookie")
    assert "session=abc" in cookies[0]
    assert "HttpOnly" in cookies[0]
    assert "Max-Age=0" in cookies[1]


def test_file_response_missing_file_raises_at_call_time(tmp_path):
    response = FileResponse(tmp_path / "missing.txt")
    with pytest.raises(RuntimeError):
        _run_asgi(response, _http_scope())


def test_request_missing_session_auth_and_user_raise_assertion():
    request = Request(_http_scope())
    for attribute in ("session", "auth", "user"):
        with pytest.raises(AssertionError):
            getattr(request, attribute)


# Explicit cross-view invariants.
