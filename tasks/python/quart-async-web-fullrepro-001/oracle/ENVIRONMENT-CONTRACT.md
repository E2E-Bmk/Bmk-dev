# Environment contract

- Python 3.12, UTF-8, Windows-compatible filesystem behavior.
- Ordinary runtime dependency: Quart 0.20.0 from the declared isolated dependency site.
- The candidate starts source blank except for `TASK.md`, `SPEC.md`, and this contract.
- The candidate owns `quart_workflow`; it must not copy, patch, or shadow the `quart` package.
- Durable state may be placed only below caller-provided roots. Calls can be repeated after fresh-process reopen.
- Public behavior must not depend on evaluator paths, root identifiers, execution order, or hidden environment switches.
