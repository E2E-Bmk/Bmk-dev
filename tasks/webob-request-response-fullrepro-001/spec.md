
# WebOb Specification

## Product Overview

WebOb provides Python objects for HTTP requests and responses by wrapping the WSGI request `environ` dictionary and the WSGI response triple of status, headers, and body iterator. A request object must expose parsed, writable views of URL parts, headers, cookies, query variables, form variables, conditional headers, and WSGI subrequest execution. A response object must expose parsed, writable views of status, headers, body bytes, text, JSON, cookies, cache headers, conditional response handling, and WSGI application behavior.

The primary design rule is that each high-level view must project one underlying HTTP/WSGI state. A write through a public view must be visible through the other public views that describe the same state, and invalid writes must raise the documented Python exception instead of silently corrupting the state.

## Scope

This specification covers:

- Request construction from WSGI environ dictionaries, blank URLs, HTTP bytes/text/file input, and WSGI application calls.
- Response construction, WSGI response emission, status/header/body projections, cookies, caching, compression, ETag and range handling.
- Multi-value dictionaries and header views used by request and response objects.
- Accept, Cache-Control, Range, Content-Range, ETag, and If-Range parser objects exposed through request and response properties.
- Cookie generation, cookie profiles, signed cookie profiles, and serializers.
- HTTP exception response classes, exception middleware, static file applications, outbound WSGI-over-HTTP sending, and the `wsgify` decorator.
- Top-level datetime helpers and `html_escape`.

## Installable Surface

The package must be importable as `webob`.

Top-level imports:

```python
from webob import Request, Response, UTC
from webob import day, week, hour, minute, second, month, year
from webob import html_escape
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
from webob.static import FileApp, DirectoryApp
from webob.client import SendRequest, send_request_app
from webob.dec import wsgify
```

`webob.exc` must export the base exception classes, all concrete public `HTTP*` status classes, `HTTPExceptionMiddleware`, and `status_map`.

## Public API

### Requests

`Request(environ, **kw)` and `BaseRequest(environ, **kw)` must wrap a WSGI environ dictionary. The constructor must raise `TypeError` when `environ` is not a plain `dict`. Each keyword argument must name an existing request attribute; unknown keywords must raise `TypeError`. The `method` keyword must be applied before body-related keywords.

`Request.blank(path, environ=None, base_url=None, headers=None, POST=None, **kw)` must create a complete minimal WSGI environ for the supplied URL path. The path must be URL-decoded into `PATH_INFO`, and the query string must be stored in `QUERY_STRING`. `base_url` must set scheme, host, port, and script name; when an HTTP or HTTPS base URL omits its default port, `host` must still include the effective port and `host_port` must return that port as a string. A `base_url` with a query or fragment must raise `ValueError`, and an unknown URL scheme must raise `ValueError`. Supplied `environ` values must replace generated environ values. Supplied `headers` must update the request header view. `POST` must create a form body and must select `POST` as the request method for non-`POST`/`PUT` methods. File values submitted with `application/x-www-form-urlencoded` must raise `ValueError`.

The request must expose these core properties:

- URL and environ views: `method`, `scheme`, `http_version`, `script_name`, `path_info`, `path`, `path_qs`, `host`, `host_port`, `host_url`, `application_url`, `path_url`, `url`, `relative_url(other_url, to_application=False)`, `domain`, `client_addr`, `remote_user`, `remote_host`, `remote_addr`, `server_name`, `server_port`, `query_string`, `content_type`, `content_length`.
- Body views: `body`, `body_file`, `body_file_raw`, `body_file_seekable`, `is_body_readable`, `is_body_seekable`, `text`, `json`, `json_body`.
- Variable and cookie views: `GET`, `POST`, `params`, `cookies`, `charset`, `decode(charset=None, errors='strict')`.
- Header views: `headers`, `accept`, `accept_charset`, `accept_encoding`, `accept_language`, `authorization`, `cache_control`, `date`, `if_match`, `if_none_match`, `if_modified_since`, `if_unmodified_since`, `if_range`, `max_forwards`, `pragma`, `range`, `referer`, `referrer`, `user_agent`.
- Request utilities: `path_info_peek()`, `path_info_pop(pattern=None)`, `copy()`, `copy_get()`, `make_body_seekable()`, `copy_body()`, `remove_conditional_headers(remove_encoding=True, remove_range=True, remove_match=True, remove_modified=True)`, `as_bytes(skip_body=False)`, `as_text(skip_body=False)`, `from_bytes(b)`, `from_text(s)`, `from_file(fp)`, `call_application(application, catch_exc_info=False)`, `send(application=None, catch_exc_info=False)`, and `get_response`.

