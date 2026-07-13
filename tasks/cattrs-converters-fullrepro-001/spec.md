# cattrs Specification

## Product Overview

cattrs converts between structured Python objects and unstructured data made from dictionaries, lists, tuples, strings, numbers, booleans and `None`. It is designed for attrs classes and dataclasses, and it composes built-in handling with user-registered hooks on converter objects.

The central object is `cattrs.Converter`. Top-level functions such as `cattrs.structure()` and `cattrs.unstructure()` use one shared global converter for convenience. Applications that need local customization should create their own `Converter` instances.

## Scope

This specification covers the converter core:

- Top-level imports from `cattrs`.
- `Converter`, `BaseConverter`, `GenConverter`, and `UnstructureStrategy`.
- Structuring and unstructuring attrs classes, dataclasses, collections, tuples, mappings, enums, `Any`, `Literal`, `Annotated`, `Optional`, and nested combinations of these types.
- Hook registration and hook lookup through public converter methods and global converter functions.
- Dictionary and tuple handling for attrs classes and dataclasses.
- Generated dictionary hook customization with `cattrs.override()`.
- Detailed and non-detailed validation errors, `transform_error()`, and public validation exception classes.

## Installable Surface

The package import name is `cattrs`.

The following names must be importable from `cattrs`:

```python
AttributeValidationNote
BaseConverter
BaseValidationError
ClassValidationError
Converter
ForbiddenExtraKeysError
GenConverter
IterableValidationError
IterableValidationNote
SimpleStructureHook
StructureHandlerNotFoundError
UnstructureStrategy
get_structure_hook
get_unstructure_hook
global_converter
override
register_structure_hook
register_structure_hook_func
register_unstructure_hook
register_unstructure_hook_func
structure
structure_attrs_fromdict
structure_attrs_fromtuple
transform_error
unstructure
```

`cattrs.gen.override` must refer to the same public override factory as `cattrs.override`. The public generated-hook factories in `cattrs.gen` are only required where needed to honor override behavior exposed through `Converter` and `override()`.

## Public API

`Converter` and `GenConverter` must be constructible with:

```python
Converter(
    dict_factory=dict,
    unstruct_strat=UnstructureStrategy.AS_DICT,
    omit_if_default=False,
    forbid_extra_keys=False,
    type_overrides={},
    unstruct_collection_overrides={},
    prefer_attrib_converters=False,
    detailed_validation=True,
    unstructure_fallback_factory=...,
    structure_fallback_factory=...,
    use_alias=False,
)
```

`BaseConverter` must accept the shared subset:

```python
BaseConverter(
    dict_factory=dict,
    unstruct_strat=UnstructureStrategy.AS_DICT,
    prefer_attrib_converters=False,
    detailed_validation=True,
    unstructure_fallback_factory=...,
    structure_fallback_factory=...,
)
```

Converters must expose these public methods:

```python
converter.structure(obj, cl)
converter.unstructure(obj, unstructure_as=None)
converter.structure_attrs_fromdict(obj, cl)
converter.structure_attrs_fromtuple(obj, cl)
converter.get_structure_hook(type, cache_result=True)
converter.get_unstructure_hook(type, cache_result=True)
converter.register_structure_hook(cl, func=None)
converter.register_unstructure_hook(cls=None, func=None)
converter.register_structure_hook_func(check_func, func)
converter.register_unstructure_hook_func(check_func, func)
converter.register_structure_hook_factory(predicate, factory)
converter.register_unstructure_hook_factory(predicate, factory)
converter.copy(**overrides)
```

The top-level functions `structure`, `unstructure`, `structure_attrs_fromdict`, `structure_attrs_fromtuple`, `register_structure_hook`, `register_structure_hook_func`, `register_unstructure_hook`, `register_unstructure_hook_func`, `get_structure_hook`, and `get_unstructure_hook` must delegate to `global_converter`.

`override()` must accept:

```python
override(
    omit_if_default=None,
    rename=None,
    omit=None,
    struct_hook=None,
    unstruct_hook=None,
)
```

