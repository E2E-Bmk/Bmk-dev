<!-- spec.md -->
# cattrs Compatibility Specification

This document is the sole source of truth. Implement a Python package named
`cattrs` for converting attrs classes, dataclasses and typed Python values to
and from dictionaries, lists, tuples, sets, scalar values and `None`.

The contract is behavioral. Private dispatch objects, generated source text,
function names, call counts, performance, traceback layout and exact error
wording are not observable.

## Core converter

`cattrs.Converter` (also exported as `BaseConverter` and `GenConverter`) owns
independent conversion rules. `structure(value, type)` recursively converts to
the requested type. `unstructure(value, unstructure_as=None)` recursively emits
plain Python data, using `unstructure_as` when supplied. The shared
`global_converter` backs top-level `structure`, `unstructure`, hook registration
and hook lookup functions.

Support:

- `Any`, scalar constructors, enums, Literal, Optional and PEP 604 unions;
- homogeneous and heterogeneous tuples, lists, deques, mappings, concrete and
  abstract sequences/sets, frozen sets, `defaultdict`, NewType and Annotated;
- attrs classes, dataclasses, NamedTuple and TypedDict;
- parameterized generic classes and TypedDicts, including nested TypeVars,
  generic inheritance, generic unions and recursive generic fields;
- dictionary and tuple class projections, aliases, defaults and factories.

Abstract `Sequence[T]` structures to a list by default. Abstract `Set[T]`
structures to a frozenset by default. `defaultdict[K,V]` retains a default
factory for `V`. TypedDict `Required` and `NotRequired` markers are honored.

## Hooks, factories and lifecycle

Exact hooks are registered with `register_structure_hook(type, hook)` and
`register_unstructure_hook(type, hook)`. Predicate hooks use the corresponding
`*_hook_func` methods. Structure hooks accept `(value, requested_type)`;
unstructure hooks accept `(value)`.

`register_structure_hook_factory(predicate, factory=None)` and
`register_unstructure_hook_factory(predicate, factory=None)` work both as
ordinary calls and decorators. A factory receives the matching type. A factory
declared with a second positional parameter also receives the owning converter.
It returns the corresponding hook.

`get_structure_hook(type, cache_result=True)` and
`get_unstructure_hook(type, cache_result=True)` return effective hooks.
`cache_result=False` requests lookup/generation without storing that result.
The returned hook must have the same behavior as conversion through the same
converter state.

Later exact registration has precedence over factory, predicate, fallback and
built-in rules. A later public rule must be visible through direct conversion,
lookup and already-used dependent composite types. Implementations may
invalidate or regenerate anything internally.

Fallbacks are supplied by `structure_fallback_factory` and
`unstructure_fallback_factory`; they compose in nested classes and collections.

`Converter.copy(**option_replacements)` preserves current exact, predicate and
factory rules plus converter options. The result is independent: later changes
to either converter do not change the other, including after composite hooks
were generated.

## Generated and collection helpers

The following public callables must be available:

```python
from cattrs.gen import (
    make_dict_structure_fn, make_dict_unstructure_fn,
    make_mapping_structure_fn,
    make_hetero_tuple_structure_fn, make_hetero_tuple_unstructure_fn,
    make_iterable_unstructure_fn,
)
from cattrs.cols import (
    is_sequence, is_set,
    namedtuple_dict_structure_factory,
    namedtuple_dict_unstructure_factory,
)
```

Generated hooks use the converter's effective nested hooks. Mapping generators
structure both keys and values. Heterogeneous tuple generators apply each
positional type. Iterable unstructure generators accept an optional output
container. NamedTuple dictionary factories use field names, defaults and nested
rules; the unstructure factory can omit default-valued fields.

Dictionary class generators accept per-field `override(...)` values and public
settings including `_cattrs_omit_if_default`, `_cattrs_forbid_extra_keys` and
`_cattrs_use_alias`. Per-field `struct_hook`, `unstruct_hook`, `rename`, `omit`
and `omit_if_default` settings take precedence over converter defaults.

## Overrides and projections

`override(rename=..., omit=..., omit_if_default=..., struct_hook=...,
unstruct_hook=...)` is exported from both `cattrs` and `cattrs.gen`.
Annotated field overrides apply to attrs classes, dataclasses and TypedDicts.

`type_overrides` supplies defaults for exact field annotations.
`unstruct_collection_overrides` selects output constructors for collection
origins while nested element hooks continue to apply. Explicit field metadata
beats converter-wide defaults. Explicit class hooks beat generated rules.

## High-level strategies

```python
from cattrs.strategies import (
    configure_tagged_union,
    configure_union_passthrough,
    include_subclasses,
    use_class_methods,
)
```

### Tagged unions

`configure_tagged_union(union, converter, tag_generator=..., tag_name="_type",
default=...)` installs structure and unstructure hooks for a union of classes.
The default tag value is the class name. Unstructuring emits the selected tag
alongside the member's dictionary. Structuring selects the member by tag. A
custom tag name and generator are supported. If `default` is supplied, missing
or unknown tags structure as that member. The strategy must work with
`forbid_extra_keys=True` without exposing its tag as an extra member field and
must compose inside optional sequences and generated classes.

### Native union passthrough

