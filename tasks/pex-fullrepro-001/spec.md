# PEX Local Archive Construction Specification

## Product Overview

PEX builds executable Python application environments. A generated `.pex`
can be observed as an executable zip application or as a directory layout,
and the same application fact can be checked through archive files,
`PEX-INFO`, public metadata readers, command-line entry points, interpreter
argument behavior, and runtime cache or venv side effects.

This specification uses tiny generated fixtures: one source tree and one
pure-Python wheel file written locally. The durable facts are the build
inputs, public layout files, `PEX-INFO` fields, entry point output, injected
application and interpreter arguments, and filesystem changes under a runner
owned `PEX_ROOT`.

## Scope

This specification covers service-free behavior for:

- invoking `python -m pex` to build local artifacts
- local wheel requirements supplied as filesystem paths
- source trees supplied with `-D` or `--sources-directory`
- `zipapp`, `packed`, and `loose` layouts
- root-level `PEX-INFO` and `__main__.py` projections
- public `pex.pex_info.PexInfo.from_pex` and `from_json`
- public `pex.layout.Layout` identification
- `-m` module/function entry points
- `-c` console script entry points from a local wheel
- `--inject-args` application arguments
- `--inject-python-args` interpreter arguments
- runner controlled `PEX_ROOT` execution side effects
- `--venv` execution side effects under the controlled runtime root

All packages are created locally by the tests. The wheel fixture is a minimal
valid `py3-none-any` wheel and the source fixture imports that wheel at
runtime.

## Installable Surface

The public imports used by the tests are:

```python
from pex.layout import Layout
from pex.pex_info import PexInfo
```

The command surface is `python -m pex`. The target package is supplied by the
invocation environment through installation or `PYTHONPATH`; the tests do not
import private modules or repository test helpers.

## Product State Model

A PEX construction state starts with a local source tree, a local wheel file,
selected layout options, selected entry point options, and optional injected
arguments. Building writes either a single zip application or a directory
layout. Each output has readable metadata and executable bootstrap files.

A runtime state starts with a generated PEX and an optional `PEX_ROOT` owned by
the runner. Executing the PEX runs the configured entry point, imports the
source package and wheel dependency, applies injected application arguments,
applies injected Python interpreter arguments, and may populate cache or venv
directories below the controlled runtime root.

## Error Semantics

Invalid behavior is represented by normal assertion failures: missing public
files, wrong layout identification, missing metadata fields, wrong entry point
output, ignored injected arguments, or missing runtime side effects.

The tests avoid broad exception matching and do not assert exact traceback,
resolver, or incidental command text.

## Cross-View Invariants

1. A zipapp PEX contains `PEX-INFO` and `__main__.py`, and `Layout.identify`
   identifies it as `zipapp`.
2. Packed and loose directory layouts execute through the same configured
   entry point as a zipapp built from the same local fixtures.
3. `PexInfo.from_pex` agrees with the raw `PEX-INFO` fields for entry point,
   build metadata, and included distributions.
4. The local wheel distribution appears in both archive layout projections
   and public metadata.
5. The source package files appear in source-backed builds and are imported
   by the entry point at runtime.
6. Console script builds resolve to the wheel's public console-script callable
   and execute without the source tree.
7. `--inject-args` is visible through metadata and through application
   `sys.argv`.
8. `--inject-python-args` is visible through metadata and through Python
   runtime flags.
9. Executing with a controlled `PEX_ROOT` creates runner-owned runtime files.
10. Executing a `--venv` PEX produces the same application projection while
    running from a venv-shaped runtime prefix.

## Representative Workflows

Build and run a zipapp from both fixtures:

```sh
python -m pex --no-index ./supportlib-1.0.0-py3-none-any.whl \
  -D ./source -m demo_app.main:main -o ./app.pex
python ./app.pex
```

Build a console-script PEX with injected application arguments:

```sh
python -m pex --no-index ./supportlib-1.0.0-py3-none-any.whl \
  -c support-cli --inject-args "--console yes" -o ./support.pex
python ./support.pex
```

Build and run a venv-mode PEX under a controlled runtime root:

```sh
python -m pex --no-index ./supportlib-1.0.0-py3-none-any.whl \
  -D ./source -m demo_app.main:main --venv -o ./app-venv.pex
PEX_ROOT=./runner-root python ./app-venv.pex
```

## Non-Goals

- Live package downloads, package index queries, sockets, services, or
  credentials.
- Scie construction, eager or lazy scie fetching, embedded interpreter
  downloads, or remote bootstrap URLs.
- Broad interpreter or platform matrices beyond Python 3.10 and Python 3.11
  local replay.
- Private modules, repository test helpers, source checkout tests, or private
  cache layout internals.
- Host user caches, home-directory state, timing claims, performance claims,
  exact archive bytes, exact generated hashes, or full output snapshots.

## Invocation Protocol

Expose the target `pex` package through installation or `PYTHONPATH`, install
the listed test requirements, and run pytest from this directory against the
two public test files. Each test creates local fixtures and invokes subprocess
commands with explicit timeouts.

The same cases are replayed with Python 3.10 and Python 3.11. JSON reporting
records local reproducibility results only.

## Environment

Run on Linux with Python 3.11 without network access. Python 3.10 is also
supported for compatibility replay. The target package is not pre-installed;
the runner supplies it through installation or `PYTHONPATH`. Required packages
are `pytest` and `pytest-json-report`.

No package index, service endpoint, credential, Docker runtime, scie fetch,
host cache, source checkout mutation, or prebuilt binary fixture is required.

## Evaluation Notes

Assertions prioritize public command behavior, generated source and wheel
fixtures, `PEX-INFO`, layout file projections, parsed metadata, entry point
JSON fields, injected arguments, and runtime side effects under temporary
roots. Exact command stderr, traceback strings, output byte ordering outside
the parsed JSON fields, cache hash names, and archive byte identity are outside
the contract.

The local replay records are reproducibility artifacts for this package and
must be interpreted with artifact-only status and same-process execution.
