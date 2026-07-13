# Spec2Repo oracle - integration tests for httpcore-transport-fullrepro-001
import re
import ssl

import pytest

import httpcore


def http11_response(status=200, reason=b"OK", headers=(), body=b"Hello"):
    header_items = list(headers)
    lower_names = {name.lower() for name, value in header_items}
    if b"content-length" not in lower_names:
        header_items.append((b"Content-Length", str(len(body)).encode("ascii")))
    lines = [b"HTTP/1.1 %d %s\r\n" % (status, reason)]
    lines += [name + b": " + value + b"\r\n" for name, value in header_items]
    lines.append(b"\r\n")
    if body:
        lines.append(body)
    return lines


def written_bytes(stream):
    return b"".join(stream.writes)


def header_block(stream):
    return written_bytes(stream).split(b"\r\n\r\n", 1)[0]


def assert_header(stream, name, value):
    lines = header_block(stream).split(b"\r\n")[1:]
    assert name + b": " + value in lines


class TLSInfo:
    def selected_alpn_protocol(self):
        return "http/1.1"


class RecordingStream(httpcore.NetworkStream):
    def __init__(self, chunks):
        self.chunks = list(chunks)
        self.writes = []
        self.read_calls = []
        self.close_calls = 0
        self.tls_calls = []
        self.extra_info_queries = []

    def read(self, max_bytes, timeout=None):
        self.read_calls.append((max_bytes, timeout))
        if not self.chunks:
            return b""
        return self.chunks.pop(0)

    def write(self, buffer, timeout=None):
        self.writes.append(bytes(buffer))
        self.write_timeout = timeout

    def close(self):
        self.close_calls += 1

    def start_tls(self, ssl_context, server_hostname=None, timeout=None):
        assert isinstance(ssl_context, ssl.SSLContext)
        self.tls_calls.append((server_hostname, timeout))
        return self

    def get_extra_info(self, info):
        self.extra_info_queries.append(info)
        if info == "ssl_object":
            return TLSInfo()
        return None


class RecordingBackend(httpcore.NetworkBackend):
    def __init__(self, scripts):
        self.scripts = list(scripts)
        self.tcp_calls = []
        self.uds_calls = []
        self.sleep_calls = []
        self.streams = []

    def _next_stream(self):
        script = self.scripts.pop(0)
        if isinstance(script, BaseException):
            raise script
        stream = RecordingStream(script)
        self.streams.append(stream)
        return stream

    def connect_tcp(
        self, host, port, timeout=None, local_address=None, socket_options=None
    ):
        self.tcp_calls.append(
            {
                "host": host,
                "port": port,
                "timeout": timeout,
                "local_address": local_address,
                "socket_options": socket_options,
            }
        )
        return self._next_stream()

    def connect_unix_socket(self, path, timeout=None, socket_options=None):
        self.uds_calls.append(
            {"path": path, "timeout": timeout, "socket_options": socket_options}
        )
        return self._next_stream()

    def sleep(self, seconds):
        self.sleep_calls.append(seconds)


def pool_with(script, **kwargs):
    backend = RecordingBackend([script])
    pool = httpcore.ConnectionPool(network_backend=backend, **kwargs)
    return pool, backend


def test_pool_request_returns_status_headers_content_and_extensions():
    pool, backend = pool_with(
        http11_response(
            201,
            b"Created",
            [(b"X-Token", b"abc"), (b"X-Token", b"def")],
            b"created",
        )
    )
    response = pool.request("GET", "http://example.com/items")
    assert response.status == 201
    assert response.headers == [
        (b"X-Token", b"abc"),
        (b"X-Token", b"def"),
        (b"Content-Length", b"7"),
    ]
    assert response.content == b"created"
    assert response.extensions["http_version"] == b"HTTP/1.1"
    assert response.extensions["reason_phrase"] == b"Created"
    assert backend.tcp_calls[0]["host"] == "example.com"


def test_request_line_uses_path_and_query_from_url():
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request("GET", "http://example.com/search?q=red&sort=asc")
    assert written_bytes(backend.streams[0]).startswith(
        b"GET /search?q=red&sort=asc HTTP/1.1\r\n"
    )


