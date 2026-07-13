# Task Judge Diagnosis - attrs-classes-fullrepro-001

## Preflight output

Command:

```powershell
$env:PYTHONPATH='G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-attrs-specv1-20260704-001\output'; python -c "import attrs, attr; print(attrs.__file__); print(attr.__file__)"
```

Literal output:

```text
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-attrs-specv1-20260704-001\output\attrs\__init__.py
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-attrs-specv1-20260704-001\output\attr\__init__.py
```

Both imports point into the candidate output directory.

## Verdict

VERDICT=QUALIFIED

The task is valid and may be counted in the strict legal benchmark set. The scoring run is provenance-clean, the reference gate passes, the candidate score is non-saturated and discriminating, and the candidate failures are real public-behavior weaknesses rather than oracle/spec gaps.

## Hard Checks

### Anti-cheat scan

- Import provenance: passed; `attrs` and `attr` both resolve to `candidate-runs/codex-attrs-specv1-20260704-001/output`.
- Static scan of the candidate output and packet files for forbidden paths/artifacts found no suspicious candidate-side access. The only match was the packet README warning not to expose tests, maps, nodeids, reference score, or oracle repo.
- No full implementation trajectory artifact was present in the candidate-run directory, so this audit is limited to provided artifacts and candidate output contents.

### Reference gate

- Reference result: 81/81 passed.
- Platform: Linux-5.15.153.1-microsoft-standard-WSL2-x86_64-with-glibc2.31.
- Isolation: remove-path isolation included `src/attrs`, `src/attr`, `attrs`, and `attr`.
- Collection/errors: none.

### Candidate score

- Candidate result: 71/81 passed, 10 failed.
- Platform: Linux-5.15.153.1-microsoft-standard-WSL2-x86_64-with-glibc2.31.
- Collection/errors: 81 collected; no collection error and no run-level error.
- By layer: atomic 46/53, integration 10/12, system_e2e 15/16.

## Gate A - Spec Mapping Spot-check

| nodeid | assertion summary | spec_section | verdict |
|--------|-------------------|--------------|---------|
| test_attrs_public_behavior_generated.py::test_fields_support_tuple_index_and_attribute_lookup | `attrs.fields()` supports integer indexing and field-name attribute lookup. | "Public API" | derivable |
| test_attrs_public_behavior_generated.py::test_private_attribute_default_alias_strips_leading_underscore | A single-leading-underscore stored field uses a stripped initializer argument and keeps the stored field name in `asdict()`. | "Initialization and Defaults" | derivable |
| test_attrs_public_behavior_generated.py::test_validator_list_and_decorator_validator_both_run | A declared validator and decorator validator are combined and both reject invalid values. | "Validators" | derivable |
| test_attrs_public_behavior_generated.py::test_decorator_converter_can_use_instance_and_attribute | A converter registered through `@field.converter` behaves like field-declaration converters and can observe instance/attribute context. | "Converters" | derivable |
| test_attrs_public_behavior_generated.py::test_make_class_honors_bases_argument | `attrs.make_class(..., bases=...)` creates an attrs class inheriting from supplied bases. | "Dynamic Class Creation" | derivable |

Gate A result: passed.

## Gate B - Failure Pattern Audit

All 10 failures are traceable to public, spec-documented behavior and are observable through public API calls. They do not require private imports, exact exception message wording, private storage names, or exact `Attribute.__repr__` formatting.

| failing tests | root cause | spec trace | layer(s) | judgment |
|---------------|------------|------------|----------|----------|
| fields lookup and fields_dict identity tests | `_Fields` is tuple-like but field name `count` is shadowed by tuple's built-in `.count` method, so field-name attribute lookup is incomplete. | "Public API"; "Cross-View Invariants" | atomic, integration | real candidate weakness; cross-view-consistency |
| private alias and explicit alias signature tests | Generated `__init__` is implemented as `*args, **kwargs`, so public `inspect.signature()` does not expose stripped or explicit initializer aliases. | "Initialization and Defaults" | atomic | real candidate weakness; api-surface |
| decorator default and `init=False` default tests | Decorator methods are collected as fields or required init args, corrupting field collection and default lifecycle. | "Field Collection and Class Definition"; "Initialization and Defaults" | atomic | real candidate weakness; state-management |
| `__attrs_init_subclass__` and `make_class(..., bases=...)` tests | slots rebuilding adds an invalid `__weakref__` slot for base-inheritance cases and fails before public behavior is observable. | "Initialization and Defaults"; "Dynamic Class Creation" | integration, system_e2e | real candidate weakness; workflow-completeness |
| decorator validator test | The decorator validator method is also collected as a field, making `fits_byte` a missing required argument. | "Validators"; "Field Collection and Class Definition" | atomic | real candidate weakness; state-management |
| decorator converter test | `@field.converter` stores a plain method but calls it as a one-argument converter, so instance and `Attribute` are not passed. | "Converters" | atomic | real candidate weakness; atomic-behavior |

