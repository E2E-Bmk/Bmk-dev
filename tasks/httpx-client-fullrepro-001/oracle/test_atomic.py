"""Atomic tests for httpx-client-fullrepro-001.

Each test exercises ONE public API entry point with ONE behavior.
"""
from __future__ import annotations

import json

import pytest

import httpx


# =============================================================================
# Headers
# =============================================================================


def test_headers_case_insensitive_lookup():
    h = httpx.Headers([("Content-Type", "text/html"), ("x-id", "42")])
    assert h["content-type"] == "text/html"
    assert h["X-ID"] == "42"


def test_headers_get_list_returns_all_values():
    h = httpx.Headers([("Accept", "text/html"), ("accept", "application/json")])
    assert h.get_list("ACCEPT") == ["text/html", "application/json"]


def test_headers_combined_value_for_duplicates():
    h = httpx.Headers([("X-Tag", "a"), ("x-tag", "b")])
    assert h["x-tag"] == "a, b"


def test_headers_split_commas():
    h = httpx.Headers([("Accept", "text/html, text/plain"), ("Accept", "application/xml")])
    assert h.get_list("accept", split_commas=True) == ["text/html", "text/plain", "application/xml"]


def test_headers_set_replaces_all_existing():
    h = httpx.Headers([("X-A", "1"), ("x-a", "2"), ("X-B", "3")])
    h["x-a"] = "final"
    assert h.get_list("X-A") == ["final"]


def test_headers_delete_removes_all():
    h = httpx.Headers([("X-A", "1"), ("x-a", "2")])
    del h["X-A"]
    assert "x-a" not in h


def test_headers_missing_key_raises():
    h = httpx.Headers({"Only": "one"})
    with pytest.raises(KeyError):
        _ = h["missing"]
    assert h.get("missing", "fallback") == "fallback"


def test_headers_multi_items_preserves_all_pairs():
    h = httpx.Headers([("A", "1"), ("a", "2"), ("B", "3")])
    items = list(h.multi_items())
    assert ("a", "1") in items
    assert ("a", "2") in items


# =============================================================================
# QueryParams
# =============================================================================


def test_queryparams_lookup_returns_first_value():
    qp = httpx.QueryParams([("k", "one"), ("k", "two")])
    assert qp["k"] == "one"
    assert qp.get_list("k") == ["one", "two"]


def test_queryparams_set_replaces_all():
    qp = httpx.QueryParams("k=1&k=2&x=3")
    new = qp.set("k", "final")
    assert new.get_list("k") == ["final"]
    assert qp.get_list("k") == ["1", "2"]


def test_queryparams_add_appends():
    qp = httpx.QueryParams("k=1")
    new = qp.add("k", "2")
    assert new.get_list("k") == ["1", "2"]


def test_queryparams_remove_deletes_key():
    qp = httpx.QueryParams("a=1&b=2")
    new = qp.remove("a")
    assert "a" not in new


def test_queryparams_merge_replaces_existing_keys():
    qp = httpx.QueryParams("a=1&b=2")
    new = qp.merge({"a": "new", "c": "3"})
    assert new["a"] == "new"
    assert new["b"] == "2"
    assert new["c"] == "3"


# =============================================================================
# URL
# =============================================================================


def test_url_parses_all_components():
    url = httpx.URL("https://user:pw@host.test:9443/path?q=1#frag")
    assert url.scheme == "https"
    assert url.username == "user"
    assert url.password == "pw"
    assert url.host == "host.test"
    assert url.port == 9443
    assert url.path == "/path"
    assert url.fragment == "frag"


def test_url_copy_with_returns_new_url():
    url = httpx.URL("https://host.test/a?x=1")
    new = url.copy_with(path="/b")
    assert str(new) == "https://host.test/b?x=1"
    assert str(url) == "https://host.test/a?x=1"


def test_url_param_helpers():
    url = httpx.URL("https://host.test/p?a=1")
    assert "a=2" in str(url.copy_set_param("a", "2"))
    assert "a=1&a=2" in str(url.copy_add_param("a", "2"))
    assert "a=" not in str(url.copy_remove_param("a"))


def test_url_join_resolves_relative():
    base = httpx.URL("https://host.test/a/b/c")
    assert str(base.join("../d")) == "https://host.test/a/d"


def test_invalid_url_raises():
    with pytest.raises(httpx.InvalidURL):
        httpx.URL("http://host.test:abc").port


# =============================================================================
# Cookies
# =============================================================================


def test_cookies_set_get_delete():
    c = httpx.Cookies()
    c.set("sid", "val1", domain="a.test", path="/")
    assert c.get("sid", domain="a.test") == "val1"
    c.delete("sid", domain="a.test", path="/")
    assert c.get("sid", domain="a.test", default=None) is None


def test_cookies_conflict_on_ambiguous_get():
    c = httpx.Cookies()
    c.set("tok", "one", domain="a.test")
    c.set("tok", "two", domain="b.test")
    with pytest.raises(httpx.CookieConflict):
        c.get("tok")


