# Marshmallow Specification

## Product Overview

Marshmallow converts application objects and dictionaries to plain Python data, validates incoming data, and converts plain data back into application-level structures. A schema class declares named fields. A schema instance applies that declaration to one object, one dictionary, or a collection.

The public contract is centered on three views of the same declared schema state: serialized dictionaries returned by `dump`, deserialized dictionaries or objects returned by `load`, and validation details exposed through `ValidationError` and `validate`.

## Scope

This specification covers the core in-process Python API for defining schemas, field conversion, validators, nested schemas, pre/post processors, JSON helpers, and context lookup. It excludes command line behavior because marshmallow does not provide a supported command line interface.

The covered public imports are:

```python
from marshmallow import EXCLUDE, INCLUDE, RAISE, Schema, SchemaOpts, ValidationError
from marshmallow import fields, missing, post_dump, post_load, pre_dump, pre_load
from marshmallow import validates, validates_schema
from marshmallow import validate
from marshmallow.experimental.context import Context
```

## Installable Surface

`marshmallow` must be importable as a Python package. The top-level package must export `Schema`, `SchemaOpts`, `ValidationError`, `fields`, `missing`, the unknown-policy constants `EXCLUDE`, `INCLUDE`, and `RAISE`, and the decorator functions `pre_load`, `post_load`, `pre_dump`, `post_dump`, `validates`, and `validates_schema`.

The `marshmallow.fields` module must export the field classes documented in the API reference, including `Raw`, `String`/`Str`, `Integer`/`Int`, `Float`, `Number`, `Decimal`, `Boolean`/`Bool`, `Date`, `DateTime`, `Time`, `TimeDelta`, `Email`, `Url`/`URL`, `UUID`, `IP`, `IPv4`, `IPv6`, `IPInterface`, `List`, `Tuple`, `Dict`, `Mapping`, `Nested`, `Pluck`, `Method`, `Function`, `Constant`, and `Enum`.

The `marshmallow.validate` module must export callable validator classes including `Range`, `Length`, `Equal`, `OneOf`, `NoneOf`, `ContainsOnly`, `Predicate`, `Regexp`, `Email`, `URL`, and `And`.

## Product State Model

A schema class owns a declared field set. A schema instance owns an active projection of that field set after applying `only`, `exclude`, `many`, `unknown`, `partial`, `load_only`, `dump_only`, and nested-field options.

The declared field set must be visible through public schema field mappings. The serialization view must contain dump-eligible fields. The deserialization view must contain load-eligible fields. The error view must refer to external input keys when `data_key` changes an incoming key.

## Schema Declaration and Field Binding

A `Schema` subclass must collect field objects declared as class attributes. `Schema.from_dict(mapping)` must return a schema class using the supplied field mapping. Instantiating a schema with `only` must keep only those fields in dump and load views. Instantiating with `exclude` must remove those fields from dump and load views. Dotted `only` and `exclude` paths must apply to nested schemas.

Field instances must support `data_key` for the external serialized/deserialized key and `attribute` for the internal attribute or dictionary key. A dump operation must read object attributes or mapping keys by field name unless `attribute` is set. A load operation must return internal field names unless the schema returns an object through a processor.

When a requested `only` or `exclude` field is not declared, schema construction must raise an exception rather than silently accepting the typo.

## Serialization and Deserialization

`Schema.dump(obj, many=False)` must return a dictionary for one object and a list of dictionaries when `many=True` or the schema instance was created with `many=True`. `Schema.load(data, many=False)` must validate and deserialize dictionaries, returning a dictionary by default and a list when loading a collection.

`Schema.dumps` must serialize the `dump` result as a JSON string. `Schema.loads` must parse a JSON string and then apply `load`.

Dumping must skip `load_only` fields. Loading must skip `dump_only` fields unless the input policy treats them as unknown. Validation must run during loading and `validate`; dump must not run validators against already trusted application objects.

When loading invalid data, `load` must raise `ValidationError`. `Schema.validate(data)` must return the error dictionary instead of raising.

## Field Types and Conversion

String fields must accept string input and serialize string values as strings; non-string input must raise a validation error. Integer, Float, Number, and Decimal fields must deserialize compatible numeric input to their documented Python numeric types. `Decimal(as_string=True)` must serialize decimals as strings. Boolean fields must recognize documented truthy and falsy input values.

Date, Time, DateTime, TimeDelta, UUID, IP address, URL, Email, List, Tuple, Dict, Mapping, Nested, Pluck, Method, Function, Constant, and Enum fields must perform the documented conversion between Python values and plain serialized values.

A field with `load_default` must provide that value when input omits the field. A callable default must be called for each load. A field with `dump_default` must provide that value when the application object lacks the field during dump.

If `load_default=None` and `allow_none` is not explicitly set, `None` must be accepted during load. If `allow_none=False`, `None` must raise a validation error.

Field-level `pre_load` processors must run before field deserialization. Field-level `post_load` processors must run after field deserialization and validation. A processor that raises `ValidationError` must attach the error to that field.

## Validation and Error Reporting

Field validators run during load and validate. A validator that returns `False` or raises `ValidationError` must make the field invalid. A field with multiple validators must collect validation failures for that field.

