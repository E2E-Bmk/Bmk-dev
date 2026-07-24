# HTTPX Specification

## Product Overview

HTTPX is an HTTP client library with synchronous and asynchronous APIs. It exposes one-shot helper functions, reusable clients, request and response models, URL and collection models, authentication helpers, custom transport hooks, in-process WSGI/ASGI transports, a mock transport, public exception classes, and a command line entry point.

This document describes the public client and model behavior needed to build, send, inspect, stream, and close requests without depending on live external services.

## Scope

This specification covers:

- Top-level helper functions: `request`, `stream`, `get`, `options`, `head`, `post`, `put`, `patch`, and `delete`.
- `Client` and `AsyncClient` construction, context-manager lifecycle, `is_closed`, request helpers, `build_request`, `send`, `stream`, `close`, and `aclose`.
- Request construction and dispatch through `MockTransport`, `WSGITransport`, `ASGITransport`, `BaseTransport`, and `AsyncBaseTransport`.
- `Request`, `Response`, `URL`, `QueryParams`, `Headers`, `Cookies`, `ByteStream`, `SyncByteStream`, and `AsyncByteStream`.
- Client-level and request-level headers, cookies, query parameters, auth, redirects, response history, `next_request`, event hooks, and stream/read state.
- Public auth helpers: `Auth`, `BasicAuth`, `DigestAuth`, `NetRCAuth`, and callable auth via `FunctionAuth`.
- Public exception classes that callers catch for request errors, HTTP status errors, stream state errors, cookie lookup conflicts, and invalid URLs.
- Selected `httpx` command line behavior for option parsing, request method selection, output/download handling, and exit status.

## Product State Model

HTTPX presents one shared request/response exchange through three public projections:

- The client projection stores reusable configuration: `base_url`, `headers`, `cookies`, `params`, `auth`, `event_hooks`, redirect policy, timeout configuration, and transport.
- The request projection stores the prepared outgoing exchange: `method`, normalized `url`, `headers`, `content` or stream, and extensions.
- The response projection stores the returned exchange: `status_code`, `headers`, content or stream state, associated `request`, redirect `history`, cookies extracted from response headers, and derived properties such as status category booleans.

Core invariants:

- A value prepared by `Client.build_request(...)` must be visible through the returned `Request` object's `url`, `headers`, `content`, and cookie header before the request is sent; if request content is streaming and has not been read, `Request.content` raises `RequestNotRead`.
- A `Response` returned by `Client.send(...)`, `Client.request(...)`, or a method helper must reference the final `Request` through `response.request`; if a response has no associated request, `response.request` raises `RuntimeError`.
- A response body read through `read()` or `aread()` must become available through `content`, `text`, `json()`, and stream state flags; if a streaming response body has not been read, `content` and `text` raise `ResponseNotRead`.
- A streamed response consumed through `iter_bytes()`, `iter_text()`, `iter_lines()`, `iter_raw()`, or their async variants must mark the stream consumed; a second streaming pass raises `StreamConsumed`.
- A closed client must report `is_closed == True`; requests sent after closing raise `RuntimeError`.
- Redirect responses followed by a client must appear in `response.history` in request order, and each history response must retain its own associated request.

## Installable Surface

The package import path is `httpx`. The scoped public names are imported directly from `httpx`:

```python
from httpx import (
    AsyncBaseTransport,
    AsyncByteStream,
    AsyncClient,
    ASGITransport,
    Auth,
    BaseTransport,
    BasicAuth,
    ByteStream,
    Client,
    CookieConflict,
    Cookies,
    DecodingError,
    DigestAuth,
    FunctionAuth,
    Headers,
    HTTPError,
    HTTPStatusError,
    InvalidURL,
    MockTransport,
    NetRCAuth,
    QueryParams,
    Request,
    RequestError,
    RequestNotRead,
    Response,
    ResponseNotRead,
    StreamClosed,
    StreamConsumed,
    StreamError,
    TooManyRedirects,
    URL,
    WSGITransport,
    codes,
    delete,
    get,
    head,
    main,
    options,
    patch,
    post,
    put,
    request,
    stream,
)
```

`HTTPTransport`, `AsyncHTTPTransport`, `Proxy`, `Timeout`, `Limits`, and `create_ssl_context` are public imports, and clients accept their instances in constructor arguments. Their live socket, proxy routing, TLS, pooling, and retry behavior is outside this document.