`Request` must store ad hoc public attributes in the wrapped environ so another `Request` over the same environ returns the same attribute. Deleting a missing ad hoc attribute must raise `AttributeError`.

### Responses

`Response(body=None, status=None, headerlist=None, app_iter=None, content_type=None, conditional_response=None, charset=<default marker>, **kw)` must represent a WSGI response. The constructor must accept either `body` or `app_iter`, and must raise `TypeError` when both are supplied. Unknown keyword arguments must raise `TypeError`. Without arguments, it must create status `200 OK`, a default `Content-Type` of `text/html; charset=UTF-8`, a `Content-Length` of `0`, and an empty byte body.

The response must expose these core properties:

- Status views: `status`, `status_code`, and `status_int`.
- Header views: `headerlist`, `headers`, `content_type`, `charset`, `content_type_params`, `content_length`, `content_encoding`, `content_language`, `content_location`, `content_md5`, `content_disposition`, `accept_ranges`, `content_range`, `date`, `expires`, `last_modified`, `etag`, `etag_strong`, `location`, `pragma`, `age`, `retry_after`, `server`, `www_authenticate`, `allow`, `vary`, and `cache_control`.
- Body views: `body`, `text`, `unicode_body`, `ubody`, `json`, `json_body`, `body_file`, `app_iter`, `has_body`.
- Methods: `from_file(fp)`, `copy()`, `write(text)`, `set_cookie(name, value='', max_age=None, path='/', domain=None, secure=False, httponly=False, comment=None, overwrite=False, samesite=None)`, `delete_cookie(name, path='/', domain=None)`, `unset_cookie(name, strict=True)`, `merge_cookies(resp)`, `cache_expires(seconds=0, **attrs)`, `encode_content(encoding='gzip', lazy=False)`, `decode_content()`, `md5_etag(body=None, set_content_md5=False)`, `conditional_response_app(environ, start_response)`, `app_iter_range(start, stop)`, and WSGI `__call__(environ, start_response)`.

`Response.from_file(fp)` must read the representation emitted by `str(response)`. A malformed header line must raise `ValueError`. `Response.copy()` must return an independent response object with copied status, header list, app iterator contents, and conditional response flag.

### Multi-Value and Header Dictionaries

`MultiDict(*args, **kw)` must store an ordered list of key/value pairs. `__getitem__(key)` must return the last value for that key and must raise `KeyError` when the key is absent. `getall(key)` must return all matching values in storage order and must return an empty list when absent. `getone(key)` must return the only matching value, must raise `KeyError` when no value exists, and must raise `KeyError` when multiple values exist. `items()`, `keys()`, and `values()` must include repeated keys. `add(key, value)` must append without removing existing values. `__setitem__` must remove all existing values for the key before appending the new value. `update()` must overwrite dictionary-style duplicate keys; `extend()` must append incoming items.

`NestedMultiDict(*dicts)` must provide a read-only merged view. `__getitem__` must return the first child dictionary value that contains the key. `getall(key)` must concatenate values from each child dictionary in child order. Mutating operations including item assignment, `add`, deletion, `clear`, `setdefault`, `pop`, `popitem`, and `update` must raise `KeyError`.

`NoVars(reason=None)` must act as an empty read-only variable mapping. Reads through `get()` must return the supplied default, `getall()` must return an empty list, `mixed()` and `dict_of_lists()` must return empty dictionaries, and mutating operations must raise `KeyError`.

`ResponseHeaders` must be a case-insensitive `MultiDict` view over a response `headerlist`. Setting a header key must remove all existing headers with the same case-insensitive name and append the new header. `add()` must preserve repeated headers. `getall()` must return every matching value in header order.

`EnvironHeaders(environ)` must map HTTP header names to WSGI CGI keys. `Content-Type` and `Content-Length` must map to `CONTENT_TYPE` and `CONTENT_LENGTH`; other headers must map to `HTTP_` keys. Missing headers must raise `KeyError`.

### Cookies and Serializers

`make_cookie(name, value, max_age=None, path='/', domain=None, secure=False, httponly=False, comment=None, samesite=None)` must return one `Set-Cookie` header value. A `None` value must produce an expired empty-value cookie. `max_age` must accept integer-compatible values and `datetime.timedelta`; non-integer-compatible values must raise `ValueError`. `samesite` must accept `strict`, `lax`, `none`, or `None`; accepted SameSite values must be serialized with the supplied lowercase token, so `samesite='lax'` returns a header containing `SameSite=lax`. Invalid values must raise `ValueError` while SameSite validation is enabled.

