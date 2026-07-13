# Full-Reproduction Layer-0 Audit

Date: 2026-06-28

This audit applies the full-reproduction gate before any PRD/rubric build. The
goal is to reject mini surfaces early and select candidates whose natural shape
requires a package/service, persistent state, materialized projections, and
50+ hidden checks.

## Scale Evidence

| Candidate | Source repo | Files | Text LOC | Status |
|---|---:|---:|---:|---|
| JobLedger | oban-bg/oban | 170 | 19301 | counted |
| BuildCache | buchgr/bazel-remote | 135 | 28183 | counted |
| SchemaRegistry | confluentinc/schema-registry | 1215 | 296515 | counted |
| FeatureFlagControlPlane | thomaspoignant/go-feature-flag | 9894 | 465642 | counted |
| DurableWorkflow | cschleiden/go-workflows | 389 | 58436 | counted |
| BackupRepository | kopia/kopia | 1251 | 139575 | counted |
| DurableAppPlatform | restatedev/restate | 1412 | 296869 | counted with filesystem fallback |
| FeatureHub | featurehub-io/featurehub | 0 | 0 | clone failed; do not audit |

## Candidate Audits

### JobLedger

- Source: https://github.com/oban-bg/oban
- Product surface: durable job queue with scheduling, retry, cron, uniqueness,
  metrics, event stream, and recovery.
- Shared fact source: retained job rows, attempt ledger, cron ledger,
  uniqueness windows, event stream, and queue state.
- Public projections: job detail/history, queue counts, cron next-run view,
  conflict report, metrics rollups, event stream, recovery report.
- Local free choices: claim ordering, retry backoff materialization,
  uniqueness-window representation, metrics aggregation timing, event ordering.
- Global invariants: queue counts and metrics must match retained rows and
  events after enqueue/claim/complete/fail/retry/cancel/cron workflows.
- Contamination risk: medium. Oban/Celery/Sidekiq patterns are common, but a
  custom public API and custom storage schema can avoid exact clone behavior.
- Feature-pure risks: manageable if unit tests mock store/scheduler boundaries.
- Collapse risk: low if metrics/events/cron/recovery are materialized and not
  recomputed from one current dict.
- Verdict: `BUILD`.
- Next action: create full subsystem PRD and rubric. Keep name `JobLedger`, not
  `MiniJobLedger`.

### BuildCache

- Source: https://github.com/buchgr/bazel-remote
- Product surface: remote build cache with CAS blobs, action-result metadata,
  namespace isolation, eviction, status, audit, and recovery.
- Shared fact source: CAS blob store, action-cache index, namespace metadata,
  access-order ledger, failed-write markers, and eviction log.
- Public projections: CAS lookup, action-cache lookup, status counters,
  namespace hit/miss report, eviction audit, recovery report.
- Local free choices: access-order update timing, missing-blob handling,
  namespace key encoding, failed-write recovery, eviction victim selection.
- Global invariants: action-cache entries must reference existing CAS blobs;
  status bytes/counts and eviction logs must agree with reachable blobs after
  reads, writes, overwrites, failed writes, and GC.
- Contamination risk: medium from Bazel remote-cache domain. Avoid exact REAPI;
  use custom HTTP/CLI schemas.
- Feature-pure risks: manageable by testing digest, namespace, eviction, and
  status primitives separately.
- Collapse risk: low if status/audit/eviction are durable projections.
- Verdict: `BUILD`.
- Next action: create full subsystem PRD and rubric. Keep name `BuildCache`.

### SchemaRegistry

- Source: https://github.com/confluentinc/schema-registry
- Product surface: schema subject/version registry with global IDs,
  compatibility rules, references, deletes/tombstones, and reports.
- Shared fact source: subject version history, global schema-ID table,
  compatibility config history, tombstones, and reference graph.
- Public projections: subject list, version list, ID lookup, compatibility
  result, referenced-by reverse index, deleted-inclusive views, audit report.
- Local free choices: canonicalization, ID reuse policy, config fallback,
  tombstone visibility, reverse-reference update timing.
- Global invariants: canonical-equivalent schemas reuse IDs; subject versions
  advance only for new content; deletes and references affect all views
  consistently.
- Contamination risk: high if Avro/Confluent APIs are copied. Use a custom
  record schema language and custom endpoint/CLI names.
- Feature-pure risks: compatibility/parser unit tests can become forced if they
  mirror a public standard; keep the schema language benchmark-defined.
- Collapse risk: medium. Require materialized reverse indexes, config history,
  tombstones, and export/import replay.
- Verdict: `BUILD_WITH_RESCOPE`.
- Next action: build a custom SchemaRegistry task, not a Confluent clone.

### FeatureFlagControlPlane

- Source: https://github.com/thomaspoignant/go-feature-flag
- Product surface: feature-flag repository with retrievers, evaluation,
  targeting contexts, exporters, notifiers, relay/proxy behavior, and audit.