and return a value usable by generated dictionary hooks and `typing.Annotated` metadata.

## Product State Model

A converter owns a set of public conversion rules. Those rules are visible through three public projections:

- Calls to `structure()` and `unstructure()`.
- Hook lookup through `get_structure_hook()` and `get_unstructure_hook()`.
- Validation exceptions and transformed validation messages from failed structuring calls.

The same converter state must drive all three projections. A hook registered on a converter must affect later conversion calls on that converter. A hook registered on one converter must not affect another converter. A hook registered through the top-level registration functions must affect the top-level conversion functions because they share `global_converter`.

`Converter.copy()` must return an independent converter initialized with the original converter's rules and any explicit constructor overrides. Mutating hooks on the copy must not mutate the original converter, and mutating hooks on the original after copying must not mutate the copy.

## Structuring

`structure(obj, cl)` must return an instance of `cl` or a value conforming to `cl`.

Primitive target types `int`, `float`, `str`, and `bytes` must structure by calling the target type. If that call fails, the original exception must propagate in non-detailed validation and must be grouped in detailed validation when the failure occurs inside a structured container or class.

`Any` must structure by returning the original object unchanged.

`Optional[T]` and `T | None` must return `None` when the input is `None`; otherwise they must structure the input as `T`. Bare `Optional` must not be treated as a useful target type.

`Literal[...]` must accept values present in the literal set and return the matching value. It must raise a cattrs error when the value is not in the literal set.

Lists and mutable sequences parameterized with `T` must structure any iterable into a new list and must structure each element as `T`. Bare list-like targets must treat their element type as `Any`.

Homogeneous tuples such as `tuple[T, ...]` must structure an iterable into a tuple and structure each element as `T`. Heterogeneous tuples such as `tuple[A, B]` must structure each position against the corresponding type and must raise when the input length does not match the number of tuple type parameters.

Sets and mutable sets must structure iterables into sets. Frozen sets and abstract sets must structure iterables into frozensets. Each element must be structured according to the element type when one is provided.

Mappings such as `dict[K, V]` and `Mapping[K, V]` must structure mapping-like input into a dictionary. Keys must be structured as `K` and values as `V`. Missing type parameters or `Any` parameters must pass through without conversion.

Enums must structure from their values. If no enum member matches, the enum constructor's exception must propagate or be grouped according to validation mode.

attrs classes and dataclasses must structure from mappings by applying field type hooks and passing the resulting values into the class initializer. Missing required fields must fail. Unknown keys must be ignored by default.

`structure_attrs_fromdict(obj, cl)` must structure attrs/dataclass fields from keys matching field names or configured aliases. `structure_attrs_fromtuple(obj, cl)` must structure attrs/dataclass fields from positional values in field order.

When `Converter(unstruct_strat=UnstructureStrategy.AS_TUPLE)` is used, structuring attrs classes and dataclasses through `converter.structure()` must accept tuple/list input in field order.

When `Converter(forbid_extra_keys=True)` is used, structuring an attrs class or dataclass from a mapping containing keys that do not correspond to accepted fields must fail with a validation error that contains `ForbiddenExtraKeysError`. A generated structure hook with `_cattrs_forbid_extra_keys=False` must override the converter default for that class and ignore extra keys.

`typing.Annotated[T, override(...)]` must structure using `T` while applying supported override metadata for attrs classes, dataclasses, TypedDicts, and dictionary-style named tuple hooks. `Annotated[T, ...]` without a cattrs override must behave like `T`.

## Unstructuring

`unstructure(obj, unstructure_as=None)` must convert a structured object into unstructured Python data. If `unstructure_as` is provided, the converter must use hooks for that target type rather than relying only on the runtime type.

Primitive values, strings, bytes, booleans, numbers, `None`, and non-attrs objects without registered hooks must pass through unchanged unless a fallback or hook changes them.

Enums must unstructure to their enum values.

Lists and list-like containers must unstructure to lists. Deques must unstructure to lists under `Converter`. Mappings must unstructure to dictionaries. Collection elements, keys, and values must be unstructured recursively when type information or runtime values require it.

