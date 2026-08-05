from __future__ import annotations

import datetime
import logging
from uuid import uuid4

import pytest

from huey import MemoryHuey


FIXED_ETA = datetime.datetime(2030, 1, 2, 12, 0, 0)


def unique_name(prefix: str = "huey") -> str:
    return f"{prefix}-{uuid4().hex}"


@pytest.fixture
def huey():
    return MemoryHuey(unique_name(), immediate=False, utc=False)


@pytest.fixture
def immediate_huey():
    return MemoryHuey(unique_name("immediate"), immediate=True, utc=False)


@pytest.fixture
def fixed_eta():
    return FIXED_ETA


def execute_next(huey, timestamp=None):
    task = huey.dequeue()
    assert task is not None
    return huey.execute(task, timestamp=timestamp)


@pytest.fixture
def run_next():
    return execute_next


@pytest.fixture
def signal_events():
    return []


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): atomic behaviors required by an integration test",
    )
    config.addinivalue_line(
        "markers",
        "suppress_logs(*names): expected logger output already covered by behavioral assertions",
    )


@pytest.fixture(autouse=True)
def suppress_marked_logs(request):
    marker = request.node.get_closest_marker("suppress_logs")
    if marker is None:
        yield
        return
    loggers = [logging.getLogger(name) for name in marker.args]
    previous = [logger.disabled for logger in loggers]
    for logger in loggers:
        logger.disabled = True
    try:
        yield
    finally:
        for logger, disabled in zip(loggers, previous):
            logger.disabled = disabled
