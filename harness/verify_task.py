#!/usr/bin/env python3
"""Static checks for one task packet.

Ported from the release repo's `harness/verify_task.py`. Two differences:

* the oracle is read from `tasks/{id}/oracle/` (Bmk-dev nests the oracle inside
  the task packet) rather than a top-level `oracle/{id}/`;
* `TARGET_IMPORTS` and the `depends_on` parser come from their own modules here,
  because the construction side does not carry the scoring sandbox.

Every check derives from the physical oracle files, so no separate bookkeeping
file has to be kept in step with them.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

try:
    from harness.oracle_import_lint import allowed_from_spec, imports_from_ast
    from harness.target_imports import TARGET_IMPORTS
    from harness.depends_on import _parse_depends_on
    from harness.runners import get_runner
except ModuleNotFoundError:  # Direct execution from the repository root.
    from oracle_import_lint import allowed_from_spec, imports_from_ast
    from target_imports import TARGET_IMPORTS
    from depends_on import _parse_depends_on
    from runners import get_runner

try:
    from analysis.annotate_assertions import annotate_file as _annotate_assertions
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from analysis.annotate_assertions import annotate_file as _annotate_assertions


ROOT = Path(__file__).resolve().parent.parent
REQUIRED_HEADINGS = {
    "overview": ("product overview",),
    "scope": ("scope", "non-goals"),
    "surface": (
        "installable surface",
        "public import surface",
        "public interface",
        "public api",
    ),
    "state": ("product state model", "notebook json state model", "state model"),
    "errors": ("error semantics", "validation and error reporting"),
    "cross_view": ("cross-view invariants", "cross-component invariants"),
    "workflow": ("representative workflow", "representative workflows"),
    "non_goals": ("non-goals",),
    "invocation": ("invocation protocol", "public interface", "public api"),
    "environment": ("environment",),
    "evaluation": ("evaluation notes", "implementation guidance", "assessment notes"),
}

# Assertion-composition gate for the atomic layer. Atomic tests exist to
# prove primitives WORK; a layer dominated by failure_path checks (raises /
# non-zero exit / falsy asserts) can be passed by an implementation that
# rejects everything, which inflates atomic rates and fabricates gap.
ATOMIC_POSITIVE_MIN = 0.60
ATOMIC_TEST_MIN = 30
INTEGRATION_TEST_MIN = 25
TOTAL_TEST_MIN = 60
DEPENDS_ON_COVERAGE_MIN = 0.50
FORBIDDEN_BODY_TERMS = (
    "task_id",
    "source_boundary",
    "candidate-visible",
    "benchmark",
    "oracle",
    "judge",
    "scoring",
)


def test_count(path: Path) -> int:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    return sum(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
        for node in ast.walk(tree)
    )


def test_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }


def check_task(task_id: str) -> list[str]:
    task_dir = ROOT / "tasks" / task_id
    oracle_dir = task_dir / "oracle"
    errors: list[str] = []
    warnings: list[str] = []
    required = [task_dir / "spec.md", task_dir / "task.json"]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        return ["missing files: " + ", ".join(missing)]

    spec = (task_dir / "spec.md").read_text(encoding="utf-8", errors="replace")
    headings = [value.strip().lower() for value in re.findall(r"(?m)^##\s+(.+?)\s*$", spec)]
    for label, alternatives in REQUIRED_HEADINGS.items():
        if not any(any(alt in heading for alt in alternatives) for heading in headings):
            errors.append(f"missing semantic section: {label}")
    # Inline code spans document API identifiers; scan prose only for leakage.
    leakage_text = re.sub(r"`[^`]*`", " ", spec).lower()
    for term in FORBIDDEN_BODY_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", leakage_text):
            errors.append(f"candidate-visible leakage term: {term}")

    try:
        data = json.loads((task_dir / "task.json").read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return errors + [f"invalid task.json: {exc}"]
    language = str(data.get("language", "python")).lower()
    if language == "java":
        required = [
            oracle_dir / "pom.xml",
            oracle_dir / "src" / "test" / "java" / "atomic",
            oracle_dir / "src" / "test" / "java" / "integration",
        ]
    elif language == "typescript":
        required = [
            oracle_dir / "package.json",
            oracle_dir / "requirements.txt",
            oracle_dir / "atomic",
            oracle_dir / "integration",
        ]
    elif language in {"go", "rust"}:
        required = [oracle_dir / "atomic", oracle_dir / "integration"]
    else:
        required = [oracle_dir / "test_atomic.py", oracle_dir / "test_integration.py"]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        return errors + ["missing files: " + ", ".join(missing)]
    if data.get("instance_id") != task_id:
        errors.append("task.json instance_id does not match directory")
    strict_assertion_gate = isinstance(data.get("validation"), dict)

    runner_language = language in {"go", "rust", "typescript"}
    if language == "java" or runner_language:
        runner = get_runner(language)
        atomic_ids = runner.discover(oracle_dir, "atomic")
        integration_ids = runner.discover(oracle_dir, "integration")
        atomic = len(atomic_ids)
        integration = len(integration_ids)
        atomic_names = {test_id.rpartition("::")[2] for test_id in atomic_ids}
        integration_names = {test_id.rpartition("::")[2] for test_id in integration_ids}
        expected_keys = {*atomic_ids, *integration_ids}
    else:
        atomic = test_count(oracle_dir / "test_atomic.py")
        integration = test_count(oracle_dir / "test_integration.py")
        atomic_names = test_names(oracle_dir / "test_atomic.py")
        integration_names = test_names(oracle_dir / "test_integration.py")
        expected_keys = {
            *(f"test_atomic::{name}" for name in atomic_names),
            *(f"test_integration::{name}" for name in integration_names),
        }
    if atomic < ATOMIC_TEST_MIN or integration < INTEGRATION_TEST_MIN:
        errors.append(f"layer floor failed: atomic={atomic}, integration={integration}")
    stats = data.get("stats", {})
    score_atomic = int(stats.get("atomic", 0))
    score_integration = int(stats.get("integration", 0)) + int(stats.get("system_e2e", 0))
    oracle_count = int(data.get("oracle", {}).get("count", 0))
    if score_atomic < atomic or score_integration < integration:
        errors.append(
            "task.json layer counts are below test functions: "
            f"metadata={score_atomic}/{score_integration}, functions={atomic}/{integration}"
        )
    if score_atomic + score_integration != oracle_count:
        errors.append("task.json stats do not sum to oracle.count")
    if oracle_count < TOTAL_TEST_MIN:
        errors.append(f"scoreable case floor failed: {oracle_count}")

    taxonomy = data.get("taxonomy", {})
    if set(taxonomy) != expected_keys:
        errors.append("taxonomy keys do not match the physical test functions")
    atomic_keys = atomic_ids if language == "java" or runner_language else [f"test_atomic::{name}" for name in atomic_names]
    integration_keys = integration_ids if language == "java" or runner_language else [f"test_integration::{name}" for name in integration_names]
    if any(taxonomy.get(key) != "atomic" for key in atomic_keys):
        errors.append("an atomic-file test has a non-atomic taxonomy layer")
    allowed_integration = {"integration", "system_e2e"}
    if any(
        taxonomy.get(key) not in allowed_integration
        for key in integration_keys
    ):
        errors.append("an integration-file test has an invalid taxonomy layer")
    base_layers = {
        layer: sum(value == layer for value in taxonomy.values())
        for layer in ("atomic", "integration", "system_e2e")
    }
    score_layers = {
        "atomic": score_atomic,
        "integration": int(stats.get("integration", 0)),
        "system_e2e": int(stats.get("system_e2e", 0)),
    }
    if any(base_layers[layer] > score_layers[layer] for layer in base_layers):
        errors.append("taxonomy base-function counts exceed scoreable layer counts")

    if language == "java":
        dependency_map = get_runner(language).dependencies(oracle_dir)
        referenced_atomic = {
            dependency
            for dependencies in dependency_map.values()
            for dependency in dependencies
        }
        unknown_dependencies = referenced_atomic - atomic_names
    elif runner_language:
        dependency_map = _json_depends_on_map(oracle_dir / "depends_on.json")
        referenced_atomic = {
            dependency
            for dependencies in dependency_map.values()
            for dependency in dependencies
        }
        unknown_dependencies = referenced_atomic - set(atomic_ids)
    else:
        dependency_map = _depends_on_map(oracle_dir / "test_integration.py")
        referenced_atomic = {
            dependency
            for dependencies in dependency_map.values()
            for dependency in dependencies
        }
        unknown_dependencies = referenced_atomic - atomic_names
    dependency_coverage = len(dependency_map) / max(integration, 1)
    if dependency_coverage < DEPENDS_ON_COVERAGE_MIN:
        errors.append(
            "depends_on coverage below floor: "
            f"{len(dependency_map)}/{integration} = {dependency_coverage:.0%}"
        )
    if unknown_dependencies:
        errors.append(
            "depends_on references unknown atomic tests: "
            + ", ".join(sorted(unknown_dependencies))
        )

    if language == "python":
        section, _ = allowed_from_spec(task_dir / "spec.md")
        targets = set(TARGET_IMPORTS.get(task_id, []))
        for module, lineno in imports_from_ast(oracle_dir / "test_atomic.py"):
            if module.split(".", 1)[0] not in targets:
                continue
            if not re.search(rf"(?<![\w.]){re.escape(module)}(?!\w)", section):
                errors.append(f"atomic import not promised by the spec public surface: {module}:{lineno}")

    # Assertion-composition gate: the atomic layer must mostly verify produced
    # values, not merely correct rejection, or the Integration Gap numerator
    # inherits a systematic bias (failure_path tests are dummy-passable).
    annotations = {} if language != "python" else _annotate_assertions(oracle_dir / "test_atomic.py")
    external_assert_helpers = {
        "assert_nonzero": "failure_path",
        "assert_raises": "failure_path",
    }
    source = "" if language != "python" else (oracle_dir / "test_atomic.py").read_text(
        encoding="utf-8-sig", errors="replace"
    )
    for helper_name, kind in external_assert_helpers.items():
        for match in re.finditer(rf"(?m)^\s*{helper_name}\s*\(", source):
            line = source.count("\n", 0, match.start()) + 1
            owner = _test_at_line(oracle_dir / "test_atomic.py", line)
            key = f"test_atomic::{owner}" if owner else ""
            if key in annotations and annotations[key]["kind"] == "no_check":
                annotations[key]["kind"] = kind
    atomic_ann = {k: v for k, v in annotations.items() if k.startswith("test_atomic::")}
    if atomic_ann:
        positive = sum(1 for v in atomic_ann.values() if v["kind"] == "positive")
        share = positive / len(atomic_ann)
        if share < ATOMIC_POSITIVE_MIN:
            target = errors if strict_assertion_gate else warnings
            target.append(
                "atomic layer verifies too few produced values: "
                f"positive {positive}/{len(atomic_ann)} = {share:.0%} < {ATOMIC_POSITIVE_MIN:.0%}"
            )
        no_check = [k for k, v in atomic_ann.items() if v["kind"] == "no_check"]
        if no_check:
            target = errors if strict_assertion_gate else warnings
            target.append("atomic tests without any check: " + ", ".join(sorted(no_check)))

    # Gate 3f: duplicate top-level imports that shadow each other (warning-only)
    if language == "python":
        for test_file in (oracle_dir / "test_atomic.py", oracle_dir / "test_integration.py"):
            _check_duplicate_imports(test_file, warnings)

        # Gate 3g: fixture files referenced via Path(__file__).parent must exist
        for test_file in (oracle_dir / "test_atomic.py", oracle_dir / "test_integration.py"):
            _check_fixture_references(test_file, oracle_dir, errors)

    return errors, warnings


def _depends_on_map(path: Path) -> dict[str, list[str]]:
    return _parse_depends_on(path)


def _json_depends_on_map(path: Path) -> dict[str, list[str]]:
    """Read the language-neutral dependency map used by Go/Rust/TypeScript."""
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    mapping = data.get("depends_on", data) if isinstance(data, dict) else {}
    if not isinstance(mapping, dict):
        return {}
    return {
        str(test_id): [str(dep) for dep in dependencies]
        for test_id, dependencies in mapping.items()
        if isinstance(dependencies, list)
    }


def _test_at_line(path: Path, line: int) -> str | None:
    tree = ast.parse(
        path.read_text(encoding="utf-8-sig", errors="replace"), filename=str(path)
    )
    candidates = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
        and node.lineno <= line <= (node.end_lineno or node.lineno)
    ]
    return min(candidates, key=lambda node: node.end_lineno - node.lineno).name if candidates else None


def _check_duplicate_imports(path: Path, errors: list[str]) -> None:
    """Flag top-level 'from X import a, b' lines that import the same name twice."""
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    seen: dict[str, int] = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                name = alias.asname or alias.name
                if name in seen:
                    errors.append(
                        f"{path.name}: duplicate import '{name}' "
                        f"(lines {seen[name]} and {node.lineno})"
                    )
                else:
                    seen[name] = node.lineno


def _check_fixture_references(path: Path, oracle_dir: Path, errors: list[str]) -> None:
    """Detect Path(__file__).parent / 'subdir' / 'file' references to missing fixtures."""
    source = path.read_text(encoding="utf-8-sig")
    for match in re.finditer(
        r"""Path\(__file__\)\.parent\s*/\s*['"]([^'"]+)['"](?:\s*/\s*['"]([^'"]+)['"])?""",
        source,
    ):
        parts = [p for p in match.groups() if p is not None]
        fixture = oracle_dir.joinpath(*parts)
        if not fixture.exists():
            errors.append(
                f"{path.name}: fixture not found: {'/'.join(parts)}"
            )


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python harness/verify_task.py <task_id>", file=sys.stderr)
        return 2
    result = check_task(argv[1])
    errors, warnings = result if isinstance(result, tuple) else (result, [])
    if errors:
        print("STATIC_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    if warnings:
        print("STATIC_VALID (with warnings)")
        for w in warnings:
            print(f"  WARN: {w}")
    else:
        print("STATIC_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
