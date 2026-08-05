# APISchema Specification

=== Context Layer ===

## Product Overview

`apischema` maps Python type annotations and dataclass metadata to several coordinated public projections. It deserializes JSON-like values into typed Python objects, serializes typed objects back into JSON-like values, validates input, and generates JSON Schema documents for input and output models.

The shared source of truth is a Python type or data model: primitive types, collections, unions, enums, dataclasses, field metadata, conversions, constraints, defaults, and computed serialized methods. The same declarations control runtime conversion, serialized key/value shape, validation locations, required fields, schema constraints, references, and definitions.

## Non-Goals

- GraphQL schema generation and execution are outside this specification because the optional GraphQL dependency is not part of the environment.
- Optional C extensions, code generation, performance claims, and build optimization are not required.
- Network services, databases, web frameworks, filesystem persistence, and command-line workflows are outside scope.
- Private modules, internal visitor classes, generated method code, and exact internal error prose are not defined.
- Arbitrary custom global settings and mutation of process-wide conversion registries are not required.
- Full JSON Schema standard coverage is not required beyond the versions, types, constraints, references, and object projections explicitly described below.

## Scope

This specification covers public deserialization, serialization, reusable conversion methods, field aliases, runtime aliasers, default and exclusion behavior, undefined fields, computed serialized methods, key ordering, enum name conversion, JSON Schema input/output generation, named references, definition generation, validation errors, primitive coercion, and standard typed values.

All behavior operates on local Python and JSON-like values in one process. Inputs and outputs consist of dictionaries, lists, strings, integers, floats, booleans, null values, and the explicitly supported Python types below.

=== Orientation Layer ===

## Representative Workflows

A dataclass can be structured from a dictionary and projected back to a dictionary:

```python
from dataclasses import dataclass
from apischema import deserialize, serialize

@dataclass
class User:
    user_id: int
    name: str
    active: bool = True

payload = {"user_id": 17, "name": "Nia", "active": False}
user = deserialize(User, payload)
assert user == User(17, "Nia", False)
assert serialize(User, user) == payload
```

The same model produces an input schema:

```python
from apischema.json_schema import deserialization_schema

document = deserialization_schema(User)
assert document["type"] == "object"
assert document["properties"]["user_id"] == {"type": "integer"}
assert document["required"] == ["user_id", "name"]
```

Metadata changes every relevant projection:

```python
from dataclasses import dataclass, field
from apischema import alias, deserialize, serialize

@dataclass
class Record:
    record_id: int = field(metadata=alias("recordId"))

record = deserialize(Record, {"recordId": 4})
assert serialize(Record, record) == {"recordId": 4}
```

=== Behavior Layer ===

## Dictionary Conversion

**Deserialization.** `deserialize(type, data, ...)` converts JSON-like input into the requested Python type. Integer input deserializes as `int`. Integer input for `float` becomes an equal `float`. `None` is accepted by optional types. Dataclasses are built recursively from object properties, including nested dataclasses and dataclasses inside lists or mappings.

Deserialization is strict by default. A string is not accepted for an integer field unless `coerce=True`. Coercion converts primitive values throughout nested models, including string integers and floats. `additional_properties=True` permits unknown object properties for models that do not retain them; the resulting dataclass contains its declared fields only.

`fall_back_on_default=True` replaces an invalid supplied field with its dataclass default when one exists. Without that option, invalid field input raises `ValidationError`.

**Serialization.** `serialize(type, obj, ...)` projects typed values to JSON-like data recursively. Dataclasses become dictionaries, tuples and sets become list-like values, standard wire types become strings, and nested collections preserve their logical shape. A caller may omit the explicit type only when runtime `Any` behavior is intended.

`no_copy=True` may return an already compatible mapping object unchanged. `exclude_none=True` omits fields whose value is `None`. `exclude_defaults=True` omits fields equal to their declared defaults. Such reduced dictionaries must deserialize back to the same defaulted model.

**Reusable methods.** `deserialization_method(type, ...)` returns a callable that can structure repeated inputs using one prepared method. `serialization_method(type, ...)` returns the corresponding reusable output callable. Their results must agree with direct `deserialize` and `serialize` calls for the same options.

**Directional mappings.** Coercing a mapping with integer key type turns string input keys into integers. Serializing that typed mapping preserves its integer keys; serialization does not force them back to strings. JSON Schema generation for mappings requires a string-compatible key schema and may reject an integer-key mapping with `ValueError`.

## Typed Values And Collections

Lists deserialize each element according to their item type. A fixed tuple uses one type per position, deserializes from a list, and serializes back to a list. Its schema is an array with equal minimum and maximum lengths and positional item schemas. Sets deserialize from arrays, remove duplicates, serialize as arrays, and use `uniqueItems: true` in schema.

