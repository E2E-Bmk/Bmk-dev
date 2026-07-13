# TOMLKit Reconstruction Spec v5

Status: candidate-visible public packet
Task id: tomlkit-fullrepro-001
Delta from v4: keeps the documented public member names exposed by `tomlkit.items` and `tomlkit.exceptions`, but removes `AbstractTable` because the public API reference excludes it from the documented `tomlkit.items` members.
Source boundary: derived from public TOMLKit README.md, docs/index.rst, docs/quickstart.rst, docs/api.rst, and public top-level package API names. Use this public behavior packet as the implementation contract; repository internals and non-public benchmark artifacts are outside the contract.

---

## Product Overview

Build an installable Python package named `tomlkit`. TOMLKit is a TOML library whose defining behavior is not just decoding TOML into plain dictionaries: it preserves comments, indentation, whitespace, table order, array formatting, and other user-visible style while allowing callers to inspect and edit the TOML document through a Python mapping-like API.

The central shared fact source is a mutable TOML document tree. That tree has several public projections:

- dictionary-style semantic access to values, tables, arrays, and nested keys;
- item objects that retain TOML formatting trivia and can be serialized back to TOML;
- helper APIs for constructing documents, tables, arrays, comments, whitespace, keys, and scalar values;
- parser and dumper functions that convert between strings/files and the document tree;
- `TOMLFile` for reading and writing documents on disk.

The library should support TOML 1.0 style data types and enough style-preserving behavior for practical editing of existing TOML files such as `pyproject.toml`.

## Scope

This task covers these public feature areas:

- importable public API from `tomlkit` and documented public modules;
- parsing TOML strings/bytes and file objects into `TOMLDocument`;
- dumping plain mappings and TOMLKit document/item objects to strings or file objects;
- creating new TOML documents from helper functions;
- preserving comments, whitespace, newlines, table order, array formatting, and inline-table formatting when parsing and editing;
- mapping/list/scalar behavior of TOML items where documented by the public API;
- `TOMLFile` read/write behavior;
- documented parse and conversion errors.

## Non-Goals

- No CLI is required.
- No network access or external services.
- No implementation-specific parser architecture is required.
- No byte-for-byte compatibility for undocumented malformed-input diagnostics.
- No requirement to expose private modules, private attributes, or private helper functions.
- No requirement to cover compatibility scenarios that are not reasonably inferable from public TOMLKit documentation and TOML 1.0 behavior.
- No requirement to preserve invisible implementation objects beyond user-visible comments, whitespace, ordering, and serialized TOML output.

## Installable Surface

The project must be installable as a Python distribution that provides:

```python
import tomlkit
```

Expose `tomlkit.__version__` as a string.

The public top-level imports must include:

```python
from tomlkit import TOMLDocument
from tomlkit import parse, loads, load, dumps, dump
from tomlkit import document, item, value, key, key_value
from tomlkit import integer, float_, boolean, string, date, time, datetime
from tomlkit import array, table, inline_table, aot
from tomlkit import comment, ws, nl
from tomlkit import register_encoder, unregister_encoder
```

Public documented modules/classes include:

```python
from tomlkit.toml_document import TOMLDocument
from tomlkit.toml_file import TOMLFile
from tomlkit import items
from tomlkit import exceptions
```

The documented `tomlkit.items` module exposes these public item classes and helper types:

```python
from tomlkit.items import (
    StringType, BoolType, Trivia, KeyType, Key, SingleKey, DottedKey,
    Item, Whitespace, Comment, Integer, Float, Bool, DateTime, Date,
    Time, Array, Table, InlineTable, String, AoT, Null,
)
```

The documented `tomlkit.exceptions` module exposes these public error classes:

```python
from tomlkit.exceptions import (
    TOMLKitError, ParseError, MixedArrayTypesError, InvalidNumberError,
    InvalidDateTimeError, InvalidDateError, InvalidTimeError,
    InvalidNumberOrDateError, InvalidUnicodeValueError, UnexpectedCharError,
    EmptyKeyError, EmptyTableNameError, InvalidCharInStringError,
    UnexpectedEofError, InternalParserError, NonExistentKey,
    KeyAlreadyPresent, InvalidControlChar, InvalidStringError, ConvertError,
)
```

## Public API

### Parsing and Loading

```python
parse(string: str | bytes) -> TOMLDocument
loads(string: str | bytes) -> TOMLDocument
load(fp) -> TOMLDocument
```

Behavior:

- `parse()` accepts TOML text as `str` or bytes and returns a `TOMLDocument`.
- `loads()` is an alias for parsing from a string/bytes object.
- `load()` reads text or bytes from a file-like object and parses it.
- Parsed documents behave like mutable mappings for semantic access: nested tables and values can be read through normal key access.
- Parsing a document and immediately dumping it should preserve the original user-visible TOML text for comments, whitespace, indentation, ordering, table headers, and scalar formatting that the library supports.
- Invalid TOML should raise a TOMLKit parse error rather than silently producing an incorrect document.

