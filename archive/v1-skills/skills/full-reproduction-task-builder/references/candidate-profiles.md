# Candidate Profiles

Use these profiles after a candidate passes Layer-0 audit. They define the
agreement surface, unit template, system template, and oracle plan required by
the benchmark loop.

## JobLedger

Agreement surface:

- Shared fact source: job rows, attempt ledger, cron ledger, uniqueness windows,
  event stream, queue state.
- Free parameters: claim ordering, retry materialization, uniqueness window
  representation, event ordering, metrics aggregation timing.
- Public invariant: queue counts, metrics, events, and job history must agree
  after enqueue, schedule, claim, complete, fail, retry, cancel, cron insert,
  and recovery.

Unit template:

- Store: insert/update/read jobs, status transitions, error paths.
- Scheduler: due-time selection, virtual clock edges, invalid schedules.
- Retry: backoff math, max-attempt edges, terminal failure.
- Uniqueness: conflict windows, replacement policy, expired conflicts.
- Metrics/events: single event emission, aggregation primitives, malformed
  event rejection.

System template:

- Enqueue/claim/complete sequence keeps history, queue counts, events, and
  metrics consistent.
- Failed job schedules retry; retry ledger, pending queue, metrics, and event
  stream agree.
- Cron tick inserts at most one job per slot across restart/replay.
- Cancel or uniqueness conflict removes visibility from queue while retaining
  correct audit/history.
- Recovery from partial write rolls forward or rolls back without drifting
  queue counts, events, and metrics.

Oracle plan:

- Use Oban docs/tests as behavior inspiration for retained jobs, retries,
  cron, uniqueness, and telemetry.
- Use benchmark-defined storage schema and CLI/API names to avoid exact clone
  contamination.
- Validate reference with deterministic virtual clock and filesystem or SQLite
  state.

## BuildCache

Agreement surface:

- Shared fact source: CAS blobs, action-cache entries, namespace metadata,
  access-order ledger, failed-write markers, eviction log.
- Free parameters: access-order updates, missing-blob handling, namespace
  encoding, eviction victim selection, failed-write recovery.
- Public invariant: action-cache entries only point to existing CAS blobs;
  status counters, namespace reports, audit logs, and lookup results agree
  after uploads, reads, overwrites, failed writes, and eviction.

Unit template:

- Digest: hash/size validation, malformed digest errors.
- CAS: put/get/missing/blob-size primitives.
- Action cache: insert/lookup/update with missing CAS references rejected.
- Namespace: isolation and conflict behavior.
- Eviction/status: single victim choice, byte accounting, audit event emission.

System template:

- Upload blobs and action result; CAS lookup, AC lookup, status, and audit
  projections agree.
- Overwrite or touch entries updates LRU/access ledger and eviction victims.
- Failed blob write leaves no reachable AC entry and records recovery marker.
- Eviction removes only unreachable or selected blobs and keeps AC/status
  coherent.
- Export/import or restart replays status and namespace reports exactly.

Oracle plan:

- Use bazel-remote docs/source/tests for CAS/action-cache/status/eviction
  concepts.
- Do not clone Bazel REAPI exactly; define custom local HTTP/CLI schemas.
- Use filesystem-backed reference with deterministic timestamps.

## SchemaRegistry

Agreement surface:

- Shared fact source: subject version history, global schema-ID table,
  compatibility config history, tombstones, reference graph.
- Free parameters: canonicalization, ID reuse, config fallback, tombstone
  visibility, reverse-reference timing.
- Public invariant: equivalent schemas reuse global IDs; subject versions
  advance only for new content; compatibility, deletes, and references update
  all list/get/reverse/report views consistently.

Unit template:

- Parser/canonicalizer for benchmark-defined schema language.
- Compatibility primitive checks: backward/forward rules and errors.
- Subject store: version append, duplicate detection, tombstone primitives.
- ID table: global ID reuse and lookup failures.
- Reference graph: forward/reverse edge creation and deletion checks.

