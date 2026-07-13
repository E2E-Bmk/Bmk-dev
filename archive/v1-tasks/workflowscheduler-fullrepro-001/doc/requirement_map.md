# FlowLedger Requirement Map

## Requirement IDs

| ID | Capability | Public packet section | Source evidence | Fairness status |
|---|---|---|---|---|
| REQ-artifact-shape | Installable package, importable API, JSON CLI, durable data dir | Required Artifact Shape | Dagu README CLI/server sections; `cmd/`, `api/` | Benchmark-owned, fair |
| REQ-spec-model | Reduced workflow spec with graph/chain, params, steps, dependencies, retries, queues, schedule | Workflow Spec | `README_SCHEMA.md`, `specs/002-yaml-schema.md` | Variant, fair if public |
| REQ-validation | Spec validation is side-effect free and rejects duplicate/unknown dependencies | Spec Validation | `specs/002-yaml-schema.md` | Public semantic behavior |
| REQ-virtual-clock | All scheduling/retry/lease decisions use explicit virtual UTC time | Determinism | Dagu scheduling docs; benchmark variant | Variant, fair if public |
| REQ-schedule-ledger | Scheduler records due slots and catch-up decisions | Schedule Lifecycle | README schedule/catch-up; `internal/service/scheduler/catchup*` | Public chosen policy |
| REQ-overlap-policy | `skip`, `all`, and `latest` overlap policies are public | Schedule Lifecycle | README overlap policy section | Public semantic behavior |
| REQ-queue-lease | Queue entries can be enqueued, claimed, acked, timed out, and reclaimed | Queue Lifecycle | README queues; `internal/dagrun/intake`, `internal/persis/store/queue*` | Public semantic behavior |
| REQ-run-state | Runs and step attempts have durable statuses and terminal transitions | Run State Model | `internal/persis/file/dagrun/*`, API run files | Public semantic behavior |
| REQ-retry | Retry policy materializes retry attempts and next retry times | Retry Semantics | README retry policy; scheduler retry scanner tests | Public semantic behavior |
| REQ-runner | Fake actions deterministically emit success, failure, output, log, or wait result | Runner Semantics | Dagu actions as inspiration; benchmark variant | Variant, fair if public |
| REQ-logs-events | Step logs/events are durable public projections | Logs And Events | README logs; `internal/output`, `eventstore` | Public semantic behavior |
| REQ-history | History/list/detail views agree with run/attempt records | History Projections | API `dagruns*`, file dagrun store | Public semantic behavior |
| REQ-next-run | Next-run projection agrees with schedules, overlap, and virtual clock | Schedule Projections | Scheduler tests and README schedule section | Public semantic behavior |
| REQ-recovery | Recovery classifies partial leases, partial logs, and in-flight runs after restart | Recovery | file-backed state, scheduler zombie/retry behavior | Variant, fair if public |
| REQ-export-import | Export/import preserves specs, schedules, histories, queues, logs, and recovery-visible records | Replay | Dagu file-backed state; benchmark variant | Variant, fair if public |
| REQ-cli-json | CLI returns JSON reports equivalent to API projections | CLI/API | README command list, API files | Benchmark-owned, fair |
| REQ-errors | Public errors are structured and failed operations are atomic | Error Semantics | Source validation tests; benchmark variant | Public if specified |
| REQ-feature-pure | Unit tests isolate module primitives with direct fixtures or mocks | Evaluation Contract | Benchmark design rule | Hidden scoring rule |
| REQ-system-invariants | System tests check cross-projection consistency after multi-step workflows | Evaluation Contract | Benchmark design rule | Hidden scoring rule |

## Source-To-Public Transform

The public packet must state benchmark-owned policies for schedule catch-up,
overlap, retry materialization, lease timeout/reclaim, status rollup, log
ordering, cancellation, and restart recovery. Hidden tests may then assert those
policies because they are public product behavior, not private oracle choices.
