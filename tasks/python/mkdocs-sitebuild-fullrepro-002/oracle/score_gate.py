#!/usr/bin/env python3
"""Strict fresh-process scorer for the MkDocs v14 formal gate."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback
from typing import Any

from anchor_protocol import candidate_tree_snapshot, verify_admission
from audit_public_operations import audit as audit_public_operations
from audit_record_shapes import audit as audit_record_shapes

GATE = Path(__file__).resolve().parent
CONFIG = json.loads((GATE / "SCORER-CONFIG.json").read_text(encoding="utf-8"))
ROOT_MAP = json.loads((GATE / "ROOT-MAP.json").read_text(encoding="utf-8"))


class InvalidRun(RuntimeError):
    pass


def require(value: bool, message: str) -> None:
    if not value:
        raise InvalidRun(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def aggregate(files: dict[str, str]) -> str:
    return hashlib.sha256("".join(f"{name}\t{digest}\n" for name, digest in sorted(files.items())).encode("utf-8")).hexdigest()


def gate_snapshot() -> dict[str, Any]:
    files: dict[str, str] = {}
    for relative in CONFIG["gate_files"]:
        path = GATE / relative
        require(path.is_file() and not path.is_symlink(), f"missing/unsafe gate file: {relative}")
        path.read_bytes().decode("utf-8", "strict")
        files[relative] = sha256(path)
    return {"files": files, "file_count": len(files), "aggregate_sha256": aggregate(files)}


def tree_snapshot(root: Path) -> dict[str, Any]:
    excluded = {".git", ".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache", ".tox", ".nox", "build", "dist"}
    files: dict[str, str] = {}
    for current, dirs, names in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        require(not any((current_path / name).is_symlink() for name in dirs), f"directory symlink under candidate: {current}")
        dirs[:] = sorted(name for name in dirs if name not in excluded)
        for name in sorted(names):
            path = current_path / name
            require(path.is_file() and not path.is_symlink(), f"unsafe candidate file: {path}")
            files[path.relative_to(root).as_posix()] = sha256(path)
    return {"files": files, "file_count": len(files), "aggregate_sha256": aggregate(files)}


def git(source: Path, *args: str) -> str:
    done = subprocess.run(["git", "-c", f"safe.directory={source}", "-C", str(source), *args], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False)
    require(done.returncode == 0, f"git {' '.join(args)} failed: {done.stderr.decode('utf-8', 'replace')}")
    return done.stdout.decode("utf-8", "strict").strip()


def provenance(mode: str, candidate: Path, candidate_seal: Path | None) -> dict[str, Any]:
    if mode == "anchor":
        require(candidate_seal is not None, "anchor mode requires a candidate admission seal")
        return verify_admission(candidate_seal, candidate)
    require(candidate_seal is None, "candidate admission seal is only valid in anchor mode")
    if mode == "dummy":
        require(candidate == (GATE / "dummy").resolve(), "dummy root mismatch")
        return {"kind": "behavior-empty", "root": str(candidate)}
    reference = CONFIG["reference"]
    require(candidate == (GATE / reference["source_root"]).resolve(), "reference source root mismatch")
    require(git(candidate, "rev-parse", "HEAD") == reference["commit"], "reference commit mismatch")
    require(git(candidate, "rev-parse", "HEAD^{tree}") == reference["tree"], "reference tree mismatch")
    status = git(candidate, "status", "--porcelain=v1", "--untracked-files=all").splitlines()
    build_path = candidate / "mkdocs" / "commands" / "build.py"
    recovery_path = candidate / "mkdocs" / "commands" / "_recovery.py"
    if mode == "m1":
        require(status == ["M mkdocs/commands/build.py", "?? mkdocs/commands/_recovery.py"], f"patched source status mismatch: {status}")
        require(sha256(build_path) == reference["patched_build_sha256"], "patched build hash mismatch")
        require(recovery_path.is_file() and sha256(recovery_path) == reference["recovery_sha256"], "recovery overlay hash mismatch")
    else:
        require(status == [], f"M2 source is not clean: {status}")
        require(sha256(build_path) == reference["clean_build_sha256"], "clean build hash mismatch")
        require(not recovery_path.exists(), "clean M2 contains recovery overlay")
    return {"kind": mode, "commit": reference["commit"], "tree": reference["tree"], "status": status, "build_sha256": sha256(build_path), "recovery_sha256": sha256(recovery_path) if recovery_path.exists() else None}


def static_registry() -> list[dict[str, Any]]:
    roots = ROOT_MAP["roots"]
    ids = [row["id"] for row in roots]
    expected = [f"A{i:02d}" for i in range(1, 13)] + [f"I{i:02d}" for i in range(1, 15)] + [f"S{i:02d}" for i in range(1, 11)]
    require(ids == expected and len(ids) == len(set(ids)), "ROOT-MAP registry mismatch")
    require(sum(row["layer"] == "Atomic" for row in roots) == 12 and sum(row["layer"] == "Integration" for row in roots) == 14 and sum(row["layer"] == "System" for row in roots) == 10, "layer counts mismatch")
    require(sum(bool(row["mutation"]) for row in roots) == 26, "mutation count mismatch")
    require(all(len(row["owners"]) == 1 and not row["prerequisites"] for row in roots if row["layer"] == "Atomic"), "Atomic structure invalid")
    require(all(len(row["owners"]) >= 2 and row["prerequisites"] for row in roots if row["layer"] != "Atomic"), "Composition structure invalid")
    tree = ast.parse((GATE / "probe_root.py").read_text(encoding="utf-8"))
    functions = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    require(set(ids) <= functions, "oracle root function missing")
    require(set(CONFIG["expected"]["m1"]) == set(ids) and set(CONFIG["expected"]["m2"]) == set(ids[:6] + ids[12:16]) and CONFIG["expected"]["dummy"] == [], "expected vector registration mismatch")
    require(ROOT_MAP["suite"] == CONFIG["suite"] == "mkdocs-v14-formal-a", "suite registry mismatch")
    require(CONFIG["protocol"]["anchor_mode"] == "sealed-arbitrary-candidate-v1", "anchor mode registration mismatch")
    operation_audit = audit_public_operations()
    require(operation_audit["valid"] is True, f"public-operation audit failed: {operation_audit['failures']}")
    require(operation_audit["public_import_count"] == 14 and operation_audit["operation_count"] == 44, "public-operation audit cardinality mismatch")
    require(operation_audit["resource_warning_contract"] is True, "resource/warning lifecycle contract missing")
    record_audit = audit_record_shapes()
    require(record_audit["valid"] is True, f"record-shape audit failed: {record_audit['failures']}")
    require(record_audit["owner_count"] == 6 and record_audit["direct_path_count"] == 36, "record-shape audit cardinality mismatch")
    return roots


def orders(ids: list[str]) -> dict[str, list[str]]:
    start = int(CONFIG["protocol"]["permutation_start_zero_based"])
    stride = int(CONFIG["protocol"]["permutation_stride"])
    require(math.gcd(stride, len(ids)) == 1, "permutation stride is not coprime")
    result = {"natural": ids[:], "reverse": list(reversed(ids)), "permuted": [ids[(start + stride * i) % len(ids)] for i in range(len(ids))]}
    require(list(result) == CONFIG["protocol"]["orders"] and all(len(order) == len(ids) and set(order) == set(ids) for order in result.values()), "order vector invalid")
    return result


def root_process(root_id: str, candidate: Path, receipt: Path) -> dict[str, Any]:
    env = dict(os.environ)
    dependency_site = (GATE / CONFIG["environment"]["dependency_site_packages"]).resolve()
    require(dependency_site.is_dir(), "dependency site-packages missing")
    env.update({"PYTHONPATH": str(dependency_site), "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1", "PYTHONHASHSEED": "0", "PIP_NO_INDEX": "1"})
    done = subprocess.run([sys.executable, "-s", "-X", "utf8", "-B", str(GATE / "probe_root.py"), "--root", root_id, "--candidate-root", str(candidate), "--output", str(receipt)], cwd=GATE, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=CONFIG["protocol"]["per_root_timeout_seconds"], check=False)
    require(receipt.is_file(), f"{root_id} emitted no receipt")
    value = json.loads(receipt.read_text(encoding="utf-8"))
    require(done.returncode in {0, 2}, f"{root_id} abnormal return {done.returncode}")
    require(value.get("root") == root_id, f"{root_id} receipt identity mismatch")
    require(value.get("valid") is True and done.returncode == 0, f"{root_id} invalid: {value}; stderr={done.stderr.decode('utf-8','replace')[-1200:]}")
    require(value.get("phase") == "semantic-call", f"{root_id} did not reach semantic-call phase: {value}")
    require(value.get("passed") in {True, False}, f"{root_id} missing pass boolean")
    return value


def rates(vector: dict[str, bool], roots: list[dict[str, Any]]) -> dict[str, Any]:
    def layer(name: str) -> tuple[int, int, float]:
        selected = [row["id"] for row in roots if row["layer"] == name]
        passed = sum(vector[root] for root in selected)
        return passed, len(selected), passed / len(selected)
    ap, at, ar = layer("Atomic"); ip, it, ir = layer("Integration"); sp, st, sr = layer("System")
    composition_ids = [row["id"] for row in roots if row["layer"] != "Atomic"]
    cp = sum(vector[root] for root in composition_ids); ct = len(composition_ids); cr = cp / ct
    eligible = [row for row in roots if row["layer"] != "Atomic" and all(vector[item] for item in row["prerequisites"])]
    conditional = (sum(vector[row["id"]] for row in eligible) / len(eligible)) if eligible else None
    mutation_ids = [row["id"] for row in roots if row["mutation"]]; ordinary_ids = [row["id"] for row in roots if not row["mutation"]]
    combined = (ar + cr) / 2
    return {
        "Atomic": {"passed": ap, "total": at, "rate": ar}, "Integration": {"passed": ip, "total": it, "rate": ir}, "System": {"passed": sp, "total": st, "rate": sr},
        "Composition": {"passed": cp, "total": ct, "rate": cr}, "native_all_root_rate": sum(vector.values()) / len(vector),
        "Combined": combined, "raw_Gap": ar - cr,
        "conditional_Composition": {"eligible": len(eligible), "passed": sum(vector[row["id"]] for row in eligible), "rate": conditional},
        "adjusted_Gap": (ar - conditional) if conditional is not None else None,
        "cascade_ineligible": sorted(set(composition_ids) - {row["id"] for row in eligible}),
        "mutation": {"passed": sum(vector[root] for root in mutation_ids), "total": len(mutation_ids), "rate": sum(vector[root] for root in mutation_ids) / len(mutation_ids)},
        "non_mutation": {"passed": sum(vector[root] for root in ordinary_ids), "total": len(ordinary_ids), "rate": sum(vector[root] for root in ordinary_ids) / len(ordinary_ids)},
    }


def execute(args: argparse.Namespace) -> dict[str, Any]:
    require(sys.flags.no_user_site == 1 and sys.flags.utf8_mode == 1 and sys.dont_write_bytecode, "scorer requires -s -X utf8 -B")
    candidate = args.candidate_root.resolve(); require(candidate.is_dir(), "candidate root missing")
    expected_python = (GATE / CONFIG["environment"]["python"]).resolve(); require(Path(sys.executable).resolve() == expected_python, "interpreter provenance mismatch")
    roots = static_registry(); ids = [row["id"] for row in roots]; order_map = orders(ids)
    before_gate = gate_snapshot()
    before_candidate = candidate_tree_snapshot(candidate, strict=args.mode == "anchor")
    source_provenance = provenance(args.mode, candidate, args.candidate_seal)
    if args.mode == "anchor":
        require(source_provenance["candidate_tree"] == before_candidate, "sealed and scorer candidate snapshots disagree")
    rounds: list[dict[str, Any]] = []
    stable_vector: dict[str, bool] | None = None
    with tempfile.TemporaryDirectory(prefix=f"mkdocs-v14-{args.mode}-") as temporary:
        temporary_root = Path(temporary)
        for order_name, order in order_map.items():
            for round_number in range(1, int(CONFIG["protocol"]["rounds_per_order"]) + 1):
                vector: dict[str, bool] = {}
                classifications: dict[str, str] = {}
                phases: dict[str, str] = {}
                for index, root_id in enumerate(order):
                    receipt = temporary_root / f"{order_name}-{round_number}-{index:02d}-{root_id}.json"
                    result = root_process(root_id, candidate, receipt)
                    vector[root_id] = bool(result["passed"]); classifications[root_id] = str(result["classification"])
                    phases[root_id] = str(result["phase"])
                ordered_vector = {root_id: vector[root_id] for root_id in ids}
                if stable_vector is None:
                    stable_vector = ordered_vector
                require(ordered_vector == stable_vector, f"unstable vector at {order_name} round {round_number}")
                rounds.append({"order": order_name, "round": round_number, "passed": sum(vector.values()), "vector": ordered_vector, "classifications": classifications, "phases": phases})
    assert stable_vector is not None
    if args.mode in CONFIG["expected"]:
        expected = set(CONFIG["expected"][args.mode]); actual = {root for root, passed in stable_vector.items() if passed}
        require(actual == expected, f"{args.mode} vector mismatch: expected={sorted(expected)} actual={sorted(actual)}")
    after_gate = gate_snapshot(); after_candidate = candidate_tree_snapshot(candidate, strict=args.mode == "anchor")
    require(after_gate == before_gate, "gate payload changed during scoring"); require(after_candidate == before_candidate, "candidate tree changed during scoring")
    if args.mode != "dummy":
        require(provenance(args.mode, candidate, args.candidate_seal) == source_provenance, "source provenance changed during scoring")
    return {"schema_version": 2, "suite": CONFIG["suite"], "valid": True, "mode": args.mode, "fresh_process_per_root": True, "orders": order_map, "rounds": rounds, "stable_vector": stable_vector, "scores": rates(stable_vector, roots), "provenance": source_provenance, "gate_payload": before_gate, "candidate_tree": before_candidate}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--mode", choices=("m1", "m2", "dummy", "anchor"), required=True); parser.add_argument("--candidate-root", type=Path, required=True); parser.add_argument("--candidate-seal", type=Path); parser.add_argument("--output", type=Path, required=True); args = parser.parse_args()
    try:
        record = execute(args); code = 0
    except BaseException as exc:
        record = {"schema_version": 2, "suite": CONFIG.get("suite"), "valid": False, "classification": "invalid-gate", "error_type": type(exc).__name__, "error": str(exc), "traceback": traceback.format_exc()}; code = 2
    require_output_unused = not args.output.exists()
    if require_output_unused:
        args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
