# TOMLKit Reconstruction Spec v1

Status: candidate-visible public packet
Task id: evaluation set
Delta from v0: initial Type 3 behavior specification for a style-preserving TOML library.
Source boundary: derived from public TOMLKit README.md, docs/index.rst, docs/quickstart.rst, docs/api.rst, and public package API names exported from tomlkit. Do not inspect source code, original tests, scoring files, prior attempts, or evaluation set notes.

---

## Product Overview

Build an installable Python package named `tomlkit`. TOMLKit is a TOML library whose defining behavior is not just decoding TOML into plain dictionaries: it preserves comments, indentation, whitespace, line endings where feasible, table order, array formatting, and other user-visible style while allowing callers to inspect and edit the TOML document through a Python mapping-like API.

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
- documented parse and conversion exceptions.

## Non-Goals

- No CLI is required.
- No network access or external services.
- No implementation-specific parser architecture is required.
- No byte-for-byte compatibility for undocumented malformed-input diagnostics.
- No requirement to expose private modules, private attributes, or private helper functions.
- No requirement to pass external TOML compliance fixtures that are not inferable from public TOMLKit docs and TOML 1.0 behavior.
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
- Parsed documents behave like mutable mappings for semantic access: `doc["table"]["key"]` returns the TOML value.
- Parsing a document and immediately dumping it should preserve the original user-visible TOML text for comments, whitespace, indentation, ordering, table headers, and scalar formatting that the library supports.
- Invalid TOML should raise a documented TOMLKit exception rather than silently producing an incorrect document.

### Dumping and Writing

```python
dumps(data, sort_keys: bool = False) -> str
dump(data, fp, *, sort_keys: bool = False) -> None
```

Behavior:

- `dumps()` serializes a `TOMLDocument`, TOMLKit item/table/container, or plain Python mapping to TOML text.
- If `data` is a parsed or constructed TOMLKit document and `sort_keys=False`, serialization should use the document's preserved order and style.
- If `sort_keys=True`, mapping keys should be serialized in deterministic sorted order where applicable.
- Plain Python mappings should be converted to TOML using standard TOML types and nested tables.
- `dump()` writes the serialized TOML text to a writable file-like object.

### Document Creation

```python
document() -> TOMLDocument
```

A new document starts empty, supports mapping-style assignment, and can be built by adding comments, newlines, scalar values, tables, arrays, inline tables, and arrays of tables. `dumps(document())` should produce valid TOML text for the current document state.

### Item Creation Helpers

```python
integer(raw: str | int)
float_(raw: str | float)
boolean(raw: str | bool)
string(raw: str, *, literal=False, multiline=False, escape=True)
date(raw: str)
time(raw: str)
datetime(raw: str)
array(raw: str = "[]")
table(is_super_table: bool | None = None)
inline_table()
aot()
key(k: str | list[str] | tuple[str, ...])
value(raw: str)
key_value(src: str)
ws(src: str)
nl()
comment(string: str)
item(value, _parent=None, _sort_keys=False)
```

Behavior:

- Scalar helpers create TOMLKit item objects whose Python value behaves like the corresponding Python scalar when unwrapped or compared naturally.
- `string()` supports basic/literal and single-line/multiline TOML string forms and escapes invalid TOML string characters when requested.
- `date()`, `time()`, and `datetime()` parse TOML/RFC3339-compatible date/time strings and reject incompatible values.
- `array()` creates a mutable array item. It should behave like a list for append/extend/insert/delete and serialize as TOML array syntax.
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

- A registered encoder is called when a value cannot otherwise be converted to a TOML item.
- An encoder should return a TOMLKit item or raise `ConvertError`.
- Unregistering an encoder removes it without disrupting other encoders.

### TOMLDocument

`TOMLDocument` is the public document object returned by `parse()` and `document()`.

Required behavior:

- It behaves like a mutable mapping for top-level TOML keys.
- `doc[key]`, assignment, deletion, `pop()`, `setdefault()`, `update()`, iteration, membership, and copying should follow normal mapping expectations while preserving TOML style.
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
- Existing line-ending style should be preserved when a file is read, modified, and written where feasible. If no existing style is known, use the platform default line separator.

### Public Items

The public `tomlkit.items` module exposes item classes for TOML values and containers, including scalar items, arrays, tables, inline tables, arrays of tables, comments, whitespace, and keys.

Required behavior:

