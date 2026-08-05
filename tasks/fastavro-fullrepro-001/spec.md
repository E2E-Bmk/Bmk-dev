# fastavro Specification

## Product Overview

fastavro is a Python Avro serialization library. It reads and writes Avro object-container files, schemaless binary values, Avro JSON encodings, and schema descriptions while exposing matching Python, command-line, validation, repository, block, logical-type, canonical-form, and fingerprint views.

The main package is imported as `fastavro`. The expected workflow is to define Avro schemas as Python dictionaries or `.avsc` JSON files, write Python records into Avro encodings, and read those encodings back through the selected projection.

## Scope

This specification covers:

- Top-level public functions and attributes: `reader`, `writer`, `block_reader`, `schemaless_reader`, `schemaless_writer`, `json_reader`, `json_writer`, `is_avro`, `validate`, `parse_schema`, and `__version__`.
- Schema APIs in `fastavro.schema`: `fullname`, `parse_schema`, `expand_schema`, `load_schema`, `load_schema_ordered`, `to_parsing_canonical_form`, `fingerprint`, `UnknownType`, and `SchemaParseException`.
- Validation APIs in `fastavro.validation`, including `validate_many`.
- Repository APIs in `fastavro.repository`, including `FlatDictRepository` and `SchemaRepositoryError`.
- Public logical-type registries `LOGICAL_READERS` from `fastavro.read` and `LOGICAL_WRITERS` from `fastavro.write`.
- The `python -m fastavro` command-line entry point and its record, schema, metadata, codec, version, stdin, and pretty-print modes.

## Non-Goals

- This specification does not require Cython extension parity or private extension modules.
- This specification does not require optional native codec packages beyond codecs available in the local environment.
- This specification does not require exact binary block offsets, exact exception message text, exact `repr()` output, or log wording.
- This specification does not require network access, remote schema registries, or live services.

## Representative Workflows

### Object-Container Round Trip

```python
import io
import fastavro

schema = {
    "type": "record",
    "name": "Profile",
    "fields": [{"name": "id", "type": "long"}, {"name": "name", "type": "string"}],
}
records = [{"id": 31, "name": "Ada"}]

buffer = io.BytesIO()
fastavro.writer(buffer, schema, records, codec="null", metadata={"owner": "docs"})
buffer.seek(0)
assert list(fastavro.reader(buffer)) == records
```

### Schema Repository Workflow

```python
from fastavro.repository import FlatDictRepository
from fastavro.schema import load_schema

repo = FlatDictRepository("/schemas")
schema = load_schema("Customer", repo=repo)
```

### JSON Projection Workflow

```python
import io
import fastavro

schema = {"type": "record", "name": "MaybeText", "fields": [{"name": "value", "type": ["null", "string"]}]}
out = io.StringIO()
fastavro.json_writer(out, schema, [{"value": "present"}])
assert list(fastavro.json_reader(io.StringIO(out.getvalue()), schema)) == [{"value": "present"}]
```

## Schema Names, Parsing, Repositories, And Fingerprints

WHEN `fullname` receives a named schema with `name` and `namespace`, THE system SHALL return the fully qualified Avro name. WHEN `name` is already qualified, THE system SHALL preserve that qualified name.

WHEN `parse_schema` receives a record schema, THE system SHALL preserve public schema facts such as `aliases`, field `default` values, field order, namespaces, named types, and logical type declarations. WHEN a shared named-schema mapping is supplied, THE system SHALL use it to resolve later named references.

IF `parse_schema` sees an unknown named type, duplicate enum symbols, or an invalid decimal logical type whose scale exceeds precision, THEN THE system SHALL raise `UnknownType` or `SchemaParseException` as appropriate.

WHEN `expand_schema` receives a parsed schema with named references, THE system SHALL return a schema view where named references can be inspected through the referenced schema body.

WHEN `to_parsing_canonical_form` is called, THE system SHALL return the Avro parsing canonical form with non-canonical fields such as docs, aliases, and defaults omitted and canonical keys ordered. WHEN `fingerprint` receives canonical form text and a supported algorithm such as `CRC-64-AVRO` or `md5`, THE system SHALL return the matching hexadecimal fingerprint string. IF the algorithm is unsupported, THEN THE system SHALL raise `ValueError`.

WHEN `FlatDictRepository` is constructed from a directory, THE system SHALL load `<name>.avsc` JSON schema files by public name. IF a requested schema file is absent or unreadable, THEN THE system SHALL raise `SchemaRepositoryError`. WHEN `load_schema` is supplied a repository, THE system SHALL resolve named references through that repository. WHEN `load_schema_ordered` receives ordered schema file paths, THE system SHALL resolve references across those files.

## Validation And Record Selection

WHEN `validate` receives a record that matches the declared Avro schema, THE system SHALL return `True`. IF a record field has the wrong type and `raise_errors` is false, THEN THE system SHALL return `False`; otherwise invalid records SHALL raise an exception.

