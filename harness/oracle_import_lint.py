#!/usr/bin/env python3
"""Lint oracle test imports against the public Installable Surface spec section."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
IGNORE_PACKAGES = {
    "pytest",
    "unittest",
    "os",
    "sys",
    "re",
    "io",
    "json",
    "pathlib",
    "tempfile",
    "contextlib",
    "typing",
    "collections",
    "itertools",
    "functools",
    "shutil",
    "subprocess",
    "textwrap",
    "hashlib",
    "time",
    "datetime",
    "warnings",
    "copy",
    "abc",
    "dataclasses",
    "enum",
}
if hasattr(sys, "stdlib_module_names"):
    IGNORE_PACKAGES.update(sys.stdlib_module_names)


def top_package(name: str) -> str:
    return name.split(".", 1)[0].replace("-", "_")


def installable_surface(text: str) -> str:
    match = re.search(r"(?ims)^##\s+Installable Surface\s*$([\s\S]*?)(?=^##\s+|\Z)", text)
    return match.group(1) if match else ""


def allowed_from_spec(spec_path: Path) -> tuple[set[str], set[str]]:
    text = spec_path.read_text(encoding="utf-8", errors="replace")
    section = installable_surface(text)
    allowed: set[str] = set()
    scripts: set[str] = set()

    for match in re.finditer(r"\bfrom\s+([A-Za-z_][\w.]*)\s+import\b", section):
        allowed.add(top_package(match.group(1)))
    for match in re.finditer(r"(?<!from\s)\bimport\s+([A-Za-z_][\w.]*)", section):
        allowed.add(top_package(match.group(1)))

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
                allowed.add(top_package(match.group(1)))

    return allowed, scripts


def test_root(task_id: str) -> Path:
    wip_filter = ROOT / "wip" / task_id / "filter"
    if wip_filter.exists():
        return wip_filter
    return ROOT / "tasks" / task_id


def iter_python_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.py") if path.is_file())


def imports_from_ast(path: Path) -> list[tuple[str, int]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return imports_from_regex(text)

    imports: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((top_package(alias.name), node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                continue
            if node.module:
                imports.append((top_package(node.module), node.lineno))
    return imports


def imports_from_regex(text: str) -> list[tuple[str, int]]:
    imports: list[tuple[str, int]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        from_match = re.match(r"\s*from\s+([A-Za-z_][\w.]*)\s+import\b", line)
        if from_match:
            imports.append((top_package(from_match.group(1)), lineno))
            continue
        import_match = re.match(r"\s*import\s+([A-Za-z_][\w.]*)", line)
        if import_match:
            imports.append((top_package(import_match.group(1)), lineno))
    return imports


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

    allowed, _scripts = allowed_from_spec(spec_path)
    root = test_root(task_id)
    violations: list[tuple[str, Path, int]] = []
    for path in iter_python_files(root):
        for package, lineno in imports_from_ast(path):
            if package in allowed or package in IGNORE_PACKAGES or package.startswith("_"):
                continue
            violations.append((package, path, lineno))

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
