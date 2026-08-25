# Environment contract

- Python 3.12; UTF-8 source.
- Ordinary runtime: pinned HTTPX 0.28.1 source at commit `b5addb64f0161ff6bfe94c124ef76f6a1fba5254`.
- Declared dependencies are supplied by the evaluator; no installation or network access occurs.
- Candidate import ownership: `httpx` and `httpx.orchestration` are candidate-owned. The evaluator places the parent of the declared HTTPX source tree on the import path immediately after the candidate root, so ordinary package-path extension can resolve existing HTTPX implementation submodules only from that declared runtime tree.
- Each root receives only an evaluator-owned temporary path. Roots are process isolated and order independent.
- Once a semantic call starts, any product exception other than a `Warning` is a valid failed root. Setup, import, provenance, warning, timeout, malformed receipt, or containment failures invalidate the score.
- The scored candidate is immutable across natural, reverse, and fixed-permuted execution.
