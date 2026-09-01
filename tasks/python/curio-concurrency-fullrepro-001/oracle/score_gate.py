from __future__ import annotations

import argparse
import ast
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import random


GATE = Path(__file__).resolve().parent
TEST_FILES = {
    "atomic": GATE / "tests" / "test_atomic.py",
    "integration": GATE / "tests" / "test_integration.py",
    "system_e2e": GATE / "tests" / "test_system.py",
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def discover_roots():
    roots = []
    for layer, path in TEST_FILES.items():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test_"):
                continue
            root = node.name.split("_", 2)[1].upper()
            roots.append({
                "root": root,
                "layer": layer,
                "nodeid": f"tests/{path.name}::{node.name}",
            })
    return roots


def parse_dependencies():
    dependencies = {}
    for line in (GATE / "ROOT-MAP.md").read_text(encoding="utf-8").splitlines():
        if not line.startswith("| A") and not line.startswith("| I") and not line.startswith("| S"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        dependencies[cells[0]] = [] if cells[3] == "-" else cells[3].split(",")
    return dependencies


def root_process(root, mode, candidate, report_dir, timeout, semantic_deadline):
    report_path = report_dir / f"{root['root']}.jsonl"
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "0"
    env["CURIO_V7_ROOT_REPORT"] = str(report_path)
    env["CURIO_V7_SEMANTIC_DEADLINE"] = str(semantic_deadline)
    env.pop("CURIO_V7_REFERENCE_PATCH", None)
    env.pop("CURIO_V7_INCOMPLETE_PATCH", None)
    if mode in {"reference", "incomplete_admission", "incomplete_completion"}:
        env["CURIO_V7_REFERENCE_PATCH"] = str(GATE / "reference_patch" / "curio_v7_patch.py")
    if mode == "incomplete_admission":
        env["CURIO_V7_INCOMPLETE_PATCH"] = str(
            GATE / "incomplete_dummy_patches" / "stalled_admission.py"
        )
    if mode == "incomplete_completion":
        env["CURIO_V7_INCOMPLETE_PATCH"] = str(
            GATE / "incomplete_dummy_patches" / "stalled_completion.py"
        )
    if candidate is not None:
        current = env.get("PYTHONPATH")
        env["PYTHONPATH"] = str(candidate) if not current else str(candidate) + os.pathsep + current
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "-q",
        root["nodeid"],
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=GATE,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        completed = None
        timed_out = True
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
    else:
        stdout = completed.stdout
        stderr = completed.stderr

    reports = []
    if report_path.exists():
        for line in report_path.read_text(encoding="utf-8").splitlines():
            reports.append(json.loads(line))
    phases = {record["when"]: record for record in reports}
    call = phases.get("call")
    setup = phases.get("setup")
    teardown = phases.get("teardown")
    infrastructure_valid = (
        not timed_out
        and setup is not None
        and setup["outcome"] == "passed"
        and call is not None
        and teardown is not None
        and teardown["outcome"] == "passed"
    )
    passed = infrastructure_valid and call["outcome"] == "passed"
    return {
        **root,
        "passed": passed,
        "infrastructure_valid": infrastructure_valid,
        "call_phase": call is not None,
        "outcome": None if call is None else call["outcome"],
        "exception_type": None if call is None else call["exception_type"],
        "returncode": None if completed is None else completed.returncode,
        "timed_out": timed_out,
        "semantic_deadline_failure": (
            "candidate behavior exceeded evaluator semantic deadline" in stdout
        ),
        "stdout": stdout[-4000:],
        "stderr": stderr[-4000:],
    }


def rate(results, layer=None, roots=None):
    selected = [item for item in results if (layer is None or item["layer"] == layer)]
    if roots is not None:
        selected = [item for item in selected if item["root"] in roots]
    return sum(item["passed"] for item in selected) / len(selected) if selected else None


def score(results, config, dependencies):
    by_root = {item["root"]: item for item in results}
    atomic = rate(results, "atomic")
    integration = rate(results, "integration")
    system = rate(results, "system_e2e")
    composition_items = [item for item in results if item["layer"] != "atomic"]
    composition = sum(item["passed"] for item in composition_items) / len(composition_items)
    combined = (atomic + composition) / 2
    mutation_roots = set(config["mutation_roots"])
    conditional = []
    for item in composition_items:
        prereqs = dependencies.get(item["root"], [])
        if all(by_root[root]["passed"] for root in prereqs):
            conditional.append(item)
    conditional_rate = (
        sum(item["passed"] for item in conditional) / len(conditional)
        if conditional else None
    )
    adjusted_gap = None if conditional_rate is None else atomic - conditional_rate
    return {
        "atomic_rate": atomic,
        "integration_rate": integration,
        "system_e2e_rate": system,
        "composition_rate": composition,
        "combined": combined,
        "gap": atomic - composition,
        "native_all_root_rate": rate(results),
        "conditional_composition_rate": conditional_rate,
        "conditional_composition_eligible": len(conditional),
        "adjusted_gap": adjusted_gap,
        "mutation_root_rate": rate(results, roots=mutation_roots),
        "non_mutation_root_rate": rate(results, roots=set(by_root) - mutation_roots),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=(
            "reference",
            "upstream",
            "candidate",
            "dummy",
            "incomplete_admission",
            "incomplete_completion",
        ),
        required=True,
    )
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=12)
    parser.add_argument("--semantic-deadline", type=float, default=4.0)
    parser.add_argument("--root-order", choices=("natural", "reverse", "permuted"), default="natural")
    parser.add_argument("--order-seed", type=int, default=7001)
    args = parser.parse_args()
    if args.mode in {"candidate", "dummy"} and args.candidate is None:
        parser.error("--candidate is required for candidate and dummy modes")
    candidate = args.candidate.resolve() if args.candidate is not None else None
    config = json.loads((GATE / "SCORER-CONFIG.json").read_text(encoding="utf-8"))
    roots = discover_roots()
    execution_roots = list(roots)
    if args.root_order == "reverse":
        execution_roots.reverse()
    elif args.root_order == "permuted":
        random.Random(args.order_seed).shuffle(execution_roots)
    dependencies = parse_dependencies()
    if len(roots) != 60 or len({item["root"] for item in roots}) != 60:
        raise SystemExit("root discovery did not produce 60 unique roots")

    with tempfile.TemporaryDirectory(prefix="curio-v7-roots-") as directory:
        report_dir = Path(directory)
        results = []
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(
                    root_process,
                    root,
                    args.mode,
                    candidate,
                    report_dir,
                    args.timeout,
                    args.semantic_deadline,
                ): root
                for root in execution_roots
            }
            for future in as_completed(futures):
                results.append(future.result())
    order = {item["root"]: index for index, item in enumerate(roots)}
    results.sort(key=lambda item: order[item["root"]])
    scores = score(results, config, dependencies)
    pass_roots = [item["root"] for item in results if item["passed"]]
    invalid = [item["root"] for item in results if not item["infrastructure_valid"]]
    semantic_deadlines = [item["root"] for item in results if item["semantic_deadline_failure"]]
    formerly_unbounded = {"A09", "A15", "I04", "I22", "I24"}
    termination_audit_complete = (
        args.mode not in {"incomplete_admission", "incomplete_completion"}
        or (not invalid and formerly_unbounded.issubset(semantic_deadlines))
    )
    m2_expected = config["m2_expected_pass_roots"]
    payload = {
        "schema_version": 2,
        "suite": config["suite"],
        "mode": args.mode,
        "constitution": config["constitution"],
        "formula": config["formula"],
        "fresh_process_per_root": True,
        "root_order": args.root_order,
        "order_seed": args.order_seed if args.root_order == "permuted" else None,
        "semantic_deadline_seconds": args.semantic_deadline,
        "candidate": None if candidate is None else str(candidate),
        "asset_hashes": {
            "spec": sha256(GATE / "SPEC.md"),
            "root_map": sha256(GATE / "ROOT-MAP.md"),
            "scorer_config": sha256(GATE / "SCORER-CONFIG.json"),
        },
        "scores": scores,
        "passed_roots": pass_roots,
        "failed_roots": [item["root"] for item in results if not item["passed"]],
        "infrastructure_invalid_roots": invalid,
        "semantic_deadline_failure_roots": semantic_deadlines,
        "incomplete_dummy_termination_audit_complete": termination_audit_complete,
        "m2_exact_preregistration_match": args.mode != "upstream" or pass_roots == m2_expected,
        "dummy_call_phase_zero": (
            args.mode != "dummy"
            or (not pass_roots and not invalid and all(item["call_phase"] for item in results))
        ),
        "roots": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "mode": args.mode,
        "scores": scores,
        "passed": len(pass_roots),
        "failed": len(results) - len(pass_roots),
        "invalid": invalid,
        "m2_exact": payload["m2_exact_preregistration_match"],
        "dummy_call_phase_zero": payload["dummy_call_phase_zero"],
        "root_order": args.root_order,
        "semantic_deadline_failures": semantic_deadlines,
        "termination_audit_complete": termination_audit_complete,
    }, indent=2))
    if invalid:
        raise SystemExit(2)
    if args.mode == "reference" and len(pass_roots) != 60:
        raise SystemExit(3)
    if args.mode == "upstream" and not payload["m2_exact_preregistration_match"]:
        raise SystemExit(4)
    if args.mode == "dummy" and not payload["dummy_call_phase_zero"]:
        raise SystemExit(5)
    if args.mode in {"incomplete_admission", "incomplete_completion"} and not termination_audit_complete:
        raise SystemExit(6)


if __name__ == "__main__":
    main()
