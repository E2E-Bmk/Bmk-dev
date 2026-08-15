# WebOb Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

WebOb provides Python objects for HTTP requests and responses by wrapping the WSGI request `environ` dictionary and the WSGI response triple of status, headers, and body iterator. A request object must expose parsed, writable views of URL parts, headers, cookies, query variables, form variables, conditional headers, and WSGI subrequest execution. A response object must expose parsed, writable views of status, headers, body bytes, text, JSON, cookies, cache headers, conditional response handling, and WSGI application behavior.

The primary design rule is that each high-level view must project one underlying HTTP/WSGI state. A write through a public view must be visible through the other public views that describe the same state, and invalid writes must raise the documented Python exception instead of silently corrupting the state.

## Non-Goals

- This specification does not require private helper names, private descriptors, private parser functions, or environment-specific scaffolding.
- This specification does not require exact internal storage names, cached attribute names, singleton implementation details, or algorithm step order.
- This specification does not require optional performance measurement utilities.
- This specification does not require external network availability for ordinary request/response, parser, cookie, static-file, or decorator behavior.
- This specification does not require implementation of undocumented compatibility aliases beyond the public import paths and documented behavior listed above.
- This specification does not require byte-for-byte reproduction of generated default HTML beyond status, content type selection, escaping, and inclusion of documented detail/comment content.

## Representative Workflows

### In-Process WSGI Request and Response

```python
from webob import Request, Response

def app(environ, start_response):
    req = Request(environ)
    name = req.params.get('name', 'world')
    res = Response(text='Hello, %s' % name, content_type='text/plain')
    res.set_cookie('seen', 'yes', httponly=True)
    return res(environ, start_response)

req = Request.blank('/hello?name=WebOb')
res = req.get_response(app)

assert res.status == '200 OK'
assert res.content_type == 'text/plain'
assert res.text == 'Hello, WebOb'
assert 'seen=' in res.headers['Set-Cookie']
```

This workflow must preserve a single state path: the blank request stores URL parts in environ, `req.params` reads query variables from that environ, the response writes body bytes and content length, and `req.get_response` returns those response projections to the caller.

### Decorated Application

```python
from webob import Response
from webob.dec import wsgify
from webob.exc import HTTPForbidden

@wsgify
def app(req):
    if req.method != 'GET':
        raise HTTPForbidden('GET required')
    return Response(text='ok', content_type='text/plain')

response = app.get('/status')
assert response.status_int == 200
assert response.text == 'ok'
```

The decorated application must run as a request-taking callable and as a WSGI application. Raised WebOb HTTP exceptions must become HTTP responses.

## Request Behavior

A `Request` wraps the WSGI `environ` dictionary and exposes parsed, writable views of URL parts, headers, cookies, query variables, form variables, and body content.

**URL attributes.** Request URL attributes must be derived from WSGI `SCRIPT_NAME`, `PATH_INFO`, `QUERY_STRING`, `HTTP_HOST`, `SERVER_NAME`, `SERVER_PORT`, and `wsgi.url_scheme`. `scheme` must return the URL scheme. `host` must return the effective host with its effective port. `host_port` must return the effective port as text. `host_url` must omit default ports for HTTP and HTTPS. `script_name` must return the value of `SCRIPT_NAME`. `path_info` must return the value of `PATH_INFO`. `query_string` must return `QUERY_STRING`. `application_url` must include `SCRIPT_NAME` and must omit `PATH_INFO` and query string. `path_url` must include `SCRIPT_NAME` and `PATH_INFO` and must omit query string. `url` must include query string when `QUERY_STRING` is non-empty. Missing required WSGI keys must raise `KeyError` through the accessed property.

**Path navigation.** `path_info_peek()` must return the next non-empty path segment without changing the request and must return `None` when no segment exists. `path_info_pop(pattern=None)` must move the next segment from `PATH_INFO` to `SCRIPT_NAME` and return it. It must return `None` without changing the request when no segment exists or when `pattern` is supplied and does not match.

