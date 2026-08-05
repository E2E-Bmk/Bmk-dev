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
        help="Path containing the pypika package under test",
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
        if name == "pypika" or name.startswith("pypika."):
            sys.modules.pop(name, None)
    sys.path.insert(0, str(target_root))


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


@pytest.fixture
def sql():
    return normalize_sql


@pytest.fixture
def tables():
    import pypika

    return pypika.Table("users"), pypika.Table("orders"), pypika.Table("products")
