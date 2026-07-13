# Starlette Specification

## Product Overview

Starlette is a lightweight ASGI toolkit for building HTTP and WebSocket applications. A Starlette application is itself an ASGI callable, and its public behavior is visible through route matching, request and WebSocket wrapper objects, response ASGI messages, middleware effects, lifespan startup and shutdown, TestClient calls, and file-serving responses.

This specification describes the core application behavior needed to build and test in-process Starlette applications. It focuses on observable behavior through documented public imports and ASGI/TestClient interactions.

## Scope

The covered feature areas are:

- `Starlette` application construction and ASGI invocation.
- HTTP `Route`, `Mount`, `Host`, `Router`, `WebSocketRoute`, reverse lookups, and URL convertors.
- `Request`, `HTTPConnection`, `WebSocket`, and connection state.
- `Response`, `HTMLResponse`, `PlainTextResponse`, `JSONResponse`, `RedirectResponse`, `StreamingResponse`, `FileResponse`, cookies, background tasks, and range/file headers.
- `Middleware`, `BaseHTTPMiddleware`, CORS, GZip, HTTPS redirects, and trusted host checks.
- `HTTPException`, `WebSocketException`, `WebSocketDisconnect`, and `NoMatchFound`.
- `TestClient` HTTP and WebSocket sessions, including lifespan entry and shutdown.
- `StaticFiles` serving from directories and packages, HTML mode, conditional responses, method restrictions, and filesystem containment.

## Installable Surface

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

## Public API

`Starlette(debug=False, routes=None, middleware=None, exception_handlers=None, lifespan=None)` returns an ASGI application. It stores arbitrary application-level values on `app.state`, exposes `app.routes`, delegates `app.url_path_for(name, **path_params)`, and supports `app.mount(path, app, name=None)`, `app.host(host, app, name=None)`, `app.add_route(path, route, methods=None, name=None, include_in_schema=True)`, `app.add_middleware(middleware_class, *args, **kwargs)`, and `app.add_exception_handler(exc_class_or_status_code, handler)`.

`Router(routes=None, redirect_slashes=True, default=None, on_startup=None, on_shutdown=None, lifespan=None, middleware=None)` is a standalone ASGI router. It supports `url_path_for`, `mount`, `host`, `add_route`, and `add_websocket_route`.

`Route(path, endpoint, methods=None, name=None, include_in_schema=True, middleware=None)` maps HTTP requests to a function endpoint that receives `Request` and returns a response, or to a class that implements the ASGI interface. Function endpoints default to `GET`, and a route that includes `GET` must also accept `HEAD`. Unsupported methods must produce a 405 response or raise an HTTP 405 handled exception when routed inside an app.

`WebSocketRoute(path, endpoint, name=None, middleware=None)` maps WebSocket connections to an async callable that receives `WebSocket`, or to a class that implements the ASGI interface.

`Mount(path, app=None, routes=None, name=None, middleware=None)` mounts an ASGI app or nested routes beneath a path prefix. `Host(host, app, name=None)` routes by host name, ignoring the request port for matching.

`Request(scope, receive=empty_receive, send=empty_send)` wraps an HTTP scope. It is mapping-compatible with the scope and exposes `method`, `url`, `base_url`, `headers`, `query_params`, `path_params`, `cookies`, `client`, `session`, `auth`, `user`, `state`, `app`, `url_for`, `stream`, `body`, `json`, `form`, `close`, `is_disconnected`, and `send_push_promise`.

`WebSocket(scope, receive, send)` wraps a WebSocket scope. It is mapping-compatible with the scope and exposes `url`, `headers`, `query_params`, `path_params`, `state`, `accept`, `receive`, `send`, typed receive/send helpers, typed async iterators, `close`, and `send_denial_response`.

`Response(content=None, status_code=200, headers=None, media_type=None, background=None)` is an ASGI app. It has `set_cookie` and `delete_cookie`. `HTMLResponse`, `PlainTextResponse`, and `JSONResponse` specialize the media type and rendering. `RedirectResponse(url, status_code=307, headers=None, background=None)` sets a redirect location. `StreamingResponse(content, status_code=200, headers=None, media_type=None, background=None)` streams sync or async iterables. `FileResponse(path, status_code=200, headers=None, media_type=None, background=None, filename=None, stat_result=None, method=None, content_disposition_type="attachment")` streams a file.

`StaticFiles(directory=None, packages=None, html=False, check_dir=True, follow_symlink=False)` is an ASGI app for HTTP static serving.

