#!/usr/bin/env python3
"""Static audit for a Spec2Repo ROOT-MAP JSON file.

The script accepts either {"atomic": [...], "composition": [...]} or
{"roots": [...]} and optionally an observed score JSON with a `passed_ids`
array. It uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rows(document: dict[str, Any]) -> list[dict[str, Any]]:
    if "roots" in document:
        return list(document["roots"])
    return [*document.get("atomic", ()), *document.get("composition", ())]


def layer(row: dict[str, Any]) -> str:
    value = str(row.get("layer") or row.get("tier") or "")
    if value in {"atomic", "A"} or str(row.get("id", "")).startswith("A"):
        return "atomic"
    if value in {"system", "system_e2e", "e2e", "S", "E"}:
        return "system"
    return "integration"


def rate(passed: int, total: int) -> float | None:
    return passed / total if total else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root_map", type=Path)
    parser.add_argument("--score", type=Path, help="JSON containing passed_ids")
    parser.add_argument("--mutation-min", type=float, default=0.60)
    parser.add_argument("--mutation-max", type=float, default=0.75)
    parser.add_argument("--family-max-share", type=float, default=0.25)
    args = parser.parse_args()

    document = load(args.root_map)
    roots = rows(document)
    identifiers = [str(row.get("id", "")) for row in roots]
    id_set = set(identifiers)
    mutation = [row for row in roots if bool(row.get("mutation"))]
    native = [row for row in roots if not bool(row.get("mutation"))]
    families: dict[str, list[str]] = {}
    for row in mutation:
        families.setdefault(str(row.get("family", "<missing>")), []).append(str(row.get("id")))

    counts = {
        "total": len(roots),
        "atomic": sum(layer(row) == "atomic" for row in roots),
        "integration": sum(layer(row) == "integration" for row in roots),
        "system": sum(layer(row) == "system" for row in roots),
        "mutation": len(mutation),
        "native": len(native),
    }
    mutation_fraction = rate(len(mutation), len(roots)) or 0.0
    largest_family = max((len(values) for values in families.values()), default=0)
    largest_share = rate(largest_family, len(mutation)) or 0.0

    problems: list[str] = []
    if not roots:
        problems.append("root inventory is empty")
    if any(not identifier for identifier in identifiers):
        problems.append("one or more roots lack an id")
    if len(id_set) != len(identifiers):
        problems.append("duplicate root ids")
    if not args.mutation_min <= mutation_fraction <= args.mutation_max:
        problems.append(f"mutation fraction {mutation_fraction:.3f} outside [{args.mutation_min:.3f}, {args.mutation_max:.3f}]")
    if "<missing>" in families:
        problems.append("mutation roots missing family")
    if largest_share > args.family_max_share:
        problems.append(f"largest mutation family share {largest_share:.3f} exceeds {args.family_max_share:.3f}")

    unknown_dependencies = sorted({str(dep) for row in roots for dep in row.get("depends_on", ()) if str(dep) not in id_set})
    if unknown_dependencies:
        problems.append(f"unknown dependencies: {unknown_dependencies}")

    local_mutation_composition = [str(row.get("id")) for row in mutation if layer(row) != "atomic" and len(set(row.get("owners", ()))) < 2]
    if local_mutation_composition:
        problems.append(f"mutation Composition roots with fewer than two owners: {local_mutation_composition}")
    narrow_system = [str(row.get("id")) for row in roots if layer(row) == "system" and len(set(row.get("owners", ()))) < 4]
    if narrow_system:
        problems.append(f"System roots with fewer than four owners: {narrow_system}")
    native_composition = [str(row.get("id")) for row in native if layer(row) != "atomic"]
    if not native_composition:
        problems.append("no native Composition controls; clean Gap may be vote-allocation driven")

    result: dict[str, Any] = {
        "valid": not problems,
        "counts": counts,
        "mutation_fraction": round(mutation_fraction, 8),
        "families": families,
        "largest_family_share": round(largest_share, 8),
        "native_composition_controls": native_composition,
        "problems": problems,
    }

    if args.score:
        score = load(args.score)
        passed_ids = set(map(str, score.get("passed_ids", ())))
        atomic_ids = {str(row["id"]) for row in roots if layer(row) == "atomic"}
        composition_ids = id_set - atomic_ids
        eligible_composition = {
            str(row["id"])
            for row in roots
            if layer(row) != "atomic" and set(map(str, row.get("depends_on", ()))).issubset(passed_ids)
        }
        atomic_rate = rate(len(passed_ids & atomic_ids), len(atomic_ids))
        composition_rate = rate(len(passed_ids & composition_ids), len(composition_ids))
        conditional_rate = rate(len(passed_ids & eligible_composition), len(eligible_composition))
        result["observed"] = {
            "atomic_rate": atomic_rate,
            "composition_rate": composition_rate,
            "combined_rate": (atomic_rate + composition_rate) / 2 if atomic_rate is not None and composition_rate is not None else None,
            "raw_gap": atomic_rate - composition_rate if atomic_rate is not None and composition_rate is not None else None,
            "conditional_composition_rate": conditional_rate,
            "adjusted_gap": atomic_rate - conditional_rate if atomic_rate is not None and conditional_rate is not None else None,
        }

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not problems else 2


if __name__ == "__main__":
    raise SystemExit(main())
