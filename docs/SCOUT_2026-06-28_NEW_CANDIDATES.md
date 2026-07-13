# New Candidate Scout

Date: 2026-06-28

Purpose: collect fresh candidate domains after the Layer-0 structural-audit reset. These are not accepted tasks. They are prospects that must still pass a task-specific enrichment brief, reference gate, candidate gate, and fairness judge.

## Source-Grounded Checks

- Oban exposes persistent job processing surfaces such as scheduled jobs, cancellation, uniqueness, triggered execution, and lifecycle/telemetry events. Source: https://hexdocs.pm/oban/Oban.html
- Aptly exposes mirrors, local repositories, immutable snapshots, published repositories, switching, cleanup, and graph-like repository operations. Source: https://www.aptly.info/doc/overview/
- Bazel remote caching separates action cache metadata from content-addressable storage blobs. Source: https://bazel.build/remote/caching
- `bazel-remote` adds a disk-backed remote cache with size limits and LRU enforcement. Source: https://github.com/buchgr/bazel-remote
- Alembic exposes revision graph workflows including branches, heads, current, history, upgrade, downgrade, merge, and stamp. Sources: https://alembic.sqlalchemy.org/en/latest/branches.html and https://alembic.sqlalchemy.org/en/latest/api/commands.html

## Build-Leaning Prospects

### MiniJobLedger

- Inspiration: Oban-style database-backed job processing.
- Public surface: enqueue, schedule, cancel, claim, complete, fail, retry, inspect queues, inspect job history, inspect metrics, register cron entries.
- Durable state: retained job rows, attempt history, cron insertion ledger, cancellation markers, uniqueness windows, lifecycle event stream.
- Public projections: job detail/history, queue counts, cron next-run view, uniqueness/conflict report, metrics rollups, event stream.
- Agreement surface: local schema and indexes are free, but job row state, event log, queue counts, cron ledger, uniqueness windows, and metrics must agree after lifecycle transitions.
- Why unit is not enough: retry math, cron parsing, and enqueue primitives can pass while system rows expose stale metrics, duplicate cron inserts, failed insert rollback, and uniqueness drift across retained history.
- Risks: medium known-pattern risk from Oban/Celery/Sidekiq. Avoid exact Oban schemas and names.
- Verdict: `BUILD`.

### MiniAptly

- Inspiration: aptly-style Debian archive snapshot manager.
- Public surface: add/remove package artifacts, import mirror, create/merge/filter snapshots, publish/switch repositories, list/search/show, cleanup, recover, graph.
- Durable state: package pool, repo DB, immutable snapshots, published distribution/component state, pending publish journal, recovery journal.
- Public projections: package index files, release metadata with hashes, search/show references, published tree, snapshot diff/list, graph output, cleanup dry-run report.
- Agreement surface: storage layout is free, but package identity, version, architecture, checksum, snapshot membership, published component, and unreferenced-file reachability must agree across all projections.
- Why unit is not enough: control parsing and checksum formatting do not prove snapshot immutability, publish switching, refcount cleanup, graph consistency, or crash recovery.
- Risks: moderate known-pattern risk, but the mirror/local/snapshot/publish lifecycle is less one-shot than static package-index generation.
- Verdict: `BUILD`; strongest archive/recovery prospect.

### MiniBuildCache

- Inspiration: Bazel remote cache / bazel-remote.
- Public surface: put/get/head CAS blobs, put/get action results, status, namespace listing, cache size limits, eviction/audit log.
- Durable state: on-disk blob store, action-result index, access times, insertion order, evicted keys, failed upload markers.
- Public projections: CAS lookup, action-cache lookup, status counters, eviction/audit log, namespace hit/miss report.
- Agreement surface: internal layout is free, but every action-cache entry must reference existing CAS digests; status must match reachable stored bytes; LRU/access order must remain coherent after reads, writes, overwrites, failed writes, and eviction.
- Why unit is not enough: digest validation and size accounting can pass while system rows expose dangling action results, stale status counters, and incorrect eviction order.
- Risks: medium known-pattern risk. Use a compact custom protocol, not exact REAPI.
- Verdict: `BUILD`.

