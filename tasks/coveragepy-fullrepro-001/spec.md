# Coverage.py Specification

## Product Overview

Coverage.py measures which Python code executed while a program ran. It records measured files, executed statement lines, optional branch transitions, and optional measurement contexts. The same measured data can be inspected through a Python API, stored in a `.coverage` data file, combined across runs, and rendered as text, JSON, XML, HTML, LCOV, or annotated source reports.

The main user workflow is:

1. Run Python code under coverage measurement.
2. Save the collected data.
3. Read the data through `Coverage` or `CoverageData`.
4. Produce reports that compare executed data with the executable lines and branches found in source files.

## Scope

This specification covers the local, documented coverage.py contract:

- The `coverage` import package and its documented top-level public names.
- The command-line interface for `coverage help`, `run`, `report`, `json`, `html`, `xml`, `combine`, `erase`, and `debug`.
- Programmatic measurement with `Coverage`, including start/stop, context-manager collection, saving/loading, source include/omit selection, branch measurement, exclusions, contexts, analysis, and reports.
- Public data access with `CoverageData`, including measured files, lines, arcs, contexts, file tracer names, serialization, erasure, update/combination, and file persistence.
- Configuration files and environment variables that affect ordinary measurement and reporting.
- The user-visible meaning of statement coverage, branch coverage, contexts, report totals, missing-line descriptions, and generated report files.
- Public exceptions and warnings raised for configuration, source, data, plugin, and no-data problems.

## Installable Surface

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

## Public API

### Coverage

```python
Coverage(
    data_file=".coverage",
    data_suffix=None,
    cover_pylib=None,
    auto_data=False,
    timid=None,
    branch=None,
    config_file=True,
    source=None,
    source_pkgs=None,
    source_dirs=None,
    omit=None,
    include=None,
    debug=None,
    concurrency=None,
    check_preimported=False,
    context=None,
    messages=False,
    plugins=None,
)
```

`Coverage` controls measurement and reporting. Missing constructor arguments use values from configuration files. `data_file=None` keeps measurement from writing a disk data file. `data_suffix=True` creates a unique dotted suffix for parallel data files. `branch=True` records branch transitions instead of only statement lines. `source`, `source_pkgs`, `source_dirs`, `include`, and `omit` determine which files are measured. `context` sets a static context label for the run.

Important methods:

```python
Coverage.current() -> Coverage | None
cov.start() -> None
cov.stop() -> None
cov.collect() -> context manager
cov.save() -> None
cov.load() -> None
cov.erase() -> None
cov.get_data() -> CoverageData
cov.get_option("section:option") -> object
cov.set_option("section:option", value) -> None
cov.switch_context(new_context: str) -> None
cov.exclude(regex: str, which: str = "exclude") -> None
cov.clear_exclude(which: str = "exclude") -> None
cov.get_exclude_list(which: str = "exclude") -> list[str]
cov.analysis(morf) -> tuple[str, list[int], list[int], str]
cov.analysis2(morf) -> tuple[str, list[int], list[int], list[int], str]
cov.branch_stats(morf) -> dict[int, tuple[int, int]]
cov.report(...) -> float
cov.json_report(...) -> float
cov.html_report(...) -> float
cov.xml_report(...) -> float
cov.lcov_report(...) -> float
cov.annotate(...) -> None
cov.combine(data_paths=None, strict=False, keep=False) -> None
```

`start()` begins collecting data for code that runs after it is called. `stop()` stops collection. `collect()` is a context manager that starts and stops collection around the block. `save()` writes measured data to the configured data file. `load()` reads existing data into the object. `erase()` removes existing data for the configured data file.

`get_data()` returns the `CoverageData` associated with the `Coverage` object. `analysis()` and `analysis2()` analyze a module object or filename against currently loaded data. `analysis2()` returns the filename, executable statement lines, excluded lines, missing lines, and a compact formatted missing-line string. `branch_stats()` returns, for each branch line, a `(total_exits, taken_exits)` tuple.

