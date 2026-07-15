# Curio Stage 5 Independent Diagnosis Report

## Verdict

- **Task status: `QUALIFIED`**
- **Evaluation run:** `curio-stage4-20260714-212427-60032`
- **Candidate result:** 58/62, 93.548387%; not fully saturated
- **Labels:** `generated-only`, `discriminating`, `cancellation-liveness`, `timeout-error-semantics`, `not-saturated`
- **Route:** `S5_JUDGE -> QUALIFIED`

Anti-Cheat, Solvability, and Fairness Gates A-D all pass. All four candidate failures are directly predictable from the public specification, and they check public exceptions, termination state, and blocking/completion effects rather than internal shapes. No verifier, specification, or environment issue was found.

## 1. Anti-Cheat and Import-Source Preflight

The Judge reran the candidate import-source preflight before reading any Stage 4 score file. Because the Judge subagent had no access to the Docker socket, the main-thread orchestrator executed the command on its behalf; the command exited with code `0`.

Exact command:

```sh
docker run --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m --mount type=bind,src=/Users/zijian/bench/Bmk-dev/candidate-runs/curio-stage4-20260714-212427-60032/output,dst=/candidate,readonly --workdir /candidate --env PYTHONPATH=/candidate --env PYTHONNOUSERSITE=1 curio-stage4-20260714-212427-60032-pytest python -c 'import platform,sys,curio,pytest; print("platform="+platform.platform()); print("sys_platform="+sys.platform); print("python="+sys.version.replace("\\n"," ")); print("curio_file="+curio.__file__); print("pytest="+pytest.__version__)'
```

### Preflight output

```text
platform=Linux-6.12.76-linuxkit-aarch64-with-glibc2.41
sys_platform=linux
python=3.11.15 (main, Jul 14 2026, 02:16:19) [GCC 14.2.0]
curio_file=/candidate/curio/__init__.py
pytest=9.1.1
```

The literal preflight path points to the candidate output, not the reference, oracle worktree, or a system-installed package.

The candidate CLI thread was `019f6039-95d5-72a0-87b9-3de10111516b`. Events recovered from the parent rollout run continuously from `item_0` through `item_19` and end with `turn.completed`: the candidate used only two `sed` commands to read `SPEC.md`, made exactly five invocations of `PYTHONPATH=output python output/self_check.py`, and changed only `output/curio/__init__.py` and `output/self_check.py`. Command and path metadata contain no `repo-pool/`, tests, `kept_nodeids.txt`, `spec_test_map.md`, scores, prior attempts, or actions that install the target package. One outer streaming payload was token-truncated, but every command type, command text, file path, and the final `turn.completed` event were recoverable; a forbidden-marker scan of the candidate output also found no match.

The candidate copy and untouched cleanroom original have identical hashes; the candidate-visible prompt and public `SPEC.md` both have hash `dedc332228c173f702159a8bbdd55df08b77c4c7207602e5392476cec7032ee2`. **Anti-Cheat: PASS.**

## 2. Solvability

The reference used the same Linux/arm64 image, Python 3.11.15, and pytest 9.1.1 as Stage 4; both the reference checkout and oracle were mounted read-only, with `--network none` and `PYTHONPATH=/reference`.

Reference provenance:

```text
platform=Linux-6.12.76-linuxkit-aarch64-with-glibc2.41
sys_platform=linux
python=3.11.15 (main, Jul 14 2026, 02:16:19) [GCC 14.2.0]
curio_file=/reference/curio/__init__.py
pytest=9.1.1
```

Reference oracle result:

```text
..............................................................           [100%]
62 passed, 2 warnings in 0.08s
```

Both warnings come from rejected-path resource cleanup in `test_run_rejects_nested_runtime`; the assertions pass, with no collection error or failure. The complete command and literal output are stored in `judge/evidence/reference_preflight.log` and `reference_pytest.log`. **Solvability: PASS (62/62, 100%).**

## 3. Candidate Score and Layer Breakdown

| layer | passed | failed | total |
|---|---:|---:|---:|
| atomic | 25 | 1 | 26 |
| integration | 20 | 3 | 23 |
| system_e2e | 13 | 0 | 13 |
| **total** | **58** | **4** | **62** |

The frozen nodeid set, order, and uniqueness all match `kept_nodeids.txt`. Two blocking failures were isolated by a per-test 15-second limit, while the other two produced complete JUnit output and tracebacks; the initial batch stall was excluded from scoring.

