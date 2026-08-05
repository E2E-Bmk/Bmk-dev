# attrs Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

attrs is a library for building Python classes from declared fields. A class decorated with `attrs.define`, `attrs.mutable`, `attrs.frozen`, or the classic `attr.s` family receives generated initialization, representation, comparison, hashing, validation, conversion, and assignment behavior according to the declared fields and decorator options.

The central state of an attrs class is its ordered field declaration set. That field set must be visible through all public projections: generated instance behavior, `attrs.fields()` and `attrs.fields_dict()` introspection, collection conversion through `attrs.asdict()` and `attrs.astuple()`, and copy construction through `attrs.evolve()`.

## Non-Goals

- This specification does not require Private test helpers, private modules, or internal field storage names.
- This specification does not require Exact exception message text, exact `repr()` text for `Attribute` objects, or implementation-specific helper classes.
- This specification does not require Static type-checker plugin behavior, property-based testing strategies, package metadata formatting, or performance characteristics.
- This specification does not require a command-line interface. `python -m attrs` and `python -m attr` are not supported workflows.

## Representative Workflows

### Modern Data Class

```python
import attrs

@attrs.define
class User:
    login: str
    email: str
    password: str = attrs.field(repr=False)
    active: bool = attrs.field(default=True, converter=attrs.converters.to_bool)

u = User("jane", "jane@example.invalid", "secret", active="yes")
assert u.active is True
assert attrs.asdict(u, filter=attrs.filters.exclude("password")) == {
    "login": "jane",
    "email": "jane@example.invalid",
    "active": True,
}
assert attrs.evolve(u, email="new@example.invalid").login == "jane"
```

### Validated Frozen Configuration

```python
import attrs

@attrs.frozen
class Config:
    port: int = attrs.field(converter=int, validator=attrs.validators.ge(1))
    hosts: list[str] = attrs.field(factory=list)

c = Config("8080")
assert c.port == 8080
assert attrs.astuple(c) == (8080, [])
```

### Dynamic Class Creation

```python
import attrs

Point = attrs.make_class("Point", {"x": attrs.field(type=int), "y": attrs.field(default=0)})
p = Point(3)
assert attrs.fields(Point).x.type is int
assert attrs.asdict(p) == {"x": 3, "y": 0}
```

## Field Collection and Class Definition

Field collection determines which class attributes become attrs fields and in what order, driving all generated behavior.

**Annotation-based collection.** When `attrs.define` decorates a class with only annotated attributes and no unannotated `attrs.field()` declarations, annotated instance attributes must become fields. `typing.ClassVar` attributes must not become fields.

**Explicit field collection.** When any unannotated `attrs.field()` declaration is present in a class body, attrs must use explicit field declarations and must ignore annotated attributes that are not assigned an `attrs.field()` or compatible field declaration.

**Field ordering and inheritance.** Field order must follow the order in which fields are collected from bases and the class body. For attrs subclasses, inherited fields must appear before subclass fields in generated initialization, representation, comparison, `fields()`, `asdict()`, and `astuple()`. If a mandatory field without a default follows a field with a default in the same positional initializer group, class creation must raise `ValueError`. A keyword-only mandatory field must be allowed after defaults.

**External field definitions.** When `these` is supplied to `attrs.define`, it must use the supplied mapping as the field declaration set for the target class. When `init=False` is used with `these`, attrs must leave the existing initializer in place while generated representation and comparison use the declared fields.

**Dynamic class creation.** `attrs.make_class` must produce a class equivalent to declaring a class with `attrs.define` and the same field declarations, accepting either a list of field name strings or a mapping of field declarations. When `bases` is supplied, the generated class must inherit from those bases.

**Subclass hooks.** When a class defines `__attrs_init_subclass__`, attrs must call it after attrs processing completes for each subclass.

## Initialization and Defaults

The generated initializer creates instances from field values, defaults, and factories in a defined order.

**Positional and keyword arguments.** The generated initializer must accept positional arguments for non-keyword-only fields with `init=True`, keyword arguments for all initializer fields, and required keyword-only arguments for fields marked `kw_only=True` or classes declared with `kw_only=True`. Fields with `init=False` must not be accepted by the initializer; they must receive their default or factory value when one is declared.

