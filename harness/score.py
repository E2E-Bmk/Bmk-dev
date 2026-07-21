#!/usr/bin/env python3
import argparse
import json
import os
import shlex
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path


def normalize_text(text):
    return (text or "").replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")


def run_python_case(case, solution_dir, timeout):
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
    actual = normalize_text(proc.stdout)
    expected = case["expected_output"].rstrip("\n")
    return proc.returncode == 0 and actual == expected, actual, expected, normalize_text(proc.stderr), proc.returncode


def command_to_line(command):
    if isinstance(command, dict):
        command = command["args"]
    return " ".join(shlex.quote(str(part)) for part in command)


def command_args(command):
    return command["args"] if isinstance(command, dict) else command


def json_equal_or_unordered(actual, expected, command_name):
    if command_name in {"KEYS", "SMEMBERS"} and isinstance(actual, list) and isinstance(expected, list):
        return sorted(actual) == sorted(expected)
    return actual == expected


def run_miniredis_case(case, solution_dir, timeout):
    script = solution_dir / "miniredis.py"
    if not script.exists():
        return False, "", "miniredis.py present", "missing miniredis.py", 127

    commands = case["commands"]
    stdin = "\n".join(command_to_line(cmd) for cmd in commands) + "\n"
    proc = subprocess.run(
        [sys.executable, str(script), "--batch"],
        cwd=solution_dir,
        input=stdin,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    stdout_lines = normalize_text(proc.stdout).splitlines() if normalize_text(proc.stdout) else []
    stderr = normalize_text(proc.stderr)

    output_by_step = {}
    cursor = 0
    for index, command in enumerate(commands):
        if isinstance(command, dict) and command.get("expect_error"):
            continue
        if cursor < len(stdout_lines):
            output_by_step[str(index)] = stdout_lines[cursor]
        cursor += 1

    failures = []
    checks = case.get("checks", {})

    for step, expected_lines in checks.get("step_stdout", {}).items():
        actual = output_by_step.get(str(step), "")
        for expected in expected_lines:
            if actual != str(expected):
                failures.append(f"step {step}: expected stdout {expected!r}, got {actual!r}")

    for step, expected in checks.get("step_stdout_json", {}).items():
        actual_line = output_by_step.get(str(step), "")
        try:
            actual = json.loads(actual_line)
        except Exception:
            failures.append(f"step {step}: stdout is not JSON: {actual_line!r}")
            continue
        cmd = commands[int(step)]
        cmd_name = (cmd["args"][0] if isinstance(cmd, dict) else cmd[0]).upper()
        if not json_equal_or_unordered(actual, expected, cmd_name):
            failures.append(f"step {step}: expected JSON {expected!r}, got {actual!r}")

    for step, expected_members in checks.get("step_stdout_json_contains", {}).items():
        actual_line = output_by_step.get(str(step), "")
        try:
            actual = json.loads(actual_line)
        except Exception:
            failures.append(f"step {step}: stdout is not JSON: {actual_line!r}")
            continue
        if isinstance(actual, dict):
            missing = [k for k in expected_members if k not in actual]
        elif isinstance(actual, (list, set, tuple)):
            missing = [x for x in expected_members if x not in actual]
        else:
            failures.append(f"step {step}: expected JSON collection, got {actual!r}")
            continue
        if missing:
            failures.append(f"step {step}: JSON missing {missing!r} from {actual!r}")

    for step, expected_len in checks.get("step_stdout_json_len", {}).items():
        actual_line = output_by_step.get(str(step), "")
        try:
            actual = json.loads(actual_line)
        except Exception:
            failures.append(f"step {step}: stdout is not JSON: {actual_line!r}")
            continue
        if len(actual) != expected_len:
            failures.append(f"step {step}: expected JSON length {expected_len}, got {len(actual)}")

    for step, bounds in checks.get("step_stdout_in_range", {}).items():
        actual_line = output_by_step.get(str(step), "")
        try:
            actual = int(float(actual_line))
        except Exception:
            failures.append(f"step {step}: stdout is not numeric: {actual_line!r}")
            continue
        low, high = bounds
        if not (low <= actual <= high):
            failures.append(f"step {step}: expected {low} <= {actual} <= {high}")

    for step in checks.get("step_expect_error", []):
        if not stderr:
            failures.append(f"step {step}: expected an error on stderr")

    for step, options in checks.get("step_stderr_contains_any", {}).items():
        lowered = stderr.lower()
        if not any(str(option).lower() in lowered for option in options):
            failures.append(f"step {step}: stderr did not contain any of {options!r}")

    has_expected_error = any(isinstance(command, dict) and command.get("expect_error") for command in commands)
    passed = (proc.returncode == 0 or has_expected_error) and not failures
    actual = "\n".join(stdout_lines)
    expected = "all rubric checks pass"
    if failures:
        expected = "\n".join(failures)
    return passed, actual, expected, stderr, proc.returncode


def is_bitcask_case(case, solution_dir):
    if not (solution_dir / "kvmini.py").exists():
        return False
    commands = case.get("commands", [])
    if not commands:
        return False
    return all(command_args(command) and command_args(command)[0] == "store" for command in commands)


def run_bitcask_case(case, solution_dir, timeout):
    script = solution_dir / "kvmini.py"
    if not script.exists():
        return False, "", "kvmini.py present", "missing kvmini.py", 127

    commands = case["commands"]
    output_by_step = {}
    failures = []
    stderr_lines = []
    exit_code = 0

    with tempfile.TemporaryDirectory() as td:
        dbdir = Path(td) / "store"
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env.update({str(k): str(v) for k, v in case.get("env", {}).items()})

        for index, command in enumerate(commands):
            args = [str(part) for part in command_args(command)]
            expect_error = isinstance(command, dict) and command.get("expect_error")
            if not args or args[0] != "store":
                failures.append(f"step {index}: unsupported Bitcask command shape {args!r}")
                continue

            proc = subprocess.run(
                [sys.executable, str(script), str(dbdir), *args[1:]],
                cwd=solution_dir,
                env=env,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
            )
            exit_code = proc.returncode
            stdout = normalize_text(proc.stdout)
            stderr = normalize_text(proc.stderr)
            if stderr:
                stderr_lines.append(f"step {index}: {stderr}")

            if expect_error:
                if proc.returncode == 0:
                    failures.append(f"step {index}: expected nonzero exit")
                continue

            if proc.returncode != 0:
                failures.append(f"step {index}: expected zero exit, got {proc.returncode}")
                continue
            output_by_step[str(index)] = stdout

    checks = case.get("checks", {})

    for step, expected in checks.get("stdout_equals", {}).items():
        actual = output_by_step.get(str(step), "")
        if actual != str(expected):
            failures.append(f"step {step}: expected stdout {expected!r}, got {actual!r}")

    for step, expected in checks.get("stdout_json", {}).items():
        actual_line = output_by_step.get(str(step), "")
        try:
            actual = json.loads(actual_line)
        except Exception:
            failures.append(f"step {step}: stdout is not JSON: {actual_line!r}")
            continue
        if actual != expected:
            failures.append(f"step {step}: expected JSON {expected!r}, got {actual!r}")

    passed = not failures
    actual = "\n".join(f"{step}: {output_by_step[step]}" for step in sorted(output_by_step, key=int))
    expected = "all rubric checks pass"
    if failures:
        expected = "\n".join(failures)
    return passed, actual, expected, "\n".join(stderr_lines), exit_code


def run_case(case, solution_dir, timeout):
    if "test_code" in case:
        return run_python_case(case, solution_dir, timeout)
    if "commands" in case:
        if is_bitcask_case(case, solution_dir):
            return run_bitcask_case(case, solution_dir, timeout)
        return run_miniredis_case(case, solution_dir, timeout)
    return False, "", "known rubric shape", "unsupported rubric item", 2


def score(rubrics_path, solution_dir, timeout):
    rubrics_payload = json.loads(rubrics_path.read_text(encoding="utf-8"))
    rubrics = rubrics_payload.get("items", rubrics_payload) if isinstance(rubrics_payload, dict) else rubrics_payload
    results = []
    for case in rubrics:
        try:
            passed, actual, expected, stderr, exit_code = run_case(case, solution_dir, timeout)
        except subprocess.TimeoutExpired:
            passed, actual, expected, stderr, exit_code = False, "", "complete before timeout", "timeout", 124
        result = {
            **case,
            "passed": passed,
            "actual": actual,
            "expected": expected,
            "stderr": stderr,
            "exit_code": exit_code,
        }
        results.append(result)

    total_weight = sum(int(r["weight"]) for r in results)
    passed_weight = sum(int(r["weight"]) for r in results if r["passed"])
    by_layer = defaultdict(lambda: {"weight": 0, "passed_weight": 0, "cases": 0, "passed": 0})
    by_category = defaultdict(lambda: {"weight": 0, "passed_weight": 0, "cases": 0, "passed": 0})
    for result in results:
        for bucket in (by_layer[result["layer"]], by_category[result["category"]]):
            bucket["weight"] += int(result["weight"])
            bucket["cases"] += 1
            if result["passed"]:
                bucket["passed_weight"] += int(result["weight"])
                bucket["passed"] += 1

    unit = by_layer["unit"]
    system = by_layer["system"]
    unit_score = unit["passed_weight"] / unit["weight"] if unit["weight"] else 0.0
    system_score = system["passed_weight"] / system["weight"] if system["weight"] else 0.0
    return {
        "rubrics": str(rubrics_path),
        "solution_dir": str(solution_dir),
        "total_cases": len(results),
        "passed_cases": sum(1 for r in results if r["passed"]),
        "total_weight": total_weight,
        "passed_weight": passed_weight,
        "score": passed_weight / total_weight if total_weight else 0.0,
        "unit_score": unit_score,
        "system_score": system_score,
        "gap_pp": (unit_score - system_score) * 100,
        "layers": dict(sorted(by_layer.items())),
        "categories": dict(sorted(by_category.items())),
        "failed_cases": [r for r in results if not r["passed"]],
        "all_cases": results,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("rubrics", type=Path)
    parser.add_argument("--solution-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    report = score(args.rubrics.resolve(), args.solution_dir.resolve(), args.timeout)
    print(f"Passed cases: {report['passed_cases']} / {report['total_cases']}")
    print(f"Weighted score: {report['passed_weight']} / {report['total_weight']}")
    print(f"Unit: {report['unit_score'] * 100:.2f}%")
    print(f"System: {report['system_score'] * 100:.2f}%")
    print(f"Gap: {report['gap_pp']:.2f}pp")
    for result in report["failed_cases"]:
        print(f"FAIL {result['id']}: {result['expected']}; actual={result['actual']!r}; stderr={result['stderr']!r}")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
