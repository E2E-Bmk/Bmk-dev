# Hypercorn

## Product Overview

Hypercorn is an ASGI and WSGI application server. It serves HTTP/1.1, HTTP/2, and WebSocket applications with asyncio, uvloop, or Trio workers, and it supports optional HTTP/3 service when the HTTP/3 extra is installed. Applications are launched from the `hypercorn` command or served inside an existing asyncio or Trio event loop.

Hypercorn uses one configuration model across command-line and programmatic operation. The same model controls application loading, network binds, TLS, worker behavior, protocol limits, logging, and graceful shutdown. The included middleware adapts WSGI applications, dispatches requests among ASGI applications, redirects insecure traffic, and restores client information supplied by trusted proxies.

## Scope

This document covers:

- the `hypercorn` command and application-path syntax;
- the `Config` object, documented configuration sources, defaults, normalization, and precedence;
- programmatic service with asyncio and Trio;
- the middleware exported by `hypercorn.middleware`;
- application dispatch, proxy correction, HTTPS redirects, and WSGI adaptation;
- observable startup, shutdown, request-routing, response-header, and logging behavior.

The ASGI and WSGI specifications remain the authority for application call signatures and message schemas. Hypercorn-specific behavior at those boundaries is defined below.

## Product State Model

A running service has three public projections of one state:

1. **Configuration projection.** A `Config` instance contains the effective application path, bind groups, TLS settings, worker policy, protocol limits, log destinations, and lifecycle timeouts. A configuration file supplies the initial values and explicitly supplied command-line options replace the corresponding values.
2. **Application projection.** Hypercorn loads or receives an ASGI or WSGI application, optionally wraps it in middleware, and exposes request, WebSocket, and lifespan events according to the selected mode and worker backend.
3. **Service projection.** Bound endpoints, response headers, status codes, access records, metrics, and graceful-shutdown completion are observable consequences of the effective configuration and application behavior.

Changing a `Config` attribute before service startup changes both the application and service projections that depend on it. Configuration is consumed when service starts; command-line parsing and programmatic `serve()` do not create separate configuration dialects.

## Installable Surface

Hypercorn installs the `hypercorn` command and the following Python interfaces:

```python
from hypercorn import Config
from hypercorn.config import Config
from hypercorn.asyncio import serve as asyncio_serve
from hypercorn.trio import serve as trio_serve
from hypercorn.logging import Logger
from hypercorn.middleware import (
    AsyncioWSGIMiddleware,
    DispatcherMiddleware,
    HTTPToHTTPSRedirectMiddleware,
    ProxyFixMiddleware,
    TrioWSGIMiddleware,
)
```

`Config` imported from `hypercorn` and `hypercorn.config` is the same public configuration class.

## Configuration

### Creating and Loading Configuration

```python
class Config:
    @classmethod
    def from_mapping(cls, mapping=None, **kwargs) -> "Config": ...

    @classmethod
    def from_toml(cls, filename) -> "Config": ...

    @classmethod
    def from_pyfile(cls, filename) -> "Config": ...

    @classmethod
    def from_object(cls, instance) -> "Config": ...

    def set_statsd_logger_class(self, statsd_logger: type[Logger]) -> None: ...
```

- `Config()` returns a mutable configuration with the defaults listed below.
- `from_mapping()` applies entries from `mapping`, then applies keyword arguments. A keyword argument must therefore win when both sources contain the same name.
- `from_toml()` reads top-level TOML keys and applies them as configuration attributes. An unreadable or malformed file must propagate the corresponding file or TOML parsing exception.
- `from_pyfile()` executes the named Python file and applies its configuration attributes. Import and execution failures must propagate to the caller.
- `from_object()` accepts an object or a dotted import string. A dotted string names either a module or an object inside a module. Import and attribute lookup failures must propagate when the requested object cannot be resolved.
- `bind`, `insecure_bind`, and `quic_bind` accept either one string or a list of strings. Assigning one string must expose a one-element list when the attribute is read.
- Assigning `root_path` must remove trailing `/` characters; assigning `"/api/"` must therefore return `"/api"` when read.

### Documented Defaults

The following values are part of the default configuration:

