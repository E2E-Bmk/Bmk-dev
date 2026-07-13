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


def test_client_reentering_open_context_raises():
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200)))
    with client:
        with pytest.raises(RuntimeError):
            with client:
                pass


def test_client_enter_after_close_raises():
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200)))
    client.close()
    with pytest.raises(RuntimeError):
        with client:
            pass


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


def test_base_url_relative_paths_resolve_under_base_path():
    client = httpx.Client(base_url="https://example.org/root/path/")
    assert str(client.build_request("GET", "child").url) == "https://example.org/root/path/child"
    assert str(client.build_request("GET", "../sibling").url) == "https://example.org/root/sibling"


def test_invalid_url_construction_raises_public_exception():
    with pytest.raises(httpx.InvalidURL):
        httpx.URL("http://example.org:abc").port


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


def test_headers_case_insensitive_lookup_and_duplicates():
    headers = httpx.Headers([("X-Thing", "one"), ("x-thing", "two"), ("Other", "ok")])
    assert headers["x-thing"] == "one, two"
    assert headers.get_list("X-THING") == ["one", "two"]
    assert ("x-thing", "one") in list(headers.multi_items())
    assert ("x-thing", "two") in list(headers.multi_items())


def test_headers_setting_replaces_all_existing_values():
    headers = httpx.Headers([("A", "1"), ("a", "2"), ("B", "3")])
    headers["a"] = "final"
    assert headers.get_list("A") == ["final"]
    assert headers["b"] == "3"
    del headers["A"]
    assert "a" not in headers


def test_headers_get_and_missing_key_behavior():
    headers = httpx.Headers({"Content-Type": "text/plain"})
    assert headers.get("content-type") == "text/plain"
    assert headers.get("missing", "fallback") == "fallback"
    with pytest.raises(KeyError):
        _ = headers["missing"]


def test_headers_split_commas_keeps_ordered_values():
    headers = httpx.Headers([("Accept", "text/html, application/json"), ("Accept", "text/plain")])
    assert headers.get_list("accept", split_commas=True) == ["text/html", "application/json", "text/plain"]


def test_invalid_header_value_is_rejected():
    with pytest.raises(TypeError):
        httpx.Request("GET", "https://example.org/", headers={"X-Bad": None})


def test_queryparams_lookup_lists_and_string_encoding():
    params = httpx.QueryParams([("a", "1"), ("a", "2"), ("space", "a b")])
    assert params["a"] == "1"
    assert params.get_list("a") == ["1", "2"]
    assert "space=a+b" in str(params)


def test_queryparams_set_add_remove_and_merge_are_immutable():
    params = httpx.QueryParams("a=1&a=2&b=3")
    changed = params.set("a", "final")
    added = changed.add("a", "again")
    removed = added.remove("b")
    merged = removed.merge({"c": "4", "a": "merged"})
    assert params.get_list("a") == ["1", "2"]
    assert changed.get_list("a") == ["final"]
    assert added.get_list("a") == ["final", "again"]
    assert "b" not in removed
    assert dict(merged) == {"a": "merged", "c": "4"}


def test_url_exposes_normalized_components():
    url = httpx.URL("https://user:pass@example.org:8443/a/b?x=1#frag")
    assert url.scheme == "https"
    assert url.username == "user"
    assert url.password == "pass"
    assert url.host == "example.org"
    assert url.port == 8443
    assert url.path == "/a/b"
    assert url.query == b"x=1"
    assert url.fragment == "frag"


def test_url_copy_and_param_helpers_return_new_urls():
    url = httpx.URL("https://example.org/path?a=1")
    assert str(url.copy_with(path="/other")) == "https://example.org/other?a=1"
    assert str(url.copy_set_param("a", "2")) == "https://example.org/path?a=2"
    assert str(url.copy_add_param("a", "3")) == "https://example.org/path?a=1&a=3"
    assert str(url.copy_remove_param("a")) == "https://example.org/path"
    assert str(url.copy_merge_params({"b": "4"})) == "https://example.org/path?a=1&b=4"
    assert str(url) == "https://example.org/path?a=1"


def test_url_join_resolves_relative_references():
    base = httpx.URL("https://example.org/a/b/c")
    assert str(base.join("../d?x=1")) == "https://example.org/a/d?x=1"