**Argument naming.** For fields whose name starts with a single underscore, the default initializer argument name must strip the leading underscore. When `alias` is supplied to a field, it must override the initializer argument name, including for underscore-prefixed fields.

**Defaults and factories.** A direct default value must be used when no argument is provided. A `Factory` or `field(factory=callable)` must call the factory for each new instance, so mutable defaults created by factories are not shared between instances. When `Factory(callable, takes_self=True)` is used, the factory must receive the partially initialized instance.

**Decorator defaults.** A decorator default registered through `@field.default` must be called when no argument is supplied. The decorated default must receive the partially initialized instance and its result must become the field value.

**Initialization order.** The order must be: `__attrs_pre_init__` for the current class when present, then for each field in declaration order the default factory followed by converter, then all validators, then `__attrs_post_init__` for the current class when present.

**Custom initializers.** When `init=False` or auto-detection preserves a user-defined `__init__`, attrs must attach `__attrs_init__` with the initializer it would otherwise have generated, so the custom `__init__` can delegate to it.

## Generated Methods

attrs generates representation, comparison, hashing, and pattern-matching methods from the declared field set.

**Representation.** Unless disabled, an attrs class must receive a readable `__repr__` that includes the class name and fields whose `repr` option is truthy. A field with `repr=False` must be omitted.

**Equality.** When equality is enabled, instances of the same attrs class with equal participating field values must compare equal. Different attrs classes must not compare equal solely because their field values match. A field with `eq=False` must not participate in equality.

**Ordering.** When ordering is enabled, ordering comparisons must use participating fields in field order and must reject comparison with unrelated classes. A field with `order=False` must not participate in ordering.

**Hashing.** Frozen value classes with equality enabled must be hashable unless options request otherwise. Mutable classes with equality enabled must be unhashable unless unsafe hash behavior is requested.

**Slots.** `attrs.define`, `attrs.mutable`, and `attrs.frozen` must accept the documented `slots` option and default it to `True`.

**Pattern matching.** When `match_args=True`, positional structural pattern matching must use initializer fields in declaration order and must exclude keyword-only fields.

## Assignment, Frozen Classes, and Setters

`attrs.frozen` and `attrs.define(frozen=True)` must reject assignment to fields after initialization by raising `attrs.exceptions.FrozenInstanceError`. Field-level frozen setters must reject assignment to that field by raising `attrs.exceptions.FrozenAttributeError`.

For modern `attrs.define` classes, validators and converters must run on assignment by default. A converter must transform the assigned value before storage. A validator must receive the instance, the `Attribute`, and the converted value, and must reject invalid assignments by raising the validator's exception.

`attrs.setters.NO_OP` must disable class-wide assignment hooks for a field. `attrs.setters.convert` must run converters on assignment. `attrs.setters.validate` must run validators on assignment. `attrs.setters.frozen` must reject assignment. `attrs.setters.pipe(...)` must combine setters in order.

Classic `attr.s` classes must run validators and converters on initialization by default. Assignment validation or conversion for classic classes must happen only when the user configures assignment hooks.

## Validators

Validators enforce constraints on field values during initialization and, for modern classes, on assignment.

**Validator protocol.** A validator callable must receive `(instance, attribute, value)` as positional arguments. A validator must accept valid values silently and reject invalid values by raising an exception. Passing a list of validators to a field must behave like `attrs.validators.and_` over that list. A decorator validator registered through `@field.validator` must be combined with validators supplied in the field declaration.

`attrs.validators.instance_of(type_or_tuple)` must accept values that are instances of the supplied type or tuple and must raise `TypeError` for other values.

`attrs.validators.lt`, `le`, `gt`, and `ge` must enforce the corresponding numeric comparison and must raise `ValueError` when the comparison fails.

`attrs.validators.min_len(n)` and `max_len(n)` must enforce `len(value) >= n` and `len(value) <= n`. They must raise `ValueError` when the length check fails.