| Attribute | Default |
|---|---|
| `access_log_format` | `%(h)s %(l)s %(l)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"` |
| `accesslog` | `None` |
| `alpn_protocols` | `["h2", "http/1.1"]` |
| `backlog` | `100` |
| `bind` | `["127.0.0.1:8000"]` |
| `ciphers` | `"ECDHE+AESGCM"` |
| `debug` | `False` |
| `errorlog` | `"-"` |
| `graceful_timeout` | `3` seconds |
| `h11_max_incomplete_size` | `16384` bytes |
| `h11_pass_raw_headers` | `False` |
| `h2_max_concurrent_streams` | `100` |
| `h2_max_header_list_size` | `65536` bytes |
| `h2_max_inbound_frame_size` | `16384` bytes |
| `include_date_header` | `True` |
| `include_server_header` | `True` |
| `insecure_bind` | `[]` |
| `keep_alive_max_requests` | `1000` |
| `keep_alive_timeout` | `5` seconds |
| `loglevel` | `"INFO"` |
| `max_app_queue_size` | `10` |
| `max_requests` | `None` |
| `max_requests_jitter` | `0` |
| `quic_bind` | `[]` |
| `read_timeout` | `None` |
| `root_path` | `""` |
| `server_names` | `[]` |
| `shutdown_timeout` | `60` seconds |
| `ssl_handshake_timeout` | `60` seconds |
| `startup_timeout` | `60` seconds |
| `statsd_prefix` | `""` |
| `use_reloader` | `False` |
| `websocket_max_message_size` | `16777216` bytes |
| `websocket_ping_interval` | `None` |
| `worker_class` | `"asyncio"` |
| `workers` | `1` |
| `wsgi_max_body_size` | `16777216` bytes |

Certificate paths, key passwords, logging configuration, PID path, StatsD host, user, group, umask, verification settings, and optional Alt-Svc values default to no configured value unless listed otherwise.

### Binds and TLS

- TCP binds accept `host:port`, `host`, and bracketed IPv6 forms. Omitting the port selects port `8000`.
- Unix-domain binds use `unix:/path/to/socket`. `umask`, `user`, and `group` control a created Unix socket when configured.
- Existing file descriptors use `fd://<number>` and must refer to the required socket type; a mismatched socket type must fail rather than being silently repurposed.
- Repeated bind values represent simultaneous listeners. `bind` is the normal listener group, `insecure_bind` remains plaintext when TLS is enabled, and `quic_bind` is the UDP listener group used for HTTP/3.
- TLS is enabled only when both `certfile` and `keyfile` are non-`None`. `ssl_enabled` returns that condition.
- `create_ssl_context()` returns `None` when TLS is not enabled. When enabled, it returns a server context using the configured certificate, key, key password, CA certificates, cipher string, ALPN protocols, verification mode, and verification flags; the minimum TLS version is TLS 1.2 and compression is disabled.
- `server_names` restricts accepted Host values. When the list is non-empty, an HTTP request whose Host value is absent from the list must receive a 404 response. An empty list accepts any Host value.

### Response Metadata and Metrics

- `response_headers(protocol)` returns byte-pair headers for service-generated metadata. It must include `date` when `include_date_header` is true and `server: hypercorn-<protocol>` when `include_server_header` is true.
- Every value in `alt_svc_headers` must appear as a separate `alt-svc` response header. Configured values take precedence over automatically derived HTTP/3 Alt-Svc values.
- Setting `statsd_host` enables StatsD output. `statsd_prefix` prefixes metric names and `dogstatsd_tags` supplies DogStatsD tags.
- `set_statsd_logger_class()` selects the supplied class only when `statsd_host` is configured and `logger_class` is still Hypercorn's default `Logger`. An explicitly customized `logger_class` must not be replaced.
- StatsD output covers request count, request duration, response-status count, and critical, error, warning, and exception log counts.

## Command-Line Service

```console
hypercorn [OPTIONS] MODULE_APP
```

`MODULE_APP` normally has the form `package.module:application`. A module without `:application` uses the name `app`. Prefixing the value with `asgi:` or `wsgi:` forces the corresponding application mode. A missing module or named application must terminate startup with a non-success result.

`-c` or `--config` chooses the initial configuration source:

