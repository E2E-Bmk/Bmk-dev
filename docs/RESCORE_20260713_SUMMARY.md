# Candidate Rescore Summary - 2026-07-13

This index records fresh Stage 4 candidate scoring only. It does not replace Stage 5 judgments or change task qualification state.

## Results

| Task | Candidate run | Passed / executed | Pass rate | Atomic | Integration | System E2E | Audit note |
|---|---|---:|---:|---:|---:|---:|---|
| dbt-core-fullrepro-001 | codex-dbt-specv1-20260710-001 | 0 / 54 | 0.00% | 0 / 4 | 0 / 27 | 0 / 23 | All 54 setup errors cascade from one inline-compile fixture prerequisite. |
| starlette-asgi-fullrepro-001 | codex-starlette-specv1-20260710-001 | 63 / 64 | 98.44% | 22 / 22 | 30 / 31 | 11 / 11 | One binary WebSocket JSON payload-key defect; no cascade. |
| h2-protocol-fullrepro-001 | codex-h2-specv1-20260704-002 | 46 / 55 | 83.64% | 19 / 22 | 20 / 26 | 7 / 7 | Nine failures reduce to seven implementation roots. |
| luigi-workflow-fullrepro-001 | codex-luigi-specv1-20260710-001 | 55 / 60 | 91.67% | 24 / 26 | 11 / 13 | 20 / 21 | Five independent roots; config_path shape is less explicit than the other tested contracts. |
| httpx-client-fullrepro-001 | codex-httpx-specv1-20260710-001 | 71 / 78 | 91.03% | 36 / 40 | 23 / 26 | 12 / 12 | Seven failures, six roots. Response.is_closed and custom-auth history deserve spec-explicitness review. |
| bandit-securityscan-fullrepro-001 | codex-bandit-specv2-20260711-001 | 60 / 61 | 98.36% | 24 / 24 | 25 / 26 | 11 / 11 | One SARIF notification projection defect; no cascade. |
| kedro-pipeline-fullrepro-001 | codex-kedro-specv1-20260710-002 | 66 / 71 | 92.96% | 47 / 50 | 18 / 20 | 1 / 1 | Five failures, four roots. Runner missing-input exception type deserves spec-explicitness review. |
| nbformat-notebook-fullrepro-001 | codex-nbformat-specv1-20260710-002 | 67 / 67 | 100.00% | 36 / 36 | 27 / 27 | 4 / 4 | Saturated candidate score; useful as a leakage/recall challenge, weak as a discriminator by itself. |
| pgqueuer-fullrepro-001 | codex-pgqueuer-specv1-20260704-001 | 50 / 59 | 84.75% | 25 / 27 | 12 / 17 | 13 / 15 | Fifty-seven base nodeids expand to 59 cases. Eight failures cascade from one scheduler argument bug; one is independent. |

## Daily Agent-Tree Usage

The authoritative 2026-07-13 backend aggregate supplied by the user covers the main agent and all subagents for the full day, not only these nine rescoring tasks:

| Requests | Provider-counted tokens | Actual cost | Standard cost |
|---:|---:|---:|---:|
| 1,997 | 277.57M | $18.14 | $316.00 |

Derived values:

- Average provider-counted throughput: approximately 138,994 tokens per request.
- Average actual cost: approximately $0.0091 per request.
- Average standard cost: approximately $0.1582 per request.
- Actual cost is approximately 5.74% of standard cost, a 94.26% reduction.

The backend token total includes repeated full-context input, cache reads, tool results reintroduced into context, and outputs across requests. It must not be compared with a deduplicated estimate of unique material read. The aggregate cannot be reliably allocated to individual tasks without a per-thread or per-request usage export, so this report intentionally does not invent per-task token or cost values.

## Artifact Convention

Each selected candidate-run directory contains:

- `score_result_rescore_20260713.json`: machine-readable score and per-case outcomes.
- `rescore_note_20260713.md`: provenance, platform, invocation, layer totals, root causes, and cascade analysis.
- A fresh run directory where retained by the scorer.

Candidate-run directory dates identify when the frozen candidate implementation was generated. The `20260713` rescore filenames identify when the current oracle was executed.

## Interpretation

- Raw scores remain unchanged by audit caveats; any fairness repair requires the normal spec-writer/test-filter flow and a downstream Stage 4/5 rerun.
- dbt's zero is a real workflow failure but not 54 independent failures.
- nbformat's 100% score should trigger saturation and contamination analysis before treating it as benchmark difficulty evidence.
- Kedro remains reopened; this Stage 4 result alone does not restore `QUALIFIED`.