def test_cookies_set_get_delete_and_conflict():
    cookies = httpx.Cookies()
    cookies.set("sid", "one", domain="example.org", path="/")
    cookies.set("sid", "two", domain="api.example.org", path="/")
    assert cookies.get("sid", domain="example.org") == "one"
    with pytest.raises(httpx.CookieConflict):
        cookies.get("sid")
    cookies.delete("sid", domain="example.org", path="/")
    assert cookies.get("sid", domain="api.example.org") == "two"


def test_cookies_extract_and_send_matching_cookie_header():
    request = httpx.Request("GET", "https://example.org/login")
    response = httpx.Response(200, headers={"Set-Cookie": "sid=abc; Path=/"}, request=request)
    cookies = httpx.Cookies()
    cookies.extract_cookies(response)
    outgoing = httpx.Request("GET", "https://example.org/account")
    cookies.set_cookie_header(outgoing)
    assert outgoing.headers["cookie"] == "sid=abc"


def test_cookies_clear_removes_matching_domain_and_path():
    cookies = httpx.Cookies()
    cookies.set("sid", "one", domain="example.org", path="/")
    cookies.set("sid", "two", domain="api.example.org", path="/")
    cookies.clear(domain="example.org", path="/")
    assert cookies.get("sid", domain="example.org", default=None) is None
    assert cookies.get("sid", domain="api.example.org") == "two"


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


def test_request_model_adds_default_headers_and_content_length():
    request = httpx.Request("post", "https://example.org/submit", content=b"abc")
    assert request.method == "POST"
    assert request.url == httpx.URL("https://example.org/submit")
    assert request.headers["host"] == "example.org"
    assert request.headers["content-length"] == "3"
    assert request.content == b"abc"


def test_request_json_body_sets_content_type_and_bytes():
    request = httpx.Request("POST", "https://example.org/", json={"a": 1})
    assert request.headers["content-type"].startswith("application/json")
    assert json.loads(request.content.decode()) == {"a": 1}


def test_request_stream_content_requires_read_before_content_access():
    request = httpx.Request("POST", "https://example.org/", stream=httpx.ByteStream(b"abc"))
    with pytest.raises(httpx.RequestNotRead):
        _ = request.content
    assert request.read() == b"abc"
    assert request.content == b"abc"
    assert request.read() == b"abc"


def test_response_status_reason_http_version_and_url_projection():
    request = httpx.Request("GET", "https://example.org/")
    response = httpx.Response(201, request=request, extensions={"http_version": b"HTTP/2"})
    assert response.status_code == 201
    assert response.reason_phrase == "Created"
    assert response.http_version == "HTTP/2"
    assert response.url == request.url


def test_response_request_and_url_require_attached_request():
    response = httpx.Response(200)
    with pytest.raises(RuntimeError):
        _ = response.request
    with pytest.raises(RuntimeError):
        _ = response.url


def test_response_content_text_json_and_cookies():
    request = httpx.Request("GET", "https://example.org/")
    response = httpx.Response(200, json={"ok": True}, headers={"Set-Cookie": "a=b"}, request=request)
    assert response.content
    assert response.json() == {"ok": True}
    assert response.text == response.content.decode(response.encoding)
    assert response.cookies.get("a") == "b"


def test_response_links_are_parsed_by_relation():
    response = httpx.Response(200, headers={"Link": '<https://example.org/page/2>; rel="next"'})
    assert response.links["next"]["url"] == "https://example.org/page/2"


def test_raise_for_status_returns_self_for_success_and_raises_for_error():
    request = httpx.Request("GET", "https://example.org/")
    ok = httpx.Response(204, request=request)
    assert ok.raise_for_status() is ok
    error = httpx.Response(404, request=request)
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        error.raise_for_status()
    assert exc_info.value.request is request
    assert exc_info.value.response is error


def test_response_status_category_booleans():
    assert httpx.Response(101).is_informational is True
    assert httpx.Response(204).is_success is True
    assert httpx.Response(302).is_redirect is True
    assert httpx.Response(404).is_client_error is True
    assert httpx.Response(503).is_server_error is True
    assert httpx.Response(503).is_error is True


def test_response_has_redirect_location_requires_redirect_status_and_location():
    assert httpx.Response(302, headers={"Location": "/next"}).has_redirect_location is True
    assert httpx.Response(200, headers={"Location": "/next"}).has_redirect_location is False
    assert httpx.Response(302).has_redirect_location is False


def test_streamed_response_read_caches_content_and_closes_stream():
    response = httpx.Response(200, stream=httpx.ByteStream(b"hello"))
    with pytest.raises(httpx.ResponseNotRead):
        _ = response.text
    assert response.read() == b"hello"
    assert response.content == b"hello"
    assert response.is_closed is True


