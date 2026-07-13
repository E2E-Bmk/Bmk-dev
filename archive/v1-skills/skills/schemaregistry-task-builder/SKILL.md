---
name: schemaregistry-task-builder
description: Build, audit, and iterate the custom SchemaRegistry full-reproduction SWE-E2E benchmark task. Use when creating or revising schema-registry PRDs, requirement maps, hidden unit/integration/system rubrics, executable checks, cleanroom harnesses, reference implementations, or judge notes for subject/version/global-ID/reference compatibility compositional gap measurement.
---

# SchemaRegistry Task Builder

Use this skill for the `schemaregistry-fullrepro-001` family. The task must be
a benchmark-owned schema registry, not a Confluent, Avro, JSON Schema, or
Protobuf clone. Mark the task `FORCED` or `CONTAMINATED` if the agreement
surface becomes a public standard with one obvious implementation.

## Required Task Shape

Require a package or local service with public modules for:

- benchmark-defined schema parser;
- canonicalizer;
- subject/version store;
- global schema-ID table;
- compatibility engine;
- config history;
- forward and reverse references;
- tombstones/deletion visibility;
- reports/export/import;
- CLI and importable API.

Reference implementations must use 10+ modules and roughly 2,000+ non-test LOC.
Hidden tests may import only documented public modules or execute the public
CLI/API boundary.

## Agreement Surface

Shared fact sources:

- subject version history;
- global schema-ID table;
- compatibility config history;
- tombstones;
- reference graph;
- audit/export ledger.

Free parameters:

- canonicalization: normalize field order/defaults/comments or preserve them;
- ID reuse: global canonical reuse versus subject-scoped allocation;
- version append: duplicate schemas reuse latest version or create aliases;
- config fallback: global-to-subject inheritance and historical lookup timing;
- tombstone visibility: hidden by default but retained in deleted-inclusive
  views;
- reverse references: eager materialization versus replay-derived index;
- export/import replay: preserve original IDs or allocate new IDs.

The PRD must publicly settle enough of these choices for hidden tests to be
fair while still leaving system consistency work across modules.

## Unit Test Template

Unit checks must be feature-pure:

- Parser: benchmark schema grammar, invalid syntax, duplicate field errors.
- Canonicalizer: semantic equivalence and normalization boundaries.
- Compatibility: backward/forward/full primitives and explainable failures.
- Subject store: append, duplicate detection, latest lookup, tombstone
  primitive behavior.
- ID table: canonical ID reuse and missing-ID errors.
- Config history: fallback lookup and timestamp/version boundaries.
- References: forward edge validation and reverse edge primitive updates.
- Reports/export: stable public schema from direct fixtures.

Do not let parser or compatibility primitives dominate the whole score. Cluster
repeated parser failures before interpreting system gap.

## Integration And System Test Template

Each system row must name the public cross-feature contract:

- Register canonical-equivalent schemas across subjects: ID lookup, version
  list, audit, and export agree.
- Subject config override: compatibility result, config history, and report
  explain the same decision.
- Delete/tombstone: normal list/get, deleted-inclusive views, referenced-by,
  and audit history agree.
- Register referenced schemas: forward references, reverse index, compatibility,
  and export/import replay agree.
- Import exported registry then continue registering: IDs, versions, configs,
  tombstones, and compatibility outcomes preserve public behavior.

Do not assert private serialization, private file layout, exact exception
classes, or arbitrary ordering unless the PRD defines them.

## Oracle Plan

Use `confluentinc/schema-registry` only as inspiration for subjects, versions,
global IDs, compatibility modes, references, deletes, and registry reports.
Define a custom record-schema language and custom CLI/API names. Mark every
benchmark-owned variant in the requirement map so judges can distinguish fair
custom behavior from accidental divergence.

Reference validation must prove reference=100%, hidden checks trace to public
requirements, no private helper imports exist, and scoring runs from outside
the candidate workspace.

## Cleanroom Rules

Candidate-visible files may include only the public packet, starter skeleton,
and public examples. Hide rubric, reference, score reports, previous attempts,
iteration notes, and trace audits. Use mini-SWE-agent-style cleanroom runs for
strict evidence; treat OpenHands as debugging unless it follows the same
visibility contract.
