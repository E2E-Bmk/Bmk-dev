# agate Public Data Specification

## Product Overview

agate is a Python data-analysis library centered on immutable, typed tables.
Users construct tables from in-memory rows or local files, inspect rows and
columns, derive new tables through relational and analytical operations, and
project the same data through local CSV, JSON, and text output.

The primary import surface is `agate`. The public workflow in this package is
deliberately local and deterministic: define typed rows, transform them, and
compare the resulting public table facts across independent projections.

## Scope

This specification covers:

- `Table` and `TableSet` construction from rows, objects, local CSV, and local JSON.
- `TypeTester` and the public `Text`, `Number`, `Boolean`, `Date`, `DateTime`, and
  `TimeDelta` data types with explicit locale or format settings.
- Row and column metadata, keyed access, immutable mapped sequences, and typed values.
- `select`, `exclude`, `where`, `order_by`, `limit`, `distinct`, and `find`.
- `join`, `group_by`, `aggregate`, `having`, `merge`, and table-set proxy methods.
- `compute` with public `Formula`, `Percent`, `PercentChange`, `Rank`, and `Slug`.
- `pivot`, `normalize`, and `denormalize`, including sparse values and metadata.
- Local CSV and JSON round trips, newline-delimited JSON, and table-set directories.
- Stable public text projections from structure, table, and bar-chart output.

## Installable Surface

The package is imported as `agate` and exposes the table classes, public data
types, type tester, aggregations, computations, mapped sequences, and public
exceptions used by the workflows above. Covered public aggregation and
sequence names include `Count`, `Sum`, `Min`, `Max`, `Mean`, and
`MappedSequence`. The required behavior uses documented public names and public
submodules only.

## Product State Model

A `Table` owns ordered column names, typed column values, and immutable rows.
Optional row names provide keyed access to rows and columns. A `TableSet` owns
ordered keys and tables with a shared column schema. Transformations return new
tables or table sets and leave the input data available for comparison.

Data types cast source values at construction time. Derived columns carry the
declared computation type, and grouped or pivoted outputs expose their grouping
keys through ordinary columns and row names.

## Error Semantics

Invalid casts raise a public cast error. Invalid column references raise a
key-related error. Incompatible joins, duplicate computation names without
replacement, invalid join modes, and invalid reshape arguments raise
`ValueError` or another documented public exception. Tests check exception
classes and resulting state, not exact diagnostic wording.

## Cross-View Invariants

The following facts must agree across public projections:

- Column names and public data types remain ordered and inspectable after
  selection, grouping, joins, computation, reshaping, and local I/O.
- Rows written to CSV or JSON and read back with the same public types preserve
  values, order, and selected metadata.
- Grouped aggregate totals agree with the corresponding pivot counts and with
  direct column aggregates.
- Normalizing properties and denormalizing them restores the same key/value
  relationship, including explicit defaults for sparse properties.
- Text output exposes the same headers, labels, values, and data-type names as
  the table objects that produced it.

## Representative Workflow

```python
from agate import Formula, Number, Sum, Table, Text

table = Table(
    [("east", "alpha", "2", "10.50")],
    ["region", "product", "units", "revenue"],
    [Text(), Text(), Number(locale="en_US"), Number(locale="en_US")],
)
computed = table.compute(
    [("line_total", Formula(Number(locale="en_US"),
                            lambda row: row["units"] * row["revenue"]))]
)
summary = computed.group_by("region").aggregate([("revenue", Sum("revenue"))])
```

The same workflow may then be projected through `to_csv`, `to_json`,
`print_structure`, `print_table`, or `print_bars` and checked against the
typed rows and columns.

## Non-Goals

This package does not cover private implementation modules, upstream source
tests, host-specific locale installation, network access, remote services,
database backends, sleeps, timing behavior, process state, or exact whole-output
snapshots. Locale-sensitive parsing is either explicitly configured with
`en_US` or an explicit format, or excluded.

## Invocation Protocol

Run from the task directory with the fixed source checkout supplied on
`PYTHONPATH`:

```text
PYTHONPATH=<fixed-source-checkout> PYTHONDONTWRITEBYTECODE=1 LC_ALL=C LANG=C TZ=UTC
python -m pytest <public-test-directory> -q -W error --json-report
```

The local report is written below `logs/`. The support environment must run the
two public test files without modifying the source checkout or requiring a
service.

## Environment

The intended environment is Python 3.11 on Linux without network access, and
these tests require no remote service. This is an environment contract; the
local replay does not prove network isolation. The support packages `pytest`,
`pytest-json-report`, `Babel`, `isodate`,
`leather`, `parsedatetime`, `python-slugify`, and `pytimeparse` are installed.
The target package is not pre-installed; the fixed source checkout is supplied
as the import surface. A separate Python 3.10 replay uses the same requirements.
All locale-sensitive cases use explicit `en_US` settings or explicit date and
datetime formats.

## Evaluation Notes

The atomic cases establish construction, metadata, type, operation, I/O, and
text contracts. The integration cases compose those public contracts across
multiple operations and compare independent projections. The package records
local reproducibility evidence only; no claim is made about a trusted external
runner or delivery status.
