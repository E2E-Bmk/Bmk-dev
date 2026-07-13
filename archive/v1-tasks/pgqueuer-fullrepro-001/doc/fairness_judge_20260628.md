# PgQueueLedger Fairness Judge

Date: 2026-06-28

Verdict: `BLOCKED`

Candidate model runs must not start.

## Positive Evidence

- Upstream provenance is valid: `janbjorge/pgqueuer` at commit
  `b475e4b9afbed1834cd7c478f1eec9d59ec0c5cd`.
- Source gate shows 190 tracked files and 21154 nonblank LOC.
- Reference implementation passes current executable scorer: 53/53.
- Empty starter baseline passes only 4/53, so the scorer is not empty.

## Blocking Defects

1. Task is still too mini for full reproduction.
   - Current reference is about 498 nonblank source lines.
   - It passes with compact dict/file snapshot mechanics.
   - This does not satisfy the full-reproduction target of a bounded subsystem.

2. Public requirements are not fully enforced.
   - Public packet requires per-entrypoint and global concurrency limits.
   - Current worker claim logic does not enforce registry/global concurrency.
   - No hidden check verifies duplicate-processing prevention under active
     concurrency gates.

3. Public underspecification and private-shape assertions.
   - `PQL-U016` asserts exact `job-1` id generation without public schema.
   - `PQL-U023` asserts priority-first ordering while claim ordering is listed
     as a free parameter.
   - `PQL-U029` mutates private store metadata for `max_attempts`.
   - `PQL-U031` assumes completion offset is a raw list index.
   - `PQL-U032` asserts exact metric key strings not specified publicly.

4. Feature-pure unit violations.
   - Several `unit` rows use facade + store + worker/completion/metrics
     workflows.
   - These should move to integration/system rows or be rewritten with direct
     module setup and mocks.

5. System tests mostly assert recomputed final tuples.
   - Current system checks do not sufficiently test job history, schedule
     state, logs, retry history, recovery report, dashboard, metrics, and
     adapter-visible state together.
   - Several projections share the same `queue_report()` computation path.

6. Cleanroom leakage risk.
   - Starter had `__pycache__`; this was removed after judge.

7. Metadata drift.
   - `rubric.json` and `doc/source_repo.md` were stale; updated after judge.

## Required Repair Before Candidate Runs

- Increase public surface and hidden checks around retained history, logs,
  retry ledger, schedule ledger, dashboard snapshots, metrics snapshots,
  recovery reports, and durable replay.
- Move facade workflow checks out of unit layer.
- Remove or publicly specify exact ids, metric schemas, completion offsets, and
  priority ordering.
- Add explicit concurrency enforcement and tests.
- Rebuild reference to pass the repaired suite.
- Re-run fairness judge before OpenHands, mini-swe-agent, DeepSeek, Qwen, or
  Codex candidate runs.
