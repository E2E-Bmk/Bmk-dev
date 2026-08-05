# Starlette Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Starlette is a lightweight ASGI toolkit for building HTTP and WebSocket applications. A Starlette application is itself an ASGI callable, and its public behavior is visible through route matching, request and WebSocket wrapper objects, response ASGI messages, middleware effects, lifespan startup and shutdown, TestClient calls, and file-serving responses.

This specification describes the core application behavior needed to build and test in-process Starlette applications. It focuses on observable behavior through documented public imports and ASGI/TestClient interactions.

## Non-Goals

- Template rendering, authentication backends, session signing internals, schema generation, config loading, threadpool helpers, WSGI adapter behavior, server push, GraphQL, database integration, and third-party middleware are outside this specification.
- Exact exception message text, object `repr` strings, private modules, private helper names, and private attributes are outside this specification.
- Live network behavior, production ASGI server behavior, alternate event-loop performance, browser behavior, and platform-specific filesystem edge cases are outside this specification.
- Internal module organization is outside this specification except for documented public import paths.

## Representative Workflows

```python
from contextlib import asynccontextmanager

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.testclient import TestClient


@asynccontextmanager
async def lifespan(app):
    yield {"visits": []}


async def homepage(request: Request):
    request.state["visits"].append("home")
    return JSONResponse({"url": str(request.url_for("user", username="sam"))})


async def user(request: Request):
    return PlainTextResponse(request.path_params["username"])


async def socket(websocket):
    await websocket.accept()
    await websocket.send_json({"path": websocket.url.path})
    await websocket.close()


app = Starlette(
    routes=[
        Route("/", homepage, name="home"),
        Route("/users/{username}", user, name="user"),
        WebSocketRoute("/ws", socket, name="socket"),
        Mount("/static", StaticFiles(directory="static"), name="static"),
    ],
    middleware=[Middleware(GZipMiddleware, minimum_size=100)],
    lifespan=lifespan,
)

with TestClient(app) as client:
    response = client.get("/")
    assert response.status_code == 200
    with client.websocket_connect("/ws") as ws:
        assert ws.receive_json()["path"] == "/ws"
```

`TestClient` provides synchronous HTTP client methods and websocket connection helpers for in-process testing.

## Application and Lifespan Behavior

This section covers how applications are constructed, how the middleware stack is built and locked, how lifespan context is managed, and how TestClient drives the application lifecycle.

**Application Construction**

When `Starlette` is constructed with routes, middleware, and a lifespan, it must return an ASGI application. It must store application-level values on `app.state`, expose `app.routes`, delegate reverse path lookup through `app.url_path_for`, and support mounting, host routing, route registration, middleware registration, and exception-handler registration.

`Router` must be a standalone ASGI router with reverse path lookup, mount, host, route, and websocket-route registration.

**Scope Injection**

`Starlette` must place the application instance into `scope["app"]` before calling the middleware stack. When a caller constructs `Request` or `WebSocket` from that scope, `request.app` or `websocket.app` must return the originating application. If no app exists in scope, accessing `.app` must raise `KeyError`.

**Middleware Stack Locking**

When `app.add_middleware(cls)` is called after the application has handled its first request, it must raise `RuntimeError`. Middleware must only be addable before the middleware stack is built on first use.

Middleware listed on `Starlette(..., middleware=[...])` must process inbound requests top-to-bottom and must unwind outbound responses in reverse order. If one middleware appends a response header after `call_next` and a later middleware appends the same header after `call_next`, the later middleware's appended response value returns before the earlier middleware's appended value.

**Lifespan Context**

A lifespan context must complete startup before the application serves requests in a context-managed `TestClient`. Teardown must run when the context exits after open connections close and in-process background tasks complete.

Lifespan state yielded as a mapping must be copied shallowly to request and WebSocket state for each request. Rebinding a top-level state key on one request must not change that key for later requests. Mutating a shared mutable object stored under a state key must be visible to later requests in the same lifespan session.

If the lifespan function raises during startup, entering the `TestClient` context must raise that exception when `raise_server_exceptions=True`.

