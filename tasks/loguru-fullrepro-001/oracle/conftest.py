"""Shared fixtures, helpers, and constants for loguru oracle tests."""

from __future__ import annotations

import io
import logging
import sys

import pytest
import loguru
from loguru import logger

TEXT = "Delta\nEpsilon\nZeta\nMarker\n135792468\nQWE!RTY\nDelta Marks The Start\n"


@pytest.fixture(autouse=True)
def clean_logger_():
    """Reset global logger state before and after each test."""
    logger.remove()
    logger.configure(extra={}, patcher=lambda record: None, activation=[(__name__, True)])
    yield
    logger.remove()
    logger.configure(extra={}, patcher=lambda record: None, activation=[(__name__, True)])


def make_writer():
    messages = []

    def sink(message):
        messages.append(message)

    return messages, sink


class TtyStream(io.StringIO):
    def isatty(self):
        return True


class NonTtyStream(io.StringIO):
    def isatty(self):
        return False


class BrokenSink:
    def __init__(self):
        self.calls = 0

    def write(self, message):
        self.calls += 1
        raise RuntimeError("sink failed")


class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


@pytest.fixture
def writer():
    class Writer:
        def __init__(self):
            self.messages = []

        def write(self, message):
            self.messages.append(message)

        def read(self):
            return "".join(map(str, self.messages))

    return Writer()


@pytest.fixture
def fileobj():
    with io.StringIO(TEXT) as file:
        yield file
