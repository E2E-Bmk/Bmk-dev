# Spec2Repo oracle - integration tests for httpx-client-fullrepro-001
import asyncio
import json

import pytest

import httpx


def test_client_close_is_idempotent_and_blocks_later_send():
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200)))
    assert client.is_closed is False
    assert client.close() is None
    assert client.close() is None
    assert client.is_closed is True
    with pytest.raises(RuntimeError):
        client.get("https://example.org/")


def test_client_context_returns_self_and_closes_transport():
    closed = []

    class Transport(httpx.BaseTransport):
        def handle_request(self, request):
            return httpx.Response(200, request=request)

        def close(self):
            closed.append("transport")

    client = httpx.Client(transport=Transport())
    with client as entered:
        assert entered is client
        assert entered.get("https://example.org/").status_code == 200
    assert client.is_closed is True
    assert closed == ["transport"]


def test_async_client_context_and_aclose_are_idempotent():
    async def run():
        closed = []

        class Transport(httpx.AsyncBaseTransport):
            async def handle_async_request(self, request):
                return httpx.Response(200, request=request)

            async def aclose(self):
                closed.append("transport")

        client = httpx.AsyncClient(transport=Transport())
        async with client as entered:
            assert entered is client
            response = await entered.get("https://example.org/")
            assert response.status_code == 200
        assert client.is_closed is True
        assert closed == ["transport"]
        assert await client.aclose() is None

    asyncio.run(run())


def test_build_request_merges_base_url_headers_cookies_and_params():
    client = httpx.Client(
        base_url="https://example.org/api/v1",
        headers={"X-Client": "yes", "X-Override": "client"},
        cookies={"session": "abc"},
        params={"client": "1", "replace": "old"},
        transport=httpx.MockTransport(lambda request: httpx.Response(200)),
    )
    request = client.build_request(
        "get",
        "items?replace=url",
        headers={"X-Override": "request"},
        cookies={"request": "cookie"},
        params={"replace": "new", "local": "2"},
    )
    assert request.method == "GET"
    assert str(request.url) == "https://example.org/api/v1/items?client=1&replace=new&local=2"
    assert request.headers["x-client"] == "yes"
    assert request.headers["x-override"] == "request"
    assert "session=abc" in request.headers["cookie"]
    assert "request=cookie" in request.headers["cookie"]


def test_client_request_sends_prepared_request_and_reads_body():
    seen = []

    def handler(request):
        seen.append((request.method, str(request.url), request.headers["x-token"]))
        return httpx.Response(201, content=b"created", request=request)

    client = httpx.Client(base_url="https://example.org", transport=httpx.MockTransport(handler))
    response = client.post("/items", headers={"X-Token": "abc"}, content=b"payload")
    assert seen == [("POST", "https://example.org/items", "abc")]
    assert response.status_code == 201
    assert response.content == b"created"
    assert response.request.method == "POST"


def test_client_send_stream_true_leaves_response_unread_until_read():
    response = httpx.Response(200, stream=httpx.ByteStream(b"streamed"))
    client = httpx.Client(transport=httpx.MockTransport(lambda request: response))
    request = client.build_request("GET", "https://example.org/")
    streamed = client.send(request, stream=True)
    with pytest.raises(httpx.ResponseNotRead):
        _ = streamed.content
    assert streamed.read() == b"streamed"
    assert streamed.content == b"streamed"


def test_client_stream_context_closes_response_on_exit():
    response = httpx.Response(200, stream=httpx.ByteStream(b"abc"))
    client = httpx.Client(transport=httpx.MockTransport(lambda request: response))
    with client.stream("GET", "https://example.org/") as streamed:
        assert streamed.is_closed is False
        assert streamed.read() == b"abc"
    assert streamed.is_closed is True


def test_async_client_request_and_build_request():
    async def run():
        seen = []

        async def handler(request):
            seen.append((request.method, str(request.url)))
            return httpx.Response(200, json={"ok": True}, request=request)

        async with httpx.AsyncClient(base_url="https://example.org", transport=httpx.MockTransport(handler)) as client:
            request = client.build_request("POST", "/submit", json={"a": 1})
            assert request.method == "POST"
            assert request.url.path == "/submit"
            response = await client.send(request)
            assert response.json() == {"ok": True}
        assert seen == [("POST", "https://example.org/submit")]

    asyncio.run(run())


def test_request_level_auth_none_disables_client_auth():
    def handler(request):
        return httpx.Response(200, json={"auth": request.headers.get("authorization")}, request=request)

    client = httpx.Client(auth=("user", "pass"), transport=httpx.MockTransport(handler))
    assert client.get("https://example.org/").json()["auth"].startswith("Basic ")
    assert client.get("https://example.org/", auth=None).json()["auth"] is None


