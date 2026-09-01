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
import warnings


GATE = Path(__file__).resolve().parent
CONFIG = json.loads((GATE / "SCORER-CONFIG.json").read_text(encoding="utf-8"))
ROOT_MAP = json.loads((GATE / "ROOT-MAP.json").read_text(encoding="utf-8"))
GATE_INPUTS = (
    "SPEC.md", "TASK.md", "ENVIRONMENT-CONTRACT.md", "ROOT-MAP.json", "MUTATION-PORTFOLIO.json",
    "SCORER-CONFIG.json", "run_root.py", "score_gate.py", "reference-overlay/kedro_v2_run_state.py",
    "reference-overlay/kedro_v2_controls.py", "clean-api-scaffold/kedro_v2_scaffold.py",
    "tests/native_support.py", "tests/recovery_support.py", "tests/test_native_controls.py", "tests/test_recovery_atomic.py",
    "tests/test_recovery_integration.py", "tests/test_recovery_system.py",
)


def sha256_tree(root: Path) -> str:
    digest = hashlib.sha256(); ignored = {".git", "__pycache__", ".pytest_cache", ".tmp"}
    files = sorted(path for path in root.rglob("*") if path.is_file() and not ignored.intersection(path.relative_to(root).parts))
    for path in files:
        relative = path.relative_to(root).as_posix().encode("utf-8"); data = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big")); digest.update(relative)
        digest.update(len(data).to_bytes(8, "big")); digest.update(data)
    return digest.hexdigest()


def rows() -> list[dict[str, object]]:
    return [*ROOT_MAP["atomic"], *ROOT_MAP["composition"]]


def gate_input_sha256() -> str:
    digest = hashlib.sha256()
    for name in GATE_INPUTS:
        data = (GATE / name).read_bytes(); encoded = name.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big")); digest.update(encoded)
        digest.update(len(data).to_bytes(8, "big")); digest.update(data)
    return digest.hexdigest()


def module_for(root_id: str) -> str:
    if root_id in {*(f"A{i:02d}" for i in range(1, 9)), *(f"I{i:02d}" for i in range(1, 5)), "S01", "S02"}:
        return "test_native_controls.py"
    if root_id.startswith("A"): return "test_recovery_atomic.py"
    if root_id.startswith("I"): return "test_recovery_integration.py"
    return "test_recovery_system.py"


def static_inventory() -> tuple[list[str], list[str]]:
    expected_ids = [*(f"A{i:02d}" for i in range(1, 17)), *(f"I{i:02d}" for i in range(1, 25)), *(f"S{i:02d}" for i in range(1, 9))]
    ids = [str(row["id"]) for row in rows()]; errors: list[str] = []
    if ids != expected_ids: errors.append("root inventory/order differs from 16A+24I+8S")
    for root_id in ids:
        path = GATE / "tests" / module_for(root_id); tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        function = functions.get(f"test_{root_id.lower()}")
        if function is None: errors.append(f"missing root function: {root_id}"); continue
        names = [item.arg for item in [*function.args.posonlyargs, *function.args.args, *function.args.kwonlyargs]]
        if names != ["tmp_path"] or function.args.vararg or function.args.kwarg or function.decorator_list:
            errors.append(f"invalid root signature: {root_id}")
    mutation = {str(row["id"]) for row in rows() if row["mutation"]}
    native = set(ids) - mutation
    portfolio = json.loads((GATE / "MUTATION-PORTFOLIO.json").read_text(encoding="utf-8"))
    declared_mutation = {item for values in portfolio["families"].values() for item in values}
    if mutation != declared_mutation or native != set(portfolio["native"]): errors.append("mutation/native partition mismatch")
    dependencies = {str(dep) for row in rows() for dep in row.get("depends_on", ())}
    if not dependencies.issubset(ids): errors.append("unknown dependency root")
    return ids, errors


