from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time


GATE = Path(__file__).resolve().parent
CONFIG = json.loads((GATE / "SCORER-CONFIG.json").read_text(encoding="utf-8"))
ROOT_MAP = json.loads((GATE / "ROOT-MAP.json").read_text(encoding="utf-8"))
GATE_INPUTS = (
    "ROOT-MAP.json",
    "SCORER-CONFIG.json",
    "run_root.py",
    "score_gate.py",
    "reference-overlay/griffe_v3_workflow.py",
    "reference-overlay/griffe_v3_controls.py",
    "clean-api-scaffold/griffe_v3_scaffold.py",
    "dummy/griffe_v3_dummy.py",
    "tests/conftest.py",
    "tests/support.py",
    "tests/workflow_support.py",
    "tests/test_native_controls.py",
    "tests/test_workflow_atomic.py",
    "tests/test_workflow_integration.py",
    "tests/test_workflow_system.py",
)


def sha256_tree(root: Path) -> str:
    digest = hashlib.sha256()
    ignored = {".git", "__pycache__", ".pytest_cache"}
    files = sorted(
        path for path in root.rglob("*")
        if path.is_file() and not ignored.intersection(path.relative_to(root).parts)
    )
    for path in files:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        data = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def rows() -> list[dict[str, object]]:
    return [*ROOT_MAP["atomic"], *ROOT_MAP["composition"]]


def gate_input_sha256() -> str:
    digest = hashlib.sha256()
    for name in GATE_INPUTS:
        data = (GATE / name).read_bytes()
        encoded = name.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def static_inventory() -> tuple[list[str], list[str]]:
    discovered: dict[str, str] = {}
    errors: list[str] = []
    filenames = (
        "test_native_controls.py",
        "test_workflow_atomic.py",
        "test_workflow_integration.py",
        "test_workflow_system.py",
    )
    for filename in filenames:
        path = GATE / "tests" / filename
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                parameters = [argument.arg for argument in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]]
                if parameters not in ([], ["tmp_path"]) or node.args.vararg or node.args.kwarg:
                    errors.append(f"invalid root signature: {node.name}")
                if node.decorator_list:
                    errors.append(f"decorated root: {node.name}")
                discovered[node.name] = filename
    expected_functions = {str(row["function"]) for row in rows()}
    if set(discovered) != expected_functions:
        errors.append("test function inventory differs from ROOT-MAP.json")
    ids = [str(row["id"]) for row in rows()]
    expected_ids = [
        *(f"A{i:02d}" for i in range(1, 17)),
        *(f"I{i:02d}" for i in range(1, 25)),
        *(f"S{i:02d}" for i in range(1, 9)),
    ]
    if ids != expected_ids:
        errors.append("root ID inventory or order is invalid")
    if set(ROOT_MAP["mutation_expected_fail"]) | set(ROOT_MAP["mutation_expected_pass"]) != set(ids):
        errors.append("mutation/native partition does not cover the root inventory")
    if set(ROOT_MAP["mutation_expected_fail"]) & set(ROOT_MAP["mutation_expected_pass"]):
        errors.append("mutation/native partition overlaps")
    return ids, errors


def candidate_policy_errors(candidate: Path, profile: str) -> list[str]:
    errors: list[str] = []
    if not candidate.is_dir() or not (candidate / "griffe" / "__init__.py").is_file():
        return ["candidate does not contain griffe/__init__.py"]
    for path in candidate.rglob("*"):
        if path.is_symlink():
            errors.append(f"candidate symlink is not allowed: {path.relative_to(candidate).as_posix()}")
        elif path.is_file() and path.suffix == ".py":
            try:
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except (UnicodeDecodeError, SyntaxError) as exc:
                errors.append(f"candidate source is not valid UTF-8 Python: {path.relative_to(candidate).as_posix()}: {exc}")
    reference = Path(CONFIG["reference_package_root"]).resolve()
    if profile in {"reference", "clean", "dummy", "broad-snapshot-promotion", "broad-acknowledgement"} and candidate != reference:
        errors.append(f"{profile} profile requires the pinned reference package root")
    if profile in {"anchor", "arbitrary"} and candidate == reference:
        errors.append(f"{profile} profile requires an independent candidate")
    return errors


def ordered_roots(mode: str) -> list[str]:
    root_ids = [str(row["id"]) for row in rows()]
    if mode == "reverse":
        root_ids.reverse()
    elif mode == "permuted":
        random.Random(CONFIG["permutation_seed"]).shuffle(root_ids)
    return root_ids


def rate(passed: int, total: int) -> float | None:
    return round(passed / total, 6) if total else None


def metric(results: list[dict[str, object]], ids: set[str]) -> dict[str, object]:
    selected = [item for item in results if item["root"] in ids]
    passed = sum(item.get("passed") is True for item in selected)
    return {"passed": passed, "total": len(selected), "rate": rate(passed, len(selected))}


