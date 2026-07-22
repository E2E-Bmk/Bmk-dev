"""Shared fixtures, helpers, and constants for requests-cache oracle tests."""

import pytest

import requests_cache

MOCK_URL = "https://example.test/resource"
MOCK_URL_ALT = "https://example.test/other"
MOCK_URL_ITEMS = "https://example.test/items"


@pytest.fixture(autouse=True)
def cleanup_patcher():
    """Ensure patcher is uninstalled before and after each test."""
    requests_cache.uninstall_cache()
    yield
    requests_cache.uninstall_cache()