**Body and text.** `body` must return bytes. Setting `body` to bytes must replace `wsgi.input`, set `CONTENT_LENGTH`, and make `body_file_seekable` return a seekable stream positioned at the start containing the assigned bytes. Setting `body` to bytes must also replace `body_file_raw` with a new stream object. Setting `body` to `None` must store an empty byte body. Setting `body` to any non-bytes non-`None` value must raise `TypeError`. Setting `body_file` to bytes must raise `ValueError`; setting it to a file-like object must reset content length and mark the input readable but not seekable. Accessing `text` must require a charset and must raise `AttributeError` when no charset is available; setting `text` to a non-string must raise `TypeError`. `json` and `json_body` must decode and encode request bodies using the request charset.

**Query, form, and parameters.** `GET` must parse `QUERY_STRING` into a `GetDict`. Mutating that object must rewrite `environ['QUERY_STRING']`. `POST` must return a `MultiDict` for form submissions using `application/x-www-form-urlencoded`, `multipart/form-data`, or an empty content type on a POST-like request. For non-form requests, `POST` must return `NoVars`. Form parsing with a non-UTF-8 charset must raise `DeprecationWarning`. `params` must return a `NestedMultiDict` over `GET` followed by `POST`: `params[key]` must return the query value when the same key exists in both, and `params.getall(key)` must return query values followed by form values.

**Headers and cookies.** `cookies` must return a dict-like request cookie object backed by the `Cookie` header. Assigning a mapping to `cookies` must replace the request cookie header. Cookie reads for missing keys must follow ordinary mapping `KeyError` or default-return behavior.

**Copy operations.** `copy()` must shallow-copy the environ and must copy the request body so the copy has an independent body stream. `copy_get()` must copy the environ, force method `GET`, remove content type so `content_type` returns an empty string, and set an empty body.

**Conditional headers.** `remove_conditional_headers()` must remove only the selected conditional request headers. Its boolean arguments must control removal of `Accept-Encoding`, `If-Range`/`Range`, `If-None-Match`, and `If-Modified-Since`. When `remove_range` is `False`, `Range` must be preserved. When `remove_encoding` is `False`, `Accept-Encoding` must be preserved.

**Application dispatch.** `call_application(application, catch_exc_info=False)` must call a WSGI application with the request environ and return `(status, headers, app_iter)`. If the WSGI application supplies `exc_info` and `catch_exc_info` is false, the original exception must be raised. If `catch_exc_info` is true, the return tuple must include the captured `exc_info` as a fourth value. `send()` and `get_response()` must wrap that result in the request's `ResponseClass`; with no application they must use the default HTTP-sending app. The `status`, `headers`, and `body` of the response returned by `get_response(app)` must agree with the outputs of `call_application(app)`.

**Ad hoc attributes.** Assigning an ad hoc public attribute on a `Request` must store it in the environ so a new `Request` wrapping the same environ returns the same value. Deleting that attribute must remove it for both views, and accessing it afterward must raise `AttributeError`. The `response` attribute must provide a default `Response` object usable by `wsgify` when the decorated function returns `None`.

## Response Behavior

A `Response` wraps a status string, ordered header list, and body iterator, exposing parsed writable views of status, headers, body, cache directives, and content encoding.

**Status.** Setting `status` to an integer must convert it to the standard status string for known codes and a generic family reason for unknown codes. Setting `status` to a string must require the first token to be an integer and must raise `ValueError` otherwise. Setting `status` to a non-string non-integer must raise `TypeError`. `status_code` and `status_int` must return the integer code and must update `status` when assigned. A default `Response()` must have status `"200 OK"`.

**Headers.** `headerlist` must be the ordered response header list. `headers` must be a case-insensitive `ResponseHeaders` view over that list. Mutating `headers` must mutate `headerlist`, and replacing `headerlist` must reset the cached `headers` view so subsequent reads reflect the replacement list.

