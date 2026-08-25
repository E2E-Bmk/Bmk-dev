# Environment contract

- Python is the evaluator's pinned CPython runtime.
- The ordinary runtime is the sealed `attr` and `attrs` package tree from attrs
  commit `ae37edd71a691b8ca797a0a53d0248543abfe12b`, tree
  `986bcfe39ec563b8e6e656e5b1863adb0b4f20ce` (upstream version line
  `26.1.0-23-gae37edd`).
- The runtime has no third-party runtime dependencies.
- `attrs/__init__.py` and `attrs/workspace.py` must resolve inside the submitted
  source-blank candidate.  Ordinary `attr` and `attrs` submodules may resolve
  only from the declared runtime through package-path extension.
- Every evaluator root receives only an evaluator-owned temporary directory.
- Import, provenance, package-search, collection, harness, and timeout failures
  invalidate a run; they are not behavioral misses.