`TestClient(app, base_url="http://testserver", raise_server_exceptions=True, root_path="", backend="asyncio", backend_options=None, cookies=None, headers=None, follow_redirects=True, client=("testclient", 50000))` provides synchronous HTTP client methods and `websocket_connect(url, subprotocols=None, **options)`.

## Product State Model

The core Starlette state has three public projections:

- The ASGI projection: scopes, receive events, send events, and response messages.
- The object projection: `Starlette`, `Router`, `Request`, `WebSocket`, response, middleware, and state objects.
- The client projection: `TestClient` HTTP responses and WebSocket sessions.

Cross-view invariants:

- A route appended to a `Starlette` or `Router` route table must be visible through ASGI dispatch and through `TestClient` calls to the same path.
- A path parameter matched by a route must be visible on `request.path_params`, `websocket.path_params`, and reverse URL generation for that route name.
- A response object returned by an endpoint must produce the same status, headers, cookies, and body through raw ASGI send messages and through `TestClient` response objects.
- A value yielded by lifespan state must be visible on `request.state` and `websocket.state` during a context-managed `TestClient` session.
- A file served by `StaticFiles` or `FileResponse` must expose the same bytes through a `Response` ASGI call and through a `TestClient` request.
- Middleware that changes a request scope or response headers must be visible to downstream endpoint objects and to the final HTTP response.
- A WebSocket message sent with `WebSocket.send_text`, `send_bytes`, or `send_json` must be received by `TestClient.websocket_connect` using the corresponding typed receive method.

## Application And Lifespan Behavior

- `Starlette` must place the application instance into `scope["app"]` before calling the middleware stack. If a caller constructs `Request` or `WebSocket` from that scope, `request.app` or `websocket.app` must return the originating application; if no app exists in scope, accessing `.app` must raise `KeyError`.
- Middleware listed on `Starlette(..., middleware=[...])` must process inbound requests top-to-bottom and must unwind outbound responses in reverse order. If one middleware appends a response header after `call_next` and a later middleware appends the same header after `call_next`, the later middleware's appended response value returns before the earlier middleware's appended value.
- A lifespan context must complete startup before the application serves requests in a context-managed `TestClient`. Teardown must run when the context exits after open connections close and in-process background tasks complete.
- Lifespan state yielded as a mapping must be copied shallowly to request and WebSocket state. Rebinding a top-level state key on one request must not change that key for later requests, while mutating a shared object stored under a state key must be visible to later requests in the same lifespan session.
- `TestClient(app)` construction alone must not run lifespan. `with TestClient(app) as client:` must run startup before the first request and shutdown on context exit.
- If the lifespan function raises during startup, entering the `TestClient` context must raise that exception when `raise_server_exceptions=True`.

## Routing Behavior

- Routes must match incoming HTTP and WebSocket paths in the order they appear in the route table. When two routes can match the same request, the first matching route must handle it.
- `Route` paths must start with `/`; constructing a route with a path that does not start with `/` must raise `AssertionError`.
- Path templates must support `{name}` and `{name:convertor}`. Built-in convertors are `str`, `int`, `float`, `uuid`, and `path`. The `path` convertor must include `/` characters in the captured value.
- Captured route parameters must be converted before being exposed on `request.path_params` or `websocket.path_params`. If a path segment does not match the convertor, the route must not match.
- Duplicate parameter names in one path template must raise `ValueError` during path compilation.
- A custom `Convertor` registered with `register_url_convertor(name, convertor)` must be usable in later route templates and reverse URL generation. Unknown convertor names in route templates must raise `AssertionError`.
- A function `Route` with `methods=None` must accept `GET` and `HEAD`. A route with explicit methods must uppercase method names, and `GET` must imply `HEAD`.
- When an HTTP path matches a route but the method is unsupported, the app must return or raise HTTP 405 and include an `Allow` header listing the accepted methods. When no route matches an HTTP request, the app must return 404.
- `WebSocketRoute` must only match WebSocket scopes. A plain HTTP `Route` must not handle WebSocket scopes.
- `Mount` must strip its own matched prefix for routing inside the mounted app and must preserve route parameters already captured by parent routes.
- A named `Mount` must use `"{mount}:{child}"` names for reverse URL lookup of child routes. Mounted static files must accept the `path` parameter for reverse lookup.
- `Host` must match the hostname portion of the Host header while ignoring the port for matching. Host parameters must be available to child reverse lookups and must be accepted by `request.url_for`.
- `request.url_for(name, **path_params)` must return an absolute URL using the request base URL. `app.url_path_for(name, **path_params)` must return a `URLPath` path without scheme and host unless a host route supplies them.
- Reverse URL lookup must raise `NoMatchFound` when the name does not exist or when the provided parameters do not exactly match the route's required parameters.

