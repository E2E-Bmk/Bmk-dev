# mashumaro Behavioral Specification

## Product Overview

`mashumaro` converts typed Python dataclasses between Python objects, basic
dictionary and collection forms, serialized wire formats, and JSON Schema
descriptions. A dataclass and its annotations are the durable facts. Config,
field metadata, strategies, and dialects alter how those facts appear in each
public projection.

The package is a Python library. The covered behavior is deterministic and
does not require a service, database, subprocess, or remote resource.

## Scope

This specification covers:

- Dataclass conversion through `DataClassDictMixin.to_dict()` and
  `DataClassDictMixin.from_dict()`.
- Primitive, date, datetime, enum, tuple, named tuple, set, nested dataclass,
  and typed collection conversion.
- Public field metadata from `field_options()` and configuration through
  `BaseConfig`.
- `SerializationStrategy`, `pass_through`, `RoundedDecimal`, `Alias`, and
  `Discriminator` behavior.
- Basic and JSON typed codecs, plus JSON, YAML, TOML, and MessagePack dataclass
  mixins.
- Per-call and default `Dialect` behavior.
- JSON Schema generation through `build_json_schema()` and
  `JSONSchemaBuilder`.

## Installable Surface

The package import name is `mashumaro`. The following imports are part of the
covered public surface:

```python
from mashumaro import DataClassDictMixin, MissingField, field_options, pass_through
from mashumaro.codecs.basic import BasicDecoder, BasicEncoder
from mashumaro.codecs.json import JSONDecoder, JSONEncoder, json_decode, json_encode
from mashumaro.config import (
    ADD_DIALECT_SUPPORT,
    ADD_SERIALIZATION_CONTEXT,
    BaseConfig,
    TO_DICT_ADD_BY_ALIAS_FLAG,
    TO_DICT_ADD_OMIT_NONE_FLAG,
)
from mashumaro.dialect import Dialect
from mashumaro.exceptions import ExtraKeysError, InvalidFieldValue
from mashumaro.jsonschema import JSONSchemaBuilder, OPEN_API_3_1, build_json_schema
from mashumaro.jsonschema.annotations import MaxItems, Maximum, MinLength
from mashumaro.jsonschema.models import JSONSchema
from mashumaro.mixins.json import DataClassJSONMixin
from mashumaro.mixins.msgpack import DataClassMessagePackMixin
from mashumaro.mixins.toml import DataClassTOMLMixin
from mashumaro.mixins.yaml import DataClassYAMLMixin
from mashumaro.types import Alias, Discriminator, RoundedDecimal, SerializationStrategy
from typing_extensions import Annotated
```

No import from a private module or a generated implementation module is part
of the contract.

## Public API

`DataClassDictMixin` supplies class method `from_dict()` and instance method
`to_dict()` to a dataclass. Format mixins supply the corresponding pairs
`from_json()` and `to_json()`, `from_yaml()` and `to_yaml()`, `from_toml()` and
`to_toml()`, and `from_msgpack()` and `to_msgpack()`.

`BasicEncoder` and `JSONEncoder` are constructed for a target annotation and
expose `encode()`. `BasicDecoder` and `JSONDecoder` expose `decode()` for the
same purpose. JSON codec construction may specify `default_dialect`.
`json_encode()` and `json_decode()` are convenience functions for typed JSON
values.

`SerializationStrategy` subclasses expose `serialize()` and `deserialize()`.
Subclass declarations may enable `use_annotations` so strategy input and
output annotations participate in conversion, or `match_subclasses` so one
registration applies to subclasses. An exact-type strategy takes precedence
over a matching base-type strategy.

`Dialect` subclasses describe conversion policy and `Dialect.merge()` creates
a combined dialect in which later policy values override earlier values.

`build_json_schema()` returns a public schema model with `to_dict()`.
`JSONSchemaBuilder.build()` returns a schema for one annotation and
`JSONSchemaBuilder.get_definitions()` returns accumulated named definitions.
`JSONSchema` can be used as `Annotated` metadata to overlay content keywords.