System template:

- Register equivalent schemas across subjects; ID lookup, subject versions, and
  audit report agree.
- Subject-level config overrides global config and compatibility report explains
  the decision.
- Delete/tombstone changes normal list/get but deleted-inclusive views and
  audit history remain consistent.
- Referenced-by reverse index updates after register/delete/reimport.
- Export/import replay preserves IDs, versions, configs, tombstones, and
  compatibility outcomes.

Oracle plan:

- Use Confluent schema-registry as product inspiration for subjects, versions,
  IDs, compatibility, and references.
- Avoid Avro/Confluent API contamination by defining a custom record schema
  language and custom CLI/API.
- Make canonicalization and compatibility public in PRD to avoid hidden oracle
  ambiguity.

## BackupRepository

Agreement surface:

- Shared fact source: content-addressed packs, manifest index, snapshot graph,
  retention policy state, repair log, restore plan.
- Free parameters: pack layout, manifest grouping, retention marking, repair
  quarantine, restore conflict handling.
- Public invariant: snapshots, manifests, reachable content, prune output,
  verify/repair reports, and restored files agree after backup, delete, prune,
  corrupt, repair, and restore.

Unit template:

- File-tree hashing and ignore rules.
- Pack write/read and digest errors.
- Manifest insert/list/delete.
- Retention marking and expiry.
- Restore conflict primitive behavior.

System template:

- Backup two overlapping trees; snapshot list, manifest index, reachable bytes,
  and restore output agree.
- Delete/prune removes only unreachable content and reports exact reachability.
- Corrupt pack is detected by verify and handled by repair/quarantine.
- Policy update changes prune plan without mutating snapshots until apply.
- Export/import repository metadata preserves snapshot and restore behavior.

Oracle plan:

- Use Kopia docs/source/tests for backup repository lifecycle concepts.
- Do not copy Kopia repository formats; use benchmark-defined pack/manifest
  files with public schemas.

## DurableWorkflow

Agreement surface:

- Shared fact source: workflow event history, timers, activity attempts, worker
  queues, signal/query records, retry state.
- Free parameters: event schema, timer ordering, retry materialization, signal
  buffering, query consistency.
- Public invariant: replay from history reproduces workflow status and query
  results; pending work and retry schedules match history after timers,
  failures, signals, and worker restarts.

Unit template:

- Event append/read and malformed event rejection.
- Virtual timer scheduling and ordering.
- Activity retry backoff and terminal failures.
- Signal buffering and query snapshots.
- Worker task leasing/ack primitives.

System template:

- Workflow with activity failure/retry keeps history, pending work, and query
  output coherent.
- Timer fires under virtual clock and replay reproduces result.
- Signal before/after wait is buffered exactly once and visible in history.
- Worker restart replays from durable history without duplicate completion.
- Export/import history preserves status, query result, and pending timers.

Oracle plan:

- Use go-workflows and durable workflow docs as inspiration.
- Keep deterministic virtual clock; avoid real async timing in hidden tests.

## WorkflowScheduler

Agreement surface:

- Shared fact source: workflow specs, run records, step attempts, queue leases,
  schedules, log/event records, and history indexes.
- Free parameters: schedule catch-up policy, retry event materialization,
  step-output capture, queue leasing, status rollup timing, log ordering, and
  restart recovery boundaries.
- Public invariant: workflow status, step attempts, queue leases, logs, next
  runs, and history must agree after schedule, start, failure, retry, cancel,
  restart, and recovery.

Unit template:

- Spec parser: graph/chain step order, dependency validation, invalid IDs,
  defaults, params, and legacy-compatible fields that are public.
- Scheduler: virtual clock next-run calculation, catch-up windows, max-active
  limits, and disabled schedules.
- Queue/lease: enqueue, claim, ack, timeout, worker selector match/miss, and
  duplicate lease rejection.