**TestClient Lifecycle**

`TestClient(app)` construction alone must not run lifespan. `with TestClient(app) as client:` must run startup before the first request and shutdown on context exit.

When `TestClient(app, raise_server_exceptions=False)` is used, unhandled server errors must not propagate as exceptions to the client caller; instead they must result in HTTP 500 responses.

When `TestClient(app, base_url="http://host:port")` is used, requests must use that base URL for host header and scheme resolution.

When `TestClient(app, follow_redirects=False)` is used, redirect responses must be returned directly without following the redirect location.

## Routing Behavior

This section covers how routes are declared and matched, how path parameters are captured and converted, how reverse URL generation works, and how method enforcement operates.

**Route Matching Order**

Routes must match incoming HTTP and WebSocket paths in the order they appear in the route table. When two routes can match the same request, the first matching route must handle it.

**Route Path Validation**

`Route` paths must start with `/`; constructing a route with a path that does not start with `/` must raise `AssertionError`.

**Path Parameter Templates**

Path templates must support `{name}` and `{name:convertor}`. Built-in convertors must include `str`, `int`, `float`, `uuid`, and `path`. The `path` convertor must include `/` characters in the captured value. Captured route parameters must be converted to their Python types before being exposed on `request.path_params` or `websocket.path_params`. If a path segment does not match the convertor, the route must not match.

**Path Compilation Errors**

Duplicate parameter names in one path template must raise `ValueError` during path compilation. Unknown convertor names in route templates must raise `AssertionError`.

**Custom Convertors**

A custom `Convertor` registered with `register_url_convertor(name, convertor)` must be usable in later route templates and reverse URL generation.

**Method Handling**

A function `Route` with `methods=None` must accept `GET` and `HEAD`. A route with explicit methods must uppercase method names, and `GET` must imply `HEAD`. When an HTTP path matches a route but the method is unsupported, the app must return HTTP 405 and include an `Allow` header listing the accepted methods as a comma-separated set. When no route matches an HTTP request, the app must return 404.

**WebSocket and HTTP Scope Separation**

`WebSocketRoute` must only match WebSocket scopes. A plain HTTP `Route` must not handle WebSocket scopes.

**Mount and Host Routing**

`Mount` must strip its own matched prefix for routing inside the mounted app and must preserve route parameters already captured by parent routes. A named `Mount` must use `"{mount}:{child}"` names for reverse URL lookup of child routes. Mounted static files must accept the `path` parameter for reverse lookup.

`Host` must match the hostname portion of the Host header while ignoring the port for matching. Host parameters must be available to child reverse lookups and must be accepted by `request.url_for`.

**Reverse URL Generation**

`request.url_for(name, **path_params)` must return an absolute URL using the request base URL. `app.url_path_for(name, **path_params)` must return a `URLPath` path without scheme and host unless a host route supplies them. Reverse URL lookup must raise `NoMatchFound` when the name does not exist or when the provided parameters do not exactly match the route's required parameters.

## Request and Data Structures Behavior

This section covers the HTTP request wrapper, its connection-level properties, body consumption semantics, and the public data structure classes used for URLs, headers, and query parameters.

**Request Scope Wrapping**

`Request` must wrap an HTTP scope, must be mapping-compatible with the scope, and must expose method, URL, base URL, headers, query parameters, path parameters, cookies, client address, session, auth, user, state, app, and reverse URL lookup.

`Request` must assert `scope["type"] == "http"` at construction. It must behave like a mapping over the ASGI scope: `request["path"]` must return the path from scope, and `len(request)` must equal `len(scope)`.

**URL Object**

`request.url` must include scheme, host, path, and query string from the scope and headers. The `URL` class must expose `scheme`, `hostname`, `port`, `path`, `query`, and `fragment` attributes parsed from the URL string. `str(url)` must produce the full URL string. `url.replace(scheme=..., path=...)` must return a new `URL` with the specified components changed and all other components preserved; the original URL must remain unchanged.

