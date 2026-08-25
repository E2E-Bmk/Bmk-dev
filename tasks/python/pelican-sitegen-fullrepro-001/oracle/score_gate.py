from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import time
from typing import Any


GATE = Path(__file__).resolve().parent
CONFIG = json.loads((GATE / "SCORER-CONFIG.json").read_text(encoding="utf-8"))
ROOT_MAP = json.loads((GATE / "ROOT-MAP.json").read_text(encoding="utf-8"))
ENVIRONMENT = json.loads((GATE / "ENVIRONMENT-MANIFEST.json").read_text(encoding="utf-8"))
EXCLUDED = {".git", ".pdm-build", ".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache", ".venv", "venv"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_tree(root: Path) -> str:
    records: list[tuple[str, str]] = []
    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        base = Path(current)
        kept_dirs: list[str] = []
        for name in sorted(dirs):
            if name in EXCLUDED:
                continue
            directory = base / name
            if directory.is_symlink():
                raise RuntimeError(f"unsafe candidate directory: {directory}")
            kept_dirs.append(name)
        dirs[:] = kept_dirs
        for name in sorted(files):
            path = base / name
            if path.is_symlink() or not path.is_file():
                raise RuntimeError(f"unsafe candidate file: {path}")
            records.append((path.relative_to(root).as_posix(), sha256_file(path)))
    body = "".join(f"{name}\t{digest}\n" for name, digest in records).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def configured_path(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (GATE / path).resolve()


def environment_preflight(*, runner_override: str | None = None, verify_dependency: bool = False) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    configured_runner = configured_path(CONFIG["runner"])
    manifest_runner = configured_path(ENVIRONMENT["runner"])
    runner = Path(runner_override).resolve() if runner_override else configured_runner
    dependency_site = configured_path(CONFIG["dependency_site"])
    manifest_dependency = configured_path(ENVIRONMENT["dependency_site"])
    runner_hash = sha256_file(runner) if runner.is_file() else None
    if configured_runner != manifest_runner:
        errors.append("runner path disagrees with environment manifest")
    if runner != configured_runner:
        errors.append("runner override violates frozen runner provenance")
    if not runner.is_file():
        errors.append("runner executable is absent")
    elif runner_hash != CONFIG["runner_sha256"] or runner_hash != ENVIRONMENT["runner_sha256"]:
        errors.append("runner executable hash mismatch")
    if dependency_site != manifest_dependency:
        errors.append("dependency site disagrees with environment manifest")
    if not dependency_site.is_dir():
        errors.append("qualified dependency site is absent")
    dependency_hash = None
    if verify_dependency and dependency_site.is_dir():
        try:
            dependency_hash = sha256_tree(dependency_site)
        except RuntimeError as exc:
            errors.append(str(exc))
        if dependency_hash != CONFIG["dependency_tree_sha256"] or dependency_hash != ENVIRONMENT["dependency_tree_sha256"]:
            errors.append("qualified dependency site tree hash mismatch")
    return {
        "runner": str(runner),
        "runner_sha256": runner_hash,
        "dependency_site": str(dependency_site),
        "dependency_tree_sha256_expected": CONFIG["dependency_tree_sha256"],
        "dependency_tree_sha256_observed": dependency_hash,
        "dependency_access": ENVIRONMENT["dependency_access"],
    }, errors


def candidate_preflight(candidate: Path, candidate_mode: str, provenance_path: Path | None) -> tuple[str | None, dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    tree_hash: str | None = None
    provenance: dict[str, Any] | None = None
    if not candidate.is_dir():
        errors.append("candidate source directory is absent")
    elif not (candidate / "pelican" / "__init__.py").is_file():
        errors.append("candidate package structure is absent")
    else:
        try:
            tree_hash = sha256_tree(candidate)
        except RuntimeError as exc:
            errors.append(str(exc))
    if candidate_mode not in CONFIG["candidate_modes"]:
        errors.append("unknown candidate mode")
    if candidate_mode == "provenance-bound":
        if provenance_path is None or not provenance_path.is_file():
            errors.append("provenance-bound mode requires a candidate provenance file")
        else:
            try:
                provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                errors.append(f"candidate provenance is unreadable: {type(exc).__name__}")
            if provenance is not None:
                if provenance.get("schema") != CONFIG["candidate_provenance_schema"]:
                    errors.append("candidate provenance schema mismatch")
                if provenance.get("case") != CONFIG["case"] or provenance.get("status") != "sealed":
                    errors.append("candidate provenance is not sealed for this case")
                recorded_path = provenance.get("candidate")
                if not isinstance(recorded_path, str) or (provenance_path.parent / recorded_path).resolve() != candidate:
                    errors.append("candidate path does not match provenance")
                if tree_hash is None or provenance.get("candidate_tree_sha256") != tree_hash:
                    errors.append("candidate tree does not match sealed provenance")
    elif provenance_path is not None:
        errors.append("arbitrary mode must not claim provenance-bound status")
    return tree_hash, provenance, errors


def inventory() -> list[dict[str, Any]]:
    return [*ROOT_MAP["atomic"], *ROOT_MAP["composition"]]


def ordered_rows(mode: str, round_number: int) -> list[dict[str, Any]]:
    rows = inventory()
    if mode == "reverse":
        return list(reversed(rows))
    if mode == "permuted":
        rows = list(rows)
        random.Random(CONFIG["permutation_seed"] + round_number).shuffle(rows)
    return rows


def _rate(results: dict[str, dict[str, Any]], ids: list[str]) -> float:
    return sum(bool(results[root_id]["passed"]) for root_id in ids) / len(ids) if ids else 0.0


def _slice(results: dict[str, dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    ids = [row["id"] for row in rows]
    passed = sum(bool(results[root_id]["passed"]) for root_id in ids)
    return {"passed": passed, "total": len(ids), "rate": passed / len(ids) if ids else None}


def score(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {row["root"]: row for row in rows}
    atomic_rows = ROOT_MAP["atomic"]
    composition_rows = ROOT_MAP["composition"]
    integration_rows = [row for row in composition_rows if row["tier"] == "integration"]
    system_rows = [row for row in composition_rows if row["tier"] == "system_e2e"]
    atomic_ids = [row["id"] for row in atomic_rows]
    composition_ids = [row["id"] for row in composition_rows]
    atomic_rate = _rate(by_id, atomic_ids)
    composition_rate = _rate(by_id, composition_ids)
    eligible = [row for row in composition_rows if all(by_id[dependency]["passed"] for dependency in row["depends_on"])]
    conditional = _slice(by_id, eligible)
    conditional_rate = conditional["rate"]
    root_cause = [row["id"] for row in eligible if not by_id[row["id"]]["passed"]]
    cascaded = [row["id"] for row in composition_rows if row not in eligible and not by_id[row["id"]]["passed"]]
    native_rows = [row for row in inventory() if row["origin"] == "native"]
    mutation_rows = [row for row in inventory() if row["origin"] == "mutation"]
    family_ids = sorted({row.get("family") for row in mutation_rows if row.get("family")})
    return {
        "native_all_root": _slice(by_id, inventory()),
        "atomic": _slice(by_id, atomic_rows),
        "composition": _slice(by_id, composition_rows),
        "integration": _slice(by_id, integration_rows),
        "system_e2e": _slice(by_id, system_rows),
        "native_slice": _slice(by_id, native_rows),
        "mutation_slice": _slice(by_id, mutation_rows),
        "mutation_families": {family: _slice(by_id, [row for row in mutation_rows if row.get("family") == family]) for family in family_ids},
        "combined": (atomic_rate + composition_rate) / 2,
        "raw_gap": atomic_rate - composition_rate,
        "conditional_composition": conditional,
        "adjusted_gap": (atomic_rate - conditional_rate) if conditional_rate is not None else None,
        "root_cause_composition_failures": root_cause,
        "primitive_cascade_ineligible_failures": cascaded,
    }


def clean_env(profile: str) -> dict[str, str]:
    env = dict(os.environ)
    for key in list(env):
        upper = key.upper()
        if upper.startswith("PYTEST_") or upper in {"PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP"}:
            env.pop(key, None)
    env.update({
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "PELICAN_SYNTHETIC_PROFILE": profile,
    })
    return env


def run(
    candidate: Path,
    mode: str,
    round_number: int,
    only: str | None,
    profile: str,
    *,
    candidate_mode: str = "arbitrary",
    candidate_provenance: Path | None = None,
    runner_override: str | None = None,
    timeout_override: float | None = None,
    verify_dependency: bool = False,
) -> dict[str, Any]:
    candidate = candidate.resolve()
    candidate_provenance = candidate_provenance.resolve() if candidate_provenance else None
    rows = ordered_rows(mode, round_number)
    if only:
        wanted = {item.strip() for item in only.split(",") if item.strip()}
        rows = [row for row in rows if row["id"] in wanted]
        if {row["id"] for row in rows} != wanted:
            raise ValueError("--only contains unknown roots")
    environment, invalid = environment_preflight(
        runner_override=runner_override,
        verify_dependency=verify_dependency,
    )
    tree_before, provenance, candidate_errors = candidate_preflight(
        candidate, candidate_mode, candidate_provenance
    )
    invalid.extend(candidate_errors)
    if provenance is not None and provenance.get("profile") != profile:
        invalid.append("candidate provenance is not bound to the requested control profile")
    runner = Path(environment["runner"])
    env = clean_env(profile)
    results: list[dict[str, Any]] = []
    started = time.time()
    for row in rows if not invalid else []:
        command = [str(runner), "-I", "-X", "utf8", "-B", str(GATE / "run_root.py"), row["id"], str(candidate)]
        try:
            done = subprocess.run(
                command,
                cwd=GATE,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout_override or CONFIG["root_timeout_seconds"],
                check=False,
            )
        except subprocess.TimeoutExpired:
            invalid.append(f"{row['id']}: root timeout")
            results.append({"root": row["id"], "valid": False, "passed": False, "phase": "infrastructure", "infrastructure_error": "root timeout"})
            continue
        stderr = done.stderr.decode("utf-8", "strict")
        stdout = done.stdout.decode("utf-8", "strict")
        try:
            payload = json.loads(stdout.strip())
        except (json.JSONDecodeError, UnicodeError) as exc:
            invalid.append(f"{row['id']}: malformed root receipt: {type(exc).__name__}")
            results.append({"root": row["id"], "valid": False, "passed": False, "phase": "infrastructure", "infrastructure_error": "malformed root receipt"})
            continue
        payload["layer"] = "atomic" if row["id"].startswith("A") else row["tier"]
        payload["origin"] = row["origin"]
        if row.get("family"):
            payload["family"] = row["family"]
        if (
            done.returncode != 0
            or stderr
            or not payload.get("valid")
            or payload.get("phase") != "call"
            or payload.get("semantic_call_reached") is not True
        ):
            reason = payload.get("infrastructure_error") or f"child return={done.returncode} stderr={stderr!r}"
            invalid.append(f"{row['id']}: {reason}")
        results.append(payload)
    tree_after = None
    if tree_before is not None:
        try:
            tree_after = sha256_tree(candidate)
        except RuntimeError as exc:
            invalid.append(str(exc))
        if tree_before != tree_after:
            invalid.append("candidate tree changed during scoring")
    complete = len(rows) == len(inventory())
    receipt = {
        "schema": "spec2repo.score-receipt.v4",
        "case": CONFIG["case"],
        "constitution": CONFIG["constitution"],
        "scoring_formula": CONFIG["scoring_formula"],
        "candidate": str(candidate),
        "candidate_mode": candidate_mode,
        "candidate_provenance": {
            "path": str(candidate_provenance) if candidate_provenance else None,
            "id": provenance.get("id") if provenance else None,
            "sealed_tree_sha256": provenance.get("candidate_tree_sha256") if provenance else None,
        },
        "candidate_tree_sha256_before": tree_before,
        "candidate_tree_sha256_after": tree_after,
        "environment": environment,
        "mode": mode,
        "round": round_number,
        "only": only,
        "control_profile": profile,
        "valid": not invalid and len(results) == len(rows),
        "invalid_reasons": invalid,
        "inventory": [row["id"] for row in rows],
        "results": results,
        "semantic_call_count": sum(row.get("semantic_call_reached") is True for row in results),
        "score": score(results) if not invalid and complete else None,
        "started_epoch": started,
        "finished_epoch": time.time(),
    }
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--candidate-mode", choices=CONFIG["candidate_modes"], default="arbitrary")
    parser.add_argument("--candidate-provenance")
    parser.add_argument("--mode", choices=CONFIG["execution_modes"], default="natural")
    parser.add_argument("--round", type=int, choices=range(1, CONFIG["rounds_per_mode"] + 1), default=1)
    parser.add_argument("--only")
    parser.add_argument("--reference-patch", action="store_true", help="alias for --control-profile full")
    parser.add_argument("--control-profile", choices=["none", "full", "broad-collapsed", "broad-stale"], default="none")
    parser.add_argument("--runner-override", help="admission-only override; any value outside frozen provenance is invalid")
    parser.add_argument("--timeout-override", type=float, help="admission-only root timeout override")
    parser.add_argument("--verify-dependency", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    profile = "full" if args.reference_patch else args.control_profile
    receipt = run(
        Path(args.candidate),
        args.mode,
        args.round,
        args.only,
        profile,
        candidate_mode=args.candidate_mode,
        candidate_provenance=Path(args.candidate_provenance) if args.candidate_provenance else None,
        runner_override=args.runner_override,
        timeout_override=args.timeout_override,
        verify_dependency=args.verify_dependency,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    summary = {"valid": receipt["valid"], "score": receipt["score"], "output": str(output)}
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
