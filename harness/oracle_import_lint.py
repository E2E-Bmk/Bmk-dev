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
    candidates = (
        ROOT / "wip" / task_id / "filter",
        ROOT / "tasks" / task_id / "oracle",
        ROOT / "oracle" / task_id,
    )
    for candidate in candidates:
        if (candidate / "test_atomic.py").is_file() or (
            candidate / "src" / "test" / "java" / "atomic"
        ).is_dir() or (candidate / "atomic").is_dir():
            return candidate
    for candidate in candidates:
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
        import_match = re.match(
            r"\s*import\s+(?:static\s+)?"
            r"([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*(?:\.\*)?)",
            line,
        )
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


def _java_call_chain(line: str, start: int) -> list[str]:
    """Return calls in a ``.member(...).next(...)`` chain.

    ``start`` points at the first dot. Arguments are skipped with balanced
    parentheses so helper calls passed as arguments are not mistaken for
    members of the target object.
    """
    calls: list[str] = []
    cursor = start
    while cursor < len(line):
        match = re.match(
            r"\s*\.\s*([A-Za-z_$][\w$]*)\s*\(", line[cursor:]
        )
        if not match:
            break
        calls.append(match.group(1))
        opening = cursor + match.end() - 1
        depth = 1
        index = opening + 1
        quote: str | None = None
        escaped = False
        while index < len(line) and depth:
            char = line[index]
            if quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
            elif char in {'"', "'"}:
                quote = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            index += 1
        if depth:
            break
        cursor = index
    return calls


def java_target_symbols(path: Path, target_roots: set[str]) -> list[tuple[str, int]]:
    """Collect imported Java target types and public members read from them.

    Wildcard imports require resolving the target type from source use. Member
    chains are followed after a target type or target-typed variable so a call
    such as ``API.builder().hiddenMember()`` cannot evade the lint merely
    because only ``builder`` is directly qualified by ``API``.
    """
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    target_types: set[str] = set()
    non_target_imports: set[str] = set()
    wildcard_target = False
    found: list[tuple[str, int]] = []
    for module, lineno in imports_from_regex(text):
        if any(module == root or module.startswith(root + ".") for root in target_roots):
            symbol = module.rsplit(".", 1)[-1]
            if symbol == "*":
                wildcard_target = True
            else:
                target_types.add(symbol)
                found.append((symbol, lineno))
        elif not module.endswith(".*"):
            non_target_imports.add(module.rsplit(".", 1)[-1])

    local_types = set(
        re.findall(r"\b(?:class|interface|enum|record)\s+([A-Z][A-Za-z0-9_$]*)", text)
    )
    java_lang_types = {
        "Boolean", "Byte", "Character", "Class", "Double", "Enum", "Float",
        "Integer", "Long", "Math", "Number", "Object", "Short", "String",
        "StringBuilder", "System", "Throwable", "Void",
    }
    if wildcard_target:
        inferred = set(re.findall(r"\b([A-Z][A-Za-z0-9_$]*)\s*\.", text))
        inferred.update(
            match.group(1).split(".", 1)[0]
            for match in re.finditer(
                r"\b([A-Z][A-Za-z0-9_$]*(?:\.[A-Z][A-Za-z0-9_$]*)?)"
                r"(?:\s*<[^;=(){}]+>)?(?:\[\])?\s+\w+\b",
                text,
            )
        )
        inferred.difference_update(non_target_imports | local_types | java_lang_types)
        target_types.update(inferred)
        for target_type in inferred:
            match = re.search(rf"\b{re.escape(target_type)}\b", text)
            if match:
                found.append((target_type, text.count("\n", 0, match.start()) + 1))

    if not target_types:
        return found

    type_alt = "|".join(re.escape(name) for name in sorted(target_types, key=len, reverse=True))
    declarations: dict[str, list[tuple[int, str]]] = {}
    declaration = re.compile(
        r"\b([A-Z][A-Za-z0-9_$.]*(?:\s*<[^;=(){}]+>)?(?:\[\])?)\s+(\w+)\b"
    )
    offset = 0
    lines = text.splitlines(keepends=True)
    for line in lines:
        for match in declaration.finditer(line):
            raw_type = re.sub(r"\s*<.*>", "", match.group(1)).removesuffix("[]")
            declarations.setdefault(match.group(2), []).append(
                (offset + match.start(), raw_type)
            )
        offset += len(line)

    offset = 0
    for lineno, line in enumerate(lines, 1):
        for match in re.finditer(r"\b([a-zA-Z_$][\w$]*)\s*(?=\.)", line):
            receiver = match.group(1)
            use_offset = offset + match.start()
            candidates = [item for item in declarations.get(receiver, []) if item[0] < use_offset]
            raw_type = candidates[-1][1] if candidates else ""
            type_parts = set(raw_type.split("."))
            if candidates and type_parts.intersection(target_types):
                found.extend((member, lineno) for member in _java_call_chain(line, match.end()))
        for match in re.finditer(rf"new\s+(?:{type_alt})\s*\([^;]*?\)\s*\.\s*([A-Za-z_$][\w$]*)\s*\(", line):
            found.append((match.group(1), lineno))
        for match in re.finditer(rf"\b(?:{type_alt})\s*::\s*([A-Za-z_$][\w$]*)", line):
            found.append((match.group(1), lineno))
        for match in re.finditer(rf"\b(?:{type_alt})\s*(?=\.)", line):
            found.extend((member, lineno) for member in _java_call_chain(line, match.end()))
        offset += len(line)
    return found


