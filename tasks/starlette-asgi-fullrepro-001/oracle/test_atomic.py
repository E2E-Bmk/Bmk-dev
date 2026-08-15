"""Atomic tests for starlette-asgi-fullrepro-001.

Each test exercises ONE public API with ONE behavior.
"""
from __future__ import annotations

import asyncio
import json
import math
from io import BytesIO
from pathlib import Path

import pytest

from starlette.background import BackgroundTask, BackgroundTasks
from starlette.convertors import Convertor, register_url_convertor
from starlette.datastructures import FormData, Headers, MutableHeaders, QueryParams, URL, UploadFile
from starlette.exceptions import HTTPException, WebSocketException
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)
from starlette.routing import Mount, NoMatchFound, Route, Router, WebSocketRoute
from starlette.testclient import TestClient
from starlette.websockets import WebSocket, WebSocketDisconnect
from conftest import http_scope, run_asgi


# =============================================================================
# URL datastructure
# =============================================================================


def test_url_parses_components():
    url = URL("https://host.test:9443/path?q=1#frag")
    assert url.scheme == "https"
    assert url.hostname == "host.test"
    assert url.port == 9443
    assert url.path == "/path"
    assert url.query == "q=1"
    assert url.fragment == "frag"


def test_url_replace_returns_new_instance():
    url = URL("http://host.test/original?x=1")
    new = url.replace(scheme="https", path="/changed")
    assert str(new) == "https://host.test/changed?x=1"
    assert url.path == "/original"


# =============================================================================
# Headers
# =============================================================================


def test_headers_immutable_case_insensitive():
    h = Headers(raw=[(b"content-type", b"text/plain"), (b"x-id", b"42")])
    assert h["Content-Type"] == "text/plain"
    assert h["X-ID"] == "42"
    with pytest.raises(KeyError):
        _ = h["missing"]
    with pytest.raises(TypeError):
        h["x-id"] = "new"


def test_headers_getlist():
    h = Headers(raw=[(b"accept", b"text/html"), (b"accept", b"application/json")])
    assert h.getlist("accept") == ["text/html", "application/json"]


def test_mutable_headers_assignment():
    mh = MutableHeaders(raw=[(b"x-a", b"1")])
    mh["X-A"] = "2"
    assert mh["x-a"] == "2"


# =============================================================================
# QueryParams
# =============================================================================


def test_queryparams_multidict():
    qp = QueryParams("a=1&a=2&b=3")
    assert qp.getlist("a") == ["1", "2"]
    assert qp.get("a") == "2"
    assert qp.get("missing", "default") == "default"
    assert list(qp.keys()) == ["a", "b"]
    assert qp.multi_items() == [("a", "1"), ("a", "2"), ("b", "3")]


# =============================================================================
# Response types
# =============================================================================


def test_plain_text_response():
    resp = PlainTextResponse("hello")
    scope = http_scope()
    msgs = run_asgi(resp, scope)
    start = msgs[0]
    body = msgs[1]
    assert start["status"] == 200
    headers = dict(start["headers"])
    assert b"text/plain" in headers.get(b"content-type", b"")
    assert body["body"] == b"hello"


def test_html_response():
    resp = HTMLResponse("<b>hi</b>")
    msgs = run_asgi(resp, http_scope())
    headers = dict(msgs[0]["headers"])
    assert b"text/html" in headers.get(b"content-type", b"")
    assert msgs[1]["body"] == b"<b>hi</b>"


def test_json_response_compact_utf8():
    resp = JSONResponse({"key": "value", "emoji": "\U0001f600"})
    msgs = run_asgi(resp, http_scope())
    data = json.loads(msgs[1]["body"])
    assert data == {"key": "value", "emoji": "\U0001f600"}
    assert b"\\u" not in msgs[1]["body"]


def test_json_response_rejects_non_finite():
    with pytest.raises(ValueError):
        JSONResponse({"x": float("inf")})


def test_redirect_response_default_307():
    resp = RedirectResponse("/target path")
    msgs = run_asgi(resp, http_scope())
    assert msgs[0]["status"] == 307
    headers = dict(msgs[0]["headers"])
    assert b"/target%20path" in headers[b"location"]


def test_response_none_body_sends_empty():
    resp = Response(content=None, status_code=204)
    msgs = run_asgi(resp, http_scope())
    assert msgs[0]["status"] == 204
    assert msgs[1]["body"] == b""


def test_response_auto_content_length():
    resp = Response(content="body", media_type="text/plain")
    msgs = run_asgi(resp, http_scope())
    headers = dict(msgs[0]["headers"])
    assert headers[b"content-length"] == b"4"


