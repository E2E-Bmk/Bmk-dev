from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import random
from typing import Any


GATE = Path(__file__).resolve().parent


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_hash(root: Path, excluded: set[str] | None = None) -> str:
    excluded = excluded or set()
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if any(part in {"__pycache__", ".pytest_cache"} for part in path.parts):
            continue
        if relative.split("/", 1)[0] in excluded:
            continue
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def run(command: list[str], env: dict[str, str], timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=GATE,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )


def make_env(candidate_root: Path, role: str, patch: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(candidate_root)
    env.pop("TRANSITIONS_V4_REFERENCE_PATCH", None)
    env.pop("TRANSITIONS_V4_PHASE_FILE", None)
    env.pop("TRANSITIONS_V4_CONTROL", None)
    if role == "m1" or role.startswith("control-"):
        env["TRANSITIONS_V4_REFERENCE_PATCH"] = str(patch)
    if role.startswith("control-"):
        env["TRANSITIONS_V4_CONTROL"] = role.removeprefix("control-")
    return env


def provenance(env: dict[str, str], candidate_root: Path) -> dict[str, Any]:
    script = (
        "import json, pathlib, transitions; "
        "print(json.dumps({'module_file': str(pathlib.Path(transitions.__file__).resolve()), "
        "'version': getattr(transitions, '__version__', None)}))"
    )
    result = run([sys.executable, "-c", script], env, 30)
    if result.returncode != 0:
        raise RuntimeError(f"provenance import failed:\n{result.stdout}")
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    module_file = Path(payload["module_file"]).resolve()
    try:
        module_file.relative_to(candidate_root)
    except ValueError as error:
        raise RuntimeError(
            f"provenance mismatch: {module_file} is outside {candidate_root}"
        ) from error
    payload["candidate_root"] = str(candidate_root)
    payload["candidate_tree_sha256"] = tree_hash(candidate_root)
    return payload


def collect_nodeids(env: dict[str, str], timeout: int) -> tuple[list[str], str]:
    command = [sys.executable, "-m", "pytest", "--collect-only", "-q"]
    result = run(command, env, timeout)
    nodeids = sorted(
        line.strip()
        for line in result.stdout.splitlines()
        if "::test_" in line and not line.lstrip().startswith("<")
    )
    if result.returncode != 0:
        raise RuntimeError(f"collection failed with {result.returncode}:\n{result.stdout}")
    return nodeids, result.stdout


def atomic_dependencies(root: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> set[str]:
    discovered: set[str] = set()
    pending = list(root.get("depends_on", []))
    while pending:
        dependency = pending.pop()
        if dependency in discovered:
            continue
        discovered.add(dependency)
        pending.extend(by_id[dependency].get("depends_on", []))
    return {item for item in discovered if item.startswith("A")}


def percent(numerator: int, denominator: int) -> float:
    return round(100.0 * numerator / denominator, 6) if denominator else 0.0


def score(roots: list[dict[str, Any]], passed: set[str]) -> dict[str, Any]:
    atomic = [root for root in roots if root["kind"] == "atomic"]
    integration = [root for root in roots if root["kind"] == "composition"]
    system = [root for root in roots if root["kind"] == "system"]
    composition = integration + system
    native = [root for root in roots if root["origin"] == "native"]
    mutation = [root for root in roots if root["origin"] == "mutation"]
    by_id = {root["id"]: root for root in roots}
    eligible = [
        root
        for root in composition
        if atomic_dependencies(root, by_id).issubset(passed)
    ]
    atomic_rate = percent(sum(root["id"] in passed for root in atomic), len(atomic))
    composition_rate = percent(
        sum(root["id"] in passed for root in composition), len(composition)
    )
    conditional_rate = percent(
        sum(root["id"] in passed for root in eligible), len(eligible)
    )
    return {
        "AtomicRate": atomic_rate,
        "IntegrationRate": percent(
            sum(root["id"] in passed for root in integration), len(integration)
        ),
        "SystemRate": percent(sum(root["id"] in passed for root in system), len(system)),
        "CompositionRate": composition_rate,
        "Combined": round((atomic_rate + composition_rate) / 2.0, 6),
        "Gap": round(atomic_rate - composition_rate, 6),
        "ConditionalCompositionRate": conditional_rate,
        "AdjustedGap": round(atomic_rate - conditional_rate, 6),
        "NativeAllRootRate": percent(
            sum(root["id"] in passed for root in native), len(native)
        ),
        "MutationRootRate": percent(
            sum(root["id"] in passed for root in mutation), len(mutation)
        ),
        "NonMutationRootRate": percent(
            sum(root["id"] in passed for root in native), len(native)
        ),
        "conditional_composition_ids": [root["id"] for root in eligible],
    }


def expected_check(role: str, passed: set[str], failed: set[str], config: dict[str, Any]) -> list[str]:
    if role == "candidate":
        return []
    expected = config["expected"][role]
    errors = []
    if len(passed) != expected["passed"]:
        errors.append(f"expected {expected['passed']} passes, got {len(passed)}")
    if len(failed) != expected["failed"]:
        errors.append(f"expected {expected['failed']} failures, got {len(failed)}")
    if "failed_ids" in expected and failed != set(expected["failed_ids"]):
        errors.append(
            f"{role} exact set mismatch: "
            f"missing={sorted(set(expected['failed_ids']) - failed)} "
            f"extra={sorted(failed - set(expected['failed_ids']))}"
        )
    return errors


def ordered_roots(roots: list[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    items = list(roots)
    if mode == "reverse":
        items.reverse()
    elif mode == "permuted":
        random.Random("transitions-v4-fixed-permutation").shuffle(items)
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="Transitions v4 durable publication gate scorer")
    parser.add_argument("--role", choices=("m1", "m2", "dummy", "candidate", "control-no-outbox", "control-stale-reconcile", "control-no-owner-generation", "control-eager-publish"), required=True)
    parser.add_argument("--candidate-root", type=Path)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--order-mode", choices=("natural", "reverse", "permuted"), default="natural")
    arguments = parser.parse_args()

    config = read_json(GATE / "SCORER-CONFIG.json")
    root_map = read_json(GATE / config["root_map"])
    roots = root_map["roots"]
    patch = (GATE / config["patch"]).resolve()
    if arguments.candidate_root:
        candidate_root = arguments.candidate_root.resolve()
    elif arguments.role in {"m1", "m2", "control-no-outbox", "control-stale-reconcile", "control-no-owner-generation", "control-eager-publish"}:
        candidate_root = (GATE / config["reference"]["source_root_relative"]).resolve()
    elif arguments.role == "dummy":
        candidate_root = (GATE / config["dummy_root"]).resolve()
    else:
        parser.error("--candidate-root is required for candidate role")

    evidence = arguments.evidence_dir.resolve()
    evidence.mkdir(parents=True, exist_ok=False)
    (evidence / "phases").mkdir()
    (evidence / "junit").mkdir()

    env = make_env(candidate_root, arguments.role, patch)
    timeout = config["timeouts"]["root_seconds"]
    expected_nodeids = sorted(root["nodeid"] for root in roots)
    collected, collection_output = collect_nodeids(
        env, config["timeouts"]["collection_seconds"]
    )
    collection_errors = []
    if collected != expected_nodeids:
        collection_errors.append(
            f"collection mismatch: missing={sorted(set(expected_nodeids)-set(collected))}; "
            f"extra={sorted(set(collected)-set(expected_nodeids))}"
        )

    provenance_payload = provenance(env, candidate_root)
    results: dict[str, Any] = {}
    passed: set[str] = set()
    failed: set[str] = set()
    infrastructure_errors = list(collection_errors)

    execution_roots = ordered_roots(roots, arguments.order_mode)
    for root in execution_roots:
        root_id = root["id"]
        phase_path = evidence / "phases" / f"{root_id}.json"
        junit_path = evidence / "junit" / f"{root_id}.xml"
        root_env = env.copy()
        root_env["TRANSITIONS_V4_PHASE_FILE"] = str(phase_path)
        command = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-W",
            "error",
            root["nodeid"],
            f"--junitxml={junit_path}",
        ]
        try:
            completed = run(command, root_env, timeout)
        except subprocess.TimeoutExpired:
            infrastructure_errors.append(f"{root_id}: timeout")
            continue
        phase = read_json(phase_path) if phase_path.exists() else {}
        phases = phase.get("phases", {})
        if completed.returncode == 0:
            outcome = "passed"
            passed.add(root_id)
        elif completed.returncode == 1:
            outcome = "failed"
            failed.add(root_id)
        else:
            outcome = "invalid"
            infrastructure_errors.append(
                f"{root_id}: pytest exit {completed.returncode}"
            )
        if phases.get("setup", {}).get("outcome") != "passed":
            infrastructure_errors.append(f"{root_id}: setup did not pass")
        call_outcome = phases.get("call", {}).get("outcome")
        if outcome == "passed" and call_outcome != "passed":
            infrastructure_errors.append(f"{root_id}: passing root lacks passing call phase")
        if outcome == "failed" and call_outcome != "failed":
            infrastructure_errors.append(f"{root_id}: failure was not in call phase")
        if phases.get("teardown", {}).get("outcome") != "passed":
            infrastructure_errors.append(f"{root_id}: teardown did not pass")
        results[root_id] = {
            "nodeid": root["nodeid"],
            "outcome": outcome,
            "returncode": completed.returncode,
            "phases": phases,
            "output": completed.stdout[-8000:],
        }

    expectation_errors = expected_check(
        arguments.role, passed, failed, config
    )
    payload = {
        "schema_version": 1,
        "suite_id": config["suite_id"],
        "role": arguments.role,
        "python": sys.version,
        "python_executable": sys.executable,
        "gate_root": str(GATE),
        "gate_tree_sha256": tree_hash(GATE, {"evidence", "FREEZE-MANIFEST.json"}),
        "provenance": provenance_payload,
        "reference_patch_enabled": arguments.role == "m1" or arguments.role.startswith("control-"),
        "order_mode": arguments.order_mode,
        "execution_order": [root["id"] for root in execution_roots],
        "collection": {
            "expected": expected_nodeids,
            "collected": collected,
            "output": collection_output,
        },
        "passed_ids": sorted(passed),
        "failed_ids": sorted(failed),
        "counts": {"passed": len(passed), "failed": len(failed), "total": len(roots)},
        "scores": score(roots, passed),
        "root_results": results,
        "expectation_errors": expectation_errors,
        "infrastructure_errors": infrastructure_errors,
        "valid": not expectation_errors and not infrastructure_errors,
    }
    (evidence / "score.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps({
        "role": arguments.role,
        "valid": payload["valid"],
        "counts": payload["counts"],
        "scores": payload["scores"],
        "evidence": str(evidence),
        "errors": expectation_errors + infrastructure_errors,
    }, indent=2, sort_keys=True))
    return 0 if payload["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
