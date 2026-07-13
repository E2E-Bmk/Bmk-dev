# GatewayConfig Fairness And Scale Judge

Date: 2026-06-28

## Verdict

`revise_before_candidate_runs`

Do not run Codex, OpenHands, DeepSeek, Qwen, or mini-SWE-agent candidates yet.

## Evidence

- PRD: `task/gatewayconfig-fullrepro-001/prd.md`
- rubric: `task/gatewayconfig-fullrepro-001/rubric.json`
- scorer: `task/gatewayconfig-fullrepro-001/scoring/run_executable_checks.py`
- reference: `runs/gatewayconfig-fullrepro-001/solution-reference`
- reference score: `runs/gatewayconfig-fullrepro-001/score_report_reference_v2_fairness.json`
- starter baseline: `runs/gatewayconfig-fullrepro-001/score_report_starter_baseline_v2_fairness.json`
- cleanroom smoke: `runs/cleanroom/gatewayconfig-cleanroom-smoke-20260628-v2`

## Scores

- reference: 60/60, score 100%.
- reference by layer: unit 16/16, integration 24/24, system 20/20.
- starter baseline: 0/60.

No model candidate has been run, so no unit/system gap exists yet.

## Fairness Findings

### Public Contract

The scorer uses public APIs and CLI behavior from the `edgegate` package. It does
not import hidden reference modules or APISIX source files. Error assertions use
public `EdgeGateError.code` values rather than exact message text.

Remaining risk: some public result shapes such as `plugin_plan.final`,
`reference_report.reverse`, and `runtime_report.routes` must stay explicitly
documented in the PRD/public packet if they remain hidden-scored.

### Feature-Pure Unit Layer

Initial rubric had several unit rows that built multi-resource state through the
facade. The following repair was applied before this judge was recorded:

- direct schema/patch/matcher/balancer/plugin primitive checks now exercise
  module-level functions;
- cross-feature rows `EG-U012`, `EG-U015`, `EG-U019`, and `EG-U020` were moved
  from unit to integration.

Current unit layer is improved but not fully final: `EG-U008`, `EG-U009`, and
`EG-U010` still use store/reference primitives together. This is acceptable as
module-local shared state, but a stricter judge may split them further.

### Private Shape / Exact Text

No exact APISIX error strings, etcd keys, modifiedIndex values, file order, or
private source layout are scored.

### Contamination

Risk is medium. APISIX is a well-known gateway. The task mitigates this by using
benchmark-owned product name, Python package surface, public error codes, a
small deterministic plugin set, and in-process request simulation. However, the
candidate-visible PRD explicitly says the task is inspired by APISIX, which may
increase pattern matching. This is acceptable for source provenance but should
be reconsidered before strict model runs.

### Cleanroom

Cleanroom v1 copied generated `__pycache__` files from the starter. The
cleanroom tool was repaired to ignore `__pycache__`, `.pyc`, and `.pyo`, and v2
was regenerated.

V2 contains only:

- public PRD;
- public packet;
- starter skeleton;
- task prompt.

No `rubric.json`, score reports, reference solution, source repo, manifest, or
prior candidate traces are present.

### Scale

This is the blocking concern.

- Upstream APISIX source scale passes Layer 0.
- Candidate-visible starter has 14 Python files and about 42 nonblank LOC.
- Local reference has 14 Python files and about 716 nonblank LOC.
- Scorer has 60 checks, but the implemented reference proves that a compact
  implementation can satisfy the current public surface.

This means the current GatewayConfig task is not yet a strict full-reproduction
benchmark. It is a good executable prototype and agreement-surface scaffold, but
candidate runs would likely measure a compressed subsystem, not full
system-scale reconstruction.

## Hacking Concerns

Medium. Because the hidden checks currently use deterministic small fixtures, a
candidate might pass by hard-coding the visible resource semantics rather than
building a broad gateway-config system. More fixture diversity and metamorphic
checks are needed before model runs.

## Required Repair Before Candidate Runs

1. Expand public surface with additional product-natural behavior:
   - route variables or path params;
   - upstream health/disable state;
   - consumer/credential or environment-scoped config;
   - plugin execution audit and report pagination;
   - snapshot export/import with generation history.
2. Raise executable checks from 60 toward 80+ with more metamorphic/system rows.
3. Keep unit layer feature-pure after expansion.
4. Re-run reference and starter gates.
5. Re-run cleanroom smoke.
6. Run an independent fairness judge again.

Only after those pass should strict candidate model runs begin.
