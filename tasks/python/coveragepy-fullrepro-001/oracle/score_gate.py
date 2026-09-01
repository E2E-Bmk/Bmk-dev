"""Fresh-process scorer for the frozen Coverage.py v2 synthetic gate."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import random
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


GATE_ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((GATE_ROOT / "SCORER-CONFIG.json").read_text(encoding="utf-8"))
ROOT_MAP = json.loads((GATE_ROOT / CONFIG["root_map"]).read_text(encoding="utf-8"))
ROOTS = ROOT_MAP["roots"]
ROOT_BY_ID = {row["id"]: row for row in ROOTS}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _excluded(path: Path) -> bool:
    return any(part in {".git", "__pycache__", ".pytest_cache"} for part in path.parts) or path.suffix in {
        ".pyc",
        ".pyo",
    }


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root)
        if _excluded(relative):
            continue
        digest.update(relative.as_posix().encode("utf-8"))
        if path.is_symlink():
            digest.update(b"L")
            digest.update(os.readlink(path).encode("utf-8"))
        elif path.is_file():
            digest.update(b"F")
            digest.update(_sha256(path).encode("ascii"))
        elif path.is_dir():
            digest.update(b"D")
    return digest.hexdigest()


def gate_digest() -> str:
    digest = hashlib.sha256()
    excluded_parts = {"evidence", "prefreeze-discarded", "anchor-payload", "__pycache__", ".pytest_cache"}
    excluded_files = {"FREEZE-MANIFEST.json"}
    for path in sorted(GATE_ROOT.rglob("*"), key=lambda item: item.relative_to(GATE_ROOT).as_posix()):
        relative = path.relative_to(GATE_ROOT)
        if any(part in excluded_parts for part in relative.parts) or relative.name in excluded_files or relative.suffix in {".pyc", ".pyo"}:
            continue
        digest.update(relative.as_posix().encode("utf-8"))
        if path.is_symlink():
            digest.update(b"L" + os.readlink(path).encode("utf-8"))
        elif path.is_file():
            digest.update(b"F" + _sha256(path).encode("ascii"))
        elif path.is_dir():
            digest.update(b"D")
    return digest.hexdigest()


def _git(reference: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", "safe.directory=*", "-C", str(reference), *args],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=20,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "git command failed")
    return result.stdout.strip()


def reference_provenance(candidate: Path) -> dict[str, Any]:
    configured = (GATE_ROOT / CONFIG["reference"]["path"]).resolve()
    if candidate != configured:
        return {"is_pinned_reference": False}
    expected = CONFIG["reference"]
    actual = {
        "commit": _git(candidate, "rev-parse", "HEAD"),
        "tree": _git(candidate, "rev-parse", "HEAD^{tree}"),
        "status": _git(candidate, "status", "--porcelain"),
        "license_sha256": _sha256(candidate / expected["license_file"]),
    }
    mismatches = {
        key: {"expected": expected[key], "actual": actual[key]}
        for key in ("commit", "tree", "license_sha256")
        if actual[key] != expected[key]
    }
    if actual["status"]:
        mismatches["status"] = {"expected": "", "actual": actual["status"]}
    return {"is_pinned_reference": True, "actual": actual, "mismatches": mismatches}


def static_audit() -> dict[str, Any]:
    errors: list[str] = []
    ids = [row["id"] for row in ROOTS]
    expected_ids = [*(f"A{i:02d}" for i in range(1, 19)), *(f"I{i:02d}" for i in range(1, 25)), *(f"S{i:02d}" for i in range(1, 9))]
    if ids != expected_ids:
        errors.append("root id roster/order differs from exact 18A+24I+8S registration")
    if len(ids) != len(set(ids)):
        errors.append("duplicate root ids")
    tier_counts = Counter(row["tier"] for row in ROOTS)
    if dict(tier_counts) != {"Atomic": 18, "Integration": 24, "System": 8}:
        errors.append(f"tier count mismatch: {dict(tier_counts)}")
    registered_mutations = [row["id"] for row in ROOTS if row["family"]]
    if set(registered_mutations) != set(CONFIG["exact_m2_failures"]):
        errors.append("root map mutation union differs from exact M2 registration")
    family_counts = Counter(row["family"] for row in ROOTS if row["family"])
    if family_counts != Counter({"M-CANON": 7, "M-RCBASE": 6, "M-MERGE": 4, "M-CONTEXT": 3, "M-COLLECT": 3, "M-REPORT": 3}):
        errors.append(f"mutation family count mismatch: {dict(family_counts)}")
    if max(family_counts.values(), default=0) > 7:
        errors.append("mutation family dominance exceeds 7/26")
    atomic_ids = {row["id"] for row in ROOTS if row["tier"] == "Atomic"}
    for row in ROOTS:
        if row["tier"] != "Atomic":
            if not row["depends_on"]:
                errors.append(f"{row['id']} has no Atomic dependency")
            invalid = set(row["depends_on"]) - atomic_ids
            if invalid:
                errors.append(f"{row['id']} has non-Atomic dependencies: {sorted(invalid)}")

    expected_functions: dict[str, str] = {}
    for module_name, filename in (
        ("tests.test_atomic", "tests/test_atomic.py"),
        ("tests.test_integration", "tests/test_integration.py"),
        ("tests.test_system", "tests/test_system.py"),
    ):
        source = (GATE_ROOT / filename).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=filename)
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [alias.name for alias in node.names]
                if any(name == "coverage" or name.startswith("coverage.") for name in names):
                    errors.append(f"candidate import at module scope in {filename}:{node.lineno}")
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                if node.decorator_list:
                    errors.append(f"decorated root is forbidden: {node.name}")
                if node.args.posonlyargs or node.args.args or node.args.kwonlyargs or node.args.vararg or node.args.kwarg:
                    errors.append(f"root must be zero-argument: {node.name}")
                expected_functions[node.name] = module_name
    mapped_functions = {row["function"]: row["module"] for row in ROOTS}
    if expected_functions != mapped_functions:
        errors.append("AST root functions differ from ROOT-MAP.json")

    conftest_tree = ast.parse((GATE_ROOT / "tests/conftest.py").read_text(encoding="utf-8"))
    if any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) for node in conftest_tree.body):
        errors.append("conftest must not centralize behavioral fixtures")

    return {
        "valid": not errors,
        "errors": errors,
        "counts": {"roots": len(ids), "tiers": dict(tier_counts), "families": dict(family_counts)},
        "mutation_union": registered_mutations,
    }


def candidate_audit(candidate: Path) -> dict[str, Any]:
    errors: list[str] = []
    if not candidate.is_dir():
        errors.append("candidate is not a directory")
    if not (candidate / "coverage" / "__init__.py").is_file():
        errors.append("candidate must contain coverage/__init__.py")
    configured_reference = (GATE_ROOT / CONFIG["reference"]["path"]).resolve()
    forbidden = {".git", ".hg", ".svn", ".venv", "venv", ".tox", ".nox", ".cache", ".pytest_cache", "__pycache__"}
    if candidate.exists():
        for path in candidate.rglob("*"):
            if path.is_symlink():
                errors.append(f"candidate symlink forbidden: {path.relative_to(candidate).as_posix()}")
            if candidate != configured_reference and path.is_dir() and path.name in forbidden:
                errors.append(f"candidate control/cache directory forbidden: {path.relative_to(candidate).as_posix()}")
    return {"valid": not errors, "errors": errors}


def ordered_ids(mode: str, seed: int) -> list[str]:
    ids = [row["id"] for row in ROOTS]
    if mode == "reverse":
        ids.reverse()
    elif mode == "permuted":
        random.Random(seed).shuffle(ids)
    return ids


def run_one(candidate: Path, root_id: str, reference_patch: bool, timeout: int, env: dict[str, str]) -> dict[str, Any]:
    command = [sys.executable, "-B", str(GATE_ROOT / CONFIG["runner"]), root_id, str(candidate)]
    if reference_patch:
        command.append("--reference-patch")
    try:
        result = subprocess.run(
            command,
            cwd=GATE_ROOT,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {"root_id": root_id, "status": "invalid", "phase": "timeout", "error_type": "TimeoutExpired", "error_message": str(exc)}
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if len(lines) != 1:
        return {
            "root_id": root_id,
            "status": "invalid",
            "phase": "protocol",
            "error_type": "RunnerProtocolError",
            "error_message": f"expected one JSON line, received {len(lines)}",
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    try:
        raw = json.loads(lines[0])
    except json.JSONDecodeError as exc:
        return {"root_id": root_id, "status": "invalid", "phase": "protocol", "error_type": type(exc).__name__, "error_message": str(exc)}
    origins = raw.get("provenance", {}).get("origins", {})
    escaped = raw.get("provenance", {}).get("escaped", {})
    provenance_digest = hashlib.sha256(json.dumps(origins, sort_keys=True).encode("utf-8")).hexdigest()
    return {
        "root_id": root_id,
        "status": raw.get("status", "invalid"),
        "phase": raw.get("phase"),
        "error_type": raw.get("error_type", ""),
        "error_message": raw.get("error_message", ""),
        "warnings": raw.get("warnings", []),
        "captured_stdout": raw.get("stdout", ""),
        "captured_stderr": raw.get("stderr", ""),
        "main_origin": origins.get("coverage"),
        "provenance_module_count": len(origins),
        "provenance_digest": provenance_digest,
        "escaped": escaped,
        "runner_returncode": result.returncode,
        "runner_stderr": result.stderr,
    }


def _rate(passed: Iterable[str], ids: Iterable[str]) -> float:
    selected = list(ids)
    passed_set = set(passed)
    return sum(root_id in passed_set for root_id in selected) / len(selected)


def score_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    passed = [row["root_id"] for row in results if row["status"] == "passed"]
    atomic = [row["id"] for row in ROOTS if row["tier"] == "Atomic"]
    integration = [row["id"] for row in ROOTS if row["tier"] == "Integration"]
    system = [row["id"] for row in ROOTS if row["tier"] == "System"]
    composition = integration + system
    atomic_rate = _rate(passed, atomic)
    integration_rate = _rate(passed, integration)
    system_rate = _rate(passed, system)
    composition_rate = _rate(passed, composition)
    eligible = [row["id"] for row in ROOTS if row["tier"] != "Atomic" and all(dep in passed for dep in row["depends_on"])]
    conditional = _rate(passed, eligible) if eligible else 0.0
    return {
        "AtomicPassed": sum(root_id in passed for root_id in atomic),
        "AtomicRate": atomic_rate,
        "IntegrationPassed": sum(root_id in passed for root_id in integration),
        "IntegrationRate": integration_rate,
        "SystemPassed": sum(root_id in passed for root_id in system),
        "SystemRate": system_rate,
        "CompositionPassed": sum(root_id in passed for root_id in composition),
        "CompositionRate": composition_rate,
        "Combined": (atomic_rate + composition_rate) / 2,
        "Gap": atomic_rate - composition_rate,
        "ConditionalCompositionEligible": len(eligible),
        "ConditionalCompositionRate": conditional,
        "AdjustedGap": atomic_rate - conditional,
        "AllPassed": len(passed),
        "MutationPassed": sum(root_id in passed for root_id in CONFIG["exact_m2_failures"]),
        "NativePassed": sum(root_id in passed for root_id in ROOT_BY_ID if root_id not in CONFIG["exact_m2_failures"]),
    }


def expectation_check(expectation: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = {row["root_id"]: row["status"] for row in results}
    passed = {root_id for root_id, status in statuses.items() if status == "passed"}
    failed = {root_id for root_id, status in statuses.items() if status == "failed"}
    invalid = {root_id for root_id, status in statuses.items() if status == "invalid"}
    expected_all = set(ROOT_BY_ID)
    if expectation == "none":
        return {"profile": expectation, "match": not invalid, "invalid": sorted(invalid)}
    if expectation == "m1":
        match = passed == expected_all and not failed and not invalid
    elif expectation == "m2":
        expected_failed = set(CONFIG["exact_m2_failures"])
        match = failed == expected_failed and passed == expected_all - expected_failed and not invalid
    elif expectation == "dummy":
        match = failed == expected_all and not passed and not invalid and all(row["phase"] == "call" for row in results)
    else:
        raise ValueError(expectation)
    return {"profile": expectation, "match": match, "passed": sorted(passed), "failed": sorted(failed), "invalid": sorted(invalid)}


def write_output(payload: dict[str, Any], output: str | None) -> None:
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output:
        destination = Path(output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", nargs="?")
    parser.add_argument("--order", choices=("natural", "reverse", "permuted"), default="natural")
    parser.add_argument("--seed", type=int, default=20260814)
    parser.add_argument("--expectation", choices=("none", "m1", "m2", "dummy"), default="none")
    parser.add_argument("--reference-patch", action="store_true")
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    static = static_audit()
    if args.static_only:
        payload = {"schema": "coveragepy-v2-static-audit-1", "static": static}
        write_output(payload, args.output)
        return 0 if static["valid"] else 2
    if not args.candidate:
        parser.error("candidate is required unless --static-only is used")
    candidate = Path(args.candidate).resolve()
    candidate_check = candidate_audit(candidate)
    try:
        provenance = reference_provenance(candidate)
    except Exception as exc:
        provenance = {"is_pinned_reference": candidate == (GATE_ROOT / CONFIG["reference"]["path"]).resolve(), "mismatches": {"probe": str(exc)}}
    if args.reference_patch and (not provenance.get("is_pinned_reference") or provenance.get("mismatches")):
        candidate_check["valid"] = False
        candidate_check["errors"].append("reference patch may run only against the clean pinned reference")

    before = tree_digest(candidate) if candidate.exists() else ""
    gate_before = gate_digest()
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="coveragepy-v2-scorer-") as temp_home:
        env = os.environ.copy()
        for name in list(env):
            if name.startswith("COVERAGE_"):
                env.pop(name)
        env.update({"HOME": temp_home, "USERPROFILE": temp_home, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", "NO_COLOR": "1"})
        if static["valid"] and candidate_check["valid"]:
            for root_id in ordered_ids(args.order, args.seed):
                results.append(run_one(candidate, root_id, args.reference_patch, CONFIG["root_timeout_seconds"], env))
    after = tree_digest(candidate) if candidate.exists() else ""
    gate_after = gate_digest()
    immutable = before == after
    gate_immutable = gate_before == gate_after
    expectation = expectation_check(args.expectation, results) if results else {"profile": args.expectation, "match": False}
    result_invalid = any(row["status"] == "invalid" for row in results)
    overall_valid = static["valid"] and candidate_check["valid"] and immutable and gate_immutable and not result_invalid and expectation["match"]
    payload = {
        "schema": "coveragepy-v2-score-evidence-1",
        "candidate": str(candidate),
        "order": args.order,
        "seed": args.seed,
        "reference_patch": args.reference_patch,
        "runtime": {"executable": sys.executable, "version": sys.version, "platform": sys.platform},
        "static": static,
        "candidate_audit": candidate_check,
        "reference_provenance": provenance,
        "tree": {"before": before, "after": after, "immutable": immutable},
        "gate_tree": {"before": gate_before, "after": gate_after, "immutable": gate_immutable},
        "expectation": expectation,
        "valid": overall_valid,
        "metrics": score_results(results) if results and not result_invalid else None,
        "results": results,
    }
    write_output(payload, args.output)
    return 0 if overall_valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
