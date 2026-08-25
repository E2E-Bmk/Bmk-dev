
# Toml Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`toml` is a Rust workspace implementing the TOML configuration format. It must provide two crates as its primary public surface. The `toml` crate maps TOML documents to and from arbitrary Rust types through the `serde` trait system, and exposes a typed value model (`Value` and `Table`) for documents whose exact layout is not needed. The `toml_edit` crate provides a lossless document model: parsed text is represented as an editable tree of items that keeps every comment, blank line, quote style, number literal form, and whitespace detail intact, so that a document is parsed, edited through a structured API, and serialized back to text with formatting preserved.

Two supporting crates complete the public surface. `toml_datetime` defines the RFC 3339 date-time value types (`Date`, `Time`, `Offset`, `Datetime`) shared by both primary crates. `serde_spanned` defines `Spanned<T>`, which captures the byte range of a deserialized value within its source text. The remaining workspace crates (`toml_parser`, `toml_writer`) are implementation support for parsing and rendering; the specification does not require their public APIs.

The central invariant of the system is round-trip identity across projections. A document parsed from text must serialize back to the same text; a typed value deserialized from a document must re-serialize to a document that deserializes to the same typed value; and the lossless document model and the typed value model must agree on the logical key/value data of any document. Editing operations must be visible consistently across the query API, the iteration order, and the rendered text.

## Non-Goals

- This specification does not require the public APIs of the `toml_parser` and `toml_writer` crates, their event-stream and low-level builder interfaces, or any corpus-compliance harness built on them.
- This specification does not require exact error-message text, caret diagrams, or line/column rendering for errors; only the error types and byte spans stated in the Error Semantics section are contract.
- This specification does not require the order of dotted keys within a table to survive a parse-and-serialize round trip.
- This specification does not require serialized output to reproduce the input's final-newline state: a non-empty document must serialize with a trailing newline, and an empty document must serialize to the empty string.
- This specification does not require exact `Debug` output for public types, or snapshot-identical rendering of any construct beyond the exact renderings stated in the Behavior sections.
- This specification does not require the `toml::macros` module, the deprecated `ImDocument` type, or the `unbounded`, `fast_hash`, and `debug` optional features of the `toml` crate.
- This specification does not require command-line binaries, interactive shells, process exit-code behavior, or terminal output protocols.
- This specification does not require network access, package download behavior, or documentation-site generation.

## Representative Workflows

### Workflow 1: Lossless parse, edit, and re-serialize

```rust
use toml_edit::{value, DocumentMut};

fn main() -> Result<(), toml_edit::TomlError> {
    let input = "hello = 'toml!' # comment\n[abc]\nb = true\n";
    let mut doc: DocumentMut = input.parse()?;
    assert_eq!(doc.to_string(), input);

    doc["abc"]["b"] = value(false);
    assert_eq!(doc.to_string(), "hello = 'toml!' # comment\n[abc]\nb = false\n");

    doc["abc"].as_table_mut().unwrap().insert("c", value(3_i64));
    assert_eq!(doc["abc"]["c"].as_value().and_then(|v| v.as_integer()), Some(3));
    assert!(doc.to_string().contains("c = 3"));
    Ok(())
}
```

### Workflow 2: Typed round trip with span capture

```rust
use serde::{Deserialize, Serialize};
use serde_spanned::Spanned;

#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct Config {
    title: String,
    database: Database,
    servers: Vec<Server>,
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct Database {
    ip: String,
    port: Spanned<u16>,
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct Server {
    name: String,
}

fn main() -> Result<(), toml::de::Error> {
    let text = "title = \"demo\"\n\n[database]\nip = \"192.168.0.1\"\nport = 5432\n\n[[servers]]\nname = \"web\"\n";
    let config: Config = toml::from_str(text)?;
    assert_eq!(config.database.ip, "192.168.0.1");
    assert_eq!(&text[config.database.port.span()], "5432");

    let out = toml::to_string(&config)?;
    let reparsed: Config = toml::from_str(&out)?;
    assert_eq!(config, reparsed);
    Ok(())
}
```

### Workflow 3: Datetime values through the value model

```rust
use toml::value::{Datetime, Offset};
use toml::Value;

fn main() -> Result<(), toml::de::Error> {
    let text = "dt = 1979-05-27T07:32:00Z\n";
    let value: Value = toml::from_str(text)?;
    let dt = value.get("dt").and_then(|v| v.as_datetime()).unwrap();
    assert_eq!(dt.to_string(), "1979-05-27T07:32:00Z");
    assert_eq!(dt.offset, Some(Offset::Z));
    assert_eq!(dt.date.unwrap().year, 1979);

    let parsed: Datetime = "1979-05-27T07:32:00.123456789123Z".parse().unwrap();
    assert_eq!(parsed.time.unwrap().nanosecond, Some(123_456_789));

    assert_eq!(toml::to_string(&value).unwrap(), text);
    Ok(())
}
```

