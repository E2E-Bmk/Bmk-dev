# WebOb Specification

## Product Overview

WebOb provides Python objects for HTTP requests and responses by wrapping the WSGI request environment and the WSGI response triple of status, headers, and body iterator. A `Request` is primarily a mutable view over a WSGI `environ` dictionary. A `Response` is both a mutable HTTP response object and a WSGI application.

The library is designed for applications, middleware, subrequests, and lightweight HTTP parsing/formatting. It exposes dictionary-like header and parameter views, parsed HTTP header helpers, HTTP exception responses, cookie helpers, a request-to-WSGI decorator, and simple static-file WSGI applications.

## Scope

This specification covers:

- Construction and mutation of `Request`, `BaseRequest`, and `Response`.
- The public request projections over `environ`: method, URL parts, headers, body, query variables, form variables, cookies, conditional headers, cache-control, and Accept headers.
- The public response projections over status, header list, header mapping, body, text, JSON, app iterator, content type, cache-control, cookies, conditional responses, and WSGI calling.
- `MultiDict`, `GetDict`, `NestedMultiDict`, `NoVars`, `ResponseHeaders`, and `EnvironHeaders`.
- Accept, Accept-Charset, Accept-Encoding, and Accept-Language helper objects and factory functions.
- Range, Content-Range, ETag, If-Range, Cache-Control, datetime, and HTML escaping helpers.
- Cookie serialization profiles and signed/base64/JSON serializers.
- `webob.exc` HTTP exception response classes and middleware.
- `webob.dec.wsgify`, `webob.static.FileApp`, `webob.static.DirectoryApp`, and `webob.client.SendRequest`.

## Installable Surface

The top-level package exports:

```python
from webob import Request, Response
from webob import UTC, day, week, hour, minute, second, month, year
from webob import html_escape
from webob import exc
```

The main public modules are:

```python
from webob.request import BaseRequest, Request
from webob.response import Response
from webob.multidict import MultiDict, GetDict, NestedMultiDict, NoVars
from webob.headers import ResponseHeaders, EnvironHeaders
from webob.acceptparse import (
    AcceptOffer, Accept, AcceptValidHeader, AcceptNoHeader, AcceptInvalidHeader,
    MIMEAccept, AcceptCharset, AcceptCharsetValidHeader, AcceptCharsetNoHeader,
    AcceptCharsetInvalidHeader, AcceptEncoding, AcceptEncodingValidHeader,
    AcceptEncodingNoHeader, AcceptEncodingInvalidHeader, AcceptLanguage,
    AcceptLanguageValidHeader, AcceptLanguageNoHeader,
    AcceptLanguageInvalidHeader, create_accept_header,
    create_accept_charset_header, create_accept_encoding_header,
    create_accept_language_header,
)
from webob.byterange import Range, ContentRange
from webob.etag import AnyETag, NoETag, ETagMatcher, IfRange, etag_property
from webob.cachecontrol import CacheControl, UpdateDict
from webob.cookies import (
    Cookie, CookieProfile, SignedCookieProfile, SignedSerializer,
    JSONSerializer, Base64Serializer, make_cookie,
)
from webob.dec import wsgify
from webob.static import FileApp, DirectoryApp
from webob.client import SendRequest, send_request_app
from webob.exc import HTTPExceptionMiddleware, status_map
```

`webob.exc` also exports `HTTPException`, `WSGIHTTPException`, `HTTPError`, `HTTPRedirection`, `HTTPOk`, all named public `HTTP*` response classes for the documented 2xx, 3xx, 4xx, and 5xx status codes, and maps concrete status codes to classes through `status_map`.

WebOb does not define a command-line entry point. Its public surface is the Python API.

## Public API

### Request

```python
Request(environ: dict, **kw)
BaseRequest(environ: dict, **kw)
Request.blank(path, environ=None, base_url=None, headers=None, POST=None, **kw)
req.copy()
req.copy_get()
req.decode(charset=None, errors="strict")
req.path_info_pop(pattern=None)
req.path_info_peek()
req.relative_url(other_url, to_application=False)
req.remove_conditional_headers(
    remove_encoding=True,
    remove_range=True,
    remove_match=True,
    remove_modified=True,
)
req.as_bytes(skip_body=False)
req.as_text(skip_body=False)
Request.from_bytes(data)
Request.from_text(text)
Request.from_file(fileobj)
req.call_application(application, catch_exc_info=False)
req.get_response(application=None, catch_exc_info=False)
req.send(application=None, catch_exc_info=False)
```

