# Pylint Public CLI And Reporting Specification

## Product Overview

Pylint is a Python static analysis tool. A run consumes Python files and
configuration, registers a public message catalog, applies enabled checks,
and projects the results through text, JSON, json2, generated message lists,
ratings, process exit codes, and standalone diagram or similarity tools.

This specification uses small local Python modules and packages. Durable
facts are message identifiers and symbols, category fields, enabled and
disabled message controls, configuration discovery, public reporter fields,
exit behavior, generated message listings, and deterministic local files
created by `pyreverse` and output from `symilar`.

## Scope

This specification covers:

- top-level public runners: `run_pylint`, `run_pyreverse`, and `run_symilar`
- local Pylint invocation against files, packages, and stdin input
- discovered `.pylintrc` and `pyproject.toml` settings
- command-line and inline enable/disable controls
- generated rcfile, message list, enabled message list, and help-message
  commands
- representative built-in messages such as `unused-import`, `invalid-name`,
  `line-too-long`, `syntax-error`, `import-error`, `undefined-variable`, and
  `duplicate-code`
- old JSON reporter and json2 reporter fields
- score, `--fail-under`, `--exit-zero`, and report-output routing behavior
- local `pyreverse` dot and PlantUML projections
- local `symilar` duplicate and ignore-option projections

All source files are created inside temporary directories and are removed by
the test runner.

## Installable Surface

The public imports are:

```python
from pylint import __version__, run_pylint, run_pyreverse, run_symilar
from pylint.interfaces import HIGH
from pylint.reporters.json_reporter import JSONReporter, JSON2Reporter
from pylint.message import Message
from pylint.typing import MessageLocationTuple
```

`HIGH` and `MessageLocationTuple` are the public confidence and location
value types used to construct deterministic reporter inputs.

The target package is provided by the invocation environment. The tests do
not import repository test helpers or private modules.

## Product State Model

A Pylint run has an input set, a configuration namespace, a registry of
messages, enabled and disabled message state, a reporter, lint statistics,
and a process exit status. A message has a stable public id, symbol, category,
location, path, object name, and formatted user message.

Configuration comes from discovered local files and command-line arguments.
Inline pragmas apply to the current source file. Reporter views expose the
same lint facts as text, JSON, json2, and output files. `pyreverse` reads the
same local Python package structure and writes deterministic diagram files.
`symilar` reads local files and reports duplicate blocks according to its
ignore options.

## Error Semantics

Invalid Python syntax is reported as a normal public lint message. Missing
imports and undefined variables are reported as enabled error-category
messages. Disable controls may suppress a message globally or inside a file.
When no non-internal checks remain enabled, Pylint exits with the documented
no-files-to-lint status. Rating thresholds and `--exit-zero` affect the
process status without changing the emitted message facts.

## Cross-View Invariants

1. Message ids and symbols agree between help output, text output, JSON, and
   json2.
2. A message disabled by a discovered configuration file is absent from lint
   output and from the enabled-message list.
3. A command-line enable can select one message from an otherwise disabled
   set.
4. Inline disable and re-enable pragmas affect only their source-file scope.
5. Text output, JSON, and json2 describe the same representative checker
   facts.
6. Clean modules receive the maximum rating and can pass a rating threshold.
7. `--exit-zero` forces a zero process status without erasing emitted
   messages.
8. Output-file routing moves reporter content into the selected file and
   leaves stdout empty.
9. Package and stdin invocations preserve useful public path/module
   projections.
10. `pyreverse` and `symilar` project local Python source facts without
    service calls or host-specific state.

## Representative Workflows

A local run can select one warning from an otherwise disabled set:

```python
run_pylint([
    "--disable=all",
    "--enable=unused-import",
    "--output-format=json",
    "sample.py",
])
```

A discovered configuration file can suppress docstring messages while the
same run still reports an enabled warning from the source file.

JSON and json2 reporters can be run on the same module and compared by
message id, symbol, line number, and category counts.

`pyreverse` can read a small package and write dot or PlantUML class and
package diagrams into a local output directory. `symilar` can compare two
local files, then repeat the comparison with ignore options to verify the
duplicate projection changes.

## Non-Goals

- Primer-style repository sweeps, performance comparisons, timing claims, or
  long-running workloads.
- Host-installed extensions, spelling dictionaries, editor integrations,
  credentials, service calls, sockets, or network access.
- Private checker state, repository test utilities, source-test imports, or
  implementation-only modules.
- Exact prose, complete generated output snapshots, terminal colors,
  traceback text, absolute temporary paths, cache directories, or graph
  rendering through external image tools.
- Docker runtime behavior, trusted-runner claims, delivery status, or
  provenance guarantees.

## Invocation Protocol

Expose the target `pylint` package through installation or a target root, then
run pytest from this directory against the atomic and integration test files.
The tests use local temporary files, public runner functions, and public
reporter APIs.

The same cases are replayed with Python 3.10 and Python 3.11. JSON reporting
is used only to record local reproducibility results.

## Environment

Run on Linux with Python 3.11 without network access. Python 3.10 is also
supported for compatibility replay. The target package is not pre-installed;
the runner supplies it through installation or a target root. Required
packages are `pytest`, `pytest-json-report`, `astroid`, `dill`, `isort`,
`mccabe`, `platformdirs`, `tomli`, and `tomlkit`.

No service credentials, endpoints, sockets, image-rendering binaries, Docker
runtime, host editor state, or global Pylint cache state are required.

## Evaluation Notes

Assertions prefer message ids, symbols, categories, path endings, JSON keys,
json2 statistics, process status values, and the existence and content
markers of generated diagram or similarity projections. Full command output,
incidental explanatory prose, tracebacks, timings, temporary absolute paths,
and complete diagram snapshots are intentionally outside the contract.

The local replay records are reproducibility artifacts for this package and
must be interpreted with the explicit artifact-only status and same-process
execution boundary.
