# Full-Reproduction Layer0 Continuation

Date: 2026-06-28

This pass continues the corrected source-repo pipeline:

real upstream repository -> source evidence map -> public packet -> cleanroom
candidate reconstruction -> external hidden scoring.

It explicitly rejects hand-written LOC as task-scale evidence.

## Subagent Results

### PgQueueLedger v2 Repair Judge

Verdict: `BLOCK`.

The v2 repair is not ready for candidate model runs.

Blocking defects:

- public packet, starter, and scorer still disagree on public shape:
  `register_entrypoint` and `register_schedule` are scored but not exposed in
  starter signatures;
- CLI checks assert unstated command syntax and JSON schema;
- reference score is 55/55, but the public job event history and dashboard
  snapshot surface promised by the packet are not contract-complete;
- system tests only partially check cross-projection invariants and still miss
  durable history, schedule duplicate detection, recovery reports,
  dashboard snapshots, CLI/API/store agreement, and two-worker concurrency;
- reduced but remaining feature-pure violations exist in worker/retry/store and
  worker/store/completion unit rows;
- candidate packet must remove `__pycache__` before any clean run.

Decision: keep PgQueueLedger as `BUILD`, but candidate runs remain forbidden.
Next repair must align public packet, starter signatures, scorer, and
projection surfaces before another judge.

### TorkWorkflow Scout

Verdict: `BUILD_WITH_RESCOPE`.

Tork has a real full-reproduction surface: job specs, REST/API projections,
coordinator/worker execution, broker queues, datastore-backed jobs/tasks/logs,
schedules, retries, progress, subjobs, parallel/each tasks, and runtime
adapters.

The usable benchmark core is not full production Tork. Exclude Docker/Podman,
RabbitMQ, Postgres, auth middleware, web UI, network webhooks, and cloud
runtime behavior. Keep a deterministic local core with:

- API or CLI facade;
- in-memory broker;
- local durable datastore;
- deterministic fake/shell runtime;
- scheduler;
- worker;
- retry/cancel/restart;
- logs and progress;
- summaries, detail pages, queue views, schedule views, and recovery reports.

Decision: TorkWorkflow is the best current Layer1 entry after PgQueueLedger's
fairness block.

## Newly Network-Scouted Candidates

| Candidate | Source repo | Commit | Files | Nonblank LOC | Verdict |
|---|---|---:|---:|---:|---|
| BackupIndex | `restic/restic` | `75de8b5` | 1389 | 92105 | `BUILD_WITH_RESCOPE` |
| FlagConfigRuntime | `thomaspoignant/go-feature-flag` | `4c9bb15` | 9894 | 465686 | `RESCOPE` |
| ObjectVersionLake | `treeverse/lakeFS` | `4cf60fd` | 2840 | 437074 | `BUILD_WITH_RESCOPE` |

Objective gate files:

- `prospects/backupindex-fullrepro-001/source_candidate_gate.md`
- `prospects/flagconfigruntime-fullrepro-001/source_candidate_gate.md`
- `prospects/objectversionlake-fullrepro-001/source_candidate_gate.md`

### BackupIndex

Source: `restic/restic`.

Product surface: backup repository with snapshots, trees, blobs, pack files,
indexes, locks, restore, check, forget, prune, stats, and repository repair.

Shared fact source: snapshot metadata, tree records, file blobs, pack/index
metadata, locks, forget/prune marks, and check/repair reports.

Public projections:

- snapshot list/detail;
- tree/list/find views;
- restore output;
- repository stats;
- check/verify reports;
- forget/prune plans;
- pack/index list;
- repair/rebuild reports.

Agreement surface:

- pack/index compaction policy;
- parent snapshot selection and change detection;
- stale lock visibility;
- forget group policy;
- prune reachability and missing blob handling;
- restore conflict policy;
- check report severity and repair materialization.

Layer0 risks:

- contamination is medium/high because restic is a well-known public backup
  tool;
- crypto, compression, platform filesystem metadata, and exact repository
  layout can become primitive or private-shape traps;
- the task collapses if it becomes simple copy/restore without packs, indexes,
  forget/prune, and repair projections.

Verdict: `BUILD_WITH_RESCOPE`. Build a benchmark-owned local backup repository
with deterministic content IDs and no encryption/compression fidelity.

### FlagConfigRuntime

Source: `thomaspoignant/go-feature-flag`.

Product surface: feature flag configuration, retrievers, evaluation, relay
proxy, exporters, notifiers, rollout strategies, targeting, and CLI lint/eval.

Shared fact source: flag config files, retriever cache, evaluation contexts,
variation decisions, exporter event batches, notifier diff state, relay
snapshots, and lint reports.

Public projections:

- single flag evaluation;
- all-flags evaluation;
- lint/manifest output;
- relay API responses;
- exporter event files;
- notifier change records;
- refresh/cache status.

Agreement surface:

- percentage rollout bucketing;
- rule priority and default behavior;
- cache refresh boundaries;
- exporter batching;
- notifier diff granularity;
- retriever failure fallback;
- multi-format config normalization.

Layer0 risks:

- contamination is high because OpenFeature and feature-flag rules are common;
- without retained refresh/export/notifier history, this becomes a one-shot
  config evaluator and strong agents will solve it;
- rule parsing, hashing, and YAML/TOML/JSON shape can dominate unit failures.

Verdict: `RESCOPE`. Keep only if the public packet centers on retriever cache,
exporter/notifier lifecycle, and relay consistency, not standalone evaluation.

### ObjectVersionLake

Source: `treeverse/lakeFS`.

Product surface: Git-like object repository for data lakes with repositories,
branches, commits, refs, staging, object metadata, diffs, merges, tags, hooks,
import/export, and garbage collection.

Shared fact source: object store entries, staging area, commit graph, branch
heads, tags, action/hook runs, metadata indexes, and garbage-collection marks.

Public projections:

- repository/branch list;
- tree/object listing;
- diff;
- commit log;
- merge result/conflicts;
- tag/ref reads;
- hook/action audit;
- import/export reports;
- GC/reachability reports.

Agreement surface:

- staging conflict and delete marker semantics;
- branch head update atomicity;
- merge conflict policy;
- hook ordering and failure blocking;
- ref/tag resolution;
- object metadata normalization;
- GC reachability and uncommitted object visibility.

Layer0 risks:

- contamination is medium/high because Git-like semantics are familiar and
  lakeFS is public;
- production lakeFS is too broad, so the benchmark must use a local object
  store and deterministic API;
- exact S3/Hadoop/client behavior would be environment noise.

Verdict: `BUILD_WITH_RESCOPE`. Strong reserve candidate after Tork; keep scope
to local object-versioning core with hooks and GC.

## Current Priority

1. `TorkWorkflow`: proceed to Layer1 skill-driven public packet and rubric.
2. `ObjectVersionLake`: strong reserve, higher scope risk.
3. `BackupIndex`: promising backup/index/repair candidate, watch restic
   contamination and private repository layout.
4. `PgQueueLedger`: repair before any model run.
5. `FlagConfigRuntime`: rescope or hold; standalone evaluator is too easy.

## Next Actions

- Use `skills/tork-task-builder/SKILL.md` to draft TorkWorkflow public packet,
  requirement map, 10+ module starter skeleton, and 50+ check rubric.
- Do not run OpenHands, mini-swe-agent, Qwen, DeepSeek, or Codex candidates on
  PgQueueLedger until the fairness judge is green.
- Keep newly cloned repositories as source evidence only; candidate workspaces
  must not include `.repo_cache`, rubrics, score reports, traces, or iteration
  notes.
