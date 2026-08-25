# Schematics Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Schematics defines declarative Python data models. A model declaration combines
field types with validation and export rules so callers receive native Python
values for program use and primitive values for interchange formats.

## Non-Goals

This specification excludes persistence backends, database integration,
network-service implementation, undocumented schema internals, private
attributes, error-message wording, object representations, and a command-line
interface. It does not require a particular storage layout or implementation
algorithm.

## Representative Workflows

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

## Model Declaration and Instance Access

This section covers how model classes are declared, how instances are constructed, and how field values are accessed, assigned, and imported.

**Class declaration.** A `Model` subclass must be declared by assigning field-type instances to class attributes. Declared-field order must remain the declaration order. A declared field must support both attribute access and mapping access on each instance.

**Instance construction.** When `raw_data` is supplied, the constructor must convert it into field-native values. When `validate` is `True`, the constructor must raise `DataError` if the supplied data violates a conversion, field, or model validation rule. When `strict` is `True` (the default), the constructor must raise `DataError` if the input contains an unrecognized key. When `partial` is `True`, the constructor must allow missing required fields without raising; when `partial` is `False`, the constructor must report missing required fields as a validation failure.

**Instance access.** Each instance must support attribute access (`instance.name`) and mapping access (`instance["name"]`), and both must return the same converted native value for a present field. `keys()`, `items()`, and `values()` must iterate over declared fields in declaration order. `get(key, default)` must return the field value or the supplied default.

**Data import.** `import_data` must accept `raw_data`, update the same instance with converted values, and return that same instance so calls can be chained.

**Assignment.** Attribute assignment (`instance.name = value`) and mapping assignment (`instance["name"] = value`) must accept declared field names and make the new value available through both access styles and through subsequent export. Mapping assignment, lookup, or deletion with an undeclared field name must raise `UnknownFieldError`. Attribute access to a declared but absent value must raise `UndefinedValueError` when no serializable value supplies that name.

**Mock generation.** `get_mock_object` must return a model instance populated with mock field values suitable for testing.

## Field Types and Conversion

This section covers the built-in field types, their conversion behavior, validation constraints, and naming options that control inbound and outbound field mapping.

**Base field behavior.** Every field must provide `to_native`, `to_primitive`, and `validate` methods. When `required` is `True`, validation must reject absent or `None` values during non-partial validation. When `default` is a literal value, it must supply that value when input omits the field. When `default` is a callable, it must be freshly evaluated for each model instance. When `choices` is set, validation must reject values not in the supplied set. Each supplied validator function must reject invalid converted values by raising `ValidationError`.

**Field naming.** When `serialized_name` is set, native and primitive export must use that name instead of the declared attribute name. When `deserialize_from` is set, the field must accept that alternate inbound key. When an input contains the declared field name, the `serialized_name`, and the `deserialize_from` name simultaneously, conversion must use the declared field name. When the input lacks the declared name but contains both alternate names, conversion must use the `serialized_name` value.

**String fields.** `StringType` must produce Unicode text and must raise `ConversionError` for values it cannot coerce (e.g. converting an integer to its text form must succeed). When `min_length` is set, validation must reject values shorter than the minimum. When `max_length` is set, validation must reject values longer than the maximum. When `regex` is set, validation must reject values that do not match the pattern.

**Numeric fields.** `IntType` must convert accepted numeric text to an integer. `LongType` must behave as the integer variant. `FloatType` must convert numeric text to a floating-point value. `DecimalType` must return `decimal.Decimal` values natively and strings primitively. All numeric types must raise `ConversionError` for unconvertible input. When `min_value` or `max_value` is set, validation must raise `ValidationError` for out-of-range values.

**Boolean fields.** `BooleanType` must accept booleans, integer values `0` and `1`, and the strings `"True"`, `"true"`, `"1"`, `"False"`, `"false"`, and `"0"`. It must raise `ConversionError` for any other value.

