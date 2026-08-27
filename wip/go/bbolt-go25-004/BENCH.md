# bbolt-go25-004

This is a bench, not a task. The packet was converted from an
externally authored bundle and has not cleared the static gate, so it is
not presented as ready.

- Language: `go`
- Packet: `packet/` — the same layout a graduated task has under `tasks/go/`
- Authoring bundle: `dataset/` — copied verbatim from `spec2repo-aligned-25_GO`
- Measurement: `runs/index.jsonl` — the run that placed this bench here
- Verdict: `verdict.json` — written by `harness/core/verdict.py`, do not edit by hand

## Provenance

- module: `go.etcd.io/bbolt`
- upstream_version: `v1.5.0`
- upstream_commit: `18bfb4b4f882e50819e5c85a99059749b1eb3997`

## Oracle

- kind: `frozen-go-gate`, layout: `flat-package`
- scoreable tests: 48 (atomic 16, integration 32)
- The tests form one Go package and share `helpers_test.go`; the layer of each
  test is declared in `packet/oracle/ROOT-MAP.json` rather than by directory.

## Measurement

- qwen3.8-max: status `error`, atomic 0/16, integration 0/32
- scorer error: 3/3 batches had collection/report errors (invalid score)

## Why the score is zero

- class: `candidate-broken`
- first failure: ./bucket_api.go:4:6: Bucket redeclared in this block

## Graduating

Clear the static gate, then move `packet/` to `tasks/go/bbolt-go25-004/`.
The gate reads the packet from either tree, so it can be run in place first:

    python harness/core/verify_task.py bbolt-go25-004

