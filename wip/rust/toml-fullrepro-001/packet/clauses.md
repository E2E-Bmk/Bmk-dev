# Clause Sidecar — toml-fullrepro-001, spec_v2

Stable clause IDs for spec_v2.md (spec_version v1 clauses carried forward
unchanged; v2 additive patch per spec_patch_request.md adds TOML-DOC-031..042,
TOML-FMT-017, TOML-SERDE-021..025 and re-quotes TOML-DOC-012, TOML-DOC-024,
TOML-VAL-001). Each row quotes the clause verbatim from the spec and gives its
section anchor. This file is internal to the pipeline; it is never shown to the
candidate.

## Behavior: Lossless Document Model and Editing

| Clause ID | Section | Clause (verbatim) |
|---|---|---|
| TOML-DOC-001 | Document parsing and round-trip identity | "When text that is a valid TOML document is parsed with `DocumentMut::from_str` or the `parse` method, the operation must return a `DocumentMut`; when the text is not a valid TOML document, the operation must raise a `TomlError`." |
| TOML-DOC-002 | Document parsing and round-trip identity | "When the input text is empty, the returned document must contain no items and must serialize to the empty string." |
| TOML-DOC-003 | Document parsing and round-trip identity | "Serializing a parsed document must return text identical to the input, with two exceptions: when the input is non-empty and does not end with a newline, the output must end with a newline; and the order of dotted keys within a table is not required to match the input order." |
| TOML-DOC-004 | Document parsing and round-trip identity | "When a document is modified and re-serialized, every character belonging to nodes the edit did not touch — comments, whitespace, quote style, and raw number or key representations — must appear in the output unchanged." |
| TOML-DOC-005 | Document parsing and round-trip identity | "Nodes parsed from text must report their byte range in the input through `span()`; the reported range must be measured in bytes from the start of the input text. Nodes constructed programmatically must report `span()` returning no range." |
| TOML-DOC-006 | Structure of the item tree | "A document must contain a root table, and each table must map keys to items in a sequence that preserves insertion order; iteration over a table must visit the pairs in that order." |
| TOML-DOC-007 | Structure of the item tree | "The `Item` type must provide exactly the variants None, Value, Table, and ArrayOfTables, with accessors that return the contained table, array-of-tables, or value when the variant matches and return nothing otherwise, and a method that returns a textual name of the variant." |
| TOML-DOC-008 | Structure of the item tree | "A table must provide lookup (`get`, `get_mut`, `contains_key`), insertion (`insert`, `entry`), removal (`remove`, `remove_entry`), and iteration (`iter`, `iter_mut`, `keys`, `values`, `values_mut`) over its key/item pairs, plus `len`, `is_empty`, `clear`, and `retain`." |
| TOML-DOC-009 | Structure of the item tree | "An array of tables must be an ordered sequence of tables with `push`, `get`, `insert`, `remove`, `clear`, and `retain`, where iteration follows insertion order." |
| TOML-DOC-010 | Structure of the item tree | "The `Value` type must provide exactly the variants String, Integer (64-bit), Float (64-bit), Boolean, Datetime, Array, and InlineTable, with `as_*` accessors that return the contained value when the variant matches and return nothing otherwise." |
| TOML-DOC-011 | Structure of the item tree | "An inline table must hold key/value pairs where every value is a `Value`; it must provide `get`, `get_mut`, `entry`, `insert`, `remove`, `remove_entry`, `contains_key`, `iter`, `iter_mut`, `keys`, `values`, `values_mut`, `len`, `is_empty`, `clear`, and `retain`." |
| TOML-DOC-012 | Structure of the item tree | "Values must be constructible from the primitive forms: `Value` must implement `From` for strings, 64-bit integers, 64-bit floats, booleans, datetimes, dates, times, arrays, and inline tables, and must implement `FromIterator` so that iterating values builds an array and iterating key/value pairs builds an inline table; `Array` must implement `FromIterator` so that iterating values builds an array." |
| TOML-DOC-013 | Indexing and insertion | "Reading a document or table with `doc["key"]` when the key is absent must panic; reading through an item that is not a table must panic." |
| TOML-DOC-014 | Indexing and insertion | "Writing `doc["key"] = item` must insert a new item at that key, or must replace the existing item when the key is present." |
| TOML-DOC-015 | Indexing and insertion | "Writing `doc["a"]["b"] = item` must insert `b` into the table at `a` when `a` is a table; when `a` is absent, the operation must create an inline table at `a` and insert `b` into it; when `a` is present but is not a table, the operation must panic." |
| TOML-DOC-016 | Indexing and insertion | "When several intermediate keys are absent, the operation must create an inline table at each missing level." |
| TOML-DOC-017 | Table editing semantics | "`insert` must return the item previously stored at the key when one exists, and must return nothing when the key was absent." |
| TOML-DOC-018 | Table editing semantics | "When `insert` replaces an existing entry, the key must keep its position in iteration order, and the formatting of the replaced key and value must reset to the defaults stated in the Formatting and Serialization section." |
| TOML-DOC-019 | Table editing semantics | "`remove` must return the removed item, and must return nothing when the key was absent; the removed key must no longer be visible through `get`, `contains_key`, or iteration, and must not appear in the serialized text. The relative order of the remaining entries must be unchanged." |
| TOML-DOC-020 | Table editing semantics | "`remove_entry` must return the removed key/item pair." |
| TOML-DOC-021 | Table editing semantics | "`entry(key).or_insert(item)` must return a mutable reference to the item at the key, inserting the given item first when the key is absent." |
| TOML-DOC-022 | Table editing semantics | "A table marked implicit must render without a header of its own; a table marked dotted must render its entries as dotted keys attached to the parent entry rather than as a `[header]` section." |
| TOML-DOC-023 | Table editing semantics | "`sort_values` and `sort_values_by` must reorder the table's own entries by key, must not change the order of sub-tables or sub-arrays, and must apply recursively to dotted tables only." |
| TOML-DOC-024 | Table editing semantics | "`Key::parse` must parse a dotted key path and must return the sequence of keys in the path, raising `TomlError` when the text is not a valid key path." |
| TOML-DOC-025 | Array and array-of-tables editing | "An array must provide `push` to append, `insert` to insert at an index, `replace` to replace the element at an index, `remove` to remove the element at an index, and `get` to read the element at an index." |
| TOML-DOC-026 | Array and array-of-tables editing | "`insert`, `replace`, and `remove` at an index beyond the array length must panic; `get` beyond the array length must return nothing." |
| TOML-DOC-027 | Array and array-of-tables editing | "`remove` must return the removed element and must leave the relative order of the remaining elements unchanged." |
| TOML-DOC-028 | Dotted keys | "Parsing a dotted key such as `a.b = 1` must create a dotted table `a` at the document root with the key `b` stored in it." |
| TOML-DOC-029 | Dotted keys | "Defining a key that already exists as a value, or defining a sub-key under a key that exists as a value, must raise a parse error for the duplicate key." |
| TOML-DOC-030 | Dotted keys | "Dotted and non-dotted definitions must agree: after parsing `a.b = 1` followed by `a.c = 2`, both keys must be reachable under the single dotted table `a`, and serializing must render both assignments as dotted key lines under `a`." |
| TOML-DOC-031 | Structure of the item tree | "The `Item` type must provide `is_value`, `is_table`, and `is_array_of_tables`, each returning whether the item holds that variant." |
| TOML-DOC-032 | Structure of the item tree | "`Item::as_integer` and `Item::as_str` must return the 64-bit integer or the string contained in a value item, and must return nothing when the item is not a value holding the matching kind." |
| TOML-DOC-033 | Structure of the item tree | "`Item::as_table_like` must return the table view of an item holding a table or an inline table, and must return nothing otherwise; the returned view must provide `iter`, `iter_mut`, `len`, `is_empty`, `get`, `get_mut`, `contains_key`, `insert`, `remove`, `entry`, `clear`, and `fmt`. `Item::make_value` must convert an item holding a table in place into an item holding an inline-table value." |
| TOML-DOC-034 | Structure of the item tree | "`toml_edit::Value` must provide `is_str`, `is_integer`, `is_array`, and `is_inline_table`, each returning whether the value holds that variant, and `decorated`, returning the value carrying the given prefix and suffix decoration." |
| TOML-DOC-035 | Structure of the item tree | "An inline table must provide `fmt`, resetting its formatting to the defaults; `get_or_insert`, returning a mutable reference to the value at a key and inserting the given value first when the key is absent; and `into_table`, converting the inline table into a `Table` containing the same entries." |
| TOML-DOC-036 | Table editing semantics | "`insert_formatted` must insert a formatted item at the key with the same return semantics as `insert`." |
| TOML-DOC-037 | Table editing semantics | "`Table::decor_mut` must return the table's decoration mutably; the decoration of a table is the whitespace and comments that surround its header." |
| TOML-DOC-038 | Table editing semantics | "`Key` must implement `FromStr`, parsing a key from text and raising `TomlError` when the text is not a valid key, and `Display`, rendering the key in its TOML form; `Key::get` must return the key's text." |
| TOML-DOC-039 | Table editing semantics | "`DocumentMut` must expose the editing API of its root table: `insert`, `insert_formatted`, `remove`, `get_mut`, `iter`, `decor`, `decor_mut`, and `set_trailing`, with the same semantics as the corresponding `Table` methods, where `set_trailing` sets the trailing raw text of the document." |
| TOML-DOC-040 | Array and array-of-tables editing | "An array must provide `push_formatted`, `insert_formatted`, and `replace_formatted`, which operate like `push`, `insert`, and `replace` on items that carry explicit formatting, and `fmt`, which must reset the array to its default single-line formatting, removing any trailing comma and trailing whitespace." |
| TOML-DOC-041 | Array and array-of-tables editing | "An array of tables must provide `replace`, replacing the table at an index and returning the previous table, and `len`, returning the number of tables; `replace` at an index beyond the length must panic." |