def test_empty_url_path_is_sent_as_slash():
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request("GET", "http://example.com")
    assert written_bytes(backend.streams[0]).startswith(b"GET / HTTP/1.1\r\n")


def test_default_http_port_is_omitted_from_host_header():
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request("GET", "http://example.com:80/")
    assert_header(backend.streams[0], b"Host", b"example.com")


def test_non_default_http_port_is_included_in_host_header():
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request("GET", "http://example.com:8080/")
    assert_header(backend.streams[0], b"Host", b"example.com:8080")


def test_user_supplied_host_header_is_not_replaced():
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request("GET", "http://example.com/", headers={"Host": "alt.example"})
    block = header_block(backend.streams[0])
    assert b"Host: alt.example" in block.split(b"\r\n")
    assert b"Host: example.com" not in block.split(b"\r\n")


def test_mapping_headers_are_sent_as_http_headers():
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request("GET", "http://example.com/", headers={"User-Agent": "client"})
    assert_header(backend.streams[0], b"User-Agent", b"client")


def test_sequence_headers_preserve_duplicate_names():
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request(
        "GET",
        "http://example.com/",
        headers=[("Accept", "text/plain"), ("Accept", "application/json")],
    )
    block = header_block(backend.streams[0])
    assert block.count(b"\r\nAccept: ") == 2


def test_bytes_method_and_url_are_accepted():
    pool, backend = pool_with(http11_response(body=b"ok"))
    response = pool.request(b"GET", b"http://example.com/bytes")
    assert response.status == 200
    assert written_bytes(backend.streams[0]).startswith(b"GET /bytes HTTP/1.1\r\n")


def test_bytes_content_adds_content_length_and_body():
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request("POST", "http://example.com/upload", content=b"abcdef")
    wire = written_bytes(backend.streams[0])
    assert b"\r\nContent-Length: 6\r\n" in wire
    assert wire.endswith(b"\r\n\r\nabcdef")


def test_empty_bytes_content_adds_zero_content_length():
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request("POST", "http://example.com/upload", content=b"")
    assert_header(backend.streams[0], b"Content-Length", b"0")


def test_iterable_content_uses_chunked_transfer_encoding():
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request("POST", "http://example.com/upload", content=iter([b"ab", b"cde"]))
    wire = written_bytes(backend.streams[0])
    assert b"\r\nTransfer-Encoding: chunked\r\n" in wire
    assert b"\r\n\r\n2\r\nab\r\n3\r\ncde\r\n0\r\n\r\n" in wire


def test_explicit_content_length_is_preserved():
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request(
        "POST",
        "http://example.com/upload",
        headers={"Content-Length": "3"},
        content=b"abc",
    )
    lines = header_block(backend.streams[0]).split(b"\r\n")
    assert lines.count(b"Content-Length: 3") == 1


def test_explicit_transfer_encoding_prevents_auto_content_length():
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request(
        "POST",
        "http://example.com/upload",
        headers={"Transfer-Encoding": "chunked"},
        content=b"abc",
    )
    block = header_block(backend.streams[0])
    assert b"Transfer-Encoding: chunked" in block.split(b"\r\n")
    assert all(not line.startswith(b"Content-Length:") for line in block.split(b"\r\n"))


def test_stream_response_iterates_body_chunks_without_preloading_content():
    pool, backend = pool_with(
        http11_response(headers=[(b"Content-Length", b"10")], body=b"hello")
        + [b"world"]
    )
    with pool.stream("GET", "http://example.com/") as response:
        with pytest.raises(RuntimeError):
            _ = response.content
        assert list(response.iter_stream()) == [b"hello", b"world"]
    assert backend.streams[0].close_calls == 0


def test_stream_response_read_makes_content_available():
    pool, backend = pool_with(
        http11_response(headers=[(b"Content-Length", b"6")], body=b"abc") + [b"def"]
    )
    with pool.stream("GET", "http://example.com/") as response:
        assert response.read() == b"abcdef"
        assert response.content == b"abcdef"
    assert backend.streams[0].close_calls == 0


