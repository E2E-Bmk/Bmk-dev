"""Shared public test helpers for Textual artifact-only oracle tests."""

from __future__ import annotations


def pytest_configure(config):
    config.addinivalue_line("markers", "depends_on(*tests): document atomic dependencies")