## Behavior: Lossless Document Model and Editing

The `toml_edit` crate must provide a lossless document model: a parsed document is an editable tree of items that retains every character of the input text except where an edit explicitly changes it.

**Document parsing and round-trip identity.**

- When text that is a valid TOML document is parsed with `DocumentMut::from_str` or the `parse` method, the operation must return a `DocumentMut`; when the text is not a valid TOML document, the operation must raise a `TomlError`.
- When the input text is empty, the returned document must contain no items and must serialize to the empty string.
- Serializing a parsed document must return text identical to the input, with two exceptions: when the input is non-empty and does not end with a newline, the output must end with a newline; and the order of dotted keys within a table is not required to match the input order.
- When a document is modified and re-serialized, every character belonging to nodes the edit did not touch — comments, whitespace, quote style, and raw number or key representations — must appear in the output unchanged.
- Nodes parsed from text must report their byte range in the input through `span()`; the reported range must be measured in bytes from the start of the input text. Nodes constructed programmatically must report `span()` returning no range.

**Structure of the item tree.**

- A document must contain a root table, and each table must map keys to items in a sequence that preserves insertion order; iteration over a table must visit the pairs in that order.
- The `Item` type must provide exactly the variants None, Value, Table, and ArrayOfTables, with accessors that return the contained table, array-of-tables, or value when the variant matches and return nothing otherwise, and a method that returns a textual name of the variant.
- The `Item` type must provide `is_value`, `is_table`, and `is_array_of_tables`, each returning whether the item holds that variant.
- `Item::as_integer` and `Item::as_str` must return the 64-bit integer or the string contained in a value item, and must return nothing when the item is not a value holding the matching kind.
- `Item::as_table_like` must return the table view of an item holding a table or an inline table, and must return nothing otherwise; the returned view must provide `iter`, `iter_mut`, `len`, `is_empty`, `get`, `get_mut`, `contains_key`, `insert`, `remove`, `entry`, `clear`, and `fmt`. `Item::make_value` must convert an item holding a table in place into an item holding an inline-table value.
- A table must provide lookup (`get`, `get_mut`, `contains_key`), insertion (`insert`, `entry`), removal (`remove`, `remove_entry`), and iteration (`iter`, `iter_mut`, `keys`, `values`, `values_mut`) over its key/item pairs, plus `len`, `is_empty`, `clear`, and `retain`.
- An array of tables must be an ordered sequence of tables with `push`, `get`, `insert`, `remove`, `clear`, and `retain`, where iteration follows insertion order.
- The `Value` type must provide exactly the variants String, Integer (64-bit), Float (64-bit), Boolean, Datetime, Array, and InlineTable, with `as_*` accessors that return the contained value when the variant matches and return nothing otherwise.
- `toml_edit::Value` must provide `is_str`, `is_integer`, `is_array`, and `is_inline_table`, each returning whether the value holds that variant, and `decorated`, returning the value carrying the given prefix and suffix decoration.
- An inline table must hold key/value pairs where every value is a `Value`; it must provide `get`, `get_mut`, `entry`, `insert`, `remove`, `remove_entry`, `contains_key`, `iter`, `iter_mut`, `keys`, `values`, `values_mut`, `len`, `is_empty`, `clear`, and `retain`.
- An inline table must provide `fmt`, resetting its formatting to the defaults; `get_or_insert`, returning a mutable reference to the value at a key and inserting the given value first when the key is absent; and `into_table`, converting the inline table into a `Table` containing the same entries.
- Values must be constructible from the primitive forms: `Value` must implement `From` for strings, 64-bit integers, 64-bit floats, booleans, datetimes, dates, times, arrays, and inline tables, and must implement `FromIterator` so that iterating values builds an array and iterating key/value pairs builds an inline table; `Array` must implement `FromIterator` so that iterating values builds an array.

**Indexing and insertion.**

- Reading a document or table with `doc["key"]` when the key is absent must panic; reading through an item that is not a table must panic.
- Writing `doc["key"] = item` must insert a new item at that key, or must replace the existing item when the key is present.
- Writing `doc["a"]["b"] = item` must insert `b` into the table at `a` when `a` is a table; when `a` is absent, the operation must create an inline table at `a` and insert `b` into it; when `a` is present but is not a table, the operation must panic.
- When several intermediate keys are absent, the operation must create an inline table at each missing level.

