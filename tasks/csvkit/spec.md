# csvkit Specification

## Product Overview

csvkit is a suite of command-line tools for converting, inspecting, cleaning, reshaping, querying, and exporting tabular data. CSV is the common interchange format: tools read CSV from files or standard input, write their primary result to standard output, and are designed to be chained with pipes or redirected to files.

The suite treats rows, columns, headers, inferred data types, null values, CSV dialect settings, and optional SQL table metadata as the shared facts behind its views. A table can be converted from Excel, JSON, DBF, fixed-width text, or SQL, then projected as filtered CSV, sorted CSV, joined CSV, stacked CSV, JSON, GeoJSON, SQL statements, database query results, statistics, or a Markdown-compatible table.

## Scope

This specification covers:

- The installed console commands `in2csv`, `sql2csv`, `csvclean`, `csvcut`, `csvgrep`, `csvjoin`, `csvsort`, `csvstack`, `csvformat`, `csvjson`, `csvlook`, `csvpy`, `csvsql`, and `csvstat`.
- Shared CSV input options, header handling, column identifiers, type inference controls, null handling, dialect sniffing, line numbers, and standard input/output behavior.
- Conversion to CSV from CSV-like and tabular formats, including JSON, newline-delimited JSON, GeoJSON, fixed-width text with a schema, DBF, XLS, and XLSX.
- Public tabular transformations: cutting, filtering, sorting, joining, stacking, cleaning, formatting, JSON/GeoJSON export, SQL generation/querying, summary statistics, and interactive exploration.
- The legacy top-level Python CSV reader and writer aliases exported by `csvkit`.

## Installable Surface

Installing the `csvkit` package provides the following console commands:

- Input commands: `in2csv`, `sql2csv`.
- Processing commands: `csvclean`, `csvcut`, `csvgrep`, `csvjoin`, `csvsort`, `csvstack`.
- Output and analysis commands: `csvformat`, `csvjson`, `csvlook`, `csvpy`, `csvsql`, `csvstat`.

Each command supports `--help` and `--version`. The version flag prints the command name and the installed csvkit version, then exits.

Most commands accept a single input file and read from standard input when the file is omitted or `-` is used. Commands that accept multiple files use `-` as one input among file paths. Primary output is written to standard output. Diagnostics, validation reports, and command-line errors are written to standard error.

Commands that expose `--add-bom` write a UTF-8 byte order mark before their normal standard-output stream for compatibility with Excel.

Input paths ending in `.gz`, `.bz2`, and `.xz` are read through the corresponding compression formats. Paths ending in `.zst` are supported when Zstandard support is installed.

## Public API

The Python package has a small legacy API at the top-level `csvkit` module:

```python
import csvkit

csvkit.reader
csvkit.writer
csvkit.DictReader
csvkit.DictWriter
```

These names are compatibility aliases for the CSV reader and writer objects supplied by `agate.csv`. They are intended as a drop-in style replacement for the standard library `csv` reader and writer surface in legacy code. New code should prefer using agate directly. The utility modules, utility classes, CLI base classes, conversion helpers, and exception classes are not documented as a general-purpose Python API.

## Behavioral Sections

### Common CSV Input Behavior

Commands that parse CSV share the same dialect and typing controls:

- `--delimiter` sets the input delimiter, and `--tabs` treats input as tab-delimited and overrides `--delimiter`.
- `--quotechar`, `--quoting`, `--no-doublequote`, and `--escapechar` control how quoted fields and escaped delimiter or quote characters are read.
- `--maxfieldsize` sets the maximum accepted size for a single CSV field.
- `--encoding` sets the input text encoding. The default input encoding accepts UTF-8 with an optional UTF-8 byte order mark.
- `--skipinitialspace` ignores whitespace immediately after delimiters.
- `--skip-lines N` skips the first `N` physical lines before reading the header row.
- `--no-header-row` treats the first row as data and creates default headers `a`, `b`, `c`, and so on.
- `--linenumbers` inserts a leading line-number column in command output.
- `--zero` uses zero-based column numbers when interpreting or displaying column positions. Without it, column positions are one-based.

CSV dialect sniffing defaults to a finite sample of the beginning of the file. `--snifflimit 0` disables sniffing, and `--snifflimit -1` uses the entire file as the sample.

