# MiniSQLiteUtils Unit/System Public Packet

## Overview

Build `dbmini.py`, a compact SQLite database utility. It imports structured data, mutates tables, creates derived structures, searches text, and exposes database state as compact JSON.

This task is designed around the distinction between local feature correctness and system correctness. Individual commands should work on their own, but the product is only complete if data, schema, indexes, and error recovery remain consistent across multi-command workflows.

The implementation language is Python 3.11. Place `dbmini.py` at the root of your solution directory. It must run as:

```console
py -3.11 dbmini.py DATABASE COMMAND [ARGS...]
```

Use Python's standard `sqlite3`, `json`, and `csv` libraries. Mutation commands may print a short success message. Data-returning commands must print compact JSON to stdout.

## Feature Set

The product has seven feature modules:

1. `insert`
2. `upsert`
3. `rows` / `query` / `tables` / `schema`
4. `extract`
5. `enable-fts` / `search`
6. `transform`
7. error and atomicity behavior

These modules are intentionally state-dependent. Rows created by `insert` are later read by `rows`, updated by `upsert`, normalized by `extract`, indexed by `enable-fts`, searched by `search`, and reshaped by `transform`.

## Global Invariants

The following invariants define system correctness:

- Primary-key identity and row count should be preserved unless a command explicitly inserts, updates, or drops rows.
- Omitted values during `upsert` must preserve existing column values.
- Derived structures must remain consistent with the command that created or rebuilt them.
- `transform` must preserve rows and primary keys unless a column is explicitly dropped.
- `transform` must not alter unrelated tables.
- Failed commands must not leave half-applied schema or row changes.
- Metadata commands should reflect the actual current database state after previous mutations.

## Data Import

### `insert TABLE FILE --json|--csv [--pk COL[,COL...]] [--alter]`

Insert records into `TABLE`.

- `--json`: `FILE` contains a JSON array of objects or newline-delimited JSON objects.
- `--csv`: `FILE` contains a header row.
- `--pk`: one or more primary-key columns. Compound keys are comma-separated.
- If the table does not exist, create it.
- If `--alter` is set and incoming rows contain new columns, add them before inserting.
- Without `--alter`, unknown columns for an existing table must fail non-zero and preserve existing rows.

Type inference:

- Booleans and integers are stored as `INTEGER`.
- Floats are stored as `REAL`.
- JSON nulls do not determine column type.
- CSV `true` and `false` are stored as integer `1` and `0`.
- Empty CSV fields are stored as empty strings.
- Lists and dicts are stored as compact JSON text.
- Everything else is stored as `TEXT`.

Duplicate primary-key insertions should fail non-zero.

## Upsert

### `upsert TABLE FILE --json|--csv --pk COL[,COL...] [--alter]`

Insert or update records by primary key.

- Existing rows are matched by the complete primary key.
- Columns present in an upsert row update the existing row.
- Columns omitted from an upsert row preserve the existing values.
- New rows are inserted.
- With `--alter`, new incoming columns are added before upserting.
- Without `--alter`, unknown columns must fail non-zero and preserve existing rows.

Compound primary keys must match on all key columns.

## Querying And Metadata

### `rows TABLE [--where SQL] [--order EXPR] [--limit N]`

Return a JSON array of row objects. `--where` is a SQL fragment without the `WHERE` keyword. `--order` is an order expression such as `age desc, name`.

### `query SQL`

Run a SQL query and return a JSON array of row objects.

### `tables [--counts]`

Return table names. With `--counts`, return objects with `table` and `count`.

### `schema TABLE`

Print the `CREATE TABLE` SQL for `TABLE`.

## Extract

### `extract TABLE COLUMN NEW_TABLE`

Normalize repeated non-null text values from `TABLE.COLUMN` into `NEW_TABLE`.

- Create `NEW_TABLE(id INTEGER PRIMARY KEY, value TEXT UNIQUE)`.
- Insert one row per distinct non-null value.
- Assign ids in first-seen row order.
- Replace `COLUMN` on the original table with `COLUMN_id INTEGER`.
- Existing rows should point at the correct lookup id.
- Null source values remain null after extraction.
- Add a foreign key from `COLUMN_id` to `NEW_TABLE(id)` where practical.
- Preserve original row order and all other columns.

## Full Text Search

### `enable-fts TABLE COLUMN [COLUMN...]`

Create or rebuild a SQLite FTS5 table named `TABLE_fts` for the specified text columns.

- The FTS table should reference original rowids so search results can return original table rows.
- Re-running `enable-fts` after data changes must replace old FTS content with current table content.

### `search TABLE QUERY [--limit N]`

Search the FTS table for `TABLE` and return original table rows as JSON.

- Results should be ordered by FTS rank where SQLite exposes it.
- If FTS is not enabled, fail non-zero.

## Transform

### `transform TABLE [--rename OLD:NEW ...] [--drop COL ...] [--not-null COL ...] [--default COL=VALUE ...]`

Recreate `TABLE` with requested schema changes while preserving rows.

Supported changes:

- Rename columns.
- Drop columns.
- Apply `NOT NULL` to named columns.
- Add default-valued columns with `--default`.
- Preserve primary-key columns when they are not dropped.

Default behavior:

- `--default COL=VALUE` may refer to a column that does not yet exist.
- If `COL` does not exist, create it and set every existing row to `VALUE`.
- Defaults are parsed as JSON when possible; otherwise they are strings.
- For example, `--default priority=1` creates integer values, and `--default done=false` creates integer boolean values.

Ordering behavior:

- Rename operations are visible to later transform options in the same command. For example, `--rename name:title --not-null title` is valid.

Failure behavior:

- A missing rename/drop/not-null source column must fail.
- A not-null constraint that existing rows violate must fail.
- Failed transforms must leave the original schema and rows unchanged.

## Error Behavior

Invalid JSON/CSV, missing tables/columns, duplicate primary keys on insert, failed FTS search, invalid transforms, and unknown columns without `--alter` must fail non-zero with useful stderr.

Failed commands must not corrupt existing rows, schemas, lookup tables, unrelated tables, or FTS tables.

## Non-Goals

- No plugin system.
- No GIS.
- No WAL controls.
- No remote imports.
- No table formatting output.
- No automatic FTS trigger maintenance is required beyond explicit `enable-fts` rebuilds.

## Evaluation Style

Hidden tests are split into two scores:

- Unit tests exercise one feature module at a time. When a command needs existing database state, tests may set up that state directly instead of invoking other product commands.
- System tests exercise interactions across at least two feature modules. They inspect final database rows, schemas, derived lookup tables, FTS tables, JSON outputs, metadata, and atomic failure behavior.

System tests are labeled by dimension:

- `cross_feature_dataflow`
- `state_accumulation`
- `global_invariant`
- `error_atomicity`
- `operation_order_sensitivity`
- `boundary_crossing`

The benchmark does not inspect private implementation details.