`Request(environ)` wraps the supplied WSGI environment directly. The environment must be a plain `dict`. Keyword arguments are applied as attribute assignments; `method` is applied before body-related keywords.

`Request.blank(path, ...)` creates a minimal WSGI environment. `path` may be an absolute URL or an encoded path with an optional query string. Missing defaults include `GET`, `localhost:80`, `HTTP/1.0`, an empty seekable input stream, and standard WSGI flags. When `base_url` is provided, its scheme, host, port, and path fill `wsgi.url_scheme`, `HTTP_HOST`, `SERVER_NAME`, `SERVER_PORT`, and `SCRIPT_NAME`; a `base_url` with query or fragment is invalid. Values supplied in `environ` override generated values. `headers` are applied through `req.headers`.

Core request attributes are mutable projections over `environ`: `method`, `scheme`, `http_version`, `script_name`, `path_info`, `query_string`, `server_name`, `server_port`, `remote_user`, `remote_host`, `remote_addr`, `content_type`, `content_length`, `headers`, `host`, `host_port`, `host_url`, `application_url`, `path_url`, `path`, `path_qs`, `url`, `domain`, `client_addr`, `is_xhr`, `charset`, `body`, `body_file`, `body_file_seekable`, `text`, `json`, `json_body`, `GET`, `POST`, `params`, `cookies`, `cache_control`, `accept`, `accept_charset`, `accept_encoding`, `accept_language`, `authorization`, `date`, `if_match`, `if_none_match`, `if_modified_since`, `if_unmodified_since`, `if_range`, `range`, `max_forwards`, and `pragma`.

`req.headers` is a case-insensitive dictionary-like wrapper over CGI-style environment keys. Setting `req.headers["Content-Type"]` updates `CONTENT_TYPE`; setting ordinary headers updates `HTTP_*` keys.

`req.body` is bytes. Reading it makes the request input seekable and restores the body stream to the beginning. Setting it replaces `wsgi.input`, updates `CONTENT_LENGTH`, and marks the body seekable. `req.text` decodes and encodes through `req.charset`; it is only available when a charset is present. `req.json` and `req.json_body` parse or serialize the body as JSON using the request charset.

`req.GET` is a `GetDict` over the query string. It parses both `&` and `;` separators, percent-decodes names and values, preserves repeated keys, and stores its parsed view in the environment until the query string changes. `req.POST` is a `MultiDict` for HTML form submissions. It parses `application/x-www-form-urlencoded`, `multipart/form-data`, and POST requests with an empty content type; other non-form requests return a read-only `NoVars`. Form parsing expects UTF-8; non-UTF-8 form submissions should be handled by `req.decode(charset)`. `req.params` is a read-only `NestedMultiDict(req.GET, req.POST)`, so single-value lookup prefers query-string values while `getall`, `items`, `keys`, and `values` include query values before body values.

`req.cookies` is a dict-like view over the `Cookie` header. Assigning `req.cookies` replaces the outgoing `HTTP_COOKIE` value represented by the request environment.

`req.copy()` shallow-copies the environment and copies the request body so that the new request can read independently. `req.copy_get()` returns a copy with method `GET`, no content type, and an empty body.

Ad-hoc public attributes assigned to a `Request` instance are stored in the shared request environment and are visible to other `Request` wrappers around the same environment.

`req.call_application(app)` calls a WSGI app and returns `(status, headerlist, app_iter)`. If `catch_exc_info=True`, it returns `(status, headerlist, app_iter, exc_info)`. If the app uses the `write` callable or does not call `start_response` before returning, WebOb consumes and closes the returned iterator and returns the accumulated output list. `req.get_response(app)` and `req.send(app)` return a `Response` built from the captured status, headers, and app iterator.

### Response

