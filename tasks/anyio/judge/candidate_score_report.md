# Candidate Score Report - anyio

run_id: codex-anyio-specv1-20260707-001
spec_version: v1
candidate_output: output/

## Score

- passed: 57
- failed: 8
- skipped: 0
- total: 65
- pass_rate: 87.69%

## Isolation

Import preflight:

```text
/Users/zijian/bench/Bmk-dev/candidate-runs/codex-anyio-specv1-20260707-001/output/anyio/__init__.py
```

Score command:

```text
PYTHONPATH=/Users/zijian/bench/Bmk-dev/candidate-runs/codex-anyio-specv1-20260707-001/output pytest -q /Users/zijian/bench/Bmk-dev/wip/anyio/filter/rewritten_upstream_tests.py /Users/zijian/bench/Bmk-dev/wip/anyio/filter/generated_tests.py
```

The first scoring attempt also passed `-p anyio.pytest_plugin`; pytest had already loaded the anyio plugin from entry points, so that attempt failed before collection with duplicate plugin registration. The scored run removed the redundant `-p` flag.

## Layer Breakdown

| layer | passed | failed | total |
|---|---:|---:|---:|
| atomic | 38 | 7 | 45 |
| integration | 16 | 1 | 17 |
| system_e2e | 3 | 0 | 3 |

## Source Breakdown

| source | passed | failed | total |
|---|---:|---:|---:|
| upstream | 9 | 3 | 12 |
| generated | 48 | 5 | 53 |

## Failure Clusters

| cluster | failed | spec sections | summary |
|---|---:|---|---|
| buffered-byte-receive-over-object-stream | 6 | Streams and Networking; Error Semantics | `BufferedByteReceiveStream` calls `receive(max_bytes)` on `MemoryObjectReceiveStream`, but the candidate memory stream receive method accepts no size argument. |
| deprecated-worker-interpreter-alias | 1 | Installable Surface | Accessing `BrokenWorkerIntepreter` does not emit `DeprecationWarning`. |
| temporary-directory-context-value | 1 | Files, Processes and Workers | `TemporaryDirectory` async context returns a `TemporaryDirectory` object instead of a path-like directory value. |

## Failed Nodeids

- `filter/rewritten_upstream_tests.py::test_upstream_buffered_receive_exactly`
- `filter/rewritten_upstream_tests.py::test_upstream_buffered_receive_exactly_incomplete`
- `filter/rewritten_upstream_tests.py::test_upstream_buffered_receive_until`
- `filter/generated_tests.py::test_deprecated_worker_interpreter_alias_warns`
- `filter/generated_tests.py::test_buffered_receive_exactly_reads_across_chunks`
- `filter/generated_tests.py::test_buffered_receive_until_returns_before_delimiter`
- `filter/generated_tests.py::test_buffered_receive_exactly_incomplete_raises`
- `filter/generated_tests.py::test_temporary_directory_context_removes_path`

## Notes

The scored run used direct `PYTHONPATH` isolation to point imports at `output/`. It ran in the local macOS sandbox, not native Windows.
