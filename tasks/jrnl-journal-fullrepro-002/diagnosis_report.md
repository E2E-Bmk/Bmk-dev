# Diagnosis Report - jrnl-journal-fullrepro-002

Verdict: QUALIFIED

Judged score artifact: `candidate-runs/codex-jrnl-specv1-20260701-001/score_result_wsl_481_import_fairness.json`

Labels: `discriminating`, `import-fairness-repaired`, `cascade-dominated`, `workflow-completeness-gap`, `api-surface-gap`

## Preflight output

Command:

```powershell
$env:PYTHONPATH='G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-jrnl-specv1-20260701-001\solution'; python -c "import jrnl; print(jrnl.__file__)"
```

Literal output:

```text
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-jrnl-specv1-20260701-001\solution\jrnl\__init__.py
```

The provenance check points to the candidate solution `jrnl/__init__.py`, not the oracle source, repo-pool, or an installed package.

## Anti-Cheat Scan

No cheat verdict is issued.

Evidence checked:

- `cleanroom_manifest.json` says the candidate packet included only `public_packet/spec.md` and `task_prompt.txt`; hidden benchmark assets, reference artifacts, prior runs, filter files, tests, and scoring outputs were excluded by policy.
- `task_prompt.txt` explicitly forbids reading tests, feature files, conftest files, parent/sibling benchmark directories, source repositories, filter artifacts, score reports, reference solutions, prior candidate runs, and the real `jrnl` package.
- The candidate implementation directory contains a compact implementation under `solution/jrnl`; available run artifacts do not include a separate implementation transcript/log. I therefore base the anti-cheat conclusion on the cleanroom manifest, prompt, available artifacts, and the required import provenance preflight.
- The score artifact itself reports `solution_dir` as the candidate solution and `remove_paths: {jrnl}`.

## Score Hard Checks

The current repaired 481 score is the only score used for this judgement.

Candidate score metadata:

- platform: `Linux-5.15.153.1-microsoft-standard-WSL2-x86_64-with-glibc2.31`
- `remove_paths`: `{jrnl}`
- source repo for carrier/oracle: `candidate-runs/codex-jrnl-specv1-20260701-001/oracle_source_481_current`
- nodeids: `wip/jrnl-journal-fullrepro-002/filter/kept_nodeids.txt`
- summary: 98 passed, 383 failed, 481 total
- pass rate excluding skips: 0.20374220374220375

Candidate by layer:

- atomic: 6/9 passed, 3 failed
- integration: 58/285 passed, 227 failed
- system_e2e: 34/187 passed, 153 failed

This is the repaired import-fairness 481 score, not the old 473 score and not the pre-repair 481 score.

## Reference Gate

Reference solvability passes. `wip/jrnl-journal-fullrepro-002/filter/reference_score.json` reports:

- platform: `Linux-5.15.153.1-microsoft-standard-WSL2-x86_64-with-glibc2.31`
- `remove_paths`: `{jrnl}`
- source repo: `candidate-runs/codex-jrnl-specv1-20260701-001/oracle_source_481_current`
- run dir: `results/jrnl-journal-fullrepro-002/reference_481_import_fairness`
- summary: 481 passed, 481 total
- pass rate excluding skips: 1.0

Reference by layer:

- atomic: 9/9 passed
- integration: 285/285 passed
- system_e2e: 187/187 passed

This establishes that the current 481-nodeid repaired oracle is solvable under Linux/WSL with `--remove-path jrnl`.

## Gate A - Spec Mapping Spot Check

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `filter/generated_tests.py::test_journal_entry_parses_title_body_star_and_tags` | `Entry` derives title, body, and normalized tags from text. | `### Journal Objects` | derivable |
| `filter/generated_tests.py::test_display_export_plugins_are_publicly_importable` | documented plugin classes import from `jrnl.plugins`. | `### Plugins and Exporters` | derivable |
| `tests/bdd/test_features.py::test_read_a_journal_from_an_alternate_config` | `--config-file` selects an alternate config and journal mapping. | `## Configuration` | derivable |
| `tests/bdd/test_features.py::test_changetime_with_edit_modifies_selected_entries[basic_onefile.yaml]` | edit/change-time acts on the selected search result set. | `### Actions on Search Results` | derivable |
| `tests/bdd/test_features.py::test_writing_an_entry_from_command_line_should_store_the_entry[simple.yaml]` | CLI composition stores an entry in the journal text format. | `## Format Contracts` | derivable |
| `tests/bdd/test_features.py::test_tags_are_saved_when_an_entry_is_edited_with_edit_and_can_be_searched_afterward[basic_folder.yaml]` | edited tags remain visible to later search/display behavior. | `## Cross-View Invariants` | derivable |

Gate A passes: sampled covered rows trace to exact candidate-visible headings and assert observable behavior.

## Generated Rows and Import Fairness

`spec_test_map.md` uses `oracle_source: upstream_plus_retro_generated`, so Gate C as `generated_only` is not applicable. Because generated rows are present, I still sampled the generated supplement for import fairness and behavioral traceability.

Generated import repair evidence from `filter/generated_tests.py`:

- `Entry` rows use `from jrnl.journals import Entry`, matching the public import surface in `## Installable Surface`.
- journal object surface row uses `from jrnl.journals import DayOne, Entry, Folder, Journal, open_journal`, matching the public import surface.
- plugin rows use `from jrnl.plugins import JSONExporter, MarkdownExporter, TextExporter, EXPORT_FORMATS, IMPORT_FORMATS, get_exporter`, matching the public plugin import surface.
- no generated row imports undocumented submodules such as `jrnl.journals.Entry` or `jrnl.plugins.*_exporter`.