```python
Response(
    body=None,
    status=None,
    headerlist=None,
    app_iter=None,
    content_type=None,
    conditional_response=None,
    charset=<omitted>,
    **kw,
)
Response.from_file(fileobj)
resp.copy()
resp.write(text_or_bytes)
resp.set_cookie(
    name,
    value="",
    max_age=None,
    path="/",
    domain=None,
    secure=False,
    httponly=False,
    comment=None,
    overwrite=False,
    samesite=None,
)
resp.delete_cookie(name, path="/", domain=None)
resp.unset_cookie(name, strict=True)
resp.merge_cookies(resp_or_wsgi_app)
resp.cache_expires(seconds=0, **attrs)
resp.encode_content(encoding="gzip", lazy=False)
resp.decode_content()
resp.md5_etag(body=None, set_content_md5=False)
resp.conditional_response_app(environ, start_response)
resp.app_iter_range(start, stop)
resp(environ, start_response)
```

A `Response` has `status`, `headerlist`, and `app_iter` as its fundamental state. `status` defaults to `"200 OK"`. Passing an integer status sets the standard reason phrase when known, or a generic phrase for the status class. `status_code` and `status_int` expose the integer status code.

When no `headerlist` is supplied and the status code allows a body, WebOb sets a `Content-Type` using `default_content_type` (`"text/html"`) and, for text or XML content types, adds `default_charset` (`"UTF-8"`) if no charset is already present. Omitting `charset` allows this default behavior; passing `charset=None` suppresses adding a charset parameter while still allowing bytes bodies. Status codes in the 1xx range and statuses 204, 205, and 304 do not receive the default content type and use an empty body.

`body` and `app_iter` are mutually exclusive constructor arguments. If `body` is omitted and `app_iter` is omitted, the response body is empty. If `body` is text in the constructor, WebOb encodes it using the explicit charset or the response charset when one is available. The `resp.body` property itself is bytes only; `resp.text`, `resp.unicode_body`, and `resp.ubody` decode and encode using `resp.charset` or `default_body_encoding`.

`resp.json` and `resp.json_body` decode and encode JSON using UTF-8. Passing `json=` or `json_body=` to the constructor creates a compact UTF-8 JSON body and defaults the content type to `application/json`.

`resp.headerlist` is the ordered list of `(name, value)` response headers. `resp.headers` is a `ResponseHeaders` view over the same list. It is case-insensitive, supports repeated headers, replaces all existing values for a key on assignment, and preserves repeated values when `add` is used.

Setting `resp.body` replaces the app iterator with a single bytes item and updates `Content-Length`. Setting `resp.app_iter` clears any existing `Content-Length`. Reading `resp.body` consumes and closes the current app iterator, stores the resulting bytes as a single-item iterator, and sets `Content-Length` when possible. If an existing `Content-Length` does not match the consumed body length, reading the body is an error.

`resp.body_file` returns a file-like writer. Writing bytes appends bytes to the response body. Writing text requires a response charset and appends encoded bytes. `resp.write` follows the same rules and returns the number of bytes written.

`resp.content_type` gets or sets the media type without parameters. Setting it removes old parameters and resets the default charset for text and XML content types. `resp.charset` gets, sets, or removes the `charset` parameter. `resp.content_type_params` returns a plain dictionary of content-type parameters; changing that dictionary does not mutate the response until it is assigned back.

`resp.cache_control` is a mutable `CacheControl` object bound to the `Cache-Control` header. Mutating properties on it updates the header string. `resp.cache_expires(seconds)` sets cache headers and `Expires`: `seconds=0` makes the response explicitly uncacheable, a positive value sets `max-age`, and a `datetime.timedelta` is converted to seconds.

`resp(environ, start_response)` is the WSGI interface. It makes relative `Location` headers absolute using the request URL. On `HEAD`, it starts the same response headers but returns an empty body iterator. If `resp.conditional_response` is true, calling the response delegates to `conditional_response_app`.

`conditional_response_app` uses the incoming request's conditional headers. For `GET` and `HEAD`, matching `If-None-Match` or `If-Modified-Since` returns `304 Not Modified` with entity headers such as `Content-Length` and `Content-Type` removed. A satisfiable byte `Range` request against a 200 response with known content length returns `206 Partial Content` with `Content-Range` and adjusted `Content-Length`; an unsatisfiable range returns `416 Requested Range Not Satisfiable`. `If-Range` controls whether a requested range is honored.

### Multi-Value Mappings

```python
MultiDict(*args, **kw)
MultiDict.view_list(list_object)
MultiDict.from_fieldstorage(fieldstorage)
md.add(key, value)
md.getall(key)
md.getone(key)
md.mixed()
md.dict_of_lists()
md.extend(other=None, **kwargs)
md.update(*args, **kw)

NestedMultiDict(*dicts)
NoVars(reason=None)
GetDict(data, env)
ResponseHeaders.view_list(headerlist)
EnvironHeaders(environ)
```

