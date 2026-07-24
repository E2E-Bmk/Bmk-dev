# Spec2Repo oracle - atomic tests for httpcore-transport-fullrepro-001
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


def test_response_iter_stream_can_only_be_consumed_once():
    response = httpcore.Response(200, content=iter([b"a", b"b"]))
    assert list(response.iter_stream()) == [b"a", b"b"]
    with pytest.raises(RuntimeError):
        list(response.iter_stream())


def test_response_read_caches_content_for_repeated_access():
    response = httpcore.Response(200, content=iter([b"a", b"b"]))
    assert response.read() == b"ab"
    assert response.read() == b"ab"
    assert response.content == b"ab"


def test_response_close_calls_stream_close_when_available():
    class ClosableBody:
        def __init__(self):
            self.closed = False

        def __iter__(self):
            yield b"body"

        def close(self):
            self.closed = True

    body = ClosableBody()
    response = httpcore.Response(200, content=body)
    response.close()
    assert body.closed is True


def test_request_object_target_extension_changes_url_target():
    request = httpcore.Request(
        "GET", "http://example.com/original", extensions={"target": b"/other"}
    )
    assert bytes(request.url) == b"http://example.com/other"


def test_url_from_string_exposes_components_and_default_origin_port():
    url = httpcore.URL("https://example.com/items?q=1")
    assert url.scheme == b"https"
    assert url.host == b"example.com"
    assert url.port is None
    assert url.target == b"/items?q=1"
    assert url.origin == httpcore.Origin(b"https", b"example.com", 443)


def test_url_from_explicit_components_round_trips_to_bytes():
    url = httpcore.URL(scheme=b"http", host=b"example.com", port=8080, target=b"/x")
    assert bytes(url) == b"http://example.com:8080/x"
    assert url.origin == httpcore.Origin(b"http", b"example.com", 8080)


def test_url_target_allows_options_star_request():
    pool, backend = pool_with(http11_response(body=b"ok"))
    url = httpcore.URL(scheme=b"http", host=b"example.com", target=b"*")
    pool.request("OPTIONS", url)
    assert written_bytes(backend.streams[0]).startswith(b"OPTIONS * HTTP/1.1\r\n")


def test_request_rejects_non_ascii_method_strings():
    with pytest.raises(TypeError):
        httpcore.Request("G\u00c9T", "http://example.com/")


def test_request_rejects_non_ascii_header_values():
    with pytest.raises(TypeError):
        httpcore.Request("GET", "http://example.com/", headers={"X-Name": "caf\u00e9"})


def test_url_rejects_non_ascii_url_strings():
    with pytest.raises(TypeError):
        httpcore.URL("http://example.com/caf\u00e9")


def test_response_header_mapping_is_normalized_to_byte_pairs():
    response = httpcore.Response(200, headers={"Content-Type": "text/plain"})
    assert response.headers == [(b"Content-Type", b"text/plain")]


def test_proxy_auth_adds_basic_proxy_authorization_header():
    proxy = httpcore.Proxy("http://proxy.example:8080", auth=("user", "pass"))
    assert proxy.url.origin == httpcore.Origin(b"http", b"proxy.example", 8080)
    assert proxy.headers == [(b"Proxy-Authorization", b"Basic dXNlcjpwYXNz")]


def test_proxy_preserves_custom_headers_after_authorization_header():
    proxy = httpcore.Proxy(
        "http://proxy.example:8080",
        auth=("user", "pass"),
        headers={"X-Proxy": "yes"},
    )
    assert proxy.headers == [
        (b"Proxy-Authorization", b"Basic dXNlcjpwYXNz"),
        (b"X-Proxy", b"yes"),
    ]


def test_mock_stream_read_returns_configured_chunks_then_empty_bytes():
    stream = httpcore.MockStream([b"abc", b"def"])
    assert stream.read(10) == b"abc"
    assert stream.read(10) == b"def"
    assert stream.read(10) == b""


def test_mock_stream_start_tls_returns_stream_itself():
    stream = httpcore.MockStream([b""])
    context = ssl.create_default_context()
    assert stream.start_tls(context, server_hostname="example.com") is stream
