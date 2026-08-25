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
RUNTIME = (GATE / "../../.venv-reference/Lib/site-packages").resolve()


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _root_record(root_id: str) -> tuple[str, str]:
    root_map = json.loads((GATE / "ROOT-MAP.json").read_text(encoding="utf-8"))
    if root_id.startswith("A"):
        lane = "atomic"
        module = "tests.test_atomic"
    else:
        lane = "composition"
        module = "tests.test_composition"
    matches = [row for row in root_map[lane] if row["id"] == root_id]
    if len(matches) != 1:
        raise KeyError(f"unknown root: {root_id}")
    return module, str(matches[0]["function"])


def main() -> int:
    if len(sys.argv) != 3:
        print(json.dumps({"valid": False, "error": "usage: run_root.py ROOT CANDIDATE"}))
        return 2
    root_id = sys.argv[1]
    candidate = Path(sys.argv[2]).resolve()
    if not (candidate / "cookiecutter" / "__init__.py").is_file():
        print(json.dumps({"valid": False, "root": root_id, "error": "candidate package is absent"}))
        return 2

    sys.path.insert(0, str(GATE))
    sys.path.insert(1, str(candidate))
    if RUNTIME.is_dir():
        sys.path.insert(2, str(RUNTIME))
    stdout = io.StringIO()
    stderr = io.StringIO()
    started = time.perf_counter()
    payload: dict[str, object] = {"root": root_id, "valid": True, "passed": False, "phase": "setup"}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            if os.environ.get("COOKIECUTTER_SYNTHETIC_PROFILE"):
                from reference_patch import apply

                apply()
            elif os.environ.get("COOKIECUTTER_SYNTHETIC_API_SCAFFOLD") == "1":
                from reference_api_scaffold import apply

                apply()
            module_name, function_name = _root_record(root_id)
            module = importlib.import_module(module_name)
            function = getattr(module, function_name)
            if inspect.signature(function).parameters:
                raise TypeError("root function must have zero parameters")
            payload["phase"] = "call"
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
        invalid_types = (ImportError, AttributeError, TypeError, NotImplementedError, Warning)
        if payload["phase"] != "call":
            payload["valid"] = False
            payload["infrastructure_error"] = "root did not reach call phase"
        elif isinstance(exc, invalid_types):
            payload["valid"] = False
            payload["infrastructure_error"] = f"invalid failure type: {type(exc).__name__}"

    package = sys.modules.get("cookiecutter")
    imported = getattr(package, "__file__", None) if package else None
    payload["cookiecutter_import"] = str(Path(imported).resolve()) if imported else None
    payload["candidate_contained"] = bool(imported and _inside(Path(imported), candidate))
    escaped = []
    for name, module in sys.modules.items():
        if name == "cookiecutter" or not name.startswith("cookiecutter."):
            continue
        location = getattr(module, "__file__", None)
        if location and not _inside(Path(location), candidate):
            escaped.append({"module": name, "path": str(Path(location).resolve())})
    payload["escaped_cookiecutter_modules"] = escaped
    if imported and not payload["candidate_contained"]:
        payload["valid"] = False
        payload["infrastructure_error"] = "cookiecutter import escaped candidate tree"
    elif escaped:
        payload["valid"] = False
        payload["infrastructure_error"] = "cookiecutter submodule import escaped candidate tree"
    payload["stdout"] = stdout.getvalue()
    payload["stderr"] = stderr.getvalue()
    payload["duration_seconds"] = round(time.perf_counter() - started, 6)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
