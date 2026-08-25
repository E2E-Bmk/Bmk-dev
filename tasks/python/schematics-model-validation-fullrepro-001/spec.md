<!-- clauses.md -->
# Clause anchors for schematics-model-validation-fullrepro-001

| clause_id | section | clause |
|---|---|---|
| SCHEMATICS-PSM-001 | Product State Model | The instance projection must return the same native field value through attribute and mapping lookup. |
| SCHEMATICS-PSM-002 | Product State Model | A value written through either access style must appear in subsequent native and primitive export. |
| SCHEMATICS-PSM-003 | Product State Model | A field excluded by a role must be absent from both export projections for that role. |
| SCHEMATICS-PSM-004 | Product State Model | A conversion or validation failure must raise its documented error and must not present the invalid value as successfully validated. |
| SCHEMATICS-MDAC-001 | Model declarations and construction | Declared-field order must remain the declaration order. |
| SCHEMATICS-MDAC-002 | Model declarations and construction | A declared field must support attribute access and mapping access on each instance. |
| SCHEMATICS-MDAC-003 | Model declarations and construction | The constructor must convert supplied `raw_data` into the field-native values. |
| SCHEMATICS-MDAC-004 | Model declarations and construction | It must raise `DataError` when `validate=True` and supplied data violates a conversion, field, or model validation rule. |
| SCHEMATICS-MDAC-005 | Model declarations and construction | It must raise `DataError` when `strict=True` and the input contains an unrecognized key. |
| SCHEMATICS-MDAC-006 | Model declarations and construction | It must return an instance without required-field failure when validation is not requested or when partial validation is requested. |
| SCHEMATICS-MDAC-007 | Model declarations and construction | Each instance must expose `validate(partial=False, convert=True, app_data=None, **kwargs)`, `import_data(raw_data, recursive=False, **kwargs)`, `to_native(role=None, app_data=None, **kwargs)`, `to_primitive(role=None, app_data=None, **kwargs)`, `serialize(*args, **kwargs)`, `export(field_converter=None, role=None, app_data=None, **kwargs)`, `keys()`, `items()`, `values()`, `get(key, default=None)`, and `get_mock_object(context=None, overrides={})`. |
| SCHEMATICS-MDAC-008 | Model declarations and construction | `import_data` must update the same instance and return that instance. |
| SCHEMATICS-MDAC-009 | Model declarations and construction | Attribute assignment and `instance[field_name] = value` must accept declared field names. |
| SCHEMATICS-MDAC-010 | Model declarations and construction | Mapping assignment, lookup, or deletion with an undeclared field name must raise `UnknownFieldError`. |
| SCHEMATICS-MDAC-011 | Model declarations and construction | Attribute access to a declared but absent value must raise `UndefinedValueError` when no serializable value supplies that name. |
| SCHEMATICS-FOAST-001 | Field options and scalar types | Every field must provide `to_native(value, context=None)`, `to_primitive(value, context=None)`, and `validate(value, context=None)`. |
| SCHEMATICS-FOAST-002 | Field options and scalar types | `required=True` must reject absent or `None` values during non-partial validation. |
| SCHEMATICS-FOAST-003 | Field options and scalar types | `default` must supply a literal value or a newly evaluated callable result when input omits the field. |
| SCHEMATICS-FOAST-004 | Field options and scalar types | `choices` and each supplied validator must reject invalid converted values by raising `ValidationError`. |
| SCHEMATICS-FOAST-005 | Field options and scalar types | `serialized_name` must name the field in native and primitive export. |
| SCHEMATICS-FOAST-006 | Field options and scalar types | `deserialize_from` must supply alternate inbound keys. |
| SCHEMATICS-FOAST-007 | Field options and scalar types | When an input contains the declared field name, its `serialized_name`, and its `deserialize_from` name at once, conversion must use the declared field name; when it lacks that name but contains both alternate names, conversion must use `serialized_name`. |
| SCHEMATICS-FOAST-008 | Field options and scalar types | `StringType(regex=None, max_length=None, min_length=None, **kwargs)` must produce Unicode text and must raise `ConversionError` for values it cannot coerce. |
| SCHEMATICS-FOAST-009 | Field options and scalar types | It must raise `ValidationError` when a converted value violates its length or regular-expression constraint. |
| SCHEMATICS-FOAST-010 | Field options and scalar types | `NumberType(min_value=None, max_value=None, strict=False, **kwargs)` and its `IntType`, `LongType`, `FloatType`, and `DecimalType` variants must convert accepted numeric input and must raise `ConversionError` for unconvertible input or `ValidationError` for out-of-range values. |
| SCHEMATICS-FOAST-011 | Field options and scalar types | `LongType` must behave as the integer variant. |
| SCHEMATICS-FOAST-012 | Field options and scalar types | `DecimalType` must return `decimal.Decimal` values natively and strings primitively. |
| SCHEMATICS-FOAST-013 | Field options and scalar types | `BooleanType` must accept booleans, `0`/`1`, and the strings `"True"`, `"true"`, `"1"`, `"False"`, `"false"`, and `"0"`; it must raise `ConversionError` for other values. |
| SCHEMATICS-FOAST-014 | Field options and scalar types | `UUIDType` must produce `uuid.UUID` values natively and strings primitively. |
| SCHEMATICS-FOAST-015 | Field options and scalar types | `DateType` must produce `datetime.date` values and ISO date strings. |
| SCHEMATICS-FOAST-016 | Field options and scalar types | `DateTimeType` must produce `datetime.datetime` values and ISO-8601 strings, and it must raise `ConversionError` for input it cannot parse or timezone policy it rejects. |
| SCHEMATICS-FOAST-017 | Field options and scalar types | `UTCDateTimeType` must normalize to UTC as a naive native datetime and emit an ISO-8601 value with `Z`. |
| SCHEMATICS-FOAST-018 | Field options and scalar types | `TimestampType` must emit a Unix timestamp. |
| SCHEMATICS-FOAST-019 | Field options and scalar types | `TimedeltaType(precision='seconds', **kwargs)` must convert supported numeric unit values to `datetime.timedelta` and must raise `ConversionError` for unconvertible input. |
| SCHEMATICS-FOAST-020 | Field options and scalar types | `GeoPointType` must accept a two-element numeric list, tuple, or mapping and must raise `ConversionError` for another shape or value kind and `ValidationError` for coordinates outside latitude/longitude bounds. |
| SCHEMATICS-FOAST-021 | Field options and scalar types | `HashType`, `MD5Type`, and `SHA1Type` must reject malformed hash values through `ConversionError` or `ValidationError`; `MD5Type` and `SHA1Type` must enforce their respective fixed digest lengths. |
| SCHEMATICS-FOAST-022 | Field options and scalar types | `IPAddressType`, `IPv4Type`, `IPv6Type`, `MACAddressType`, `URLType`, and `EmailType` must reject malformed values with `ValidationError` or `ConversionError`. |
| SCHEMATICS-FOAST-023 | Field options and scalar types | `URLType(fqdn=True, verify_exists=False, **kwargs)` must apply FQDN checking when `fqdn=True` and must reject an unreachable URL when `verify_exists=True`. |
| SCHEMATICS-FOAST-024 | Field options and scalar types | `MultilingualStringType(regex=None, max_length=None, min_length=None, default_locale=None, locale_regex=..., **kwargs)` must store a locale-to-text mapping. |
| SCHEMATICS-FOAST-025 | Field options and scalar types | Primitive export must select the first available locale from `app_data['locale']` followed by `default_locale`; it must raise `ConversionError` when neither source supplies a locale or no selected locale exists in the mapping. |
| SCHEMATICS-FOAST-026 | Field options and scalar types | It must raise `ValidationError` when locale names or localized values violate configured constraints. |
| SCHEMATICS-CACF-001 | Compound and calculated fields | `ModelType(model_spec, **kwargs)` must accept its model class or a model-name string. |
| SCHEMATICS-CACF-002 | Compound and calculated fields | It must convert a mapping into the specified model and must accept an instance of that model; it must raise `ConversionError` for another input kind. |
| SCHEMATICS-CACF-003 | Compound and calculated fields | `ListType(field, min_size=None, max_size=None, **kwargs)` must convert each element with its nested field and must raise a nested error for an invalid element or `ValidationError` when length constraints fail. |
| SCHEMATICS-CACF-004 | Compound and calculated fields | `DictType(field, coerce_key=None, **kwargs)` must convert each mapping value through its nested field and must raise `ConversionError` for non-mapping input. |
| SCHEMATICS-CACF-005 | Compound and calculated fields | `PolyModelType` must accept only its configured model family and must raise a conversion error when no configured model claims the input. |
| SCHEMATICS-CACF-006 | Compound and calculated fields | `UnionType(types=None, resolver=None, **kwargs)` must resolve a value through one configured type and must raise `ConversionError` when no configured type accepts it. |
| SCHEMATICS-CACF-007 | Compound and calculated fields | `serializable` must decorate a model method as a calculated exported field with the method name by default. |
| SCHEMATICS-CACF-008 | Compound and calculated fields | `calculated(type, fget, fset=None)` must define a calculated field with the supplied type and accessors. |
| SCHEMATICS-CACF-009 | Compound and calculated fields | `Serializable` must raise `AttributeError` when assignment is attempted without a setter. |
| SCHEMATICS-VEAR-001 | Validation, export, and roles | `validate()` must populate the model's validated projection when every field and model validator succeeds. |
| SCHEMATICS-VEAR-002 | Validation, export, and roles | It must raise `DataError` when validation fails; the error must expose a structured `to_primitive()` projection of field and nested-field errors without requiring a particular human-readable message. |
| SCHEMATICS-VEAR-003 | Validation, export, and roles | Field validators and `validate_<field_name>(self, data, value)` model methods must contribute their failures to that structured result. |
| SCHEMATICS-VEAR-004 | Validation, export, and roles | `to_native()` must return a mapping with native Python values. |
| SCHEMATICS-VEAR-005 | Validation, export, and roles | `to_primitive()` must return a mapping with field primitive values. |
| SCHEMATICS-VEAR-006 | Validation, export, and roles | Both methods must apply serialized field names, calculated fields, `serialize_when_none`, and export role rules. |
| SCHEMATICS-VEAR-007 | Validation, export, and roles | A role created with `whitelist(names...)` must export only the listed fields; a role created with `blacklist(names...)` must omit the listed fields; `wholelist(names...)` must define the corresponding complete field list. |
| SCHEMATICS-VEAR-008 | Validation, export, and roles | A requested undefined role must raise an error rather than silently exporting a different role. |
| SCHEMATICS-VEAR-009 | Validation, export, and roles | A model `Options.roles` mapping must supply named roles, and an `Options.roles['default']` role must apply when callers omit the `role` argument. |
| SCHEMATICS-VEAR-010 | Validation, export, and roles | `serialize()` must export a primitive mapping after attempting validation. |
| SCHEMATICS-VEAR-011 | Validation, export, and roles | It must still return the exportable projection when validation fails, and it must restore the instance's pending input state after the call. |
| SCHEMATICS-ES-001 | Error Semantics | `ConversionError` must report a field conversion failure. |
| SCHEMATICS-ES-002 | Error Semantics | `ValidationError` must report a field validation failure. |
| SCHEMATICS-ES-003 | Error Semantics | `StopValidationError` must stop the remaining validation chain for that field. |
| SCHEMATICS-ES-004 | Error Semantics | `CompoundError` and `FieldError` must preserve nested error structure. |
| SCHEMATICS-ES-005 | Error Semantics | `DataError` must report aggregated model-data failures. |
| SCHEMATICS-ES-006 | Error Semantics | `MockCreationError` must report an unsatisfiable mock request. |
| SCHEMATICS-ES-007 | Error Semantics | `UndefinedValueError` must report access to an absent declared value. |
| SCHEMATICS-ES-008 | Error Semantics | `UnknownFieldError` must report a mapping operation for an undeclared field. |
| SCHEMATICS-ES-009 | Error Semantics | `BaseError.to_primitive()` must return a serializable structured error projection. |
| SCHEMATICS-CVI-001 | Cross-View Invariants | A declared field value read as `instance.name` must return the same native value as `instance['name']` when the field is present. 2. |
| SCHEMATICS-CVI-002 | Cross-View Invariants | A value assigned through `instance.name = value` must return through `instance['name']` and `to_native()` after conversion. 3. |
| SCHEMATICS-CVI-003 | Cross-View Invariants | A value assigned through `instance['name'] = value` must return through `instance.name` and `to_native()` after conversion. 4. |
| SCHEMATICS-CVI-004 | Cross-View Invariants | `to_native()` must return each included field under its `serialized_name` when that option is configured. 5. |
| SCHEMATICS-CVI-005 | Cross-View Invariants | `to_primitive()` must return each included scalar field through that field's primitive conversion while `to_native()` returns its native value. 6. |
| SCHEMATICS-CVI-006 | Cross-View Invariants | A nested model accepted by `ModelType` must return as a nested model in the instance projection and as a nested mapping in both export projections. 7. |
| SCHEMATICS-CVI-007 | Cross-View Invariants | A role exclusion must remove the same declared field from native and primitive export for the requested role. 8. |
| SCHEMATICS-CVI-008 | Cross-View Invariants | A `DataError.to_primitive()` result must return errors keyed by the failing declared field or nested position rather than a formatted exception string. |

