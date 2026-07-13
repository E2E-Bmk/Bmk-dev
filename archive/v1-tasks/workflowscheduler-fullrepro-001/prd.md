# FlowLedger Full-Reproduction PRD

## Product Overview

FlowLedger is a durable local workflow scheduler for teams that need inspectable
automation without an external database or distributed control plane. Users
define workflows as small JSON or YAML documents, start or schedule runs, watch
step history and logs, retry failures, manage queues, and recover after a
process restart.

FlowLedger is inspired by real file-backed workflow schedulers, but it is a
benchmark-owned product with custom public APIs, command names, schemas, and
storage reports.

## Audience

The target user is an operator or application developer who wants to:

- define graph or chain workflows;
- run workflows immediately or on a virtual schedule;
- limit concurrency with durable queues and leases;
- inspect run history, step attempts, logs, events, and next-run reports;
- retry failed steps predictably;
- cancel or recover in-flight runs;
- export/import state for replay or migration.

## Non-Goals

- No Web UI.
- No MCP server.
- No Docker, Kubernetes, SSH, or shell command execution.
- No real wall-clock timing in tests.
- No clone of any upstream command names, private file layout, or full workflow
  schema.
- No distributed worker protocol. Worker behavior is represented by explicit
  queue lease and fake action calls.

## Required Artifact Shape

Candidates must implement an installable Python package named `flowledger` with
the public files in the provided starter skeleton:

```text
pyproject.toml
src/flowledger/
  __init__.py
  api.py
  cli.py
  models.py
  spec.py
  scheduler.py
  queue.py
  retry.py
  runner.py
  logs.py
  history.py
  recovery.py
  export.py
```

Candidates may add private helpers, but they must preserve public module names,
classes, functions, arguments, and return-shape intent.

The package must expose:

- an importable API in `flowledger.api`;
- primitive modules for unit-level behavior;
- a CLI runnable as `python -m flowledger.cli`;
- durable local state in a user-provided directory;
- JSON-compatible public reports.

## Interface-Locked Module Responsibilities

- `models.py`: public records, status names, public error, JSON helpers.
- `spec.py`: workflow spec loading, normalization, validation.
- `scheduler.py`: virtual-clock schedule and overlap decisions.
- `queue.py`: durable queue item and lease primitives.
- `retry.py`: retry policy and next-attempt decisions.
- `runner.py`: deterministic fake action execution.
- `logs.py`: public log/event records and merge ordering.
- `history.py`: run, attempt, queue, next-run, and status reports.
- `recovery.py`: restart scan and recovery report classification.
- `export.py`: export/import payload validation and replay.
- `api.py`: integrated `FlowLedger` facade.
- `cli.py`: JSON CLI over the integrated facade.

## Workflow Spec

The public workflow document is a JSON object or equivalent YAML object:

```json
{
  "name": "release-check",
  "mode": "graph",
  "params": {"ENV": "staging"},
  "queue": "default",
  "max_active_runs": 1,
  "schedule": {
    "every_seconds": 3600,
    "catchup": "latest",
    "overlap": "skip"
  },
  "steps": [
    {
      "id": "test",
      "action": "emit",
      "with": {"message": "ok"},
      "retry": {"limit": 2, "delay_seconds": 10}
    },
    {
      "id": "deploy",
      "depends": ["test"],
      "action": "ok"
    }
  ]
}
```

Public fields:

- `name`: non-empty workflow identifier.
- `mode`: `graph` or `chain`; default `graph`.
- `params`: JSON object.
- `queue`: default queue for runs and steps.
- `max_active_runs`: positive integer, default `1`.
- `schedule`: optional schedule object.
- `steps`: non-empty list of step objects.

Each step has:

- `id`: unique stable identifier.
- `depends`: list of step IDs; only valid in `graph` mode.
- `action`: one of `ok`, `fail`, `emit`, `wait`.
- `with`: JSON object interpreted by the fake runner.
- `retry`: optional retry policy with `limit` and `delay_seconds`.

