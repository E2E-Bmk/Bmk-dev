# Stage 5 Judge Diagnosis - httpcore-transport-fullrepro-001

Verdict: QUALIFIED

Run judged: `candidate-runs/codex-httpcore-specv1-20260704-001/score_retry_specv2/score_result.json`.

The old `score_result.json` and `score_result_retry_jsonreport.json` were not used as the scoring basis for this judgment.

## Preflight output

Command run before opening the spec_v2 score:

```text
$env:PYTHONPATH='G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-httpcore-specv1-20260704-001\output'; python -c "import httpcore; print(httpcore.__file__)"
```

Literal output:

```text
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-httpcore-specv1-20260704-001\output\httpcore\__init__.py
```

The import provenance points to the candidate solution package.

The formal scorer's own preflight also records:

```text
pytest_jsonreport preflight:
/mnt/g/research/01_agents/swe-e2e/Bmk-dev/.envs/s4-score-linux/lib/python3.11/site-packages/pytest_jsonreport/__init__.py
httpcore preflight:
/mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-httpcore-specv1-20260704-001/output/httpcore/__init__.py
```

## Anti-cheat scan

Available preserved candidate artifacts were scanned for forbidden implementation-phase access markers after excluding scorer-generated oracle/score directories and report files. The scan covered `task_prompt.txt` and the candidate `output/` package and searched for source/oracle/prior-score indicators including `repo-pool`, `oracle_repo`, `oracle_worktree`, `kept_nodeids`, `spec_test_map`, `score_result`, `pytest_report`, `reference_score`, and target-package install markers. No matches were found.

No preserved full interactive trajectory is present in this candidate run directory, so the anti-cheat conclusion is based on preserved prompt/output artifacts plus import provenance. I found no evidence of forbidden source, oracle, prior-score, generated-test, or installed-package access.

## Score and reference gate

Candidate score gate:

- Score file: `candidate-runs/codex-httpcore-specv1-20260704-001/score_retry_specv2/score_result.json`.
- Platform: `Linux-5.15.153.1-microsoft-standard-WSL2-x86_64-with-glibc2.31`.
- `remove_paths`: `["httpcore"]`.
- Summary: 58 passed / 64 total.
- By layer: atomic 15/15, integration 30/35, system_e2e 13/14.

Reference gate:

- Reference file: `wip/httpcore-transport-fullrepro-001/filter/reference_score.json`.
- Platform: `Linux-5.15.153.1-microsoft-standard-WSL2-x86_64-with-glibc2.31`.
- `remove_paths`: `["httpcore"]`.
- Summary: 64 passed / 64 total.
- This satisfies the Linux/WSL solvability gate.

## Gate C - generated-only oracle spot-check

`filter/spec_test_map.md` declares `filter/oracle_source: generated_only`. I manually checked generated tests for both principles: spec-driven and behavioral. No sampled row depends on private field names, exact repr strings, exact exception message text, or reference-only circular expectations.

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `tests/test_transport_fullrepro.py::test_pool_request_returns_status_headers_content_and_extensions` | Custom backend receives `connect_tcp()` host as ASCII Python `str` while response status, headers, content, and extensions match the HTTP bytes. | `Network Backends and Mock Streams` | derivable; public backend-call and response behavior |
| `tests/test_transport_fullrepro.py::test_stream_response_iterates_body_chunks_without_preloading_content` | Streaming response rejects early `.content` access and `iter_stream()` yields `[b"hello", b"world"]` without coalescing adjacent body chunks. | `HTTP/1.1 Response Handling and Streaming` | derivable; public streaming behavior |
| `tests/test_transport_fullrepro.py::test_https_request_connects_to_default_tls_port_and_starts_tls` | HTTPS without explicit port connects to 443 and calls `start_tls()` using a default `ssl.SSLContext` and request host SNI. | `TLS, UDS, Timeouts, and Retries` | derivable; public TLS/backend behavior |
| `tests/test_transport_fullrepro.py::test_https_request_uses_sni_hostname_extension_when_present` | `"sni_hostname"` overrides TLS server hostname while preserving the default SSLContext rule. | `TLS, UDS, Timeouts, and Retries` | derivable; public extension/TLS behavior |
| `tests/test_transport_fullrepro.py::test_request_line_uses_path_and_query_from_url` | Serialized HTTP/1.1 request line uses the URL path plus query target. | `HTTP/1.1 Request Serialization` | derivable; public wire behavior |
| `tests/test_transport_fullrepro.py::test_iterable_content_uses_chunked_transfer_encoding` | Iterable request content writes chunked transfer encoding when no explicit length or transfer encoding exists. | `HTTP/1.1 Request Serialization` | derivable; public wire behavior |
| `tests/test_transport_fullrepro.py::test_same_origin_reuses_connection_after_response_is_read` | Sequential same-origin requests reuse one idle HTTP/1.1 connection after the first body is consumed. | `Connection Pool Lifecycle` | derivable; public backend-call/lifecycle behavior |
| `tests/test_transport_fullrepro.py::test_trace_extension_reports_started_and_complete_events` | A trace callback receives TCP connection started and complete events. | `Trace Events and Extensions` | derivable; public callback behavior |

The three prior spec gaps are now explicitly covered in `spec_v2.md`:

- `NetworkBackend.connect_tcp()` receives `host` as an ASCII Python `str`.
- `iter_stream()` preserves response body chunk grouping and must not coalesce adjacent chunks.
- HTTPS with `ssl_context=None` creates and passes a default `ssl.SSLContext` to `start_tls()`.