### Dumping and Writing

```python
dumps(data, **options) -> str
dump(data, fp, **options) -> None
```

Behavior:

- `dumps()` serializes a `TOMLDocument`, TOMLKit item/table/container, or plain Python mapping to TOML text.
- If `data` is a parsed or constructed TOMLKit document and no key-sorting option is requested, serialization should use the document's preserved order and style.
- If the public API is given a documented key-sorting option, mapping keys should be serialized in deterministic sorted order where applicable.
- Plain Python mappings should be converted to TOML using standard TOML types and nested tables.
- `dump()` writes the serialized TOML text to a writable file-like object.

### Document Creation

```python
document() -> TOMLDocument
```

A new document starts empty, supports mapping-style assignment, and can be built by adding comments, newlines, scalar values, tables, arrays, inline tables, and arrays of tables. Serializing the document should produce valid TOML text for the current document state.

### Item Creation Helpers

```python
integer(raw)
float_(raw)
boolean(raw)
string(raw, **options)
date(raw)
time(raw)
datetime(raw)
array(raw=None)
table(**options)
inline_table()
aot()
key(k)
value(raw)
key_value(src)
ws(src)
nl()
comment(string)
item(value)
```

Behavior:

- Scalar helpers create TOMLKit item objects that represent the corresponding TOML scalar value.
- `string()` creates TOML string items and supports the documented string styles and escaping behavior.
- `date()`, `time()`, and `datetime()` parse TOML/RFC3339-compatible date/time strings and reject incompatible values.
- `array()` creates a mutable array item. It should behave like a list for ordinary append/extend/insert/delete operations and serialize as TOML array syntax.
- `table()` creates a mutable table item. It should behave like a mapping for adding/removing keys and serialize as TOML table syntax when attached to a document.
- `inline_table()` creates a mapping item serialized with inline table syntax such as `{x = 1, y = 2}`.
- `aot()` creates an array-of-tables item.
- `key()` creates TOML keys. Passing a sequence creates a dotted key.
- `value()` parses a single TOML value string into the corresponding item.
- `key_value()` parses one TOML key/value assignment into a key object and item.
- `ws()`, `nl()`, and `comment()` create whitespace, newline, and comment items that affect serialized output.
- `item()` converts Python values into appropriate TOMLKit item objects; dictionaries become tables or inline tables as appropriate, lists become arrays, and arrays of dictionaries may become arrays of tables where required by TOML structure.

### Custom Encoders

```python
register_encoder(encoder)
unregister_encoder(encoder)
```

Behavior:

- Registered encoders let callers teach TOMLKit how to convert otherwise unsupported Python values into TOMLKit items.
- An encoder should return a TOMLKit item or raise a conversion error.
- Unregistering an encoder removes it from the custom conversion registry.

### TOMLDocument

`TOMLDocument` is the public document object returned by `parse()` and `document()`.

Required behavior:

- It behaves like a mutable mapping for top-level TOML keys.
- Key access, assignment, deletion, `pop()`, `setdefault()`, `update()`, iteration, membership, and copying should follow normal mapping expectations while preserving TOML style.
- Nested tables behave like mappings as well.
- `unwrap()` returns plain Python dictionaries/lists/scalars for semantic data.
- `as_string()` returns TOML text for the document.
- Adding a key to an existing table preserves existing comments and table layout where possible.
- Adding a new table after an existing table emits the appropriate table header and spacing.
- Removing or replacing keys should not leave spurious separators, duplicated headers, or broken TOML syntax.
- Dotted keys and out-of-order tables should maintain consistent semantic access and deterministic serialized output.

### TOMLFile

```python
TOMLFile(path)
TOMLFile.read() -> TOMLDocument
TOMLFile.write(data) -> None
```

Behavior:

- `read()` reads the file content from disk and returns a parsed `TOMLDocument`.
- `write()` serializes and writes a TOML document or mapping to the same file path.
- A read/modify/write cycle should preserve user-visible formatting of the document where feasible.

### Public Items

The public `tomlkit.items` module exposes item classes for TOML values and containers, including scalar items, arrays, tables, inline tables, arrays of tables, comments, whitespace, and keys.

Required behavior:

- Item objects expose `as_string()` for TOML serialization and `unwrap()` for plain Python values where meaningful.
- Scalar items should expose the corresponding Python semantic value through public value/unwrap behavior.
- Arrays behave like mutable lists and serialize each contained item in order.
- Tables and inline tables behave like mutable mappings.
- Comments and whitespace affect `as_string()` but do not create semantic TOML key/value pairs.
- Item comments can be attached or updated through public item methods where documented by examples.

### Public Exceptions

The public `tomlkit.exceptions` module exposes TOMLKit error classes for parse and conversion failures.

Behavior:

