# Gunicorn Specification

## Product Overview

Gunicorn is a UNIX application server for Python web applications. It accepts WSGI applications with its standard workers and ASGI applications with the `asgi` worker, binds one or more network or UNIX sockets, and supervises worker processes from a master process. Configuration is available through Python files, environment-provided command arguments, direct command-line arguments, and an embedding API. Optional public facilities provide HTTP/2, the nginx uWSGI protocol, runtime control, instrumentation, and a separate Dirty worker pool for persistent heavy resources.

## Scope

This contract covers:

- launching and resolving WSGI or ASGI application callables;
- resolved configuration, its precedence, principal settings, hooks, and validation modes;
- observable request, response, proxy-header, protocol, and lifecycle behavior;
- signal and control-socket management of a running server;
- the documented Python embedding and logger extension points;
- Dirty applications, clients, streaming execution, worker allocation, and stash tables;
- optional HTTP/2 capability reporting and user-facing protocol selection.

## Installable Surface

Installation provides the `gunicorn` package, the `gunicorn` and `gunicornc` commands, and `python -m gunicorn`. `python -m gunicorn.app.wsgiapp` provides the same WSGI application runner.

The supported Python imports are:

```python
from gunicorn import __version__, version_info
from gunicorn.app.base import BaseApplication
from gunicorn.app.wsgiapp import WSGIApplication, run
from gunicorn.config import Config, KNOWN_SETTINGS
from gunicorn.errors import ConfigError, AppImportError
from gunicorn.glogging import Logger, CONFIG_DEFAULTS
from gunicorn.debug import spew, unspew

from gunicorn.ctl import ControlClient
from gunicorn.ctl.client import ControlClientError

from gunicorn.dirty import (
    DirtyApp, DirtyClient, get_dirty_client, get_dirty_client_async,
    close_dirty_client, close_dirty_client_async, stash,
    StashClient, StashTable, StashError, StashTableNotFoundError,
    StashKeyNotFoundError, DirtyError, DirtyTimeoutError,
    DirtyConnectionError, DirtyWorkerError, DirtyAppError,
    DirtyAppNotFoundError, DirtyProtocolError,
)
from gunicorn.dirty.errors import DirtyNoWorkersAvailableError

from gunicorn.http2 import is_http2_available, get_h2_version, H2_MIN_VERSION
```

`gunicorn.http`, `gunicorn.uwsgi`, `gunicorn.asgi`, connection classes under `gunicorn.http2`, `gunicorn.ctl.ControlSocketServer`, `gunicorn.ctl.ControlProtocol`, and `gunicorn.dirty.DirtyArbiter` are server-core surfaces rather than application extension contracts.

## Product State Model

Gunicorn exposes one running product state through five public projections:

1. **Resolved configuration:** the effective values reported by `--print-config`, exposed through an embedded application's `cfg`, and reported by `show config`.
2. **Loaded application:** the callable selected by the application target and worker class, including its WSGI or ASGI protocol projection.
3. **Request/response projection:** the WSGI environment or ASGI scope/events produced from accepted HTTP, HTTP/2, or uWSGI traffic.
4. **Runtime projection:** listeners, master and worker population, lifecycle state, logs, metrics, signals, and control commands.
5. **Dirty projection:** configured Dirty applications, their allocated workers and persistent per-worker instances, execution results, and arbiter-owned stash tables.

The projections obey these state rules:

- A value selected in resolved configuration must govern the corresponding listener, worker, protocol, logging, control, and Dirty runtime behavior.
- A successfully loaded application must be the callable receiving every request assigned to its worker until a reload or worker replacement changes that worker's application state.
- A graceful reload must replace workers while listeners remain serviceable, and the new workers must reflect the newly resolved configuration.
- A control operation that changes a worker target must be reflected by subsequent control status and by the runtime worker population.
- A stash write acknowledged through one client must be returned through every stash client connected to the same running arbiter until the key, table, or arbiter state is removed.

Invalid configuration or application loading must prevent a normal serving state. A runtime operation that cannot be completed must report an error instead of reporting a successful state transition.

## Public API

### Application targets and runners

