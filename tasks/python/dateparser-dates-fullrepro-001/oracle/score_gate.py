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
CONTROL_MODES = {item["mode"] for item in json.loads((GATE / "INCOMPLETE-CONTROLS.json").read_text(encoding="utf-8"))["controls"]}


def all_rows() -> list[dict[str, object]]:
    return [*ROOT_MAP["atomic"], *ROOT_MAP["composition"], *ROOT_MAP["e2e"]]


def sha256_tree(root: Path) -> str:
    digest = hashlib.sha256()
    ignored = {".git", "__pycache__", ".pytest_cache"}
    files = sorted(path for path in root.rglob("*") if path.is_file() and not ignored.intersection(path.relative_to(root).parts))
    for path in files:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        data = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def static_inventory() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    found: set[str] = set()
    for filename in ("test_atomic.py", "test_composition.py", "test_e2e.py"):
        path = GATE / "tests" / filename
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                found.add(node.name)
                if node.decorator_list or node.args.args or node.args.posonlyargs or node.args.kwonlyargs or node.args.vararg or node.args.kwarg:
                    errors.append(f"root is decorated or has arguments: {node.name}")
    expected_functions = {str(row["function"]) for row in all_rows()}
    if found != expected_functions:
        errors.append("test function inventory differs from ROOT-MAP.json")
    ids = [str(row["id"]) for row in all_rows()]
    expected_ids = [*(f"A{i:02d}" for i in range(1, 21)), *(f"C{i:02d}" for i in range(1, 27)), *(f"E{i:02d}" for i in range(1, 5))]
    if ids != expected_ids:
        errors.append("root id inventory or order is invalid")
    return ids, errors


def candidate_policy_errors(candidate: Path, reference: Path) -> list[str]:
    if candidate == reference or not candidate.is_dir():
        return []
    errors: list[str] = []
    forbidden = {"subprocess", "socket", "requests", "httpx"}
    for path in candidate.rglob("*"):
        if path.is_symlink():
            errors.append(f"candidate symlink is forbidden: {path.relative_to(candidate).as_posix()}")
            continue
        if not path.is_file() or path.suffix != ".py" or {".git", "__pycache__", ".pytest_cache"}.intersection(path.relative_to(candidate).parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=str(path))
        except (UnicodeDecodeError, SyntaxError) as exc:
            errors.append(f"invalid candidate Python: {path.relative_to(candidate).as_posix()}: {exc}")
            continue
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".", 1)[0])
        blocked = sorted(imports & forbidden)
        if blocked:
            errors.append(f"forbidden candidate import in {path.relative_to(candidate).as_posix()}: {','.join(blocked)}")
        if "urllib.request" in text:
            errors.append(f"forbidden candidate network import in {path.relative_to(candidate).as_posix()}: urllib.request")
    return errors


def ordered_roots(mode: str) -> list[str]:
    roots = [str(row["id"]) for row in all_rows()]
    if mode == "reverse":
        roots.reverse()
    elif mode == "permuted":
        random.Random(CONFIG["permutation_seed"]).shuffle(roots)
    return roots


def rate(passed: int, total: int) -> float | None:
    return round(passed / total, 6) if total else None


def metric(results: list[dict[str, object]], ids: set[str]) -> dict[str, object]:
    selected = [item for item in results if item["root"] in ids]
    passed = sum(item.get("passed") is True for item in selected)
    return {"passed": passed, "total": len(selected), "rate": rate(passed, len(selected))}