**Table editing semantics.**

- `insert` must return the item previously stored at the key when one exists, and must return nothing when the key was absent.
- When `insert` replaces an existing entry, the key must keep its position in iteration order, and the formatting of the replaced key and value must reset to the defaults stated in the Formatting and Serialization section.
- `remove` must return the removed item, and must return nothing when the key was absent; the removed key must no longer be visible through `get`, `contains_key`, or iteration, and must not appear in the serialized text. The relative order of the remaining entries must be unchanged.
- `remove_entry` must return the removed key/item pair.
- `entry(key).or_insert(item)` must return a mutable reference to the item at the key, inserting the given item first when the key is absent.
- `insert_formatted` must insert a formatted item at the key with the same return semantics as `insert`.
- `Table::decor_mut` must return the table's decoration mutably; the decoration of a table is the whitespace and comments that surround its header.
- A table marked implicit must render without a header of its own; a table marked dotted must render its entries as dotted keys attached to the parent entry rather than as a `[header]` section.
- `sort_values` and `sort_values_by` must reorder the table's own entries by key, must not change the order of sub-tables or sub-arrays, and must apply recursively to dotted tables only.
- `Key::parse` must parse a dotted key path and must return the sequence of keys in the path, raising `TomlError` when the text is not a valid key path.
- `Key` must implement `FromStr`, parsing a key from text and raising `TomlError` when the text is not a valid key, and `Display`, rendering the key in its TOML form; `Key::get` must return the key's text.
- `DocumentMut` must expose the editing API of its root table: `insert`, `insert_formatted`, `remove`, `get_mut`, `iter`, `decor`, `decor_mut`, and `set_trailing`, with the same semantics as the corresponding `Table` methods, where `set_trailing` sets the trailing raw text of the document.

**Array and array-of-tables editing.**

- An array must provide `push` to append, `insert` to insert at an index, `replace` to replace the element at an index, `remove` to remove the element at an index, and `get` to read the element at an index.
- An array must provide `push_formatted`, `insert_formatted`, and `replace_formatted`, which operate like `push`, `insert`, and `replace` on items that carry explicit formatting, and `fmt`, which must reset the array to its default single-line formatting, removing any trailing comma and trailing whitespace.
- An array must provide `sort_by`, which reorders its elements in place according to a comparison function over pairs of array elements.
- `insert`, `replace`, and `remove` at an index beyond the array length must panic; `get` beyond the array length must return nothing.
- `remove` must return the removed element and must leave the relative order of the remaining elements unchanged.
- An array of tables must provide `replace`, replacing the table at an index and returning the previous table, and `len`, returning the number of tables; `replace` at an index beyond the length must panic.

**Dotted keys.**

- Parsing a dotted key such as `a.b = 1` must create a dotted table `a` at the document root with the key `b` stored in it.
- Defining a key that already exists as a value, or defining a sub-key under a key that exists as a value, must raise a parse error for the duplicate key.
- Dotted and non-dotted definitions must agree: after parsing `a.b = 1` followed by `a.c = 2`, both keys must be reachable under the single dotted table `a`, and serializing must render both assignments as dotted key lines under `a`.

## Behavior: Formatting, Rendering, and Serialization

Every key and value in the lossless document model must carry formatting metadata — a prefix, a suffix, and an optional raw representation — that determines exactly how the node renders to text.

**Decoration.**

- Each key, scalar value, array, and inline table must expose its prefix and suffix through `decor()`, with `decor_mut()` for modification; a parsed node must carry the whitespace and comments that surround it in the input, and a programmatically created node must carry no decoration.
- `set_prefix` and `set_suffix` must replace the corresponding part of the decoration; `clear` must reset both to none.
- A value inserted as a table entry with default formatting must render as `key = value`, with a single space between the key and the value.

**Raw representation.**

- A parsed scalar must retain the raw text of its representation, including quote style for strings, the literal form for numbers, and the offset form for datetimes.
- `Formatted::fmt` must clear the raw representation; after `fmt`, the value must render with its default representation, and its span must no longer be reported.
- The default representation of a float must be a TOML float literal that parses back to the same 64-bit float value.
- A key must render quoted when its text is not a valid bare key, and must render bare when it is; clearing a key's raw representation must restore this default behavior.

**Rendering order and forms.**

