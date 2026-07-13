# Full-Reproduction Benchmark Workflow

Date: 2026-06-28

## Why The Mini Loop Failed

The old loop selected large upstream repositories, then compressed them into
100-1,000 LOC single-file tasks. That compression removed the software
engineering surface: packaging, service boundaries, persistence, migrations,
indexes, cache invalidation, generated artifacts, recovery, and cross-command
lifecycle. The resulting tests were necessarily small and often measured final
answers rather than maintained system behavior.

This is a task-design failure, not just a model-strength problem. A 300k LOC
upstream repository does not produce a hard benchmark if the public packet asks
for a 300 LOC toy clone.

## New Task Level

Strict tasks now target complete bounded subsystem reproduction, not mini
reimplementation.

Correction after source-pipeline audit: do not create task scale by manually
expanding a local reference implementation. The source of task scale is the
upstream repository and a bounded subsystem selected from it. The workflow is
real source repo -> source evidence map -> public packet -> cleanroom candidate
reconstruction -> external hidden scoring.

Minimum task shape:

- installable package or runnable service;
- 10+ candidate-owned source modules;
- roughly 2,000+ non-test reference LOC;
- CLI or service entrypoint plus importable public API;
- persistent state, generated artifacts, or materialized indexes;
- at least four public projections that can drift;
- at least three realistic multi-step workflows.

For strict unit/system gap measurement, prefer interface-defined architecture:
provide candidate-visible starter modules and public signatures, then ask the
agent to implement behavior. Unit tests isolate those public modules with mocks
or direct fixtures; system tests integrate the real modules and check global
invariants.

Do not build a strict task if a competent agent can naturally pass it with one
file and one in-memory model.

## Public Packet Requirements

Each task must include a product-grade PRD:

- product overview and non-goals;
- state model and lifecycle;
- public API schemas;
- CLI/service contracts;
- persistence/artifact semantics;
- error and rollback semantics;
- ordering, determinism, and compatibility rules;
- recovery/replay/export/import behavior;
- realistic multi-step examples;
- ambiguity boundaries.

The PRD should describe the public product, not the reference implementation.
However, it must be complete enough for a qualified engineer to build the
system without guessing hidden oracle preferences.

## Hidden Test Requirements

First strict candidate run requires at least 50 executable checks. Stabilized
tasks should move toward 80+ checks.

Required test layers:

- unit: feature-pure primitive checks across modules;
- integration: API/CLI/persistence/artifact boundaries;
- system: operation sequences, rollback, replay, cache/index invalidation,
  reverse projections, generated reports, and recovery;
- metamorphic: order-insensitive, replay, export/import, idempotence, and
  consistency checks;
- black-box: score from outside the candidate package using only public APIs,
  CLIs, or service endpoints.

Forbidden test shapes:

- private helper imports;
- exact text traps unless public contract;
- final-result-only checks over one-shot recomputation;
- repeated primitive cascade counted as many system failures;
- evaluator-only projections not owned by the candidate.

## Harness Requirements

Strict model runs must use a cleanroom mini-SWE-agent-style harness:

- visible workspace contains only public packet, starter skeleton, and empty or
  incomplete implementation files;
- no rubric, reference, score reports, prior candidates, iteration notes, or
  trace-analysis files;
- network disabled unless the task explicitly requires it;
- full trajectory saved;
- final artifact copied out and scored externally.

OpenHands runs can remain debugging evidence, but strict pass-rate evidence
must come from the same cleanroom contract.

## Current Priority Queue

Build only full-reproduction variants:

1. JobLedger: durable job queue with scheduler, uniqueness, retry, cron,
   metrics, events, recovery, CLI, and API.
2. BuildCache: CAS/action cache service with namespace, eviction, status,
   audit, recovery, CLI/API, and durable artifacts.
3. SchemaRegistry: custom schema registry with parser, canonicalizer, subject
   store, global IDs, compatibility, references, deletion, reports, CLI/API,
   and persistent history.

ArchiveManager and MigrationManager can be reconsidered only after replacing
their current one-file references with full subsystem packets and 50+ check
rubrics.

## Promotion Gate

A task can enter strict candidate evaluation only when:

- PRD passes full-reproduction review;
- reference passes all unit/integration/system checks;
- reference scale satisfies the module/LOC gate;
- scoring harness is isolated from all hidden assets;
- judge confirms the tests measure public product behavior, not private shape.

A task can enter core only when:

- reference = 100%;
- capable candidates do not trivially solve the current surface;
- residual compositional gap >= 15pp after removing primitive/cascade/evaluator
  defects;
- trace provenance is clean;
- the gap is reproduced or judge-approved as a true system-maintenance failure.