def test_request_level_follow_redirects_overrides_client_default():
    calls = []

    def handler(request):
        calls.append(request.url.path)
        if request.url.path == "/start":
            return httpx.Response(302, headers={"Location": "/end"}, request=request)
        return httpx.Response(200, text="done", request=request)

    client = httpx.Client(base_url="https://example.org", follow_redirects=False, transport=httpx.MockTransport(handler))
    response = client.get("/start", follow_redirects=True)
    assert response.status_code == 200
    assert [item.status_code for item in response.history] == [302]
    assert calls == ["/start", "/end"]


def test_cookies_extract_and_send_matching_cookie_header():
    request = httpx.Request("GET", "https://example.org/login")
    response = httpx.Response(200, headers={"Set-Cookie": "sid=abc; Path=/"}, request=request)
    cookies = httpx.Cookies()
    cookies.extract_cookies(response)
    outgoing = httpx.Request("GET", "https://example.org/account")
    cookies.set_cookie_header(outgoing)
    assert outgoing.headers["cookie"] == "sid=abc"


def test_client_cookie_jar_persists_between_requests():
    paths = []

    def handler(request):
        paths.append((request.url.path, request.headers.get("cookie")))
        if request.url.path == "/login":
            return httpx.Response(200, headers={"Set-Cookie": "sid=abc; Path=/"}, request=request)
        return httpx.Response(200, request=request)

    client = httpx.Client(base_url="https://example.org", transport=httpx.MockTransport(handler))
    client.get("/login")
    client.get("/profile")
    assert paths == [("/login", None), ("/profile", "sid=abc")]


def test_async_response_aread_and_aiter_bytes():
    async def run():
        response = httpx.Response(200, stream=httpx.ByteStream(b"abc"))
        assert await response.aread() == b"abc"
        assert response.content == b"abc"

        streamed = httpx.Response(200, stream=httpx.ByteStream(b"xy"))
        chunks = []
        async for chunk in streamed.aiter_bytes():
            chunks.append(chunk)
        assert chunks == [b"xy"]
        with pytest.raises(httpx.StreamConsumed):
            async for _ in streamed.aiter_bytes():
                pass

    asyncio.run(run())


def test_redirect_without_following_exposes_next_request():
    def handler(request):
        return httpx.Response(302, headers={"Location": "/next"}, request=request)

    client = httpx.Client(base_url="https://example.org", transport=httpx.MockTransport(handler))
    response = client.get("/start", follow_redirects=False)
    assert response.history == []
    assert response.next_request.method == "GET"
    assert str(response.next_request.url) == "https://example.org/next"


def test_follow_redirects_populates_history_and_final_request():
    def handler(request):
        if request.url.path == "/one":
            return httpx.Response(302, headers={"Location": "/two"}, request=request)
        if request.url.path == "/two":
            return httpx.Response(301, headers={"Location": "/done"}, request=request)
        return httpx.Response(200, text=request.url.path, request=request)

    client = httpx.Client(base_url="https://example.org", follow_redirects=True, transport=httpx.MockTransport(handler))
    response = client.get("/one")
    assert response.text == "/done"
    assert [item.status_code for item in response.history] == [302, 301]
    assert [item.request.url.path for item in response.history] == ["/one", "/two"]
    assert response.next_request is None


def test_post_303_redirect_rewrites_to_get():
    seen = []

    def handler(request):
        seen.append((request.method, request.url.path))
        if request.url.path == "/submit":
            return httpx.Response(303, headers={"Location": "/result"}, request=request)
        return httpx.Response(200, request=request)

    client = httpx.Client(base_url="https://example.org", transport=httpx.MockTransport(handler))
    response = client.post("/submit", content=b"payload", follow_redirects=True)
    assert response.status_code == 200
    assert seen == [("POST", "/submit"), ("GET", "/result")]


def test_request_and_response_hooks_run_in_order_and_mutate_request():
    events = []

    def first_request(request):
        events.append(("request", "first"))
        request.headers["X-Trace"] = "1"

    def second_request(request):
        events.append(("request", request.headers["X-Trace"]))
        request.headers["X-Trace"] = "2"

    def response_hook(response):
        events.append(("response", response.request.headers["X-Trace"]))

    def handler(request):
        events.append(("handler", request.headers["X-Trace"]))
        return httpx.Response(200, request=request)

    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        event_hooks={"request": [first_request, second_request], "response": [response_hook]},
    )
    client.get("https://example.org/")
    assert events == [("request", "first"), ("request", "1"), ("handler", "2"), ("response", "2")]