`MultiDict` is an ordered mapping backed by ordered key/value pairs. `md[key]` returns the last value for the key. `md.add(key, value)` appends without removing earlier values. `md[key] = value` removes all previous values for that key and appends the new pair. `getall` always returns a list. `getone` returns the sole value or raises `KeyError` when there are zero or multiple values. `items`, `keys`, and `values` include repeated keys in order.

`mixed()` returns a plain dictionary where single-occurrence keys map to a scalar and repeated keys map to a list. `dict_of_lists()` maps every key to a list. `extend()` appends pairs. `update()` follows normal mapping assignment semantics and may overwrite duplicate-key behavior.

`GetDict` is the query-string view used by `Request.GET`; any mutation updates the cached query string representation in the environment. `NestedMultiDict` combines multiple dict-like objects as a read-only view. `NoVars` is a read-only empty mapping used when request variables are not applicable.

`ResponseHeaders` is a case-insensitive multi-value mapping over a response `headerlist`. `EnvironHeaders` is a single-value mapping over WSGI `environ` request headers and translates between HTTP header names and CGI-style environment keys.

### Header Helpers

```python
create_accept_header(header_value)
create_accept_charset_header(header_value)
create_accept_encoding_header(header_value)
create_accept_language_header(header_value)
```

Each factory returns a no-header object when `header_value is None`, a valid-header object when parsing succeeds, and an invalid-header object when parsing fails. Existing objects of the corresponding family are copied rather than reparsed.

Valid Accept objects expose `header_value`, `parsed`, `copy`, `acceptable_offers`, `best_match`, `quality`, stringification, iteration by preference, addition operators that return new objects, and containment for backward-compatible acceptability checks. Invalid and missing Accept objects are falsey; they keep `parsed` as `None` and behave as "no usable preference" for matching. Accept objects are immutable from the caller's perspective; adding values creates a new header object.

`Accept.accept_html()` and `accepts_html` check whether an HTML-like media type is acceptable among `text/html`, `application/xhtml+xml`, `application/xml`, and `text/xml`. `AcceptLanguage` additionally exposes `basic_filtering`, `lookup`, `best_match`, and `quality` for language tags.

```python
Range(start, end)
Range.parse(header)
range_obj.range_for_length(length)
range_obj.content_range(length)

ContentRange(start, stop, length)
ContentRange.parse(value)

ETagMatcher(etags)
ETagMatcher.parse(value, strong=True)
IfRange.parse(value)
```

`Range` uses Python-style non-inclusive end offsets. Parsing `bytes=0-100` creates a range whose end is 101. Suffix ranges are represented with a negative start and `end is None`. Invalid or unsupported range strings parse as `None`. `range_for_length(length)` returns a satisfiable `(start, stop)` pair or `None`; `content_range(length)` returns a `ContentRange` or `None`.

`ContentRange` also uses a Python-style non-inclusive `stop` internally and serializes to HTTP's inclusive final byte. `None` represents `*` in content-range fields. Invalid content-range combinations raise `ValueError` on construction or parse as `None`.

`AnyETag` represents `*` or a safe missing ETag and contains every candidate. `NoETag` represents an unsafe missing ETag and contains no candidate. `ETagMatcher.parse("*")` returns `AnyETag`; strong parsing ignores weak tags. `IfRange.parse` returns an ETag-based matcher for entity tags and a date-based matcher for HTTP dates.

```python
CacheControl.parse(header, updates_to=None, type=None)
str(cache_control)
cache_control.copy()
```

`CacheControl` parses comma-separated directives into a mutable properties mapping. When it is bound to a request or response, changing properties updates the corresponding header. Request-only properties include `max_stale`, `min_fresh`, and `only_if_cached`. Response-only properties include `public`, `private`, `must_revalidate`, `proxy_revalidate`, `s_maxage`, `stale_while_revalidate`, and `stale_if_error`. Shared properties include `no_cache`, `no_store`, `no_transform`, and `max_age`. Setting a directive on the wrong request/response type raises `AttributeError`.

### Cookies

