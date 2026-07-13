# Stage 5 Judge Diagnosis - dateparser-dates-fullrepro-001

Verdict: QUALIFIED
Date: 2026-07-04
Candidate run: candidate-runs/codex-dateparser-specv1-20260704-001
Score artifact used: candidate-runs/codex-dateparser-specv1-20260704-001/score_retry_specv2/score_result.json
Spec/oracle version: spec_v2 / oracle_version 20260704T112154Z

## Anti-Cheat Preflight

Command:

```powershell
$env:PYTHONPATH="G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-dateparser-specv1-20260704-001\output"; python -c "import dateparser; print(dateparser.__file__)"
```

Preflight output:

```text
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-dateparser-specv1-20260704-001\output\dateparser\__init__.py
```

The import provenance points to the candidate solution, specifically `candidate-runs/codex-dateparser-specv1-20260704-001/output/dateparser/__init__.py`.

I scanned the available implementation-phase artifacts (`task_prompt.txt` and `output/dateparser`) for forbidden access markers: `repo-pool`, `oracle_worktree`, `reference`, `kept_nodeids`, `spec_test_map`, `score_result`, `pytest_report`, direct target-package installation, and generated test paths. No forbidden access was found in those artifacts. A full command trajectory log was not present in the candidate-run directory, so the anti-cheat conclusion is based on available prompt/solution artifacts plus the import-provenance preflight.

## Hard Checks

| check | evidence | verdict |
|---|---|---|
| Pipeline state | `wip/dateparser-dates-fullrepro-001/PIPELINE_STATE.md` was in `S5_JUDGE`. | pass |
| Score platform | Score platform is `Linux-5.15.153.1-microsoft-standard-WSL2-x86_64-with-glibc2.31`. | pass |
| Score isolation | `remove_paths` is `["dateparser"]`; `solution_dir` is the candidate output directory. | pass |
| Candidate score | `60/72` passed, `12/72` failed, `72` collected. | pass |
| Reference gate | `wip/dateparser-dates-fullrepro-001/filter/reference_score.json` shows WSL/Linux, `remove_paths=["dateparser"]`, reference `72/72` passed, `72` collected. | pass |
| Oracle source | `spec_test_map.md` header says `filter/oracle_source: generated_only`. | pass |

## Score By Layer

| layer | passed | failed | total |
|---|---:|---:|---:|
| atomic | 49 | 6 | 55 |
| integration | 6 | 6 | 12 |
| system_e2e | 5 | 0 | 5 |
| total | 60 | 12 | 72 |

## Gate C - Generated-Only Oracle Spot-Check

Sampled generated tests are public-behavior assertions against `parse`, `DateDataParser`, `search_dates`, settings validation, and cross-view consistency. They do not require private modules, private field names, repr strings, or exact provider-specific timezone classes.

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| tests/test_swe_e2e_dateparser_generated.py::test_parse_no_spaces_time_when_parser_enabled | With `PARSERS=["no-spaces-time"]`, compact input `"121994"` parses as `datetime(1994, 1, 2)`. | `### Parser Selection, Formats, and Normalization` | derivable + behavioral |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_input_timezone_converts_to_target_zone_with_tzinfo | Timezone-bearing UTC input with `TO_TIMEZONE="US/Eastern"` converts to 17:00, remains timezone-aware, and has UTC-5 offset. | `### Timezone Behavior` | derivable + behavioral |
| tests/test_swe_e2e_dateparser_generated.py::test_search_dates_return_time_span_for_past_week_default_monday | `"past week"` under fixed base returns the completed prior Monday-Sunday span and preserves base time-of-day. | `### Search Time Spans` | derivable + behavioral |
| tests/test_swe_e2e_dateparser_generated.py::test_search_dates_return_time_span_respects_sunday_week_start | With `DEFAULT_START_OF_WEEK="sunday"`, `"past week"` returns the completed prior Sunday-Saturday span and preserves base time-of-day. | `### Search Time Spans` | derivable + behavioral |
| tests/test_swe_e2e_dateparser_generated.py::test_search_dates_extracts_multiple_dates_in_order | `search_dates` returns ordered parsed datetimes for two English date expressions; returned match text must parse back to the same datetimes. | '### `search_dates`' / '## Cross-View Invariants' | derivable + behavioral |
| tests/test_swe_e2e_dateparser_generated.py::test_search_dates_languages_argument_prevents_detector_call | Explicit `languages=["es"]` searches Spanish and does not invoke the supplied detector. | '### `search_dates`' | derivable + behavioral |
| tests/test_swe_e2e_dateparser_generated.py::test_unknown_parser_name_raises_setting_validation_error | Unknown `PARSERS` entry raises `SettingValidationError`. | `### Parser Selection, Formats, and Normalization` / `## Error Semantics` | derivable + behavioral |