`attrs.validators.in_(options)` must accept values that are members of `options`. For enum classes, enum members must be accepted and unrelated values must be rejected.

`attrs.validators.optional(validator)` must accept `None` and must otherwise apply the wrapped validator. `attrs.validators.is_callable()` must accept callable values and raise `attrs.exceptions.NotCallableError` for non-callable values.

`attrs.validators.matches_re(pattern, flags=0, func=None)` must accept strings matched by the regular expression. It must raise `ValueError` for non-matching strings.

`attrs.validators.deep_iterable(member_validator, iterable_validator=None)` must first validate the iterable itself when an iterable validator is supplied and must then validate each member. `attrs.validators.deep_mapping(key_validator, value_validator, mapping_validator=None)` must validate the mapping itself when supplied, then each key and each value.

`attrs.validators.or_(...)` must accept a value if any wrapped validator accepts it and must raise `ValueError` if all wrapped validators reject it. `attrs.validators.not_(validator, msg=None, exc_types=(ValueError, TypeError))` must reject values accepted by the wrapped validator and accept values rejected with the configured exception types.

`attrs.validators.set_disabled(True)` must globally disable validators. `set_disabled(False)` must re-enable them. `attrs.validators.disabled()` must disable validators only for the dynamic extent of its context manager and must restore the previous setting afterward.

## Converters

A converter supplied to `field(converter=...)` must receive the incoming value and its return value must be stored. Converters must run before validators during initialization and assignment.

Passing a list of converters to `field(converter=...)` must behave like `attrs.converters.pipe` over that list. `attrs.converters.pipe(c1, c2, ...)` must pass the value through each converter in order.

`attrs.converters.optional(converter)` must return `None` unchanged and must apply the converter to non-`None` values. `attrs.converters.default_if_none(default=..., factory=...)` must replace `None` with the supplied default or with a fresh factory result and must leave non-`None` values unchanged.

`attrs.converters.to_bool` must convert common truthy values such as `True`, `1`, `"1"`, `"true"`, `"yes"`, `"on"`, and `"y"` to `True`, and common falsy values such as `False`, `0`, `"0"`, `"false"`, `"no"`, `"off"`, and `"n"` to `False`. It must raise `ValueError` for values outside the supported boolean vocabulary.

**Converter wrapper.** `attrs.Converter` must wrap a converter callable. When `takes_self` is `True`, the converter must receive the partially initialized instance. When `takes_field` is `True`, it must receive the `Attribute`. When both flags are `True`, the converter must receive value, instance, and field.

A converter registered through `@field.converter` must behave like a converter supplied in the field declaration.

## Metadata and Type Information

Field metadata and type annotations provide introspection and documentation for attrs fields.

**Field metadata.** Metadata supplied through a field must be exposed through the corresponding `Attribute.metadata` as a read-only mapping. attrs must not interpret metadata contents.

**Field type annotations.** Field types supplied by annotations or by `field(type=...)` must be visible through `Attribute.type`. A converter whose first argument has a type annotation must expose that input type in the generated initializer annotations. `attrs.resolve_types` must update field type metadata by resolving string annotations and forward references using the supplied global and local namespaces, and must return the class.

**Field introspection.** `attrs.fields` must return an ordered tuple-like object of `Attribute` instances for an attrs class. The result must support integer indexing and named attribute access—`fields(Cls)[0]` and `fields(Cls).field_name` must both work. `attrs.fields` must also accept an attrs instance and return the same tuple as for its class. `attrs.fields_dict` must return an ordered name-to-`Attribute` mapping using the same field objects. `attrs.has` must return `True` for attrs classes and for instances of attrs classes, and must return `False` for non-attrs classes. `attrs.validate` must re-run all validators against the current values of an attrs instance.

## Collection Conversion and Filters

Collection conversion transforms attrs instances into plain dictionaries and tuples for serialization and data exchange.

**Dictionary conversion.** `attrs.asdict` must return a dictionary whose keys are field names and whose values are field values. When `recurse=True`, nested attrs instances must be converted recursively, including attrs instances inside lists, tuples, dictionaries, and sets. When `recurse=False`, field values must be returned unchanged.

