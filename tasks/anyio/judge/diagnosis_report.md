# Task Judge Diagnosis — anyio

## Preflight output

Command:

```bash
PYTHONPATH=/Users/zijian/bench/Bmk-dev/candidate-runs/codex-anyio-specv1-20260707-001/output python3 -c "import anyio; print(anyio.__file__)"
```

Literal output:

```text
/Users/zijian/bench/Bmk-dev/candidate-runs/codex-anyio-specv1-20260707-001/output/anyio/__init__.py
```

## Verdict

**QUALIFIED**. The candidate run is valid task-difficulty evidence: hard checks pass, reference oracle is solvable, fairness gates pass, and the observed failures are spec-driven behavioral model failures rather than spec gaps, verifier overreach, filter issues, or environment failures.

## Anti-cheat Scan

- Provenance: PASS. The required preflight imports `anyio` from the candidate output directory.
- Candidate packet: PASS. `task_prompt.txt` contains the cleanroom spec body only. It does not expose `spec_test_map.md`, `kept_nodeids.txt`, scorer output, source repository paths, or test expected values.
- Candidate output: PASS. Candidate files under `output/` do not contain source repo paths, oracle references, scorer artifacts, `spec_test_map`, or `kept_nodeids`. The only test-like file is `tests_cleanroom.py`, a small self-check written inside the output directory.
- Score report: PASS for judge-time use. It naturally references scoring artifacts after evaluation; no evidence indicates those artifacts were visible during implementation.
- Forbidden access verdict: none found. No `repo-pool/`, reference worktree, target-package install, source tests, prior score reports, `spec_test_map.md`, or `kept_nodeids.txt` access was visible in the candidate implementation materials.

## Solvability

Reference oracle result: **65/65 passed**, pass rate **100.00%**.

This is above the task-judge hard threshold of 95%. The reference result reports no failures, skips, or collection errors. The scoring set has 65 tests: 45 atomic, 17 integration, and 3 system_e2e.

Environment note: the reference score used an explicit `PYTHONPATH` to the reference implementation. Candidate scoring used direct `PYTHONPATH` isolation to the candidate output. The Stage 4 note says the local run was macOS sandbox rather than native Windows; no observed failure cluster is platform-specific, and reference/candidate import provenance is clear.

## Candidate Score

Overall: **57/65 passed**, pass rate **87.69%**.

| layer | passed | failed | total |
|---|---:|---:|---:|
| atomic | 38 | 7 | 45 |
| integration | 16 | 1 | 17 |
| system_e2e | 3 | 0 | 3 |

| source | passed | failed | total |
|---|---:|---:|---:|
| upstream | 9 | 3 | 12 |
| generated | 48 | 5 | 53 |

The candidate did not saturate the oracle, so the saturation heuristic is not triggered.

## Fairness Gate A — Spec Mapping Spot-check

Gate A verdict: **PASS**.

Sampled covered mappings from `spec_test_map.md`:

| test | mapped section | audit |
|---|---|---|
| `test_upstream_invalid_max_buffer` | Streams and Networking | Spec states memory stream `max_buffer_size` must be non-negative integer or `math.inf`; invalid values raise `ValueError`. |
| `test_upstream_closed_send_stream_errors` | Error Semantics | Spec states clean EOF is `EndOfStream` and same-end closed use is `ClosedResourceError`. |
| `test_effective_deadline_reflects_timeout_scope` | Cross-View Invariants | Spec explicitly requires timeout scopes to be reflected by `current_effective_deadline()`. |
| `test_task_handle_projection_matches_started_and_returned_values` | Product State Model | Spec requires task handle status/value to reflect the same child task state as the task group. |
| `test_wrap_file_closes_underlying_file` | Cross-View Invariants | Spec explicitly requires `wrap_file()` close to close the wrapped file object. |
| `test_functools_cache_reuses_coroutine_result` | Async Helpers and Testing | Spec requires coroutine cache wrappers to cache results. |
| `test_representative_task_memory_file_workflow` | Representative Workflows | Spec includes a representative composed task/memory/file/timeout workflow category. |

All sampled mappings are spec-driven and behavioral.

## Fairness Gate B — Failure Pattern Audit

Gate B verdict: **PASS**.

The 8 failures form three behavioral clusters. None depends on private module paths, private fields, exact repr strings, arbitrary internal names, or undocumented test harness shape.

