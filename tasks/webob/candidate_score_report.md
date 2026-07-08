# Stage 4 Rerun Score Report: webob filter_v2

This report records the downstream evaluation after the Stage 3 fairness repair requested by `wip/webob/filter/filter_correction_request.md`.

## Cleanroom packet

Candidate run directory:

`/Users/zijian/Bmk-dev-main/candidate-runs/codex-webob-spec_v1-2026-07-05-run1`

The candidate implementation was not regenerated for this rerun. Scoring reused the existing cleanroom solution and only changed the oracle inputs:

- `/Users/zijian/Bmk-dev-main/wip/webob/filter/kept_nodeids.txt`
- `/Users/zijian/Bmk-dev-main/wip/webob/filter/taxonomy.jsonl`

The candidate-visible packet remained limited to:

- `public_packet/spec.md`
- `task_prompt.txt`

## Preflight output

Candidate import:

```text
/Users/zijian/Bmk-dev-main/candidate-runs/codex-webob-spec_v1-2026-07-05-run1/solution/webob/__init__.py
['', '/Users/zijian/Bmk-dev-main/candidate-runs/codex-webob-spec_v1-2026-07-05-run1/solution', '/opt/anaconda3/lib/python313.zip', '/opt/anaconda3/lib/python3.13', '/opt/anaconda3/lib/python3.13/lib-dynload']
```

Reference import:

```text
/Users/zijian/Bmk-dev-main/repo-pool/webob-main/src/webob/__init__.py
['', '/Users/zijian/Bmk-dev-main/repo-pool/webob-main/src', '/opt/anaconda3/lib/python313.zip', '/opt/anaconda3/lib/python3.13', '/opt/anaconda3/lib/python3.13/lib-dynload']
```

## Stage 3 repaired oracle

- Total collected upstream nodeids: 2299
- Covered/kept/final scoreable: 68
- Spec gaps: 0
- Source-only: 190
- Excluded: 2041
- Layers: atomic 31, integration 24, system_e2e 13
- Track B triggered: false

Main-thread validation:

- `kept_nodeids.txt` lines: 68
- `taxonomy.jsonl` lines: 68
- Covered rows with invalid spec sections: 0
- Kept carrier hits for `text_`, `_item_n_weight_re`, `environ_from_url`, `_is_content_range_valid`, `Transcoder`, or `test_serialize_date`: 0

Reference gate:

```text
68 passed in 0.03s
```

## Reference scorer rerun

Command:

```text
/Users/zijian/Bmk-dev-main/candidate-runs/codex-webob-spec_v1-2026-07-05-run1/eval_venv/bin/python /Users/zijian/Bmk-dev-main/harness/score_pytest_original.py --source-repo /Users/zijian/Bmk-dev-main/repo-pool/webob-main --solution-dir /Users/zijian/Bmk-dev-main/repo-pool/webob-main/src --nodeids /Users/zijian/Bmk-dev-main/wip/webob/filter/kept_nodeids.txt --taxonomy /Users/zijian/Bmk-dev-main/wip/webob/filter/taxonomy.jsonl --run-dir /Users/zijian/Bmk-dev-main/candidate-runs/codex-webob-spec_v1-2026-07-05-run1/reference_output_filter_v2 --json-out /Users/zijian/Bmk-dev-main/candidate-runs/codex-webob-spec_v1-2026-07-05-run1/reference_score_report_filter_v2.json --timeout 120 --pytest-arg=-o --pytest-arg=addopts=
```

Result:

```json
{
  "summary": {
    "passed": 68,
    "total": 68
  },
  "pass_rate_excluding_skips": 1.0,
  "by_layer": {
    "atomic": {
      "passed": 31,
      "total": 31
    },
    "integration": {
      "passed": 24,
      "total": 24
    },
    "system_e2e": {
      "passed": 13,
      "total": 13
    }
  }
}
```

## Candidate scorer rerun

Command:

```text
/Users/zijian/Bmk-dev-main/candidate-runs/codex-webob-spec_v1-2026-07-05-run1/eval_venv/bin/python /Users/zijian/Bmk-dev-main/harness/score_pytest_original.py --source-repo /Users/zijian/Bmk-dev-main/repo-pool/webob-main --solution-dir /Users/zijian/Bmk-dev-main/candidate-runs/codex-webob-spec_v1-2026-07-05-run1/solution --nodeids /Users/zijian/Bmk-dev-main/wip/webob/filter/kept_nodeids.txt --taxonomy /Users/zijian/Bmk-dev-main/wip/webob/filter/taxonomy.jsonl --run-dir /Users/zijian/Bmk-dev-main/candidate-runs/codex-webob-spec_v1-2026-07-05-run1/output_filter_v2 --json-out /Users/zijian/Bmk-dev-main/candidate-runs/codex-webob-spec_v1-2026-07-05-run1/score_report_filter_v2.json --timeout 120 --pytest-arg=-o --pytest-arg=addopts= --remove-path src/webob
```

Result:

```json
{
  "summary": {
    "failed": 42,
    "passed": 26,
    "total": 68
  },
  "pass_rate_excluding_skips": 0.38235294117647056,
  "by_layer": {
    "atomic": {
      "failed": 16,
      "passed": 15,
      "total": 31
    },
    "integration": {
      "failed": 14,
      "passed": 10,
      "total": 24
    },
    "system_e2e": {
      "failed": 12,
      "passed": 1,
      "total": 13
    }
  }
}
```

Outcome distribution:

- Reference: 68 passed, 0 failed, 0 collection_error
- Candidate: 26 passed, 42 failed, 0 collection_error

Candidate failures by file:

- `tests/test_cachecontrol.py`: 2 passed, 3 failed
- `tests/test_client.py`: 2 passed, 11 failed
- `tests/test_datetime_utils.py`: 7 passed, 3 failed
- `tests/test_etag.py`: 6 passed, 1 failed
- `tests/test_exc.py`: 5 passed, 16 failed
- `tests/test_headers.py`: 4 passed, 8 failed

## Stage 4 rerun status

Ready for Stage 5 judging. The previous collection-error fairness failure appears repaired for this rerun because the candidate score contains no collection errors and the reference scorer passes 68/68.

Residual risk: the conservative repair reduced the oracle from 1040 to 68 nodeids. The repaired oracle remains above the 30-node minimum and has nonzero atomic, integration, and system_e2e coverage, but the judge should decide whether coverage loss warrants Track B or upstream test rewrites before qualification.