def candidate_policy_errors(candidate: Path, profile: str) -> list[str]:
    errors: list[str] = []
    reference = Path(CONFIG["reference_package_root"]).resolve(); dummy = (GATE / "dummy").resolve()
    if not candidate.is_dir() or not (candidate / "kedro" / "__init__.py").is_file(): return ["candidate lacks kedro/__init__.py"]
    if profile in {"reference", "clean", "broad-plan-collapse", "broad-publish-is-ack"} and candidate != reference:
        errors.append(f"{profile} requires pinned reference package root")
    if profile == "dummy" and candidate != dummy: errors.append("dummy profile requires sealed dummy root")
    if profile in {"anchor", "arbitrary"} and candidate in {reference, dummy}: errors.append("independent candidate required")
    for path in candidate.rglob("*"):
        if path.is_symlink(): errors.append(f"candidate symlink forbidden: {path}")
        elif path.is_file() and path.suffix == ".py":
            relative = path.relative_to(candidate)
            if any("{{" in part or "}}" in part for part in relative.parts):
                continue
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", SyntaxWarning)
                    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except (UnicodeDecodeError, SyntaxError) as exc: errors.append(f"invalid candidate Python source: {path}: {exc}")
    return errors


def order_for(mode: str) -> list[str]:
    values = [str(row["id"]) for row in rows()]
    if mode == "reverse": values.reverse()
    elif mode == "permuted": random.Random(CONFIG["permutation_seed"]).shuffle(values)
    return values


def rate(passed: int, total: int) -> float | None:
    return round(passed / total, 8) if total else None


def metric(results: list[dict[str, object]], ids: set[str]) -> dict[str, object]:
    selected = [item for item in results if item["root"] in ids]; passed = sum(item.get("passed") is True for item in selected)
    return {"passed": passed, "total": len(selected), "rate": rate(passed, len(selected))}


def score(results: list[dict[str, object]]) -> dict[str, object]:
    atomic_ids = {str(row["id"]) for row in ROOT_MAP["atomic"]}; composition_ids = {str(row["id"]) for row in ROOT_MAP["composition"]}
    integration_ids = {str(row["id"]) for row in ROOT_MAP["composition"] if row["tier"] == "integration"}
    system_ids = composition_ids - integration_ids; mutation_ids = {str(row["id"]) for row in rows() if row["mutation"]}; native_ids = (atomic_ids | composition_ids) - mutation_ids
    passed_ids = {str(item["root"]) for item in results if item.get("passed") is True}
    conditional_ids = {str(row["id"]) for row in ROOT_MAP["composition"] if set(row.get("depends_on", ())).issubset(passed_ids)}
    atomic = metric(results, atomic_ids); composition = metric(results, composition_ids); conditional = metric(results, conditional_ids)
    all_roots = metric(results, atomic_ids | composition_ids)
    combined = all_roots["rate"]
    gap = round(atomic["rate"] - composition["rate"], 8) if atomic["rate"] is not None and composition["rate"] is not None else None
    adjusted = round(atomic["rate"] - conditional["rate"], 8) if conditional["rate"] is not None else None
    families = sorted({str(row.get("family")) for row in rows() if row.get("family")})
    return {
        "all_roots": all_roots, "atomic": atomic, "composition": composition,
        "integration": metric(results, integration_ids), "system_e2e": metric(results, system_ids),
        "combined_rate": combined, "gap": gap, "conditional_composition": conditional, "adjusted_gap": adjusted,
        "mutation_designated": metric(results, mutation_ids), "native_controls": metric(results, native_ids),
        "mutation_families": {family: metric(results, {str(row["id"]) for row in rows() if row.get("family") == family}) for family in families},
    }


def git_fact(repository: Path, *arguments: str) -> str | None:
    child = subprocess.run([CONFIG["git_executable"], "-c", f"safe.directory={repository}", "-C", str(repository), *arguments],
                           text=True, encoding="utf-8", errors="replace", capture_output=True, check=False)
    return child.stdout.strip() if child.returncode == 0 else None


