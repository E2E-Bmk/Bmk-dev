# Marshmallow Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Marshmallow converts application objects and dictionaries to plain Python data, validates incoming data, and converts plain data back into application-level structures. A schema class declares named fields. A schema instance applies that declaration to one object, one dictionary, or a collection.

The public contract is centered on three views of the same declared schema state: serialized dictionaries returned by `dump`, deserialized dictionaries or objects returned by `load`, and validation details exposed through `ValidationError` and `validate`.

## Non-Goals

This specification does not require deprecated or removed APIs from prior major versions. It does not require private modules, private attributes, exact exception message wording, exact `repr` output, upstream test helpers, or undocumented internal class layout. It does not require a command line program.

This specification covers the core in-process Python API for defining schemas, field conversion, validators, nested schemas, pre/post processors, JSON helpers, and context lookup. It excludes command line behavior because marshmallow does not provide a supported command line interface.

The covered public imports are:

```python
from marshmallow import EXCLUDE, INCLUDE, RAISE, Schema, SchemaOpts, ValidationError
from marshmallow import fields, missing, post_dump, post_load, pre_dump, pre_load
from marshmallow import validates, validates_schema
from marshmallow import validate
from marshmallow.experimental.context import Context
```

## Representative Workflows

```python
from dataclasses import dataclass
from marshmallow import EXCLUDE, Schema, fields, post_load, validate

@dataclass
class User:
    name: str
    email: str
    age: int

class UserSchema(Schema):
    name = fields.Str(required=True)
    email = fields.Email(required=True)
    age = fields.Int(load_default=0, validate=validate.Range(min=0))

    @post_load
    def make_user(self, data, **kwargs):
        return User(**data)

payload = {"name": "Ada", "email": "ada@example.com", "extra": "ignored"}
user = UserSchema(unknown=EXCLUDE).load(payload)
public_data = UserSchema().dump(user)
```

The workflow must return a `User` instance from `load`, ignore the unknown key because the schema instance selected `EXCLUDE`, apply the age default, and dump the public fields back to a dictionary.

## Schema Declaration and Field Binding

This section covers how schemas declare their field set and how field projections are controlled.

**Class-based declaration.** A `Schema` subclass must collect field objects declared as class attributes. `Schema.from_dict(mapping)` must return a schema class using the supplied field mapping.

**Field projection.** Instantiating a schema with `only` must keep only those fields in dump and load views. Instantiating with `exclude` must remove those fields from dump and load views. Dotted `only` and `exclude` paths must apply to nested schemas. When a requested `only` or `exclude` field is not declared, schema construction must raise an exception.

**Active field views.** `Schema.fields` must reflect the active field projection after applying `only` and `exclude`. `Schema.dump_fields` must contain dump-eligible fields. `Schema.load_fields` must contain load-eligible fields. Fields removed by `only` or `exclude` must not appear in any of these views.

**Data key and attribute mapping.** `data_key` must set the external serialized/deserialized key while preserving the internal field name in loaded output. `attribute` must set the internal attribute or dictionary key read during dump. A dump operation must read object attributes or mapping keys by field name unless `attribute` overrides it.

**Load-only and dump-only.** A `load_only=True` field must be omitted from dump output. A `dump_only=True` field must be omitted from load processing unless the input policy treats it as unknown.

## Serialization and Deserialization

This section covers the dump and load operations and their collection variants.

**Dump.** `Schema.dump(obj, many=False)` must return a dictionary for one object and a list of dictionaries when `many=True` or the schema instance was created with `many=True`. Dump must not run validators against application objects. Dump must read from the application object using the field name or the `attribute` override.

**Load.** `Schema.load(data, many=False)` must validate and deserialize dictionaries, returning a dictionary by default and a list when loading a collection. When loading invalid data, `load` must raise `ValidationError`.

