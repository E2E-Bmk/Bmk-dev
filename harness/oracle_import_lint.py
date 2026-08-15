#!/usr/bin/env python3
"""Lint oracle tests against the spec's public surface.

Two checks run over ``test_atomic.py``:

* module level -- every import of the target package must name a module that
  the public surface section mentions;
* symbol level -- every attribute read off the target package (``pkg.Name``)
  and every name imported from it must appear somewhere in the spec text.

The symbol check exists because module level linting alone let a task ship
assertions about an upstream exception tree the spec never declared
(``httpcore.PoolTimeout``, ``httpcore.TimeoutException`` and five siblings).
A delivery written from the spec cannot satisfy such an assertion, so it
scores reproduction of upstream internals rather than the specified
behaviour.

Only imports whose root is the task's target package are checked. A test that
imports ``pytest`` or ``requests`` is importing a declared dependency of the
oracle environment, not asserting an undeclared symbol of the package under
reconstruction, so reporting it produces noise that buries the real signal.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

try:
    from harness.target_imports import TARGET_IMPORTS
except ModuleNotFoundError:  # Direct execution: python harness/oracle_import_lint.py
    from target_imports import TARGET_IMPORTS


ROOT = Path(__file__).resolve().parent.parent


def public_surface(text: str) -> str:
    """The spec section that enumerates publicly reachable names.

    Four headings are accepted. ``Public Interface`` is the current name from
    the six-layer structure in ``SPEC_STANDARD.md``; ``Installable Surface``
    and ``Public Import Surface`` are earlier names still present in specs
    written before the restructure; ``Public API`` appears in a few. Matching
    only one of them makes the lint silently vacuous for every spec using
    another: with no section text, no import can match it, and every import is
    reported.
    """
    match = re.search(
        r"(?ims)^##\s+(?:Installable Surface|Public Import Surface|Public Interface|Public API)\s*$"
        r"([\s\S]*?)(?=^##\s+|\Z)",
        text,
    )
    return match.group(1) if match else ""


def allowed_from_spec(spec_path: Path) -> tuple[str, set[str]]:
    text = spec_path.read_text(encoding="utf-8-sig", errors="replace")
    section = public_surface(text)
    scripts: set[str] = set()

    in_console_block = False
    for line in section.splitlines():
        stripped = line.strip().strip("`")
        if re.search(r"console[-_ ]scripts", stripped, flags=re.IGNORECASE):
            in_console_block = True
            continue
        if in_console_block and stripped.startswith("##"):
            in_console_block = False
        if in_console_block:
            match = re.match(r"[-*]?\s*([A-Za-z0-9_.-]+)\s*(?:=|:)", stripped)
            if match:
                scripts.add(match.group(1))

    return section, scripts


def oracle_dir(task_id: str) -> Path:
    """Locate the oracle directory, supporting both repository layouts.

    Bmk-dev nests the oracle inside the task packet; a task still under
    construction keeps it in ``wip/{task}/filter``; the release repo keeps a
    flat ``oracle/{task}`` tree. Checking all three lets the same lint run on
    either side without a path flag.
    """
    for candidate in (
        ROOT / "wip" / task_id / "filter",
        ROOT / "tasks" / task_id / "oracle",
        ROOT / "oracle" / task_id,
    ):
        if candidate.is_dir():
            return candidate
    return ROOT / "tasks" / task_id / "oracle"


def imports_from_ast(path: Path) -> list[tuple[str, int]]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return imports_from_regex(text)

    imports: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                continue
            if node.module:
                imports.append((node.module, node.lineno))
    return imports


def imports_from_regex(text: str) -> list[tuple[str, int]]:
    imports: list[tuple[str, int]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        from_match = re.match(r"\s*from\s+([A-Za-z_][\w.]*)\s+import\b", line)
        if from_match:
            imports.append((from_match.group(1), lineno))
            continue
        import_match = re.match(r"\s*import\s+([A-Za-z_][\w.]*)", line)
        if import_match:
            imports.append((import_match.group(1), lineno))
    return imports


def target_symbols(path: Path, target_roots: set[str]) -> list[tuple[str, int]]:
    """Public names read off the target package: ``pkg.Name`` and ``from pkg import Name``.

    Three shapes are deliberately skipped, because flagging them produces noise
    rather than fairness signal:

    * single character attributes (``attr.s``, ``attr.ib``, ``quart.g``) -- a
      one letter name cannot be matched against spec prose reliably;
    * attribute chains whose head is itself an attribute already reported, so a
      violation is reported once at its root rather than per segment;
    * imports guarded by ``try``/``except ImportError``, which probe for an
      optional module instead of asserting it exists.
    """
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return []

    guarded: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            handles_import_error = any(
                isinstance(handler.type, ast.Name) and handler.type.id == "ImportError"
                or isinstance(handler.type, ast.Tuple)
                and any(
                    isinstance(elt, ast.Name) and elt.id == "ImportError"
                    for elt in handler.type.elts
                )
                for handler in node.handlers
            )
            if handles_import_error:
                for child in ast.walk(node):
                    if isinstance(child, (ast.Import, ast.ImportFrom)):
                        guarded.add(child.lineno)

    found: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        # pkg.Name / pkg.sub.Name
        if isinstance(node, ast.Attribute) and not node.attr.startswith("_"):
            if len(node.attr) < 2:
                continue
            base = node.value
            while isinstance(base, ast.Attribute):
                base = base.value
            if isinstance(base, ast.Name) and base.id in target_roots:
                found.append((node.attr, node.lineno))
        # from pkg import Name
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            if node.lineno in guarded:
                continue
            if node.module.split(".", 1)[0] in target_roots:
                for alias in node.names:
                    if len(alias.name) > 1 and not alias.name.startswith("_"):
                        found.append((alias.name, node.lineno))
    return found


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: python oracle_import_lint.py <task_id> <spec_md_path>", file=sys.stderr)
        return 2

    task_id = argv[1]
    spec_path = Path(argv[2])
    if not spec_path.is_absolute():
        spec_path = (Path.cwd() / spec_path).resolve()
    if not spec_path.exists():
        print("LINT_FAIL")
        print(f"[spec] found in {spec_path}::0")
        return 1

    # An unmapped task has no target roots, so every import is skipped and the
    # lint would print LINT_PASS without having checked anything. Fail instead.
    if task_id not in TARGET_IMPORTS:
        print("LINT_FAIL")
        print(f"[target-imports] missing [harness/target_imports.py]::0 task={task_id}")
        return 1

    section, _scripts = allowed_from_spec(spec_path)
    atomic_path = oracle_dir(task_id) / "test_atomic.py"
    target_roots = set(TARGET_IMPORTS[task_id])
    violations: list[tuple[str, Path, int]] = []
    if not atomic_path.exists():
        print("LINT_FAIL")
        print(f"[oracle] missing [{atomic_path}]::0")
        return 1
    for module, lineno in imports_from_ast(atomic_path):
        root = module.split(".", 1)[0]
        if root not in target_roots:
            continue
        if re.search(rf"(?<![\w.]){re.escape(module)}(?!\w)", section):
            continue
        violations.append((module, atomic_path, lineno))

    # Symbol level: the whole spec text is the reference, not just the surface
    # section, because behaviour clauses introduce names outside that section.
    spec_text = spec_path.read_text(encoding="utf-8-sig", errors="replace")
    spec_words = set(re.findall(r"[A-Za-z_]\w+", spec_text))
    for symbol, lineno in target_symbols(atomic_path, target_roots):
        if symbol in spec_words:
            continue
        violations.append((symbol, atomic_path, lineno))

    if violations:
        print("LINT_FAIL")
        for package, path, lineno in sorted(set(violations), key=lambda item: (item[0], str(item[1]), item[2])):
            try:
                display = path.relative_to(ROOT)
            except ValueError:
                display = path
            print(f"[{package}] found in [{display}]::{lineno}")
        return 1

    print("LINT_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
