#!/usr/bin/env python3
"""Create a clean public-packet workspace for candidate agent runs.

The generated workspace is intentionally smaller than the benchmark repository:
it contains only the public task packet and an empty solution directory. Hidden
rubrics, score reports, reference solutions, prior candidates, and iteration
notes stay outside the model-visible path.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


BANNED_NAMES = {
    "rubric.json",
    "score_reports",
    "solution-reference",
    "reference",
    "score_summary.csv",
    "MANIFEST.json",
    "CANDIDATES.md",
}


def _copy_required(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _ignore_generated(dirpath: str, names: list[str]) -> set[str]:
    ignored = set()
    for name in names:
        if name == "__pycache__" or name.endswith(".pyc") or name.endswith(".pyo"):
            ignored.add(name)
    return ignored


def _copy_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    if dst.exists():
        raise FileExistsError(dst)
    shutil.copytree(src, dst, ignore=_ignore_generated)


def _assert_no_banned_paths(root: Path) -> None:
    leaked = []
    for path in root.rglob("*"):
        if path.name in BANNED_NAMES:
            leaked.append(path)
        if "score_report" in path.name.lower():
            leaked.append(path)
        if path.name.startswith("solution-") and path.name != "solution":
            leaked.append(path)
    if leaked:
        rel = [str(p.relative_to(root)) for p in leaked]
        raise RuntimeError(f"cleanroom contains banned paths: {rel}")


def create_cleanroom(
    task_dir: Path,
    output_root: Path,
    run_id: str,
    program_file: str,
    model_label: str,
    include_source_repo_note: bool = False,
) -> Path:
    task_dir = task_dir.resolve()
    output_root = output_root.resolve()
    workspace = output_root / run_id

    if workspace.exists():
        raise FileExistsError(
            f"{workspace} already exists; choose a new run id or remove it manually"
        )

    public_packet = workspace / "public_packet"
    solution_dir = workspace / "solution"
    solution_dir.mkdir(parents=True)

    _copy_required(task_dir / "prd.md", public_packet / "prd.md")

    task_public_packet = task_dir / "candidate_task" / "public_packet.md"
    if task_public_packet.exists():
        _copy_required(task_public_packet, public_packet / "public_packet.md")

    source_repo = task_dir / "doc" / "source_repo.md"
    if include_source_repo_note and source_repo.exists():
        _copy_required(source_repo, public_packet / "source_repo.md")

    starter = task_dir / "candidate_task" / "starter"
    _copy_tree(starter, workspace / "starter")

    prompt = f"""You are solving an isolated SWE-E2E benchmark task.

This is a fresh candidate run for {model_label}.

Read only the public packet in this workspace:
{public_packet}

If a starter skeleton exists, preserve its public module boundaries and
implement the solution by copying or extending it inside the solution directory:
{workspace / "starter"}

Implement the requested solution in this directory only:
{solution_dir}

Do not inspect parent directories, benchmark repositories, source repositories,
rubrics, score reports, reference solutions, or prior candidate solutions.
When finished, ensure the requested program file is present at:
{solution_dir / program_file}
"""
    (workspace / "task_prompt.txt").write_text(prompt, encoding="utf-8")

    manifest = {
        "run_id": run_id,
        "model_label": model_label,
        "task_dir_source": str(task_dir),
        "public_packet": str(public_packet),
        "starter": str(workspace / "starter") if (workspace / "starter").exists() else None,
        "solution_dir": str(solution_dir),
        "program_file": program_file,
        "included": sorted(
            str(p.relative_to(workspace))
            for root in (public_packet, workspace / "starter")
            if root.exists()
            for p in root.rglob("*")
            if p.is_file()
        )
        + ["task_prompt.txt"],
        "excluded_by_policy": "hidden benchmark assets, reference artifacts, prior runs, and scoring outputs",
        "strict_note": (
            "Run candidate agents with this workspace as the visible project root. "
            "Score from outside this directory after the artifact is produced."
        ),
    }
    (workspace / "cleanroom_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    _assert_no_banned_paths(workspace)
    return workspace


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--program-file", required=True)
    parser.add_argument("--model-label", required=True)
    parser.add_argument(
        "--include-source-repo-note",
        action="store_true",
        help="Copy doc/source_repo.md into the public packet. Disabled by default for cleanroom full-reproduction tasks.",
    )
    args = parser.parse_args()

    workspace = create_cleanroom(
        task_dir=args.task_dir,
        output_root=args.output_root,
        run_id=args.run_id,
        program_file=args.program_file,
        model_label=args.model_label,
        include_source_repo_note=args.include_source_repo_note,
    )
    print(workspace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