Type inference converts parsed values to booleans, numbers, dates, datetimes, timedeltas, text, and nulls where appropriate. `--no-inference` keeps values textual for commands that expose the flag and disables the locale, date format, datetime format, and leading-zero numeric parsing controls for that parse. `--blanks` prevents the default blank-like strings from being converted to null. `--null-value` adds one or more explicit strings that should be read as null. `--date-format` and `--datetime-format` provide explicit `strptime` formats. `--no-leading-zeroes` prevents values with leading zeroes from being parsed as numbers.

Commands normalize their CSV output using csvkit's default formatting: comma delimiter, double-quote quote character, line-feed row terminator, and UTF-8 text. When csvkit commands are chained, input parsing options generally need to be supplied only to the first command that reads the original data.

### Column Identification

Column-selecting commands accept comma-separated column identifiers. Identifiers can be column names, numeric positions, or numeric ranges. Ranges may use `-` or `:` between positions. Open-ended ranges select from the beginning or through the end of the current header.

Numeric identifiers are positional column numbers, not header names, even when a header has the same text as a number. Non-numeric identifiers are matched against header names. Unknown names are errors for inclusion lists, while `csvcut --not-columns` ignores unknown excluded columns. A selected column appears in the output in the order requested. Commands that print column names use the active column numbering base.

`--names` prints available column names and positions, then exits. It requires a header row.

### `in2csv`

`in2csv` converts tabular input to CSV. The input format can be supplied with `--format` as `csv`, `dbf`, `fixed`, `geojson`, `json`, `ndjson`, `xls`, or `xlsx`. If `--format` is omitted, the format is inferred from the input path or from the fixed-width schema option. Standard input requires an explicit format when the format cannot be inferred from a filename.

CSV input is standardized through the common CSV parser. JSON input is converted from an array of objects by default, and `--key` selects a top-level key containing the list of records to convert. Nested JSON object keys are flattened into tabular columns using slash-separated key paths. Newline-delimited JSON reads one JSON object per line. GeoJSON input is flattened to tabular rows. DBF input is read from a filename. Fixed-width input requires `--schema`, a CSV schema with a header row and the columns `column`, `start`, and `length`; schema columns may appear in any order. The `start` values are text-character offsets after decoding. If the first schema data row has `start` equal to `1`, all `start` values in that schema are interpreted as one-based, with `1` naming the first character. Otherwise, `start` values are interpreted as zero-based, with `0` naming the first character. `length` is the number of characters read from the adjusted start position, and extracted fixed-width values are stripped of surrounding whitespace before being written as CSV cells.

Excel input supports both `.xls` and `.xlsx`. `--names` prints worksheet names for Excel files. `--sheet` selects a worksheet. `--write-sheets` writes named or all worksheets to separate CSV files, and `--use-sheet-names` uses worksheet names in those output filenames. `--reset-dimensions` ignores stored worksheet dimensions for XLSX files when the file reports an incorrect used range. `--encoding-xls` supplies an encoding override for XLS files.

### `sql2csv`

`sql2csv` executes SQL and writes the returned rows as CSV. `--db` supplies a SQLAlchemy connection string; when omitted, an in-memory SQLite connection is used. `--query` supplies the SQL text directly and takes precedence over an input file or standard input. If `--query` is omitted, SQL is read from the input file or standard input. `--engine-option` passes key-value options to SQLAlchemy engine creation, and `--execution-option` passes key-value execution options to the connection. `--no-header-row` suppresses the CSV header row in query results.

Statements that return rows produce CSV. Statements that do not return rows complete without row output.

### `csvcut`

`csvcut` selects, excludes, reorders, and truncates CSV columns. `--columns` selects columns by name, position, or range and defaults to all columns. `--not-columns` excludes columns by name, position, or range and ignores unknown excluded names. `--delete-empty-rows` removes rows that are completely empty after cutting. If a data row is longer than the header row, extra cells beyond the header are truncated.

`csvcut` does not filter rows by cell value; row filtering belongs to `csvgrep`.

### `csvgrep`

`csvgrep` filters rows by matching cell values in selected columns. `--columns` selects the columns to search. Exactly one match source is required: `--match` for an exact string, `--regex` for a regular expression, or `--file` for a file whose lines are exact match values after line separators are stripped.