WHEN a record contains fields not declared in the schema, THE system SHALL still validate declared fields and SHALL NOT reject the record only because of the extra fields. WHEN schema fields have defaults and the record omits those fields, THE system SHALL validate the record using the declared defaults.

WHEN `validate_many` receives records that all match a schema, THE system SHALL return `True`. IF any record is invalid and `raise_errors` is false, THEN THE system SHALL return `False`.

WHEN a union contains multiple named record branches, THE system SHALL accept tuple notation whose first item names the selected branch and second item is the record value. WHEN `disable_tuple_notation` is enabled, THE system SHALL reject tuple notation. WHEN writing record unions, THE system SHALL also accept a public `-type` record hint to select the named record branch.

WHEN reading named union branches with `return_record_name` or `return_named_type`, THE system SHALL include the selected record name with the returned value where the option applies.

## Binary, Object-Container, Blocks, And Schema Resolution

WHEN `schemaless_writer` writes primitive values, THE system SHALL encode them using Avro binary encoding. WHEN `schemaless_reader` reads those bytes with the matching schema, THE system SHALL return the original Python value. WHEN a reader schema adds a field with a default, THE system SHALL include that default in the returned record.

IF `schemaless_writer` or `writer` is called with `strict=True` and required non-defaulted fields are missing, THEN THE system SHALL raise an exception. WHEN `writer` is called with `strict_allow_default=True`, THE system SHALL allow missing fields that have schema defaults and SHALL serialize values that `reader` returns with those defaults applied.

WHEN `writer` writes an object-container file to a binary stream, THE system SHALL accept records from any iterable, including generators. WHEN `reader` consumes that container, THE system SHALL return every record in order and expose public attributes including `metadata`, `codec`, and `writer_schema` where present.

WHEN `writer` is called with `validator=True`, THE system SHALL validate records before writing and SHALL raise an exception for invalid data. WHEN `is_avro` receives a string path or file-like object, THE system SHALL return whether the input begins with an Avro object-container header.

WHEN a reader schema drops writer fields, adds defaulted fields, uses field aliases, uses record aliases, or supplies an enum default for an unknown writer symbol, THE system SHALL resolve records according to Avro schema-resolution rules.

WHEN `block_reader` consumes an object-container file, THE system SHALL iterate public block objects. Each block SHALL expose `num_records`, `codec`, and record iteration. The block reader object SHALL expose container `metadata`.

## JSON Encoding And Logical Types

WHEN `json_writer` writes records, THE system SHALL write Avro JSON encoding to the supplied text stream. By default, non-null union branch values SHALL be wrapped by branch name. WHEN `write_union_type=False`, THE system SHALL omit that wrapper.

WHEN `json_reader` reads Avro JSON encoding, THE system SHALL return Python records for the supplied writer schema and SHALL apply a compatible reader schema, including defaulted fields. IF unwrapped union JSON is read with a schema that requires wrapped union values, THEN THE system SHALL raise an exception.

WHEN decimal, UUID, date, datetime, and other supported logical types are written and read through binary or JSON projections, THE system SHALL convert between Avro representation and the documented Python logical values.

`LOGICAL_WRITERS` and `LOGICAL_READERS` SHALL be mutable public mappings. WHEN matching custom logical-type handlers are registered in those mappings, THE system SHALL call the writer handler before serialization and the reader handler after deserialization.

## Command Line Behavior

The package SHALL be executable as `python -m fastavro`.

WHEN the command receives one or more Avro object-container files with no mode flag, THE system SHALL print one JSON record per line. WHEN input is provided through standard input and no file path is supplied, THE system SHALL read the object-container bytes from standard input.

WHEN `--pretty` is supplied, THE system SHALL pretty-print JSON records. WHEN `--schema` is supplied, THE system SHALL print the container schema as JSON. WHEN `--metadata` is supplied, THE system SHALL print container metadata as JSON, including user metadata and `avro.codec`. WHEN `--codecs` is supplied, THE system SHALL list supported codec names including `null`, `deflate`, `bzip2`, and `xz` when those built-ins are available. WHEN `--version` is supplied, THE system SHALL print the importable package `__version__`.

## Product State Model

The product state is the combination of Avro schema definitions, Python records, Avro binary object-container bytes, schemaless binary bytes, Avro JSON text, repository files, logical-type registries, and command-line projections.

The same facts must remain coherent across projections:

- Schemas used by `writer`, `reader`, `json_writer`, `json_reader`, `validate`, and schema utilities must agree on names, namespaces, aliases, defaults, enum symbols, union branches, and logical types.
- Records written by `writer` must be readable by `reader` with the same data values after schema resolution.
- Records written by `json_writer` must be readable by `json_reader` when the selected union representation matches.
- Public block metadata and reader metadata must describe the same object-container file.
- Command-line record, schema, metadata, codec, stdin, and version projections must agree with the public Python APIs.

## Error Semantics

