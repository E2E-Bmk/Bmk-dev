from __future__ import annotations

import importlib
import os
from pathlib import Path
import sys


def pytest_configure(config) -> None:
    profile = os.environ.get("GRIFFE_V3_PROFILE", "anchor")
    gate = Path(__file__).resolve().parents[1]
    if profile == "reference":
        root = gate / "reference-overlay"
        module_name = "griffe_v3_workflow"
    elif profile in {"clean", "dummy"}:
        root = gate / "clean-api-scaffold"
        module_name = "griffe_v3_scaffold"
    elif profile == "anchor":
        return
    else:
        raise RuntimeError(f"unknown GRIFFE_V3_PROFILE: {profile}")
    sys.path.insert(0, str(root))
    griffe = importlib.import_module("griffe")
    importlib.import_module(module_name).install(griffe)