## Dictionary Conversion

WHEN a dataclass inheriting `DataClassDictMixin` calls `to_dict()`, THE library
SHALL return a dictionary whose keys represent fields and whose values are in
basic Python form.

WHEN `from_dict()` receives a valid basic-form dictionary, THE library SHALL
construct an equivalent dataclass and recursively convert supported field
types.

The default basic projections are:

- `bool`, `int`, `float`, `str`, and `None` retain their ordinary values.
- `date` and `datetime` values use ISO 8601 strings and parse those strings on
  input.
- Enum values use their public `.value` and reconstruct the corresponding
  member.
- A typed tuple becomes a list. A set becomes a list whose element order is
  not contractual.
- A named tuple becomes a positional list by default.
- Nested dataclasses and collections are converted recursively.

IF a required field is absent THEN THE library SHALL raise `MissingField`.
The exception exposes `field_name` and `holder_class`.

IF a supplied field value cannot be converted to its annotation THEN THE
library SHALL raise `InvalidFieldValue` or the underlying public conversion
error. `InvalidFieldValue` exposes `field_name`.

## Field Metadata And Configuration

`field_options()` returns metadata containing each supplied standard option
and any additional metadata keys. The covered standard keys are `serialize`,
`deserialize`, and `alias`.

WHEN a field has `alias`, THE alias SHALL be accepted as its external input
key. A field-level alias takes precedence over an entry for the same field in
`BaseConfig.aliases`.

WHEN a field has a `serialize` callable, THE callable SHALL transform that
field on output. WHEN a field has a `deserialize` callable, THE callable SHALL
transform its input before the dataclass is constructed.

The following `BaseConfig` attributes are contractual:

- `aliases` maps field names to external names.
- `serialize_by_alias` selects aliases for output keys.
- `allow_deserialization_not_by_alias` also accepts field names on input.
- `omit_none` omits fields whose current value is `None`.
- `omit_default` omits values equal to a declared default or default factory
  result.
- `namedtuple_as_dict` projects named tuples as keyed dictionaries rather than
  lists.
- `sort_keys` emits dictionary and JSON keys in sorted order.
- `forbid_extra_keys` rejects unrecognized input keys with `ExtraKeysError`.
- `serialization_strategy` maps annotations to strategies.
- `dialect` selects a default dialect.
- `code_generation_options` enables documented optional call arguments and
  context propagation.

`ExtraKeysError.extra_keys` SHALL contain the set of rejected keys. Extra-key
checking SHALL use alias-aware accepted names.

WHERE `TO_DICT_ADD_BY_ALIAS_FLAG` is enabled, `to_dict(by_alias=...)` SHALL
override the configured output alias policy for that call. WHERE
`TO_DICT_ADD_OMIT_NONE_FLAG` is enabled, `to_dict(omit_none=...)` SHALL
override the configured omission policy for that call.

## Strategies And Dialects

`pass_through.serialize()` and `pass_through.deserialize()` return the exact
object supplied to them.

`RoundedDecimal` serializes a decimal using the configured number of places
and rounding mode, returning its decimal string, and deserializes decimal
strings to `Decimal` values.

`Alias` values compare and hash by their public `name` value.

`Discriminator` exposes `field`, `include_subtypes`, and
`include_supertypes`. IF neither inclusion direction is enabled THEN
construction SHALL raise `ValueError`.

WHEN a `SerializationStrategy` is registered for a type in
`BaseConfig.serialization_strategy`, THE strategy SHALL apply recursively in
dictionary conversion and typed codecs. A strategy declared with
`match_subclasses=True` SHALL apply to matching subclasses unless an exact
strategy is registered. A strategy declared with `use_annotations=True`
SHALL convert values according to its annotated input and output types before
and after its custom methods.

