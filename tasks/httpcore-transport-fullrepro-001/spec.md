# httpcore Specification

## Product Overview

`httpcore` is a low-level HTTP transport library. It sends HTTP requests through pluggable network backends, parses HTTP responses into response objects, and manages reusable connections through a connection pool. This specification covers the synchronous HTTP/1.1 transport surface and the data objects needed to use it without making real network calls.

## Scope

The covered surface is the synchronous request/response path:

- URL, request, response, origin, and proxy data objects.
- `ConnectionPool` and `HTTPConnection` for HTTP/1.1 requests.
- `NetworkBackend`, `NetworkStream`, `MockBackend`, and `MockStream`.
- Local behavior for TLS startup, Unix domain sockets, timeouts, retries, trace callbacks, and response streaming.

## Installable Surface

The package must be importable as `httpcore`. The covered public names are:

- `URL`, `Origin`, `Request`, `Response`, `Proxy`.
- `ConnectionPool`, `HTTPConnection`.
- `NetworkBackend`, `NetworkStream`, `MockBackend`, `MockStream`.
- `UnsupportedProtocol`, `ConnectError`, `LocalProtocolError`, `RemoteProtocolError`.

## Public API

`URL(url="", *, scheme=b"", host=b"", port=None, target=b"")` accepts either a full URL string/bytes value or explicit components. String inputs must be ASCII. A parsed URL exposes `scheme`, `host`, `port`, `target`, and `origin`. `bytes(url)` returns the full URL bytes; explicit non-default ports must be preserved.

`Origin(scheme, host, port)` stores byte-valued `scheme` and `host` plus an integer `port`. Origins compare equal when all three values match.

`Request(method, url, *, headers=None, content=None, extensions=None)` stores the method as bytes, the URL as a `URL`, headers as a list of byte pairs, a sync iterable body stream, and an extensions dictionary. A `"target"` extension must replace the URL target used for the request.

`Response(status, *, headers=None, content=None, extensions=None)` stores the integer status, headers as byte pairs, a sync iterable body stream, and extensions. `read()` consumes the body into `content`; `iter_stream()` yields the body once; `close()` closes the body stream when it has a `close()` method.

`ConnectionPool(...)` accepts `ssl_context=None`, `proxy=None`, `max_connections=10`, `max_keepalive_connections=None`, `keepalive_expiry=None`, `http1=True`, `http2=False`, `retries=0`, `local_address=None`, `uds=None`, `network_backend=None`, and `socket_options=None`. `ssl_context=None` means HTTPS connections must create and use a default TLS `ssl.SSLContext`. `request()` returns a fully read `Response`. `stream()` returns a context-managed streaming `Response`. `close()` closes idle connections. `connections` returns a list snapshot of current connection objects.

`HTTPConnection(origin, ..., network_backend=None, retries=0, local_address=None, uds=None, socket_options=None)` sends requests for one origin. `handle_request(request)` returns a streaming `Response`. `can_handle_request(origin)`, `is_available()`, `is_idle()`, and `is_closed()` expose connection state.

`NetworkBackend` defines `connect_tcp(host, port, timeout=None, local_address=None, socket_options=None)`, `connect_unix_socket(path, timeout=None, socket_options=None)`, and `sleep(seconds)`. `connect_tcp()` receives `host` as an ASCII Python `str` and `port` as an integer. `NetworkStream` defines `read(max_bytes, timeout=None)`, `write(buffer, timeout=None)`, `close()`, `start_tls(ssl_context, server_hostname=None, timeout=None)`, and `get_extra_info(info)`.

`MockBackend(buffer, http2=False)` and `MockStream(buffer, http2=False)` are local testing implementations. A mock stream returns configured byte chunks from `read()` and then returns `b""`. `start_tls()` returns the stream itself.

## Product State Model

The transport state has three public projections: the response object returned to the caller, the bytes written to the selected network stream, and the connection lifecycle exposed by pool or connection methods. A request must update all three consistently: serialized request bytes must match the `Request`, response attributes must match received bytes, and idle/closed state must follow body consumption and closing.

## URL, Request, Response Models

URL parsing must split scheme, host, optional port, and target. Missing path must produce target `b"/"`. Query strings must remain in the target. Default origin ports are `80` for `http` and `443` for `https`.

Request and response headers must accept mappings or sequences of two-tuples. Header names and values must become bytes. Duplicate sequence headers must be preserved. Non-ASCII string methods, URLs, or header values must raise `TypeError`.

Response bodies are lazy when a streaming response is returned. Accessing `content` before `read()` on a streaming response must raise `RuntimeError`. Calling `iter_stream()` more than once must raise `RuntimeError`.

## HTTP/1.1 Request Serialization

HTTP/1.1 requests must write a request line using the method and URL target. The default target is the parsed path and query; an explicit URL target such as `b"*"` or an absolute-form proxy target must be sent unchanged.