def test_response_no_content_length_for_204():
    resp = Response(status_code=204)
    msgs = run_asgi(resp, http_scope())
    headers = dict(msgs[0]["headers"])
    assert b"content-length" not in headers


# =============================================================================
# Cookie operations
# =============================================================================


def test_set_cookie_adds_header():
    resp = Response(content="ok")
    resp.set_cookie("sid", "abc", max_age=3600, httponly=True)
    msgs = run_asgi(resp, http_scope())
    cookie_headers = [v for k, v in msgs[0]["headers"] if k == b"set-cookie"]
    assert any(b"sid=abc" in h for h in cookie_headers)
    assert any(b"httponly" in h.lower() for h in cookie_headers)


def test_delete_cookie_sets_max_age_zero():
    resp = Response(content="ok")
    resp.delete_cookie("sid")
    msgs = run_asgi(resp, http_scope())
    cookie_headers = [v for k, v in msgs[0]["headers"] if k == b"set-cookie"]
    assert any(b"max-age=0" in h.lower() for h in cookie_headers)


def test_set_cookie_invalid_samesite_raises():
    resp = Response(content="ok")
    with pytest.raises(AssertionError):
        resp.set_cookie("x", "y", samesite="invalid")


# =============================================================================
# Routing
# =============================================================================


def test_route_path_must_start_with_slash():
    with pytest.raises(AssertionError):
        Route("no-slash", lambda r: PlainTextResponse("x"))


def test_duplicate_path_param_raises():
    with pytest.raises(ValueError):
        Route("/{name}/{name}", lambda r: PlainTextResponse("x"))


def test_unknown_convertor_raises():
    with pytest.raises(AssertionError):
        Route("/{id:nonexistent}", lambda r: PlainTextResponse("x"))


def test_no_match_found_on_bad_reverse_lookup():
    router = Router(routes=[Route("/items/{id:int}", lambda r: PlainTextResponse("x"), name="item")])
    with pytest.raises(NoMatchFound):
        router.url_path_for("nonexistent")


# =============================================================================
# Request attributes from scope
# =============================================================================


def test_request_asserts_http_scope_type():
    with pytest.raises(AssertionError):
        Request({"type": "websocket", "headers": []})


def test_request_mapping_access():
    scope = http_scope(path="/test")
    scope["custom"] = "val"
    req = Request(scope)
    assert req["path"] == "/test"
    assert req["custom"] == "val"


# =============================================================================
# HTTPException
# =============================================================================


def test_http_exception_preserves_attributes():
    exc = HTTPException(status_code=403, detail="forbidden", headers={"X-Err": "1"})
    assert exc.status_code == 403
    assert exc.detail == "forbidden"
    assert exc.headers == {"X-Err": "1"}


# =============================================================================
# WebSocket
# =============================================================================


def test_websocket_asserts_websocket_scope():
    with pytest.raises(AssertionError):
        WebSocket({"type": "http", "headers": []}, None, None)


def test_websocket_disconnect_preserves_code_and_reason():
    exc = WebSocketDisconnect(code=1001, reason="going away")
    assert exc.code == 1001
    assert exc.reason == "going away"


def test_formdata_preserves_repeated_values_and_uploads():
    upload = UploadFile(BytesIO(b"payload"), filename="sample.txt")
    form = FormData([("tag", "one"), ("tag", "two"), ("file", upload)])

    assert form.getlist("tag") == ["one", "two"]
    assert form["file"] is upload
    assert upload.filename == "sample.txt"


def test_uploadfile_async_io_updates_size():
    upload = UploadFile(BytesIO(), size=0, filename="sample.bin")

    async def exercise_upload():
        await upload.write(b"abc")
        await upload.seek(0)
        body = await upload.read()
        await upload.close()
        return body

    assert asyncio.run(exercise_upload()) == b"abc"
    assert upload.size == 3
    assert upload.file.closed is True


def test_response_set_cookie_with_secure_flag():
    resp = Response(content="ok")
    resp.set_cookie(
        "token",
        "abc",
        max_age=60,
        path="/api",
        domain="example.test",
        secure=True,
        httponly=True,
        samesite="strict",
    )
    msgs = run_asgi(resp, http_scope())
    cookie_headers = [v for k, v in msgs[0]["headers"] if k == b"set-cookie"]
    cookie = cookie_headers[-1].lower()
    assert b"token=abc" in cookie
    assert b"max-age=60" in cookie
    assert b"domain=example.test" in cookie
    assert b"path=/api" in cookie
    assert b"secure" in cookie
    assert b"httponly" in cookie
    assert b"samesite=strict" in cookie


def test_websocket_exception_preserves_code_and_reason():
    exc = WebSocketException(code=1008, reason="policy violation")
    assert exc.code == 1008
    assert exc.reason == "policy violation"