`gunicorn [OPTIONS] [APP_MODULE]` and `WSGIApplication` accept `module`, `module:callable`, or `module:factory(literal_args...)`. An omitted object name resolves to `application`. Factory references must use a simple name and Python literal positional or keyword arguments; the factory result must be callable. A missing module propagates its import failure. A malformed expression, missing attribute, invalid factory argument list, `None` result, or non-callable result raises `AppImportError`. Omitting both the command target and the `wsgi_app` setting raises `ConfigError`.

`BaseApplication(usage=None, prog=None)` is the embedding extension point. A subclass must provide configuration loading and `load()` returning a callable; `wsgi()` returns the cached loaded callable after the first successful load. Invalid setup exits unsuccessfully and writes the configuration or loading error to standard error. Embedded option dictionaries must ignore unknown setting names and apply known names through Gunicorn's setting validation.

`__version__` returns the dotted release string and `version_info` returns its integer tuple.

### Configuration objects and logging

`Config` exposes known settings as attributes and through `settings`; setting a known value must apply that setting's validator, while an unknown setting name raises an error. `KNOWN_SETTINGS` identifies the settings represented in the generated settings reference.

`Logger` is the configurable logging base. A replacement selected by `logger_class` must provide the same setup, error logging, access logging, reopen, and close behavior expected by the server. `CONFIG_DEFAULTS` returns the default dictionary usable as a base for `logconfig_dict`. An invalid logging configuration must fail startup rather than silently reverting to unrelated defaults.

`spew(trace_names=None, show_values=False)` installs detailed line tracing on the current interpreter; `unspew()` removes that trace. The `spew` server setting must install tracing when true.

### Control client

`ControlClient(socket_path: str, timeout: float = 30.0)` connects to a Gunicorn control UNIX socket. `send_command(command: str, args: list | None = None) -> dict` connects on demand, returns the response data for a successful command, and raises `ControlClientError` for connection, communication, or server-reported command failure. The context manager must connect on entry and close on exit; `close()` must permit a later command to reconnect.

### HTTP/2 capability queries

`is_http2_available() -> bool` returns true only when the optional `h2` package is importable at or above `H2_MIN_VERSION`. `get_h2_version()` returns the installed `(major, minor, patch)` tuple after capability detection, or `None` when `h2` is absent.

## Configuration Semantics

### Sources and precedence

Gunicorn must resolve recognized settings in this increasing order of precedence:

1. setting-specific environment values;
2. framework-provided values from Paste Deploy;
3. the Python configuration file, defaulting to `./gunicorn.conf.py` when present;
4. options in `GUNICORN_CMD_ARGS`;
5. direct command-line options.

When both `GUNICORN_CMD_ARGS` and direct CLI arguments name a configuration file, Gunicorn must load only the file named directly on the CLI. Unknown names in a Python configuration file must be ignored. Invalid values for known names must fail configuration. A missing explicitly selected file must fail; absence of the implicit default file must not fail.

`--print-config` must print fully resolved values, validate application loading, and exit without serving. `--check-config` must validate configuration and application loading and exit zero on success; either mode must exit nonzero when configuration or application loading fails. `--print-config` implies check mode.

### Principal settings

The following defaults and interactions are part of the public contract:

