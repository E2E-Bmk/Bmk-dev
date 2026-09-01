# serf-query-fullrepro-003

This is a bench, not a task. The packet was converted from an
externally authored bundle and has not cleared the static gate, so it is
not presented as ready.

- Language: `go`
- Packet: `packet/` — the same layout a graduated task has under `tasks/go/`
- Authoring bundle: `dataset/` — copied verbatim from `spec2repo-aligned-25_GO`
- Measurement: `runs/index.jsonl` — the run that placed this bench here
- Verdict: `verdict.json` — written by `harness/core/verdict.py`, do not edit by hand

## Provenance

- The bundle records no upstream repository for this case.

## Oracle

- kind: `frozen-go-gate`, layout: `flat-package`
- scoreable tests: 64 (atomic 32, integration 32)
- The tests form one Go package and share `helpers_test.go`; the layer of each
  test is declared in `packet/oracle/ROOT-MAP.json` rather than by directory.

## Measurement

- qwen3.8-max: status `error`, atomic 0/32, integration 0/32
- scorer error: 4/4 batches had collection/report errors (invalid score)

## Why the score is zero

- class: `candidate-surface-mismatch`
- first failure: vet: ./coherent_targets_atomic_roots_test.go:15:33: cluster.source.node.DefaultQueryParams undefined (type *serf.Serf has no field or method

## Graduating

Clear the static gate, then move `packet/` to `tasks/go/serf-query-fullrepro-003/`.
The gate reads the packet from either tree, so it can be run in place first:

    python harness/core/verify_task.py serf-query-fullrepro-003