**JSON projections.** `Schema.dumps` must serialize the `dump` result as a JSON string. `Schema.loads` must parse a JSON string and then apply `load`. Data returned by `loads` must match data returned by `load` on the parsed JSON object.

**Validate without raising.** `Schema.validate(data)` must return the error dictionary instead of raising.

**Many via instance.** When the schema instance was created with `many=True`, `dump` and `load` must process collections without requiring the `many` argument.

## Field Types and Conversion

This section covers how individual fields convert between Python and serialized values.

**Raw field.** `fields.Raw` must pass values through unchanged in both dump and load directions.

**String and numeric fields.** `fields.Str` must accept string input and serialize strings; non-string input must raise a validation error. `fields.Int`, `fields.Float`, `fields.Number`, and `fields.Decimal` must deserialize compatible input to their Python numeric types. When `as_string=True` is set on a `Decimal` field, it must serialize decimal values as strings. `fields.Bool` must recognize documented truthy and falsy input values.

**Date and time fields.** `fields.Date`, `fields.Time`, `fields.DateTime`, and `fields.TimeDelta` must perform documented conversion between Python datetime values and plain serialized values. When `precision` is set on a `TimeDelta` field, it must control the units used for numeric representation.

**Identity and network fields.** `fields.UUID` must deserialize UUID strings. `fields.IP` must deserialize IP address strings into `ipaddress` objects. `fields.Url` and `fields.Email` must validate and pass through URL and email strings respectively.

**Collection fields.** `fields.List` must deserialize and serialize lists of typed elements. `fields.Tuple` must deserialize fixed-position typed elements into tuples. `fields.Dict` and `fields.Mapping` must deserialize typed key-value pairs.

**Special fields.** `fields.Constant` must return its configured constant value on both dump and load regardless of input. `fields.Function` must call its serialize function during dump. `fields.Method` must call the named schema method during dump. `fields.Enum` must convert between enum members and their values or names based on the `by_value` setting.

**Defaults.** A field with `load_default` must provide that value when input omits the field. A callable default must be called for each load. A field with `dump_default` must provide that value when the application object lacks the field. If `load_default=None` and `allow_none` is not explicitly set, `None` must be accepted during load. If `allow_none=False`, `None` must raise a validation error.

**Field-level processors.** Field-level `pre_load` processors must run before field deserialization. Field-level `post_load` processors must run after deserialization and validation. A processor that raises `ValidationError` must attach the error to that field.

## Validation and Error Reporting

This section covers how validators run and how errors are structured.

**Validator execution.** Field validators run during load and validate. A validator that returns `False` or raises `ValidationError` must make the field invalid. A field with multiple validators must collect all validation failures for that field.

**Error structure.** `ValidationError` must expose `messages`, `field_name`, `data`, and `valid_data` attributes. For collection loads, errors must be keyed by the invalid item index. For schema-level errors without a field key, messages must be stored under `_schema`.

**Built-in validators.** `Range` must enforce minimum and maximum numeric boundaries. `Length` must enforce string or collection length. `OneOf`, `NoneOf`, and `ContainsOnly` must compare values against their configured choices. `Equal`, `Regexp`, `Predicate`, `Email`, `URL`, and `And` must raise `ValidationError` when their condition is not met. `And` must compose multiple validators and collect all failures.

## Unknown, Partial, Defaults, and Key Mapping

This section covers how unknown keys, partial loading, and key mappings are handled.

**Unknown key policies.** `RAISE` must raise `ValidationError` for unknown keys. `EXCLUDE` must remove unknown keys from loaded data. `INCLUDE` must include unknown keys in the returned data. Fields removed from the active load view by `only` or `exclude` must be treated as unknown if those keys appear in input data.

**Policy precedence.** A `load(..., unknown=...)` argument must override an instance-level unknown policy. An instance-level unknown policy must override `class Meta.unknown`.

**Partial loading.** `partial=True` must skip required-field checks for missing fields. `partial=(...)` must skip required-field checks only for the named fields. Dotted partial paths must apply to nested fields.

