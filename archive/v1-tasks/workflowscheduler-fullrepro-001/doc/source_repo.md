# WorkflowScheduler Source Repository Notes

## Source

- upstream repository: `dagucloud/dagu`
- local cache: `.repo_cache/dagucloud__dagu`
- measured scale: 2601 tracked files, 2516 counted text files, 645085 nonblank
  LOC, including 467376 Go LOC.
- candidate-facing source name: not exposed. Candidate packet describes a
  benchmark-owned product named FlowLedger.

## Source Evidence Used

- `README.md`: Dagu is a self-contained workflow scheduler with declarative
  workflow files, Web/UI/API management, queues, retries, schedules, logs, local
  file-backed state, CLI commands, worker/coordinator deployment, and persistent
  state directories.
- `README_SCHEMA.md`: workflow shape includes graph/chain execution, params,
  runtime fields, step dependencies, retry policies, outputs, queue/enqueue
  actions, and structured action examples.
- `specs/001-project.md` and `specs/002-yaml-schema.md`: project/schema
  boundaries and validation side-effect rules.
- `internal/service/scheduler/*`: scheduler, catch-up, queue dispatcher,
  retry scanner, enqueue, zombie detection, and executor behavior.
- `internal/dagrun/intake/*`: local queue intake.
- `internal/persis/file/dagrun/*`: run history, attempts, retry candidates,
  latest attempt, and persisted run data.
- `internal/persis/store/queue*`: queue index, cursor, and item behavior.
- `internal/persis/file/eventstore/*`: event log storage and query behavior.
- `internal/service/frontend/api/v1/dags*.go`, `dagruns*.go`, `queues*.go`,
  `events*.go`: API projections for workflows, runs, queues, and events.

## Benchmark Variant

FlowLedger is not a Dagu clone. It keeps the product shape of a local durable
workflow scheduler but uses benchmark-owned names, reduced schemas, and
deterministic fake step actions.

Included:

- reduced JSON/YAML workflow spec;
- graph and chain execution;
- virtual clock schedules and catch-up policy;
- local durable run, attempt, queue, schedule, log, and event state;
- importable API and JSON CLI;
- restart/recovery reports;
- queue leases and retry plans;
- public projection reports for status, history, queue, next-run, logs/events,
  and recovery.

Excluded:

- Web UI, MCP, installers, Docker/Kubernetes/SSH execution, remote worker
  protocol, exact Dagu YAML schema, exact CLI names, private file layout, and
  exact Go package/API names.

## Layer-1 Status

This task currently has a public packet, requirement map, starter skeleton, and
hidden rubric draft. It does not yet have executable hidden test code or a
reference implementation. Do not run candidate models until those exist and the
reference passes unit=100%, integration=100%, and system=100%.