**Body and text.** `body` must return bytes and must consume `app_iter` into a single byte body when needed. If `Content-Length` exists and differs from the consumed body length, reading `body` must raise `AssertionError`. Setting `body` must require bytes and must raise `TypeError` for text or other objects. Setting `body` must update `app_iter` to a single bytes chunk and must update `content_length`. Setting `text` must require a string and must encode using `charset` or `default_body_encoding`; if neither exists, it must raise `AttributeError`. Assignment of `text` with a non-string must raise `TypeError`. `write(text)` must accept bytes. It must accept text only when `charset` is set and must raise `TypeError` otherwise. Assigning `app_iter` must clear an automatic content length. A default `Response()` must have `content_type` of `"text/html"`, `charset` of `"UTF-8"`, `content_length` of `0`, and `body` of `b""`.

**JSON.** Setting `json` on a response must encode the value as JSON and store it in `body`. Reading `json` must decode `body` using the response charset and return the parsed value. Both getter and setter must round-trip faithfully.

**Content type and charset.** `content_type` assignment must update the `Content-Type` header and must add the default charset for `text/html`, `text/*`, `application/xml`, and `*/*+xml` content types when a default charset exists and no charset is supplied. Assigning non-string truthy content type values must raise `TypeError`. Setting `charset` without a `Content-Type` header must raise `AttributeError`. `content_type_params` assignment must rewrite the parameters on `Content-Type`; values needing quoting must be quoted.

**Cache headers.** `cache_expires(0)` must set cache-control directives for an immediately uncacheable response, must set `Expires`, must set `Last-Modified` when absent, must set `Pragma` to `"no-cache"`, and must set `cache_control.no_cache` and `cache_control.no_store` to `True`. Positive seconds must clear existing cache-control properties, set `max-age`, make `cache_control.max_age` return the integer seconds value, set `Expires`, and remove `Pragma` so that `pragma` returns `None`. A `datetime.timedelta` value must be converted to seconds. `pragma` must be readable as a response attribute reflecting the `Pragma` header.

**Content encoding.** `encode_content('gzip')` must gzip the body iterator and set `Content-Encoding: gzip`; repeated gzip encoding must leave an already gzipped response unchanged. `encode_content('identity')` must decode content. Any other encoding must raise `AssertionError`. `decode_content()` must support `gzip` and `deflate`, must clear `Content-Encoding`, and must raise `ValueError` for unknown encodings. `content_encoding` must be readable as a response attribute reflecting the `Content-Encoding` header value, returning `None` when the header is absent.

**Conditional response handling.** When `conditional_response` is `True` on a response, `Response.__call__` must process conditional and range requests. `etag` must be settable as a constructor keyword or response attribute. Matching `If-None-Match` or `If-Modified-Since` on `GET` or `HEAD` must return `304 Not Modified` with entity headers filtered. A satisfiable byte range on a 200 response with known content length must return `206 Partial Content` with a `content_range` reflecting the slice boundaries; an unsatisfiable range must return `416 Requested Range Not Satisfiable`; a non-range or ineligible request must return the original response status and body.

**Copy.** `copy()` must return an independent copy of the response. Modifying the copy's `text` or `body` must not affect the original response.

**WSGI call behavior.** `Response.__call__` must act as a WSGI application. It must absolutize `Location` headers relative to the incoming request URI. A `HEAD` request must return an empty iterable while preserving headers including `Content-Length`.

## Collection and Header View Behavior

WebOb provides ordered multi-valued mapping types for query parameters, form data, and response headers.

**MultiDict.** `MultiDict` must store an ordered list of key/value pairs and must allow duplicate keys. `__getitem__` must return the last value for a key. `getall(key)` must return all values for a key in their original order. `keys()` must return all keys including duplicates. `__setitem__` must replace all existing values for the key with a single new value. `getone(key)` must return the sole value and must raise `KeyError` when the key has zero or multiple values. `pop(key)` and `__delitem__` must raise `KeyError` for missing keys. `MultiDict()` must raise `TypeError` when more than one positional argument is supplied.

**NestedMultiDict.** `NestedMultiDict` must provide a read-only merged view over multiple child `MultiDict` objects. `__getitem__` must return the value from the first child that contains the key. `getall(key)` must return values from all children in their construction order. Mutation methods must raise `KeyError`.

