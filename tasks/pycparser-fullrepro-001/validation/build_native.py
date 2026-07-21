"""Convert the retained upstream identities to task-local native identities."""

from __future__ import annotations

import json
import re
from pathlib import Path


TASK_DIR = Path(__file__).resolve().parent.parent
EXTRACTION = Path("/tmp/pycparser-extraction-map.json")
SOURCE_MAP = Path("/tmp/pycparser-spec-map-source.md")


def base_nodeid(nodeid: str) -> str:
    return re.sub(r"\[[^\]]*\]$", "", nodeid)


def taxonomy_key(nodeid: str) -> str:
    parts = base_nodeid(nodeid).split("::")
    return ".".join([Path(parts[0]).stem, *parts[1:]])


payload = json.loads(EXTRACTION.read_text(encoding="utf-8"))
source_rows: dict[str, tuple[str, str, str]] = {}
for line in SOURCE_MAP.read_text(encoding="utf-8").splitlines():
    if not line.startswith("| `"):
        continue
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    source_rows[cells[0].strip("`")] = (cells[1], cells[2], cells[4])

cases = []
map_lines = [
    "| test_nodeid | source_type | layer | spec_section | status | notes |",
    "|---|---|---|---|---|---|",
]
for case in payload["cases"]:
    source = case["source_nodeid"]
    oracle = case["oracle_nodeid"]
    layer, section, notes = source_rows[source]
    if source.endswith("::test_generate_struct_union_enum_exception"):
        section = "Cross-View Invariants"
    cases.append(
        {
            "source_nodeid": source,
            "oracle_nodeid": oracle,
            "source_type": "upstream_rewritten",
            "layer": layer,
            "spec_section": section,
        }
    )
    map_lines.append(
        f"| `{oracle}` | upstream_rewritten | {layer} | {section} | covered | source: `{source}`; {notes} |"
    )

(TASK_DIR / "kept_nodeids.txt").write_text(
    "\n".join(case["oracle_nodeid"] for case in cases) + "\n", encoding="utf-8"
)

seen = set()
taxonomy_lines = []
for case in cases:
    key = taxonomy_key(case["oracle_nodeid"])
    if key in seen:
        continue
    seen.add(key)
    taxonomy_lines.append(json.dumps({"taxonomy_key": key, "layer": case["layer"]}, separators=(",", ":")))
(TASK_DIR / "taxonomy.jsonl").write_text("\n".join(taxonomy_lines) + "\n", encoding="utf-8")

map_lines.extend(
    [
        "",
        f"Total: {len(cases)} | kept: {len(cases)} | spec_gap: 0 | source-only: 0 | excluded: 45 | final_scoreable: {len(cases)}",
    ]
)
(TASK_DIR / "spec_test_map.md").write_text("\n".join(map_lines) + "\n", encoding="utf-8")

layers: dict[str, int] = {}
for case in cases:
    layers[case["layer"]] = layers.get(case["layer"], 0) + 1
(TASK_DIR / "source_nodeid_map.json").write_text(
    json.dumps(
        {
            "schema_version": 1,
            "mapping_contract": {
                "source_nodeid": "upstream provenance",
                "oracle_nodeid": "task-local native score identity",
                "canonical_score_identity": "oracle_nodeid",
                "source_type": "upstream_rewritten",
                "carrier_dependency": False,
                "subprocess_wrapper_dependency": False,
            },
            "validation": {"expected_cases": len(cases), "layers": layers},
            "cases": cases,
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

taxonomy = {case["oracle_nodeid"]: case["layer"] for case in cases}
task = {
    "instance_id": "pycparser-fullrepro-001",
    "status": "DRAFT",
    "repo": "eliben/pycparser",
    "repo_commit": "89c9f3d8642b9ec84cfdd6921faffaba7e95c43c",
    "spec_version": "v1",
    "oracle_version": "2026-07-20-native-v1",
    "oracle": {
        "test_files": sorted({case["oracle_nodeid"].split("::", 1)[0] for case in cases}),
        "requirements": "oracle/requirements.txt",
        "count": len(cases),
        "source": "upstream_rewritten",
        "nodeid_file": "kept_nodeids.txt",
        "mapping_file": "source_nodeid_map.json",
        "scorer_isolation": ["--remove-path", "pycparser"],
    },
    "taxonomy": taxonomy,
    "stats": layers,
    "reference_pass_rate": 1.0,
    "reference_score": {"passed": 90, "total": 90},
    "dummy_score": {"passed": 0, "total": 90},
    "candidate_score": {
        "runner": "swe-agent",
        "model": "gpt-5.5",
        "run_id": "swe-agent-gpt-5.5-pycparser-fullrepro-001-20260702T035227Z",
        "passed": 33,
        "total": 90,
        "pass_rate": 33 / 90,
        "summary": {"failed": 57, "passed": 33, "total": 90},
        "by_layer": {
            "atomic": {"failed": 29, "passed": 31, "total": 60},
            "integration": {"failed": 28, "passed": 2, "total": 30},
        },
        "import_provenance": "/root/autodl-tmp/Bmk-Lizhiqian/candidate-runs/e2e10-sweagent/swe-agent-gpt-5.5-pycparser-fullrepro-001-20260702T035227Z/output/pycparser/__init__.py",
        "python_sha256": {
            "pycparser/__init__.py": "3b1a265d7a6d3a4244da4d2fb7dde6ecc28048154c62c9f337cc0395029b0b49",
            "pycparser/ast_transforms.py": "b7d8be8213c9420fed04045a0d148a7730dc314fa5da6031ec0dfbdf65da8d88",
            "pycparser/c_ast.py": "0da16236814bafc0193b5e260ed5685072c6c171e3668b579d232c8eee788265",
            "pycparser/c_generator.py": "8959ad1568c6f8e6039bf076583bc07a3b51bd726ac03f666c9cb7ac0929aa78",
            "pycparser/c_lexer.py": "6a2c28eda3b8fb6f170dabd565f3884d1106d96ed30d91b17f06eb185468fa2a",
            "pycparser/c_parser.py": "16c63e479f5c0f456bb41878beb051eccba6552bf9e7d8219b80b15952e82008",
        },
        "unchanged_from_prior_scoring": {
            "summary_match": True,
            "layer_match": True,
            "outcome_mismatches": 0,
        },
    },
    "judge": {
        "date": "2026-07-20",
        "verdict": "PENDING_INDEPENDENT_REVIEW",
        "fairness_gates": {
            "A_spec_mapping": "passed",
            "B_failure_pattern": "passed_no_collection_errors",
            "C_generated_only": "not_applicable_upstream_rewritten",
            "D_coverage_gap": "FULL",
        },
    },
    "weaknesses": [
        {
            "dimension": "C grammar and AST integration",
            "description": "The candidate diverges on parser grammar, AST coordinates, declarations, and parse/generate round trips.",
            "affected_tests": 28,
        },
        {
            "dimension": "lexer and generator behavior",
            "description": "The candidate diverges on public tokenization, invalid-token handling, and C source generation behavior.",
            "affected_tests": 29,
        },
    ],
    "labels": [
        "upstream-rewritten-native-oracle",
        "discriminating",
        "parser-ast-cross-view-signal",
        "zero-candidate-collection-errors",
        "full-spec-section-coverage",
    ],
    "caveats": [
        "Current main uses same-process pytest execution and is not adversarial black-box proof against a malicious candidate."
    ],
    "validation_evidence": "validation/summary.json",
}
(TASK_DIR / "task.json").write_text(json.dumps(task, indent=2) + "\n", encoding="utf-8")