`attrs.astuple()` must return a tuple of field values in field order. When `recurse=True`, nested attrs instances must be converted recursively. When `recurse=False`, field values must be returned unchanged.

The `filter` argument to `asdict()` and `astuple()` must be called with `(attribute, value)` for each field. A truthy return value includes the field, and a falsy return value excludes it.

`attrs.filters.include(*what)` must create a filter that includes fields whose `Attribute`, field name, or value type matches an item in `what`. `attrs.filters.exclude(*what)` must create a filter that excludes matching fields and includes the rest.

The `value_serializer` argument to `asdict()` must be called with `(instance, attribute, value)` for included field values and its return value must be placed into the output.

## Copying and Evolution

Evolution creates modified copies of attrs instances while preserving the initializer contract.

**Evolve behavior.** `attrs.evolve` must return a new instance of the same class. Unchanged initializer fields must use values from the original instance. Changed values must be passed through the initializer, so converters and validators must run.

For fields whose stored name starts with an underscore and whose initializer argument strips that underscore, `evolve()` changes must use the stripped initializer name. Fields declared with `init=False` must not be changeable through `evolve()` and must raise an error when supplied.

The original instance must remain unchanged after `evolve()`.

## Classic attr Namespace

The classic `attr` namespace provides backward-compatible decorators and functions that interoperate with the modern `attrs` API.

**Classic decorators.** `attr.s`, `attr.attrs`, and `attr.attributes` must define attrs classes using classic defaults. `attr.ib`, `attr.attrib`, and `attr.attr` must declare fields. `attr.dataclass` must behave like `attr.s(auto_attribs=True)`.

Objects exposed through shared submodules must be identical enough that exceptions raised through `attrs.exceptions` are catchable through `attr.exceptions`, and validators, converters, filters, and setters are usable from either namespace with classes created through either namespace.

`attr.set_run_validators(flag)` and `attr.get_run_validators()` must control the same global validator switch as the classic API. The modern validator disabling helpers must interoperate with the same validation behavior.

## State Model

An attrs class has one public field declaration set. Every field has a declaration order, a public field name, an initializer argument name, default information, validation and conversion hooks, metadata, type metadata, and method participation flags.

The field declaration set must drive all generated behavior:

- constructor arguments must correspond to fields with `init=True`;
- instance attributes must store the converted values for declared fields;
- `fields()` and `fields_dict()` must expose the same fields in declaration order;
- `asdict()` and `astuple()` must traverse the same field order;
- `evolve()` must rebuild an instance through the same initializer semantics;
- validators and converters must observe the same field values that generated methods expose.

## Error Semantics

Decorating a class that mixes annotated fields with an unannotated field declaration in auto-attribute mode must raise `attrs.exceptions.UnannotatedAttributeError`.

Calling `attrs.fields()` or `attrs.fields_dict()` on a non-attrs class must raise `attrs.exceptions.NotAnAttrsClassError`.

Creating an instance without a required initializer argument, with an unknown initializer argument, with too many positional arguments, or without a required keyword-only argument must raise `TypeError`.

Supplying both `default=` and `factory=` for the same field must raise an error. Setting a decorator default after a default has already been set must raise `attrs.exceptions.DefaultAlreadySetError`.

Validators must raise their documented exception type for invalid values. Frozen classes and frozen fields must raise the documented frozen exception types on assignment. `attrs.evolve()` must raise an error when asked to set a non-init field or an unknown initializer argument.

## Cross-View Invariants

- A field accepted by a generated initializer must appear in `attrs.fields()` and `attrs.fields_dict()` with the same field name and declaration order.
- A value passed through the initializer must be visible through direct attribute access, equality, ordering when enabled, `asdict()`, `astuple()`, and `evolve()` unless the corresponding field option excludes that projection.
- A converter result must be the value observed by direct attribute access, validators, generated comparison, `asdict()`, `astuple()`, and assignment hooks.
- A validator failure must prevent the invalid value from becoming the stored value during initialization and during assignment validation.
- A default factory result must be unique per instance and must be visible through direct attribute access and collection conversion.
- `fields_dict(cls)[name]` must be the same field object exposed as `fields(cls).name` for that field.
- `asdict()` and `astuple()` must use the same field order as `fields()` and the generated initializer.
- `evolve()` must produce an instance whose unchanged fields match the original through all public projections and whose changed fields reflect the initializer semantics.
- The `attrs` and `attr` namespaces must agree on shared validators, converters, filters, setters, exceptions, field metadata, and collection conversion behavior.