`request.base_url` must represent the application base URL and root path for reverse URL construction.

**Headers**

`request.headers` must be immutable, case-insensitive, and multi-valued. Missing header lookup must raise `KeyError`; `get` must return the caller's default. Assigning to headers must raise `TypeError`.

`Headers` may be constructed with `raw=[(bytes, bytes), ...]` to create an immutable header collection from raw byte pairs. `headers.getlist(name)` must return all values for a given header name as a list of strings.

`MutableHeaders` must support assignment and must be constructable from `raw=` byte pair lists for response header manipulation.

**Query Parameters**

`request.query_params` must be an immutable multidict of string keys and values parsed from the query string.

`QueryParams` may be constructed with a query string like `QueryParams("a=1&a=2&b=3")`. It must expose `getlist(key)` returning all values for the key as a list, `get(key, default=None)` returning the last value or default, `keys()` returning distinct key names, and `multi_items()` returning all key-value pairs including duplicates as a list of tuples.

**Cookies and Client**

`request.cookies` must parse valid Cookie header pairs into a regular dictionary and must ignore invalid cookie fragments.

`request.client` must return an address object with `host` and `port` when the ASGI scope has a client tuple, and must return `None` when no client is provided.

**Body Consumption**

`await request.body()` must collect and cache the entire request body. Later `await request.body()` calls must return the cached bytes.

`await request.json()` must parse the cached body as JSON and must raise `json.JSONDecodeError` when the body is not valid JSON.

`request.stream()` must yield incoming body chunks without storing the whole body. After the stream has been consumed directly, later calls to `body`, `form`, or `json` must raise `RuntimeError`.

If the receive channel reports `http.disconnect` while streaming, `request.stream()` must raise `ClientDisconnect`.

**Form and File Upload**

`request.form(max_files=1000, max_fields=1000, max_part_size=1048576)` must parse form and multipart bodies into immutable `FormData`. Multipart parts with a `filename` field must be represented as `UploadFile`; parts without `filename` must be represented as strings. If multipart support is not installed and multipart parsing is requested, the call must raise an assertion error.

`UploadFile` must expose `filename`, `content_type`, `file`, `headers`, and `size`. Its async `write`, `read`, `seek`, and `close` methods must operate on the underlying file object.

**Disconnect Detection**

`request.is_disconnected()` must return a boolean indicating whether an `http.disconnect` message has been observed.

**Scope-Dependent Attributes**

Accessing `request.session`, `request.auth`, or `request.user` without the corresponding middleware-provided scope key must raise `AssertionError`.

## Response Behavior

This section covers how response objects render bodies, manage headers, set cookies, handle background tasks, and send ASGI messages for various response types.

**Base Response Rendering**

`Response` must be an ASGI app with cookie set and delete helpers. A `Response` must render `None` as an empty body, bytes and memoryview unchanged, and strings with the response charset. It must send one `http.response.start` message followed by one `http.response.body` message.

`Response` must automatically add `Content-Length` when a body exists and the status code allows a body. It must not add `Content-Length` for informational responses, 204, or 304.

`Response` must automatically add `Content-Type` when a media type exists and the caller did not provide one. Text media types must include `; charset=utf-8` unless the media type already includes a charset.

Caller-provided `content-length` or `content-type` headers must not be overwritten by automatic header generation.

**Specialized Response Types**

`HTMLResponse` must set `text/html` as the media type and must render the provided content as its body with appropriate content-length.

`PlainTextResponse` must set `text/plain` as the media type.

`JSONResponse` must render compact UTF-8 JSON, must preserve non-ASCII characters without escaping them to ASCII sequences, and must reject non-finite numeric values by raising `ValueError`. The content-type must be `application/json`. The JSON body must round-trip: parsing it back must produce the original data structure.

`RedirectResponse` must default to status 307 and must set `Location` to the quoted redirect URL where spaces and special characters are percent-encoded.

**Cookie Operations**

`Response.set_cookie` must append a `Set-Cookie` header with the provided key, value, max age, expiry, path, domain, secure, httponly, samesite, and partitioned attributes. Invalid `samesite` values must raise `AssertionError`.

