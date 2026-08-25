"""Isolated root runner for the attrs v2 draft gate."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path


GATE_ROOT = Path(__file__).resolve().parent
TESTS_ROOT = GATE_ROOT / "tests"
RUNTIME_ROOT = GATE_ROOT / "runtime-site"
FIXED_ORDER = (
    23, 4, 41, 12, 32, 0, 18, 46, 7, 29, 15, 37,
    2, 44, 20, 9, 34, 26, 5, 39, 16, 31, 11, 47,
    1, 25, 42, 13, 35, 6, 28, 21, 45, 8, 33, 17,
    40, 3, 30, 14, 43, 10, 36, 22, 27, 19, 38, 24,
)
CONFIG = json.loads((GATE_ROOT / "SCORER-CONFIG.json").read_text(encoding="utf-8"))
GATE_INPUTS = (
    "TASK.md", "SPEC.md", "ENVIRONMENT-CONTRACT.md", "ANCHOR-ADMISSION-PREREG.md",
    "SCORER-CONFIG.json", "runtime-identity.json", "root-manifest.json", "run_gate.py",
    "finalize_gate.py", "tests/root_suite.py",
)


def tree_hash(root):
    root = Path(root).resolve()
    ignored = {".git", "__pycache__", ".pytest_cache", ".tmp"}
    rows = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root)
        if ignored.intersection(relative.parts) or path.suffix in {".pyc", ".pyo"}:
            continue
        data = path.read_bytes()
        rows.append((relative.as_posix(), hashlib.sha256(data).hexdigest(), len(data)))
    logical = "".join(f"{name}\0{digest}\0{size}\n" for name, digest, size in rows)
    return hashlib.sha256(logical.encode("utf-8")).hexdigest()


def gate_input_sha256():
    digest = hashlib.sha256()
    for name in GATE_INPUTS:
        data = (GATE_ROOT / name).read_bytes()
        encoded = name.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def git_state():
    repository = Path(CONFIG["reference_repository_root"])
    command = [CONFIG["git_executable"], "-c", f"safe.directory={repository}", "-C", str(repository)]
    def fact(*arguments):
        child = subprocess.run([*command, *arguments], text=True, encoding="utf-8", errors="replace", capture_output=True)
        return child.stdout.strip() if child.returncode == 0 else None
    return {
        "commit": fact("rev-parse", "HEAD"),
        "tree": fact("rev-parse", "HEAD^{tree}"),
        "status": fact("status", "--porcelain=v1", "--untracked-files=all"),
    }


def _inside(path, root):
    try:
        Path(path).resolve().relative_to(Path(root).resolve())
        return True
    except ValueError:
        return False


def _prepare(candidate):
    candidate = str(Path(candidate).resolve())
    runtime = str(RUNTIME_ROOT.resolve())
    sys.path[:] = [candidate, runtime, str(TESTS_ROOT), *[item for item in sys.path if item not in {candidate, runtime, str(TESTS_ROOT)}]]
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    return candidate, runtime


def preflight(candidate):
    candidate, runtime = _prepare(candidate)
    try:
        attrs = importlib.import_module("attrs")
        workspace = importlib.import_module("attrs.workspace")
        attr = importlib.import_module("attr")
        validators = importlib.import_module("attrs.validators")
    except Exception:
        return {"status": "invalid", "reason": "import", "traceback": traceback.format_exc()}
    origins = {
        "attrs": str(Path(attrs.__file__).resolve()),
        "attrs.workspace": str(Path(workspace.__file__).resolve()),
        "attr": str(Path(attr.__file__).resolve()),
        "attrs.validators": str(Path(validators.__file__).resolve()),
        "attrs.__path__": [str(Path(item).resolve()) for item in attrs.__path__],
    }
    valid = (
        _inside(origins["attrs"], candidate)
        and _inside(origins["attrs.workspace"], candidate)
        and _inside(origins["attr"], runtime)
        and _inside(origins["attrs.validators"], runtime)
        and origins["attrs.__path__"] == [candidate + os.sep + "attrs", runtime + os.sep + "attrs"]
    )
    return {"status": "ok" if valid else "invalid", "reason": None if valid else "provenance", "origins": origins}


def child(root_id, candidate):
    _prepare(candidate)
    try:
        suite = importlib.import_module("root_suite")
    except Exception:
        return {"status": "invalid", "reason": "collection", "traceback": traceback.format_exc()}
    matches = [root for root in suite.ROOTS if root.root_id == root_id]
    if len(matches) != 1:
        return {"status": "invalid", "reason": "collection", "detail": "root identity mismatch"}
    root = matches[0]
    started = time.monotonic()
    try:
        root.function()
    except BaseException as exc:
        return {
            "status": "fail",
            "root_id": root.root_id,
            "level": root.level,
            "designation": root.designation,
            "behavior": root.behavior,
            "exception": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
            "seconds": time.monotonic() - started,
        }
    return {
        "status": "pass",
        "root_id": root.root_id,
        "level": root.level,
        "designation": root.designation,
        "behavior": root.behavior,
        "seconds": time.monotonic() - started,
    }


def run(candidate, order, timeout):
    candidate = Path(candidate).resolve()
    candidate_before = tree_hash(candidate)
    runtime_before = tree_hash(RUNTIME_ROOT)
    reference_before = git_state()
    gate_hash = gate_input_sha256()
    sys.path.insert(0, str(TESTS_ROOT))
    try:
        import root_suite
    except Exception:
        return {"status": "invalid", "reason": "collection", "traceback": traceback.format_exc()}
    roots = list(root_suite.ROOTS)
    if order == "reverse":
        roots.reverse()
    elif order == "fixed":
        roots = [roots[index] for index in FIXED_ORDER]
    preflight_command = [sys.executable, "-S", "-B", str(Path(__file__).resolve()), "--preflight", "--candidate", str(Path(candidate).resolve())]
    checked = subprocess.run(preflight_command, capture_output=True, text=True, timeout=timeout)
    if checked.returncode != 0:
        return {"status": "invalid", "reason": "preflight-harness", "stdout": checked.stdout, "stderr": checked.stderr}
    try:
        preflight_result = json.loads(checked.stdout)
    except Exception:
        return {"status": "invalid", "reason": "preflight-protocol", "stdout": checked.stdout, "stderr": checked.stderr}
    if preflight_result["status"] != "ok":
        return {"status": "invalid", "reason": preflight_result.get("reason"), "preflight": preflight_result}
    results = []
    for root in roots:
        command = [sys.executable, "-S", "-B", str(Path(__file__).resolve()), "--child", root.root_id, "--candidate", str(Path(candidate).resolve())]
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return {"status": "invalid", "reason": "timeout", "root_id": root.root_id, "results": results}
        if completed.returncode != 0:
            return {"status": "invalid", "reason": "child-harness", "root_id": root.root_id, "stdout": completed.stdout, "stderr": completed.stderr, "results": results}
        try:
            result = json.loads(completed.stdout)
        except Exception:
            return {"status": "invalid", "reason": "child-protocol", "root_id": root.root_id, "stdout": completed.stdout, "stderr": completed.stderr, "results": results}
        if result["status"] == "invalid":
            return {"status": "invalid", "reason": result.get("reason"), "root_id": root.root_id, "detail": result, "results": results}
        results.append(result)
    passed = sum(item["status"] == "pass" for item in results)
    atomic = [item for item in results if item["level"] == "Atomic"]
    combined_high = [item for item in results if item["level"] in {"Integration", "System"}]
    native = [item for item in results if item["designation"] == "native"]
    mutation = [item for item in results if item["designation"] == "mutation"]
    atomic_rate = sum(item["status"] == "pass" for item in atomic) / 16
    high_rate = sum(item["status"] == "pass" for item in combined_high) / 32
    candidate_after = tree_hash(candidate)
    runtime_after = tree_hash(RUNTIME_ROOT)
    reference_after = git_state()
    invalid_reasons = []
    if candidate_before != candidate_after:
        invalid_reasons.append("candidate tree changed")
    if runtime_before != runtime_after or runtime_after != CONFIG["runtime_tree_sha256"]:
        invalid_reasons.append("runtime tree changed or mismatched")
    expected_reference = {"commit": CONFIG["reference_commit"], "tree": CONFIG["reference_tree"], "status": ""}
    if reference_before != reference_after or reference_after != expected_reference:
        invalid_reasons.append("reference provenance changed or mismatched")
    return {
        "schema": "spec2repo.score-receipt.v3",
        "case": CONFIG["case"],
        "constitution": CONFIG["constitution"],
        "status": "invalid" if invalid_reasons else "ok",
        "invalid_reasons": invalid_reasons,
        "order": order,
        "candidate": str(candidate),
        "gate_input_sha256": gate_hash,
        "candidate_tree_sha256_before": candidate_before,
        "candidate_tree_sha256_after": candidate_after,
        "runtime_tree_sha256_before": runtime_before,
        "runtime_tree_sha256_after": runtime_after,
        "reference_before": reference_before,
        "reference_after": reference_after,
        "passed": passed,
        "total": 48,
        "combined": passed / 48,
        "atomic_passed": sum(item["status"] == "pass" for item in atomic),
        "integration_passed": sum(item["status"] == "pass" and item["level"] == "Integration" for item in results),
        "system_passed": sum(item["status"] == "pass" and item["level"] == "System" for item in results),
        "native_passed": sum(item["status"] == "pass" for item in native),
        "mutation_passed": sum(item["status"] == "pass" for item in mutation),
        "gap": atomic_rate - high_rate,
        "preflight": preflight_result,
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--order", choices=("natural", "reverse", "fixed"), default="natural")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--output")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--child")
    args = parser.parse_args()
    if args.preflight:
        result = preflight(args.candidate)
    elif args.child:
        result = child(args.child, args.candidate)
    else:
        result = run(args.candidate, args.order, args.timeout)
    encoded = json.dumps(result, sort_keys=True, indent=None if (args.preflight or args.child) else 2)
    if args.output and not (args.preflight or args.child):
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
