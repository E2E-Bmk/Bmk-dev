# csvkit spec_v3 cleanroom score report

Run id: gpt-5.5-csvkit-spec_v2-20260702-run1

This report scores the existing cleanroom candidate solution against the Stage 3
v3 public black-box oracle. The candidate was not re-prompted and did not
receive the generated tests.

## Oracle

Primary artifacts:

- `wip/csvkit/spec/spec_v3.md`
- `wip/csvkit/filter/spec_test_map.md`
- `wip/csvkit/filter/kept_nodeids.txt`
- `wip/csvkit/filter/taxonomy.jsonl`
- `wip/csvkit/filter/public_tests/test_public_cli_blackbox.py`

The oracle remains `generated_only` and contains 45 public-surface tests:
36 atomic, 7 integration, and 2 system_e2e.

## Reference score

Command:

```text
LC_ALL=en_US.UTF-8 PYTHONPATH=/Users/zijian/Bmk-dev-main/candidate-runs/gpt-5.5-csvkit-spec_v2-20260702-run1/score_shims PYTEST_PLUGINS=pytest_jsonreport_compat /private/tmp/csvkit-score-venv/bin/python harness/score_pytest_original.py --source-repo repo-pool/csvkit-master --solution-dir repo-pool/csvkit-master --nodeids wip/csvkit/filter/kept_nodeids.txt --taxonomy wip/csvkit/filter/taxonomy.jsonl --run-dir candidate-runs/gpt-5.5-csvkit-spec_v2-20260702-run1/v3_reference_output --timeout 120 --json-out candidate-runs/gpt-5.5-csvkit-spec_v2-20260702-run1/v3_reference_score_report.json
```

Summary:

```json
{
  "summary": {
    "passed": 45,
    "total": 45
  },
  "pass_rate_excluding_skips": 1.0,
  "by_layer": {
    "atomic": {
      "passed": 36,
      "total": 36
    },
    "integration": {
      "passed": 7,
      "total": 7
    },
    "system_e2e": {
      "passed": 2,
      "total": 2
    }
  }
}
```

## Candidate score

Command:

```text
LC_ALL=en_US.UTF-8 PYTHONPATH=/Users/zijian/Bmk-dev-main/candidate-runs/gpt-5.5-csvkit-spec_v2-20260702-run1/score_shims PYTEST_PLUGINS=pytest_jsonreport_compat /private/tmp/csvkit-score-venv/bin/python harness/score_pytest_original.py --source-repo repo-pool/csvkit-master --solution-dir candidate-runs/gpt-5.5-csvkit-spec_v2-20260702-run1/solution --nodeids wip/csvkit/filter/kept_nodeids.txt --taxonomy wip/csvkit/filter/taxonomy.jsonl --run-dir candidate-runs/gpt-5.5-csvkit-spec_v2-20260702-run1/v3_output --remove-path csvkit --timeout 120 --json-out candidate-runs/gpt-5.5-csvkit-spec_v2-20260702-run1/v3_score_report.json
```

Summary:

```json
{
  "summary": {
    "failed": 4,
    "passed": 41,
    "total": 45
  },
  "pass_rate_excluding_skips": 0.9111111111111111,
  "by_layer": {
    "atomic": {
      "failed": 4,
      "passed": 32,
      "total": 36
    },
    "integration": {
      "passed": 7,
      "total": 7
    },
    "system_e2e": {
      "passed": 2,
      "total": 2
    }
  }
}
```

Failing v3 tests:

- `test_csvstat_json_reports_structured_statistics`
- `test_csvstat_csv_selected_column_outputs_csv_statistics`
- `test_csvclean_length_mismatch_reports_structured_stderr`
- `test_in2csv_converts_fixed_width_with_schema`

The two previously unfair failures, `test_csvcut_names_lists_positions` and
`test_csvsql_generates_create_table_statement`, pass after semantic assertion
correction.

## Notes for Stage 5

The v3 reference run passes at ceiling and the candidate run has no collection
errors. All remaining failures are atomic. Because the oracle is still
generated-only, Stage 5 must perform the generated-only spot check before
deciding whether these four failures are valid model weakness evidence.