- an unprefixed path is a TOML file;
- `file:<path>` is a Python file;
- `python:<dotted.name>` is a Python module or object.

Explicit command-line values must override values loaded from that source. Values not supplied on the command line must remain unchanged. The positional application always becomes `application_path`. Repeated `--bind`, `--insecure-bind`, `--quic-bind`, and `--server-name` options preserve their command-line order and, when present, replace the corresponding configured list.

The command exposes the documented configuration controls, including access and error log destinations, backlog, certificate and key files, ciphers, debug mode, graceful and read timeouts, worker class and count, keep-alive timeout, logging configuration and level, maximum requests and jitter, PID path, reload mode, root path, StatsD destination and prefix, Unix-socket ownership and mask, TLS verification mode, and WebSocket ping interval. `--verify-mode` accepts names from Python's `ssl.VerifyMode`; an unknown name is an invocation error.

`--access-logfile -` writes access records to stdout. `--error-logfile -` writes error records to stderr. Other non-`None` values are paths. The older `--access-log` and `--error-log` forms remain accepted but emit deprecation warnings.

## Programmatic Service

### asyncio

```python
async def hypercorn.asyncio.serve(
    app,
    config: Config,
    *,
    shutdown_trigger=None,
    mode: Literal["asgi", "wsgi"] | None = None,
) -> None: ...
```

### Trio

```python
async def hypercorn.trio.serve(
    app,
    config: Config,
    *,
    shutdown_trigger=None,
    task_status=trio.TASK_STATUS_IGNORED,
    mode: Literal["asgi", "wsgi"] | None = None,
) -> None: ...
```

- `serve()` runs inside the caller's existing event-loop environment. It must not configure a new loop or create a separate worker process.
- `mode="asgi"` and `mode="wsgi"` force application adaptation. With `mode=None`, Hypercorn selects the mode from whether the application callable is asynchronous.
- When `shutdown_trigger` is provided, Hypercorn awaits the awaitable returned by that callable. Its completion initiates graceful shutdown and waits for normal lifespan shutdown up to the configured timeout.
- `worker_class` and `workers` are process-launch settings and do not alter programmatic service. A `workers` value other than `1` must emit a warning. Enabling `debug` through `Config` must likewise emit a warning because loop-level debug setup is controlled by the caller.
- Trio service must report its bound endpoint descriptions through a supplied `task_status` when startup completes.
- Startup or shutdown lifespan timeouts and explicit lifespan failure messages must fail service rather than report successful lifecycle completion.

## Middleware

### Dispatching Applications

```python
DispatcherMiddleware(mounts: dict[str, ASGI_application])
```

Mount keys are root paths without trailing slashes. For each HTTP or WebSocket scope, `DispatcherMiddleware` selects the first insertion-ordered key for which `scope["path"].startswith(key)` is true. More-specific paths must therefore be inserted before less-specific paths.

The selected application receives a copied scope whose `root_path` is extended by the matched mount. The request `path` remains unchanged. If no mount matches, the middleware returns an empty 404 HTTP response. A lifespan request is broadcast to every mounted application; one startup or shutdown completion is sent upstream only after all mounted applications report that completion.

### Redirecting HTTP to HTTPS

```python
HTTPToHTTPSRedirectMiddleware(app, host: str | None)
```

- An HTTP scope with scheme `http` must receive status 307 and a `location` built from `https`, the redirect host, `root_path + raw_path`, and the original query string.
- A WebSocket scope with scheme `ws` and the `websocket.http.response` extension must receive a 307 denial response. The redirect scheme is `wss` for HTTP/1.x WebSockets and `https` for HTTP/2 WebSockets.
- A `ws` scope without that extension must receive `websocket.close` because a redirect response cannot be represented.
- Scopes already using secure schemes and non-HTTP/WebSocket scopes must be passed to the wrapped application unchanged.
- A non-`None` constructor `host` is authoritative. When it is `None`, the middleware uses the request Host header. If neither source provides a host, redirect construction raises `ValueError`.
- The middleware preserves the encoded `raw_path` and query string in the redirect target rather than decoding and re-encoding them.

### Restoring Proxy Information

```python
ProxyFixMiddleware(
    app,
    mode: Literal["legacy", "modern"] = "legacy",
    trusted_hops: int = 1,
)
```

