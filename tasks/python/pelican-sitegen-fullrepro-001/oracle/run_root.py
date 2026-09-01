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
CONFIG = json.loads((GATE / "SCORER-CONFIG.json").read_text(encoding="utf-8"))
RUNTIME = (GATE / CONFIG["dependency_site"]).resolve()
HARD_INVALID_EXCEPTIONS = (
    ImportError,
    ModuleNotFoundError,
    AttributeError,
    TypeError,
    NotImplementedError,
    Warning,
)


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


def _candidate_traceback_functions(exc: BaseException, candidate: Path) -> list[str]:
    functions: list[str] = []
    traceback_cursor = exc.__traceback__
    while traceback_cursor is not None:
        frame = traceback_cursor.tb_frame
        try:
            filename = Path(frame.f_code.co_filename)
            if filename.is_absolute() and _inside(filename, candidate):
                functions.append(frame.f_code.co_name)
        except (OSError, RuntimeError, ValueError):
            pass
        traceback_cursor = traceback_cursor.tb_next
    return functions


def _candidate_declared_exception(exc: BaseException, candidate: Path) -> bool:
    module = sys.modules.get(type(exc).__module__)
    location = getattr(module, "__file__", None) if module is not None else None
    if not location:
        return False
    try:
        return _inside(Path(location), candidate)
    except (OSError, RuntimeError, ValueError):
        return False


def classify_call_exception(exc: BaseException, root_id: str, candidate: Path) -> dict[str, object]:
    """Classify an exception after the scored semantic call has begun.

    The evaluator owns this boundary.  Candidate product behavior is a scored
    miss, while evaluator, import, public-shape, and execution failures remain
    invalid evidence.  IndexError is deliberately narrower because an index
    operation in the oracle is never candidate behavior.
    """
    candidate_functions = _candidate_traceback_functions(exc, candidate)
    declared = _candidate_declared_exception(exc, candidate)
    detail: dict[str, object] = {
        "exception_origin": "candidate-product" if candidate_functions or declared else "harness-or-evaluator",
        "candidate_traceback_functions": candidate_functions,
        "candidate_declared_exception": declared,
    }
    if isinstance(exc, HARD_INVALID_EXCEPTIONS):
        detail["disposition"] = "infrastructure-invalid"
        detail["reason"] = "hard-invalid exception type"
        return detail
    if isinstance(exc, SystemExit):
        code = exc.code
        normal_code = isinstance(code, int) and not isinstance(code, bool) and code != 0
        if root_id in CONFIG["semantic_system_exit_roots"] and normal_code:
            detail["disposition"] = "semantic-failure"
            detail["exception_origin"] = "cli-contract"
            detail["reason"] = "normal CLI SystemExit during the declared CLI root"
        else:
            detail["disposition"] = "infrastructure-invalid"
            detail["reason"] = "SystemExit outside the declared CLI boundary"
        return detail
    if not isinstance(exc, Exception):
        detail["disposition"] = "infrastructure-invalid"
        detail["reason"] = "non-Exception control-flow escape"
        return detail
    if isinstance(exc, IndexError):
        allowed_calls = set(CONFIG["semantic_index_error_public_calls"])
        if candidate_functions and allowed_calls.intersection(candidate_functions):
            detail["disposition"] = "semantic-failure"
            detail["exception_origin"] = "candidate-product"
            detail["reason"] = "candidate-owned no-result/range public behavior"
        else:
            detail["disposition"] = "infrastructure-invalid"
            detail["reason"] = "IndexError was not raised by an allowed candidate public call"
        return detail
    if detail["candidate_declared_exception"] or candidate_functions:
        detail["disposition"] = "semantic-failure"
        detail["exception_origin"] = "candidate-product"
        detail["reason"] = "candidate-owned product behavior"
        return detail
    if isinstance(exc, KeyError):
        detail["disposition"] = "semantic-failure"
        detail["reason"] = "documented public record key is absent"
        return detail
    detail["disposition"] = "infrastructure-invalid"
    detail["reason"] = "exception is owned by the harness or evaluator"
    return detail


