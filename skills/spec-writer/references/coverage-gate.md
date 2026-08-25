# Spec-Test Coverage Gate

## Purpose

Before the first candidate run, verify that every kept test checks behavior that is actually described in the spec. This is the oracle validity mechanism.

## Procedure

For each test in the kept scoring suite, assign one status:

| Status | Meaning | Action |
|--------|---------|--------|
| `covered` | Behavior explicitly or inferrably described in spec | Keep in scoring set |
| `spec_gap` | Behavior is in official docs but missing from spec | Expand spec, re-evaluate |
| `undocumented` | Behavior only in source/tests, no public doc anywhere | Exclude from scoring set |
| `excluded` | Removed for other reasons (evaluator defect, format trap) | Exclude from scoring set |

## Artifact

Create `wip/{task}/spec_test_map.md`:

```markdown
| test_node_id | spec_section | status | notes |
|-------------|--------------|--------|-------|
| tests/test_X.py::test_foo | §Rendering | covered | |
| tests/test_X.py::test_bar | — | undocumented | _cookiecutter key not in any public doc |
```

Footer summary:
```
- Total kept tests: N
- covered: N
- spec_gap: N
- undocumented: N
- excluded: N
- Final scoreable (covered only): N
```

## Gate

**≥ 90% of kept tests must be `covered` before first candidate run.**

If < 90%:
- `spec_gap` rows → expand spec section, then re-label as `covered`
- `undocumented` rows → exclude from scoring set, recompute denominator

Do not run candidate evaluation until the gate passes.

## Example (cookiecutter)

`tests/test_main.py::test_original_cookiecutter_options_preserved_in__cookiecutter` → `undocumented`

The `_cookiecutter` context key is not described in any public Cookiecutter documentation. Excluding it from the scoring set is correct; do not add it to the spec.