def score(results: list[dict[str, object]]) -> dict[str, object]:
    atomic_ids = {str(row["id"]) for row in ROOT_MAP["atomic"]}
    composition_ids = {str(row["id"]) for row in ROOT_MAP["composition"]}
    integration_ids = {str(row["id"]) for row in ROOT_MAP["composition"] if row["tier"] == "integration"}
    system_ids = {str(row["id"]) for row in ROOT_MAP["composition"] if row["tier"] == "system_e2e"}
    mutation_ids = set(ROOT_MAP["mutation_expected_fail"])
    native_ids = set(ROOT_MAP["mutation_expected_pass"])
    passed_ids = {str(item["root"]) for item in results if item.get("passed") is True}
    conditional_ids = {
        str(row["id"]) for row in ROOT_MAP["composition"]
        if set(row["depends_on"]).issubset(passed_ids)
    }
    atomic = metric(results, atomic_ids)
    composition = metric(results, composition_ids)
    conditional = metric(results, conditional_ids)
    combined = (
        round((atomic["rate"] + composition["rate"]) / 2, 6)
        if atomic["rate"] is not None and composition["rate"] is not None
        else None
    )
    gap = (
        round(atomic["rate"] - composition["rate"], 6)
        if atomic["rate"] is not None and composition["rate"] is not None
        else None
    )
    adjusted = round(atomic["rate"] - conditional["rate"], 6) if conditional["rate"] is not None else None
    families = sorted({str(row["family"]) for row in rows() if row.get("family")})
    return {
        "all_roots": metric(results, atomic_ids | composition_ids),
        "atomic": atomic,
        "composition": composition,
        "combined_rate": combined,
        "gap": gap,
        "integration": metric(results, integration_ids),
        "system_e2e": metric(results, system_ids),
        "conditional_composition": conditional,
        "adjusted_gap": adjusted,
        "mutation_designated": metric(results, mutation_ids),
        "native_controls": metric(results, native_ids),
        "mutation_families": {
            family: metric(results, {str(row["id"]) for row in rows() if row.get("family") == family})
            for family in families
        },
    }


def git_fact(repository: Path, *arguments: str) -> str | None:
    child = subprocess.run(
        ["git", "-c", f"safe.directory={repository}", "-C", str(repository), *arguments],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    return child.stdout.strip() if child.returncode == 0 else None


def run(candidate: Path, profile: str, mode: str, only: str | None) -> dict[str, object]:
    started = time.time()
    candidate = candidate.resolve()
    inventory, invalid = static_inventory()
    invalid.extend(candidate_policy_errors(candidate, profile))
    order = [only] if only else ordered_roots(mode)
    if only and only not in inventory:
        invalid.append(f"unknown root: {only}")
    tree_before = sha256_tree(candidate) if candidate.is_dir() else None
    repository = Path(CONFIG["reference_repository_root"]).resolve()
    reference_before = {
        "commit": git_fact(repository, "rev-parse", "HEAD"),
        "tree": git_fact(repository, "rev-parse", "HEAD^{tree}"),
        "status": git_fact(repository, "status", "--porcelain=v1", "--untracked-files=all"),
    }
    if profile in {"reference", "clean", "dummy", "broad-snapshot-promotion", "broad-acknowledgement"} and reference_before["status"] != "":
        invalid.append("pinned reference repository is not clean")
    results: list[dict[str, object]] = []
    if not invalid:
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        for root_id in order:
            try:
                child = subprocess.run(
                    [sys.executable, str(GATE / "run_root.py"), root_id, str(candidate), profile],
                    cwd=GATE,
                    env=env,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                    timeout=CONFIG["root_timeout_seconds"],
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                invalid.append(f"root timeout: {root_id}")
                results.append({"root": root_id, "valid": False, "timeout": True, "stdout": exc.stdout, "stderr": exc.stderr})
                continue
            if child.returncode != 0:
                invalid.append(f"unexpected root process status: {root_id}={child.returncode}")
                results.append({"root": root_id, "valid": False, "process_status": child.returncode, "stdout": child.stdout, "stderr": child.stderr})
                continue
            try:
                record = json.loads(child.stdout)
            except json.JSONDecodeError:
                invalid.append(f"malformed root receipt: {root_id}")
                record = {"root": root_id, "valid": False, "stdout": child.stdout, "stderr": child.stderr}
            if record.get("root") != root_id or record.get("valid") is not True or record.get("phase") != "call":
                invalid.append(f"invalid root receipt: {root_id}")
            results.append(record)
    tree_after = sha256_tree(candidate) if candidate.is_dir() else None
    if tree_before != tree_after:
        invalid.append("candidate tree changed during scoring")
    reference_after = {
        "commit": git_fact(repository, "rev-parse", "HEAD"),
        "tree": git_fact(repository, "rev-parse", "HEAD^{tree}"),
        "status": git_fact(repository, "status", "--porcelain=v1", "--untracked-files=all"),
    }
    if reference_before != reference_after:
        invalid.append("reference repository provenance changed during scoring")
    return {
        "schema": "spec2repo.score-receipt.v2",
        "case": CONFIG["case"],
        "constitution": CONFIG["constitution"],
        "scoring_formula": CONFIG["scoring_formula"],
        "gate_input_sha256": gate_input_sha256(),
        "candidate": str(candidate),
        "candidate_profile": profile,
        "candidate_tree_sha256_before": tree_before,
        "candidate_tree_sha256_after": tree_after,
        "reference_before": reference_before,
        "reference_after": reference_after,
        "mode": mode,
        "only": only,
        "valid": not invalid and len(results) == len(order),
        "invalid_reasons": invalid,
        "inventory": inventory,
        "order": order,
        "results": results,
        "score": score(results),
        "started_epoch": started,
        "finished_epoch": time.time(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--profile", choices=["reference", "clean", "dummy", "broad-snapshot-promotion", "broad-acknowledgement", "anchor", "arbitrary"], required=True)
    parser.add_argument("--mode", choices=CONFIG["execution_modes"], default="natural")
    parser.add_argument("--only")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    receipt = run(Path(args.candidate), args.profile, args.mode, args.only)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"valid": receipt["valid"], "score": receipt["score"], "output": str(output)}, ensure_ascii=False))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
