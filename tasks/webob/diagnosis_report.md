# Stage 5 Diagnosis Report: webob filter_v2

## Fresh judge redo note

This is a Stage 5 redo by a fresh task-judge agent. I did not use or inherit the prior judge verdict. I did not read `/Users/zijian/Bmk-dev-main/tasks/webob` as evidence. This verdict is based on the repaired `filter_v2` artifacts under `wip/webob` and `candidate-runs/codex-webob-spec_v1-2026-07-05-run1`.

## Verdict

QUALIFIED

The older 1040-node run is relevant only as background for why Stage 3 repaired the oracle. The current verdict is based on the `filter_v2` rerun.

## Preflight output

```text
/Users/zijian/Bmk-dev-main/candidate-runs/codex-webob-spec_v1-2026-07-05-run1/solution/webob/__init__.py
```

The candidate import points to the candidate solution directory, not to the oracle worktree, source repository, or installed package.

## Anti-cheat scan result

Result: no cheat detected in the supplied cleanroom/public artifacts and candidate solution.

Scanned:

- `cleanroom_manifest.json`
- `task_prompt.txt`
- `public_packet/spec.md`
- `solution/webob/**`

Forbidden-leakage patterns checked included source repository paths, `repo-pool`, `wip`, `tasks`, score reports, pytest reports, filter maps, kept nodeids, taxonomy files, reference/oracle outputs, previous attempts, workflow skills, Stage 1-5 language, and filter versions.

Findings:

- `task_prompt.txt` contains only the allowed run-local paths to the public spec and solution directory.
- `cleanroom_manifest.json` contains an explicit policy sentence naming excluded materials: source repository, tests, filter maps, score reports, workflow skills, previous attempts, and the internal spec header. Per the user instruction, I treated this as a cleanroom policy statement, not leakage.
- `public_packet/spec.md` contains a public `Evaluation Notes` section and ordinary product wording such as "workflow"; it does not expose hidden tests, nodeids, filter maps, score reports, reference outputs, or internal paths.
- Candidate solution files did not contain forbidden paths, score artifacts, nodeids, filter maps, workflow skills, or hidden-test leakage.

No separate candidate trajectory transcript was present in the supplied run directory, so this scan is limited to the available run artifacts and import provenance.

## Solvability and reference health

Solvability: pass.

- Stage 3 reference gate: `68 passed in 0.03s`, exit code 0.
- Stage 3 summary: 68 kept tests, with layer split atomic 31, integration 24, system_e2e 13.
- Reference scorer `reference_score_report_filter_v2.json`: 68 passed / 68 total, pass rate 1.0, 0 collection errors.
- Reference by layer: atomic 31/31, integration 24/24, system_e2e 13/13.

The oracle is conservative but above the 30-test minimum and has nonzero coverage in all three layers.

## Candidate score

Candidate scorer `score_report_filter_v2.json`:

- Overall: 26 passed, 42 failed, 68 total, 0 collection errors.
- Pass rate excluding skips: 0.38235294117647056.
- Atomic: 15 passed, 16 failed, 31 total.
- Integration: 10 passed, 14 failed, 24 total.
- System_e2e: 1 passed, 12 failed, 13 total.

Failure distribution:

- `tests/test_cachecontrol.py`: 3 failures.
- `tests/test_client.py`: 11 failures.
- `tests/test_datetime_utils.py`: 3 failures.
- `tests/test_etag.py`: 1 failure.
- `tests/test_exc.py`: 16 failures.
- `tests/test_headers.py`: 8 failures.

## Fairness audit

Fairness decision: pass.

Gate A, spec mapping spot-check:

- `tests/test_cachecontrol.py::*CacheControl*` maps to `### Header Helpers`. The retained tests check public cache-control parsing/copy/property behavior.
- `tests/test_client.py::TestSendRequest::*` maps to `### Decorators, Static Files, and Client Sending`. The retained tests check public `SendRequest` WSGI behavior: host/port derivation, injected connection classes, request body length handling, timeouts, socket errors, status, headers, and returned bytes.
- `tests/test_datetime_utils.py::*` maps to `### Datetime and HTML Helpers`. The retained tests check documented public date parsing and delta helpers.
- `tests/test_etag.py::Test_Parse::*` maps to `### Header Helpers`. The retained tests check public `ETagMatcher.parse` results for missing, quoted, comma-separated, and weak ETags.
- `tests/test_exc.py::*` maps to `### HTTP Exceptions`. The retained tests check public exception response behavior, content negotiation, WSGI calling, middleware conversion, named HTTP classes, and `status_map`.
- `tests/test_headers.py::*` maps to `### Multi-Value Mappings`. The retained tests check observable `ResponseHeaders` and `EnvironHeaders` mapping behavior.

