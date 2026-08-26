# univocity-parsers Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`univocity-parsers` is a flat-file parsing and writing engine for CSV, TSV, and fixed-width formats. One configuration model drives every format: a settings object carries behavior switches (header extraction, column selection, value trimming, null and empty substitutions, safety limits) and a format object carries the character-level dialect (delimiter, quote, quote escape, comment marker, line separator). Parsers expose the same reading surface in each format — whole-input lists, streaming iteration, one-line parsing, and typed `Record` views keyed by header — and writers expose the mirrored producing surface, so a document written with a given settings object parses back to the original values under the same settings.

The engine reads from `java.io.Reader` sources and writes through `java.io.Writer` targets; no file-system or network access is part of the contract.

## Non-Goals

- This specification does not define annotation-driven bean mapping, object routines, or JDBC integration.
- This specification does not define conversion pipelines beyond the typed accessors of `Record`.
- This specification does not define concurrent parsing or the separate-thread input reading option.
- This specification does not define multi-schema (master-detail) parsing or lookahead/lookbehind field matching.
- This specification does not require character-set detection; input arrives as already-decoded character streams.

## Representative Workflows

The first workflow parses a CSV document with headers and reads typed values through records.

```java
import com.univocity.parsers.csv.CsvParser;
import com.univocity.parsers.csv.CsvParserSettings;
import com.univocity.parsers.common.record.Record;
import java.io.StringReader;

CsvParserSettings settings = new CsvParserSettings();
settings.setHeaderExtractionEnabled(true);
CsvParser parser = new CsvParser(settings);

String csv = "name,age,city\n\"Smith, John\",30,NYC\nJane,25,\"LA\"\n";
for (Record record : parser.parseAllRecords(new StringReader(csv))) {
    String name = record.getString("name");
    int age = record.getInt("age");
}
```

The second workflow writes rows and parses them back under the same dialect.

```java
import com.univocity.parsers.csv.CsvWriter;
import com.univocity.parsers.csv.CsvWriterSettings;
import java.io.StringWriter;

StringWriter out = new StringWriter();
CsvWriter writer = new CsvWriter(out, new CsvWriterSettings());
writer.writeHeaders("name", "age");
writer.writeRow("Smith, John", 30);   // value with delimiter is quoted
writer.close();
// out: name,age\n"Smith, John",30\n
```

The third workflow parses a fixed-width document described by named fields.

```java
import com.univocity.parsers.fixed.FixedWidthFields;
import com.univocity.parsers.fixed.FixedWidthParser;
import com.univocity.parsers.fixed.FixedWidthParserSettings;

FixedWidthFields fields = new FixedWidthFields();
fields.addField("id", 4);
fields.addField("name", 6);
FixedWidthParser parser = new FixedWidthParser(new FixedWidthParserSettings(fields));
```

## CSV Parsing

A `CsvParser` is constructed over a `CsvParserSettings` object and reads rows of `String[]` values. This section defines the dialect, the reading entry points, and the value-shaping switches.

**Dialect.** `getFormat()` on the settings returns a `CsvFormat` whose defaults are delimiter `,`, quote `"`, quote escape `"`, and comment marker `#`. `setDelimiter`, `setQuote`, and the other format setters change the dialect. A value containing the delimiter must be enclosed in quotes; inside a quoted value the escape character doubles the quote (`"he said ""hi"""` reads as `he said "hi"`). With `setLineSeparatorDetectionEnabled(true)` the parser accepts `\n`, `\r\n`, or `\r` input transparently. `detectFormatAutomatically()` inspects the input and chooses the delimiter; after parsing, `getDetectedFormat()` on the parser reports the chosen dialect.

**Reading entry points.** `parseAll(Reader)` returns every row as a `List<String[]>`. `parseLine(String)` parses one line to a `String[]`. `beginParsing(Reader)` starts a streaming session in which `parseNext()` returns one row at a time and null at the end of input, and `stopParsing()` ends the session early. `iterate(Reader)` returns an iterable of rows for use in for-each loops. Each entry point applies the same settings.

**Comments and empty lines.** Lines starting with the comment marker are skipped, and empty lines are skipped, both by default.

**Whitespace trimming.** Leading and trailing whitespace around unquoted values is trimmed by default; `trimValues(false)` preserves it.

**Null and empty substitutions.** An absent (unquoted, zero-length) value parses as the configured null value — null by default, replaced by `setNullValue(String)`. A quoted zero-length value (`""`) parses as the configured empty value — null by default, replaced by `setEmptyValue(String)`. The two switches are independent: with a null value of `N/A` and an empty value of `<empty>`, the line `a,,""` parses as `a`, `N/A`, `<empty>`.

