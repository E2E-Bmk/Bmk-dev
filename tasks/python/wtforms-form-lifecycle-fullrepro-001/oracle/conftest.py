"""Shared helpers for WTForms oracle tests."""
import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "mutated(clause_id): asserts behavior that diverges from the upstream package",
    )


class FormData(dict):
    """Small public getlist-compatible submitted-data adapter."""

    def getlist(self, name):
        value = self.get(name, [])
        return value if isinstance(value, list) else [value]
