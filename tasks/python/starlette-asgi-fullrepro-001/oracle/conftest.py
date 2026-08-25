"""Shared fixtures, helpers, and constants for starlette oracle tests."""
from __future__ import annotations

import asyncio


# ---------------------------------------------------------------------------
# ASGI runner for direct scope testing
# ---------------------------------------------------------------------------


def run_asgi(app, scope, incoming=None):
    """Run an ASGI app synchronously with a given scope, return sent messages."""
    sent = []
    messages = list(incoming or [{"type": "http.request", "body": b"", "more_body": False}])

    async def receive():
        return messages.pop(0) if messages else {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    asyncio.run(app(scope, receive, send))
    return sent


def http_scope(path="/", method="GET", headers=None, query_string=b"", root_path=""):
    """Build a minimal HTTP ASGI scope."""
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "path": path,
        "root_path": root_path,
        "query_string": query_string,
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
        "server": ("testserver", 80),
    }