**Safety limits.** `setMaxCharsPerColumn(int)` bounds a single value's length; when the input exceeds it, parsing must raise `TextParsingException`.

**Empty input.** Parsing empty input returns an empty list.

## Headers and Column Selection

Header handling and column projection are settings-level behaviors shared by every format.

**Header extraction.** With `setHeaderExtractionEnabled(true)`, the first row is consumed as the header row: it does not appear in parsed output, and `getContext().headers()` on the parser returns it. Without extraction, the first row is ordinary data and `headers()` still reports the first row seen.

**Selection with reordering.** `selectFields(String...)` (by header name) or `selectIndexes(Integer...)` (by zero-based position) restricts output to the chosen columns. By default column reordering is enabled: each output row contains only the selected columns, in the order they were selected — selecting `city` then `name` from a `name,age,city` document yields rows of `[city, name]`.

**Selection without reordering.** With `setColumnReorderingEnabled(false)`, output rows keep the full row length and original positions: selected columns carry their values and unselected columns are null.

**Unknown selections.** Selecting a field name absent from the headers is not an error at selection time; the resulting rows contain no values (an empty projection), and no exception is raised.

**Context.** `getContext()` returns a `ParsingContext` whose `headers()` reports the header row and whose `currentRecord()` reports the count of rows produced so far in the session.

## Records

A `Record` is a typed view over one parsed row, keyed by the document's headers.

**Obtaining records.** `parseAllRecords(Reader)` returns a `List<Record>`; `iterateRecords(Reader)` streams them. Header extraction must be enabled for header-keyed access to work against the document's own header row.

**Typed access.** `getString(String header)`, `getInt`, `getLong`, `getDouble`, and `getBoolean` convert the addressed value; `getValues()` returns the underlying `String[]` row. `getValue(String header, T defaultValue)` returns the default when the stored value is null. A numeric accessor on a non-numeric value must raise `NumberFormatException`. Addressing a header that does not exist must raise `IllegalArgumentException` naming the available columns.

**Metadata.** `getRecordMetadata()` on the parser describes the record schema: `headers()` returns the header row and `containsColumn(String)` tests membership.

## Writing

A `CsvWriter` is constructed over a `CsvWriterSettings` object, with an optional `java.io.Writer` target, and produces one line per row.

**Row production.** `writeRow(Object...)` writes the values separated by the delimiter and terminated by the line separator; `writeRows` writes a collection of rows; `writeHeaders(String...)` writes a header row; `close()` flushes and closes the target. `writeRowToString(Object...)` returns one formatted line without a line separator and without needing a target writer.

**Quoting rules.** A value is enclosed in quotes only when it contains the delimiter or a line separator; a value containing only a quote character is written as-is, unquoted. When a value is quoted, embedded quotes are doubled with the escape character. `setQuoteAllFields(true)` quotes every value unconditionally.

**Null substitution on write.** A null value is written as the writer's configured null value — the empty string by default, replaced by `setNullValue(String)`.

**Round trip.** Under matching settings, a document produced by the writer parses back to the original values, with one documented exception: a null and an empty string are both written as the empty field and both parse back as the parser's null value under default settings.

## TSV Format

TSV uses tab as the delimiter and backslash escape sequences instead of quoting.

**Parsing.** A `TsvParser` over `TsvParserSettings` splits rows on tabs. The two-character sequences `\t` and `\n` inside a value decode to a real tab and a real line break.

**Writing.** A `TsvWriter` over `TsvWriterSettings` encodes a real tab inside a value as the two-character sequence `\t` and a real line break as `\n`, keeping each record on one physical line. `writeHeaders` and `writeRow` behave as in CSV, and a TSV round trip restores values containing tabs and line breaks exactly.

## Fixed-Width Format

Fixed-width documents have no delimiters: each field occupies a fixed number of characters.

**Field layout.** A `FixedWidthFields` object defines the layout, either positionally (`new FixedWidthFields(5, 5, 5)`) or by named fields (`addField(String name, int length)`); named fields become the derived headers reported by the parsing context and usable for record access. An `addField` overload accepts a `FieldAlignment` (`LEFT`, `RIGHT`, `CENTER`) and a padding character.

**Parsing.** A `FixedWidthParser` over `FixedWidthParserSettings(fields)` cuts each line at the configured boundaries and trims surrounding whitespace from each value by default. With header extraction enabled the first physical row is consumed as headers.

