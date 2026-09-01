#!/usr/bin/env python3
"""Manifest-bound layer-balanced scorer for the Dynaconf v5 synthetic gate."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import random
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any


ROOT_RE = re.compile(r"test_([ais]\d{2})_")
GATE_DIR = Path(__file__).resolve().parent


class InvalidRun(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InvalidRun(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_bytes().decode("utf-8", "strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidRun(f"invalid UTF-8 JSON: {path}: {exc}") from exc


def aggregate_assets(items: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for item in sorted(items, key=lambda value: value["path"]):
        digest.update(item["path"].encode("utf-8", "strict"))
        digest.update(b"\0")
        digest.update(item["sha256"].encode("ascii", "strict"))
        digest.update(b"\n")
    return digest.hexdigest()


def verify_gate(config: dict[str, Any]) -> dict[str, Any]:
    manifest_path = GATE_DIR / config["manifest_file"]
    manifest = load_json(manifest_path)
    assets = manifest["score_bearing_payload"]["assets"]
    require(len(assets) == len(config["gate_payload_files"]), "manifest asset count mismatch")
    require(
        [item["path"] for item in assets] == sorted(config["gate_payload_files"]),
        "manifest payload membership mismatch",
    )
    observed: list[dict[str, Any]] = []
    for expected in assets:
        relative = expected["path"]
        path = (GATE_DIR / relative).resolve()
        require(path.is_file() and not path.is_symlink(), f"missing or unsafe gate file: {relative}")
        require(path.is_relative_to(GATE_DIR.resolve()), f"gate path escapes root: {relative}")
        raw = path.read_bytes()
        raw.decode("utf-8", "strict")
        observed.append(
            {
                "path": relative,
                "size": len(raw),
                "sha256": sha256_file(path),
            }
        )
    require(observed == assets, "gate payload hashes changed")
    aggregate = aggregate_assets(observed)
    require(
        aggregate == manifest["score_bearing_payload"]["aggregate_sha256"],
        "gate payload aggregate mismatch",
    )
    return {
        "manifest_sha256": sha256_file(manifest_path),
        "payload_aggregate_sha256": aggregate,
        "asset_count": len(observed),
    }


def tree_record(root: Path, excluded: set[str]) -> dict[str, Any]:
    files: list[dict[str, str]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root)
        if any(part in excluded for part in relative.parts) or path.suffix in {".pyc", ".pyo"}:
            continue
        files.append({"path": relative.as_posix(), "sha256": sha256_file(path)})
    return {"aggregate_sha256": aggregate_assets(files), "files": files}


def clean_environment(candidate_root: Path, temp_root: Path) -> dict[str, str]:
    environment = dict(os.environ)
    for key in list(environment):
        upper = key.upper()
        if (
            upper.startswith("PYTEST_")
            or upper.startswith("DYNACONF_")
            or upper.startswith("S2R_")
            or upper.endswith("_FOR_DYNACONF")
            or upper in {"PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "GIT_DIR", "GIT_WORK_TREE"}
        ):
            environment.pop(key, None)
    environment.update(
        {
            "PYTHONPATH": str(candidate_root),
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",
            "PYTHONHASHSEED": "0",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "NO_COLOR": "1",
            "TEMP": str(temp_root),
            "TMP": str(temp_root),
            "PYTHONWARNINGS": "error",
        }
    )
    return environment


def run_process(
    command: list[str], cwd: Path, environment: dict[str, str], timeout: float
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        stdout = completed.stdout.decode("utf-8", "strict")
        stderr = completed.stderr.decode("utf-8", "strict")
        return {
            "returncode": completed.returncode,
            "timed_out": False,
            "duration_seconds": round(time.perf_counter() - started, 6),
            "stdout": stdout[-12000:],
            "stderr": stderr[-12000:],
            "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "returncode": None,
            "timed_out": True,
            "duration_seconds": round(time.perf_counter() - started, 6),
            "stdout": "",
            "stderr": str(exc),
        }
    except UnicodeDecodeError as exc:
        raise InvalidRun(f"child emitted non-UTF-8 output: {command[0]}") from exc


def json_line(process: dict[str, Any], label: str) -> dict[str, Any]:
    require(not process["timed_out"], f"{label} timed out")
    require(process["returncode"] == 0, f"{label} failed: {process['stderr'][-500:]}")
    lines = [line for line in process["stdout"].splitlines() if line.strip()]
    require(len(lines) == 1, f"{label} did not emit one JSON line")
    try:
        return json.loads(lines[0])
    except json.JSONDecodeError as exc:
        raise InvalidRun(f"{label} emitted invalid JSON") from exc


def provenance(
    python: Path, candidate_root: Path, environment: dict[str, str]
) -> dict[str, Any]:
    code = (
        "import importlib.metadata as m,json,pathlib,sys,dynaconf;"
        "eps=[e.name for e in m.entry_points(group='console_scripts') if e.name=='dynaconf'];"
        "print(json.dumps({'module_file':str(pathlib.Path(dynaconf.__file__).resolve()),"
        "'distribution_version':m.version('dynaconf'),'executable':sys.executable,"
        "'console_entries':eps},sort_keys=True))"
    )
    process = run_process([str(python), "-B", "-c", code], candidate_root, environment, 60)
    record = json_line(process, "provenance probe")
    module_file = Path(record["module_file"]).resolve()
    require(module_file.is_relative_to(candidate_root), "dynaconf import escaped candidate source root")
    require(record["console_entries"] == ["dynaconf"], "installed dynaconf console entry mismatch")
    require(bool(record["distribution_version"]), "empty installed distribution version")
    require(Path(record["executable"]).resolve() == python, "provenance used another Python")
    return {"record": record, "process": process}


def git_identity(candidate_root: Path, config: dict[str, Any], environment: dict[str, str]) -> dict[str, str]:
    def value(*arguments: str) -> str:
        process = run_process(
            ["git", "-c", f"safe.directory={candidate_root}", "-C", str(candidate_root), *arguments],
            candidate_root,
            environment,
            60,
        )
        require(process["returncode"] == 0, f"git {' '.join(arguments)} failed")
        return process["stdout"].strip()

    top = Path(value("rev-parse", "--show-toplevel")).resolve()
    commit = value("rev-parse", "HEAD")
    tree = value("rev-parse", "HEAD^{tree}")
    status = value("status", "--porcelain=v1", "--untracked-files=all")
    require(top == candidate_root, "reference candidate is not Git toplevel")
    require(commit == config["reference"]["commit"], "reference commit mismatch")
    require(tree == config["reference"]["tree"], "reference tree mismatch")
    require(status == "", "reference source is not clean")
    return {"commit": commit, "tree": tree, "clean": "true"}


def collect_roots(
    python: Path, config: dict[str, Any], environment: dict[str, str]
) -> dict[str, Any]:
    command = [str(python), "-B", "-m", "pytest", "--collect-only", *config["pytest_args"]]
    process = run_process(command, GATE_DIR, environment, config["collection_timeout_seconds"])
    require(not process["timed_out"], "collection timed out")
    require(process["returncode"] == 0, f"collection failed: {process['stderr'][-500:]}")
    nodeids = []
    ids = []
    for line in process["stdout"].splitlines():
        candidate = line.strip()
        if "::test_" not in candidate:
            continue
        match = ROOT_RE.search(candidate)
        if match:
            nodeids.append(candidate)
            ids.append(match.group(1).upper())
    expected_ids = config["expected_ids"]
    expected_nodeids = [config["expected_nodeids"][root_id] for root_id in expected_ids]
    require(ids == expected_ids, f"collected root IDs differ: {ids!r}")
    require(nodeids == expected_nodeids, f"collected node IDs differ: {nodeids!r}")
    require(len(set(nodeids)) == config["counts"]["total"], "collected node IDs are not unique")
    return {"ids": ids, "nodeids": nodeids, "process": process}


def exact_score(roots: list[dict[str, Any]]) -> dict[str, Any]:
    atomic = sum(item["passed"] for item in roots if item["id"].startswith("A"))
    integration = sum(item["passed"] for item in roots if item["id"].startswith("I"))
    system = sum(item["passed"] for item in roots if item["id"].startswith("S"))
    atomic_total = 22
    integration_total = 40
    system_total = 28
    composition = integration + system
    composition_total = integration_total + system_total
    atomic_rate = Fraction(atomic, atomic_total)
    integration_rate = Fraction(integration, integration_total)
    system_rate = Fraction(system, system_total)
    composition_rate = Fraction(composition, composition_total)
    combined = (atomic_rate + composition_rate) / 2
    gap = atomic_rate - composition_rate
    mutation_ids = set(load_json(GATE_DIR / "SCORER-CONFIG.json")["mutation_expected_fail"])
    mutation = sum(item["passed"] for item in roots if item["id"] in mutation_ids)
    native = sum(item["passed"] for item in roots if item["id"] not in mutation_ids)
    return {
        "atomic_passed": atomic,
        "integration_passed": integration,
        "system_e2e_passed": system,
        "composition_passed": composition,
        "total_passed": atomic + composition,
        "atomic_rate_fraction": str(atomic_rate),
        "integration_rate_fraction": str(integration_rate),
        "system_e2e_rate_fraction": str(system_rate),
        "composition_rate_fraction": str(composition_rate),
        "combined_fraction": str(combined),
        "gap_fraction": str(gap),
        "atomic_rate": float(atomic_rate),
        "integration_rate": float(integration_rate),
        "system_e2e_rate": float(system_rate),
        "composition_rate": float(composition_rate),
        "combined": float(combined),
        "gap": float(gap),
        "native_passed": native,
        "native_total": 18,
        "mutation_passed": mutation,
        "mutation_total": 72,
        "vector": [item["passed"] for item in roots],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", required=True, type=Path)
    parser.add_argument("--candidate-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--round-label", required=True)
    parser.add_argument("--candidate-name", required=True)
    parser.add_argument("--mode", choices=("clean", "patched", "dummy", "candidate"), required=True)
    parser.add_argument("--order", choices=("natural", "reverse", "permuted"), default="natural")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--expected-gate-hash")
    parser.add_argument("--expected-candidate-hash")
    args = parser.parse_args()

    config_path = (args.config or GATE_DIR / "SCORER-CONFIG.json").resolve()
    config = load_json(config_path)
    python = args.python.resolve()
    candidate_root = args.candidate_root.resolve()
    excluded = set(config["candidate_tree_excluded_parts"])
    temp_parent = GATE_DIR.parent / ".score-temp"
    temp_parent.mkdir(parents=True, exist_ok=True)
    temp_root = Path(tempfile.mkdtemp(prefix="dynaconf-v5-", dir=temp_parent))
    environment = clean_environment(candidate_root, temp_root)
    record: dict[str, Any] = {
        "schema_version": 1,
        "suite": config["suite"],
        "candidate_name": args.candidate_name,
        "round_label": args.round_label,
        "mode": args.mode,
        "order": args.order,
        "python": str(python),
        "candidate_root": str(candidate_root),
        "gate_root": str(GATE_DIR),
        "config_sha256": sha256_file(config_path),
        "valid": False,
        "invalid_reason": None,
    }

    try:
        require(python.is_file(), "Python executable missing")
        require(candidate_root.is_dir(), "candidate root missing")
        gate_before = verify_gate(config)
        if args.expected_gate_hash:
            require(gate_before["payload_aggregate_sha256"] == args.expected_gate_hash, "expected gate hash mismatch")
        record["gate_before"] = gate_before
        record["candidate_tree_before"] = tree_record(candidate_root, excluded)
        if args.expected_candidate_hash:
            require(
                record["candidate_tree_before"]["aggregate_sha256"] == args.expected_candidate_hash,
                "expected candidate hash mismatch",
            )
        record["provenance_before"] = provenance(python, candidate_root, environment)
        if args.mode == "clean":
            record["reference_git"] = git_identity(candidate_root, config, environment)
            require(
                record["provenance_before"]["record"]["distribution_version"]
                == config["reference"]["distribution_version"],
                "reference distribution version mismatch",
            )
        record["collection"] = collect_roots(python, config, environment)

        execution_ids = list(config["expected_ids"])
        if args.order == "reverse":
            execution_ids.reverse()
        elif args.order == "permuted":
            random.Random(config["permutation_seed"]).shuffle(execution_ids)
        record["execution_ids"] = execution_ids
        def execute_root(root_id: str) -> dict[str, Any]:
            nodeid = config["expected_nodeids"][root_id]
            root_environment = dict(environment)
            report_path = temp_root / f"phase-{root_id}.json"
            root_environment["S2R_PHASE_REPORT"] = str(report_path)
            process = run_process(
                [
                    str(python), "-B", "-m", "pytest", *config["pytest_args"],
                    "-p", "score_report_plugin", nodeid,
                ],
                GATE_DIR,
                root_environment,
                config["root_timeout_seconds"],
            )
            if process["timed_out"]:
                raise InvalidRun(f"root timed out: {root_id}")
            if process["returncode"] not in {0, config["scoreable_failure_return_code"]}:
                raise InvalidRun(
                    f"unexpected pytest return code for {root_id}: {process['returncode']}"
                )
            require(report_path.is_file(), f"phase report missing: {root_id}")
            reports = load_json(report_path)
            phases = reports.get(nodeid)
            require(phases is not None, f"root phase record missing: {root_id}")
            require(phases.get("setup", {}).get("outcome") == "passed", f"setup failure: {root_id}")
            require(phases.get("teardown", {}).get("outcome") == "passed", f"teardown failure: {root_id}")
            call = phases.get("call", {})
            require(call.get("outcome") in {"passed", "failed"}, f"non-call result: {root_id}")
            require(not call.get("wasxfail"), f"xfail is invalid evidence: {root_id}")
            warning_markers = (
                "PytestUnraisableExceptionWarning", "PytestUnhandledThreadExceptionWarning",
                "ResourceWarning:", "RuntimeWarning:", "UserWarning:",
            )
            require(
                not any(marker in call.get("longrepr", "") for marker in warning_markers),
                f"warning failure: {root_id}",
            )
            passed = call["outcome"] == "passed"
            status = "passed" if passed else "failed"
            return {
                "id": root_id, "nodeid": nodeid, "status": status,
                "passed": passed, "phases": phases, "process": process,
            }

        with ThreadPoolExecutor(max_workers=3) as executor:
            roots = list(executor.map(execute_root, execution_ids))
        roots_by_id = {item["id"]: item for item in roots}
        ordered_roots = [roots_by_id[root_id] for root_id in config["expected_ids"]]
        record["roots"] = ordered_roots
        record["score"] = exact_score(ordered_roots)
        record["provenance_after"] = provenance(python, candidate_root, environment)
        record["candidate_tree_after"] = tree_record(candidate_root, excluded)
        require(
            record["candidate_tree_before"]["aggregate_sha256"]
            == record["candidate_tree_after"]["aggregate_sha256"],
            "candidate source tree changed during scoring",
        )
        record["gate_after"] = verify_gate(config)
        require(record["gate_before"] == record["gate_after"], "gate changed during scoring")
        record["valid"] = True
    except BaseException as exc:
        record["invalid_reason"] = f"{type(exc).__name__}: {exc}"
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if record["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
