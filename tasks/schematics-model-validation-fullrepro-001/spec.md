# Schematics Specification

## Product Overview

Schematics defines declarative Python data models. A model declaration combines
field types with validation and export rules so callers receive native Python
values for program use and primitive values for interchange formats.

## Scope

This specification covers model declaration and instances, scalar and compound
types, type conversion and validation, model import and export, serialization
roles, calculated fields, error objects, and supported public imports.

## Installable Surface

Install the `schematics` package and import the model base as either
`from schematics import Model` or `from schematics.models import Model`.

Import field types from `schematics.types`. The package exports `BaseType`,
`UUIDType`, `StringType`, `MultilingualStringType`, `NumberType`, `IntType`,
`LongType`, `FloatType`, `DecimalType`, `HashType`, `MD5Type`, `SHA1Type`,
`BooleanType`, `GeoPointType`, `DateType`, `DateTimeType`, `UTCDateTimeType`,
`TimestampType`, `TimedeltaType`, `CompoundType`, `MultiType`, `ModelType`,
`ListType`, `DictType`, `PolyModelType`, `calculated`, `serializable`,
`Serializable`, `IPAddressType`, `IPv4Type`, `IPv6Type`, `MACAddressType`,
`URLType`, `EmailType`, and `UnionType`.

Import error classes from `schematics.exceptions`: `BaseError`, `ErrorMessage`,
`FieldError`, `ConversionError`, `ValidationError`, `StopValidationError`,
`CompoundError`, `DataError`, `MockCreationError`, `UndefinedValueError`, and
`UnknownFieldError`. Import `wholelist`, `whitelist`, and `blacklist` from
`schematics.transforms` for export-role definitions.

No command-line interface is provided.

## Product State Model

A model has three caller-visible projections of one declared field state:

1. The instance projection exposes declared values through attributes and the
   mapping interface after inbound conversion.
2. The native projection exposes the same exportable values as Python-native
   data through `to_native()`.
3. The primitive projection exposes the same exportable values in their field
   primitive form through `to_primitive()` or `serialize()`.

The instance projection must return the same native field value through
attribute and mapping lookup. A value written through either access style must
appear in subsequent native and primitive export. A field excluded by a role
must be absent from both export projections for that role. A conversion or
validation failure must raise its documented error and must not present the
invalid value as successfully validated.

## Public API

### Model declarations and construction

Declare a `Model` subclass by assigning field-type instances to class
attributes. Declared-field order must remain the declaration order. A declared
field must support attribute access and mapping access on each instance.

Construct an instance with
`Model(raw_data=None, trusted_data=None, deserialize_mapping=None, init=True,
partial=True, strict=True, validate=False, app_data=None, lazy=False, **kwargs)`.
The constructor must convert supplied `raw_data` into the field-native values.
It must raise `DataError` when `validate=True` and supplied data violates a
conversion, field, or model validation rule. It must raise `DataError` when
`strict=True` and the input contains an unrecognized key. It must return an
instance without required-field failure when validation is not requested or
when partial validation is requested.

Each instance must expose `validate(partial=False, convert=True, app_data=None,
**kwargs)`, `import_data(raw_data, recursive=False, **kwargs)`,
`to_native(role=None, app_data=None, **kwargs)`,
`to_primitive(role=None, app_data=None, **kwargs)`, `serialize(*args, **kwargs)`,
`export(field_converter=None, role=None, app_data=None, **kwargs)`, `keys()`,
`items()`, `values()`, `get(key, default=None)`, and `get_mock_object(context=None,
overrides={})`.

`import_data` must update the same instance and return that instance. Attribute
assignment and `instance[field_name] = value` must accept declared field names.
Mapping assignment, lookup, or deletion with an undeclared field name must
raise `UnknownFieldError`. Attribute access to a declared but absent value must
raise `UndefinedValueError` when no serializable value supplies that name.

### Field options and scalar types

