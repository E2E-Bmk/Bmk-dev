import json
import socket
from contextlib import contextmanager

import pytest

from vcr.request import Request

# ── Constants ──────────────────────────────────────────────────
TEST_HOST = "api.example.test"
TEST_URL = f"http://{TEST_HOST}/resources"
TEST_HTTPS_URL = f"https://{TEST_HOST}/resources"


# ── Shared helpers ─────────────────────────────────────────────

def make_response(body=b"ok", status=200, message="OK", headers=None):
    """Build a minimal response dict in cassette interaction format."""
    return {
        "status": {"code": status, "message": message},
        "headers": headers or {},
        "body": {"string": body},
    }


def make_request(method="GET", uri=TEST_URL, body=None, headers=None):
    """Build a Request with sensible defaults."""
    return Request(method, uri, body, headers or {})


class IdentitySerializer:
    """Pass-through serializer for cassette-level tests that skip file I/O."""

    @staticmethod
    def serialize(data):
        return data

    @staticmethod
    def deserialize(data):
        return data


class InMemoryJsonSerializer:
    """JSON serializer for filesystem round-trip tests."""

    @staticmethod
    def serialize(data):
        return json.dumps(data)

    @staticmethod
    def deserialize(data):
        return json.loads(data)


@contextmanager
def patched_dns(overrides):
    """Temporarily override DNS resolution for specified hostnames."""
    _real = socket.getaddrinfo

    def _fake(*args, **kwargs):
        if args[0] in overrides:
            return [(2, 1, 6, "", (overrides[args[0]], args[1]))]
        return _real(*args, **kwargs)

    socket.getaddrinfo = _fake
    try:
        yield
    finally:
        socket.getaddrinfo = _real


# ── Marker registration ───────────────────────────────────────

def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): atomic tests this integration test depends on",
    )


# ── Fixtures ───────────────────────────────────────────────────

@pytest.fixture
def cassette_dir(tmp_path):
    """Temporary directory for cassette files."""
    d = tmp_path / "cass"
    d.mkdir()
    return d


@pytest.fixture(autouse=True)
def _strip_proxy_env(monkeypatch):
    """Prevent proxy env vars from interfering with local HTTP tests."""
    for name in (
        "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
        "http_proxy", "https_proxy", "all_proxy",
    ):
        monkeypatch.delenv(name, raising=False)
