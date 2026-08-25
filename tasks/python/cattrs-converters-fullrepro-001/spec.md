# cattrs Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

cattrs converts between structured Python objects and unstructured data made from dictionaries, lists, tuples, strings, numbers, booleans and `None`. It is designed for attrs classes and dataclasses, and it composes built-in handling with user-registered hooks on converter objects.

The central object is `cattrs.Converter`. Top-level functions such as `cattrs.structure()` and `cattrs.unstructure()` use one shared global converter for convenience. Applications that need local customization should create their own `Converter` instances.

## Non-Goals

- This specification does not require Private dispatch table objects, private compatibility helpers, private generated function source code, or exact generated function names.
- This specification does not require Exact exception message wording, traceback formatting, or `repr()` output; only public exception classes, attributes, and transformed path semantics apply.
- This specification does not require Preconfigured converters for specific serialization formats.
- This specification does not require Internal dispatch, disambiguation, or collection helper modulesexcept where public core behavior depends on them indirectly.
- This specification does not require Performance characteristics, code generation strategy, caching internals, or line numbers.

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

## Structuring

Structuring converts unstructured data into typed Python objects according to a target type and registered hooks.

**Primitive types.** `structure` must return an instance of the target type or a value conforming to it. Primitive target types `int`, `float`, `str`, and `bytes` must structure by calling the target type. If that call fails, the original exception must propagate in non-detailed validation and must be grouped in detailed validation when the failure occurs inside a structured container or class.

**Any and optional.** `Any` must structure by returning the original object unchanged. `Optional[T]` and `T | None` must return `None` when the input is `None`; otherwise they must structure the input as `T`.

**Literals.** `Literal[...]` must accept values present in the literal set and return the matching value. It must raise a cattrs error when the value is not in the literal set.

**Lists and sequences.** Lists and mutable sequences parameterized with `T` must structure any iterable into a new list and must structure each element as `T`. Bare list-like targets must treat their element type as `Any`.

**Tuples.** Homogeneous tuples such as `tuple[T, ...]` must structure an iterable into a tuple and structure each element as `T`. Heterogeneous tuples such as `tuple[A, B]` must structure each position against the corresponding type and must raise `IterableValidationError` when the input length does not match the number of tuple type parameters.

**Sets.** Sets and mutable sets must structure iterables into sets. Frozen sets and abstract sets must structure iterables into frozensets. Each element must be structured according to the element type when one is provided.

**Mappings.** Mappings such as `dict[K, V]` must structure mapping-like input into a dictionary. Keys must be structured as `K` and values as `V`. Missing type parameters or `Any` parameters must pass through without conversion.

**Enums.** Enums must structure from their values. If no enum member matches, the enum constructor's exception must propagate or be grouped according to validation mode.

**Classes.** attrs classes and dataclasses must structure from mappings by applying field type hooks and passing the resulting values into the class initializer. Missing required fields must fail with `ClassValidationError`. Unknown keys must be ignored by default.

**Dictionary and tuple structuring.** `structure_attrs_fromdict` must structure attrs/dataclass fields from keys matching field names or configured aliases. `structure_attrs_fromtuple` must structure attrs/dataclass fields from positional values in field order. When `Converter(unstruct_strat=UnstructureStrategy.AS_TUPLE)` is used, structuring attrs classes and dataclasses through `converter.structure` must accept tuple/list input in field order.

**Forbidding extra keys.** When `Converter(forbid_extra_keys=True)` is used, structuring an attrs class or dataclass from a mapping containing keys that do not correspond to accepted fields must fail with a validation error that contains `ForbiddenExtraKeysError`. A generated structure hook with `_cattrs_forbid_extra_keys=False` must override the converter default for that class and ignore extra keys.

**Annotated overrides.** `typing.Annotated[T, override(...)]` must structure using `T` while applying supported override metadata for attrs classes, dataclasses, TypedDicts, and dictionary-style named tuple hooks. `Annotated[T, ...]` without a cattrs override must behave like `T`.

## Unstructuring

Unstructuring converts typed Python objects into plain data suitable for serialization.

**Core behavior.** `unstructure` must convert a structured object into unstructured Python data. When `unstructure_as` is provided, the converter must use hooks for that target type rather than relying only on the runtime type, enabling nested custom hooks to apply.