- Item objects expose `as_string()` for TOML serialization and `unwrap()` for plain Python values where meaningful.
- Scalar items should compare and operate like their Python values for ordinary equality and simple arithmetic/string/date/time behavior.
- Arrays behave like mutable lists and serialize each contained item in order.
- Tables and inline tables behave like mutable mappings.
- Comments and whitespace affect `as_string()` but do not create semantic TOML key/value pairs.
- Item comments can be attached or updated through public item methods where documented by examples.
- TOMLKit item objects should be copyable/pickleable where this follows normal Python container expectations.

### Public Exceptions

The public `tomlkit.exceptions` module exposes `TOMLKitError`, `ParseError`, `MixedArrayTypesError`, `InvalidNumberError`, `InvalidDateTimeError`, `InvalidDateError`, `InvalidTimeError`, `InvalidNumberOrDateError`, `InvalidUnicodeValueError`, `UnexpectedCharError`, `EmptyKeyError`, `EmptyTableNameError`, `InvalidCharInStringError`, `UnexpectedEofError`, `NonExistentKey`, `KeyAlreadyPresent`, `InvalidControlChar`, `InvalidStringError`, and `ConvertError`.

Behavior:

- Parse errors should be TOMLKit exceptions and include useful line/column information when applicable.
- Duplicate keys or tables should raise a key/table conflict exception rather than overwriting silently.
- Invalid scalar strings passed to value helpers should raise documented parse/invalid-value exceptions.
- Mixed-type arrays should raise the documented mixed-array exception where TOML rules require homogeneous arrays.
- Conversion failures should raise `ConvertError`.

## Behavioral Sections

### Style Preservation

Style preservation is the core product contract.

- Parsing and dumping without mutation should preserve the original TOML text for supported TOML syntax, including comments, blank lines, indentation, table ordering, inline comments, inline table separators, array formatting, and newline style where feasible.
- Mutating a document should preserve unrelated surrounding style. For example, adding a key to a table should not remove existing comments in that table; deleting one inline-table key should not leave a trailing comma/separator; editing an array should preserve existing multiline formatting where feasible.
- TOML semantics and style must remain linked: if `doc["table"]["name"]` changes, `dumps(doc)` should serialize the changed value in the correct table location without corrupting unrelated tables.

### TOML Data Model

Support the standard TOML data types used by public examples and normal TOML 1.0 files:

- strings, including escaped strings and literal/multiline variants;
- integers, including TOML integer forms that Python can represent;
- floats, including infinities and NaN where TOML/Python behavior supports them;
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
- `sort_keys=True` should sort mapping keys deterministically.

## Error Semantics

- Invalid TOML text raises a TOMLKit parse exception.
- Invalid date/time/number/string literals raise the corresponding TOMLKit invalid-value exception when identifiable.
- Duplicate keys or tables raise a conflict exception.
- Accessing a non-existent TOML key through item/table APIs should raise the documented missing-key exception or normal mapping-style `KeyError` where appropriate.
- Unsupported conversion to TOML raises `ConvertError` unless a registered encoder handles it.

## Cross-View Invariants

1. Parsing and dumping are two views of the same document tree: `dumps(parse(text))` must preserve supported user-visible TOML style and semantic values.
2. Mapping access and serialized output must agree: after `doc["section"]["key"] = value`, both `doc` access and `dumps(doc)` show the new value in the correct table.
3. Item wrappers and plain values must agree: `item(value).unwrap()` and item comparison should reflect the original Python semantic value.
4. Comments/whitespace are style facts in the document tree: mutations to semantic values must not erase unrelated comments or layout.
5. File and string APIs must agree: reading through `TOMLFile.read()`, mutating, and writing should produce the same TOML content that `dumps()` would produce for that document, subject to preserved line endings.
6. Dotted keys, tables, inline tables, and arrays of tables must agree across semantic access and serialized TOML headers/inline syntax.
7. Custom encoders must integrate with dumps/item conversion without corrupting ordering or style of surrounding document data.

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

The scoreable behavior should focus on public, documented behavior:

- public imports and helper functions;
- parse/load/dump round trips;
- document/table/array mutation through public mapping/list APIs;
- preservation of comments, whitespace, ordering, inline tables, arrays, and line endings when that is the documented product behavior;
- TOMLFile read/write;
- public exceptions for invalid TOML or conversion failures.

Tests should be excluded if they require private parser internals, exact internal trivia object shapes, external fixture-suite bookkeeping, or undocumented malformed-input message text. Exact string checks are fair only when they assert the public style-preservation contract or documented serialization behavior.

