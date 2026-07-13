# PgQueueLedger Requirement Map Draft

This is a source evidence seed, not a final rubric. Each row must become one or
more executable checks before candidate runs.

| ID | Public capability | Source evidence | Hidden check direction |
|---|---|---|---|
| PQL-REQ-001 | Jobs have a durable lifecycle: queued, picked/running, successful, exception/failed, canceled, deleted/terminal. | `docs/getting-started/core-concepts.md` job lifecycle; `test/test_cancellation.py`; `test/test_pgqueuer.py` | Unit status transitions; system queue/dashboard/completion consistency. |
| PQL-REQ-002 | Enqueue can be transactional with application data: rollback means no visible job. | `README.md` transactional enqueue; `docs/index.md`; `docs/reference/skip-locked.md` | Integration transaction adapter; system rollback leaves queue, metrics, completion watcher unchanged. |
| PQL-REQ-003 | Workers claim eligible jobs without duplicate processing, respecting entrypoint and global concurrency limits. | `README.md` safe concurrency; `docs/guides/concurrency-control.md`; `test/test_concurrency_limit.py`; `test/test_strict_serialized.py` | Unit concurrency primitives; system two-worker claim race and dashboard counts. |
| PQL-REQ-004 | Deferred jobs are invisible until `execute_after`, then become claimable under virtual time. | `README.md`; `docs/index.md`; `test/test_execute_after.py` | Unit time eligibility; system deferred job affects queue, dashboard, metrics after clock advance. |
| PQL-REQ-005 | Recurring schedules produce due work and track their own last-run/heartbeat state. | `docs/guides/scheduling.md`; `test/test_scheduler.py`; `test/test_scheduler_heartbeat.py` | Unit cron/interval primitive; system schedule tick updates schedules, jobs, logs, dashboard. |
| PQL-REQ-006 | Retry records attempts, delay, and log/history metadata; terminal failure is distinct from retryable failure. | `docs/guides/retry.md`; `docs/guides/reliability.md`; `test/test_retry.py`; `test/test_retry_requeue.py`; `test/test_traceback_record.py` | Unit retry policy; system failure/retry consistency across job row, logs, metrics, completion. |
| PQL-REQ-007 | Stale picked jobs can be recovered after heartbeat timeout without disturbing live workers. | `docs/guides/reliability.md`; `docs/reference/skip-locked.md`; `test/test_heartbeat.py` | Unit heartbeat expiry; system worker crash recovery and replay report. |
| PQL-REQ-008 | Completion watcher observes only terminal states and must agree with job detail/history. | `docs/guides/completion-tracking.md`; `test/test_completion.py` | Integration watcher event stream; system terminal state and dashboard agreement. |
| PQL-REQ-009 | In-memory adapter follows the same public queue/entrypoint/schedule contracts as durable adapter, except documented durability limits. | `README.md` in-memory mode; `test/test_inmemory.py`; `test/test_port_conformance.py` | Unit adapter conformance; system same workflow under two adapters. |
| PQL-REQ-010 | Metrics/dashboard expose queue counts, entrypoint counts, terminal counts, and recent jobs without private storage access. | `README.md` dashboard; `docs/integrations/prometheus.md`; `test/test_metrics_prometheus.py` | Integration metrics; system dashboard/metrics/job-history consistency. |

Agreement surface:

- claim ordering and concurrency gating;
- notification vs polling fallback visibility;
- retry delay and attempt materialization;
- schedule catch-up and heartbeat semantics;
- completion watcher event boundaries;
- dashboard/metrics aggregation timing;
- adapter conformance between durable and in-memory stores.

System invariant target:

After enqueue, claim, heartbeat, retry, schedule, cancel, complete, rollback,
and recovery operations, all public projections must agree: job detail/history,
queue counts, completion watcher, scheduler view, dashboard, metrics, and
adapter-visible state.
