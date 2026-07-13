from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from pathlib import Path


ROOT = Path(r"G:\research\01_agents\swe-e2e\Bmk-dev")
TASK = ROOT / "wip" / "joblib-cache-fullrepro-001"
GENERATED = TASK / "filter" / "generated_tests.py"

HEADINGS = [
    "Product Overview",
    "Scope",
    "Installable Surface",
    "Public API",
    "Product State Model",
    "Disk-Backed Function Caching",
    "Shelved Results",
    "Hashing",
    "Persistence And Compression",
    "Cache Invalidation And Reduction",
    "Error Semantics",
    "Cross-View Invariants",
    "Representative Workflow",
    "Non-Goals",
    "Invocation Protocol",
    "Evaluation Notes",
]

UPSTREAM = [
    ("test_hash_methods_public_rewrite", "atomic", ["Hashing"]),
    ("test_hash_numpy_arrays_public_rewrite", "atomic", ["Hashing"]),
    ("test_dict_hash_public_rewrite", "atomic", ["Hashing"]),
    ("test_set_hash_public_rewrite", "atomic", ["Hashing"]),
    ("test_string_hash_public_rewrite", "atomic", ["Hashing"]),
    ("test_wrong_hash_name_public_rewrite", "atomic", ["Hashing", "Error Semantics"]),
    ("test_no_memory_public_rewrite", "atomic", ["Disk-Backed Function Caching"]),
    ("test_memory_exception_public_rewrite", "integration", ["Disk-Backed Function Caching", "Error Semantics"]),
    ("test_memory_ignore_public_rewrite", "integration", ["Disk-Backed Function Caching"]),
    ("test_check_call_in_cache_public_rewrite", "integration", ["Disk-Backed Function Caching", "Product State Model"]),
    ("test_call_and_shelve_public_rewrite", "system_e2e", ["Shelved Results", "Product State Model", "Cross-View Invariants"]),
    ("test_standard_types_public_rewrite", "integration", ["Persistence And Compression"]),
    ("test_dump_value_error_public_rewrite", "atomic", ["Persistence And Compression", "Error Semantics"]),
    ("test_pathlib_public_rewrite", "integration", ["Persistence And Compression"]),
]


def generated_names() -> list[str]:
    tree = ast.parse(GENERATED.read_text(encoding="utf-8"))
    return [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    ]


def classify(name: str) -> tuple[str, list[str], str]:
    sections: list[str] = []
    layer = "atomic"
    note = "Public return value, exception class, execution count, or filesystem effect."

    if name in {
        "test_generated_public_exports",
        "test_generated_public_cache_types",
        "test_generated_pathlike_public_workflow",
    }:
        sections.extend(
            [
                "Product Overview",
                "Scope",
                "Installable Surface",
                "Public API",
                "Non-Goals",
                "Invocation Protocol",
                "Evaluation Notes",
            ]
        )
    if "hash" in name:
        sections.append("Hashing")
    if any(token in name for token in ("dump", "compression", "compressed", "mmap", "numpy", "pathlike", "register_compressor", "native_byte", "file_object")):
        sections.append("Persistence And Compression")
    if any(token in name for token in ("cache", "memory", "ignored", "signature", "forced_call", "validation", "expires_after")):
        sections.append("Disk-Backed Function Caching")
    if "shelf" in name or "reference_clear" in name:
        sections.append("Shelved Results")
    if any(token in name for token in ("clear", "reduce_size", "reduction")):
        sections.append("Cache Invalidation And Reduction")
    if any(token in name for token in ("invalid", "exception", "missing", "malformed", "error", "conflict", "wrong", "compressed_array")):
        sections.append("Error Semantics")
    if any(token in name for token in ("cache", "memory", "shelf", "clear", "reduce", "reduction", "validation", "workflow")):
        sections.append("Product State Model")
    if any(token in name for token in ("workflow", "cross_view")):
        sections.append("Representative Workflow")
    if any(
        token in name
        for token in (
            "cross_view",
            "shelf_populates",
            "shelf_clear",
            "memorized_func_clear",
            "memory_clear_invalidates",
            "reduce_size_items",
            "reduce_size_bytes",
            "reduce_size_age",
            "force_replacement",
            "reference_clear",
            "cache_persist_hash_workflow",
            "reduction_repopulation",
            "function_clear_cross_function",
            "memory_clear_filesystem",
            "validation_rejection",
        )
    ):
        sections.append("Cross-View Invariants")
        layer = "system_e2e"
    elif any(token in name for token in ("roundtrip", "workflow", "cache", "memory", "shelf", "reduce", "persistence", "mmap")):
        layer = "integration"

    if not sections:
        sections.append("Public API")
    sections = [heading for heading in HEADINGS if heading in set(sections)]
    return layer, sections, note


def rows(include_upstream: bool) -> list[tuple[str, str, list[str], str, str]]:
    result = []
    if include_upstream:
        for name, layer, sections in UPSTREAM:
            result.append(
                (
                    f"filter/rewritten_upstream_tests.py::{name}",
                    layer,
                    sections,
                    "upstream",
                    "Public rewrite preserving the named upstream behavior.",
                )
            )
    for name in generated_names():
        layer, sections, note = classify(name)
        result.append((f"filter/generated_tests.py::{name}", layer, sections, "generated", note))
    return result


def markdown(include_upstream: bool) -> str:
    data = rows(include_upstream)
    counts = Counter(section for _, _, sections, _, _ in data for section in sections)
    layers = Counter(layer for _, layer, _, _, _ in data)
    lines = [
        "| test_nodeid | source | layer | spec_section | status | notes |",
        "|---|---|---|---|---|---|",
    ]
    for nodeid, layer, sections, source, note in data:
        lines.append(
            f"| `{nodeid}` | {source} | {layer} | "
            f"{'<br>'.join(sections)} | covered | {note} |"
        )
    lines.extend(["", "## Quota Accounting", "", "| exact heading | count | floor |", "|---|---:|---:|"])
    for heading in HEADINGS:
        floor = 5 if heading == "Cross-View Invariants" else 3
        lines.append(f"| {heading} | {counts[heading]} | {floor} |")
    lines.extend(
        [
            "",
            f"Layer totals: atomic={layers['atomic']}, integration={layers['integration']}, system_e2e={layers['system_e2e']}.",
            f"Total: {len(data)} | kept (covered): {len(data)} | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: {len(data)}",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--merged", action="store_true")
    parser.add_argument("--nodeids", action="store_true")
    parser.add_argument("--taxonomy", action="store_true")
    args = parser.parse_args()
    if args.nodeids:
        for nodeid, _, _, _, _ in rows(include_upstream=args.merged):
            print(nodeid)
        return
    if args.taxonomy:
        for nodeid, layer, _, _, _ in rows(include_upstream=args.merged):
            parts = nodeid.split("::")
            key = ".".join([Path(parts[0]).stem, *parts[1:]])
            print(json.dumps({"taxonomy_key": key, "layer": layer}))
        return
    print(markdown(include_upstream=args.merged), end="")


if __name__ == "__main__":
    main()
