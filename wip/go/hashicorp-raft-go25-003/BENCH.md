# hashicorp-raft-go25-003

This is a bench, not a task. The packet was converted from an
externally authored bundle and has not cleared the static gate, so it is
not presented as ready.

- Language: `go`
- Packet: `packet/` — the same layout a graduated task has under `tasks/go/`
- Authoring bundle: `dataset/` — copied verbatim from `spec2repo-aligned-25_GO`
- Measurement: `runs/index.jsonl` — the run that placed this bench here
- Verdict: `verdict.json` — written by `harness/core/verdict.py`, do not edit by hand

## Provenance

- repository: `https://github.com/hashicorp/raft`
- module: `github.com/hashicorp/raft`
- upstream_tag: `v1.7.3`
- upstream_commit: `c0dc6a0b2c7e889f31e5ab2f7ed90ceb159acffe`

## Oracle

- kind: `frozen-go-gate`, layout: `flat-package`
- scoreable tests: 23 (atomic 8, integration 15)
- The tests form one Go package and share `helpers_test.go`; the layer of each
  test is declared in `packet/oracle/ROOT-MAP.json` rather than by directory.

## Measurement

- qwen3.8-max: status `error`, atomic 0/8, integration 0/15
- scorer error: 2/2 batches had collection/report errors (invalid score)

## Why the score is zero

- class: `spec-underspecified`
- first failure: oracle needs InmemStore, which the spec never names

## Graduating

Clear the static gate, then move `packet/` to `tasks/go/hashicorp-raft-go25-003/`.
The gate reads the packet from either tree, so it can be run in place first:

    python harness/core/verify_task.py hashicorp-raft-go25-003

