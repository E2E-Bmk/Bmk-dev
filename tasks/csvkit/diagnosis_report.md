# csvkit Stage 5 task-judge diagnosis report

Current artifact: spec_v3 rerun / current verdict for `gpt-5.5-csvkit-spec_v2-20260702-run1`.

## Hard-check order

I read `/Users/zijian/Bmk-dev-main/skills/task-judge/SKILL.md` first and ran the import provenance preflight before opening or quoting any score file.

## Preflight output

```text
/Users/zijian/Bmk-dev-main/candidate-runs/gpt-5.5-csvkit-spec_v2-20260702-run1/solution/csvkit/__init__.py
```

The imported `csvkit` package resolves inside the candidate solution directory:
`/Users/zijian/Bmk-dev-main/candidate-runs/gpt-5.5-csvkit-spec_v2-20260702-run1/solution`.

## Anti-cheat scan result

Status: PASS, no `CHEAT_DETECTED` on the available audit record.

Evidence reviewed:

- `cleanroom_manifest.json` says the only candidate-visible files were `public_packet/spec.md` and `task_prompt.txt`.
- `task_prompt.txt` explicitly prohibited inspecting parent directories, source, tests, scores, workflow files, and previous attempts.
- `candidate_final.txt` reports only the cleanroom implementation path and smoke-check summary.
- A text scan across `candidate_final.txt`, `task_prompt.txt`, `cleanroom_manifest.json`, and the candidate `solution` found no implementation-phase references to forbidden scoring artifacts such as `spec_test_map`, `kept_nodeids`, public tests, score reports, pytest reports, reference outputs, or `repo-pool` source access. The only `repo-pool`-adjacent hit was the manifest's policy sentence naming excluded categories, not candidate access.
- The preflight import path is candidate-local, not `repo-pool`, reference output, or an installed package.

Limit note: I did not find a full interactive trajectory transcript in the run directory. The available manifest/final/prompt/solution evidence supports accepting the run as clean for Stage 5.

## Solvability / reference result

Status: PASS.

Reference run:

- Score: 45 passed / 45 total.
- Pass rate excluding skips: 1.0.
- By layer: atomic 36/36, integration 7/7, system_e2e 2/2.
- Environment notes: the v3 reference score used `/private/tmp/csvkit-score-venv/bin/python`, `PYTEST_PLUGINS=pytest_jsonreport_compat`, `PYTHONPATH` pointed at `score_shims`, and the source/solution were both `repo-pool/csvkit-master`. The report had no collection errors; only a harmless unknown pytest mark warning appeared.

The oracle ceiling is therefore high enough for QUALIFIED consideration.

## Candidate score by layer

Candidate run:

- Overall: 41 passed / 45 total, pass rate excluding skips 0.9111111111111111.
- Atomic: 32 passed / 36 total, 4 failed.
- Integration: 7 passed / 7 total.
- System E2E: 2 passed / 2 total.

Failing tests:

- `test_csvstat_json_reports_structured_statistics`
- `test_csvstat_csv_selected_column_outputs_csv_statistics`
- `test_csvclean_length_mismatch_reports_structured_stderr`
- `test_in2csv_converts_fixed_width_with_schema`

## Fairness Gate A - spec mapping spot-check

Status: PASS.

Sampled covered rows from `spec_test_map.md`:

- `test_csvcut_selects_named_columns_in_requested_order` maps to `### csvcut`. The section states `csvcut` selects, excludes, reorders, and truncates columns and `--columns` selects columns by name, position, or range. A senior engineer can derive the requested-order CSV output from the spec.
- `test_csvcut_no_header_row_uses_generated_headers` maps to `### Common CSV Input Behavior`. The section states `--no-header-row` creates default headers `a`, `b`, `c`, and so on. The assertion checks observable projection by generated names.
- `test_csvjoin_left_join_preserves_left_rows` maps to `### csvjoin`. The section states `--left` selects left outer joins. The expected left-preserved row with a blank unmatched right value is public table behavior.
- `test_csvjson_lat_lon_outputs_geojson` maps to `### csvjson`. The section states `--lat` and `--lon` switch output to GeoJSON and selected lat/lon form point coordinates. The assertion checks public JSON fields.
- `test_csvstat_csv_selected_column_outputs_csv_statistics` maps to `### csvstat`. spec_v3 explicitly defines `--csv` field names and selected-column ordering; the test uses those documented fields.
- `test_pipeline_cut_grep_then_json_preserves_filtered_table` maps to `## Cross-View Invariants`. It checks a public pipeline over stdout/stdin, consistent with the invariant that csvkit command output remains readable by downstream csvkit commands.

No incorrect mapping found in this sample.

## Fairness Gate B - failure pattern audit

Status: PASS.

The four candidate failures are all public-surface atomic behaviors. They do not assert private helper classes, internal field names, repr strings, or exact incidental error wording.

- `csvstat --json`: spec_v3 says JSON output is an array of per-column objects using documented fields including `column_id` and `column_name`. Candidate returned a JSON object keyed by column name, so the failure is a documented output-shape mismatch.
- `csvstat --csv`: spec_v3 says CSV output has documented header fields including `column_name`. Candidate emitted `column` instead. This is a public structured-output contract, not an internal name.
- `csvclean --length-mismatch`: spec_v3 says check-only mode writes the input header and all data rows to stdout, even when a long row has more fields than the header; candidate truncated the long row. The assertion checks stdout data behavior plus nonzero status/stderr category.
- `in2csv --format fixed --schema`: spec_v3 says schema `start` values are interpreted as one-based when the first schema row has start `1`; candidate treated starts as zero-based, shifting slices. The assertion checks observable converted CSV.

No fairness correction is required for the current v3 scoring set.

## Fairness Gate C - generated-only oracle spot-check

Status: PASS. `spec_test_map.md` header is `oracle_source: generated_only`, so I manually spot-checked generated tests against the two core principles.

1. `test_top_level_reader_writer_aliases_roundtrip`
   - Spec-driven: yes, `## Public API` documents top-level `reader` and `writer` aliases.
   - Behavioral: yes, it checks public round-trip CSV rows through the documented aliases.

2. `test_csvcut_names_lists_positions`
   - Spec-driven: yes, `### Column Identification` says `--names` prints available column names and positions with active numbering.
   - Behavioral: yes, it parses semantic position/name pairs and does not require exact padding or message wording.

3. `test_csvjson_key_writes_object_keyed_by_column`
   - Spec-driven: yes, `### csvjson` says `--key` writes an object keyed by the selected column and key values must be unique.
   - Behavioral: yes, it checks public JSON output after type inference; no implementation internals are inspected.

4. `test_csvstat_json_reports_structured_statistics`
   - Spec-driven: yes, spec_v3 explicitly defines JSON as an array of per-column objects with field names and statistic values.
   - Behavioral: yes, it reads stdout JSON and checks documented fields/values only.

5. `test_csvclean_length_mismatch_reports_structured_stderr`
   - Spec-driven: yes, spec_v3 explicitly defines check-only stdout preservation of long rows, stderr CSV error rows, and exit status 1 when errors are found.
   - Behavioral: yes, it checks exit status plus stdout/stderr streams, not exact prose wording.

6. `test_in2csv_converts_fixed_width_with_schema`
   - Spec-driven: yes, spec_v3 defines fixed-width schema columns `column`, `start`, `length`, one-based detection when first start is `1`, and stripping.
   - Behavioral: yes, it invokes the public CLI and compares converted CSV cells.

7. `test_csvsql_insert_then_sql2csv_query_roundtrip`
   - Spec-driven: yes, `## Representative Workflows` documents loading CSV into SQLite with `csvsql --db ... --insert` and querying via `sql2csv`.
   - Behavioral: yes, it validates an observable database workflow through documented commands.

The generated tests sampled are acceptable as scoring tests.

