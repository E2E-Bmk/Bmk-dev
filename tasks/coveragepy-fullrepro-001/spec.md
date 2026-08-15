# coverage Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`coverage` is a code-coverage measurement tool with a `coverage` CLI entry point. It measures which Python code executed while a program ran. It records measured files, executed statement lines, optional branch transitions, and optional measurement contexts. The same measured data can be inspected through a Python API, stored in a `.coverage` data file, combined across runs, and rendered as text, JSON, XML, HTML, LCOV, or annotated source reports.

The main user workflow is:

1. Run Python code under coverage measurement.
2. Save the collected data.
3. Read the data through `Coverage` or `CoverageData`.
4. Produce reports that compare executed data with the executable lines and branches found in source files.

## Non-Goals

- This specification does not require Reproducing internal module layout, private attributes, debug implementation, cache details, or helper functions.
- This specification does not require Implementing the C extension tracer or matching which tracing core is selected.
- This specification does not require Matching exact text table spacing, generated HTML asset names, CSS, JavaScript, or byte-for-byte report files.
- This specification does not require Supporting every plugin authoring behavior beyond preserving the documented public imports or ordinary plugin error handling.
- This specification does not require Optional concurrency integrations such as greenlet, gevent, eventlet, multiprocessing patching, or subprocess sitecustomize behavior beyond the documented `process_startup()` trigger.
- This specification does not require Project-specific development harnesses, demonstration-only helper modules, golden-file comparison infrastructure, or pytest plugin configuration.
- This specification does not require Platform-specific path spelling beyond documented include/omit/path mapping semantics.
- This specification does not require Treating unsupported importable modules as public API merely because their module names have no leading underscore.

## Representative Workflows

```python
from pathlib import Path
import json

from coverage import Coverage, CoverageData

work = Path("demo")
work.mkdir(exist_ok=True)
program = work / "sample.py"
program.write_text(
    "flag = True\n"
    "if flag:\n"
    "    print('yes')\n"
    "else:\n"
    "    print('no')\n",
    encoding="utf-8",
)

cov = Coverage(data_file=str(work / ".coverage"), branch=True, source=[str(work)])
cov.start()
exec(compile(program.read_text(encoding="utf-8"), str(program), "exec"), {})
cov.stop()
cov.save()

data = CoverageData(basename=str(work / ".coverage"))
data.read()
measured = next(name for name in data.measured_files() if name.endswith("sample.py"))
assert data.has_arcs() is True
assert data.arcs(measured)

json_file = work / "coverage.json"
total = cov.json_report(outfile=str(json_file), pretty_print=True)
payload = json.loads(json_file.read_text(encoding="utf-8"))
assert "totals" in payload
assert total == payload["totals"]["percent_covered"]
```

The same workflow can be performed from the command line:

```text
coverage run --branch --source=demo demo/sample.py
coverage report -m
coverage json -o demo/coverage.json --pretty-print
coverage html -d demo/htmlcov
```

## Command-Line Behavior

The CLI provides commands for measuring, reporting, combining, and managing coverage data.

**Help and version.** `coverage help` must print the command summary. `coverage --version` must display the coverage.py version string containing `"Coverage.py"`. Both must exit with status 0.

**Run command.** `coverage run` executes a Python script or importable module while collecting coverage data. When `--branch` is supplied, branch transitions must be recorded. `--source`, `--include`, and `--omit` restrict measured files. `--context` records a static context label. `--data-file` chooses the base output file. `--parallel-mode` writes a uniquely suffixed data file for later combining. `-m` runs a module as Python's `-m` switch would, and program arguments must be passed through in `sys.argv`. When no script or module is supplied, the command must fail with a nonzero exit status. When the measured program prints output, that output must appear on stdout.

**Report command.** `coverage report` reads data and prints a table with each measured file. When `-m` or `--show-missing` is supplied, missing line ranges and missing branch transitions must be included. `--format=total` must print only the total percentage value. `--precision` controls decimal places. `--fail-under` must exit with status `2` when total coverage is below the threshold.

**JSON, XML, HTML, and LCOV reports.** `coverage json` writes a JSON report containing per-file coverage data and totals. When `--show-contexts` is supplied, context information must be included in the per-file data. `coverage xml` writes a Cobertura-style XML report. `coverage html` writes an HTML report directory containing `index.html` and per-file source pages. Each report command accepts `-o` or `-d` for output location.