## Behavior: Formatting, Rendering, and Serialization

| Clause ID | Section | Clause (verbatim) |
|---|---|---|
| TOML-FMT-001 | Decoration | "Each key, scalar value, array, and inline table must expose its prefix and suffix through `decor()`, with `decor_mut()` for modification; a parsed node must carry the whitespace and comments that surround it in the input, and a programmatically created node must carry no decoration." |
| TOML-FMT-002 | Decoration | "`set_prefix` and `set_suffix` must replace the corresponding part of the decoration; `clear` must reset both to none." |
| TOML-FMT-003 | Decoration | "A value inserted as a table entry with default formatting must render as `key = value`, with a single space between the key and the value." |
| TOML-FMT-004 | Raw representation | "A parsed scalar must retain the raw text of its representation, including quote style for strings, the literal form for numbers, and the offset form for datetimes." |
| TOML-FMT-005 | Raw representation | "`Formatted::fmt` must clear the raw representation; after `fmt`, the value must render with its default representation, and its span must no longer be reported." |
| TOML-FMT-006 | Raw representation | "The default representation of a float must be a TOML float literal that parses back to the same 64-bit float value." |
| TOML-FMT-007 | Raw representation | "A key must render quoted when its text is not a valid bare key, and must render bare when it is; clearing a key's raw representation must restore this default behavior." |
| TOML-FMT-008 | Rendering order and forms | "A document must render its root key/value pairs first, followed by its tables and arrays of tables in document order, with each table rendered under a `[header]` line and each array-of-tables element under a `[[header]]` line, and any trailing raw text appended at the end." |
| TOML-FMT-009 | Rendering order and forms | "A standalone `Value` must render in its inline form: strings quoted, numbers and booleans bare, arrays as `[item, item]`, inline tables as `{ key = value }`, and datetimes as bare literals." |
| TOML-FMT-010 | Rendering order and forms | "`toml_edit::ser::to_string` and `to_string_pretty` must serialize any value implementing `Serialize` into TOML text; `to_document` must serialize into a `DocumentMut`; serializing a root that is not table-shaped must raise `toml_edit::ser::Error`." |
| TOML-FMT-011 | Rendering order and forms | "`toml_edit::ser::to_string_pretty` must render every array with at least two elements as one element per line; arrays with fewer than two elements must render on a single line." |
| TOML-FMT-012 | Rendering order and forms | "`toml::ser::to_string` and `toml::ser::to_string_pretty` must serialize a table-shaped value into a TOML document; `to_string_pretty` must apply the same multiline-array policy as `toml_edit::ser::to_string_pretty`." |
| TOML-FMT-013 | Rendering order and forms | "`toml::ser::to_string` on a root that is not table-shaped must raise `toml::ser::Error`: this includes scalars, booleans, characters, byte strings, arrays, tuples, unit values, and `None`." |
| TOML-FMT-014 | Rendering order and forms | "When serializing a map whose keys are not strings, `toml::ser::to_string` must raise `toml::ser::Error`." |
| TOML-FMT-015 | Rendering order and forms | "When serializing a struct, every field whose value is `None` must be omitted from the output entirely; all other fields must appear." |
| TOML-FMT-016 | Rendering order and forms | "When serializing an enum, the output must be a table containing exactly one key, the name of the active variant, with the variant's payload mapped by its shape: a struct variant must map to a table, a tuple variant must map to an array, a newtype variant must map to its wrapped value, and a plain variant must map to a table containing its fields." |
| TOML-FMT-017 | Rendering order and forms | "`toml::Value` and `toml::Table` must implement `Display`: a `Table` must render as a TOML document, and a `Value` must render in its inline form, with a table value rendering as an inline table." |

