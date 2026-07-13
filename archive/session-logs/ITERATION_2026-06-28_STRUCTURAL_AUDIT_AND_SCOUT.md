# Structural Audit Reset And New Candidate Scout

Date: 2026-06-28

## Purpose

Continue the benchmark iteration after the no-gap/primitive-cascade stall. This pass applies the later discussion rather than the first-version design manual:

- do not treat shared dict/tree/graph as sufficient composition;
- do not accept raw unit-system gaps before residual-gap judging;
- do not rescue structurally dead mini tasks with adjacent hidden rows;
- do not ban good implementation practices such as shared helpers to create artificial separation;
- use Layer-0 structural audit before any new task construction.

## Files Updated

- `DESIGN_MANUAL.md`
  - Rewritten around Layer-0 structural audit, Layer-1 skill-driven construction, and Layer-2 residual-gap judging.
  - Demotes raw-gap evidence to triage only.
  - Adds explicit verdicts: `BUILD`, `REPAIR_PRIMITIVES`, `RESCOPE`, `RETIRE_SOLVED`, `STRUCTURAL_DEAD`, `FORCED`, `KNOWN_PATTERN`, `COLLAPSE`, `EXCLUDED`.

- `STRUCTURAL_AUDIT.csv`
  - New machine-readable Layer-0 audit table for existing candidates.

- `CANDIDATES.md`
  - Existing candidate statuses updated to current-scope retirement / needs-redesign / excluded / prospect.
  - Added 2026-06-28 prospect entries: MiniAptly, MiniMigrationManager, MiniJobLedger, MiniBuildCache, MiniSchemaRegistry.

- `MANIFEST.json`
  - Existing candidate statuses synchronized with the new structural-audit routing.
  - Original raw-gap core rows are now marked as retro-judge repair candidates rather than automatically accepted core.
  - Added five new prospect records.

- `SCOUT_2026-06-28_NEW_CANDIDATES.md`
  - New source-grounded scout report from three parallel subagents plus main-thread source checks.

## Existing Candidate Routing

| Task | Current route | Reason |
|---|---|---|
| MiniBitcask | `retired/current-scope-solved` | Current CLI surface solved by Codex and OpenHands; no fair remaining invariant at this scale. |
| MiniKV | `retired/current-scope-structural-dead` | Obvious typed store; system rows solved while unit misses primitives. |
| MiniRedis | `retired/current-scope-structural-dead` | Obvious single-store model plus feature-pure unit violations. |
| MiniPackaging | `retired/current-scope-forced-pep-surface` | PEP surface is forced and one-shot; custom repo lifecycle would be a new task. |
| MiniTemplate | `needs-redesign/known-pattern-lifecycle` | Jinja2-like lifecycle solved and known-pattern saturated. |
| MiniDynaconf | `needs-redesign/primitive-readiness-and-rescope` | Current evidence is primitive-capped or system-solved; only larger lifecycle may continue. |
| MiniMarkdown | `needs-redesign/collapse-or-provenance-retire` | Workspace-v4 below gate; helper collapse is not a public bug. |
| Xitkit | `excluded` | No reliable public agreement surface. |

## New Prospect Priority

1. `MiniAptly`
   - Best archive/recovery prospect.
   - Strong lifecycle: package pool, immutable snapshots, published tree, cleanup/recovery, graph.

2. `MiniMigrationManager`
   - Strong graph/schema/version/plan agreement surface.
   - Needs branches, stamping, downgrade, rollback, not only linear migrations.

3. `MiniJobLedger`
   - Strong retained job history/metrics/cron/uniqueness surface.
   - Avoid exact Oban/Celery/Sidekiq naming and schemas.

4. `MiniBuildCache`
   - Strong AC/CAS/status/eviction agreement surface.
   - Avoid exact Bazel REAPI clone and final-file-only tests.

5. `MiniSchemaRegistry`
   - Good projections but contamination risk is higher.
   - Use custom record schema, not an exact Confluent/Avro clone.

## Verification

- `MANIFEST.json` was parsed with PowerShell `ConvertFrom-Json`.
- `STRUCTURAL_AUDIT.csv` was parsed with `Import-Csv`.
- `CANDIDATES.md` was grep-checked for new status and prospect entries.
- All three scout subagents completed and were closed.

## Next Action

Do not build PRDs yet. Pick one or two prospects and write task-specific enrichment briefs first:

```text
agreement_surface:
local_free_choices:
global_public_invariant:
shared_fact_source:
public_projections:
lifecycle_sequence:
why_unit_not_enough:
oracle_semantics:
fairness_risks:
stop_condition:
```

Recommended first brief: `MiniAptly`, because it has the strongest durable state plus public projection drift and the lowest one-shot recomputation risk among the fresh prospects.

## Follow-Up Briefs Started

Two prospects now have enrichment briefs and must pass forward audit before PRD construction:

- `prospects/miniaptly-prospect-001/enrichment_brief.md`
- `prospects/minimigrationmanager-prospect-001/enrichment_brief.md`

Open gate:

- Independent forward-audit subagents are checking each brief for forced surfaces, known-pattern saturation, one-shot recomputation, feature-pure unit risks, hidden oracle ambiguity, and whether the proposed system rows genuinely test cross-feature contracts.

First-pass audit result:

- `MiniAptly`: `revise before PRD`. Required tighter public oracle schemas, merge/filter semantics, anti-one-shot lifecycle, primitive-cascade guards, semantic comparisons, and public failure injection.
- `MiniMigrationManager`: `revise before PRD`. Required exact public verbs, target syntax, semantic JSON outputs, downgrade/reversibility rules, stamp semantics, a single recovery state machine, anti-one-shot ledger constraints, and primitive-cascade guards.

Revision applied:

- `MiniAptly` now specifies package artifact fields, identity tuple, checksum rule, semantic output objects, merge/filter conflict rules, public `--fail-at` injection, pending recovery behavior, anti-recompute lifecycle, and prevalidated system fixtures.
- `MiniMigrationManager` now specifies CLI/module verbs, targets, semantic JSON objects, toy operation inverses, recovery state machine, stamp semantics, anti-recompute ledger constraints, and prevalidated system fixtures.

Open gate:

- Second-pass audit result: both revised briefs are `PRD_READY`.
- `MiniAptly` first PRD section: `Public Product Contract And Semantic Output Schemas`.
- `MiniMigrationManager` first PRD section: `Public Product Contract And Migration State Model`.

PRD/rubric draft started:

- `MiniAptly` advanced from `prospect/prd-ready` to `candidate/prd-draft`.
- Created `task/miniaptly-realrepo-001/prd.md`.
- Created `task/miniaptly-realrepo-001/rubric.json` with 10 unit rows and 5 system rows.
- Created `task/miniaptly-realrepo-001/doc/requirement_map.md`.
- Created `task/miniaptly-realrepo-001/doc/source_repo.md`.
- Updated `MANIFEST.json` and `CANDIDATES.md` to point at the draft files.

Verification:

- `MANIFEST.json` parses.
- MiniAptly rubric parses and contains 15 rows.

Next gate:

- Build reference implementation and scorer for MiniAptly.
- Reference must pass 100% unit and 100% system before any candidate model run.