`USE_CLIENT_DEFAULT` is an exported sentinel used as the default value on client method parameters such as `auth`, `follow_redirects`, and `timeout`. Callers normally leave those parameters omitted to use the client default, pass an explicit value to override it, or pass `auth=None` to disable client-level auth for that request.

## Public API

Top-level synchronous helpers:

```python
httpx.request(method, url, *, params=None, content=None, data=None, files=None,
              json=None, headers=None, cookies=None, auth=None, proxy=None,
              timeout=Timeout(5.0), follow_redirects=False, verify=True,
              trust_env=True) -> Response
httpx.stream(method, url, *, params=None, content=None, data=None, files=None,
             json=None, headers=None, cookies=None, auth=None, proxy=None,
             timeout=Timeout(5.0), follow_redirects=False, verify=True,
             trust_env=True) -> context manager yielding Response
httpx.get(url, *, params=None, headers=None, cookies=None, auth=None,
          proxy=None, follow_redirects=False, verify=True,
          timeout=Timeout(5.0), trust_env=True) -> Response
httpx.options(...)
httpx.head(...)
httpx.post(url, *, content=None, data=None, files=None, json=None, ...)
httpx.put(url, *, content=None, data=None, files=None, json=None, ...)
httpx.patch(url, *, content=None, data=None, files=None, json=None, ...)
httpx.delete(url, *, params=None, headers=None, cookies=None, auth=None, ...)
```

Clients:

```python
Client(*, auth=None, params=None, headers=None, cookies=None, verify=True,
       cert=None, trust_env=True, http1=True, http2=False, proxy=None,
       mounts=None, timeout=Timeout(5.0), follow_redirects=False,
       limits=Limits(max_connections=100, max_keepalive_connections=20,
                     keepalive_expiry=5.0),
       max_redirects=20, event_hooks=None, base_url="", transport=None,
       default_encoding="utf-8")

AsyncClient(*, auth=None, params=None, headers=None, cookies=None, verify=True,
            cert=None, http1=True, http2=False, proxy=None, mounts=None,
            timeout=Timeout(5.0), follow_redirects=False, limits=Limits(...),
            max_redirects=20, event_hooks=None, base_url="", transport=None,
            trust_env=True, default_encoding="utf-8")
```

`Client` exposes `request`, `stream`, `send`, `build_request`, `get`, `options`, `head`, `post`, `put`, `patch`, `delete`, `close`, and context-manager methods. `AsyncClient` exposes async equivalents and `aclose`; `build_request` remains synchronous because it only prepares a `Request`.

Models and transports:

```python
Request(method, url, *, params=None, headers=None, cookies=None,
        content=None, data=None, files=None, json=None, stream=None,
        extensions=None)
Response(status_code, *, headers=None, content=None, text=None, html=None,
         json=None, stream=None, request=None, extensions=None,
         history=None, default_encoding="utf-8")
URL(url="", **kwargs)
QueryParams(*args, **kwargs)
Headers(headers=None, encoding=None)
Cookies(cookies=None)
ByteStream(stream: bytes)
MockTransport(handler)
WSGITransport(app, raise_app_exceptions=True, script_name="",
              remote_addr="127.0.0.1", wsgi_errors=None)
ASGITransport(app, raise_app_exceptions=True, root_path="",
              client=("127.0.0.1", 123))
```

`BaseTransport.handle_request(request)` returns a `Response` for sync clients. `AsyncBaseTransport.handle_async_request(request)` returns a `Response` for async clients. If a transport does not implement the required method, dispatch raises `NotImplementedError`.

## Behavioral Sections

### Client Lifecycle

- `Client` must act as a synchronous context manager. Entering returns the client. Exiting closes the transport and any mounted transports.
- `AsyncClient` must act as an asynchronous context manager. Entering returns the client. Exiting awaits transport closure.
- `client.is_closed` returns `False` before close and `True` after `close()` or `aclose()` completes.
- Calling `close()` or `aclose()` more than once must leave the client closed and return `None`.
- Sending a request after the client is closed raises `RuntimeError`.
- Entering a client context after it has already been closed raises `RuntimeError`.
- Re-entering an already opened client context raises `RuntimeError`.

### Request Building and Sending

