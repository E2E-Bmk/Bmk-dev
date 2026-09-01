from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


GATE = Path(__file__).resolve().parent
CONFIG = json.loads((GATE / "SCORER-CONFIG.json").read_text(encoding="utf-8"))
ROOT_MAP = json.loads((GATE / "ROOT-MAP.json").read_text(encoding="utf-8"))
ROOTS = [item["id"] for item in ROOT_MAP["atomic"] + ROOT_MAP["composition"]]


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    ignored = {"__pycache__", ".pytest_cache", ".git"}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if not path.is_file() or ignored.intersection(relative.parts) or path.suffix in {".pyc", ".pyo"}:
            continue
        digest.update(relative.as_posix().encode("utf-8") + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def runtime_inventory_hash(root: Path) -> str:
    rows: list[str] = []
    paths = sorted(root.rglob("*"), key=lambda path: path.relative_to(root).as_posix())
    for path in paths:
        relative = path.relative_to(root)
        if not path.is_file() or "__pycache__" in relative.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        rows.append(
            f"{relative.as_posix()}\t{hashlib.sha256(path.read_bytes()).hexdigest()}\t{path.stat().st_size}\n"
        )
    return hashlib.sha256("".join(rows).encode("utf-8")).hexdigest()


def order_for(mode: str) -> list[str]:
    roots = list(ROOTS)
    if mode == "reverse": roots.reverse()
    elif mode == "permuted": random.Random(CONFIG["permutation_seed"]).shuffle(roots)
    elif mode != "natural": raise ValueError(f"unknown mode: {mode}")
    return roots


def wrapper_probe(candidate: Path, profile: str) -> dict[str, Any]:
    child = subprocess.run([sys.executable, str(GATE / "wrapper_probe.py"), str(candidate), CONFIG["reference_package_root"], profile], text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=30, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    try: return json.loads(child.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError): return {"valid": False, "error": f"wrapper probe emitted invalid JSON: {child.stdout} {child.stderr}"}


def score(candidate: Path, profile: str, mode: str) -> dict[str, Any]:
    before = tree_hash(candidate)
    runtime_before = runtime_inventory_hash(Path(CONFIG["reference_package_root"]).resolve())
    probe = wrapper_probe(candidate, profile)
    results: list[dict[str, Any]] = []
    timeout = int(CONFIG["root_timeout_seconds"])
    for root in order_for(mode):
        started = time.perf_counter()
        try:
            child = subprocess.run([sys.executable, str(GATE / "run_root.py"), root, str(candidate), profile], text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            try:
                result = json.loads(child.stdout.strip().splitlines()[-1])
            except (IndexError, json.JSONDecodeError):
                result = {"root": root, "profile": profile, "valid": False, "passed": False, "phase": "outer", "infrastructure_error": "runner emitted invalid JSON", "stdout": child.stdout, "stderr": child.stderr}
        except subprocess.TimeoutExpired as exc:
            result = {"root": root, "profile": profile, "valid": False, "passed": False, "phase": "outer-timeout", "infrastructure_error": "outer timeout", "stdout": exc.stdout or "", "stderr": exc.stderr or ""}
        result["outer_duration_seconds"] = round(time.perf_counter() - started, 6)
        results.append(result)
    after = tree_hash(candidate)
    runtime_after = runtime_inventory_hash(Path(CONFIG["reference_package_root"]).resolve())
    passed = {item["root"] for item in results if item.get("passed") is True}
    a = sum(root in passed for root in ROOTS if root.startswith("A")); i = sum(root in passed for root in ROOTS if root.startswith("I")); s = sum(root in passed for root in ROOTS if root.startswith("S"))
    mutation_ids = {item["id"] for item in ROOT_MAP["atomic"] + ROOT_MAP["composition"] if item["mutation"]}
    native_ids = set(ROOTS) - mutation_ids
    valid = bool(probe.get("valid")) and before == after and runtime_before == runtime_after and len(results) == 48 and all(item.get("valid") is True and item.get("phase") == "call" for item in results)
    return {
        "schema": "spec2repo.score-receipt.vnext", "case": "whoosh-vnext-draft-a", "profile": profile, "mode": mode,
        "valid": valid, "wrapper_probe": probe, "candidate_tree_sha256_before": before, "candidate_tree_sha256_after": after,
        "runtime_tree_sha256_before": runtime_before, "runtime_tree_sha256_after": runtime_after,
        "score": {
            "atomic": {"passed": a, "total": 16}, "integration": {"passed": i, "total": 24}, "system": {"passed": s, "total": 8},
            "composition": {"passed": i + s, "total": 32}, "all_roots": {"passed": a + i + s, "total": 48},
            "combined_rate": round((a + i + s) / 48, 8), "gap": round(a / 16 - (i + s) / 32, 8),
            "mutation": {"passed": len(passed & mutation_ids), "total": 34}, "native": {"passed": len(passed & native_ids), "total": 14}
        },
        "results": results
    }


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("candidate"); parser.add_argument("--profile", required=True, choices=CONFIG["profiles"]); parser.add_argument("--mode", default="natural", choices=CONFIG["execution_modes"]); parser.add_argument("--output")
    args = parser.parse_args(); receipt = score(Path(args.candidate).resolve(), args.profile, args.mode)
    text = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output: Path(args.output).write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({"valid": receipt["valid"], "score": receipt["score"], "output": args.output}, ensure_ascii=False, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__": raise SystemExit(main())
