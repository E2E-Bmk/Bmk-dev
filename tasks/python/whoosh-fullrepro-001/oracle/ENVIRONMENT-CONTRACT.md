# Environment contract

- Python: CPython 3.12.
- Declared runtime dependencies from `requirements.txt`: `whoosh==2.7.4` and
  its exact ordinary dependency `cached-property==2.0.1`.
- The candidate directory must contain an importable `whoosh` package entry.
- Candidate-authored entry and extension modules must load from the candidate
  tree. Ordinary Whoosh runtime submodules may load only from the evaluator's
  exact installed `whoosh==2.7.4` dependency tree. The evaluator also verifies
  that `cached_property` loads from the declared runtime site at version 2.0.1.
- The reference candidate is a normal installed runtime, not an upstream source checkout
  and not payload content.
- Evaluation is offline, filesystem-local, and uses evaluator-owned temporary
  directories.
- The wrapper probe imports a real candidate extension together with runtime
  field machinery and records candidate-relative and runtime-relative origins.
- CPython 3.12's legacy-escape `SyntaxWarning` for a fixed set of Whoosh 2.7.4
  runtime modules is suppressed only while those exact runtime-origin modules
  are preloaded. Candidate modules and semantic root calls retain the strict
  warning-invalid policy.
- Every root is isolated in a fresh interpreter with a 30 second outer
  timeout. Setup/import/signature/provenance failures, warnings, and outer
  timeouts invalidate a measurement. Once semantic invocation begins, every
  other candidate exception is a valid semantic failure.
