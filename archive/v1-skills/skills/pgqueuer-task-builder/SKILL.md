---
name: pgqueuer-task-builder
description: Build, audit, or iterate the PgQueueLedger full-reproduction SWE-E2E benchmark task derived from janbjorge/pgqueuer. Use when editing PgQueueLedger PRD/public packet, requirement map, starter skeleton, hidden unit/integration/system rubrics, reference implementation, cleanroom harness, or fairness/judge notes.
---

# PgQueuer Task Builder

## Rule

Treat `janbjorge/pgqueuer` as the upstream source of product evidence, not as a
codebase to copy. Build the benchmark-owned product `PgQueueLedger`.

Do not use reference LOC as proof of scale. Scale evidence is the upstream
repository gate in `prospects/pgqueuer-fullrepro-001/source_candidate_gate.md`.

Candidate-visible files are limited to:

- `task/pgqueuer-fullrepro-001/candidate_task/public_packet.md`;
- `task/pgqueuer-fullrepro-001/candidate_task/starter/`;
- an empty solution directory.

Never expose `rubric.json`, `doc/requirement_map.md`, `scoring/`,
`solution-reference`, score reports, prior traces, or source repo internals to a
candidate run.

## Agreement Surface

Shared fact source:

- job rows;
- schedule records;
- worker claim/heartbeat records;
- retry attempt metadata;
- completion events;
- dashboard/metrics projections;
- file-backed replay state.

Free parameters with multiple plausible implementations:

- claim ordering alternatives exist, but PgQueueLedger publicly chooses
  priority-descending, created-at ascending, id ascending;
- retry materialization: update same job row or append attempt ledger;
- schedule catch-up: one tick, latest-only, or full catch-up;
- completion watcher boundary: terminal-only or every status transition;
- stale heartbeat recovery: immediate requeue, quarantine, or failed terminal;
- metrics aggregation timing: eager counters or report-time scan;
- durable adapter format: append log, snapshot file, or SQLite table.

Public invariant:

After enqueue, transaction rollback, claim, heartbeat, retry, schedule tick,
cancel, completion, recovery, and reopen, all public projections must agree:
job detail/history, queue counts, schedule state, completion watcher, dashboard,
metrics, and recovery report.

## Unit Template

Keep unit tests feature-pure:

- models/status lifecycle;
- store put/get/list/replace primitives;
- retry backoff and exhaustion;
- entrypoint registry validation;
- worker claim eligibility, priority, limit, heartbeat;
- scheduler due/not-due decisions;
- completion watcher offset;
- metrics snapshot from direct store state;
- recovery stale/live heartbeat primitive.

Unit setup may use direct constructors or explicit mocks. Do not enqueue through
the full facade just to test a low-level primitive unless the facade itself is
the unit.

## Integration Template

Cross one boundary at a time:

- API facade with store;
- scheduler with store;
- worker with store;
- completion watcher with terminal events;
- file store reopen;
- CLI enqueue/report;
- in-memory vs durable adapter conformance.

Avoid private file-layout assertions; test public reopen behavior instead.

## System Template

Every system row must name a cross-feature contract:

- success path keeps job status, completion event, metrics, and dashboard
  consistent;
- retry path keeps attempts, delayed visibility, queue counts, and history
  consistent;
- retry-then-success updates terminal projections once;
- cancel path removes queue visibility and creates terminal completion;
- schedule tick creates due work and updates schedule/dashboard views;
- stale worker recovery requeues only expired picked jobs;
- rollback leaves no queue, metrics, or completion visibility;
- commit makes queued work visible everywhere;
- file-backed reopen preserves job, terminal status, and completion event.

System tests should use operation sequences and public APIs, not final-state
shortcuts through private storage.

## Oracle Plan

Use source evidence:

- `README.md`: transactional enqueue, safe concurrency, scheduling, completion,
  metrics/dashboard, in-memory mode;
- `docs/getting-started/core-concepts.md`: status lifecycle, entrypoints,
  schedules, tables/projections;
- `docs/guides/completion-tracking.md`: terminal completion watcher;
- `docs/guides/retry.md` and `docs/guides/reliability.md`: retry, heartbeat,
  stale recovery;
- `docs/guides/scheduling.md`: recurring schedules;
- `docs/reference/ports-and-adapters.md`: public port boundaries;
- tests under `test/`: behavior evidence for completion, concurrency,
  scheduling, heartbeat, retry, metrics, in-memory, and port conformance.

Benchmark variants:

- no PostgreSQL dependency;
- no exact PgQueuer CLI/module names;
- deterministic virtual time;
- file or SQLite persistence allowed;
- no web UI or Prometheus server.

## Current Gates

Reference command:

```powershell
python task\pgqueuer-fullrepro-001\scoring\run_executable_checks.py `
  --solution-dir runs\pgqueuer-fullrepro-001\solution-reference `
  --json-out runs\pgqueuer-fullrepro-001\score_report_reference_v2_repair.json
```

Candidate runs remain gated until a fairness judge confirms the repaired suite
does not overfit the reference implementation or underspecify public behavior.
