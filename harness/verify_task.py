#!/usr/bin/env python3
"""Verify the required files and bookkeeping for one qualified task."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT / "tasks"
REQUIRED_FILES = ["spec.md", "kept_nodeids.txt", "taxonomy.jsonl", "spec_test_map.md"]
ALLOWED_LAYERS = {"atomic", "integration", "system_e2e"}
CLEANROOM_FORBIDDEN = [
    "task_id",
    "delta:",
    "source_boundary:",
    "Candidate Agent Input Boundary",
    "benchmark",
    "oracle",
    "judge",
]


def read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]


def base_nodeid(nodeid: str) -> str:
    return re.sub(r"\[[^\]]*\]$", "", nodeid.strip())


def count_covered_rows(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if re.search(r"\bcovered\b", line, flags=re.IGNORECASE):
            count += 1
    return count


def final_scoreable(path: Path) -> int | None:
    if not path.exists():
        return None
    match = re.search(
        r"final_scoreable[^0-9]*(\d+)",
        path.read_text(encoding="utf-8", errors="replace"),
        flags=re.IGNORECASE,
    )
    return int(match.group(1)) if match else None


def check_taxonomy_layers(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, "taxonomy.jsonl missing"
    bad: list[str] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            bad.append(f"line {lineno} invalid JSON: {exc.msg}")
            continue
        layer = row.get("layer")
        if layer not in ALLOWED_LAYERS:
            bad.append(f"line {lineno} layer={layer!r}")
    if bad:
        return False, "; ".join(bad[:10])
    return True, "all taxonomy layers are allowed"


def check_cleanroom(spec_path: Path, task_id: str) -> tuple[bool, str]:
    if not spec_path.exists():
        return False, "spec.md missing"
    text = spec_path.read_text(encoding="utf-8", errors="replace")
    forbidden = [task_id, *CLEANROOM_FORBIDDEN]
    found: list[str] = []
    lower = text.lower()
    for token in forbidden:
        if token.lower() in lower:
            found.append(token)
    if found:
        return False, "forbidden strings found: " + ", ".join(dict.fromkeys(found))
    return True, "spec.md cleanroom strings absent"


def report(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    status = "PASS" if ok else "FAIL"
    print(f"{status} {name}: {detail}")
    if not ok:
        failures.append(f"{name}: {detail}")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python verify_task.py <task_id>", file=sys.stderr)
        return 2

    task_id = argv[1]
    task_dir = TASKS_DIR / task_id
    failures: list[str] = []

    report("task_dir_exists", task_dir.is_dir(), str(task_dir), failures)

    missing = [name for name in REQUIRED_FILES if not (task_dir / name).exists()]
    report(
        "required_files_exist",
        not missing,
        "all required files present" if not missing else "missing: " + ", ".join(missing),
        failures,
    )

    kept_lines = read_lines(task_dir / "kept_nodeids.txt")
    unique_base_count = len({base_nodeid(line) for line in kept_lines})
    taxonomy_lines = read_lines(task_dir / "taxonomy.jsonl")
    report(
        "kept_taxonomy_line_count",
        bool(kept_lines) and unique_base_count == len(taxonomy_lines),
        f"unique_base_kept={unique_base_count}, taxonomy_lines={len(taxonomy_lines)}",
        failures,
    )

    covered_rows = count_covered_rows(task_dir / "spec_test_map.md")
    report(
        "spec_test_map_covered_rows",
        covered_rows >= len(kept_lines) and bool(kept_lines),
        f"covered_rows={covered_rows}, kept_nodeids={len(kept_lines)}",
        failures,
    )

    final = final_scoreable(task_dir / "spec_test_map.md")
    report(
        "spec_test_map_final_scoreable",
        final == len(kept_lines),
        f"final_scoreable={final}, kept_nodeids={len(kept_lines)}",
        failures,
    )

    clean_ok, clean_detail = check_cleanroom(task_dir / "spec.md", task_id)
    report("spec_cleanroom", clean_ok, clean_detail, failures)

    taxonomy_ok, taxonomy_detail = check_taxonomy_layers(task_dir / "taxonomy.jsonl")
    report("taxonomy_layers", taxonomy_ok, taxonomy_detail, failures)

    bad_nodeids = [line for line in kept_lines if "::" not in line or line.startswith("::") or line.endswith("::")]
    report(
        "kept_nodeid_format",
        bool(kept_lines) and not bad_nodeids,
        "all nodeids contain ::" if not bad_nodeids else "bad nodeids: " + ", ".join(bad_nodeids[:10]),
        failures,
    )

    if failures:
        print("QUALIFIED_INVALID")
        print("FAIL items:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("QUALIFIED_VALID")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