def test_iter_bytes_text_lines_and_raw_consume_streams():
    byte_response = httpx.Response(200, stream=httpx.ByteStream(b"ab"))
    assert list(byte_response.iter_bytes()) == [b"ab"]
    with pytest.raises(httpx.StreamConsumed):
        list(byte_response.iter_bytes())

    text_response = httpx.Response(200, stream=httpx.ByteStream("a\r\nb".encode()))
    assert list(text_response.iter_lines()) == ["a", "b"]

    raw_response = httpx.Response(200, stream=httpx.ByteStream(b"xyz"))
    assert list(raw_response.iter_raw()) == [b"xyz"]


def test_response_closed_before_read_raises_stream_closed():
    response = httpx.Response(200, stream=httpx.ByteStream(b"abc"))
    response.close()
    with pytest.raises(httpx.StreamClosed):
        response.read()


def test_num_bytes_downloaded_tracks_raw_stream_consumption():
    response = httpx.Response(200, stream=httpx.ByteStream(b"abcdef"))
    assert response.num_bytes_downloaded == 0
    assert list(response.iter_raw(chunk_size=2)) == [b"ab", b"cd", b"ef"]
    assert response.num_bytes_downloaded == 6


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


def test_too_many_redirects_raises_with_request():
    def handler(request):
        return httpx.Response(302, headers={"Location": "/loop"}, request=request)

    client = httpx.Client(base_url="https://example.org", max_redirects=1, transport=httpx.MockTransport(handler))
    with pytest.raises(httpx.TooManyRedirects) as exc_info:
        client.get("/loop", follow_redirects=True)
    assert exc_info.value.request.url.path == "/loop"


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


def test_client_event_hooks_property_can_be_mutated():
    client = httpx.Client()
    seen = []

    def hook(request):
        seen.append(str(request.url))

    client.event_hooks["request"].append(hook)
    request = client.build_request("GET", "https://example.org/")
    for registered in client.event_hooks["request"]:
        registered(request)
    assert seen == ["https://example.org/"]


def test_async_client_rejects_sync_hook_when_awaited():
    async def run():
        def sync_hook(request):
            return None

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(lambda request: httpx.Response(200, request=request)),
            event_hooks={"request": [sync_hook]},
        ) as client:
            with pytest.raises(TypeError):
                await client.get("https://example.org/")

    asyncio.run(run())


def test_basic_auth_tuple_sets_authorization_header():
    def handler(request):
        return httpx.Response(200, json={"auth": request.headers["authorization"]}, request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    response = client.get("https://example.org/", auth=("user", "pass"))
    assert response.json()["auth"].startswith("Basic ")


def test_callable_auth_mutates_prepared_request():
    def add_auth(request):
        request.headers["Authorization"] = "Token abc"
        return request

    def handler(request):
        return httpx.Response(200, text=request.headers["authorization"], request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    assert client.get("https://example.org/", auth=add_auth).text == "Token abc"


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


def test_base_transport_without_handle_request_raises_not_implemented():
    client = httpx.Client(transport=httpx.BaseTransport())
    with pytest.raises(NotImplementedError):
        client.get("https://example.org/")


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


def test_sync_client_with_async_transport_raises_capability_error():
    client = httpx.Client(transport=httpx.AsyncBaseTransport())
    assert client.is_closed is False
    with pytest.raises(Exception):
        client.get("https://example.org/")


def test_public_exception_hierarchy_and_request_attribute():
    request = httpx.Request("GET", "https://example.org/")
    error = httpx.RequestError("problem", request=request)
    assert isinstance(error, httpx.HTTPError)
    assert error.request is request

    unattached = httpx.RequestError("problem")
    with pytest.raises(RuntimeError):
        _ = unattached.request


def test_stream_state_exceptions_are_public_stream_errors():
    assert issubclass(httpx.StreamConsumed, httpx.StreamError)
    assert issubclass(httpx.StreamClosed, httpx.StreamError)
    assert issubclass(httpx.ResponseNotRead, httpx.StreamError)
    assert issubclass(httpx.RequestNotRead, httpx.StreamError)
    response = httpx.Response(200, stream=httpx.ByteStream(b"state"))
    with pytest.raises(httpx.ResponseNotRead):
        _ = response.content


def test_unsupported_protocol_raises_request_error_subclass():
    client = httpx.Client()
    with pytest.raises(httpx.UnsupportedProtocol):
        client.get("ftp://example.org/")


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
