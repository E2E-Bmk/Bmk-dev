# Environment contract

- Python 3.12 on Windows.
- The starting project is an extension shim, not an upstream source checkout.
- `vcrpy==8.1.1` is an ordinary installed runtime dependency, together with its declared runtime dependencies.
- The extension owns `vcr/__init__.py` and `vcr/workflow.py`. Its package entry preserves the ordinary VCR.py 8.1.1 top-level objects by identity: the `VCR` class from `vcr.config`, the `mode` alias of `vcr.record_mode.RecordMode`, the exact default configured instance and its bound cassette callable, version text, and the package logger's null-handler behavior.
- The extension package search path contains exactly its own `vcr` directory followed by the declared runtime's `vcr` directory. This keeps `vcr.workflow` project-owned while normal submodules such as requests, configuration, cassettes, matching, serialization, and persistence resolve from the installed dependency.
- Ordinary `vcr` submodules are imported from that exact installed dependency; the new workflow module remains part of this project.
- Network access is unavailable during verification.
- Durable data must remain usable after objects are discarded and recreated for the same path.
- Use only public Python modules and local filesystem operations; no service process or database is supplied.