For HTTP and WebSocket scopes, the middleware passes a copied scope to the application and leaves the caller's original scope unchanged.

- In `legacy` mode it reads `X-Forwarded-For`, `X-Forwarded-Proto`, and `X-Forwarded-Host`.
- In `modern` mode it reads the `for`, `proto`, and `host` parameters from `Forwarded`. If no trusted `Forwarded` value is available, legacy headers are used.
- Comma-separated proxy values are ordered from the original client toward the proxy nearest Hypercorn. The trusted value is the item `trusted_hops` positions from the right. If fewer values exist, that field must remain unchanged.
- A trusted client value replaces `scope["client"]` with `(value, 0)`. A trusted protocol replaces `scope["scheme"]`. A trusted host removes existing Host headers and appends one Host header with the trusted value.
- `trusted_hops=0` trusts no forwarded value. Lifespan and other non-HTTP scopes pass through without proxy-derived changes.

### Adapting WSGI Applications

```python
AsyncioWSGIMiddleware(wsgi_app, max_body_size: int = 65536)
TrioWSGIMiddleware(wsgi_app, max_body_size: int = 65536)
```

Each class exposes a WSGI application as an ASGI callable using the named concurrency backend. The standalone middleware default of 65536 bytes is independent from `Config.wsgi_max_body_size`, whose default applies when Hypercorn performs WSGI adaptation itself.

- HTTP request body chunks are collected into `wsgi.input` before invoking the WSGI application. If their combined size exceeds `max_body_size`, the middleware returns an empty 400 response and must not call the application.
- The WSGI environment reflects the ASGI method, root path, path, query string, server, client, protocol, scheme, headers, and body. `SCRIPT_NAME` is `root_path`; `PATH_INFO` is the remaining path. A path outside the root path returns an empty 404 response.
- `Content-Type` and `Content-Length` map to `CONTENT_TYPE` and `CONTENT_LENGTH`; other headers map to `HTTP_<UPPERCASE_NAME>`. Repeated values for one environment key are comma-joined.
- The first WSGI body item requires a prior `start_response` call. If the application yields body data without calling `start_response`, the middleware raises `RuntimeError`.
- Response header names are lowercased and encoded with Latin-1. Every yielded body item is emitted in order, and a response iterable with `close()` must be closed even when response iteration fails.
- WebSocket scopes receive `websocket.close`. Lifespan scopes complete without invoking the WSGI application.

## Logging

```python
class Logger:
    def __init__(self, config: Config) -> None: ...
    async def access(self, request, response, request_time: float) -> None: ...
    async def critical(self, message, *args, **kwargs) -> None: ...
    async def error(self, message, *args, **kwargs) -> None: ...
    async def warning(self, message, *args, **kwargs) -> None: ...
    async def info(self, message, *args, **kwargs) -> None: ...
    async def debug(self, message, *args, **kwargs) -> None: ...
    async def exception(self, message, *args, **kwargs) -> None: ...
```

`Config.logger_class` selects the logger implementation; `Logger` is the default. Access records use `Config.access_log_format`. Supported atoms include remote address (`h`), request line with or without query (`r`, `R`), method (`m`), path (`U`, `Uq`), query (`q`), protocol (`H`), status and phrase (`s`, `st`), scheme (`S`), response size (`B`, `b`), referer (`f`), user agent (`a`), durations (`T`, `D`, `L`), process ID (`p`), request and response headers (`{Header}i`, `{Header}o`), and environment variables (`{Variable}e`). A missing atom must render as `-` rather than fail access logging.

`logconfig_dict` is applied as a Python logging dictionary configuration. `logconfig` uses logging's file configuration by default; `json:` and `toml:` prefixes load dictionary configurations from the named file.

## Error Semantics