- Retry/status: retry policy primitives, terminal status rules, cancel/skip
  primitives, and status rollup from step attempts.
- Logs/events: append/read ordering, structured step output capture, malformed
  event rejection, and log truncation policy when public.

System template:

- Graph workflow with independent and dependent steps keeps run status, step
  attempts, logs, queue leases, and history coherent.
- Failed step retries under virtual time; retry plan, event stream, step
  history, and status rollup agree.
- Scheduled workflow catches up or skips according to public policy after
  downtime, without duplicate run records.
- Cancel or approval/skip workflow updates queue visibility, logs, history,
  and status consistently.
- Restart/recovery replays persisted specs, queues, leases, logs, and run
  history without duplicate completion or lost terminal state.

Oracle plan:

- Use Dagu README, README_SCHEMA, examples, docs, and source tests for workflow
  specs, file-backed state, queues, retries, logs, and server/API concepts.
- Use benchmark-owned command/API names and a deterministic local runner; do
  not clone Dagu UI, exact YAML formatting, MCP endpoints, or private file
  layout.
- Build hidden checks around public projections: run status, step history,
  queue state, next-run view, log stream, and recovery report.

## EventRuntime

Agreement surface:

- Shared fact source: event records, function definitions, run metadata,
  step attempt history, durable step outputs/errors, pause/sleep/wait records,
  cancellation/replay links, queue items, and trace/log records.
- Free parameters: checkpoint-vs-yield materialization, opcode/state model,
  queue partitioning, retry/no-retry event emission, cancellation timing,
  wait-event matching, replay lineage, and history grouping.
- Public invariant: API run status, trace/history views, debug queue output,
  replay/cancel records, and step output projections must agree after event
  ingestion, execution, retry, sleep/wait, cancellation, replay, and restart.

Unit template:

- Event/function registry: event match, function sync, invalid function specs.
- State/checkpoint: append/read step output, error, sleep, wait, and terminal
  markers without running the executor.
- Queue: enqueue, claim, ack, partition/backlog, duplicate item rejection.
- Retry/cancel/replay: primitive eligibility and lineage rules under a virtual
  clock.
- History/trace: append and read normalized public events without UI grouping.

System template:

- Event creates a run; API status, queue, trace, history, and debug views agree.
- Failed step retries; retry count, queued work, step history, and final status
  agree.
- Sleep/wait suspends and resumes without duplicate completion after restart.
- Cancellation hides queued work while preserving audit/history.
- Replay links old/new runs and keeps output/history/trace projections coherent.

Oracle plan:

- Use Inngest docs, dev-server architecture notes, API docs, and lifecycle tests
  for durable event runtime concepts.
- Use benchmark-owned API names and record schemas; do not score SDK protocol
  conformance or vendored implementation details.
- Use a deterministic virtual clock and local file/SQLite state.

## StreamPipeline

Agreement surface:

- Shared fact source: pipeline config, component registry, config schema,
  plugin metadata, lint/test metadata, checkpoint state, runtime ack ledger,
  and generated docs catalog.
- Free parameters: YAML normalization, registry/schema representation, lint
  severity, unit-test target addressing, docs generation order, ack/backpressure
  handling, checkpoint/cache layout, and cloud-purity policy.
- Public invariant: CLI lint/test/dry-run, schema API, generated docs,
  component catalog, readiness, metrics, and checkpoint/resume projections must
  agree after config load, test, run, failure, restart, and resume.

Unit template:

- Schema registry: component registration, duplicate handling, required fields.
- Config parser/linter: isolated warnings/errors and normalization.
- Unit-test runner: input/output assertions and mock resources without runtime.
- Checkpoint/cache: single source offset save/load and malformed state errors.
- Ack/backpressure: primitive success/failure accounting.

System template:

- Config with labeled components produces matching CLI lint, schema API, docs,
  and catalog output.
