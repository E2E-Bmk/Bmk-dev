# Quart Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Quart is an asynchronous Python web framework for HTTP applications, JSON APIs, templates, streamed request or response bodies, and WebSockets. Application handlers and the client-facing helpers in this specification are awaitable when they perform I/O or dispatch work.

## Non-Goals

This specification does not define production-server deployment, ASGI message internals, HTTP/2 push details, static-file cache policy, logging format, signal delivery order, private context structures, exact header ordering, exact exception text, or internal routing and template-loader implementation.

## Representative Workflows

```python
from quart import Quart, jsonify, request, session, url_for

app = Quart(__name__)
app.secret_key = "development-secret"

@app.route("/items/<int:item_id>", methods=["POST"])
async def save_item(item_id):
    payload = await request.get_json()
    session["last_item"] = item_id
    return jsonify(item=payload["name"], detail=url_for("item", item_id=item_id)), 201

@app.route("/items/<int:item_id>")
async def item(item_id):
    return {"item_id": item_id, "last_item": session.get("last_item")}

async def exercise():
    client = app.test_client()
    created = await client.post("/items/3", json={"name": "book"})
    assert created.status_code == 201
    fetched = await client.get("/items/3")
    assert await fetched.get_json() == {"item_id": 3, "last_item": 3}
```

## Application Registration and Routing

This section covers how applications are created, how routes and blueprints are registered, and how URLs are generated from registered endpoints.

**Application creation.** A `Quart` application must be created by passing a Python import name. The resulting object holds all routing, configuration, and handler state for the application.

**Route registration.** `app.route` must register a handler for HTTP requests matching the supplied rule and return the decorated function. The handler may be either an asynchronous or a synchronous callable. When `methods` is supplied, only those HTTP methods must be dispatched to the handler. `app.websocket` must register a handler for WebSocket upgrade requests and return the decorated function. An invalid rule must raise during registration rather than become dispatchable.

**Test client.** `app.test_client()` must return a bound `QuartClient`. When `use_cookies` is `True` (the default), the client must retain cookies across requests. `app.app_context()` must return an async context manager that establishes an application context. `app.test_request_context` must return an async context manager that establishes a request context for the supplied `path` with an optional `method` defaulting to `"GET"`.

**Blueprint registration.** A `Blueprint` must provide the same `route` and `websocket` decorator style for modular route grouping. `app.register_blueprint` must make the blueprint's registered handlers available on the application, accepting an optional `url_prefix` to mount the blueprint's routes under a common path prefix. Registering an incompatible value must raise an exception. A handler registered on a blueprint must be addressable by an endpoint whose name is qualified by that blueprint name. A nested blueprint must expose child endpoint names qualified by both blueprint names. A missing endpoint must cause URL generation to raise rather than invent a URL.

**Route converters.** Route rules must support static paths and variables written as `<name>` or `<converter:name>`. The `int` converter must pass an integer to the handler and must reject non-integer path text with a 404 response. The `path` converter must accept slashes. The default string converter must not accept a slash; a request whose path segment contains a slash for a default-converter variable must return a 404 response. When a default value is supplied for a route variable, it must be passed to the handler when that rule matches. An unresolved required variable must cause URL generation to raise.

**URL generation.** `url_for` must return a URL for a registered endpoint using the supplied route variables. It must raise when no matching endpoint or required variable exists. When `_external` is `True` and `app.config["SERVER_NAME"]` is set, `url_for` must produce an absolute URL using that server name as the URL authority. When `_external` is `False`, `url_for` must produce a relative path. When `_scheme` is supplied, the generated external URL must use that scheme. When `_anchor` is supplied, the URL must include that value as a fragment (e.g. `#details`). Within a blueprint handler, an endpoint beginning with `.` must resolve against the active blueprint. Outside a matching context, a relative endpoint that cannot be resolved must raise.

**Configuration.** `app.config` must be a `Config` mapping. `from_prefixed_env` must load environment variables whose names begin with the given `prefix` followed by `"_"`, dropping that prefix to form the configuration key. It must apply a `loads` callable (defaulting to JSON parsing) to each value; when `loads` raises, it must retain the original string. A double underscore in the remaining name must address nested mapping keys, creating an intermediate mapping when it is absent. An environment variable without the required prefix must not alter the mapping.

## HTTP Request and Response Handling