def test_same_origin_reuses_connection_after_response_is_read():
    backend = RecordingBackend(
        [
            http11_response(200, body=b"one")
            + http11_response(200, body=b"two"),
        ]
    )
    pool = httpcore.ConnectionPool(network_backend=backend)
    assert pool.request("GET", "http://example.com/one").content == b"one"
    assert pool.request("GET", "http://example.com/two").content == b"two"
    assert len(backend.tcp_calls) == 1


def test_different_origins_open_distinct_connections():
    backend = RecordingBackend(
        [http11_response(body=b"one"), http11_response(body=b"two")]
    )
    pool = httpcore.ConnectionPool(network_backend=backend)
    pool.request("GET", "http://one.example/")
    pool.request("GET", "http://two.example/")
    assert [call["host"] for call in backend.tcp_calls] == [
        "one.example",
        "two.example",
    ]


def test_pool_close_closes_idle_connections():
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request("GET", "http://example.com/")
    pool.close()
    assert backend.streams[0].close_calls == 1


def test_pool_context_manager_closes_idle_connections_on_exit():
    backend = RecordingBackend([http11_response(body=b"ok")])
    with httpcore.ConnectionPool(network_backend=backend) as pool:
        pool.request("GET", "http://example.com/")
    assert backend.streams[0].close_calls == 1


def test_zero_keepalive_limit_closes_connection_after_response_body():
    pool, backend = pool_with(http11_response(body=b"ok"), max_keepalive_connections=0)
    pool.request("GET", "http://example.com/")
    assert backend.streams[0].close_calls == 1


def test_unsupported_protocol_raises_public_exception():
    pool, _backend = pool_with(http11_response(body=b"unused"))
    with pytest.raises(httpcore.UnsupportedProtocol):
        pool.request("GET", "ftp://example.com/file")


def test_missing_protocol_raises_public_exception():
    pool, _backend = pool_with(http11_response(body=b"unused"))
    with pytest.raises(httpcore.UnsupportedProtocol):
        pool.request("GET", "example.com/file")


def test_local_address_is_passed_to_tcp_connect():
    pool, backend = pool_with(http11_response(body=b"ok"), local_address="127.0.0.1")
    pool.request("GET", "http://example.com/")
    assert backend.tcp_calls[0]["local_address"] == "127.0.0.1"


def test_socket_options_are_passed_to_tcp_connect():
    options = [(1, 2, 3)]
    pool, backend = pool_with(http11_response(body=b"ok"), socket_options=options)
    pool.request("GET", "http://example.com/")
    assert backend.tcp_calls[0]["socket_options"] is options


def test_unix_domain_socket_uses_connect_unix_socket():
    pool, backend = pool_with(http11_response(body=b"ok"), uds="/tmp/httpcore.sock")
    pool.request("GET", "http://example.com/")
    assert backend.tcp_calls == []
    assert backend.uds_calls[0]["path"] == "/tmp/httpcore.sock"


def test_connect_timeout_extension_is_passed_to_backend_connect():
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request(
        "GET",
        "http://example.com/",
        extensions={"timeout": {"connect": 2.5}},
    )
    assert backend.tcp_calls[0]["timeout"] == 2.5


def test_read_timeout_extension_is_passed_to_stream_reads():
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request(
        "GET",
        "http://example.com/",
        extensions={"timeout": {"read": 3.5}},
    )
    assert any(call[1] == 3.5 for call in backend.streams[0].read_calls)


def test_write_timeout_extension_is_passed_to_stream_writes():
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request(
        "POST",
        "http://example.com/",
        content=b"data",
        extensions={"timeout": {"write": 4.5}},
    )
    assert backend.streams[0].write_timeout == 4.5


def test_https_request_connects_to_default_tls_port_and_starts_tls():
    pool, backend = pool_with(http11_response(body=b"secure"))
    response = pool.request("GET", "https://example.com/")
    assert response.content == b"secure"
    assert backend.tcp_calls[0]["port"] == 443
    assert backend.streams[0].tls_calls[0][0] == "example.com"


def test_https_request_uses_sni_hostname_extension_when_present():
    pool, backend = pool_with(http11_response(body=b"secure"))
    pool.request(
        "GET",
        "https://example.com/",
        extensions={"sni_hostname": "alt.example"},
    )
    assert backend.streams[0].tls_calls[0][0] == "alt.example"