Mappings structure keys and values recursively. With coercion enabled, a mapping declared with integer keys converts string keys to integers and recursively converts values. The `Any` type returns an input object unchanged during deserialization and recursively projects runtime mappings and tuples during serialization; an `Any` schema is unconstrained.

`Literal` accepts only declared values and projects them as an `enum` in schema. Optional values accept both their non-null type and null; JSON Schema 2020-12 may express this as a `type` array such as `["integer", "null"]`.

Normal enums deserialize and serialize by member value. An enum decorated with `apischema.conversions.as_names` uses member names for both directions and lists those names in schema.

`NewType` uses its underlying runtime and schema type. A `NewType` over `int` structures and serializes integers and projects an integer schema.

Bytes use base64 text. `datetime.date` uses ISO date text. `uuid.UUID` uses canonical string form. When these values are fields of one dataclass, the complete model must round-trip and all three output values must be strings.

## Field Metadata And Configuration

`alias(name)` used as dataclass field metadata replaces the Python field name in deserialization, serialization, and schema properties. The aliased required name appears in input schema `required`. A call-level `aliaser` applies the same transformation to every unannotated field for deserialization, serialization, and schema generation.

Dataclass defaults make input properties optional and appear as `default` values in input schema. Normal serialization still emits default-valued fields, so output schema marks those emitted fields required. Input and output schemas therefore share field shapes but may have different `required` lists and default keywords.

`Undefined` is the singleton instance of `UndefinedType`. A field declared as a union with `UndefinedType` and defaulted to `Undefined` represents absence. Deserializing an omitted field leaves that singleton, serialization omits the field, and input schema does not mark it required.

`serialized` decorates a module-visible method whose return value becomes an output property. The method name is its default key. The computed property appears in serialized output and serialization schema, but not in deserialization schema. It is required in output schema when it always returns its annotated type.

`order([...])` defines serialized field order. The serialized mapping and serialization schema `properties` preserve the declared order.

`exclude_none` and `exclude_defaults` affect the current serialized payload but do not mutate the data model or its declarations. `additional_properties=True` affects acceptance of unknown input; unknown fields not represented by the dataclass are not invented during later serialization.

## Schema Projection

`deserialization_schema(type, ...)` returns the input JSON Schema mapping. `serialization_schema(type, ...)` returns the output mapping. Both use a top-level `$schema` URI, object `properties`, type-specific keywords, and `additionalProperties: false` by default for dataclasses.

Primitive and collection projections include `type: integer`, `number`, `string`, `boolean`, `array`, and `object` as applicable. Array schemas expose `items`; fixed tuples expose positional items and fixed bounds. Dataclass fields become properties. Required input fields are fields without defaults, while required output fields are values always emitted during normal serialization.

The input and output schemas of a plain nested dataclass share top-level and nested property names and primitive types. Defaults may appear only in input schema, and defaulted output fields may still be required. A computed serialized method appears only in output schema.

`schema(min=..., max=...)` applied to an integer-like type produces `minimum` and `maximum`. Those bounds also govern runtime validation when the constrained type appears as a field.

`type_name(name)` assigns a public reference name. With `all_refs=True`, a named type may project as `$ref: "#/$defs/{name}"` plus a `$defs` entry. `definitions_schema` returns named definitions for requested deserialization and serialization types when references are enabled.

`JsonSchemaVersion.DRAFT_7` selects the Draft 7 schema URI and Draft 7 reference conventions. The current default version uses the JSON Schema 2020-12 URI and `$defs` keyword.

Aliases, runtime aliasers, enum names or values, literals, constraints, standard string formats, undefined defaults, computed methods, and ordering must be reflected consistently in their corresponding schema direction.

## Validation And Errors

`ValidationError` is raised for type mismatches, out-of-range constrained values, unexpected properties under default strictness, and other invalid structured input. Its public `errors` attribute is a nonempty list of dictionaries.

Each error dictionary exposes a `loc` list locating the invalid value. A direct invalid dataclass field has a one-element location such as `["count"]`. A nested invalid field includes the full model path, such as `["address", "postal_code"]`.

Unexpected fields are rejected by default, matching `additionalProperties: false` in input schema. Passing `additional_properties=True` permits them. Passing `fall_back_on_default=True` recovers an invalid defaulted field instead of returning a validation failure.

Values outside a `schema(min=..., max=...)` constraint raise `ValidationError` at the constrained field location. Values within the range deserialize normally and serialize to their underlying primitive value.

When no conversion or public data-model support exists for a class, deserialization raises the public `Unsupported` exception. Exact exception message prose is not defined.