This section covers how the test client sends requests, how request data is accessed within handlers, and how handler results are converted into HTTP responses.

**Client requests.** `client.open` must send an in-process request and return a `Response`, accepting a `path` and a `method` defaulting to `"GET"`. The client must provide shorthand methods `get`, `post`, `put`, `patch`, `delete`, `head`, `options`, and `trace` that delegate to the corresponding HTTP method. When `query_string` is a mapping of parameter names to values, the active handler must observe those key/value pairs through `request.args`. When `json` is supplied, the request body must be JSON-encoded. When `data` is supplied, the request body must contain the supplied bytes. A request to an unmatched HTTP rule must return a 404 response. A request using a method that the matched rule does not accept must return a 405 response.

**Request body access.** Within an active request, `request` must expose `method`, `path`, `headers`, and query arguments through `request.args`. `await request.get_data()` must return the received body as bytes by default, or as text when `as_text` is `True`. After a call with `cache` set to `False`, subsequent body access must return an empty body. `await request.get_json()` must return parsed JSON for a JSON-content-type request and must return `None` for a non-JSON request unless `force` is `True`. Malformed JSON must raise unless `silent` is `True`, in which case it must return `None`.

**Handler result conversion.** A handler result must convert as follows: a `str` must produce a text response. `bytes`, `bytearray`, synchronous generators, and asynchronous generators must produce a response body. A `dict` or `list` must produce a JSON response. A `Response` must be returned as the response. A tuple of `(value, status)`, `(value, headers)`, or `(value, status, headers)` must apply the supplied status or headers to the converted value. `None`, an unsupported value type, or a tuple with an unsupported length must raise `TypeError` rather than produce a successful response.

**Response access.** `Response` must expose `status_code`, `headers`, and `await response.get_data()`, returning bytes by default and text when `as_text` is `True`. `await response.get_json()` must follow the same JSON failure rule as request JSON access.

**JSON responses.** `jsonify` must return a JSON `Response` with Content-Type `application/json` and status code 200. It must accept positional arguments, keyword arguments, or both; positional arguments must produce a JSON array response. Invalid JSON serialization must raise rather than return a partial response. `make_response` must apply the same response-value conversion as handler result conversion. Passing a `Response` directly must return it. Passing a tuple of `(Response, headers)` or `(Response, status, headers)` must apply the supplied status or headers. Passing `None` or an invalid response value must raise `TypeError`.

## Context and Session Management

This section covers application and request contexts, context-bound proxies, session state persistence, and flash messaging.

**Application context.** Inside `async with app.app_context()`, `current_app` must resolve to the entered application and `g` must resolve to its application-global namespace. Values assigned to `g` (e.g. `g.answer = 42`) must be readable within the same context. `has_app_context()` must return `True` inside an app context and `False` outside.

**Request context.** Inside `async with app.test_request_context(path, method=...)`, `request`, `session`, `current_app`, and `g` must all resolve for that context. `request.path` must return the supplied path and `request.method` must return the supplied method. `has_request_context()` must return `True` inside and `False` outside. A request context must also establish an application context, so `has_app_context()` must return `True` during a request context. On exit from either context, accessing the corresponding proxies must raise `RuntimeError`.

**WebSocket context.** `has_websocket_context()` must return whether a WebSocket context is active.

**Context copying.** `copy_current_app_context` must decorate an async callable so that the decorated callable runs with a copy of the app context captured at decoration time. The decorated callable must observe the same `g` values that were set before decoration. `copy_current_request_context` must do the same for request context, making `request` and its attributes (such as `request.path`) available in the decorated callable. `copy_current_websocket_context` must do the same for WebSocket context, making `websocket` and its headers available in the decorated callable. Each helper must raise `RuntimeError` when decoration occurs without its matching active context.

**After-request callbacks.** `after_this_request` must register a callback for the active request's response processing and return that callback. It must raise `RuntimeError` outside a request context.

**Session management.** `session` must be a mutable mapping during a request or WebSocket context. When the application has a `secret_key` and the test client retains cookies, a session value written by one HTTP request must be visible to a later HTTP request from the same client. When no secret key permits a persistent secure-cookie session, code attempting to persist a session update must receive an error response with a status code of 400 or above rather than report a successful persisted update. A session update made after an accepted WebSocket must not be promised to persist because an accepted WebSocket has no HTTP response on which to set a cookie.