**Combine and erase.** `coverage combine` reads multiple data files and writes a single combined file. `--keep` preserves input data files after combining. `--parallel-mode` data files are found automatically near the configured data file. `coverage erase` removes the configured data file and must leave no data available for subsequent reports.

**Debug.** `coverage debug data` must report information about measured files in the data file.

## Configuration

The package reads configuration from `.coveragerc` by default, and also looks for coverage sections in `setup.cfg`, `tox.ini`, and `pyproject.toml`.

**Run settings.** Common `[run]` settings include `branch`, `source`, `include`, `omit`, `parallel`, `data_file`, `relative_files`, `context`, and `dynamic_context`. When `branch = True` is configured, branch data must be recorded without requiring the CLI flag.

**Report settings.** `[report]` settings include `precision`, `fail_under`, `show_missing`, `skip_covered`, and output filenames. When `show_missing = True` is configured, the report command must include missing line information.

**Environment variables.** `COVERAGE_FILE` overrides the data-file path. `COVERAGE_RCFILE` selects a specific configuration file.

**Invalid configuration.** Malformed configuration files or invalid configuration values must raise `ConfigError`.

## Measurement and Data Semantics

Measurement records which code executed during a program run, and data objects manage the resulting information.

**Statement coverage.** Statement coverage records executable source lines that were run. The package analyzes Python source to decide which lines are executable.

**Branch coverage.** Branch coverage records transitions between line numbers as `(from_line, to_line)` pairs. Negative line numbers represent entry to or exit from a code object. Missing branch output identifies transitions that did not happen. When branch measurement is enabled, `CoverageData.has_arcs()` must return `True` and `arcs(filename)` must return recorded transitions.

**Contexts.** A static context is fixed for a run via `context`. Dynamic contexts can change during execution through `Coverage.switch_context()`. When both static and dynamic contexts apply, they are recorded together separated by a pipe (e.g., `"static|dynamic"`). `measured_contexts()` must return recorded context names.

**In-memory data.** When `data_file=None`, measurement must be kept in memory without writing a disk file. `Coverage.get_data()` must return the associated `CoverageData` object.

**CoverageData persistence.** `CoverageData` manages measured data. A data object is associated with a base filename via `basename`, or can be created with `no_disk=True` for in-memory operation. `read()` opens an existing data file. `write()` persists current data. `erase()` removes in-memory data and deletes the data file.

**Line and arc operations.** `add_lines(data_dict)` inserts line execution data. `add_arcs(data_dict)` inserts branch transition data. `lines(filename)` returns executed line numbers as a sorted list, or an empty list for a measured file with no executed lines, or `None` for an unmeasured file. `arcs(filename)` returns executed transitions as sorted `(from_line, to_line)` pairs.

**Serialization.** `dumps()` serializes data to bytes. `loads(blob)` deserializes data from bytes. Serialized data must preserve lines, arcs, files, and contexts.

**File operations.** `touch_file(filename, plugin_name=...)` marks a file as measured without line data and records the optional plugin tracer name. `file_tracer(filename)` returns the tracer name recorded for a file. `purge_files(filenames)` removes measurement records for named files. `update(other)` merges another data object into the receiver, preserving measured files, contexts, lines, arcs, and file tracer names.

**Context filtering.** `set_query_context(context)` and `set_query_contexts(contexts)` narrow later `lines()`, `arcs()`, and `contexts_by_lineno()` calls. When the context does not match recorded data, queries must return empty results rather than raising.

**Exclusion rules.** `Coverage.exclude(regex)` adds a regular expression to the exclusion list. `clear_exclude()` clears the exclusion list. `get_exclude_list(which)` returns configured exclusion regular expressions. Excluded lines must not be reported as missing statements.

## Report Semantics

Reports calculate coverage from measured data and source analysis.

**Text reports.** Text reports show file rows and a TOTAL row. Missing line ranges are compacted into readable ranges. The total coverage percentage must agree between text, JSON, XML, HTML, and LCOV reports generated from the same data.

**JSON reports.** `Coverage.json_report(outfile=..., pretty_print=...)` must write a JSON file containing `totals` with `percent_covered`, `covered_lines`, `num_statements`, and branch-related counts. Per-file data must include contexts when `show_contexts` is enabled.

**XML reports.** `Coverage.xml_report(outfile=...)` must write a Cobertura-style XML document with a root `<coverage>` element containing branch rate, branch coverage counts, and per-line data with `condition-coverage` and `missing-branches` attributes for branch lines.

