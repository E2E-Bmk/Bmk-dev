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


GATE = Path(__file__).resolve().parent


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def root_record(root_id: str) -> tuple[str, str]:
    mapping = json.loads((GATE / "ROOT-MAP.json").read_text(encoding="utf-8"))
    if root_id.startswith("A"):
        lane, module = "atomic", "tests.test_atomic"
    elif root_id.startswith("C"):
        lane, module = "composition", "tests.test_composition"
    else:
        lane, module = "e2e", "tests.test_e2e"
    rows = [row for row in mapping[lane] if row["id"] == root_id]
    if len(rows) != 1:
        raise KeyError(f"unknown root: {root_id}")
    return module, rows[0]["function"]


def main() -> int:
    if len(sys.argv) != 3:
        print(json.dumps({"valid": False, "error": "usage: run_root.py ROOT CANDIDATE"}))
        return 2
    root_id = sys.argv[1]
    candidate = Path(sys.argv[2]).resolve()
    if not (candidate / "dateparser" / "__init__.py").is_file():
        print(json.dumps({"valid": False, "root": root_id, "error": "candidate package is absent"}))
        return 2

    sys.path.insert(0, str(GATE))
    sys.path.insert(1, str(candidate))
    stdout, stderr = io.StringIO(), io.StringIO()
    started = time.perf_counter()
    record: dict[str, object] = {"root": root_id, "valid": True, "passed": False, "phase": "call"}
    try:
        if os.environ.get("DATEPARSER_V4_REFERENCE_PATCH") == "1":
            from reference_patch import apply

            apply(os.environ.get("DATEPARSER_V4_CONTROL_MODE"))
        module_name, function_name = root_record(root_id)
        module = importlib.import_module(module_name)
        function = getattr(module, function_name)
        if inspect.signature(function).parameters:
            raise TypeError("root function must have zero parameters")
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            function()
        record["passed"] = True
    except AssertionError as exc:
        record["failure"] = str(exc)
        record["traceback"] = traceback.format_exc()
    except BaseException as exc:
        record["exception_type"] = type(exc).__name__
        record["failure"] = str(exc)
        record["traceback"] = traceback.format_exc()

    package = sys.modules.get("dateparser")
    package_file = getattr(package, "__file__", None) if package else None
    record["dateparser_import"] = str(Path(package_file).resolve()) if package_file else None
    record["candidate_contained"] = bool(package_file and inside(Path(package_file), candidate))
    escaped = []
    for name, module in sys.modules.items():
        if name != "dateparser" and not name.startswith("dateparser."):
            continue
        location = getattr(module, "__file__", None)
        if location and not inside(Path(location), candidate):
            escaped.append({"module": name, "path": str(Path(location).resolve())})
    record["escaped_dateparser_modules"] = escaped
    if package_file and not record["candidate_contained"]:
        record["valid"] = False
        record["infrastructure_error"] = "dateparser import escaped candidate tree"
    elif escaped:
        record["valid"] = False
        record["infrastructure_error"] = "dateparser submodule import escaped candidate tree"
    record["stdout"] = stdout.getvalue()
    record["stderr"] = stderr.getvalue()
    record["duration_seconds"] = round(time.perf_counter() - started, 6)
    print(json.dumps(record, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
