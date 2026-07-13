# Stage 5 Diagnosis Report: tomlkit-fullrepro-001

## Verdict

`QUALIFIED`

The repaired v4 oracle is valid for scoring this candidate. The import provenance check resolves to the candidate solution directory, the reference implementation passes the complete scoring set, the oracle is mapped to public spec behavior, and the candidate failures are mostly real reconstruction failures in public TOMLKit behavior rather than verifier failures.

## Preflight output

Command:

```powershell
$env:PYTHONPATH='G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-tomlkit-specv5-20260630-001\output'; python -c "import tomlkit; print(tomlkit.__file__)"
```

Literal output:

```text
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-tomlkit-specv5-20260630-001\output\tomlkit\__init__.py
```

## Anti-Cheat Scan

Result: no cheat detected.

The import preflight resolves inside `candidate-runs/codex-tomlkit-specv5-20260630-001/output`, not the oracle worktree, reference repository, or an installed package. The candidate run directory contains only `input/spec.md`, the submitted `output/tomlkit` package, and score JSONs produced after evaluation. A local artifact scan for forbidden strings found no access to `repo-pool`, `spec_test_map`, `kept_nodeids`, reference scores, prior score files in the implementation input/output, `pip install tomlkit`, or private `tomlkit.parser.Parser`. The only `Parser` matches are public spec text naming exception classes or rejecting parser-architecture requirements.

Limitation: no full model trajectory/log artifact was present under the listed candidate run directory, so this scan is limited to available task artifacts and candidate-run files.

## Solvability

Reference score: 195 / 195 passed, pass rate excluding skips 1.0.

Reference by layer:

| layer | passed | total |
|---|---:|---:|
| atomic | 108 | 108 |
| integration | 68 | 68 |
| system_e2e | 19 | 19 |

The repair status records the reference command using `harness/score_pytest_original.py` with `--remove-path tomlkit`, the repaired oracle worktree, and the task-specific nodeid/taxonomy files. This satisfies the solvability gate: the scoring set is executable and fully passed by the reference implementation.

## Candidate Score

Candidate score: 106 / 195 passed, 89 failed, pass rate excluding skips 0.5435897435897435.

Candidate by layer:

| layer | passed | failed | total |
|---|---:|---:|---:|
| atomic | 55 | 53 | 108 |
| integration | 44 | 24 | 68 |
| system_e2e | 7 | 12 | 19 |

This is not a high-score or saturation case. The candidate output is a small cleanroom-style implementation, but the score is far below 95%, so the high-score mandatory probe and saturation heuristic do not change the verdict beyond the normal provenance preflight above.

## Gate A: Spec Mapping Spot-Check

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `tests/test_api.py::test_parse_can_parse_valid_toml_files` | Public `parse()` reads valid TOML examples into mapping-like documents. | `### Parsing and Loading` | derivable |
| `tests/test_api.py::test_parse_raises_errors_for_invalid_toml_files` | Invalid TOML raises TOMLKit parse errors rather than silent bad documents. | `## Error Semantics` | derivable |
| `tests/test_toml_file.py::test_keep_old_eol` | `TOMLFile` read/write preserves file line-ending style during a write cycle. | `### TOMLFile` and `### Style Preservation` | derivable |
| `filter/generated_tests.py::test_generated_array_unwraps_nested_values` | Array item wrappers expose plain list values through `unwrap()`. | `### Public Items` | derivable |
| `filter/generated_tests.py::test_generated_document_setdefault_preserves_mapping_semantics` | `TOMLDocument.setdefault()` behaves like mutable mapping access and serializes the inserted table. | `### TOMLDocument` | derivable |
| `filter/generated_tests.py::test_generated_custom_encoder_for_decimal_item` | Registered encoders convert unsupported values into TOMLKit items for item conversion and dumping. | `### Custom Encoders` | derivable |
| `filter/generated_tests.py::test_generated_inline_table_array_round_trip` | Inline tables inside arrays remain semantically accessible and serializable after edits. | `### TOML Data Model` and `## Cross-View Invariants` | derivable |

No sampled mapping requires private parser structure, private attributes, exact undocumented exception wording, or hidden implementation layout.

## Gate B: Failure Pattern Audit

The candidate failures are consistent with public TOMLKit behavior described in the spec:

| cluster | examples | layer impact | judge finding |
|---|---|---|---|
| Incomplete style-preserving mutation | multiline array append, array comment survival, string mutation preserving inline comment, `TOMLFile` EOL preservation | system_e2e and integration | real model failure: violates `### Style Preservation` and `## Cross-View Invariants` |
| Missing public item semantics | missing `.value`, item wrappers degrading to plain strings, arithmetic not updating serialized form, table get/setdefault/update errors | atomic and integration | real model failure: violates `### Public Items` and `### TOMLDocument` |
| Incomplete table/dotted-key/AoT serialization | nested table assignment, dotted key helper, array-of-dicts to AoT, super-table headers | atomic and integration | real model failure: violates `### TOML Data Model`, `### Document Mutation`, and mapping/serialization invariants |
| Error and conversion semantics gaps | invalid strings not raising, encoder unregister not restoring conversion error, unsupported conversion behavior, parse-error parametrizations | atomic | real model failure where the candidate accepts/raises the wrong public error behavior |
| Plain mapping and sorted dumping gaps | sorted mapping dump, tuple/dict arrays, nested arrays with inline tables | integration | real model failure: violates `### Sorting and Plain Mapping Conversion` and `### Dumping and Writing` |

