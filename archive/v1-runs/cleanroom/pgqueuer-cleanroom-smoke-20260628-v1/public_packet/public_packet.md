# PgQueueLedger Public Packet Draft

`PgQueueLedger` is a small durable job-queue package with a public Python API
and CLI. It is inspired by database-backed queues, but uses benchmark-owned
names and schemas. Implement the package in `src/queueledger`.

## Product Shape

Provide an installable Python package with:

- importable API in `queueledger.api`;
- CLI entrypoint `queueledger`;
- durable local store and in-memory adapter;
- deterministic virtual clock support for tests;
- public reports for dashboard, metrics, schedules, completion, and recovery.

Do not require PostgreSQL, Redis, Docker, network services, or real wall-clock
sleep. Persistent behavior may use files or SQLite under a caller-provided
directory.

## Core Concepts

A job has an id, entrypoint, payload, priority, status, attempt count,
`execute_after`, heartbeat timestamp, creation/update timestamps, and log
entries. Terminal statuses are `successful`, `exception`, `failed`,
`canceled`, and `deleted`.

Entrypoints are named handlers. Workers claim eligible jobs for registered
entrypoints. Concurrency limits apply per entrypoint and globally.

Schedules produce jobs from recurring definitions. The scheduler must track
last run and heartbeat state so duplicate schedule execution can be detected.

Completion watchers observe terminal status changes. Dashboard and metrics
reports must be derived from public queue state and must agree with job
history.

## Required Workflows

- transactional enqueue and rollback;
- enqueue, claim, heartbeat, complete;
- failure with retry delay and attempt history;
- terminal failure after retry exhaustion;
- cancel before and after claim;
- deferred job via `execute_after`;
- recurring schedule tick;
- stale worker heartbeat recovery;
- in-memory and durable adapter conformance;
- dashboard, metrics, and completion watcher agreement.

## Public Module Boundaries

Use the starter skeleton public signatures. Hidden unit tests may import these
modules directly. Hidden system tests will prefer `QueueLedger` and the CLI.

- `models.py`: dataclasses/enums for jobs, schedules, reports, and events.
- `store.py`: durable and in-memory store contracts.
- `entrypoints.py`: handler registry and validation.
- `scheduler.py`: schedule registration and deterministic due-work logic.
- `worker.py`: claim/heartbeat/complete/fail/cancel workflows.
- `retry.py`: retry policy and terminal failure decisions.
- `completion.py`: terminal-state watcher.
- `metrics.py`: counters and dashboard projections.
- `recovery.py`: stale heartbeat and partial-write recovery reports.
- `api.py`: high-level facade.
- `cli.py`: command-line boundary.

## Non-goals

Do not implement a web UI, Prometheus server, tracing integrations, Postgres
SQL compatibility, external broker integration, or real distributed locks.

## Evaluation Style

Unit checks isolate module contracts. Integration checks cross API, CLI, store,
and adapter boundaries. System checks run operation sequences and assert that
job history, queue counts, schedules, completion watcher, dashboard, metrics,
and recovery reports stay consistent.
