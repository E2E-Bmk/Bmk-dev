# Environment contract

- Python runs offline with UTF-8 mode and bytecode writing disabled.
- The ordinary dependency runtime is exactly httpcore 1.0.9 with its declared
  dependencies. Its site-packages tree is evaluator-owned and read-only.
- A source-blank submission starts without an upstream checkout. It must own
  `httpcore/__init__.py` and `httpcore/transport_state.py`.
- Ordinary `httpcore` submodules may resolve only from the exact declared
  runtime tree. `httpcore.transport_state` must resolve from the submission.
- Evaluation supplies an isolated temporary directory to each semantic root.
- Network access, live services, wall-clock timing, random races, symlinks,
  compiled extensions added by the submission, and evaluator-private imports
  are unavailable.
- Exceptions raised after a root reaches its semantic call are ordinary false
  outcomes, except warnings, which invalidate the run. Setup, import,
  signature, provenance, collection, or timeout failures are invalid evidence.