**Writing.** A `FixedWidthWriter` over `FixedWidthWriterSettings(fields)` pads every value to its exact field length — with spaces and left alignment by default, or with the field's configured padding character and alignment (a right-aligned field of length 6 padded with `0` writes `42` as `000042`). With `setHeaderWritingEnabled(true)` the writer first emits the field names, each padded to its field length.

## State Model

A settings object is the complete description of a dialect and its behavior switches; parsers and writers are constructed over settings and hold only session state. The public projections of one parsing session are: the row list (`parseAll`), the streamed rows (`parseNext`/`iterate`), the typed records (`parseAllRecords`/`iterateRecords`), and the session context (headers, current record count, detected format). All projections of the same input under the same settings present the same values in the same order.

- A parser can run any number of sessions; each `parseAll`/`beginParsing` call starts fresh state.
- Writers accumulate output on their target writer; `close` completes the document.
- A parser or writer captures its settings at construction; mutating a settings object affects only parsers and writers constructed afterwards, never one already built.

## Error Semantics

| Condition | Required result |
|---|---|
| A value exceeding `setMaxCharsPerColumn` | Parsing must raise `TextParsingException`. |
| `Record` numeric accessor on a non-numeric value | Must raise `NumberFormatException`. |
| `Record` access with a header not in the schema | Must raise `IllegalArgumentException` naming the available columns. |
| Selecting an unknown field name | Not an error: rows parse to an empty projection. |

Comment lines, empty lines, and end of input are normal conditions, not errors: they produce skipped lines, skipped lines, and a null `parseNext` result respectively.

## Cross-View Invariants

1. Write-then-parse round trip: rows written by a writer parse back to the original values under matching settings for CSV, TSV, and fixed-width alike, with the documented null/empty collapse as the only exception.
2. `parseAll`, the `parseNext` stream, and `iterate` over the same input and settings must produce the same rows in the same order.
3. For every record, `getValues()` must equal the `String[]` row that `parseAll` produces at the same position under the same settings.
4. `getContext().headers()` and `getRecordMetadata().headers()` must agree, and with header extraction enabled the header row must not appear among the parsed rows.
5. With column reordering enabled, each output row must contain exactly the selected columns in selection order; with it disabled, the same values must appear at their original indexes with null elsewhere.
6. A value quoted because it contains the delimiter must parse back to the identical unquoted value; a TSV escape sequence written for a tab or line break must decode to the identical character on parse.
7. The fixed-width writer must emit lines whose length equals the sum of the field lengths, and the parser over the same layout must recover the trimmed values.
8. `currentRecord()` after consuming n rows must be n, in every format.

## Public Interface

### Import Surface

```java
import com.univocity.parsers.common.ParsingContext;
import com.univocity.parsers.common.TextParsingException;
import com.univocity.parsers.common.record.Record;
import com.univocity.parsers.common.record.RecordMetaData;
import com.univocity.parsers.csv.CsvFormat;
import com.univocity.parsers.csv.CsvParser;
import com.univocity.parsers.csv.CsvParserSettings;
import com.univocity.parsers.csv.CsvWriter;
import com.univocity.parsers.csv.CsvWriterSettings;
import com.univocity.parsers.fixed.FieldAlignment;
import com.univocity.parsers.fixed.FixedWidthFields;
import com.univocity.parsers.fixed.FixedWidthParser;
import com.univocity.parsers.fixed.FixedWidthParserSettings;
import com.univocity.parsers.fixed.FixedWidthWriter;
import com.univocity.parsers.fixed.FixedWidthWriterSettings;
import com.univocity.parsers.tsv.TsvParser;
import com.univocity.parsers.tsv.TsvParserSettings;
import com.univocity.parsers.tsv.TsvWriter;
import com.univocity.parsers.tsv.TsvWriterSettings;
```

### Public Members