### MiniMigrationManager

- Inspiration: Alembic-style revision graph plus applied database state.
- Public surface: init, create revision, heads, history, current, upgrade, downgrade, stamp, merge, dry-run plan.
- Durable state: migration files, revision DAG, database version table, applied-step ledger, schema snapshot, rollback marker.
- Public projections: revision graph/history, current DB version(s), schema introspection, upgrade/downgrade plan, branch-head report, dry-run SQL.
- Agreement surface: migration file format is free, but revision graph, applied version table, schema state, and generated plans must agree after branch merges, partial upgrades, stamping, downgrade, and failed transactional migration.
- Why unit is not enough: DAG traversal and schema operation units can pass while `history`, `current`, schema state, and downgrade/merge plans drift.
- Risks: medium known-pattern risk; avoid an exact Alembic clone by using deterministic toy DDL and custom migration files.
- Verdict: `BUILD`.

### MiniSchemaRegistry

- Inspiration: schema registry with subject/version compatibility, references, soft deletes, and lookup surfaces.
- Public surface: register schema, list subjects, list versions, get by id/version, lookup existing schema, set global/subject compatibility, compatibility check, soft delete/restore.
- Durable state: subject version history, global schema-id table, compatibility config history, tombstones, schema references.
- Public projections: subject list, version list, id lookup, compatibility result, referenced-by reverse index, deleted-inclusive views.
- Agreement surface: parser/storage are free, but canonical-equivalent schemas must reuse IDs, subject versions must advance only for new schema content, compatibility must apply subject override/global fallback, and deletes must affect all list/get/reverse-reference views consistently.
- Why unit is not enough: schema parsing and compatibility units do not prove id reuse, subject-local versioning, config override behavior, deletes, and reverse-reference consistency.
- Risks: medium-high known-pattern risk if too close to Confluent/Avro. Use a custom record-schema language.
- Verdict: `BUILD_WITH_RESCOPE`.

## Conditional Prospects

### MiniRestic

- Inspiration: restic/Borg-style deduplicating backup repository.
- Concern: content-addressed backup is a known pattern and can be recomputed unless cached indexes, failed prune ordering, stale index rebuild, and orphan recovery are public.
- Verdict: `BUILD_WITH_STRONG_ANTI_RECOMPUTE_LIFECYCLE`.

### MiniCondaIndex

- Inspiration: conda channel indexing plus incremental repodata/JLAP-like patch stream.
- Concern: static `conda index` is one-pass. Only incremental patch replay, tombstones, client cache recovery, and reverse query state make it promising.
- Verdict: `BUILD_ONLY_AROUND_INCREMENTAL_STATE`.

### Redis-Style Delayed Queue

- Inspiration: BullMQ/Sidekiq delayed, repeat, retry, and dead-letter queues.
- Concern: high known-pattern risk and Redis data-structure prior. It can work only if retained attempt events, stale lock recovery, repeat config history, and manual dead-job actions are public.
- Verdict: `BUILD_WITH_CONTAMINATION_CONTROL`.

## Rejected Or Deprioritized

### APScheduler/RQ-Style Lightweight Scheduler

- Reason: current schedule, trigger math, and registries are too easy to recompute from current job definitions unless retained execution history and cross-node duplicate suppression are added.
- Verdict: `REJECT_AS_IS`.

### Plain Notebook / Expression Evaluator

- Reason: parser/evaluator/environment tasks collapse to one AST plus environment dict. Consider only as a notebook workspace with cell dependency graph, cached values, diagnostics, undo, export/import, and update/delete propagation.
- Verdict: `REJECT_AS_PLAIN_EVALUATOR`.

## Recommended Build Order

1. `MiniAptly`
2. `MiniMigrationManager`
3. `MiniJobLedger`
4. `MiniBuildCache`
5. `MiniSchemaRegistry`

Each selected prospect must next get a task-specific enrichment brief before any PRD or rubric is written.
