# Packaging Stage 3 Test Filter Map

Spec source: `../spec/spec_v2.md` (spec judge PASS after narrow public API signature patches).

## Filter Policy

- Exclude any test file with top-level imports of private `packaging._*` modules or private names, because collection would require candidate implementations to ship undocumented internals.
- Exclude rows asserting exact error/warning text, private attributes, monkeypatch/platform internals, deprecation/pickle compatibility not described as public behavior in the spec, or files whose top-level collection requires private candidate-package names.
- Keep rows whose assertions are traceable to public docs/API reference and `spec_v2.md`: version/specifier/range semantics, requirement parsing, metadata validation, dependency groups, pylock, and public utilities.
- Property tests are retained when they import public modules plus test-suite strategy helpers outside the candidate package namespace. The retained set must be scored with pytest marker override `-m "property or not property"`, because Packaging defaults to `-m not property` in `pyproject.toml`.

## Summary

- AST-counted test rows: 1196
- Kept rows: 518
- Excluded rows: 678
- Preserved rate: 43.31%

## Kept By Layer

- atomic: 185
- integration: 327
- system_e2e: 6

## Required Scorer Arguments

Use these extra pytest arguments when validating the retained set:

```
--pytest-arg -m --pytest-arg "property or not property"
```

Without this override, retained property tests are deselected by the upstream default `-m not property`, producing a misleading executable count.

The scoring environment must also install `tomli_w`; `tests/test_pylock.py` imports it at module collection time for TOML round-trip assertions.

## File Decisions

| File | Kept | Excluded | Decision | Rationale |
|---|---:|---:|---|---|
| `tests/property/test_ranges_cross_epoch.py` | 2 | 0 | keep_all_selected_rows | keep_docs_backed_public_behavior |
| `tests/property/test_ranges_pep440_extended.py` | 20 | 0 | keep_all_selected_rows | keep_docs_backed_public_behavior |
| `tests/property/test_ranges_pubgrub.py` | 20 | 0 | keep_all_selected_rows | keep_docs_backed_public_behavior |
| `tests/property/test_ranges_set_algebra.py` | 28 | 1 | mixed_node_filter | keep_docs_backed_public_behavior |
| `tests/property/test_ranges_set_relations.py` | 10 | 0 | keep_all_selected_rows | keep_docs_backed_public_behavior |
| `tests/property/test_specifier_comparison.py` | 48 | 2 | mixed_node_filter | keep_docs_backed_public_behavior |
| `tests/property/test_specifier_extended.py` | 6 | 0 | keep_all_selected_rows | keep_docs_backed_public_behavior |
| `tests/property/test_specifier_implied.py` | 45 | 2 | mixed_node_filter | keep_docs_backed_public_behavior |
| `tests/property/test_specifier_matching.py` | 55 | 0 | keep_all_selected_rows | keep_docs_backed_public_behavior |
| `tests/property/test_version_format.py` | 44 | 0 | keep_all_selected_rows | keep_docs_backed_public_behavior |
| `tests/property/test_version_normalization.py` | 41 | 0 | keep_all_selected_rows | keep_docs_backed_public_behavior |
| `tests/property/test_version_ordering.py` | 28 | 0 | keep_all_selected_rows | keep_docs_backed_public_behavior |
| `tests/property/test_version_releases.py` | 61 | 0 | keep_all_selected_rows | keep_docs_backed_public_behavior |
| `tests/test_dependency_groups.py` | 10 | 16 | mixed_node_filter | exact error/warning message text is not a stable public contract |
| `tests/test_direct_url.py` | 0 | 22 | exclude_file_or_rows | excluded_file_private_top_level_import: packaging.direct_url._strip_url |
| `tests/test_elffile.py` | 0 | 6 | exclude_file_or_rows | excluded_file_private_top_level_import: packaging._elffile |
| `tests/test_errors.py` | 0 | 7 | exclude_file_or_rows | excluded_file_outside_spec_stage3_scope_or_requires_manual_review; private attribute access |
| `tests/test_licenses.py` | 0 | 4 | exclude_file_or_rows | excluded_file_private_top_level_import: packaging.licenses._spdx |
| `tests/test_manylinux.py` | 0 | 15 | exclude_file_or_rows | excluded_file_private_top_level_import: packaging._manylinux, packaging._manylinux._GLibCVersion, packaging._manylinux._get_glibc_version, packaging._manylinux._get_manylinux_module, packaging._manylinux._glibc_version_string; excluded_file_platform_mocking_helper_dependency; mock/monkeypatch/platform or internal environment setup |
| `tests/test_markers.py` | 0 | 55 | exclude_file_or_rows | excluded_file_private_top_level_import: packaging._parser, packaging.markers._format_full_version |
| `tests/test_metadata.py` | 0 | 74 | exclude_file_or_rows | excluded_file_private_top_level_carrier: `packaging.metadata._STRING_FIELDS` |
| `tests/test_musllinux.py` | 0 | 2 | exclude_file_or_rows | excluded_file_private_top_level_import: packaging._musllinux, packaging._musllinux._MuslVersion, packaging._musllinux._get_musl_version, packaging._musllinux._parse_musl_version; excluded_file_platform_mocking_helper_dependency |
| `tests/test_pylock.py` | 36 | 3 | mixed_node_filter | keep_docs_backed_public_behavior |
| `tests/test_pylock_select.py` | 6 | 5 | mixed_node_filter | keep_docs_backed_public_behavior |
| `tests/test_ranges.py` | 0 | 147 | exclude_file_or_rows | excluded_file_private_top_level_import: packaging._ranges; exact error/warning message text is not a stable public contract |
| `tests/test_requirements.py` | 47 | 3 | mixed_node_filter | keep_docs_backed_public_behavior |
| `tests/test_specifiers.py` | 0 | 108 | exclude_file_or_rows | excluded_file_depends_on_private_import_carrier_test_version |
| `tests/test_tags.py` | 0 | 126 | exclude_file_or_rows | excluded_file_private_top_level_import: packaging._manylinux, packaging._manylinux._GLibCVersion, packaging._musllinux, packaging._musllinux._MuslVersion; excluded_file_platform_mocking_helper_dependency |
| `tests/test_utils.py` | 11 | 0 | keep_all_selected_rows | keep_docs_backed_public_behavior |
| `tests/test_version.py` | 0 | 80 | exclude_file_or_rows | excluded_file_private_top_level_import: packaging._structures, packaging.version._BaseVersion, packaging.version._VersionReplace; excluded_file_platform_mocking_helper_dependency |

