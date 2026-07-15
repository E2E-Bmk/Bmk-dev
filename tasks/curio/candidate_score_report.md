# Curio Stage 4 Score Report

- Run ID: `curio-stage4-20260714-212427-60032`
- Result: **58 passed, 4 failed, denominator 62**
- Score: **93.54838709677419%**
- Frozen nodeid verification: 62 rows, 62 unique nodeids, exact set and order match `filter/kept_nodeids.txt`.

## Per-layer result

| Layer | Passed | Failed | Denominator |
|---|---:|---:|---:|
| atomic | 25 | 1 | 26 |
| integration | 20 | 3 | 23 |
| system_e2e | 13 | 0 | 13 |

## Failures

- `generated_tests.py::test_blocking_cancel_terminates_task_and_marks_cancelled` - exceeded the 15-second per-test limit.
- `generated_tests.py::test_taskgroup_cancel_remaining_terminates_non_daemons` - exceeded the 15-second per-test limit.
- `generated_tests.py::test_timeout_after_raises_task_timeout_when_blocking_operation_expires` - raised `TaskCancelled` instead of `TaskTimeout`.
- `generated_tests.py::test_timeout_escaping_matching_boundary_raises_uncaught_timeout` - raised `TaskCancelled` instead of `UncaughtTimeoutError`.

## Evidence and command

The authoritative per-test machine-readable record is `raw/per_test_status.tsv`. The 60 completed pytest invocations emitted JUnit XML under `raw/per_test/`; the two GNU `timeout` exits are recorded with exit code 124 in the TSV and have empty raw logs. `raw/per_test_command_template.txt` records the exact command template, and every frozen nodeid is recorded verbatim in the status table. `raw/eval_command.txt` and `raw/batch_attempt_*` preserve the initial batch attempt, which was stopped after candidate behavior blocked progress and was excluded from scoring.

Each scoring invocation used Docker image `curio-stage4-20260714-212427-60032-pytest` (`sha256:931058522d4933140dd3e73a3a4dd7485bc7cec5cc476d467bca72f9a936ac67`), with `--network none --read-only`, candidate mounted read-only at `/candidate`, oracle mounted read-only at `/oracle`, working directory `/oracle`, `PYTHONPATH=/candidate`, and `PYTHONNOUSERSITE=1`. The only package added to the base image was pytest and its dependencies; curio was never installed.

## Anomaly and saturation analysis

The initial all-nodeid pytest process emitted 12 progress marks and then stalled for more than two minutes. This is consistent with the two cancellation tests that independently hit the 15-second limit. Per-test isolation prevented one hang from hiding later outcomes. No native macOS score was read. The 93.55% outcome is high but not saturated: failures span cancellation liveness and timeout exception semantics, while all 13 system-level tests pass. Stage 4 records these observations without making a Stage 5 quality verdict.
