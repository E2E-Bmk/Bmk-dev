# Environment contract

- Python: the evaluator's pinned CPython runtime.
- Ordinary runtime: the sealed `runtime-site/traitlets` tree, exactly Traitlets
  5.15.1. `RUNTIME-IDENTITY.json` authenticates its marker, complete tree and
  import origins before semantic roots run.
- Candidate ownership: `traitlets/__init__.py` and `traitlets/workspace.py`
  resolve inside the submitted source-blank tree. Ordinary Traitlets submodules
  resolve only from the declared runtime through package-path extension.
- Available dependencies: Python standard library and the declared runtime.
- Workspaces receive distinct evaluator-owned temporary directories. Persistent
  content must remain below the supplied directory.
- Setup, import, warning, provenance, containment, timeout and harness failures
  invalidate a scoring call rather than counting as low semantic scores.

