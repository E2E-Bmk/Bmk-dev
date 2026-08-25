# gix-ref-txn-001

This is a bench, not a task. The static gate does not pass, so the packet is not
presented as ready:

> depends_on coverage below floor: 0/39 = 0%

- Language: `rust`
- Packet: `packet/` — the same layout a graduated task has under `tasks/rust/`
- Verdict: `verdict.json` — written by `harness/core/verdict.py`, do not edit by hand

This file is a starting point and is meant to be edited as the work proceeds.
`verdict.json` is not: it is regenerated from measurements, and
`harness/core/verdict.py --check` reports any hand edit as drift.

## What the gate objects to

- depends_on coverage below floor: 0/39 = 0%

## Evidence not yet on record

- `reference_pass`
- `dummy_pass`
- `coverage_gap`

## Graduating

Clear every objection above, then move `packet/` back to `tasks/rust/gix-ref-txn-001/`.
The gate reads the packet from either tree, so it can be re-run in place first:

    python harness/core/verify_task.py gix-ref-txn-001

## Working material already here

- `PIPELINE_STATE.md`
- `ROOT-MAP.json`
- `controls_record.md`
- `eval/`
- `filter/`
- `filter_notes.md`
- `mutation/`
- `oracle/`
- `source/`
- `spec/`
- `task.json`
