from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


GATE = Path(__file__).resolve().parent


def hash_tree(root: Path) -> str:
    digest = hashlib.sha256()
    excluded_dirs = {"__pycache__", ".pytest_cache", ".git"}
    excluded_suffixes = {".pyc", ".pyo"}
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root)
        if any(part in excluded_dirs for part in relative.parts):
            continue
        if path.is_file() and path.suffix not in excluded_suffixes:
            digest.update(relative.as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def rates(passed, root_map, dependencies):
    layers = {"atomic": [], "integration": [], "system": []}
    for root, record in root_map.items():
        layers[record["layer"]].append(root)

    def rate(roots):
        return sum(root in passed for root in roots) / len(roots)

    atomic = rate(layers["atomic"])
    integration = rate(layers["integration"])
    system = rate(layers["system"])
    composition_roots = layers["integration"] + layers["system"]
    composition = rate(composition_roots)
    eligible = [root for root in composition_roots if all(item in passed for item in dependencies[root])]
    conditional = rate(eligible) if eligible else None
    mutation_roots = [root for root, record in root_map.items() if record["mutation"]]
    ordinary_roots = [root for root, record in root_map.items() if not record["mutation"]]
    combined = (atomic + composition) / 2
    return {
        "atomic": atomic,
        "integration": integration,
        "system": system,
        "composition": composition,
        "combined": combined,
        "gap": atomic - composition,
        "native_all_root": len(passed) / len(root_map),
        "conditional_composition": conditional,
        "adjusted_gap": None if conditional is None else atomic - conditional,
        "conditional_eligible_roots": eligible,
        "mutation_root_rate": rate(mutation_roots),
        "non_mutation_root_rate": rate(ordinary_roots),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Score one nbformat candidate in a fresh pytest process")
    parser.add_argument("candidate")
    parser.add_argument("--expect", choices=("m1", "m2", "dummy"))
    parser.add_argument("--order-mode", choices=("natural", "reverse", "permuted"), default="natural")
    parser.add_argument("--receipt")
    args = parser.parse_args(argv)

    candidate = Path(args.candidate).resolve()
    if not (candidate / "nbformat").is_dir():
        parser.error("candidate must contain an nbformat package directory")

    root_map = json.loads((GATE / "ROOT-MAP.json").read_text(encoding="utf-8"))["roots"]
    dependencies = json.loads((GATE / "DEPENDENCY-MAP.json").read_text(encoding="utf-8"))["dependencies"]
    prereg = json.loads((GATE / "PREREGISTRATION.json").read_text(encoding="utf-8"))
    before_hash = hash_tree(candidate)

    environment = os.environ.copy()
    environment.update({
        "NBF_GATE_CANDIDATE": str(candidate),
        "PYTHONPATH": str(candidate),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUTF8": "1",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "NBF_GATE_ORDER_MODE": args.order_mode,
    })
    with tempfile.TemporaryDirectory(prefix=".nbformat-v5-score-", dir=GATE) as temporary:
        temp = Path(temporary)
        phase_receipt = temp / "phases.json"
        environment["NBF_GATE_PHASE_RECEIPT"] = str(phase_receipt)
        launcher = (
            "import sys,pytest; "
            "sys.path.insert(0,sys.argv[1]); "
            "raise SystemExit(pytest.main(sys.argv[2:]))"
        )
        command = [
            sys.executable, "-B", "-c", launcher, str(candidate), str(GATE / "tests"),
            "-q", "--tb=no", "--basetemp", str(temp / "pytest"),
        ]
        completed = subprocess.run(
            command, cwd=GATE, env=environment, text=True, encoding="utf-8", errors="replace",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180, check=False,
        )
        phases = json.loads(phase_receipt.read_text(encoding="utf-8")) if phase_receipt.exists() else {
            "roots": {}, "exitstatus": None, "order_mode": None, "collection_order": []
        }
        provenance_command = [
            sys.executable, "-B", "-c",
            "import pathlib,sys;sys.path.insert(0,sys.argv[1]);import nbformat;print(pathlib.Path(nbformat.__file__).resolve())",
            str(candidate),
        ]
        provenance = subprocess.run(
            provenance_command, cwd=GATE, env=environment, text=True, encoding="utf-8", errors="replace",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False,
        )

    expected_roots = set(root_map)
    observed_roots = set(phases["roots"])
    passed = {
        root for root, records in phases["roots"].items()
        if records.get("setup") == records.get("call") == records.get("teardown") == "passed"
    }
    failed = expected_roots - passed
    phase_invalid = {
        root: records for root, records in phases["roots"].items()
        if records.get("setup") != "passed" or records.get("teardown") != "passed" or "call" not in records
    }
    call_failure_invalid = {
        root: phases["roots"].get(root, {}).get("call")
        for root in failed
        if phases["roots"].get(root, {}).get("call") != "failed"
    }
    thread_audits = phases.get("thread_audits", [])
    thread_audit_invalid = [
        audit for audit in thread_audits
        if audit.get("thread_alive") or audit.get("live_owned")
    ]
    provenance_path = Path(provenance.stdout.strip()).resolve() if provenance.returncode == 0 and provenance.stdout.strip() else None
    try:
        provenance_ok = provenance_path is not None and provenance_path.is_relative_to(candidate)
    except AttributeError:
        provenance_ok = provenance_path is not None and str(provenance_path).startswith(str(candidate) + os.sep)
    after_hash = hash_tree(candidate)

    exact_ok = True
    expected_passed = None
    if args.expect:
        expected_passed = set(prereg["expected_pass_roots"][args.expect])
        exact_ok = passed == expected_passed
    qualified = (
        observed_roots == expected_roots
        and phases.get("order_mode") == args.order_mode
        and len(phases.get("collection_order", [])) == len(expected_roots)
        and not phase_invalid
        and not call_failure_invalid
        and not thread_audit_invalid
        and provenance_ok
        and before_hash == after_hash
        and exact_ok
    )
    receipt = {
        "schema_version": 1,
        "suite": "nbformat-v5-gate-draft-a",
        "scorer_process": os.getpid(),
        "test_process_returncode": completed.returncode,
        "candidate": str(candidate),
        "candidate_hash_before": before_hash,
        "candidate_hash_after": after_hash,
        "candidate_tree_immutable": before_hash == after_hash,
        "provenance_path": None if provenance_path is None else str(provenance_path),
        "provenance_ok": provenance_ok,
        "observed_root_count": len(observed_roots),
        "passed_roots": sorted(passed),
        "failed_roots": sorted(failed),
        "phase_invalid": phase_invalid,
        "call_failure_invalid": call_failure_invalid,
        "thread_audits": thread_audits,
        "thread_audit_invalid": thread_audit_invalid,
        "order_mode": args.order_mode,
        "observed_order_mode": phases.get("order_mode"),
        "collection_order": phases.get("collection_order", []),
        "rates": rates(passed, root_map, dependencies),
        "expectation": args.expect,
        "exact_vector_match": exact_ok,
        "qualified": qualified,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }
    rendered = json.dumps(receipt, indent=2, sort_keys=True)
    if args.receipt:
        Path(args.receipt).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if qualified else 2


if __name__ == "__main__":
    raise SystemExit(main())