**NoVars.** `NoVars` must be an empty read-only variable mapping. `get(key, default)` must return the default. `getall(key)` must return an empty list. Mutation methods and item assignment must raise `KeyError`.

**GetDict.** `GetDict` must be a `MultiDict` subclass that updates `environ['QUERY_STRING']` whenever its contents are mutated.

**ResponseHeaders.** `ResponseHeaders` must be a case-insensitive `MultiDict` view over the response `headerlist`. Setting a header must update the underlying `headerlist`. The `add(name, value)` method must append a new header entry. `getall(name)` must return all values for that header name in a case-insensitive manner.

**EnvironHeaders.** `EnvironHeaders` must map HTTP header names to WSGI environ keys. `Content-Type` must map to `CONTENT_TYPE`. Headers prefixed with `HTTP_` must be accessible by their HTTP name (e.g. `X-Token` maps to `HTTP_X_TOKEN`). Accessing a header not present in the environ must raise `KeyError`.

## Cookie and Serializer Behavior

WebOb provides cookie management through header-level helpers and profile objects that combine serialization, signing, and multi-domain cookie generation.

**make_cookie.** `make_cookie(name, value, ...)` must build a single `Set-Cookie` header value. It must accept `max_age`, `httponly`, and `samesite` parameters. When `samesite` is set, the cookie must include a `SameSite` attribute. When `httponly` is `True`, the cookie must include `HttpOnly`. When `value` is `None`, the cookie must be set with an expiration date in the past to expire the client-side cookie. Invalid `max_age` conversion must raise `ValueError`, and invalid `samesite` values must raise `ValueError` while validation is enabled.

**CookieProfile.** `CookieProfile` must manage cookies with optional multi-domain support. When `domains` is a list, `get_headers(value)` must return one `Set-Cookie` header pair per domain, each including the appropriate `Domain` attribute. `get_value()` must raise `ValueError` when the profile is not bound to a request. `get_headers()` must raise `ValueError` when the serialized cookie value exceeds the maximum allowed length.

**SignedCookieProfile.** `SignedCookieProfile` must extend `CookieProfile` with HMAC-signed serialization.

**Serializers.** `JSONSerializer` must encode and decode values as UTF-8 JSON with `dumps` and `loads` methods. `Base64Serializer` must wrap another serializer and encode its output with URL-safe base64. `Base64Serializer.dumps` must return bytes, and `Base64Serializer.loads` must round-trip faithfully. `SignedSerializer` must sign serialized values with HMAC using a `secret` and `salt`. `SignedSerializer.loads` must raise `ValueError` for tampered data. `Base64Serializer.loads` must raise `ValueError` for malformed base64.

## Parsed Header Behavior

WebOb provides parsed header objects that expose structured access to Accept, Cache-Control, Range, ETag, and If-Range header values.

**Accept headers.** `create_accept_header(header_value)` must parse an `Accept` header string into an accept object. `best_match(offers)` must return the offer with the highest quality. `quality(media_type)` must return the quality factor for a given media type. The `in` operator must test whether a media type is acceptable. When the header value is `None`, the accept object must allow all offers: `best_match` must return the first offer, and `in` must return `True` for any media type.

**Accept-Language.** `create_accept_language_header(header_value)` must parse an `Accept-Language` header string. `lookup(languages, default=...)` must return the best matching language or the default. `best_match(offers, default_match=...)` must return the best match or the default match value.

**Cache-Control.** `CacheControl.parse(header_string, type=...)` must parse a `Cache-Control` header into a directive object. Directive attributes such as `max_age`, `no_cache`, `no_store`, and `public` must be readable and writable. Mutating a directive attribute on `req.cache_control` or `res.cache_control` must rewrite the corresponding `Cache-Control` header. Replacing the header string must make the next cache-control view reflect the new directives.

**Range.** `Range.parse(header_string)` must parse a byte range header. `start` must return the range start (inclusive). `end` must return the range end (exclusive, one past the last byte). `content_range(length)` must return a `ContentRange` object whose string form uses HTTP inclusive byte positions.