def run(candidate: Path, profile: str, mode: str, only: str | None) -> dict[str, object]:
    started = time.time(); candidate = candidate.resolve(); inventory, invalid = static_inventory(); invalid.extend(candidate_policy_errors(candidate, profile))
    order = [only] if only else order_for(mode)
    if only and only not in inventory: invalid.append(f"unknown root: {only}")
    tree_before = sha256_tree(candidate) if candidate.is_dir() else None
    repository = Path(CONFIG["reference_repository_root"]).resolve()
    reference_before = {"commit": git_fact(repository, "rev-parse", "HEAD"), "tree": git_fact(repository, "rev-parse", "HEAD^{tree}"),
                        "status": git_fact(repository, "status", "--porcelain=v1", "--untracked-files=all")}
    if reference_before != {"commit": CONFIG["reference_commit"], "tree": CONFIG["reference_tree"], "status": ""}:
        invalid.append("pinned reference provenance mismatch")
    results: list[dict[str, object]] = []
    if not invalid:
        env = dict(os.environ); env["PYTHONPATH"] = CONFIG["dependency_site"]
        env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        for root_id in order:
            try:
                child = subprocess.run([sys.executable, str(GATE / "run_root.py"), root_id, str(candidate), profile], cwd=GATE, env=env,
                                       text=True, encoding="utf-8", errors="replace", capture_output=True,
                                       timeout=CONFIG["root_timeout_seconds"], check=False)
            except subprocess.TimeoutExpired as exc:
                invalid.append(f"root timeout: {root_id}"); results.append({"root": root_id, "valid": False, "timeout": True, "stdout": exc.stdout, "stderr": exc.stderr}); continue
            if child.returncode != 0:
                invalid.append(f"unexpected root process status: {root_id}={child.returncode}"); results.append({"root": root_id, "valid": False, "stdout": child.stdout, "stderr": child.stderr}); continue
            try: record = json.loads(child.stdout)
            except json.JSONDecodeError:
                invalid.append(f"malformed root receipt: {root_id}"); record = {"root": root_id, "valid": False, "stdout": child.stdout, "stderr": child.stderr}
            if record.get("root") != root_id or record.get("valid") is not True or record.get("phase") != "call": invalid.append(f"invalid root receipt: {root_id}")
            results.append(record)
    tree_after = sha256_tree(candidate) if candidate.is_dir() else None
    if tree_before != tree_after: invalid.append("candidate tree changed during scoring")
    reference_after = {"commit": git_fact(repository, "rev-parse", "HEAD"), "tree": git_fact(repository, "rev-parse", "HEAD^{tree}"),
                       "status": git_fact(repository, "status", "--porcelain=v1", "--untracked-files=all")}
    if reference_before != reference_after: invalid.append("reference provenance changed during scoring")
    return {"schema": "spec2repo.score-receipt.v3", "case": CONFIG["case"], "constitution": CONFIG["constitution"],
            "gate_input_sha256": gate_input_sha256(), "candidate": str(candidate), "candidate_profile": profile,
            "candidate_tree_sha256_before": tree_before, "candidate_tree_sha256_after": tree_after,
            "reference_before": reference_before, "reference_after": reference_after, "mode": mode, "only": only,
            "valid": not invalid and len(results) == len(order), "invalid_reasons": invalid, "inventory": inventory,
            "order": order, "results": results, "score": score(results), "started_epoch": started, "finished_epoch": time.time()}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--candidate", required=True)
    parser.add_argument("--profile", choices=CONFIG["profiles"], required=True); parser.add_argument("--mode", choices=CONFIG["execution_modes"], default="natural")
    parser.add_argument("--only"); parser.add_argument("--output", required=True); args = parser.parse_args()
    receipt = run(Path(args.candidate), args.profile, args.mode, args.only); output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"valid": receipt["valid"], "score": receipt["score"], "output": str(output)}, ensure_ascii=False))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__": raise SystemExit(main())