attrs classes and dataclasses must unstructure to dictionaries by default, with keys matching field names or configured aliases. `UnstructureStrategy.AS_DICT` must produce dictionaries. `UnstructureStrategy.AS_TUPLE` must produce tuples in field order.

`structure()` followed by `unstructure()` must preserve the public data shape for supported attrs/dataclass models when the target field types and hooks are the same converter rules. `unstructure()` followed by `structure()` must reconstruct an equivalent object for supported models when the unstructured data contains all required fields.

## Hook Registration and Lookup

`register_structure_hook(type, hook)` must register `hook(value, type)` for the exact target or applicable type. A registered structure hook must take priority over default structuring for that type.

`register_unstructure_hook(type, hook)` must register `hook(value)` for values of that type. A registered unstructure hook must take priority over default unstructuring for that type.

Both `register_structure_hook` and `register_unstructure_hook` must work as decorators when the hook has enough type annotation information for cattrs to infer the registered type. If annotations are absent or ambiguous, callers must be able to use the explicit two-argument registration form.

`register_structure_hook_func(predicate, hook)` and `register_unstructure_hook_func(predicate, hook)` must register predicate-based hooks. When the predicate returns true for a target type, the hook must be used for that type unless a more specific later registration overrides it.

Hook factory registration must accept a predicate and a factory. The factory must receive enough converter context to produce a hook for the matching type. Generated hooks must be reused through hook lookup when caching is enabled.

`get_structure_hook(type)` and `get_unstructure_hook(type)` must return callable hooks that implement the same behavior as later calls to `structure()` and `unstructure()` for that type. For example, `cattrs.structure(value, T)` must be equivalent to `cattrs.get_structure_hook(T)(value, T)` for supported `T`.

## Attribute Overrides and Defaults

`override(rename="key")` must map an attrs/dataclass field to the unstructured dictionary key `"key"` for both structuring and unstructuring when the override is active.

`override(omit=True)` must omit the field from generated structuring and unstructuring for that class. During structuring, an omitted field must not be read from input; the class initializer or default behavior must determine whether construction succeeds.

`override(omit_if_default=True)` must omit a field during unstructuring when its value equals the field default or the value produced by its default factory. It must not affect structuring.

The class-level `_cattrs_omit_if_default=True` setting must apply to all fields that have defaults or factories. A per-field `override(omit_if_default=False)` must override the class-level setting and force that field to appear in unstructured output.

`override(struct_hook=callable)` must use the callable for that field during structuring. `override(unstruct_hook=callable)` must use the callable for that field during unstructuring.

`Converter(omit_if_default=True)` must make default-skipping the converter default for generated attrs/dataclass dictionary unstructuring hooks. Explicit generated-hook arguments and per-field overrides must take priority over the converter default.

`Converter(use_alias=True)` and generated hooks with `_cattrs_use_alias=True` must use attrs field aliases as dictionary keys when aliases are present. When alias support is not enabled, field names must be used.

`Converter(prefer_attrib_converters=False)` must prefer a registered structure hook for a field type over an attrs field converter. `Converter(prefer_attrib_converters=True)` must run the attrs field converter in preference to the registered type hook for that field.

## Validation and Error Semantics

`detailed_validation=True` must be the default. In detailed mode, structuring failures inside attrs/dataclasses, sequences, mappings, and typed containers must be collected into public validation exception groups instead of stopping at the first nested failure.

Class field failures must raise `ClassValidationError`, a subclass of `BaseValidationError`. Iterable and mapping failures must raise `IterableValidationError`, also a subclass of `BaseValidationError`.

Nested failures must carry public notes identifying the field, index, or key path. Class-field notes must be represented by `AttributeValidationNote`; iterable index/key notes must be represented by `IterableValidationNote`.

`ForbiddenExtraKeysError` must identify the target class and the set of extra input keys. In detailed validation for classes, it appears as a sub-exception inside `ClassValidationError`.