- `Client.build_request(method, url, ...)` returns a `Request` without sending it.
- `Client.request(...)` and method helpers must build, send, and return a `Response`.
- `Client.send(request, stream=False, auth=USE_CLIENT_DEFAULT, follow_redirects=USE_CLIENT_DEFAULT)` must send a previously built `Request`. When `stream=False`, the returned response body must be read before return. When `stream=True`, the response body remains streaming and must be read, iterated, or closed by the caller.
- `Client.stream(method, url, ...)` must return a context manager. Entering yields a streaming `Response`; exiting closes the response.
- Async client methods follow the same observable contract, with request helpers and `send` awaited and `stream` used as an async context manager.
- `base_url` must join with relative request URLs. If the client base URL path ends in a path segment, relative request paths resolve under that base path.
- If a request URL is malformed or unsupported as a URL value, URL construction raises `InvalidURL`.
- If no transport is supplied, helper calls use the default HTTP transport. Live network behavior of that transport is outside this document.

### Configuration Merge Rules

These priority rules are verified by conflicting reference calls:

- Client-level and request-level headers must merge. Non-conflicting headers from both levels must be present. When both levels define the same header field, the request-level value wins.
- Client-level and request-level cookies must merge into the outgoing `Cookie` header. Non-conflicting cookies from both levels must be present.
- Client-level query parameters and request-level query parameters must merge. Non-conflicting parameters from both levels must be present. When the same key is present at both levels, the request-level values replace the client-level values for that key.
- Query parameters already present in the request URL are replaced when request-level `params` supplies the same key.
- For auth, timeout, and redirect policy, an explicit request-level value wins over the client default.
- When client auth is configured and a request passes `auth=None`, the outgoing request must not include the client auth credentials.
- When a request leaves `auth` omitted, the client default auth is applied.

If a configuration value has an unsupported type, construction or request preparation raises `TypeError` or the documented public exception for that value category.

### Headers

- `Headers` is a mutable, case-insensitive multi-dict preserving duplicate raw header entries.
- Header lookup by any casing returns the combined comma-separated value for duplicate field names.
- `get_list(key)` returns all values for a field name in insertion order. With `split_commas=True`, comma-separated header values are split according to header-list semantics.
- `multi_items()` returns all field/value pairs, including duplicate field names, with normalized string keys.
- Setting a header replaces all existing entries for that field name. Deleting a header removes all entries for that field name.
- Missing header lookup through `headers[key]` raises `KeyError`; `get(key, default)` returns the default.
- Invalid header names or values raise a public request/preparation error rather than creating an invalid outgoing request.

### Query Parameters and URLs

- `QueryParams` is an immutable query multi-dict. Standard mapping lookup returns the first value for a key; `get_list(key)` returns all values.
- `QueryParams.set(key, value)` returns a new object with all existing values for that key replaced by one value.
- `QueryParams.add(key, value)` returns a new object with the value appended for that key.
- `QueryParams.remove(key)` returns a new object with all values for that key removed.
- `QueryParams.merge(params)` returns a new object where supplied keys replace existing values for those keys and preserve unrelated existing keys.
- Stringifying `QueryParams` percent-encodes names and values and repeats keys for multiple values.
- `URL` normalizes and exposes `scheme`, `raw_scheme`, `userinfo`, `username`, `password`, `host`, `raw_host`, `port`, `netloc`, `path`, `query`, `params`, `raw_path`, and `fragment`.
- `URL.copy_with(...)`, `copy_set_param(...)`, `copy_add_param(...)`, `copy_remove_param(...)`, and `copy_merge_params(...)` return new `URL` instances and leave the original unchanged.
- `URL.join(other)` returns an absolute URL resolved against the base URL.
- Invalid URL component combinations raise `InvalidURL`.

### Cookies

- `Cookies` is a mutable mapping backed by an HTTP cookie jar.
- `cookies.set(name, value, domain="", path="/")` stores a cookie with optional domain and path.
- `cookies.get(name, default=None, domain=None, path=None)` returns the matching value. When multiple cookies match a name and no domain/path disambiguates them, it raises `CookieConflict`.
- `cookies.delete(name, domain=None, path=None)` removes matching cookies. If no matching cookie exists, it raises `KeyError`.
- `cookies.clear(domain=None, path=None)` removes all matching cookies.
- `Cookies.extract_cookies(response)` must read `Set-Cookie` response headers into the jar.
- `Cookies.set_cookie_header(request)` must apply matching cookie values to the outgoing `Request` according to standard domain and path matching.

