# Diagnosis Report - mkdocs-sitebuild-fullrepro-002

## Preflight output

Command:

```powershell
$env:PYTHONPATH='G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-mkdocs-specv1-20260701-001\solution'; python -c "import mkdocs; print(mkdocs.__file__)"
```

Literal output:

```text
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-mkdocs-specv1-20260701-001\solution\mkdocs\__init__.py
```

The import resolves inside the candidate run's `solution` directory, not the reference repository, oracle worktree, repo pool package, or an installed package.

## Verdict

Status: QUALIFIED after legal Stage 5 re-judge.

This re-judge accepts the retroactive 50-test oracle only with a real 50-test candidate score. The accepted candidate score is `candidate-runs/codex-mkdocs-specv1-20260701-001/score_result_wsl_50.json`, run on Linux/WSL, with 38/50 passed. The reference solvability ceiling is `wip/mkdocs-sitebuild-fullrepro-002/filter/reference_score_retro_gate_d.json`, with 50/50 passed. Earlier 37-test diagnosis evidence is superseded for the terminal task export.

## Hard Checks

### Anti-cheat and provenance

Import provenance passed before reading or quoting the WSL 50-test score. The preflight output above points to the candidate solution directory.

Candidate-visible artifacts checked:

- `candidate-runs/codex-mkdocs-specv1-20260701-001/public_packet/spec.md`
- `candidate-runs/codex-mkdocs-specv1-20260701-001/task_prompt.txt`
- `candidate-runs/codex-mkdocs-specv1-20260701-001/cleanroom_manifest.json`
- `candidate-runs/codex-mkdocs-specv1-20260701-001/solution`

Focused scan result: no forbidden source repository paths, reference-score files, score-result files, spec-test maps, kept-nodeid files, rewritten oracle files, generated oracle files, or oracle worktree paths were found in the delivered candidate solution. The cleanroom manifest says only `public_packet/spec.md` and `task_prompt.txt` were included for the candidate, with hidden benchmark assets, reference artifacts, prior runs, filter files, tests, and scoring outputs excluded by policy.

### Candidate score platform

Accepted score file: `candidate-runs/codex-mkdocs-specv1-20260701-001/score_result_wsl_50.json`.

Platform:

```text
Linux-5.15.153.1-microsoft-standard-WSL2-x86_64-with-glibc2.31
```

The score platform does not contain `Windows`. The score `solution_dir` is `/mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-mkdocs-specv1-20260701-001/solution`.

### Reference solvability

Accepted reference evidence: `wip/mkdocs-sitebuild-fullrepro-002/filter/reference_score_retro_gate_d.json`.

Reference result: 50/50 passed, pass rate excluding skips 1.0.

Layer ceiling:

| layer | reference |
|---|---:|
| atomic | 25/25 passed |
| integration | 15/15 passed |
| system_e2e | 10/10 passed |

WSL reference attempts exist but are not used as the solvability ceiling: `reference_score_wsl_50.json` and `reference_score_wsl_50_pydeps.json` collected 0/50 because the WSL reference environment was missing dependencies such as `click`; `reference_score_wsl_50_pydeps2.json` reached only 26/50. These are treated as reference-environment failures, not oracle failures. The valid reference ceiling is the existing 50/50 dependency-complete reference run.

## Fairness Gates

### Gate A - Spec Mapping Spot-check

Passed. Sampled covered rows quote real candidate-visible spec headings and the tested behavior is derivable from those sections.

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `filter/generated_tests.py::test_build_api_writes_site_pages_and_search_assets` | Public build writes rendered pages and search assets into `site_dir`. | `Build API` | derivable |
| `filter/generated_tests.py::test_build_site_dir_override_keeps_config_and_output_consistent` | CLI/API output path override agrees with config and generated output. | `Cross-View Invariants` | derivable |
| `filter/generated_tests.py::test_validation_rejects_unknown_theme_name` | Invalid theme names are reported as handled configuration aborts. | `Exceptions and Error Semantics` | derivable |
| `filter/rewritten_upstream_tests.py::test_yaml_inherit_deep_merges_mappings_and_replaces_lists` | `INHERIT` loads parent config first, deep-merges mappings, and replaces lists. | `Configuration Loading` | derivable |
| `filter/rewritten_upstream_tests.py::test_file_directory_url_mapping` | Markdown files map to directory URLs and destination paths according to `use_directory_urls`. | `Source Files and Generated Files` | derivable |
| `filter/rewritten_upstream_tests.py::test_search_index_titles_mode_omits_section_entries` | Search indexing mode changes whether section entries or only page titles/text are included. | `Search` | derivable |

### Gate B - Failure Pattern Audit

Passed. The 12 candidate failures are public observable behavior gaps, not private structure checks. They cover package/CLI surface, strict and build-error behavior, repository/edit-link projections, theme validation, YAML inheritance, file discovery and URL mapping, template URL filters, search index output/modes, and metadata parsing.

The failing assertions do not require private modules, private attributes, exact object repr strings, hidden fixture objects, implementation call order, exact source layout, or exact internal exception message wording.

### Gate C - Generated-only Oracle Spot-check

