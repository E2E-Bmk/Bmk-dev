# Environment contract

- Runtime: CPython 3.12 on Windows.
- The candidate is imported directly from its submitted source root.
- A Redis-compatible in-memory connection is supplied by the caller for ordinary RQ operations; the candidate must not contact a network service.
- Public compatibility target: the RQ 2.10.0 surface described by `SPEC.md`.
- Tests use fresh temporary directories and may reopen them in a new interpreter.
- Warnings are errors. Candidate source and evaluator-owned state remain unchanged by imports except for caller-selected workflow directories.
