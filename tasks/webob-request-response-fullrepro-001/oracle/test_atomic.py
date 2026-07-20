import datetime as _datetime
import json
import socket

import pytest

from webob import (
    Request,
    Response,
    UTC,
    day,
    hour,
    html_escape,
    minute,
    month,
    parse_date,
    second,
    serialize_date,
    timedelta_to_seconds,
    week,
    year,
)
from webob import exc as webob_exc
from webob.acceptparse import (
    create_accept_header,
    create_accept_language_header,
)
from webob.byterange import ContentRange, Range
from webob.cachecontrol import CacheControl
from webob.client import SendRequest
from webob.cookies import (
    Base64Serializer,
    CookieProfile,
    JSONSerializer,
    SignedSerializer,
    make_cookie,
)
from webob.dec import wsgify
from webob.etag import AnyETag, ETagMatcher, IfRange, NoETag
from webob.headers import EnvironHeaders, ResponseHeaders
from webob.multidict import MultiDict, NestedMultiDict, NoVars
from webob.static import DirectoryApp, FileApp


def _start_response(status, headers, exc_info=None):
    _start_response.status = status
    _start_response.headers = headers


def test_public_request_blank_url_projection():
    req = Request.blank("/item/42?name=webob", base_url="https://example.com/root")
    assert req.scheme == "https"
    assert req.host == "example.com:443"
    assert req.host_port == "443"
    assert req.host_url == "https://example.com"
    assert req.script_name == "/root"
    assert req.path_info == "/item/42"
    assert req.query_string == "name=webob"
    assert req.params["name"] == "webob"


def test_public_request_headers_and_cookies_views():
    req = Request.blank("/x", headers={"Cookie": "a=1; b=two", "X-Trace": "abc"})
    assert req.headers["X-Trace"] == "abc"
    assert req.cookies["a"] == "1"
    req.cookies = {"session": "fresh"}
    assert "session=fresh" in req.headers["Cookie"]


def test_public_request_copy_get_resets_body_state():
    req = Request.blank("/submit", method="POST", body=b"payload")
    copied = req.copy_get()
    assert copied.method == "GET"
    assert copied.body == b""
    assert copied.content_type == ""


def test_public_response_defaults_and_body_views():
    res = Response()
    assert res.status == "200 OK"
    assert res.content_type == "text/html"
    assert res.charset == "UTF-8"
    assert res.content_length == 0
    assert res.body == b""


def test_public_response_json_round_trip_sets_body():
    res = Response()
    res.json = {"answer": 42}
    assert json.loads(res.body.decode(res.charset)) == {"answer": 42}
    assert res.json == {"answer": 42}


def test_public_response_copy_is_independent():
    res = Response(text="first", content_type="text/plain")
    copied = res.copy()
    copied.text = "second"
    assert res.text == "first"
    assert copied.text == "second"


def test_multidict_duplicate_lookup_and_getall_order():
    md = MultiDict([("a", "1"), ("a", "2"), ("b", "3")])
    assert md["a"] == "2"
    assert md.getall("a") == ["1", "2"]
    assert list(md.keys()) == ["a", "a", "b"]


def test_multidict_setitem_replaces_existing_values():
    md = MultiDict([("a", "1"), ("a", "2")])
    md["a"] = "3"
    assert md.getall("a") == ["3"]


def test_nested_multidict_reads_first_child_and_all_values():
    first = MultiDict([("x", "query")])
    second = MultiDict([("x", "form"), ("y", "body")])
    nested = NestedMultiDict(first, second)
    assert nested["x"] == "query"
    assert nested.getall("x") == ["query", "form"]
    assert nested["y"] == "body"


def test_novars_empty_readonly_mapping():
    nv = NoVars("not a form request")
    assert nv.get("missing", "fallback") == "fallback"
    assert nv.getall("missing") == []
    with pytest.raises(KeyError):
        nv["x"] = "y"


