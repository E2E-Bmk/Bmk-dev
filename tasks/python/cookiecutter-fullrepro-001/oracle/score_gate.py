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
    files = sorted(path for path in root.rglob("*") if path.is_file() and not ignored.intersection(path.relative_to(root).parts))
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


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
                if node.decorator_list:
                    errors.append(f"decorated root: {node.name}")
                discovered[node.name] = filename
    expected_functions = {str(row["function"]) for row in expected_rows()}
    if set(discovered) != expected_functions:
        errors.append("test function inventory differs from ROOT-MAP.json")
    ids = [str(row["id"]) for row in expected_rows()]
    expected_ids = [*(f"A{i:02d}" for i in range(1, 25)), *(f"I{i:02d}" for i in range(1, 37)), *(f"S{i:02d}" for i in range(1, 13))]
    if ids != expected_ids:
        errors.append("root id inventory or order is invalid")
    return ids, errors


def candidate_policy_errors(candidate: Path, reference_source: Path) -> list[str]:
    if candidate == reference_source or not candidate.is_dir():
        return []
    errors: list[str] = []
    forbidden_imports = {"cookiecutter", "requests", "httpx", "socket"}
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
        relative = path.relative_to(candidate)
        if relative.parts and relative.parts[0] == "cookiecutter":
            imports.discard("cookiecutter")
        blocked = sorted(imports & forbidden_imports)
        if blocked:
            errors.append(f"forbidden candidate import in {relative.as_posix()}: {','.join(blocked)}")
        if "urllib" in imports and "urllib.request" in text:
            errors.append(f"forbidden candidate network import in {relative.as_posix()}: urllib.request")
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
    system_ids = {row["id"] for row in ROOT_MAP["composition"] if row["tier"] == "system_e2e"}
    mutation_ids = set(ROOT_MAP["mutation_expected_fail"])
    native_ids = set(ROOT_MAP["mutation_expected_pass"])
    passed_ids = {item["root"] for item in results if item.get("passed") is True}
    conditional_ids = {row["id"] for row in ROOT_MAP["composition"] if set(row["depends_on"]).issubset(passed_ids)}
    atomic = metric(results, atomic_ids)
    composition = metric(results, composition_ids)
    conditional = metric(results, conditional_ids)
    combined = round((atomic["rate"] + composition["rate"]) / 2, 6) if atomic["rate"] is not None and composition["rate"] is not None else None
    gap = round(atomic["rate"] - composition["rate"], 6) if atomic["rate"] is not None and composition["rate"] is not None else None
    adjusted = round(atomic["rate"] - conditional["rate"], 6) if atomic["rate"] is not None and conditional["rate"] is not None else None
    families = sorted({str(row.get("family")) for row in expected_rows() if row.get("family")})
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
        "mutation_families": {family:metric(results, {str(row["id"]) for row in expected_rows() if row.get("family") == family}) for family in families},
    }


