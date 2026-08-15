#!/usr/bin/env python3
"""Synchronize task.json scoring metadata with the physical oracle tests.

`taxonomy`, `stats` and `oracle.count` describe the oracle. Whenever oracle
files change, hand-maintained copies of those numbers drift, and a drifted
`stats` fails `verify_task.py` while also making every reported layer rate
wrong. Deriving them from the files removes the class of error rather than
fixing instances of it.

Existing `system_e2e` labels are preserved: that split is a judgement made
during filtering and cannot be recovered from a test name. Only tests absent
from the previous taxonomy get a name-based guess, which the operator should
review.

Mirrors `harness/sync_task_metadata.py` in the release repo, minus the
release-inventory outputs (metadata.csv, README table), and reads the oracle
from `tasks/{id}/oracle/` rather than a top-level `oracle/{id}/`.

    python harness/sync_task_metadata.py --all           # rewrite
    python harness/sync_task_metadata.py --all --check    # report drift only
"""

from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SYSTEM_E2E_HINTS = ("cross_view", "representative", "workflow", "end_to_end")


def oracle_dir(task_id: str) -> Path:
    return ROOT / "tasks" / task_id / "oracle"


def task_ids() -> list[str]:
    return sorted(
        path.name
        for path in (ROOT / "tasks").iterdir()
        if path.is_dir()
        and (path / "task.json").exists()
        and (path / "oracle" / "test_atomic.py").exists()
        and (path / "oracle" / "test_integration.py").exists()
    )


def test_names(path: Path) -> list[str]:
    if not path.exists():
        return []
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    return [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    ]


def inferred_integration_layer(name: str) -> str:
    return "system_e2e" if any(hint in name for hint in SYSTEM_E2E_HINTS) else "integration"


def synchronized_metadata(task_id: str) -> dict:
    task_path = ROOT / "tasks" / task_id / "task.json"
    data = json.loads(task_path.read_text(encoding="utf-8-sig"))
    previous = data.get("taxonomy", {})
    data["instance_id"] = task_id
    data.setdefault("status", "STATICALLY_VALIDATED")
    data.setdefault("language", "python")

    atomic = test_names(oracle_dir(task_id) / "test_atomic.py")
    integration = test_names(oracle_dir(task_id) / "test_integration.py")
    taxonomy: dict[str, str] = {}
    for name in atomic:
        taxonomy[f"test_atomic::{name}"] = "atomic"
    for name in integration:
        key = f"test_integration::{name}"
        old_layer = previous.get(key)
        taxonomy[key] = (
            old_layer
            if old_layer in {"integration", "system_e2e"}
            else inferred_integration_layer(name)
        )

    counts = Counter(taxonomy.values())
    total = len(taxonomy)
    data["taxonomy"] = taxonomy
    data["taxonomy_unit"] = "base_test_functions"
    data["stats"] = {
        "atomic": counts["atomic"],
        "integration": counts["integration"],
        "system_e2e": counts["system_e2e"],
    }
    data.setdefault("oracle", {})["count"] = total
    data["oracle"]["count_unit"] = "base_test_functions"
    data["oracle"]["base_function_count"] = total
    # Test-level @pytest.mark.depends_on is the only dependency authority.
    data.pop("depends_on", None)
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_ids", nargs="*")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    selected = task_ids() if args.all else args.task_ids
    if not selected:
        parser.error("provide task IDs or --all")

    stale: list[str] = []
    for task_id in selected:
        path = ROOT / "tasks" / task_id / "task.json"
        raw = path.read_bytes()
        current = json.loads(raw.decode("utf-8-sig"))
        expected = synchronized_metadata(task_id)
        if current == expected:
            continue
        stale.append(task_id)
        if not args.check:
            # Preserve the file's existing BOM state: rewriting it is unrelated
            # to metadata drift and would enlarge every diff.
            prefix = b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b""
            body = json.dumps(expected, indent=2, ensure_ascii=False) + "\n"
            path.write_bytes(prefix + body.encode("utf-8"))

    if stale:
        action = "stale" if args.check else "updated"
        print(f"{action}: {', '.join(stale)}")
        print(f"summary: {len(stale)}/{len(selected)} tasks")
    else:
        print(f"summary: 0/{len(selected)} tasks stale")
    return int(args.check and bool(stale))


if __name__ == "__main__":
    raise SystemExit(main())