- An application path with an unsupported explicit mode, a missing module, or a missing application object must fail startup before binding service endpoints.
- A malformed command line or invalid typed option must terminate command processing with a non-success result.
- Configuration file read, parse, import, and execution errors must propagate; Hypercorn must not continue with silent defaults after an explicitly selected configuration fails.
- A TLS context request with TLS disabled returns `None`. Invalid certificate, key, CA, cipher, or verification inputs must propagate the relevant SSL or file error.
- A mismatched inherited socket type must fail socket creation.
- Missing redirect host information raises `ValueError` only when an insecure redirect is required; requests that are passed through do not require a redirect host.
- WSGI request bodies over the configured limit return 400, WSGI paths outside `root_path` return 404, and a WSGI application that yields before `start_response` raises `RuntimeError`.
- Lifespan startup or shutdown timeout and application-reported lifespan failure must be observable as service failure, not successful shutdown.

## Cross-View Invariants

1. A configuration loaded from a file and then overridden explicitly on the command line **must** produce the same effective value as assigning that final value to a `Config` instance before programmatic service.
2. A command-line bind repeated in a particular order **must** remain in that order in `Config.bind`, and service startup **must** attempt all effective binds rather than only the last value.
3. TLS-enabled `bind` endpoints **must** use the certificate and key represented by the effective configuration, while `insecure_bind` endpoints **must** remain plaintext under the same configuration.
4. The `root_path` visible to an ASGI application or mapped to WSGI `SCRIPT_NAME` **must** reflect the normalized effective `Config.root_path` plus any selected dispatcher mount.
5. A `server_names` rejection **must** produce a 404 before the application handles the request, while an accepted Host value **must** reach the configured application.
6. `include_date_header`, `include_server_header`, and Alt-Svc configuration **must** control the corresponding service-generated response headers in every supported HTTP protocol projection.
7. A middleware-generated redirect, rejection, or body-limit response **must** bypass the wrapped application; a pass-through scope **must** reach it exactly once.
8. Proxy-derived client, scheme, and Host values **must** be visible to the wrapped application together in one copied scope, while the original caller-owned scope **must** retain its original values.
9. Completion of `shutdown_trigger` **must** initiate the same graceful application shutdown sequence as normal server termination and **must** honor the effective graceful and lifespan timeout settings.
10. Access logging and StatsD metrics **must** describe the same completed request status and duration observed at the service boundary.

## Representative Workflows

### Programmatic asyncio Service

```python
import asyncio

from hypercorn.asyncio import serve
from hypercorn.config import Config

from myproject import app

config = Config.from_mapping(
    bind=["127.0.0.1:8080"],
    server_names=["localhost"],
    accesslog="-",
)
shutdown = asyncio.Event()

asyncio.run(serve(app, config, shutdown_trigger=shutdown.wait))
```

The caller owns the event loop. Returning from `shutdown.wait()` starts graceful shutdown; `serve()` returns after active service and application lifespan shutdown complete or raises if shutdown fails.

### Command-Line TLS Service

```console
hypercorn \
  --config service.toml \
  --bind 0.0.0.0:443 \
  --insecure-bind 0.0.0.0:80 \
  --certfile cert.pem \
  --keyfile key.pem \
  myproject.web:app
```

The explicit binds and certificate paths replace conflicting values from `service.toml`; non-conflicting file values remain active. Redirect middleware must be the outermost application wrapper when plaintext listeners are used only to redirect clients to HTTPS.

## Non-Goals

- This document does not redefine ASGI, WSGI, HTTP, TLS, WebSocket, or StatsD standards.
- Internal protocol engines, worker-context classes, queue implementations, task groups, socket syscall order, and reload-process organization are not public interfaces.
- Exact diagnostic wording, traceback formatting, logging timestamps, operating-system error text, and absolute paths are not compatibility guarantees.
- Optional HTTP/3 protocol internals and third-party event-loop installation are outside this surface; the documented HTTP/3 extra, QUIC bind, and Alt-Svc integration remain supported.
- Deprecated or undocumented internal import paths are not stable merely because an object is reachable from them.

## Compatibility Guarantees

Alternative implementations are free to choose different internal modules, concurrency helpers, protocol engines, and data structures. Compatibility requires the documented imports, signatures, defaults, precedence rules, state transitions, side effects, return values, warnings, and failure categories to remain observable at the public boundaries above.

Variable values such as generated dates, operating-system-assigned ports, process identifiers, and platform error messages are compared by their documented meaning rather than by one captured representation. ASGI event streams and middleware effects remain ordered behavioral contracts even when their internal scheduling differs.
