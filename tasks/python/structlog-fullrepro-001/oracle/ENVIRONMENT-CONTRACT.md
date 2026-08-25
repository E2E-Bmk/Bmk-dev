# Environment contract

- Python 3.12 is used with UTF-8 mode and bytecode writing disabled.
- The candidate is source-blank and must contain `structlog/__init__.py` and its own `structlog/delivery.py` (or an equivalent candidate-contained module).
- The evaluator supplies an ordinary, importable structlog runtime as a declared dependency.  Its package root is named by `SPEC2REPO_STRUCTLOG_RUNTIME`; it is a materialized copy of commit `628bffc2e5edc0e12a9d44b42bed5485fc424b43`, independently hashed before and after scoring.
- A candidate may extend its package search path with `<runtime>/structlog` and execute that runtime's ordinary `__init__.py` inside the candidate-owned wrapper namespace.  The top-level `structlog` module must still originate in the candidate.  Only ordinary runtime submodules may originate in the declared runtime; `structlog.delivery` must originate in the candidate.
- The runtime wrapper must not consult or name the reference checkout.  The evaluator rejects imports from any undeclared structlog location.
- No network, clock, randomness, filesystem persistence, background work, or optional service is required by the delivery extension.  Tests supply all times and temporary paths.
- Each capability root runs in a fresh interpreter.  Roots may run in natural, reverse, or deterministic permuted order.
- After the root has entered its semantic call, an exception is a valid failed capability.  An import/setup/provenance failure, escaped warning, malformed receipt, timeout, or candidate/reference mutation is invalid evidence.