## Behavior: Typed Deserialization and Serialization through serde

| Clause ID | Section | Clause (verbatim) |
|---|---|---|
| TOML-SERDE-001 | Document entry points | "`toml::from_str` and `toml::from_slice` must deserialize a TOML document into the requested type, and must raise `toml::de::Error` when the input is not a valid TOML document, when the document does not match the target type, or when the document contains a duplicate key." |
| TOML-SERDE-002 | Document entry points | "A TOML document must be table-shaped: deserializing text that is a bare value rather than a table must raise `toml::de::Error`." |
| TOML-SERDE-003 | Document entry points | "Only the first error encountered must be reported: deserialization must stop at the first failure, and the returned error must be that failure." |
| TOML-SERDE-004 | Document entry points | "`toml::Table::from_str` must parse a document and must raise `toml::de::Error` on any failure; `toml::Value::from_str` must parse a single value and must raise `toml::de::Error` on any failure." |
| TOML-SERDE-005 | Document entry points | "`toml_edit::de::from_str`, `from_slice`, and `from_document` must apply the same mapping to the lossless document model and must raise `toml_edit::de::Error` on failure." |
| TOML-SERDE-006 | Structure mapping | "A struct must map to a table, with each field mapping to a key named by the field's serde name." |
| TOML-SERDE-007 | Structure mapping | "A struct field whose type is a struct must map to a `[key]` sub-table." |
| TOML-SERDE-008 | Structure mapping | "A field whose type is a sequence of structs must map to a `[[key]]` array of tables; a field whose type is a sequence of values must map to a `[key, key]` array." |
| TOML-SERDE-009 | Structure mapping | "A field of type `Option<T>` must deserialize to `None` when the key is absent and to the contained value when the key is present." |
| TOML-SERDE-010 | Structure mapping | "A map with string keys must map to a table." |
| TOML-SERDE-011 | Structure mapping | "An enum must deserialize from a table containing exactly one key that names the variant, with the payload mapped by its shape." |
| TOML-SERDE-012 | Structure mapping | "A field of datetime type must deserialize from a bare datetime literal; deserializing a quoted string into a datetime field must raise `toml::de::Error`." |
| TOML-SERDE-013 | Structure mapping | "An integer field must deserialize from a TOML integer whose value fits the field's type; an out-of-range integer must raise `toml::de::Error`." |
| TOML-SERDE-014 | Structure mapping | "A float field must deserialize from a TOML float or integer." |
| TOML-SERDE-015 | Structure mapping | "A missing struct field with no default must raise `toml::de::Error`; unknown keys must be ignored unless the target type rejects them." |
| TOML-SERDE-016 | Structure mapping | "A type mismatch — a value whose TOML form cannot satisfy the target field's type — must raise `toml::de::Error`." |
| TOML-SERDE-017 | Span capture | "Any field whose type is `Spanned<T>` must deserialize the value as `T` and must additionally capture the byte range of the value's raw text within the input; the input slice at that range must be the raw text of the value." |
| TOML-SERDE-018 | Span capture | "When deserializing through `toml_edit::de` a `Spanned` field whose value carries no span information, the operation must raise `toml_edit::de::Error`." |
| TOML-SERDE-019 | Value conversions | "`Value::try_into` and `Table::try_into` must deserialize the value tree into the requested type and must raise `toml::de::Error` when the tree does not match." |
| TOML-SERDE-020 | Value conversions | "The `toml::Value` and `toml::Table` types must round trip through the typed entry points: a value tree deserialized with `toml::from_str` must serialize with `toml::to_string` to a document that parses back to an equal value tree." |
| TOML-SERDE-021 | Document entry points | "`toml::de::ValueDeserializer::parse` must parse a single TOML value from text and must raise `toml::de::Error` when the text is not a valid TOML value." |
| TOML-SERDE-022 | Document entry points | "`toml::from_str` and `toml::from_slice` must support target types that borrow from the input text; `toml::to_string` and `toml::to_string_pretty` must accept any type implementing `Serialize`, including unsized types." |
| TOML-SERDE-023 | Value conversions | "`Value::try_from` and `Table::try_from` must serialize any type implementing `Serialize` into the value tree, and must raise `toml::ser::Error` when the value cannot be represented as TOML, such as when it contains an integer wider than 64 bits or a map with non-string keys." |
| TOML-SERDE-024 | Span capture | "`Spanned<T>` must implement `Ord` and `PartialOrd` when `T` does, comparing by the contained value, and must implement `AsRef`, returning the contained value." |
| TOML-SERDE-025 | Serde and value-model integration | "`Date` must serialize as a bare date literal and must deserialize only from one; `Time` must serialize as a bare time literal and must deserialize only from one." |

