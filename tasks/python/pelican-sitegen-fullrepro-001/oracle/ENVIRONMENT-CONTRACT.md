# Environment contract

- Python: CPython 3.12
- Target package: `pelican`
- Seed compatibility boundary: Pelican 4.12.0 public APIs described by
  `SPEC.md`
- Available runtime dependencies: the dependencies of Pelican 4.12.0 in the
  qualified environment
- Network access: unavailable
- Filesystem: local temporary directories are writable; paths may contain
  spaces and non-ASCII characters
- Process model: every evaluated behavior starts in a fresh interpreter
- Warnings: treated as invalid evaluator evidence
- Time: no behavior may rely on sleeps, wall-clock races, or external services
