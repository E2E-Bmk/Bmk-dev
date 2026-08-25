from __future__ import annotations
import contextlib, importlib, inspect, io, json, os, sys, tempfile, time, traceback, warnings
from pathlib import Path

GATE = Path(__file__).resolve().parent
CONFIG = json.loads((GATE / "SCORER-CONFIG.json").read_text(encoding="utf-8"))
INTERPRETER_BASELINE = frozenset(sys.modules)

def inside(path: Path, root: Path) -> bool:
    try: path.resolve().relative_to(root.resolve()); return True
    except ValueError: return False

def root_module(root_id: str) -> str:
    native = {*(f"A{i:02d}" for i in range(1, 9)), *(f"I{i:02d}" for i in range(1, 5)), "S01", "S02"}
    if root_id in native: return "tests.test_native_controls"
    if root_id.startswith("A"): return "tests.test_workflow_atomic"
    if root_id.startswith("I"): return "tests.test_workflow_integration"
    return "tests.test_workflow_system"

def classify_failure(payload: dict[str, object], exc: BaseException) -> None:
    if payload["phase"] != "call":
        payload.update(valid=False, infrastructure_error="root did not reach semantic call")
    elif isinstance(exc, Warning):
        payload.update(valid=False, infrastructure_error=f"unexpected warning during semantic call: {type(exc).__name__}")

def install_profile(profile: str, astroid: object) -> None:
    if profile == "reference":
        sys.path.insert(0, str(GATE / "reference-overlay")); importlib.import_module("astroid_v2_workflow").install(astroid)
    elif profile == "clean":
        sys.path.insert(0, str(GATE / "clean-api-scaffold")); importlib.import_module("astroid_v2_scaffold").install(astroid)
    elif profile in {"broad-owner-collapse", "broad-ack-is-delivery"}:
        sys.path.insert(0, str(GATE / "reference-overlay")); importlib.import_module("astroid_v2_controls").install(astroid, profile)
    elif profile in {"dummy", "shallow-surface", "anchor", "arbitrary"}: return
    else: raise RuntimeError(f"unknown profile: {profile}")

def main() -> int:
    if len(sys.argv) != 4:
        print(json.dumps({"valid": False, "error": "usage: run_root.py ROOT CANDIDATE PROFILE"})); return 2
    root_id, candidate_arg, profile = sys.argv[1:]; candidate = Path(candidate_arg).resolve()
    payload: dict[str, object] = {"root": root_id, "valid": True, "passed": False, "phase": "setup", "profile": profile}
    stdout, stderr = io.StringIO(), io.StringIO(); started = time.perf_counter()
    if not (candidate / "astroid" / "__init__.py").is_file():
        print(json.dumps({**payload, "valid": False, "error": "candidate astroid package is absent"}, sort_keys=True)); return 0
    sys.path.insert(0, str(candidate)); sys.path.insert(1, str(GATE)); os.environ["SPEC2REPO_CANDIDATE_ROOT"] = str(candidate)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error"); astroid = importlib.import_module("astroid"); install_profile(profile, astroid)
            importlib.import_module("astroid.workflow")
            sys.path.insert(0, str(GATE))
            for loaded in [name for name in sys.modules if name == "tests" or name.startswith("tests.")]:
                del sys.modules[loaded]
            module = importlib.import_module(root_module(root_id)); function = getattr(module, f"test_{root_id.lower()}")
            if [item.name for item in inspect.signature(function).parameters.values()] != ["tmp_path"]: raise TypeError("root must request only evaluator-owned tmp_path")
            payload["phase"] = "call"; parent = GATE / ".tmp" / "roots"; parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=f"{root_id.lower()}-", dir=parent) as directory:
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr): function(Path(directory))
        payload["passed"] = True
    except AssertionError as exc:
        payload.update(exception_type=type(exc).__name__, failure=str(exc), traceback=traceback.format_exc())
        if payload["phase"] != "call": payload.update(valid=False, infrastructure_error="assertion before semantic call")
    except BaseException as exc:
        payload.update(exception_type=type(exc).__name__, failure=str(exc), traceback=traceback.format_exc())
        classify_failure(payload, exc)
    imported = sys.modules.get("astroid"); origin = getattr(imported, "__file__", None)
    payload["astroid_import"] = str(Path(origin).resolve()) if origin else None; payload["candidate_contained"] = bool(origin and inside(Path(origin), candidate))
    escaped: list[dict[str, str]] = []; overlay_allowed = profile in {"reference", "clean", "broad-owner-collapse", "broad-ack-is-delivery"}
    for name, module in list(sys.modules.items()):
        if name != "astroid" and not name.startswith("astroid."): continue
        location = getattr(module, "__file__", None)
        if location and not inside(Path(location), candidate):
            if overlay_allowed and name == "astroid.workflow": continue
            escaped.append({"module": name, "path": str(Path(location).resolve())})
    payload["escaped_astroid_modules"] = escaped
    if not payload["candidate_contained"] or escaped: payload.update(valid=False, infrastructure_error="astroid import escaped candidate tree")
    dependency_root = Path(CONFIG["dependency_site"]).resolve()
    stdlib_root = Path(os.__file__).resolve().parent
    stdlib_dlls = Path(sys.base_prefix).resolve() / "DLLs"
    declared_dependencies: list[dict[str, str]] = []
    undeclared_dependencies: list[dict[str, str]] = []
    for name, module in list(sys.modules.items()):
        if name in INTERPRETER_BASELINE:
            continue
        location = getattr(module, "__file__", None)
        if not location:
            continue
        path = Path(location).resolve()
        if inside(path, candidate) or inside(path, GATE):
            continue
        if inside(path, dependency_root) and profile in {"reference", "clean", "broad-owner-collapse", "broad-ack-is-delivery"}:
            declared_dependencies.append({"module": name, "path": str(path)})
            continue
        lowered = {part.lower() for part in path.parts}
        if (inside(path, stdlib_root) or inside(path, stdlib_dlls)) and not {"site-packages", "dist-packages"}.intersection(lowered):
            continue
        undeclared_dependencies.append({"module": name, "path": str(path)})
    payload["declared_dependency_modules"] = declared_dependencies
    payload["undeclared_dependency_modules"] = undeclared_dependencies
    if undeclared_dependencies:
        payload.update(valid=False, infrastructure_error="undeclared dependency provenance")
    payload.update(stdout=stdout.getvalue(), stderr=stderr.getvalue(), duration_seconds=round(time.perf_counter() - started, 6))
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True)); return 0

if __name__ == "__main__": raise SystemExit(main())