The `Host` header must be added when missing. Default ports must be omitted from `Host`; non-default ports must be included. A caller-supplied `Host` header must not be replaced.

Byte request bodies must add `Content-Length` when neither `Content-Length` nor `Transfer-Encoding` is already present. Iterable request bodies must use `Transfer-Encoding: chunked` when no length or transfer encoding is supplied. Explicit `Content-Length` and `Transfer-Encoding` headers must be respected.

## HTTP/1.1 Response Handling and Streaming

HTTP/1.1 response bytes must produce a `Response` with status, headers, content, and extensions. The `"http_version"` extension must be `b"HTTP/1.1"` for HTTP/1.1 responses. The `"reason_phrase"` extension must contain the response reason bytes.

Streaming responses must not preload the body. Reading or iterating the stream must yield received body bytes in order. `iter_stream()` must preserve the chunk grouping received from the HTTP response stream and must not coalesce adjacent body chunks. Closing a response must release the associated stream or body resource according to the public close methods.

For successful `CONNECT` responses, the response extensions must expose a `"network_stream"` object with `read`, `write`, and `close` methods for direct stream use outside the request/response model.

## Network Backends and Mock Streams

`ConnectionPool` and `HTTPConnection` must use the configured `network_backend` instead of opening sockets directly. For HTTP URLs they must call `connect_tcp()` with the host decoded from the byte-valued origin into an ASCII Python `str`, plus the integer port from the origin. For `uds`, they must call `connect_unix_socket()` with the configured path and must not call `connect_tcp()`.

`local_address`, `socket_options`, and connect timeout values must be forwarded to backend connection calls. Read and write timeout values from request extensions must be forwarded to stream `read()` and `write()` calls.

`MockBackend` must create mock streams that serve the configured byte chunks. `MockStream.read()` must return each chunk and then `b""`. `MockStream.start_tls()` must return itself.

## Connection Pool Lifecycle

A pool must reuse an idle HTTP/1.1 connection for sequential requests to the same origin after the prior response body has been consumed or closed. Requests to different origins must open distinct connections.

`max_keepalive_connections=0` must close an idle connection after its response body is complete. `close()` and context manager exit must close idle connections. `connections` must return a list snapshot, so mutating the returned list must not mutate pool state.

## Direct HTTP Connections

`HTTPConnection` must only accept requests for its configured origin. A request for another origin must raise `RuntimeError` before opening a network connection.

After a direct response body is read and closed, the connection must become idle and reusable for another request to the same origin. Calling `close()` on the connection must close the underlying stream.

## TLS, UDS, Timeouts, and Retries

HTTPS requests must connect to port `443` when no port is specified, then call `start_tls()` on the stream. When no explicit SSL context was supplied, the connection must create and pass a default `ssl.SSLContext` object to `start_tls()`. The default TLS server hostname is the request host; a `"sni_hostname"` extension must override it while preserving the same SSL context rule.

When a backend raises `ConnectError`, the connection must retry up to the configured `retries` count. Retry sleeps must begin with `0` seconds and then use `0.5`, doubling after that. When no retry remains, the original `ConnectError` must be raised.

## Proxy Configuration

`Proxy(url, auth=None, headers=None, ssl_context=None)` stores the proxy URL as a `URL`, normalizes headers to byte pairs, and stores the SSL context. When `auth=(username, password)` is supplied, the proxy headers must begin with a `Proxy-Authorization` Basic header for `username:password`, followed by any custom headers.

## Trace Events and Extensions

When a request extension contains a `"trace"` callback, connection operations must call it with event names and information dictionaries. TCP connection attempts must emit started and complete events on success, and failed events with an exception on failure.

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

## Representative Workflows

A caller creates a custom `NetworkBackend`, passes it to `ConnectionPool`, issues a request, inspects the response, and closes the pool. For repeated requests to the same origin, the second request must reuse the connection once the first response body has been completed.

```python
backend = MyNetworkBackend([...])
with httpcore.ConnectionPool(network_backend=backend) as pool:
    first = pool.request("GET", "http://example.com/one")
    second = pool.request("GET", "http://example.com/two")
```

## Non-Goals

This specification does not require asynchronous APIs, HTTP/2 framing, SOCKS proxy negotiation, real socket I/O, environment configuration, logging formatting, exact `repr()` output, or exact exception message text.

## Invocation Protocol

There is no console script in scope. `python -m httpcore` is not supported for this surface. Importing `httpcore` must make the covered public names available.

Exit codes are not part of the covered API.

## Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment. External network access is not required because the documented transport workflows accept local custom backends and mock streams.

## Evaluation Notes

Assessment exercises the documented imports, request and response models, byte serialization, streaming lifecycle, connection reuse, backend dispatch, TLS and UDS selection, retries, tracing, and public exception classes. Observable return values, backend calls, stream bytes, and lifecycle state are checked; private organization, exact representations, and exact error prose are not.
