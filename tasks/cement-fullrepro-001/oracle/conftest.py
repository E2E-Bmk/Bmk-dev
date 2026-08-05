from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


class TargetOnlyCementFinder:
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "cement" or fullname.startswith("cement."):
            raise ModuleNotFoundError("cement is not available from the selected target root")
        return None


def pytest_addoption(parser):
    parser.addoption(
        "--target-root",
        action="store",
        default=os.environ.get("TARGET_ROOT"),
        help="Path containing the cement package under test",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): atomic behaviors required by an integration test",
    )


def pytest_sessionstart(session):
    configured_root = session.config.getoption("--target-root")
    if configured_root is None:
        return

    target_root = Path(configured_root).resolve()
    for name in list(sys.modules):
        if name == "cement" or name.startswith("cement."):
            sys.modules.pop(name, None)
    sys.path.insert(0, str(target_root))
    if not (target_root / "cement").is_dir():
        sys.meta_path.insert(0, TargetOnlyCementFinder())
