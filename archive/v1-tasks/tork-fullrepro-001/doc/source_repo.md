# TorkWorkflow Source Repository

Candidate id: `tork-fullrepro-001`

Source repository: `https://github.com/runabol/tork`

Local source path:
`G:\research\01_agents\swe-e2e\Bmk-dev\.repo_cache\runabol__tork`

Pinned commit: `7c126fc586a49cb0012842273a0e69d76b61710a`

Objective gate:

- tracked files: 217
- nonblank LOC: 30056
- top directories: `internal`, `runtime`, `middleware`, `engine`, `broker`,
  `cli`, `locker`, `datastore`, `docs`, `examples`
- docs/examples: `README.md`, `docs/swagger.json`, `examples/hello.yaml`,
  `examples/parallel.yaml`, `examples/each.yaml`, `examples/prepost.yaml`,
  `examples/retry.yaml`, `examples/subjob.yaml`, `examples/timeout.yaml`,
  `examples/job_output.yaml`
- tests: `broker/inmemory_test.go`, `broker/queues_test.go`,
  `engine/broker_test.go`, `engine/coordinator_test.go`,
  `engine/datastore_test.go`, `engine/engine_test.go`,
  `runtime/shell/*`, `datastore/postgres/*`

Layer0 verdict: `BUILD_WITH_RESCOPE`.

This task uses Tork as source evidence for a benchmark-owned local workflow
engine. It must not copy exact Docker, RabbitMQ, Postgres, web UI, auth,
middleware, SQL schema, or internal source layout.

Candidate runs are forbidden until a public packet, requirement map, starter
skeleton, executable scorer, passing reference, cleanroom leakage scan, and
fairness judge all exist.
