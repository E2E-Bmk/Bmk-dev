# japicmp-classvalue-001

This is a bench, not a task. The static gate does not pass, so the packet is not
presented as ready:

> layer floor failed: atomic=35, integration=23

- Language: `java`
- Packet: `packet/` — the same layout a graduated task has under `tasks/java/`
- Verdict: `verdict.json` — written by `harness/core/verdict.py`, do not edit by hand

This file is a starting point and is meant to be edited as the work proceeds.
`verdict.json` is not: it is regenerated from measurements, and
`harness/core/verdict.py --check` reports any hand edit as drift.

## What the gate objects to

- layer floor failed: atomic=35, integration=23
- scoreable case floor failed: 58
- depends_on coverage below floor: 0/23 = 0%

## Evidence not yet on record

- `reference_pass`
- `dummy_pass`
- `candidate_score`
- `adjusted_gap`
- `mutation`
- `coverage_gap`

## Graduating

Clear every objection above, then move `packet/` back to `tasks/java/japicmp-classvalue-001/`.
The gate reads the packet from either tree, so it can be re-run in place first:

    python harness/core/verify_task.py japicmp-classvalue-001

## Working material already here

- `filter/`
