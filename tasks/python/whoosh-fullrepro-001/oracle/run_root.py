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
CONFIG = json.loads((GATE / "SCORER-CONFIG.json").read_text(encoding="utf-8"))
RUNTIME = Path(CONFIG["reference_package_root"]).resolve()
COMPATIBILITY_MODULES = (
    "whoosh.fields",
    "whoosh.lang.paicehusk",
    "whoosh.lang.porter2",
)


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def root_module(root_id: str) -> str:
    if root_id.startswith("A"): return "tests.test_atomic"
    if root_id.startswith("I"): return "tests.test_integration"
    if root_id.startswith("S"): return "tests.test_system"
    raise ValueError(f"unknown root: {root_id}")


def install_profile(profile: str, whoosh: object) -> set[Path]:
    if profile not in {"reference", "clean", "dummy", "broad-owner-collapse", "broad-eager-visibility", "shallow-workflow", "arbitrary"}:
        raise RuntimeError(f"unknown profile: {profile}")
    return set()


def main() -> int:
    if len(sys.argv) != 4:
        print(json.dumps({"valid": False, "error": "usage: run_root.py ROOT CANDIDATE PROFILE"}))
        return 2
    root_id, candidate_arg, profile = sys.argv[1:]
    candidate = Path(candidate_arg).resolve()
    payload: dict[str, object] = {"root": root_id, "profile": profile, "valid": True, "passed": False, "phase": "setup"}
    stdout, stderr = io.StringIO(), io.StringIO()
    started = time.perf_counter()
    allowed_overlay: set[Path] = set()
    sys.dont_write_bytecode = True
    if not (candidate / "whoosh" / "__init__.py").is_file():
        print(json.dumps({**payload, "valid": False, "infrastructure_error": "candidate whoosh package is absent"}, sort_keys=True))
        return 0
    sys.path.insert(0, str(candidate)); sys.path.insert(1, str(RUNTIME)); sys.path.insert(2, str(GATE))
    os.environ["SPEC2REPO_CANDIDATE_ROOT"] = str(candidate)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            whoosh = importlib.import_module("whoosh")
        if profile != "dummy":
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                warnings.filterwarnings("ignore", message=r"invalid escape sequence .*", category=SyntaxWarning)
                for module_name in COMPATIBILITY_MODULES:
                    module = importlib.import_module(module_name)
                    module_origin = Path(module.__file__).resolve()
                    if not inside(module_origin, RUNTIME):
                        raise RuntimeError(f"compatibility module escaped declared runtime: {module_name}")
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            allowed_overlay = install_profile(profile, whoosh)
            for loaded in [name for name in sys.modules if name == "tests" or name.startswith("tests.")]:
                del sys.modules[loaded]
            module = importlib.import_module(root_module(root_id))
            function = getattr(module, f"test_{root_id.lower()}")
            if [item.name for item in inspect.signature(function).parameters.values()] != ["tmp_path"]:
                raise TypeError("root must request only evaluator-owned tmp_path")
            payload["phase"] = "call"
            parent = GATE / ".tmp" / "roots"; parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=f"{root_id.lower()}-", dir=parent) as directory:
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    function(Path(directory))
        payload["passed"] = True
    except Warning as exc:
        payload.update(valid=False, exception_type=type(exc).__name__, failure=str(exc), traceback=traceback.format_exc(), infrastructure_error="warning during root execution")
    except BaseException as exc:
        payload.update(exception_type=type(exc).__name__, failure=str(exc), traceback=traceback.format_exc())
        if payload["phase"] != "call":
            payload.update(valid=False, infrastructure_error="root did not reach semantic call")

    imported = sys.modules.get("whoosh")
    origin = getattr(imported, "__file__", None)
    payload["whoosh_import"] = "candidate://" + Path(origin).resolve().relative_to(candidate).as_posix() if origin and inside(Path(origin), candidate) else ("runtime://" + Path(origin).resolve().relative_to(RUNTIME).as_posix() if origin and inside(Path(origin), RUNTIME) else (str(Path(origin).resolve()) if origin else None))
    payload["candidate_contained"] = bool(origin and inside(Path(origin), candidate))
    escaped: list[dict[str, str]] = []
    module_origins: dict[str, str] = {}
    for name, module in list(sys.modules.items()):
        if name != "whoosh" and not name.startswith("whoosh."):
            continue
        location = getattr(module, "__file__", None)
        if not location:
            continue
        resolved = Path(location).resolve()
        if inside(resolved, candidate):
            module_origins[name] = "candidate://" + resolved.relative_to(candidate).as_posix()
        elif inside(resolved, RUNTIME):
            module_origins[name] = "runtime://" + resolved.relative_to(RUNTIME).as_posix()
        else:
            escaped.append({"module": name, "path": str(resolved)})
    payload["whoosh_module_origins"] = dict(sorted(module_origins.items()))
    payload["escaped_whoosh_modules"] = escaped
    invalid_candidate_modules = sorted(
        name for name, label in module_origins.items()
        if label.startswith("candidate://") and name not in {"whoosh", "whoosh.workflow"}
    )
    payload["invalid_candidate_runtime_overrides"] = invalid_candidate_modules
    if not payload["candidate_contained"] or escaped or invalid_candidate_modules:
        payload.update(valid=False, infrastructure_error="whoosh import escaped candidate plus declared-runtime provenance closure")
    payload.update(stdout=stdout.getvalue(), stderr=stderr.getvalue(), duration_seconds=round(time.perf_counter() - started, 6))
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