**ContentRange.** `ContentRange.parse(header_string)` must parse a content range header. `start` must return the range start. `stop` must return the range end (exclusive). `length` must return the total content length. Parsing an invalid header must return `None`. Constructing a `ContentRange` with an invalid triple (e.g. start greater than stop) must raise `ValueError`.

**ETag matchers.** `ETagMatcher.parse(header_string, strong=True)` must parse an ETag list. When `strong` is `True`, weak ETags must be excluded from matching. The `in` operator must test whether a tag is in the matcher. `AnyETag` must be a sentinel where the `in` operator returns `True` for any tag. `NoETag` must be a sentinel where the `in` operator returns `False` for any tag.

**IfRange.** `IfRange.parse(header_value)` must parse an `If-Range` header. When the header value is `None` or empty, the parsed object's `etag` must match any tag via the `in` operator.

## Exception and WSGI Helper Behavior

WebOb defines HTTP exception classes for status codes, WSGI application helpers for static files, a request-to-response decorator, and an HTTP client adapter.

**HTTP exceptions.** HTTP exception responses must derive status, title, and default body from the concrete exception class. `status_map` must map concrete public status codes to their exception classes (e.g. `status_map[404]` must be `HTTPNotFound`). `HTTPClientError` must be the base class for 4xx client error exceptions; `HTTPForbidden` must be a subclass of `HTTPClientError`. Generated exception bodies must escape HTML in HTML output, strip tags for plain text output, and pass JSON output through the selected JSON formatter. When the request `Accept` header prefers `application/json`, the exception response must have `content_type` of `"application/json"` and the body must include a `code` key with the status string. `HTTPNotModified` must emit an empty body when called as a WSGI application. Redirect HTTP exceptions must raise `ValueError` for CR or LF in `location` and must raise `TypeError` when both `location` and `add_slash=True` are supplied.

**Static file applications.** `FileApp` must serve a single file as a WSGI response with `Accept-Ranges: bytes` in the response headers. Static file responses must use conditional response handling so request `Range`, `If-Range`, and safe-method conditional headers affect the emitted status and body. `DirectoryApp` must serve files from a directory. `DirectoryApp(path)` must raise `OSError` when the path does not exist or is not a directory.

**HTTPExceptionMiddleware.** `HTTPExceptionMiddleware(app)` must wrap a WSGI application and catch `HTTPException` raised during the call, converting it into the corresponding HTTP response.

**wsgify decorator.** `wsgify` must convert a request-taking function into a WSGI application. The wrapped function must be preserved as `undecorated`. When used on a class method, `wsgify` must support descriptor binding so the instance is passed as `self`. When the decorated function returns a string, `wsgify` must convert it to a `Response` with that string as the text body. When the decorated function returns `None`, `wsgify` must return the response stored as `req.response`, including cookies set on that response. Subclasses may override `RequestClass` or `call_func`. `wsgify.__call__()` must raise `TypeError` for unbound calls with extra arguments and for WSGI calls with the wrong signature.

**wsgify middleware.** `wsgify.middleware` must create middleware factories. The wrapped application must be supplied to the middleware function as the first positional argument after the request, before any configured positional arguments. The middleware factory must produce a WSGI application that chains the inner application response through the middleware function.

**SendRequest client.** `SendRequest` must be a WSGI-to-HTTP outbound request client. It must accept an `HTTPConnection` parameter to override the connection class used for outbound requests. When the connection raises `socket.timeout`, the response must have status code `504`. `SendRequest.__call__()` must raise `ValueError` for unknown schemes and for missing server/host information.

## Date and Utility Behavior

WebOb provides date-time helpers, time constant aliases, and an HTML escaping function used across request and response processing.

**UTC and time constants.** `UTC` must be a `tzinfo` object whose `utcoffset` returns a zero timedelta. The constants `day`, `week`, `hour`, `minute`, `second`, `month`, and `year` must be `timedelta` objects. `second` must be one second. `minute` must equal `60 * second`. `hour` must equal `60 * minute`. `day` must equal `24 * hour`. `week` must equal `7 * day`. `month` must equal `30 * day`. `year` must equal `365 * day`.

