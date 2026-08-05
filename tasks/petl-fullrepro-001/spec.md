# PETL Public Table Specification

## Product Overview

PETL provides Python tools for extracting, transforming, loading, and
inspecting tables. A table is an iterable whose first row is a header and
whose later rows are data. Public operations build new table views or
materialize documented projections of the same rows.

The durable facts in this specification are small in-memory tables and local
CSV files. The same facts are observed through row iteration, field
projections, transformed rows, joins, grouped reductions, reshaped tables,
lookups, text inspection, HTML display projections, and CSV round trips.

## Scope

This specification covers the public `petl` package import and the following
documented service-free operations:

- `wrap`, `header`, `fieldnames`, `data`, `values`, and `fromdicts`
- lazy table views and independent repeated iteration
- `cut`, `convert`, `convertall`, `select`, `selectgt`, and `cat`
- local path-based `fromcsv` and `tocsv` with a custom delimiter
- `join`, `leftjoin`, and `outerjoin` over in-memory tables
- `aggregate` with scalar and multiple named reductions
- `pivot` with explicit values for empty cells
- `lookup` and `lookupone`, including compound keys and duplicate handling
- `look`, `lookstr`, and the documented HTML table display projection

Inputs are Python values, lists, tuples, generators wrapped as table
containers, and files created beneath a test-provided temporary directory.
Outputs are table rows, dictionaries, text inspection strings, HTML strings,
or the documented public exception type.

## Installable Surface

The public import is:

```python
import petl as etl
```

The tests use only names re-exported by `petl` or the documented special
display method on a returned table. No private package module is required.
The target package is supplied by the invocation environment rather than by
the task files.

## Product State Model

A table state consists of a header row followed by zero or more data rows.
Field names and zero-based field positions identify values. A transformation
creates a view over a source table; constructing the view does not consume
source rows, while iterating the view applies the transformation.

Joins match rows by a key and retain the left key field once. Outer joins
insert `None`, or the supplied missing value, for an absent side. Aggregation
groups rows by a key and emits one output row per group. A pivot groups by a
row field and creates sorted columns from a second field.

Lookup operations create dictionaries from key values to lists or single
values. Text and HTML views are projections of the current header and data
values and do not change the underlying table.

## Error Semantics

Selecting a field that is not present raises `petl.FieldSelectionError`.
Strict `lookupone` raises `petl.DuplicateKeyError` when a key occurs more than
once. These are public exception classes and the tests do not depend on
incidental exception wording.

## Cross-View Invariants

1. Wrapping a table preserves its rows and permits independent iterators.
2. Header, data, and values projections agree on the same transformed table.
3. A view is lazy at construction and produces the same rows on repeated
   iteration.
4. CSV loading returns strings, and an explicit conversion restores numeric
   values for later transformations.
5. A join and a lookup over the same key expose the same related values.
6. Aggregation and pivot results retain the grouped facts used to produce
   them.
7. Text and HTML display projections contain the current field names and
   values without changing table data.

## Representative Workflows

A local CSV can be loaded, converted, filtered, cut to a public projection,
and written back:

```python
table = etl.fromcsv("sales.csv")
table = etl.convert(table, "amount", int)
table = etl.select(table, "active", lambda value: value == "True")
table = etl.cut(table, "customer", "region", "amount")
etl.tocsv(table, "active-sales.csv")
```

Two in-memory tables can be joined and reduced:

```python
enriched = etl.join(sales, managers, "region")
summary = etl.aggregate(enriched, "manager", sum, "amount")
```

A table can also be reshaped and inspected:

```python
grid = etl.pivot(sales, "region", "category", "amount", sum, missing=0)
text_view = str(etl.lookstr(grid))
html_view = grid._repr_html_()
```

## Non-Goals

- Database, server, socket, remote-file, cloud, and Google Sheets services.
- Network access, service credentials, subprocess pipelines, and host state.
- Optional heavy formats such as Excel, HDF5, NumPy, pandas, Avro, XML, and
  database adapters.
- Private modules, implementation helpers, repository tests, sleeps, timing,
  performance, concurrency, and generated package metadata.
- Full byte-for-byte inspection of table borders, spacing, quoting, or HTML
  layout beyond stable values and documented projection markers.

## Invocation Protocol

Install or otherwise expose the target `petl` package, install the listed
local test requirement, and run pytest from the task directory. The suite
uses the two public test files and creates only temporary local CSV files
through pytest's temporary-directory fixture.

The same public cases are run with Python 3.10 and Python 3.11. Test discovery
uses only the explicit pytest JSON reporter needed for local replay records.

## Environment

Run on Linux with Python 3.11 without network access. Python 3.10 is also
supported for compatibility replay. The target package is not pre-installed;
the runner supplies it through installation or `PYTHONPATH`. The required
test package is `pytest`. No service credentials, endpoints, databases,
optional format adapters, or Docker runtime are required.

## Evaluation Notes

Assertions prioritize returned rows, headers, dictionary contents, lazy
iteration, local file facts, public exception classes, and stable display
markers. Exact incidental alignment and complete rendered snapshots are
intentionally outside the contract.

The local replay records are reproducibility artifacts for this package. They
must be read together with the explicit `ARTIFACT_ONLY` status and the
disclosed same-process evaluation boundary.
