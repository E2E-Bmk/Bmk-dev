# TorkWorkflow PRD Draft

`TorkWorkflow` is a source-derived, benchmark-owned workflow engine task based
on `runabol/tork` evidence at commit
`7c126fc586a49cb0012842273a0e69d76b61710a`.

See `candidate_task/public_packet.md` for the current candidate-visible draft.

Required task level:

- installable package;
- 10+ candidate-owned modules;
- public API plus CLI or HTTP-style facade;
- local durable store plus in-memory broker;
- deterministic clock and local runtime;
- retained job history, task attempts, outputs, logs, schedules, queue state,
  progress, and recovery reports;
- no external DB, broker, container engine, network, or web UI.

Core system invariant:

After submit, run, retry, timeout, cancel, restart, schedule tick, worker loss,
and reopen, job summary, job detail, task history, outputs, log pages, progress,
queue state, schedule state, and recovery reports must agree.

Current status: Layer1 draft only. Candidate model runs are forbidden until a
50+ check executable scorer, passing reference, cleanroom packet, leakage scan,
and fairness judge exist.