def test_response_hook_can_read_streaming_body_before_return():
    def handler(request):
        return httpx.Response(200, stream=httpx.ByteStream(b"hook-body"), request=request)

    def read_body(response):
        assert response.read() == b"hook-body"

    client = httpx.Client(transport=httpx.MockTransport(handler), event_hooks={"response": [read_body]})
    response = client.get("https://example.org/")
    assert response.content == b"hook-body"


def test_custom_auth_flow_can_retry_with_response_history():
    class RetryAuth(httpx.Auth):
        def auth_flow(self, request):
            request.headers["Authorization"] = "first"
            response = yield request
            if response.status_code == 401:
                request.headers["Authorization"] = "second"
                yield request

    seen = []

    def handler(request):
        seen.append(request.headers["authorization"])
        if len(seen) == 1:
            return httpx.Response(401, request=request)
        return httpx.Response(200, request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    response = client.get("https://example.org/", auth=RetryAuth())
    assert response.status_code == 200
    assert seen == ["first", "second"]
    assert [item.status_code for item in response.history] == [401]


def test_auth_flow_reads_request_body_when_required():
    class BodyAuth(httpx.Auth):
        requires_request_body = True

        def auth_flow(self, request):
            request.headers["X-Body-Length"] = str(len(request.content))
            yield request

    def handler(request):
        return httpx.Response(200, text=request.headers["x-body-length"], request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    assert client.post("https://example.org/", content=b"abcdef", auth=BodyAuth()).text == "6"


def test_mock_transport_calls_sync_handler_with_request():
    seen = []

    def handler(request):
        seen.append((request.method, request.url.path))
        return httpx.Response(204, request=request)

    client = httpx.Client(base_url="https://example.org", transport=httpx.MockTransport(handler))
    assert client.delete("/resource").status_code == 204
    assert seen == [("DELETE", "/resource")]


def test_async_mock_transport_awaits_async_handler():
    async def run():
        seen = []

        async def handler(request):
            seen.append(request.url.path)
            return httpx.Response(200, text="async", request=request)

        async with httpx.AsyncClient(base_url="https://example.org", transport=httpx.MockTransport(handler)) as client:
            response = await client.get("/resource")
        assert response.text == "async"
        assert seen == ["/resource"]

    asyncio.run(run())


def test_wsgi_transport_populates_environ_and_returns_response():
    captured = {}

    def app(environ, start_response):
        captured["method"] = environ["REQUEST_METHOD"]
        captured["path"] = environ["PATH_INFO"]
        captured["query"] = environ["QUERY_STRING"]
        captured["remote"] = environ["REMOTE_ADDR"]
        body = environ["wsgi.input"].read()
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [body + b":" + environ["PATH_INFO"].encode()]

    transport = httpx.WSGITransport(app=app, remote_addr="10.0.0.5")
    client = httpx.Client(transport=transport, base_url="http://testserver")
    response = client.post("/items?x=1", content=b"data")
    assert response.text == "data:/items"
    assert captured == {"method": "POST", "path": "/items", "query": "x=1", "remote": "10.0.0.5"}


def test_wsgi_transport_can_return_error_response_when_configured():
    def app(environ, start_response):
        start_response("500 ERROR", [("Content-Type", "text/plain")], (RuntimeError, RuntimeError("boom"), None))
        return [b"error"]

    client = httpx.Client(transport=httpx.WSGITransport(app=app, raise_app_exceptions=False), base_url="http://testserver")
    response = client.get("/")
    assert response.status_code == 500
    assert response.text == "error"


def test_asgi_transport_populates_scope_and_returns_response():
    async def app(scope, receive, send):
        assert scope["method"] == "POST"
        assert scope["path"] == "/api/items"
        assert scope["query_string"] == b"x=1"
        await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"text/plain")]})
        await send({"type": "http.response.body", "body": scope["path"].encode()})

    async def run():
        transport = httpx.ASGITransport(app=app, root_path="/api", client=("1.2.3.4", 1234))
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver/api") as client:
            response = await client.post("/items?x=1", content=b"data")
        assert response.text == "/api/items"

    asyncio.run(run())


def test_request_hook_header_visible_to_transport_cross_view():
    def hook(request):
        request.headers["X-Cross"] = "visible"

    def handler(request):
        return httpx.Response(200, text=request.headers["x-cross"], request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler), event_hooks={"request": [hook]})
    assert client.get("https://example.org/").text == "visible"