<!-- spec.md -->
# Schematics Specification


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

The package must be installable through a standard Python packaging workflow.

<!-- spec-addendum-v1.md -->
# Schematics lifecycle and nested-model semantics

This addendum clarifies the observable behavior of validation, calculated fields,
nested roles, and serialization state. It forms part of the package contract.

## Validation pipeline

- A field-level validator may be supplied with a type through the public
  `validators` argument. Validators run after the field has converted its input.
- A model may define a `validate_<field>` method. It receives the converted field
  value and may return a replacement value.
- Failures from ordinary fields, field-level validators, and `validate_<field>`
  methods are aggregated into a structured `DataError` message instead of being
  discarded after the first failing field.

## Nested structured errors

- Errors from `ModelType` preserve the nested field structure in
  `DataError.messages`.
- Errors from `ListType(ModelType(...))` preserve both the list index and the
  nested field structure.

## Calculated fields

- A field whose `serialized_name` names a `calculate_<field>` method obtains its
  value from that method when validation or serialization needs the value.
- The calculated value participates in normal conversion and validation.
- Calculated values appear in native and primitive output under the configured
  serialized name.

## Roles across nested models

- A named role supplied to a model's native or primitive conversion limits the
  top-level output to that role's fields.
- The same named role is propagated through `ModelType` and through
  `ListType(ModelType(...))`, so nested output follows the corresponding role on
  the nested model.

