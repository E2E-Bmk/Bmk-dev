"""Activate the evaluator-only reference shim inside M1 CLI child processes."""

from __future__ import annotations

import os
from pathlib import Path


if os.environ.get("SYNTHETIC_REFERENCE_PATCH") == "1":
    from reference_patch import activate

    activate(Path(os.environ["SYNTHETIC_CANDIDATE_ROOT"]))