- A document must render its root key/value pairs first, followed by its tables and arrays of tables in document order, with each table rendered under a `[header]` line and each array-of-tables element under a `[[header]]` line, and any trailing raw text appended at the end.
- A standalone `Value` must render in its inline form: strings quoted, numbers and booleans bare, arrays as `[item, item]`, inline tables as `{ key = value }`, and datetimes as bare literals.
- `toml_edit::ser::to_string` and `to_string_pretty` must serialize any value implementing `Serialize` into TOML text; `to_document` must serialize into a `DocumentMut`; serializing a root that is not table-shaped must raise `toml_edit::ser::Error`.
- `toml_edit::ser::to_string_pretty` must render every array with at least two elements as one element per line; arrays with fewer than two elements must render on a single line.
- `toml::ser::to_string` and `toml::ser::to_string_pretty` must serialize a table-shaped value into a TOML document; `to_string_pretty` must apply the same multiline-array policy as `toml_edit::ser::to_string_pretty`.
- `toml::Value` and `toml::Table` must implement `Display`: a `Table` must render as a TOML document, and a `Value` must render in its inline form, with a table value rendering as an inline table.
- `toml::ser::to_string` on a root that is not table-shaped must raise `toml::ser::Error`: this includes scalars, booleans, characters, byte strings, arrays, tuples, unit values, and `None`.
- When serializing a map whose keys are not strings, `toml::ser::to_string` must raise `toml::ser::Error`.
- When serializing a struct, every field whose value is `None` must be omitted from the output entirely; all other fields must appear.
- When serializing an enum, the output must be a table containing exactly one key, the name of the active variant, with the variant's payload mapped by its shape: a struct variant must map to a table, a tuple variant must map to an array, a newtype variant must map to its wrapped value, and a plain variant must map to a table containing its fields.

## Behavior: Typed Deserialization and Serialization through serde

The `toml` crate must deserialize TOML documents into any serde-supported Rust type and serialize any serde-supported Rust type into TOML, with a fixed mapping between TOML constructs and Rust types.

**Document entry points.**

- `toml::from_str` and `toml::from_slice` must deserialize a TOML document into the requested type, and must raise `toml::de::Error` when the input is not a valid TOML document, when the document does not match the target type, or when the document contains a duplicate key.
- A TOML document must be table-shaped: deserializing text that is a bare value rather than a table must raise `toml::de::Error`.
- Only the first error encountered must be reported: deserialization must stop at the first failure, and the returned error must be that failure.
- `toml::Table::from_str` must parse a document and must raise `toml::de::Error` on any failure; `toml::Value::from_str` must parse a single value and must raise `toml::de::Error` on any failure.
- `toml::de::ValueDeserializer::parse` must parse a single TOML value from text and must raise `toml::de::Error` when the text is not a valid TOML value.
- `toml_edit::de::from_str`, `from_slice`, and `from_document` must apply the same mapping to the lossless document model and must raise `toml_edit::de::Error` on failure.
- `toml::from_str` and `toml::from_slice` must support target types that borrow from the input text; `toml::to_string` and `toml::to_string_pretty` must accept any type implementing `Serialize`, including unsized types.

**Structure mapping.**

- A struct must map to a table, with each field mapping to a key named by the field's serde name.
- A struct field whose type is a struct must map to a `[key]` sub-table.
- A field whose type is a sequence of structs must map to a `[[key]]` array of tables; a field whose type is a sequence of values must map to a `[key, key]` array.
- A field of type `Option<T>` must deserialize to `None` when the key is absent and to the contained value when the key is present.
- A map with string keys must map to a table.
- An enum must deserialize from a table containing exactly one key that names the variant, with the payload mapped by its shape.
- A field of datetime type must deserialize from a bare datetime literal; deserializing a quoted string into a datetime field must raise `toml::de::Error`.
- An integer field must deserialize from a TOML integer whose value fits the field's type; an out-of-range integer must raise `toml::de::Error`.
- A float field must deserialize from a TOML float or integer.
- A missing struct field with no default must raise `toml::de::Error`; unknown keys must be ignored unless the target type rejects them.
- A type mismatch — a value whose TOML form cannot satisfy the target field's type — must raise `toml::de::Error`.

**Span capture.**

- Any field whose type is `Spanned<T>` must deserialize the value as `T` and must additionally capture the byte range of the value's raw text within the input; the input slice at that range must be the raw text of the value.
- When deserializing through `toml_edit::de` a `Spanned` field whose value carries no span information, the operation must raise `toml_edit::de::Error`.
- `Spanned<T>` must implement `Ord` and `PartialOrd` when `T` does, comparing by the contained value, and must implement `AsRef`, returning the contained value.

**Value conversions.**

