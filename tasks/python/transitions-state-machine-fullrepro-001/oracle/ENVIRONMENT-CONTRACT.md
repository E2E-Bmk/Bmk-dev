# Environment contract

- Python 3.12
- Dependency-free candidate package named `transitions`
- Candidate import must resolve inside the submitted source root
- Writable evaluator-provided temporary directories are available
- Tests promote Python warnings to errors
- No network, service, daemon, clock, or pre-existing file is required
- Scheduler time is provided explicitly by callers

The candidate may use only the Python standard library. It must not read the
evaluator, reference source, control implementations, or prior submissions.