Not formally applicable because `spec_test_map.md` declares `oracle_source: upstream_rewritten`, not `generated_only`. The 50-test oracle is mixed upstream-rewritten plus generated. As an extra audit, sampled generated rows were checked and found spec-driven and behavioral:

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `filter/generated_tests.py::test_public_package_exposes_version_and_cli_group` | Package exposes `mkdocs.__version__` and CLI group surface. | `Installable Surface` / `Public API` | derivable, behavioral |
| `filter/generated_tests.py::test_strict_build_aborts_on_warning` | Strict mode converts user-visible warnings into abort conditions. | `Error Semantics` | derivable, behavioral |
| `filter/generated_tests.py::test_plugin_lifecycle_events_run_during_build` | Public build invokes documented plugin lifecycle hooks. | `Plugins` | derivable, behavioral |
| `filter/generated_tests.py::test_repo_url_and_site_url_shape_page_edit_links` | Repository/site URL settings shape rendered page edit links. | `Cross-View Invariants` | derivable, behavioral |
| `filter/generated_tests.py::test_full_new_then_build_workflow` | `mkdocs new` followed by build creates a rendered site. | `Representative Workflow(s)` | derivable, behavioral |

### Gate D - Coverage Gap Audit

Passed with PARTIAL coverage. `kept_nodeids.txt` contains 50 non-empty nodeids, matching `oracle_count: 50` in `PIPELINE_STATE.md`. `spec_test_map.md` reports `Total: 50 | kept (covered): 50 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 50`.

| spec section | uncovered behaviors | impact | recommendation |
|---|---|---|---|
| `Product Overview` | No direct tests for narrative overview text. | Non-blocking; overview is descriptive rather than a testable contract. | No action. |
| `Scope` | No direct tests for boundary summary bullets. | Non-blocking; covered behaviors appear under concrete sections. | No action. |
| `Non-Goals` | No direct tests for exclusions. | Non-blocking; non-goals constrain verifier scope rather than define positive behavior. | No action. |
| `Evaluation Notes` | No direct tests for evaluation prose. | Non-blocking; this section describes verifier intent. | No action. |

Coverage verdict: PARTIAL. Core behavioral sections, including `Error Semantics`, `Cross-View Invariants`, `Build API`, `Search`, `Plugins`, `Configuration Loading`, and public file/page/navigation/theme utilities, have coverage.

## Candidate Score

Candidate score: 38/50 passed on Linux/WSL.

Layer breakdown:

| layer | candidate |
|---|---:|
| atomic | 20/25 passed |
| integration | 10/15 passed |
| system_e2e | 8/10 passed |

Failed tests:

- `filter/generated_tests.py::test_public_package_exposes_version_and_cli_group`
- `filter/generated_tests.py::test_strict_build_aborts_on_warning`
- `filter/generated_tests.py::test_plugin_build_error_hook_observes_build_failure`
- `filter/generated_tests.py::test_repo_url_and_site_url_shape_page_edit_links`
- `filter/generated_tests.py::test_validation_rejects_unknown_theme_name`
- `filter/rewritten_upstream_tests.py::test_yaml_inherit_deep_merges_mappings_and_replaces_lists`
- `filter/rewritten_upstream_tests.py::test_file_directory_url_mapping`
- `filter/rewritten_upstream_tests.py::test_get_files_prefers_index_over_readme`
- `filter/rewritten_upstream_tests.py::test_template_filters_normalize_urls_and_scripts`
- `filter/rewritten_upstream_tests.py::test_search_index_serializes_page_and_section_entries`
- `filter/rewritten_upstream_tests.py::test_search_index_titles_mode_omits_section_entries`
- `filter/rewritten_upstream_tests.py::test_meta_parser_extracts_yaml_and_multimarkdown_metadata`

## Failure Diagnosis

Root cause cluster 1: package and CLI installable surface gaps.

The candidate misses or mis-shapes parts of the public package/CLI surface exposed through `mkdocs.__version__`, `python -m mkdocs`, or the CLI group. Dimension: `api-surface`. Affected: 1 atomic failure.

Root cause cluster 2: error semantics and validation handling.

The candidate does not consistently turn strict warnings, plugin build errors, and invalid theme names into the documented user-facing abort/validation behavior. Dimension: `error-semantics`. Affected: 3 failures.

Root cause cluster 3: configuration and discovery state lifecycle.

YAML `INHERIT` path resolution/deep merge behavior and index-over-README file discovery diverge from the spec. Dimension: `state-management`. Affected: 2 integration failures.

Root cause cluster 4: URL, edit-link, and template projection consistency.

Directory URL mapping, repository/site URL edit-link output, and template `url` / `script_tag` filters do not share one coherent public URL model. Dimension: `cross-view-consistency`. Affected: 3 failures.

Root cause cluster 5: search index workflow completeness.

The search index public output and indexing modes are incomplete. Dimension: `workflow-completeness`. Affected: 1 system_e2e plus 1 integration failure.

Root cause cluster 6: metadata parser return contract.

`mkdocs.utils.meta.get_data()` does not match the documented stripped-Markdown plus parsed-metadata behavior. Dimension: `atomic-behavior`. Affected: 1 atomic failure.

## Cascade Analysis

The 12 failures reduce to six public behavior clusters rather than one setup/import cascade. The candidate still passes 38/50, so the score is discriminating: reference is at ceiling, the candidate imports from the submitted solution, and failures span separate public subsystems.

Task labels:

- `discriminating`: reference passes 50/50 while candidate misses 12 public behaviors.
- `multi-subsystem-signal`: failures span CLI/package surface, config, URL/template projections, search, error semantics, and metadata parsing.
- `low-cascade`: failures are not dominated by a single missing import or one broad environment failure.

## Final Action

Keep task status QUALIFIED using the legal WSL 50-test candidate score. Export terminal artifacts to `tasks/mkdocs-sitebuild-fullrepro-002`, with `score_result.json` copied from `score_result_wsl_50.json`, and append a CANDIDATES row documenting WSL rejudge 38/50 with reference 50/50.
