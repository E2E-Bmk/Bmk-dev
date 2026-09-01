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


def inside(path, root):
    try: Path(path).resolve().relative_to(Path(root).resolve()); return True
    except ValueError: return False


def root_module(root_id):
    native = {*(f"A{i:02d}" for i in range(1, 9)), *(f"I{i:02d}" for i in range(1, 5)), "S01", "S02"}
    if root_id in native: return "tests.test_native_controls"
    if root_id.startswith("A"): return "tests.test_workspace_atomic"
    if root_id.startswith("I"): return "tests.test_workspace_integration"
    return "tests.test_workspace_system"


def install_profile(profile, traitlets):
    if profile == "reference":
        sys.path.insert(0, str(GATE / "reference-overlay")); importlib.import_module("traitlets_v6_workspace").install(traitlets)
    elif profile == "clean":
        sys.path.insert(0, str(GATE / "clean-api-scaffold")); importlib.import_module("traitlets_v6_scaffold").install(traitlets)
    elif profile in {"broad-eager", "broad-delivery-blind"}:
        sys.path.insert(0, str(GATE / "reference-overlay")); importlib.import_module("traitlets_v6_controls").install(traitlets, profile)
    elif profile in {"dummy", "shallow", "anchor", "arbitrary"}:
        return
    else:
        raise RuntimeError(f"unknown profile {profile!r}")


def main():
    if len(sys.argv) != 4:
        print(json.dumps({"valid": False, "error": "usage: run_root.py ROOT CANDIDATE PROFILE"})); return 2
    root_id, candidate_arg, profile = sys.argv[1:]; candidate = Path(candidate_arg).resolve()
    payload = {"root": root_id, "valid": True, "passed": False, "phase": "setup", "profile": profile}
    stdout, stderr = io.StringIO(), io.StringIO(); started = time.perf_counter()
    if not (candidate / "traitlets" / "__init__.py").is_file():
        print(json.dumps({**payload, "valid": False, "error": "candidate traitlets package absent"}, sort_keys=True)); return 0
    sys.path.insert(0, str(candidate)); sys.path.insert(1, str(GATE)); os.environ["SPEC2REPO_CANDIDATE_ROOT"] = str(candidate)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error"); traitlets = importlib.import_module("traitlets"); install_profile(profile, traitlets)
            sys.path.insert(0, str(GATE))
            for loaded in [name for name in sys.modules if name == "tests" or name.startswith("tests.")]: del sys.modules[loaded]
            module = importlib.import_module(root_module(root_id)); function = getattr(module, f"test_{root_id.lower()}")
            if [item.name for item in inspect.signature(function).parameters.values()] != ["tmp_path"]: raise TypeError("invalid root signature")
            payload["phase"] = "call"; parent = GATE / ".tmp" / "roots"; parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=f"{root_id.lower()}-", dir=parent) as directory:
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr): function(Path(directory))
        payload["passed"] = True
    except AssertionError as exc:
        payload.update(exception_type=type(exc).__name__, failure=str(exc), traceback=traceback.format_exc())
        if payload["phase"] != "call": payload.update(valid=False, infrastructure_error="assertion before semantic call")
    except BaseException as exc:
        payload.update(exception_type=type(exc).__name__, failure=str(exc), traceback=traceback.format_exc())
        if payload["phase"] != "call" or isinstance(exc, Warning):
            payload.update(valid=False, infrastructure_error="root failed before a valid semantic result")
    imported = sys.modules.get("traitlets"); origin = getattr(imported, "__file__", None)
    payload["traitlets_import"] = str(Path(origin).resolve()) if origin else None
    payload["candidate_contained"] = bool(origin and inside(origin, candidate))
    runtime = (GATE / "runtime-site").resolve(); overlay_allowed = profile in {"reference", "clean", "broad-eager", "broad-delivery-blind"}
    escaped = []
    for name, module in list(sys.modules.items()):
        if name != "traitlets" and not name.startswith("traitlets."): continue
        location = getattr(module, "__file__", None)
        if location and not inside(location, candidate):
            if overlay_allowed and name == "traitlets.workspace": continue
            if inside(location, runtime) and name != "traitlets.workspace": continue
            escaped.append({"module": name, "path": str(Path(location).resolve())})
    workspace_module = sys.modules.get("traitlets.workspace"); workspace_origin = getattr(workspace_module, "__file__", None)
    payload["workspace_import"] = str(Path(workspace_origin).resolve()) if workspace_origin else "overlay"
    payload["escaped_traitlets_modules"] = escaped
    if not payload["candidate_contained"] or escaped: payload.update(valid=False, infrastructure_error="traitlets import escaped candidate/runtime roots")
    payload.update(stdout=stdout.getvalue(), stderr=stderr.getvalue(), duration_seconds=round(time.perf_counter() - started, 6))
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True)); return 0


if __name__ == "__main__": raise SystemExit(main())