## Gate D - coverage audit

Coverage verdict: PARTIAL, acceptable. All core transport behavior sections have direct covered rows. The only uncovered sections are overview/meta sections or cross-cutting summary sections whose behaviors are exercised through narrower mapped sections.

| spec section | uncovered behaviors | impact | recommendation |
|---|---|---|---|
| `Product Overview`, `Scope`, `Evaluation Notes` | Descriptive/meta material, not standalone behavior. | None. | No action. |
| `Installable Surface` | Public imports are exercised by all tests but not directly mapped to this heading. | Low. | Optional future map precision improvement. |
| `Public API` | Constructor/method behavior is covered under model, backend, pool, connection, TLS, proxy, and error sections. | Low. | Optional future map precision improvement. |
| `Product State Model` | Response/wire/lifecycle projections are covered through concrete subsystem tests. | Low. | Optional future map precision improvement. |
| `Proxy Configuration` | Proxy auth/header behavior is covered, but the two proxy tests are mapped to `URL, Request, Response Models`. | Low map precision issue. | Optional future map correction. |
| `Cross-View Invariants` | No direct row uses this heading, but every bullet has indirect coverage through request target/header serialization, response byte projection, backend argument, pool state, TLS/UDS, and retry tests. | Acceptable because this is a cross-cutting summary and the concrete invariant behaviors are covered. | Optional future map rows may name this section directly. |
| `Representative Workflows`, `Non-Goals`, `Invocation Protocol` | No direct workflow/negative invocation row. | Low; not core scoring surface for sync transport behavior. | Optional future expansion only. |

Direct covered core sections include `URL, Request, Response Models`, `HTTP/1.1 Request Serialization`, `HTTP/1.1 Response Handling and Streaming`, `Network Backends and Mock Streams`, `Connection Pool Lifecycle`, `Direct HTTP Connections`, `TLS, UDS, Timeouts, and Retries`, `Trace Events and Extensions`, and `Error Semantics`.

## Failure audit

All six candidate failures are valid model failures under spec_v2. They are spec-driven, behaviorally observable through public custom backends/streams or public response APIs, and pass on the Linux/WSL reference gate.

| failing test | layer | observed mismatch | judge classification |
|---|---:|---|---|
| `test_pool_request_returns_status_headers_content_and_extensions` | integration | Candidate calls backend `connect_tcp()` with `host=b"example.com"` while spec_v2 requires ASCII `str` `"example.com"`. | valid model failure; `atomic-behavior` |
| `test_different_origins_open_distinct_connections` | system_e2e | Candidate records backend host calls as bytes for two origins while spec_v2 requires strings. | valid model failure; same backend host root cause |
| `test_stream_response_iterates_body_chunks_without_preloading_content` | integration | Candidate yields `[b"helloworld"]`; spec_v2 requires preserving received chunk grouping as `[b"hello", b"world"]`. | valid model failure; `state-management`/streaming lifecycle |
| `test_https_request_connects_to_default_tls_port_and_starts_tls` | integration | Candidate passes `ssl_context=None` into `start_tls()`; spec_v2 requires a default `ssl.SSLContext`. | valid model failure; `atomic-behavior` |
| `test_https_request_uses_sni_hostname_extension_when_present` | integration | Same missing default SSLContext root cause before completing the SNI assertion. | valid model failure; TLS default-context cascade |
| `test_https_non_default_port_is_used_for_connect_and_host_header` | integration | Same missing default SSLContext root cause before completing port/Host assertions. | valid model failure; TLS default-context cascade |

## Real failure clusters

| cluster | affected tests | layer(s) | root cause | dimension | cascade |
|---|---:|---|---|---|---|
| Backend host type | 2 | integration, system_e2e | Candidate keeps origin host as bytes when calling public `NetworkBackend.connect_tcp()`, instead of decoding to ASCII `str`. | `atomic-behavior` | One system_e2e failure cascades from the same primitive mismatch. |
| Streaming chunk grouping | 1 | integration | Candidate coalesces adjacent response body bytes during streaming iteration. | `state-management` | No cascade. |
| Default TLS context | 3 | integration | Candidate treats `ssl_context=None` as a value to pass to `start_tls()` instead of creating a default `ssl.SSLContext`. | `atomic-behavior` | Three HTTPS tests stop at the same public stream assertion. |

Cascade analysis: six failing tests reduce to three root causes. The failures are mostly primitive public-transport behavior gaps rather than evidence of broad cross-component state drift.

## Protocol issues

No protocol-blocking issues remain. The generated-only oracle is behaviorally valid for the sampled rows, the reference gate passes 64/64, the candidate scorer ran on Linux/WSL with `--remove-path httpcore`, and all six failures are attributable to candidate behavior under spec_v2.

One interpretive caveat: the candidate run directory name and preserved `task_prompt.txt` reflect the earlier spec_v1 packet. This judge is intentionally evaluating the formal spec_v2 score requested for Stage 5; the failures are valid against the repaired task surface and oracle, but downstream analysis should avoid overclaiming that this exact candidate saw the clarified v2 prose during implementation.

## Labels

- `generated-only-oracle`
- `discriminating`
- `public-backend-contract`
- `streaming-boundary`
- `tls-default-context`
- `partial-map-coverage-acceptable`
