---
name: minijobledger-task-builder
description: Build, audit, and iterate the JobLedger full-reproduction SWE-E2E benchmark task. Use when creating or revising JobLedger PRDs, requirement maps, hidden unit/integration/system rubrics, executable checks, cleanroom harnesses, reference implementations, or judge notes for durable job-queue compositional gap measurement.
---

# MiniJobLedger Task Builder

Use this skill only for the `jobledger-fullrepro-001` family. The task is a
full-reproduction durable job-queue subsystem, not a mini queue. Reject any
revision that can naturally pass with one file, one in-memory dict, or one
final-state recomputation helper.

## Required Task Shape

Preserve the candidate-visible package skeleton:

- `api.py`: public facade and user workflows.
- `cli.py`: black-box command entrypoint.
- `models.py`: public records, states, and validation.
- `store.py`: durable job, attempt, queue, and cron storage.
- `scheduler.py`: virtual-time due selection and leasing.
- `retry.py`: retry/backoff policy.
- `uniqueness.py`: uniqueness windows and conflict reports.
- `cron.py`: deterministic cron materialization.
- `events.py`: event stream emission and replay.
- `metrics.py`: materialized counters and rollups.
- `recovery.py`: repair/replay after partial writes.
- `export.py`: export/import and diagnostic reports.

Reference implementations must keep 10+ modules and target roughly 2,000+
non-test LOC. Candidate implementations may add private helpers, but hidden
tests may import only documented public modules or run the CLI.

## Agreement Surface

Shared fact sources:

- retained job rows;
- attempt ledger;
- cron ledger;
- uniqueness windows;
- event stream;
- materialized queue state and metrics.

Free parameters that must be made public by the PRD or resolved by public
invariants:

- claim ordering: priority, due time, insertion order, or a specified tie-break;
- retry materialization: job-row fields, attempt events, or both;
- uniqueness key scope: queue, kind, args, configured keys, and expiry window;
- event ordering: before/after state transition and deterministic replay order;
- metrics timing: eager writes versus event-rollup snapshots;
- cron slot handling: lazy next-run calculation versus materialized slot ledger;
- recovery policy: rollback incomplete writes versus roll-forward from events.

System tests should fail only when these choices are inconsistent across public
views, not because the reference used a private representation.

## Unit Test Template

Unit rows must be feature-pure. Setup may use direct model fixtures,
constructor state, temp files for the module under test, or explicit mocks.
Do not enqueue through the public API just to test retry, cron, metrics, or
uniqueness.

Use three levels:

- Basic: valid construction and one successful operation.
- Edge: boundary times, priorities, retry counts, empty queues, expired
  uniqueness windows, duplicate cron slots.
- Error: invalid transitions, malformed args, stale leases, missing jobs,
  corrupt records, impossible recovery markers.

Required unit areas:

- `models`: validation, public states, transition legality.
- `store`: atomic insert/update/read and durable reload of one record family.
- `scheduler`: due-time filtering, lease ownership, deterministic ordering.
- `retry`: backoff sequence, terminal failure, retryable state projection.
- `uniqueness`: conflict creation, expiry, replacement, report semantics.
- `cron`: slot parsing/materialization with virtual time.
- `events`: append/replay order and malformed event rejection.
- `metrics`: single-event counter updates and reset/reload behavior.
- `recovery`: partial marker classification without integrated API setup.
- `export`: stable public export schema for direct fixtures.

Reject unit rows that assert private IDs, internal JSON key order, repr strings,
private file names, or exact exception classes unless the PRD explicitly makes
them public.

## Integration And System Test Template

Each system row must name its `cross_feature_contract`. Prefer operation
sequences with independent public projections:

- Enqueue -> claim -> complete: job history, queue counts, event stream, and
  metrics all agree.
- Enqueue -> fail -> retry -> claim: retry ledger, pending queue, attempts,
  events, and metrics agree.
- Cron tick -> restart -> tick same slot: exactly one job is materialized; cron
  ledger, job list, and events agree.
- Unique enqueue conflict -> expiry -> enqueue: visible queue, conflict report,
  history, and metrics agree.
- Cancel executing or scheduled job: queue visibility changes while audit
  history and events remain retained.
- Partial write marker -> recovery: recovery report, queue counts, metrics,
  and event replay converge without hidden repair hooks.
- Export -> import -> continue processing: IDs, histories, metrics, cron state,
  and uniqueness windows preserve public behavior.

Do not count repeated primitive failures as broad system gap. Cluster failures
by root cause before interpreting the unit/system difference.

## Oracle Plan

Use `oban-bg/oban` only as product inspiration for retained jobs, attempts,
retries, cron, uniqueness, and telemetry. Do not expose Oban module names,
database schema, SQL, or exact API names to candidates. Benchmark-owned PRD
decisions are allowed, but they must be explicit in the requirement map.

Reference validation must prove:

- reference passes every executable unit/integration/system check;
- hidden checks are justified by PRD sections and requirement IDs;
- no hidden check imports private helpers;
- system checks execute from outside the candidate workspace;
- full trajectory and final artifact are saved for every model run.

## Cleanroom Rules

Candidate workspace may contain only:

- public packet/PRD;
- starter skeleton;
- public examples or empty fixtures.

Candidate workspace must not contain:

- `rubric.json`;
- reference implementation;
- score reports;
- prior candidate outputs;
- iteration notes;
- trace leakage audits.

Use mini-SWE-agent-style cleanroom runs for strict evidence. OpenHands runs are
debugging evidence unless they follow the same cleanroom visibility contract.
