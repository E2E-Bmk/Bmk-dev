# Stage 5 Diagnosis - repaired-carrier WSL re-judge

Task: `packaging-core-fullrepro-001`  
Candidate run: `candidate-runs/codex-packaging-specv2-20260630-001`  
Score JSON: `candidate-runs/codex-packaging-specv2-20260630-001/score_result_wsl_123_carrier.json`  
Reference score: `wip/packaging-core-fullrepro-001/filter/reference_score_wsl_123_carrier.json`  
Date: 2026-07-03

## Anti-cheat preflight

Preflight command run before reading score values:

```powershell
$env:PYTHONPATH='G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-packaging-specv2-20260630-001\solution'; python -c "import packaging; print(packaging.__file__)"
```

Preflight output:

```text
__file__=G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-packaging-specv2-20260630-001\solution\packaging\__init__.py
```

The import provenance points inside the candidate solution directory.

## Verdict

`QUALIFIED`.

The repaired carrier score is a valid task result. The previous WSL blocker was the missing `filter/generated_tests.py` carrier file; in this rerun the generated Gate D rows collect and the reference passes the full repaired oracle. Candidate failures are concentrated in documented public behavior for requirements, dependency groups, pylock, pylock selection, metadata, markers, and utilities.

## Anti-cheat scan

- Import provenance passed; `packaging.__file__` points inside `candidate-runs/codex-packaging-specv2-20260630-001/solution`.
- `run_meta.json` records cleanroom inputs as `task_prompt.txt` and `public_packet/spec.md`; forbidden inputs include source repositories, original tests, filter artifacts, score reports, previous attempts, and Bmk-dev workflow skills.
- Static scan of available candidate-run implementation artifacts found no evidence of source repo access, oracle metadata access during implementation, score report access during implementation, or target-package installation.
- No full implementation trajectory transcript was present in the candidate-run directory, so the scan is limited to available run artifacts plus import provenance. The available evidence does not show cheating.

## Reference solvability

Reference file: `wip/packaging-core-fullrepro-001/filter/reference_score_wsl_123_carrier.json`.

- Platform: Linux/WSL.
- Summary: `5488 passed / 5488 total`.
- Pass rate excluding skips: `1.0`.
- By layer: atomic `70/70`; integration `5390/5390`; system_e2e `15/15`; generated/unknown `13/13`.
- Generated carrier rows: `13/13` passed.

Solvability passes. The repaired carrier establishes a clean reference ceiling for the full retained oracle.

## Candidate score

Candidate file: `candidate-runs/codex-packaging-specv2-20260630-001/score_result_wsl_123_carrier.json`.

- Platform: Linux/WSL.
- Summary: `149 passed / 153 failed / 2 timeout / 304 total`.
- Pass rate excluding skips: `0.4901315789473684`.
- By layer: atomic `66 passed / 4 failed / 70 total`; integration `73 passed / 131 failed / 2 timeout / 206 total`; system_e2e `15 failed / 15 total`; generated/unknown `10 passed / 3 failed / 13 total`.
- Generated carrier rows: candidate `10/13` passed, reference `13/13` passed.

The candidate score is discriminating and far below the reference ceiling; no high-score saturation probe beyond the mandatory provenance preflight is triggered.

## Gate A - Spec mapping spot-check

