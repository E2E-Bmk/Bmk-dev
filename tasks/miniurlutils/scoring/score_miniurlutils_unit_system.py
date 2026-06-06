#!/usr/bin/env python3
"""Score MiniURLUtils unit/system rubrics against a candidate solution."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path


def norm(text):
    return (text or "").replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")


def run_case(case, solution_dir, timeout):
    with tempfile.TemporaryDirectory() as td:
        script = Path(td) / "case.py"
        script.write_text(case["test_code"], encoding="utf-8")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(solution_dir)
        env["PYTHONUTF8"] = "1"
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=td,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    actual = norm(proc.stdout)
    expected = case["expected_output"].rstrip("\n")
    errors = []
    if proc.returncode != 0:
        errors.append(f"exit {proc.returncode}; stderr={norm(proc.stderr)!r}")
    if actual != expected:
        errors.append(f"expected {expected!r}, got {actual!r}")
    return {
        **case,
        "passed": not errors,
        "errors": errors,
        "actual": actual,
        "expected": expected,
        "stderr": norm(proc.stderr),
        "exit_code": proc.returncode,
    }


def bucket_summary(results, key_fn):
    bucket = defaultdict(lambda: {"weight": 0, "passed_weight": 0, "cases": 0, "passed": 0})
    for result in results:
        weight = int(result["weight"])
        key = key_fn(result)
        bucket[key]["weight"] += weight
        bucket[key]["cases"] += 1
        if result["passed"]:
            bucket[key]["passed_weight"] += weight
            bucket[key]["passed"] += 1
    return dict(sorted(bucket.items()))


def score_for(results, layer):
    selected = [result for result in results if result.get("layer") == layer]
    total = sum(int(result["weight"]) for result in selected)
    passed = sum(int(result["weight"]) for result in selected if result["passed"])
    return {
        "weight": total,
        "passed_weight": passed,
        "score": passed / total if total else None,
        "cases": len(selected),
        "passed_cases": sum(1 for result in selected if result["passed"]),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("rubrics", type=Path)
    parser.add_argument("--solution-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    rubrics = json.loads(args.rubrics.read_text(encoding="utf-8"))
    results = [run_case(case, args.solution_dir.resolve(), args.timeout) for case in rubrics]
    total_weight = sum(int(result["weight"]) for result in results)
    passed_weight = sum(int(result["weight"]) for result in results if result["passed"])
    unit_score = score_for(results, "unit")
    system_score = score_for(results, "system")
    gap = None
    if unit_score["score"] is not None and system_score["score"] is not None:
        gap = unit_score["score"] - system_score["score"]

    report = {
        "total_cases": len(results),
        "passed_cases": sum(1 for result in results if result["passed"]),
        "total_weight": total_weight,
        "passed_weight": passed_weight,
        "score": passed_weight / total_weight if total_weight else 0,
        "unit_score": unit_score,
        "system_score": system_score,
        "unit_system_gap": gap,
        "layers": bucket_summary(results, lambda r: r.get("layer", "unspecified")),
        "categories": bucket_summary(results, lambda r: r.get("category", "unspecified")),
        "system_dimensions": bucket_summary(
            [r for r in results if r.get("layer") == "system"],
            lambda r: r.get("system_dimension", "unspecified"),
        ),
        "failed_cases": [result for result in results if not result["passed"]],
        "all_cases": results,
    }

    print(f"Passed cases: {report['passed_cases']} / {report['total_cases']}")
    print(f"Weighted score: {passed_weight} / {total_weight}")
    print(f"Unit score: {unit_score['passed_weight']} / {unit_score['weight']} = {unit_score['score'] * 100:.2f}%")
    print(f"System score: {system_score['passed_weight']} / {system_score['weight']} = {system_score['score'] * 100:.2f}%")
    print(f"Gap: {gap * 100:.2f}pp")
    for result in report["failed_cases"]:
        print(f"FAIL {result['id']}: {'; '.join(result['errors'])}")
    if args.json_out:
        args.json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
