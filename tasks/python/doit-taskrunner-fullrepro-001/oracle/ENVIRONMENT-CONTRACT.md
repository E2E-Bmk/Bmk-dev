# Environment contract

- Runtime: CPython 3.12 on Windows.
- The candidate is imported directly from its submitted source root.
- Standard-library-only implementations are accepted; no network access is available.
- Public compatibility target: the Doit 0.38 development surface described by `SPEC.md`.
- Tests use fresh temporary directories and may reopen them in a new interpreter.
- Warnings are errors. Candidate source and evaluator-owned state remain unchanged by imports except for caller-selected workflow directories.