def java_accessor_declared(symbol: str, spec_text: str, public_section: str) -> bool:
    """Recognize JavaBean accessors covered by an explicit property contract."""
    match = re.fullmatch(r"(?:get|set|is)([A-Z][A-Za-z0-9_]*)", symbol)
    if not match or not re.search(
        r"\bgetters?(?:/setters?)?|\bsetters?\b", public_section, re.IGNORECASE
    ):
        return False
    stem = match.group(1)
    spec_words = {word.lower() for word in re.findall(r"[A-Za-z_]\w+", spec_text)}
    if stem.lower() in spec_words:
        return True
    components = re.findall(r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|\d+", stem)
    return bool(components) and all(component.lower() in spec_words for component in components)


JAVA_CHAIN_OBSERVERS = {
    # Calls on declared JDK/Jackson return carriers. These are observations of
    # already-declared values, not members of the target package. Deliberately
    # exclude Map-specific keySet()/values(): requiring a Map-shaped carrier is
    # a candidate-visible signature constraint and must remain lint-visible.
    "add", "allMatch", "asInt", "asText", "clear", "collect", "contains",
    "equals", "filter", "findFirst", "flatMap", "get", "iterator", "map",
    "next", "orElseThrow", "size", "stream", "toLowerCase", "toPlainString",
}


def java_builder_member_declared(symbol: str, spec_text: str) -> bool:
    """Match fluent/property names to explicitly documented property words."""
    match = re.fullmatch(r"(?:add|with|get|set|is)([A-Z][A-Za-z0-9_]*)", symbol)
    if not match:
        return False
    spec_words = {word.lower() for word in re.findall(r"[A-Za-z_]\w+", spec_text)}
    components = re.findall(
        r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|\d+", match.group(1)
    )

    def declared(component: str) -> bool:
        word = component.lower()
        variants = {word}
        if word.endswith("ies"):
            variants.add(word[:-3] + "y")
        elif word.endswith("s"):
            variants.add(word[:-1])
        else:
            variants.add(word + "s")
        return bool(variants.intersection(spec_words))

    return bool(components) and all(declared(component) for component in components)


def go_target_symbols(path: Path, target_roots: set[str]) -> list[tuple[str, int]]:
    """Collect exported names selected from aliases of target Go imports."""
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    aliases: set[str] = set()
    for match in re.finditer(
        r'(?m)^\s*(?:import\s+)?(?:(?P<alias>[A-Za-z_]\w*)\s+)?"(?P<module>[^"]+)"',
        text,
    ):
        module = match.group("module")
        if module not in target_roots:
            continue
        aliases.add(match.group("alias") or module.rsplit("/", 1)[-1])
    if not aliases:
        return []
    alias_alt = "|".join(map(re.escape, sorted(aliases)))
    found: list[tuple[str, int]] = []
    for match in re.finditer(rf"\b(?:{alias_alt})\.([A-Z][A-Za-z0-9_]*)", text):
        found.append((match.group(1), text.count("\n", 0, match.start()) + 1))
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
    selected_oracle = oracle_dir(task_id)
    atomic_path = selected_oracle / "test_atomic.py"
    java_atomic_dir = selected_oracle / "src" / "test" / "java" / "atomic"
    java_source_root = selected_oracle / "src" / "test" / "java"
    go_atomic_dir = selected_oracle / "atomic"
    go_integration_dir = selected_oracle / "integration"
    target_roots = set(TARGET_IMPORTS[task_id])
    violations: list[tuple[str, Path, int]] = []
    if atomic_path.exists():
        source_language = "python"
        atomic_sources = [atomic_path]
    elif java_atomic_dir.is_dir():
        source_language = "java"
        atomic_sources = sorted(java_source_root.rglob("*.java"))
    elif go_atomic_dir.is_dir() and go_integration_dir.is_dir():
        source_language = "go"
        atomic_sources = sorted(go_atomic_dir.glob("*_test.go")) + sorted(
            go_integration_dir.glob("*_test.go")
        )
    else:
        print("LINT_FAIL")
        print(
            f"[oracle] missing [{atomic_path}], [{java_atomic_dir}], "
            f"or Go suites [{go_atomic_dir}] [{go_integration_dir}]::0"
        )
        return 1
    if source_language == "python":
        for source_path in atomic_sources:
            for module, lineno in imports_from_ast(source_path):
                if not any(
                    module == target or module.startswith(target + ".")
                    for target in target_roots
                ):
                    continue
                if re.search(rf"(?<![\w.]){re.escape(module)}(?!\w)", section):
                    continue
                violations.append((module, source_path, lineno))
    elif source_language == "go":
        for source_path in atomic_sources:
            text = source_path.read_text(encoding="utf-8-sig", errors="replace")
            for target in target_roots:
                if f'"{target}"' not in text:
                    continue
                lineno = text.count("\n", 0, text.find(f'"{target}"')) + 1
                if not re.search(rf"(?<![\w./-]){re.escape(target)}(?![\w./-])", section):
                    violations.append((target, source_path, lineno))

    # Symbol level: the whole spec text is the reference, not just the surface
    # section, because behaviour clauses introduce names outside that section.
    spec_text = spec_path.read_text(encoding="utf-8-sig", errors="replace")
    spec_words = set(re.findall(r"[A-Za-z_]\w+", spec_text))
    if source_language == "python":
        for symbol, lineno in target_symbols(atomic_path, target_roots):
            if symbol in spec_words:
                continue
            violations.append((symbol, atomic_path, lineno))
    elif source_language == "java":
        for source_path in atomic_sources:
            for symbol, lineno in java_target_symbols(source_path, target_roots):
                if (
                    symbol in spec_words
                    or symbol in JAVA_CHAIN_OBSERVERS
                    or java_accessor_declared(symbol, spec_text, section)
                    or java_builder_member_declared(symbol, spec_text)
                ):
                    continue
                violations.append((symbol, source_path, lineno))
    else:
        for source_path in atomic_sources:
            for symbol, lineno in go_target_symbols(source_path, target_roots):
                if symbol in spec_words:
                    continue
                violations.append((symbol, source_path, lineno))

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