## Request Behavior

- `Request` must assert `scope["type"] == "http"` at construction. It must behave like a mapping over the ASGI scope.
- `request.url` must include scheme, host, path, and query string from the scope and headers. `request.base_url` must represent the application base URL and root path for reverse URL construction.
- `request.headers` must be immutable, case-insensitive, and multi-valued. Missing header lookup must raise `KeyError`; `get` must return the caller's default.
- `request.query_params` must be an immutable multidict of string keys and values parsed from the query string.
- `request.cookies` must parse valid Cookie header pairs into a regular dictionary and must ignore invalid cookie fragments.
- `request.client` must return an address object with `host` and `port` when the ASGI scope has a client tuple, and must return `None` when no client is provided.
- `await request.body()` must collect and cache the entire request body. Later `await request.body()` calls must return the cached bytes.
- `await request.json()` must parse the cached body as JSON and must raise the underlying JSON parsing exception when the body is not valid JSON.
- `request.stream()` must yield incoming body chunks without storing the whole body. After the stream has been consumed directly, later calls to `body`, `form`, or `json` must raise `RuntimeError`.
- If the receive channel reports `http.disconnect` while streaming, `request.stream()` must raise `ClientDisconnect`.
- `request.form(max_files=1000, max_fields=1000, max_part_size=1024*1024)` must parse form and multipart bodies into immutable `FormData`. Multipart parts with a `filename` field must be represented as `UploadFile`; parts without `filename` must be represented as strings. If multipart support is not installed and multipart parsing is requested, the call must raise an assertion error.
- `UploadFile` must expose `filename`, `content_type`, `file`, `headers`, and `size`. Its async `write`, `read`, `seek`, and `close` methods must operate on the underlying file object.
- `request.is_disconnected()` must return a boolean indicating whether an `http.disconnect` message has been observed.

## Response Behavior

- A `Response` must render `None` as an empty body, bytes and memoryview unchanged, and strings with the response charset. It must send one `http.response.start` message followed by one `http.response.body` message.
- `Response` must automatically add `Content-Length` when a body exists and the status code allows a body. It must not add `Content-Length` for informational responses, 204, or 304.
- `Response` must automatically add `Content-Type` when a media type exists and the caller did not provide one. Text media types must include `; charset=utf-8` unless the media type already includes a charset.
- Caller-provided `content-length` or `content-type` headers must not be overwritten by automatic header generation.
- `JSONResponse` must render compact UTF-8 JSON, must preserve non-ASCII characters, and must reject non-finite numeric values by raising `ValueError`.
- `RedirectResponse` must default to status 307 and must set `Location` to the quoted redirect URL.
- `Response.set_cookie` must append a `Set-Cookie` header with the provided key, value, max age, expiry, path, domain, secure, httponly, samesite, and partitioned attributes. Invalid `samesite` values must raise `AssertionError`. `partitioned=True` must raise `ValueError` on Python versions below 3.14.
- `Response.delete_cookie` must expire a cookie by setting `max-age=0` and `expires=0` using the provided path, domain, secure, httponly, and samesite options.
- If a response has a background task, it must run after the response body has been sent. `BackgroundTasks` must execute tasks in insertion order and must stop executing later tasks when one task raises.
- `StreamingResponse` must send chunks from async iterables directly and must run sync iterables through a threadpool-compatible iterator. If the client disconnects during streaming, the response must stop streaming and raise or propagate the disconnect condition according to the active ASGI receive behavior.
- `FileResponse` must stream the target file and include `Content-Length`, `Last-Modified`, `ETag`, and `Accept-Ranges: bytes` when the file exists. If the file does not exist at call time, it must raise `RuntimeError`; if the path is not a regular file, it must raise `RuntimeError`.
- `FileResponse` must infer media type from `filename` or path when `media_type` is not provided. When `filename` is provided, it must set `Content-Disposition` using `attachment` by default or the provided disposition type.
- `FileResponse` must support single and multiple byte ranges for `Range: bytes=...`. A satisfiable range must return 206 with `Content-Range` and the selected bytes. An unsatisfiable range must return 416 with `Content-Range: */<file-size>`. A malformed range must return 400.
- `FileResponse` must honor `If-Range`: when the condition matches the current ETag or last-modified value it must serve the requested range; otherwise it must serve the full file.
- For `HEAD` requests, file and static responses must return headers without a response body.

