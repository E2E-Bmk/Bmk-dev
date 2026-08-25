"""Trusted support shared by the DVC scorer and fixed gate tests."""

from __future__ import annotations

import os
from pathlib import Path
import sys


class ScorerInfrastructureError(RuntimeError):
    """An environmental failure that invalidates scoring rather than missing a root."""


def require_dvc_console() -> str:
    """Return the scorer-attested console beside the exact active interpreter."""

    configured = os.environ.get("DVC_EXPECTED_CONSOLE")
    if not configured:
        raise ScorerInfrastructureError(
            "scorer did not provide DVC_EXPECTED_CONSOLE"
        )
    expected = Path(configured).resolve()
    sibling = Path(sys.executable).resolve().with_name(
        "dvc.exe" if os.name == "nt" else "dvc"
    )
    if expected != sibling:
        raise ScorerInfrastructureError(
            "attested DVC console is not beside the active interpreter"
        )
    if not expected.is_file():
        raise ScorerInfrastructureError(
            f"attested DVC console is missing: {expected}"
        )
    return os.fspath(expected)