`Response.set_cookie()` must append a `Set-Cookie` header. With `overwrite=True`, it must remove existing response cookies with the same name before appending the new cookie. A `None` value must delete the client cookie. `delete_cookie()` must set an empty cookie with immediate expiration. `unset_cookie(name, strict=True)` must remove matching `Set-Cookie` headers from the response object and must raise `KeyError` when strict mode is true and no matching response cookie exists. `merge_cookies(resp)` must add this response's `Set-Cookie` headers to another `Response`, or must return a WSGI wrapper that appends those headers to a non-`Response` application.

`JSONSerializer.dumps()` must return UTF-8 JSON bytes, and `loads()` must parse UTF-8 JSON bytes. `Base64Serializer` must wrap another serializer with URL-safe base64 and must raise `ValueError` for malformed base64. `SignedSerializer(secret, salt, hashalg='sha512', serializer=None)` must prepend an HMAC signature to serialized bytes, encode the result with URL-safe base64 without required padding, and must raise `ValueError` when base64 decoding fails or the signature does not match.

`CookieProfile(cookie_name, secure=False, max_age=None, httponly=None, samesite=None, path='/', domains=None, serializer=None)` must bind to a request through `bind(request)` or `profile(request)`. An unbound profile `get_value()` must raise `ValueError`. A bound profile must return `None` when the named request cookie is missing or cannot be deserialized. `get_headers(value, ...)` must return `Set-Cookie` header tuples, one per configured domain or one header without a domain. Values longer than the supported cookie size must raise `ValueError`. `set_cookies(response, value, ...)` must append those headers to the response and return the response.

`SignedCookieProfile(secret, salt, cookie_name, ...)` must behave like `CookieProfile` with a `SignedSerializer`; tampered cookie input must return `None` from `get_value()` through the profile's deserialization failure path.

### Header Parser Objects

`create_accept_header(header_value)`, `create_accept_charset_header(header_value)`, `create_accept_encoding_header(header_value)`, and `create_accept_language_header(header_value)` must return an object representing a valid header, a missing header, or an invalid header.

Valid Accept objects must support string conversion, representation, truth testing, iteration in preference order, containment checks, `quality(offer)`, `acceptable_offers(offers)`, and `best_match(offers, default_match=None)`. Missing Accept headers must represent the protocol default that ordinary offers are acceptable; invalid Accept headers must remain printable and iterable without raising during ordinary inspection. `MIMEAccept` must remain a deprecated compatibility alias with matching accept behavior.

`AcceptLanguage` objects must also support `basic_filtering(language_tags)`, `lookup(language_tags, default_range=None, default_tag=None, default=None)`, and `best_match(offers, default_match=None)`. A fallback language must be returned by `best_match` only when it is both present in the offers and supplied as `default_match`.

`CacheControl.parse(header, updates_to=None, type=None)` must return a `CacheControl` object exposing request directives `max_stale`, `min_fresh`, `only_if_cached`, shared directives `no_cache`, `no_store`, `no_transform`, `max_age`, and response directives `public`, `private`, `must_revalidate`, `proxy_revalidate`, `s_maxage`, `s_max_age`, `stale_while_revalidate`, and `stale_if_error`. Numeric directive getters such as `max_age` must return integers when a numeric directive value is present. Setting or deleting directive attributes on a request or response bound cache-control object must rewrite the associated `Cache-Control` header. Unsupported directives for the object's type must raise `AttributeError`.

`Range.parse(header)` must parse a single bytes range into a `Range(start, end)` object using Python-style non-inclusive `end`; invalid range headers must return `None`. `Range.content_range(length)` must return a `ContentRange` when satisfiable and must return `None` when not satisfiable. `ContentRange.parse(value)` must return a `ContentRange` for valid `bytes start-stop/length` and `bytes */length` forms and must return `None` for invalid input. Constructing an invalid `ContentRange` must raise `ValueError`.

`ETagMatcher.parse(value, strong=True)` must parse ETag lists. A value of `*` must return `AnyETag`. Strong parsing must ignore weak ETags; non-strong parsing must include them. `AnyETag` must be false in boolean context and must contain every tested tag. `NoETag` must be false in boolean context and must contain no tested tag. `IfRange.parse(value)` must parse empty input as an always-matching ETag sentinel, `GMT` date input as a date matcher, and other input as an ETag matcher.

