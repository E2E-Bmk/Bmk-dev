"""Integration tests for cattrs-converters-fullrepro-001.

Each test crosses ≥2 public API boundaries.
"""

from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Any, NewType, Optional

import pytest
from attrs import Factory, define, field

import cattrs
from cattrs import (
    BaseValidationError,
    ClassValidationError,
    Converter,
    ForbiddenExtraKeysError,
    IterableValidationError,
    StructureHandlerNotFoundError,
    UnstructureStrategy,
    override,
    transform_error,
)
from cattrs.gen import make_dict_structure_fn, make_dict_unstructure_fn


# --- State Consistency: register hook → structure/unstructure/lookup ---


def test_registered_hook_affects_structure_and_lookup():
    """Seam: state consistency between register and structure + get_hook."""
    @define
    class Token:
        v: int

    converter = Converter()
    converter.register_structure_hook(
        Token, lambda val, _: Token(int(val["v"]) + 10)
    )

    assert converter.structure({"v": "5"}, Token) == Token(15)
    hook = converter.get_structure_hook(Token)
    assert hook({"v": "3"}, Token) == Token(13)


def test_registered_hook_affects_unstructure_and_lookup():
    """Seam: state consistency between register and unstructure + get_hook."""
    @define
    class Token:
        v: int

    converter = Converter()
    converter.register_unstructure_hook(Token, lambda val: {"value": val.v * 2})

    assert converter.unstructure(Token(4)) == {"value": 8}
    hook = converter.get_unstructure_hook(Token)
    assert hook(Token(3)) == {"value": 6}


def test_hook_on_one_converter_does_not_affect_another():
    """Seam: state consistency - converter instances are isolated."""
    first = Converter()
    second = Converter()
    first.register_structure_hook(int, lambda v, _: int(v) + 100)

    assert first.structure("1", int) == 101
    assert second.structure("1", int) == 1


def test_global_registration_affects_top_level_functions():
    """Seam: state consistency between global registration and cattrs.structure."""
    @define
    class UniqueGlobalModel:
        v: int

    cattrs.register_structure_hook(
        UniqueGlobalModel, lambda val, _: UniqueGlobalModel(int(val["v"]) + 2)
    )

    assert cattrs.structure({"v": "8"}, UniqueGlobalModel) == UniqueGlobalModel(10)
    assert cattrs.get_structure_hook(UniqueGlobalModel)(
        {"v": "1"}, UniqueGlobalModel
    ) == UniqueGlobalModel(3)


# --- Protocol Handoff: nested type hooks ---


def test_custom_int_hook_applies_inside_list_field():
    """Seam: protocol handoff - type hook recurses into containers."""
    @define
    class Model:
        nums: list[int]

    converter = Converter()
    converter.register_structure_hook(int, lambda v, _: int(v) + 1)

    assert converter.structure({"nums": ["1", "2"]}, Model) == Model([2, 3])


def test_custom_int_hook_applies_inside_mapping_values():
    """Seam: protocol handoff - type hook recurses into mapping values."""
    @define
    class Model:
        data: dict[str, int]

    converter = Converter()
    converter.register_structure_hook(int, lambda v, _: int(v) + 10)

    assert converter.structure({"data": {"a": "1"}}, Model) == Model({"a": 11})


def test_custom_hook_applies_to_nested_attrs_class():
    """Seam: protocol handoff - hook for child class used in parent structuring."""
    @define
    class Inner:
        v: int

    @define
    class Outer:
        child: Inner

    converter = Converter()
    converter.register_structure_hook(
        Inner, lambda val, _: Inner(int(val["v"]) + 5)
    )

    assert converter.structure({"child": {"v": "3"}}, Outer) == Outer(Inner(8))


# --- Config Interaction: converter options ---


def test_converter_omit_if_default_omits_all_defaults():
    """Seam: config interaction between converter default and unstructure."""
    @define
    class Model:
        v: int = 0
        tags: list[int] = Factory(list)

    converter = Converter(omit_if_default=True)

    assert converter.unstructure(Model()) == {}
    assert converter.unstructure(Model(1)) == {"v": 1}


def test_class_level_omit_if_default_overridden_per_field():
    """Seam: config interaction between class-level and field-level override."""
    @define
    class Model:
        v: int = 0
        keep: int = 99

    converter = Converter()
    converter.register_unstructure_hook(
        Model,
        make_dict_unstructure_fn(
            Model, converter,
            _cattrs_omit_if_default=True,
            keep=override(omit_if_default=False),
        ),
    )

    assert converter.unstructure(Model()) == {"keep": 99}


def test_prefer_attrib_converters_true_uses_field_converter():
    """Seam: config interaction between attrib converter priority and hook."""
    @define
    class Model:
        v: int = field(converter=lambda raw: int(raw) + 5)

    converter = Converter(prefer_attrib_converters=True)
    converter.register_structure_hook(int, lambda v, _: int(v) + 100)

    assert converter.structure({"v": "1"}, Model).v == 6


def test_prefer_attrib_converters_false_applies_hook_first():
    """Seam: config interaction between default priority and hook."""
    @define
    class Model:
        v: int = field(converter=lambda raw: int(raw) + 5)

    converter = Converter()
    converter.register_structure_hook(int, lambda v, _: int(v) + 100)

    assert converter.structure({"v": "1"}, Model).v == 106


def test_use_alias_true_uses_attrs_alias():
    """Seam: config interaction between use_alias and field alias."""
    @define
    class Model:
        number: int = field(alias="count")

    converter = Converter(use_alias=True)

    assert converter.structure({"count": "4"}, Model) == Model(4)
    assert converter.unstructure(Model(5)) == {"count": 5}


