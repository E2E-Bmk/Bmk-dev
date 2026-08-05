"""Parse ``@pytest.mark.depends_on`` markers off integration tests.

The marker records which atomic-layer tests an integration test logically
builds on. It is what separates a True Integration Gap Event (an integration
test fails while every atomic test it depends on passes -- a composition
failure) from cascade (the integration test fails because a primitive it needs
is broken). Without the annotation the two are indistinguishable and every
reported gap is suspect.

Extracted from the release repo's `harness/sandbox.py` so the construction side
can verify annotation coverage without carrying the scoring sandbox.
"""

from __future__ import annotations

import ast
from pathlib import Path


def _parse_depends_on(test_file: Path) -> dict[str, list[str]]:
    """
    Parse dependency markers from an integration test file via AST.

    Both ``@pytest.mark.depends_on(...)`` and a module-level alias such as
    ``depends_on = pytest.mark.depends_on`` are supported. Dependencies use
    bare atomic function names internally; the legacy ``test_atomic::`` prefix
    is accepted and normalized away.

    Returns {function_name: [dep_atomic_fn_1, dep_atomic_fn_2, ...]}.
    """
    try:
        tree = ast.parse(test_file.read_text(encoding="utf-8-sig", errors="replace"),
                         filename=str(test_file))
    except SyntaxError:
        return {}

    aliases = {"pytest.mark.depends_on"}
    for statement in tree.body:
        if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
            continue
        value = statement.value
        if _dotted_name(value) != "pytest.mark.depends_on":
            continue
        targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
        aliases.update(target.id for target in targets if isinstance(target, ast.Name))

    result = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("test"):
            continue
        dependencies: list[str] = []
        for dec in node.decorator_list:
            deps = _extract_depends_on_args(dec, aliases)
            for dep in deps:
                if dep not in dependencies:
                    dependencies.append(dep)
        if dependencies:
            result[node.name] = dependencies
    return result


def _dotted_name(node: ast.expr) -> str:
    """Return the dotted name represented by a Name/Attribute AST node."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return ""
    parts.append(node.id)
    return ".".join(reversed(parts))


def _extract_depends_on_args(
    decorator: ast.expr, aliases: set[str] | None = None
) -> list[str]:
    """
    Match a recognized dependency marker and return normalized function names.
    """
    if not isinstance(decorator, ast.Call):
        return []
    recognized = aliases or {"pytest.mark.depends_on"}
    if _dotted_name(decorator.func) not in recognized:
        return []

    deps = []
    for arg in decorator.args:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            dependency = arg.value
            if dependency.startswith("test_atomic::"):
                dependency = dependency.removeprefix("test_atomic::")
            deps.append(dependency)
    return deps