| Type | Public members in scope |
|---|---|
| `CsvParser` | `CsvParser(CsvParserSettings)`; `parseAll(Reader)`, `parseAllRecords(Reader)`, `parseLine(String)`, `beginParsing(Reader)`, `parseNext()`, `stopParsing()`, `iterate(Reader)`, `iterateRecords(Reader)`, `getContext()`, `getRecordMetadata()`, `getDetectedFormat()` |
| `CsvParserSettings` | `getFormat()`, `setHeaderExtractionEnabled(boolean)`, `selectFields(String...)`, `selectIndexes(Integer...)`, `setColumnReorderingEnabled(boolean)`, `setNullValue(String)`, `setEmptyValue(String)`, `trimValues(boolean)`, `setMaxCharsPerColumn(int)`, `setLineSeparatorDetectionEnabled(boolean)`, `detectFormatAutomatically()` |
| `CsvFormat` | `getDelimiter()`, `setDelimiter(char)`, `getQuote()`, `setQuote(char)`, `getQuoteEscape()`, `setQuoteEscape(char)`, `getComment()`, `setComment(char)` |
| `CsvWriter` | `CsvWriter(CsvWriterSettings)`, `CsvWriter(Writer, CsvWriterSettings)`; `writeHeaders(String...)`, `writeRow(Object...)`, `writeRows(Collection)`, `writeRowsAndClose(Iterable)`, `writeRowToString(Object...)`, `close()` |
| `CsvWriterSettings` | `getFormat()`, `setQuoteAllFields(boolean)`, `setNullValue(String)` |
| `TsvParser` / `TsvParserSettings` | the CSV reading surface over the tab dialect |
| `TsvWriter` / `TsvWriterSettings` | the CSV writing surface over the tab dialect |
| `FixedWidthFields` | `FixedWidthFields(int...)`, `addField(String, int)`, `addField(String, int, FieldAlignment, char)` |
| `FixedWidthParser` / `FixedWidthParserSettings` | `FixedWidthParserSettings(FixedWidthFields)`; the shared reading surface plus `setHeaderExtractionEnabled` |
| `FixedWidthWriter` / `FixedWidthWriterSettings` | `FixedWidthWriterSettings(FixedWidthFields)`, `setHeaderWritingEnabled(boolean)`; the shared writing surface |
| `FieldAlignment` | enum constants `LEFT`, `RIGHT`, `CENTER` |
| `Record` | `getString(String)`, `getInt(String)`, `getLong(String)`, `getDouble(String)`, `getBoolean(String)`, `getValue(String, Object)`, `getValues()` |
| `RecordMetaData` | `headers()`, `containsColumn(String)` |
| `ParsingContext` | `headers()`, `currentRecord()` |
| `TextParsingException` | raised on parsing safety-limit violations |

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `CsvParser` | class | CSV reading engine. |
| `CsvParserSettings` | class | CSV parser configuration. |
| `CsvFormat` | class | CSV character dialect. |
| `CsvWriter` | class | CSV producing engine. |
| `CsvWriterSettings` | class | CSV writer configuration. |
| `TsvParser` | class | TSV reading engine. |
| `TsvParserSettings` | class | TSV parser configuration. |
| `TsvWriter` | class | TSV producing engine. |
| `TsvWriterSettings` | class | TSV writer configuration. |
| `FixedWidthParser` | class | Fixed-width reading engine. |
| `FixedWidthParserSettings` | class | Fixed-width parser configuration. |
| `FixedWidthWriter` | class | Fixed-width producing engine. |
| `FixedWidthWriterSettings` | class | Fixed-width writer configuration. |
| `FixedWidthFields` | class | Field layout: lengths, names, alignment, padding. |
| `FieldAlignment` | enum | Fixed-width value alignment. |
| `Record` | interface | Typed, header-keyed view of one row. |
| `RecordMetaData` | interface | Schema of a record set. |
| `ParsingContext` | interface | Session state: headers, record count. |
| `TextParsingException` | exception | Parsing failure carrying location detail. |

### CLI Entry Points

There is no console script for this package. Java callers use the library through Maven dependencies and Java imports.

## Appendix A: Environment

The working environment runs Java 17 on Linux without network access. The Java standard library is available; the target artifact's own declared dependencies resolve through Maven. The assessment environment provides the same JDK and offline execution policy.

The project must provide a Maven `pom.xml` at its root with coordinate `com.univocity:univocity-parsers`. Source must compile through the standard Maven lifecycle using locally available artifacts.

## Appendix B: Assessment Notes

Assessment exercises the public parsing, header/selection, record, writing, TSV, and fixed-width surfaces. Tests compare parsed row contents and order, header reporting, projection shapes under both reordering modes, null/empty substitutions, typed record values and their failure classes, written document text under the documented quoting and padding rules, escape handling, round-trip equality between writers and parsers, and session context counters; they do not require internal parser state, processor classes, or annotation support. Assessment outcomes reflect the proportion of independently passing public behavior cases, with integration cases checking that reading, writing, and projection stay mutually consistent across formats and settings.