def candidate_provenance(candidate: Path, candidate_mode: str, candidate_id: str | None, provenance_path: Path | None, tree_sha256: str | None, reference_source: Path) -> tuple[dict[str, object], list[str]]:
    errors: list[str] = []
    dummy = (GATE / "_dummy").resolve()
    record: dict[str, object] = {"mode":candidate_mode,"candidate_id":candidate_id,"root":str(candidate),"tree_sha256":tree_sha256}
    if candidate_mode == "reference":
        if tree_sha256 != PROVENANCE["source_tree_sha256"]:
            errors.append("reference candidate mode requires a byte-identical fresh root of the pinned reference source")
        record.update({"commit":PROVENANCE["commit"],"source_tree_sha256":PROVENANCE["source_tree_sha256"]})
    elif candidate_mode == "dummy":
        dummy_sha256 = sha256_tree(dummy)
        if tree_sha256 != dummy_sha256:
            errors.append("dummy candidate mode requires a byte-identical fresh root of the gate-owned dummy")
        record.update({"kind":"behavior-empty-control","control_tree_sha256":dummy_sha256})
    elif candidate_mode in {"anchor", "sealed"}:
        if candidate in {reference_source, dummy}:
            errors.append(f"{candidate_mode} candidate mode requires an independent source tree")
        if not candidate_id:
            errors.append(f"{candidate_mode} candidate mode requires --candidate-id")
        if provenance_path is None or not provenance_path.is_file():
            errors.append(f"{candidate_mode} candidate mode requires a provenance JSON document")
        else:
            try:
                document = json.loads(provenance_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                errors.append(f"anchor provenance is unreadable: {exc}")
            else:
                expected_schema = (
                    "spec2repo.anchor-candidate-provenance.v1"
                    if candidate_mode == "anchor"
                    else "spec2repo.sealed-candidate-provenance.v1"
                )
                if document.get("schema") != expected_schema:
                    errors.append(f"{candidate_mode} provenance schema is invalid")
                if document.get("candidate_id") != candidate_id:
                    errors.append(f"{candidate_mode} provenance candidate_id does not match")
                if document.get("candidate_tree_sha256") != tree_sha256:
                    errors.append(f"{candidate_mode} provenance candidate tree hash does not match")
                if candidate_mode == "anchor" and not document.get("payload_manifest_sha256"):
                    errors.append("anchor provenance omits payload_manifest_sha256")
                record.update({"manifest_path":str(provenance_path.resolve()),"manifest_sha256":sha256_file(provenance_path),"manifest":document})
    elif candidate_mode == "arbitrary":
        if candidate_id is not None:
            record["candidate_id"] = candidate_id
        if provenance_path is not None:
            if not provenance_path.is_file():
                errors.append("arbitrary candidate provenance path is absent")
            else:
                record.update({"manifest_path":str(provenance_path.resolve()),"manifest_sha256":sha256_file(provenance_path)})
    return record, errors


def run(candidate: Path, mode: str, only: str | None, control_profile: str, candidate_mode: str = "arbitrary", candidate_id: str | None = None, provenance_path: Path | None = None) -> dict[str, object]:
    started = time.time()
    candidate = candidate.resolve()
    inventory, invalid = static_inventory()
    if not candidate.is_dir():
        invalid.append("candidate directory is absent")
    elif not (candidate / "cookiecutter" / "__init__.py").is_file():
        invalid.append("candidate does not contain cookiecutter/__init__.py")
    reference_source = (GATE / PROVENANCE["source"]).resolve()
    if control_profile != "none" and candidate_mode != "reference":
        invalid.append("synthetic control profiles require reference candidate mode")
    if candidate_mode in {"anchor", "sealed", "arbitrary", "dummy"} and control_profile != "none":
        invalid.append("non-reference candidate modes cannot enable a synthetic control profile")
    if candidate_mode != "reference":
        invalid.extend(candidate_policy_errors(candidate, reference_source))
    order = [only] if only else ordered_roots(mode)
    if only and only not in inventory:
        invalid.append(f"unknown root: {only}")
    tree_before = sha256_tree(candidate) if candidate.is_dir() else None
    provenance, provenance_errors = candidate_provenance(candidate, candidate_mode, candidate_id, provenance_path, tree_before, reference_source)
    invalid.extend(provenance_errors)
    provenance_hash_before = sha256_file(provenance_path) if provenance_path is not None and provenance_path.is_file() else None
    results: list[dict[str, object]] = []
    if not invalid:
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        if control_profile != "none":
            env["COOKIECUTTER_SYNTHETIC_PROFILE"] = control_profile
        else:
            env.pop("COOKIECUTTER_SYNTHETIC_PROFILE", None)
        if control_profile == "concurrency-stall":
            env["COOKIECUTTER_EVALUATOR_CONCURRENCY_CONTROL"] = "stall-first-worker"
        else:
            env.pop("COOKIECUTTER_EVALUATOR_CONCURRENCY_CONTROL", None)
        if candidate_mode == "reference" and control_profile == "none":
            env["COOKIECUTTER_SYNTHETIC_API_SCAFFOLD"] = "1"
        else:
            env.pop("COOKIECUTTER_SYNTHETIC_API_SCAFFOLD", None)
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
    provenance_hash_after = sha256_file(provenance_path) if provenance_path is not None and provenance_path.is_file() else None
    if provenance_hash_before != provenance_hash_after:
        invalid.append("candidate provenance changed during scoring")
    return {
        "schema":"spec2repo.score-receipt.v2",
        "case":CONFIG["case"],
        "constitution":CONFIG["constitution"],
        "scoring_formula":CONFIG["scoring_formula"],
        "candidate":str(candidate),
        "candidate_mode":candidate_mode,
        "candidate_id":candidate_id,
        "candidate_provenance":provenance,
        "candidate_provenance_sha256_before":provenance_hash_before,
        "candidate_provenance_sha256_after":provenance_hash_after,
        "candidate_tree_sha256_before":tree_before,
        "candidate_tree_sha256_after":tree_after,
        "mode":mode,
        "only":only,
        "control_profile":control_profile,
        "reference_patch":control_profile == "full",
        "reference_api_scaffold":candidate_mode == "reference" and control_profile == "none",
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
    parser.add_argument("--reference-patch", action="store_true", help="alias for --control-profile full")
    parser.add_argument("--control-profile", choices=["none","full","incomplete-transaction","concurrency-stall"], default="none")
    parser.add_argument("--candidate-mode", choices=["reference","dummy","anchor","sealed","arbitrary"], default="arbitrary")
    parser.add_argument("--candidate-id")
    parser.add_argument("--candidate-provenance", type=Path)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    profile = "full" if args.reference_patch else args.control_profile
    receipt = run(Path(args.candidate), args.mode, args.only, profile, args.candidate_mode, args.candidate_id, args.candidate_provenance)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"valid":receipt["valid"],"score":receipt["score"],"output":str(output)}, ensure_ascii=False))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
