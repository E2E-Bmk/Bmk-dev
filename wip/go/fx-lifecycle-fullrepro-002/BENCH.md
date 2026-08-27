# fx-lifecycle-fullrepro-002

This is a bench, not a task. The packet was converted from an
externally authored bundle and has not cleared the static gate, so it is
not presented as ready.

- Language: `go`
- Packet: `packet/` — the same layout a graduated task has under `tasks/go/`
- Authoring bundle: `dataset/` — copied verbatim from `spec2repo-aligned-25_GO`
- Measurement: `runs/index.jsonl` — the run that placed this bench here
- Verdict: `verdict.json` — written by `harness/core/verdict.py`, do not edit by hand

## Provenance

- upstream_repository: `https://github.com/uber-go/fx`
- module: `go.uber.org/fx`
- upstream_version: `v1.24.0`
- upstream_commit: `443b55a9f03efcacafac0b7777d5c91425cf2c35`

## Oracle

- kind: `frozen-go-gate`, layout: `flat-package`
- scoreable tests: 75 (atomic 32, integration 43)
- The tests form one Go package and share `helpers_test.go`; the layer of each
  test is declared in `packet/oracle/ROOT-MAP.json` rather than by directory.

## Measurement

- qwen3.8-max: status `error`, atomic 0/32, integration 0/43
- scorer error: 4/4 batches had collection/report errors (invalid score)

## Why the score is zero

- class: `spec-underspecified`
- first failure: oracle needs NopLogger, which the spec never names

## Graduating

Clear the static gate, then move `packet/` to `tasks/go/fx-lifecycle-fullrepro-002/`.
The gate reads the packet from either tree, so it can be run in place first:

    python harness/core/verify_task.py fx-lifecycle-fullrepro-002