def test_as_tuple_strategy_structures_from_sequence():
    """Seam: config interaction between strategy and structure input format."""
    @define
    class Model:
        a: int
        b: list[int]

    converter = Converter(unstruct_strat=UnstructureStrategy.AS_TUPLE)

    assert converter.structure(["1", ["2", 3]], Model) == Model(1, [2, 3])


# --- Override rename ---


def test_override_rename_maps_both_directions():
    """Seam: protocol handoff between rename and dict key mapping."""
    @define
    class Model:
        klass: int

    converter = Converter()
    converter.register_structure_hook(
        Model, make_dict_structure_fn(Model, converter, klass=override(rename="class"))
    )
    converter.register_unstructure_hook(
        Model, make_dict_unstructure_fn(Model, converter, klass=override(rename="class"))
    )

    assert converter.structure({"class": "9"}, Model) == Model(9)
    assert converter.unstructure(Model(10)) == {"class": 10}


def test_annotated_override_rename():
    """Seam: protocol handoff between Annotated override and key mapping."""
    @define
    class Model:
        klass: Annotated[int, override(rename="class")]

    assert cattrs.structure({"class": "7"}, Model) == Model(7)
    assert cattrs.unstructure(Model(8)) == {"class": 8}


# --- Lifecycle: converter copy ---


def test_converter_copy_preserves_and_isolates():
    """Seam: lifecycle crossing between copy and hook mutation."""
    original = Converter()
    original.register_structure_hook(int, lambda v, _: int(v) + 1)
    copied = original.copy()
    copied.register_structure_hook(str, lambda v, _: f"c:{v}")

    assert copied.structure("4", int) == 5
    assert original.structure("4", int) == 5
    assert copied.structure(7, str) == "c:7"
    assert original.structure(7, str) == "7"


# --- Error Propagation: validation groups and paths ---


def test_detailed_validation_groups_multiple_field_errors():
    """Seam: error propagation through class field structuring."""
    @define
    class Model:
        nums: list[int]
        data: dict[str, int]

    with pytest.raises(ClassValidationError) as exc:
        cattrs.structure({"nums": ["bad"], "data": {"k": "bad"}}, Model)

    paths = transform_error(exc.value)
    assert len(paths) == 2
    assert any("$.nums[0]" in p for p in paths)
    assert any("$.data" in p for p in paths)


def test_transform_error_custom_formatter():
    """Seam: error propagation through custom path formatting."""
    @define
    class Model:
        v: int

    def fmt(exc, _type):
        return "custom-msg"

    with pytest.raises(ClassValidationError) as exc:
        cattrs.structure({"v": "bad"}, Model)

    result = transform_error(exc.value, format_exception=fmt)
    assert result == ["custom-msg @ $.v"]


def test_forbidden_extra_keys_in_detailed_validation():
    """Seam: error propagation with forbidden extra keys."""
    @define
    class Model:
        v: int

    converter = Converter(forbid_extra_keys=True)
    with pytest.raises(ClassValidationError) as exc:
        converter.structure({"v": 1, "bad": 2, "worse": 3}, Model)

    assert any(isinstance(e, ForbiddenExtraKeysError) for e in exc.value.exceptions)


# --- Round-trip consistency ---


def test_structure_then_unstructure_preserves_shape():
    """Seam: state consistency between structure and unstructure."""
    @define
    class Child:
        v: int

    @define
    class Parent:
        child: Child
        values: list[int]

    converter = Converter()
    structured = converter.structure(
        {"child": {"v": "1"}, "values": ["2", 3]}, Parent
    )

    assert converter.unstructure(structured) == {
        "child": {"v": 1},
        "values": [2, 3],
    }


def test_unstructure_then_structure_reconstructs():
    """Seam: state consistency between unstructure and structure."""
    @dataclass
    class Inner:
        v: int

    @dataclass
    class Outer:
        inner: Inner
        pair: tuple[int, str]

    converter = Converter()
    original = Outer(Inner(7), (3, "x"))
    payload = converter.unstructure(original)

    assert converter.structure(payload, Outer) == original


def test_hook_factory_builds_hook_for_matching_type():
    """Seam: protocol handoff between factory predicate and hook generation."""
    @define
    class Box:
        v: int

    converter = Converter()
    converter.register_structure_hook_factory(
        lambda t: t is Box,
        lambda t, c: lambda val, _: Box(c.structure(val["v"], int) + 3),
    )

    assert converter.structure({"v": "4"}, Box) == Box(7)


def test_unstructure_hook_factory_builds_hook():
    """Seam: protocol handoff between factory and unstructure."""
    @define
    class Box:
        v: int

    converter = Converter()
    converter.register_unstructure_hook_factory(
        lambda t: t is Box,
        lambda t, c: lambda val: {"v": c.unstructure(val.v) + 2},
    )

    assert converter.unstructure(Box(5)) == {"v": 7}


# --- get_structure/unstructure_hook match calls ---


def test_get_structure_hook_matches_structure():
    """Seam: state consistency between get_hook and structure."""
    @define
    class Item:
        v: int

    hook = cattrs.get_structure_hook(Item)
    assert hook({"v": "3"}, Item) == cattrs.structure({"v": "3"}, Item)


def test_get_unstructure_hook_matches_unstructure():
    """Seam: state consistency between get_hook and unstructure."""
    @define
    class Item:
        v: int

    hook = cattrs.get_unstructure_hook(Item)
    assert hook(Item(4)) == cattrs.unstructure(Item(4))


# --- unstructure_as ---


def test_unstructure_as_applies_target_type_hooks():
    """Seam: protocol handoff between unstructure_as and hook dispatch."""
    @define
    class Item:
        v: int

    converter = Converter()
    converter.register_unstructure_hook(int, lambda v: f"i:{v}")

    assert converter.unstructure(Item(3), unstructure_as=Item) == {"v": "i:3"}
