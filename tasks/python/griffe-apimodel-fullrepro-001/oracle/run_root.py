from __future__ import annotations

import contextlib
import importlib
import inspect
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import traceback
import warnings


GATE = Path(__file__).resolve().parent
ROOT_MAP = json.loads((GATE / "ROOT-MAP.json").read_text(encoding="utf-8"))


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _root_record(root_id: str) -> tuple[str, str]:
    rows = [*ROOT_MAP["atomic"], *ROOT_MAP["composition"]]
    match = [row for row in rows if row["id"] == root_id]
    if len(match) != 1:
        raise KeyError(root_id)
    if root_id <= "A08" or root_id <= "I06" and root_id.startswith("I"):
        module = "tests.test_native_controls"
    elif root_id.startswith("A"):
        module = "tests.test_workflow_atomic"
    elif root_id.startswith("I"):
        module = "tests.test_workflow_integration"
    else:
        module = "tests.test_workflow_system"
    return module, str(match[0]["function"])


def _install_profile(profile: str, griffe: object) -> None:
    if profile == "reference":
        sys.path.insert(0, str(GATE / "reference-overlay"))
        importlib.import_module("griffe_v3_workflow").install(griffe)
    elif profile == "clean":
        sys.path.insert(0, str(GATE / "clean-api-scaffold"))
        importlib.import_module("griffe_v3_scaffold").install(griffe)
    elif profile == "dummy":
        sys.path.insert(0, str(GATE / "dummy"))
        importlib.import_module("griffe_v3_dummy").install(griffe)
    elif profile in {"broad-snapshot-promotion", "broad-acknowledgement"}:
        sys.path.insert(0, str(GATE / "reference-overlay"))
        importlib.import_module("griffe_v3_controls").install(griffe, profile)
    elif profile == "classifier-call-type":
        # A07 imports and calls this public name only after setup completes.
        setattr(griffe, "get_parser", None)
    elif profile == "classifier-setup-type":
        raise TypeError("evaluator setup sentinel")
    elif profile not in {"anchor", "arbitrary"}:
        raise RuntimeError(f"unknown profile: {profile}")


def main() -> int:
    if len(sys.argv) != 4:
        print(json.dumps({"valid": False, "error": "usage: run_root.py ROOT CANDIDATE PROFILE"}))
        return 2
    root_id, candidate_arg, profile = sys.argv[1:]
    candidate = Path(candidate_arg).resolve()
    if not (candidate / "griffe" / "__init__.py").is_file():
        print(json.dumps({"valid": False, "root": root_id, "error": "candidate griffe package is absent"}))
        return 2

    sys.path.insert(0, str(GATE))
    sys.path.insert(1, str(candidate))
    stdout = io.StringIO()
    stderr = io.StringIO()
    started = time.perf_counter()
    payload: dict[str, object] = {
        "root": root_id,
        "valid": True,
        "passed": False,
        "phase": "setup",
        "profile": profile,
    }
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            griffe = importlib.import_module("griffe")
            _install_profile(profile, griffe)
            module_name, function_name = _root_record(root_id)
            module = importlib.import_module(module_name)
            function = getattr(module, function_name)
            parameters = list(inspect.signature(function).parameters.values())
            if parameters and [parameter.name for parameter in parameters] != ["tmp_path"]:
                raise TypeError("root may only request the evaluator-owned tmp_path")
            payload["phase"] = "call"
            temp_parent = GATE / ".tmp" / "roots"
            temp_parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=f"{root_id.lower()}-", dir=temp_parent) as directory:
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    if parameters:
                        function(Path(directory))
                    else:
                        function()
        payload["passed"] = True
    except AssertionError as exc:
        payload["failure"] = str(exc)
        payload["exception_type"] = type(exc).__name__
        payload["traceback"] = traceback.format_exc()
        if payload["phase"] != "call":
            payload["valid"] = False
            payload["infrastructure_error"] = "assertion before semantic call"
    except BaseException as exc:
        payload["exception_type"] = type(exc).__name__
        payload["failure"] = str(exc)
        payload["traceback"] = traceback.format_exc()
        # Setup is complete before ``phase`` becomes ``call``.  A public
        # AttributeError or TypeError at that point is an incomplete-product
        # outcome, not a runner failure.  Import, syntax, explicit-stub and
        # warning failures remain scoreless.
        hard_invalid = (ImportError, NotImplementedError, Warning, SyntaxError)
        if payload["phase"] != "call":
            payload["valid"] = False
            payload["infrastructure_error"] = "root did not reach semantic call"
        elif isinstance(exc, hard_invalid):
            payload["valid"] = False
            payload["infrastructure_error"] = f"invalid failure type: {type(exc).__name__}"

    package = sys.modules.get("griffe")
    imported = getattr(package, "__file__", None) if package else None
    payload["griffe_import"] = str(Path(imported).resolve()) if imported else None
    payload["candidate_contained"] = bool(imported and _inside(Path(imported), candidate))
    escaped: list[dict[str, str]] = []
    for name, module in sys.modules.items():
        if name != "griffe" and not name.startswith("griffe."):
            continue
        location = getattr(module, "__file__", None)
        if location and not _inside(Path(location), candidate):
            escaped.append({"module": name, "path": str(Path(location).resolve())})
    payload["escaped_griffe_modules"] = escaped
    if imported and not payload["candidate_contained"]:
        payload["valid"] = False
        payload["infrastructure_error"] = "griffe import escaped candidate tree"
    elif escaped:
        payload["valid"] = False
        payload["infrastructure_error"] = "griffe submodule import escaped candidate tree"
    payload["stdout"] = stdout.getvalue()
    payload["stderr"] = stderr.getvalue()
    payload["duration_seconds"] = round(time.perf_counter() - started, 6)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