## Serialization state restoration

- A successful serialization may update the model's serialized state.
- If a later serialization fails, the model's observable state is restored to
  the last successfully serialized state.
- If no serialization has succeeded, a failed serialization leaves the model in
  its pending pre-serialization state.

<!-- spec-addendum-v2.md -->
# Schematics composed lifecycle semantics

This addendum is part of the public contract. It clarifies how validation,
writable calculated fields, compound containers, roles, and successful
serialization compose. It specifies observable behavior only; no storage layout
or private implementation structure is required.

## Validation context and aggregation

A field validator may accept either the converted value alone or the converted
value followed by a validation context. A model `validate_<field>` method may
accept converted sibling data and the converted field value, with an optional
validation context. When `validate(..., app_data=value)` is used, that same
application data is available as `context.app_data` at both validator levels.

A field's validator chain accumulates ordinary `ValidationError` failures.
When a validator raises `StopValidationError`, failures accumulated earlier
in that field's chain and the stopping failure remain in the structured field
error, while later validators in that chain do not run.

Construction with `lazy=True` defers raw-data conversion to validation. A
later `validate()` call aggregates a deferred conversion failure with
independent field or model-validator failures in one structured `DataError`;
one branch may not hide another branch's failure.

## Writable calculated input and errors

A `serializable` or `calculated` field with a public setter is writable
input. When inbound model data supplies that field's declared or serialized
name, conversion routes the value through the setter before validation. The
backing values established by the setter participate in validation and both
export projections.

