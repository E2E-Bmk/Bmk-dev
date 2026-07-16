# Stage 4 Score Report: rich spec_v1 run1

Run directory:
`/Users/zijian/bench/Bmk-dev/candidate-runs/codex-rich-spec_v1-2026-07-05-run1`

## Cleanroom Packet

- Candidate-visible spec: `public_packet/spec.md`
- Candidate solution: `solution/rich`
- Candidate-visible files: `public_packet/spec.md`, `task_prompt.txt`
- Excluded from candidate context: source repository, tests, filter maps, score reports, workflow skills, previous attempts, and the INTERNAL spec header.

Leakage keyword scan over the public packet, task prompt, and solution found no matches for internal workflow paths or artifact names such as `wip/rich`, `repo-pool`, `kept_nodeids`, `taxonomy`, `score_report`, `source_boundary`, or `INTERNAL`.

## Import Provenance

Candidate import preflight:

```text
PYTHONPATH=/Users/zijian/bench/Bmk-dev/candidate-runs/codex-rich-spec_v1-2026-07-05-run1/solution \
python -c "import rich, sys; print(rich.__file__); print(sys.path[:5])"

/Users/zijian/bench/Bmk-dev/candidate-runs/codex-rich-spec_v1-2026-07-05-run1/solution/rich/__init__.py
```

Reference import preflight:

```text
PYTHONPATH=/Users/zijian/bench/Bmk-dev/repo-pool/rich-main \
python -c "import rich, sys; print(rich.__file__); print(sys.path[:5])"

/Users/zijian/bench/Bmk-dev/repo-pool/rich-main/rich/__init__.py
```

The candidate scoring command used `--remove-path rich`, so the copied oracle worktree could not import the reference package.

## Commands

Reference:

```bash
PYTHONPATH=/Users/zijian/bench/Bmk-dev/candidate-runs/codex-rich-spec_v1-2026-07-05-run1/score_shims \
PYTEST_PLUGINS=pytest_jsonreport_compat \
python harness/score_pytest_original.py \
  --source-repo repo-pool/rich-main \
  --solution-dir repo-pool/rich-main \
  --nodeids wip/rich/filter/kept_nodeids.txt \
  --taxonomy wip/rich/filter/taxonomy.jsonl \
  --run-dir candidate-runs/codex-rich-spec_v1-2026-07-05-run1/reference_output \
  --remove-path rich \
  --timeout 180 \
  --json-out candidate-runs/codex-rich-spec_v1-2026-07-05-run1/reference_score_report.json
```

Candidate:

```bash
PYTHONPATH=/Users/zijian/bench/Bmk-dev/candidate-runs/codex-rich-spec_v1-2026-07-05-run1/score_shims \
PYTEST_PLUGINS=pytest_jsonreport_compat \
python harness/score_pytest_original.py \
  --source-repo repo-pool/rich-main \
  --solution-dir candidate-runs/codex-rich-spec_v1-2026-07-05-run1/solution \
  --nodeids wip/rich/filter/kept_nodeids.txt \
  --taxonomy wip/rich/filter/taxonomy.jsonl \
  --run-dir candidate-runs/codex-rich-spec_v1-2026-07-05-run1/output \
  --remove-path rich \
  --timeout 180 \
  --json-out candidate-runs/codex-rich-spec_v1-2026-07-05-run1/score_report.json
```

## Reference Summary

```json
{
  "summary": {
    "passed": 293,
    "total": 293
  },
  "pass_rate_excluding_skips": 1.0,
  "by_layer": {
    "atomic": {"passed": 200, "total": 200},
    "integration": {"passed": 87, "total": 87},
    "system_e2e": {"passed": 6, "total": 6}
  }
}
```

## Candidate Summary

```json
{
  "summary": {
    "collection_error": 16,
    "failed": 109,
    "not_collected": 125,
    "passed": 29,
    "total": 279
  },
  "pass_rate_excluding_skips": 0.1039426523297491,
  "by_layer": {
    "atomic": {"failed": 75, "not_collected": 86, "passed": 9, "total": 170},
    "integration": {"failed": 32, "not_collected": 38, "passed": 17, "total": 87},
    "system_e2e": {"failed": 2, "not_collected": 1, "passed": 3, "total": 6},
    "unknown": {"collection_error": 16, "total": 16}
  }
}
```

The reference oracle contains 293 scoreable nodeids. The candidate raw report totals 279 because module-level collection errors in the offline json-report shim compress part of the parametrized collection surface into file-level collection-error records. The raw candidate pass count is 29.

## Collection Error Distribution

- 2 files: missing import `RenderableType` from `rich.console`
- 1 file each: missing import `VerticalCenter` from `rich.align`, `ProgressBar` from `rich.progress_bar`, `blend_rgb` from `rich.color`, `escape_control_codes` from `rich.control`, `Emoji` from `rich.emoji`, `measure_renderables` from `rich.measure`, `ConsoleDimensions` from `rich.console`, `ColorSystem` from `rich.color`, `ThemeStack` from `rich.theme`
- 1 file each: missing module `rich.containers`, `rich.abc`, `rich.cells`
- 1 file: `Console.__init__()` does not accept `_environ`
- 1 file: `rich.box` lacks `HEAVY_HEAD`

## Failure Surface

Largest failed-test clusters:

- `tests/test_text.py`: 58 failures
- `tests/test_live.py`: 10 failures
- `tests/test_rule.py`: 8 failures
- `tests/test_traceback.py`: 7 failures
- `tests/test_tree.py`: 7 failures
- `tests/test_spinner.py`: 5 failures
- `tests/test_rule_in_table.py`: 4 failures
- `tests/test_jupyter.py`: 3 failures

Not-collected clusters mostly follow from module-level import failures or missing public helper modules in the candidate implementation.

Stage 4 status: ready for Stage 5 judging.
