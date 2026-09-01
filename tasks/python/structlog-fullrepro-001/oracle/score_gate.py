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
RUNTIME_PROVENANCE = json.loads((GATE / "RUNTIME-PROVENANCE.json").read_text(encoding="utf-8"))
GATE_INPUTS = (
    "SPEC.md", "TASK.md", "ENVIRONMENT-CONTRACT.md", "ANCHOR-ADMISSION-PREREG.md",
    "ROOT-MAP.json", "MUTATION-PORTFOLIO.json", "SCORER-CONFIG.json", "RUNTIME-PROVENANCE.json",
    "ANCHOR-PAYLOAD-MANIFEST.json", "seal_anchor_payload.py",
    "anchor-payload/TASK.md", "anchor-payload/SPEC.md", "anchor-payload/ENVIRONMENT-CONTRACT.md",
    "run_root.py", "score_gate.py", "audit_prefreeze.py", "finalize_gate.py",
    "reference-overlay/structlog_delivery_reference.py", "clean-api-scaffold/structlog_delivery_scaffold.py",
    "dummy/structlog/__init__.py", "source-blank-shallow/structlog/__init__.py",
    "source-blank-shallow/structlog/delivery.py", "tests/__init__.py", "tests/delivery_support.py",
    "tests/test_native_controls.py", "tests/test_delivery_atomic.py", "tests/test_delivery_integration.py",
    "tests/test_delivery_system.py",
)


def sha256_tree(root: Path) -> str:
    digest = hashlib.sha256()
    ignored = {".git", "__pycache__", ".pytest_cache", ".tmp"}
    files = sorted(path for path in root.rglob("*") if path.is_file() and not ignored.intersection(path.relative_to(root).parts))
    for path in files:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        data = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big")); digest.update(relative)
        digest.update(len(data).to_bytes(8, "big")); digest.update(data)
    return digest.hexdigest()


def rows():
    return [*ROOT_MAP["atomic"], *ROOT_MAP["composition"]]


def gate_input_sha256() -> str:
    digest = hashlib.sha256()
    for name in GATE_INPUTS:
        data = (GATE / name).read_bytes(); encoded = name.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big")); digest.update(encoded)
        digest.update(len(data).to_bytes(8, "big")); digest.update(data)
    return digest.hexdigest()


def module_for(root_id: str) -> str:
    native = {*(f"A{i:02d}" for i in range(1, 7)), *(f"I{i:02d}" for i in range(1, 5)), *(f"S{i:02d}" for i in range(1, 5))}
    if root_id in native: return "test_native_controls.py"
    if root_id.startswith("A"): return "test_delivery_atomic.py"
    if root_id.startswith("I"): return "test_delivery_integration.py"
    return "test_delivery_system.py"


def static_inventory():
    expected = [*(f"A{i:02d}" for i in range(1, 17)), *(f"I{i:02d}" for i in range(1, 25)), *(f"S{i:02d}" for i in range(1, 9))]
    ids = [str(row["id"]) for row in rows()]
    errors: list[str] = []
    if ids != expected:
        errors.append("root inventory/order differs from 16A+24I+8S")
    for root_id in ids:
        path = GATE / "tests" / module_for(root_id)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (UnicodeDecodeError, SyntaxError) as exc:
            errors.append(f"invalid test source: {path}: {exc}"); continue
        functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        function = functions.get(f"test_{root_id.lower()}")
        if function is None:
            errors.append(f"missing root function: {root_id}"); continue
        names = [item.arg for item in [*function.args.posonlyargs, *function.args.args, *function.args.kwonlyargs]]
        if names != ["tmp_path"] or function.args.vararg or function.args.kwarg or function.decorator_list:
            errors.append(f"invalid root signature: {root_id}")
    mutation = {str(row["id"]) for row in rows() if row["mutation"]}
    native = set(ids) - mutation
    portfolio = json.loads((GATE / "MUTATION-PORTFOLIO.json").read_text(encoding="utf-8"))
    declared = {item for values in portfolio["families"].values() for item in values}
    if mutation != declared or native != set(portfolio["native"]):
        errors.append("mutation/native partition mismatch")
    if len(mutation) != 34 or len(native) != 14:
        errors.append("portfolio is not 34 mutation plus 14 native")
    if max(map(len, portfolio["families"].values()), default=0) > 5:
        errors.append("mutation family exceeds five roots")
    dependencies = {str(dep) for row in rows() for dep in row.get("depends_on", ())}
    if not dependencies.issubset(ids):
        errors.append("unknown dependency root")
    return ids, errors