The failures do not cluster around undocumented atomic internal shapes. Some generated tests assert exact serialized TOML strings, but those strings are the observable public behavior for a style-preserving TOML library and are anchored in the spec's style, ordering, mutation, and cross-view contracts. The candidate often emits valid but style-losing TOML or semantically stale TOML; those are public behavior failures under this task.

## Gate C: Generated Tests

The map declares `oracle_source: upstream_plus_generated`, not `generated_only`, so Gate C is not mandatory. I still spot-checked generated tests because the repair depends on the generated public carrier.

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `filter/generated_tests.py::test_generated_scalar_items_unwrap_to_plain_values` | Scalar item wrappers unwrap to matching Python scalar values. | `### Public Items` | derivable |
| `filter/generated_tests.py::test_generated_multiline_array_append_preserves_layout` | Appending to parsed multiline arrays preserves multiline layout in serialized output. | `### Style Preservation` and `## Cross-View Invariants` | derivable |
| `filter/generated_tests.py::test_generated_inline_table_deletion_removes_separator` | Deleting an inline-table key leaves valid inline-table serialization without stray separators. | `### Document Mutation` and `### Public Items` | derivable |
| `filter/generated_tests.py::test_generated_custom_encoder_unregister_restores_conversion_error` | Unregistering an encoder removes conversion support for that value type. | `### Custom Encoders` and `## Error Semantics` | derivable |
| `filter/generated_tests.py::test_generated_file_style_cycle_via_string_projection` | String parse/edit/dump cycle preserves unrelated comments and exposes the edited semantic value. | `## Representative Workflows` and `## Cross-View Invariants` | derivable |

No sampled generated test checks private parser imports, internal field names, repr layout, or exact error-message wording.

## Gate D: Coverage Gap Audit

Coverage verdict: `FULL`.

Every spec H2/H3 section with behavioral obligations has at least one `covered` row in `spec_test_map.md`. Administrative sections such as `## Product Overview`, `## Scope`, `## Non-Goals`, `## Behavioral Sections`, and `## Evaluation Notes` are context rather than independently scoreable behavior. Core invariant sections are covered:

| spec section | coverage evidence | impact |
|---|---|---|
| `## Error Semantics` | upstream invalid TOML/value tests and generated duplicate/missing/conversion tests | no gap |
| `## Cross-View Invariants` | generated array/table/style/file round-trip tests and dotted/inline-table round trips | no gap |
| `### Style Preservation` | upstream write/TOMLFile tests and generated mutation-preservation tests | no gap |
| `### Document Mutation` | generated inline-table deletion, replacing tables, out-of-order edits, super-table header tests | no gap |
| `### TOMLDocument` | generated mapping copy/pop/setdefault/nested-table tests | no gap |
| `### TOMLFile` | upstream file read/write and EOL preservation tests | no gap |
| `### Custom Encoders` | generated register/unregister/custom context tests | no gap |

## Protocol Issues

No protocol issue requires routing back to spec or filter. The prior 2026-06-30 judge report retired the older narrow surface because public item behavior was lost when private-parser-importing upstream modules were excluded. The 2026-07-04 repair addresses that issue by keeping the 51 public upstream base nodeids and adding 45 generated public carrier tests that avoid `tomlkit.parser.Parser`.

## Real Failure Clusters

| dimension | root cause | affected tests |
|---|---|---|
| `state-management` | Candidate does not maintain formatting trivia and semantic state through mutation; edits collapse or lose multiline layout, comments, EOL style, and inline-table spacing. | 12 system_e2e failures plus related integration failures |
| `cross-view-consistency` | Candidate's item wrappers and serialized TOML diverge after list/table/scalar edits; some removals do not affect serialized/read-back semantics. | array removal, arithmetic/string mutation, inline-table array round trip, file-style cycle |
| `atomic-behavior` | Public item helpers are incomplete for documented scalar/date/time/string behavior and wrapper properties. | date/time/datetime, string styles, `.value`, item dict/list conversion |
| `error-semantics` | Invalid strings/conversions and missing-key operations do not reliably raise the documented public TOMLKit exception family. | invalid string creation, conversion unregister, missing table key, parse/value errors |
| `workflow-completeness` | Dumping/loading complete TOML structures is incomplete for nested tables, dotted keys, arrays of tables, sorted mappings, and nested inline tables. | dotted table dump, tuple/list-of-dict AoT, generated nested arrays, super-table headers |

## Cascade Analysis

The 89 failed expanded cases collapse to 50 failed base nodeids. The largest repeated failures are parametrized public behavior groups rather than independent bugs:

- `tests/test_api.py::test_parse_raises_errors_for_invalid_toml_files`: 16 parametrized failures around invalid TOML/error behavior.
- `tests/test_api.py::test_create_string`: 16 parametrized failures around string style and escaping behavior.
- `tests/test_api.py::test_create_string_with_invalid_characters`: 8 parametrized failures around invalid string rejection.
- `tests/test_api.py::test_parsed_document_are_properly_json_representable`: 3 parametrized failures around document JSON/mapping projection.

The remaining failures are mostly single-case public behavior gaps. System failures are not just a cascade from a missing import or absent top-level API; they expose incomplete style-preserving document state management across parse/edit/dump workflows.

## Labels

- `discriminating`
- `style-preservation-signal`
- `cross-view-consistency-signal`
- `public-generated-carrier`
- `workflow-completeness-signal`
