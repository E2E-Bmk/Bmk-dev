#!/usr/bin/env python3
"""Static checks for one task packet.

Ported from the release repo's `harness/verify_task.py`. Two differences:

* the oracle is read from `tasks/{id}/oracle/` (Bmk-dev nests the oracle inside
  the task packet) rather than a top-level `oracle/{id}/`;
* `TARGET_IMPORTS` comes from its own module here, because the construction side
  does not carry the scoring sandbox.

Test enumeration, the `depends_on` relation and the layer counts all come from
the task's per-language runner, so a task in any registered language is measured
by the same gates rather than only Python and Java. The checks below the language
guard read Python source and have no equivalent elsewhere yet.

Every check derives from the physical oracle files, so no separate bookkeeping
file has to be kept in step with them.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

# Direct execution puts this file's own directory on the import path rather than
# the repository root, so the absolute `harness.` imports below would not
# resolve. Adding the root keeps the script form and the module form equivalent.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from harness.core import layout
from harness.core.oracle_import_lint import allowed_from_spec, imports_from_ast
from harness.core.target_imports import TARGET_IMPORTS
from harness.runners import get_runner

from analysis.annotate_assertions import annotate_file as _annotate_assertions


ROOT = layout.ROOT
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


def check_task(task_id: str) -> list[str]:
    task_dir = layout.task_dir(task_id)
    if task_dir is None:
        return [f"no packet under tasks/<language>/{task_id}"]
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
    # The bucket is what every per-language tool dispatches on, so a packet whose
    # `task.json` names a different language is measured by one toolchain and
    # filed under another.
    filed_under = layout.language_of(task_id)
    if filed_under is not None and language != filed_under:
        errors.append(
            f"task.json language {language!r} but the packet is filed under "
            f"tasks/{filed_under}/"
        )
    try:
        runner = get_runner(language)
    except (KeyError, ValueError) as exc:
        return errors + [f"no runner for language {language!r}: {exc}"]
    if data.get("instance_id") != task_id:
        errors.append("task.json instance_id does not match directory")
    strict_assertion_gate = isinstance(data.get("validation"), dict)

    # A suite the runner enumerates as empty is either absent or unreadable.
    # Either way its denominator is zero, which is the defect worth reporting;
    # naming the expected file here would re-introduce the Python assumption.
    atomic_ids = runner.discover(oracle_dir, "atomic")
    integration_ids = runner.discover(oracle_dir, "integration")
    for suite, found in (("atomic", atomic_ids), ("integration", integration_ids)):
        if not found:
            errors.append(
                f"{suite} suite enumerates no tests under tasks/{task_id}/oracle"
            )
    if errors and not (atomic_ids or integration_ids):
        return errors, warnings

    # Counted from what the runner enumerated, so the number is the scoring
    # denominator itself rather than a second parse that could disagree with it.
    atomic = len({runner.function_of(test) for test in atomic_ids})
    integration = len({runner.function_of(test) for test in integration_ids})
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

    # Taxonomy keys are `{suite}::{leaf}`. `function_of` keeps a class path
    # (`test_atomic::TestLRI.test_x`) because that is the form `score.tests`
    # uses, while task.json stores the leaf alone (`test_atomic::test_x`) --
    # several tasks group their atomic tests in classes. Comparing the two forms
    # directly reports every one of those tasks as broken, so the leaf is taken
    # from the key rather than assumed to be all of it.
    taxonomy = data.get("taxonomy", {})

    def _leaf_keys(ids: list[str]) -> set[str]:
        out = set()
        for test in ids:
            suite, _, rest = runner.function_of(test).partition("::")
            out.add(f"{suite}::{rest.rsplit('.', 1)[-1]}" if rest else suite)
        return out

    atomic_keys = _leaf_keys(atomic_ids)
    integration_keys = _leaf_keys(integration_ids)
    expected_keys = atomic_keys | integration_keys
    if set(taxonomy) != expected_keys:
        errors.append("taxonomy keys do not match the physical test functions")
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

    dependency_map = runner.dependencies(oracle_dir)
    dependency_coverage = len(dependency_map) / max(integration, 1)
    if dependency_coverage < DEPENDS_ON_COVERAGE_MIN:
        errors.append(
            "depends_on coverage below floor: "
            f"{len(dependency_map)}/{integration} = {dependency_coverage:.0%}"
        )
    referenced_atomic = {
        dependency
        for dependencies in dependency_map.values()
        for dependency in dependencies
    }
    # `depends_on` names a bare function while a taxonomy key carries the whole
    # nesting chain the runner emits. Compare leaves so a rename cannot slip
    # through as a match at some intermediate depth.
    atomic_leaves = {key.rsplit("::", 1)[-1] for key in atomic_keys}
    unknown_dependencies = referenced_atomic - atomic_leaves
    if unknown_dependencies:
        errors.append(
            "depends_on references unknown atomic tests: "
            + ", ".join(sorted(unknown_dependencies))
        )

    targets = set(TARGET_IMPORTS.get(task_id, []))
    if not targets:
        # Without a registered import root the scoring sandbox cannot audit
        # provenance, so it aborts before running the oracle and the task yields
        # no score at all -- not a zero, an absent measurement. The import check
        # below would also pass vacuously, since an empty target set skips every
        # import. Checked for every language, not just Python: provenance
        # auditing lives in the sandbox rather than in the runner.
        errors.append(
            f"no TARGET_IMPORTS entry for {task_id}: "
            "scoring will abort before running the oracle"
        )

    # Everything below reads Python source. A non-Python task has no equivalent
    # yet, and running these against its oracle would report a defect that is
    # only this checker's Python assumption.
    if language != "python":
        return errors, warnings

    if not (oracle_dir / "requirements.txt").exists():
        errors.append(f"missing files: tasks/{task_id}/oracle/requirements.txt")

    section, _ = allowed_from_spec(task_dir / "spec.md")
    for module, lineno in imports_from_ast(oracle_dir / "test_atomic.py"):
        if module.split(".", 1)[0] not in targets:
            continue
        if not re.search(rf"(?<![\w.]){re.escape(module)}(?!\w)", section):
            errors.append(f"atomic import not promised by the spec public surface: {module}:{lineno}")

    # Assertion-composition gate: the atomic layer must mostly verify produced
    # values, not merely correct rejection, or the Integration Gap numerator
    # inherits a systematic bias (failure_path tests are dummy-passable).
    annotations = _annotate_assertions(oracle_dir / "test_atomic.py")
    external_assert_helpers = {
        "assert_nonzero": "failure_path",
        "assert_raises": "failure_path",
    }
    source = (oracle_dir / "test_atomic.py").read_text(
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
    for test_file in (oracle_dir / "test_atomic.py", oracle_dir / "test_integration.py"):
        _check_duplicate_imports(test_file, warnings)

    # Gate 3g: fixture files referenced via Path(__file__).parent must exist
    for test_file in (oracle_dir / "test_atomic.py", oracle_dir / "test_integration.py"):
        _check_fixture_references(test_file, oracle_dir, errors)

    return errors, warnings


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