**Flash messages.** `await flash(message, category)` must store a message in the current session under the supplied `category` (defaulting to `"message"`). `get_flashed_messages` must return and consume the stored messages for the current request. When `with_categories` is `True`, it must return `(category, message)` pairs. A subsequent request must observe that the consumed messages are no longer available; `get_flashed_messages` must return an empty list when no messages remain. When no messages are stored, it must return an empty list.

## Templates and WebSocket Communication

This section covers template rendering and streaming, WebSocket message exchange, and the WebSocket test client.

**Template rendering.** `await render_template` must render a named template and `await render_template_string` must render a template source string, both returning rendered text with supplied context variables substituted. Template context must include explicitly supplied values and, when their contexts are active, `config`, `g`, `request`, and `session`. Templates must also expose `url_for` and `get_flashed_messages` as standard globals. A missing template or template syntax error must raise rather than render an empty string.

**Template streaming.** `await stream_template_string` must return rendered text for a template source string with streaming support. `stream_with_context` must preserve the active request context for iteration of the returned stream, so that `request` and its attributes remain accessible during iteration. Decorating a stream without an active request context must raise. An undecorated generator must raise when it accesses request-bound proxies after the request context has ended.

**WebSocket messages.** Within an active WebSocket handler, `websocket` must expose `headers` and awaitable `accept`, `close`, `receive`, `send`, `receive_json`, and `send_json` methods. `receive` must accept the connection and return `str` for a text frame and `bytes` for a binary frame, preserving the text-or-bytes kind of the sent value. `send` must accept the connection and transmit the supplied text or bytes. `send_json` must serialize a value as JSON and transmit it. `receive_json` must receive and decode a JSON message. `send_json` must raise `TypeError` when positional and keyword JSON arguments are mixed. JSON decoding must raise for invalid JSON rather than returning a substituted value. Closing an unaccepted WebSocket must result in an HTTP 403 rejection.

**WebSocket test client.** `client.websocket` must return an async context manager for a WebSocket test connection. Its `send`, `receive`, `send_json`, and `receive_json` methods must mirror the corresponding WebSocket message behavior. When a WebSocket handler returns an HTTP response instead of accepting the connection, the test connection must raise `WebsocketResponseError`; its `response` attribute must expose the rejection status code and body. When a WebSocket handler calls `abort(status)` before accepting the connection, the client connection must raise `WebsocketResponseError` whose `response.status_code` must return the supplied status value. Closing or disconnecting a test connection must end the peer operation rather than leave it waiting indefinitely.

## State Model

An application has one public routing/configuration state with three observable projections:

1. Registration projection: decorators and blueprint registration define HTTP and WebSocket endpoints.
2. Dispatch projection: a `QuartClient` sends an HTTP request or opens a WebSocket and receives the handler's observable result.
3. Context projection: the active handler observes `current_app`, `g`, and either `request`/`session` or `websocket`/`session`.

The registration projection must be complete before a matching client operation dispatches. The dispatch projection must expose a route handler's returned value through a `Response`. The context projection must expose the application that received the operation while that handler runs. Attempting to use a context-bound proxy without its required active context must raise `RuntimeError`.

## Error Semantics

| Condition | Required outcome |
|---|---|
| Context-bound proxy is used outside its active context | Raises `RuntimeError`. |
| HTTP rule is absent | Returns status 404. |
| HTTP method is not allowed by a matching rule | Returns status 405. |
| Route converter rejects a path value | Returns status 404. |
| URL endpoint or required route variable is absent | Raises during `url_for`. |
| Handler returns `None`, an unsupported value, or an invalid-length tuple | Raises `TypeError`. |
| JSON data is invalid and `silent=False` | Raises. |
| `copy_current_*_context` is applied without its matching context | Raises `RuntimeError`. |
| `after_this_request` is used outside a request context | Raises `RuntimeError`. |
| `stream_with_context` is applied without a request context | Raises. |
| `websocket.send_json` receives positional and keyword arguments together | Raises `TypeError`. |
| WebSocket route rejects with an HTTP response in test-client use | Raises `WebsocketResponseError` with that response. |
| WebSocket handler calls `abort(status)` before accepting the connection | Raises `WebsocketResponseError`; its public `response.status_code` returns `status`. |
| Session write without a configured secret key | Returns error response (status ≥ 400). |

