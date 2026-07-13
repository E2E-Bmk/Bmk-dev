---
name: tork-task-builder
description: Build, audit, or iterate the TorkWorkflow full-reproduction SWE-E2E benchmark derived from runabol/tork. Use when editing TorkWorkflow Layer0 audits, public packet, requirement map, starter skeleton, hidden rubrics, reference gate, cleanroom harness, or fairness judge notes.
---

# Tork Task Builder

## Rule

Treat `runabol/tork` as upstream product evidence, not as code to copy. Build
the benchmark-owned product `TorkWorkflow`.

Candidate-visible files are limited to the public packet, starter skeleton, and
an empty solution directory. Never expose source repo internals, hidden rubrics,
score reports, prior traces, or reference code to candidate model runs.

## Scope

Build a deterministic core workflow engine:

- YAML/JSON job definitions;
- importable API plus local HTTP-style facade or CLI;
- in-memory datastore plus durable local persistence;
- in-memory broker/queue;
- deterministic fake or shell runtime;
- scheduler, worker, retry, cancel, restart, logs, progress, and task outputs;
- public summaries, detailed reads, execution pages, queue views, log pages,
  schedule views, and recovery reports.

Exclude real Docker/Podman, RabbitMQ, PostgreSQL, web UI, auth middleware,
network webhooks, CORS, and cloud integrations unless a later public packet
explicitly makes them benchmark-owned local fakes.

## Agreement Surface

Shared fact source:

- job definitions;
- durable job/task records;
- task attempts and runtime output records;
- broker queue events;
- schedule records;
- node/worker heartbeat records;
- log chunks;
- progress snapshots;
- restart/cancel/recovery events.

Free parameters with multiple plausible implementations:

- datastore: normalized record tables, append log, snapshot files;
- broker: event queue, polling worker, deterministic event loop;
- runtime: shell subprocess, fake command registry, callback executor;
- retry materialization: mutate task row, append attempt ledger, separate retry queue;
- schedule catch-up: one tick, latest-only, or full catch-up;
- log storage: chunked pages, append-only lines, task-local log files;
- parent status rollup: eager propagation or report-time aggregation.

Public invariants must choose one policy and expose it consistently.

## Unit Template

Keep unit tests feature-pure:

- job spec parsing and validation;
- DAG dependency expansion;
- condition/each/parallel/subjob planning primitives;
- state transition rules;
- retry/backoff and timeout rules;
- broker enqueue/dequeue acknowledgement;
- log page append/read primitives;
- progress aggregation primitive;
- schedule due/not-due decisions;
- datastore put/get/list/update primitives.

Unit setup may use direct constructors or mocks. Do not run a full workflow just
to test a parser, broker, or retry primitive.

## Integration Template

Cross one boundary at a time:

- API facade with datastore;
- scheduler with broker;
- worker with broker and runtime;
- log writer with log reader;
- retry planner with datastore;
- durable reopen with job/task/log projections;
- CLI/API output with service layer.

Avoid exact private file layout, exact error text, or internal source package
names. Test public behavior and stable machine-readable projections.

## System Template

Every system row must name a cross-feature contract:

- submit -> queue -> worker -> completion keeps job detail, summary, task
  history, logs, progress, and queue empty state consistent;
- retry path keeps attempt ledger, delayed visibility, logs, and final status
  consistent;
- cancel propagates to active tasks, queue visibility, logs, and summaries;
- parallel/each tasks update parent progress and final status correctly;
- conditional skip advances downstream dependencies without fake success logs;
- subjob parent status agrees with child job terminal state;
- schedule tick creates run instances and preserves schedule provenance;
- restart/recovery rebuilds queue and projections from durable state.

System checks should use operation sequences through public APIs and compare
multiple public projections, not private datastore objects.

## Oracle Plan

Use source evidence:

- `README.md`: workflow/job engine overview and public examples;
- `examples/*.yaml`: job specs for hello, parallel, each, pre/post, outputs,
  and composed jobs;
- `docs/swagger.json`: REST API surface and response shapes;
- `engine/*_test.go`: coordinator, broker, datastore, and execution behavior;
- `broker/*_test.go`: queue semantics;
- `datastore/*_test.go`: persistence semantics;
- `runtime/*` and tests: runtime output and lifecycle evidence;
- `middleware/*` only for rescope boundaries, not strict hidden behavior.

Benchmark variants:

- deterministic local runtime;
- no container engine;
- no external DB or broker;
- benchmark-owned API names are allowed;
- no exact Tork source layout, SQL schema, or internal package names.

## Current Gate

Layer0 verdict: `BUILD_WITH_RESCOPE`.

Completed:

- write a source evidence map with file/test/example citations;
- write a public packet from docs/examples/API behavior;
- create a 10+ module starter skeleton justified by product surface;
- implement 50+ executable checks with unit/integration/system layers;
- build a reference implementation that passes 100%;
- run a cleanroom leakage scan.

Before candidate runs:

- pass independent fairness judge;
- keep candidate runs inside `runs/cleanroom/tork-cleanroom-smoke-20260628-v5`
  or a newer cleanroom generated from the same public packet;
- save full agent trajectory, final solution tree, score report, leakage scan,
  and failure cluster analysis.
