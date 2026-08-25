#!/usr/bin/env python3
"""AST audit for candidate-visible public operations and object protocols."""

from __future__ import annotations

import argparse
import ast
import fnmatch
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


GATE = Path(__file__).resolve().parent
CONTRACT = GATE / "PUBLIC-OPERATION-CONTRACT.json"
ORACLE_FILES = ("probe_root.py", "scenario_driver.py")
PUBLIC_MODULES = {
    "mkdocs.commands.build",
    "mkdocs.config",
    "mkdocs.exceptions",
    "mkdocs.structure.files",
    "mkdocs.structure.nav",
    "mkdocs.structure.pages",
}
CALL_RESULTS = {
    "mkdocs.config.load_config": "Config",
    "mkdocs.commands.build.build": "None",
    "mkdocs.structure.files.File": "File",
    "mkdocs.structure.files.Files": "Files",
    "mkdocs.structure.files.get_files": "Files",
    "mkdocs.structure.nav.Link": "Link",
    "mkdocs.structure.nav.Section": "Section",
    "mkdocs.structure.nav.get_navigation": "Navigation",
    "mkdocs.structure.pages.Page": "Page",
}
ATTRIBUTE_RESULTS = {
    ("File", "page"): "Page",
    ("Files", "src_uris"): "UriMapping",
    ("Navigation", "pages"): "PageList",
    ("Navigation", "items"): "NavList",
    ("Page", "file"): "File",
    ("Page", "meta"): "MetaMapping",
    ("Page", "toc"): "TOC",
    ("Page", "previous_page"): "Page",
    ("Page", "next_page"): "Page",
}
METHOD_RESULTS = {
    ("Files", "get_file_from_path"): "File",
}
ITEM_RESULTS = {
    "PageList": "Page",
    "NavList": "NavItem",
    "UriMapping": "File",
    "MetaMapping": "Scalar",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _api_symbol(node: ast.AST, aliases: dict[str, str]) -> str | None:
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "api":
        value = node.slice
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            short = value.value
            matches = sorted(name for name in aliases.values() if name.rsplit(".", 1)[-1] == short)
            return matches[0] if len(matches) == 1 else None
    if isinstance(node, ast.Name):
        return aliases.get(node.id)
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "mapping_item"
        and len(node.args) >= 2
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "api"
        and isinstance(node.args[1], ast.Constant)
        and isinstance(node.args[1].value, str)
    ):
        short = node.args[1].value
        matches = sorted(name for name in aliases.values() if name.rsplit(".", 1)[-1] == short)
        return matches[0] if len(matches) == 1 else None
    return None


