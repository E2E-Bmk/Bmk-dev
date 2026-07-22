"""Integration tests for httpx-client-fullrepro-001.

Each test exercises ≥2 public API boundaries working together.
Seams tested: client config → request preparation, hooks → transport,
cookies → jar → request, redirects → history, auth → transport, etc.
"""
from __future__ import annotations

import asyncio
import json

import pytest

import httpx
from conftest import BASE_URL, redirect_handler, run_async


# =============================================================================
# Client lifecycle (context manager → transport → is_closed)
# Seam: lifecycle crossing
# =============================================================================


def test_client_context_returns_self_and_closes():
    """Seam: lifecycle crossing — client context manager closes transport on exit."""
    closed = []

    class T(httpx.BaseTransport):
        def handle_request(self, request):
            return httpx.Response(200, request=request)
        def close(self):
            closed.append(True)

    with httpx.Client(transport=T()) as client:
        assert client.is_closed is False
    assert client.is_closed is True
    assert closed == [True]


def test_close_idempotent_and_blocks_requests():
    """Seam: lifecycle crossing — close is idempotent and blocks subsequent requests."""
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200)))
    client.close()
    client.close()
    assert client.is_closed is True
    with pytest.raises(RuntimeError):
        client.get("https://host.test/")


def test_reenter_open_context_raises():
    """Seam: lifecycle crossing — re-entering open client context raises RuntimeError."""
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200)))
    with client:
        with pytest.raises(RuntimeError):
            with client:
                pass


def test_enter_after_close_raises():
    """Seam: lifecycle crossing — entering context after close raises RuntimeError."""
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200)))
    client.close()
    with pytest.raises(RuntimeError):
        with client:
            pass


def test_async_client_lifecycle():
    """Seam: lifecycle crossing — AsyncClient context closes transport via aclose."""
    async def run():
        closed = []

        class T(httpx.AsyncBaseTransport):
            async def handle_async_request(self, request):
                return httpx.Response(200, request=request)
            async def aclose(self):
                closed.append(True)

        async with httpx.AsyncClient(transport=T()) as client:
            resp = await client.get("https://host.test/")
            assert resp.status_code == 200
        assert client.is_closed is True
        assert closed == [True]

    run_async(run())


# =============================================================================
# Configuration merge (client config + request config → prepared request)
# Seam: state consistency — merged values visible in request
# =============================================================================


def test_build_request_merges_headers_params_cookies():
    """Seam: state consistency — client and request config merge into prepared request."""
    client = httpx.Client(
        base_url="https://api.test/v2",
        headers={"X-Client": "yes", "X-Over": "client"},
        params={"client_p": "1"},
        cookies={"sess": "abc"},
        transport=httpx.MockTransport(lambda r: httpx.Response(200)),
    )
    req = client.build_request(
        "GET", "items",
        headers={"X-Over": "request"},
        params={"req_p": "2"},
        cookies={"extra": "cookie"},
    )
    assert req.headers["x-client"] == "yes"
    assert req.headers["x-over"] == "request"
    assert req.url.params["client_p"] == "1"
    assert req.url.params["req_p"] == "2"
    assert "sess=abc" in req.headers["cookie"]


def test_request_auth_none_disables_client_auth():
    """Seam: config interaction — per-request auth=None disables client-level auth."""
    def handler(request):
        return httpx.Response(200, json={"auth": request.headers.get("authorization")}, request=request)

    client = httpx.Client(auth=("user", "pw"), transport=httpx.MockTransport(handler))
    assert client.get("https://host.test/").json()["auth"].startswith("Basic ")
    assert client.get("https://host.test/", auth=None).json()["auth"] is None


def test_base_url_resolves_relative_paths():
    """Seam: config interaction — client base_url resolves relative request paths."""
    client = httpx.Client(base_url="https://api.test/root/")
    req = client.build_request("GET", "child")
    assert str(req.url) == "https://api.test/root/child"


# =============================================================================
# Request sending (client → transport → response)
# Seam: protocol handoff — client dispatches to transport
# =============================================================================