**HTML reports.** `Coverage.html_report(directory=...)` must write a directory containing `index.html` and per-file source pages.

**LCOV reports.** `Coverage.lcov_report(outfile=...)` must write an LCOV file containing `SF:` source file entries and `DA:line,count` hit data.

**Annotate reports.** `Coverage.annotate(directory=...)` must write annotated source files using `>` for executed lines and `!` for missed lines.

**Analysis methods.** `Coverage.analysis(filename)` must return `(filename, statements, missing, missing_text)`. `Coverage.analysis2(filename)` must return structured data including excluded lines. `Coverage.branch_stats(filename)` must return, for each branch line, a `(total_exits, taken_exits)` tuple.

**Report totals.** All programmatic report methods must return the total coverage percentage as a float. When multiple report methods are called on the same data, they must return the same total.

## State Model

A coverage run has one measured data set containing files, executed lines or arcs, contexts, and optional file-tracer names. The active `Coverage` object, `CoverageData`, the configured data file, report methods, and CLI commands are public projections of that same state.

- Data collected by `Coverage` must be visible through `get_data()` and through a `CoverageData` object that reads the written data file.
- Line, branch, and context filters must select the same measurements in programmatic queries and generated reports.
- JSON, XML, HTML, LCOV, annotate, and text reports generated from the same data must agree on measured files and overall coverage totals.
- `combine()` must merge parallel data into the same state subsequently read by report commands and programmatic `CoverageData` queries.

## Error Semantics

`CoverageException` is the base class for coverage.py exceptions. It can carry a short `slug` identifying related documentation.

`ConfigError` is raised for invalid configuration files or invalid configuration values.

`DataError` is raised for invalid, unreadable, incompatible, or conflicting coverage data.

`NoDataError` is raised when a report or analysis requires measured data and none is available.

`NoSource` is raised when coverage.py cannot find source for a measured module or file. `NoCode` is a `NoSource` subclass for files with no Python code.

`NotPython` is raised when a source file cannot be parsed as Python.

`PluginError` is raised when a plugin violates the expected plugin contract.

`CoverageWarning` is a warning category for non-fatal coverage.py warnings.

## Cross-View Invariants

1. A file measured by `coverage run` must appear as a measured file through `CoverageData.measured_files()` and must contribute to `coverage report`, `coverage json`, `coverage xml`, and `coverage html` unless filters omit it.
2. A run made with statement coverage must produce line data: `CoverageData.has_arcs()` must be false, `lines(filename)` must report executed lines, and branch columns must be absent from ordinary text reports.
3. A run made with branch coverage must produce arc data: `CoverageData.has_arcs()` must be true, `arcs(filename)` must report transitions, and reports must include branch and partial-branch information.
4. The same configured data file must be used consistently by CLI commands, `Coverage(data_file=...)`, `CoverageData(basename=...)`, and `COVERAGE_FILE`.
5. Static and dynamic contexts recorded during measurement must be visible through `CoverageData.measured_contexts()`, must narrow data queries, and must narrow report output with context filters.
6. Combining data must preserve the union of measured files, contexts, and executed lines or arcs from the input data files.
7. Include and omit patterns must affect measurement and reporting by filename pattern; files omitted from measurement must not later appear as measured data.
8. Excluded lines must not be reported as missing statements, and excluded branch choices must not create partial-branch obligations.
9. Programmatic report methods and their corresponding CLI reporting commands must describe the same measured data when given the same data file, source files, and filters.
10. Erasing data through the CLI or API must remove the persisted data so later reporting without new measurement has no measured data to report.

## Public Interface

### Import Surface

The package is imported as `coverage`. The command-line program is invoked as `coverage` when installed, and equivalently as `python -m coverage` when the package is on `PYTHONPATH`.

Public imports:

```python
import coverage
from coverage import Coverage, CoverageData, CoverageException
from coverage import __version__, version_info
from coverage import process_startup
from coverage import CoveragePlugin, FileReporter, FileTracer, CodeRegion
from coverage.exceptions import (
    ConfigError, DataError, NoDataError, NoSource, NoCode,
    NotPython, PluginError, CoverageWarning,
)
```

`coverage.coverage` is a compatibility alias for `coverage.Coverage`.

The command line has the form:

```text
coverage <command> [options] [args]
```