### HTTP Exceptions

`webob.exc` must expose `HTTPException`, `WSGIHTTPException`, status-family bases `HTTPError`, `HTTPRedirection`, `HTTPOk`, `HTTPClientError`, `HTTPServerError`, all public concrete `HTTP*` status classes, `HTTPExceptionMiddleware`, and `status_map`.

Every `WSGIHTTPException` subclass must also be a response and a WSGI application. Construction must accept `detail=None`, `headers=None`, `comment=None`, `body_template=None`, `json_formatter=None`, and response keyword arguments unless the concrete redirect class replaces the signature with `location` and `add_slash`. `headers` must extend the response headers. Empty-body status classes such as `HTTPNotModified` must remove content headers and emit no body.

Calling an HTTP exception as a WSGI application must return a response body based on request `Accept`: `text/html` must produce HTML, `application/json` must produce JSON, and no supported match must produce plain text. HEAD requests must return an empty iterable while preserving response headers.

Redirect classes that require a location must accept `location=None` and `add_slash=False`. A supplied location containing carriage return or line feed must raise `ValueError`. Supplying both `location` and `add_slash=True` must raise `TypeError`. Relative locations must be resolved against the request path URL when the exception is called as WSGI.

`HTTPExceptionMiddleware(application)` must catch `HTTPException` raised during the initial application call and must invoke the exception as the response. It must not promise to catch exceptions raised later by the returned body iterator.

### Static Files, Client, and Decorator

`FileApp(filename, **kw)` must be a WSGI application serving the named file. `GET` and `HEAD` must be allowed; other methods must return `HTTPMethodNotAllowed`. A missing file must return `HTTPNotFound`; an open-permission failure must return `HTTPForbidden`. Successful responses must include inferred content type, content encoding, `Accept-Ranges: bytes`, file size, last-modified time, and conditional/range response behavior.

`DirectoryApp(path, index_page='index.html', hide_index_with_redirect=False, **kw)` must serve files below the absolute directory path. Construction must raise `OSError` when the path is not an existing directory. Requests escaping the directory must return `HTTPForbidden`; missing files must return `HTTPNotFound`. Directory requests must serve `index_page` when it exists, must redirect to a trailing slash before serving an index, and must redirect direct index-page URLs to the containing directory URL when `hide_index_with_redirect=True`.

`SendRequest(HTTPConnection=..., HTTPSConnection=...)` and `send_request_app` must turn a WSGI request environ into an outbound HTTP or HTTPS request. Unknown schemes must raise `ValueError`. If neither `SERVER_NAME` nor `HTTP_HOST` is present, it must raise `ValueError`. Socket timeout must produce `HTTPGatewayTimeout`; name-resolution failure must produce `HTTPBadGateway`. Response headers returned to WSGI must exclude `Transfer-Encoding`.

`wsgify(func=None, RequestClass=None, args=(), kwargs=None, middleware_wraps=None)` must convert a request-taking function into an object callable both as a WSGI app and as a normal function with a request object. Calling an unbound decorator with additional arguments must raise `TypeError`. Calling a bound decorator as WSGI with the wrong signature must raise `TypeError`. In WSGI mode, it must create a request, attach a default response as `req.response`, call the function, convert `None` to `req.response`, convert `str` or `bytes` returns into the response body, turn raised WebOb HTTP exceptions into responses, and merge cookies from `req.response` into returned responses or WSGI apps. `wsgify.middleware` must create middleware factories that pass the wrapped application as the first function argument.

### Datetime and HTML Helpers

`UTC` must be a UTC `tzinfo` object. `day`, `week`, `hour`, `minute`, and `second` must be `datetime.timedelta` constants with their named durations. `month` must be a 30-day timedelta and `year` must be a 365-day timedelta. `timedelta_to_seconds(td)` must return whole seconds from days and seconds.

`parse_date(value)` must return a UTC `datetime` for parseable HTTP dates and must return `None` for empty, non-string-convertible, or unparsable input. `serialize_date(dt)` must accept bytes, text, `timedelta`, `datetime`, `date`, time tuple, integer, or float input and must return an HTTP date string; unsupported input must raise `ValueError`. `parse_date_delta(value)` must parse integer delta seconds relative to current time and must fall back to HTTP-date parsing. `serialize_date_delta(value)` must return integer seconds for numeric input and otherwise must use `serialize_date`.

