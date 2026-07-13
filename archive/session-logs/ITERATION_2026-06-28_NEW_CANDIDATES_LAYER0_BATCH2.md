# New Candidates Layer-0 Batch 2

Date: 2026-06-28

## Scope

This iteration resumed the full-reproduction workflow after the mini-task route
was judged ineffective for SOTA agents. Network access was used to clone and
measure four additional multi-file source repositories. No candidate model runs
were performed in this iteration; all four tasks remain at Layer 0.

## Source Gates

| Candidate | Source repo | Commit | Tracked files | Nonblank LOC | Gate |
|---|---|---:|---:|---:|---|
| `eventruntime-fullrepro-001` | `inngest/inngest` | `5daffebaab80d7f958349cef00084af6173a8a47` | 12,839 | 8,866,888 raw; about 504,535 excluding vendor-like dirs | PASS |
| `streampipeline-fullrepro-001` | `redpanda-data/connect` | `d33d3abd864cbb896cf7c8e2d49da388adfeadc8` | 1,991 | 269,879 | PASS |
| `gatewayconfig-fullrepro-001` | `apache/apisix` | `496cb68c47db836b3cdecda0281dfb94de11b27f` | 1,918 | 229,257 | PASS |
| `telemetrypipeline-fullrepro-001` | `open-telemetry/opentelemetry-collector` | `524483419325fd238aa7db88add57dc17ff37888` | 2,754 | 252,120 | PASS |

Source gate artifacts:

- `prospects/eventruntime-fullrepro-001/source_candidate_gate.md`
- `prospects/streampipeline-fullrepro-001/source_candidate_gate.md`
- `prospects/gatewayconfig-fullrepro-001/source_candidate_gate.md`
- `prospects/telemetrypipeline-fullrepro-001/source_candidate_gate.md`

## Layer-0 Verdicts

### EventRuntime

- verdict: `BUILD`
- reason: Strong durable runtime surface. Run state, queues, retry/no-retry,
  sleep/wait, cancellation, replay, trace/history, REST API, UI history, and
  debug views all share a durable fact source and can drift.
- risk: Raw LOC is vendor-inflated; SDK-protocol-only scoring would be forced.
- next action: Build a benchmark-owned durable event runtime packet from the
  bounded core lifecycle, not from vendored SDK details.

### StreamPipeline

- verdict: `BUILD`
- reason: Shared registry/schema/config metadata drives CLI lint/test/dry-run,
  generated docs, public schema API, component catalog, readiness, metrics, and
  checkpoint/resume behavior.
- risk: Benthos/Redpanda conventions are recognizable; exact fixtures and line
  numbers must be avoided.
- next action: Build PRD/rubric around registry -> schema -> CLI/lint/test/docs
  plus one stateful replay/checkpoint workflow.

### GatewayConfig

- verdict: `BUILD`
- reason: Admin resources, schema validation, standalone config, reference
  graph, runtime routing, upstream selection, plugin precedence, version/digest
  views, and deletion semantics form a strong agreement surface.
- risk: APISIX is a known gateway, so use benchmark-owned names and avoid exact
  APISIX strings/private key layout.
- next action: Best immediate Layer-1 candidate. Build a bounded gateway config
  runtime with in-process request simulation rather than Nginx/APISIX cloning.

### TelemetryPipeline

- verdict: `BUILD_WITH_RESCOPE`
- reason: Collector-style config snapshots, component factories, pipeline graph,
  queue/batch/retry, readiness, metrics, and restart recovery are structurally
  strong.
- risk: OpenTelemetry/OTLP is a highly recognizable protocol surface.
- next action: Keep as reserve. Use only as a benchmark-owned local telemetry
  pipeline variant, not exact Collector or OTLP reproduction.

## Skill Update

Updated `skills/full-reproduction-task-builder/references/candidate-profiles.md`
with four new profiles:

- `EventRuntime`
- `StreamPipeline`
- `GatewayConfig`
- `TelemetryPipeline`