`StructureHandlerNotFoundError` must be raised when no structure hook is found for a target type and no fallback handles it.

When `detailed_validation=False`, structuring must raise the first underlying exception directly for nested conversion failures instead of grouping all failures.

`transform_error(exc, path="$", format_exception=...)` must convert `ClassValidationError` and `IterableValidationError` trees into a list of user-facing path messages. Paths must use `$` for the root, `.field` for class fields, `[index]` for sequence indexes, and `['key']` or equivalent bracket notation for mapping keys. A custom formatter must be able to replace messages for leaf exceptions.

## Cross-View Invariants

- A hook registered through `converter.register_structure_hook(T, hook)` must affect `converter.structure(value, T)` and the callable returned by `converter.get_structure_hook(T)`.
- A hook registered through `converter.register_unstructure_hook(T, hook)` must affect `converter.unstructure(value)` and the callable returned by `converter.get_unstructure_hook(T)`.
- A hook registered on one `Converter` instance must not affect another independently-created `Converter` instance.
- A hook registered through `cattrs.register_structure_hook` or `cattrs.register_unstructure_hook` must affect top-level `cattrs.structure` and `cattrs.unstructure`, because those functions use `global_converter`.
- The same `Converter` rules must apply recursively: a custom hook for `int` must be used for an `int` field nested inside a list, tuple, attrs class, dataclass, or mapping unless a more specific field override takes priority.
- An object structured from a supported dictionary and then unstructured with the same converter must produce a public unstructured representation consistent with the converter's strategy, aliases, omits, and hooks.
- A detailed validation exception raised by `structure()` must contain enough field/index/key notes for `transform_error()` to produce paths to each failing nested value.
- A copied converter must preserve behavior visible through conversion calls and hook lookup at copy time, while later registrations on the original and copy must remain independent.

## Representative Workflows

```python
from typing import Annotated
from attrs import define, Factory
import cattrs

@define
class User:
    user_id: Annotated[int, cattrs.override(rename="id")]
    name: str
    tags: list[int] = Factory(list)

converter = cattrs.Converter(omit_if_default=True)

raw = {"id": "1", "name": "Ada", "tags": ["2", 3]}
user = converter.structure(raw, User)
assert user == User(1, "Ada", [2, 3])
assert converter.unstructure(user) == {"id": 1, "name": "Ada", "tags": [2, 3]}
assert converter.unstructure(User(2, "Grace")) == {"id": 2, "name": "Grace"}
```

```python
from attrs import define, field
from cattrs import Converter

@define
class Item:
    count: int = field(converter=lambda v: int(v) + 5)

converter = Converter(prefer_attrib_converters=True)
converter.register_structure_hook(int, lambda value, _: int(value) + 100)

assert converter.structure({"count": "1"}, Item).count == 6
assert converter.structure("1", int) == 101
```

## Non-Goals

This specification does not require:

- Reproducing private dispatch table objects, private compatibility helpers, private generated function source code, or exact generated function names.
- Matching exact exception message wording, traceback formatting, or `repr()` output beyond public exception classes, attributes, and transformed path semantics.
- Implementing optional preconfigured converters for JSON, msgpack, cbor2, bson, PyYAML, tomlkit, or msgspec.
- Implementing undocumented `cattrs.cols`, `cattrs.dispatch`, `cattrs.fns`, or `cattrs.disambiguators` helpers except where public core behavior depends on them indirectly.
- Matching performance, code generation strategy, caching internals, or line numbers.

## Invocation Protocol

cattrs is a Python library. It has no required console script for the covered functionality.

`python -m cattrs` is not supported for the covered functionality.

Exit codes are not part of the covered public API because there is no covered command-line interface.

## Evaluation Notes

The tests exercise public converter behavior only. They call `cattrs` and `cattrs.gen` public imports, create attrs classes and dataclasses in test code, register hooks through public methods, and assert on returned objects, plain dictionaries/lists/tuples, public exception classes, and transformed error paths.

Tests do not require private module imports, private converter attributes, generated function source text, exact traceback text, exact exception message wording, or optional serialization backends.