If a writable calculated setter raises a documented field error, that error is
keyed by the calculated field in `DataError`. It is aggregated with unrelated
required-field or validator failures from the same validation attempt.

A calculated field backed by `ModelType` exports a mapping in both native and
primitive projections. An explicitly requested named role is propagated into
that returned nested model exactly as it is for an ordinary `ModelType`
field.

## Roles through compound containers

Named and default roles propagate recursively through `ModelType`,
`ListType`, and `DictType`, including compositions such as a dictionary of
models and a dictionary whose values are lists of models. Native and primitive
projections apply the same role at every nested model boundary.

Each export call is independent. Alternating default and explicitly named roles
must not leak a prior call's included or excluded fields into a later call.

## Compound error paths

For a compound value that combines dictionary keys, list positions, and nested
models, `DataError.to_primitive()` preserves each public position in order:
the dictionary key, then list index, then nested declared field. Failures in
multiple dictionary entries or list positions remain present together.

## Successful serialization projection

A model validator may update the converted sibling-data mapping it receives.
When validation succeeds inside `serialize()`, that validated projection is used
for the returned primitive mapping, and calculated fields in that return value
are evaluated from the same validated projection. After `serialize()` returns,
the instance restores the pending converted state that was visible immediately
before the call; the transient validator update is not exposed as a later
instance mutation.