- `Value::try_into` and `Table::try_into` must deserialize the value tree into the requested type and must raise `toml::de::Error` when the tree does not match.
- `Value::try_from` and `Table::try_from` must serialize any type implementing `Serialize` into the value tree, and must raise `toml::ser::Error` when the value cannot be represented as TOML, such as when it contains an integer wider than 64 bits or a map with non-string keys.
- The `toml::Value` and `toml::Table` types must round trip through the typed entry points: a value tree deserialized with `toml::from_str` must serialize with `toml::to_string` to a document that parses back to an equal value tree.

## Behavior: Datetime and Value Semantics

Date-time values must be first-class values in both crates, with parsing and rendering defined by the RFC 3339 forms used in TOML.

**Datetime types.**

- `Date` must expose public fields `year`, `month`, and `day` with types `u16`, `u8`, and `u8` respectively; `Time` must expose public fields `hour` and `minute` of type `u8`, an optional `second` field of type `u8`, and an optional `nanosecond` field of type `u32`; `Offset` must expose exactly the variants Z and Custom (a signed minute offset); `Datetime` must expose public fields `date`, `time`, and `offset`, each of an optional type.
- The four datetime forms must be supported: an offset date-time, a local date-time without offset, a date, and a time.

**Parsing and rendering.**

- `Datetime::from_str` must accept the four forms and must raise `DatetimeParseError` when the text does not conform.
- A time must contain a two-digit hour and a two-digit minute; a seconds component and a fractional-seconds component are optional. An hour or minute that is not exactly two digits must raise `DatetimeParseError`.
- An hour above 23, a minute above 59, or a second above 60 must raise `DatetimeParseError`; a second of 60 (leap second) must parse.
- A fractional part longer than nine digits must be truncated to nanoseconds by discarding digits beyond the ninth, never rounded; no fractional input raises a parse error.
- An offset must be either the letter Z or a two-digit signed hour and two-digit minute separated by a colon; the Z form and the zero offset form must remain distinct values.
- `Datetime` must implement `Display` so that the rendered form round trips through `from_str` to an equal value: the date must render as `YYYY-MM-DD`; the time must render as `HH:MM:SS` with the seconds shown when present, a fractional part shown when the nanosecond is non-zero with trailing zeros trimmed, and the seconds part shown as `00` when absent but a fraction is present; the offset must render as `Z` for the Z variant and as a signed `HH:MM` otherwise.
- A parsed datetime must render back to the text it was parsed from when that text uses the canonical two-digit forms.

**Serde and value-model integration.**

- `Datetime` must serialize as a bare datetime literal and must deserialize only from a bare datetime literal.
- `Date` must serialize as a bare date literal and must deserialize only from one; `Time` must serialize as a bare time literal and must deserialize only from one.
- `toml::Value::Datetime` must render as a bare datetime literal inside any document it is serialized into.
- `toml_edit::Value` must provide a Datetime variant carrying a formatted datetime, and must implement `From` for `Datetime`, `Date`, and `Time`.

**The typed value model.**

- `toml::Value` must provide exactly the variants String, Integer (64-bit), Float (64-bit), Boolean, Datetime, Array (of values), and Table (of values), with `as_*` accessors, `get` and `get_mut` keyed lookup, and an indexing operator that panics when the key is absent or the container variant does not match.
- `toml::Table` must be the map type backing table values, with `new`, `with_capacity`, `len`, `is_empty`, `get`, `get_mut`, `insert`, `remove`, `remove_entry`, `contains_key`, `iter`, `iter_mut`, `keys`, `values`, `values_mut`, `clear`, `retain`, and `entry`.
- Map iteration must visit keys in ascending lexicographic order when the `preserve_order` feature is not enabled, and must visit keys in insertion order when it is enabled.

## State Model

The system maintains two persistent value states and two transient text states.

- **Lossless tree state**: a `DocumentMut` rooted at a table, where every key, value, and table carries formatting metadata (decoration, raw representation) and, when parsed from text, span information; plus the trailing raw text of the document, which `set_trailing` sets.
- **Typed value state**: a `toml::Value` tree (or a deserialized instance of any user type) with no formatting information.
- **Text state**: the input text being parsed and the output text being rendered.

Transitions:

- Parsing text with `DocumentMut::from_str` or `toml_edit::de` moves text into the lossless tree state; parsing with `toml::from_str` moves text into the typed value state.
- Editing operations (indexing, `insert`, `remove`, `entry`, array and inline-table operations) transform the lossless tree in place; they must never mutate the input text.
- Serializing (`Display`, `to_string`, `to_document`) moves the lossless tree back to text; the round-trip identity invariant governs the result.
- `Value::try_into`, `Table::try_into`, and the `Deserialize` implementation of `Value` move between the typed value state and arbitrary user types.