**Date serialization.** `timedelta_to_seconds(td)` must convert a `timedelta` to total seconds as a number. `serialize_date(dt)` must convert a `datetime` to an HTTP date string. `parse_date(s)` must parse an HTTP date string back into a `datetime`. `serialize_date` and `parse_date` must round-trip faithfully. `serialize_date(value)` must raise `ValueError` for unsupported input types.

**HTML escaping.** `html_escape(value)` must escape HTML special characters using XML character references. `html_escape(None)` must return an empty string. When `value` provides an `__html__()` method, `html_escape` must call it and return the result directly.

## State Model

WebOb has three public projections of core state:

- Request state: the WSGI `environ` dictionary plus its body stream.
- Response state: status string, ordered header list, body iterator, and response flags.
- Parsed helper state: dictionary-like, cookie, cache, accept, ETag, and range objects that are returned from request or response properties.

Each projection must stay synchronized with the underlying state it represents. A parsed helper returned from a request or response property must reflect the current header or environ value, and a helper mutation that is documented as writable must rewrite the corresponding header or environ value. A parsed helper that represents an invalid or missing header must remain safe to inspect through its documented methods and must not corrupt the underlying request or response.

## Error Semantics

- `Request(environ)` raises `TypeError` when `environ` is not a plain dictionary.
- `Request(..., unknown=value)` raises `TypeError` when a keyword does not correspond to a request attribute.
- `Request.blank(base_url=...)` raises `ValueError` when `base_url` has a query or fragment, and raises `ValueError` for unknown schemes.
- `Request.body = value` raises `TypeError` for non-bytes values except `None`.
- `Request.body_file = value` raises `ValueError` for bytes.
- `Request.text` raises `AttributeError` when no charset is available; `Request.text = value` raises `TypeError` for non-string values.
- `Request.POST` raises `DeprecationWarning` for form parsing when the request charset is not UTF-8.
- `Request.from_bytes(b)` raises `ValueError` when unread bytes remain after parsing one request.
- `Request.from_file(fp)` raises `ValueError` for a malformed request line.
- `Request.call_application()` reraises the supplied `exc_info` exception when `catch_exc_info` is false.
- `MultiDict()` raises `TypeError` when more than one positional argument is supplied.
- `MultiDict.view_list(obj)` raises `TypeError` when `obj` is not an actual list.
- `MultiDict.__getitem__`, `getone`, `pop`, and deletion raise `KeyError` for missing keys; `getone` also raises `KeyError` for multiple values.
- `NestedMultiDict` mutation methods raise `KeyError`.
- `NoVars` mutation methods and item access raise `KeyError`.
- `Response()` raises `TypeError` when both `body` and `app_iter` are supplied, or when an unknown keyword is supplied.
- `Response.status = value` raises `ValueError` for strings without an integer first token and raises `TypeError` for unsupported value types.
- `Response.body = value` raises `TypeError` for text and non-bytes values.
- `Response.text` raises `AttributeError` when neither charset nor default body encoding exists; assignment raises `TypeError` for non-string values.
- `Response.charset = value` raises `AttributeError` when no `Content-Type` header exists.
- `Response.content_type = value` raises `TypeError` for non-string truthy values.
- `Response.from_file(fp)` raises `ValueError` for malformed header lines.
- `Response.unset_cookie(name, strict=True)` raises `KeyError` when no matching response cookie exists.
- `Response.encode_content(encoding)` raises `AssertionError` for unsupported encodings.
- `Response.decode_content()` raises `ValueError` for unsupported content encodings.
- `ContentRange(start, stop, length)` raises `ValueError` for invalid range triples.
- `make_cookie()` raises `ValueError` for invalid integer conversion of `max_age` and for invalid SameSite values while validation is enabled.
- `Base64Serializer.loads()` and `SignedSerializer.loads()` raise `ValueError` for malformed base64; `SignedSerializer.loads()` raises `ValueError` for invalid signatures.
- `CookieProfile.get_value()` raises `ValueError` when the profile is not bound to a request.
- `CookieProfile.get_headers()` raises `ValueError` when the serialized cookie value is too long.
- Redirect HTTP exceptions raise `ValueError` for CR or LF in `location` and raise `TypeError` when both `location` and `add_slash=True` are supplied.
- `DirectoryApp(path)` raises `OSError` when the path does not exist or is not a directory.
- `SendRequest.__call__()` raises `ValueError` for unknown schemes and for missing server/host information.
- `wsgify.__call__()` raises `TypeError` for unbound calls with extra arguments and for WSGI calls with the wrong signature.
- `serialize_date(value)` raises `ValueError` for unsupported input types.