```python
make_cookie(
    name,
    value,
    max_age=None,
    path="/",
    domain=None,
    secure=False,
    httponly=False,
    comment=None,
    samesite=None,
)

Cookie(input=None)
JSONSerializer()
Base64Serializer(serializer=None)
SignedSerializer(secret, salt, hashalg="sha512", serializer=None)
CookieProfile(
    cookie_name,
    secure=False,
    max_age=None,
    httponly=None,
    samesite=None,
    path="/",
    domains=None,
    serializer=None,
)
SignedCookieProfile(
    secret,
    salt,
    cookie_name,
    secure=False,
    max_age=None,
    httponly=False,
    samesite=None,
    path="/",
    domains=None,
    hashalg="sha512",
    serializer=None,
)
```

`make_cookie` returns a serialized `Set-Cookie` value. `value=None` generates a deletion cookie with an empty value, `Max-Age=0`, and an expiration date in the past. `max_age` accepts seconds or `datetime.timedelta`; when present it also determines `Expires`. `secure`, `httponly`, `comment`, `domain`, `path`, and `samesite` control the corresponding cookie attributes. `samesite` accepts `"strict"`, `"lax"`, `"none"`, or `None` while validation is enabled.

`CookieProfile` serializes application values into cookies using a serializer object with `dumps` and `loads`. By default it uses URL-safe base64 around JSON. Calling or binding a profile to a request returns a copy bound to that request. `get_value()` reads the named cookie from the bound request, deserializes it, returns `None` for a missing or malformed cookie, and raises `ValueError` if no request is bound. `get_headers(value, ...)` returns `("Set-Cookie", value)` header pairs. `set_cookies(response, value, ...)` extends a response header list and returns the response. If `domains` contains multiple domains, a cookie header is produced for each domain. A serialized cookie value longer than WebOb's cookie-size limit is rejected.

`SignedCookieProfile` uses `SignedSerializer` to add an HMAC signature before base64 encoding. `SignedSerializer.loads` raises `ValueError` for malformed base64 or an invalid signature. `Base64Serializer.loads` raises `ValueError` for malformed base64. `JSONSerializer` uses JSON text encoded as UTF-8 bytes.

### Decorators, Static Files, and Client Sending

```python
wsgify(func=None, RequestClass=None, args=(), kwargs=None, middleware_wraps=None)
wsgify.middleware(middle_func=None, app=None, **kw)
```

`wsgify` turns a function that accepts a request into a WSGI app. The decorated object can be called as a WSGI application with `(environ, start_response)` or directly with a `Request` instance. When called as WSGI, it creates a request using `RequestClass`, creates `req.response`, calls the wrapped function, converts `webob.exc.HTTPException` into a response, and then calls the resulting response as WSGI.

A wrapped function may return a `Response`, any WSGI application, `None` to use `req.response`, `str`, or `bytes`. Text and bytes are written into `req.response`. Cookies set on `req.response` are merged into a distinct returned response or WSGI app. `wsgify.get`, `wsgify.post`, and `wsgify.request` create blank requests and return responses for convenient in-process calls.

`wsgify.middleware` creates middleware factories. Middleware functions receive `(req, app, *configured_args, **configured_kwargs)` and may return the app unchanged, a response, or a modified response obtained through `req.get_response(app)`.

```python
FileApp(filename, **kw)
DirectoryApp(path, index_page="index.html", hide_index_with_redirect=False, **kw)
```

`FileApp` is a WSGI application for one file. It allows `GET` and `HEAD`; other methods return `HTTPMethodNotAllowed`. It guesses content type and content encoding from the filename, sets `Accept-Ranges: bytes`, uses `wsgi.file_wrapper` when available, sets `Content-Length` and `Last-Modified`, and applies WebOb conditional response handling for range and freshness requests. Missing files return `HTTPNotFound`; files that cannot be opened return `HTTPForbidden`.

`DirectoryApp` serves files beneath a directory. It normalizes the root directory and rejects construction for a non-directory path. It prevents traversal outside the root. If a requested path is a directory and `index_page` is set, it serves that index file; if the request for a directory lacks a trailing slash, it redirects to the slash form. With `hide_index_with_redirect=True`, direct requests to the index filename redirect to the containing directory URL. Subclasses may override `make_fileapp(path)`.

```python
SendRequest(HTTPConnection=http.client.HTTPConnection, HTTPSConnection=http.client.HTTPSConnection)
send_request_app
```