## Error Semantics

| Condition | Required result |
|---|---|
| Text is not a valid TOML document when parsed with `toml::from_str`, `toml::from_slice`, or `toml::Table::from_str` | must raise `toml::de::Error` carrying a message and the byte span of the offending region |
| Text is not a valid TOML document when parsed with `DocumentMut::from_str` or `parse` | must raise `TomlError` carrying a message and the byte span of the offending region |
| Text is not a valid TOML value when parsed with `toml_edit::Value::from_str` or `toml::Value::from_str` | must raise the corresponding parse error carrying a message and span |
| A document defines the same key twice, or defines a key both as a value and as a table or array of tables | must raise a parse error for the duplicate key |
| The document does not match the target type: missing required field, type mismatch, or integer out of range | must raise `toml::de::Error` (or `toml_edit::de::Error`) |
| The document contains a bare value rather than a table at the top level | must raise `toml::de::Error` |
| A datetime field receives a quoted string | must raise `toml::de::Error` |
| Datetime text does not conform to the four datetime forms in `Datetime::from_str` | must raise `DatetimeParseError` |
| `toml::ser::to_string` receives a root that is not table-shaped, or a map with non-string keys | must raise `toml::ser::Error` |
| `toml_edit::ser::to_string` or `to_document` receives a root that is not table-shaped | must raise `toml_edit::ser::Error` |
| A `Spanned` field is deserialized through `toml_edit::de` from a value without span information | must raise `toml_edit::de::Error` |
| Indexing a document, table, or value at an absent key, or through a container of the wrong kind | must panic |
| `insert`, `replace`, or `remove` on an array at an index beyond its length | must panic |
| Lookup operations (`get`, `contains_key`, `remove`) on an absent key | must return nothing rather than raising |

## Cross-View Invariants

1. **Parse-to-render identity** (parse domain, formatting domain): for any document parsed with `DocumentMut::from_str`, rendering the document must produce text identical to the input, with the two stated exceptions of trailing-newline addition and dotted-key ordering.
2. **Edit visibility** (editing domain, query domain, rendering domain): every item inserted through indexing, `Table::insert`, `entry`, `Array::push`, or `InlineTable::insert` must be returned by the corresponding lookup and iteration methods and must appear in the serialized text; every item removed must be absent from all three.
3. **Typed round trip** (typed deserialization domain, typed serialization domain): for any type implementing `Serialize`, `Deserialize`, and `PartialEq` whose values are representable in TOML, serializing a value and deserializing the result must produce a value equal to the original; values whose serialization must raise an error (non-table roots, non-string map keys) must raise the same error class on every attempt.
4. **Value-model agreement** (lossless domain, typed value domain): parsing the same text with `toml::from_str` into a `Value` and with `toml_edit::DocumentMut::from_str` must expose the same logical key/value data, and re-serializing the `Value` must yield text that parses to the same logical data.
5. **Span agreement** (parse domain, typed deserialization domain): when a `Spanned` field deserializes from text, the reported range must be a byte range of that text whose content is the raw TOML of the value, and any error raised during deserialization of that value must carry a span within the text.
6. **Datetime identity** (datetime domain, document domain, typed domain): a datetime literal parsed by `Datetime::from_str` must equal the `Datetime` obtained by deserializing a document that contains the same literal into a datetime field, and rendering that document must reproduce the literal.
7. **Replacement semantics** (editing domain, rendering domain): after `insert` replaces an existing key, exactly one entry for the key must remain, the value returned by the lookup methods must be the new item, the previous item must be the one returned by `insert`, and the rendered text must contain the new value.

## Public Interface

### Import Surface

The primary crate paths must be importable as shown.

