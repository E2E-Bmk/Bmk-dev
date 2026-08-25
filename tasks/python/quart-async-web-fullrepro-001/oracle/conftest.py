"""Shared fixtures, helpers, and constants for quart oracle tests."""
from __future__ import annotations

import asyncio

import pytest

from quart import Quart, Blueprint


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_app(secret_key: str | None = "test-secret") -> Quart:
    """Create a minimal Quart app with optional secret key."""
    app = Quart(__name__)
    if secret_key:
        app.secret_key = secret_key
    return app


def run_async(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)