By default, a row matches when all selected columns satisfy the match source. `--any-match` changes this to rows where any selected column matches. `--invert-match` selects non-matching rows instead of matching rows.

### `csvsort`

`csvsort` sorts rows while preserving the header. `--columns` selects the sort key columns by name, position, or range and defaults to all columns. `--reverse` sorts in descending order. `--ignore-case` performs case-insensitive sorting for text values. Sorting uses csvkit's parsed values unless type inference is disabled.

### `csvjoin`

`csvjoin` merges two or more CSV tables. With `--columns`, it performs SQL-like joins on key columns. A single key applies to all inputs; a comma-separated list supplies one key per input in the same order as the files. Without `--columns`, files are joined sequentially by row position without key matching.

The default key join is an inner join. `--outer`, `--left`, and `--right` select full outer, left outer, or right outer joins. For more than two files, left and right joins are applied as a sequence starting from the corresponding side. If only one file is provided, it is copied to standard output.

### `csvstack`

`csvstack` concatenates rows from multiple CSV files under one header. `--groups` supplies one grouping value per input and adds those values as a new column. `--group-name` names that grouping column and is used only with `--groups`. `--filenames` uses each input filename as its grouping value and takes precedence over `--groups`.

### `csvclean`

`csvclean` reports and fixes common CSV shape problems. `--length-mismatch` reports rows whose field count differs from the header. `--empty-columns` reports columns that contain no values. `--enable-all-checks` enables all checks.

Fix options modify the CSV written to standard output. `--header-normalize-space` strips leading and trailing header whitespace and collapses internal whitespace sequences in headers. `--join-short-rows` merges short rows into a single row using `--separator`, which defaults to a newline. `--fill-short-rows` appends missing cells using `--fillvalue`, which defaults to an empty value. `--remove-empty-columns` drops empty columns from standard output.

When checks are enabled, error rows are written to standard error as CSV with line numbers, descriptions, and the original row values. `--label` adds a label column to the error report; `--label -` uses the input filename or `stdin`. Check-only mode writes the input header and all data rows to standard output using csvkit's normal CSV serialization, even when a reported long row contains more fields than the header. It does not drop extra fields or fill missing fields unless a selected fix option changes the row. `--omit-error-rows` writes only rows that pass the selected checks to standard output, so rows reported by `--length-mismatch` are omitted from the data stream when that option is set. If enabled checks find errors, the command exits with status 1 after writing the data and error report.

### `csvformat`

`csvformat` rewrites CSV into a chosen output dialect. `--skip-header` omits the header row from output. `--out-delimiter` sets the output delimiter, `--out-tabs` writes tab-delimited output and overrides the delimiter, and `--out-asv` writes ASCII unit and record separator output and overrides the other delimiter and line terminator controls.

`--out-quotechar`, `--out-quoting`, `--out-no-doublequote`, `--out-escapechar`, and `--out-lineterminator` control output quoting, escaping, and row termination. When output quoting is set to quote-none, an output escape character or empty output quote character is needed for data that would otherwise require escaping.

### `csvjson`

`csvjson` converts CSV to JSON. Without GeoJSON options, it writes an array of objects. `--indent` pretty-prints with the requested indentation. `--key` writes an object keyed by the selected column; key values must be unique.

`--stream` writes newline-separated JSON objects instead of a JSON array. `--lat` and `--lon` switch output to GeoJSON and require each other. In GeoJSON mode, the selected latitude and longitude columns form point coordinates. `--type` and `--geometry` select columns containing GeoJSON geometry type or geometry data. `--key` becomes the GeoJSON feature id. `--crs` adds a coordinate reference system string. A bounding box is calculated by default and `--no-bbox` disables it.

### `csvlook`

`csvlook` renders CSV as a Markdown-compatible fixed-width table. It accepts the common parsing and type inference controls. `--max-rows`, `--max-columns`, and `--max-column-width` truncate displayed rows, columns, or cell text. `--max-precision` truncates displayed decimal precision, and `--no-number-ellipsis` suppresses the ellipsis marker when precision is truncated.

