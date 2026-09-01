from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time


ROOT_RE = re.compile(r"test_([ace]\d{2})_")
DEFAULT_EXCLUDED_PARTS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "evidence",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tree_record(root: Path, excluded_parts: set[str]) -> dict:
    files = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in excluded_parts for part in relative.parts):
            continue
        if path.suffix in {".pyc", ".pyo"}:
            continue
        files.append({"path": relative.as_posix(), "sha256": _sha256(path)})

    aggregate = hashlib.sha256()
    for item in files:
        aggregate.update(item["path"].encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(item["sha256"].encode("ascii"))
        aggregate.update(b"\n")
    return {"aggregate_sha256": aggregate.hexdigest(), "files": files}


def _run(command: list[str], cwd: Path, env: dict[str, str], timeout: float) -> dict:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "timed_out": False,
            "duration_seconds": round(time.perf_counter() - started, 6),
            "stdout": completed.stdout[-16000:],
            "stderr": completed.stderr[-16000:],
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {
            "command": command,
            "returncode": None,
            "timed_out": True,
            "duration_seconds": round(time.perf_counter() - started, 6),
            "stdout": stdout[-16000:],
            "stderr": stderr[-16000:],
        }


def _last_json_line(text: str) -> dict:
    for line in reversed(text.splitlines()):
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    raise ValueError("subprocess produced no JSON record")


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _provenance(python: Path, candidate_root: Path, env: dict[str, str]) -> dict:
    code = (
        "import json,pathlib,sys,jupyter_client;"
        "mods={n:str(pathlib.Path(m.__file__).resolve()) for n,m in sys.modules.items() "
        "if (n=='jupyter_client' or n.startswith('jupyter_client.')) and getattr(m,'__file__',None)};"
        "print(json.dumps({'module_file':str(pathlib.Path(jupyter_client.__file__).resolve()),"
        "'module_files':mods,'version':getattr(jupyter_client,'__version__',None),"
        "'executable':sys.executable}))"
    )
    process = _run([str(python), "-B", "-c", code], candidate_root, env, 30)
    if process["returncode"] != 0 or process["timed_out"]:
        return {"valid": False, "reason": "candidate import failed", "process": process}
    try:
        record = _last_json_line(process["stdout"])
        module_file = Path(record["module_file"]).resolve()
        module_files = {name: Path(path).resolve() for name, path in record["module_files"].items()}
    except (KeyError, TypeError, ValueError) as exc:
        return {"valid": False, "reason": f"invalid provenance record: {exc}", "process": process}
    escaped = {name: str(path) for name, path in module_files.items() if not _is_within(path, candidate_root)}
    valid = _is_within(module_file, candidate_root) and not escaped
    return {
        "valid": valid,
        "reason": None if valid else "jupyter_client import escaped candidate root",
        "escaped_modules": escaped,
        "record": record,
        "process": process,
    }


def _collect(
    python: Path,
    gate_root: Path,
    env: dict[str, str],
    pytest_args: list[str],
    timeout: float,
    expected_ids: list[str],
    expected_nodeids: dict[str, str],
) -> dict:
    process = _run(
        [str(python), "-B", "-m", "pytest", "--collect-only", *pytest_args],
        gate_root,
        env,
        timeout,
    )
    nodeids = []
    ids = []
    for line in process["stdout"].splitlines():
        candidate = line.strip().replace("\\", "/")
        if "::test_" not in candidate:
            continue
        match = ROOT_RE.search(candidate)
        if match:
            nodeids.append(candidate)
            ids.append(match.group(1).upper())
    nodeid_by_id = dict(zip(ids, nodeids))
    valid = (
        not process["timed_out"]
        and process["returncode"] == 0
        and len(nodeids) == len(expected_ids)
        and len(set(nodeids)) == len(expected_ids)
        and ids == expected_ids
        and nodeid_by_id == expected_nodeids
    )
    reason = None
    if not valid:
        reason = (
            f"collection mismatch: returncode={process['returncode']} "
            f"timed_out={process['timed_out']} count={len(nodeids)} ids={ids!r}"
        )
    return {
        "valid": valid,
        "reason": reason,
        "nodeids": nodeids,
        "ids": ids,
        "nodeid_by_id": nodeid_by_id,
        "process": process,
    }


def _read_phase_report(path: Path, nodeid: str) -> dict:
    if not path.is_file():
        return {"valid": False, "reason": "missing phase report", "phases": []}
    phases = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            phases.append(json.loads(line))
    relevant = [item for item in phases if item.get("nodeid", "").replace("\\", "/") == nodeid]
    by_when = {item.get("when"): item for item in relevant}
    valid = (
        len(relevant) == 3
        and set(by_when) == {"setup", "call", "teardown"}
        and by_when["setup"].get("outcome") == "passed"
        and by_when["teardown"].get("outcome") == "passed"
        and by_when["call"].get("outcome") in {"passed", "failed"}
    )
    reason = None if valid else f"invalid phase vector: {relevant!r}"
    return {"valid": valid, "reason": reason, "phases": relevant, "by_when": by_when}


def _rate(passed: set[str], roots: list[str]) -> float:
    return sum(root in passed for root in roots) / len(roots) if roots else 0.0


def _score(config: dict, roots: list[dict]) -> dict:
    passed = {item["id"] for item in roots if item["passed"]}
    layers = config["layers"]
    atomic = list(layers["atomic"])
    integration = list(layers["integration"])
    system = list(layers["system_e2e"])
    composition = integration + system
    atomic_rate = _rate(passed, atomic)
    composition_rate = _rate(passed, composition)
    eligible = [
        root for root in composition
        if all(dependency in passed for dependency in config["depends_on"][root])
    ]
    conditional_rate = _rate(passed, eligible) if eligible else None
    mutation = list(config["mutation_impact"])
    non_mutation = list(config["non_mutation_roots"])
    cascaded = [
        root for root in composition
        if root not in passed and any(dep not in passed for dep in config["depends_on"][root])
    ]
    root_cause = [root for root in composition if root not in passed and root not in cascaded]
    family_rates = {
        family: {
            "passed": sum(root in passed for root in members),
            "total": len(members),
            "rate": _rate(passed, members),
        }
        for family, members in config["mutation_families"].items()
    }
    return {
        "atomic_passed": sum(root in passed for root in atomic),
        "atomic_total": len(atomic),
        "composition_passed": sum(root in passed for root in composition),
        "composition_total": len(composition),
        "integration_passed": sum(root in passed for root in integration),
        "integration_total": len(integration),
        "system_e2e_passed": sum(root in passed for root in system),
        "system_e2e_total": len(system),
        "total_passed": len(passed),
        "total": len(roots),
        "atomic_rate": atomic_rate,
        "composition_rate": composition_rate,
        "combined": (atomic_rate + composition_rate) / 2,
        "gap": atomic_rate - composition_rate,
        "all_root_rate": len(passed) / len(roots),
        "integration_rate": _rate(passed, integration),
        "system_e2e_rate": _rate(passed, system),
        "conditional_composition_eligible": eligible,
        "conditional_composition_rate": conditional_rate,
        "adjusted_gap": None if conditional_rate is None else atomic_rate - conditional_rate,
        "mutation_passed": sum(root in passed for root in mutation),
        "mutation_total": len(mutation),
        "mutation_rate": _rate(passed, mutation),
        "non_mutation_passed": sum(root in passed for root in non_mutation),
        "non_mutation_total": len(non_mutation),
        "non_mutation_rate": _rate(passed, non_mutation),
        "family_rates": family_rates,
        "cascaded_composition_failures": cascaded,
        "root_cause_composition_failures": root_cause,
        "passed_ids": sorted(passed),
        "failed_ids": [root for root in config["expected_ids"] if root not in passed],
        "vector": [root in passed for root in config["expected_ids"]],
    }


def _validate_expected_vector(mode: str, config: dict, score: dict) -> None:
    if mode == "anchor":
        return
    expected = config["expected_vectors"][mode]
    if score["passed_ids"] != sorted(expected["pass"]):
        raise RuntimeError(
            f"{mode} pass set mismatch: expected={sorted(expected['pass'])!r} "
            f"actual={score['passed_ids']!r}"
        )
    if score["failed_ids"] != expected["fail"]:
        raise RuntimeError(
            f"{mode} fail set mismatch: expected={expected['fail']!r} actual={score['failed_ids']!r}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", required=True, type=Path)
    parser.add_argument("--candidate-root", required=True, type=Path)
    parser.add_argument("--gate-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--round-label", required=True)
    parser.add_argument("--candidate-name", required=True)
    parser.add_argument("--mode", choices=("reference", "upstream", "dummy", "control-connection", "control-delivery", "anchor"), required=True)
    parser.add_argument("--root-order", choices=("natural", "reverse", "permuted"), default="natural")
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()

    python = args.python.resolve()
    candidate_root = args.candidate_root.resolve()
    gate_root = args.gate_root.resolve()
    config_path = (args.config or gate_root / "SCORER-CONFIG.json").resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    excluded = set(config.get("candidate_tree_excluded_parts", DEFAULT_EXCLUDED_PARTS))
    expected_ids = list(config["expected_ids"])
    expected_nodeids = dict(config["expected_nodeids"])

    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    support_paths = [entry for entry in env.get("PYTHONPATH", "").split(os.pathsep) if entry]
    support_paths = [entry for entry in support_paths if Path(entry).resolve() != candidate_root]
    env["PYTHONPATH"] = os.pathsep.join([str(candidate_root), *support_paths])
    env["PYTHONWARNINGS"] = "error"
    if args.mode in {"reference", "control-connection", "control-delivery"}:
        env["JUPYTER_CLIENT_V4_REFERENCE_PATCH"] = str((gate_root / config["reference_patch_file"]).resolve())
        controls = {
            "control-connection": "connection-ledger-bypass",
            "control-delivery": "delivery-validation-bypass",
        }
        if args.mode in controls:
            env["JUPYTER_CLIENT_V4_CONTROL"] = controls[args.mode]
        else:
            env.pop("JUPYTER_CLIENT_V4_CONTROL", None)
    else:
        env.pop("JUPYTER_CLIENT_V4_REFERENCE_PATCH", None)
        env.pop("JUPYTER_CLIENT_V4_CONTROL", None)

    record = {
        "schema_version": 1,
        "suite": config["suite"],
        "constitution": config["constitution"],
        "formula_version": config["formula_version"],
        "candidate_name": args.candidate_name,
        "round_label": args.round_label,
        "mode": args.mode,
        "root_order": args.root_order,
        "python": str(python),
        "candidate_root": str(candidate_root),
        "gate_root": str(gate_root),
        "config_sha256": _sha256(config_path),
        "valid": False,
        "invalid_reason": None,
    }

    try:
        record["candidate_tree_before"] = _tree_record(candidate_root, excluded)
        gate_excluded = set(config.get("gate_tree_excluded_parts", DEFAULT_EXCLUDED_PARTS))
        record["gate_tree_before"] = _tree_record(gate_root, gate_excluded)
        record["provenance_before"] = _provenance(python, candidate_root, env)
        if not record["provenance_before"]["valid"]:
            raise RuntimeError(record["provenance_before"]["reason"])

        collection = _collect(
            python,
            gate_root,
            env,
            list(config["pytest_args"]),
            float(config["collection_timeout_seconds"]),
            expected_ids,
            expected_nodeids,
        )
        record["collection"] = collection
        if not collection["valid"]:
            raise RuntimeError(collection["reason"])

        if args.root_order == "natural":
            execution_ids = list(expected_ids)
        elif args.root_order == "reverse":
            execution_ids = list(reversed(expected_ids))
        else:
            execution_ids = list(config["root_orders"]["permuted"])
        if sorted(execution_ids) != sorted(expected_ids) or len(execution_ids) != len(set(execution_ids)):
            raise RuntimeError(f"invalid execution order: {execution_ids!r}")

        roots = []
        with tempfile.TemporaryDirectory(prefix="jupyter-client-v4-root-reports-") as temp_dir:
            report_dir = Path(temp_dir)

            def run_root(root_id):
                nodeid = collection["nodeid_by_id"][root_id]
                report_path = report_dir / f"{root_id}.jsonl"
                root_env = env.copy()
                root_env["JUPYTER_CLIENT_V4_ROOT_REPORT"] = str(report_path)
                root_temp = report_dir / f"tmp-{root_id}"
                root_temp.mkdir()
                root_env["TEMP"] = str(root_temp)
                root_env["TMP"] = str(root_temp)
                process = _run(
                    [str(python), "-B", "-m", "pytest", *config["pytest_args"], nodeid],
                    gate_root,
                    root_env,
                    float(config["root_timeout_seconds"]),
                )
                if process["timed_out"]:
                    raise RuntimeError(f"root timed out: {root_id}")
                phase = _read_phase_report(report_path, nodeid)
                if not phase["valid"]:
                    raise RuntimeError(f"{root_id}: {phase['reason']}")
                call = phase["by_when"]["call"]
                warning_failure = bool(
                    call.get("exception_type") and call["exception_type"].split(".")[-1].endswith("Warning")
                )
                if warning_failure:
                    raise RuntimeError(f"warning-as-error is infrastructure-invalid for {root_id}")
                if process["returncode"] == 0 and call["outcome"] == "passed":
                    passed = True
                    status = "passed"
                elif (
                    process["returncode"] == int(config["scoreable_failure_return_code"])
                    and call["outcome"] == "failed"
                ):
                    passed = False
                    status = "failed"
                else:
                    raise RuntimeError(
                        f"unexpected pytest result for {root_id}: "
                        f"returncode={process['returncode']} call={call['outcome']}"
                    )
                return {
                    "id": root_id,
                    "nodeid": nodeid,
                    "passed": passed,
                    "status": status,
                    "phase_report": phase["phases"],
                    "process": process,
                }

            workers = int(config.get("root_workers", 1))
            if workers == 1:
                roots = [run_root(root_id) for root_id in execution_ids]
            else:
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    roots = list(executor.map(run_root, execution_ids))

        record["roots"] = roots
        if len(roots) != len(expected_ids):
            raise RuntimeError(f"incomplete vector: {len(roots)} roots")
        record["score"] = _score(config, roots)
        _validate_expected_vector(args.mode, config, record["score"])

        record["provenance_after"] = _provenance(python, candidate_root, env)
        if not record["provenance_after"]["valid"]:
            raise RuntimeError(record["provenance_after"]["reason"])
        record["candidate_tree_after"] = _tree_record(candidate_root, excluded)
        if (
            record["candidate_tree_before"]["aggregate_sha256"]
            != record["candidate_tree_after"]["aggregate_sha256"]
        ):
            raise RuntimeError("candidate tree changed during scoring")
        record["gate_tree_after"] = _tree_record(gate_root, gate_excluded)
        if record["gate_tree_before"]["aggregate_sha256"] != record["gate_tree_after"]["aggregate_sha256"]:
            raise RuntimeError("evaluator tree changed during scoring")
        record["valid"] = True
    except BaseException as exc:
        record["invalid_reason"] = f"{type(exc).__name__}: {exc}"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0 if record["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