Gate B, failure-pattern audit:

- The repaired run has 0 collection errors. The old collection-error carrier issue is fixed for this rerun.
- The retained oracle no longer contains the old private/import carrier hits called out in the rerun summary (`text_`, `_item_n_weight_re`, `environ_from_url`, `_is_content_range_valid`, `Transcoder`, or `test_serialize_date`).
- Most failures are real public behavior gaps: `SendRequest` call semantics, HTTP exception response generation and middleware, response header mapping operations, cache-control numeric parsing, datetime parsing, ETag missing-header projection, and public HTTP status map coverage.
- Some retained tests are compatibility-narrow: direct `ResponseHeaders()` / `ResponseHeaders(a=1)` construction, direct `CacheControl(props, typ)` construction, exact default HTTP exception body templates, and deterministic monkeypatching through `webob.datetime_utils._now`. These are worth noting, but they do not dominate the failure set and do not turn the rerun into a verifier-artifact result.

Gate C: not applicable. `spec_test_map.md` does not declare `oracle_source: generated_only`.

No `filter_correction_request.md` or `spec_patch_request.md` is required from this judgment.

## Real failure clusters

### Atomic behavior

The candidate missed public helper and mapping details:

- `CacheControl.parse` leaves `max_age` as a string instead of an integer; construction/copy also loses the expected type marker.
- `parse_date(1)` returns an epoch datetime instead of `None`; parsing an object whose `__str__` raises leaks `NotImplementedError`; `parse_date_delta` lacks the expected current-time delta hook.
- `ETagMatcher.parse(None)` returns an object without the expected empty `.etags` projection.
- `ResponseHeaders` cannot be constructed empty or from keyword pairs, which cascades into `getall`, `mixed`, `setdefault`, replacement, containment, and missing-key behavior.

Primary dimension: `atomic-behavior`.

### SendRequest workflow

Eleven integration failures share one main root: `SendRequest` calls injected connection factories as `(host, port, ...)`, while the retained public behavior expects the WebOb-style injectable connection target. This cascades across normal HTTP/HTTPS calls, host fallback, content-length handling, timeout support, socket-error translation, and no-length reads.

Primary dimension: `workflow-completeness`.

### HTTP exception API and semantics

The candidate's exception implementation is shallow:

- `HTTPException` and `WSGIHTTPException` miss public `wsgi_response` / response-generation behavior.
- Plain, HTML, JSON, content-negotiated, custom JSON formatter, explicit-body, and proxied-HEAD paths fail.
- `HTTPExceptionMiddleware` does not convert raised base `HTTPException` values as expected.
- `webob.exc` omits named HTTP classes/status-map entries such as `HTTPLocked` and related public status classes.

Primary dimensions: `api-surface`, `error-semantics`, and `workflow-completeness`.

## Cascade analysis

The 42 failures are cascade-heavy rather than 42 independent roots:

- 11 `SendRequest` failures reduce to one connection-factory/host-port workflow issue.
- 16 `test_exc.py` failures reduce mainly to incomplete exception response generation, WSGI response behavior, middleware conversion, and missing status-map classes.
- 8 `ResponseHeaders` failures reduce to one constructor/multi-value mapping root.
- 3 `CacheControl` failures reduce to numeric directive parsing and type preservation.
- The remaining singleton roots are datetime parsing/delta behavior and missing ETag projection.

This is a useful discriminating signal: the verifier is narrow but clean enough, and the candidate failures expose concrete public API reconstruction gaps.

## Weakness table status

No new `weakness_table.md` rows were appended by this redo. Existing equivalent rows for `codex-webob | webob | ... | spec_v1 | filter_v2` already cover the needed dimensions:

- `atomic-behavior`
- `workflow-completeness`
- `api-surface`
- `error-semantics`

Those existing rows are reused to avoid duplication.

## Task labels

- `discriminating`
- `cascade-dominated`
- `conservative-oracle`
- `public-api-reconstruction`

## Recommended orchestrator action

Accept the Stage 5 verdict as `QUALIFIED`. The orchestrator should proceed with graduation/record updates as appropriate. This judge did not modify `/Users/zijian/Bmk-dev-main/tasks/` or `/Users/zijian/Bmk-dev-main/CANDIDATES.md`.