Schema parse failures SHALL use `UnknownType` or `SchemaParseException` for the public error classes covered here. Repository loading failures SHALL use `SchemaRepositoryError`. Unsupported fingerprint algorithms SHALL raise `ValueError`.

Validation, writer, reader, JSON reader, and schemaless operations SHALL raise exceptions for invalid data, malformed schema/data combinations, missing required strict fields, invalid union hints, and incompatible JSON union representation. Tests only rely on exception type families or successful failure, not exact message text.

## Cross-View Invariants

- A schema read back from an object-container file must have the same parsing canonical form and fingerprint as the schema supplied to `writer`.
- A record set written by `writer` must be returned in order by `reader`, and CLI record output must match the reader projection.
- CLI schema output must match the Python reader schema projection for the same file.
- CLI metadata output must agree with reader-visible metadata for user metadata and codec.
- `block_reader` record iteration must compose to the same record sequence as `reader` for the same file.
- Schema resolution behavior must be consistent across schemaless reads, object-container reads, JSON reads, aliases, defaults, and enum defaults.
- Custom logical-type handlers registered in the public registries must affect both write and read projections for the same logical type.

## Installable Surface

Public imports:

```python
import fastavro
from fastavro import reader, writer, block_reader, schemaless_reader, schemaless_writer
from fastavro import json_reader, json_writer, is_avro, validate, parse_schema
from fastavro.schema import fullname, parse_schema, expand_schema, load_schema, load_schema_ordered
from fastavro.schema import to_parsing_canonical_form, fingerprint, UnknownType, SchemaParseException
from fastavro.validation import ValidationError, validate_many
from fastavro.repository import FlatDictRepository, SchemaRepositoryError
from fastavro.read import LOGICAL_READERS
from fastavro.write import LOGICAL_WRITERS
```

API catalog:

| Name | Kind | Role |
|---|---|---|
| `fastavro.__version__` | attribute | Importable package version string. |
| `reader` | function/class | Reads Avro object-container records and exposes schema, metadata, and codec projections. |
| `writer` | function | Writes Avro object-container files from schemas and record iterables. |
| `block_reader` | function/class | Iterates object-container blocks and exposes block metadata. |
| `schemaless_reader` | function | Reads one Avro binary value without an object-container header. |
| `schemaless_writer` | function | Writes one Avro binary value without an object-container header. |
| `json_reader` | function | Reads Avro JSON encoding into Python records. |
| `json_writer` | function | Writes Python records as Avro JSON encoding. |
| `is_avro` | function | Detects Avro object-container inputs from paths or file-like objects. |
| `validate` | function | Validates one Python datum against an Avro schema. |
| `validate_many` | function | Validates an iterable of Python records against an Avro schema. |
| `ValidationError` | exception | Reports a datum that does not satisfy its supplied Avro schema. |
| `parse_schema` | function | Parses Avro schemas and resolves named types. |
| `fullname` | function | Computes a named schema's full Avro name. |
| `expand_schema` | function | Expands named references for inspection. |
| `load_schema` | function | Loads a schema by name through a repository. |
| `load_schema_ordered` | function | Loads ordered schema files with cross-file references. |
| `to_parsing_canonical_form` | function | Produces Avro parsing canonical form. |
| `fingerprint` | function | Computes fingerprints from canonical form text. |
| `UnknownType` | exception | Public schema error for unresolved named types. |
| `SchemaParseException` | exception | Public schema parse error. |
| `FlatDictRepository` | class | Loads schemas from a flat directory of `.avsc` files. |
| `SchemaRepositoryError` | exception | Public repository loading error. |
| `LOGICAL_READERS` | mapping | Registry for logical-type reader hooks. |
| `LOGICAL_WRITERS` | mapping | Registry for logical-type writer hooks. |
| `metadata` | attribute | Reader and block-reader metadata mapping. |
| `codec` | attribute | Reader and block codec name. |
| `schema` | attribute | Reader schema projection. |
| `writer_schema` | attribute | Reader writer-schema projection. |
| `num_records` | attribute | Number of records in a block. |

Command-line entry points:

```text
python -m fastavro [--schema] [--metadata] [--codecs] [--version] [--pretty] [file ...]
```

## Invocation Protocol

Callers use normal Python imports or run `python -m fastavro` in a local process. File input is local filesystem or standard input only. Tests may use temporary files and in-memory `io.BytesIO` or `io.StringIO` streams.

## Environment

The working environment runs Python 3.11 on Linux without network access. The following third-party package is preinstalled and importable: `pytest`. The target package is not pre-installed. The assessment environment provides the same interpreter and package set.

The project must declare its packaging metadata in a standard `pyproject.toml` or `setup.py` at the project root so the package can be installed with pip.

## Evaluation Notes

The expected implementation should follow documented public Avro behavior and the public fastavro API names listed above. Exact exception text, exact pretty-print whitespace, exact binary block offsets, private modules, and optional native extensions are not part of this specification.