## Behavior: Datetime and Value Semantics

| Clause ID | Section | Clause (verbatim) |
|---|---|---|
| TOML-VAL-001 | Datetime types | "`Date` must expose public fields `year`, `month`, and `day` with types `u16`, `u8`, and `u8` respectively; `Time` must expose public fields `hour` and `minute` of type `u8`, an optional `second` field of type `u8`, and an optional `nanosecond` field of type `u32`; `Offset` must expose exactly the variants Z and Custom (a signed minute offset); `Datetime` must expose public fields `date`, `time`, and `offset`, each of an optional type." |
| TOML-VAL-002 | Datetime types | "The four datetime forms must be supported: an offset date-time, a local date-time without offset, a date, and a time." |
| TOML-VAL-003 | Parsing and rendering | "`Datetime::from_str` must accept the four forms and must raise `DatetimeParseError` when the text does not conform." |
| TOML-VAL-004 | Parsing and rendering | "A time must contain a two-digit hour and a two-digit minute; a seconds component and a fractional-seconds component are optional. An hour or minute that is not exactly two digits must raise `DatetimeParseError`." |
| TOML-VAL-005 | Parsing and rendering | "An hour above 23, a minute above 59, or a second above 60 must raise `DatetimeParseError`; a second of 60 (leap second) must parse." |
| TOML-VAL-006 | Parsing and rendering | "A fractional part longer than nine digits must be truncated to nanoseconds by discarding digits beyond the ninth, never rounded; no fractional input raises a parse error." |
| TOML-VAL-007 | Parsing and rendering | "An offset must be either the letter Z or a two-digit signed hour and two-digit minute separated by a colon; the Z form and the zero offset form must remain distinct values." |
| TOML-VAL-008 | Parsing and rendering | "`Datetime` must implement `Display` so that the rendered form round trips through `from_str` to an equal value: the date must render as `YYYY-MM-DD`; the time must render as `HH:MM:SS` with the seconds shown when present, a fractional part shown when the nanosecond is non-zero with trailing zeros trimmed, and the seconds part shown as `00` when absent but a fraction is present; the offset must render as `Z` for the Z variant and as a signed `HH:MM` otherwise." |
| TOML-VAL-009 | Parsing and rendering | "A parsed datetime must render back to the text it was parsed from when that text uses the canonical two-digit forms." |
| TOML-VAL-010 | Serde and value-model integration | "`Datetime` must serialize as a bare datetime literal and must deserialize only from a bare datetime literal." |
| TOML-VAL-011 | Serde and value-model integration | "`toml::Value::Datetime` must render as a bare datetime literal inside any document it is serialized into." |
| TOML-VAL-012 | Serde and value-model integration | "`toml_edit::Value` must provide a Datetime variant carrying a formatted datetime, and must implement `From` for `Datetime`, `Date`, and `Time`." |
| TOML-VAL-013 | The typed value model | "`toml::Value` must provide exactly the variants String, Integer (64-bit), Float (64-bit), Boolean, Datetime, Array (of values), and Table (of values), with `as_*` accessors, `get` and `get_mut` keyed lookup, and an indexing operator that panics when the key is absent or the container variant does not match." |
| TOML-VAL-014 | The typed value model | "`toml::Table` must be the map type backing table values, with `new`, `with_capacity`, `len`, `is_empty`, `get`, `get_mut`, `insert`, `remove`, `remove_entry`, `contains_key`, `iter`, `iter_mut`, `keys`, `values`, `values_mut`, `clear`, `retain`, and `entry`." |
| TOML-VAL-015 | The typed value model | "Map iteration must visit keys in ascending lexicographic order when the `preserve_order` feature is not enabled, and must visit keys in insertion order when it is enabled." |

