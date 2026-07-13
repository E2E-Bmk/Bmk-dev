#!/usr/bin/env python3
"""Validate the benchmark task ledger against task, wip, and weakness files."""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ALLOWED_STATUSES = {"SELECTED", "RETIRED", "QUALIFIED", "REOPENED"}


def parse_markdown_table(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    header: list[str] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells:
            continue
        if all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells):
            continue
        if header is None:
            header = cells
            continue
        if len(cells) < len(header):
            cells.extend([""] * (len(header) - len(cells)))
        rows.append(dict(zip(header, cells)))
    return rows


def pipeline_state_is_qualified(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return bool(re.search(r"(?im)^\s*state\s*[:=]\s*QUALIFIED\s*$", text))


def emit(rule_id: str, task_id: str, detail: str, errors: list[str]) -> None:
    errors.append(f"ERROR [{rule_id}] [{task_id}] [{detail}]")


def main() -> int:
    candidates_path = ROOT / "CANDIDATES.md"
    tasks_dir = ROOT / "tasks"
    wip_dir = ROOT / "wip"
    weakness_path = ROOT / "weakness_table.md"

    errors: list[str] = []
    candidates = parse_markdown_table(candidates_path)
    weakness_rows = parse_markdown_table(weakness_path)

    by_repo: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in candidates:
        repo = row.get("repo", "").strip()
        status = row.get("status", "").strip()
        if repo:
            by_repo[repo].append(row)
        if status not in ALLOWED_STATUSES:
            emit("R6", repo or "<missing-repo>", f"invalid status={status!r}", errors)

    qualified_repos = {
        row.get("repo", "").strip()
        for row in candidates
        if row.get("status", "").strip() == "QUALIFIED" and row.get("repo", "").strip()
    }
    selected_repos = {
        row.get("repo", "").strip()
        for row in candidates
        if row.get("status", "").strip() == "SELECTED" and row.get("repo", "").strip()
    }
    retired_or_qualified = {
        row.get("repo", "").strip()
        for row in candidates
        if row.get("status", "").strip() in {"QUALIFIED", "RETIRED"} and row.get("repo", "").strip()
    }

    task_dirs = {p.name for p in tasks_dir.iterdir() if p.is_dir()} if tasks_dir.exists() else set()

    for repo in sorted(qualified_repos):
        if repo not in task_dirs:
            emit("R1", repo, "QUALIFIED repo has no same-name directory under tasks/", errors)

    for task_id in sorted(task_dirs):
        if task_id not in qualified_repos:
            emit("R2", task_id, "tasks/ directory has no QUALIFIED row in CANDIDATES.md", errors)

    if wip_dir.exists():
        for task_dir in sorted((p for p in wip_dir.iterdir() if p.is_dir()), key=lambda p: p.name):
            if pipeline_state_is_qualified(task_dir / "PIPELINE_STATE.md") and task_dir.name not in by_repo:
                emit("R3", task_dir.name, "wip PIPELINE_STATE.md is QUALIFIED but CANDIDATES.md has no row", errors)

    for row in weakness_rows:
        task_id = row.get("task", "").strip()
        if task_id and task_id not in retired_or_qualified:
            emit("R4", task_id, "weakness_table task has no QUALIFIED or RETIRED row in CANDIDATES.md", errors)

    for repo in sorted(qualified_repos):
        if repo not in selected_repos:
            emit("R5", repo, "QUALIFIED repo has no matching SELECTED row", errors)

    for repo, rows in sorted(by_repo.items()):
        statuses = sorted({row.get("status", "").strip() for row in rows})
        if len(statuses) > 1:
            emit("R7", repo, "duplicate repo appears with inconsistent statuses: " + ",".join(statuses), errors)

    if errors:
        for error in errors:
            print(error)
    else:
        print("OK")
    print(f"summary: {len(errors)} errors found")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