Rows with more cells than the header are errors for `csvlook`. Users can clean, cut, or skip problematic rows before rendering.

### `csvstat`

`csvstat` prints descriptive statistics for CSV columns. It infers each column's type and reports statistics appropriate to that type, such as null presence, unique values, ranges, sums, means, medians, standard deviations, text lengths, frequent values, and row count.

`--columns` restricts the columns analyzed, and structured output contains one row or object per selected column in the selected order. `--csv` writes statistics as CSV with the header fields `column_id`, `column_name`, `type`, `nulls`, `nonnulls`, `unique`, `min`, `max`, `sum`, `mean`, `median`, `stdev`, `len`, `maxprecision`, and `freq`. `--json` writes a JSON array of per-column objects using the same field names; each object contains `column_id` and `column_name`, then includes the statistic fields whose values are available for that column. `column_id` is one-based. `column_name` is the input header name. `type` is the inferred agate data type name, `nulls` is a boolean null-presence value, `nonnulls` is the count of non-null values, `unique` is the count of distinct values, and `min`, `max`, `sum`, `mean`, `median`, `stdev`, `len`, and `maxprecision` carry the corresponding calculated statistic when meaningful for the column type. `freq` is a list of value/count objects in JSON output and a comma-separated value list in CSV output. `--indent` pretty-prints JSON. A single statistic flag such as `--min`, `--max`, `--mean`, or `--count` limits output to that statistic. If a single statistic and a single column are requested, the command writes only the value. `--freq-count` limits the number of frequent values displayed. `--decimal-format` controls decimal formatting, and `--no-grouping-separator` disables grouping separators.

### `csvsql`

`csvsql` turns CSV files into SQL tables or executes SQL workflows around those tables. Without `--db`, it writes SQL `CREATE TABLE` statements for each input table. `--dialect` selects the SQL dialect for generated statements and cannot be combined with a database connection.

`--db` supplies a SQLAlchemy connection string and lets the command execute generated SQL. `--insert` inserts CSV rows into the target table and requires a database connection or query mode. `--tables` supplies table names; otherwise file basenames are used, or `stdin` for standard input. `--no-constraints` omits generated length and null constraints. `--unique-constraint` adds a unique constraint over the named columns. `--db-schema` places tables in the named database schema.

`--no-create` inserts into existing tables without creating them. `--create-if-not-exists` keeps going if a table already exists. `--overwrite` drops an existing table before creating it and cannot be combined with `--no-create`. `--chunk-size` controls batch insert size. `--prefix` adds one or more expressions after `INSERT`, such as dialect-specific conflict handling. `--before-insert` and `--after-insert` execute SQL before or after the insert; multiple statements are separated by `--sql-delimiter`, which defaults to `;`.

When `--query` is supplied, csvkit loads the CSV inputs into a temporary or requested database and executes one or more queries. If no `--db` is supplied in query mode, an in-memory SQLite database is used. Each `--query` value may be SQL text or a path to a file containing SQL. File contents are read before the query text is split by the active SQL delimiter, and `--query` can be supplied multiple times. The result of the last row-returning query is written as CSV.

### `csvpy`

`csvpy` opens a Python shell after loading a CSV file into an object named `reader`. By default `reader` is a CSV reader. `--dict` loads a `DictReader`, and `--agate` loads an agate table. IPython is used when available; otherwise the running Python shell is used. Due to platform limitations, `csvpy` does not accept piped standard input as its data source.

## Error Semantics

Command-line usage errors exit non-zero and write a concise parser error to standard error. Examples include missing required inputs, invalid option combinations, unsupported use of an option for a file type, invalid column identifiers, and operations that require headers when `--no-header-row` is active.

Without `--verbose`, uncaught command errors are rendered as a short exception type and message. Unicode decoding errors are rendered as an encoding hint that names the active input encoding. With `--verbose`, commands allow the full traceback to be displayed.

`in2csv` reports usage errors when standard input is used without enough information to determine the input format, when fixed-width conversion lacks a schema, when sheet-name listing is requested for a non-Excel file, when automatic format detection fails, or when DBF conversion is attempted from standard input.

