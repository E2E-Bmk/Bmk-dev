# PgQueueLedger Source Repository

Candidate id: `pgqueuer-fullrepro-001`

Source repository: `https://github.com/janbjorge/pgqueuer`

Local source path:
`G:\research\01_agents\swe-e2e\Bmk-dev\.repo_cache\janbjorge__pgqueuer`

Pinned commit: `b475e4b9afbed1834cd7c478f1eec9d59ec0c5cd`

Objective gate:

- tracked files: 190
- nonblank LOC: 21154
- package directories: `pgqueuer/adapters`, `pgqueuer/core`, `pgqueuer/domain`,
  `pgqueuer/metrics`, `pgqueuer/ports`
- docs: `README.md`, `docs/getting-started/core-concepts.md`,
  `docs/guides/completion-tracking.md`, `docs/guides/concurrency-control.md`,
  `docs/guides/reliability.md`, `docs/guides/retry.md`,
  `docs/guides/scheduling.md`, `docs/reference/ports-and-adapters.md`
- tests: `test/test_completion.py`, `test/test_concurrency_limit.py`,
  `test/test_execute_after.py`, `test/test_heartbeat.py`,
  `test/test_inmemory.py`, `test/test_metrics_prometheus.py`,
  `test/test_retry.py`, `test/test_scheduler.py`,
  `test/test_strict_serialized.py`

This task uses PgQueuer as source evidence for a benchmark-owned queue product.
It must not copy exact PostgreSQL schemas, SQL, CLI names, exception classes, or
internal module layout. The public product name is `PgQueueLedger`.

Reference implementation status: built as a calibration implementation at
`runs/pgqueuer-fullrepro-001/solution-reference`.

Reference score: 55/55 on
`runs/pgqueuer-fullrepro-001/score_report_reference_v2_repair.json`.

Candidate runs are still forbidden. The fairness judge blocked this task after
the first reference gate. A v2 repair removed several underspecified/private
shape assertions, moved facade checks out of the unit layer, and added public
concurrency checks. Candidate runs remain forbidden until a new fairness judge
approves the repaired scorer.
