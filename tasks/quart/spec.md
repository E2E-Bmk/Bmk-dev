
# Quart Specification

## Product Overview

Quart is an asynchronous Python web framework for HTTP applications, JSON APIs, templates, streamed request or response bodies, and WebSockets. Application handlers and the client-facing helpers in this specification are awaitable when they perform I/O or dispatch work.

## Scope

This specification covers creating an application, registering HTTP and WebSocket handlers, dispatching requests through the in-process test client, response conversion and inspection, application/request/websocket contexts, secure-cookie sessions, templating, and public WebSocket testing.

## Installable Surface

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

## Public API

### Application and registration

`Quart(import_name, **options)` creates an application. `app.route(rule, methods=None, **options)` must register a handler for HTTP requests and return the decorated function. `app.websocket(rule, **options)` must register a handler for WebSocket upgrade requests and return the decorated function. An invalid rule must raise during registration rather than become dispatchable.

`app.test_client(use_cookies=True, **kwargs)` returns a bound `QuartClient`. `app.app_context()` and `app.test_request_context(path, method="GET", **kwargs)` return async context managers. `app.register_blueprint(blueprint, **options)` must make the blueprint's registered handlers available on the application; registering an incompatible value must raise an exception.

`Blueprint(name, import_name, **options)` provides the same route and websocket decorator style for a modular application. A handler registered on a blueprint must be addressable by an endpoint whose name is qualified by that blueprint name. A nested blueprint must expose child endpoint names qualified by both blueprint names; a missing endpoint must cause URL generation to raise rather than invent a URL.

### Configuration

`app.config` must be a `Config` mapping. `app.config.from_prefixed_env(prefix="QUART", *, loads=json.loads)` must load environment variables whose names begin with `prefix + "_"`, dropping that prefix to form the configuration key. It must apply `loads` to each value; when `loads` raises, it must retain the original string. A double underscore in the remaining name must address nested mapping keys, creating an intermediate mapping when it is absent. An environment variable without the required prefix must not alter the mapping.

### Product State Model

An application has one public routing/configuration state with three observable projections:

1. Registration projection: decorators and blueprint registration define HTTP and WebSocket endpoints.
2. Dispatch projection: a `QuartClient` sends an HTTP request or opens a WebSocket and receives the handler's observable result.
3. Context projection: the active handler observes `current_app`, `g`, and either `request`/`session` or `websocket`/`session`.

The registration projection must be complete before a matching client operation dispatches. The dispatch projection must expose a route handler's returned value through a `Response`. The context projection must expose the application that received the operation while that handler runs. Attempting to use a context-bound proxy without its required active context must raise `RuntimeError`.

### HTTP requests and responses

`await client.open(path, *, method="GET", headers=None, data=None, form=None, files=None, query_string=None, json=..., follow_redirects=False, **kwargs)` sends an in-process request and returns a `Response`. `client.get`, `post`, `put`, `patch`, `delete`, `head`, `options`, and `trace` must delegate to the corresponding HTTP method. When `query_string` is a mapping of parameter names to values, `client.open` must accept that mapping and an active handler must observe its key/value pairs through `request.args`. A request to an unmatched HTTP rule must return a 404 response. A request using a method that the matched rule does not accept must return a 405 response.

Within an active request, `request` must expose the method, path, headers, query arguments, and body access. `await request.get_data(cache=True, as_text=False, parse_form_data=False)` must return received body bytes, or text when `as_text=True`; after a call with `cache=False`, subsequent body access must return an empty body. `await request.get_json(force=False, silent=False, cache=True)` must return parsed JSON for a JSON request and must return `None` for a non-JSON request unless `force=True`. Malformed JSON must raise unless `silent=True`, in which case it must return `None`.

A handler result must convert as follows:

- A `str` must produce a text response; `bytes`, `bytearray`, synchronous generators, and asynchronous generators must produce a response body.
- A `dict` or `list` must produce a JSON response.
- A `Response` must be returned as the response.
- `(value, status)`, `(value, headers)`, and `(value, status, headers)` must apply the supplied status or headers to the converted value.
- `None`, an unsupported value type, or a tuple with an unsupported length must raise `TypeError` rather than produce a successful response.

`Response` must expose `status_code`, headers, and `await response.get_data(as_text=False)`, returning bytes by default and text when `as_text=True`. `await response.get_json(force=False, silent=False)` must follow the same JSON failure rule as request JSON access.

`jsonify(*args, **kwargs)` must return a JSON `Response`; invalid JSON serialisation must raise rather than return a partial response. `await make_response(*args)` must apply the same response-value conversion; an invalid response value must raise `TypeError`.

### Routing and URL generation

Route rules must support static paths and variables written as `<name>` or `<converter:name>`. The `int` converter must pass an integer to the handler and must reject non-integer path text with a 404 response. The `path` converter must accept slashes; the default string converter must not accept a slash. Defaults supplied for a route variable must be passed to the handler when that rule matches; an unresolved required variable must cause URL generation to raise.