def test_https_non_default_port_is_used_for_connect_and_host_header():
    pool, backend = pool_with(http11_response(body=b"secure"))
    pool.request("GET", "https://example.com:8443/")
    assert backend.tcp_calls[0]["port"] == 8443
    assert_header(backend.streams[0], b"Host", b"example.com:8443")


def test_connect_error_is_retried_when_retries_are_available():
    backend = RecordingBackend(
        [httpcore.ConnectError("boom"), http11_response(body=b"ok")]
    )
    pool = httpcore.ConnectionPool(network_backend=backend, retries=1)
    response = pool.request("GET", "http://example.com/")
    assert response.content == b"ok"
    assert len(backend.tcp_calls) == 2
    assert backend.sleep_calls == [0]


def test_connect_error_is_raised_when_no_retries_remain():
    backend = RecordingBackend([httpcore.ConnectError("boom")])
    pool = httpcore.ConnectionPool(network_backend=backend, retries=0)
    with pytest.raises(httpcore.ConnectError):
        pool.request("GET", "http://example.com/")
    assert len(backend.tcp_calls) == 1


def test_multiple_retries_use_exponential_backoff_sequence():
    backend = RecordingBackend(
        [
            httpcore.ConnectError("one"),
            httpcore.ConnectError("two"),
            http11_response(body=b"ok"),
        ]
    )
    pool = httpcore.ConnectionPool(network_backend=backend, retries=2)
    assert pool.request("GET", "http://example.com/").content == b"ok"
    assert backend.sleep_calls == [0, 0.5]


def test_http_connection_direct_handle_request_returns_response():
    backend = RecordingBackend([http11_response(202, b"Accepted", body=b"accepted")])
    origin = httpcore.Origin(b"http", b"example.com", 80)
    connection = httpcore.HTTPConnection(origin, network_backend=backend)
    request = httpcore.Request(
        "GET", "http://example.com/direct", headers={"Host": "example.com"}
    )
    response = connection.handle_request(request)
    assert response.status == 202
    assert response.read() == b"accepted"


def test_http_connection_rejects_requests_for_other_origins():
    backend = RecordingBackend([http11_response(body=b"unused")])
    origin = httpcore.Origin(b"http", b"example.com", 80)
    connection = httpcore.HTTPConnection(origin, network_backend=backend)
    request = httpcore.Request("GET", "http://other.example/")
    with pytest.raises(RuntimeError):
        connection.handle_request(request)
    assert backend.tcp_calls == []


def test_http_connection_close_closes_the_underlying_stream():
    backend = RecordingBackend([http11_response(body=b"ok")])
    origin = httpcore.Origin(b"http", b"example.com", 80)
    connection = httpcore.HTTPConnection(origin, network_backend=backend)
    connection.handle_request(
        httpcore.Request("GET", "http://example.com/", headers={"Host": "example.com"})
    ).read()
    connection.close()
    assert backend.streams[0].close_calls == 1


def test_http_connection_reuses_its_stream_for_same_origin_requests():
    backend = RecordingBackend(
        [
            http11_response(body=b"one")
            + http11_response(body=b"two"),
        ]
    )
    origin = httpcore.Origin(b"http", b"example.com", 80)
    connection = httpcore.HTTPConnection(origin, network_backend=backend)
    first = connection.handle_request(
        httpcore.Request("GET", "http://example.com/1", headers={"Host": "example.com"})
    )
    assert first.read() == b"one"
    first.close()
    second = connection.handle_request(
        httpcore.Request("GET", "http://example.com/2", headers={"Host": "example.com"})
    )
    assert second.read() == b"two"
    second.close()
    assert len(backend.tcp_calls) == 1


def test_request_target_extension_overrides_url_target_on_the_wire():
    pool, backend = pool_with(http11_response(body=b"ok"))
    pool.request(
        "GET",
        "http://example.com/original",
        extensions={"target": b"/override?x=1"},
    )
    assert written_bytes(backend.streams[0]).startswith(
        b"GET /override?x=1 HTTP/1.1\r\n"
    )


