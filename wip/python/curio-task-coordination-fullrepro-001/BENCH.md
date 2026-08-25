# curio-task-coordination-fullrepro-001

This is a bench, not a task. It is not part of the authoritative qualified
python sample, so the packet is not presented as ready:

> id is absent from the qualified release sample (spec2repo-aligned-43_PYTHON)

- Language: `python`
- Packet: `packet/` — the same layout a graduated task has under `tasks/python/`
- Verdict: `verdict.json` — written by `harness/core/verdict.py`, do not edit by hand

## Why this is parked

The qualified python set for this round is defined by the release sample of 43
cases. This task's instance id is not among them, so it is filed as a bench
pending inclusion in a future qualified sample.

## Graduating

Land this id in the qualified sample, then move `packet/` back to
`tasks/python/curio-task-coordination-fullrepro-001/`:

    python harness/core/verify_task.py curio-task-coordination-fullrepro-001