def main() -> int:
    if len(sys.argv) != 3:
        print(json.dumps({"valid": False, "error": "usage: run_root.py ROOT CANDIDATE"}))
        return 2
    root_id = sys.argv[1]
    candidate = Path(sys.argv[2]).resolve()
    if not (candidate / "pelican" / "__init__.py").is_file():
        print(json.dumps({"valid": False, "root": root_id, "error": "candidate package is absent"}))
        return 2

    sys.path.insert(0, str(GATE))
    sys.path.insert(1, str(candidate))
    if RUNTIME.is_dir():
        sys.path.insert(2, str(RUNTIME))
    stdout = io.StringIO()
    stderr = io.StringIO()
    started = time.perf_counter()
    payload: dict[str, object] = {
        "root": root_id,
        "valid": True,
        "passed": False,
        "phase": "setup",
        "semantic_call_reached": False,
    }
    profile = os.environ.get("PELICAN_SYNTHETIC_PROFILE", "none")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                if not RUNTIME.is_dir():
                    raise RuntimeError("qualified dependency site is absent")
                package = importlib.import_module("pelican")
                imported = getattr(package, "__file__", None)
                if not imported or not _inside(Path(imported), candidate):
                    raise ImportError("pelican package did not import from candidate tree")
                if profile != "none":
                    from reference_patch import apply

                    apply(profile)
                payload["phase"] = "collection"
                module_name, function_name = _root_record(root_id)
                module = importlib.import_module(module_name)
                function = getattr(module, function_name)
                if inspect.signature(function).parameters:
                    raise TypeError("root function must have zero parameters")
                payload["phase"] = "call"
                payload["semantic_call_reached"] = True
                function()
                payload["phase"] = "teardown"
        payload["phase"] = "call"
        payload["passed"] = True
    except AssertionError as exc:
        payload["failure"] = str(exc)
        payload["traceback"] = traceback.format_exc()
        if payload["phase"] != "call":
            payload["valid"] = False
            payload["infrastructure_error"] = f"assertion during {payload['phase']} phase"
    except BaseException as exc:
        payload["exception_type"] = type(exc).__name__
        payload["failure"] = str(exc)
        payload["traceback"] = traceback.format_exc()
        if payload["phase"] != "call":
            payload["valid"] = False
            payload["infrastructure_error"] = f"exception during {payload['phase']} phase"
        else:
            classification = classify_call_exception(exc, root_id, candidate)
            payload["exception_disposition"] = classification.pop("disposition")
            payload["exception_classification_reason"] = classification.pop("reason")
            payload.update(classification)
            if payload["exception_disposition"] == "infrastructure-invalid":
                payload["valid"] = False
                payload["infrastructure_error"] = (
                    f"invalid call-phase exception: {type(exc).__name__}: "
                    f"{payload['exception_classification_reason']}"
                )

    package = sys.modules.get("pelican")
    imported = getattr(package, "__file__", None) if package else None
    payload["pelican_import"] = str(Path(imported).resolve()) if imported else None
    payload["candidate_contained"] = bool(imported and _inside(Path(imported), candidate))
    escaped = []
    for name, module in sys.modules.items():
        if name == "pelican" or not name.startswith("pelican.") or (profile != "none" and name == "pelican.publication"):
            continue
        location = getattr(module, "__file__", None)
        if location and not _inside(Path(location), candidate):
            escaped.append({"module": name, "path": str(Path(location).resolve())})
    payload["escaped_pelican_modules"] = escaped
    if imported and not payload["candidate_contained"]:
        payload["valid"] = False
        payload["infrastructure_error"] = "pelican import escaped candidate tree"
    elif escaped:
        payload["valid"] = False
        payload["infrastructure_error"] = "pelican submodule import escaped candidate tree"
    payload["stdout"] = stdout.getvalue()
    payload["stderr"] = stderr.getvalue()
    payload["profile"] = profile
    payload["duration_seconds"] = round(time.perf_counter() - started, 6)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