## State Model

| Clause ID | Section | Clause (verbatim) |
|---|---|---|
| TOML-STATE-001 | Transitions | "Parsing text with `DocumentMut::from_str` or `toml_edit::de` moves text into the lossless tree state; parsing with `toml::from_str` moves text into the typed value state." |
| TOML-STATE-002 | Transitions | "Editing operations (indexing, `insert`, `remove`, `entry`, array and inline-table operations) transform the lossless tree in place; they must never mutate the input text." |
| TOML-STATE-003 | Transitions | "Serializing (`Display`, `to_string`, `to_document`) moves the lossless tree back to text; the round-trip identity invariant governs the result." |
| TOML-STATE-004 | Transitions | "`Value::try_into`, `Table::try_into`, and the `Deserialize` implementation of `Value` move between the typed value state and arbitrary user types." |

## Error Semantics

| Clause ID | Section | Clause (verbatim) |
|---|---|---|
| TOML-ERR-001 | Error Semantics | "Text is not a valid TOML document when parsed with `toml::from_str`, `toml::from_slice`, or `toml::Table::from_str` — must raise `toml::de::Error` carrying a message and the byte span of the offending region" |
| TOML-ERR-002 | Error Semantics | "Text is not a valid TOML document when parsed with `DocumentMut::from_str` or `parse` — must raise `TomlError` carrying a message and the byte span of the offending region" |
| TOML-ERR-003 | Error Semantics | "Text is not a valid TOML value when parsed with `toml_edit::Value::from_str` or `toml::Value::from_str` — must raise the corresponding parse error carrying a message and span" |
| TOML-ERR-004 | Error Semantics | "A document defines the same key twice, or defines a key both as a value and as a table or array of tables — must raise a parse error for the duplicate key" |
| TOML-ERR-005 | Error Semantics | "The document does not match the target type: missing required field, type mismatch, or integer out of range — must raise `toml::de::Error` (or `toml_edit::de::Error`)" |
| TOML-ERR-006 | Error Semantics | "The document contains a bare value rather than a table at the top level — must raise `toml::de::Error`" |
| TOML-ERR-007 | Error Semantics | "A datetime field receives a quoted string — must raise `toml::de::Error`" |
| TOML-ERR-008 | Error Semantics | "Datetime text does not conform to the four datetime forms in `Datetime::from_str` — must raise `DatetimeParseError`" |
| TOML-ERR-009 | Error Semantics | "`toml::ser::to_string` receives a root that is not table-shaped, or a map with non-string keys — must raise `toml::ser::Error`" |
| TOML-ERR-010 | Error Semantics | "`toml_edit::ser::to_string` or `to_document` receives a root that is not table-shaped — must raise `toml_edit::ser::Error`" |
| TOML-ERR-011 | Error Semantics | "A `Spanned` field is deserialized through `toml_edit::de` from a value without span information — must raise `toml_edit::de::Error`" |
| TOML-ERR-012 | Error Semantics | "Indexing a document, table, or value at an absent key, or through a container of the wrong kind — must panic" |
| TOML-ERR-013 | Error Semantics | "`insert`, `replace`, or `remove` on an array at an index beyond its length — must panic" |
| TOML-ERR-014 | Error Semantics | "Lookup operations (`get`, `contains_key`, `remove`) on an absent key — must return nothing rather than raising" |

