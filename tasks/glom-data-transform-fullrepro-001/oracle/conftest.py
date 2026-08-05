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
        help="Path containing the glom package under test",
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
        if name == "glom" or name.startswith("glom."):
            sys.modules.pop(name, None)
    sys.path.insert(0, str(target_root))


@pytest.fixture
def nested_record():
    return {
        "profile": {
            "name": "Ada",
            "scores": [4, 7, 9],
            "contact": {"email": "ada@example.test"},
        },
        "events": [
            {"kind": "login", "ok": True},
            {"kind": "export", "ok": False},
        ],
    }


@pytest.fixture
def object_record():
    class Account:
        def __init__(self):
            self.name = "Ada"
            self.meta = {"tier": "pro"}
            self.values = [2, 5, 8]

        def label(self, prefix=""):
            return prefix + self.name

    return Account()