def test_cookies_clear_by_domain():
    c = httpx.Cookies()
    c.set("a", "1", domain="x.test", path="/")
    c.set("a", "2", domain="y.test", path="/")
    c.clear(domain="x.test", path="/")
    assert c.get("a", domain="x.test", default=None) is None
    assert c.get("a", domain="y.test") == "2"


# =============================================================================
# Request model
# =============================================================================


def test_request_normalizes_method_to_uppercase():
    req = httpx.Request("post", "https://host.test/")
    assert req.method == "POST"


def test_request_sets_host_and_content_length():
    req = httpx.Request("PUT", "https://host.test/item", content=b"body")
    assert req.headers["host"] == "host.test"
    assert req.headers["content-length"] == "4"


def test_request_json_body_sets_content_type():
    req = httpx.Request("POST", "https://host.test/", json={"x": 1})
    assert "application/json" in req.headers["content-type"]
    assert json.loads(req.content) == {"x": 1}


def test_request_stream_requires_read():
    req = httpx.Request("POST", "https://host.test/", stream=httpx.ByteStream(b"data"))
    with pytest.raises(httpx.RequestNotRead):
        _ = req.content
    assert req.read() == b"data"
    assert req.content == b"data"


# =============================================================================
# Response model
# =============================================================================


def test_response_status_and_reason():
    resp = httpx.Response(201)
    assert resp.status_code == 201
    assert resp.reason_phrase == "Created"


def test_response_json_and_text():
    resp = httpx.Response(200, json={"ok": True})
    assert resp.json() == {"ok": True}
    assert resp.text


def test_response_request_required():
    resp = httpx.Response(200)
    with pytest.raises(RuntimeError):
        _ = resp.request
    with pytest.raises(RuntimeError):
        _ = resp.url


def test_response_status_booleans():
    assert httpx.Response(100).is_informational is True
    assert httpx.Response(200).is_success is True
    assert httpx.Response(301).is_redirect is True
    assert httpx.Response(400).is_client_error is True
    assert httpx.Response(500).is_server_error is True
    assert httpx.Response(500).is_error is True


def test_response_has_redirect_location():
    assert httpx.Response(302, headers={"Location": "/x"}).has_redirect_location is True
    assert httpx.Response(200, headers={"Location": "/x"}).has_redirect_location is False
    assert httpx.Response(302).has_redirect_location is False


def test_raise_for_status_returns_self_for_2xx():
    req = httpx.Request("GET", "https://host.test/")
    ok = httpx.Response(204, request=req)
    assert ok.raise_for_status() is ok


def test_raise_for_status_raises_for_4xx():
    req = httpx.Request("GET", "https://host.test/")
    err = httpx.Response(404, request=req)
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        err.raise_for_status()
    assert exc_info.value.request is req
    assert exc_info.value.response is err


def test_response_links_parsed():
    resp = httpx.Response(200, headers={"Link": '<https://api.test/p2>; rel="next"'})
    assert resp.links["next"]["url"] == "https://api.test/p2"


def test_response_cookies_from_set_cookie():
    req = httpx.Request("GET", "https://host.test/")
    resp = httpx.Response(200, headers={"Set-Cookie": "sid=xyz"}, request=req)
    assert resp.cookies.get("sid") == "xyz"


# =============================================================================
# Streaming and read state
# =============================================================================


def test_streamed_response_requires_read():
    resp = httpx.Response(200, stream=httpx.ByteStream(b"lazy"))
    with pytest.raises(httpx.ResponseNotRead):
        _ = resp.text
    assert resp.read() == b"lazy"
    assert resp.content == b"lazy"


def test_iter_bytes_consumes_stream():
    resp = httpx.Response(200, stream=httpx.ByteStream(b"chunk"))
    assert list(resp.iter_bytes()) == [b"chunk"]
    with pytest.raises(httpx.StreamConsumed):
        list(resp.iter_bytes())


def test_closed_response_raises_stream_closed():
    resp = httpx.Response(200, stream=httpx.ByteStream(b"x"))
    resp.close()
    with pytest.raises(httpx.StreamClosed):
        resp.read()


def test_num_bytes_downloaded_tracks_raw():
    resp = httpx.Response(200, stream=httpx.ByteStream(b"abcdef"))
    list(resp.iter_raw())
    assert resp.num_bytes_downloaded == 6


# =============================================================================
# Exception hierarchy
# =============================================================================


def test_exception_hierarchy():
    assert issubclass(httpx.RequestError, httpx.HTTPError)
    assert issubclass(httpx.HTTPStatusError, httpx.HTTPError)
    assert issubclass(httpx.StreamConsumed, httpx.StreamError)
    assert issubclass(httpx.StreamClosed, httpx.StreamError)


def test_request_error_without_request_raises():
    err = httpx.RequestError("problem")
    with pytest.raises(RuntimeError):
        _ = err.request