## Artifacts

- `kept_nodeids.txt`: retained pytest nodeids.
- `taxonomy.jsonl`: full keep/exclude audit rows.
- `taxonomy.csv`: scorer-compatible taxonomy derived from the same rows.


## Retroactive Generated Coverage Rows

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| `filter/generated_tests.py::test_package_shape_exposes_public_modules_and_version` | generated | atomic | Package Shape + Utilities | covered | Retroactive public packaging behavior test for Gate D coverage. |
| `filter/generated_tests.py::test_marker_extra_evaluation_normalizes_requested_extra` | generated | atomic | Markers | covered | Retroactive public packaging behavior test for Gate D coverage. |
| `filter/generated_tests.py::test_marker_missing_environment_name_raises_public_error` | generated | atomic | Error Semantics | covered | Retroactive public packaging behavior test for Gate D coverage. |
| `filter/generated_tests.py::test_requirement_parses_url_extras_and_marker_together` | generated | integration | Requirements + Dependency Groups | covered | Retroactive public packaging behavior test for Gate D coverage. |
| `filter/generated_tests.py::test_metadata_parse_email_reports_unparsed_fields_as_errors` | generated | atomic | Metadata | covered | Retroactive public packaging behavior test for Gate D coverage. |
| `filter/generated_tests.py::test_metadata_from_raw_validates_required_core_fields` | generated | atomic | Metadata | covered | Retroactive public packaging behavior test for Gate D coverage. |
| `filter/generated_tests.py::test_direct_url_round_trips_archive_info_to_json` | generated | integration | Direct URL Records | covered | Retroactive public packaging behavior test for Gate D coverage. |
| `filter/generated_tests.py::test_direct_url_rejects_missing_info_section` | generated | atomic | Error Semantics | covered | Retroactive public packaging behavior test for Gate D coverage. |
| `filter/generated_tests.py::test_license_expression_canonicalizes_spdx_operators` | generated | atomic | License Expressions | covered | Retroactive public packaging behavior test for Gate D coverage. |
| `filter/generated_tests.py::test_invalid_license_expression_raises_public_error` | generated | atomic | Error Semantics | covered | Retroactive public packaging behavior test for Gate D coverage. |
| `filter/generated_tests.py::test_error_helper_exception_group_collects_public_errors` | generated | atomic | Error Helpers + Pylock Files | covered | Retroactive public packaging behavior test for Gate D coverage. |
| `filter/generated_tests.py::test_cross_component_requirement_marker_and_specifier_agree` | generated | integration | Version Handling + Specifiers + Version Ranges + Cross-Component Invariants | covered | Retroactive public packaging behavior test for Gate D coverage. |

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| `filter/generated_tests.py::test_tag_object_and_parse_tag_round_trip_public_values` | generated | atomic | Tags | covered | Retroactive public Packaging tags test for Gate D coverage. |
Total: 123 | kept (covered): 123 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 123