`csvgrep` requires one of `--match`, `--regex`, or `--file`. `csvclean` requires at least one check or fix option, rejects simultaneous `--join-short-rows` and `--fill-short-rows`, and exits with status 1 when selected checks find error rows. `csvsql` rejects incompatible SQL options such as combining `--dialect` with `--db`, using insert-only options without insert mode, or combining `--overwrite` with `--no-create`.

Exact wording of error messages is not part of the public contract; the command, trigger condition, exit status category, and output stream are.

## Cross-View Invariants

- A table read from a file, read from standard input, or produced by an upstream csvkit command represents the same headers and rows unless the receiving command explicitly filters, sorts, joins, stacks, cleans, or reformats them.
- Common parsing options have the same meaning across commands that accept them. For example, the same delimiter, quote, encoding, null, date, and header options should cause `csvcut`, `csvgrep`, `csvsort`, `csvjson`, `csvlook`, `csvstat`, and `csvsql` to interpret the original CSV consistently.
- Column identifiers mean the same thing across selection, filtering, sorting, statistics, joining, and JSON/GeoJSON options: names match headers, numeric strings are positions, ranges expand over positions, and `--zero` changes the displayed and interpreted numeric base.
- When a command emits CSV for another csvkit command, the downstream command can read that output with default parsing options unless the user intentionally requested a non-default output format.
- Headerless input receives generated headers before column-based operations. Those generated headers participate in later projections just like ordinary headers.
- Type inference and null handling are shared across statistical, JSON, SQL, and display views. Disabling inference or changing null values changes those views consistently.
- `--linenumbers` adds an ordinary leading output column that can be viewed, cut, sorted, filtered, converted to JSON, or loaded into SQL like other columns.
- Operations that change the row set preserve the header. `csvgrep` removes or keeps rows, `csvsort` reorders rows, `csvjoin` combines rows from multiple tables, and `csvstack` appends rows under a combined header.
- Validation output from `csvclean` is separate from cleaned data: standard output remains a CSV data stream, while standard error carries the error report when checks are enabled.

## Representative Workflows

Convert an Excel workbook to CSV, select a few columns, filter for relevant records, inspect the result, and save a normalized CSV:

```bash
in2csv source.xlsx \
  | csvcut -c county,item_name,quantity \
  | csvgrep -c county -m LANCASTER \
  | csvlook
```

The same pipeline can be redirected to a file instead of displayed:

```bash
in2csv source.xlsx \
  | csvcut -c county,item_name,quantity \
  | csvgrep -c county -m LANCASTER \
  > lancaster_items.csv
```

Load CSV data into SQLite, query it, and write query results as CSV:

```bash
csvsql --db sqlite:///example.db --tables items --insert items.csv
sql2csv --db sqlite:///example.db --query "select * from items"
```

Or query CSV files directly with an in-memory SQLite database:

```bash
csvsql --query "select county, count(*) as n from items group by county" items.csv
```

## Non-Goals

- csvkit is not a spreadsheet editor and does not preserve workbook formatting, formulas, charts, styles, or merged-cell presentation.
- csvkit does not promise a broad Python API for utility classes, parser helpers, conversion internals, or exception classes beyond the legacy top-level CSV aliases.
- csvkit is not a general row-expression language. Use other tools for arbitrary value replacement, row mutation, transposition, plotting, CSV diffing, or large-scale database administration.
- csvkit does not guarantee efficient processing for every large input. Joins and SQL query mode may require loading data into memory or a database.
- csvkit does not guarantee exact human-facing wording for parser errors, exception messages, tracebacks, or help text beyond the documented trigger conditions and output streams.
- Optional database backends and optional compression support depend on the corresponding Python packages being installed.

## Evaluation Notes

The implementation is exercised through the installed console commands and the legacy top-level `csvkit` reader and writer aliases. Evaluation focuses on observable behavior: command availability, common CSV parsing controls, column selection semantics, format conversion, pipeline compatibility, JSON and GeoJSON export, SQL generation and query behavior, cleaning diagnostics, statistics, display formatting, and documented error conditions.

Correct behavior is determined from public inputs and outputs: process exit status, standard output data, standard error diagnostics by category, generated files for documented options, and importable top-level aliases. Structured CSV, JSON, SQL, and table output are compared by their documented semantics rather than by private helper classes, internal field names, undocumented modules, or exact wording of incidental error messages.