`Response.delete_cookie` must expire a cookie by setting `max-age=0` and `expires=0` using the provided path, domain, secure, httponly, and samesite options.

**Background Tasks**

If a response has a background task, it must run after the response body has been sent. `BackgroundTasks` must execute tasks in insertion order via `tasks.add_task(fn, *args)`. When one task raises, later tasks must not execute.

**Streaming Response**

`StreamingResponse` must send chunks from async iterables directly and must run sync iterables through a threadpool-compatible iterator. If the client disconnects during streaming, the response must stop streaming and propagate the disconnect condition.

**File Response**

`FileResponse` must stream the target file and include `Content-Length`, `Last-Modified`, `ETag`, and `Accept-Ranges: bytes` when the file exists. If the file does not exist at ASGI call time, it must raise `RuntimeError`. If the path is not a regular file, it must raise `RuntimeError`.

`FileResponse` must infer media type from `filename` or path when `media_type` is not provided. When `filename` is provided, it must set `Content-Disposition` using `attachment` by default or the provided disposition type.

`FileResponse` must support single and multiple byte ranges for `Range: bytes=...`. A satisfiable range must return 206 with a `Content-Range` header in the format `bytes start-end/total` and the selected bytes as the body. An unsatisfiable range must return 416 with `Content-Range: */<file-size>`. A malformed range must return 400.

`FileResponse` must honor `If-Range`: when the condition matches the current ETag or last-modified value it must serve the requested range; otherwise it must serve the full file.

For `HEAD` requests, file and static responses must return headers without a response body.

## WebSocket Behavior

This section covers how WebSocket connections are accepted, how messages are sent and received in typed modes, how disconnections are signaled, and how subprotocol selection works.

**WebSocket Scope Wrapping**

`WebSocket` must wrap a WebSocket scope, must be mapping-compatible with the scope, and must expose URL, headers, query parameters, path parameters, state, accept, receive, send, typed receive and send helpers, typed async iterators, close, and denial-response helpers.

`WebSocket` must assert `scope["type"] == "websocket"` at construction. `websocket.url`, `headers`, `query_params`, `path_params`, `state`, and `url_for` must follow the same connection-scope semantics as `HTTPConnection`.

**Connection Acceptance**

`await websocket.accept(subprotocol=None, headers=None)` must wait for the connection message when needed, then send an accept message with the selected subprotocol and headers. When a subprotocol is provided, the client-side test session must expose the selected value through `session.accepted_subprotocol`.

**Typed Message Receiving**

`await websocket.receive_text()`, `receive_bytes()`, and `receive_json(mode="text")` must require an accepted connection. If called before accept, they must raise `RuntimeError`.

`receive_json(mode="text")` must decode JSON from text messages by default. With `mode="binary"` it must decode JSON from binary messages. Invalid mode values must raise `RuntimeError`.

**Typed Message Sending**

`send_json(data, mode="text")` must send JSON as a text message by default. With `mode="binary"` it must send JSON bytes. Invalid mode values must raise `RuntimeError`.

**Disconnect Handling**

If an incoming message is `websocket.disconnect`, typed receive helpers must raise `WebSocketDisconnect` with the close code and reason. The `WebSocketDisconnect` exception must preserve `code` and `reason` attributes matching the values sent by the remote end.

`iter_text`, `iter_bytes`, and `iter_json` must yield incoming messages until `WebSocketDisconnect`, then exit the iterator without re-raising the disconnect.

**Close Behavior**

`await websocket.close(code=1000, reason=None)` must send a close message. Calling `close` before `accept` must deny the upgrade with an HTTP 403 response in server contexts that follow Starlette's default behavior; the client must observe a `WebSocketDisconnect` with code 1000.

`await websocket.send_denial_response(response)` must send the supplied HTTP response as a WebSocket denial response and then close. If the ASGI scope does not advertise support for the denial response extension, it must raise `RuntimeError`.

## Static Files Behavior