Generated row spot-check:

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `filter/generated_tests.py::test_journal_package_exposes_documented_public_objects` | public journal objects are exported from `jrnl.journals`. | `## Installable Surface` / `### Journal Objects` | derivable, behavioral |
| `filter/generated_tests.py::test_plugin_registry_exposes_documented_builtin_formats` | `EXPORT_FORMATS` includes documented built-in names and `IMPORT_FORMATS` includes `jrnl`. | `### Plugins and Exporters` | derivable, behavioral |
| `filter/generated_tests.py::test_get_exporter_maps_documented_public_format_names` | `get_exporter` maps public format names to documented exporter classes or `None`. | `### Plugins and Exporters` | derivable, behavioral |
| `filter/generated_tests.py::test_missing_config_path_reports_handled_cli_error` | missing config path is a handled CLI error. | `## Error Semantics` | derivable, behavioral |
| `filter/generated_tests.py::test_daily_journaling_dry_run_help_surfaces_write_and_search_options` | CLI help returns success and surfaces documented options/usage. | `### CLI Entry` / `### Daily journaling and search` | derivable, behavioral |

The previous BROKEN cause is repaired. Current generated failures are not import-surface verifier failures; they execute candidate behavior and expose model gaps.

## Gate B - Failure Pattern Audit

Sampled failing tests are valid model failures:

| nodeid | observed failure | spec basis | judgement |
|---|---|---|---|
| `filter/generated_tests.py::test_journal_entry_parses_title_body_star_and_tags` | candidate `Entry.tags` expects `journal.tagsymbols` and fails with `AttributeError` for a journal-like object carrying config. | `### Journal Objects` says `Entry` exposes `title`, `body`, `tags`, and derives tags from the journal's configured tag symbols. | model failure, `atomic-behavior` |
| `filter/generated_tests.py::test_entry_fulltext_combines_title_and_body` | candidate `fulltext` routes through timestamp formatting and requires `journal.timeformat`. | `### Journal Objects` exposes `fulltext`; `## Format Contracts` specifies visible entry text behavior. | model failure, `atomic-behavior` |
| `filter/generated_tests.py::test_daily_journaling_dry_run_help_surfaces_write_and_search_options` | help output omits `--config-file`. | `## Configuration` documents `--config-file`; `### Standalone Commands` documents help. | model failure, `api-surface` |
| `tests/bdd/test_features.py::test_changetime_with_edit_modifies_selected_entries[basic_onefile.yaml]` | candidate reports editor command not found instead of handling empty edit result. | `### Actions on Search Results` and `## Error Semantics` document edit workflow and empty-editor handling. | model failure, `workflow-completeness` |
| `tests/bdd/test_features.py::test_dont_crash_if_no_default_journal_is_specified_using_an_alternate_config` | candidate emits a different default-journal error contract. | `## Configuration` and `## Error Semantics` document default journal selection and user-facing configured-journal failures. | model failure, `error-semantics` |
| `tests/bdd/test_features.py::test_write_to_specified_journal` | output contains extra blank-line formatting relative to expected journal display. | `## Format Contracts` and `## Cross-View Invariants` specify stable storage/display projections. | model failure, `cross-view-consistency` |

The failures are not dominated by undocumented internal shapes, exact private names, or hidden submodule imports. They are public CLI/API/storage behaviors. Gate B passes.

## Gate D - Coverage Gap Audit

Coverage scan over spec H2/H3 sections:

| spec section | uncovered behaviors | impact | recommendation |
|---|---|---|---|
| `## Product Overview` | no direct rows | narrative/non-behavioral overview | no action |
| `## Scope` | no direct rows | boundary list, covered indirectly by behavior sections | no action |
| `## Non-Goals` | no direct rows | exclusions, not scoreable behavior | no action |
| `## Evaluation Notes` | no direct rows | benchmark notes, not candidate behavior | no action |

Core behavior sections are covered, including `## Error Semantics`, `## Cross-View Invariants`, `### Journal Objects`, `### Plugins and Exporters`, `### Actions on Search Results`, `## Configuration`, `## Journal Storage`, `## Format Contracts`, and `## Encryption`.

Coverage verdict: PARTIAL acceptable. Product Overview zero coverage is narrative/non-behavioral and is not a core GAP.

## Real Failure Clusters

Root clusters:

- `api-surface`: candidate exposes enough package surface to pass some imports but misses documented CLI/help detail such as `--config-file` surfacing.
- `atomic-behavior`: `Entry` derived properties are brittle around journal configuration and text projection.
- `error-semantics`: handled CLI failures often emit different messages/conditions than the public contract.
- `workflow-completeness`: editor, delete, change-time, encryption, import/export, and multi-journal workflows are incomplete or time out.
- `cross-view-consistency`: storage/display/export projections diverge in blank lines, tag reports, starred markers, and date formatting.

## Cascade Analysis

383 failures collapse into a smaller set of root causes: incomplete CLI workflow engine, incomplete journal/config state model, brittle `Entry` behavior, and partial formatter/exporter semantics. Many system_e2e failures are cascades from those primitives, so the run is more `cascade-dominated` than a pure cross-component composition signal.

## Protocol Issues and Action

No spec patch or filter correction is required.

The current oracle passes reference 481/481, uses Linux/WSL with `--remove-path jrnl`, the candidate score is valid at 98/481, generated import fairness has been repaired, and Gate A/B/D pass. Set pipeline state to `QUALIFIED` and synchronize the current repaired 481 artifacts into `tasks/jrnl-journal-fullrepro-002`.