**Primitives and enums.** Primitive values, strings, bytes, booleans, numbers, `None`, and non-attrs objects without registered hooks must pass through unchanged. Enums must unstructure to their enum values.

**Collections.** Lists and list-like containers must unstructure to lists. Deques must unstructure to lists under `Converter`. Mappings must unstructure to dictionaries. Collection elements, keys, and values must be unstructured recursively when type information or runtime values require it.

**Classes.** attrs classes and dataclasses must unstructure to dictionaries by default, with keys matching field names or configured aliases. `UnstructureStrategy.AS_DICT` must produce dictionaries. `UnstructureStrategy.AS_TUPLE` must produce tuples in field order.

**Round-trip consistency.** Structuring followed by unstructuring must preserve the public data shape for supported attrs/dataclass models when the target field types and hooks are the same converter rules. Unstructuring followed by structuring must reconstruct an equivalent object for supported models when the unstructured data contains all required fields.

## Hook Registration and Lookup

Hooks customize how specific types are structured and unstructured, and the lookup API provides access to the effective hook for any type.

**Type-based hooks.** `register_structure_hook` must register a `hook(value, type)` callable for the exact target or applicable type. A registered structure hook must take priority over default structuring for that type. `register_unstructure_hook` must register a `hook(value)` callable for values of that type. Both must work as decorators when the hook has enough type annotation information for cattrs to infer the registered type—structure hooks must infer from the return type annotation, and unstructure hooks must infer from the first argument type annotation.

**Predicate-based hooks.** `register_structure_hook_func` and `register_unstructure_hook_func` must register predicate-based hooks. When the predicate returns true for a target type, the hook must be used for that type unless a more specific later registration overrides it.

**Hook factories.** `register_structure_hook_factory` and `register_unstructure_hook_factory` must accept a predicate and a factory callable. The factory must receive the target type and the converter instance, and must produce a hook for the matching type.

**Hook lookup.** `get_structure_hook` and `get_unstructure_hook` must return callable hooks that implement the same behavior as later calls to `structure` and `unstructure` for that type. When no hook can be found for a target type, `get_structure_hook` must raise `StructureHandlerNotFoundError`.

**Generated hook functions.** `cattrs.gen.make_dict_structure_fn` and `cattrs.gen.make_dict_unstructure_fn` must generate hook functions for attrs classes and dataclasses. These functions accept per-field `override` arguments and class-level settings such as `_cattrs_omit_if_default`, `_cattrs_forbid_extra_keys`, and `_cattrs_use_alias`. Generated hooks must be suitable for registration through `register_structure_hook` and `register_unstructure_hook`.

## Attribute Overrides and Defaults

Overrides customize how individual fields are handled during structuring and unstructuring, both per-field and at the converter level.

**Renaming.** When `override(rename="key")` is active, it must map an attrs/dataclass field to the unstructured dictionary key `"key"` for both structuring and unstructuring.

**Omitting fields.** `override(omit=True)` must omit the field from generated structuring and unstructuring for that class. During structuring, an omitted field must not be read from input; the class initializer or default behavior must determine whether construction succeeds.

**Omitting defaults.** `override(omit_if_default=True)` must omit a field during unstructuring when its value equals the field default or the value produced by its default factory. It must not affect structuring.

The class-level `_cattrs_omit_if_default=True` setting must apply to all fields that have defaults or factories. A per-field `override(omit_if_default=False)` must override the class-level setting and force that field to appear in unstructured output.

**Per-field hooks.** `override(struct_hook=callable)` must use the callable for that field during structuring. `override(unstruct_hook=callable)` must use the callable for that field during unstructuring.

**Converter-level defaults.** `Converter(omit_if_default=True)` must make default-skipping the converter default for generated attrs/dataclass dictionary unstructuring hooks. When all fields have defaults and the instance uses those defaults, the unstructured result must be an empty dictionary. Explicit generated-hook arguments and per-field overrides must take priority over the converter default.

**Alias support.** When `Converter(use_alias=True)` is used or a generated hook passes `_cattrs_use_alias=True`, attrs field aliases must be used as dictionary keys for both structuring and unstructuring. When alias support is not enabled, field names must be used.

