"""Shared fixtures for structlog oracle tests."""

import pytest

import structlog
from structlog import contextvars


@pytest.fixture(autouse=True)
def reset_structlog():
    """Reset structlog global defaults and context-local state around each test."""
    structlog.reset_defaults()
    contextvars.clear_contextvars()
    yield
    contextvars.clear_contextvars()
    structlog.reset_defaults()


class RecordingReturnLoggerFactory:
    """Logger factory that records positional args and returns a ReturnLogger."""

    def __init__(self):
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        return structlog.ReturnLogger()