Each profile now includes:

- agreement surface;
- feature-pure unit template;
- system test template;
- oracle plan.

## Manifest Update

Updated `MANIFEST.json` with four new `full_reproduction_queue` entries. Their
status remains Layer 0:

- `eventruntime-fullrepro-001`: `layer0/network-scout-build`
- `streampipeline-fullrepro-001`: `layer0/network-scout-build`
- `gatewayconfig-fullrepro-001`: `layer0/network-scout-build`
- `telemetrypipeline-fullrepro-001`: `layer0/network-scout-build-with-rescope`

## Next Priority

Promote `gatewayconfig-fullrepro-001` to Layer 1 first.

Reason: It has the clearest non-mini agreement surface: resource CRUD/PATCH,
schema validation, reference graph, standalone replay/versioning, runtime route
matching, upstream selection, and plugin precedence. A one-file dict solution
should fail if the PRD/rubric keeps all these public projections.

Layer-1 entry tasks:

1. Write public PRD from APISIX evidence using benchmark-owned gateway names.
2. Write requirement map linking public behavior to upstream docs/source/tests.
3. Build starter skeleton with 10+ modules: resource store, schema validator,
   reference graph, standalone loader, route matcher, upstream balancer, plugin
   merger, runtime simulator, admin API, CLI/report.
4. Build hidden scorer with at least 50 checks across unit/integration/system.
5. Run reference/starter gates only after fairness review confirms no APISIX
   private-shape or exact-text traps.

## Layer-1 Draft Started

Created initial GatewayConfig artifacts:

- `task/gatewayconfig-fullrepro-001/prd.md`
- `task/gatewayconfig-fullrepro-001/doc/source_repo.md`
- `task/gatewayconfig-fullrepro-001/doc/requirement_map.md`
- `task/gatewayconfig-fullrepro-001/doc/harness.md`
- `task/gatewayconfig-fullrepro-001/rubric.json`

Current status: `layer1/draft-prd-rubric-needs-starter-reference`.

Candidate runs remain disallowed. The rubric is a 60-check draft and still needs
an executable scorer, starter skeleton, reference implementation, starter
baseline, fairness judge, and cleanroom leakage scan.

## Layer-1 Reference Gate

GatewayConfig was advanced from draft rubric to executable reference gate:

- public packet: `task/gatewayconfig-fullrepro-001/candidate_task/public_packet.md`
- candidate-visible PRD copy: `task/gatewayconfig-fullrepro-001/candidate_task/prd.md`
- starter skeleton: `task/gatewayconfig-fullrepro-001/candidate_task/starter`
- executable scorer: `task/gatewayconfig-fullrepro-001/scoring/run_executable_checks.py`
- reference: `runs/gatewayconfig-fullrepro-001/solution-reference`
- reference score: `runs/gatewayconfig-fullrepro-001/score_report_reference_v1.json`
- starter baseline: `runs/gatewayconfig-fullrepro-001/score_report_starter_baseline_v1.json`

Current executable scores:

- reference: 60/60, unit 20/20, integration 20/20, system 20/20.
- starter baseline: 0/60.

Current status: `layer1/executable-reference-100-scale-risk-awaiting-fairness-cleanroom`.

Candidate runs remain disallowed. The next gate is a fairness/cleanroom review
that checks feature-pure unit layering, public-only assertions, APISIX
contamination risk, no exact private-shape traps, and no leaked reference or
rubric visibility in the candidate workspace.

Scale caveat:

- starter package has 14 Python modules and 42 nonblank LOC.
- local reference package has 14 Python modules and 716 nonblank LOC.

This is a real warning. The upstream APISIX subsystem is large, but the current
EdgeGate public packet may still be too compressed for strict full-reproduction
promotion. Do not run candidate models until the fairness/scale judge either
approves the bounded subsystem as sufficiently hard despite compact reference
LOC, or expands the surface with additional public behavior and hidden checks.
