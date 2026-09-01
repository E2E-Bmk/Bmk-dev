from __future__ import annotations
import contextlib, importlib, inspect, io, json, os, sys, tempfile, time, traceback, warnings
from pathlib import Path

GATE = Path(__file__).resolve().parent

def inside(path: Path, root: Path) -> bool:
    try: path.resolve().relative_to(root.resolve()); return True
    except ValueError: return False

def root_module(root_id: str) -> str:
    native = {*(f"A{i:02d}" for i in range(1, 7)), *(f"I{i:02d}" for i in range(1, 6)), "S01", "S02", "S03"}
    if root_id in native: return "tests.test_native_controls"
    if root_id.startswith("A"): return "tests.test_workspace_atomic"
    if root_id.startswith("I"): return "tests.test_workspace_integration"
    return "tests.test_workspace_system"

def classify_failure(payload: dict[str, object], exc: BaseException) -> None:
    if payload["phase"] != "call":
        payload.update(valid=False, infrastructure_error="root did not reach semantic call")
    elif isinstance(exc, Warning):
        payload.update(valid=False, infrastructure_error=f"unexpected warning during semantic call: {type(exc).__name__}")

def install_profile(profile: str, networkx: object) -> None:
    if profile == "reference":
        sys.path.insert(0, str(GATE / "reference-overlay")); importlib.import_module("networkx_v3_workspace").install(networkx)
    elif profile == "clean":
        sys.path.insert(0, str(GATE / "clean-api-scaffold")); importlib.import_module("networkx_v3_clean").install(networkx)
    elif profile in {"broad-owner-collapse", "broad-cache-eager"}:
        sys.path.insert(0, str(GATE / "reference-overlay"))
        importlib.import_module("networkx_v3_workspace").install(networkx, profile)
    elif profile == "shallow":
        sys.path.insert(0, str(GATE / "reference-overlay")); importlib.import_module("networkx_v3_workspace").install(networkx, "shallow")
    elif profile in {"dummy", "anchor", "arbitrary"}: return
    else: raise RuntimeError(f"unknown profile: {profile}")

def main() -> int:
    if len(sys.argv) != 4:
        print(json.dumps({"valid": False, "error": "usage: run_root.py ROOT CANDIDATE PROFILE"})); return 2
    root_id, candidate_arg, profile = sys.argv[1:]; candidate = Path(candidate_arg).resolve()
    payload: dict[str, object] = {"root": root_id, "valid": True, "passed": False, "phase": "setup", "profile": profile}
    stdout, stderr = io.StringIO(), io.StringIO(); started = time.perf_counter()
    if not (candidate / "networkx" / "__init__.py").is_file():
        print(json.dumps({**payload, "valid": False, "error": "candidate networkx package is absent"}, sort_keys=True)); return 0
    sys.path.insert(0, str(candidate)); sys.path.insert(1, str(GATE)); os.environ["SPEC2REPO_CANDIDATE_ROOT"] = str(candidate)
    config = json.loads((GATE / "SCORER-CONFIG.json").read_text(encoding="utf-8"))
    os.environ["SPEC2REPO_NETWORKX_RUNTIME"] = str(Path(config["reference_package_root"]) / "networkx")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error"); networkx = importlib.import_module("networkx"); install_profile(profile, networkx)
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
    imported = sys.modules.get("networkx"); origin = getattr(imported, "__file__", None)
    payload["networkx_import"] = str(Path(origin).resolve()) if origin else None; payload["candidate_contained"] = bool(origin and inside(Path(origin), candidate))
    escaped: list[dict[str, str]] = []; overlay_allowed = profile in {"reference", "clean", "broad-owner-collapse", "broad-cache-eager"}
    runtime = Path(json.loads((GATE / "SCORER-CONFIG.json").read_text(encoding="utf-8"))["reference_package_root"]) / "networkx"
    for name, module in list(sys.modules.items()):
        if name != "networkx" and not name.startswith("networkx."): continue
        location = getattr(module, "__file__", None)
        if location and not inside(Path(location), candidate):
            if overlay_allowed and name == "networkx.workspace": continue
            if profile in {"shallow", "anchor", "arbitrary"} and name != "networkx.workspace" and inside(Path(location), runtime): continue
            escaped.append({"module": name, "path": str(Path(location).resolve())})
    payload["escaped_networkx_modules"] = escaped
    if not payload["candidate_contained"] or escaped: payload.update(valid=False, infrastructure_error="networkx import escaped candidate tree")
    payload.update(stdout=stdout.getvalue(), stderr=stderr.getvalue(), duration_seconds=round(time.perf_counter() - started, 6))
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True)); return 0

if __name__ == "__main__": raise SystemExit(main())
