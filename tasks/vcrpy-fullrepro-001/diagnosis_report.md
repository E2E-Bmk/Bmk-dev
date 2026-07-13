# vcrpy-fullrepro-001 Stage 5 Diagnosis

user-authorized exception on 2026-07-03: this report repairs missing exit artifacts for an already-exported task and recreates the missing WIP state. The WSL score below is a real rerun against the existing filter_v5 oracle; the exception is only for retroactive packaging/state repair and is not presented as an ordinary SKILL rescue path.

## Preflight output

```text
vcr.__file__=/mnt/g/research/01_agents/swe-e2e/Bmk-dev/candidate-runs/codex-vcrpy-specv3-20260630-001/solution/vcr/__init__.py
```

The import provenance points inside the candidate solution directory.

## Candidate score platform

Accepted score file: `candidate-runs/codex-vcrpy-specv3-20260630-001/score_result_wsl_py311native2_20260703.json`, copied to `score_result.json` and `tasks/vcrpy-fullrepro-001/score_result.json`. Platform: `Linux-5.15.153.1-microsoft-standard-WSL2-x86_64-with-glibc2.31`; it does not contain Windows. Candidate score: 28 passed / 38 expanded cases, 10 failed, pass_rate_excluding_skips 0.7368421052631579. Layer summary: integration 10/16, system_e2e 18/22.

## Anti-cheat scan

The cleanroom manifest records only `public_packet/spec.md`, `task_prompt.txt`, and the candidate `solution` directory as implementation inputs. No implementation-phase artifact in the run directory contradicts that cleanroom boundary. The WSL preflight above confirms the scorer imported from the candidate solution, not from the source repository.

## Reference solvability

Reference score: `tasks/vcrpy-fullrepro-001/reference_score_filter_v5.json`, 38/38 expanded cases passed on filter_v5. The task uses local pytest-httpbin fixtures; the WSL rerun set `REQUESTS_CA_BUNDLE` to pytest_httpbin's client certificate and cleared proxy variables for local httpbin traffic.

## Gate A - Spec Mapping Spot-check

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `tests/integration/test_config.py::test_set_drop_unused_requests` | saving with `drop_unused_requests=True` removes unused recorded interactions | `Playback Repeats And Drop Unused` | derivable |
| `tests/integration/test_register_matcher.py::test_registered_true_matcher` | a registered matcher name participates in replay matching | `Request Matching` | derivable |
| `tests/integration/test_requests.py::test_redirects` | redirects record and replay multiple interactions with consistent playback bookkeeping | `Cross-View Invariants` | derivable |
| `tests/unit/test_unittest.py::test_vcr_kwargs_passed` | `VCRTestCase` passes customization kwargs through the mixin lifecycle | `Unittest Integration` | derivable |

## Gate B - Failure Pattern Audit

The 10 candidate failures are public behavioral gaps, not private shape checks. They cluster around cassette lifecycle and cross-view behavior: `record_on_exception=False`, `drop_unused_requests`, repeated custom matcher playback, redirect playback count, multi-value response headers, decoded compressed response storage, and `VCRTestCase` keyword override propagation.

## Gate D - Coverage Gap Audit

| spec section | uncovered behaviors | impact | recommendation |
|---|---|---|---|
| Product Overview / Non-Goals / Implementation Freedom | narrative or boundary text only | no scoring gap | no action |
| Atomic helper surface not retained from upstream import-carrier files | some primitive helper APIs are intentionally not measured | caveat: Integration/system_e2e-only task | future benchmark-owned tests may enrich this area |

Coverage verdict: PARTIAL. Core lifecycle, request matching, serializers, filters, ignoring, HTTP interception, unittest integration, error-adjacent exception-saving, and `Cross-View Invariants` all have covered rows in `spec_test_map.md`. Gate C is not applicable because this is an upstream-filtered oracle, not generated-only.

## Verdict

QUALIFIED. The legal WSL score, preflight output, recreated WIP state, cleanroom spec repair, and terminal oracle files are now present. This qualification is recorded with `user-authorized exception on 2026-07-03` for the retroactive packaging/state repair.