def test_responseheaders_case_insensitive_updates_headerlist():
    res = Response()
    view = res.headers
    view["x-test"] = "two"
    view.add("X-Test", "three")
    assert res.headerlist[-2:] == [("x-test", "two"), ("X-Test", "three")]
    assert view.getall("X-TEST") == ["two", "three"]


def test_environheaders_maps_http_and_content_keys():
    environ = {"CONTENT_TYPE": "text/plain", "HTTP_X_TOKEN": "abc"}
    view = EnvironHeaders(environ)
    assert view["Content-Type"] == "text/plain"
    assert view["X-Token"] == "abc"
    with pytest.raises(KeyError):
        view["Missing"]


def test_make_cookie_accepts_samesite_and_httponly():
    header = make_cookie("sid", "abc", max_age=60, httponly=True, samesite="lax")
    assert header.startswith("sid=abc")
    assert "Max-Age=60" in header
    assert "HttpOnly" in header
    assert "SameSite=lax" in header


def test_make_cookie_none_value_expires_client_cookie():
    header = make_cookie("sid", None)
    assert header.startswith("sid=")
    assert "expires=" in header.lower()


def test_json_and_base64_serializers_round_trip_bytes():
    serializer = Base64Serializer(JSONSerializer())
    payload = serializer.dumps({"name": "webob"})
    assert isinstance(payload, bytes)
    assert serializer.loads(payload) == {"name": "webob"}


def test_signed_serializer_round_trip_and_tamper_failure():
    serializer = SignedSerializer("secret", "salt")
    payload = serializer.dumps({"ok": True})
    assert serializer.loads(payload) == {"ok": True}
    with pytest.raises(ValueError):
        serializer.loads(payload[:-1] + b"x")


def test_cookie_profile_generates_one_header_per_domain():
    profile = CookieProfile("pref", domains=["example.com", "www.example.com"])
    headers = profile.get_headers({"theme": "light"})
    assert [name for name, value in headers] == ["Set-Cookie", "Set-Cookie"]
    assert any("Domain=example.com" in value for name, value in headers)
    assert any("Domain=www.example.com" in value for name, value in headers)


def test_accept_header_best_match_and_quality():
    accept = create_accept_header("text/html;q=0.5, application/json")
    assert accept.best_match(["text/html", "application/json"]) == "application/json"
    assert accept.quality("text/html") == pytest.approx(0.5)


def test_accept_missing_header_allows_offers():
    accept = create_accept_header(None)
    assert accept.best_match(["text/plain"]) == "text/plain"
    assert "text/plain" in accept


def test_accept_language_lookup_and_default_match():
    accept = create_accept_language_header("en-US,en;q=0.8")
    assert accept.lookup(["fr", "en-us"], default="fallback") == "en-us"
    assert accept.best_match(["fr"], default_match="fr") == "fr"


def test_cachecontrol_parse_and_mutation_rewrites_header():
    cc = CacheControl.parse("max-age=10, no-cache", type="response")
    assert cc.max_age == 10
    assert cc.no_cache
    cc.no_store = True
    assert cc.no_store is True

    res = Response(headerlist=[("Cache-Control", "max-age=10, no-cache")])
    res.cache_control.no_store = True
    directives = {part.strip() for part in res.headers["Cache-Control"].split(",")}
    assert {"max-age=10", "no-cache", "no-store"} <= directives


def test_range_parse_and_content_range_conversion():
    rng = Range.parse("bytes=1-3")
    assert (rng.start, rng.end) == (1, 4)
    content = rng.content_range(6)
    assert str(content) == "bytes 1-3/6"


def test_contentrange_parse_valid_and_invalid_inputs():
    parsed = ContentRange.parse("bytes 2-5/10")
    assert (parsed.start, parsed.stop, parsed.length) == (2, 6, 10)
    assert ContentRange.parse("not-a-range") is None