**Required and data_key.** `required=True` must raise a validation error when the field is absent unless partial loading skips that required check. `data_key` must change the external key used in dump, load, and error dictionaries while preserving the internal field name in loaded output. Errors for fields with `data_key` must use the external key.

## Nested Data and Collection Handling

This section covers nested schemas, collections of nested objects, and pluck fields.

**Nested schema resolution.** `fields.Nested` must use another schema to dump and load nested objects. Passing a schema class, schema instance, callable returning a schema, `"self"`, or a registered schema class name must all resolve to the nested schema behavior.

**List of nested.** `fields.List(fields.Nested(...))` must process collections of nested objects. When nested input is invalid, the parent error dictionary must contain nested errors under the field name, keyed by collection index.

**Pluck.** `fields.Pluck(schema, field_name, many=False)` must replace a nested object with a single selected field on dump and reconstruct a nested dictionary on load. When `many=True`, it must dump a list of scalar values and load a list of nested dictionaries.

**Nested options.** Nested `only`, `exclude`, and `partial` options must affect nested schemas by dotted path. A nested schema's own `unknown` policy must apply inside that nested level.

## Processor and Validator Decorators

This section covers how schema-level hooks and validators are declared and how they transform data.

**Processing hooks.** `pre_load`, `post_load`, `pre_dump`, and `post_dump` must register instance methods as processing hooks. Hook methods must receive keyword arguments such as `many`. Load hooks must receive `partial` and `unknown` where documented.

**Pass-collection hooks.** When `pass_collection=True` is set, the hook must receive the full collection and `many` flag instead of one item at a time.

**Pass-original hooks.** When `pass_original=True` is set on `post_load`, the hook must receive the original input data as an additional `original` keyword argument. When `pass_original=True` is set on `post_dump`, the hook must receive the original application object.

**Per-field validators.** `validates(*field_names)` must register a method as a validator for one or more fields. The method must receive the deserialized value and a `data_key` keyword argument containing the external key name. When multiple field names are supplied, the validator must run independently for each named field.

**Schema-level validators.** `validates_schema` must register a schema-level validator. It must skip execution when field errors exist unless configured with `skip_on_field_errors=False`. Schema-level validation errors without a field key must be stored under `_schema`; errors with field keys must be merged into the per-field error dictionary.

**Hook data flow.** Hooks that return transformed data must feed that data into the next stage. Hooks that raise `ValidationError` must merge their messages into the error reporting model.

## JSON and Context Projections

This section covers JSON-string projections and the experimental context manager.

**JSON agreement.** `dumps` and `loads` must provide JSON string projections over the same behavior as `dump` and `load`. Data returned by `loads` must match data returned by `load` on the parsed JSON object. External `data_key` values and defaults must be preserved consistently across direct and JSON operations.

**Context manager.** `Context[T]` from `marshmallow.experimental.context` must act as a context manager. Entering the context must make the provided context object available through `Context.get()`. Exiting the context must restore the previous context. `Context.get(default)` must return the default when no context is active; `Context.get()` without a default must raise `LookupError` when no context is active.

## State Model

A schema class owns a declared field set. A schema instance owns an active projection of that field set after applying `only`, `exclude`, `many`, `unknown`, `partial`, `load_only`, `dump_only`, and nested-field options.

The declared field set must be visible through public schema field mappings. The serialization view must contain dump-eligible fields. The deserialization view must contain load-eligible fields. The error view must refer to external input keys when `data_key` changes an incoming key.

## Error Semantics