`BaseType(required=False, default=Undefined, serialized_name=None, choices=None,
validators=None, deserialize_from=None, export_level=None,
serialize_when_none=None, messages=None, metadata=None)` is the field base.
Every field must provide `to_native(value, context=None)`,
`to_primitive(value, context=None)`, and `validate(value, context=None)`.
`required=True` must reject absent or `None` values during non-partial
validation. `default` must supply a literal value or a newly evaluated callable
result when input omits the field. `choices` and each supplied validator must
reject invalid converted values by raising `ValidationError`.

`serialized_name` must name the field in native and primitive export.
`deserialize_from` must supply alternate inbound keys. When an input contains
the declared field name, its `serialized_name`, and its `deserialize_from` name
at once, conversion must use the declared field name; when it lacks that name
but contains both alternate names, conversion must use `serialized_name`.

`StringType(regex=None, max_length=None, min_length=None, **kwargs)` must
produce Unicode text and must raise `ConversionError` for values it cannot
coerce. It must raise `ValidationError` when a converted value violates its
length or regular-expression constraint. `NumberType(min_value=None,
max_value=None, strict=False, **kwargs)` and its `IntType`, `LongType`,
`FloatType`, and `DecimalType` variants must convert accepted numeric input and
must raise `ConversionError` for unconvertible input or `ValidationError` for
out-of-range values. `LongType` must behave as the integer variant.
`DecimalType` must return `decimal.Decimal` values natively and strings
primitively.

`BooleanType` must accept booleans, `0`/`1`, and the strings `"True"`,
`"true"`, `"1"`, `"False"`, `"false"`, and `"0"`; it must raise
`ConversionError` for other values. `UUIDType` must produce `uuid.UUID`
values natively and strings primitively. `DateType` must produce
`datetime.date` values and ISO date strings. `DateTimeType` must produce
`datetime.datetime` values and ISO-8601 strings, and it must raise
`ConversionError` for input it cannot parse or timezone policy it rejects.
`UTCDateTimeType` must normalize to UTC as a naive native datetime and emit an
ISO-8601 value with `Z`. `TimestampType` must emit a Unix timestamp.
`TimedeltaType(precision='seconds', **kwargs)` must convert supported numeric
unit values to `datetime.timedelta` and must raise `ConversionError` for
unconvertible input. `GeoPointType` must accept a two-element numeric list,
tuple, or mapping and must raise `ConversionError` for another shape or value
kind and `ValidationError` for coordinates outside latitude/longitude bounds.

`HashType`, `MD5Type`, and `SHA1Type` must reject malformed hash values through
`ConversionError` or `ValidationError`; `MD5Type` and `SHA1Type` must enforce
their respective fixed digest lengths. `IPAddressType`, `IPv4Type`, `IPv6Type`,
`MACAddressType`, `URLType`, and `EmailType` must reject malformed values with
`ValidationError` or `ConversionError`. `URLType(fqdn=True,
verify_exists=False, **kwargs)` must apply FQDN checking when `fqdn=True` and
must reject an unreachable URL when `verify_exists=True`.

`MultilingualStringType(regex=None, max_length=None, min_length=None,
default_locale=None, locale_regex=..., **kwargs)` must store a locale-to-text
mapping. Primitive export must select the first available locale from
`app_data['locale']` followed by `default_locale`; it must raise
`ConversionError` when neither source supplies a locale or no selected locale
exists in the mapping. It must raise `ValidationError` when locale names or
localized values violate configured constraints.

### Compound and calculated fields

`ModelType(model_spec, **kwargs)` must accept its model class or a model-name
string. It must convert a mapping into the specified model and must accept an
instance of that model; it must raise `ConversionError` for another input kind.
`ListType(field, min_size=None, max_size=None, **kwargs)` must convert each
element with its nested field and must raise a nested error for an invalid
element or `ValidationError` when length constraints fail. `DictType(field,
coerce_key=None, **kwargs)` must convert each mapping value through its nested
field and must raise `ConversionError` for non-mapping input. `PolyModelType`
must accept only its configured model family and must raise a conversion error
when no configured model claims the input. `UnionType(types=None,
resolver=None, **kwargs)` must resolve a value through one configured type and
must raise `ConversionError` when no configured type accepts it.