| Setting | Default | Required behavior and failure |
|---|---:|---|
| `bind` | `127.0.0.1:8000` | Each value must create a TCP, IPv6, or `unix:PATH` listener; an invalid or unavailable address must fail binding. |
| `workers` | `1` | The master must maintain this target; negative values must fail validation. |
| `worker_class` | `sync` | `asgi`, `gthread`, `gevent`, and documented import paths must select their worker behavior; an unknown or unavailable class must fail startup. |
| `threads` | `1` | A sync worker with more than one thread must use threaded behavior; ASGI workers must ignore this setting in favor of `worker_connections`. |
| `worker_connections` | `1000` | Async-capable workers must use it as their per-worker simultaneous-client limit. |
| `timeout` | `30` | A worker silent beyond the value must be terminated and replaced; `0` disables this timeout. |
| `graceful_timeout` | `30` | Restarting workers must receive this long to finish before forced termination. |
| `keepalive` | `2` | Workers that support persistent connections must wait this many seconds; the sync worker must not retain keep-alive connections. |
| `max_requests` | `0` | A positive value must restart a worker after that many requests; `0` disables request-count recycling. |
| `max_requests_jitter` | `0` | A positive value must add a per-worker random amount from zero through this value to the restart threshold. |
| `preload_app` | `False` | True must load application code before workers are forked; on `HUP`, application code reloads only when preloading is false. |
| `reload` | `False` | True must restart workers after watched source changes; application preloading must prevent worker reload from re-importing changed application code. |
| `accesslog` | `None` | `-` must write access logs to stdout; `None` must disable access logging. |
| `errorlog` | `-` | `-` must write error logs to stderr. |
| `capture_output` | `False` | True must redirect application stdout and stderr to the configured error log. |
| `forwarded_allow_ips` | `127.0.0.1,::1` | Forwarded scheme and client-certificate headers must affect WSGI/ASGI state only for trusted peer addresses; `*` trusts every peer. |
| `proxy_protocol` | `off` | Enabled modes must accept PROXY metadata only from `proxy_allow_ips`; an untrusted sender must be rejected. |
| `protocol` | `http` | `uwsgi` must select nginx uWSGI traffic handling; other string values remain configuration values and may fail only when the selected runtime cannot serve them. |
| `control_socket_disable` | `False` | False must create the configured UNIX control socket with `control_socket_mode`; true, including through `--no-control-socket`, must create no control socket. |

Hook settings must invoke the configured callable at their documented lifecycle point. A hook with an invalid callable arity must fail configuration. Exceptions raised by startup hooks must prevent the affected startup transition; exceptions in request or exit hooks must be logged and must not be reported as successful hook execution.

## Request and Protocol Semantics

For WSGI workers, Gunicorn must call the selected application with a WSGI environment and `start_response`, transmit the returned byte chunks in order, and close a returned iterable that defines `close()`. An application loading or invocation failure must produce an error response when response transmission has not begun and must be logged.

For the `asgi` worker, Gunicorn must call the selected ASGI callable with `scope`, `receive`, and `send`. HTTP scopes must carry method, path, query string, headers, scheme, client/server addresses, and configured `root_path`. Request body events must preserve byte order and terminate with `more_body=False`. Response start must precede ordinary response body events; invalid event ordering or invalid event types must fail that request. WebSocket upgrade traffic must use a `websocket` scope under HTTP proxying. The uWSGI protocol must not provide WebSocket transport.

`asgi_loop` accepts `auto`, `asyncio`, or `uvloop`; `auto` must prefer uvloop when installed and otherwise use asyncio, while explicit `uvloop` must fail when unavailable. `asgi_lifespan` accepts `auto`, `on`, or `off`; `on` must fail worker startup when the app rejects lifespan, `off` must send no lifespan events, and `auto` must continue without lifespan only when the application reports that protocol as unsupported. Startup must complete before serving requests, and shutdown must be offered before worker exit when lifespan is active.

HTTP request-line and header limits must reject requests that exceed `limit_request_line`, `limit_request_fields`, or `limit_request_field_size`. The strict defaults must reject obsolete header folding, spaces before a header colon, unconventional methods, and unconventional HTTP versions unless their corresponding permit settings are enabled. `header_map=drop` must discard ambiguous underscore-bearing headers; stricter configured behavior must reject them rather than expose a conflicting WSGI key.

Forwarded scheme headers must change the application-visible scheme only when the immediate peer is trusted and the header/value pair matches `secure_scheme_headers`. Forwarded `SCRIPT_NAME` and `PATH_INFO` values must be copied only from trusted peers and only when named by `forwarder_headers`. Conflicting secure-scheme headers must reject the request instead of choosing one silently.

With `protocol=uwsgi`, TCP requests must be accepted only from `uwsgi_allow_ips`; UNIX-socket requests must be accepted regardless of that IP list. Malformed, forbidden, or unsupported uWSGI input must be rejected without invoking the application.