<!-- spec-standalone.md -->
# Schematics Specification


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

The package must be installable through a standard Python packaging workflow.

---

# Schematics lifecycle and nested-model semantics

This addendum clarifies the observable behavior of validation, calculated fields,
nested roles, and serialization state. It forms part of the package contract.

## Validation pipeline

- A field-level validator may be supplied with a type through the public
  `validators` argument. Validators run after the field has converted its input.
- A model may define a `validate_<field>` method. It receives the converted field
  value and may return a replacement value.
- Failures from ordinary fields, field-level validators, and `validate_<field>`
  methods are aggregated into a structured `DataError` message instead of being
  discarded after the first failing field.

## Nested structured errors

- Errors from `ModelType` preserve the nested field structure in
  `DataError.messages`.
- Errors from `ListType(ModelType(...))` preserve both the list index and the
  nested field structure.

## Calculated fields

- A field whose `serialized_name` names a `calculate_<field>` method obtains its
  value from that method when validation or serialization needs the value.
- The calculated value participates in normal conversion and validation.
- Calculated values appear in native and primitive output under the configured
  serialized name.

## Roles across nested models

- A named role supplied to a model's native or primitive conversion limits the
  top-level output to that role's fields.
- The same named role is propagated through `ModelType` and through
  `ListType(ModelType(...))`, so nested output follows the corresponding role on
  the nested model.

## Serialization state restoration

- A successful serialization may update the model's serialized state.
- If a later serialization fails, the model's observable state is restored to
  the last successfully serialized state.
- If no serialization has succeeded, a failed serialization leaves the model in
  its pending pre-serialization state.

---

# Schematics composed lifecycle semantics

This addendum is part of the public contract. It clarifies how validation,
writable calculated fields, compound containers, roles, and successful
serialization compose. It specifies observable behavior only; no storage layout
or private implementation structure is required.

## Validation context and aggregation

A field validator may accept either the converted value alone or the converted
value followed by a validation context. A model `validate_<field>` method may
accept converted sibling data and the converted field value, with an optional
validation context. When `validate(..., app_data=value)` is used, that same
application data is available as `context.app_data` at both validator levels.

A field's validator chain accumulates ordinary `ValidationError` failures.
When a validator raises `StopValidationError`, failures accumulated earlier
in that field's chain and the stopping failure remain in the structured field
error, while later validators in that chain do not run.

Construction with `lazy=True` defers raw-data conversion to validation. A
later `validate()` call aggregates a deferred conversion failure with
independent field or model-validator failures in one structured `DataError`;
one branch may not hide another branch's failure.

## Writable calculated input and errors

A `serializable` or `calculated` field with a public setter is writable
input. When inbound model data supplies that field's declared or serialized
name, conversion routes the value through the setter before validation. The
backing values established by the setter participate in validation and both
export projections.

If a writable calculated setter raises a documented field error, that error is
keyed by the calculated field in `DataError`. It is aggregated with unrelated
required-field or validator failures from the same validation attempt.

A calculated field backed by `ModelType` exports a mapping in both native and
primitive projections. An explicitly requested named role is propagated into
that returned nested model exactly as it is for an ordinary `ModelType`
field.

## Roles through compound containers

Named and default roles propagate recursively through `ModelType`,
`ListType`, and `DictType`, including compositions such as a dictionary of
models and a dictionary whose values are lists of models. Native and primitive
projections apply the same role at every nested model boundary.

Each export call is independent. Alternating default and explicitly named roles
must not leak a prior call's included or excluded fields into a later call.

## Compound error paths

For a compound value that combines dictionary keys, list positions, and nested
models, `DataError.to_primitive()` preserves each public position in order:
the dictionary key, then list index, then nested declared field. Failures in
multiple dictionary entries or list positions remain present together.

## Successful serialization projection

A model validator may update the converted sibling-data mapping it receives.
When validation succeeds inside `serialize()`, that validated projection is used
for the returned primitive mapping, and calculated fields in that return value
are evaluated from the same validated projection. After `serialize()` returns,
the instance restores the pending converted state that was visible immediately
before the call; the transient validator update is not exposed as a later
instance mutation.
