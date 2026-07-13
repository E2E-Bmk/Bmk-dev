---
name: minibuildcache-task-builder
description: Build, audit, and iterate the BuildCache full-reproduction SWE-E2E benchmark task. Use when creating or revising BuildCache PRDs, requirement maps, hidden unit/integration/system rubrics, executable checks, cleanroom harnesses, reference implementations, or judge notes for CAS/action-cache compositional gap measurement.
---

# MiniBuildCache Task Builder

Use this skill for the `buildcache-fullrepro-001` family. The task is a bounded
remote build-cache subsystem with durable CAS, action metadata, eviction,
status, audit, recovery, CLI, and API behavior. Reject revisions that collapse
to one dict, one filesystem scan, or one final-state recomputation pass.

## Required Task Shape

Require a package or local service with public modules for:

- digest validation;
- CAS blob storage;
- action-cache metadata;
- namespace isolation;
- access ledger and eviction;
- status and namespace reports;
- audit events;
- recovery from failed writes;
- export/import or restart replay;
- CLI and importable API.

Reference implementations must use 10+ modules and roughly 2,000+ non-test LOC.
Hidden tests may import only public modules documented in the PRD or execute
the public CLI/service boundary.

## Agreement Surface

Shared fact sources:

- CAS blob store;
- action-result index;
- namespace metadata;
- access-order ledger;
- failed-write markers;
- eviction log;
- materialized status counters.

Free parameters:

- access-order update timing: CAS read, action-cache read, write, or all;
- missing CAS handling: reject action entry eagerly or diagnose on lookup;
- namespace encoding: separate namespace table or key prefixing;
- overwrite policy: replace metadata, append version, or reject stale writes;
- failed-write recovery: rollback temp files, roll forward, or quarantine;
- eviction choice: global LRU, namespace pressure, or configured policy;
- status accounting: eager counters versus replay from event log.

System tests should force consistency between these choices across lookup,
status, audit, eviction, recovery, and restart behavior.

## Unit Test Template

Unit checks must be feature-pure:

- Digest: valid hash/size pairs, malformed digest errors, byte accounting.
- CAS: put/get/missing, duplicate blob, corrupt content rejection.
- Action cache: insert/lookup/update, reject or flag missing blob references.
- Namespace: isolation, default namespace, conflicting keys.
- Access ledger: single access event and deterministic victim ordering.
- Eviction: one victim decision with mocked store state.
- Status: primitive counter updates, reload/reset semantics.
- Audit: single event append and malformed event rejection.
- Recovery: classify temp/marker states without full API setup.

Do not assert private paths, raw directory layout, exact JSON key order, or
private exception classes unless made public by the PRD.

## Integration And System Test Template

Each system row must name the public cross-feature contract:

- Upload blobs -> write action result -> lookup: CAS, action cache, status, and
  audit agree.
- Touch/read entries -> evict: access ledger, eviction log, lookup visibility,
  and status counters agree.
- Failed blob write -> recovery: no action result points to a missing blob, and
  recovery/audit reports explain the outcome.
- Namespace overwrite: namespace reports, lookup results, status, and audit are
  isolated.
- Restart/export/import: CAS blobs, action entries, access ledger, status, and
  eviction decisions preserve public behavior.
- Corrupt or missing blob diagnosis: lookup, status, audit, and recovery views
  converge without hidden repair hooks.

Cluster repeated primitive roots before interpreting unit/system gap.

## Oracle Plan

Use `buchgr/bazel-remote` as inspiration for CAS/action-cache/status/eviction
concepts. Do not clone Bazel REAPI, exact HTTP paths, or repository layout.
Use benchmark-owned CLI/API schemas and deterministic timestamps.

Reference validation must prove reference=100%, hidden checks trace to public
requirements, no private helper imports exist, and scoring runs from outside
the candidate workspace.

## Cleanroom Rules

Candidate-visible files may include only the public packet, starter skeleton,
and public examples. Hide rubric, reference, score reports, previous attempts,
iteration notes, and trace audits. Use mini-SWE-agent-style cleanroom runs for
strict evidence; treat OpenHands as debugging unless it follows the same
visibility contract.