`SendRequest` sends the request described by a WSGI environment over HTTP or HTTPS. It connects to `SERVER_NAME:SERVER_PORT`, sends the Host header from `HTTP_HOST`, honors `webob.client.timeout` when the connection class supports it, builds the path from `SCRIPT_NAME`, `PATH_INFO`, and `QUERY_STRING`, reads the request body according to `CONTENT_LENGTH`, and returns the upstream response body as a WSGI response. Unknown schemes raise `ValueError`. A socket timeout becomes `HTTPGatewayTimeout`; bad domain and connection-refused conditions become `HTTPBadGateway`.

### Datetime and HTML Helpers

`UTC` is a UTC `tzinfo` instance. `second`, `minute`, `hour`, `day`, `week`, `month`, and `year` are `datetime.timedelta` constants; `month` is 30 days and `year` is 365 days.

```python
timedelta_to_seconds(td)
parse_date(value)
serialize_date(value)
parse_date_delta(value)
serialize_date_delta(value)
html_escape(value)
```

`parse_date` returns a timezone-aware UTC `datetime` or `None` for missing or unparsable input. `serialize_date` accepts HTTP-date strings/bytes, `datetime`, `date`, time tuples, integer timestamps, float timestamps, and timedeltas; timedeltas are relative to the current time. `parse_date_delta` accepts either an HTTP date or a delta-seconds integer. `serialize_date_delta` serializes numbers as integer seconds and other supported values as HTTP dates.

`html_escape(None)` returns an empty string. If an object has a callable `__html__`, that value is returned. Other objects are converted to text, HTML-escaped with quotes, and non-ASCII characters are emitted as numeric character references.

### HTTP Exceptions

`WSGIHTTPException` is both an exception and a `Response`. Public subclasses define `code`, `title`, and default body text for named HTTP statuses. They can be raised and caught as exceptions, returned as responses, or called as WSGI applications.

Constructors accept `detail=None`, `headers=None`, `comment=None`, `body_template=None`, `json_formatter=None`, and response keyword arguments. `headers` are added to the response headers. `detail` appears in generated bodies and is the string value of the exception when present. Classes for empty-body statuses such as 204, 205, and 304 remove `Content-Type` and `Content-Length`.

If an exception already has an explicit body, is an empty-body status, or is serving a `HEAD` request, it behaves like a normal `Response`. Otherwise it generates a body at call time. The generated content type is selected from the request `Accept` header: `text/html` for an acceptable HTML response, `application/json` for an acceptable JSON response, and `text/plain` otherwise. A `HEAD` request returns no body.

Redirect exception classes that accept `location` resolve relative locations against the request URL when called. They reject control characters in `location`. Passing both `location` and `add_slash=True` is invalid. With `add_slash=True`, the redirect location is the current request path with a slash appended and the query string preserved.

`HTTPExceptionMiddleware(application)` catches `HTTPException` raised while initially calling the application and turns it into the corresponding WSGI response. It does not catch exceptions raised later by the returned body iterator.

## Behavioral Sections

### Request and Environ

A request is a live wrapper around its WSGI environment. Setting request attributes writes to `environ`; changing `environ` is reflected by later attribute access unless a cached parsed view is still valid for the same source value. Header access uses HTTP names while storage uses WSGI/CGI names.

URL-producing attributes derive from `wsgi.url_scheme`, `HTTP_HOST` or `SERVER_NAME`/`SERVER_PORT`, `SCRIPT_NAME`, `PATH_INFO`, and `QUERY_STRING`. Default ports are omitted in `host_url`. `application_url` includes `SCRIPT_NAME`; `path_url` includes `SCRIPT_NAME` and `PATH_INFO`; `url` includes the query string. `relative_url` resolves against `path_url` by default and against `application_url` when `to_application=True`.

`path_info_pop(pattern=None)` consumes the next non-empty path segment from `PATH_INFO`, appends it to `SCRIPT_NAME` with the consumed slashes, and returns the segment. If there is no segment or the optional regular expression does not match, it returns `None` and leaves the request unchanged. `path_info_peek()` returns the next segment without mutation.

Conditional request helpers use WebOb matching objects. Missing `If-Match` behaves as `AnyETag`, so containment succeeds. Missing `If-None-Match` behaves as `NoETag`, so containment fails. `remove_conditional_headers` removes the selected freshness, range, and encoding headers without removing `If-Match` or `If-Unmodified-Since`.