`configure_union_passthrough(union, converter,
accept_ints_as_floats=True)` configures validation-and-pass-through for native
values whose runtime classes are members of the configured union. It also
handles Literal values and NewTypes of configured bases. Subset unions are
covered. Members outside the configured native set spill into normal converter
handling, including typed collections and disambiguated attrs/dataclass
classes. Invalid native values raise `TypeError` directly or within a detailed
validation group. When configured with both int and float, ints satisfy a
float member unless `accept_ints_as_floats=False`.

### Class methods

`use_class_methods(converter, structure_method, unstructure_method)` uses named
methods when present and falls back to ordinary handling when absent. A
structure classmethod may accept `(data)` or `(data, converter)`. An unstructure
instance method may accept `()` or `(converter)`. It composes recursively.

### Subclasses

`include_subclasses(base, converter, subclasses=None, union_strategy=None)`
includes the currently known descendants of a base class. Structuring a
base-typed value selects the most specific compatible subclass from its fields;
unstructuring through a base annotation preserves subclass fields. The behavior
composes through classes, containers, explicit unions and recursive base
annotations. An optional `union_strategy` customizes the internal union, for
example a partially configured tagged-union strategy.

## Validation

Detailed validation is on by default. Independent failures inside a class,
TypedDict, iterable or mapping are retained in public exception groups:
`ClassValidationError` and `IterableValidationError`, both derived from
`BaseValidationError`. `ForbiddenExtraKeysError` represents extra keys.
`AttributeValidationNote` and `IterableValidationNote` retain field, index or
key context.

`transform_error(error, path="$", format_exception=...)` returns user-facing
messages with paths such as `$.field`, `$[0]` and mapping-key paths. It must keep
all independent leaves. Exact message wording is not required.

With `detailed_validation=False`, the first underlying error propagates.

## Public construction options

The covered `Converter` options include `detailed_validation`,
`forbid_extra_keys`, `omit_if_default`, `use_alias`,
`prefer_attrib_converters`, `unstruct_collection_overrides`, `type_overrides`,
`structure_fallback_factory`, `unstructure_fallback_factory`, and
`unstruct_strat`. `UnstructureStrategy.AS_DICT` and `.AS_TUPLE` are public.

No CLI is required. Runtime dependencies may be declared in `pyproject.toml` or
`requirements.txt`.

<!-- spec-addendum.md -->
# cattrs Compatibility Specification — v3 Addendum

This addendum and `../cattrs-loop-v2/spec.md` together form the sole public
specification for v3. The addendum clarifies existing capability families; it
does not expose tests, weights, examples from candidate implementations, or
implementation internals.

## NamedTuple dictionary factory

`namedtuple_dict_structure_factory` accepts positional controls in this order:
`(type, converter, detailed_validation="from_converter",
forbid_extra_keys=False, use_linecache=True, /, **field_overrides)`. When extra
keys are forbidden, independent extras appear as `ForbiddenExtraKeysError`
inside detailed class validation. The unstructure factory continues to accept
`omit_if_default` and per-field overrides.

## Generic completeness

All TypeVars required by a generic attrs/dataclass target must be bound by the
requested parameterization or an inherited concrete binding. Structuring an
unparameterized target with unresolved TypeVars raises
`StructureHandlerNotFoundError`; an unresolved TypeVar is not silently Any.

## Type aliases in union strategies

Both high-level union strategies accept Python 3.12 `type` aliases.
`configure_tagged_union` accepts an alias whose value is a union.
`configure_union_passthrough` recognizes alias members by their underlying
runtime base, including when mixed with Literal and None members.

For a tagged union with a default member and `forbid_extra_keys=False`, the
input mapping is passed to the default member without deleting an unknown tag.
This permits a catch-all member with a field named like the tag to observe it.
When extra keys are forbidden, the strategy may remove the tag before member
structuring so its own discriminator is not treated as an extra field.

## Subclass strategy options

`include_subclasses(base, converter, subclasses=None, union_strategy=None,
overrides=None)` accepts per-field `override(...)` values that apply to every
participating class projection. Parameterized generic bases are supported;
concrete parameters inherited by descendants remain concrete during conversion.

## Generated validation mode

`make_dict_structure_fn` accepts `_cattrs_detailed_validation`. It overrides
the converter default for the generated class hook. When false, a scalar field
conversion failure propagates its underlying exception instead of being wrapped
as a class validation group.

## Counter and attrs converters

`collections.Counter[K]` is a supported typed mapping projection. Structuring
preserves the Counter type and recursively structures its values as integers;
typed unstructuring emits an ordinary mapping with recursively unstructured
keys and values.

When `Converter(prefer_attrib_converters=True)` structures an attrs field with
an attrs field converter, that converter receives the raw field value instead
of the registered hook for the field annotation. Exact hooks still apply to
direct conversions of that annotation outside the attrs field.

<!-- spec-erratum.md -->
# cattrs Compatibility Specification — v5 Clarification

This clarification, `../cattrs-loop-v2/spec.md`, and
`../cattrs-loop-v3/spec-addendum.md` together form the final public contract.

The concrete container used to represent an abstract `collections.abc.Sequence`
is not observable. Structuring `Sequence[T]` must return a fresh ordered sequence
whose elements have been structured as `T`; either a list or tuple is valid.
Likewise, typed unstructuring through an abstract sequence/set annotation is
observed by element values, order where applicable, and recursive conversion,
not by a particular concrete sequence/set constructor.

This clarification removes an accidental contradiction between the earlier
sentence naming a list and the abstract nature of the target. Concrete targets
such as `list[T]`, `tuple[T, ...]`, `set[T]`, and `frozenset[T]` retain their
specified concrete shapes.
