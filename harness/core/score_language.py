#!/usr/bin/env python3
"""Local language-dispatch scorer.

This is the construction-side companion to the sandbox runner contracts in
``harness.runners``. It is intentionally small: the released Python scorer keeps
its historical CLI in ``score_pytest_original.py``, while this entry point makes
non-Python runners executable locally during task construction.

Rust is the first fully automated target here. The scorer copies the candidate
and oracle into a temporary run tree, lets ``RustRunner.setup`` inject Cargo
``[patch.crates-io]`` entries, runs nextest batches, records provenance, and
writes the same high-level score fields used by the Python scorer.
"""

from __future__ import annotations

import argparse
import csv
import json
import platform as _platform
import re
import shlex
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# Direct execution puts this file's own directory on the import path rather than
# the repository root, so the absolute `harness.` imports below would not
# resolve. Adding the root keeps the script form and the module form equivalent.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from harness.runners import Env, get_runner


def json_safe(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [json_safe(v) for v in value]
    return value


def load_task(task_dir: Path) -> dict[str, Any]:
    for candidate in (task_dir / "task.json", task_dir.parent / "task.json"):
        if candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8-sig"))
    return {}


def load_taxonomy(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    if not path.exists():
        raise SystemExit(f"taxonomy file not found: {path}")
    if path.suffix == ".jsonl":
        mapping: dict[str, str] = {}
        with path.open(encoding="utf-8-sig") as stream:
            for line in stream:
                if not line.strip():
                    continue
                row = json.loads(line)
                key = row.get("taxonomy_key") or row.get("test_id") or row.get("nodeid")
                if key:
                    mapping[str(key)] = str(row.get("layer") or "unknown")
        return mapping
    mapping: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            key = row.get("taxonomy_key") or row.get("test_id") or row.get("nodeid")
            if key and row.get("keep", "yes") != "no":
                mapping[str(key)] = str(row.get("layer") or "unknown")
    return mapping


def resolve_oracle_dir(task_dir: Path, override: Path | None) -> Path:
    if override is not None:
        return override.resolve()
    if (task_dir / "oracle").is_dir():
        return (task_dir / "oracle").resolve()
    if (task_dir / "filter").is_dir():
        return (task_dir / "filter").resolve()
    return task_dir.resolve()


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    ignore = shutil.ignore_patterns(
        ".git",
        "target",
        ".pytest_cache",
        "__pycache__",
        "*.pyc",
        "node_modules",
    )
    shutil.copytree(src, dst, ignore=ignore)


def infer_crate_names(solution_dir: Path) -> list[str]:
    manifest = solution_dir / "Cargo.toml"
    if not manifest.exists():
        return []
    text = manifest.read_text(encoding="utf-8-sig", errors="replace")
    package = re.search(r'(?ms)^\s*\[package\].*?^\s*name\s*=\s*"([^"]+)"', text)
    if package:
        return [package.group(1)]
    workspace = re.search(r'(?ms)^\s*\[workspace\.package\].*?^\s*name\s*=\s*"([^"]+)"', text)
    return [workspace.group(1)] if workspace else []


def target_modules(task_data: dict[str, Any], solution_dir: Path, explicit: list[str]) -> tuple[str, ...]:
    roots: Any = explicit or (
        task_data.get("target_crates")
        or task_data.get("target_imports")
        or task_data.get("oracle", {}).get("target_crates")
        or task_data.get("oracle", {}).get("target_imports")
        or infer_crate_names(solution_dir)
    )
    if isinstance(roots, str):
        roots = [roots]
    return tuple(str(root) for root in roots or [])


def run_shell(command: str, cwd: Path, timeout: int) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["/bin/bash", "-lc", command],
            cwd=cwd,
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
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "timeout": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "returncode": 124,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "timeout",
            "timeout": True,
        }


def run_setup(runner: Any, env: Env, cwd: Path) -> tuple[list[dict[str, Any]], bool]:
    records: list[dict[str, Any]] = []
    ok = True
    for step in runner.setup(env):
        record = run_shell(step.command, cwd, step.timeout)
        record["required"] = step.required
        record["capture"] = step.capture
        records.append(record)
        if step.required and record["returncode"] != 0:
            ok = False
            break
    return records, ok


def run_provenance(runner: Any, env: Env, cwd: Path, workspace: Path) -> dict[str, Any]:
    command = runner.provenance(env)
    if not command:
        return {"command": None, "rows": [], "errors": []}
    record = run_shell(command, cwd, 120)
    rows = []
    for line in (record.get("stdout") or "").splitlines():
        if not line.startswith("__PROVENANCE__"):
            continue
        try:
            rows = json.loads(line.removeprefix("__PROVENANCE__"))
        except json.JSONDecodeError as exc:
            record.setdefault("errors", []).append(f"invalid provenance JSON: {exc}")
    workspace_real = workspace.resolve()
    errors = list(record.get("errors", []))
    for row in rows:
        row_paths = [Path(path).resolve() for path in row.get("paths", [])]
        if not row_paths:
            errors.append(f"{row.get('name')}: no resolved manifest path")
            continue
        if not any(_is_relative_to(path, workspace_real) for path in row_paths):
            errors.append(
                f"{row.get('name')}: resolved outside candidate workspace: "
                + ", ".join(str(path) for path in row_paths)
            )
    record["rows"] = rows
    record["errors"] = errors
    return record


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def rust_filter_name(test_id: str) -> str:
    return test_id.split("::", 1)[1] if "::" in test_id else test_id


def run_rust_batch(
    runner: Any,
    oracle: Path,
    suite: str,
    tests: list[str],
    offset: int,
    timeout: int,
) -> dict[str, Any]:
    report = oracle.parent / f"rb_{suite}_{offset:03d}.json"
    stderr_path = oracle.parent / f"rb_{suite}_{offset:03d}.stderr"
    names = " + ".join(f"test(={rust_filter_name(test)})" for test in sorted(set(tests)))
    command = (
        f"cd {shlex.quote(str(oracle / suite))} && "
        f"NEXTEST_EXPERIMENTAL_LIBTEST_JSON=1 timeout {timeout} "
        "cargo nextest run --message-format libtest-json "
        f"-E {shlex.quote(names)} "
        f"> {shlex.quote(str(report))} 2>{shlex.quote(str(stderr_path))}"
    )
    record = run_shell(command, oracle.parent, timeout + 30)
    report_text = report.read_text(encoding="utf-8-sig", errors="replace") if report.exists() else ""
    stderr_text = stderr_path.read_text(encoding="utf-8-sig", errors="replace") if stderr_path.exists() else ""
    outcomes = runner.outcomes(report_text, "")
    if outcomes is None:
        outcome = "timeout" if record["returncode"] == 124 else "no_report"
        outcomes = {test: outcome for test in tests}
    else:
        for test in tests:
            outcomes.setdefault(test, "not_reported")
    record.update(
        {
            "suite": suite,
            "offset": offset,
            "tests": tests,
            "report": str(report),
            "stderr_file": str(stderr_path),
            "report_text": report_text,
            "stderr_text": stderr_text,
            "outcomes": outcomes,
        }
    )
    return record


def taxonomy_layer(task_data: dict[str, Any], test_id: str, suite: str, override: dict[str, str]) -> str:
    taxonomy = override or task_data.get("taxonomy") or {}
    return str(taxonomy.get(test_id) or ("atomic" if suite == "atomic" else "integration"))


def summarize(cases: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, int] = defaultdict(int)
    by_layer: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    function_outcomes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        outcome = str(case["outcome"])
        layer = str(case["layer"])
        summary[outcome] += 1
        summary["total"] += 1
        by_layer[layer][outcome] += 1
        by_layer[layer]["total"] += 1
        function_outcomes[case["base_nodeid"]].append(case)

    function_cases = []
    for key, grouped in sorted(function_outcomes.items()):
        passed = all(case["outcome"] == "passed" for case in grouped)
        layer = grouped[0]["layer"] if grouped else "unknown"
        function_cases.append(
            {
                "base_nodeid": key,
                "layer": layer,
                "outcome": "passed" if passed else "failed",
                "case_count": len(grouped),
            }
        )

    passed = summary.get("passed", 0)
    skipped = summary.get("skipped", 0)
    effective_total = max(1, summary["total"] - skipped)
    return {
        "summary": dict(sorted(summary.items())),
        "pass_rate_excluding_skips": passed / effective_total,
        "by_layer": {key: dict(sorted(value.items())) for key, value in sorted(by_layer.items())},
        "function_cases": function_cases,
    }


def score_rust(
    args: argparse.Namespace,
    task_data: dict[str, Any],
    oracle_host: Path,
    taxonomy: dict[str, str],
) -> dict[str, Any]:
    runner = get_runner("rust")
    run_dir = args.run_dir.resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    workspace = run_dir / "workspace"
    oracle = run_dir / "oracle"
    copy_tree(args.solution_dir.resolve(), workspace)
    copy_tree(oracle_host.resolve(), oracle)

    targets = target_modules(task_data, args.solution_dir.resolve(), args.target_crate)
    env = Env(
        workspace=str(workspace),
        oracle=str(oracle),
        workspace_host=args.solution_dir.resolve(),
        oracle_host=oracle_host.resolve(),
        target_modules=targets,
    )

    atomic = runner.discover(oracle_host, "atomic")
    integration = runner.discover(oracle_host, "integration")
    setup_records, setup_ok = run_setup(runner, env, run_dir)
    provenance = run_provenance(runner, env, run_dir, workspace) if setup_ok else {}

    batches: list[dict[str, Any]] = []
    cases: list[dict[str, Any]] = []
    if setup_ok:
        for suite, tests in (("atomic", atomic), ("integration", integration)):
            for offset in range(0, len(tests), args.batch_size):
                chunk = tests[offset : offset + args.batch_size]
                batch = run_rust_batch(runner, oracle, suite, chunk, offset, args.timeout)
                batches.append(batch)
                for test in chunk:
                    outcome = batch["outcomes"].get(test, "not_reported")
                    cases.append(
                        {
                            "nodeid": test,
                            "base_nodeid": runner.function_of(test),
                            "layer": taxonomy_layer(task_data, test, suite, taxonomy),
                            "outcome": outcome,
                        }
                    )
    else:
        for suite, tests in (("atomic", atomic), ("integration", integration)):
            for test in tests:
                cases.append(
                    {
                        "nodeid": test,
                        "base_nodeid": runner.function_of(test),
                        "layer": taxonomy_layer(task_data, test, suite, taxonomy),
                        "outcome": "setup_error",
                    }
                )

    report = {
        "platform": _platform.platform(),
        "python_version": sys.version,
        "language": "rust",
        "timeout_seconds": args.timeout,
        "batch_size": args.batch_size,
        "task_dir": str(args.task_dir.resolve()) if args.task_dir else None,
        "oracle_dir": str(oracle_host.resolve()),
        "solution_dir": str(args.solution_dir.resolve()),
        "run_dir": str(run_dir),
        "target_modules": list(targets),
        "setup_ok": setup_ok,
        "setup_steps": setup_records,
        "provenance": provenance,
        "batches": batches,
        "cases": cases,
        **summarize(cases),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-dir", type=Path, required=True)
    parser.add_argument("--oracle-dir", type=Path)
    parser.add_argument("--solution-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--language")
    parser.add_argument("--taxonomy", type=Path)
    parser.add_argument("--target-crate", action="append", default=[])
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--batch-size", type=int, default=20)
    args = parser.parse_args()

    task_dir = args.task_dir.resolve()
    oracle_host = resolve_oracle_dir(task_dir, args.oracle_dir)
    task_data = load_task(task_dir)
    taxonomy = load_taxonomy(args.taxonomy.resolve() if args.taxonomy else None)
    language = (args.language or task_data.get("language") or "python").lower()
    if language != "rust":
        raise SystemExit(
            f"score_language.py currently automates Rust scoring; use "
            f"harness/score_pytest_original.py for language={language!r}"
        )
    if not target_modules(task_data, args.solution_dir.resolve(), args.target_crate):
        raise SystemExit("missing target crate; set task.json target_crates or pass --target-crate")

    report = json_safe(score_rust(args, task_data, oracle_host, taxonomy))
    out = args.json_out or args.run_dir / "score.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("summary", "pass_rate_excluding_skips", "by_layer")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