Gate B result: passed. The failures measure candidate limitations, not oracle/spec gaps.

## Gate C - Generated-only Oracle Spot-check

The map declares `filter/oracle_source: generated_only`, so generated tests were spot-checked against both principles.

| nodeid | assertion summary | spec_section | verdict |
|--------|-------------------|--------------|---------|
| test_attrs_public_behavior_generated.py::test_fields_support_tuple_index_and_attribute_lookup | `fields[0].name == "sku"`, `fields.count is fields[1]`, and instance/class fields are identical. | "Public API" | spec-driven and behavioral |
| test_attrs_public_behavior_generated.py::test_private_attribute_default_alias_strips_leading_underscore | `Token.__init__` exposes `value`, not `_value`, and `asdict()` uses the stored `_value` field name. | "Initialization and Defaults" | spec-driven and behavioral |
| test_attrs_public_behavior_generated.py::test_frozen_class_rejects_assignment_with_frozen_instance_error | frozen instances reject assignment with the documented frozen exception and retain the old value. | "Assignment, Frozen Classes, and Setters" | spec-driven and behavioral |
| test_attrs_public_behavior_generated.py::test_asdict_recurses_into_nested_attrs_instances_and_collections | `asdict()` recursively converts nested attrs instances inside lists and tuples. | "Collection Conversion and Filters" | spec-driven and behavioral |
| test_attrs_public_behavior_generated.py::test_evolve_copies_instance_and_runs_converters_and_validators | `evolve()` copies unchanged fields, applies changes through converters/validators, and leaves the original unchanged. | "Copying and Evolution" | spec-driven and behavioral |
| test_attrs_public_behavior_generated.py::test_make_class_honors_bases_argument | dynamic classes created with `bases=(Base,)` inherit from and can call methods on `Base`. | "Dynamic Class Creation" | spec-driven and behavioral |

Gate C result: passed. No sampled generated test was circular or internal-shape dependent.

## Gate D - Coverage Gap Audit

Executable behavior coverage is full for scoreable sections. The only headings without direct rows are descriptive/protocol wrapper sections explicitly excluded by the map note, plus the H2 container "Representative Workflows" whose executable H3 workflows are covered.

| spec section | uncovered behaviors | impact | recommendation |
|--------------|---------------------|--------|----------------|
| Scope | Descriptive boundary statement, not an executable behavior. | none | no action |
| Representative Workflows | H2 container only; H3 workflows "Modern Data Class", "Validated Frozen Configuration", and "Dynamic Class Creation" are covered. | none | no action |
| Non-Goals | Negative scope statement, not a scoreable behavior. | none | no action |
| Invocation Protocol | Protocol statement; no CLI behavior is in scope. | none | no action |
| Evaluation Notes | Descriptive testing guidance. | none | no action |

Coverage verdict: FULL for scoreable behavior. Core sections including "Cross-View Invariants", "Error Semantics", "Initialization and Defaults", "Field Collection and Class Definition", and lifecycle/state sections all have covered rows.

## Real Failure Clusters

| dimension | description | affected_tests |
|-----------|-------------|----------------|
| cross-view-consistency | Field lookup by public field name disagrees with tuple attribute lookup when a field is named `count`, breaking `fields()` and `fields_dict()` identity invariants. | 2 |
| api-surface | Public initializer signature does not expose documented aliases because generated `__init__` is variadic. | 2 |
| state-management | Class-body decorator methods are incorrectly retained/collected as fields, breaking decorator defaults and decorator validators. | 3 |
| atomic-behavior | Decorator converters are called with the wrong protocol and do not receive instance/attribute context. | 1 |
| workflow-completeness | Slot rebuilding fails for inherited/dynamic classes with weakref slots, blocking subclass hooks and `make_class(..., bases=...)`. | 2 |

Cascade analysis: 10 failed tests reduce to 5 root causes. The candidate passed broad namespace, validators, converters, collection conversion, evolve, and classic compatibility coverage, so the task is discriminating rather than saturated. The failures are not dominated by a single missing import or collection failure.

## Labels

- discriminating
- generated-only-oracle
- candidate-non-saturated
- cross-view-consistency-signal
- state-management-signal

## Artifacts

- Candidate score: `candidate-runs/codex-attrs-specv1-20260704-001/score_result.json`
- Reference score: `wip/attrs-classes-fullrepro-001/filter/reference_score.json`
- Candidate output: `candidate-runs/codex-attrs-specv1-20260704-001/output`
- Report status: valid for strict legal count.
