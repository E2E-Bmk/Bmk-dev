# Spec2Repo oracle - integration tests for cattrs-converters-fullrepro-001
from collections import OrderedDict, deque
from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Any, Literal, NewType, Optional

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


def test_top_level_structure_and_unstructure_use_global_converter():
    @define
    class Model:
        value: int

    assert cattrs.structure({"value": "11"}, Model) == Model(11)
    assert cattrs.unstructure(Model(12)) == {"value": 12}


def test_enum_structures_from_and_unstructures_to_value():
    class Color(Enum):
        RED = "red"
        BLUE = "blue"

    assert cattrs.structure("red", Color) is Color.RED
    assert cattrs.unstructure(Color.BLUE) == "blue"


def test_attrs_class_structures_from_mapping_with_field_types():
    @define
    class Model:
        count: int
        labels: list[str]

    assert cattrs.structure({"count": "3", "labels": [1, "x"]}, Model) == Model(
        3, ["1", "x"]
    )


def test_dataclass_structures_from_mapping_with_field_types():
    @dataclass
    class Model:
        count: int
        pair: tuple[int, str]

    assert cattrs.structure({"count": "3", "pair": ["4", 5]}, Model) == Model(
        3, (4, "5")
    )


def test_as_tuple_strategy_structures_sequence_into_attrs_class():
    @define
    class Model:
        left: int
        right: list[int]

    converter = Converter(unstruct_strat=UnstructureStrategy.AS_TUPLE)

    assert converter.structure(["1", ["2", 3]], Model) == Model(1, [2, 3])


def test_unstructure_as_uses_target_type_hooks_for_nested_values():
    @define
    class Model:
        value: int

    converter = Converter()
    converter.register_unstructure_hook(int, lambda value: f"i:{value}")

    assert converter.unstructure(Model(3), unstructure_as=Model) == {"value": "i:3"}


def test_structure_hook_factory_builds_hook_for_matching_type():
    @define
    class Box:
        value: int

    converter = Converter()
    converter.register_structure_hook_factory(
        lambda target: target is Box,
        lambda target, inner: lambda value, _: Box(inner.structure(value["value"], int) + 2),
    )

    assert converter.structure({"value": "5"}, Box) == Box(7)


def test_unstructure_hook_factory_builds_hook_for_matching_type():
    @define
    class Box:
        value: int

    converter = Converter()
    converter.register_unstructure_hook_factory(
        lambda target: target is Box,
        lambda target, inner: lambda value: {"value": inner.unstructure(value.value) + 3},
    )

    assert converter.unstructure(Box(4)) == {"value": 7}


def test_get_structure_hook_matches_structure_call():
    @define
    class Model:
        value: int

    hook = cattrs.get_structure_hook(Model)

    assert hook({"value": "6"}, Model) == cattrs.structure({"value": "6"}, Model)


def test_get_unstructure_hook_matches_unstructure_call():
    @define
    class Model:
        value: int

    hook = cattrs.get_unstructure_hook(Model)

    assert hook(Model(6)) == cattrs.unstructure(Model(6))


def test_converter_hook_state_is_instance_local():
    first = Converter()
    second = Converter()
    first.register_structure_hook(int, lambda value, _: int(value) + 100)

    assert first.structure("1", int) == 101
    assert second.structure("1", int) == 1


def test_converter_copy_preserves_then_isolates_hook_state():
    original = Converter()
    original.register_structure_hook(int, lambda value, _: int(value) + 1)
    copied = original.copy()
    copied.register_structure_hook(str, lambda value, _: f"copied:{value}")

    assert copied.structure("4", int) == 5
    assert original.structure("4", int) == 5
    assert copied.structure(4, str) == "copied:4"
    assert original.structure(4, str) == "4"


def test_override_rename_maps_field_for_both_directions():
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

    assert converter.structure({"class": "8"}, Model) == Model(8)
    assert converter.unstructure(Model(9)) == {"class": 9}


