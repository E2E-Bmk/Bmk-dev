# toml-fullrepro-001

This is a bench, not a task. The static gate does not pass, so the packet is not
presented as ready:

> taxonomy keys do not match the physical test functions

- Language: `rust`
- Packet: `packet/` — the same layout a graduated task has under `tasks/rust/`
- Verdict: `verdict.json` — written by `harness/core/verdict.py`, do not edit by hand

This file is a starting point and is meant to be edited as the work proceeds.
`verdict.json` is not: it is regenerated from measurements, and
`harness/core/verdict.py --check` reports any hand edit as drift.

## What the gate objects to

- taxonomy keys do not match the physical test functions
- depends_on coverage below floor: 0/57 = 0%
- no TARGET_IMPORTS entry for toml-fullrepro-001: scoring will abort before running the oracle

## Evidence not yet on record

- `reference_pass`
- `dummy_pass`
- `candidate_score`
- `mutation`
- `coverage_gap`

## Graduating

Clear every objection above, then move `packet/` back to `tasks/rust/toml-fullrepro-001/`.
The gate reads the packet from either tree, so it can be re-run in place first:

    python harness/core/verify_task.py toml-fullrepro-001

## Working material already here

Nothing yet; this bench starts from the packet alone.
