# Environment contract

- Python: CPython 3.12 on Windows.
- Required package namespace: `coverage`.
- Required command entry point: `python -m coverage`.
- The evaluator invokes public behavior in fresh Python processes.
- The implementation must not depend on network access, inherited Coverage.py
  environment variables, an external installed `coverage` package, or files
  outside the submitted repository and evaluator-created temporary workspaces.
- The evaluator may change the process working directory between phases.
- Candidate source trees must remain unchanged during evaluation. Runtime data,
  configuration, and reports belong in evaluator-provided temporary locations.