- Unit tests run against selected processors without mutating runtime state.
- Runtime failure preserves at-least-once delivery and health/readiness state.
- CDC-style source snapshots then resumes from checkpoint after restart.
- Cloud-purity policy appears consistently in lint, docs, and schema surfaces.

Oracle plan:

- Use Redpanda Connect docs, public schema APIs, config examples, docs generator,
  and CDC/checkpoint source tests for behavior.
- Avoid exact Benthos naming, `_benthos_test` fixtures, line-number traps, and
  full connector reimplementation.
- Define benchmark-owned connector names and deterministic local sources/sinks.

## GatewayConfig

Agreement surface:

- Shared fact source: route/service/upstream/plugin/global-rule resources,
  schemas, reference graph, standalone config versions, config digests, and
  runtime routing/plugin caches.
- Free parameters: PATCH merge rules, resource versioning, route-vs-service
  precedence, plugin merge order, delete/reference policy, route priority,
  TTL/digest handling, standalone replay materialization.
- Public invariant: Admin API resources, schema validation, standalone config
  view, runtime route/upstream/plugin behavior, reference checks, and version
  reports must agree after create, patch, delete, force-delete, reload, and
  request routing.

Unit template:

- Schema validation: route/service/upstream/plugin/global-rule primitives.
- Resource store: create/read/patch/delete/version with direct fixtures.
- Reference graph: service/upstream/plugin references and force-delete rules.
- Route matcher: priority, host/path/method predicates without runtime server.
- Plugin merge: global, service, plugin-config, and route-local precedence.

System template:

- Create service/upstream/route/plugin resources; Admin API and runtime request
  routing agree.
- PATCH updates visible resource fields, versions, config digest, and runtime
  behavior without losing unrelated fields.
- Delete/reference checks prevent dangling runtime routes unless force-delete is
  public and audited.
- Standalone config reload increments version only when effective config changes.
- Global and route-local plugins execute in public precedence order.

Oracle plan:

- Use APISIX docs, Admin API docs, terminology pages, admin/resource source,
  standalone tests, and plugin merge behavior as inspiration.
- Use benchmark-owned resource names and error categories; avoid APISIX exact
  strings, private key layouts, and modifiedIndex traps.
- Implement deterministic in-process request simulation instead of real Nginx.

## TelemetryPipeline

Agreement surface:

- Shared fact source: raw/effective config snapshots, component factories,
  pipeline graph, receiver/processor/exporter state, queued export batches,
  retry outcomes, readiness transitions, and service metrics/logs.
- Free parameters: config expansion/redaction, component ID normalization,
  startup order, queue partitioning, batch merge/split policy, retry persistence,
  readiness timing, and metric aggregation.
- Public invariant: config snapshots, pipeline readiness, factory list,
  queued exporter state, retry/batch outcomes, and service metrics/logs agree
  after load, startup, send failure, retry, shutdown, and restart.

Unit template:

- Config loader: raw/effective snapshots and redaction.
- Component registry: receiver/processor/exporter factories and invalid IDs.
- Queue/batch: offer, capacity, merge/split, partition, and shutdown drain.
- Retry: backoff, permanent failure, retryable failure, persistence primitive.
- Readiness/metrics: single transition and counter updates.

System template:

- Config loads a pipeline; raw/effective config, component list, and readiness
  views agree.
- Receiver sends records through processors to exporter; metrics/logs reflect
  the same counts.
- Exporter failure queues batches; retry drains queue and updates metrics.
- Shutdown/restart preserves unsent persistent queue data.
- Config reload changes readiness and component graph without stale exporters.

Oracle plan:

- Use OpenTelemetry Collector docs/examples/source for pipeline, queue/batch,
  retry, config snapshot, and readiness concepts.
- Use benchmark-owned local telemetry records and schemas; do not clone OTLP or
  exact Collector interfaces.
- Mark as `BUILD_WITH_RESCOPE` until the public packet removes OTEL-specific
  protocol contamination.