In `chain` mode, steps run in listed order and explicit `depends` is invalid.
In `graph` mode, steps run when all dependencies have succeeded.

## Virtual Time

All time-dependent behavior uses explicit UTC timestamps passed to the API or
CLI. Tests do not depend on real wall-clock time.

## Schedule And Overlap Policies

Schedules use `every_seconds` and remember the last materialized slot.

Catch-up policy:

- `skip`: ignore slots before `now` except the next future slot.
- `latest`: materialize only the latest missed slot.
- `all`: materialize every missed slot since the last scheduled slot.

Overlap policy:

- `skip`: do not enqueue a new run while a non-terminal run exists.
- `all`: enqueue every due run.
- `latest`: keep the newest due run and cancel older queued due runs.

The schedule ledger is durable and must agree with next-run reports, queue
reports, run history, and recovery reports.

## Queue And Lease Lifecycle

Queue items represent run or step work. A queue item can be:

- `queued`;
- `leased`;
- `acked`;
- `cancelled`;
- `timed_out`.

Claiming a queued item creates a lease with `worker_id`, `leased_at`, and
`lease_seconds`. A lease can be acked only by the owning worker. If virtual time
passes the lease deadline, recovery may mark it timed out and requeue work
according to the public recovery policy.

## Run And Step Status

Run statuses:

- `queued`, `running`, `succeeded`, `failed`, `cancelled`, `waiting_recovery`.

Step statuses:

- `pending`, `queued`, `running`, `succeeded`, `failed`, `skipped`,
  `cancelled`, `retry_wait`.

Status reports are materialized public projections. They must agree with step
attempts, queue leases, logs/events, retry plans, and history.

## Retry Policy

A retry policy has:

- `limit`: maximum number of retries after the initial failure.
- `delay_seconds`: delay before the next attempt.

When a step fails and retries remain, FlowLedger records a retry event, stores a
next-attempt timestamp, and makes the step visible in retry reports. When the
retry becomes due, it returns to the queue. Exhausted retries fail the step and
may fail the run.

## Fake Actions

Hidden tests use deterministic fake actions:

- `ok`: succeeds with no output.
- `fail`: fails with a public error.
- `emit`: succeeds and appends the provided message to logs and step output.
- `wait`: records a waiting event until virtual time reaches `until`.

Candidates do not execute shell commands.

## Logs, Events, And History

FlowLedger exposes:

- run detail report;
- step attempt history;
- queue report;
- next-run report;
- log stream;
- event stream;
- recovery report.

Log/event order is `(recorded_at, sequence)`. Ties preserve insertion order.
Reports must be JSON-compatible and deterministic.

## Recovery

Opening a ledger after restart must scan durable state and classify:

- expired leases;
- running steps without live leases;
- queued items with missing run records;
- retry_wait steps whose retry time is due;
- partial log/event records that can be ignored or finalized.

Recovery must not silently delete history. It returns a public report and then
applies the documented repair actions.

## Export And Import

Export returns a JSON-compatible snapshot containing specs, schedules, runs,
attempts, queue items, logs, events, and recovery markers. Import into an empty
ledger must preserve public reports. Import into a non-empty ledger must fail
atomically.

## CLI

The CLI is JSON-in/JSON-out. It must support equivalent operations to the API:

- `init`;
- `put-spec`;
- `tick`;
- `start`;
- `claim`;
- `complete`;
- `fail`;
- `cancel`;
- `status`;
- `history`;
- `queue`;
- `next-runs`;
- `logs`;
- `events`;
- `recover`;
- `export`;
- `import`.

All commands accept `--store PATH`. Time-dependent commands accept `--now`.

## Evaluation Style

Unit tests isolate public modules with direct fixtures or mocks. Integration
tests cross API/CLI/persistence boundaries. System tests exercise operation
sequences and assert that public projections agree after scheduling, starting,
failure, retry, cancellation, restart, recovery, export, and import.