def test_etag_matcher_sentinels_and_weak_parsing():
    matcher = ETagMatcher.parse('"abc", W/"weak"', strong=True)
    assert "abc" in matcher
    assert "weak" not in matcher
    assert "anything" in AnyETag
    assert "anything" not in NoETag


def test_ifrange_empty_input_matches_any_etag():
    parsed = IfRange.parse(None)
    assert parsed.etag is not None
    assert "any-tag" in parsed.etag


def test_http_exception_status_map_exposes_public_classes():
    assert webob_exc.status_map[404] is webob_exc.HTTPNotFound
    assert issubclass(webob_exc.HTTPForbidden, webob_exc.HTTPClientError)


def test_http_exception_json_response_uses_accept_header():
    req = Request.blank("/", headers={"Accept": "application/json"})
    response = req.get_response(webob_exc.HTTPForbidden(detail="denied"))
    assert response.status_int == 403
    assert response.content_type == "application/json"
    assert json.loads(response.body.decode("utf-8"))["code"] == "403 Forbidden"


def test_http_not_modified_emits_no_body_for_wsgi_call():
    req = Request.blank("/")
    body = b"".join(webob_exc.HTTPNotModified()(req.environ, _start_response))
    assert _start_response.status.startswith("304")
    assert body == b""


def test_directoryapp_requires_existing_directory(tmp_path):
    with pytest.raises(OSError):
        DirectoryApp(str(tmp_path / "missing"))


def test_sendrequest_rejects_unknown_scheme():
    sender = SendRequest()
    environ = Request.blank("/resource").environ
    environ["wsgi.url_scheme"] = "ftp"
    with pytest.raises(ValueError):
        sender(environ, _start_response)


def test_datetime_helpers_constants_and_utc_offset():
    assert UTC.utcoffset(None) == _datetime.timedelta(0)
    assert timedelta_to_seconds(day) == 24 * 60 * 60
    assert week == 7 * day
    assert hour == 60 * minute
    assert minute == 60 * second
    assert month == 30 * day
    assert year == 365 * day


def test_datetime_serialize_and_parse_round_trip():
    dt = _datetime.datetime(2020, 1, 2, 3, 4, 5, tzinfo=UTC)
    serialized = serialize_date(dt)
    parsed = parse_date(serialized)
    assert parsed == dt


def test_html_escape_handles_none_html_protocol_and_text():
    class Htmlish:
        def __html__(self):
            return "<b>safe</b>"

    assert html_escape(None) == ""
    assert html_escape(Htmlish()) == "<b>safe</b>"
    assert html_escape("<tag>") == "&lt;tag&gt;"


def test_request_path_info_peek_and_pop_mutate_script_name():
    req = Request.blank("/api/v1/items")
    assert req.path_info_peek() == "api"
    assert req.path_info_pop() == "api"
    assert req.script_name == "/api"
    assert req.path_info == "/v1/items"
    assert req.path_info_pop("missing") is None


def test_request_body_assignment_updates_length_and_seekable_stream():
    req = Request.blank("/")
    req.body = b"abc"
    assert req.content_length == 3
    assert req.body_file_seekable.tell() == 0
    assert req.body_file_seekable.read() == b"abc"


def test_request_get_mutation_rewrites_query_string():
    req = Request.blank("/?a=1")
    req.GET.add("a", "2")
    assert req.environ["QUERY_STRING"] == "a=1&a=2"
    assert req.params.getall("a") == ["1", "2"]


def test_request_public_ad_hoc_attribute_is_environ_backed():
    environ = Request.blank("/").environ
    req = Request(environ)
    req.feature_flag = "on"
    assert Request(environ).feature_flag == "on"
    del req.feature_flag
    with pytest.raises(AttributeError):
        Request(environ).feature_flag


