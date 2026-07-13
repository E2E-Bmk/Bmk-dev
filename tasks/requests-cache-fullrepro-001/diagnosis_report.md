# Stage 5 Re-judge - requests-cache-fullrepro-001

Run: candidate-runs/codex-requests-cache-specv1-20260704-002
Date: 2026-07-04

## Anti-cheat preflight

Command:
```powershell
$env:PYTHONPATH = "
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-requests-cache-specv1-20260704-002\solution
"
python -c "import requests_cache; print(requests_cache.__file__)"
```

Preflight output:
```text
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import requests_cache; print(requests_cache.__file__)
    ^^^^^^^^^^^^^^^^^^^^^
  File "G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-requests-cache-specv1-20260704-002\solution\requests_cache\__init__.py", line 1, in <module>
    from .core import CachedSession, CacheMixin
  File "G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-requests-cache-specv1-20260704-002\solution\requests_cache\core.py", line 3, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'
```

Preflight exit code: 
1


Retry with task Windows dependency venv:
```powershell
$env:PYTHONPATH = "
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-requests-cache-specv1-20260704-002\solution
"
& "
G:\research\01_agents\swe-e2e\Bmk-dev\wip\requests-cache-fullrepro-001\.venv311\Scripts\python.exe
" -c "import requests_cache; print(requests_cache.__file__)"
```

Preflight output:
```text
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-requests-cache-specv1-20260704-002\solution\requests_cache\__init__.py
```

Preflight exit code: 
0


## Anti-cheat scan

Result: PASS. The successful preflight imports `requests_cache` from the candidate solution directory. The initial system Python attempt failed before printing `__file__` because that interpreter lacked `requests`; the retry used the task Windows dependency venv and printed the candidate path.

Trajectory scan: no forbidden implementation-phase access found. Candidate commands read `public_packet/spec.md`, listed/edited `solution`, attempted local validation, and did not read oracle files, score reports, kept_nodeids, spec_test_map, taxonomy, prior runs, repo-pool, or reference/source repos. No `pip install requests-cache` or target-package install was observed.

## Score Evidence

Score file read after preflight: `candidate-runs/codex-requests-cache-specv1-20260704-002/score_result.json`.

- Candidate total: 32 passed / 26 failed / 58 collected.
- Atomic: 11 passed / 10 failed / 21.
- Integration: 16 passed / 6 failed / 22.
- System E2E: 5 passed / 10 failed / 15.
- Reference solvability: PASS, `filter/reference_score_wsl.json` records 58/58 passed on WSL/Linux with `--remove-path requests_cache`.

## Gate A - Spec Mapping Spot-check

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `filter/generated_tests.py::test_session_get_caches_second_equivalent_request` | Second equivalent GET must come from cache with original body and no second origin call. | `## Session Caching Behavior`; also mapped to `## Cross-View Invariants` and `### Session Cache Hit` | derivable |
| `filter/generated_tests.py::test_only_if_cached_miss_returns_504_without_origin_call` | `only_if_cached=True` cache miss returns 504 `Not Cached` without origin call. | `## Session Caching Behavior`; `## Error Semantics` | derivable |
| `filter/generated_tests.py::test_ignored_query_parameter_shares_cache_entry_and_redacts_url` | Ignored query values share a cache entry and stored URL redacts ignored value. | `## Request Matching`; `## Product State Model`; `## Cross-View Invariants` | derivable |
| `filter/generated_tests.py::test_sqlite_backend_persists_across_sessions` | SQLite cache path persists response across sessions and creates `.sqlite` file. | `## Backends and Persistence`; `## Cross-View Invariants`; `### Persistent Local Cache` | derivable |
| `filter/generated_tests.py::test_serializer_pipeline_runs_dumps_and_loads_in_order` | SerializerPipeline dumps forward through stages and loads in reverse. | `## Serializers`; `## Public API` | derivable |

Gate A verdict: PASS. Sampled mappings quote real spec headings and assertions are predictable from the spec.

## Gate B - Failure Pattern Audit

Failure clusters are real candidate failures, not verifier failures:

- Response metadata lifecycle/state-management: many cache-hit tests fail because cached response copies lack `created_at`, `expires`, or `cache_key`; the spec requires those public metadata fields on cached responses.
- Cache-specific request API/api-surface: `only_if_cached` and `force_refresh` are rejected by inherited `requests.Session.request()` before reaching `send`; the spec explicitly lists these public request options.
- Mutable settings/state-management: tests mutate `session.settings.filter_fn` and `settings.expire_after`; this is a public behavior requirement in the spec's session settings model and write policy.
- Redaction/atomic behavior: normalization helpers remove ignored parameters instead of preserving `REDACTED`; the spec requires redaction in matching and stored request/response inspection.
- Persistence/workflow completeness: JSON/filesystem serializer tries to serialize raw `CachedResponse` objects and cannot round-trip public cached response workflows; SQLite lacks the public `db_path` projection.

Gate B verdict: PASS. Failures check observable public behavior, not private fields, repr, exact logs, or implementation-specific internal layout.

## Gate C - Generated-only Oracle Spot-check

`spec_test_map.md` declares `oracle_source: generated_only`, so generated tests were sampled.

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `filter/generated_tests.py::test_cache_clear_removes_response_and_next_request_misses` | Clearing the cache removes entries; next request misses and contacts origin. | `## Cache Inspection and Mutation`; `## Cross-View Invariants` | derivable, behavioral |
| `filter/generated_tests.py::test_default_policy_does_not_cache_post_or_404` | Default policy does not cache POST or non-200 GET. | `## Filtering and Write Policy` | derivable, behavioral |
| `filter/generated_tests.py::test_get_expiration_datetime_invalid_http_date_raises_value_error` | Invalid HTTP date string raises `ValueError`. | `## Error Semantics`; `## Expiration and Cache-Control` | derivable, behavioral |
| `filter/generated_tests.py::test_disabled_context_temporarily_uninstalls_and_restores` | `disabled()` uninstalls inside context and restores installed cache after exit. | `## Patcher Behavior`; `## Cross-View Invariants` | derivable, behavioral |
| `filter/generated_tests.py::test_cached_response_size_reports_body_length` | Cached response `size` reports body byte length. | `## Cache Inspection and Mutation` | derivable, behavioral |

Gate C verdict: PASS. No sampled row is circular or internal-shape dependent.

## Gate D - Coverage Gap Audit

Mapped covered sections include all core behavior headings: `Product Overview`, `Scope`, `Installable Surface`, `Public API`, `Product State Model`, `Session Caching Behavior`, `Patcher Behavior`, `Backends and Persistence`, `Request Matching`, `Expiration and Cache-Control`, `Filtering and Write Policy`, `Cache Inspection and Mutation`, `Serializers`, `Error Semantics`, `Cross-View Invariants`, `Representative Workflows`, and `Non-Goals`.

| spec section | uncovered behaviors | impact | recommendation |
|---|---|---|---|
| `## Invocation Protocol` | Packaging/run instructions only; no behavioral product assertion. | None for score validity. | No oracle action needed. |
| `## Evaluation Notes` | Benchmark process notes only. | None for score validity. | No oracle action needed. |
| `### Patching Requests` | Covered through `## Patcher Behavior` and patcher tests rather than exact subsection label. | Non-blocking metadata granularity. | Keep current map. |
| `### Persistent Local Cache` | Covered through `## Backends and Persistence` and SQLite/filesystem persistence rows rather than exact subsection label. | Non-blocking metadata granularity. | Keep current map. |

Gate D verdict: PARTIAL acceptable. No core invariant, error semantics, or state lifecycle section has zero coverage.

## Task Package Consistency

- `PIPELINE_STATE.md`: terminal `QUALIFIED` with oracle_count 58.
- `CANDIDATES.md`: requests-cache QUALIFIED row present for `codex-requests-cache-specv1-20260704-002`, score 32/58, Gates A/B/C pass and Gate D partial accepted.
- `weakness_table.md`: requests-cache rows present for state-management, api-surface, cross-view-consistency, atomic-behavior, and workflow-completeness.
- `tasks/requests-cache-fullrepro-001`: required artifacts present (`spec.md`, `spec_test_map.md`, `kept_nodeids.txt`, `taxonomy.jsonl`).
- wip/tasks hashes match for `spec.md`, `kept_nodeids.txt`, and `taxonomy.jsonl`. `spec_test_map.md` has no content diff by `git diff --no-index`; the SHA mismatch is line-ending/normalization only.

## Verdict

QUALIFIED. The scoring run is valid, anti-cheat provenance points into the candidate solution, reference solvability is 58/58, generated-only fairness Gates A/B/C pass, and Gate D is PARTIAL acceptable with only non-core/process sections uncovered. This task can be counted in the strict legal total.
