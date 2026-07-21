#!/usr/bin/env python3
"""Scan agent traces for benchmark leakage indicators.

This is a conservative text scanner for OpenHands/agent logs. It does not prove
intent, but it separates direct hidden-artifact access from weaker evidence such
as observing a directory listing that exposes hidden paths.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DIRECT_ACCESS_PATTERNS = [
    r"rubric\.json",
    r"doc[/\\]score_reports",
    r"score_report[^/\\\s]*\.json",
    r"solution-reference",
    r"solution-codex",
    r"requirement_map\.md",
    r"MANIFEST\.json",
    r"CANDIDATES\.md",
]

OBSERVED_SURFACE_PATTERNS = [
    r"score_reports[/\\]?",
    r"rubric\.json",
    r"requirement_map\.md",
    r"solution-reference",
]

TEXT_SUFFIXES = {
    ".log",
    ".txt",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".py",
    ".toml",
    ".ini",
    ".cfg",
}


def classify_line(line: str) -> str | None:
    lower = line.lower()
    has_action_path = any(token in lower for token in ('"path"', "file_editor", "view", "cat ", "get-content"))
    direct = any(re.search(p, line, re.IGNORECASE) for p in DIRECT_ACCESS_PATTERNS)
    observed = any(re.search(p, line, re.IGNORECASE) for p in OBSERVED_SURFACE_PATTERNS)

    if direct and has_action_path:
        return "direct_or_tool_visible"
    if observed:
        return "observed_access_surface"
    return None


def scan_file(path: Path, max_examples: int) -> dict:
    counts = {"direct_or_tool_visible": 0, "observed_access_surface": 0}
    examples: list[dict] = []
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return {"path": str(path), "error": str(exc), "counts": counts, "examples": examples}

    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        text = raw.decode("utf-16", errors="replace")
    else:
        text = raw.decode("utf-8", errors="replace")

    for lineno, line in enumerate(text.splitlines(), start=1):
        kind = classify_line(line)
        if kind is None:
            continue
        counts[kind] += 1
        if len(examples) < max_examples:
            examples.append(
                {
                    "line": lineno,
                    "kind": kind,
                    "text": line[:500],
                }
            )

    severity = "clean"
    if counts["direct_or_tool_visible"]:
        severity = "non_strict_direct_surface"
    elif counts["observed_access_surface"]:
        severity = "non_strict_observed_surface"

    return {
        "path": str(path),
        "severity": severity,
        "counts": counts,
        "examples": examples,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--max-examples", type=int, default=5)
    args = parser.parse_args()

    files: list[Path] = []
    for raw in args.paths:
        if raw.is_dir():
            files.extend(
                sorted(
                    path
                    for path in raw.rglob("*")
                    if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES
                )
            )
        else:
            files.append(raw)

    results = [scan_file(path, args.max_examples) for path in files]
    summary = {
        "files_scanned": len(results),
        "non_strict_direct_surface": sum(
            1 for r in results if r.get("severity") == "non_strict_direct_surface"
        ),
        "non_strict_observed_surface": sum(
            1 for r in results if r.get("severity") == "non_strict_observed_surface"
        ),
        "clean": sum(1 for r in results if r.get("severity") == "clean"),
    }
    output = {"summary": summary, "results": results}

    rendered = json.dumps(output, indent=2)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered, encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
