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
CONFIG = json.loads((GATE / "SCORER-CONFIG.json").read_text(encoding="utf-8"))


def inside(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def root_module(root_id: str) -> str:
    native = {*(f"A{i:02d}" for i in range(1, 9)), *(f"I{i:02d}" for i in range(1, 5)), "S01", "S02"}
    if root_id in native:
        return "tests.test_native_controls"
    if root_id.startswith("A"):
        return "tests.test_recovery_atomic"
    if root_id.startswith("I"):
        return "tests.test_recovery_integration"
    return "tests.test_recovery_system"


def main() -> int:
    if len(sys.argv) != 4:
        print(json.dumps({"valid": False, "error": "usage: run_root.py ROOT CANDIDATE PROFILE"}))
        return 2
    root_id, candidate_arg, profile = sys.argv[1:]
    candidate = Path(candidate_arg).resolve()
    record: dict[str, object] = {"root": root_id, "valid": True, "passed": False, "phase": "setup", "profile": profile}
    stdout, stderr = io.StringIO(), io.StringIO()
    started = time.perf_counter()
    if not (candidate / "vcr" / "__init__.py").is_file():
        print(json.dumps({**record, "valid": False, "error": "candidate vcr package is absent"}, sort_keys=True))
        return 0
    runtime = Path(CONFIG["reference_package_root"]).resolve()
    dependency_site = Path(CONFIG["dependency_site"]).resolve()
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(candidate), str(GATE), str(runtime), str(dependency_site)]
    os.environ["SPEC2REPO_CANDIDATE_ROOT"] = str(candidate)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            vcr_module = importlib.import_module("vcr")
            for name in [value for value in sys.modules if value == "tests" or value.startswith("tests.")]:
                del sys.modules[name]
            module = importlib.import_module(root_module(root_id))
            function = getattr(module, f"test_{root_id.lower()}")
            parameters = list(inspect.signature(function).parameters.values())
            if [item.name for item in parameters] != ["tmp_path"]:
                raise TypeError("decision function must request only evaluator-owned tmp_path")
            record["phase"] = "call"
            parent = GATE / ".tmp" / "roots"
            parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=f"{root_id.lower()}-", dir=parent) as directory:
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    function(Path(directory))
        record["passed"] = True
    except BaseException as exc:
        record.update(exception_type=type(exc).__name__, failure=str(exc), traceback=traceback.format_exc())
        if record["phase"] != "call":
            record.update(valid=False, infrastructure_error="decision did not reach semantic call")
        elif isinstance(exc, Warning):
            record.update(valid=False, infrastructure_error=f"warning escaped semantic call: {type(exc).__name__}")
        # Every non-warning candidate exception in call phase is a valid semantic false.
    imported = sys.modules.get("vcr")
    origin = getattr(imported, "__file__", None)
    record["vcr_import"] = str(Path(origin).resolve()) if origin else None
    record["candidate_contained"] = bool(origin and inside(Path(origin), candidate))
    escaped: list[dict[str, str]] = []
    origins: dict[str, str] = {}
    for name, module in list(sys.modules.items()):
        if name != "vcr" and not name.startswith("vcr."):
            continue
        location = getattr(module, "__file__", None)
        if not location:
            continue
        path = Path(location).resolve()
        if inside(path, candidate):
            origins[name] = "candidate://" + path.relative_to(candidate).as_posix()
        elif name != "vcr" and name != "vcr.workflow" and inside(path, runtime):
            origins[name] = "runtime://" + path.relative_to(runtime).as_posix()
        else:
            escaped.append({"module": name, "path": str(path)})
    record["vcr_origins"] = origins
    record["escaped_vcr_modules"] = escaped
    if not record["candidate_contained"] or escaped:
        record.update(valid=False, infrastructure_error="vcr import escaped candidate tree")
    record.update(stdout=stdout.getvalue(), stderr=stderr.getvalue(), duration_seconds=round(time.perf_counter() - started, 6))
    print(json.dumps(record, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