def test_client_request_sends_and_reads_body():
    """Seam: protocol handoff — client dispatches request through transport and reads body."""
    def handler(request):
        return httpx.Response(201, content=b"done", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    resp = client.post("https://host.test/items", content=b"payload")
    assert resp.status_code == 201
    assert resp.content == b"done"
    assert resp.request.method == "POST"


def test_client_send_stream_true_leaves_unread():
    """Seam: lifecycle crossing — send(stream=True) leaves response unread until explicit read."""
    resp_obj = httpx.Response(200, stream=httpx.ByteStream(b"stream"))
    client = httpx.Client(transport=httpx.MockTransport(lambda r: resp_obj))
    req = client.build_request("GET", "https://host.test/")
    streamed = client.send(req, stream=True)
    with pytest.raises(httpx.ResponseNotRead):
        _ = streamed.content
    assert streamed.read() == b"stream"


def test_client_stream_context_closes_on_exit():
    """Seam: lifecycle crossing — stream context closes response on exit."""
    resp_obj = httpx.Response(200, stream=httpx.ByteStream(b"ctx"))
    client = httpx.Client(transport=httpx.MockTransport(lambda r: resp_obj))
    with client.stream("GET", "https://host.test/") as streamed:
        assert streamed.read() == b"ctx"
    assert streamed.is_closed is True


# =============================================================================
# Redirects and history (client → redirect chain → history)
# Seam: state consistency — history captures each redirect step
# =============================================================================


def test_redirect_not_followed_exposes_next_request():
    """Seam: state consistency — unfollowed redirect exposes next_request without history."""
    client = httpx.Client(base_url="https://host.test", transport=httpx.MockTransport(redirect_handler))
    resp = client.get("/start", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.history == []
    assert resp.next_request.url.path == "/end"


def test_redirect_followed_populates_history():
    """Seam: state consistency — followed redirect populates history with intermediate responses."""
    client = httpx.Client(base_url="https://host.test", transport=httpx.MockTransport(redirect_handler), follow_redirects=True)
    resp = client.get("/start")
    assert resp.status_code == 200
    assert resp.text == "arrived"
    assert [h.status_code for h in resp.history] == [302]
    assert resp.next_request is None


def test_303_rewrites_post_to_get():
    """Seam: protocol handoff — 303 redirect rewrites POST to GET on follow."""
    seen = []

    def handler(request):
        seen.append(request.method)
        if request.url.path == "/form":
            return httpx.Response(303, headers={"Location": "/done"}, request=request)
        return httpx.Response(200, request=request)

    client = httpx.Client(base_url="https://host.test", transport=httpx.MockTransport(handler))
    client.post("/form", content=b"data", follow_redirects=True)
    assert seen == ["POST", "GET"]


def test_too_many_redirects_raises():
    """Seam: error propagation — redirect loop exceeding max_redirects raises TooManyRedirects."""
    def handler(request):
        return httpx.Response(302, headers={"Location": "/loop"}, request=request)

    client = httpx.Client(base_url="https://host.test", max_redirects=2, transport=httpx.MockTransport(handler))
    with pytest.raises(httpx.TooManyRedirects):
        client.get("/loop", follow_redirects=True)


def test_request_level_follow_redirects_overrides_client():
    """Seam: config interaction — request-level follow_redirects overrides client default."""
    calls = []

    def handler(request):
        calls.append(request.url.path)
        if request.url.path == "/go":
            return httpx.Response(302, headers={"Location": "/here"}, request=request)
        return httpx.Response(200, request=request)

    client = httpx.Client(base_url="https://host.test", follow_redirects=False, transport=httpx.MockTransport(handler))
    resp = client.get("/go", follow_redirects=True)
    assert resp.status_code == 200
    assert calls == ["/go", "/here"]


# =============================================================================
# Event hooks (hooks → transport → response)
# Seam: state consistency — hook mutations visible downstream
# =============================================================================


def test_request_hook_mutates_outgoing_request():
    """Seam: protocol handoff — request hook mutation visible in transport handler."""
    def hook(request):
        request.headers["X-Hooked"] = "yes"

    def handler(request):
        return httpx.Response(200, text=request.headers["x-hooked"], request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler), event_hooks={"request": [hook]})
    assert client.get("https://host.test/").text == "yes"


def test_hooks_run_in_list_order():
    """Seam: protocol handoff — request hooks execute in configured list order."""
    order = []

    def h1(request):
        order.append("h1")
        request.headers["X-Seq"] = "1"

    def h2(request):
        order.append("h2")

    def handler(request):
        return httpx.Response(200, request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler), event_hooks={"request": [h1, h2]})
    client.get("https://host.test/")
    assert order == ["h1", "h2"]


def test_response_hook_can_read_body():
    """Seam: lifecycle crossing — response hook read makes body available downstream."""
    def handler(request):
        return httpx.Response(200, stream=httpx.ByteStream(b"hook-read"), request=request)

    def hook(response):
        response.read()

    client = httpx.Client(transport=httpx.MockTransport(handler), event_hooks={"response": [hook]})
    resp = client.get("https://host.test/")
    assert resp.content == b"hook-read"


# =============================================================================
# Cookies across requests (jar → extraction → sending)
# Seam: state consistency — cookie jar persists between requests
# =============================================================================


def test_cookies_extracted_and_sent_on_next_request():
    """Seam: state consistency — Set-Cookie extracted and sent on subsequent request."""
    paths = []

    def handler(request):
        paths.append((request.url.path, request.headers.get("cookie")))
        if request.url.path == "/login":
            return httpx.Response(200, headers={"Set-Cookie": "tok=abc; Path=/"}, request=request)
        return httpx.Response(200, request=request)

    client = httpx.Client(base_url="https://host.test", transport=httpx.MockTransport(handler))
    client.get("/login")
    client.get("/dashboard")
    assert paths[1] == ("/dashboard", "tok=abc")