Report methods read the current data and source files. They return the total coverage percentage as a float when a percentage is meaningful. Text reports can write to a file-like object. JSON, XML, LCOV, and HTML reports write output files or directories according to their arguments and configuration.

### CoverageData

```python
CoverageData(basename=None, suffix=None, no_disk=False, warn=None, debug=None)
```

`CoverageData` manages measured data. A data object is associated with a base filename, a suffix, or an in-memory database. The default base filename is `.coverage`. A data file records either line data or arc data, not both.

Important methods:

```python
data.base_filename() -> str
data.data_filename() -> str
data.read() -> None
data.write() -> None
data.erase(parallel=False) -> None
data.dumps() -> bytes
data.loads(blob: bytes) -> None
data.has_arcs() -> bool
data.measured_files() -> set[str]
data.measured_contexts() -> set[str]
data.lines(filename: str) -> list[int] | None
data.arcs(filename: str) -> list[tuple[int, int]] | None
data.contexts_by_lineno(filename: str) -> dict[int, list[str]]
data.file_tracer(filename: str) -> str | None
data.set_query_context(context: str) -> None
data.set_query_contexts(contexts: list[str] | None) -> None
data.add_lines({filename: {lineno, ...}}) -> None
data.add_arcs({filename: {(fromno, tono), ...}}) -> None
data.add_file_tracers({filename: tracer_name}) -> None
data.touch_file(filename, plugin_name="") -> None
data.touch_files(filenames, plugin_name=None) -> None
data.purge_files(filenames) -> None
data.update(other_data, map_path=None) -> None
data.close(force=False) -> None
```

`read()` opens an existing data file if it exists. `write()` ensures the current data has been written. `erase()` removes in-memory data and deletes the configured data file; with `parallel=True`, it also removes matching parallel data files. `dumps()` and `loads()` serialize and deserialize data for the same coverage.py data format; this serialization is distinct from the SQLite on-disk file.

`lines(filename)` returns executed line numbers for a measured file, `None` for an unmeasured file, and an empty list for a measured file with no executed lines. `arcs(filename)` returns executed branch transitions as `(from_line, to_line)` pairs; negative line numbers represent entry to or exit from a code object. `contexts_by_lineno(filename)` maps each line number to context names that executed it.

`set_query_context()` and `set_query_contexts()` narrow later `lines()`, `arcs()`, and `contexts_by_lineno()` calls. If the context does not match recorded data, queries return empty results rather than raising an exception.

## Command-Line Behavior

### `coverage help`

`coverage help` prints the command summary. `coverage help <command>` prints help for one command. `coverage --version` or `coverage help version` displays the coverage.py version and whether the C extension is available. The exact executable name in help output can vary by platform.

### `coverage run`

```text
coverage run [options] <pyfile> [program options]
coverage run -m <module> [program options]
```

`run` executes a Python script or importable module while collecting coverage data. Program arguments are passed through to the measured program in `sys.argv`. By default, data is written to `.coverage` and an existing data file is replaced. `--append` appends to existing data. `--parallel-mode` writes a uniquely suffixed data file so multiple runs can later be combined.

The `--branch` option records branch transitions. `--source`, `--include`, and `--omit` restrict measured files. `--context` records a static context label. `--data-file` chooses the base output file. `--pylib` includes Python installed-library code. `--timid` uses the simpler tracing core. `--module` runs a module as Python's `-m` switch would.

If no script or module is supplied, the command fails with a usage error. When the measured program raises `SystemExit`, the command returns that exit status. When coverage.py itself reports a controlled configuration, source, or data problem, it returns a nonzero status and prints the problem.

### `coverage report`

`coverage report` reads data and prints a table with each measured file, executable statement count, missed statement count, and coverage percentage. With branch data, branch and partial-branch counts are included. `-m` or `--show-missing` includes missing line ranges and missing branch transitions such as `40->45`.