## Public Interface

### Import Surface

The packages `attrs` and `attr` must both be importable. The modern API is imported from `attrs`; the classic compatibility API is imported from `attr`. Shared submodules exposed as public API must be importable as both `attrs.validators` and `attr.validators`, both `attrs.converters` and `attr.converters`, both `attrs.filters` and `attr.filters`, both `attrs.setters` and `attr.setters`, and both `attrs.exceptions` and `attr.exceptions`.

```python
import attrs
import attr
from attrs import (
    NOTHING, Attribute, AttrsInstance, ClassProps, Converter, Factory,
    NothingType, asdict, assoc, astuple, cmp_using, converters, define,
    evolve, exceptions, field, fields, fields_dict, filters, frozen, has,
    inspect, make_class, mutable, resolve_types, setters, validate, validators,
)
from attr import (
    s, attrs, attributes, ib, attrib, attr, dataclass,
    set_run_validators, get_run_validators,
)
import attrs.validators
import attr.validators
import attrs.converters
import attr.converters
import attrs.filters
import attr.filters
import attrs.setters
import attr.setters
import attrs.exceptions
import attr.exceptions
```

### API Catalog

| Name | Kind | Role |
|------|------|------|
| `attrs.define` | decorator | Define a modern attrs class with slots-by-default |
| `attrs.mutable` | decorator | Alias for `attrs.define` |
| `attrs.frozen` | decorator | Define a frozen (immutable) attrs class |
| `attrs.field` | function | Declare a field with validators, converters, and defaults |
| `attrs.Factory` | class | Declare a default factory for field initialization |
| `attrs.Converter` | class | Wrap a converter with optional instance/field access |
| `attrs.make_class` | function | Dynamically create an attrs class from field declarations |
| `attrs.fields` | function | Return ordered `Attribute` objects for an attrs class |
| `attrs.fields_dict` | function | Return ordered name-to-`Attribute` mapping |
| `attrs.has` | function | Test whether a class is an attrs class |
| `attrs.validate` | function | Run all validators on an attrs instance |
| `attrs.asdict` | function | Convert an attrs instance to a dictionary |
| `attrs.astuple` | function | Convert an attrs instance to a tuple |
| `attrs.evolve` | function | Create a modified copy through the class initializer |
| `attrs.resolve_types` | function | Resolve string/forward-reference field types in place |
| `attrs.NOTHING` | sentinel | Marker for unset field defaults |
| `attrs.Attribute` | class | Field descriptor holding metadata and hooks |
| `attr.s` | decorator | Define a classic attrs class |
| `attr.ib` | function | Declare a classic field |
| `attr.dataclass` | decorator | Classic decorator with `auto_attribs=True` |
| `attrs.validators` | module | Built-in field validators |
| `attrs.converters` | module | Built-in field converters |
| `attrs.filters` | module | Filters for `asdict` and `astuple` |
| `attrs.setters` | module | Assignment hook combinators |
| `attrs.exceptions` | module | Public exception types |

### CLI Entry Points

The package is used as an importable Python library. There is no console script in scope. `python -m attrs` is not supported. `python -m attr` is not supported.

When public APIs succeed, they must return the documented value or mutate the documented public state. When public APIs reject invalid input, they must raise the documented exception type. Importing public namespaces must not print to stdout or stderr.

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Compatibility covers individual field declarations and validators, interactions among initialization, conversion, validation, assignment, and collection conversion, and complete class-definition workflows. It observes only the documented `attrs`, `attr`, and shared-submodule interfaces. Private modules, generated source text, helper class names, exact internal layouts, exact error wording, and exact object representation are not part of this contract.