### Request Model

- `Request.method` is the uppercase HTTP method string supplied or normalized during construction.
- `Request.url` is a `URL`.
- `Request.headers` is a `Headers` instance containing default host, accept, accept-encoding, connection, user-agent, content length, content type, cookie, and auth headers when those values apply.
- Request body inputs use this priority: `stream` supplies an explicit stream; otherwise `content`, `data`, `files`, or `json` encode the body. Supplying incompatible body inputs raises `RuntimeError` or `TypeError`.
- `Request.read()` returns the request body bytes and stores them for later `content` access.
- `Request.aread()` is the async equivalent.
- Accessing `Request.content` before reading a streaming request body raises `RequestNotRead`.
- Reading or streaming a consumed request stream again raises `StreamConsumed`.

### Response Model

- `Response.status_code` is the integer status code supplied at construction or returned by a transport.
- `Response.reason_phrase` returns the standard reason phrase for the status code unless the transport supplied a reason phrase extension.
- `Response.http_version` returns the HTTP version extension value, defaulting to `"HTTP/1.1"`.
- `Response.url` returns `response.request.url`. If no request is attached, it raises `RuntimeError`.
- `Response.request` returns the attached `Request`. If no request is attached, it raises `RuntimeError`.
- `Response.elapsed` returns the elapsed request/response time after it is set by the client. If accessed before it is set, it raises `RuntimeError`.
- `Response.cookies` returns a `Cookies` instance populated from response `Set-Cookie` headers.
- `Response.links` parses RFC-style `Link` response headers into a dictionary keyed by relation or URL.
- `Response.json(**kwargs)` decodes `content` as JSON and forwards keyword arguments to `json.loads`; invalid JSON raises `ValueError`.
- `Response.raise_for_status()` returns the response for 2xx statuses. It raises `HTTPStatusError` for 1xx, 3xx, 4xx, and 5xx statuses and attaches both `request` and `response`.
- `Response.is_informational`, `is_success`, `is_redirect`, `is_client_error`, `is_server_error`, and `is_error` reflect 1xx, 2xx, 3xx, 4xx, 5xx, and 4xx/5xx ranges respectively.
- `Response.has_redirect_location` returns `True` for redirect responses with a valid `Location` header and `False` otherwise.

### Streaming and Read State

- A response constructed or returned with eager `content`, `text`, `html`, or `json` content must expose `content` and `text` immediately.
- A response constructed or returned with a stream must raise `ResponseNotRead` from `content` and `text` until `read()` or `aread()` completes.
- `read()` and `aread()` consume the response stream, close it, cache the bytes, and return the bytes.
- `iter_bytes(chunk_size=None)` yields decoded byte chunks. `iter_raw(chunk_size=None)` yields raw byte chunks without content decoding.
- `iter_text(chunk_size=None)` yields decoded text chunks. `iter_lines()` yields text lines with universal line endings normalized to `\n`.
- Async iterator methods mirror sync iterator behavior.
- After a stream has been consumed, another attempt to iterate it raises `StreamConsumed`.
- After a stream has been closed before consumption, an attempt to read or iterate it raises `StreamClosed`.
- `num_bytes_downloaded` returns the number of raw response bytes consumed from the stream.
- `close()` and `aclose()` close the response stream and return `None`.

### Redirects and History

- Redirect following is disabled by default for top-level helpers and clients.
- When `follow_redirects=False` and the response has a redirect `Location`, the response is returned with empty `history` and `next_request` set to the prepared redirect request.
- When `follow_redirects=True`, the client follows redirects up to `max_redirects`, returns the final response, sets `history` to followed redirect responses in order, and sets the final response `next_request` to `None`.
- Exceeding `max_redirects` raises `TooManyRedirects` with the triggering request attached.
- A relative redirect location resolves against the previous request URL.
- Redirect handling must preserve safe method semantics and HTTPX's documented method rewrite behavior for common 301, 302, 303, 307, and 308 responses.

### Event Hooks