## Cross-View Invariants

| Clause ID | Section | Clause (verbatim) |
|---|---|---|
| TOML-INV-001 | Cross-View Invariants | "for any document parsed with `DocumentMut::from_str`, rendering the document must produce text identical to the input, with the two stated exceptions of trailing-newline addition and dotted-key ordering." |
| TOML-INV-002 | Cross-View Invariants | "every item inserted through indexing, `Table::insert`, `entry`, `Array::push`, or `InlineTable::insert` must be returned by the corresponding lookup and iteration methods and must appear in the serialized text; every item removed must be absent from all three." |
| TOML-INV-003 | Cross-View Invariants | "for any type implementing `Serialize`, `Deserialize`, and `PartialEq` whose values are representable in TOML, serializing a value and deserializing the result must produce a value equal to the original; values whose serialization must raise an error (non-table roots, non-string map keys) must raise the same error class on every attempt." |
| TOML-INV-004 | Cross-View Invariants | "parsing the same text with `toml::from_str` into a `Value` and with `toml_edit::DocumentMut::from_str` must expose the same logical key/value data, and re-serializing the `Value` must yield text that parses to the same logical data." |
| TOML-INV-005 | Cross-View Invariants | "when a `Spanned` field deserializes from text, the reported range must be a byte range of that text whose content is the raw TOML of the value, and any error raised during deserialization of that value must carry a span within the text." |
| TOML-INV-006 | Cross-View Invariants | "a datetime literal parsed by `Datetime::from_str` must equal the `Datetime` obtained by deserializing a document that contains the same literal into a datetime field, and rendering that document must reproduce the literal." |
| TOML-INV-007 | Cross-View Invariants | "after `insert` replaces an existing key, exactly one entry for the key must remain, the value returned by the lookup methods must be the new item, the previous item must be the one returned by `insert`, and the rendered text must contain the new value." |