Focused re-check of prior problem areas:

- `no-spaces-time`: fixed in spec_v2 with explicit compact-digit behavior and example `"121994" -> datetime(1994, 1, 2)`.
- `TO_TIMEZONE` / `tzinfo`: fixed in spec_v2 by requiring timezone-aware converted results for timezone-bearing input while avoiding provider-specific timezone object shape.
- `past week` span: fixed in spec_v2 by defining completed prior week boundaries, Monday/Sunday week starts, and preservation of `RELATIVE_BASE` time-of-day.

Caveat: `test_search_dates_custom_language_detector` also asserts the observed default detector kwarg `confidence_threshold == 0.5`; spec_v2 says the detector is called with `text` and `confidence_threshold` but does not separately spell out the numeric default. This assertion is low-risk because the candidate failure in this test is returning `None` for the public Spanish search result, not a threshold-only mismatch, and the behavior is reference-passing. Future spec cleanup could make the default threshold explicit.

Gate C verdict: pass.

## Gate D - Coverage Gap Audit

The map covers every core behavioral section used by the generated oracle:

| spec section | covered rows | uncovered behaviors | impact | recommendation |
|---|---:|---|---|---|
| '### `parse`' | 6 | none observed | none | keep |
| '### `DateData` and `DateDataParser`' | 9 | none observed | none | keep |
| '### `search_dates`' | 7 | none observed | none | keep |
| `### Date Order and Language Order` | 5 | none observed | none | keep |
| `### Incomplete and Relative Dates` | 16 | none observed | none | keep |
| `### Parser Selection, Formats, and Normalization` | 4 | none observed | none | keep |
| `### Timezone Behavior` | 5 | none observed | none | keep |
| `### Search Time Spans` | 3 | none observed | none | keep |
| `## Error Semantics` | 12 | none observed | none | keep |
| `## Cross-View Invariants` | 5 | none observed | none | keep |

Meta/non-behavioral headings such as Product Overview, Scope, Non-Goals, Invocation Protocol, and Evaluation Notes are not expected to have direct scoring rows. Representative workflow headings are covered through the public API and cross-view tests rather than as separate tutorial examples.

Coverage verdict: FULL for behavioral/core sections; no core invariant or error-semantics gap.

## Failure Review

All 12 candidate failures are valid model failures against public, spec-driven behavior. No failing test requires private implementation shape.

| cluster | failed tests | layer | root cause | dimension | verdict |
|---|---:|---|---|---|---|
| Incomplete month names | 3 | atomic | Candidate returns `None` for month-only inputs such as `"March"`/`"August"` instead of resolving missing year/day from `RELATIVE_BASE` and `PREFER_DATES_FROM`. | atomic-behavior | valid model failure |
| Compact no-spaces parser | 1 | atomic | Candidate does not implement explicitly selected `"no-spaces-time"` compact digit parsing. | atomic-behavior | valid model failure |
| Timezone-aware target conversion | 1 | atomic | Candidate converts wall time for timezone-bearing input but drops `tzinfo` despite `TO_TIMEZONE`. | atomic-behavior | valid model failure |
| Spanish and multi-date search | 4 | integration | Candidate `search_dates` misses Spanish date expressions and a multi-date English prose extraction. | workflow-completeness | valid model failure |
| Past-week span boundaries | 2 | integration | Candidate implements partly rolling/date-normalized spans rather than completed prior week spans preserving base time-of-day. | atomic-behavior | valid model failure |
| Parser setting validation | 1 | atomic | Candidate accepts an unknown parser name instead of raising `SettingValidationError`. | error-semantics | valid model failure |

Cascade analysis: 12 failures reduce to 6 root behavior gaps. The integration failures are mostly search workflow completeness and span semantics, not internal-shape verifier issues. The 5/5 system_e2e pass rate suggests no observed cross-view consistency regression in the scored set.

## Protocol Issues

No blocking verifier/spec issue found. No `filter_correction_request.md` or `spec_patch_request.md` is required for this verdict.

## Labels

- `generated-only-oracle`
- `discriminating`
- `valid-model-failures`
- `atomic-and-search-workflow-signal`

## Final Verdict

QUALIFIED. The run satisfies anti-cheat provenance, WSL/Linux isolated scoring, reference solvability, generated-only fairness spot-check, and behavioral coverage requirements. The candidate score is accepted as `60/72`.
