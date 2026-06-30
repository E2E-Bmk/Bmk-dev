#!/usr/bin/env python3
"""Score a candidate package against a filtered subset of an upstream pytest suite.

This runner is intentionally file-grouped. A collection/import error in one
test module is recorded for that module, but it does not prevent unrelated test
files from executing.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


def read_nodeids(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def taxonomy_key(pytest_nodeid: str) -> str:
    nodeid = re.sub(r"\[.*\]$", "", pytest_nodeid)
    parts = nodeid.split("::")
    stem = Path(parts[0]).stem
    if len(parts) > 2:
        return f"{stem}::" + ".".join(parts[1:])
    return "::".join([stem, *parts[1:]])


def load_taxonomy(path: Path | None) -> dict[str, str]:
    if not path:
        return {}
    mapping: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("keep") == "yes" and row.get("test_id"):
                mapping[row["test_id"]] = row.get("layer") or "unknown"
    return mapping


def copy_oracle_tree(source_repo: Path, worktree: Path, remove_paths: list[str]) -> None:
    if worktree.exists():
        shutil.rmtree(worktree)
    ignore = shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".pytest_cache")
    shutil.copytree(source_repo, worktree, ignore=ignore)
    for rel in remove_paths:
        target = worktree / rel
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()


def group_by_file(nodeids: list[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for nodeid in nodeids:
        grouped[nodeid.split("::", 1)[0]].append(nodeid)
    return dict(sorted(grouped.items()))


def run_group(
    worktree: Path,
    nodeids: list[str],
    report_path: Path,
    timeout: int,
    extra_args: list[str],
) -> tuple[int, dict]:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "--json-report",
        "--json-report-file",
        str(report_path),
        *extra_args,
        *nodeids,
    ]
    proc = subprocess.run(
        cmd,
        cwd=worktree,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    payload = {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }
    if report_path.exists():
        payload["json_report"] = json.loads(report_path.read_text(encoding="utf-8"))
    return proc.returncode, payload


def summarize(
    nodeids: list[str],
    grouped_results: dict[str, dict],
    taxonomy: dict[str, str],
) -> dict:
    cases = []
    seen_base_nodeids = set()
    for file_name, payload in grouped_results.items():
        report = payload.get("json_report") or {}
        tests = report.get("tests") or []
        if not tests:
            for nodeid in group_by_file(nodeids).get(file_name, []):
                cases.append(
                    {
                        "nodeid": nodeid,
                        "base_nodeid": nodeid,
                        "layer": taxonomy.get(taxonomy_key(nodeid), "unknown"),
                        "outcome": "collection_error",
                        "stdout": payload.get("stdout", ""),
                        "stderr": payload.get("stderr", ""),
                    }
                )
            continue
        for test in tests:
            nodeid = test.get("nodeid", "")
            base = re.sub(r"\[.*\]$", "", nodeid)
            seen_base_nodeids.add(base)
            seen_base_nodeids.add(nodeid)
            cases.append(
                {
                    "nodeid": nodeid,
                    "base_nodeid": base,
                    "layer": taxonomy.get(taxonomy_key(nodeid), "unknown"),
                    "outcome": test.get("outcome", "unknown"),
                    "call": test.get("call", {}),
                }
            )
    for nodeid in nodeids:
        if nodeid not in seen_base_nodeids and not any(c["base_nodeid"] == nodeid for c in cases):
            cases.append(
                {
                    "nodeid": nodeid,
                    "base_nodeid": nodeid,
                    "layer": taxonomy.get(taxonomy_key(nodeid), "unknown"),
                    "outcome": "not_collected",
                }
            )

    by_layer: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    summary: dict[str, int] = defaultdict(int)
    for case in cases:
        outcome = case["outcome"]
        summary_outcome = "passed" if outcome == "subtests passed" else outcome
        layer = case["layer"]
        summary[summary_outcome] += 1
        summary["total"] += 1
        by_layer[layer][summary_outcome] += 1
        by_layer[layer]["total"] += 1
    passed = summary.get("passed", 0)
    skipped = summary.get("skipped", 0)
    effective_total = max(1, summary["total"] - skipped)
    return {
        "summary": dict(sorted(summary.items())),
        "pass_rate_excluding_skips": passed / effective_total,
        "by_layer": {k: dict(sorted(v.items())) for k, v in sorted(by_layer.items())},
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-repo", required=True, type=Path)
    parser.add_argument("--solution-dir", required=True, type=Path)
    parser.add_argument("--nodeids", required=True, type=Path)
    parser.add_argument("--taxonomy", type=Path)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--remove-path", action="append", default=[])
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--pytest-arg", action="append", default=[])
    args = parser.parse_args()

    run_dir = args.run_dir.resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    worktree = run_dir / "oracle_worktree"
    copy_oracle_tree(args.source_repo.resolve(), worktree, args.remove_path)

    nodeids = read_nodeids(args.nodeids.resolve())
    taxonomy = load_taxonomy(args.taxonomy.resolve() if args.taxonomy else None)
    grouped_results = {}
    env_path = os.environ.get("PYTHONPATH", "")
    os.environ["PYTHONPATH"] = str(args.solution_dir.resolve()) + (os.pathsep + env_path if env_path else "")

    for index, (file_name, file_nodeids) in enumerate(group_by_file(nodeids).items(), start=1):
        report_path = run_dir / f"pytest_report_{index:03d}_{Path(file_name).stem}.json"
        try:
            _, payload = run_group(worktree, file_nodeids, report_path, args.timeout, args.pytest_arg)
        except subprocess.TimeoutExpired as exc:
            payload = {
                "returncode": 124,
                "stdout": exc.stdout or "",
                "stderr": exc.stderr or "timeout",
            }
        grouped_results[file_name] = payload

    report = {
        "source_repo": str(args.source_repo.resolve()),
        "solution_dir": str(args.solution_dir.resolve()),
        "nodeids": str(args.nodeids.resolve()),
        "taxonomy": str(args.taxonomy.resolve()) if args.taxonomy else None,
        "run_dir": str(run_dir),
        "grouped_results": grouped_results,
        **summarize(nodeids, grouped_results, taxonomy),
    }
    out = args.json_out or run_dir / "score.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("summary", "pass_rate_excluding_skips", "by_layer")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