Options include `--include`, `--omit`, `--contexts`, `--skip-covered`, `--skip-empty`, `--precision`, `--sort`, `--format=text|markdown|total`, and `--fail-under`. `--format=total` prints only the total percentage value. `--fail-under` exits with status `2` if the total coverage is below the configured threshold after applying precision.

### `coverage json`, `coverage xml`, and `coverage html`

`coverage json` writes `coverage.json` by default, or the file named by `-o`. The JSON report includes per-file coverage data and totals, and can include contexts with `--show-contexts`.

`coverage xml` writes `coverage.xml` by default, or the file named by `-o`. The XML report is compatible with the Cobertura style of file and line coverage reporting. Include/source configuration affects whether filenames are complete paths or shortened names.

`coverage html` writes an HTML report directory, `htmlcov` by default or the directory named by `-d`. The directory contains an `index.html` overview and per-file source pages showing executed, missing, excluded, and partial-branch lines. The report may reuse unchanged generated pages in the same directory. The exact generated asset filenames, CSS, and JavaScript are not part of the public contract.

### `coverage combine` and `coverage erase`

`coverage combine` reads multiple data files and writes a single combined data file. With no paths, it searches near the configured data file for matching parallel data files. With paths, it combines data files found at those files or directories. By default, input data files are deleted after a successful combine; `--keep` preserves them. `--append` accumulates into an existing combined file instead of starting fresh.

Different path names for the same source file can be reconciled through `[paths]` configuration or relative-file configuration.

`coverage erase` removes the configured data file. With the default data file, this removes `.coverage`.

### `coverage debug`

`coverage debug <topic>` prints diagnostic information for a supported topic such as `config`, `data`, `sys`, `premain`, `pybehave`, or `sqlite`. Debug output is intended for humans diagnosing an installation or data file; exact formatting is not a compatibility guarantee.

## Configuration

Coverage.py reads configuration from `.coveragerc` by default. If no explicit config file is provided, it also looks for supported coverage sections in `.coveragerc.toml`, `setup.cfg`, `tox.ini`, and `pyproject.toml`. `--rcfile=FILE` and `COVERAGE_RCFILE` select a specific configuration file.

INI configuration uses sections such as `[run]`, `[report]`, `[html]`, `[json]`, and `[xml]`. In `setup.cfg` and `tox.ini`, section names are prefixed with `coverage:`, such as `[coverage:run]`. TOML configuration can use `tool.coverage` sections. Boolean values accept the documented true/false forms for the file type.

Common `[run]` settings include `branch`, `source`, `include`, `omit`, `parallel`, `data_file`, `relative_files`, `context`, and `dynamic_context`. Reporting sections configure defaults such as `precision`, `fail_under`, `show_missing`, `skip_covered`, output filenames, and HTML output directory.

`COVERAGE_FILE` overrides the data-file path used by commands that read or write coverage data. `COVERAGE_PROCESS_START` names a configuration file used by `process_startup()` for subprocess measurement.

## Measurement Semantics

Statement coverage records executable source lines that were run. Coverage.py analyzes Python source to decide which lines are executable, then compares that analysis with measured line data.

Branch coverage records transitions between line numbers. A branch opportunity is a possible transition from one line to another. Missing branch output identifies transitions that did not happen. Lines excluded with coverage pragmas are not counted as missing opportunities for the excluded part.

Contexts label measured data. A static context is fixed for a run. Dynamic contexts can change during execution, for example per test function or through `Coverage.switch_context()`. When both static and dynamic contexts apply, they are recorded together. Combining data preserves context information from each run.

Exclusion rules remove lines or partial branches from missing-code reporting. `Coverage.exclude()` adds regular expressions to the exclusion list. `clear_exclude()` clears one exclusion list. `get_exclude_list()` returns the configured regular expressions for an exclusion list.

## Data Files

Coverage.py stores default data in a SQLite database named `.coverage`. The data file contains schema metadata, measured file paths, contexts, line or arc data, and optional file tracer names. The documented schema is useful for advanced consumers, but normal code should use `CoverageData` because the schema can change across versions.