## Cross-View Invariants

1. Setting `req.headers['Content-Type']` must update `req.environ['CONTENT_TYPE']`, and setting `req.content_type` must be visible through `req.headers['Content-Type']`; deleting the environ key must make the header view raise `KeyError`.
2. Mutating `req.GET` must rewrite `req.environ['QUERY_STRING']`, and a subsequent `req.params` read must return values from the updated query dictionary before form values.
3. Setting `req.body` must replace `req.body_file_raw`, update `req.content_length`, make `req.body_file_seekable` return a seekable stream positioned at the start, and make `req.body` return the assigned bytes.
4. Assigning an ad hoc public attribute on a `Request` must store it in the environ so a new `Request` wrapping the same environ returns the same value; deleting that attribute must remove it for both views.
5. Setting `res.headers[name]` must update `res.headerlist`, and replacing `res.headerlist` must make later `res.headers` reads reflect the replacement list.
6. Setting `res.body` must update `res.app_iter` to a single bytes chunk and must update `res.content_length`; assigning `res.app_iter` must clear content length unless later body consumption computes a matching length.
7. Setting `res.content_type` and `res.charset` must rewrite the single `Content-Type` header, and `res.content_type_params` must return the parameters currently present in that header.
8. Mutating `req.cache_control` or `res.cache_control` directive attributes must rewrite the corresponding `Cache-Control` header, and replacing the header string must make the next cache-control view reflect the new directives.
9. `req.range` must return a `Range` object whose `content_range(res.content_length)` result must be assignable to `res.content_range`, and the string form of `res.content_range` must use HTTP inclusive byte positions.
10. A response returned by `req.get_response(app)` must expose the status, headers, and body returned by `req.call_application(app)` through `Response.status`, `Response.headers`, and `Response.body`.
11. A `FileApp` response must expose the same file content through WSGI body iteration, `Response.body` after `Request.get_response`, and byte-range conditional response slices.
12. A `wsgify` application returning `None` must return the same response object stored as `req.response`, including cookies set on that response.
13. `wsgify.middleware` must compose with `wsgify`-decorated inner applications: the middleware function must receive the wrapped application and configured positional arguments, and the full chain must produce a response consistent with both the inner application output and middleware modifications.

## Public Interface

### Import Surface

The package must be importable as `webob`.

Top-level imports:

```python
from webob import Request, Response, UTC
from webob import day, week, hour, minute, second, month, year
from webob import html_escape
from webob import parse_date, serialize_date, timedelta_to_seconds
```

Documented module imports:

```python
from webob.request import BaseRequest, Request
from webob.response import Response
from webob.multidict import MultiDict, NestedMultiDict, NoVars, GetDict
from webob.headers import ResponseHeaders, EnvironHeaders
from webob.cookies import CookieProfile, SignedCookieProfile, SignedSerializer
from webob.cookies import JSONSerializer, Base64Serializer, make_cookie
from webob.acceptparse import create_accept_header
from webob.acceptparse import create_accept_charset_header
from webob.acceptparse import create_accept_encoding_header
from webob.acceptparse import create_accept_language_header
from webob.byterange import Range, ContentRange
from webob.etag import AnyETag, NoETag, ETagMatcher, IfRange
from webob.cachecontrol import CacheControl
from webob.exc import HTTPException, WSGIHTTPException, HTTPExceptionMiddleware
from webob.exc import HTTPClientError, HTTPForbidden, HTTPNotFound
from webob.exc import HTTPNotModified, HTTPFound
from webob.static import FileApp, DirectoryApp
from webob.client import SendRequest, send_request_app
from webob.dec import wsgify
```

