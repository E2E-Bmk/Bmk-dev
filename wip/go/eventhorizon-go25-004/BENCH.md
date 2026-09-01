# eventhorizon-go25-004

This is a bench, not a task. The packet was converted from an
externally authored bundle and has not cleared the static gate, so it is
not presented as ready.

- Language: `go`
- Packet: `packet/` — the same layout a graduated task has under `tasks/go/`
- Authoring bundle: `dataset/` — copied verbatim from `spec2repo-aligned-25_GO`
- Measurement: `runs/index.jsonl` — the run that placed this bench here
- Verdict: `verdict.json` — written by `harness/core/verdict.py`, do not edit by hand

## Provenance

- repository: `https://github.com/looplab/eventhorizon`
- module: `github.com/looplab/eventhorizon`
- version: `v0.17.0`
- commit: `d6fc4e05b8b85da191a68384866ee2cc9df74027`

## Oracle

- kind: `frozen-go-gate`, layout: `flat-package`
- scoreable tests: 36 (atomic 12, integration 24)
- The tests form one Go package and share `helpers_test.go`; the layer of each
  test is declared in `packet/oracle/ROOT-MAP.json` rather than by directory.

## Measurement

- qwen3.8-max: status `error`, atomic 0/12, integration 0/24
- scorer error: 2/2 batches had collection/report errors (invalid score)

## Why the score is zero

- class: `candidate-missing-subpackage`
- first failure: candidate module has no github.com/looplab/eventhorizon/eventbus/local

## Graduating

Clear the static gate, then move `packet/` to `tasks/go/eventhorizon-go25-004/`.
The gate reads the packet from either tree, so it can be run in place first:

    python harness/core/verify_task.py eventhorizon-go25-004

