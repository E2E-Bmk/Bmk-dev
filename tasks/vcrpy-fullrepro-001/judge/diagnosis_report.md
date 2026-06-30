# vcrpy-fullrepro-001 Stage 5 Diagnosis

Status: QUALIFIED
Date: 2026-06-30

## Inputs

- Spec: `wip/vcrpy-fullrepro-001/spec/spec_v3.md`
- Filter: `wip/vcrpy-fullrepro-001/filter/spec_test_map.md` (`filter_v5`)
- Reference score: `wip/vcrpy-fullrepro-001/filter/reference_score_filter_v5.json`
- Candidate run: `candidate-runs/codex-vcrpy-specv3-20260630-001`
- Candidate score: `candidate-runs/codex-vcrpy-specv3-20260630-001/score_report_v5.json`

## Gate Results

- Leak/provenance: no file evidence of source, tests, filter, score, or prior-run access in the candidate solution/run packet. Residual risk remains because there is no full terminal trajectory log proving absence of access.
- Reference gate: PASS. Reference passed 38/38 expanded cases: integration 16/16, system 22/22, no collection errors, no unknown layer.
- Candidate gate: PASS for gap evidence. Candidate passed 28/38 (73.68% excluding skips): integration 10/16, system 18/22, no collection errors.
- Fairness gate: PASS with caveat. `filter_v5` is intentionally narrow because original atomic test files have module-level imports or parametrization that require uncontracted helper symbols, private stubs, `vcr.mode`, `HeadersDict`, or optional client surfaces. The final verifier has no atomic layer, so this task should be interpreted as an integration/system cleanroom gate, not a full primitive coverage packet.

## Candidate Failure Roots

The failures are not import collapse: all v5 cases collected successfully and the candidate passes most core record/replay flows. Failed rows cluster around cross-view behavior:

- `record_on_exception=False` did not preserve expected decorator exception semantics because replay response shape caused a `TypeError` instead of the assertion path.
- `drop_unused_requests` failed through the public `Cassette.load(path=...)` lifecycle.
- Custom matcher replay did not preserve playback eligibility for repeated matching interactions.
- Redirect workflows did not record and replay each redirected interaction with consistent `Request.uri` and `play_count`.
- Multi-value response headers were collapsed instead of preserved as a list.
- `decode_compressed_response=True` did not store response body in the public cassette dictionary shape.
- `VCRTestCase` customization via `_get_vcr_kwargs(...)` did not pass keyword overrides through the mixin lifecycle.

These failures span cassette state, HTTP interception, request/response projection, serializer shape, matcher configuration, and unittest lifecycle. They are therefore valid compositional evidence for the current verifier.

## Filter Caveat

Earlier filter revisions retained more atomic rows, but candidate scoring exposed collection-carrier problems: files such as `unit/test_filters.py`, `unit/test_matchers.py`, `unit/test_request.py`, and `unit/test_vcr.py` import or construct surfaces outside the current public spec even for nodeids that look locally docs-backed. `filter_v5` removes those carriers to avoid scoring uncontracted import failures.

Future enrichment should add benchmark-owned clean public tests for:

- custom persister save/load/error semantics;
- all record modes without exact source exception-class coupling;
- automatic cassette naming and decorator return values;
- custom patches;
- rewind and playback repeats;
- public matcher/filter helpers without module-level private or legacy imports.

## Verdict

QUALIFIED for the current SWE-E2E task suite, with the above coverage caveat recorded.