def candidate_policy_errors(candidate: Path, profile: str):
    errors: list[str] = []
    reference = Path(CONFIG["reference_package_root"]).resolve()
    dummy = (GATE / "dummy").resolve(); shallow = (GATE / "source-blank-shallow").resolve()
    if not candidate.is_dir() or not (candidate / "structlog" / "__init__.py").is_file():
        return ["candidate lacks structlog/__init__.py"]
    if profile in {"reference", "clean", "broad-generation-collapse", "broad-retry-collapse"} and candidate != reference:
        errors.append(f"{profile} requires pinned reference package root")
    if profile == "dummy" and candidate != dummy:
        errors.append("dummy profile requires sealed dummy root")
    if profile == "source-blank-shallow" and candidate != shallow:
        errors.append("source-blank-shallow profile requires sealed shallow root")
    if profile in {"anchor", "arbitrary"} and candidate in {reference, dummy, shallow}:
        errors.append("independent candidate required")
    for path in candidate.rglob("*"):
        if path.is_symlink():
            errors.append(f"candidate symlink forbidden: {path}")
        elif path.is_file() and path.suffix == ".py":
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", SyntaxWarning)
                    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except (UnicodeDecodeError, SyntaxError) as exc:
                errors.append(f"invalid candidate Python source: {path}: {exc}")
    return errors


def order_for(mode: str):
    values = [str(row["id"]) for row in rows()]
    if mode == "reverse": values.reverse()
    elif mode == "permuted": random.Random(CONFIG["permutation_seed"]).shuffle(values)
    return values


def rate(passed, total):
    return round(passed / total, 8) if total else None


def metric(results, ids):
    selected = [item for item in results if item["root"] in ids]
    passed = sum(item.get("passed") is True for item in selected)
    return {"passed": passed, "total": len(selected), "rate": rate(passed, len(selected))}


def score(results):
    atomic_ids = {str(row["id"]) for row in ROOT_MAP["atomic"]}
    composition_ids = {str(row["id"]) for row in ROOT_MAP["composition"]}
    integration_ids = {str(row["id"]) for row in ROOT_MAP["composition"] if row["tier"] == "integration"}
    system_ids = composition_ids - integration_ids
    mutation_ids = {str(row["id"]) for row in rows() if row["mutation"]}
    native_ids = (atomic_ids | composition_ids) - mutation_ids
    passed_ids = {str(item["root"]) for item in results if item.get("passed") is True}
    conditional_ids = {str(row["id"]) for row in ROOT_MAP["composition"] if set(row.get("depends_on", ())).issubset(passed_ids)}
    atomic = metric(results, atomic_ids); composition = metric(results, composition_ids); conditional = metric(results, conditional_ids)
    return {
        "all_roots": metric(results, atomic_ids | composition_ids), "atomic": atomic, "composition": composition,
        "integration": metric(results, integration_ids), "system_e2e": metric(results, system_ids),
        "combined_rate": metric(results, atomic_ids | composition_ids)["rate"],
        "gap": round(atomic["rate"] - composition["rate"], 8) if atomic["rate"] is not None and composition["rate"] is not None else None,
        "conditional_composition": conditional,
        "adjusted_gap": round(atomic["rate"] - conditional["rate"], 8) if conditional["rate"] is not None else None,
        "mutation_designated": metric(results, mutation_ids), "native_controls": metric(results, native_ids),
        "mutation_families": {family: metric(results, {str(row["id"]) for row in rows() if row.get("family") == family})
                              for family in sorted({str(row.get("family")) for row in rows() if row.get("family")})},
    }


def git_fact(repository: Path, *arguments):
    child = subprocess.run([CONFIG["git_executable"], "-c", f"safe.directory={repository}", "-C", str(repository), *arguments],
                           text=True, encoding="utf-8", errors="replace", capture_output=True, check=False)
    return child.stdout.strip() if child.returncode == 0 else None