def test_use_alias_true_uses_attrs_field_alias():
    @define
    class Model:
        number: int = field(alias="count")

    converter = Converter(use_alias=True)

    assert converter.structure({"count": "3"}, Model) == Model(3)
    assert converter.unstructure(Model(4)) == {"count": 4}


def test_annotated_override_rename_is_honored_by_default_converter():
    @define
    class Model:
        klass: Annotated[int, override(rename="class")]

    assert cattrs.structure({"class": "5"}, Model) == Model(5)
    assert cattrs.unstructure(Model(6)) == {"class": 6}


def test_registered_type_hook_precedes_attrs_converter_by_default():
    @define
    class Model:
        value: int = field(converter=lambda raw: int(raw) + 5)

    converter = Converter()
    converter.register_structure_hook(int, lambda raw, _: int(raw) + 100)

    assert converter.structure({"value": "1"}, Model).value == 106


def test_prefer_attrib_converters_inverts_type_hook_priority():
    @define
    class Model:
        value: int = field(converter=lambda raw: int(raw) + 5)

    converter = Converter(prefer_attrib_converters=True)
    converter.register_structure_hook(int, lambda raw, _: int(raw) + 100)

    assert converter.structure({"value": "1"}, Model).value == 6


def test_detailed_validation_groups_class_field_errors_and_paths():
    @define
    class Model:
        numbers: list[int]
        mapping: dict[str, int]

    with pytest.raises(ClassValidationError) as exc:
        cattrs.structure({"numbers": ["x"], "mapping": {"bad": "y"}}, Model)

    messages = transform_error(exc.value)
    assert "invalid value for type, expected int @ $.numbers[0]" in messages
    assert "invalid value for type, expected int @ $.mapping['bad']" in messages


def test_transform_error_accepts_custom_leaf_formatter():
    @define
    class Model:
        value: int

    def formatter(exc, _type):
        if isinstance(exc, ValueError):
            return "custom integer failure"
        return "other"

    with pytest.raises(ClassValidationError) as exc:
        cattrs.structure({"value": "bad"}, Model)

    assert transform_error(exc.value, format_exception=formatter) == [
        "custom integer failure @ $.value"
    ]


def test_nested_custom_type_hook_applies_through_attrs_list_and_mapping():
    @define
    class Model:
        numbers: list[int]
        mapping: dict[str, int]

    converter = Converter()
    converter.register_structure_hook(int, lambda value, _: int(value) + 1)

    assert converter.structure(
        {"numbers": ["1", "2"], "mapping": {"a": "3"}}, Model
    ) == Model([2, 3], {"a": 4})


def test_global_registration_affects_global_conversion_and_lookup():
    @define
    class TokenForGlobalRegistration:
        value: int

    cattrs.register_structure_hook(
        TokenForGlobalRegistration,
        lambda value, _: TokenForGlobalRegistration(int(value["value"]) + 1),
    )

    assert cattrs.structure({"value": "4"}, TokenForGlobalRegistration) == (
        TokenForGlobalRegistration(5)
    )
    assert cattrs.get_structure_hook(TokenForGlobalRegistration)(
        {"value": "5"}, TokenForGlobalRegistration
    ) == TokenForGlobalRegistration(6)


def test_structure_then_unstructure_preserves_supported_public_shape():
    @define
    class Child:
        value: int

    @define
    class Parent:
        child: Child
        values: list[int]

    converter = Converter()
    structured = converter.structure(
        {"child": {"value": "1"}, "values": ["2", 3]}, Parent
    )

    assert converter.unstructure(structured) == {
        "child": {"value": 1},
        "values": [2, 3],
    }


def test_unstructure_then_structure_reconstructs_equivalent_dataclass():
    @dataclass
    class Child:
        value: int

    @dataclass
    class Parent:
        child: Child
        values: tuple[int, str]

    converter = Converter()
    original = Parent(Child(1), (2, "3"))
    payload = converter.unstructure(original)

    assert converter.structure(payload, Parent) == original
