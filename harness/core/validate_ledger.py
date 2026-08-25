#!/usr/bin/env python3
"""Validate every task packet under tasks/, and cross-check the ledger loosely.

The previous version compared `CANDIDATES.md`'s `repo` column against directory
names under `tasks/`. Those are different namespaces -- the column holds
`rq/rq`, `getnikola__nikola` and bare task IDs interchangeably (29 / 37 / 21
occurrences at the time of writing), while a directory is always a task ID -- so
rules R1, R2 and R5 could not succeed by construction and reported 94 failures
that no data change would clear. Cross-referencing runs as warnings now, and
only where the ledger states a task ID explicitly.

The authoritative per-task checks live in `verify_task.check_task`, which
derives everything from the physical oracle files. That makes this script the
static gate `docs/QUALITY_GATE.md` and the task-judge Gate E describe.

    python harness/core/validate_ledger.py            # all tasks
    python harness/core/validate_ledger.py <task_id>  # one task
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

# Direct execution puts this file's own directory on the import path rather than
# the repository root, so the absolute `harness.` imports below would not
# resolve. Adding the root keeps the script form and the module form equivalent.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from harness.core import layout
from harness.core.verify_task import check_task


ROOT = layout.ROOT
ALLOWED_STATUSES = {"SELECTED", "RETIRED", "QUALIFIED", "REOPENED", "SUPERSEDED"}
TASK_ID_RE = re.compile(r"(?:task[=\s]+`?|`)([a-z0-9_]+(?:-[a-z0-9_]+)*-fullrepro-\d+)`?")


def parse_markdown_table(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    header: list[str] | None = None
    for line in path.read_text(encoding="utf-8-sig").splitlines():
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


def ledger_warnings() -> list[str]:
    """Ledger checks that hold regardless of the repo/task-id namespace mismatch."""
    warnings: list[str] = []
    rows = parse_markdown_table(ROOT / "CANDIDATES.md")

    by_repo: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        repo = row.get("repo", "").strip()
        status = row.get("status", "").strip()
        if status and status not in ALLOWED_STATUSES:
            warnings.append(f"CANDIDATES.md: unknown status {status!r} for {repo or '<no repo>'}")
        if repo:
            by_repo[repo].add(status)

    # A task ID named anywhere in a row must exist on disk. The reverse does not
    # hold: most rows identify their repository, not their task.
    task_dirs = set(layout.task_ids())
    for row in rows:
        blob = " ".join(row.values())
        status = row.get("status", "").strip()
        for task_id in TASK_ID_RE.findall(blob):
            if task_id in task_dirs:
                continue
            if status in {"RETIRED", "SUPERSEDED"}:
                continue  # the packet is meant to be gone; the row is history
            warnings.append(
                f"CANDIDATES.md: row for {row.get('repo', '?')} names task {task_id}, "
                "which has no directory under tasks/"
            )

    # A repo accumulates rows as it moves through the pipeline, so multiple
    # statuses are normal: SELECTED then RETIRED, or SELECTED then QUALIFIED
    # then REOPENED. Only a genuine contradiction is worth reporting -- a repo
    # recorded as both finished and abandoned.
    # A packet outside the language buckets is invisible to every per-language
    # tool and to the loop in main(), so a silent skip would read as a pass.
    for path in layout.strays():
        warnings.append(
            f"{path.relative_to(ROOT)}: outside the language buckets, so no "
            "per-language tool sees it"
        )

    for repo, statuses in sorted(by_repo.items()):
        if "QUALIFIED" in statuses and "RETIRED" in statuses:
            warnings.append(
                f"CANDIDATES.md: {repo} is recorded as both QUALIFIED and RETIRED "
                "(" + ",".join(sorted(statuses)) + ")"
            )
    return warnings


def main() -> int:
    argv = sys.argv[1:]
    selected = argv or layout.task_ids()

    failures = 0
    total_warnings = 0
    for task_id in selected:
        result = check_task(task_id)
        errors, warnings = result if isinstance(result, tuple) else (result, [])
        if errors:
            failures += 1
            print(f"FAIL {task_id}")
            for error in errors:
                print(f"  - {error}")
        elif warnings:
            total_warnings += len(warnings)
            print(f"PASS {task_id} ({len(warnings)} warnings)")
        else:
            print(f"PASS {task_id}")

    if not argv:
        for warning in ledger_warnings():
            total_warnings += 1
            print(f"WARN {warning}")

    print(
        f"summary: {len(selected) - failures}/{len(selected)} tasks statically valid, "
        f"{total_warnings} warnings"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