- Client event hooks are configured as `{"request": [callables], "response": [callables]}`.
- Request hooks run after request preparation and before transport dispatch. They receive the `Request` and their mutations must affect the outgoing request.
- Response hooks run after a response is fetched and before it is returned from the client call or yielded by a stream context.
- Response hooks that need body content must call `response.read()` or `response.aread()` themselves.
- Multiple hooks for the same event run in list order.
- `AsyncClient` hooks must be async callables. Passing sync hooks to `AsyncClient` raises a runtime error when the hook is awaited.
- Unknown event hook names raise `KeyError`.

### Authentication

- `BasicAuth(username, password)` and a two-item `(username, password)` tuple apply HTTP Basic auth by setting the outgoing `Authorization` header.
- `DigestAuth(username, password)` performs a challenge/response flow. When a 401 challenge is answered and a final response is returned, the intermediate challenge response appears in `history`.
- `NetRCAuth(file=None)` looks up credentials for the request host using the given netrc file or the standard netrc location. File parsing errors propagate from the standard library.
- A callable auth value is wrapped as `FunctionAuth` and receives the prepared `Request`; it must return a `Request`.
- A custom `Auth` subclass implements `auth_flow(request)` and yields one or more requests. The response to a yielded request is sent back into the generator.
- If custom auth needs request body bytes, it sets `requires_request_body = True`; the client must read the request body before calling the flow.
- If custom auth needs response body bytes, it sets `requires_response_body = True`; the client must read the response body before resuming the flow.
- Custom auth with separate sync and async I/O implements `sync_auth_flow` and `async_auth_flow`; using an unsupported flow raises the error raised by that implementation.

### Transports

- `MockTransport(handler)` calls `handler(request)` for sync clients and awaits async handlers for async clients. The handler must return a `Response`.
- `WSGITransport(app, ...)` sends sync client requests into a WSGI app. It must populate WSGI environ values from the request method, path, query string, headers, body, `script_name`, and `remote_addr`.
- `ASGITransport(app, ...)` sends async client requests into an ASGI app. It must populate ASGI scope values from the request method, path, query string, headers, `root_path`, and `client`.
- If `raise_app_exceptions=True`, exceptions raised by a WSGI or ASGI app propagate to the caller. If `False`, app error responses are returned as HTTP responses when the protocol supplies them.
- WSGI transport is for `Client`; ASGI transport is for `AsyncClient`. Using a sync-only transport with `AsyncClient` or an async-only transport with `Client` raises a transport capability error.

## Error Semantics

- `HTTPError` is the base class for `RequestError` and `HTTPStatusError`.
- `RequestError` and its transport subclasses carry a `.request` attribute. Accessing `.request` before one is attached raises `RuntimeError`.
- `HTTPStatusError` is raised by `Response.raise_for_status()` for non-2xx status categories and carries both `.request` and `.response`.
- `InvalidURL` is raised for URLs or URL components that HTTPX cannot parse into a valid request URL.
- `CookieConflict` is raised when a cookie lookup by name matches multiple cookies and the caller did not disambiguate by domain/path.
- `StreamConsumed`, `StreamClosed`, `ResponseNotRead`, and `RequestNotRead` describe public stream state violations.
- `TooManyRedirects` is raised when redirect following exceeds the configured maximum.
- `UnsupportedProtocol` is raised when a request uses a protocol unsupported by the configured transport.
- `LocalProtocolError` represents a request-side protocol violation. `RemoteProtocolError` represents a server-side protocol violation reported by the transport.
- `DecodingError` is raised when response content decoding fails.

## Cross-View Invariants

- A header set by a request hook must be visible to the transport handler through `request.headers`.
- A response returned by a transport must become the same response observed by response hooks, client callers, and redirect history unless redirect handling replaces it with a later final response.
- A cookie extracted from a response into `client.cookies` must be sent on a later matching request from the same client.
- A request built with client defaults must show merged headers, cookies, params, timeout extensions, and URL normalization before it is sent.
- A response that reports `is_redirect == True` and has a valid redirect location must expose a `next_request` when redirects are not followed.
- A final response returned after followed redirects must have `history` containing prior responses, while each history response must have an empty or earlier history appropriate to its point in the chain.
- Bytes returned by `Response.read()` must equal the bytes later exposed through `Response.content`.
- Text returned through `Response.text` must be decoded from the same cached bytes exposed by `Response.content` using `Response.encoding`.
- Query parameters visible in `Request.url.params` must match the query string visible in `str(Request.url)`.
- Header values visible through `Headers.__getitem__`, `Headers.get_list`, and `Headers.multi_items` must describe the same underlying header entries.