## Protocol issues / actions

Current v3 protocol status: no blocking protocol issue.

Actions taken in this judgment:

- Accepted the v3 scoring set as fair and solvable.
- Did not write a new `spec_patch_request.md`.
- Did not write a new `filter_correction_request.md`.
- Existing request files under `wip/csvkit/spec/` or `wip/csvkit/filter/`, if present from prior stages, were not modified by this Stage 5 verdict.

Historical note: v3 appears to have corrected prior unfairness around `csvcut --names` formatting and `csvsql` quoting; both now pass in the candidate run and are no longer current blockers.

## Real failure clusters

### Cluster 1 - csvstat structured output shape

- Affected tests: 2 atomic.
- Tests:
  - `test_csvstat_json_reports_structured_statistics`
  - `test_csvstat_csv_selected_column_outputs_csv_statistics`
- Root cause: candidate implemented `csvstat` structured output as a simpler column-keyed object for JSON and `column`-headed table for CSV, rather than spec_v3's row/object-per-column format with `column_id`, `column_name`, `type`, `nulls`, `nonnulls`, `unique`, and statistic fields.
- Capability dimension: `atomic-behavior`.
- Model issue vs protocol issue: real model failure. The spec explicitly documents the structured field names.

### Cluster 2 - csvclean check-only long-row preservation

- Affected tests: 1 atomic.
- Test: `test_csvclean_length_mismatch_reports_structured_stderr`.
- Root cause: candidate always truncates cleaned rows to header width (`nr = nr[: len(header)]`) even in check-only mode. spec_v3 says check-only stdout preserves all data rows and long rows with extra fields unless a fix option changes them.
- Capability dimension: `atomic-behavior`.
- Model issue vs protocol issue: real model failure. The stdout preservation rule is explicit in spec_v3.

### Cluster 3 - in2csv fixed-width schema indexing

- Affected tests: 1 atomic.
- Test: `test_in2csv_converts_fixed_width_with_schema`.
- Root cause: candidate uses schema `start` values directly as Python zero-based slices. spec_v3 says if the first schema row start is `1`, all starts are one-based, so the implementation must subtract 1 before slicing.
- Capability dimension: `atomic-behavior`.
- Model issue vs protocol issue: real model failure. The start/length semantics are explicit in spec_v3.

## Cascade analysis

There are 4 failing tests rooted in 3 independent atomic root causes.

- The two `csvstat` failures are a single root cause: missing spec_v3 structured output contract.
- `csvclean` and `in2csv fixed` are independent primitive behavior gaps.
- No integration or system_e2e failures remain, so there is no evidence of composition breakdown or cross-component state drift in this run.
- The score is not cascade-dominated at higher layers; the residual failures are localized atomic omissions.

## Suggested weakness_table candidate rows

Do not write these yet; include them for main-thread review because the final status is QUALIFIED.

```markdown
| model | task | dimension | description | affected_tests |
|-------|------|-----------|-------------|----------------|
| gpt-5.5 | csvkit | atomic-behavior | Implemented csvstat JSON/CSV structured output with non-spec column-keyed/header shape instead of documented per-column objects/rows and field names | 2 atomic |
| gpt-5.5 | csvkit | atomic-behavior | csvclean length-mismatch check-only mode truncated long rows on stdout instead of preserving original ragged data rows while reporting errors | 1 atomic |
| gpt-5.5 | csvkit | atomic-behavior | in2csv fixed-width schema treated one-based start offsets as zero-based slices, shifting extracted cells | 1 atomic |
```

## Task labels

- `qualified`
- `discriminating`
- `public-cli-blackbox`
- `generated-only-validated`
- `atomic-behavior-signal`
- `not-cascade-dominated`

## Final status

QUALIFIED.

Rationale: anti-cheat provenance and available audit evidence pass, reference passes 45/45 in the scoring environment, the generated-only oracle passes manual fairness spot-checks, and the candidate failures are valid public behavioral gaps rather than verifier failures.