## 4. Fairness Gate A - Spec Mapping Spot-Check

| Sampled test | map section | Predictability from the specification | Result |
|---|---|---|---|
| `test_run_rejects_nested_runtime` | Installable Surface | `run()` must raise `RuntimeError` inside an active Curio task | PASS |
| `test_product_state_coordination_projection_retains_unfinished_work` | Product State Model | An obligation must remain after `get()` and until `task_done()` | PASS |
| `test_task_ids_are_increasing_integers_without_positivity_assumption` | Tasks and Task Groups | New task IDs are increasing integers, with no positivity condition | PASS |
| `test_blocking_cancel_terminates_task_and_marks_cancelled` | Tasks and Task Groups | Blocking cancellation must wait for termination | PASS |
| `test_queue_returns_items_in_fifo_order` | Queues | A Queue must return items in insertion order | PASS |
| `test_condition_wait_requires_held_lock` | Synchronization | Calling wait without holding the lock must raise `RuntimeError` | PASS |
| `test_timeout_after_raises_task_timeout_when_blocking_operation_expires` | Error Semantics | A matching timeout must raise `TaskTimeout` | PASS |
| `test_universal_queue_without_fd_rejects_fileno` | Universal Coordination | `fileno()` must raise `AssertionError` when `withfd=False` | PASS |
| `test_cross_view_universal_result_exception_reaches_asyncio_unchanged` | Cross-View Invariants | The same exception must propagate unchanged across environments | PASS |
| `test_representative_worker_queue_taskgroup_workflow` | Representative Workflows | The documented workflow explicitly produces 42 | PASS |

Every sampled section is a real H2/H3 heading in the specification, and the heading itself is sufficient to predict the assertion. **Gate A: PASS.**

## 5. Fairness Gate B - Failure Pattern Audit

| Failing test | layer | instrument validity | Candidate behavior |
|---|---|---|---|
| `test_blocking_cancel_terminates_task_and_marks_cancelled` | integration | Public cancellation liveness and terminated/cancelled state | Exceeded 15 seconds; blocking cancellation did not complete |
| `test_taskgroup_cancel_remaining_terminates_non_daemons` | integration | Public group cancellation and termination | Exceeded 15 seconds; cascade from primitive cancellation |
| `test_timeout_after_raises_task_timeout_when_blocking_operation_expires` | atomic | Public exception class | Raised `TaskCancelled`, not `TaskTimeout` |
| `test_timeout_escaping_matching_boundary_raises_uncaught_timeout` | integration | Public timeout-boundary exception class | Raised `TaskCancelled`, not `UncaughtTimeoutError` |

All four items follow directly from the specification and observe only public termination, blocking, or exception types. They use no repr, private fields, exact error strings, or fixture shapes. The reference passes all of them in the same environment. **Gate B: PASS; all four are genuine model failures.**

## 6. Fairness Gate C - Generated-Only Oracle Spot-Check

The oracle is labeled `generated_only`; this review manually sampled 11 tests covering every failure as well as different sections and layers.

| Test | section | spec-driven | behavioral | Result |
|---|---|---|---|---|
| `test_run_rejects_nested_runtime` | Installable Surface | Yes | Yes, public exception type | PASS |
| `test_product_state_coordination_projection_retains_unfinished_work` | Product State Model | Yes | Yes, Event deterministically brings the join waiter to its blocking point | PASS |
| `test_task_ids_are_increasing_integers_without_positivity_assumption` | Tasks and Task Groups | Yes | Yes, checks only integer type and monotonicity | PASS |
| `test_blocking_cancel_terminates_task_and_marks_cancelled` | Tasks and Task Groups | Yes | Yes, public liveness/state | PASS |
| `test_taskgroup_cancel_remaining_terminates_non_daemons` | Tasks and Task Groups | Yes | Yes, public group outcome | PASS |
| `test_timeout_after_raises_task_timeout_when_blocking_operation_expires` | Error Semantics | Yes | Yes, public exception class | PASS |
| `test_timeout_escaping_matching_boundary_raises_uncaught_timeout` | Error Semantics | Yes | Yes, public boundary exception | PASS |
| `test_priority_queue_returns_lowest_item_first` | Queues | Yes | Yes, return-value order | PASS |
| `test_condition_wait_requires_held_lock` | Synchronization | Yes | Yes, public precondition exception | PASS |
| `test_cross_view_universal_result_exception_reaches_asyncio_unchanged` | Cross-View Invariants | Yes | Yes, unchanged exception object across public environments | PASS |
| `test_representative_worker_queue_taskgroup_workflow` | Representative Workflows | Yes | Yes, complete public workflow | PASS |

