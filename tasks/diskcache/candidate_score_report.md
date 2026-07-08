# Stage 4 Score Report: diskcache spec_v3 run1

Run directory:
`/Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1`

## Inputs

- Source repo: `/Users/zijian/Bmk-dev-main/repo-pool/python-diskcache-master`
- Candidate solution: `/Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1/solution`
- Eval deps: `/Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v2-2026-07-03-run1/eval_deps`
- Full nodeids: `/Users/zijian/Bmk-dev-main/wip/diskcache/filter/kept_nodeids.txt` (148 nodeids)
- Non-Django nodeids: `/Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1/kept_nodeids_nondjango.txt` (100 nodeids)
- Taxonomy: `/Users/zijian/Bmk-dev-main/wip/diskcache/filter/taxonomy.jsonl`

## Import Provenance

Candidate import preflight:

```text
PYTHONPATH=/Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1/solution:/Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v2-2026-07-03-run1/eval_deps python -c "import diskcache, sys; print(diskcache.__file__); print(sys.path[:5])"

/Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1/solution/diskcache/__init__.py
['', '/Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1/solution', '/Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v2-2026-07-03-run1/eval_deps', ...]
```

Reference import preflight:

```text
PYTHONPATH=/Users/zijian/Bmk-dev-main/repo-pool/python-diskcache-master:/Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v2-2026-07-03-run1/eval_deps python -c "import diskcache, sys; print(diskcache.__file__); print(sys.path[:5])"

/Users/zijian/Bmk-dev-main/repo-pool/python-diskcache-master/diskcache/__init__.py
['', '/Users/zijian/Bmk-dev-main/repo-pool/python-diskcache-master', '/Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v2-2026-07-03-run1/eval_deps', ...]
```

Candidate scoring also used `--remove-path diskcache`, so the copied upstream worktree's original `diskcache` package was removed before pytest execution.

## Commands

Full reference:

```bash
PYTHONPATH=/Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v2-2026-07-03-run1/eval_deps python harness/score_pytest_original.py --source-repo /Users/zijian/Bmk-dev-main/repo-pool/python-diskcache-master --solution-dir /Users/zijian/Bmk-dev-main/repo-pool/python-diskcache-master --nodeids /Users/zijian/Bmk-dev-main/wip/diskcache/filter/kept_nodeids.txt --taxonomy /Users/zijian/Bmk-dev-main/wip/diskcache/filter/taxonomy.jsonl --run-dir /Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1/reference_output --json-out /Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1/reference_score_report.json --timeout 120 --pytest-arg=-o --pytest-arg=addopts=
```

Full candidate:

```bash
PYTHONPATH=/Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v2-2026-07-03-run1/eval_deps python harness/score_pytest_original.py --source-repo /Users/zijian/Bmk-dev-main/repo-pool/python-diskcache-master --solution-dir /Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1/solution --nodeids /Users/zijian/Bmk-dev-main/wip/diskcache/filter/kept_nodeids.txt --taxonomy /Users/zijian/Bmk-dev-main/wip/diskcache/filter/taxonomy.jsonl --run-dir /Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1/output --json-out /Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1/score_report.json --timeout 120 --pytest-arg=-o --pytest-arg=addopts= --remove-path diskcache
```

Generate non-Django nodeids:

```bash
rg -v '^tests/test_djangocache\.py::' /Users/zijian/Bmk-dev-main/wip/diskcache/filter/kept_nodeids.txt > /Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1/kept_nodeids_nondjango.txt
```

Non-Django reference:

```bash
PYTHONPATH=/Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v2-2026-07-03-run1/eval_deps python harness/score_pytest_original.py --source-repo /Users/zijian/Bmk-dev-main/repo-pool/python-diskcache-master --solution-dir /Users/zijian/Bmk-dev-main/repo-pool/python-diskcache-master --nodeids /Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1/kept_nodeids_nondjango.txt --taxonomy /Users/zijian/Bmk-dev-main/wip/diskcache/filter/taxonomy.jsonl --run-dir /Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1/reference_output_nondjango --json-out /Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1/reference_score_report_nondjango.json --timeout 120 --pytest-arg=-o --pytest-arg=addopts=
```

Non-Django candidate:

```bash
PYTHONPATH=/Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v2-2026-07-03-run1/eval_deps python harness/score_pytest_original.py --source-repo /Users/zijian/Bmk-dev-main/repo-pool/python-diskcache-master --solution-dir /Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1/solution --nodeids /Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1/kept_nodeids_nondjango.txt --taxonomy /Users/zijian/Bmk-dev-main/wip/diskcache/filter/taxonomy.jsonl --run-dir /Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1/output_nondjango --json-out /Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1/score_report_nondjango.json --timeout 120 --pytest-arg=-o --pytest-arg=addopts= --remove-path diskcache
```

## Full Scoring Summary

Reference report: `/Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1/reference_score_report.json`

```json
{
  "summary": {
    "passed": 148,
    "total": 148
  },
  "pass_rate_excluding_skips": 1.0,
  "by_layer": {
    "atomic": {
      "passed": 74,
      "total": 74
    },
    "integration": {
      "passed": 60,
      "total": 60
    },
    "system_e2e": {
      "passed": 14,
      "total": 14
    }
  }
}
```

Candidate report: `/Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1/score_report.json`

```json
{
  "summary": {
    "error": 48,
    "failed": 31,
    "passed": 69,
    "total": 148
  },
  "pass_rate_excluding_skips": 0.46621621621621623,
  "by_layer": {
    "atomic": {
      "error": 24,
      "failed": 8,
      "passed": 42,
      "total": 74
    },
    "integration": {
      "error": 24,
      "failed": 20,
      "passed": 16,
      "total": 60
    },
    "system_e2e": {
      "failed": 3,
      "passed": 11,
      "total": 14
    }
  }
}
```

Full candidate non-passed distribution by file:

- `tests/test_djangocache.py`: 48 error
- `tests/test_core.py`: 18 failed
- `tests/test_fanout.py`: 12 failed
- `tests/test_recipes.py`: 1 failed

## Non-Django Scoring Summary

Reference non-Django report: `/Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1/reference_score_report_nondjango.json`

```json
{
  "summary": {
    "passed": 100,
    "total": 100
  },
  "pass_rate_excluding_skips": 1.0,
  "by_layer": {
    "atomic": {
      "passed": 50,
      "total": 50
    },
    "integration": {
      "passed": 36,
      "total": 36
    },
    "system_e2e": {
      "passed": 14,
      "total": 14
    }
  }
}
```

Candidate non-Django report: `/Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1/score_report_nondjango.json`

```json
{
  "summary": {
    "failed": 31,
    "passed": 69,
    "total": 100
  },
  "pass_rate_excluding_skips": 0.69,
  "by_layer": {
    "atomic": {
      "failed": 8,
      "passed": 42,
      "total": 50
    },
    "integration": {
      "failed": 20,
      "passed": 16,
      "total": 36
    },
    "system_e2e": {
      "failed": 3,
      "passed": 11,
      "total": 14
    }
  }
}
```

Non-Django candidate non-passed distribution by file:

- `tests/test_core.py`: 18 failed
- `tests/test_fanout.py`: 12 failed
- `tests/test_recipes.py`: 1 failed

## Leakage and Provenance Note

- Candidate import provenance points to the spec_v3 cleanroom solution at `/Users/zijian/Bmk-dev-main/candidate-runs/codex-diskcache-spec_v3-2026-07-03-run1/solution/diskcache/__init__.py`.
- Candidate scoring used `--remove-path diskcache`, preventing accidental import from the copied source repo package.
- Reference scoring imported from `/Users/zijian/Bmk-dev-main/repo-pool/python-diskcache-master/diskcache/__init__.py`.
- No edits were made to `solution/` or `tasks/` during this Stage 4 scoring pass.

## Stage 5 Risks

- The reference oracle is healthy for both full and non-Django subsets: 148/148 full and 100/100 non-Django.
- Candidate has substantial real behavioral misses outside Django: 31 non-Django failures remain after excluding `tests/test_djangocache.py`.
- All 48 full-run errors are from `tests/test_djangocache.py`; first traceback shows `DjangoCache.__init__` calling Django `BaseCache.__init__` with an incompatible signature under the eval dependency version. Stage 5 should decide whether this reflects a candidate implementation miss, a spec coverage issue, or a Django-version fairness issue.
- Non-Django failures cluster in cache overwrite/read behavior, eviction/statistics/path behavior, FanoutCache settings/concurrency, and BoundedSemaphore release behavior.

Stage 4 status: ready for Stage 5 judging.
