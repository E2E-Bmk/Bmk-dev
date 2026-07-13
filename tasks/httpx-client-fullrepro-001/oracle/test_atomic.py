# Spec2Repo oracle - atomic tests for httpx-client-fullrepro-001
import asyncio
import json

import pytest

import httpx


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


def test_base_url_relative_paths_resolve_under_base_path():
    client = httpx.Client(base_url="https://example.org/root/path/")
    assert str(client.build_request("GET", "child").url) == "https://example.org/root/path/child"
    assert str(client.build_request("GET", "../sibling").url) == "https://example.org/root/sibling"


def test_invalid_url_construction_raises_public_exception():
    with pytest.raises(httpx.InvalidURL):
        httpx.URL("http://example.org:abc").port


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


def test_cookies_clear_removes_matching_domain_and_path():
    cookies = httpx.Cookies()
    cookies.set("sid", "one", domain="example.org", path="/")
    cookies.set("sid", "two", domain="api.example.org", path="/")
    cookies.clear(domain="example.org", path="/")
    assert cookies.get("sid", domain="example.org", default=None) is None
    assert cookies.get("sid", domain="api.example.org") == "two"


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


def test_too_many_redirects_raises_with_request():
    def handler(request):
        return httpx.Response(302, headers={"Location": "/loop"}, request=request)

    client = httpx.Client(base_url="https://example.org", max_redirects=1, transport=httpx.MockTransport(handler))
    with pytest.raises(httpx.TooManyRedirects) as exc_info:
        client.get("/loop", follow_redirects=True)
    assert exc_info.value.request.url.path == "/loop"


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


def test_base_transport_without_handle_request_raises_not_implemented():
    client = httpx.Client(transport=httpx.BaseTransport())
    with pytest.raises(NotImplementedError):
        client.get("https://example.org/")


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