def test_extract_cookies_then_set_cookie_header():
    """Seam: state consistency — jar extract_cookies and set_cookie_header round-trip."""
    req1 = httpx.Request("GET", "https://host.test/auth")
    resp = httpx.Response(200, headers={"Set-Cookie": "sid=xyz; Path=/"}, request=req1)
    jar = httpx.Cookies()
    jar.extract_cookies(resp)
    req2 = httpx.Request("GET", "https://host.test/api")
    jar.set_cookie_header(req2)
    assert req2.headers["cookie"] == "sid=xyz"


# =============================================================================
# Authentication (auth → request preparation → transport)
# Seam: configuration interaction — auth modifies outgoing headers
# =============================================================================


def test_basic_auth_tuple_adds_authorization():
    """Seam: config interaction — basic auth tuple adds Authorization header."""
    def handler(request):
        return httpx.Response(200, json={"auth": request.headers["authorization"]}, request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    resp = client.get("https://host.test/", auth=("user", "pw"))
    assert resp.json()["auth"].startswith("Basic ")


def test_callable_auth_mutates_request():
    """Seam: config interaction — callable auth mutates outgoing request headers."""
    def my_auth(request):
        request.headers["Authorization"] = "Token xyz"
        return request

    def handler(request):
        return httpx.Response(200, text=request.headers["authorization"], request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    assert client.get("https://host.test/", auth=my_auth).text == "Token xyz"


def test_custom_auth_flow_retries():
    """Seam: protocol handoff — custom auth flow retries after 401 through transport."""
    class RetryAuth(httpx.Auth):
        def auth_flow(self, request):
            request.headers["Authorization"] = "attempt1"
            response = yield request
            if response.status_code == 401:
                request.headers["Authorization"] = "attempt2"
                yield request

    calls = []

    def handler(request):
        calls.append(request.headers["authorization"])
        if len(calls) == 1:
            return httpx.Response(401, request=request)
        return httpx.Response(200, request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    resp = client.get("https://host.test/", auth=RetryAuth())
    assert resp.status_code == 200
    assert calls == ["attempt1", "attempt2"]


# =============================================================================
# Transports (MockTransport, WSGITransport, ASGITransport)
# Seam: protocol handoff — client dispatches through transport
# =============================================================================


def test_mock_transport_handler_exception_propagates():
    """Seam: error propagation — MockTransport handler exception propagates to client."""
    def handler(request):
        raise ValueError("boom")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(ValueError, match="boom"):
        client.get("https://host.test/")


def test_wsgi_transport_populates_environ():
    """Seam: protocol handoff — WSGITransport maps request to WSGI environ."""
    captured = {}

    def app(environ, start_response):
        captured["method"] = environ["REQUEST_METHOD"]
        captured["path"] = environ["PATH_INFO"]
        captured["query"] = environ["QUERY_STRING"]
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"wsgi-ok"]

    client = httpx.Client(transport=httpx.WSGITransport(app=app), base_url="http://wsgi.test")
    resp = client.get("/items?page=2")
    assert resp.text == "wsgi-ok"
    assert captured == {"method": "GET", "path": "/items", "query": "page=2"}


def test_asgi_transport_populates_scope():
    """Seam: protocol handoff — ASGITransport maps request to ASGI scope with root_path."""
    async def app(scope, receive, send):
        assert scope["method"] == "GET"
        assert scope["path"] == "/api/data"
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": scope["path"].encode()})

    async def run():
        transport = httpx.ASGITransport(app=app, root_path="/api")
        async with httpx.AsyncClient(transport=transport, base_url="http://asgi.test/api") as client:
            resp = await client.get("/data")
        assert resp.text == "/api/data"

    run_async(run())


def test_asgi_raise_app_exceptions_true_propagates():
    """Seam: error propagation — ASGITransport raise_app_exceptions propagates app errors."""
    async def app(scope, receive, send):
        raise RuntimeError("asgi-error")

    async def run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://asgi.test") as client:
            with pytest.raises(RuntimeError, match="asgi-error"):
                await client.get("/")

    run_async(run())


def test_unsupported_protocol_raises():
    """Seam: error propagation — unsupported URL protocol raises UnsupportedProtocol."""
    client = httpx.Client()
    with pytest.raises(httpx.UnsupportedProtocol):
        client.get("ftp://host.test/")


# =============================================================================
# CLI
# =============================================================================


def test_cli_help_exits_zero():
    """Seam: lifecycle crossing — CLI help invocation exits cleanly."""
    from click.testing import CliRunner
    result = CliRunner().invoke(httpx.main, ["--help"])
    assert result.exit_code == 0


def test_cli_invalid_json_exits_two():
    """Seam: error propagation — CLI invalid JSON flag exits with error code 2."""
    from click.testing import CliRunner
    result = CliRunner().invoke(httpx.main, ["https://host.test/", "--json", "{"])
    assert result.exit_code == 2