def test_response_object_seen_by_hook_is_returned_to_caller():
    seen = []

    def handler(request):
        return httpx.Response(200, text="same", request=request)

    def hook(response):
        seen.append(id(response))

    client = httpx.Client(transport=httpx.MockTransport(handler), event_hooks={"response": [hook]})
    response = client.get("https://example.org/")
    assert seen == [id(response)]


def test_built_request_defaults_match_url_header_and_query_views():
    client = httpx.Client(
        base_url="https://example.org/base",
        headers={"X-One": "1"},
        cookies={"a": "b"},
        params={"q": "client"},
    )
    request = client.build_request("GET", "/items", params={"page": "1"})
    assert request.url.params["q"] == "client"
    assert request.url.params["page"] == "1"
    assert "q=client" in str(request.url)
    assert request.headers["x-one"] == "1"
    assert request.headers["cookie"] == "a=b"


def test_response_read_bytes_match_content_and_text_cache():
    response = httpx.Response(200, stream=httpx.ByteStream("caf\xc3\xa9".encode()), default_encoding="utf-8")
    data = response.read()
    assert data == response.content
    assert response.text == "caf\xc3\xa9".encode().decode("utf-8")


def test_mocked_sync_workflow_with_hooks_redirects_and_json():
    events = []

    def app(request):
        if request.url.path == "/start":
            return httpx.Response(302, headers={"Location": "/end"}, request=request)
        return httpx.Response(200, json={"path": request.url.path, "trace": request.headers["x-trace"]}, request=request)

    def add_header(request):
        request.headers["X-Trace"] = "1"
        events.append(("request", str(request.url)))

    def remember_response(response):
        events.append(("response", response.status_code))

    with httpx.Client(
        base_url="https://example.org",
        params={"client": "yes"},
        headers={"User-Agent": "demo"},
        transport=httpx.MockTransport(app),
        event_hooks={"request": [add_header], "response": [remember_response]},
        follow_redirects=True,
    ) as client:
        request = client.build_request("GET", "/start", params={"request": "yes"})
        response = client.send(request)

    assert response.status_code == 200
    assert response.history[0].status_code == 302
    assert response.json() == {"path": "/end", "trace": "1"}
    assert [item[0] for item in events] == ["request", "response", "request", "response"]


def test_mocked_sync_workflow_handler_exception_propagates():
    def app(request):
        raise RuntimeError("boom")

    client = httpx.Client(transport=httpx.MockTransport(app))
    with pytest.raises(RuntimeError):
        client.get("https://example.org/")


def test_mocked_sync_workflow_preserves_client_params_into_redirect():
    def app(request):
        if request.url.path == "/start":
            assert request.url.params["client"] == "yes"
            return httpx.Response(302, headers={"Location": "/end"}, request=request)
        return httpx.Response(200, json={"query": str(request.url.query, "ascii")}, request=request)

    client = httpx.Client(
        base_url="https://example.org",
        params={"client": "yes"},
        transport=httpx.MockTransport(app),
        follow_redirects=True,
    )
    response = client.get("/start")
    assert response.history[0].request.url.params["client"] == "yes"
    assert response.json() == {"query": ""}


def test_async_asgi_representative_workflow():
    async def app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"text/plain")]})
        await send({"type": "http.response.body", "body": scope["path"].encode()})

    async def run():
        transport = httpx.ASGITransport(app=app, root_path="/api")
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver/api") as client:
            response = await client.get("/items")
        assert response.text == "/api/items"

    asyncio.run(run())


def test_async_asgi_representative_workflow_exception_propagates():
    async def app(scope, receive, send):
        raise RuntimeError("asgi boom")

    async def run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            with pytest.raises(RuntimeError):
                await client.get("/")

    asyncio.run(run())


def test_async_asgi_representative_workflow_can_return_error_response_when_configured():
    async def app(scope, receive, send):
        await send({"type": "http.response.start", "status": 500, "headers": [(b"content-type", b"text/plain")]})
        await send({"type": "http.response.body", "body": b"error"})
        raise RuntimeError("after response")

    async def run():
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/")
        assert response.status_code == 500
        assert response.text == "error"

    asyncio.run(run())


def test_cli_help_exits_successfully():
    from click.testing import CliRunner

    result = CliRunner().invoke(httpx.main, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_cli_rejects_invalid_json_before_request():
    from click.testing import CliRunner

    result = CliRunner().invoke(httpx.main, ["https://example.org/", "--json", "{"])
    assert result.exit_code == 2
    assert isinstance(result.exception, SystemExit)


def test_cli_requires_url_argument_before_request():
    from click.testing import CliRunner

    result = CliRunner().invoke(httpx.main, [])
    assert result.exit_code == 2
    assert isinstance(result.exception, SystemExit)