**Date and time fields.** `DateType` must produce `datetime.date` values natively and ISO date strings primitively. It must raise `ConversionError` for input it cannot parse. `DateTimeType` must produce `datetime.datetime` values natively and ISO-8601 strings primitively. It must parse ISO text such as `"2024-02-03T04:05:06"` into the corresponding datetime, and a round-trip through `to_primitive` followed by `to_native` must recover the original value. It must raise `ConversionError` for input it cannot parse or timezone policy it rejects. `UTCDateTimeType` must normalize to UTC as a naive native datetime (converting offset-aware input to the equivalent UTC time) and must emit an ISO-8601 value ending with `Z`. `TimestampType` must emit a Unix timestamp. `TimedeltaType` must convert a numeric value to `datetime.timedelta` using the configured `precision`, which must support at least `"seconds"` (the default), `"minutes"`, and `"days"` as valid unit values. It must raise `ConversionError` for unconvertible input.

**Identity and hash fields.** `UUIDType` must produce `uuid.UUID` values natively and strings primitively. `HashType`, `MD5Type`, and `SHA1Type` must reject malformed hash values through `ConversionError` or `ValidationError`. `MD5Type` must accept a correctly-sized 32-character hex digest and must reject values with the wrong digest length. `SHA1Type` must enforce its respective fixed digest length.

**Network and address fields.** `IPAddressType`, `IPv4Type`, `IPv6Type`, `MACAddressType`, `URLType`, and `EmailType` must reject malformed values with `ValidationError` or `ConversionError`. `URLType` must apply FQDN checking when `fqdn` is `True` and must reject an unreachable URL when `verify_exists` is `True`.

**Geographic fields.** `GeoPointType` must accept a two-element numeric list, tuple, or mapping and must raise `ConversionError` for another shape or value kind. It must raise `ValidationError` for coordinates outside latitude/longitude bounds.

**Multilingual fields.** `MultilingualStringType` must store a locale-to-text mapping. Primitive export must select the first available locale from `app_data['locale']` followed by `default_locale`. It must raise `ConversionError` when neither source supplies a locale or no selected locale exists in the mapping. It must raise `ValidationError` when locale names or localized values violate configured constraints.

**Compound fields.** `ModelType` must accept its model class or a model-name string. It must convert a mapping into the specified model and must accept an existing instance of that model. It must raise `ConversionError` for input that is neither a mapping nor a model instance (such as an integer). `ListType` must convert each element with its nested field and must raise a nested error for an invalid element. When `min_size` or `max_size` is set, validation must raise `ValidationError` when the element count violates the constraint. A `ListType` wrapping a `ModelType` must export each nested model as a mapping in the primitive projection. `DictType` must convert each mapping value through its nested field and must raise `ConversionError` for non-mapping input.

**Polymorphic and union fields.** `PolyModelType` must accept only its configured model family and must raise a conversion error when no configured model claims the input. `UnionType` must resolve a value through one configured type and must raise `ConversionError` when no configured type accepts it.

**Calculated fields.** `serializable` must decorate a model method as a calculated exported field with the method name by default. `calculated` must define a calculated field with the supplied type and accessors. `Serializable` must raise `AttributeError` when assignment is attempted without a setter.

## Validation, Export, and Roles

This section covers model validation, native and primitive export, role-based field filtering, and the serialize convenience method.

**Validation.** `validate()` must check every field and model validator. When all succeed, the model's validated projection must be populated. When validation fails, it must raise `DataError` with a structured `to_primitive()` projection of field and nested-field errors. Field validators and model-level `validate_<field_name>` methods must contribute their failures to that structured result. When a `ModelType` field contains an invalid nested model, the structured error must include the nested field's key (e.g. `"child"`) in the top-level error mapping.

**Native and primitive export.** `to_native()` must return a mapping with native Python values. `to_primitive()` must return a mapping with field primitive values. Both methods must apply `serialized_name` when configured, include calculated fields, and respect `serialize_when_none` and export role rules. A literal `default` must appear in native export when the input omits the field (e.g. a default of `3` must produce `3` in `to_native()`).