WHERE `ADD_DIALECT_SUPPORT` is enabled, `to_dict(dialect=...)` and matching
decode operations SHALL apply the supplied dialect for that call. A per-call
dialect takes precedence over `BaseConfig.dialect`. Codec `default_dialect`
applies when no per-call dialect is supplied.

WHERE `ADD_SERIALIZATION_CONTEXT` is enabled, `to_dict(context=...)` SHALL
pass the context to supported `__pre_serialize__` and `__post_serialize__`
hooks. The lifecycle hooks `__pre_deserialize__`, `__post_deserialize__`,
`__pre_serialize__`, and `__post_serialize__` SHALL wrap normal recursive
conversion in that order for the relevant direction.

## Typed Codecs

`BasicEncoder(T).encode(value)` SHALL produce the same basic form that typed
dictionary conversion would produce for `T`. `BasicDecoder(T).decode(value)`
SHALL reconstruct a value conforming to `T`.

`JSONEncoder(T).encode(value)` SHALL JSON-encode that typed basic form.
`JSONDecoder(T).decode(text)` SHALL parse JSON and perform typed conversion.
The convenience functions `json_encode(value, T)` and `json_decode(text, T)`
SHALL have equivalent behavior.

The JSON mixin SHALL use the same alias, omission, strategy, sort, and error
policies as dictionary conversion. It may accept custom encoder and decoder
callables that wrap the basic dictionary representation.

The YAML, TOML, and MessagePack mixins SHALL round-trip supported dataclass
values. TOML output omits `None` fields because TOML has no null value.
MessagePack retains bytes as bytes. Dictionary and JSON projections represent
bytes with the documented base64 string form.

## Schema Projection

`build_json_schema(str)` SHALL describe a string and
`build_json_schema(int)` SHALL describe an integer. Dataclass schemas SHALL
have object type, a title matching the class name, a `properties` mapping, and
a `required` list for fields without defaults.

UUID fields SHALL have string type and `uuid` format. Bytes SHALL have string
type and `base64` format.

`Annotated` metadata `Maximum`, `MaxItems`, and `MinLength` SHALL add the JSON
Schema keywords `maximum`, `maxItems`, and `minLength`. Field metadata key
`description` SHALL become a property description. A `JSONSchema` annotation
overlay SHALL retain the inferred type while adding values such as
`contentEncoding` and `contentMediaType`.

Field aliases SHALL be used for schema property names and required names.
Serialization strategies affect projected values, while schema generation
continues to describe the strategy's declared serialized type.

`JSONSchemaBuilder(OPEN_API_3_1)` SHALL emit named references under
`#/components/schemas/` and retain definitions across calls to `build()`.
`build_json_schema()` options `all_refs`, `with_definitions`,
`with_dialect_uri`, and `ref_prefix` SHALL control reference placement,
embedded definitions, the `$schema` URI, and the reference prefix.

## Product State Model

The durable state is a Python annotation graph: dataclass fields, nested type
annotations, defaults, field metadata, `BaseConfig`, strategies, and dialect
policy. The public views are:

1. Dataclass objects and basic dictionaries.
2. Basic, JSON, YAML, TOML, and MessagePack codec results.
3. JSON Schema models and accumulated builder definitions.

Each view is derived from the same annotation graph. Encoder and decoder
objects may retain their target annotation and default dialect. A
`JSONSchemaBuilder` additionally retains named definitions produced by prior
`build()` calls.

## Error Semantics

| Condition | Required result |
| --- | --- |
| A required input field is absent | Raise `MissingField` with `field_name` and `holder_class` |
| A field cannot be converted | Raise `InvalidFieldValue` or the underlying public conversion exception |
| `forbid_extra_keys` receives unknown keys | Raise `ExtraKeysError` with `extra_keys` |
| A `Discriminator` enables no inclusion direction | Raise `ValueError` |
| JSON text contains a value incompatible with a dataclass field | Propagate the field conversion failure |

