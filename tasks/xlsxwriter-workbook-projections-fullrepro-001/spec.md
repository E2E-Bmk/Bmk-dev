# XlsxWriter Workbook Projections Specification

## Product Overview

XlsxWriter is a Python library for constructing XLSX workbooks from an in-memory
public `Workbook` and `Worksheet` API. The covered behavior observes the
workbook through deterministic ZIP members and parsed XML projections rather
than complete binary equality.

## Scope

The covered surface includes:

- Importing `xlsxwriter.Workbook` and reading the public version constants.
- Creating worksheets and formats in a `BytesIO` workbook.
- Writing scalar strings, numbers, booleans, datetimes, formulas, array
  formulas, dynamic array formulas, rich strings, rows, columns, blank cells,
  hyperlinks, and comments.
- Applying row and column settings, freeze panes, merged ranges, and filters.
- Defining global and local names, adding tables, and inserting charts.
- Setting workbook properties and calculation mode.
- Inspecting stable ZIP member names, worksheet cells, shared strings, styles,
  workbook names, table parts, comments, chart parts, drawings, and
  relationships.

## Installable Surface

The import name is `xlsxwriter`. The covered public imports are:

```python
import xlsxwriter
from xlsxwriter import Workbook
```

The workbook is created with a file-like `BytesIO` destination and the
`in_memory` option. Worksheet and chart methods are reached from objects
returned by public factory methods.

## Product State Model

A workbook has ordered worksheets, workbook properties, calculation settings,
defined names, formats, and serialized package parts. A worksheet has cells
with scalar or rich values, formulas, row and column layout, view settings,
merged regions, filters, tables, hyperlinks, comments, and drawings.

Serialization projects these states into worksheet XML, workbook XML, shared
strings, styles, table parts, comments, chart XML, drawing XML, and relationship
parts. The checks compare semantic element names, attributes, text, ranges,
relationship types, and targets.

## Error Semantics

The covered checks assert successful public return values and public exception
types only where behavior is deterministic. They do not depend on exact
diagnostic wording, warning text, timestamps, relationship identifier numbers,
or complete ZIP byte order.

## Cross-View Invariants

Written cell values and formulas SHALL be represented by the corresponding
worksheet cell type, formula text, cached value, or shared-string entry.
Formatting, row settings, column settings, panes, merged ranges, and filters
SHALL appear in their stable worksheet projections.

Defined names SHALL retain their names, local-sheet scope, and formulas.
Tables SHALL retain their names and ranges and have worksheet relationships.
Hyperlinks SHALL distinguish external relationship targets from internal
locations. Comments SHALL retain cell references and authors. Charts SHALL
produce chart, drawing, and worksheet relationship projections.

Workbook properties and calculation policy SHALL be visible in their respective
parts without requiring volatile metadata fields. Repeated equivalent builds
SHALL have the same structural member set.

## Representative Workflow

A representative workflow creates named worksheets and formats, writes a
header and data block, adds formulas and dates, configures rows, columns,
panes, and filters, defines names, adds a table, inserts a chart, and annotates
or links cells. It closes to `BytesIO`, opens the ZIP locally, and observes the
same facts through worksheet XML, shared strings, styles, workbook XML, table
parts, chart parts, comments, drawings, and relationships.

## Non-Goals

The covered behavior excludes macros, VBA projects, images, text boxes,
external files, installed Excel, external executables, network access, sockets,
random data, sleeps, timing races, host-specific state, timestamps, and full
binary snapshots. It also excludes private modules, private object fields,
source tests, undocumented internals, and behaviors that require external
resources.

## Invocation Protocol

The verifier SHALL run the supplied pytest files against an implementation root
provided by `--target-root` or `TARGET_ROOT`. The target root is placed first
on `sys.path` before importing `xlsxwriter`.

An example local invocation is:

```bash
python -m pytest <check-directory> -q --target-root <implementation-root>
```

JSON reporting may be enabled with `pytest-json-report` when recording local
replay evidence.

## Environment

The target environment is Linux with Python 3.11, without network access. The
target package is not pre-installed; the implementation root is supplied at
runtime.

Required local packages:

- `pytest`
- `pytest-json-report`

The checks use only `BytesIO`, ZIP parsing, and XML parsing from the Python
standard library. They do not require Excel, files outside the supplied target
root, credentials, installed fonts, or ambient workbook state.

## Evaluation Notes

The checks use public library calls and inspect stable structural projections.
They intentionally avoid macros, images, external files, timestamps, complete
binary equality, exact incidental exception messages, network access, and
platform-dependent behavior.

Current replay evidence is same-process local replay only. It does not establish
a trusted black-box Stage 4 runner, an external signature, provenance for a
candidate result, final qualification, or a trusted candidate score.