`html_escape(s)` must return an empty string for `None`, must call `s.__html__()` when that method exists, must convert other objects to text, and must return HTML-escaped text with non-ASCII characters represented as XML character references.

## Product State Model

WebOb has three public projections of core state:

- Request state: the WSGI `environ` dictionary plus its body stream.
- Response state: status string, ordered header list, body iterator, and response flags.
- Parsed helper state: dictionary-like, cookie, cache, accept, ETag, and range objects that are returned from request or response properties.

Each projection must stay synchronized with the underlying state it represents. A parsed helper returned from a request or response property must reflect the current header or environ value, and a helper mutation that is documented as writable must rewrite the corresponding header or environ value. A parsed helper that represents an invalid or missing header must remain safe to inspect through its documented methods and must not corrupt the underlying request or response.

## Behavioral Sections

### Request Behavior

Request URL attributes must be derived from WSGI `SCRIPT_NAME`, `PATH_INFO`, `QUERY_STRING`, `HTTP_HOST`, `SERVER_NAME`, `SERVER_PORT`, and `wsgi.url_scheme`. `host` must return the effective host with its effective port, and `host_port` must return the effective port as text. `host_url` must omit default ports for HTTP and HTTPS. `application_url` must include `SCRIPT_NAME` and must omit `PATH_INFO` and query string. `path_url` must include `SCRIPT_NAME` and `PATH_INFO` and must omit query string. `url` must include query string when `QUERY_STRING` is non-empty. Missing required WSGI keys must raise `KeyError` through the accessed property.

`path_info_peek()` must return the next non-empty path segment without changing the request and must return `None` when no segment exists. `path_info_pop(pattern=None)` must move the next segment from `PATH_INFO` to `SCRIPT_NAME` and return it. It must return `None` without changing the request when no segment exists or when `pattern` is supplied and does not match.

`body` must return bytes. Setting `body` to bytes must replace `wsgi.input`, set `CONTENT_LENGTH`, and mark the body seekable. Setting `body` to `None` must store an empty byte body. Setting `body` to any non-bytes non-`None` value must raise `TypeError`. Setting `body_file` to bytes must raise `ValueError`; setting it to a file-like object must reset content length and mark the input readable but not seekable. Accessing `text` must require a charset and must raise `AttributeError` when no charset is available; setting `text` to a non-string must raise `TypeError`. `json` and `json_body` must decode and encode request bodies using the request charset.

`GET` must parse `QUERY_STRING` into a `GetDict`. Mutating that object must rewrite `environ['QUERY_STRING']`. `POST` must return a `MultiDict` for form submissions using `application/x-www-form-urlencoded`, `multipart/form-data`, or an empty content type on a POST-like request. For non-form requests, `POST` must return `NoVars`. Form parsing with a non-UTF-8 charset must raise `DeprecationWarning`. `params` must return a `NestedMultiDict` over `GET` followed by `POST`: `params[key]` must return the query value when the same key exists in both, and `params.getall(key)` must return query values followed by form values.

`cookies` must return a dict-like request cookie object backed by the `Cookie` header. Assigning a mapping to `cookies` must replace the request cookie header. Cookie reads for missing keys must follow ordinary mapping `KeyError` or default-return behavior.

`copy()` must shallow-copy the environ and must copy the request body so the copy has an independent body stream. `copy_get()` must copy the environ, force method `GET`, remove content type so `content_type` returns an empty string, and set an empty body.

`remove_conditional_headers()` must remove only the selected conditional request headers. Its boolean arguments must control removal of `Accept-Encoding`, `If-Range`/`Range`, `If-None-Match`, and `If-Modified-Since`.

`call_application(application, catch_exc_info=False)` must call a WSGI application with the request environ and return `(status, headers, app_iter)`. If the WSGI application supplies `exc_info` and `catch_exc_info` is false, the original exception must be raised. If `catch_exc_info` is true, the return tuple must include the captured `exc_info` as a fourth value. `send()` and `get_response()` must wrap that result in the request's `ResponseClass`; with no application they must use the default HTTP-sending app.

### Response Behavior

Setting `status` to an integer must convert it to the standard status string for known codes and a generic family reason for unknown codes. Setting `status` to a string must require the first token to be an integer and must raise `ValueError` otherwise. Setting `status` to a non-string non-integer must raise `TypeError`. `status_code` and `status_int` must return the integer code and must update `status` when assigned.