## Cross-View Invariants

1. A handler registered through `app.route` must return the same observable body, status, and headers through `app.test_client()` as the handler's response value specifies.
2. A handler registered through a blueprint must be reachable through the application after `app.register_blueprint`, and `url_for` must return its registered URL.
3. A value placed in `session` by an HTTP handler must be visible to a later HTTP handler when both requests use the same cookie-preserving client and persistent sessions are configured.
4. `current_app` must return the application owning the active request, WebSocket, or explicit app context.
5. A template rendered during a request must return the same current `request`, `session`, `g`, and configuration values that the handler observes through the corresponding proxies.
6. A text or binary value sent through a test WebSocket connection must return from the server's `websocket.receive` with its original text-or-bytes kind.
7. A JSON value sent through a test WebSocket connection must return from `receive_json` as the decoded JSON value when the peer sends valid JSON.
8. A context-preserving stream must return request-bound values while it is iterated from the request that created it.

## Public Interface

### Import Surface

The root package must provide these importable names:

```python
from quart import (
    Blueprint, Config, Markup, Quart, Request, Response, ResponseReturnValue,
    Websocket, abort, after_this_request, appcontext_popped,
    appcontext_pushed, appcontext_tearing_down, before_render_template,
    copy_current_app_context, copy_current_request_context,
    copy_current_websocket_context, current_app, escape, flash,
    g, get_flashed_messages, get_template_attribute, got_request_exception,
    got_websocket_exception, has_app_context, has_request_context,
    has_websocket_context, jsonify, make_push_promise, make_response,
    message_flashed, redirect, render_template, render_template_string,
    request, request_finished, request_started, request_tearing_down,
    send_file, send_from_directory, session, signals_available,
    stream_template, stream_template_string, stream_with_context,
    template_rendered, url_for, websocket, websocket_finished,
    websocket_started, websocket_tearing_down,
)
from quart.testing import (
    QuartCliRunner, QuartClient, TestApp, WebsocketResponseError,
    make_test_body_with_headers, make_test_headers_path_and_query_string,
    make_test_scope, no_op_push, sentinel,
)
```

The distribution must expose a `quart` command-line entry point. An application registers synchronous custom commands through `app.cli.command()`. Those commands must not receive an application context automatically; code that needs asynchronous work must arrange to run that work itself.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| Quart | class | Asynchronous web application |
| Blueprint | class | Modular route and handler grouping |
| Config | class | Application configuration mapping |
| Request | class | Incoming HTTP request object |
| Response | class | Outgoing HTTP response object |
| Websocket | class | WebSocket connection object |
| QuartClient | class | In-process test client for HTTP and WebSocket |
| request | proxy | Context-bound request for the active handler |
| session | proxy | Context-bound session mapping |
| websocket | proxy | Context-bound WebSocket for the active handler |
| current_app | proxy | Context-bound application reference |
| g | proxy | Context-bound application-global namespace |
| url_for | function | Generate a URL for a registered endpoint |
| jsonify | function | Return a JSON response |
| make_response | function | Convert a handler result into a Response |
| render_template | function | Render a named template with context |
| render_template_string | function | Render a template string with context |
| stream_template | function | Stream a rendered template asynchronously |
| stream_with_context | function | Preserve request context for async iteration |
| flash | function | Store a message in the current session |
| get_flashed_messages | function | Retrieve and consume stored flash messages |
| abort | function | Raise an HTTP error response |
| redirect | function | Return a redirect response |
| copy_current_app_context | function | Capture app context for a decorated callable |
| copy_current_request_context | function | Capture request context for a decorated callable |
| copy_current_websocket_context | function | Capture websocket context for a decorated callable |
| after_this_request | function | Register a callback for response processing |
| WebsocketResponseError | exception | Raised when a WebSocket is rejected with HTTP |

### CLI Entry Points

- Console script name: `quart`
- `python -m quart`: `supported`
- Exit codes:
  - `0`: success
  - `2`: an unknown command is supplied

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Evaluation exercises imports, application registration and dispatch, response conversion, routing and URL generation, client requests, contexts, sessions, templates, and WebSocket client behavior. Each checked behavior is observed from its public result, such as responses, generated URLs, context-proxy availability, and exchanged messages. The evaluation does not require a particular internal data structure, helper name, representation format, or framework implementation.
