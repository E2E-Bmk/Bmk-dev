from __future__ import annotations

import contextlib
import importlib
import inspect
import io
import json
import os
from pathlib import Path
import sys
import time
import traceback
import warnings


GATE = Path(__file__).resolve().parent


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _root_record(root_id: str) -> tuple[str, str]:
    root_map = json.loads((GATE / "ROOT-MAP.json").read_text(encoding="utf-8"))
    lane = "atomic" if root_id.startswith("A") else "composition"
    matches = [row for row in root_map[lane] if row["id"] == root_id]
    if len(matches) != 1:
        raise KeyError(f"unknown root: {root_id}")
    module = "tests.test_atomic" if lane == "atomic" else "tests.test_composition"
    return module, matches[0]["function"]


def main() -> int:
    if len(sys.argv) != 3:
        print(json.dumps({"valid": False, "error": "usage: run_root.py ROOT CANDIDATE"}))
        return 2
    root_id = sys.argv[1]
    candidate = Path(sys.argv[2]).resolve()
    if not (candidate / "authlib" / "__init__.py").is_file():
        print(json.dumps({"valid": False, "root": root_id, "error": "candidate package is absent"}))
        return 2

    # Keep the private gate's own ``tests`` package authoritative.  GATE has no
    # top-level authlib package, so the candidate remains the first eligible
    # provider of the product package while a candidate-owned ``tests`` package
    # cannot shadow the frozen roots.
    sys.path.insert(0, str(GATE))
    sys.path.insert(1, str(candidate))
    stdout = io.StringIO()
    stderr = io.StringIO()
    started = time.perf_counter()
    payload: dict[str, object] = {
        "root": root_id,
        "valid": True,
        "passed": False,
        "phase": "call",
    }
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=r"authlib\.jose module is deprecated, please use joserfc instead\..*",
                category=DeprecationWarning,
            )
            if os.environ.get("AUTHLIB_SYNTHETIC_REFERENCE_PATCH") == "1":
                from reference_patch import apply

                apply()
            module_name, function_name = _root_record(root_id)
            module = importlib.import_module(module_name)
            function = getattr(module, function_name)
            if inspect.signature(function).parameters:
                raise TypeError("root function must have zero parameters")
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                function()
        payload["passed"] = True
    except AssertionError as exc:
        payload["failure"] = str(exc)
        payload["traceback"] = traceback.format_exc()
    except BaseException as exc:
        payload["exception_type"] = type(exc).__name__
        payload["failure"] = str(exc)
        payload["traceback"] = traceback.format_exc()

    authlib_module = sys.modules.get("authlib")
    imported = getattr(authlib_module, "__file__", None) if authlib_module else None
    payload["authlib_import"] = str(Path(imported).resolve()) if imported else None
    payload["candidate_contained"] = bool(imported and _inside(Path(imported), candidate))
    escaped_modules = []
    for name, module in sys.modules.items():
        if name == "authlib" or not name.startswith("authlib."):
            continue
        location = getattr(module, "__file__", None)
        if location and not _inside(Path(location), candidate):
            escaped_modules.append({"module": name, "path": str(Path(location).resolve())})
    payload["escaped_authlib_modules"] = escaped_modules
    if imported and not payload["candidate_contained"]:
        payload["valid"] = False
        payload["infrastructure_error"] = "authlib import escaped candidate tree"
    elif escaped_modules:
        payload["valid"] = False
        payload["infrastructure_error"] = "authlib submodule import escaped candidate tree"
    payload["stdout"] = stdout.getvalue()
    payload["stderr"] = stderr.getvalue()
    payload["duration_seconds"] = round(time.perf_counter() - started, 6)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