class FunctionAudit(ast.NodeVisitor):
    def __init__(self, aliases: dict[str, str]) -> None:
        self.aliases = aliases
        self.env: dict[str, str] = {"api": "API"}
        self.operations: set[str] = set()

    def _record_iter(self, value: ast.AST) -> None:
        kind = self.infer(value)
        if kind not in {None, "Scalar", "None", "API"}:
            self.operations.add(f"protocol:{kind}.__iter__")

    def infer(self, node: ast.AST | None) -> str | None:
        if node is None:
            return None
        symbol = _api_symbol(node, self.aliases)
        if symbol is not None:
            return f"Public:{symbol}"
        if isinstance(node, ast.Name):
            return self.env.get(node.id)
        if isinstance(node, ast.Attribute):
            owner = self.infer(node.value)
            if owner and owner.startswith("Public:"):
                public = owner.removeprefix("Public:")
                self.operations.add(f"attr:{public}.{node.attr}")
                return "Scalar"
            if owner not in {None, "Scalar", "None", "API"}:
                self.operations.add(f"attr:{owner}.{node.attr}")
                return ATTRIBUTE_RESULTS.get((owner, node.attr), "Scalar")
            return None
        if isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Name) and node.value.id == "api":
                symbol = _api_symbol(node, self.aliases)
                return f"Public:{symbol}" if symbol else None
            owner = self.infer(node.value)
            self.infer(node.slice)
            if owner not in {None, "Scalar", "None", "API"}:
                self.operations.add(f"protocol:{owner}.__getitem__")
                return ITEM_RESULTS.get(owner, "Scalar")
            return None
        if isinstance(node, ast.Call):
            public = _api_symbol(node.func, self.aliases)
            for arg in node.args:
                self.infer(arg)
            for keyword in node.keywords:
                self.infer(keyword.value)
            if public is not None:
                self.operations.add(f"call:{public}")
                return CALL_RESULTS.get(public, "Scalar")
            if isinstance(node.func, ast.Name):
                name = node.func.id
                if name == "build_public":
                    return "Config"
                if name in {"list_value", "mapping_value"} and node.args:
                    return self.infer(node.args[0])
                if name == "mapping_item" and len(node.args) >= 2:
                    owner = self.infer(node.args[0])
                    if owner not in {None, "Scalar", "None", "API"}:
                        self.operations.add(f"protocol:{owner}.__getitem__")
                        return ITEM_RESULTS.get(owner, "Scalar")
                if name == "sequence_item" and node.args:
                    owner = self.infer(node.args[0])
                    if owner not in {None, "Scalar", "None", "API"}:
                        self.operations.add(f"protocol:{owner}.__getitem__")
                        return ITEM_RESULTS.get(owner, "Scalar")
                if name == "len" and node.args:
                    owner = self.infer(node.args[0])
                    if owner not in {None, "Scalar", "None", "API"}:
                        self.operations.add(f"protocol:{owner}.__len__")
                    return "Scalar"
                if name in {"list", "tuple", "set"} and node.args:
                    self._record_iter(node.args[0])
                    return "Scalar"
                if name == "bool" and node.args:
                    owner = self.infer(node.args[0])
                    if owner not in {None, "Scalar", "None", "API"}:
                        self.operations.add(f"protocol:{owner}.__bool__")
                    return "Scalar"
                if name == "isinstance" and len(node.args) >= 2:
                    checked = _api_symbol(node.args[1], self.aliases)
                    if checked is None:
                        inferred = self.infer(node.args[1])
                        checked = inferred.removeprefix("Public:") if inferred and inferred.startswith("Public:") else None
                    if checked:
                        self.operations.add(f"typecheck:isinstance:{checked}")
                    return "Scalar"
                if name == "issubclass" and len(node.args) >= 2:
                    left = _api_symbol(node.args[0], self.aliases)
                    right = _api_symbol(node.args[1], self.aliases)
                    if left is None:
                        inferred_left = self.infer(node.args[0])
                        left = inferred_left.removeprefix("Public:") if inferred_left and inferred_left.startswith("Public:") else None
                    if right is None:
                        inferred_right = self.infer(node.args[1])
                        right = inferred_right.removeprefix("Public:") if inferred_right and inferred_right.startswith("Public:") else None
                    if left and right:
                        self.operations.add(f"typecheck:issubclass:{left}:{right}")
                    return "Scalar"
            if isinstance(node.func, ast.Attribute):
                owner = self.infer(node.func.value)
                if owner not in {None, "Scalar", "None", "API"}:
                    self.operations.add(f"method:{owner}.{node.func.attr}")
                    return METHOD_RESULTS.get((owner, node.func.attr), "Scalar")
            return None
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            for item in node.elts:
                self.infer(item)
            return "Scalar"
        if isinstance(node, ast.Dict):
            for item in [*node.keys, *node.values]:
                self.infer(item)
            return "Scalar"
        if isinstance(node, ast.GeneratorExp):
            for generator in node.generators:
                self._record_iter(generator.iter)
            self.infer(node.elt)
            return "Scalar"
        if isinstance(node, ast.Compare):
            self.infer(node.left)
            for operation, comparator in zip(node.ops, node.comparators):
                owner = self.infer(comparator)
                if isinstance(operation, (ast.In, ast.NotIn)) and owner not in {None, "Scalar", "None", "API"}:
                    self.operations.add(f"protocol:{owner}.__contains__")
            return "Scalar"
        if isinstance(node, ast.BoolOp):
            for value in node.values:
                self.infer(value)
            return "Scalar"
        if isinstance(node, ast.UnaryOp):
            owner = self.infer(node.operand)
            if isinstance(node.op, ast.Not) and owner not in {None, "Scalar", "None", "API"}:
                self.operations.add(f"protocol:{owner}.__bool__")
            return "Scalar"
        return None

    def visit_Assign(self, node: ast.Assign) -> None:
        kind = self.infer(node.value)
        for target in node.targets:
            if isinstance(target, ast.Name) and kind:
                self.env[target.id] = kind
            elif isinstance(target, (ast.Tuple, ast.List)):
                for item in target.elts:
                    if isinstance(item, ast.Name) and kind:
                        self.env[item.id] = kind

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        kind = self.infer(node.value)
        if isinstance(node.target, ast.Name) and kind:
            self.env[node.target.id] = kind

    def visit_Expr(self, node: ast.Expr) -> None:
        self.infer(node.value)

    def visit_Return(self, node: ast.Return) -> None:
        self.infer(node.value)

    def visit_If(self, node: ast.If) -> None:
        owner = self.infer(node.test)
        if owner not in {None, "Scalar", "None", "API"}:
            self.operations.add(f"protocol:{owner}.__bool__")
        for item in [*node.body, *node.orelse]:
            self.visit(item)

    def visit_Try(self, node: ast.Try) -> None:
        for item in node.body:
            self.visit(item)
        for handler in node.handlers:
            public = _api_symbol(handler.type, self.aliases) if handler.type else None
            if public:
                self.operations.add(f"except:{public}")
            for item in handler.body:
                self.visit(item)
        for item in [*node.orelse, *node.finalbody]:
            self.visit(item)

    def visit_For(self, node: ast.For) -> None:
        self._record_iter(node.iter)
        for item in [*node.body, *node.orelse]:
            self.visit(item)

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            self.infer(item.context_expr)
        for item in node.body:
            self.visit(item)