Supported commands in this packet are `help`, `run`, `report`, `json`, `html`, `xml`, `combine`, `erase`, and `debug`.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| `Coverage` | class | Control measurement, reporting, and data persistence for a run |
| `Coverage.current` | class method | Return the active coverage object for the current thread, if any |
| `Coverage.start` | method | Begin collecting coverage data |
| `Coverage.stop` | method | Stop collecting coverage data |
| `Coverage.collect` | context manager | Measure code executed inside the block |
| `Coverage.save` | method | Write measured data to the configured data file |
| `Coverage.load` | method | Read existing data into the object |
| `Coverage.erase` | method | Remove existing data for the configured data file |
| `Coverage.get_data` | method | Return the associated coverage data object |
| `Coverage.get_option` | method | Read a configuration option |
| `Coverage.set_option` | method | Set a configuration option |
| `Coverage.switch_context` | method | Change the active dynamic context label |
| `Coverage.exclude` | method | Add a regular expression to an exclusion list |
| `Coverage.clear_exclude` | method | Clear one exclusion list |
| `Coverage.get_exclude_list` | method | Return configured exclusion regular expressions |
| `Coverage.analysis` | method | Analyze a module or filename against loaded data |
| `Coverage.analysis2` | method | Analyze a module or filename and return structured missing-line data |
| `Coverage.branch_stats` | method | Return branch exit statistics for a measured file |
| `Coverage.report` | method | Generate a text coverage report |
| `Coverage.json_report` | method | Generate a JSON coverage report |
| `Coverage.html_report` | method | Generate an HTML coverage report |
| `Coverage.xml_report` | method | Generate an XML coverage report |
| `Coverage.lcov_report` | method | Generate an LCOV coverage report |
| `Coverage.annotate` | method | Generate annotated source output |
| `Coverage.combine` | method | Merge parallel or external data files into the current object |
| `CoverageData` | class | Read, write, query, and merge persisted coverage data |
| `CoverageData.base_filename` | method | Return the configured base data filename |
| `CoverageData.data_filename` | method | Return the resolved on-disk data filename |
| `CoverageData.read` | method | Open an existing data file if present |
| `CoverageData.write` | method | Persist current in-memory data |
| `CoverageData.erase` | method | Remove in-memory data and delete data files |
| `CoverageData.dumps` | method | Serialize data to bytes |
| `CoverageData.loads` | method | Deserialize data from bytes |
| `CoverageData.has_arcs` | method | Report whether arc data is stored |
| `CoverageData.measured_files` | method | Return measured file paths |
| `CoverageData.measured_contexts` | method | Return recorded context names |
| `CoverageData.lines` | method | Return executed line numbers for a file |
| `CoverageData.arcs` | method | Return executed branch transitions for a file |
| `CoverageData.contexts_by_lineno` | method | Map line numbers to executing contexts |
| `CoverageData.file_tracer` | method | Return the tracer name recorded for a file |
| `CoverageData.set_query_context` | method | Narrow later queries to one context |
| `CoverageData.set_query_contexts` | method | Narrow later queries to a context list |
| `CoverageData.add_lines` | method | Insert line execution data |
| `CoverageData.add_arcs` | method | Insert branch transition data |
| `CoverageData.add_file_tracers` | method | Record file tracer names |
| `CoverageData.touch_file` | method | Mark a file measured without line data |
| `CoverageData.touch_files` | method | Mark multiple files measured without line data |
| `CoverageData.purge_files` | method | Remove measurement records for named files |
| `CoverageData.update` | method | Merge another data object into the receiver |
| `CoverageData.close` | method | Close the underlying storage handle |
| `process_startup` | function | Start subprocess measurement when configured |
| `coverage.coverage` | alias | Compatibility alias for `Coverage` |

### CLI Entry Points

The console command is `coverage`. Covered commands include `help`, `run`, `report`, `json`, `xml`, `html`, `lcov`, `annotate`, `combine`, `erase`, and `debug data`. Successful commands must return status 0. `coverage report --fail-under` must return status 2 when total coverage is below the threshold. Missing scripts, invalid configuration, missing source, and absent measurement data must return a nonzero status. Running `python -m coverage` is supported and must expose the same command behavior.

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Compatibility covers measurement, contexts, data persistence and merging, configuration, reports, errors, and CLI/API agreement against local Python programs. It observes public data queries, generated report files, structured report fields, totals, exception classes, and exit statuses. Collector internals, tracer implementation, storage schema, exact report whitespace, exact diagnostic wording, HTML styling, and source organization are not part of this contract.
