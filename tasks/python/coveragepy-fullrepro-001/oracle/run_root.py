"""Run one pre-registered gate root in a fresh Python process."""

from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
import os
import sys
import traceback
import warnings
from pathlib import Path
from typing import Any


GATE_ROOT = Path(__file__).resolve().parent
TEST_MODULES = {
    "A": "tests.test_atomic",
    "I": "tests.test_integration",
    "S": "tests.test_system",
}


def _contained(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _provenance(candidate: Path) -> dict[str, Any]:
    origins: dict[str, str] = {}
    escaped: dict[str, str] = {}
    for name, module in sorted(sys.modules.items()):
        if name != "coverage" and not name.startswith("coverage."):
            continue
        filename = getattr(module, "__file__", None)
        if not filename:
            continue
        resolved = Path(filename).resolve()
        origins[name] = str(resolved)
        if not _contained(resolved, candidate):
            escaped[name] = str(resolved)
    return {"origins": origins, "escaped": escaped}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root_id")
    parser.add_argument("candidate")
    parser.add_argument("--reference-patch", action="store_true")
    args = parser.parse_args()

    root_id = args.root_id.upper()
    candidate = Path(args.candidate).resolve()
    phase = "bootstrap"
    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()
    warning_rows: list[dict[str, str]] = []
    caught_records: list[Any] = []
    status = "invalid"
    error_type = ""
    error_message = ""
    error_traceback = ""

    try:
        if root_id[:1] not in TEST_MODULES:
            raise ValueError(f"unknown root id: {root_id}")
        sys.path[:] = [str(GATE_ROOT), str(candidate)] + [
            entry for entry in sys.path if entry not in {str(candidate), str(GATE_ROOT), ""}
        ]
        os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
        inherited_pythonpath = os.environ.get("PYTHONPATH")
        child_paths = [str(candidate)]
        if args.reference_patch:
            child_paths.insert(0, str(GATE_ROOT))
            os.environ["SYNTHETIC_REFERENCE_PATCH"] = "1"
            os.environ["SYNTHETIC_EVALUATOR_ROOT"] = str(GATE_ROOT)
        os.environ["PYTHONPATH"] = os.pathsep.join(child_paths) + (os.pathsep + inherited_pythonpath if inherited_pythonpath else "")
        os.environ["SYNTHETIC_CANDIDATE_ROOT"] = str(candidate)
        for name in list(sys.modules):
            if name == "coverage" or name.startswith("coverage."):
                del sys.modules[name]
        phase = "candidate_import"
        coverage_module = importlib.import_module("coverage")
        origin = Path(coverage_module.__file__).resolve()
        if not _contained(origin, candidate):
            raise RuntimeError(f"coverage imported outside candidate: {origin}")
        if args.reference_patch:
            from reference_patch import activate

            activate(candidate)
        phase = "root_import"
        module = importlib.import_module(TEST_MODULES[root_id[0]])
        expected_prefix = f"test_{root_id.lower()}_"
        functions = [
            value
            for name, value in vars(module).items()
            if name.startswith(expected_prefix) and callable(value)
        ]
        if len(functions) != 1:
            raise RuntimeError(f"expected one callable for {root_id}, found {len(functions)}")
        phase = "call"
        with warnings.catch_warnings(record=True) as caught_records:
            warnings.simplefilter("always")
            with contextlib.redirect_stdout(captured_stdout), contextlib.redirect_stderr(captured_stderr):
                functions[0]()
        status = "passed"
    except BaseException as exc:
        status = "failed" if phase == "call" else "invalid"
        error_type = type(exc).__name__
        error_message = str(exc)
        error_traceback = traceback.format_exc()

    warning_rows = [
        {
            "category": row.category.__name__,
            "message": str(row.message),
            "filename": str(row.filename),
        }
        for row in caught_records
    ]

    provenance = _provenance(candidate)
    if provenance["escaped"]:
        status = "invalid"
        if not error_message:
            error_type = "ContainmentError"
            error_message = "coverage modules escaped candidate containment"
    if warning_rows:
        status = "invalid"
        if not error_message:
            error_type = "UnexpectedWarning"
            error_message = "; ".join(row["message"] for row in warning_rows)

    payload = {
        "root_id": root_id,
        "status": status,
        "phase": phase,
        "error_type": error_type,
        "error_message": error_message,
        "traceback": error_traceback,
        "warnings": warning_rows,
        "stdout": captured_stdout.getvalue(),
        "stderr": captured_stderr.getvalue(),
        "provenance": provenance,
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if status in {"passed", "failed"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
