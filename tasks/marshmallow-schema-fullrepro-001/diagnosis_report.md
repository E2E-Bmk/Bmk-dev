# Diagnosis Report - marshmallow-schema-fullrepro-001

VERDICT=QUALIFIED

This task can be counted in the strict legal set. The candidate run is provenance-clean in the available artifacts, the reference gate is solvable, the candidate failures are real public-behavior gaps, and no unresolved fairness or coverage gate blocks qualification.

## Preflight output

Command:

```bash
wsl env PYTHONPATH=/mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-marshmallow-specv1-20260704-001/output /usr/bin/python3 -c 'import marshmallow; print(marshmallow.__file__)'
```

Literal output:

```text
/mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-marshmallow-specv1-20260704-001/output/marshmallow/__init__.py
```

The import provenance points into the candidate solution directory.

## Anti-Cheat Scan

No forbidden access indicator was found in the candidate solution tree. A scan of `candidate-runs/codex-marshmallow-specv1-20260704-001` found references to oracle paths only inside scorer metadata (`score_result.json`), not in the candidate implementation. The provided candidate-run artifact does not include a full implementation trajectory log; this judgment is based on the available candidate packet, prompt, output tree, scorer metadata, and import provenance.

## Reference Gate

Reference gate passed on Linux/WSL with scorer isolation:

- Platform: `Linux-5.15.153.1-microsoft-standard-WSL2-x86_64-with-glibc2.31`
- Isolation: `--remove-path marshmallow`
- Collected: 69
- Passed: 69
- Failed: 0
- Pass rate: 1.0

This satisfies the solvability requirement.

## Candidate Score

Candidate run used the same Linux/WSL scorer isolation with `--remove-path marshmallow`.

- Collected: 69
- Passed: 67
- Failed: 2
- Collection errors: 0
- Runtime/scorer errors: 0
- Pass rate excluding skips: 0.9710144927536232

Layer summary:

| layer | passed | failed | total |
|---|---:|---:|---:|
| atomic | 24 | 2 | 26 |
| integration | 19 | 0 | 19 |
| system_e2e | 24 | 0 | 24 |

## Gate A - Spec Mapping Spot-Check

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `filter/generated_tests.py::test_schema_from_dict_creates_usable_schema_class` | `Schema.from_dict` creates a schema class whose field conversion works on load. | `Schema Declaration and Field Binding` | derivable |
| `filter/generated_tests.py::test_unknown_include_preserves_extra_input` | `unknown=INCLUDE` keeps unknown input keys in loaded data. | `Unknown, Partial, Defaults, and Key Mapping` | derivable |
| `filter/generated_tests.py::test_validation_error_exposes_messages_and_valid_data` | invalid load raises `ValidationError` exposing messages and valid partial data. | `Validation and Error Reporting` | derivable |
| `filter/generated_tests.py::test_nested_only_uses_nested_field_subset` | nested schemas honor nested `only` projection during dump. | `Nested Data and Collection Handling` | derivable |
| `filter/generated_tests.py::test_dump_and_dumps_use_same_external_data_key` | `dump` and `dumps` agree on `data_key` external output key. | `Cross-View Invariants` | derivable |
| `filter/generated_tests.py::test_pre_load_and_post_load_transform_data` | schema-level load hooks transform input and final loaded result. | `Processor and Validator Decorators` | derivable |

Spot-check result: mappings are spec-driven and behavioral.

## Gate B - Failure Pattern Audit

The two candidate failures are real candidate weaknesses, not oracle/spec gaps.

| failing nodeid | mapped layer | public assertion | spec trace | audit verdict |
|---|---|---|---|---|
| `filter/generated_tests.py::test_field_pre_and_post_load_processors_transform_value` | atomic | `fields.Str(pre_load=str.strip, post_load=str.title)` must transform a loaded value from `"  ada lovelace  "` to `"Ada Lovelace"`. | `Field Types and Conversion` documents that field-level `pre_load` processors run before field deserialization and field-level `post_load` processors run after field deserialization and validation. | real model failure, atomic-behavior |
| `filter/generated_tests.py::test_field_processor_validation_error_attaches_to_field` | atomic | a field-level `pre_load` processor raising `ValidationError` must make `Schema.load` raise with an error attached to the field. | `Field Types and Conversion` and `Validation and Error Reporting` document field-level processor error attachment and field-keyed validation errors. | real model failure, atomic-behavior / error-semantics |

