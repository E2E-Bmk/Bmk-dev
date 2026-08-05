"""Shared fixtures for PyMdown Extensions public behavior tests."""
from __future__ import annotations

import base64

import markdown
import pytest


PIXEL_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


def render_markdown(text: str, extensions: list[str], configs: dict | None = None) -> str:
    """Render Markdown with public extension strings and optional configuration."""

    return markdown.Markdown(extensions=extensions, extension_configs=configs or {}).convert(text)


def pytest_configure(config):
    """Register local metadata markers used by integration tests."""

    config.addinivalue_line("markers", "depends_on(*tests): document atomic behavior dependencies")


@pytest.fixture
def markdown_renderer():
    """Return the shared renderer helper for tests that prefer fixture injection."""

    return render_markdown
