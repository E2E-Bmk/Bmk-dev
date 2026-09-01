# Environment contract

- Platform: Windows, UTF-8 process and filesystem text.
- Python: CPython 3.12 compatible source.
- Candidate import root: the directory containing the submitted `dvc` package.
- Invocation: public Python imports and `python -m dvc` subprocesses.
- Network access is not available during evaluation.
- Each workflow owns a fresh writable temporary repository directory.
- The evaluator may place caches and local remotes outside the candidate tree.
- Candidate source must not mutate itself during execution.
- Runtime dependencies available to the pinned reference environment may be
  imported, but an installed or copied external `dvc` implementation may not be
  used as the candidate implementation.