The candidate implementation accepts arbitrary field metadata but does not apply field-level `pre_load` or `post_load` processors during `Field.deserialize`. As a result, both failures root in one missing field-processor pathway. The tests assert public `load` return values and public `ValidationError.messages`; they do not inspect private fields, repr output, source layout, or exact error message wording.

Cascade analysis: 2 failed tests, 1 root cause. No integration or system_e2e failures cascade from this issue in the kept scoring set.

## Gate C - Generated Oracle Spot-Check

The oracle source is `generated_reference_observed`; because all scoreable tests are generated, I applied the generated-only spot-check standard.

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `filter/generated_tests.py::test_only_limits_dump_and_load_views` | active `only` projection limits dump and load views and rejects excluded input under default unknown handling. | `Product State Model` | spec-driven behavioral |
| `filter/generated_tests.py::test_string_integer_float_decimal_boolean_conversions` | core scalar fields deserialize documented compatible inputs and dump booleans/decimals as documented. | `Field Types and Conversion` | spec-driven behavioral |
| `filter/generated_tests.py::test_multiple_validators_collect_multiple_failures_for_field` | multiple validators on one field accumulate multiple field failures. | `Validation and Error Reporting` | spec-driven behavioral |
| `filter/generated_tests.py::test_pass_collection_hooks_receive_whole_collection` | `pass_collection=True` hooks receive and return whole collections. | `Processor and Validator Decorators` | spec-driven behavioral |
| `filter/generated_tests.py::test_load_validate_and_loads_agree_on_unknown_errors` | `load`, `loads`, and `validate` agree on unknown-field errors. | `Cross-View Invariants` | spec-driven behavioral |
| `filter/generated_tests.py::test_nested_unknown_policy_is_applied_inside_nested_schema` | nested schema `Meta.unknown = EXCLUDE` is honored inside a parent load. | `Nested Data and Collection Handling` | spec-driven behavioral |

No sampled generated test is circular or internal-shape dependent.

## Gate D - Coverage Gap Audit

Coverage verdict: PARTIAL, acceptable.

All core behavioral sections have at least one covered row: `Product State Model`, `Schema Declaration and Field Binding`, `Serialization and Deserialization`, `Field Types and Conversion`, `Validation and Error Reporting`, `Unknown, Partial, Defaults, and Key Mapping`, `Nested Data and Collection Handling`, `Processor and Validator Decorators`, `JSON and Context Projections`, and `Cross-View Invariants`.

| spec section | uncovered behaviors | impact | recommendation |
|---|---|---|---|
| `Product Overview` | overview only, no independent behavior | none | no action |
| `Scope` | scope statement only | none | no action |
| `Installable Surface` | import-only smoke test was excluded after dummy gate; public imports are still exercised by test module imports and by behavioral tests | low | no blocking action |
| `Representative Workflows` | illustrative workflow not separately mapped | low; underlying behaviors are covered elsewhere | no blocking action |
| `Non-Goals` | exclusions, not required behavior | none | no action |
| `Invocation Protocol` | no CLI behavior required | none | no action |
| `Evaluation Notes` | meta notes only | none | no action |

No core invariant, error-semantics, or state lifecycle section has zero behavioral coverage.

## Protocol Issues

No protocol issue requires routing back to spec-writer or test-filter. The only caveat is that the two failing field-processor rows are mapped in `spec_test_map.md` to `Processor and Validator Decorators`, while the most direct spec text for field-level processors is in `Field Types and Conversion`. This is a minor mapping precision issue because the behavior is still explicitly specified and behavioral; it does not affect the verdict.

## Real Failure Clusters

| cluster | affected tests | dimension | root cause |
|---|---|---|---|
| missing field-level load processors | 2 atomic tests | `atomic-behavior` | Candidate ignored field constructor `pre_load` and `post_load` processor metadata, so values were not transformed and processor-raised `ValidationError` was not attached to the field. |

## Labels

- `discriminating`
- `high-score-non-saturated`
- `atomic-field-processor-gap`
- `generated-reference-observed-oracle`

## Final Verdict

VERDICT=QUALIFIED. The task is valid for strict benchmark counting, with candidate weakness evidence concentrated in one real atomic field-processor implementation gap.
