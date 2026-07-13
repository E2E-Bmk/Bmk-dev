# FlowLedger Public Packet

FlowLedger is a durable local workflow scheduler. Implement the Python package
`flowledger` from the provided starter skeleton.

The product contract is in `prd.md` in the task root. In cleanroom runs this
file is the candidate-visible public packet; it intentionally repeats the
public requirements needed to implement the task.

Required package shape:

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

Implement:

- reduced workflow specs with graph/chain mode, params, steps, dependencies,
  retries, queues, schedules, overlap, and catch-up;
- explicit virtual time for schedules, retry, waits, and leases;
- durable local state under a user-provided store directory;
- importable `FlowLedger` API and `python -m flowledger.cli` JSON CLI;
- deterministic fake actions: `ok`, `fail`, `emit`, `wait`;
- public reports: status, history, queue, next-runs, logs, events, recovery,
  export/import.

Important public policies:

- Schedule catch-up is `skip`, `latest`, or `all`.
- Overlap is `skip`, `latest`, or `all`.
- Queue leases have owner, lease time, and timeout.
- Retry rows/events are durable and visible before the retry is due.
- Status rollups must agree with attempts, queue, logs/events, and history.
- Log/event order is `(recorded_at, sequence)`.
- Recovery reports and applies repairs for expired leases, running steps without
  live leases, due retries, and inconsistent queued items.

Do not implement a Web UI, MCP server, shell/Docker/Kubernetes/SSH execution,
or any private upstream-compatible file format.
