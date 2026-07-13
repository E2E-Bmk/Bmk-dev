# Task Judge Diagnosis - cattrs-converters-fullrepro-001

## Preflight output

Command:

```powershell
$env:PYTHONPATH='G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-cattrs-specv1-20260704-001\output'; python -c "import cattrs; print(cattrs.__file__)"
```

Literal output:

```text
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-cattrs-specv1-20260704-001\output\cattrs\__init__.py
```

The import points into the candidate solution directory.

## Verdict

VERDICT=QUALIFIED

The task is valid and may be counted in the strict benchmark set. The scoring run is provenance-clean, the reference gate passes, the generated-only oracle is spec-driven and behavioral on manual audit, and the candidate failure is a real missing public API surface: `override` is explicitly required as an importable `cattrs` name.

## Hard Checks

### Anti-cheat scan

- Import provenance: passed; `cattrs.__file__` resolves to `candidate-runs/codex-cattrs-specv1-20260704-001/output/cattrs/__init__.py`.
- Formal score-run preflight also recorded `/mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-cattrs-specv1-20260704-001/output/cattrs/__init__.py`.
- Available candidate-run cleanroom metadata says the candidate-visible behavior sources were only `task_prompt.txt` and `public_packet/spec.md`, with source repositories, tests, filter artifacts, score reports, and previous attempts excluded.
- Static scan of available candidate-run artifacts found expected post-evaluation references inside score artifacts and oracle_worktree copies, but no implementation-phase trajectory artifact showing forbidden access. No full implementation transcript was present, so this audit is limited to the provided manifest, prompt, candidate output, and score-run provenance.

### Reference gate

- Reference result: 62/62 passed.
- Platform: Linux/WSL (`platform: linux`, Python 3.11.15).
- Isolation/path evidence: `reference_import` is `/mnt/g/research/01_agents/swe-e2e/repo-pool/python-attrs__cattrs/src/cattrs/__init__.py`; the command used `PYTHONPATH=$repo/src` in the repo-specific WSL venv.
- Reference pytest output: `62 passed in 9.31s`.

### Candidate score

- Candidate result: 0/62; all 62 are `collection_error`.
- Platform: `Linux-5.15.153.1-microsoft-standard-WSL2-x86_64-with-glibc2.31`.
- Isolation: `remove_paths` is `cattrs`.
- By layer: atomic 0/39, integration 0/18, system_e2e 0/5; every case is a collection error.
- Collection root cause: `ImportError: cannot import name 'override' from 'cattrs' (.../candidate-runs/codex-cattrs-specv1-20260704-001/output/cattrs/__init__.py)`.

## Gate C - Generated-only Oracle Spot-check

The map declares `filter/oracle_source: generated_only`, so generated tests were manually checked against spec-driven and behavioral criteria.

| nodeid | assertion summary | spec_section | verdict |
|--------|-------------------|--------------|---------|
| `filter/generated_tests.py::test_public_surface_exports_converter_core_names` | Public exports include `Converter`, `BaseConverter`, `GenConverter`, `UnstructureStrategy`, `structure`, `unstructure`, `override`, public validation errors, and `transform_error`. | "Installable Surface" | spec-driven and behavioral |
| `filter/generated_tests.py::test_primitive_structure_coerces_with_target_type` | `Converter.structure()` coerces primitive targets by calling `int`, `str`, and `float`. | "Structuring" | spec-driven and behavioral |
| `filter/generated_tests.py::test_explicit_structure_hook_overrides_default_for_type` | A registered structure hook for `int` takes priority over default structuring. | "Hook Registration and Lookup" | spec-driven and behavioral |
| `filter/generated_tests.py::test_override_rename_maps_field_for_both_directions` | `override(rename="class")` maps an attrs field to the external key for both structuring and unstructuring through generated dict hooks. | "Attribute Overrides and Defaults" | spec-driven and behavioral |
| `filter/generated_tests.py::test_detailed_validation_groups_class_field_errors_and_paths` | Detailed class validation groups nested list and mapping conversion failures and `transform_error()` reports public paths. | "Validation and Error Semantics" | spec-driven and behavioral |
| `filter/generated_tests.py::test_nested_custom_type_hook_applies_through_attrs_list_and_mapping` | A custom `int` hook applies recursively inside attrs fields, lists, and mappings. | "Cross-View Invariants" | spec-driven and behavioral |

Gate C result: passed. None of the sampled tests is circular or dependent on private implementation shape, exact exception message wording, private attributes, generated source text, or repr formatting.

## Gate D - Coverage Gap Audit

Covered scoreable sections from `spec_test_map.md`:

| spec section | covered rows |
|--------------|--------------|
| "Installable Surface" | 1 |
| "Public API" | 1 |
| "Product State Model" | 3 |
| "Structuring" | 15 |
| "Unstructuring" | 5 |
| "Hook Registration and Lookup" | 8 |
| "Attribute Overrides and Defaults" | 12 |
| "Validation and Error Semantics" | 11 |
| "Cross-View Invariants" | 6 |

Sections without direct scoreable rows:

| spec section | uncovered behaviors | impact | recommendation |
|--------------|---------------------|--------|----------------|
| "Product Overview" | Descriptive overview; behavior is covered through state, structuring, unstructuring, and cross-view sections. | none | no action |
| "Scope" | Boundary statement, not a standalone executable behavior. | none | no action |
| "Representative Workflows" | Illustrative examples; behaviors are covered by attribute override, structuring, unstructuring, hook priority, and cross-view tests. | none | no action |
| "Non-Goals" | Negative scope statement; tests correctly avoid private internals and optional backends. | none | no action |
| "Invocation Protocol" | States no covered CLI; there is no positive CLI behavior to score. | none | no action |
| "Evaluation Notes" | Testing guidance, not product behavior. | none | no action |

Coverage verdict: FULL for scoreable behavior. No core invariant section, error-semantics section, state lifecycle section, or public API section has zero coverage.

## Public `override` Failure Audit

`override` is explicitly required by the spec:

- "Installable Surface" lists `override` among names that must be importable from `cattrs`.
- "Installable Surface" also states that `cattrs.gen.override` must refer to the same public override factory as `cattrs.override`.
- "Public API" documents the accepted `override(...)` parameters.
- "Attribute Overrides and Defaults" defines observable `override(rename=...)`, `override(omit=True)`, `override(omit_if_default=True)`, `override(struct_hook=...)`, and `override(unstruct_hook=...)` behavior.

The generated tests use only public imports:

```python
from cattrs import (..., override, transform_error)
from cattrs.gen import make_dict_structure_fn, make_dict_unstructure_fn
```

The candidate implemented `cattrs.gen.override` but did not export `override` from top-level `cattrs.__init__`, and its `__all__` omits `override`. This is a valid public API-surface failure, not a broken filter/spec issue.

## Real Failure Clusters

| dimension | description | affected_tests |
|-----------|-------------|----------------|
| api-surface | Top-level `cattrs.override` is missing even though the spec requires it as importable public API and generated-hook metadata surface. | 62 collection errors |

Cascade analysis: all 62 collection errors cascade from one root cause: the missing public import `override`. Because collection stops before test bodies run, no further behavioral failures can be independently attributed. The cascade is still a valid model failure because the import itself is a public, spec-required surface.

## Labels

- generated-only-oracle
- api-surface
- cascade-dominated
- floor-score-via-public-import-failure
- candidate-non-saturated
