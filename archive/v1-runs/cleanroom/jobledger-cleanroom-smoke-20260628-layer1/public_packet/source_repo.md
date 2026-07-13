# Source Repository: oban-bg/oban

Repository: https://github.com/oban-bg/oban

Local path: `G:\research\01_agents\swe-e2e\sources\oban-bg__oban`

Scale counted locally:

- tracked/filesystem files: 170
- text LOC: 19301

## Product Evidence Used

The benchmark uses Oban as product inspiration, not as an API clone.

Evidence inspected:

- `README.md`: reliability, consistency, observability, retained job data,
  isolated queues, scheduled jobs, periodic jobs, unique jobs, historic metrics,
  graceful shutdown, telemetry.
- `guides/learning/job_lifecycle.md`: states and transitions.
- `guides/learning/error_handling.md`: errors, retry behavior, max attempts,
  discard.
- `guides/learning/instrumentation.md`: lifecycle events and metrics/logging.

## Benchmark Variant Boundary

JobLedger is a custom Python package/service with deterministic virtual time,
custom CLI/API names, and benchmark-owned persistence/report semantics. It does
not implement Oban, Ecto, PostgreSQL behavior, or distributed node behavior.