### Response State

A response keeps all public projections consistent with the same response state. Header properties such as `content_length`, `content_range`, `date`, `expires`, `last_modified`, `etag`, `retry_after`, `allow`, `vary`, and authentication headers parse and serialize their corresponding HTTP header fields. Setting a header property to `None` removes the header when that property supports deletion.

`Response.copy()` materializes the current app iterator into a reusable list, closes the original iterator if needed, and returns a new response with copied status, header list, app iterator, and conditional-response flag.

`Response.from_file(fileobj)` reads the textual representation produced by `str(resp)` or an HTTP-style status line, parses headers, requires the response's content length to know how much body to read, and returns a response with that body.

### Static Serving

`FileApp` and `DirectoryApp` are ordinary WSGI applications that return WebOb responses and exceptions. Their file responses participate in conditional response handling in the same way as manually constructed responses: validators and range requests are interpreted through the request headers, `HEAD` suppresses the body, and response metadata is preserved in headers.

### Exception Responses

HTTP exception responses are regular responses with class-selected status. They are useful both for returning from a WSGI app and for raising through a WebOb-aware wrapper. Body generation is lazy so the request `Accept` header can choose plain text, HTML, or JSON at WSGI call time.

## Error Semantics

- `Request(environ)` raises `TypeError` unless `environ` is a plain `dict`.
- Passing an unknown keyword to `Request` or `Response` construction raises `TypeError`.
- Setting `Request.body` to anything other than bytes raises `TypeError`; setting `Request.text` to non-text raises `TypeError`; accessing request text without a charset raises `AttributeError`.
- `Request.blank(base_url=...)` raises `ValueError` if the base URL contains a query string or fragment, and `TypeError`/`ValueError` for unsupported URL schemes in URL construction paths.
- `Request.from_bytes` raises `ValueError` if bytes remain after a complete request has been parsed. `Request.from_file` raises `ValueError` for a bad request line.
- Form POST construction rejects file-like form values with `application/x-www-form-urlencoded` and rejects non-bytes POST data for arbitrary non-form content types with `ValueError`.
- `MultiDict.getone` raises `KeyError` for missing keys and for keys with multiple values. `MultiDict.view_list` raises `TypeError` unless the supplied object is an actual list.
- `NestedMultiDict` and `NoVars` mutation methods raise `KeyError`.
- `Response` construction raises `TypeError` when both `body` and `app_iter` are supplied. Setting `Response.body` to text raises `TypeError`; `Response.text` must be text; writing text without a response charset raises `TypeError`.
- Setting `Response.status` to a non-string, non-integer raises `TypeError`; setting it to a string whose first token is not an integer raises `ValueError`.
- Setting `Response.charset` when no `Content-Type` header exists raises `AttributeError`.
- Reading `Response.body` raises `AttributeError` when no body iterator exists and raises `AssertionError` when an existing `Content-Length` conflicts with the actual consumed body length.
- `Response.unset_cookie(name, strict=True)` raises `KeyError` if no matching cookie has been set on the response.
- `Response.decode_content()` raises `ValueError` for unsupported content encodings.
- `ContentRange(start, stop, length)` raises `ValueError` for invalid byte-range combinations.
- `CacheControl` raises `AttributeError` when a request-only directive is assigned on a response cache-control object or a response-only directive is assigned on a request cache-control object.
- `make_cookie` raises `ValueError` for invalid `max_age` values and for invalid `samesite` values while SameSite validation is enabled.
- `CookieProfile.get_value()` raises `ValueError` when the profile is not bound to a request. `CookieProfile.get_headers` raises `ValueError` when the serialized cookie value is too long.
- `Base64Serializer.loads` and `SignedSerializer.loads` raise `ValueError` for malformed data; `SignedSerializer.loads` also raises `ValueError` for an invalid signature.
- `DirectoryApp(path)` raises `OSError` when the path is not an existing directory.
- `SendRequest` raises `ValueError` for unknown URL schemes and for environments with neither `SERVER_NAME` nor `HTTP_HOST`.
- Redirect HTTP exceptions reject control characters in `location` with `ValueError` and reject specifying both `location` and `add_slash=True` with `TypeError`.

## Cross-View Invariants