Representative covered rows were checked against exact headings in `wip/packaging-core-fullrepro-001/spec/spec_v2.md`.

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `filter/generated_tests.py::test_package_shape_exposes_public_modules_and_version` | Public modules and names are importable from the `packaging` package. | `## Package Shape` | derivable |
| `filter/generated_tests.py::test_cross_component_requirement_marker_and_specifier_agree` | Requirement parsing, marker evaluation, and specifier membership agree across public objects. | `## Cross-Component Invariants` | derivable |
| `tests/test_dependency_groups.py::test_lookup_with_include_result` | `lookup()` returns public `Requirement` and `DependencyGroupInclude` objects for include directives. | `## Dependency Groups` | derivable |
| `tests/test_pylock.py::test_pylock_basic_package` | `Pylock.from_dict()` validates and builds public pylock objects from TOML-style mappings. | `## Pylock Files` | derivable |
| `tests/test_pylock_select.py::test_smoke_test` | `Pylock.select()` selects installable artifacts using pylock data, markers, tags, and packages. | `## Pylock Files` | derivable |
| `tests/test_requirements.py::TestRequirementParsing::test_valid_marker[os.name == 'linux']` | A requirement may include an environment marker after `;`. | `## Requirements` | derivable |
| `tests/test_utils.py::test_canonicalize_name_invalid[hi\n-hi\n]` | `canonicalize_name(validate=True)` rejects invalid names with `InvalidName`. | `## Utilities` | derivable |

Gate A passes. The sampled tests trace to exact public spec sections and assert observable outcomes.

## Gate B - Failure pattern audit

Sampled failures are mostly public behavioral failures:

- Requirements: marker grammar, URL/specifier parsing, equality/hash normalization, and pickle-compatible public requirement state diverge from `## Requirements`, `## Markers`, and `## Cross-Component Invariants`.
- Pylock: TOML key conversion such as `upload-time`, supported lock versions, artifact fields, filename validation, and public dataclass construction diverge from `## Pylock Files`.
- Pylock selection: all `15` system_e2e failures cascade from incomplete pylock parsing/validation into `select()` workflows, matching `## Pylock Files` and `## Cross-Component Invariants`.
- Dependency groups: include directives are parsed but expose the wrong include target surface (`group` instead of the expected public include-group surface), affecting expansion and lookup behavior under `## Dependency Groups`.
- Utilities: invalid normalized names and wheel filename validation diverge from `## Utilities` and `## Error Semantics`.
- Generated rows: candidate misses public marker and metadata behavior while reference passes the same rows.

Caveat: a subset of requirement and pylock failures assert exact public `str()`, `repr()`, or validation message text. These are not the majority of the failure signal, and the retained oracle also contains many non-message public behavior failures. They do not make the repaired carrier invalid.

Gate B passes. The dominant failure pattern is real model failure, not verifier failure.

## Gate C - Generated-row spot-check

The whole oracle is not `generated_only`, but the repaired carrier includes 13 generated Gate D rows. A manual sample was checked because these rows were the prior materialization blocker.

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `filter/generated_tests.py::test_package_shape_exposes_public_modules_and_version` | Public modules and names are importable and expose expected public callables/classes. | `## Package Shape` | derivable |
| `filter/generated_tests.py::test_marker_extra_evaluation_normalizes_requested_extra` | Marker evaluation normalizes extras supplied through the environment mapping. | `## Markers` | derivable |
| `filter/generated_tests.py::test_metadata_parse_email_reports_unparsed_fields_as_errors` | `parse_email()` returns normalized raw metadata and unparsed-field mapping. | `## Metadata` | derivable |
| `filter/generated_tests.py::test_direct_url_round_trips_archive_info_to_json` | Direct URL records serialize and deserialize equivalent public objects. | `## Direct URL Records` | derivable |
| `filter/generated_tests.py::test_license_expression_canonicalizes_spdx_operators` | SPDX license expression canonicalization normalizes license IDs and operators. | `## License Expressions` | derivable |
| `filter/generated_tests.py::test_error_helper_exception_group_collects_public_errors` | Public `ExceptionGroup` exposes collected exceptions and message behavior. | `## Error Helpers` | derivable |
| `filter/generated_tests.py::test_tag_object_and_parse_tag_round_trip_public_values` | `Tag` and `parse_tag()` round-trip public tag values. | `## Tags` | derivable |

No sampled generated test is circular or internal-shape based. Gate C passes for the generated carrier rows.

## Gate D - Coverage gap audit

Behavioral H2 sections in the spec have executable coverage in the repaired WSL carrier. Non-goal or process-only sections (`## Product Overview`, `## Non-Goals`, `## Candidate Agent Input Boundary`) are not scorer behavior surfaces.

