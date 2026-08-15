# httpcore Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`httpcore` is a low-level HTTP transport library. It sends HTTP requests through pluggable network backends, parses HTTP responses into response objects, and manages reusable connections through a connection pool. This specification covers the synchronous HTTP/1.1 transport surface and the data objects needed to use it without making real network calls.

## Non-Goals

- This specification does not require Asynchronous APIs, HTTP/2 framing, or SOCKS proxy negotiation.
- This specification does not require Real socket I/O, environment configuration, or logging formatting.
- This specification does not require Exact `repr()` output or exact exception message text.

## Representative Workflows

A caller creates a custom `NetworkBackend`, passes it to `ConnectionPool`, issues a request, inspects the response, and closes the pool. For repeated requests to the same origin, the second request must reuse the connection once the first response body has been completed.

```python
import httpcore

backend = httpcore.MockBackend([
    b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello",
    b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nworld",
])
with httpcore.ConnectionPool(network_backend=backend) as pool:
    first = pool.request("GET", "http://example.com/one")
    assert first.status == 200
    assert first.content == b"hello"

    second = pool.request("GET", "http://example.com/two")
    assert second.status == 200
    assert second.content == b"world"
```

The `MockBackend` supplies pre-configured HTTP response byte streams so tests run without real network access. The pool reuses the same connection for sequential requests to the same origin after the first response body has been consumed.

```python
import httpcore

origin = httpcore.Origin(scheme=b"http", host=b"example.com", port=80)
backend = httpcore.MockBackend([
    b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK",
])
conn = httpcore.HTTPConnection(origin=origin, network_backend=backend)

request = httpcore.Request(method=b"GET", url="http://example.com/status")
response = conn.handle_request(request)
response.read()

assert response.status == 200
assert response.content == b"OK"
assert response.extensions["http_version"] == b"HTTP/1.1"
assert conn.is_idle()
conn.close()
assert conn.is_closed()
```

A direct `HTTPConnection` sends requests for a single origin. After the response body is read, the connection transitions to idle state and is available for reuse. Calling `close()` marks it as closed. The response extensions expose protocol metadata such as the HTTP version.

## URL, Request, Response Models

URL, request, and response models provide the data containers for HTTP exchange, handling parsing, normalization, and lazy body semantics.

**URL parsing.** URL parsing must split scheme, host, optional port, and target. Missing path must produce target `b"/"`. Query strings must remain in the target. Default origin ports are `80` for `http` and `443` for `https`.

**Headers.** Request and response headers must accept mappings or sequences of two-tuples. Header names and values must become bytes. Duplicate sequence headers must be preserved. Non-ASCII string methods, URLs, or header values must raise `TypeError`.

**Streaming bodies.** Response bodies are lazy when a streaming response is returned. Accessing `content` before `read()` on a streaming response must raise `RuntimeError`. Calling `iter_stream()` more than once must raise `RuntimeError`. `read()` must cache the result so that subsequent calls return the same content.

## HTTP/1.1 Request Serialization

Request serialization converts a `Request` object into HTTP/1.1 wire bytes for transmission over a network stream.

**Request line.** HTTP/1.1 requests must write a request line using the method and URL target. The default target is the parsed path and query; an explicit URL target such as `b"*"` or an absolute-form proxy target must be sent unchanged.

**Host header.** The `Host` header must be added when missing. Default ports must be omitted from `Host`; non-default ports must be included. A caller-supplied `Host` header must not be replaced.

**Body framing.** Byte request bodies must add `Content-Length` when neither `Content-Length` nor `Transfer-Encoding` is already present. An empty bytes body must add `Content-Length: 0`. Iterable request bodies must use `Transfer-Encoding: chunked` when no length or transfer encoding is supplied. Explicit `Content-Length` and `Transfer-Encoding` headers must be respected.

## HTTP/1.1 Response Handling and Streaming

Response handling parses inbound HTTP/1.1 bytes into response objects with status, headers, body, and protocol metadata.

**Basic parsing.** HTTP/1.1 response bytes must produce a `Response` with status, headers, content, and extensions. The `"http_version"` extension must be `b"HTTP/1.1"` for HTTP/1.1 responses. The `"reason_phrase"` extension must contain the response reason bytes.

Streaming responses must not preload the body. Reading or iterating the stream must yield received body bytes in order. `iter_stream()` must preserve the chunk grouping received from the HTTP response stream and must not coalesce adjacent body chunks. Closing a response must release the associated stream or body resource according to the public close methods.

