# MiniDynaconf Primitive-Readiness Current Rerun

Date: 2026-06-28

## Purpose

Re-evaluate MiniDynaconf after the current fairness/primitive-readiness rubric revision. The question was whether the lifecycle-v3 packet still has a fair residual compositional gap, or whether the previous raw gaps were primitive-capped.

## Current Score Reports

Rubric: `task/minidynaconf-realrepo-001/rubric.json`

- Reference: `score_report_reference_primitive_readiness_current_20260628.json`
  - Unit 100.00%, system 100.00%, gap 0.00pp.
- Codex subagent lifecycle-v3 artifact: `score_report_codex_subagent_lifecycle_v3_primitive_readiness_current_20260628.json`
  - Unit 75.00%, system 100.00%, gap -25.00pp.
- OpenHands DeepSeek V4 Pro lifecycle-v3 artifact: `score_report_openhands_deepseek_v4_pro_lifecycle_v3_primitive_readiness_current_20260628.json`
  - Unit 25.00%, system 40.00%, gap -15.00pp.

## Failure Clusters

Codex has no system failures. Its remaining failures are unit-level public primitive details:

- `MDU004`: runtime `set('service.port', '2')` keeps `"2"` as a string, and `delete()` returns the settings object instead of `True`.
- `MDU007`: `import_dict` leaves `'true'` as a string rather than boolean `True`.

OpenHands remains primitive-capped:

- nested attribute proxy is missing for dict values;
- runtime string casting is incomplete;
- `delete()` return behavior is wrong or absent;
- validator/attribute behavior cascades through unit rows.

OpenHands system losses that look lifecycle-related are not clean enough to accept:

- `MDS001`: export omits the empty `FEATURE` projection after deletion.
- `MDS003`: secrets/source precedence is wrong during durable import replay.
- `MDS004`: a failed configure attempt poisons later reload lifecycle.

Because OpenHands fails many prerequisite public primitives, these cannot establish a capable-agent residual compositional gap.

## Independent Read-Only Audit

A read-only explorer audited the current PRD, rubric, requirement map, and current reports using `gap-opportunity-auditor` and `gap-invariant-task-builder`.

Verdict: `solved-audit` for the current packet.

Rationale:

- Raw gap is negative for both Codex and OpenHands.
- Residual compositional gap is effectively 0pp for the capable Codex artifact because it passes every system row while still missing unit primitives.
- OpenHands is primitive-capped and therefore not formal gap evidence.
- Adding adjacent hidden rows would chase primitive or exact projection details after a capable artifact already solves the current system layer.

## Decision

Do not accept MiniDynaconf as gap evidence at the current surface.

Do not keep revising current unit rows merely to raise unit while preserving the same system rows; that would make the packet easier without creating a new residual compositional invariant.

The only plausible continuation is a materially larger public lifecycle scope, such as multi-environment reuse/switching where durable imports, runtime overlays, deletion tombstones, validators, export, and reload remain isolated per active environment while shared defaults stay consistent. That would require explicit PRD/API additions and new rubric rows over at least three public projections.

Absent that material rescope, route MiniDynaconf to solved/provenance audit or retire the current packet as no-gap for this agent population.