`headerlist` must be the ordered response header list. `headers` must be a case-insensitive `ResponseHeaders` view over that list. Mutating `headers` must mutate `headerlist`, and replacing `headerlist` must reset the cached `headers` view.

`body` must return bytes and must consume `app_iter` into a single byte body when needed. If `Content-Length` exists and differs from the consumed body length, reading `body` must raise `AssertionError`. Setting `body` must require bytes and must raise `TypeError` for text or other objects. Setting `text` must require a string and must encode using `charset` or `default_body_encoding`; if neither exists, it must raise `AttributeError`. `write(text)` must accept bytes. It must accept text only when `charset` is set and must raise `TypeError` otherwise. `app_iter` assignment must clear an automatic content length.

`content_type` assignment must update the `Content-Type` header and must add the default charset for `text/html`, `text/*`, `application/xml`, and `*/*+xml` content types when a default charset exists and no charset is supplied. Assigning non-string truthy content type values must raise `TypeError`. Setting `charset` without a `Content-Type` header must raise `AttributeError`. `content_type_params` assignment must rewrite the parameters on `Content-Type`; values needing quoting must be quoted.

`cache_expires(0)` must set cache-control directives for an immediately uncacheable response, must set `Expires`, must set `Last-Modified` when absent, and must set `Pragma: no-cache`. Positive seconds must clear existing cache-control properties, set `max-age`, make `res.cache_control.max_age` return the integer seconds value, set `Expires`, and remove `Pragma`. A `datetime.timedelta` value must be converted to seconds.

`encode_content('gzip')` must gzip the body iterator and set `Content-Encoding: gzip`; repeated gzip encoding must leave an already gzipped response unchanged. `encode_content('identity')` must decode content. Any other encoding must raise `AssertionError`. `decode_content()` must support `gzip` and `deflate`, must clear `Content-Encoding`, and must raise `ValueError` for unknown encodings.

`Response.__call__` must act as a WSGI application. It must absolutize `Location` headers relative to the incoming request URI. A `HEAD` request must return an empty iterable while preserving headers. With `conditional_response` true, it must process conditional and range requests. Matching `If-None-Match` or `If-Modified-Since` on `GET` or `HEAD` must return `304 Not Modified` with entity headers filtered. A satisfiable byte range on a 200 response with known content length must return `206 Partial Content`; an unsatisfiable range must return `416 Requested Range Not Satisfiable`; a non-range or ineligible request must return the original response status and body.

### Exception and WSGI Helper Behavior

HTTP exception responses must derive status, title, and default body from the concrete exception class. `status_map` must map concrete public status codes to their exception classes. Generated exception bodies must escape HTML in HTML output, strip tags for plain text output, and pass JSON output through the selected JSON formatter.

`FileApp` and `DirectoryApp` must return WebOb response or exception objects through WSGI. Static file responses must use conditional response handling so request `Range`, `If-Range`, and safe-method conditional headers affect the emitted status and body.

`wsgify` must preserve the wrapped function as `undecorated`, must support descriptor binding for methods, and must let subclasses override `RequestClass` or `call_func`. In middleware mode, the wrapped application must be supplied to the middleware function before configured positional arguments.

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

## Representative Workflow(s)

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

## Non-Goals

- This specification does not require private helper names, private descriptors, private parser functions, or environment-specific scaffolding.
- This specification does not require exact internal storage names, cached attribute names, singleton implementation details, or algorithm step order.
- This specification does not require optional performance measurement utilities.
- This specification does not require external network availability for ordinary request/response, parser, cookie, static-file, or decorator behavior.
- This specification does not require implementation of undocumented compatibility aliases beyond the public import paths and documented behavior listed above.
- This specification does not require byte-for-byte reproduction of generated default HTML beyond status, content type selection, escaping, and inclusion of documented detail/comment content.

## Invocation Protocol

- Console script name: `TBD`
- `python -m webob`: `not supported`
- Exit codes:
  - `0`: success
  - `1`: `python -m webob` cannot execute because the package has no `__main__` module

## Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Evaluation Notes

Evaluation checks observable behavior through public imports and documented workflows. It exercises request/environ synchronization, response/header/body synchronization, MultiDict duplicate-key semantics, cookies and signed cookies, parsed headers, conditional and range responses, HTTP exceptions, static file WSGI behavior, `wsgify`, and representative serialization helpers.

Evaluation checks public behavior, exception types, return values, and cross-view invariants. They do not check private helper names, internal cache fields, environment-specific scaffolding, or private module organization.