For successful `CONNECT` responses, the response extensions must expose a `"network_stream"` object with `read`, `write`, and `close` methods for direct stream use outside the request/response model.

## Network Backends and Mock Streams

Network backends abstract the underlying connection mechanism, allowing tests to substitute mock streams for real sockets.

**Backend dispatch.** `ConnectionPool` and `HTTPConnection` must use the configured `network_backend` instead of opening sockets directly. For HTTP URLs they must call `connect_tcp()` with the host decoded from the byte-valued origin into an ASCII Python `str`, plus the integer port from the origin. For `uds`, they must call `connect_unix_socket()` with the configured path and must not call `connect_tcp()`.

`local_address`, `socket_options`, and connect timeout values must be forwarded to backend connection calls. Read and write timeout values from request extensions must be forwarded to stream `read()` and `write()` calls.

`MockBackend` must create mock streams that serve the configured byte chunks. `MockStream.read()` must return each chunk and then `b""`. `MockStream.start_tls()` must return itself.

## Connection Pool Lifecycle

The connection pool manages connection reuse, keepalive limits, and cleanup for efficient multi-request workflows.

**Connection reuse.** A pool must reuse an idle HTTP/1.1 connection for sequential requests to the same origin after the prior response body has been consumed or closed. Requests to different origins must open distinct connections.

**Keepalive and cleanup.** When `max_keepalive_connections` is set to `0`, the pool must close an idle connection after its response body is complete. `close()` and context manager exit must close idle connections. `connections` must return a list snapshot, so mutating the returned list must not mutate pool state.

## Direct HTTP Connections

A direct connection sends requests for a single origin, exposing connection state through lifecycle query methods.

**Origin restriction.** `HTTPConnection` must only accept requests for its configured origin. A request for another origin must raise `RuntimeError` before opening a network connection.

After a direct response body is read and closed, the connection must become idle and reusable for another request to the same origin. Calling `close()` on the connection must close the underlying stream.

## TLS, UDS, Timeouts, and Retries

Transport-level concerns including TLS, Unix domain sockets, timeouts, and connection retries affect how connections are established without changing response semantics.

**TLS.** HTTPS requests must connect to port `443` when no port is specified, then call `start_tls()` on the stream. When no explicit SSL context was supplied, the connection must create and pass a default `ssl.SSLContext` object to `start_tls()`. The default TLS server hostname is the request host; a `"sni_hostname"` extension must override it while preserving the same SSL context rule.

**Retries.** When a backend raises `ConnectError`, the connection must retry up to the configured `retries` count. Retry sleeps must begin with `0` seconds and then use `0.5`, doubling after that. When no retry remains, the original `ConnectError` must be raised.

## Proxy Configuration

Proxy configuration describes how outbound requests are routed through an intermediate proxy server.

**Construction.** `Proxy` accepts a URL, optional `auth` credentials, optional `headers`, and an optional `ssl_context`. It stores the proxy URL as a `URL`, normalizes headers to byte pairs, and stores the SSL context. When `auth` is supplied as a `(username, password)` tuple, the proxy headers must begin with a `Proxy-Authorization` Basic header encoding `username:password` in Base64, followed by any custom headers.

## Trace Events and Extensions

Trace callbacks provide observability into connection lifecycle events during request processing.

**Trace protocol.** When a request extension contains a `"trace"` callback, connection operations must call it with event names and information dictionaries. TCP connection attempts must emit `connection.connect_tcp.started` and `connection.connect_tcp.complete` events on success, and `connection.connect_tcp.failed` events with an exception on failure. TLS upgrades must emit `connection.start_tls.started` and `connection.start_tls.complete` events.

## State Model

The transport state has three public projections: the response object returned to the caller, the bytes written to the selected network stream, and the connection lifecycle exposed by pool or connection methods. A request must update all three consistently: serialized request bytes must match the `Request`, response attributes must match received bytes, and idle/closed state must follow body consumption and closing.

## Error Semantics

Unsupported or missing URL schemes must raise `UnsupportedProtocol`. Premature server disconnects or malformed response bytes must raise `RemoteProtocolError`. Invalid local request data must raise `TypeError` for ASCII/type validation failures or `LocalProtocolError` when HTTP protocol rules are violated.

## Cross-View Invariants