**Roles.** A role created with `whitelist(names...)` must export only the listed fields. A role created with `blacklist(names...)` must omit the listed fields from both native and primitive export. `wholelist(names...)` must define the corresponding complete field list. A model's `Options.roles` mapping must supply named roles. When `Options.roles` contains a `"default"` entry, that role must apply when callers omit the `role` argument from `to_native()` or `to_primitive()`. When a named role is applied, both `to_native()` and `to_primitive()` must produce the same field set (respecting `serialized_name`). A requested undefined role must raise an error rather than silently exporting a different role.

**Serialization.** `serialize()` must export a primitive mapping after attempting validation. It must still return the exportable projection when validation fails, and it must restore the instance's pending input state after the call.

## State Model

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

## Public Interface

### Import Surface

Install the `schematics` package.

```python
from schematics import Model
from schematics.models import Model
from schematics.types import (
    BaseType, UUIDType, StringType, MultilingualStringType, NumberType,
    IntType, LongType, FloatType, DecimalType, HashType, MD5Type, SHA1Type,
    BooleanType, GeoPointType, DateType, DateTimeType, UTCDateTimeType,
    TimestampType, TimedeltaType, CompoundType, MultiType, ModelType,
    ListType, DictType, PolyModelType, calculated, serializable, Serializable,
    IPAddressType, IPv4Type, IPv6Type, MACAddressType, URLType, EmailType,
    UnionType,
)
from schematics.exceptions import (
    BaseError, ErrorMessage, FieldError, ConversionError, ValidationError,
    StopValidationError, CompoundError, DataError, MockCreationError,
    UndefinedValueError, UnknownFieldError,
)
from schematics.transforms import wholelist, whitelist, blacklist
```

No command-line interface is provided.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| Model | class | Declarative data model with fields and validation |
| BaseType | class | Base field type for all field declarations |
| StringType | class | Unicode text field |
| IntType | class | Integer field |
| LongType | class | Long integer field |
| FloatType | class | Floating-point field |
| DecimalType | class | Decimal field with string primitive |
| BooleanType | class | Boolean field |
| UUIDType | class | UUID field |
| DateType | class | Date field |
| DateTimeType | class | Datetime field with ISO-8601 output |
| UTCDateTimeType | class | UTC-normalized datetime field |
| TimestampType | class | Unix timestamp field |
| TimedeltaType | class | Timedelta field |
| GeoPointType | class | Geographic coordinate field |
| HashType | class | Hash digest field |
| MD5Type | class | MD5 hash field |
| SHA1Type | class | SHA1 hash field |
| IPAddressType | class | IP address field |
| URLType | class | URL field with optional FQDN validation |
| EmailType | class | Email address field |
| MultilingualStringType | class | Locale-to-text mapping field |
| ModelType | class | Nested model field |
| ListType | class | List of typed elements |
| DictType | class | Dictionary with typed values |
| PolyModelType | class | Polymorphic model field |
| UnionType | class | Multi-type union field |
| serializable | decorator | Mark a method as a calculated exported field |
| calculated | function | Define a calculated field with type and accessors |
| whitelist | function | Create an export role including listed fields |
| blacklist | function | Create an export role excluding listed fields |
| wholelist | function | Define a complete field list for a role |

### CLI Entry Points

There is no console script for this package. `python -m schematics` is not supported. Programmatic use is through Python imports.


## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Conformance checks exercise public imports, declarative model construction,
conversion, validation, error classes and structured errors, scalar and
compound type projections, mapping and attribute access, serialization roles,
calculated fields, and end-to-end model workflows. Results aggregate the
applicable behavioral checks; failure in one dimension must not alter the
required public contract in another dimension. Checks use only public behavior
described in this specification and do not require private attributes, exact
error text, representation formatting, or a particular internal design.