```rust
// The toml facade: typed entry points and the value model
use toml::{from_str, from_slice, to_string, to_string_pretty, Value, Table, Spanned};
use toml::value::{Date, Datetime, DatetimeParseError, Offset, Time};
use toml::map::Map;
use toml::de::{Deserializer, ValueDeserializer, Error as DeError};
use toml::ser::{Serializer, ValueSerializer, Error as SerError};

// The lossless document model
use toml_edit::{
    DocumentMut, Item, Table, Array, ArrayOfTables, InlineTable, Key, Value, RawString,
    Decor, Formatted, Repr, TomlError, Date, Datetime, Time,
};
use toml_edit::de::{from_str, from_slice, from_document, ValueDeserializer, Error as EditDeError};
use toml_edit::ser::{to_string, to_string_pretty, to_document, ValueSerializer, Error as EditSerError};

// Serde integration
use serde::{Serialize, Deserialize};
use serde_spanned::Spanned;
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `toml::from_str` | function | deserialize a TOML document from a string into any `Deserialize` type |
| `toml::from_slice` | function | deserialize a TOML document from bytes into any `Deserialize` type |
| `toml::to_string` | function | serialize any `Serialize` value into a TOML document string |
| `toml::to_string_pretty` | function | serialize with multiline rendering of multi-element arrays |
| `toml::Value` | enum | typed value tree: String, Integer, Float, Boolean, Datetime, Array, Table, with `try_from`, `try_into`, and `Display` rendering |
| `toml::Value::from_str` | impl | parse a single TOML value |
| `toml::Value::try_into` | method | convert a value tree into any `Deserialize` type |
| `toml::Value::try_from` | method | build a value tree from any `Serialize` type, raising `toml::ser::Error` when the value is not representable as TOML |
| `toml::Value` accessors | methods | `get`, `get_mut`, `as_str`, `as_integer`, `as_float`, `as_bool`, `as_datetime`, `as_array`, `as_table` and mutable variants |
| `toml::Table` | type alias | table of `Value`s backed by the map type, with `try_from`, `try_into`, and `Display` rendering |
| `toml::Table::from_str` | impl | parse a TOML document into a table |
| `toml::Table::try_into` | method | convert a table into any `Deserialize` type |
| `toml::Table::try_from` | method | build a table from any `Serialize` type, raising `toml::ser::Error` when the value is not representable as TOML |
| `toml::map::Map` | struct | ordered map with `new`, `with_capacity`, `get`, `get_mut`, `insert`, `remove`, `remove_entry`, `contains_key`, `entry`, `iter`, `iter_mut`, `keys`, `values`, `values_mut`, `len`, `is_empty`, `clear`, `retain` |
| `toml::value::{Date, Time, Offset, Datetime, DatetimeParseError}` | types | RFC 3339 date-time value types with public fields, serde support, and parse/display behavior |
| `toml::Spanned` | re-export | `serde_spanned::Spanned`, byte-range capture during deserialization |
| `toml::de::Deserializer` | struct | low-level document deserializer |
| `toml::de::ValueDeserializer` | struct | low-level value deserializer, constructed from text with `parse` |
| `toml::de::Error` | struct | deserialization errors with message and optional byte span |
| `toml::ser::Serializer` | struct | low-level document serializer |
| `toml::ser::ValueSerializer` | struct | low-level serializer writing into a string, constructed with `new` |
| `toml::ser::Error` | struct | serialization errors with message and optional byte span |
| `toml` features | feature flags | default (std, serde, parse, display) and `preserve_order` (insertion-ordered maps) |
| `toml_edit::DocumentMut` | struct | lossless mutable document with `new`, `from_str`, indexing, `to_string`, root-table editing (`insert`, `insert_formatted`, `remove`, `get_mut`, `iter`, `decor`, `decor_mut`), and `set_trailing` |
| `toml_edit::Document` | struct | spanned document type underlying the lossless model |
| `toml_edit::Item` | enum | None, Value, Table, ArrayOfTables with `as_*` accessors, `is_*` predicates, `as_table_like`, `make_value`, and `span` |
| `toml_edit::TableLike` | trait | table view shared by `Table` and `InlineTable`, returned by `Item::as_table_like`, with the table lookup, insertion, removal, iteration, and formatting methods |
| `toml_edit::Table` | struct | editable table with `get`, `get_mut`, `entry`, `insert`, `insert_formatted`, `remove`, `remove_entry`, `contains_key`, `iter`, `iter_mut`, `keys`, `values`, `values_mut`, `len`, `is_empty`, `clear`, `retain`, `sort_values`, `sort_values_by`, `decor`, `decor_mut`, dotted and implicit flags |
| `toml_edit::Array` | struct | editable value array with `push`, `insert`, `replace`, `remove`, `get`, `iter`, `contains`, `len`, `is_empty`, `sort_by`, formatted variants, `fmt`, and `FromIterator` |
| `toml_edit::ArrayOfTables` | struct | ordered sequence of tables with `push`, `insert`, `replace`, `remove`, `get`, `iter`, `len`, `clear`, `retain` |
| `toml_edit::InlineTable` | struct | editable inline table with `get`, `get_mut`, `entry`, `insert`, `remove`, `remove_entry`, `contains_key`, `iter`, `iter_mut`, `keys`, `values`, `values_mut`, `len`, `is_empty`, `clear`, `retain`, `sort_values`, `sort_values_by`, `fmt`, `get_or_insert`, `into_table` |
| `toml_edit::Key` | struct | table key with decoration, raw representation, `parse`, `new`, `get`, `FromStr`, `Display` |
| `toml_edit::Value` | enum | formatted scalar (String, Integer, Float, Boolean, Datetime), Array, InlineTable with `as_*` accessors, `is_*` predicates, `decor`, `decorated`, and `FromIterator` |
| `toml_edit::RawString` | struct | raw text with optional span and string access |
| `toml_edit::Decor` | struct | prefix/suffix decoration with `new`, `clear`, `prefix`, `suffix`, `set_prefix`, `set_suffix` |
| `toml_edit::Formatted` | struct | value plus optional raw representation and decoration, with `new`, `value`, `into_value`, `as_repr`, `default_repr`, `display_repr`, `fmt`, `decor`, `decor_mut`, `span` |
| `toml_edit::Repr` | struct | raw text representation of a formatted value |
| `toml_edit::TomlError` | struct | parse errors with message and optional byte span |
| `toml_edit::de::{from_str, from_slice, from_document}` | functions | typed deserialization over the lossless model |
| `toml_edit::de::Deserializer` | struct | low-level deserializer over the lossless model |
| `toml_edit::de::ValueDeserializer` | struct | low-level value deserializer over the lossless model, parseable from text |
| `toml_edit::de::Error` | struct | deserialization errors over the lossless model |
| `toml_edit::ser::{to_string, to_string_pretty, to_document}` | functions | typed serialization into the lossless model |
| `toml_edit::ser::ValueSerializer` | struct | low-level serializer producing a value, constructed with `new` |
| `toml_edit::ser::Error` | struct | serialization errors over the lossless model |
| `toml_edit::{Date, Datetime, Time}` | re-exports | `toml_datetime` value types |
| `toml_edit::{array, table, value}` | functions | construct arrays, tables, and value items, each returning an `Item` |
| `toml_edit` features | feature flags | default (parse, display) and `serde` |
| `toml_datetime::{Date, Time, Offset, Datetime, DatetimeParseError}` | types | public-field date-time types shared by both crates |
| `serde_spanned::Spanned` | struct | value plus source byte range, `span`, `get_ref`, `into_inner`, ordering and `AsRef` access |

### CLI Entry Points

The workspace must not provide any command-line binary entry points. There are no required executables, no interactive shells, and no required process-level behaviors such as exit codes, standard-stream protocols, or signal handling. Example programs in the workspace are not required, and their output is not part of the specification.

## Appendix A: Environment

The working environment runs Rust `1.97.1` and Cargo `1.97.1` on Linux without network access. The workspace must declare edition `2024` and a minimum supported Rust version of `1.85` in its root `Cargo.toml`, and must declare its packaging metadata in `Cargo.toml` at the project root so the crates build and resolve through a patched crates.io registry.

The evaluation builds the `toml` crate with its default features plus the `preserve_order` feature, and the `toml_edit` crate with its `parse`, `display`, and `serde` features. Feature names are part of the public interface: enabling `preserve_order` must change only the map ordering behavior stated in the Datetime and Value Semantics section.

Tests are executed with `cargo-nextest`. The following non-target crates are available to the evaluation and must resolve from the local registry: `serde` (with `derive`), `serde_json`, `indexmap`, `winnow`, `foldhash`, `equivalent`, `hashbrown`, `itoa`, `ryu`, and `memchr`. The deliverable workspace must provide four packages: `toml`, `toml_edit`, `toml_datetime`, and `serde_spanned`; the evaluation resolves those package names against the deliverable. The workspace must not be required to provide `toml_parser` or `toml_writer`: this specification does not require their public APIs.

## Appendix B: Assessment Notes

The evaluation measures the behaviors stated in this specification through automated tests compiled against the public APIs listed in the Public Interface section. Tests assert the required outcomes, return values, error types, spans, and invariants; they do not assert internal structure, private helpers, or module layout.

The evaluation does not assert exact error-message text, caret diagrams, or line/column formatting of errors, and it does not require snapshot-identical rendering of any construct beyond the exact renderings stated in the specification: round-trip identity of parsed documents, the default `key = value` rendering of inserted entries, the inline rendering forms of standalone values, the multiline policy for pretty serialization, and the display forms of datetimes.

Tests exercise the lossless editing surface, the typed deserialization and serialization mapping, span capture, datetime semantics, and the cross-view invariants. Behavior is asserted through the public API in all cases; a test that cannot be phrased through the public API is out of scope for the evaluation.
