<!-- clauses.md -->
# Starlette Clause Catalog

Each row restates one normative clause from `spec.md`. Clause identifiers are
stable references for the public contract.

| clause_id | section | clause |
|---|---|---|
| STARLETTE-AALB-001 | Application and Lifespan Behavior | When `Starlette` is constructed with routes, middleware, and a lifespan, it must return an ASGI application. |
| STARLETTE-AALB-002 | Application and Lifespan Behavior | It must store application-level values on `app.state`, expose `app.routes`, delegate reverse path lookup through `app.url_path_for`, and support mounting, host routing, route registration, middleware registration, and exception-handler registration. |
| STARLETTE-AALB-003 | Application and Lifespan Behavior | `Router` must be a standalone ASGI router with reverse path lookup, mount, host, route, and websocket-route registration. |
| STARLETTE-AALB-004 | Application and Lifespan Behavior | `Starlette` must place the application instance into `scope["app"]` before calling the middleware stack. |
| STARLETTE-AALB-005 | Application and Lifespan Behavior | When a caller constructs `Request` or `WebSocket` from that scope, `request.app` or `websocket.app` must return the originating application. |
| STARLETTE-AALB-006 | Application and Lifespan Behavior | If no app exists in scope, accessing `.app` must raise `KeyError`. |
| STARLETTE-AALB-007 | Application and Lifespan Behavior | When `app.add_middleware(cls)` is called after the application has handled its first request, it must raise `RuntimeError`. |
| STARLETTE-AALB-008 | Application and Lifespan Behavior | Middleware must only be addable before the middleware stack is built on first use. |
| STARLETTE-AALB-009 | Application and Lifespan Behavior | Middleware listed on `Starlette(..., middleware=[...])` must process inbound requests top-to-bottom and must unwind outbound responses in reverse order. |
| STARLETTE-AALB-010 | Application and Lifespan Behavior | If one middleware appends a response header after `call_next` and a later middleware appends the same header after `call_next`, the later middleware's appended response value returns before the earlier middleware's appended value. |
| STARLETTE-AALB-011 | Application and Lifespan Behavior | A lifespan context must complete startup before the application serves requests in a context-managed `TestClient`. |
| STARLETTE-AALB-012 | Application and Lifespan Behavior | Teardown must run when the context exits after open connections close and in-process background tasks complete. |
| STARLETTE-AALB-013 | Application and Lifespan Behavior | Lifespan state yielded as a mapping must be copied shallowly to request and WebSocket state for each request. |
| STARLETTE-AALB-014 | Application and Lifespan Behavior | Rebinding a top-level state key on one request must not change that key for later requests. |
| STARLETTE-AALB-015 | Application and Lifespan Behavior | Mutating a shared mutable object stored under a state key must be visible to later requests in the same lifespan session. |
| STARLETTE-AALB-016 | Application and Lifespan Behavior | If the lifespan function raises during startup, entering the `TestClient` context must raise that exception when `raise_server_exceptions=True`. |
| STARLETTE-AALB-017 | Application and Lifespan Behavior | `TestClient(app)` construction alone must not run lifespan. |
| STARLETTE-AALB-018 | Application and Lifespan Behavior | `with TestClient(app) as client:` must run startup before the first request and shutdown on context exit. |
| STARLETTE-AALB-019 | Application and Lifespan Behavior | When `TestClient(app, raise_server_exceptions=False)` is used, unhandled server errors must not propagate as exceptions to the client caller; instead they must result in HTTP 500 responses. |
| STARLETTE-AALB-020 | Application and Lifespan Behavior | When `TestClient(app, base_url="http://host:port")` is used, requests must use that base URL for host header and scheme resolution. |
| STARLETTE-AALB-021 | Application and Lifespan Behavior | When `TestClient(app, follow_redirects=False)` is used, redirect responses must be returned directly without following the redirect location. |
| STARLETTE-RB-001 | Routing Behavior | Routes must match incoming HTTP and WebSocket paths in the order they appear in the route table. |
| STARLETTE-RB-002 | Routing Behavior | When two routes can match the same request, the first matching route must handle it. |
| STARLETTE-RB-003 | Routing Behavior | `Route` paths must start with `/`; constructing a route with a path that does not start with `/` must raise `AssertionError`. |
| STARLETTE-RB-004 | Routing Behavior | Path templates must support `{name}` and `{name:convertor}`. |
| STARLETTE-RB-005 | Routing Behavior | Built-in convertors must include `str`, `int`, `float`, `uuid`, and `path`. |
| STARLETTE-RB-006 | Routing Behavior | The `path` convertor must include `/` characters in the captured value. |
| STARLETTE-RB-007 | Routing Behavior | Captured route parameters must be converted to their Python types before being exposed on `request.path_params` or `websocket.path_params`. |
| STARLETTE-RB-008 | Routing Behavior | If a path segment does not match the convertor, the route must not match. |
| STARLETTE-RB-009 | Routing Behavior | Duplicate parameter names in one path template must raise `ValueError` during path compilation. |
| STARLETTE-RB-010 | Routing Behavior | Unknown convertor names in route templates must raise `AssertionError`. |
| STARLETTE-RB-011 | Routing Behavior | A custom `Convertor` registered with `register_url_convertor(name, convertor)` must be usable in later route templates and reverse URL generation. |
| STARLETTE-RB-012 | Routing Behavior | A function `Route` with `methods=None` must accept `GET` and `HEAD`. |
| STARLETTE-RB-013 | Routing Behavior | A route with explicit methods must uppercase method names, and `GET` must imply `HEAD`. |
| STARLETTE-RB-014 | Routing Behavior | When an HTTP path matches a route but the method is unsupported, the app must return HTTP 405 and include an `Allow` header listing the accepted methods as a comma-separated set. |
| STARLETTE-RB-015 | Routing Behavior | When no route matches an HTTP request, the app must return 404. |
| STARLETTE-RB-016 | Routing Behavior | `WebSocketRoute` must only match WebSocket scopes. |
| STARLETTE-RB-017 | Routing Behavior | A plain HTTP `Route` must not handle WebSocket scopes. |
| STARLETTE-RB-018 | Routing Behavior | `Mount` must strip its own matched prefix for routing inside the mounted app and must preserve route parameters already captured by parent routes. |
| STARLETTE-RB-019 | Routing Behavior | A named `Mount` must use `"{mount}:{child}"` names for reverse URL lookup of child routes. |
| STARLETTE-RB-020 | Routing Behavior | Mounted static files must accept the `path` parameter for reverse lookup. |
| STARLETTE-RB-021 | Routing Behavior | `Host` must match the hostname portion of the Host header while ignoring the port for matching. |
| STARLETTE-RB-022 | Routing Behavior | Host parameters must be available to child reverse lookups and must be accepted by `request.url_for`. |
| STARLETTE-RB-023 | Routing Behavior | `request.url_for(name, **path_params)` must return an absolute URL using the request base URL. |
| STARLETTE-RB-024 | Routing Behavior | `app.url_path_for(name, **path_params)` must return a `URLPath` path without scheme and host unless a host route supplies them. |
| STARLETTE-RB-025 | Routing Behavior | Reverse URL lookup must raise `NoMatchFound` when the name does not exist or when the provided parameters do not exactly match the route's required parameters. |
| STARLETTE-RADSB-001 | Request and Data Structures Behavior | `Request` must wrap an HTTP scope, must be mapping-compatible with the scope, and must expose method, URL, base URL, headers, query parameters, path parameters, cookies, client address, session, auth, user, state, app, and reverse URL lookup. |
| STARLETTE-RADSB-002 | Request and Data Structures Behavior | `Request` must assert `scope["type"] == "http"` at construction. |
| STARLETTE-RADSB-003 | Request and Data Structures Behavior | It must behave like a mapping over the ASGI scope: `request["path"]` must return the path from scope, and `len(request)` must equal `len(scope)`. |
| STARLETTE-RADSB-004 | Request and Data Structures Behavior | `request.url` must include scheme, host, path, and query string from the scope and headers. |
| STARLETTE-RADSB-005 | Request and Data Structures Behavior | The `URL` class must expose `scheme`, `hostname`, `port`, `path`, `query`, and `fragment` attributes parsed from the URL string. |
| STARLETTE-RADSB-006 | Request and Data Structures Behavior | `str(url)` must produce the full URL string. |
| STARLETTE-RADSB-007 | Request and Data Structures Behavior | `url.replace(scheme=..., path=...)` must return a new `URL` with the specified components changed and all other components preserved; the original URL must remain unchanged. |
| STARLETTE-RADSB-008 | Request and Data Structures Behavior | `request.base_url` must represent the application base URL and root path for reverse URL construction. |
| STARLETTE-RADSB-009 | Request and Data Structures Behavior | `request.headers` must be immutable, case-insensitive, and multi-valued. |
| STARLETTE-RADSB-010 | Request and Data Structures Behavior | Missing header lookup must raise `KeyError`; `get` must return the caller's default. |
| STARLETTE-RADSB-011 | Request and Data Structures Behavior | Assigning to headers must raise `TypeError`. |
| STARLETTE-RADSB-012 | Request and Data Structures Behavior | `headers.getlist(name)` must return all values for a given header name as a list of strings. |
| STARLETTE-RADSB-013 | Request and Data Structures Behavior | `MutableHeaders` must support assignment and must be constructable from `raw=` byte pair lists for response header manipulation. |
| STARLETTE-RADSB-014 | Request and Data Structures Behavior | `request.query_params` must be an immutable multidict of string keys and values parsed from the query string. |
| STARLETTE-RADSB-015 | Request and Data Structures Behavior | It must expose `getlist(key)` returning all values for the key as a list, `get(key, default=None)` returning the last value or default, `keys()` returning distinct key names, and `multi_items()` returning all key-value pairs including duplicates as a list of tuples. |
| STARLETTE-RADSB-016 | Request and Data Structures Behavior | `request.cookies` must parse valid Cookie header pairs into a regular dictionary and must ignore invalid cookie fragments. |
| STARLETTE-RADSB-017 | Request and Data Structures Behavior | `request.client` must return an address object with `host` and `port` when the ASGI scope has a client tuple, and must return `None` when no client is provided. |
| STARLETTE-RADSB-018 | Request and Data Structures Behavior | `await request.body()` must collect and cache the entire request body. |
| STARLETTE-RADSB-019 | Request and Data Structures Behavior | Later `await request.body()` calls must return the cached bytes. |
| STARLETTE-RADSB-020 | Request and Data Structures Behavior | `await request.json()` must parse the cached body as JSON and must raise `json.JSONDecodeError` when the body is not valid JSON. |
| STARLETTE-RADSB-021 | Request and Data Structures Behavior | `request.stream()` must yield incoming body chunks without storing the whole body. |
| STARLETTE-RADSB-022 | Request and Data Structures Behavior | After the stream has been consumed directly, later calls to `body`, `form`, or `json` must raise `RuntimeError`. |
| STARLETTE-RADSB-023 | Request and Data Structures Behavior | If the receive channel reports `http.disconnect` while streaming, `request.stream()` must raise `ClientDisconnect`. |
| STARLETTE-RADSB-024 | Request and Data Structures Behavior | `request.form(max_files=1000, max_fields=1000, max_part_size=1048576)` must parse form and multipart bodies into immutable `FormData`. |
| STARLETTE-RADSB-025 | Request and Data Structures Behavior | Multipart parts with a `filename` field must be represented as `UploadFile`; parts without `filename` must be represented as strings. |
| STARLETTE-RADSB-026 | Request and Data Structures Behavior | If multipart support is not installed and multipart parsing is requested, the call must raise an assertion error. |
| STARLETTE-RADSB-027 | Request and Data Structures Behavior | `UploadFile` must expose `filename`, `content_type`, `file`, `headers`, and `size`. |
| STARLETTE-RADSB-028 | Request and Data Structures Behavior | Its async `write`, `read`, `seek`, and `close` methods must operate on the underlying file object. |
| STARLETTE-RADSB-029 | Request and Data Structures Behavior | `request.is_disconnected()` must return a boolean indicating whether an `http.disconnect` message has been observed. |
| STARLETTE-RADSB-030 | Request and Data Structures Behavior | Accessing `request.session`, `request.auth`, or `request.user` without the corresponding middleware-provided scope key must raise `AssertionError`. |
| STARLETTE-RB-026 | Response Behavior | `Response` must be an ASGI app with cookie set and delete helpers. |
| STARLETTE-RB-027 | Response Behavior | A `Response` must render `None` as an empty body, bytes and memoryview unchanged, and strings with the response charset. |
| STARLETTE-RB-028 | Response Behavior | It must send one `http.response.start` message followed by one `http.response.body` message. |
| STARLETTE-RB-029 | Response Behavior | `Response` must automatically add `Content-Length` when a body exists and the status code allows a body. |
| STARLETTE-RB-030 | Response Behavior | It must not add `Content-Length` for informational responses, 204, or 304. |
| STARLETTE-RB-031 | Response Behavior | `Response` must automatically add `Content-Type` when a media type exists and the caller did not provide one. |
| STARLETTE-RB-032 | Response Behavior | Text media types must include `; charset=utf-8` unless the media type already includes a charset. |
| STARLETTE-RB-033 | Response Behavior | Caller-provided `content-length` or `content-type` headers must not be overwritten by automatic header generation. |
| STARLETTE-RB-034 | Response Behavior | `HTMLResponse` must set `text/html` as the media type and must render the provided content as its body with appropriate content-length. |
| STARLETTE-RB-035 | Response Behavior | `PlainTextResponse` must set `text/plain` as the media type. |
| STARLETTE-RB-036 | Response Behavior | `JSONResponse` must render compact UTF-8 JSON, must preserve non-ASCII characters without escaping them to ASCII sequences, and must reject non-finite numeric values by raising `ValueError`. |
| STARLETTE-RB-037 | Response Behavior | The content-type must be `application/json`. |
| STARLETTE-RB-038 | Response Behavior | The JSON body must round-trip: parsing it back must produce the original data structure. |
| STARLETTE-RB-039 | Response Behavior | `RedirectResponse` must default to status 307 and must set `Location` to the quoted redirect URL where spaces and special characters are percent-encoded. |
| STARLETTE-RB-040 | Response Behavior | `Response.set_cookie` must append a `Set-Cookie` header with the provided key, value, max age, expiry, path, domain, secure, httponly, samesite, and partitioned attributes. |
| STARLETTE-RB-041 | Response Behavior | Invalid `samesite` values must raise `AssertionError`. |
| STARLETTE-RB-042 | Response Behavior | `Response.delete_cookie` must expire a cookie by setting `max-age=0` and `expires=0` using the provided path, domain, secure, httponly, and samesite options. |
| STARLETTE-RB-043 | Response Behavior | If a response has a background task, it must run after the response body has been sent. |
| STARLETTE-RB-044 | Response Behavior | `BackgroundTasks` must execute tasks in insertion order via `tasks.add_task(fn, *args)`. |
| STARLETTE-RB-045 | Response Behavior | When one task raises, later tasks must not execute. |
| STARLETTE-RB-046 | Response Behavior | `StreamingResponse` must send chunks from async iterables directly and must run sync iterables through a threadpool-compatible iterator. |
| STARLETTE-RB-047 | Response Behavior | If the client disconnects during streaming, the response must stop streaming and propagate the disconnect condition. |
| STARLETTE-RB-048 | Response Behavior | `FileResponse` must stream the target file and include `Content-Length`, `Last-Modified`, `ETag`, and `Accept-Ranges: bytes` when the file exists. |
| STARLETTE-RB-049 | Response Behavior | If the file does not exist at ASGI call time, it must raise `RuntimeError`. |
| STARLETTE-RB-050 | Response Behavior | If the path is not a regular file, it must raise `RuntimeError`. |
| STARLETTE-RB-051 | Response Behavior | `FileResponse` must infer media type from `filename` or path when `media_type` is not provided. |
| STARLETTE-RB-052 | Response Behavior | When `filename` is provided, it must set `Content-Disposition` using `attachment` by default or the provided disposition type. |
| STARLETTE-RB-053 | Response Behavior | `FileResponse` must support single and multiple byte ranges for `Range: bytes=...`. |
| STARLETTE-RB-054 | Response Behavior | A satisfiable range must return 206 with a `Content-Range` header in the format `bytes start-end/total` and the selected bytes as the body. |
| STARLETTE-RB-055 | Response Behavior | An unsatisfiable range must return 416 with `Content-Range: */<file-size>`. |
| STARLETTE-RB-056 | Response Behavior | A malformed range must return 400. |
| STARLETTE-RB-057 | Response Behavior | `FileResponse` must honor `If-Range`: when the condition matches the current ETag or last-modified value it must serve the requested range; otherwise it must serve the full file. |
| STARLETTE-RB-058 | Response Behavior | For `HEAD` requests, file and static responses must return headers without a response body. |
| STARLETTE-WB-001 | WebSocket Behavior | `WebSocket` must wrap a WebSocket scope, must be mapping-compatible with the scope, and must expose URL, headers, query parameters, path parameters, state, accept, receive, send, typed receive and send helpers, typed async iterators, close, and denial-response helpers. |
| STARLETTE-WB-002 | WebSocket Behavior | `WebSocket` must assert `scope["type"] == "websocket"` at construction. |
| STARLETTE-WB-003 | WebSocket Behavior | `websocket.url`, `headers`, `query_params`, `path_params`, `state`, and `url_for` must follow the same connection-scope semantics as `HTTPConnection`. |
| STARLETTE-WB-004 | WebSocket Behavior | `await websocket.accept(subprotocol=None, headers=None)` must wait for the connection message when needed, then send an accept message with the selected subprotocol and headers. |
| STARLETTE-WB-005 | WebSocket Behavior | When a subprotocol is provided, the client-side WebSocket session must expose the selected value through `session.accepted_subprotocol`. |
| STARLETTE-WB-006 | WebSocket Behavior | `await websocket.receive_text()`, `receive_bytes()`, and `receive_json(mode="text")` must require an accepted connection. |
| STARLETTE-WB-007 | WebSocket Behavior | If called before accept, they must raise `RuntimeError`. |
| STARLETTE-WB-008 | WebSocket Behavior | `receive_json(mode="text")` must decode JSON from text messages by default. |
| STARLETTE-WB-009 | WebSocket Behavior | With `mode="binary"` it must decode JSON from binary messages. |
| STARLETTE-WB-010 | WebSocket Behavior | Invalid mode values must raise `RuntimeError`. |
| STARLETTE-WB-011 | WebSocket Behavior | `send_json(data, mode="text")` must send JSON as a text message by default. |
| STARLETTE-WB-012 | WebSocket Behavior | With `mode="binary"` it must send JSON bytes. |
| STARLETTE-WB-013 | WebSocket Behavior | Invalid mode values must raise `RuntimeError`. |
| STARLETTE-WB-014 | WebSocket Behavior | If an incoming message is `websocket.disconnect`, typed receive helpers must raise `WebSocketDisconnect` with the close code and reason. |
| STARLETTE-WB-015 | WebSocket Behavior | The `WebSocketDisconnect` exception must preserve `code` and `reason` attributes matching the values sent by the remote end. |
| STARLETTE-WB-016 | WebSocket Behavior | `iter_text`, `iter_bytes`, and `iter_json` must yield incoming messages until `WebSocketDisconnect`, then exit the iterator without re-raising the disconnect. |
| STARLETTE-WB-017 | WebSocket Behavior | `await websocket.close(code=1000, reason=None)` must send a close message. |
| STARLETTE-WB-018 | WebSocket Behavior | Calling `close` before `accept` must deny the upgrade with an HTTP 403 response in server contexts that follow Starlette's default behavior; the client must observe a `WebSocketDisconnect` with code 1000. |
| STARLETTE-WB-019 | WebSocket Behavior | `await websocket.send_denial_response(response)` must send the supplied HTTP response as a WebSocket denial response and then close. |
| STARLETTE-WB-020 | WebSocket Behavior | If the ASGI scope does not advertise support for the denial response extension, it must raise `RuntimeError`. |
| STARLETTE-SFB-001 | Static Files Behavior | `StaticFiles` must be an ASGI app for HTTP static serving with optional package directories, HTML index mode, directory existence checking, and symlink following. |
| STARLETTE-SFB-002 | Static Files Behavior | `StaticFiles` must serve only HTTP scopes; non-HTTP scopes must fail assertion. |
| STARLETTE-SFB-003 | Static Files Behavior | With `check_dir=True`, constructing `StaticFiles(directory=...)` must raise `RuntimeError` immediately when the directory does not exist. |
| STARLETTE-SFB-004 | Static Files Behavior | With `check_dir=False`, configuration must be checked on the first request and must raise `RuntimeError` if the configured path is missing or not a directory. |
| STARLETTE-SFB-005 | Static Files Behavior | `StaticFiles` must serve only `GET` and `HEAD`. |
| STARLETTE-SFB-006 | Static Files Behavior | Other methods must return HTTP 405. |
| STARLETTE-SFB-007 | Static Files Behavior | For `HEAD` requests, the response must include content headers without a response body. |
| STARLETTE-SFB-008 | Static Files Behavior | Requested paths must be normalized and must not escape the configured directories. |
| STARLETTE-SFB-009 | Static Files Behavior | Absolute paths, parent traversal, null bytes, and paths outside the served directory must return 404 rather than exposing filesystem content. |
| STARLETTE-SFB-010 | Static Files Behavior | When `follow_symlink=False`, containment checks must use the resolved real path. |
| STARLETTE-SFB-011 | Static Files Behavior | If a requested regular file exists, `StaticFiles` must return a `FileResponse` for it. |
| STARLETTE-SFB-012 | Static Files Behavior | If request validators (such as `If-None-Match` with a matching ETag) match the file's current state, it must return 304 with only cache-related headers and an empty body. |
| STARLETTE-SFB-013 | Static Files Behavior | In HTML mode, a request for a directory with `index.html` must return that file. |
| STARLETTE-SFB-014 | Static Files Behavior | If the URL path for that directory does not end with `/`, it must redirect to the slash-suffixed URL with a 301 or 307 status. |
| STARLETTE-SFB-015 | Static Files Behavior | In HTML mode, if a requested file is missing and `404.html` exists in the root directory, the response must serve that file with status 404. |
| STARLETTE-SFB-016 | Static Files Behavior | If no custom not-found file exists, the response must be 404. |
| STARLETTE-SFB-017 | Static Files Behavior | `packages=["pkg"]` must look for a `statics` directory inside that package. |
| STARLETTE-SFB-018 | Static Files Behavior | `packages=[("pkg", "static")]` must use the named package subdirectory. |
| STARLETTE-SFB-019 | Static Files Behavior | Missing packages or missing package static directories must raise `AssertionError`. |
| STARLETTE-MB-001 | Middleware Behavior | `Middleware(cls, *args, **kwargs)` must store a middleware factory and arguments and must be iterable as `(cls, args, kwargs)` for stack construction. |
| STARLETTE-MB-002 | Middleware Behavior | `BaseHTTPMiddleware` subclasses must implement `dispatch(request, call_next)`. |
| STARLETTE-MB-003 | Middleware Behavior | `call_next(request)` must call the downstream app and return a response. |
| STARLETTE-MB-004 | Middleware Behavior | If `dispatch` is not implemented, using the middleware must raise `NotImplementedError`. |
| STARLETTE-MB-005 | Middleware Behavior | Middleware configured on `Route`, `Mount`, or `Router` must wrap only that route group. |
| STARLETTE-MB-006 | Middleware Behavior | Middleware configured this way must not be automatically wrapped by Starlette's top-level exception handling middleware. |
| STARLETTE-MB-007 | Middleware Behavior | `HTTPSRedirectMiddleware` must redirect HTTP to HTTPS and WebSocket to WSS while preserving host, path, query string, and port when present. |
| STARLETTE-MB-008 | Middleware Behavior | The redirect must use status 307. |
| STARLETTE-MB-009 | Middleware Behavior | Secure HTTP or WebSocket scopes must pass through unchanged. |
| STARLETTE-MB-010 | Middleware Behavior | `TrustedHostMiddleware` must allow exact hosts, wildcard subdomains such as `*.example.com`, and `"*"`. |
| STARLETTE-MB-011 | Middleware Behavior | Invalid hosts must produce a 400 response. |
| STARLETTE-MB-012 | Middleware Behavior | With `www_redirect=True`, a valid `www.` host counterpart must redirect when the incoming host omits `www`. |
| STARLETTE-MB-013 | Middleware Behavior | `GZipMiddleware` must compress HTTP responses when the request `Accept-Encoding` includes `gzip`, the response has no existing `Content-Encoding`, the response is not `text/event-stream`, and the response body reaches `minimum_size`. |
| STARLETTE-MB-014 | Middleware Behavior | It must set the `Content-Encoding: gzip` header on compressed responses. |
| STARLETTE-MB-015 | Middleware Behavior | It must not compress smaller responses or responses that are already encoded. |
| STARLETTE-MB-016 | Middleware Behavior | `CORSMiddleware` must handle CORS preflight requests when the method is `OPTIONS` and the request includes `Origin` and `Access-Control-Request-Method`. |
| STARLETTE-MB-017 | Middleware Behavior | It must return 200 for allowed preflight requests with appropriate `Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, and `Access-Control-Allow-Headers` response headers, and 400 for disallowed CORS preflight requests. |
| STARLETTE-MB-018 | Middleware Behavior | `CORSMiddleware` must add appropriate CORS response headers to simple requests that include `Origin`. |
| STARLETTE-MB-019 | Middleware Behavior | With `allow_credentials=True` and `allow_origins=["*"]`, the middleware must echo the explicit request origin in `Access-Control-Allow-Origin` rather than using a literal wildcard, and must set `Access-Control-Allow-Credentials: true`. |
| STARLETTE-MB-020 | Middleware Behavior | If `allow_private_network=True`, an allowed private-network preflight must include `Access-Control-Allow-Private-Network: true`. |
| STARLETTE-MB-021 | Middleware Behavior | If private network access is requested and not allowed, the preflight must fail with 400. |
| STARLETTE-ES-001 | Error Semantics | `HTTPException(status_code, detail=None, headers=None)` must preserve `status_code`, `detail`, and `headers`. |
| STARLETTE-ES-002 | Error Semantics | When raised during an application request, it must become a plain-text HTTP response using the status code, detail as body text, and headers. |
| STARLETTE-ES-003 | Error Semantics | Raising `HTTPException` inside routing or endpoints must produce the configured HTTP error response. |
| STARLETTE-ES-004 | Error Semantics | Raising it before a WebSocket accept must deny the WebSocket upgrade with an HTTP response. |
| STARLETTE-ES-005 | Error Semantics | Custom exception handlers keyed by status code must handle matching `HTTPException` status codes. |
| STARLETTE-ES-006 | Error Semantics | Handlers keyed by exception class must handle matching exception instances. |
| STARLETTE-ES-007 | Error Semantics | Error handlers registered under `500` or `Exception` must handle unhandled application errors. |
| STARLETTE-ES-008 | Error Semantics | With `debug=True`, traceback responses must take precedence over an installed 500 handler. |
| STARLETTE-ES-009 | Error Semantics | `WebSocketException(code=1008, reason=None)` must preserve `code` and `reason` and must be usable with a custom WebSocket exception handler. |
| STARLETTE-ES-010 | Error Semantics | `WebSocketDisconnect(code=1000, reason=None)` must be raised by WebSocket receiving helpers when a disconnect message is received. |
| STARLETTE-ES-011 | Error Semantics | It must preserve `code` and `reason` as accessible attributes. |
| STARLETTE-ES-012 | Error Semantics | `NoMatchFound` must be raised by reverse lookup when no route name and parameter set matches. |
| STARLETTE-ES-013 | Error Semantics | Accessing `request.session`, `request.auth`, or `request.user` without the corresponding middleware-provided scope key must raise `AssertionError`. |
| STARLETTE-CVI-001 | Cross-View Invariants | A route handled successfully through `TestClient.get()` must be the same route that direct ASGI dispatch would select for the same HTTP scope path, method, host, root path, and query string. |
| STARLETTE-CVI-002 | Cross-View Invariants | A route parameter converted by an `int`, `float`, `uuid`, `path`, or registered convertor must return the converted Python value on the request or WebSocket object, must produce the same value in `request.url_for` reverse generation, and must match `app.url_path_for` for the same name and parameters. |
| STARLETTE-CVI-003 | Cross-View Invariants | A `Response` returned by an endpoint must expose the same status code, headers, body bytes, and cookies through `TestClient` as it sends over ASGI `http.response.start` and `http.response.body` messages. |
| STARLETTE-CVI-004 | Cross-View Invariants | A header appended by middleware around an endpoint must be visible in the final `TestClient` response and must be visible in `MutableHeaders` constructed from the raw ASGI start message headers. |
| STARLETTE-CVI-005 | Cross-View Invariants | Lifespan state yielded before requests must be visible in both HTTP request handlers (via `request.state`) and WebSocket handlers (via `websocket.state`) during the same context-managed client session. |
| STARLETTE-CVI-006 | Cross-View Invariants | A `StaticFiles` app mounted under a named route must serve the same file bytes when accessed via `request.url_for(mount_name, path=filename)` as when accessed by constructing the path directly. |
| STARLETTE-CVI-007 | Cross-View Invariants | A WebSocket endpoint that accepts, sends JSON over text mode, and closes must be observable through `TestClient.websocket_connect()` using `receive_json(mode="text")`, followed by a `WebSocketDisconnect` on further receive. |
| STARLETTE-CVI-008 | Cross-View Invariants | A background task attached to a response must run after the response body is sent, so the HTTP client receives the response status and body even when later background work mutates application-visible state or raises. |
| STARLETTE-CEP-001 | CLI Entry Points | \| Invocation \| Supported \| Result \| \|---\|---:\|---\| \| `from starlette.applications import Starlette` \| yes \| imports the application class \| \| `from starlette.testclient import TestClient` \| yes \| imports the synchronous in-process client when its HTTP client dependency is installed \| \| `python -m starlette` \| no \| must not be required for application behavior \| |
| STARLETTE-AAE-001 | Appendix A: Environment | Runtime dependencies must be declared in a standard `requirements.txt` or `pyproject.toml` at the project root and are installed before use. |

<!-- spec.md -->
# Starlette Specification

This document defines the public Starlette behavior in scope. The companion
composition addendum refines the contracts at composition boundaries and takes
precedence where it is more specific.

## Product Overview

Starlette is a lightweight ASGI toolkit for building HTTP and WebSocket applications. A Starlette application is itself an ASGI callable, and its public behavior is visible through route matching, request and WebSocket wrapper objects, response ASGI messages, middleware effects, lifespan startup and shutdown, TestClient calls, and file-serving responses.

This specification describes the core application behavior needed to build in-process Starlette applications. It focuses on observable behavior through documented public imports and ASGI/TestClient interactions.

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

`await websocket.accept(subprotocol=None, headers=None)` must wait for the connection message when needed, then send an accept message with the selected subprotocol and headers. When a subprotocol is provided, the client-side WebSocket session must expose the selected value through `session.accepted_subprotocol`.

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
5. Lifespan state yielded before requests must be visible in both HTTP request handlers (via `request.state`) and WebSocket handlers (via `websocket.state`) during the same context-managed client session.
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
| TestClient | class | Synchronous in-process HTTP and WebSocket client |
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
| `from starlette.testclient import TestClient` | yes | imports the synchronous in-process client when its HTTP client dependency is installed |
| `python -m starlette` | no | must not be required for application behavior |

## Appendix A: Environment

The implementation may use third-party packages available on PyPI. Runtime dependencies must be declared in a standard `requirements.txt` or `pyproject.toml` at the project root and are installed before use. Covered workflows run in process with local temporary files and do not require a live network server.

## Appendix B: Public Compatibility Boundary

The public surface includes public imports, in-process ASGI calls, `TestClient` HTTP requests, `TestClient` WebSocket sessions, temporary static files, response headers and bodies, and lifespan context entry and exit. Implementations must satisfy the observable contracts for routing, state propagation, middleware effects, request body consumption, response rendering, WebSocket lifecycle, file serving, and documented error handling.

Compatibility is defined by public behavior only. Private modules, private helper functions, exact traceback pages, exact `repr` strings, undocumented fixture carriers, and live external services are outside this specification.

<!-- spec-addendum.md -->
# Starlette Composition Addendum

This addendum refines the public contracts for applications that combine routing,
lifespan state, request and response streaming, files, WebSockets, clients, and
middleware. It takes precedence where it makes a composition boundary more
specific. It does not prescribe internal helpers, task primitives, queue types,
event-loop scheduling, or private attributes.

## Routed applications and reverse URLs

A custom path convertor keeps the same `convert()` and `to_string()` behavior when
its route is nested below a named `Mount`. With a client-visible `root_path`, the
endpoint receives the external `scope["path"]`, the mount-extended
`scope["root_path"]`, and an absolute `request.url_for()` containing the client
root, mount prefix, and converted value. `app.url_path_for()` remains path-only and
does not include the client root.

Named `Host` and `Mount` boundaries compose for both HTTP and WebSocket routes.
Host, mount, and endpoint parameters are retained together. In one lifespan
session, nested objects yielded as lifespan state are shared between an HTTP
request and a later WebSocket connection, while each connection still receives a
shallow top-level state copy. Reverse URLs generated in the HTTP and WebSocket
handlers use `https` and `wss` respectively and include the visible root path.

An HTTP route and WebSocket route may share a path without crossing protocol
boundaries. `HEAD` selects a GET-capable HTTP route and a synchronous client
exposes an empty response body while retaining representation headers such as
`Content-Length`. Method and missing-path responses remain 405 and 404.

## Lifespan sessions and state ownership

Constructing a `TestClient` has no lifespan effect. Each entry into a client
context creates one new lifespan session; each exit completes that session. A
client object may be entered again, in which case the new session receives newly
yielded top-level and nested state rather than state retained from the prior
session.

Within one session, each HTTP request and WebSocket connection receives a shallow
copy of the yielded mapping. Rebinding a top-level value is local to that
connection. Mutating a nested object is visible to later connections in the same
session. A later client context receives the values yielded for that new context.

## Client redirects, cookies, and application view

When redirect following is enabled, cookies set on an intermediate response are
stored before the redirected request is issued. The redirected request uses the
configured base scheme and authority and retains the configured `root_path` in
its ASGI scope. The initial redirect remains available in response history.
Disabling server-exception propagation continues to return an HTTP 500 response
for an unhandled endpoint exception that has not started a response.

## Background work through HTTP middleware

Passing a response through `BaseHTTPMiddleware` does not move background work
ahead of the response body. A background exception occurs after the response has
started and cannot replace the already produced status, headers, or body. With
server exceptions enabled the synchronous client surfaces the exception. With
them disabled it returns the original response, including headers added by the
middleware.

## Streaming and HEAD projections

An async `StreamingResponse` emits each non-empty application chunk in order and
then a terminal empty body message. Its background task runs after that terminal
message. A `HEAD` request through `TestClient` exposes no body while the stream and
its background task are still completed according to the response pipeline.

GZip middleware preserves an existing `Vary` value and adds
`Accept-Encoding` without discarding other fields. Small, pre-encoded, and
`text/event-stream` responses remain excluded. An eligible `HEAD` response has
the same gzip selection headers as the corresponding GET response but no client
body.

## File and static response composition

For a single file range, either the current ETag or current Last-Modified value
may satisfy `If-Range`. A matching condition returns the requested 206 range; a
stale condition returns the complete 200 representation. `HEAD` uses the same
range status and metadata as GET and returns no body. A configured background
task runs after full, range, and HEAD responses complete.

A named static mount participates in reverse lookup with the visible root path.
In addition to ETag validation, a matching `If-Modified-Since` value returns a 304
response with an empty body. HEAD retains the selected file's content metadata
without returning file bytes.

## WebSocket denial responses

A denial response may itself be streaming. With the denial extension available,
its response-start message and every response-body message are translated to the
corresponding `websocket.http.response.*` messages. The final body message is
terminal and no extra close message is required. Without the extension, denial
raises before any denial output is sent.

## CORS and redirect middleware composition

When a concrete origin is echoed, CORS responses include `Origin` in `Vary`.
Credentialed simple responses preserve the explicit origin. An allowed preflight
may simultaneously validate its method, requested headers, and private-network
request, returning the corresponding allow headers.

When trusted-host validation wraps HTTPS redirection, an allowed insecure host is
redirected to its secure scheme while preserving authority, path, and query. A
valid `www.` correction is produced by the host layer. An invalid host is rejected
without a redirect location, and an already secure allowed request reaches the
application unchanged.

## Stability boundary

The contracts above concern public ASGI messages, public wrapper values, and
synchronous client projections. They do not constrain exact exception prose,
multipart boundary strings, private task structure, event-loop tick order, or
the timing of cancellation beyond the documented terminal-message and background
ordering.