`webob.exc` must export the base exception classes, all concrete public `HTTP*` status classes, `HTTPExceptionMiddleware`, and `status_map`.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| Request | class | WSGI request wrapping an environ dictionary |
| BaseRequest | class | Base WSGI request implementation |
| Response | class | WSGI response with status, headers, and body |
| MultiDict | class | Ordered list of key/value pairs with duplicate keys |
| NestedMultiDict | class | Read-only merged view over multiple MultiDicts |
| NoVars | class | Empty read-only variable mapping |
| GetDict | class | MultiDict subclass that updates QUERY_STRING on mutation |
| ResponseHeaders | class | Case-insensitive MultiDict view over response headerlist |
| EnvironHeaders | class | Header view mapping HTTP names to WSGI environ keys |
| CookieProfile | class | Cookie management profile with serialization |
| SignedCookieProfile | class | CookieProfile with HMAC-signed serializer |
| SignedSerializer | class | HMAC-signing serializer for cookie values |
| JSONSerializer | class | UTF-8 JSON serializer for cookie values |
| Base64Serializer | class | URL-safe base64 wrapping serializer |
| make_cookie | function | Build a single Set-Cookie header value |
| create_accept_header | function | Parse Accept header into an accept object |
| create_accept_charset_header | function | Parse Accept-Charset header |
| create_accept_encoding_header | function | Parse Accept-Encoding header |
| create_accept_language_header | function | Parse Accept-Language header |
| Range | class | Parsed HTTP byte range |
| ContentRange | class | Parsed HTTP content range |
| AnyETag | class | Wildcard ETag matcher matching all tags |
| NoETag | class | Empty ETag matcher matching no tags |
| ETagMatcher | class | Parsed ETag list matcher |
| IfRange | class | Parsed If-Range header as ETag or date |
| CacheControl | class | Parsed Cache-Control header directives |
| HTTPException | exception | Base HTTP exception |
| WSGIHTTPException | exception | HTTP exception usable as WSGI response |
| HTTPClientError | exception | Base for 4xx client error exceptions |
| HTTPForbidden | exception | 403 Forbidden HTTP exception |
| HTTPNotFound | exception | 404 Not Found HTTP exception |
| HTTPNotModified | exception | 304 Not Modified HTTP exception |
| HTTPFound | exception | 302 Found HTTP redirect exception |
| HTTPExceptionMiddleware | class | Middleware catching HTTPException as responses |
| status_map | constant | Maps status codes to HTTP exception classes |
| FileApp | class | WSGI application serving a single file |
| DirectoryApp | class | WSGI application serving files from a directory |
| SendRequest | class | WSGI-to-HTTP outbound request client |
| send_request_app | constant | Default SendRequest instance |
| wsgify | decorator | Convert request-taking function into WSGI application |
| wsgify.middleware | decorator | Create middleware factory from decorated function |
| parse_date | function | Parse HTTP date string into datetime |
| serialize_date | function | Serialize datetime to HTTP date string |
| timedelta_to_seconds | function | Convert timedelta to total seconds |
| UTC | constant | UTC tzinfo object |
| day | constant | One-day timedelta |
| week | constant | One-week timedelta |
| hour | constant | One-hour timedelta |
| minute | constant | One-minute timedelta |
| second | constant | One-second timedelta |
| month | constant | 30-day timedelta |
| year | constant | 365-day timedelta |
| html_escape | function | HTML-escape text with XML character references |

### CLI Entry Points

There is no console script for this package. `python -m webob` is not supported. Programmatic use is through Python imports.


## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Assessment checks observable behavior through public imports and documented workflows. It exercises request/environ synchronization, response/header/body synchronization, MultiDict duplicate-key semantics, cookies and signed cookies, parsed headers, conditional and range responses, HTTP exceptions, static file WSGI behavior, `wsgify`, and representative serialization helpers. It checks public behavior, exception types, return values, and cross-view invariants. Private helper names, internal cache fields, environment-specific scaffolding, and private module organization are not examined.