A data file records either line data or arc data. Combining incompatible or unreadable data can raise `DataError` or print warnings through command-line operations. `CoverageData.update()` merges another data object into the receiver, preserving measured files, contexts, lines, arcs, and file tracer names. A path mapping callable can be used to map file paths while updating.

## Report Semantics

Reports calculate coverage from two inputs: measured data and source analysis. The statement percentage for a file is based on executable statement opportunities and executed statement lines. When branch data is present, branch opportunities contribute to the total.

Text reports show file rows and a TOTAL row. Missing line ranges are compacted into readable ranges. Missing branches are shown as source-to-destination transitions. JSON and XML reports expose structured equivalents of these facts. HTML reports expose the same coverage state through linked pages and highlighted source.

Report filters such as `include`, `omit`, `contexts`, `skip_covered`, and `skip_empty` affect which files or contexts contribute to the rendered report. Filtering should not mutate the underlying data file.

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

1. A file measured by `coverage run` appears as a measured file through `CoverageData.measured_files()` and contributes to `coverage report`, `coverage json`, `coverage xml`, and `coverage html` unless filters omit it.
2. A run made with statement coverage produces line data: `CoverageData.has_arcs()` is false, `lines(filename)` reports executed lines, and branch columns are absent from ordinary text reports.
3. A run made with branch coverage produces arc data: `CoverageData.has_arcs()` is true, `arcs(filename)` reports transitions, and reports can include branch and partial-branch information.
4. The same configured data file is used consistently by CLI commands, `Coverage(data_file=...)`, `CoverageData(basename=...)`, and `COVERAGE_FILE`.
5. Static and dynamic contexts recorded during measurement are visible through `CoverageData.measured_contexts()`, can narrow data queries, and can narrow report output with context filters.
6. Combining data preserves the union of measured files, contexts, and executed lines or arcs from the input data files.
7. Include and omit patterns affect measurement and reporting by filename pattern; files omitted from measurement do not later appear as measured data, and files omitted only at report time remain in the data file.
8. Excluded lines are not reported as missing statements, and excluded branch choices do not create partial-branch obligations.
9. Programmatic report methods and their corresponding CLI reporting commands describe the same measured data when given the same data file, source files, and filters.
10. Erasing data through the CLI or API removes the persisted data so later reporting without new measurement has no measured data to report.

## Representative Workflow

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

## Non-Goals

- Reproducing coverage.py's internal module layout, private attributes, debug implementation, cache details, or helper functions.
- Implementing the C extension tracer or matching which tracing core is selected.
- Matching exact text table spacing, generated HTML asset names, CSS, JavaScript, or byte-for-byte report files.
- Supporting every plugin authoring behavior beyond preserving the documented public imports and ordinary plugin error handling.
- Implementing optional concurrency integrations such as greenlet, gevent, eventlet, multiprocessing patching, or subprocess sitecustomize behavior beyond the documented `process_startup()` trigger.
- Reproducing project-specific development harnesses, demonstration-only helper modules, golden-file comparison infrastructure, or pytest plugin configuration.
- Guaranteeing platform-specific path spelling beyond documented include/omit/path mapping semantics.
- Treating unsupported importable modules as public API merely because their module names have no leading underscore.

## Evaluation Notes

Evaluation should exercise coverage.py through public imports and ordinary command-line workflows. Tests should create temporary Python files, run them under coverage measurement, inspect `CoverageData`, generate reports, combine and erase data files, and verify errors through public exception classes.

Scoring should reward semantic compatibility: measured files, line and branch data, contexts, data-file persistence, report totals, and CLI/API consistency. Checks may inspect structured JSON/XML fields and public `CoverageData` query results, but should avoid exact debug formatting, exact HTML/CSS asset contents, private attributes, project-specific helper behavior, and implementation-specific object representations.

The execution target is local Python code using the standard library. Tests should avoid external services, optional third-party concurrency libraries, and reliance on a C extension tracer.