HTTP/2 must require TLS ALPN, an available compatible `h2` package, and a compatible worker. `http_protocols` order must be the ALPN preference order. An incompatible worker must warn and fall back to HTTP/1.1 when that fallback is configured. Configured stream, flow-window, frame, and header-list limits must constrain each HTTP/2 connection. Multiplexed streams must remain isolated while sharing the connection.

The WSGI environment for HTTP/2 must expose request data through normal WSGI keys and must expose `gunicorn.http2.priority_weight`, `gunicorn.http2.priority_depends_on`, and `gunicorn.http2.send_trailers` when those features apply. WSGI applications must send early hints through `wsgi.early_hints` when present. ASGI applications must use `http.response.informational` with status `103`; malformed informational or trailer messages must fail the affected stream.

## Runtime and Control Semantics

The master must bind listeners before workers serve and must maintain the configured worker target. Unexpected worker exit must trigger replacement while the master remains healthy. Worker timeout must terminate and replace the silent worker.

Master signals have these public effects:

| Signal | Effect |
|---|---|
| `QUIT`, `INT` | Quick shutdown. |
| `TERM` | Graceful shutdown up to `graceful_timeout`. |
| `HUP` | Reload configuration, start replacement workers, then gracefully stop old workers. |
| `TTIN`, `TTOU` | Increase or decrease the worker target by one. |
| `USR1` | Reopen log files. |
| `USR2` | Start a new master for binary upgrade while the old master remains available. |
| `WINCH` | Gracefully stop workers when daemonized. |

`gunicornc` must use the configured UNIX socket. With `-c`, it must execute one command and exit; without `-c`, it must enter interactive mode. `-j` must emit machine-readable JSON. A missing socket, denied connection, unknown command, invalid argument, or server-side failure must produce a nonzero command result.

`show all`, `show workers`, `show dirty`, `show config`, `show stats`, and `show listeners` must report their corresponding current runtime projection. `worker add [N]` and `worker remove [N]` must adjust the target by `N`, defaulting to one. `worker kill PID` must gracefully terminate that worker or return an error for an unknown PID. `dirty add [N]` and `dirty remove [N]` must adjust Dirty workers subject to per-app limits. `reload`, `reopen`, and `shutdown graceful|quick` must have the same externally visible effects as `HUP`, `USR1`, and `TERM|INT` respectively.

Metrics enabled through StatsD must use the `gunicorn` namespace plus the configured prefix. The public metric projection includes request count, request duration in milliseconds, worker gauge, log severity counts, and the optional socket backlog metric. A missing or unreachable metrics sink must not change request results.

## Dirty Applications and Shared State

### Application lifecycle and allocation

`DirtyApp` instances persist for a Dirty worker's lifetime. Each selected class must be instantiated once per assigned worker, then `init()` must run once before that worker accepts Dirty calls, `__call__(action, *args, **kwargs)` must dispatch public action names, and `close()` must run during orderly worker shutdown. The default dispatcher must reject missing and underscore-prefixed actions with `ValueError`.

`dirty_apps` entries use `module:Class` or `module:Class:N`. `N` must be an integer of at least one. The explicit `:N` limit must override the class `workers` attribute; without either limit, every Dirty worker must load the app. Requests must route only to workers that loaded the requested app. No eligible live worker raises `DirtyNoWorkersAvailableError`; an unknown configured app raises `DirtyAppNotFoundError`. A replacement for a failed worker must receive the failed worker's app allocation.

With `dirty_threads=1`, one action at a time must execute in each Dirty worker. Higher values permit concurrent actions against the same persistent instance, so application state must remain shared across those actions. `dirty_timeout` must bound execution and raise `DirtyTimeoutError`; `dirty_graceful_timeout` must bound orderly Dirty worker shutdown.

### Clients and execution

`DirtyClient(socket_path, timeout=30.0)` provides:

```python
execute(app_path, action, *args, **kwargs)
execute_async(app_path, action, *args, **kwargs)
stream(app_path, action, *args, **kwargs)
stream_async(app_path, action, *args, **kwargs)
close()
close_async()
```

`execute` and `execute_async` return the action result. A sync or async generator result must be consumed through the matching streaming method, which returns chunks in production order and terminates normally only after the remote stream ends. A remote stream error must raise the corresponding Dirty exception during iteration.

