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


from conftest import _start_response


def test_public_request_get_response_uses_response_class():
    """Seam: protocol handoff from Request through WSGI app to Response."""
    def app(environ, start_response):
        res = Response(text="ok", content_type="text/plain")
        return res(environ, start_response)

    res = Request.blank("/status").get_response(app)
    assert res.status_int == 200
    assert res.text == "ok"
    assert res.content_type == "text/plain"


def test_public_response_wsgi_call_emits_status_headers_and_body():
    """Seam: protocol handoff from Response WSGI call to status, headers, and body."""
    res = Response(text="hello", content_type="text/plain")
    body = b"".join(res(Request.blank("/").environ, _start_response))
    assert _start_response.status == "200 OK"
    assert ("Content-Type", "text/plain; charset=UTF-8") in _start_response.headers
    assert body == b"hello"


def test_fileapp_serves_file_with_static_response_headers(tmp_path):
    """Seam: lifecycle crossing from filesystem file to HTTP response."""
    target = tmp_path / "hello.txt"
    target.write_bytes(b"hello file")
    response = Request.blank("/hello.txt").get_response(FileApp(str(target)))
    assert response.status_int == 200
    assert response.body == b"hello file"
    assert response.headers["Accept-Ranges"] == "bytes"


def test_wsgify_converts_string_return_to_response_body():
    """Seam: protocol handoff from wsgify decorator return value to response body."""
    @wsgify
    def app(req):
        return "decorated"

    response = Request.blank("/").get_response(app)
    assert response.status_int == 200
    assert response.text == "decorated"


def test_exception_middleware_catches_initial_http_exception():
    """Seam: error propagation from raised HTTP exception to middleware response."""
    def app(environ, start_response):
        raise webob_exc.HTTPForbidden()

    body = b"".join(webob_exc.HTTPExceptionMiddleware(app)(Request.blank("/").environ, _start_response))
    assert _start_response.status.startswith("403")
    assert body


def test_wsgify_preserves_undecorated_and_method_binding():
    """Seam: lifecycle crossing through wsgify decoration and method binding."""
    class Controller:
        @wsgify
        def app(self, req):
            return Response(text=req.path_info)

    controller = Controller()
    assert controller.app.undecorated.__name__ == "app"
    assert Request.blank("/bound").get_response(controller.app).text == "/bound"


def test_wsgi_head_request_preserves_headers_without_body():
    """Seam: state consistency between HEAD response headers and suppressed body."""
    res = Response(text="has body", content_type="text/plain")
    req = Request.blank("/", method="HEAD")
    body = b"".join(res(req.environ, _start_response))
    assert _start_response.status == "200 OK"
    assert body == b""
    assert any(name == "Content-Length" for name, value in _start_response.headers)


def test_cross_request_header_content_type_environ_sync():
    """Seam: state consistency between request headers and environ CONTENT_TYPE."""
    req = Request.blank("/")
    req.headers["Content-Type"] = "application/json"
    assert req.environ["CONTENT_TYPE"] == "application/json"
    req.content_type = "text/plain"
    assert req.headers["Content-Type"] == "text/plain"
    del req.environ["CONTENT_TYPE"]
    with pytest.raises(KeyError):
        req.headers["Content-Type"]


def test_cross_request_get_mutation_precedes_form_values():
    """Seam: state consistency between GET params and POST form values."""
    req = Request.blank("/?name=Query", method="POST")
    req.content_type = "application/x-www-form-urlencoded"
    req.body = b"name=Post"
    assert req.params["name"] == "Query"
    assert req.params.getall("name") == ["Query", "Post"]
    req.GET.add("extra", "Later")
    assert req.environ["QUERY_STRING"].endswith("extra=Later")


def test_cross_request_body_assignment_replaces_raw_stream():
    """Seam: state consistency when body assignment replaces raw stream."""
    req = Request.blank("/")
    original = req.body_file_raw
    req.body = b"new"
    assert req.body_file_raw is not original
    assert req.content_length == 3
    assert req.body == b"new"


def test_cross_response_headers_and_headerlist_are_same_state():
    """Seam: state consistency between response headers dict and headerlist."""
    res = Response()
    res.headers["X-State"] = "headers"
    assert ("X-State", "headers") in res.headerlist
    res.headerlist = [("X-State", "list")]
    assert res.headers["X-State"] == "list"


def test_cross_response_content_type_views_share_one_header():
    """Seam: state consistency across content_type, charset, and params views."""
    res = Response(content_type="text/plain")
    res.charset = "utf-8"
    assert "charset=utf-8" in res.headers["Content-Type"]
    res.content_type_params = {"charset": "utf-8", "level": "1"}
    assert res.content_type_params["level"] == "1"


def test_cross_range_request_assignable_to_response_content_range():
    """Seam: state consistency from Range request to Content-Range response."""
    req = Request.blank("/", headers={"Range": "bytes=2-4"})
    res = Response(body=b"abcdef")
    res.content_range = req.range.content_range(res.content_length)
    assert str(res.content_range) == "bytes 2-4/6"


def test_cross_get_response_exposes_call_application_outputs():
    """Seam: protocol handoff from get_response to application start_response output."""
    def app(environ, start_response):
        start_response("202 Accepted", [("X-Trace", "yes")])
        return [b"accepted"]

    req = Request.blank("/work")
    response = req.get_response(app)
    assert response.status == "202 Accepted"
    assert response.headers["X-Trace"] == "yes"
    assert response.body == b"accepted"