## WebSocket Behavior

- `WebSocket` must assert `scope["type"] == "websocket"` at construction. It must behave like a mapping over the ASGI scope.
- `websocket.url`, `headers`, `query_params`, `path_params`, `state`, and `url_for` must follow the same connection-scope semantics as `HTTPConnection`.
- `await websocket.accept(subprotocol=None, headers=None)` must wait for the connection message when needed, then send an accept message with the selected subprotocol and headers.
- `await websocket.receive_text()`, `receive_bytes()`, and `receive_json(mode="text")` must require an accepted connection. If called before accept, they must raise `RuntimeError`.
- `receive_json(mode="text")` must decode JSON from text messages by default. With `mode="binary"` it must decode JSON from binary messages. Invalid mode values must raise `RuntimeError`.
- `send_json(data, mode="text")` must send JSON as a text message by default. With `mode="binary"` it must send JSON bytes. Invalid mode values must raise `RuntimeError`.
- If an incoming message is `websocket.disconnect`, typed receive helpers must raise `WebSocketDisconnect` with the close code and reason.
- `iter_text`, `iter_bytes`, and `iter_json` must yield incoming messages until `WebSocketDisconnect`, then exit the iterator without re-raising the disconnect.
- `await websocket.close(code=1000, reason=None)` must send a close message. Calling `close` before `accept` must deny the upgrade with an HTTP 403 response in server contexts that follow Starlette's default behavior.
- `await websocket.send_denial_response(response)` must send the supplied HTTP response as a WebSocket denial response and then close. If the ASGI scope does not advertise support for the denial response extension, it must raise `RuntimeError`.

## Static Files Behavior

- `StaticFiles` must serve only HTTP scopes. Non-HTTP scopes must fail assertion.
- With `check_dir=True`, constructing `StaticFiles(directory=...)` must raise `RuntimeError` immediately when the directory does not exist. With `check_dir=False`, configuration must be checked on the first request and must raise `RuntimeError` if the configured path is missing or not a directory.
- `StaticFiles` must serve only `GET` and `HEAD`. Other methods must raise or return HTTP 405.
- Requested paths must be normalized and must not escape the configured directories. Absolute paths, parent traversal, null bytes, and paths outside the served directory must return 404 rather than exposing filesystem content.
- When `follow_symlink=False`, containment checks must use the resolved real path. When `follow_symlink=True`, symlink targets inside the absolute served tree may be followed.
- If a requested regular file exists, `StaticFiles` must return a `FileResponse` for it. If request validators match the file ETag or modification time, it must return 304 with only cache-related headers.
- In HTML mode, a request for a directory with `index.html` must return that file. If the URL path for that directory does not end with `/`, it must redirect to the slash-suffixed URL.
- In HTML mode, if a requested file is missing and `404.html` exists, the response must serve that file with status 404. If no custom not-found file exists, the response must be 404.
- `packages=["pkg"]` must look for a `statics` directory inside that package. `packages=[("pkg", "static")]` must use the named package subdirectory. Missing packages or missing package static directories must raise `AssertionError`.

## Middleware Behavior

- `Middleware(cls, *args, **kwargs)` must store a middleware factory and arguments and must be iterable as `(cls, args, kwargs)` for stack construction.
- `BaseHTTPMiddleware` subclasses must implement `dispatch(request, call_next)`. `call_next(request)` must call the downstream app and return a response. If `dispatch` is not implemented, using the middleware must raise `NotImplementedError`.
- Middleware configured on `Route`, `Mount`, or `Router` must wrap only that route group. Middleware configured this way must not be automatically wrapped by Starlette's top-level exception handling middleware.
- `HTTPSRedirectMiddleware` must redirect HTTP to HTTPS and WebSocket to WSS while preserving host, path, query string, and port when present. Secure HTTP or WebSocket scopes must pass through unchanged.
- `TrustedHostMiddleware` must allow exact hosts, wildcard subdomains such as `*.example.com`, and `"*"`. Invalid hosts must produce a 400 response. With `www_redirect=True`, a valid `www.` host counterpart must redirect when the incoming host omits `www`.
- `GZipMiddleware` must compress HTTP responses when the request `Accept-Encoding` includes `gzip`, the response has no existing `Content-Encoding`, the response is not `text/event-stream`, and the response body reaches `minimum_size`. It must not compress smaller responses or responses that are already encoded.
- `CORSMiddleware` must handle CORS preflight requests when the method is `OPTIONS` and the request includes `Origin` and `Access-Control-Request-Method`. It must return 200 for allowed preflight requests and 400 for disallowed CORS preflight requests.
- `CORSMiddleware` must add appropriate CORS response headers to simple requests that include `Origin`. With credentials enabled, wildcard origin behavior must echo the explicit origin when required rather than exposing an invalid credentialed wildcard response.
- If `allow_private_network=True`, an allowed private-network preflight must include `Access-Control-Allow-Private-Network: true`. If private network access is requested and not allowed, the preflight must fail with 400.

