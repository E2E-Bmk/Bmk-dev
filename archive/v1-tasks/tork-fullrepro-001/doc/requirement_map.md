# TorkWorkflow Requirement Map Draft

This is a source evidence seed, not a final rubric. Each row must become one or
more executable checks before candidate runs.

| ID | Public capability | Source evidence | Hidden check direction |
|---|---|---|---|
| TW-REQ-001 | Submit a workflow job from YAML/JSON and expose stable job summary/detail records. | `README.md` Quick Start and REST API; `examples/hello.yaml`; `docs/swagger.json`; `engine/engine_test.go` | API submit/read; summary/detail consistency; deterministic IDs/timestamps via fake clock. |
| TW-REQ-002 | Persist job, task, attempt, output, log, and progress records so projections survive reopen/recovery. | `README.md` architecture and datastore config; `datastore/postgres/postgres.go`; `engine/datastore_test.go` | Durable reopen preserves summaries, details, logs, progress, queue state, and terminal outputs. |
| TW-REQ-003 | Broker and worker coordinate eligible task execution without duplicate completion. | `README.md` distributed mode; `broker/inmemory_test.go`; `engine/broker_test.go`; `engine/worker.go` | Unit broker primitive; system two-worker claim/ack/requeue and queue projection agreement. |
| TW-REQ-004 | Task outputs flow into later expressions and job output. | `README.md` expressions/output sections; `examples/job_output.yaml`; `examples/hello.yaml` | Unit expression substitution; system output propagation across task detail, job output, logs, and summaries. |
| TW-REQ-005 | Parallel and each tasks expand into child task records with correct parent rollup. | `README.md` Parallel/Each; `examples/parallel.yaml`; `examples/each.yaml` | Planner unit checks; system parent progress/status agrees with child histories and queue state. |
| TW-REQ-006 | Conditional tasks can skip without blocking downstream runnable tasks. | `README.md` expressions and conditional tasks; engine tests | Unit condition evaluator; system skip state appears in detail/history while dependent tasks advance. |
| TW-REQ-007 | Subjobs have parent/child lifecycle agreement. | `README.md` Sub-Job Task; `examples/subjob.yaml` | System child terminal state updates parent task, parent job summary, logs, and output. |
| TW-REQ-008 | Retry and timeout policies materialize attempt history and final state. | `README.md` Retry/Timeout; `examples/retry.yaml`; `examples/timeout.yaml`; engine tests | Unit retry/timeout primitives; system retry logs, attempt count, queue visibility, and final status agree. |
| TW-REQ-009 | Cancel and restart mutate active/terminal workflows consistently. | `README.md` REST API cancel/restart; `docs/swagger.json`; engine tests | System cancel/restart across job detail, task history, queue, logs, progress, and summary pages. |
| TW-REQ-010 | Scheduled jobs create run instances while preserving schedule provenance. | `README.md` Scheduled jobs; scheduler examples; datastore scheduled job evidence | Unit due/not-due schedule; system tick creates job, updates schedule state, and avoids duplicate runs. |
| TW-REQ-011 | Log pages, search/filter, and task detail agree on emitted output. | `README.md` API/log features; `broker/log.go`; datastore log retention code | Integration log append/read; system logs match task attempts and job detail after reopen. |
| TW-REQ-012 | Queue, node/worker, and recovery reports agree after worker loss. | `README.md` recovery, nodes, queues; `broker/inmemory.go`; `engine/coordinator.go` | System worker crash/recovery requeues only unfinished work and updates reports. |

Agreement surface:

- datastore layout and projection materialization;
- broker acknowledgement/redelivery policy;
- retry attempt materialization;
- schedule catch-up policy;
- parent rollup for parallel/each/subjobs;
- log page chunking and ordering;
- restart/cancel boundary for terminal vs active tasks;
- recovery replay boundary after reopen.

System invariant target:

After submit, run, retry, timeout, cancel, restart, schedule tick, worker loss,
and reopen, all public projections must agree: job summary, job detail, task
history, output, log pages, progress, queue view, schedule view, and recovery
report.