def test_workflow_in_process_query_response_cookie():
    """Seam: lifecycle crossing from query params through app to Set-Cookie header."""
    def app(environ, start_response):
        req = Request(environ)
        res = Response(text="Hello, %s" % req.params.get("name", "world"), content_type="text/plain")
        res.set_cookie("seen", "yes", httponly=True)
        return res(environ, start_response)

    res = Request.blank("/hello?name=WebOb").get_response(app)
    assert res.status == "200 OK"
    assert res.text == "Hello, WebOb"
    assert "seen=yes" in res.headers["Set-Cookie"]


def test_workflow_in_process_request_body_to_response_json():
    """Seam: protocol handoff from request body to JSON response projection."""
    def app(environ, start_response):
        req = Request(environ)
        res = Response(json={"length": len(req.body), "path": req.path_info})
        return res(environ, start_response)

    res = Request.blank("/payload", method="POST", body=b"abcdef").get_response(app)
    assert res.json == {"length": 6, "path": "/payload"}


def test_workflow_in_process_conditional_response_slice():
    """Seam: protocol handoff from conditional Range request to partial response."""
    def app(environ, start_response):
        return Response(body=b"abcdef", conditional_response=True)(environ, start_response)

    req = Request.blank("/", headers={"Range": "bytes=0-2"})
    res = req.get_response(app)
    assert res.status_int == 206
    assert res.body == b"abc"


def test_workflow_decorated_application_success_response():
    """Seam: lifecycle crossing through decorated application to success response."""
    @wsgify
    def app(req):
        return Response(text="ok", content_type="text/plain")

    response = app.get("/status")
    assert response.status_int == 200
    assert response.text == "ok"


def test_workflow_decorated_application_http_exception_response():
    """Seam: error propagation from decorated app HTTP exception to response."""
    @wsgify
    def app(req):
        raise webob_exc.HTTPForbidden("GET required")

    response = Request.blank("/status").get_response(app)
    assert response.status_int == 403


def test_workflow_decorated_application_uses_default_response():
    """Seam: lifecycle crossing through default response mutation on request."""
    @wsgify
    def app(req):
        req.response.text = "from default"
        req.response.content_type = "text/plain"

    response = Request.blank("/default").get_response(app)
    assert response.status_int == 200
    assert response.text == "from default"


def test_client_socket_timeout_maps_to_gateway_timeout():
    """Seam: error propagation from socket timeout to gateway timeout response."""
    class TimeoutConnection:
        def __init__(self, *args, **kwargs):
            pass

        def request(self, *args, **kwargs):
            raise socket.timeout()

    sender = SendRequest(HTTPConnection=TimeoutConnection)
    environ = Request.blank("http://example.com/").environ
    response = Request(environ).get_response(sender)
    assert response.status_int == 504


def test_wsgify_middleware_passes_wrapped_app_and_chains_request_response():
    """Seam: protocol handoff through wsgify middleware chain. Verifies: wsgify.middleware must create middleware factories that pass the
    wrapped application as the first function argument before configured positional
    arguments, and the full chain produces a valid response through request/response
    interaction."""

    @wsgify.middleware
    def add_header(req, app, header_name, header_value):
        response = req.get_response(app)
        response.headers[header_name] = header_value
        return response

    @wsgify
    def inner_app(req):
        return Response(text="inner:" + req.path_info, content_type="text/plain")

    wrapped = add_header(inner_app, "X-Added", "middleware-value")

    response = Request.blank("/test-path").get_response(wrapped)
    assert response.status_int == 200
    assert response.text == "inner:/test-path"
    assert response.headers["X-Added"] == "middleware-value"


def test_cache_control_mutation_rewrites_request_and_response_headers():
    """Seam: state consistency between cache_control view and Cache-Control header. Verifies: Mutating req.cache_control or res.cache_control directive attributes
    must rewrite the corresponding Cache-Control header, and replacing the header
    string must make the next cache-control view reflect the new directives."""
    req = Request.blank("/")
    req.cache_control.max_age = 120
    req.cache_control.no_cache = True
    assert "max-age=120" in req.headers.get("Cache-Control", "")
    assert "no-cache" in req.headers.get("Cache-Control", "")

    res = Response()
    res.cache_control.max_age = 3600
    res.cache_control.public = True
    header = res.headers.get("Cache-Control", "")
    assert "max-age=3600" in header
    assert "public" in header
    assert res.cache_control.max_age == 3600

    res.headers["Cache-Control"] = "no-store"
    assert res.cache_control.no_store is True
    assert res.cache_control.max_age is None

def test_cachecontrol_parse_and_mutation_rewrites_header():
    """Seam: state consistency — CacheControl.parse and Response.cache_control rewrite header."""
    cc = CacheControl.parse("max-age=10, no-cache", type="response")
    assert cc.max_age == 10
    assert cc.no_cache
    cc.no_store = True
    assert cc.no_store is True

    res = Response(headerlist=[("Cache-Control", "max-age=10, no-cache")])
    res.cache_control.no_store = True
    directives = {part.strip() for part in res.headers["Cache-Control"].split(",")}
    assert {"max-age=10", "no-cache", "no-store"} <= directives

def test_request_call_application_and_get_response_agree():
    """Seam: protocol handoff — call_application and get_response expose same outputs."""
    def app(environ, start_response):
        start_response("201 Created", [("X-App", "yes")])
        return [b"created"]

    req = Request.blank("/create")
    status, headers, app_iter = req.call_application(app)
    response = req.get_response(app)
    assert status == response.status
    assert dict(headers)["X-App"] == response.headers["X-App"]
    assert b"".join(app_iter) == response.body
