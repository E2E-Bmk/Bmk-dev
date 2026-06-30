#!/usr/bin/env python3
"""Measure upstream repository scale for benchmark candidate scouting."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path


TEXT_EXTS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".scala",
    ".ex",
    ".exs",
    ".erl",
    ".hrl",
    ".c",
    ".h",
    ".cc",
    ".cpp",
    ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".sh",
    ".ps1",
    ".lua",
    ".sql",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".md",
    ".rst",
    ".txt",
}


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, check=False, capture_output=True, text=True)


def source_to_dirname(source_repo: str) -> str:
    return source_repo.replace("/", "__")


def find_local_repo(source_repo: str, roots: list[Path], cache_root: Path) -> Path | None:
    dirname = source_to_dirname(source_repo)
    candidates = [cache_root / dirname]
    candidates.extend(root / dirname for root in roots)
    candidates.append(cache_root / source_repo.split("/")[-1])
    for path in candidates:
        if path.exists():
            return path
    return None


def clone_repo(source_repo: str, cache_root: Path) -> Path | None:
    cache_root.mkdir(parents=True, exist_ok=True)
    dest = cache_root / source_to_dirname(source_repo)
    if dest.exists():
        return dest
    url = f"https://github.com/{source_repo}.git"
    proc = run(["git", "clone", "--depth", "1", url, str(dest)])
    if proc.returncode != 0:
        return None
    return dest


def list_files(repo: Path) -> list[Path]:
    proc = run(["git", "ls-files"], cwd=repo)
    if proc.returncode == 0 and proc.stdout.strip():
        return [repo / line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return [p for p in repo.rglob("*") if p.is_file() and ".git" not in p.parts]


def count_repo(repo: Path) -> dict:
    files = list_files(repo)
    suffix_counts: Counter[str] = Counter()
    loc_by_suffix: Counter[str] = Counter()
    text_files = 0
    total_loc = 0

    for path in files:
        suffix = path.suffix.lower() or "<none>"
        suffix_counts[suffix] += 1
        if suffix not in TEXT_EXTS:
            continue
        try:
            data = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        lines = data.splitlines()
        loc = sum(1 for line in lines if line.strip())
        text_files += 1
        total_loc += loc
        loc_by_suffix[suffix] += loc

    return {
        "repo_path": str(repo),
        "tracked_files": len(files),
        "text_files_counted": text_files,
        "nonblank_loc": total_loc,
        "top_extensions_by_files": suffix_counts.most_common(10),
        "top_extensions_by_loc": loc_by_suffix.most_common(10),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--cache-root", required=True, type=Path)
    parser.add_argument("--root", action="append", type=Path, default=[])
    parser.add_argument("--clone-missing", action="store_true")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    items = manifest.get("tasks", []) + manifest.get("candidates", [])
    seen: set[str] = set()
    rows = []

    for item in items:
        source_repo = item.get("source_repo")
        if not source_repo or source_repo in seen:
            continue
        seen.add(source_repo)
        repo = find_local_repo(source_repo, args.root, args.cache_root)
        cloned = False
        if repo is None and args.clone_missing:
            repo = clone_repo(source_repo, args.cache_root)
            cloned = repo is not None
        if repo is None:
            rows.append(
                {
                    "source_repo": source_repo,
                    "status": "missing",
                    "candidate_ids": [
                        x.get("id") for x in items if x.get("source_repo") == source_repo
                    ],
                }
            )
            continue
        stats = count_repo(repo)
        stats.update(
            {
                "source_repo": source_repo,
                "status": "counted",
                "cloned": cloned,
                "candidate_ids": [
                    x.get("id") for x in items if x.get("source_repo") == source_repo
                ],
            }
        )
        rows.append(stats)

    output = {"repos": rows}
    rendered = json.dumps(output, indent=2)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered, encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
