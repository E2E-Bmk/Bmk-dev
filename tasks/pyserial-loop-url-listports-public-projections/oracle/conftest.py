from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--target-root",
        action="store",
        default=os.environ.get("TARGET_ROOT"),
        help="Path containing the serial package under test",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): atomic public behaviors used by an integration test",
    )


def pytest_sessionstart(session):
    configured_root = session.config.getoption("--target-root")
    if configured_root is None:
        return
    target_root = Path(configured_root).resolve()
    for name in list(sys.modules):
        if name == "serial" or name.startswith("serial."):
            sys.modules.pop(name, None)
    sys.path.insert(0, str(target_root))


@pytest.fixture
def loop_serial():
    import serial

    port = serial.serial_for_url("loop://", timeout=0)
    try:
        yield port
    finally:
        port.close()


@pytest.fixture
def make_loop():
    import serial

    def factory(**kwargs):
        options = {"timeout": 0}
        options.update(kwargs)
        return serial.serial_for_url("loop://", **options)

    return factory