**Gate C: PASS.**

## Gate D - Coverage Gap Audit

**Coverage verdict: FULL (every scoreable behavioral section meets the workflow floor; headings with zero direct rows are descriptive, containers, or boundaries and contain no uncovered behavior).**

| spec H2/H3 | direct covered | coverage / rationale |
|---|---:|---|
| Product Overview | 0 | Descriptive overview with no independent behavioral contract |
| Scope | 0 | Execution boundary; child sections cover the concrete behavior |
| Installable Surface | 3 | FULL |
| Public API | 0 | H3 container heading; every behavioral H3 is covered separately |
| Product State Model | 3 | FULL; task, coordination, and universal projections each have a direct row |
| Tasks and Task Groups | 11 | FULL |
| Timeouts and Cancellation | 6 | FULL |
| Queues | 6 | FULL |
| Synchronization | 9 | FULL |
| Universal Coordination | 9 | FULL |
| Error Semantics | 5 | FULL |
| Cross-View Invariants | 7 | FULL |
| Representative Workflows | 3 | FULL |
| Non-Goals | 0 | Exclusion boundary; no positive test should be synthesized |
| Evaluation Notes | 0 | Evaluation-vocabulary guidance, not additional behavior |

There is no gap in any core invariant, state lifecycle, or Error Semantics contract, so no `coverage-gap` MANIFEST entry is needed. **Gate D: PASS.**

## 8. Protocol Issues

No protocol issue requiring rerouting was found:

- The reference passes 62/62 in the same image; no expected value is incorrect.
- Map spot-checks agree with direct counts; no section is incorrectly mapped.
- Every sampled generated test is spec-driven and behavioral.
- The nested-`run()` rejection test produces two reference warnings, but the test does not assert on warnings, and they do not affect solvability or fairness.
- The failures are not specific to Python 3.11: a non-scoring targeted rerun under Python 3.13, from the same family as the candidate self-checks, also produced `TaskCancelled` in both timeout tests; see `judge/evidence/python313_timeout_diagnostic.log`.

Accordingly, no new `filter_correction_request.md` or `spec_patch_request.md` is created.

## 9. Real Model Failures and Cascade Analysis

### Root cluster 1 - cancellation liveness / state-management

The candidate's `Task.cancel()` calls `_task.cancel()` while the underlying asyncio task has not yet entered the runner, but the public completion event is set only in the runner's `finally` block. Pre-start cancellation prevents the runner from executing, after which blocking `cancel()` waits forever for the completion event. This directly causes `test_blocking_cancel_terminates_task_and_marks_cancelled` to time out; `TaskGroup.cancel_remaining()` reuses the same primitive, so the second integration failure is a cascade rather than an independent composition failure.

### Root cluster 2 - timeout exception conversion / error-semantics

The candidate task wrapper records a zero-deadline underlying asyncio cancellation as `TaskCancelled` and does not reliably convert it to `TaskTimeout` at the matching timeout boundary. The direct timeout test therefore fails; the subsequent escaped-timeout test receives the same `TaskCancelled` because the first matching timeout is already incorrect, making it a same-root cascade. The targeted Python 3.13 diagnostic reproduces the same result, ruling out a 3.11 environment difference.

**Cascade summary: 4 failures are explained by 2 root causes.** One is atomic and 3 are integration failures; system_e2e is 13/13, so the report does not claim a composition failure or cross-view weakness.

## 10. Saturation

The candidate is not at 100%, so neither `trivially-solved` nor `saturated-candidate-score` applies. The candidate compresses the original package's 22 top-level Python files into one 418-line implementation, but still exposes two clear, non-overlapping capability gaps; this run is discriminating.

## 11. Final Action

- Two genuine root clusters have been recorded in `weakness_table.md`.
- `PIPELINE_STATE.md` has been routed to `QUALIFIED`.
- At the main thread's request, this Judge left promotion and the final record to the orchestrator; after independent acceptance, the main thread completed the `tasks/curio/` promotion and final `CANDIDATES.md` record.