Exact exception messages, tracebacks, generated source, and string
representations are not contractual.

## Cross-View Invariants

1. A supported object converted with `to_dict()` and reconstructed with
   `from_dict()` must preserve its dataclass value.
2. `BasicEncoder` output for a dataclass must equal its `to_dict()` result,
   and `BasicDecoder` must agree with `from_dict()`.
3. JSON mixin output and dictionary output must apply the same aliases,
   omission rules, strategies, and key ordering.
4. JSON Schema property names and required names must match alias-aware
   external dictionary keys.
5. JSON codec field names and JSON Schema property names must describe the
   same dataclass fields.
6. A registered strategy must affect dictionary and codec values while schema
   type follows the strategy's declared serialized type.
7. A per-call dialect must override the configured dialect; a merged dialect
   must combine strategy and omission policy.
8. Field conversion failures must remain observable when input travels
   through a wire-format decoder or format mixin.
9. Schema definitions accumulated by `JSONSchemaBuilder` must retain
   annotation constraints.
10. Format-specific bytes representations must round-trip to the same bytes
    value.

## Representative Workflows

```python
from dataclasses import dataclass, field
from mashumaro import DataClassDictMixin, field_options
from mashumaro.config import BaseConfig

@dataclass
class Contact(DataClassDictMixin):
    public_name: str = field(metadata=field_options(alias="publicName"))

    class Config(BaseConfig):
        serialize_by_alias = True

contact = Contact.from_dict({"publicName": "Ada"})
assert contact.to_dict() == {"publicName": "Ada"}
```

```python
from dataclasses import dataclass
from datetime import date
from mashumaro.codecs.json import JSONDecoder, JSONEncoder

@dataclass
class Event:
    name: str
    day: date

encoder = JSONEncoder(Event)
decoder = JSONDecoder(Event)
payload = encoder.encode(Event("release", date(2026, 8, 4)))
assert decoder.decode(payload) == Event("release", date(2026, 8, 4))
```

```python
from dataclasses import dataclass
from typing_extensions import Annotated
from mashumaro.jsonschema import build_json_schema
from mashumaro.jsonschema.annotations import Maximum

@dataclass
class Metric:
    score: Annotated[int, Maximum(10)]

schema = build_json_schema(Metric).to_dict()
assert schema["properties"]["score"] == {"type": "integer", "maximum": 10}
```

## Non-Goals

This specification does not require:

- Reproducing generated Python source, caches, compiler internals, private
  helper modules, or private attributes.
- Matching performance, memory layout, import timing, or exact exception
  wording.
- Optional integrations other than PyYAML, TOML writing, and MessagePack used
  by the covered format mixins.
- PEP 695-specific syntax, generic serialization beyond the covered typed
  forms, or third-party framework integrations.
- A command-line interface, remote resource, or persistent storage layer.

## Invocation Protocol

This is an importable Python library. There is no required console command.
Consumers install the project and import `mashumaro` and the documented public
submodules. Process exit codes and standard streams are not part of the
covered interface.

## Environment

The working environment runs Python 3.11 on Linux without network access. The
following third-party packages are preinstalled and importable: `pytest`,
`pytest-json-report`, `typing_extensions` version 4.14 or newer, `PyYAML`,
`tomli-w`, `tomli` on Python versions below 3.11, and `msgpack` version 0.5.6
or newer. The target `mashumaro` package is not pre-installed. The assessment
environment provides the same interpreter and package set.

The project must declare its packaging metadata in a standard
`pyproject.toml` or `setup.py` at the project root so the package can be
installed with pip.

## Evaluation Notes

Assessment focuses on observable conversion values, public exception types
and attributes, cross-format consistency, alias and strategy composition,
dialect precedence, lifecycle hooks, and schema dictionaries. It does not
inspect generated code, private modules, private attributes, exact exception
messages, or performance characteristics.