**Attrib converter priority.** When `Converter(prefer_attrib_converters=False)` is used (the default), a registered structure hook for a field type must take priority over an attrs field converter, and both must be applied in sequence. When `Converter(prefer_attrib_converters=True)` is used, the attrs field converter must run in preference to the registered type hook for that field.

## State Model

A converter owns a set of public conversion rules. Those rules are visible through three public projections:

- Calls to `structure()` and `unstructure()`.
- Hook lookup through `get_structure_hook()` and `get_unstructure_hook()`.
- Validation exceptions and transformed validation messages from failed structuring calls.

The same converter state must drive all three projections. A hook registered on a converter must affect later conversion calls on that converter. A hook registered on one converter must not affect another converter. A hook registered through the top-level registration functions must affect the top-level conversion functions because they share `global_converter`.

`Converter.copy()` must return an independent converter initialized with the original converter's rules and any explicit constructor overrides. Mutating hooks on the copy must not mutate the original converter, and mutating hooks on the original after copying must not mutate the copy.

## Error Semantics

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

## Public Interface

### Import Surface

The package import name is `cattrs`.

```python
from cattrs import (
    BaseConverter, Converter, GenConverter,
    UnstructureStrategy, SimpleStructureHook,
    AttributeValidationNote, IterableValidationNote, BaseValidationError,
    ClassValidationError, IterableValidationError, ForbiddenExtraKeysError,
    StructureHandlerNotFoundError,
    global_converter, structure, unstructure, structure_attrs_fromdict,
    structure_attrs_fromtuple, override, transform_error,
    get_structure_hook, get_unstructure_hook,
    register_structure_hook, register_structure_hook_func,
    register_unstructure_hook, register_unstructure_hook_func,
)
```

`cattrs.gen.override` must refer to the same public override factory as `cattrs.override`. The public generated-hook factories in `cattrs.gen` are only required where needed to honor override behavior exposed through `Converter` and `override()`.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| `Converter` | class | Full-featured converter with generated hooks and validation |
| `GenConverter` | class | Alias for `Converter` with generated hook support |
| `BaseConverter` | class | Minimal converter with core structuring and unstructuring |
| `UnstructureStrategy` | enum | Dict-based or tuple-based unstructuring strategy |
| `SimpleStructureHook` | class | Lightweight structure hook wrapper |
| `global_converter` | instance | Shared converter used by top-level functions |
| `structure` | function | Structure unstructured data into a typed object |
| `unstructure` | function | Unstructure a typed object into plain data |
| `structure_attrs_fromdict` | function | Structure from a dict into an attrs/dataclass |
| `structure_attrs_fromtuple` | function | Structure from a sequence into an attrs/dataclass |
| `register_structure_hook` | function | Register a type-based structure hook on the global converter |
| `register_structure_hook_func` | function | Register a predicate-based structure hook |
| `register_unstructure_hook` | function | Register a type-based unstructure hook on the global converter |
| `register_unstructure_hook_func` | function | Register a predicate-based unstructure hook |
| `get_structure_hook` | function | Look up the effective structure hook for a type |
| `get_unstructure_hook` | function | Look up the effective unstructure hook for a type |
| `override` | function | Declare per-field structuring/unstructuring overrides |
| `transform_error` | function | Convert validation exceptions to path-annotated messages |
| `BaseValidationError` | exception | Base for detailed validation failures |
| `ClassValidationError` | exception | Validation failure for class fields |
| `IterableValidationError` | exception | Validation failure for iterable/mapping elements |
| `ForbiddenExtraKeysError` | exception | Extra input keys detected with `forbid_extra_keys` |
| `StructureHandlerNotFoundError` | exception | No hook found for a target type |
| `AttributeValidationNote` | class | Path note identifying a failing class field |
| `IterableValidationNote` | class | Path note identifying a failing index or key |

### CLI Entry Points

cattrs is a Python library. It has no required console script for the covered functionality.

`python -m cattrs` is not supported for the covered functionality.

Exit codes are not part of the covered public API because there is no covered command-line interface.

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Compatibility covers structuring, unstructuring, hook registration and lookup, overrides, validation groups, transformed error paths, cross-view consistency, and round-trip workflows. It observes the documented `cattrs` and `cattrs.gen` imports, attrs classes, dataclasses, plain collection projections, and public exception classes. Private converter attributes, generated source text, tracebacks, exact exception wording, and optional serialization backends are not part of this contract.