`url_for(endpoint, *, _anchor=None, _external=None, _method=None, _scheme=None, **values)` must return a URL for a registered endpoint using the supplied route variables. It must raise when no matching endpoint or required variable exists. When `_external=True` and `app.config["SERVER_NAME"]` is set, `url_for` must use that value as the URL authority. `_scheme` must select the scheme of that external URL, and `_anchor` must append its fragment. Within a blueprint handler, an endpoint beginning with `.` must resolve against that active blueprint; outside a matching context, a relative endpoint that cannot be resolved must raise.

### Context, sessions, and messages

Inside `async with app.app_context()`, `current_app` and `g` must resolve to the entered app and its application-global namespace. Inside `async with app.test_request_context(...)`, `request`, `session`, `current_app`, and `g` must resolve for that context. The predicates `has_app_context()`, `has_request_context()`, and `has_websocket_context()` must return whether their respective contexts are active. On exit from either context, its corresponding proxies must raise `RuntimeError` when accessed.

`copy_current_app_context`, `copy_current_request_context`, and `copy_current_websocket_context` must decorate an async callable so that invoking the decorated callable runs with a copy of the matching context captured at decoration time. Each helper must raise `RuntimeError` when decoration occurs without its matching active context. `after_this_request(callback)` must register `callback` for the active request's response processing and return that callback; it must raise `RuntimeError` outside a request context.

`session` must be a mutable mapping during a request or WebSocket context. When the application has a secret key and the test client retains cookies, a session value written by one HTTP request must be visible to a later HTTP request from that client. When no secret key permits a persistent secure-cookie session, code attempting to persist a session update must receive an error response rather than report a successful persisted update. A session update made after an accepted WebSocket must not be promised to persist because an accepted WebSocket has no HTTP response on which to set a cookie.

`await flash(message, category="message")` must store a message in the current session. `get_flashed_messages(with_categories=False, category_filter=())` must return and consume the stored messages for the current request. When `with_categories=True`, it must return `(category, message)` pairs. When no messages are stored, it must return an empty list.

### Templates and streamed context

`await render_template(name_or_list, **context)` and `await render_template_string(source, **context)` must return rendered text. Template context must include explicitly supplied values and, when their contexts are active, `config`, `g`, `request`, and `session`; it must expose `url_for` and `get_flashed_messages` as standard globals. A missing template or template syntax error must raise rather than render an empty string.

`await stream_template(...)` and `await stream_template_string(...)` must return asynchronous iterators of rendered text. `stream_with_context(generator_function)` must preserve the active request context for iteration of the returned stream. Decorating a stream without an active request context must raise; an undecorated generator must raise when it accesses request-bound proxies after the request context has ended.

### WebSockets

Within an active WebSocket handler, `websocket` must expose headers and awaitable `accept`, `close`, `receive`, `send`, `receive_json`, and `send_json` methods. `receive` must accept the connection and return `str` for a text frame and `bytes` for a binary frame. `send` must accept the connection and transmit the supplied text or bytes. `send_json` must raise `TypeError` when positional and keyword JSON arguments are mixed. JSON decoding must raise for invalid JSON rather than returning a substituted value. Closing an unaccepted WebSocket must result in an HTTP 403 rejection.

`client.websocket(path, **kwargs)` must return an async context manager for a WebSocket test connection. Its `send`, `receive`, `send_json`, and `receive_json` methods must mirror the corresponding WebSocket message behavior. When a WebSocket handler returns an HTTP response instead of accepting the connection, the test connection must raise `quart.testing.WebsocketResponseError`; its `response` must expose the rejection status and body. When a WebSocket handler calls `abort(status)` before accepting the connection, the WebSocket client connection must raise `WebsocketResponseError`, whose public `response.status_code` must return `status`. Closing or disconnecting a test connection must end the peer operation rather than leave it waiting indefinitely.

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

## Cross-View Invariants

1. A handler registered through `app.route` must return the same observable body, status, and headers through `app.test_client()` as the handler's response value specifies.
2. A handler registered through a blueprint must be reachable through the application after `app.register_blueprint`, and `url_for` must return its registered URL.
3. A value placed in `session` by an HTTP handler must be visible to a later HTTP handler when both requests use the same cookie-preserving client and persistent sessions are configured.
4. `current_app` must return the application owning the active request, WebSocket, or explicit app context.
5. A template rendered during a request must return the same current `request`, `session`, `g`, and configuration values that the handler observes through the corresponding proxies.
6. A text or binary value sent through a test WebSocket connection must return from the server's `websocket.receive` with its original text-or-bytes kind.
7. A JSON value sent through a test WebSocket connection must return from `receive_json` as the decoded JSON value when the peer sends valid JSON.
8. A context-preserving stream must return request-bound values while it is iterated from the request that created it.

## Representative Workflow

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

## Non-Goals

This specification does not define production-server deployment, ASGI message internals, HTTP/2 push details, static-file cache policy, logging format, signal delivery order, private context structures, exact header ordering, exact exception text, or internal routing and template-loader implementation.

## Evaluation Notes

Evaluation exercises imports, application registration and dispatch, response conversion, routing and URL generation, client requests, contexts, sessions, templates, and WebSocket client behavior. Each checked behavior is scored from its public result, such as responses, generated URLs, context-proxy availability, and exchanged messages. The evaluation does not require a particular internal data structure, helper name, representation format, or framework implementation.