| Condition | Required result |
|---|---|
| Loading data that fails field validation | Raise `ValidationError` |
| Loading data when `unknown=RAISE` with unknown keys | Raise `ValidationError` |
| Missing `required=True` field during load (without partial) | Raise `ValidationError` |
| `None` value when `allow_none=False` | Raise `ValidationError` |
| Schema-level validator failure without field key | Store error messages under `_schema` key |
| Hook raises `ValidationError` | Merge into error dictionary |
| `only` or `exclude` names a non-existent field | Raise exception at schema construction |
| `Context.get()` without active context and no default | Raise `LookupError` |
| Invalid JSON in `loads` input | Raise underlying JSON parse error |
| Validator returns `False` | Raise `ValidationError` for that field |
| `dumps` serialization failure | Raise underlying serialization error |

## Cross-View Invariants

1. A field included in the active dump view must be represented in `dump` output and in `dumps` JSON output with the same external key.
2. A field included in the active load view must be represented in `load` output and in `loads` output with the same internal key.
3. A `data_key` mapping must use the external key in serialized output and validation errors, while successful loaded data returns the internal field name.
4. `load(..., unknown=EXCLUDE)` and a schema instance configured with `unknown=EXCLUDE` for `validate` must agree that excluded unknown keys are not errors.
5. `load(..., unknown=RAISE)` and a schema instance configured with `unknown=RAISE` for `validate` must agree that unknown keys are errors.
6. A nested schema must apply the same conversion rules whether it is reached through `Nested`, `List(Nested(...))`, or JSON loading of the same nested data.
7. Defaults must affect missing values consistently across direct `load` and JSON `loads`.
8. Decorator hooks must transform the data seen by later field conversion and by the final dump/load result.

## Public Interface

### Import Surface

`marshmallow` must be importable as a Python package. The top-level package must export `Schema`, `SchemaOpts`, `ValidationError`, `fields`, `missing`, the unknown-policy constants `EXCLUDE`, `INCLUDE`, and `RAISE`, and the decorator functions `pre_load`, `post_load`, `pre_dump`, `post_dump`, `validates`, and `validates_schema`.

The `marshmallow.fields` module must export the field classes documented in the API reference, including `Raw`, `String`/`Str`, `Integer`/`Int`, `Float`, `Number`, `Decimal`, `Boolean`/`Bool`, `Date`, `DateTime`, `Time`, `TimeDelta`, `Email`, `Url`/`URL`, `UUID`, `IP`, `IPv4`, `IPv6`, `IPInterface`, `List`, `Tuple`, `Dict`, `Mapping`, `Nested`, `Pluck`, `Method`, `Function`, `Constant`, and `Enum`.

The `marshmallow.validate` module must export callable validator classes including `Range`, `Length`, `Equal`, `OneOf`, `NoneOf`, `ContainsOnly`, `Predicate`, `Regexp`, `Email`, `URL`, and `And`.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| Schema | class | Declare fields and conversion/validation rules |
| SchemaOpts | class | Schema-level configuration container |
| ValidationError | exception | Carry field-keyed error messages |
| fields | module | Field type definitions for schema declarations |
| validate | module | Reusable validator callables |
| missing | sentinel | Distinguish absent input from explicit None |
| EXCLUDE | constant | Unknown-field policy: silently drop |
| INCLUDE | constant | Unknown-field policy: pass through |
| RAISE | constant | Unknown-field policy: raise ValidationError |
| pre_load | decorator | Register pre-deserialization hook |
| post_load | decorator | Register post-deserialization hook |
| pre_dump | decorator | Register pre-serialization hook |
| post_dump | decorator | Register post-serialization hook |
| validates | decorator | Register per-field validator |
| validates_schema | decorator | Register schema-level validator |
| Context | class | Experimental typed context accessor |

### CLI Entry Points

The package is used through Python imports. There is no supported `marshmallow` console script. `python -m marshmallow` is not supported and callers must not depend on it.

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Compatibility covers the documented imports, schema declaration, dump/load/JSON agreement, field conversion, validators, unknown and partial policies, nested schemas, processor hooks, error dictionaries, and context behavior. It uses public return values, exception types, and documented exception attributes without requiring exact error prose, private state, source layout, or maintainer-only helpers.