`ValidationError` must expose `messages`, `field_name`, `data`, and `valid_data` attributes. For collection loads, errors must be keyed by the invalid item index. For schema-level errors without a field key, messages must be stored under `_schema`.

The built-in validators must be callable objects. `Range` must enforce minimum and maximum numeric boundaries. `Length` must enforce string or collection length. `OneOf`, `NoneOf`, and `ContainsOnly` must compare values against their configured choices. `Equal`, `Regexp`, `Predicate`, `Email`, `URL`, and `And` must raise `ValidationError` when their condition is not met.

## Unknown, Partial, Defaults, and Key Mapping

Unknown input keys must follow the active unknown policy. Fields removed from the active load view by `only` or `exclude` must be treated as unknown if those keys appear in input data. `RAISE` must raise `ValidationError`, `EXCLUDE` must remove unknown keys, and `INCLUDE` must include unknown keys in the returned data. A `load(..., unknown=...)` argument must override an instance-level unknown policy, and an instance-level unknown policy must override `class Meta.unknown`.

`partial=True` must skip required-field checks for missing fields. `partial=(...)` must skip required-field checks only for the named fields. Dotted partial paths must apply to nested fields.

`required=True` must raise a validation error when the field is absent unless partial loading skips that required check. `data_key` must change the external key used in dump, load, and error dictionaries while preserving the internal field name in loaded output.

## Nested Data and Collection Handling

`fields.Nested` must use another schema to dump and load nested objects. Passing a schema class, schema instance, callable returning a schema, `"self"`, or a registered schema class name must resolve to the nested schema behavior documented for that form.

`fields.List(fields.Nested(...))` must process collections of nested objects. `fields.Pluck(schema, field_name, many=False)` must replace a nested object with a single selected field on dump and reconstruct a nested dictionary on load. Nested `only`, `exclude`, and `partial` options must affect nested schemas by dotted path.

When nested input is invalid, the parent error dictionary must contain nested error dictionaries under the nested field name, or under collection indices for list input.

## Processor and Validator Decorators

`pre_load`, `post_load`, `pre_dump`, and `post_dump` must register instance methods as processing hooks. Hook methods must receive keyword arguments such as `many`, and load hooks must receive `partial` and `unknown` where documented. `pass_collection=True` must pass the full collection to the hook instead of one item at a time. `pass_original=True` must pass the original object or input to post hooks where documented.

`validates(*field_names)` must register a method as a validator for one or more fields. The method must receive the deserialized value and a `data_key` keyword argument. `validates_schema` must register a schema-level validator. It must skip execution when field errors exist unless configured with `skip_on_field_errors=False`.

Hooks that return transformed data must feed that data into the next public stage of dumping or loading. Hooks that raise `ValidationError` must merge their messages into the same error reporting model as field and schema validation.

## JSON and Context Projections

`dumps` and `loads` must provide JSON string projections over the same behavior as `dump` and `load`. Data returned by `loads` must match data returned by `load` on the parsed JSON object.

`Context[T]` from `marshmallow.experimental.context` must act as a context manager. Entering the context must make the provided context object available through `Context.get()`. Exiting the context must restore the previous context. `Context.get(default)` must return the default when no context is active; `Context.get()` without a default must raise `LookupError` when no context is active.

Function and Method fields must be able to use current context values while dumping.

## Cross-View Invariants

1. A field included in the active dump view must be represented in `dump` output and in `dumps` JSON output with the same external key.
2. A field included in the active load view must be represented in `load` output and in `loads` output with the same internal key.
3. A `data_key` mapping must use the external key in serialized output and validation errors, while successful loaded data returns the internal field name.
4. `load(..., unknown=EXCLUDE)` and a schema instance configured with `unknown=EXCLUDE` for `validate` must agree that excluded unknown keys are not errors.
5. `load(..., unknown=RAISE)` and a schema instance configured with `unknown=RAISE` for `validate` must agree that unknown keys are errors.
6. A nested schema must apply the same conversion rules whether it is reached through `Nested`, `List(Nested(...))`, or JSON loading of the same nested data.
7. Defaults must affect missing values consistently across direct `load` and JSON `loads`.
8. Decorator hooks must transform the data seen by later field conversion and by the final dump/load result.

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

## Non-Goals

This specification does not require compatibility with marshmallow 2.x or 3.x APIs that were removed in version 4. It does not require private modules, private attributes, exact exception message wording, exact `repr` output, upstream test helpers, or undocumented internal class layout. It does not require a command line program.

## Invocation Protocol

The package is used through Python imports. There is no supported `marshmallow` console script. `python -m marshmallow` is not supported and callers must not depend on it.

Exit code behavior is therefore limited to normal Python process behavior: importing and calling the API succeeds without exiting the process; uncaught exceptions propagate according to Python rules.

## Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Evaluation Notes

Assessment exercises the documented imports, schema declaration, dump/load/JSON agreement, field conversion, validators, unknown and partial policies, nested schemas, processor hooks, error dictionaries, and context behavior. It uses public return values, exception types, and documented exception attributes without requiring exact error prose, private state, source layout, or maintainer-only helpers.
