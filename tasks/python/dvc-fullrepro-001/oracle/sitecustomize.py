"""Trusted bootstrap for DVC v3 reference subprocesses."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path


configured = os.environ.get("DVC_V3_REFERENCE_PATCH")
if configured:
    patch_path = Path(configured).resolve()
    if not patch_path.is_file():
        raise RuntimeError(f"DVC v3 reference patch is missing: {patch_path}")
    spec = importlib.util.spec_from_file_location(
        "dvc_v3_reference_patch_bootstrap", patch_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load DVC v3 reference patch: {patch_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.apply()
