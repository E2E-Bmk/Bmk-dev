# Source-Repo Pipeline Correction And Layer-0 Addendum

Date: 2026-06-28

## Correction

The previous JobLedger continuation risked rebuilding difficulty by manually
expanding a local reference implementation. That is the wrong object of
construction. Full-reproduction benchmark tasks must start from a real upstream
repository, convert upstream public/product behavior into a candidate-visible
public packet, and convert upstream evidence into hidden executable rubrics.
The candidate agent then reconstructs the system in a cleanroom workspace.

Reference LOC is not a quota to fill by hand. It is evidence that the upstream
source and selected bounded subsystem are genuinely system-scale. If a 50k+
LOC source repository yields a 1k LOC candidate that passes, the likely
diagnosis is PRD/rubric under-coverage or excessive compression into a mini
surface.

## Current Local Evidence

JobLedger currently has a runnable reference spine, but it is not promotable:

- reference path: `runs/jobledger-fullrepro-001/solution-reference/src/jobledger`
- measured scale: 31 Python files, 1028 nonblank source lines
- status: executable prototype only, not a full-reproduction task

Do not continue by adding local implementation bulk. Continue by returning to
the Oban source evidence and deriving public behavior, hidden checks, and
starter interfaces from that evidence.

## Newly Network-Scouted Source Repositories

These repositories were cloned into `.repo_cache` on 2026-06-28 and measured
from tracked files.

| Candidate | Source repo | Files | Text files | Nonblank LOC | Main LOC |
|---|---:|---:|---:|---:|---|
| NativeBuildGrid | `TraceMachina/nativelink` | 859 | 574 | 146933 | `.rs` 102593 |
| WorkflowScheduler | `dagucloud/dagu` | 2601 | 2516 | 645085 | `.go` 467376 |
| DurablePythonRuntime | `dbos-inc/dbos-transact-py` | 136 | 125 | 52838 | `.py` 51241 |
| ContentIndexCache | `npm/cacache` | 61 | 58 | 6595 | `.js` 4171 |

## Layer-0 Audit

### NativeBuildGrid

- Source: `TraceMachina/nativelink`
- Product surface: remote execution/build service with CAS, action cache,
  scheduler, workers, store backends, metrics, and service APIs.
- Shared fact source: CAS blobs, action results, scheduler leases, worker
  execution records, store backend metadata, and service status.
- Public projections: CAS lookup, action-cache lookup, scheduler queue,
  execution result, worker lease state, status/metrics, eviction/recovery
  reports.
- Local free choices: digest validation timing, lease expiry, retry
  materialization, store backend normalization, metrics aggregation timing,
  action-result invalidation.
- Global invariants: action-cache entries must reference reachable CAS blobs;
  scheduler/worker/execution/status views must agree after upload, dispatch,
  retry, worker loss, cache hit, and recovery.
- Contamination risk: medium/high because Bazel REAPI and remote execution are
  known protocols. Use a benchmark-owned local API and avoid exact REAPI names.
- Feature-pure risks: digest, action-result, and lease primitives must be
  frontloaded before system scoring.
- Unit semantic risks: avoid exact protobuf/wire-format assertions.
- Collapse risk: low if worker leases, metrics, action-cache, and recovery are
  durable projections rather than recomputed from one dict.
- Verdict: `BUILD_WITH_RESCOPE`.
- Next action: consider as a stronger replacement/variant for BuildCache only
  if the public packet includes scheduler/worker lifecycle, not just CAS.

### WorkflowScheduler

- Source: `dagucloud/dagu`
- Product surface: workflow/DAG scheduler with specs, executions, queues,
  retries, logs, history, UI/API, and persistent run state.
- Shared fact source: workflow specs, run records, step attempts, queue leases,
  schedules, log/event records, and history indexes.
- Public projections: workflow list/detail, run history, current status,
  pending queue, retry plan, log stream, schedule/next-run view, recovery
  report.
- Local free choices: schedule catch-up policy, retry event materialization,
  step-output capture, queue leasing, status rollup timing, log ordering.
- Global invariants: workflow status, step attempts, queue leases, logs, and
  history must agree after schedule, run, failure, retry, cancel, restart, and
  recovery.
