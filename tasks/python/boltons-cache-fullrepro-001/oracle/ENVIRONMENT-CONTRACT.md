# Environment contract

- Python 3.12 runs in UTF-8 mode with bytecode writing disabled.
- A submission is source-blank and owns `boltons/__init__.py` and
  `boltons/cachefabric.py`, or an equivalent candidate-contained module.
- `SPEC2REPO_BOLTONS_RUNTIME` declares a materialized ordinary Boltons runtime
  at commit `207651ee6055aabd0d9cdeac2e00140cdc208d44`, tree
  `b15dd1d55e0a8b16cf84e1096b6a12a460b53adf`.  Its 30-file tree is hashed
  independently before and after evaluation.
- A candidate may append `<runtime>/boltons` to its package path and execute
  that runtime's ordinary `boltons/__init__.py` in the candidate wrapper.
  Top-level `boltons` and `boltons.cachefabric` must still originate in the
  candidate.  Ordinary submodules may originate only in the candidate or the
  declared runtime.
- There is no reference overlay, control implementation, network, clock,
  randomness, persistence service, or worker available to a submission.
  Callers provide operation order and every durable document.
- Every capability root uses a fresh interpreter and isolated temporary state.
  Roots may run in natural, reverse, or deterministic permuted order.
- Import/setup/provenance/containment/timeout/receipt failures are invalid
  evidence and fail closed; semantic exceptions after a root begins are valid
  failed capabilities.

