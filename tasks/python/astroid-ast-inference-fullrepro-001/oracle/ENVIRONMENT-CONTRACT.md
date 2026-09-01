# Environment contract

- Python: CPython 3.12.
- Required package import: `astroid` from the submitted source tree.
- Declared runtime dependencies: Python standard library only.
- Filesystem: a writable local directory is supplied by callers of
  `astroid.workflow`; durable state must reopen from that directory.
- Network and optional services: unavailable and unnecessary.
- Time: behavior must not depend on sleeps or wall-clock timing.

The reference environment uses Astroid 4.2.0b4. Candidate implementations are
not given the reference source or installed reference distribution.