## Representative Workflows

### Mocked Sync Request With Hooks and Redirects

```python
import httpx

events = []

def app(request):
    if request.url.path == "/start":
        return httpx.Response(302, headers={"Location": "/end"}, request=request)
    return httpx.Response(200, json={"path": request.url.path}, request=request)

def add_header(request):
    request.headers["X-Trace"] = "1"
    events.append(("request", str(request.url)))

def remember_response(response):
    events.append(("response", response.status_code))

transport = httpx.MockTransport(app)

with httpx.Client(
    base_url="https://example.org",
    params={"client": "yes"},
    headers={"User-Agent": "demo"},
    transport=transport,
    event_hooks={"request": [add_header], "response": [remember_response]},
    follow_redirects=True,
) as client:
    request = client.build_request("GET", "/start", params={"request": "yes"})
    response = client.send(request)

assert response.status_code == 200
assert response.history[0].status_code == 302
assert response.json() == {"path": "/end"}
assert events[0][0] == "request"
```

If the mock handler raises an exception, the client call raises that exception unless the handler converts it into a `Response`.

### Async ASGI Request

```python
import httpx

async def app(scope, receive, send):
    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [(b"content-type", b"text/plain")],
    })
    await send({"type": "http.response.body", "body": scope["path"].encode()})

transport = httpx.ASGITransport(app=app, root_path="/api")

async with httpx.AsyncClient(
    transport=transport,
    base_url="http://testserver/api",
) as client:
    response = await client.get("/items")

assert response.text == "/api/items"
```

If the ASGI app raises and `raise_app_exceptions=True`, the awaited request raises the app exception.

## Non-Goals

- Live DNS, socket, TLS, HTTP/1.1, HTTP/2, proxy, connection-pool, retry, and private `httpcore` behavior.
- Private modules and helpers under `httpx._*`, including private URL parsing and utility helpers.
- Exact `repr(...)` output, exact exception message text, and terminal color/style formatting.
- Private transport routing internals, proxy mount sorting internals, and connection-pool object structure.
- Full multipart encoding internals beyond public request-body acceptance and observable headers/body behavior.
- Environment-variable proxy and certificate behavior beyond the public `trust_env` switch.
- ASGI lifespan startup/shutdown management.

## Invocation Protocol

The console script name is `httpx`, installed from `httpx = "httpx:main"`. `python -m httpx` is not supported because the package does not provide a `__main__.py` module.

CLI invocation:

```bash
httpx URL [OPTIONS]
```

Selected options:

- `-m, --method METHOD` sets the request method. If omitted, the method is `POST` when a request body option is supplied and `GET` otherwise.
- `-p, --params NAME VALUE` appends query parameters.
- `-c, --content TEXT` sends raw byte content.
- `-d, --data NAME VALUE` sends form fields.
- `-f, --files NAME FILENAME` sends file fields.
- `-j, --json TEXT` parses JSON text and sends it as JSON; invalid JSON raises a Click parameter error.
- `-h, --headers NAME VALUE` adds request headers.
- `--cookies NAME VALUE` adds cookies.
- `--auth USER PASS` applies Basic auth; `PASS` equal to `-` prompts for a password.
- `--proxy URL`, `--timeout FLOAT`, `--follow-redirects`, `--no-verify`, and `--http2` pass the matching client/request settings.
- `--download FILE` writes response bytes to the file instead of printing the response body.
- `-v, --verbose` prints request and response header information.
- `--help` prints help and exits without sending a request.

Exit status:

| Condition | Exit code |
| --- | --- |
| Request completes and final response is 2xx | 0 |
| Request completes and final response is not 2xx | 1 |
| A `RequestError` is raised | 1 |
| `--help` is used | 0 |

## Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment. The documented workflows may use local mock, WSGI, ASGI, or compatible custom transports and do not require external network access.

## Evaluation Notes

Assessment covers the documented imports, client and model state, request and response projections, transport interactions, streaming lifecycles, and command exit status. Exact error wording, exact representation strings, private attributes, private modules, and live-network side effects are outside the contract.
