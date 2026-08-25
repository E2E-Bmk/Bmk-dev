#!/usr/bin/env python3
"""Static audit for public durable-record shapes and fail-safe oracle access."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


GATE = Path(__file__).resolve().parent
CONTRACT = GATE / "RECORD-SHAPE-CONTRACT.json"
PROBE = GATE / "probe_root.py"
EXPECTED_OWNERS = ["config", "discovery", "lineage", "publication", "search", "outbox"]
VALID_TYPES = {"array", "boolean", "integer", "null", "nonnegative_integer", "object", "positive_integer", "string"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function_name(parents: list[ast.AST]) -> str | None:
    for node in reversed(parents):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return node.name
    return None


def literal_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def validate_schema(schema: Any, definitions: dict[str, Any], label: str, failures: list[str]) -> None:
    if not isinstance(schema, dict):
        failures.append(f"{label} is not a schema object")
        return
    if "ref" in schema:
        reference = schema.get("ref")
        if not isinstance(reference, str) or reference not in definitions:
            failures.append(f"{label} has unknown ref {reference!r}")
        return
    raw_types = schema.get("type")
    types = raw_types if isinstance(raw_types, list) else [raw_types]
    if not types or any(item not in VALID_TYPES for item in types):
        failures.append(f"{label} has invalid type declaration {raw_types!r}")
        return
    required = schema.get("required", {})
    if "object" in types:
        if not isinstance(required, dict):
            failures.append(f"{label}.required is not an object")
        else:
            for key, child in required.items():
                if not isinstance(key, str) or not key:
                    failures.append(f"{label} has an invalid required key")
                validate_schema(child, definitions, f"{label}.{key}", failures)
        if "values" in schema:
            validate_schema(schema["values"], definitions, f"{label}.*", failures)
    if "array" in types and "items" in schema:
        validate_schema(schema["items"], definitions, f"{label}[]", failures)
    if schema.get("pattern") not in {None, "sha256", "sha256_or_null"}:
        failures.append(f"{label} has an unsupported pattern")
    if "enum" in schema and (not isinstance(schema["enum"], list) or not schema["enum"]):
        failures.append(f"{label} has an invalid enum")


def resolve(schema: dict[str, Any], definitions: dict[str, Any]) -> dict[str, Any]:
    seen: set[str] = set()
    while "ref" in schema:
        name = schema["ref"]
        if name in seen or name not in definitions:
            return {}
        seen.add(name)
        schema = definitions[name]
    return schema


def path_exists(path: str, body_schemas: dict[str, Any], definitions: dict[str, Any]) -> bool:
    owner, separator, remainder = path.partition(".")
    if not separator or owner not in body_schemas:
        return False
    schema = resolve(body_schemas[owner], definitions)
    tokens = re.findall(r"[^.]+", remainder)
    for token in tokens:
        schema = resolve(schema, definitions)
        if token == "*":
            schema = resolve(schema.get("values", {}), definitions)
            continue
        if token.endswith("[]"):
            key = token[:-2]
            required = schema.get("required", {})
            if key not in required:
                return False
            schema = resolve(required[key], definitions)
            if "array" not in ([schema.get("type")] if not isinstance(schema.get("type"), list) else schema.get("type")):
                return False
            schema = resolve(schema.get("items", {}), definitions)
            continue
        required = schema.get("required", {})
        if token not in required:
            return False
        schema = resolve(required[token], definitions)
    return bool(schema)


class ProbeAudit(ast.NodeVisitor):
    def __init__(self, safe_functions: set[str]) -> None:
        self.safe_functions = safe_functions
        self.parents: list[ast.AST] = []
        self.failures: list[str] = []
        self.record_paths: set[str] = set()
        self.owner_names: set[str] = set()
        self.owner_validation_calls = 0
        self.public_keyerror_translation = 0
        self.candidate_keyerror_routing = 0

    def generic_visit(self, node: ast.AST) -> None:
        self.parents.append(node)
        super().generic_visit(node)
        self.parents.pop()

    def visit_Subscript(self, node: ast.Subscript) -> None:
        current = function_name(self.parents)
        annotation_names = {"Any", "Callable", "Mapping", "Sequence", "dict", "list", "set", "tuple", "type"}
        is_annotation = isinstance(node.value, ast.Name) and node.value.id in annotation_names
        is_string_slice = isinstance(node.slice, ast.Slice)
        if not is_annotation and not is_string_slice and current not in self.safe_functions:
            self.failures.append(f"unguarded subscript at line {node.lineno} in {current or '<module>'}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id == "record_value" and len(node.args) >= 2:
            path = literal_string(node.args[1])
            if path is None:
                self.failures.append(f"non-literal record path at line {node.lineno}")
            else:
                self.record_paths.add(path)
        if isinstance(node.func, ast.Name) and node.func.id == "owner" and len(node.args) >= 2:
            owner_name = literal_string(node.args[1])
            if owner_name is not None:
                self.owner_names.add(owner_name)
        if isinstance(node.func, ast.Name) and node.func.id == "validate_owner_record":
            self.owner_validation_calls += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        current = function_name(self.parents)
        names: set[str] = set()
        if isinstance(node.type, ast.Name):
            names.add(node.type.id)
        elif isinstance(node.type, ast.Tuple):
            names.update(item.id for item in node.type.elts if isinstance(item, ast.Name))
        if current == "invoke" and "KeyError" in names:
            self.public_keyerror_translation += 1
        if current == "main" and "KeyError" in names:
            self.candidate_keyerror_routing += 1
        self.generic_visit(node)


def audit() -> dict[str, Any]:
    failures: list[str] = []
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("schema_version") != 1 or contract.get("suite") != "mkdocs-v14-formal-a":
        failures.append("record contract identity mismatch")
    owners = contract.get("owners")
    if owners != EXPECTED_OWNERS or len(set(owners or [])) != len(EXPECTED_OWNERS):
        failures.append("record owner registry mismatch")
    definitions = contract.get("definitions")
    body_schemas = contract.get("body_schemas")
    if not isinstance(definitions, dict) or not isinstance(body_schemas, dict):
        failures.append("record schema registries are missing")
        definitions = {}
        body_schemas = {}
    if list(body_schemas) != EXPECTED_OWNERS:
        failures.append("body schema owner order/set mismatch")
    validate_schema(contract.get("envelope"), definitions, "envelope", failures)
    for owner in EXPECTED_OWNERS:
        validate_schema(body_schemas.get(owner), definitions, owner, failures)

    direct_paths = contract.get("direct_oracle_paths")
    if not isinstance(direct_paths, list) or direct_paths != sorted(set(direct_paths)):
        failures.append("direct oracle path inventory must be sorted and unique")
        direct_paths = []
    for path in direct_paths:
        if not isinstance(path, str) or not path_exists(path, body_schemas, definitions):
            failures.append(f"direct oracle path is absent from public schema: {path!r}")

    spec = (GATE / "SPEC.md").read_text(encoding="utf-8")
    packet_spec = (GATE / "candidate-payload" / "SPEC.md").read_text(encoding="utf-8")
    if spec != packet_spec:
        failures.append("candidate SPEC differs from root SPEC")
    markers = contract.get("spec_markers", {})
    if not isinstance(markers, dict) or not markers:
        failures.append("record SPEC markers are missing")
    else:
        for name, marker in markers.items():
            if not isinstance(marker, str) or " ".join(marker.split()) not in " ".join(spec.split()):
                failures.append(f"candidate SPEC is missing record marker: {name}")

    tree = ast.parse(PROBE.read_text(encoding="utf-8"), filename=PROBE.name)
    safe_functions = set(contract.get("safe_subscript_functions", []))
    probe = ProbeAudit(safe_functions)
    probe.visit(tree)
    failures.extend(probe.failures)
    if probe.record_paths != set(direct_paths):
        failures.append(f"record path inventory mismatch: registered={sorted(direct_paths)} actual={sorted(probe.record_paths)}")
    if probe.owner_names != set(EXPECTED_OWNERS):
        failures.append(f"oracle owner coverage mismatch: {sorted(probe.owner_names)}")
    if probe.owner_validation_calls != 1:
        failures.append("owner() must call validate_owner_record exactly once")
    if probe.public_keyerror_translation != 1:
        failures.append("public-call KeyError translation is missing or ambiguous")
    if probe.candidate_keyerror_routing != 1:
        failures.append("candidate-versus-harness KeyError routing is missing or ambiguous")
    if any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "next" for node in ast.walk(tree)):
        failures.append("oracle may not use unchecked next() selection")

    return {
        "schema_version": 1,
        "suite": contract.get("suite"),
        "valid": not failures,
        "owners": EXPECTED_OWNERS,
        "owner_count": len(EXPECTED_OWNERS),
        "direct_path_count": len(direct_paths),
        "direct_paths": direct_paths,
        "nonempty_observations": contract.get("nonempty_observations", []),
        "safe_subscript_functions": sorted(safe_functions),
        "candidate_keyerror_routing": probe.candidate_keyerror_routing == 1,
        "probe_sha256": sha256(PROBE),
        "contract_sha256": sha256(CONTRACT),
        "spec_sha256": sha256(GATE / "SPEC.md"),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    record = audit()
    rendered = json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        if args.output.exists():
            raise RuntimeError("output already exists")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    sys.stdout.write(rendered)
    return 0 if record["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
