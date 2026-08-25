# halodb-fullrepro-001

This is a bench, not a task. It is parked because the packet does not meet the
reconstruction-difficulty bar: a candidate model reconstructs it almost fully,
so it does not discriminate.

- Language: `java`
- Packet: `packet/` -- the same layout a graduated task has under `tasks/java/`
- Verdict: `verdict.json` -- written by `harness/core/verdict.py`, do not edit by hand

## What parks this packet

The reference oracle is solvable and the static gate passes, but the candidate
score is too high and the integration gap is effectively zero:

- reference score: 1.0
- candidate score: 1.0
- integration rate gap: 0.0

A qualifying packet leaves a measurable gap where the candidate fails
integration or end-to-end behaviour that the reference passes. This packet does
not, so it is filed as a bench rather than a task.

## Graduating

Raise the reconstruction difficulty until a candidate leaves a real integration
gap, then move `packet/` back to `tasks/java/halodb-fullrepro-001/`. The gate reads the packet
from either tree:

    python harness/core/verify_task.py halodb-fullrepro-001
