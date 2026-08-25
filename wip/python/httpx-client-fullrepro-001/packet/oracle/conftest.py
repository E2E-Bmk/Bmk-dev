"""Shared fixtures, helpers, and constants for httpx oracle tests."""
from __future__ import annotations

import asyncio

import pytest

import httpx


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://api.test"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def echo_handler(request: httpx.Request) -> httpx.Response:
    """Transport handler that echoes request details back as JSON."""
    import json
    body = {
        "method": request.method,
        "path": request.url.path,
        "query": str(request.url.query, "ascii") if request.url.query else "",
        "headers": dict(request.headers.multi_items()),
    }
    return httpx.Response(200, json=body, request=request)


def status_handler(status: int):
    """Return a handler that always responds with the given status."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, request=request)
    return handler


def redirect_handler(request: httpx.Request) -> httpx.Response:
    """Handler that redirects /start → /end."""
    if request.url.path == "/start":
        return httpx.Response(302, headers={"Location": "/end"}, request=request)
    return httpx.Response(200, text="arrived", request=request)


def run_async(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)
