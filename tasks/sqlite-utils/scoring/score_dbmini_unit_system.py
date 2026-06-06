#!/usr/bin/env python3
"""Score MiniSQLiteUtils unit/system rubrics against a candidate solution."""

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path


def norm(text):
    return (text or "").replace("\r\n", "\n").replace("\r", "\n")


def command_for(solution_dir):
    script = solution_dir / "dbmini.py"
    if script.exists():
        return ["py", "-3.11", str(script)]
    executable = solution_dir / "dbmini"
    if executable.exists():
        return [str(executable)]
    raise FileNotFoundError(f"no dbmini.py or dbmini executable found in {solution_dir}")


def write_files(base, files):
    for rel, text in files.items():
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def setup_sql(tmpdir, case):
    statements = case.get("setup_sql", [])
    if not statements:
        return
    db_name = case.get("database", "data.db")
    db_path = tmpdir / db_name
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript("\n".join(statements))
        conn.commit()
    finally:
        conn.close()


def run_case(case, solution_dir, timeout):
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        write_files(tmpdir, case.get("setup_files", {}))
        setup_sql(tmpdir, case)
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        command_results = []
        for raw in case.get("commands", []):
            if isinstance(raw, dict):
                cmd_args = raw["args"]
                expect_error = raw.get("expect_error", False)
            else:
                cmd_args = raw
                expect_error = False
            proc = subprocess.run(
                command_for(solution_dir) + cmd_args,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                cwd=str(tmpdir),
                env=env,
                timeout=timeout,
            )
            command_results.append({
                "args": cmd_args,
                "expect_error": expect_error,
                "exit_code": proc.returncode,
                "stdout": norm(proc.stdout),
                "stderr": norm(proc.stderr),
            })
        errors = evaluate(case, tmpdir, command_results)
        return {**case, "passed": not errors, "errors": errors, "command_results": command_results}


def parse_stdout_json(result):
    text = result["stdout"].strip()
    if not text:
        return None
    return json.loads(text)


def rows_for_sql(db_path, sql):
    conn = sqlite3.connect(str(db_path))
    try:
        return [list(row) for row in conn.execute(sql).fetchall()]
    finally:
        conn.close()


def evaluate(case, tmpdir, command_results):
    checks = case.get("checks", {})
    errors = []
    for index, result in enumerate(command_results):
        if result["expect_error"]:
            if result["exit_code"] == 0:
                errors.append(f"command {index} expected non-zero exit")
        elif result["exit_code"] != 0:
            errors.append(f"command {index} exit {result['exit_code']}, expected 0; stderr={result['stderr']!r}")

    db_name = case.get("database")
    if not db_name:
        for result in command_results:
            if result["args"]:
                db_name = result["args"][0]
                break
    db_path = tmpdir / (db_name or "data.db")

    for idx, expected in checks.get("stdout_json", {}).items():
        try:
            actual = parse_stdout_json(command_results[int(idx)])
        except Exception as exc:
            errors.append(f"command {idx} stdout invalid JSON: {exc}; stdout={command_results[int(idx)]['stdout']!r}")
            continue
        if actual != expected:
            errors.append(f"command {idx} JSON mismatch: expected {expected!r}, got {actual!r}")

    for idx, expected_items in checks.get("stdout_json_contains", {}).items():
        try:
            actual = parse_stdout_json(command_results[int(idx)])
        except Exception as exc:
            errors.append(f"command {idx} stdout invalid JSON: {exc}; stdout={command_results[int(idx)]['stdout']!r}")
            continue
        if not isinstance(actual, list):
            errors.append(f"command {idx} JSON is not a list: {actual!r}")
            continue
        for expected in expected_items:
            if not any(all(row.get(k) == v for k, v in expected.items()) for row in actual if isinstance(row, dict)):
                errors.append(f"command {idx} JSON missing item fragment {expected!r}; got {actual!r}")

    for idx, needles in checks.get("stdout_contains", {}).items():
        stdout = command_results[int(idx)]["stdout"]
        for needle in needles:
            if needle not in stdout:
                errors.append(f"command {idx} stdout missing {needle!r}; stdout={stdout!r}")

    for sql, expected in checks.get("sql", {}).items():
        try:
            actual = rows_for_sql(db_path, sql)
        except Exception as exc:
            errors.append(f"SQL failed {sql!r}: {exc}")
            continue
        if actual != expected:
            errors.append(f"SQL mismatch for {sql!r}: expected {expected!r}, got {actual!r}")
    return errors


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
    selected = [r for r in results if r.get("layer") == layer]
    total = sum(int(r["weight"]) for r in selected)
    passed = sum(int(r["weight"]) for r in selected if r["passed"])
    return {
        "weight": total,
        "passed_weight": passed,
        "score": passed / total if total else None,
        "cases": len(selected),
        "passed_cases": sum(1 for r in selected if r["passed"]),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("rubrics", type=Path)
    parser.add_argument("--solution-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    rubrics = json.loads(args.rubrics.read_text(encoding="utf-8"))
    results = [run_case(case, args.solution_dir, args.timeout) for case in rubrics]
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
        message = f"FAIL {result['id']}: {'; '.join(result['errors'])}"
        enc = getattr(sys.stdout, "encoding", None) or "utf-8"
        print(message.encode(enc, errors="replace").decode(enc, errors="replace"))
    if args.json_out:
        args.json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