- Shared fact source: versioned flag definitions, context attributes, rollout
  rules, cache snapshots, evaluation events, exporter/notifier delivery state.
- Public projections: flag evaluation, flag list/detail, relay cache state,
  exporter event batches, notifier audit, stale/reload diagnostics.
- Local free choices: cache invalidation timing, rollout bucketing, event
  batching, retriever precedence, stale snapshot fallback.
- Global invariants: evaluation results, exported events, notifier audit, and
  cache diagnostics must agree after reloads, partial retriever failure,
  targeting changes, and batch flushes.
- Contamination risk: medium from OpenFeature and feature-flag systems. Avoid
  exact OpenFeature SDK surface; use custom schemas.
- Feature-pure risks: bucketing and targeting can be primitive-heavy; frontload
  them into unit checks.
- Collapse risk: medium. Require durable event/exporter state and reload
  history so final evaluation alone is insufficient.
- Verdict: `BUILD`.
- Next action: consider as a fourth full-reproduction task if queue/cache/schema
  are insufficient.

### DurableWorkflow

- Source: https://github.com/cschleiden/go-workflows
- Product surface: workflow engine with durable histories, activities,
  timers, retries, signals, queries, workers, and replay.
- Shared fact source: workflow event history, pending timers, activity attempts,
  worker task queues, signal/query records, and retry state.
- Public projections: workflow status, event history, pending work, query
  result, retry schedule, worker poll output, replay diagnostics.
- Local free choices: history event schema, timer ordering, retry event
  materialization, signal buffering, query consistency.
- Global invariants: replay from event history must reproduce status/query
  results; pending work and retry schedules must match history after failures,
  timers, signals, and worker restarts.
- Contamination risk: medium/high from Temporal-style patterns. Use custom API
  and a deliberately small workflow DSL.
- Feature-pure risks: async scheduling and timing can create flaky tests; use a
  deterministic virtual clock.
- Collapse risk: low if event history is durable and replay is black-box tested.
- Verdict: `BUILD`.
- Next action: viable but likely more harness work than JobLedger/BuildCache.

### BackupRepository

- Source: https://github.com/kopia/kopia
- Product surface: backup repository with content packs, manifests, snapshots,
  policies, retention, verify, repair, and restore.
- Shared fact source: content-addressed packs, manifest index, snapshot graph,
  retention policy state, repair log, and restore plan.
- Public projections: snapshot list/detail, manifest index, content reachability,
  retention prune report, verify/repair report, restore output.
- Local free choices: pack layout, manifest grouping, retention marking,
  repair quarantine, restore conflict handling.
- Global invariants: snapshots, manifests, reachable content, retention prune
  output, verify/repair reports, and restored files must agree after backup,
  delete, prune, corrupt, repair, and restore workflows.
- Contamination risk: medium from backup tools but less forced than standards.
  Avoid exact Kopia/restic repository formats.
- Feature-pure risks: file-tree hashing and retention primitives must be
  frontloaded.
- Collapse risk: low if packs/manifests/reports are materialized and corruption
  recovery is tested.
- Verdict: `BUILD`.
- Next action: strong candidate if tests can manage filesystem setup cost.

### DurableAppPlatform

- Source: https://github.com/restatedev/restate
- Product surface: durable service platform with invocations, journals,
  timers, idempotency, subscriptions, state, and recovery.
- Shared fact source: invocation journal, service state, timer table,
  idempotency keys, inbox/outbox records, recovery cursor.
- Public projections: invocation status, service state query, journal tail,
  timer list, idempotency report, recovery report.
- Local free choices: journal compaction, timer delivery ordering, idempotency
  key scoping, failure recovery, outbox materialization.
- Global invariants: service state, journal, timers, idempotency, and recovery
  reports must agree after duplicate calls, delayed timers, failures, and
  restarts.
- Contamination risk: medium/high because durable execution platforms are
  increasingly common. A custom local-only service API is required.
- Feature-pure risks: distributed concepts can over-expand; keep one-process
  deterministic harness.
- Collapse risk: low if journals/timers/idempotency reports are durable.
- Verdict: `RESCOPE`.
- Next action: reserve as later candidate; JobLedger/DurableWorkflow cover much
  of this space with less scope risk.

## Build Priority

1. `JobLedger` - best balance of agreement surface, scope, and harness cost.
2. `BuildCache` - strong materialized CAS/action/status invariants.
3. `SchemaRegistry` - strong if custom schema language avoids Confluent/Avro
   contamination.
4. `BackupRepository` - strong but filesystem-heavy.
5. `DurableWorkflow` - strong but harness complexity is higher.
6. `FeatureFlagControlPlane` - useful reserve candidate; guard against
   bucketing/targeting primitive cascades.

Do not revive the one-file MiniAptly or MiniMigrationManager packets. Their
domains can return only as full ArchiveManager/MigrationManager reproductions.