- A `Request` attribute and the corresponding WSGI `environ` key are two views of the same request fact; mutating one is visible through the other.
- `req.headers` and `req.environ` are synchronized through HTTP/CGI header name translation; request headers are single-valued because the WSGI environment is single-valued.
- `req.host_url`, `req.application_url`, `req.path_url`, `req.path`, `req.path_qs`, and `req.url` are consistent projections of scheme, host, script name, path info, and query string.
- `req.path_info_pop()` changes both routing views together: the consumed segment leaves `PATH_INFO`, enters `SCRIPT_NAME`, and affects later URL properties.
- `req.GET`, `req.POST`, and `req.params` preserve repeated variables in order; single-value lookup on `req.params` prefers query-string values over body values.
- `req.body`, `req.body_file`, `CONTENT_LENGTH`, and the seekable-body behavior remain consistent after reading, setting, copying, and constructing requests with `POST`.
- `resp.headerlist` and `resp.headers` are the same ordered response headers; case-insensitive mapping operations mutate the ordered list that WSGI callers receive.
- `resp.status`, `resp.status_code`, and `resp.status_int` are the same status; changing one updates the others' observable value.
- `resp.body`, `resp.text`, `resp.json`, `resp.app_iter`, `resp.body_file`, and `Content-Length` remain synchronized through reads and writes, except that assigning an arbitrary app iterator intentionally clears `Content-Length`.
- `resp.content_type`, `resp.charset`, and `resp.content_type_params` are coordinated views over the `Content-Type` header.
- Response cache-control properties and request cache-control properties update their corresponding `Cache-Control` headers immediately when the bound object is mutated.
- Conditional response handling preserves the original response metadata while changing only the observable status, entity headers, and body iterator required by freshness, range, and HEAD semantics.
- Cookie helper APIs produce `Set-Cookie` headers that are visible through `resp.headerlist`, `resp.headers.getall("Set-Cookie")`, and WSGI response headers.
- HTTP exception instances behave as exceptions, response objects, and WSGI applications with the same status and headers.

## Representative Workflow

```python
from datetime import datetime

from webob import Request, Response, UTC
from webob.exc import HTTPNotFound


def app(environ, start_response):
    req = Request(environ)

    name = req.params.get("name", "world")
    if req.path_info != "/hello":
        return HTTPNotFound("No route matched")(environ, start_response)

    resp = Response(text="Hello %s" % name, content_type="text/plain")
    resp.last_modified = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
    resp.set_cookie("visited", "yes", max_age=3600, httponly=True)
    resp.conditional_response = True
    return resp(environ, start_response)


req = Request.blank("/hello?name=WebOb")
response = req.get_response(app)
assert response.status == "200 OK"
assert response.text == "Hello WebOb"
assert response.headers.getall("Set-Cookie")
```

This workflow demonstrates the intended model: request data is read through a mutable wrapper over WSGI `environ`; the application constructs a response object; headers, cookies, and body projections remain synchronized; HTTP exceptions can be returned as WSGI applications; and `Request.get_response` turns a WSGI call back into a `Response`.

## Non-Goals

- WebOb does not define a web framework, router, templating system, server, or application lifecycle.
- WebOb does not promise to parse every possible raw HTTP request or response; `from_file`, `from_bytes`, and stringification handle WebOb's own textual representation and common HTTP-style forms.
- WebOb does not make request header storage multi-valued; incoming request headers are represented by the WSGI environment.
- WebOb does not guarantee that parsed Accept header containment methods are fully RFC-perfect; several compatibility methods intentionally keep historical behavior while newer methods expose stricter matching.
- WebOb does not provide cryptographic confidentiality for signed cookies; signing prevents undetected tampering, not reading.
- WebOb does not catch exceptions raised while iterating a WSGI response body through `HTTPExceptionMiddleware`.
- Implementation-specific helper functions, local storage choices, and private extension points are outside this public contract.

## Evaluation Notes

Evaluation focuses on observable WebOb behavior from public APIs: request/environ synchronization, response/header/body synchronization, multi-value mapping semantics, parsed HTTP helper objects, cookie serialization, static-file applications, WSGI decorator behavior, client sending behavior, and HTTP exception responses. Scoring is based on whether public calls, mutations, returned objects, WSGI outputs, and documented exceptions match the contract described here. The assessment does not require a particular internal organization or helper design.