- Parse errors should be TOMLKit exceptions and include useful location information when available.
- Duplicate keys or tables should raise a key/table conflict error rather than overwriting silently.
- Invalid scalar strings passed to value helpers should raise TOMLKit invalid-value errors.
- Conversion failures should raise a TOMLKit conversion error unless a registered encoder handles the value.

## Behavioral Sections

### Style Preservation

Style preservation is the core product contract.

- Parsing and dumping without mutation should preserve the original TOML text for supported TOML syntax, including comments, blank lines, indentation, table ordering, inline comments, inline table separators, array formatting, and user-visible newlines/whitespace where feasible.
- Mutating a document should preserve unrelated surrounding style. For example, adding a key to a table should not remove existing comments in that table; deleting one inline-table key should not leave a trailing comma/separator; editing an array should preserve existing multiline formatting where feasible.
- TOML semantics and style must remain linked: when a semantic value changes through the mapping API, serialized TOML should show the changed value in the correct table location without corrupting unrelated tables.

### TOML Data Model

Support the standard TOML data types used by public examples and normal TOML 1.0 files:

- strings, including escaped strings and literal/multiline variants;
- integers;
- floats;
- booleans;
- local dates, local times, local datetimes, and offset datetimes;
- arrays;
- tables;
- inline tables;
- arrays of tables;
- dotted keys.

### Document Mutation

Public mutation behavior should include:

- assigning scalar values into documents and tables;
- adding/removing tables;
- adding/removing keys from arrays, inline tables, and regular tables;
- replacing a scalar with a table or a table with a scalar while producing valid TOML;
- moving, deleting, or overwriting nested/out-of-order table keys without breaking semantic access;
- preserving correct spacing around table headers after insertion/deletion.

### Sorting and Plain Mapping Conversion

When dumping plain Python mappings:

- nested dictionaries serialize as TOML tables;
- arrays/lists serialize as TOML arrays;
- tuples may serialize as arrays;
- unsupported objects may be handled by registered encoders;
- public key-sorting options should sort mapping keys deterministically.

## Error Semantics

- Invalid TOML text raises a TOMLKit parse exception.
- Invalid date/time/number/string literals raise TOMLKit invalid-value exceptions when identifiable.
- Duplicate keys or tables raise a conflict exception.
- Accessing a non-existent TOML key through item/table APIs should raise a missing-key exception or normal mapping-style `KeyError` where appropriate.
- Unsupported conversion to TOML raises a conversion error unless a registered encoder handles it.

## Cross-View Invariants

1. Parsing and serialization must describe the same document tree: semantic values and supported user-visible style survive a read-back/write-back cycle.
2. Mapping access and serialized TOML must agree after edits: changes made through public document/table APIs appear in the correct serialized TOML location.
3. TOMLKit item wrappers and plain Python values must agree on semantic value while item wrappers retain TOML formatting for serialization.
4. Comments and whitespace are style facts in the document tree: mutations to semantic values must not erase unrelated comments or layout.
5. File and string APIs must agree on document content: a document read from disk, modified, and written should reflect the same semantic values and user-visible style as string serialization of that document.
6. Dotted keys, regular tables, inline tables, and arrays of tables must agree across semantic access and serialized TOML syntax.
7. Custom encoders must integrate with item conversion and serialization without corrupting ordering or style of surrounding document data.

## Representative Workflows

### Parse, Edit, Preserve

```python
from tomlkit import dumps, parse

content = '[tool]\nname = "demo"  # package name\n'

doc = parse(content)
doc["tool"]["version"] = "1.0"
output = dumps(doc)

assert doc["tool"]["name"] == "demo"
assert 'name = "demo"  # package name' in output
assert 'version = "1.0"' in output
```

### Build a New Document

```python
from tomlkit import comment, document, dumps, nl, table

doc = document()
doc.add(comment("Generated file"))
doc.add(nl())
doc.add("title", "Example")
owner = table()
owner.add("name", "Tom")
doc.add("owner", owner)
text = dumps(doc)
```

### File Round Trip

```python
from tomlkit.toml_file import TOMLFile

file = TOMLFile("pyproject.toml")
doc = file.read()
doc.setdefault("tool", {})
file.write(doc)
```

## Evaluation Notes

A correct implementation should satisfy public TOMLKit behavior rather than any particular parser architecture. The important public dimensions are:

- importability of documented public functions, classes, modules, and exceptions;
- parsing and loading TOML into a mutable document;
- dumping documents, items, and plain mappings back to valid TOML;
- document/table/array mutation through public mapping and list-like APIs;
- preservation of comments, whitespace, ordering, inline tables, arrays, and user-visible newlines as part of the documented style-preserving contract;
- `TOMLFile` read/write behavior;
- public errors for invalid TOML or conversion failures.

Implementation internals such as parser state machines, hidden trivia object layout, and exact wording of undocumented error messages are outside the public contract.