- A URL target visible on the `Request` must match the request target written to the network stream.
- Headers visible on a `Request` must match the serialized headers, with automatic `Host` and body framing headers added only when required.
- Response status, headers, body, HTTP version, and reason phrase returned to the caller must match the response bytes read from the stream.
- Backend connection call arguments must reflect pool configuration and request extensions.
- Pool connection state must reflect whether response streams have been consumed, closed, kept alive, or explicitly closed by the pool.
- TLS and UDS configuration must change the backend operations while preserving the same response object semantics.
- Retry behavior must be visible both as repeated backend connection calls and as sleeps between failed attempts.

## Public Interface

### Import Surface

The package must be importable as `httpcore`.

```python
from httpcore import (
    URL, Origin, Request, Response, Proxy,
    ConnectionPool, HTTPConnection,
    NetworkBackend, NetworkStream, MockBackend, MockStream,
    UnsupportedProtocol, ConnectError, LocalProtocolError, RemoteProtocolError,
)
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `URL` | class | Parsed URL with scheme, host, port, target, and origin |
| `Origin` | class | Byte-valued origin identity for connection reuse |
| `Request` | class | Outbound HTTP request with method, URL, headers, body, and extensions |
| `Response` | class | Inbound HTTP response with status, headers, body stream, and extensions |
| `Proxy` | class | Proxy URL, authentication, headers, and TLS context |
| `ConnectionPool` | class | Pooled HTTP/1.1 connections with reuse and retry policy |
| `HTTPConnection` | class | Single-origin HTTP/1.1 connection |
| `NetworkBackend` | class | Pluggable TCP, UDS, and sleep operations |
| `NetworkStream` | class | Readable, writable, closable network stream with TLS upgrade |
| `MockBackend` | class | Test backend that serves configured byte chunks |
| `MockStream` | class | Test stream that returns configured read chunks |
| `UnsupportedProtocol` | exception | Unsupported or missing URL scheme |
| `ConnectError` | exception | Backend connection failure |
| `LocalProtocolError` | exception | Invalid local request serialization |
| `RemoteProtocolError` | exception | Malformed or truncated server response |

`URL` accepts either a full URL value or explicit components. String inputs must be ASCII. A parsed URL exposes `scheme`, `host`, `port`, `target`, and `origin`. `bytes(url)` returns the full URL bytes; explicit non-default ports must be preserved.

`Origin` stores byte-valued `scheme` and `host` plus an integer `port`. Origins compare equal when all three values match.

`Request` stores the method as bytes, the URL as a `URL`, headers as a list of byte pairs, a sync iterable body stream, and an extensions dictionary. A `"target"` extension must replace the URL target used for the request.

`Response` stores the integer status, headers as byte pairs, a sync iterable body stream, and extensions. `read()` consumes the body into `content`; `iter_stream()` yields the body once; `close()` closes the body stream when it has a `close()` method.

`ConnectionPool` accepts TLS context, proxy, connection limits, keepalive settings, HTTP version flags, retry count, local address, UDS path, network backend, and socket options. `ssl_context=None` means HTTPS connections must create and use a default TLS context. `request()` returns a fully read `Response`. `stream()` returns a context-managed streaming `Response`. `close()` closes idle connections. `connections` returns a list snapshot of current connection objects.

`HTTPConnection` sends requests for one origin. `handle_request(request)` returns a streaming `Response`. `can_handle_request(origin)`, `is_available()`, `is_idle()`, and `is_closed()` expose connection state.

`NetworkBackend` defines TCP connection, UDS connection, and sleep operations. `connect_tcp()` receives `host` as an ASCII Python `str` and `port` as an integer. `NetworkStream` defines read, write, close, TLS upgrade, and extra-info lookup operations.

`MockBackend` and `MockStream` are local testing implementations. A mock stream returns configured byte chunks from `read()` and then returns `b""`. `start_tls()` returns the stream itself.

### CLI Entry Points

There is no console script in scope. `python -m httpcore` is not supported for this surface. Importing `httpcore` must make the covered public names available.

Exit codes are not part of the covered API.

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment. External network access is not required because the documented transport workflows accept local custom backends and mock streams.

## Appendix B: Assessment Notes

Compatibility covers the documented imports, request and response models, byte serialization, streaming lifecycle, connection reuse, backend dispatch, TLS and UDS selection, retries, tracing, and public exception classes. Public return values, backend calls, stream bytes, and lifecycle state form the compatibility boundary; private organization, exact representations, and exact error prose are not.