| spec section | uncovered behaviors | impact | recommendation |
|---|---|---|---|
| `## Package Shape` | none | generated row now executes | keep |
| `## Version Handling` | none | property/upstream rows cover parsing, normalization, ordering, properties | keep |
| `## Specifiers` | none | property/upstream rows cover membership, filtering, prereleases, combination | keep |
| `## Version Ranges` | none | property rows cover range algebra and `SpecifierSet.to_range()` consistency | keep |
| `## Markers` | none | generated and requirement rows cover parsing/evaluation/extra normalization | keep |
| `## Requirements` | none | upstream rows cover parsing, equality, hashing, markers, extras, URL/specifier behavior | keep |
| `## Tags` | none | generated tag row covers public tag round trip | keep |
| `## Utilities` | none | upstream rows cover name/version canonicalization and wheel/sdist parsing | keep |
| `## Metadata` | none | generated metadata rows execute and pass on reference | keep |
| `## Direct URL Records` | none | generated direct-url rows execute and pass on reference | keep |
| `## Dependency Groups` | none | upstream rows cover lookup, include expansion, normalization, and resolver behavior | keep |
| `## Pylock Files` | none | upstream rows cover validation, serialization, object construction, and selection workflows | keep |
| `## License Expressions` | none | generated license rows execute and pass on reference | keep |
| `## Error Helpers` | none | generated error-helper row executes and passes on reference | keep |
| `## Cross-Component Invariants` | none | generated and pylock/requirement rows cover shared marker/specifier/name/tag behavior | keep |
| `## Error Semantics` | none | generated and upstream invalid-input rows cover public exception surfaces | keep |

Coverage verdict: `FULL`. Gate D passes.

## Protocol issues and actions

No blocking protocol issue remains after carrier repair. The earlier WSL problem was a filter materialization issue, but this run uses `.tmp/packaging-oracle-carrier-123` with `filter/generated_tests.py` present; reference and candidate both collect the generated rows.

No `filter_correction_request.md` or `spec_patch_request.md` is needed.

## Real failure clusters

| cluster | layer | dimension | evidence | cascade |
|---|---|---|---|---|
| Requirement grammar and normalization | integration | `atomic-behavior` | `tests/test_requirements.py`: `77` failed and `2` timeout, including marker grammar, invalid specifiers, extras syntax, URL parsing, equality/hash normalization, and pickle compatibility. | Explains many integration failures; not a cross-component-only signal. |
| Pylock parsing, validation, and TOML mapping | integration | `workflow-completeness` | `tests/test_pylock.py`: `51` failed, including lock version handling, TOML key mapping, artifact fields, validation, and serialization round trips. | Root cause for all downstream pylock selection failures. |
| Pylock selection across markers/tags/extras/groups | system_e2e | `cross-view-consistency` | `tests/test_pylock_select.py`: `15/15` failed. | Mostly cascades from incomplete `Pylock.from_dict()` and artifact modeling. |
| Dependency-group include object surface | integration | `api-surface` | `tests/test_dependency_groups.py`: `3` failures around include directive public surface and representation. | Small local cluster. |
| Public invalid-input exceptions | atomic | `error-semantics` | `tests/test_utils.py` invalid names/wheel names plus generated marker/metadata validation failures. | Independent atomic failures. |

Cascade analysis: the `153` failures and `2` timeouts reduce to roughly five root clusters. The largest cascades come from requirement grammar and pylock object/validation incompleteness; pylock selection system failures are downstream of the pylock root cluster.

## Task labels

- `discriminating`: reference is at ceiling while candidate is below half pass rate.
- `standards-grammar-composition`: failures concentrate in grammar-heavy packaging standards and their composition.
- `cascade-dominated`: system_e2e pylock failures mostly cascade from lower-level pylock parsing and validation gaps.
- `full-coverage-repaired-carrier`: generated Gate D rows now collect and pass on reference.