This section covers how static file serving operates including directory validation, method enforcement, path security, conditional responses, HTML mode, and package directories.

**Basic Static Serving**

`StaticFiles` must be an ASGI app for HTTP static serving with optional package directories, HTML index mode, directory existence checking, and symlink following. `StaticFiles` must serve only HTTP scopes; non-HTTP scopes must fail assertion.

**Directory Validation**

With `check_dir=True`, constructing `StaticFiles(directory=...)` must raise `RuntimeError` immediately when the directory does not exist. With `check_dir=False`, configuration must be checked on the first request and must raise `RuntimeError` if the configured path is missing or not a directory.

**Method Enforcement**

`StaticFiles` must serve only `GET` and `HEAD`. Other methods must return HTTP 405. For `HEAD` requests, the response must include content headers without a response body.

**Path Security**

Requested paths must be normalized and must not escape the configured directories. Absolute paths, parent traversal, null bytes, and paths outside the served directory must return 404 rather than exposing filesystem content. When `follow_symlink=False`, containment checks must use the resolved real path. When `follow_symlink=True`, symlink targets inside the absolute served tree may be followed.

**File Serving and Conditional Responses**

If a requested regular file exists, `StaticFiles` must return a `FileResponse` for it. If request validators (such as `If-None-Match` with a matching ETag) match the file's current state, it must return 304 with only cache-related headers and an empty body.

**HTML Mode**

In HTML mode, a request for a directory with `index.html` must return that file. If the URL path for that directory does not end with `/`, it must redirect to the slash-suffixed URL with a 301 or 307 status.

In HTML mode, if a requested file is missing and `404.html` exists in the root directory, the response must serve that file with status 404. If no custom not-found file exists, the response must be 404.

**Package Directories**

`packages=["pkg"]` must look for a `statics` directory inside that package. `packages=[("pkg", "static")]` must use the named package subdirectory. Missing packages or missing package static directories must raise `AssertionError`.

## Middleware Behavior

This section covers how middleware factories are declared, how the base HTTP middleware dispatch pattern works, and how each built-in middleware transforms requests and responses.

**Middleware Declaration**

`Middleware(cls, *args, **kwargs)` must store a middleware factory and arguments and must be iterable as `(cls, args, kwargs)` for stack construction.

**BaseHTTPMiddleware**

`BaseHTTPMiddleware` subclasses must implement `dispatch(request, call_next)`. `call_next(request)` must call the downstream app and return a response. If `dispatch` is not implemented, using the middleware must raise `NotImplementedError`.

Middleware configured on `Route`, `Mount`, or `Router` must wrap only that route group. Middleware configured this way must not be automatically wrapped by Starlette's top-level exception handling middleware.

**HTTPSRedirectMiddleware**

`HTTPSRedirectMiddleware` must redirect HTTP to HTTPS and WebSocket to WSS while preserving host, path, query string, and port when present. The redirect must use status 307. Secure HTTP or WebSocket scopes must pass through unchanged.

**TrustedHostMiddleware**

`TrustedHostMiddleware` must allow exact hosts, wildcard subdomains such as `*.example.com`, and `"*"`. Invalid hosts must produce a 400 response. With `www_redirect=True`, a valid `www.` host counterpart must redirect when the incoming host omits `www`.

**GZipMiddleware**

`GZipMiddleware` must compress HTTP responses when the request `Accept-Encoding` includes `gzip`, the response has no existing `Content-Encoding`, the response is not `text/event-stream`, and the response body reaches `minimum_size`. It must set the `Content-Encoding: gzip` header on compressed responses. It must not compress smaller responses or responses that are already encoded.

**CORSMiddleware**