def test_request_remove_conditional_headers_respects_flags():
    req = Request.blank(
        "/",
        headers={
            "If-None-Match": '"abc"',
            "If-Modified-Since": "Wed, 21 Oct 2015 07:28:00 GMT",
            "Range": "bytes=1-3",
            "Accept-Encoding": "gzip",
        },
    )
    req.remove_conditional_headers(remove_range=False, remove_encoding=False)
    assert "If-None-Match" not in req.headers
    assert "If-Modified-Since" not in req.headers
    assert req.headers["Range"] == "bytes=1-3"
    assert req.headers["Accept-Encoding"] == "gzip"


def test_request_call_application_and_get_response_agree():
    def app(environ, start_response):
        start_response("201 Created", [("X-App", "yes")])
        return [b"created"]

    req = Request.blank("/create")
    status, headers, app_iter = req.call_application(app)
    response = req.get_response(app)
    assert status == response.status
    assert dict(headers)["X-App"] == response.headers["X-App"]
    assert b"".join(app_iter) == response.body


def test_response_headerlist_replacement_resets_headers_view():
    res = Response()
    res.headers["X-One"] = "1"
    assert ("X-One", "1") in res.headerlist
    res.headerlist = [("X-Two", "2")]
    assert "X-One" not in res.headers
    assert res.headers["X-Two"] == "2"


def test_response_body_and_app_iter_keep_length_in_sync():
    res = Response()
    res.body = b"abcdef"
    assert list(res.app_iter) == [b"abcdef"]
    assert res.content_length == 6
    res.app_iter = [b"xy"]
    assert res.content_length is None
    assert res.body == b"xy"


def test_response_content_type_charset_and_params_sync():
    res = Response(content_type="text/plain")
    res.charset = "utf-8"
    res.content_type_params = {"charset": "utf-8", "format": "flowed"}
    assert res.content_type == "text/plain"
    assert res.content_type_params["charset"] == "utf-8"
    assert res.content_type_params["format"] == "flowed"
    header_parts = {part.strip() for part in res.headers["Content-Type"].split(";")}
    assert {"text/plain", "charset=utf-8", "format=flowed"} <= header_parts


def test_response_cache_expires_updates_cache_headers():
    res = Response()
    res.cache_expires(0)
    assert res.cache_control.no_cache
    assert res.cache_control.no_store is True
    assert res.pragma == "no-cache"
    res.cache_expires(60)
    assert res.cache_control.max_age == 60
    assert res.pragma is None


def test_response_encode_and_decode_gzip_body():
    res = Response(body=b"compress me")
    res.encode_content("gzip")
    assert res.content_encoding == "gzip"
    assert res.body != b"compress me"
    res.decode_content()
    assert res.content_encoding is None
    assert res.body == b"compress me"


def test_response_conditional_range_request_returns_partial_content():
    res = Response(body=b"abcdef", conditional_response=True, etag="tag")
    req = Request.blank("/", headers={"Range": "bytes=1-3"})
    response = req.get_response(res)
    assert response.status_int == 206
    assert response.content_range.start == 1
    assert response.content_range.stop == 4
    assert response.body == b"bcd"


def test_error_request_blank_base_url_rejects_query_or_fragment():
    with pytest.raises(ValueError):
        Request.blank("/x", base_url="http://example.com/root?bad=1")
    with pytest.raises(ValueError):
        Request.blank("/x", base_url="http://example.com/root#frag")


def test_error_response_body_rejects_text_values():
    res = Response()
    with pytest.raises(TypeError):
        res.body = "not bytes"


def test_error_multidict_getone_duplicate_raises_keyerror():
    md = MultiDict([("a", "1"), ("a", "2")])
    with pytest.raises(KeyError):
        md.getone("a")


def test_error_content_range_invalid_triple_raises_valueerror():
    with pytest.raises(ValueError):
        ContentRange(5, 2, 10)


def test_error_cookie_profile_unbound_get_value_raises():
    profile = CookieProfile("session")
    with pytest.raises(ValueError):
        profile.get_value()


def test_error_redirect_rejects_newline_in_location():
    with pytest.raises(ValueError):
        webob_exc.HTTPFound(location="http://example.com/\nnext")


