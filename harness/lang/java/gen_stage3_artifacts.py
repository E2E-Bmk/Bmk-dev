#!/usr/bin/env python3
"""Generate Stage-3 filter artifacts for one staged Java packet.

Reads `staging/{task_id}/oracle/` with the JavaRunner's own discovery, plus the
`Verifies:` javadoc lines, and writes:

- `filter/kept_nodeids.txt`
- `filter/taxonomy.jsonl`
- `filter/spec_test_map.md`
- `task.json` (merging counts/taxonomy into the packet-level metadata given on
  the command line via a small JSON stub already present in the packet root as
  `task_meta.json`)

Everything is derived from the physical oracle sources so the artifacts cannot
drift from the tests.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from harness.runners import get_runner  # noqa: E402

_VERIFIES = re.compile(r"(?m)Verifies:\s*([^—\r\n]+?)\s*(?:—|$)")
_TEST_METHOD = re.compile(r"@Test\s+void\s+(\w+)")


def _sections_by_method(source: Path) -> dict[str, str]:
    """Map each test method to the section named on its `Verifies:` line.

    Only the javadoc chunk between the previous test method and the current
    `@Test` is searched, so a parse failure surfaces as `(unmapped)` instead of
    silently inheriting the previous test's section.
    """
    text = source.read_text(encoding="utf-8-sig", errors="replace")
    out: dict[str, str] = {}
    previous_end = 0
    for match in _TEST_METHOD.finditer(text):
        chunk = text[previous_end: match.start()]
        verifies = None
        for v in _VERIFIES.finditer(chunk):
            verifies = v.group(1).strip().rstrip(".")
        out[match.group(1)] = verifies or "(unmapped)"
        previous_end = match.end()
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: gen_stage3_artifacts.py <task_id>", file=sys.stderr)
        return 2
    task_id = argv[1]
    packet = ROOT / "staging" / task_id
    oracle = packet / "oracle"
    filter_dir = packet / "filter"
    filter_dir.mkdir(exist_ok=True)

    runner = get_runner("java")
    atomic_ids = runner.discover(oracle, "atomic")
    integration_ids = runner.discover(oracle, "integration")
    all_ids = atomic_ids + integration_ids

    # Per-method spec sections, keyed by the full node id.
    sections: dict[str, str] = {}
    for suite in ("atomic", "integration"):
        for source in sorted((oracle / "src" / "test" / "java" / suite).rglob("*.java")):
            class_name = source.stem
            for method, section in _sections_by_method(source).items():
                sections[f"{suite}::{class_name}::{method}"] = section

    (filter_dir / "kept_nodeids.txt").write_text(
        "\n".join(all_ids) + "\n", encoding="utf-8"
    )

    with (filter_dir / "taxonomy.jsonl").open("w", encoding="utf-8") as fh:
        for test in all_ids:
            layer = "atomic" if test.startswith("atomic::") else "integration"
            fh.write(json.dumps({"test_id": test, "layer": layer}) + "\n")

    rows = ["# Spec Test Map", "", "| test_nodeid | layer | spec_section | status | notes |",
            "|---|---|---|---|---|"]
    for test in all_ids:
        layer = "atomic" if test.startswith("atomic::") else "integration"
        section = sections.get(test, "(unmapped)")
        leaf = test.rsplit("::", 1)[-1]
        rows.append(
            f"| {test} | {layer} | {section} | covered | "
            f"Covers public behavior for `{leaf}`. |"
        )
    (filter_dir / "spec_test_map.md").write_text("\n".join(rows) + "\n", encoding="utf-8")

    meta_path = packet / "task_meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    taxonomy = {test: ("atomic" if test.startswith("atomic::") else "integration")
                for test in all_ids}
    task = {
        "instance_id": task_id,
        "pipeline_note": "S3_DONE; Docker dummy gate and Docker reference run PENDING",
        **meta,
        "language": "java",
        "program_file": "pom.xml",
        "spec_version": "v1",
        "oracle_version": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "oracle": {
            "count": len(all_ids),
            "count_unit": "base_test_functions",
            "base_function_count": len(all_ids),
            "source": "generated_only",
            "generated_retained": len(all_ids),
            "upstream_rewritten_retained": 0,
            "maven_pom": "oracle/pom.xml",
            "reference_score": "PENDING (Docker unavailable; see filter/local_reference_run.txt)",
            "dummy_gate": "PENDING (Docker unavailable)",
        },
        "stats": {
            "atomic": len(atomic_ids),
            "integration": len(integration_ids),
            "system_e2e": 0,
        },
        "taxonomy": taxonomy,
        "taxonomy_unit": "base_test_functions",
    }
    (packet / "task.json").write_text(
        json.dumps(task, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    deps = runner.dependencies(oracle)
    print(f"atomic={len(atomic_ids)} integration={len(integration_ids)} "
          f"depends_on={len(deps)}/{len(integration_ids)}")
    unmapped = [test for test, section in sections.items() if section == "(unmapped)"]
    if unmapped:
        print("UNMAPPED sections:", *unmapped, sep="\n  ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
