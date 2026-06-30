#!/usr/bin/env python3
"""Generate a source-repo gate record before full-reproduction task design.

This script is intentionally a scaffold, not a judge. It records objective
evidence that must exist before a task builder writes a PRD or reference:
upstream scale, public documentation/test signals, and likely source modules.
Qualitative Layer-0 fields still need human or subagent audit.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path


TEXT_EXTS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".kt",
    ".scala", ".ex", ".exs", ".erl", ".hrl", ".c", ".h", ".cc", ".cpp",
    ".hpp", ".cs", ".rb", ".php", ".sh", ".ps1", ".lua", ".sql", ".toml",
    ".yaml", ".yml", ".json", ".md", ".rst", ".txt", ".xml", ".proto",
}

DOC_NAMES = {"readme", "docs", "doc", "examples", "example", "guides", "guide"}
TEST_MARKERS = {"test", "tests", "spec", "specs", "__tests__"}


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, check=False, capture_output=True, text=True)


def list_files(repo: Path) -> list[Path]:
    proc = run(["git", "ls-files"], cwd=repo)
    if proc.returncode == 0 and proc.stdout.strip():
        return [repo / line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return [p for p in repo.rglob("*") if p.is_file() and ".git" not in p.parts]


def rel_parts(path: Path, repo: Path) -> tuple[str, ...]:
    try:
        return path.relative_to(repo).parts
    except ValueError:
        return path.parts


def count_nonblank(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return 0
    return sum(1 for line in text.splitlines() if line.strip())


def summarize(repo: Path, candidate_id: str, source_repo: str | None) -> dict:
    files = list_files(repo)
    suffix_counts: Counter[str] = Counter()
    loc_by_suffix: Counter[str] = Counter()
    top_dirs: Counter[str] = Counter()
    doc_files: list[str] = []
    test_files: list[str] = []
    example_files: list[str] = []
    text_files = 0
    total_loc = 0

    for path in files:
        parts = rel_parts(path, repo)
        suffix = path.suffix.lower() or "<none>"
        suffix_counts[suffix] += 1
        if parts:
            top_dirs[parts[0]] += 1
        lowered = [p.lower() for p in parts]
        stem = path.stem.lower()
        if any(p in DOC_NAMES for p in lowered) or stem == "readme":
            doc_files.append(str(Path(*parts)))
        if any(p in TEST_MARKERS for p in lowered) or "test" in stem or "spec" in stem:
            test_files.append(str(Path(*parts)))
        if any("example" in p.lower() for p in parts):
            example_files.append(str(Path(*parts)))
        if suffix not in TEXT_EXTS:
            continue
        loc = count_nonblank(path)
        text_files += 1
        total_loc += loc
        loc_by_suffix[suffix] += loc

    commit = run(["git", "rev-parse", "HEAD"], cwd=repo)
    remote = run(["git", "remote", "get-url", "origin"], cwd=repo)
    scale_gate = {
        "tracked_files_ge_50": len(files) >= 50,
        "nonblank_loc_ge_2000": total_loc >= 2000,
        "doc_signal_present": bool(doc_files),
        "test_signal_present": bool(test_files),
        "multi_dir_signal": len(top_dirs) >= 3,
    }
    return {
        "candidate_id": candidate_id,
        "source_repo": source_repo,
        "repo_path": str(repo),
        "remote": remote.stdout.strip() if remote.returncode == 0 else None,
        "commit": commit.stdout.strip() if commit.returncode == 0 else None,
        "tracked_files": len(files),
        "text_files_counted": text_files,
        "nonblank_loc": total_loc,
        "top_extensions_by_files": suffix_counts.most_common(10),
        "top_extensions_by_loc": loc_by_suffix.most_common(10),
        "top_dirs_by_files": top_dirs.most_common(12),
        "doc_files_sample": doc_files[:20],
        "test_files_sample": test_files[:20],
        "example_files_sample": example_files[:20],
        "scale_gate": scale_gate,
        "gate_passed_objective_signals": all(scale_gate.values()),
    }


def render_markdown(data: dict) -> str:
    gates = "\n".join(
        f"- {key}: {'PASS' if value else 'FAIL'}"
        for key, value in data["scale_gate"].items()
    )
    return f"""# Source Candidate Gate: {data['candidate_id']}

## Source

- source_repo: {data.get('source_repo') or 'not recorded'}
- repo_path: `{data['repo_path']}`
- remote: {data.get('remote') or 'not recorded'}
- commit: `{data.get('commit') or 'not recorded'}`

## Objective Scale

- tracked_files: {data['tracked_files']}
- text_files_counted: {data['text_files_counted']}
- nonblank_loc: {data['nonblank_loc']}
- top_extensions_by_loc: {data['top_extensions_by_loc']}
- top_dirs_by_files: {data['top_dirs_by_files']}

## Evidence Signals

- docs/examples sample: {data['doc_files_sample'][:10]}
- tests sample: {data['test_files_sample'][:10]}
- examples sample: {data['example_files_sample'][:10]}

## Gate

{gates}

Objective signal verdict: {'PASS' if data['gate_passed_objective_signals'] else 'FAIL'}

## Qualitative Layer-0 Fields To Fill

- product_surface:
- shared_fact_source:
- public_projections:
- local_free_choices:
- global_public_invariants:
- contamination_risk:
- feature_pure_risks:
- unit_semantic_risks:
- collapse_risk:
- verdict:
- next_action:
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-path", required=True, type=Path)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--source-repo")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--md-out", type=Path)
    args = parser.parse_args()

    data = summarize(args.repo_path.resolve(), args.candidate_id, args.source_repo)
    rendered_json = json.dumps(data, indent=2)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered_json, encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(render_markdown(data), encoding="utf-8")
    print(rendered_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
