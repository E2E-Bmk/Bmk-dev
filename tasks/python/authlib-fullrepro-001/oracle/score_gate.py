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
PROVENANCE = json.loads((GATE / "REFERENCE-PROVENANCE.json").read_text(encoding="utf-8"))


def sha256_tree(root: Path) -> str:
    digest = hashlib.sha256()
    ignored = {".git", "__pycache__", ".pytest_cache"}
    files = sorted(
        path for path in root.rglob("*")
        if path.is_file() and not ignored.intersection(path.relative_to(root).parts)
    )
    for path in files:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        data = path.read_bytes()
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def expected_rows() -> list[dict[str, object]]:
    return [*ROOT_MAP["atomic"], *ROOT_MAP["composition"]]


def static_inventory() -> tuple[list[str], list[str]]:
    discovered: dict[str, str] = {}
    errors: list[str] = []
    for filename in ("test_atomic.py", "test_composition.py"):
        path = GATE / "tests" / filename
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                if node.args.args or node.args.posonlyargs or node.args.kwonlyargs or node.args.vararg or node.args.kwarg:
                    errors.append(f"non-zero-argument root: {node.name}")
                discovered[node.name] = filename
    expected_functions = {str(row["function"]) for row in expected_rows()}
    if set(discovered) != expected_functions:
        errors.append("test function inventory differs from ROOT-MAP.json")
    ids = [str(row["id"]) for row in expected_rows()]
    expected_ids = [*(f"A{i:02d}" for i in range(1, 21)), *(f"C{i:02d}" for i in range(1, 17))]
    if ids != expected_ids:
        errors.append("root id inventory or order is invalid")
    return ids, errors


def candidate_policy_errors(candidate: Path, reference_source: Path) -> list[str]:
    """Apply candidate-facing source-blank rules; the pinned reference is exempt."""
    if candidate == reference_source or not candidate.is_dir():
        return []
    errors: list[str] = []
    forbidden_imports = {"joserfc", "subprocess", "socket", "requests", "httpx"}
    for path in candidate.rglob("*"):
        if path.is_symlink():
            errors.append(f"candidate symlink is not allowed: {path.relative_to(candidate).as_posix()}")
            continue
        if not path.is_file() or path.suffix != ".py" or {"__pycache__", ".pytest_cache", ".git"}.intersection(path.relative_to(candidate).parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=str(path))
        except (UnicodeDecodeError, SyntaxError) as exc:
            errors.append(f"candidate source is not valid UTF-8 Python: {path.relative_to(candidate).as_posix()}: {exc}")
            continue
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".", 1)[0])
        blocked = sorted(imports & forbidden_imports)
        if blocked:
            errors.append(f"forbidden candidate import in {path.relative_to(candidate).as_posix()}: {','.join(blocked)}")
        if "urllib" in imports and "urllib.request" in text:
            errors.append(f"forbidden candidate network import in {path.relative_to(candidate).as_posix()}: urllib.request")
    return errors


def ordered_roots(mode: str) -> list[str]:
    roots = [str(row["id"]) for row in expected_rows()]
    if mode == "reverse":
        roots.reverse()
    elif mode == "permuted":
        random.Random(CONFIG["permutation_seed"]).shuffle(roots)
    return roots


def rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def metric(results: list[dict[str, object]], ids: set[str]) -> dict[str, object]:
    selected = [item for item in results if item["root"] in ids]
    passed = sum(item.get("passed") is True for item in selected)
    return {"passed": passed, "total": len(selected), "rate": rate(passed, len(selected))}


def score(results: list[dict[str, object]]) -> dict[str, object]:
    atomic_ids = {row["id"] for row in ROOT_MAP["atomic"]}
    composition_ids = {row["id"] for row in ROOT_MAP["composition"]}
    integration_ids = {row["id"] for row in ROOT_MAP["composition"] if row["tier"] == "integration"}
    e2e_ids = {row["id"] for row in ROOT_MAP["composition"] if row["tier"] == "system_e2e"}
    mutation_ids = set(ROOT_MAP["mutation_expected_fail"])
    native_ids = set(ROOT_MAP["mutation_expected_pass"])
    passed_ids = {item["root"] for item in results if item.get("passed") is True}
    conditional_ids = {
        row["id"] for row in ROOT_MAP["composition"]
        if set(row["depends_on"]).issubset(passed_ids)
    }
    atomic = metric(results, atomic_ids)
    composition = metric(results, composition_ids)
    conditional = metric(results, conditional_ids)
    combined = None
    gap = None
    adjusted_gap = None
    if atomic["rate"] is not None and composition["rate"] is not None:
        combined = round((atomic["rate"] + composition["rate"]) / 2, 6)
        gap = round(atomic["rate"] - composition["rate"], 6)
    if atomic["rate"] is not None and conditional["rate"] is not None:
        adjusted_gap = round(atomic["rate"] - conditional["rate"], 6)
    return {
        "atomic": atomic,
        "composition": composition,
        "combined_rate": combined,
        "gap": gap,
        "integration": metric(results, integration_ids),
        "system_e2e": metric(results, e2e_ids),
        "conditional_composition": conditional,
        "adjusted_gap": adjusted_gap,
        "mutation_designated": metric(results, mutation_ids),
        "native_controls": metric(results, native_ids),
    }


def run(candidate: Path, mode: str, only: str | None, reference_patch: bool) -> dict[str, object]:
    started = time.time()
    candidate = candidate.resolve()
    inventory, invalid = static_inventory()
    if not candidate.is_dir():
        invalid.append("candidate directory is absent")
    elif not (candidate / "authlib" / "__init__.py").is_file():
        invalid.append("candidate does not contain authlib/__init__.py")
    reference_source = (GATE / PROVENANCE["source"]).resolve()
    if reference_patch and candidate != reference_source:
        invalid.append("reference patch may only target pinned reference source")
    invalid.extend(candidate_policy_errors(candidate, reference_source))
    order = [only] if only else ordered_roots(mode)
    if only and only not in inventory:
        invalid.append(f"unknown root: {only}")
    tree_before = sha256_tree(candidate) if candidate.is_dir() else None
    results: list[dict[str, object]] = []
    if not invalid:
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        if reference_patch:
            env["AUTHLIB_SYNTHETIC_REFERENCE_PATCH"] = "1"
        else:
            env.pop("AUTHLIB_SYNTHETIC_REFERENCE_PATCH", None)
        for root_id in order:
            try:
                child = subprocess.run(
                    [sys.executable, str(GATE / "run_root.py"), root_id, str(candidate)],
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
    return {
        "schema":"spec2repo.score-receipt.v2",
        "case":CONFIG["case"],
        "candidate":str(candidate),
        "candidate_tree_sha256_before":tree_before,
        "candidate_tree_sha256_after":tree_after,
        "mode":mode,
        "only":only,
        "reference_patch":reference_patch,
        "valid":not invalid and len(results) == len(order),
        "invalid_reasons":invalid,
        "inventory":inventory,
        "order":order,
        "results":results,
        "score":score(results),
        "started_epoch":started,
        "finished_epoch":time.time()
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--mode", choices=CONFIG["execution_modes"], default="natural")
    parser.add_argument("--only")
    parser.add_argument("--reference-patch", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    receipt = run(Path(args.candidate), args.mode, args.only, args.reference_patch)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"valid":receipt["valid"],"score":receipt["score"],"output":str(output)}, ensure_ascii=False))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
