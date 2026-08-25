# Griffe v3 environment contract

The candidate must provide an importable `griffe` package for CPython 3.12.
Only Python source in the submitted candidate tree is admitted.  The evaluator
provides the Python standard library and the ordinary runtime dependencies of
Griffe 2.1.1.dev14; network access is disabled.

The public candidate packet is `TASK.md`, `SPEC.md`, and this file.  Evaluator
tests, root maps, mutation labels, expected vectors, receipts, reference
overlays, and historical candidates are not candidate inputs.

Every scored root runs in a fresh interpreter with bytecode writing disabled
and warnings promoted to errors.  Import, collection, signature, warning,
timeout, provenance, or candidate-tree mutation failures invalidate the run;
they are never converted to a low product score.