`CORSMiddleware` must handle CORS preflight requests when the method is `OPTIONS` and the request includes `Origin` and `Access-Control-Request-Method`. It must return 200 for allowed preflight requests with appropriate `Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, and `Access-Control-Allow-Headers` response headers, and 400 for disallowed CORS preflight requests.

`CORSMiddleware` must add appropriate CORS response headers to simple requests that include `Origin`. With `allow_credentials=True` and `allow_origins=["*"]`, the middleware must echo the explicit request origin in `Access-Control-Allow-Origin` rather than using a literal wildcard, and must set `Access-Control-Allow-Credentials: true`.

If `allow_private_network=True`, an allowed private-network preflight must include `Access-Control-Allow-Private-Network: true`. If private network access is requested and not allowed, the preflight must fail with 400.

## State Model

The core Starlette state has three public projections:

- The ASGI projection: scopes, receive events, send events, and response messages.
- The object projection: `Starlette`, `Router`, `Request`, `WebSocket`, response, middleware, and state objects.
- The client projection: `TestClient` HTTP responses and WebSocket sessions.

## Error Semantics

`HTTPException(status_code, detail=None, headers=None)` must preserve `status_code`, `detail`, and `headers`. When raised during an application request, it must become a plain-text HTTP response using the status code, detail as body text, and headers.

Raising `HTTPException` inside routing or endpoints must produce the configured HTTP error response. Raising it before a WebSocket accept must deny the WebSocket upgrade with an HTTP response.

Custom exception handlers keyed by status code must handle matching `HTTPException` status codes. Handlers keyed by exception class must handle matching exception instances.

Error handlers registered under `500` or `Exception` must handle unhandled application errors. With `debug=True`, traceback responses must take precedence over an installed 500 handler.

`WebSocketException(code=1008, reason=None)` must preserve `code` and `reason` and must be usable with a custom WebSocket exception handler.

`WebSocketDisconnect(code=1000, reason=None)` must be raised by WebSocket receiving helpers when a disconnect message is received. It must preserve `code` and `reason` as accessible attributes.

`NoMatchFound` must be raised by reverse lookup when no route name and parameter set matches.

Accessing `request.session`, `request.auth`, or `request.user` without the corresponding middleware-provided scope key must raise `AssertionError`.

## Cross-View Invariants

1. A route handled successfully through `TestClient.get()` must be the same route that direct ASGI dispatch would select for the same HTTP scope path, method, host, root path, and query string.
2. A route parameter converted by an `int`, `float`, `uuid`, `path`, or registered convertor must return the converted Python value on the request or WebSocket object, must produce the same value in `request.url_for` reverse generation, and must match `app.url_path_for` for the same name and parameters.
3. A `Response` returned by an endpoint must expose the same status code, headers, body bytes, and cookies through `TestClient` as it sends over ASGI `http.response.start` and `http.response.body` messages.
4. A header appended by middleware around an endpoint must be visible in the final `TestClient` response and must be visible in `MutableHeaders` constructed from the raw ASGI start message headers.
5. Lifespan state yielded before requests must be visible in both HTTP request handlers (via `request.state`) and WebSocket handlers (via `websocket.state`) during the same context-managed test session.
6. A `StaticFiles` app mounted under a named route must serve the same file bytes when accessed via `request.url_for(mount_name, path=filename)` as when accessed by constructing the path directly.
7. A WebSocket endpoint that accepts, sends JSON over text mode, and closes must be observable through `TestClient.websocket_connect()` using `receive_json(mode="text")`, followed by a `WebSocketDisconnect` on further receive.
8. A background task attached to a response must run after the response body is sent, so the HTTP client receives the response status and body even when later background work mutates application-visible state or raises.

## Public Interface

### Import Surface

The public application core is imported from these modules:

```python
from starlette.applications import Starlette
from starlette.routing import Router, Route, WebSocketRoute, Mount, Host, NoMatchFound
from starlette.requests import Request, HTTPConnection, ClientDisconnect
from starlette.responses import (
    Response,
    HTMLResponse,
    PlainTextResponse,
    JSONResponse,
    RedirectResponse,
    StreamingResponse,
    FileResponse,
)
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketClose
from starlette.testclient import TestClient
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.exceptions import HTTPException, WebSocketException
from starlette.background import BackgroundTask, BackgroundTasks
from starlette.convertors import Convertor, register_url_convertor
from starlette.datastructures import URL, URLPath, Headers, MutableHeaders, QueryParams, UploadFile, FormData, State
```

The package root exposes `__version__`. The root package is not the documented import location for the application objects above.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| Starlette | class | ASGI application with routes, middleware, and lifespan |
| Router | class | Standalone ASGI router |
| Route | class | HTTP route mapping |
| WebSocketRoute | class | WebSocket route mapping |
| Mount | class | Mount a nested app or route group under a path prefix |
| Host | class | Route by host name |
| NoMatchFound | exception | Raised when reverse URL lookup fails |
| Request | class | HTTP request wrapper over an ASGI scope |
| HTTPConnection | class | Shared HTTP and WebSocket connection base |
| ClientDisconnect | exception | Raised when the client disconnects during streaming |
| Response | class | Base ASGI HTTP response |
| HTMLResponse | class | HTML media-type response |
| PlainTextResponse | class | Plain-text response |
| JSONResponse | class | JSON-encoded response |
| RedirectResponse | class | HTTP redirect response |
| StreamingResponse | class | Streamed HTTP response body |
| FileResponse | class | File-backed HTTP response |
| WebSocket | class | WebSocket connection wrapper |
| WebSocketDisconnect | exception | Raised on WebSocket disconnect messages |
| WebSocketClose | class | WebSocket close helper |
| TestClient | class | Synchronous in-process HTTP and WebSocket test client |
| StaticFiles | class | HTTP static file serving app |
| Middleware | class | Middleware factory descriptor for stack construction |
| BaseHTTPMiddleware | class | Base class for dispatch-style middleware |
| CORSMiddleware | class | Cross-origin resource sharing middleware |
| GZipMiddleware | class | Conditional gzip compression middleware |
| HTTPSRedirectMiddleware | class | Redirect HTTP to HTTPS and WS to WSS |
| TrustedHostMiddleware | class | Host allow-list and optional www redirect middleware |
| HTTPException | exception | HTTP error with status, detail, and headers |
| WebSocketException | exception | WebSocket error with code and reason |
| BackgroundTask | class | Single deferred background task |
| BackgroundTasks | class | Ordered collection of background tasks |
| Convertor | class | Base URL path parameter convertor |
| register_url_convertor | function | Register a custom URL convertor by name |
| URL | class | Parsed URL value with component access and replace |
| URLPath | class | Path-only URL value for reverse lookup |
| Headers | class | Immutable case-insensitive headers with getlist |
| MutableHeaders | class | Mutable response headers |
| QueryParams | class | Immutable query parameter multidict |
| UploadFile | class | Uploaded multipart file wrapper |
| FormData | class | Immutable parsed form data |
| State | class | Lifespan and request state mapping |

### CLI Entry Points

Starlette's core public interface is a Python importable ASGI application toolkit. There is no Starlette console script in this scope.

`python -m starlette` is not supported for serving or managing applications.

Exit behavior:

| Invocation | Supported | Result |
|---|---:|---|
| `from starlette.applications import Starlette` | yes | imports the application class |
| `from starlette.testclient import TestClient` | yes | imports the synchronous in-process test client when its HTTP client dependency is installed |
| `python -m starlette` | no | must not be required for application behavior |

## Appendix A: Environment

The implementation may use third-party packages available on PyPI. Runtime dependencies must be declared in a standard `requirements.txt` or `pyproject.toml` at the project root and are installed before use. Covered workflows run in process with local temporary files and do not require a live network server.

## Appendix B: Assessment Notes

Behavior is exercised through public imports, in-process ASGI calls, `TestClient` HTTP requests, `TestClient` WebSocket sessions, temporary static files, response headers and bodies, and lifespan context entry and exit. The expected implementation should satisfy observable contracts for routing, state propagation, middleware effects, request body consumption, response rendering, WebSocket lifecycle, file serving, and documented error handling.

Assessment is based on public behavior only. Tests do not require private modules, private helper functions, exact traceback pages, exact `repr` strings, undocumented fixture carriers, or live external services.
