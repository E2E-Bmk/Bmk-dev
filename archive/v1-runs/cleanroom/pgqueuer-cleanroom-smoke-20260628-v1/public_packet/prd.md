# PgQueueLedger PRD Draft

This public PRD draft is source-derived from `janbjorge/pgqueuer` evidence at
commit `b475e4b9afbed1834cd7c478f1eec9d59ec0c5cd`. It defines a benchmark-owned
job queue product. It is not run-ready until hidden rubrics and a reference
implementation exist.

See `candidate_task/public_packet.md` for the current candidate-visible product
packet.

Required product level:

- installable Python package;
- public API plus CLI;
- durable local store plus in-memory adapter;
- deterministic clock, no external DB/broker/network;
- retained job history, schedule history, completion events, dashboard report,
  metrics snapshot, and recovery report;
- operation sequences that keep every public projection consistent.

Required module shape:

- `models`, `store`, `entrypoints`, `scheduler`, `worker`, `retry`,
  `completion`, `metrics`, `recovery`, `api`, and `cli`.

Core system invariant:

After enqueue, transaction rollback, claim, heartbeat, retry, schedule tick,
cancel, completion, and stale-worker recovery, job detail/history, queue
counts, schedule state, completion watcher, dashboard, metrics, and recovery
reports must agree.
