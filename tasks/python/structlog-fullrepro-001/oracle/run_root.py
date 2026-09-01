from __future__ import annotations

import contextlib
import importlib
import inspect
import io
import json
import os
import sys
import tempfile
import time
import traceback
import warnings
from pathlib import Path


GATE = Path(__file__).resolve().parent
RUNTIME = (GATE / "runtime-site").resolve()
OVERLAY_PROFILES = {"reference", "clean", "broad-generation-collapse", "broad-retry-collapse"}


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def root_module(root_id: str) -> str:
    native = {*(f"A{i:02d}" for i in range(1, 7)), *(f"I{i:02d}" for i in range(1, 5)), *(f"S{i:02d}" for i in range(1, 5))}
    if root_id in native:
        return "tests.test_native_controls"
    if root_id.startswith("A"):
        return "tests.test_delivery_atomic"
    if root_id.startswith("I"):
        return "tests.test_delivery_integration"
    return "tests.test_delivery_system"


def install_profile(profile: str, structlog: object) -> None:
    if profile in {"reference", "broad-generation-collapse", "broad-retry-collapse"}:
        sys.path.insert(0, str(GATE / "reference-overlay"))
        importlib.import_module("structlog_delivery_reference").install(structlog, profile)
    elif profile == "clean":
        sys.path.insert(0, str(GATE / "clean-api-scaffold"))
        importlib.import_module("structlog_delivery_scaffold").install(structlog)
    elif profile in {"dummy", "source-blank-shallow", "anchor", "arbitrary"}:
        return
    else:
        raise RuntimeError(f"unknown profile: {profile}")


def main() -> int:
    if len(sys.argv) != 4:
        print(json.dumps({"valid": False, "error": "usage: run_root.py ROOT CANDIDATE PROFILE"}))
        return 2
    root_id, candidate_arg, profile = sys.argv[1:]
    candidate = Path(candidate_arg).resolve()
    payload: dict[str, object] = {"root": root_id, "valid": True, "passed": False, "phase": "setup", "profile": profile}
    stdout, stderr = io.StringIO(), io.StringIO()
    started = time.perf_counter()
    if not (candidate / "structlog" / "__init__.py").is_file():
        print(json.dumps({**payload, "valid": False, "error": "candidate structlog package is absent"}, sort_keys=True))
        return 0
    sys.path.insert(0, str(candidate))
    sys.path.insert(1, str(GATE))
    os.environ["SPEC2REPO_CANDIDATE_ROOT"] = str(candidate)
    os.environ["SPEC2REPO_STRUCTLOG_RUNTIME"] = str(RUNTIME)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            structlog = importlib.import_module("structlog")
            install_profile(profile, structlog)
            for loaded in [name for name in sys.modules if name == "tests" or name.startswith("tests.")]:
                del sys.modules[loaded]
            module = importlib.import_module(root_module(root_id))
            function = getattr(module, f"test_{root_id.lower()}")
            parameters = [item.name for item in inspect.signature(function).parameters.values()]
            if parameters != ["tmp_path"]:
                raise TypeError("root must request only evaluator-owned tmp_path")
            payload["phase"] = "call"
            parent = GATE / ".tmp" / "roots"
            parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=f"{root_id.lower()}-", dir=parent) as directory:
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    function(Path(directory))
        payload["passed"] = True
    except AssertionError as exc:
        payload.update(exception_type=type(exc).__name__, failure=str(exc), traceback=traceback.format_exc())
        if payload["phase"] != "call":
            payload.update(valid=False, infrastructure_error="assertion before semantic call")
    except BaseException as exc:
        payload.update(exception_type=type(exc).__name__, failure=str(exc), traceback=traceback.format_exc())
        if payload["phase"] != "call":
            payload.update(valid=False, infrastructure_error="root did not reach semantic call")
        elif isinstance(exc, Warning):
            payload.update(valid=False, infrastructure_error=f"warning escaped semantic call: {type(exc).__name__}")
    imported = sys.modules.get("structlog")
    origin = getattr(imported, "__file__", None)
    payload["structlog_import"] = str(Path(origin).resolve()) if origin else None
    payload["candidate_contained"] = bool(origin and inside(Path(origin), candidate))
    escaped: list[dict[str, str]] = []
    runtime_modules: list[dict[str, str]] = []
    for name, module in list(sys.modules.items()):
        if name != "structlog" and not name.startswith("structlog."):
            continue
        location = getattr(module, "__file__", None)
        if not location or inside(Path(location), candidate):
            continue
        path = Path(location).resolve()
        if profile in OVERLAY_PROFILES and name == "structlog.delivery" and inside(path, GATE):
            continue
        if profile in {"source-blank-shallow", "anchor", "arbitrary"} and name != "structlog.delivery" and inside(path, RUNTIME):
            runtime_modules.append({"module": name, "path": str(path)})
            continue
        escaped.append({"module": name, "path": str(path)})
    payload["declared_runtime_modules"] = sorted(runtime_modules, key=lambda row: row["module"])
    payload["escaped_structlog_modules"] = escaped
    if not payload["candidate_contained"] or escaped:
        payload.update(valid=False, infrastructure_error="structlog import escaped candidate or declared runtime")
    if profile == "source-blank-shallow" and not runtime_modules:
        payload.update(valid=False, infrastructure_error="source-blank wrapper did not use declared runtime")
    payload.update(stdout=stdout.getvalue(), stderr=stderr.getvalue(), duration_seconds=round(time.perf_counter() - started, 6))
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