def score(results: list[dict[str, object]]) -> dict[str, object]:
    atomic_ids = {row["id"] for row in ROOT_MAP["atomic"]}
    integration_ids = {row["id"] for row in ROOT_MAP["composition"]}
    system_ids = {row["id"] for row in ROOT_MAP["e2e"]}
    composition_ids = integration_ids | system_ids
    mutation_ids = set(ROOT_MAP["mutation_expected_fail"])
    native_ids = set(ROOT_MAP["mutation_expected_pass"])
    passed_ids = {item["root"] for item in results if item.get("passed") is True}
    conditional_ids = {
        row["id"] for row in [*ROOT_MAP["composition"], *ROOT_MAP["e2e"]]
        if set(row["depends_on"]).issubset(passed_ids)
    }
    atomic = metric(results, atomic_ids)
    composition = metric(results, composition_ids)
    conditional = metric(results, conditional_ids)
    combined = gap = adjusted_gap = None
    if atomic["rate"] is not None and composition["rate"] is not None:
        combined = round((atomic["rate"] + composition["rate"]) / 2, 6)
        gap = round(atomic["rate"] - composition["rate"], 6)
    if atomic["rate"] is not None and conditional["rate"] is not None:
        adjusted_gap = round(atomic["rate"] - conditional["rate"], 6)
    owner_slices = {}
    for owner in sorted({row.get("owner") for row in ROOT_MAP["atomic"] if row.get("owner")} | {owner for row in [*ROOT_MAP["composition"], *ROOT_MAP["e2e"]] for owner in row.get("owners", [])}):
        ids = {row["id"] for row in ROOT_MAP["atomic"] if row.get("owner") == owner}
        ids |= {row["id"] for row in [*ROOT_MAP["composition"], *ROOT_MAP["e2e"]] if owner in row.get("owners", [])}
        owner_slices[owner] = metric(results, ids)
    return {
        "atomic": atomic,
        "composition_inclusive": composition,
        "combined_rate": combined,
        "gap": gap,
        "integration": metric(results, integration_ids),
        "system_e2e": metric(results, system_ids),
        "conditional_composition": conditional,
        "adjusted_gap": adjusted_gap,
        "all_roots": metric(results, atomic_ids | composition_ids),
        "mutation_designated": metric(results, mutation_ids),
        "native_controls": metric(results, native_ids),
        "owner_surfaces": owner_slices,
    }


def run(candidate: Path, mode: str, only: str | None, reference_patch: bool, control_mode: str | None) -> dict[str, object]:
    started = time.time()
    candidate = candidate.resolve()
    inventory, invalid = static_inventory()
    reference = (GATE / PROVENANCE["source"]).resolve()
    if not candidate.is_dir():
        invalid.append("candidate directory is absent")
    elif not (candidate / "dateparser" / "__init__.py").is_file():
        invalid.append("candidate does not contain dateparser/__init__.py")
    if reference_patch and candidate != reference:
        invalid.append("reference patch may only target the pinned reference source")
    if control_mode and (not reference_patch or control_mode not in CONTROL_MODES):
        invalid.append("control mode requires the patched reference and a preregistered mode")
    invalid.extend(candidate_policy_errors(candidate, reference))
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
            env["DATEPARSER_V4_REFERENCE_PATCH"] = "1"
        else:
            env.pop("DATEPARSER_V4_REFERENCE_PATCH", None)
        if control_mode:
            env["DATEPARSER_V4_CONTROL_MODE"] = control_mode
        else:
            env.pop("DATEPARSER_V4_CONTROL_MODE", None)
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
        "schema": "spec2repo.score-receipt.v4",
        "case": CONFIG["case"],
        "candidate": str(candidate),
        "candidate_tree_sha256_before": tree_before,
        "candidate_tree_sha256_after": tree_after,
        "mode": mode,
        "only": only,
        "reference_patch": reference_patch,
        "control_mode": control_mode,
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
    parser.add_argument("--mode", choices=CONFIG["execution_modes"], default="natural")
    parser.add_argument("--only")
    parser.add_argument("--reference-patch", action="store_true")
    parser.add_argument("--control-mode", choices=sorted(CONTROL_MODES))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    receipt = run(Path(args.candidate), args.mode, args.only, args.reference_patch, args.control_mode)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"valid": receipt["valid"], "score": receipt["score"], "output": str(output)}, ensure_ascii=False))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