def test_absolute_form_target_is_sent_unchanged():
    pool, backend = pool_with(http11_response(body=b"ok"))
    url = httpcore.URL(
        scheme=b"http",
        host=b"proxy.local",
        port=8080,
        target=b"http://example.com/path",
    )
    pool.request("GET", url)
    assert written_bytes(backend.streams[0]).startswith(
        b"GET http://example.com/path HTTP/1.1\r\n"
    )


def test_mock_backend_can_serve_documented_http11_response():
    backend = httpcore.MockBackend(http11_response(200, headers=[(b"X-Doc", b"1")], body=b"doc"))
    with httpcore.ConnectionPool(network_backend=backend) as pool:
        response = pool.request("GET", "https://example.com/")
    assert response.status == 200
    assert response.headers == [(b"X-Doc", b"1"), (b"Content-Length", b"3")]
    assert response.content == b"doc"


def test_network_stream_extra_info_defaults_to_none():
    class EmptyStream(httpcore.NetworkStream):
        def read(self, max_bytes, timeout=None):
            return b""

        def write(self, buffer, timeout=None):
            pass

        def close(self):
            pass

        def start_tls(self, ssl_context, server_hostname=None, timeout=None):
            return self

    assert EmptyStream().get_extra_info("missing") is None


def test_trace_extension_reports_started_and_complete_events():
    events = []

    def trace(name, info):
        events.append((name, dict(info)))

    pool, _backend = pool_with(http11_response(body=b"ok"))
    response = pool.request(
        "GET",
        "http://example.com/",
        extensions={"trace": trace},
    )
    assert response.content == b"ok"
    names = [name for name, info in events]
    assert "connection.connect_tcp.started" in names
    assert "connection.connect_tcp.complete" in names


def test_trace_extension_reports_failed_connection_event():
    events = []

    def trace(name, info):
        events.append((name, dict(info)))

    backend = RecordingBackend([httpcore.ConnectError("boom")])
    pool = httpcore.ConnectionPool(network_backend=backend)
    with pytest.raises(httpcore.ConnectError):
        pool.request("GET", "http://example.com/", extensions={"trace": trace})
    names = [name for name, info in events]
    assert "connection.connect_tcp.failed" in names
    assert any(isinstance(info.get("exception"), httpcore.ConnectError) for name, info in events)


def test_premature_server_disconnect_raises_remote_protocol_error():
    pool, _backend = pool_with([])
    with pytest.raises(httpcore.RemoteProtocolError):
        pool.request("GET", "http://example.com/")


def test_invalid_response_header_raises_remote_protocol_error():
    pool, _backend = pool_with(
        [b"HTTP/1.1 200 OK\r\n", b"Broken Header\r\n", b"\r\n", b"body"]
    )
    with pytest.raises(httpcore.RemoteProtocolError):
        pool.request("GET", "http://example.com/")


def test_connect_response_exposes_network_stream_extension():
    body = http11_response(200, headers=[(b"Content-Length", b"0")], body=b"")
    pool, backend = pool_with(body)
    with pool.stream("CONNECT", "http://example.com:80/") as response:
        assert response.status == 200
        network_stream = response.extensions["network_stream"]
        assert hasattr(network_stream, "read")
        assert hasattr(network_stream, "write")
        assert hasattr(network_stream, "close")


def test_pool_connections_property_returns_a_list_snapshot():
    pool, _backend = pool_with(http11_response(body=b"ok"))
    assert pool.connections == []
    pool.request("GET", "http://example.com/")
    first = pool.connections
    first.clear()
    assert len(pool.connections) == 1


def test_connection_available_state_is_publicly_queryable():
    backend = RecordingBackend([http11_response(body=b"ok")])
    origin = httpcore.Origin(b"http", b"example.com", 80)
    connection = httpcore.HTTPConnection(origin, network_backend=backend)
    assert connection.can_handle_request(origin) is True
    assert connection.is_closed() is False
    response = connection.handle_request(
        httpcore.Request("GET", "http://example.com/", headers={"Host": "example.com"})
    )
    response.read()
    response.close()
    assert connection.is_idle() is True