| cluster | failed tests | mapped sections | fairness result |
|---|---:|---|---|
| buffered-byte-receive-over-object-stream | 6 | Streams and Networking; Error Semantics | Behavioral. The spec defines buffered exact/delimiter reads and `IncompleteRead` on EOF. The tests exercise observable return values/exceptions. |
| deprecated-worker-interpreter-alias | 1 | Installable Surface | Behavioral. The spec explicitly requires the deprecated top-level spelling to return the canonical class and emit `DeprecationWarning`. |
| temporary-directory-context-value | 1 | Files, Processes and Workers | Behavioral. The spec requires temporary directory context managers to mirror tempfile lifetimes; the test checks that the context value is a usable existing path and is removed after exit. |

## Fairness Gate C — Generated Test Audit

Gate C formal trigger: `oracle_source` is `upstream_plus_generated`, not `generated_only`; the generated-only hard gate does not apply.

Additional generated-test spot-check: **PASS**. Sampled generated tests are spec-driven and behavioral:

| generated test | audit |
|---|---|
| `test_deprecated_worker_interpreter_alias_warns` | Directly derived from Installable Surface deprecated alias requirement; checks warning class and public alias identity. |
| `test_all_backends_public_tuple` | Directly derived from Public API `get_all_backends()` tuple requirement. |
| `test_task_group_start_returns_started_value` | Directly derived from Public API `TaskGroup.start()` started value behavior. |
| `test_buffered_receive_exactly_reads_across_chunks` | Directly derived from Streams and Networking buffered exact-read behavior. |
| `test_temporary_directory_context_removes_path` | Derived from Files, Processes and Workers temporary directory lifetime requirement; checks observable filesystem state. |
| `test_to_thread_copies_contextvars_without_back_propagation` | Directly derived from Cross-View Invariants worker context propagation requirement. |

## Gate D — Coverage Gap Audit

Coverage verdict: **FULL**.

All behavior-bearing H2 sections in the spec have at least one `covered` row in `spec_test_map.md`. Meta sections are listed below but do not define separate executable behavior beyond the behavior sections.

| spec section | covered rows | uncovered behaviors | impact | recommendation |
|---|---:|---|---|---|
| Product Overview | n/a | none; overview only | none | no action |
| Scope | n/a | none; scope inventory is exercised through behavior sections | none | no action |
| Installable Surface | 3 | none found | none | no action |
| Public API | 8 | none found | none | no action |
| Product State Model | 3 | none found | none | no action |
| Streams and Networking | 14 | none found | none | no action |
| Files, Processes and Workers | 5 | none found | none | no action |
| Synchronization, Typed Attributes and Low Level APIs | 8 | none found | none | no action |
| Async Helpers and Testing | 3 | none found | none | no action |
| Error Semantics | 10 | none found | none | no action |
| Cross-View Invariants | 8 | none found | none | no action |
| Representative Workflows | 3 | none found | none | no action |
| Non-Goals | n/a | none; exclusion guidance only | none | no action |
| Evaluation Notes | n/a | none; scoring guidance only | none | no action |

No core invariant section has zero coverage.

## Protocol Issues

No spec gap, spec factual error, filter issue, or environment issue was found.

The failed assertions are derivable from the spec and pass on the reference implementation. The candidate behavior diverges from the spec in each failure cluster.

## Real Failure Clusters

| cluster | root cause | layer | dimension | affected tests | cascade |
|---|---|---|---|---:|---|
| buffered-byte-receive-over-object-stream | `BufferedByteReceiveStream` forwards a byte-count argument into `MemoryObjectReceiveStream.receive()`, whose candidate signature accepts no size argument; exact/delimiter buffered reads over memory byte objects fail before producing the required bytes or EOF exceptions. | atomic | atomic-behavior | 6 | One primitive buffered-read bug explains all six failures. |
| deprecated-worker-interpreter-alias | Candidate binds `BrokenWorkerIntepreter` at module import time, so attribute access returns the alias without invoking `__getattr__` and without emitting `DeprecationWarning`. | atomic | error-semantics | 1 | Isolated warning/alias behavior failure. |
| temporary-directory-context-value | Candidate async temp wrapper returns the `tempfile.TemporaryDirectory` object from `__aenter__` instead of the path-like directory name, so public filesystem checks receive the wrong context value. | integration | state-management | 1 | Isolated context manager value/lifetime projection failure. |

Cascade analysis: **8 failed tests root in 3 root causes**. The buffered-byte cluster is a small primitive cascade; system_e2e tests all pass, so the run is not composition-failure dominated.

## Labels

- `discriminating`: candidate score is neither saturated nor floor-level.
- `non-saturated-candidate-score`: 57/65 leaves clear behavioral failures.
- `primitive-cascade`: six failures root in one buffered receive primitive mismatch.

## Final Action

State transition: `S5_JUDGE -> QUALIFIED`.

Do not migrate to `tasks/` in this Stage 5 run; migration is intentionally left for the main thread after review, per user instruction.