def run(candidate: Path, profile: str, mode: str, only: str | None):
    started = time.time(); candidate = candidate.resolve()
    inventory, invalid = static_inventory(); invalid.extend(candidate_policy_errors(candidate, profile))
    order = [only] if only else order_for(mode)
    if only and only not in inventory: invalid.append(f"unknown root: {only}")
    tree_before = sha256_tree(candidate) if candidate.is_dir() else None
    runtime = Path(CONFIG["runtime_site"]).resolve(); runtime_before = sha256_tree(runtime)
    if runtime_before != RUNTIME_PROVENANCE["tree_sha256"]:
        invalid.append("declared runtime provenance mismatch")
    repository = Path(CONFIG["reference_repository_root"]).resolve()
    reference_before = {"commit": git_fact(repository, "rev-parse", "HEAD"), "tree": git_fact(repository, "rev-parse", "HEAD^{tree}"),
                        "status": git_fact(repository, "status", "--porcelain=v1", "--untracked-files=all")}
    if reference_before != {"commit": CONFIG["reference_commit"], "tree": CONFIG["reference_tree"], "status": ""}:
        invalid.append("pinned reference provenance mismatch")
    results = []
    if not invalid:
        env = dict(os.environ)
        env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", PYTHONUTF8="1", SPEC2REPO_STRUCTLOG_RUNTIME=str(runtime))
        env.pop("PYTHONPATH", None)
        for root_id in order:
            try:
                child = subprocess.run([sys.executable, str(GATE / "run_root.py"), root_id, str(candidate), profile], cwd=GATE, env=env,
                                       text=True, encoding="utf-8", errors="replace", capture_output=True,
                                       timeout=CONFIG["root_timeout_seconds"], check=False)
            except subprocess.TimeoutExpired as exc:
                invalid.append(f"root timeout: {root_id}"); results.append({"root": root_id, "valid": False, "timeout": True, "stdout": exc.stdout, "stderr": exc.stderr}); continue
            if child.returncode != 0:
                invalid.append(f"unexpected root process status: {root_id}={child.returncode}")
                results.append({"root": root_id, "valid": False, "stdout": child.stdout, "stderr": child.stderr}); continue
            try: record = json.loads(child.stdout)
            except json.JSONDecodeError:
                invalid.append(f"malformed root receipt: {root_id}"); record = {"root": root_id, "valid": False, "stdout": child.stdout, "stderr": child.stderr}
            if record.get("root") != root_id or record.get("valid") is not True or record.get("phase") != "call":
                invalid.append(f"invalid root receipt: {root_id}")
            results.append(record)
    tree_after = sha256_tree(candidate) if candidate.is_dir() else None
    runtime_after = sha256_tree(runtime)
    if tree_before != tree_after: invalid.append("candidate tree changed during scoring")
    if runtime_before != runtime_after: invalid.append("runtime tree changed during scoring")
    reference_after = {"commit": git_fact(repository, "rev-parse", "HEAD"), "tree": git_fact(repository, "rev-parse", "HEAD^{tree}"),
                       "status": git_fact(repository, "status", "--porcelain=v1", "--untracked-files=all")}
    if reference_before != reference_after: invalid.append("reference provenance changed during scoring")
    return {"schema":"spec2repo.score-receipt.v4", "case":CONFIG["case"], "constitution":CONFIG["constitution"],
            "gate_input_sha256":gate_input_sha256(), "candidate":str(candidate), "candidate_profile":profile,
            "candidate_tree_sha256_before":tree_before, "candidate_tree_sha256_after":tree_after,
            "runtime_tree_sha256_before":runtime_before, "runtime_tree_sha256_after":runtime_after,
            "reference_before":reference_before, "reference_after":reference_after, "mode":mode, "only":only,
            "valid":not invalid and len(results) == len(order), "invalid_reasons":invalid, "inventory":inventory,
            "order":order, "results":results, "score":score(results), "started_epoch":started, "finished_epoch":time.time()}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--candidate", required=True)
    parser.add_argument("--profile", choices=CONFIG["profiles"], required=True)
    parser.add_argument("--mode", choices=CONFIG["execution_modes"], default="natural")
    parser.add_argument("--only"); parser.add_argument("--output", required=True); args = parser.parse_args()
    receipt = run(Path(args.candidate), args.profile, args.mode, args.only)
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"valid": receipt["valid"], "score": receipt["score"], "output": str(output)}, ensure_ascii=False))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