`get_dirty_client(timeout=30.0)` must return the same live client within a thread; `get_dirty_client_async(timeout=30.0)` must return the same live client within an async context. `close_dirty_client()` must close and clear the thread-local client so the next sync getter returns a new client. `close_dirty_client_async()` must close the current async client's connection; subsequent operations in the same async context must reconnect as needed. If no socket path is configured through the running server or `GUNICORN_DIRTY_SOCKET`, getters raise `DirtyError`.

Connection failure raises `DirtyConnectionError`, expiration raises `DirtyTimeoutError`, an application exception raises `DirtyAppError`, worker failure raises `DirtyWorkerError`, and malformed communication raises `DirtyProtocolError`. Dirty exceptions must preserve their public diagnostic details, including app path, action, worker identifier, timeout, socket path, or remote traceback when supplied.

### Stash tables

The `stash` namespace and `StashClient(socket_path, timeout=30.0)` provide `put`, `get`, `delete`, `keys`, `clear`, `info`, `ensure`, `exists`, `delete_table`, `tables`, and `table`. `put` must create a missing table. `get(table, key, default=None)` returns the stored value, including a stored `None`, or the provided default for a missing key. `delete` returns true only when a key was removed. `ensure` must be idempotent. `keys(table, pattern)` must apply glob matching when a pattern is supplied. Missing tables for strict table operations raise `StashTableNotFoundError`; communication failures raise `StashError`.

`table(name) -> StashTable` returns a mapping projection. Index lookup returns a stored value and raises `KeyError` for a missing key; indexed deletion raises `KeyError` when nothing was removed. Iteration returns keys, `len()` returns table size, and `items()` and `values()` reflect current entries. Module functions and mapping operations must observe the same table state.

Stash state belongs to one running arbiter. It must be visible across that arbiter's web and Dirty workers, must support serializable values including bytes, and must be lost on arbiter restart. It provides no persistence, TTL, distributed replication, transaction, or atomic read-modify-write guarantee.

## Error Semantics

| Error | Required trigger |
|---|---|
| `ConfigError` | Missing application target or invalid high-level configuration selection. |
| `AppImportError` | Invalid target expression, missing target attribute, invalid literal factory call, null result, or non-callable result. |
| `ControlClientError` | Control socket connection/communication failure or an error response. |
| `DirtyError` | Dirty setup failure not represented by a more specific subclass. |
| `DirtyConnectionError` | Dirty socket connection failure. |
| `DirtyTimeoutError` | Dirty operation exceeds its timeout. |
| `DirtyWorkerError` | Selected Dirty worker fails while handling a call. |
| `DirtyAppError` | Dirty app loading or action execution fails. |
| `DirtyAppNotFoundError` | Requested app path is not loaded/configured. |
| `DirtyNoWorkersAvailableError` | The app is known but no eligible live worker is available. |
| `DirtyProtocolError` | Dirty response framing or content is invalid. |
| `StashTableNotFoundError` | A strict operation targets an absent table. |
| `StashKeyNotFoundError` | A strict stash operation targets an absent key; default-returning `get` and mapping lookup translate this as specified above. |
| `StashError` | Other stash connection, communication, or operation failure. |

Startup errors must produce a nonzero exit and must not leave a server claiming readiness. Per-request protocol or application errors must be isolated to the affected request or stream when the underlying connection remains valid. Master-fatal listener or configuration errors must terminate startup.

## Cross-View Invariants

