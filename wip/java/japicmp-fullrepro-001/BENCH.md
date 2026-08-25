# japicmp-fullrepro-001

This is a bench, not a task. It is parked pending an unresolved measurement
conflict, so the packet is not presented as ready:

> reference gate and candidate probe disagree, and the conflict is unresolved

- Language: `java`
- Packet: `packet/` — the same layout a graduated task has under `tasks/java/`
- Verdict: `verdict.json` — written by `harness/core/verdict.py`, do not edit by hand

## What parks this packet

Two runs on record contradict each other and the conflict has not been resolved:

- reference gate: atomic 44/44, integration 42/42, gap 0 — reads as qualified
- candidate `qwen-probe`: `error` — tests not collected (atomic 0/44, integration 0/42)

The static gate itself passes (`verdict.json` records `tier: tasks`), so this is
a "passes the static gate but parked" case: graduation waits on reconciling the
two measurements, not on the packet contents.

## Graduating

Reconcile the two runs above, then move `packet/` back to
`tasks/java/japicmp-fullrepro-001/`. The gate reads the packet from either
tree, so it can be re-run in place first:

    python harness/core/verify_task.py japicmp-fullrepro-001