=== Contract Layer ===

## Product State Model

The central state is a graph of Python types and declarations: dataclass fields, annotations, defaults, aliases, constraints, enum rules, type names, computed methods, and collection element types. Runtime objects, JSON-like payloads, input schemas, output schemas, definitions, and validation error locations are independent projections of that graph.

Deserialization moves from payload to typed object while validating declarations. Serialization moves from typed object to payload while applying output rules. Schema generation describes the accepted input or emitted output without executing a network service or persisting state.

## Error Semantics

| Condition | Required result |
|---|---|
| Strict integer receives string input | Raise `ValidationError` |
| Nested field has invalid type | Raise `ValidationError` with full `loc` path |
| Unknown property under default strictness | Raise `ValidationError` |
| Constrained number is outside its bounds | Raise `ValidationError` at that field |
| Unsupported class has no public conversion | Raise `Unsupported` |
| Signed or service-backed behavior | Outside scope |
| JSON Schema requested for non-string-compatible mapping keys | May raise `ValueError` |

## Cross-View Invariants

1. A payload accepted for a model must produce field values matching its annotations and must serialize back to the documented output shape.
2. Dataclass nesting and collection order must agree across input payloads, typed objects, output payloads, and schema properties.
3. Alias rules must select the same external key in both conversion directions and the relevant schema.
4. Input schema required fields must match fields required to deserialize, while output schema required fields must match fields emitted by normal serialization.
5. Default and undefined behavior must agree across absent input, typed field value, exclusion options, serialized output, and schema required/default keywords.
6. Validation locations must identify the same field path represented by nested schema properties.
7. Enum and literal allowed values must agree across deserialization, serialization, and schema enums.
8. Named references and definitions must describe the same type that direct conversion handles.
9. Computed serialized methods must affect output and output schema only, leaving input schema unchanged.
10. Reusable conversion methods must produce the same values as direct conversion functions.

=== Reference Layer ===

## Installable Surface

### Public Import Surface

```python
from apischema import (
    Undefined,
    UndefinedType,
    Unsupported,
    ValidationError,
    alias,
    deserialize,
    deserialization_method,
    order,
    schema,
    serialize,
    serialization_method,
    serialized,
    type_name,
)
from apischema.conversions import as_names
from apischema.json_schema import (
    JsonSchemaVersion,
    definitions_schema,
    deserialization_schema,
    serialization_schema,
)
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `deserialize` | function | Validates and converts JSON-like values to typed Python values. |
| `serialize` | function | Converts typed Python values to JSON-like values. |
| `deserialization_method` | function | Builds a reusable input converter. |
| `serialization_method` | function | Builds a reusable output converter. |
| `ValidationError` | exception | Exposes structured validation errors and locations. |
| `Unsupported` | exception | Signals a type with no supported conversion route. |
| `alias` | metadata helper | Assigns an external field name. |
| `schema` | decorator/metadata helper | Adds JSON Schema and validation constraints. |
| `serialized` | decorator | Adds a computed output property. |
| `order` | decorator | Controls output field order. |
| `type_name` | decorator | Assigns a named schema reference. |
| `Undefined` | singleton | Represents an absent rather than null value. |
| `UndefinedType` | class | Type used in unions for potentially absent fields. |
| `as_names` | enum decorator | Uses enum member names instead of values. |
| `deserialization_schema` | function | Generates an input JSON Schema mapping. |
| `serialization_schema` | function | Generates an output JSON Schema mapping. |
| `definitions_schema` | function | Generates named schema definitions for requested types. |
| `JsonSchemaVersion` | enum | Selects supported JSON Schema versions. |

### CLI Entry Points

There is no required command-line interface. The package is used through Python imports and function calls.

## Invocation Protocol

Install the project as a standard Python distribution, import the public functions and helpers listed above, define normal annotated Python types or dataclasses, and call conversion or schema functions directly. Inputs are local JSON-like Python values and outputs are local Python objects or dictionaries. No daemon, service, generated source file, or external process is involved.

=== Meta Layer ===

## Environment

The working environment runs Python 3.11 on Linux without network access. The third-party package `pytest` is preinstalled and importable. The target package is not pre-installed. The optional GraphQL package and external services are unavailable.

The project must include standard packaging metadata in `pyproject.toml` or `setup.py` so it installs with pip. The public conversion and JSON Schema surface must work without optional C extensions.

## Evaluation Notes

The implementation is exercised through public imports and deterministic local values. Checks use module-visible dataclasses so postponed annotations resolve consistently. They do not import private target modules, access network resources, launch subprocesses, depend on local timezone settings, inspect exact exception prose, or compare private generated code.