`serializable` must decorate a model method as a calculated exported field with
the method name by default. `calculated(type, fget, fset=None)` must define a
calculated field with the supplied type and accessors. `Serializable` must
raise `AttributeError` when assignment is attempted without a setter.

### Validation, export, and roles

`validate()` must populate the model's validated projection when every field
and model validator succeeds. It must raise `DataError` when validation fails;
the error must expose a structured `to_primitive()` projection of field and
nested-field errors without requiring a particular human-readable message.
Field validators and `validate_<field_name>(self, data, value)` model methods
must contribute their failures to that structured result.

`to_native()` must return a mapping with native Python values. `to_primitive()`
must return a mapping with field primitive values. Both methods must apply
serialized field names, calculated fields, `serialize_when_none`, and export
role rules. A role created with `whitelist(names...)` must export only the
listed fields; a role created with `blacklist(names...)` must omit the listed
fields; `wholelist(names...)` must define the corresponding complete field
list. A requested undefined role must raise an error rather than silently
exporting a different role. A model `Options.roles` mapping must supply named
roles, and an `Options.roles['default']` role must apply when callers omit the
`role` argument.

`serialize()` must export a primitive mapping after attempting validation. It
must still return the exportable projection when validation fails, and it must
restore the instance's pending input state after the call.

## Error Semantics

`ConversionError` must report a field conversion failure. `ValidationError`
must report a field validation failure. `StopValidationError` must stop the
remaining validation chain for that field. `CompoundError` and `FieldError`
must preserve nested error structure. `DataError` must report aggregated
model-data failures. `MockCreationError` must report an unsatisfiable mock
request. `UndefinedValueError` must report access to an absent declared value.
`UnknownFieldError` must report a mapping operation for an undeclared field.
`BaseError.to_primitive()` must return a serializable structured error
projection.

## Cross-View Invariants

1. A declared field value read as `instance.name` must return the same native
   value as `instance['name']` when the field is present.
2. A value assigned through `instance.name = value` must return through
   `instance['name']` and `to_native()` after conversion.
3. A value assigned through `instance['name'] = value` must return through
   `instance.name` and `to_native()` after conversion.
4. `to_native()` must return each included field under its `serialized_name`
   when that option is configured.
5. `to_primitive()` must return each included scalar field through that
   field's primitive conversion while `to_native()` returns its native value.
6. A nested model accepted by `ModelType` must return as a nested model in the
   instance projection and as a nested mapping in both export projections.
7. A role exclusion must remove the same declared field from native and
   primitive export for the requested role.
8. A `DataError.to_primitive()` result must return errors keyed by the failing
   declared field or nested position rather than a formatted exception string.

## Representative Workflow

```python
import datetime
from schematics.models import Model
from schematics.types import DateTimeType, DecimalType, StringType
from schematics.exceptions import DataError

class WeatherReport(Model):
    city = StringType(required=True)
    temperature = DecimalType()
    taken_at = DateTimeType(default=datetime.datetime.now)

report = WeatherReport({'city': 'NYC', 'temperature': '80'})
assert report.temperature == report['temperature']
assert report.to_native()['temperature'] == report.temperature
assert report.to_primitive()['temperature'] == '80'
report.validate()

try:
    WeatherReport({'temperature': '80'}, validate=True, partial=False)
except DataError as error:
    assert 'city' in error.to_primitive()
```

## Non-Goals

This specification excludes persistence backends, database integration,
network-service implementation, undocumented schema internals, private
attributes, error-message wording, object representations, and a command-line
interface. It does not require a particular storage layout or implementation
algorithm.

## Invocation Protocol

- Console script name: `TBD`
- `python -m schematics`: `not supported`
- Exit codes:
  - `0`: success
  - `1`: `python -m schematics` cannot execute because the package has no `__main__` module

## Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Implementation Guidance

Conformance checks exercise public imports, declarative model construction,
conversion, validation, error classes and structured errors, scalar and
compound type projections, mapping and attribute access, serialization roles,
calculated fields, and end-to-end model workflows. Results aggregate the
applicable behavioral checks; failure in one dimension must not alter the
required public contract in another dimension. Checks use only public behavior
described in this specification and do not require private attributes, exact
error text, representation formatting, or a particular internal design.