## Error Semantics

- `HTTPException(status_code, detail=None, headers=None)` must preserve `status_code`, `detail`, and `headers`. When raised during an application request, it must become a plain-text HTTP response using the status code and headers.
- Raising `HTTPException` inside routing or endpoints must produce the configured HTTP error response. Raising it before a WebSocket accept must deny the WebSocket upgrade with an HTTP response.
- Custom exception handlers keyed by status code must handle matching `HTTPException` status codes. Handlers keyed by exception class must handle matching exception instances.
- Error handlers registered under `500` or `Exception` must handle unhandled application errors. With `debug=True`, traceback responses must take precedence over an installed 500 handler.
- `WebSocketException(code=1008, reason=None)` must preserve `code` and `reason` and must be usable with a custom WebSocket exception handler.
- `WebSocketDisconnect(code=1000, reason=None)` must be raised by WebSocket receiving helpers when a disconnect message is received.
- `NoMatchFound` must be raised by reverse lookup when no route name and parameter set matches.
- Accessing `request.session`, `request.auth`, or `request.user` without the corresponding middleware-provided scope key must raise `AssertionError`.

## Cross-View Invariants

- A route handled successfully through `TestClient.get()` must be the same route that direct ASGI dispatch would select for the same HTTP scope path, method, host, root path, and query string.
- A route parameter converted by an `int`, `float`, `uuid`, `path`, or registered convertor must return the converted Python value on the request or WebSocket object and must use the convertor's `to_string` behavior during reverse URL generation.
- A `Response` returned by an endpoint must expose the same status code, headers, body bytes, and cookies through `TestClient` as it sends over ASGI messages.
- A header appended by middleware around an endpoint must be visible in the final `TestClient` response and must be visible to any outer ASGI send wrapper.
- Lifespan state yielded before requests must be visible in both HTTP and WebSocket handlers during the same context-managed test session.
- A `StaticFiles` app mounted under a named route must serve the same file bytes that `request.url_for` or `app.url_path_for` produces for that mounted name and `path` parameter.
- A WebSocket endpoint that accepts, sends JSON over text mode, and closes must be observable through `TestClient.websocket_connect()` using `receive_json(mode="text")`, followed by a `WebSocketDisconnect` on further receive.
- A background task attached to a response must run after the response body is sent, so the HTTP client receives the response even when later background work mutates application-visible state or raises.

## Representative Workflow

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

## Non-Goals

- Template rendering, authentication backends, session signing internals, schema generation, config loading, threadpool helpers, WSGI adapter behavior, server push, GraphQL, database integration, and third-party middleware are outside this specification.
- Exact exception message text, object `repr` strings, private modules, private helper names, and private attributes are outside this specification.
- Live network behavior, production ASGI server behavior, alternate event-loop performance, browser behavior, and platform-specific filesystem edge cases are outside this specification.
- Internal module organization is outside this specification except for documented public import paths.

## Invocation Protocol

Starlette's core public interface is a Python importable ASGI application toolkit. There is no Starlette console script in this scope.

`python -m starlette` is not supported for serving or managing applications.

Exit behavior:

| Invocation | Supported | Result |
|---|---:|---|
| `from starlette.applications import Starlette` | yes | imports the application class |
| `from starlette.testclient import TestClient` | yes | imports the synchronous in-process test client when its HTTP client dependency is installed |
| `python -m starlette` | no | must not be required for application behavior |

## Evaluation Notes

Behavior is exercised through public imports, in-process ASGI calls, `TestClient` HTTP requests, `TestClient` WebSocket sessions, temporary static files, response headers and bodies, and lifespan context entry and exit. The expected implementation should satisfy observable contracts for routing, state propagation, middleware effects, request body consumption, response rendering, WebSocket lifecycle, file serving, and documented error handling.

Scoring is based on public behavior only. Tests do not require private modules, private helper functions, exact traceback pages, exact `repr` strings, undocumented fixture carriers, or live external services.