- Contamination risk: medium. DAG schedulers are common, but a local custom
  workflow spec and deterministic runner can avoid Airflow/Dagu exact cloning.
- Feature-pure risks: expression parsing and schedule parsing can dominate if
  not covered in unit tests.
- Unit semantic risks: do not assert private YAML formatting or UI text.
- Collapse risk: low if run history, logs, schedules, and queue leases are
  materialized and replayed.
- Verdict: `BUILD`.
- Next action: strong new candidate. Build a public packet from Dagu docs and
  examples, but use benchmark-owned schemas and deterministic local execution.

### DurablePythonRuntime

- Source: `dbos-inc/dbos-transact-py`
- Product surface: durable Python workflow/runtime with steps, transactions,
  queues, recovery, idempotency, and workflow status/query APIs.
- Shared fact source: workflow records, step records, transaction outputs,
  queue records, idempotency keys, recovery cursors, and event history.
- Public projections: workflow status, step output, queue status, idempotency
  lookup, recovery report, history/export view.
- Local free choices: idempotency scope, step-result materialization,
  transaction rollback marker, queue delivery ordering, recovery replay
  boundaries.
- Global invariants: recovered workflow status and query results must match
  durable history after duplicate calls, step failure, transaction rollback,
  queue delivery, and restart.
- Contamination risk: medium/high because durable execution patterns are
  increasingly recognizable. Use a small benchmark-owned decorator/API surface.
- Feature-pure risks: decorator/context mechanics can become primitive
  failures; unit tests must isolate them.
- Unit semantic risks: avoid requiring exact exception classes or SQL schema.
- Collapse risk: low if history, idempotency, queues, and recovery are
  independent public projections.
- Verdict: `BUILD_WITH_RESCOPE`.
- Next action: viable reserve or DurableWorkflow replacement. Keep deterministic
  and local; do not ask candidates to recreate the full DBOS runtime.

### ContentIndexCache

- Source: `npm/cacache`
- Product surface: content-addressable cache with index entries, integrity
  metadata, verification, removal, and garbage collection.
- Shared fact source: content blobs, index records, integrity metadata,
  access/update timestamps, verify/repair logs.
- Public projections: content lookup, index lookup, list, verify report,
  garbage-collection report, recovery/repair report.
- Local free choices: index compaction, stale entry visibility, access-time
  update timing, missing blob repair, duplicate content identity.
- Global invariants: index entries, content files, list output, verify report,
  and GC results must agree after put, get, rm, corrupt, verify, and collect.
- Contamination risk: medium because npm cache and SRI concepts are known.
- Feature-pure risks: integrity parsing/hashing can dominate unless frontloaded.
- Unit semantic risks: avoid exact private file layout and path naming.
- Collapse risk: medium. At 6595 LOC upstream and compact API, a capable agent
  may solve a fair surface with a small implementation unless repair/GC/history
  workflows are central.
- Verdict: `RESCOPE`.
- Next action: keep only if merged into a larger BuildCache/ContentCache task
  with durable index, verify, repair, namespace, and eviction workflows.

## Updated Priority

1. `WorkflowScheduler` from Dagu: best new source candidate after correction.
2. `NativeBuildGrid` from NativeLink: strong if scoped beyond CAS into
   scheduler/worker/cache coordination.
3. `JobLedger` from Oban: still viable, but must restart from source evidence
   instead of local reference expansion.
4. `BuildCache` from bazel-remote or NativeLink: viable if action/cache/status
   plus failure/recovery lifecycle is broad enough.
5. `DurablePythonRuntime` from DBOS: promising reserve; watch contamination.
6. `ContentIndexCache` from cacache: under-scoped unless merged into a larger
   cache lifecycle.

## Process Change

Before any next candidate run:

- source repo scale and evidence map must exist;
- candidate-visible packet must be generated from public behavior, not local
  reference code;
- hidden rubrics must cite upstream evidence or explicit benchmark variant
  decisions;
- cleanroom workspace must contain no source repo, reference, hidden rubrics,
  score reports, or prior traces;
- model trace must be saved before scoring is accepted.
