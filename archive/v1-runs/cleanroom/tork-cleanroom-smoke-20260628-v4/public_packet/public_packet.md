# TorkWorkflow Public Packet Draft

Build `TorkWorkflow`, a deterministic local workflow engine inspired by public
workflow-runner behavior.

This packet describes the product contract. It does not require source-identical
package structure, SQL schemas, container engines, external brokers, or web UI.

## Product Shape

Provide an installable Python package with:

- importable service API;
- local CLI or HTTP-style facade;
- YAML and JSON job submission;
- local durable store;
- in-memory broker;
- deterministic fake clock;
- deterministic fake/shell runtime;
- job/task/log/progress/schedule/queue/recovery projections.

The implementation should be multi-module. Natural modules include models,
spec parser, datastore, broker, scheduler, planner, worker, runtime, retry,
logs, progress, API, CLI, and recovery.

The starter package's module, class, function, method, parameter, and return
shape signatures are part of the public contract. Hidden tests may import these
starter modules directly to check feature-pure primitives, and may use the
`WorkflowEngine` API or CLI facade for integration and system checks.

## Workflow Model

A job has metadata, inputs, secrets, optional schedule, and tasks. A task may
run a command, declare a variable name, consume previous task outputs, define
pre/post steps, retry, timeout, condition, parallel children, each expansion, or
a subjob.

The runtime is local and deterministic. It may be a fake command registry or a
carefully bounded shell runner. Do not require Docker, Podman, RabbitMQ,
Postgres, S3, webhooks, or network access.

Hidden tests will use this deterministic command subset:

- `echo TEXT`: succeeds and emits `TEXT`;
- `fail TEXT`: fails and emits `TEXT` as the error message;
- `set-progress N`: succeeds and records task progress as integer percent
  `N`;
- `sleep N`: advances logical runtime duration by `N` seconds without real
  waiting.

Implementations may support more commands, but these four commands are public
contract. Shell-specific behavior, quoting tricks, environment variables, and
platform-dependent commands are out of scope.

## Required Public Projections

Expose stable machine-readable views for:

- job list/summary;
- job detail including task tree/history;
- task detail;
- queue status;
- log pages;
- progress;
- schedules;
- recovery report;
- restart/cancel outcome.

All projections must be derived from the same durable workflow history and must
agree after lifecycle operations.

Minimal projection schemas:

- job summary: `id`, `name`, `state`, `created_at`, `updated_at`;
- job detail: all summary fields plus `tasks`, `output`, and optional
  `history`;
- task detail entries: `id`, `job_id`, `name`, `state`, `attempts`, `output`,
  `progress`;
- queue status: `queued` integer and optional detail fields;
- progress: `job_id` and `percent` integer from 0 to 100;
- log entries: `task_id`, `text`, `stream`, `ts`;
- schedule entries: `id`, `name`, `next_due_at`, `last_run_at`, `paused`;
- cancel/restart results: include the affected `id` and resulting `state`;
- recovery report: include `recovered` and `queued` integer counts.

## Core Invariant

After submit, run, retry, timeout, cancel, restart, schedule tick, worker loss,
and reopen, job summary, job detail, task history, outputs, log pages, progress,
queue state, schedule state, and recovery reports must describe the same facts.

## Behavioral Principles

- Terminal job states are stable after completion unless an explicit restart is
  requested.
- A queued task must not be completed twice.
- Failed attempts remain visible in task history.
- Retried tasks keep attempt count, logs, and delay metadata.
- Canceling active work removes future queue visibility and records terminal
  cancellation.
- Reopen/recovery rebuilds runnable queue state from durable history.
- Scheduled ticks must not create duplicate runs for the same schedule instant.
- Parallel/each/subjob parents roll up from child states, not from a separate
  final-result shortcut.

## Non-Goals

- No real container runtime.
- No real distributed broker.
- No real database server.
- No web UI.
- No auth, CORS, or production middleware.
- No exact Tork internal package layout or SQL schema.

## Evaluation Style

Hidden tests will use only public APIs, CLI/facade commands, and persisted
files created by the implementation. They will not inspect private helpers.
Tests will include unit, integration, and system workflows. System workflows
will compare multiple projections after operation sequences.