1. `--print-config`, embedded `cfg`, and `show config` must report the same resolved setting values for one running generation.
2. The resolved `bind` values must correspond to `show listeners` and to the sockets accepting application traffic.
3. The resolved worker target must correspond to control statistics and must be restored after an unexpected worker exit.
4. A CLI override must govern both the loaded application environment and runtime behavior even when lower-priority sources specify conflicting values.
5. A successful `HUP` or control `reload` must preserve listener availability while replacing workers with the reloaded configuration and application state.
6. `TTIN`/`TTOU` and control worker add/remove must update the same worker target and subsequent status projection.
7. A trusted proxy scheme must appear consistently in the WSGI `wsgi.url_scheme`, ASGI `scope['scheme']`, and access-log request projection; an untrusted proxy header must affect none of them.
8. The application callable selected by the target must receive equivalent method, path, query, header, body, client, and server information across supported HTTP/1.1, HTTP/2, and uWSGI transports, except for protocol-specific extensions explicitly documented here.
9. A Dirty app listed by `show dirty` for a live worker must accept routed calls on that worker; an app absent from every live allocation must return the documented unavailability failure.
10. A Dirty action result must be identical through sync and async clients for the same app state and arguments; streaming clients must preserve the same chunk order.
11. A stash mutation acknowledged through module functions, `StashClient`, or `StashTable` must be visible through the other two projections under the same arbiter.
12. Closing a client must release its connection without deleting Dirty application state or stash state; reconnecting must observe the surviving server state.

## Representative Workflows

### Configured WSGI server with runtime inspection

Create `myapp.py`:

```python
def app(environ, start_response):
    body = b"ok\n"
    start_response("200 OK", [
        ("Content-Type", "text/plain"),
        ("Content-Length", str(len(body))),
    ])
    return [body]
```

Create `gunicorn.conf.py`:

```python
bind = "127.0.0.1:8080"
workers = 2
accesslog = "-"
control_socket = "/tmp/myapp.ctl"
```

Run and inspect:

```bash
gunicorn --check-config myapp:app
gunicorn myapp:app
gunicornc -s /tmp/myapp.ctl -c "show config" -j
gunicornc -s /tmp/myapp.ctl -c "worker add 1" -j
gunicornc -s /tmp/myapp.ctl -c "show workers" -j
```

The check command must validate and exit without serving. The running server must bind port 8080, initially maintain two workers, return the WSGI response, expose the resolved configuration, then report a target and population increased by one after the control command. A missing callable or invalid setting must stop the workflow at validation with a nonzero exit.

### Persistent Dirty application and shared stash

```python
from gunicorn.dirty import DirtyApp, get_dirty_client, stash

class CounterApp(DirtyApp):
    stashes = ["results"]

    def init(self):
        self.calls = 0

    def calculate(self, value):
        self.calls += 1
        result = {"value": value * 2, "calls": self.calls}
        stash.put("results", str(value), result)
        return result
```

With `dirty_apps = ["tasks:CounterApp:1"]` and `dirty_workers = 2`, only one Dirty worker must load this app. Repeated `get_dirty_client().execute("tasks:CounterApp", "calculate", 5)` calls must observe persistent `calls` state, and `stash.table("results")["5"]` must return the acknowledged result from any worker connected to the same arbiter. If the allocated worker is unavailable, execution must raise `DirtyNoWorkersAvailableError` rather than route to a worker without the app.

## Non-Goals

- This contract does not prescribe parser, arbiter, worker, socket, IPC framing, or scheduler implementation structure.
- It does not restate the full WSGI, ASGI, HTTP/1.1, HTTP/2, TLS, WebSocket, StatsD, or uWSGI standards.
- It does not guarantee support on non-UNIX operating systems.
- It does not guarantee behavior of third-party worker classes beyond Gunicorn's loading and lifecycle contract.
- It does not define framework-specific deployment files, reverse-proxy configuration, exact process IDs, timing, or resource consumption.
- Beta HTTP/2 and Dirty facilities retain their documented compatibility status; only behavior stated in this specification is contractual here.

## Compatibility Guarantees

A conforming implementation must preserve the documented behavior visible through Python imports, command invocations, embedded applications, network-facing WSGI and ASGI service behavior, configuration conflicts, runtime control, and Dirty/stash workflows. Compatibility includes successful paths, validation boundaries, failure types, precedence, lifecycle transitions, and consistency among public projections.

Protocol-standard behavior is part of the contract only through application-visible request and response effects, not through private parser or worker object shapes. Platform-specific behavior is required only where the documented UNIX facilities and optional dependencies are available. Implementations may choose different internal architecture when the public imports, signatures, side effects, errors, and cross-view invariants above remain observable.