def extract() -> tuple[list[str], list[str]]:
    imports: set[str] = set()
    aliases: dict[str, str] = {}
    trees: list[ast.Module] = []
    for relative in ORACLE_FILES:
        tree = ast.parse((GATE / relative).read_text(encoding="utf-8"), filename=relative)
        trees.append(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in PUBLIC_MODULES:
                for item in node.names:
                    public = f"{node.module}.{item.name}"
                    imports.add(public)
                    aliases[item.asname or item.name] = public
    operations: set[str] = set()
    for tree in trees:
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                analyzer = FunctionAudit(aliases)
                for statement in node.body:
                    analyzer.visit(statement)
                operations.update(analyzer.operations)
    return sorted(imports), sorted(operations)


def audit(*, discover: bool = False) -> dict[str, Any]:
    registered = json.loads(CONTRACT.read_text(encoding="utf-8"))
    imports, operations = extract()
    if discover:
        return {"public_imports": imports, "operations": operations}

    failures: list[str] = []
    expected_imports = sorted(registered["public_imports"])
    expected_operations = sorted(registered["operations"])
    if imports != expected_imports:
        failures.append(f"public import registry mismatch: expected={expected_imports} actual={imports}")
    if operations != expected_operations:
        failures.append(f"public operation registry mismatch: expected={expected_operations} actual={operations}")

    environment = json.loads((GATE / "ENVIRONMENT.json").read_text(encoding="utf-8"))
    if sorted(environment["entry_points"]) != imports:
        failures.append("ENVIRONMENT entry points do not exactly match AST public imports")

    packet_files = ["TASK.md", "SPEC.md", "ENVIRONMENT.json"]
    for relative in packet_files:
        if (GATE / relative).read_bytes() != (GATE / "candidate-payload" / relative).read_bytes():
            failures.append(f"candidate payload differs from root {relative}")
    packet_text = " ".join(
        "\n".join((GATE / relative).read_text(encoding="utf-8") for relative in packet_files).split()
    )
    markers = registered["markers"]
    for name, marker in markers.items():
        if " ".join(marker.split()) not in packet_text:
            failures.append(f"candidate packet is missing contract marker: {name}")

    uncovered: list[str] = []
    for operation in operations:
        matching = [rule for rule in registered["coverage_rules"] if fnmatch.fnmatchcase(operation, rule["operation"])]
        if not matching:
            uncovered.append(operation)
            continue
        for rule in matching:
            for marker in rule["markers"]:
                if marker not in markers:
                    failures.append(f"coverage rule references unknown marker {marker}: {operation}")
    if uncovered:
        failures.append(f"uncovered public operations: {uncovered}")

    for object_name, dimensions in registered["protocol_dimensions"].items():
        missing = [name for name, marker in dimensions.items() if marker not in markers]
        if missing:
            failures.append(f"{object_name} protocol dimensions lack markers: {missing}")

    return {
        "schema_version": 1,
        "suite": registered["suite"],
        "valid": not failures,
        "oracle_files": list(ORACLE_FILES),
        "oracle_sha256": {relative: _sha256(GATE / relative) for relative in ORACLE_FILES},
        "public_import_count": len(imports),
        "public_imports": imports,
        "operation_count": len(operations),
        "operations": operations,
        "coverage_rule_count": len(registered["coverage_rules"]),
        "protocol_objects": sorted(registered["protocol_dimensions"]),
        "root_payload_equal": not any("candidate payload differs" in item for item in failures),
        "resource_warning_contract": "resource_safety" in markers and "warnings_as_errors" in markers,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--discover", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    record = audit(discover=args.discover)
    rendered = json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        if args.output.exists():
            raise RuntimeError("output already exists")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    sys.stdout.write(rendered)
    return 0 if args.discover or record["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
