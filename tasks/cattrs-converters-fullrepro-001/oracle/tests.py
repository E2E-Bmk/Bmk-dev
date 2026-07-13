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


def test_public_surface_exports_converter_core_names():
    expected = {
        "Converter",
        "BaseConverter",
        "GenConverter",
        "UnstructureStrategy",
        "structure",
        "unstructure",
        "override",
        "transform_error",
        "ClassValidationError",
        "IterableValidationError",
        "ForbiddenExtraKeysError",
    }

    assert expected <= set(cattrs.__all__)
    for name in expected:
        assert hasattr(cattrs, name)


def test_top_level_structure_and_unstructure_use_global_converter():
    @define
    class Model:
        value: int

    assert cattrs.structure({"value": "11"}, Model) == Model(11)
    assert cattrs.unstructure(Model(12)) == {"value": 12}


def test_converter_constructs_with_documented_defaults():
    converter = Converter()

    assert converter.unstruct_strat is UnstructureStrategy.AS_DICT
    assert converter.structure("7", int) == 7


def test_primitive_structure_coerces_with_target_type():
    converter = Converter()

    assert converter.structure("5", int) == 5
    assert converter.structure(5, str) == "5"
    assert converter.structure("2.5", float) == 2.5


def test_primitive_structure_propagates_conversion_failure():
    with pytest.raises(ValueError):
        cattrs.structure("not-an-int", int)


def test_any_structure_returns_original_object():
    payload = {"a": [1, 2]}

    assert cattrs.structure(payload, Any) is payload


def test_optional_accepts_none_and_structures_present_value():
    assert cattrs.structure(None, Optional[int]) is None
    assert cattrs.structure("4", Optional[int]) == 4
    assert cattrs.structure(None, int | None) is None


def test_literal_accepts_member_and_rejects_non_member():
    assert cattrs.structure("red", Literal["red", "blue"]) == "red"

    with pytest.raises(Exception) as exc:
        cattrs.structure("green", Literal["red", "blue"])
    assert exc.value.__class__.__module__.startswith("cattrs")


def test_list_structure_accepts_any_iterable_and_converts_elements():
    assert cattrs.structure(("1", 2, 3.0), list[int]) == [1, 2, 3]


def test_homogeneous_tuple_structure_converts_each_element():
    assert cattrs.structure(["1", 2, 3.0], tuple[int, ...]) == (1, 2, 3)


def test_heterogeneous_tuple_structure_uses_position_types():
    assert cattrs.structure(["1", 2, "3.5"], tuple[int, str, float]) == (
        1,
        "2",
        3.5,
    )


def test_heterogeneous_tuple_length_mismatch_fails():
    with pytest.raises(IterableValidationError):
        cattrs.structure(["1"], tuple[int, str])


def test_sets_and_frozensets_structure_to_expected_collection_type():
    assert cattrs.structure(["1", "2", "2"], set[int]) == {1, 2}
    assert cattrs.structure(["1", "2"], frozenset[int]) == frozenset({1, 2})


def test_mapping_structure_converts_keys_and_values():
    result = cattrs.structure(OrderedDict([(1, "2"), (3, "4")]), dict[str, int])

    assert result == {"1": 2, "3": 4}


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


def test_missing_required_attrs_field_raises_class_validation_error():
    @define
    class Model:
        required: int

    with pytest.raises(ClassValidationError):
        cattrs.structure({}, Model)


def test_unknown_keys_are_ignored_by_default_for_attrs_classes():
    @define
    class Model:
        value: int = 1

    assert cattrs.structure({"value": "2", "extra": "ignored"}, Model) == Model(2)


def test_forbid_extra_keys_groups_public_error():
    @define
    class Model:
        value: int = 1

    converter = Converter(forbid_extra_keys=True)

    with pytest.raises(ClassValidationError) as exc:
        converter.structure({"value": 2, "extra": 3}, Model)

    assert any(isinstance(sub, ForbiddenExtraKeysError) for sub in exc.value.exceptions)


def test_structure_attrs_fromtuple_uses_field_order():
    @define
    class Model:
        left: int
        right: str

    assert cattrs.structure_attrs_fromtuple(["1", 2], Model) == Model(1, "2")


def test_as_tuple_strategy_structures_sequence_into_attrs_class():
    @define
    class Model:
        left: int
        right: list[int]

    converter = Converter(unstruct_strat=UnstructureStrategy.AS_TUPLE)

    assert converter.structure(["1", ["2", 3]], Model) == Model(1, [2, 3])


def test_attrs_unstructure_defaults_to_dictionary():
    @define
    class Model:
        count: int
        labels: list[int]

    assert cattrs.unstructure(Model(1, [2, 3])) == {"count": 1, "labels": [2, 3]}


def test_dataclass_unstructure_defaults_to_dictionary():
    @dataclass
    class Model:
        count: int
        pair: tuple[int, str]

    assert cattrs.unstructure(Model(1, (2, "3"))) == {"count": 1, "pair": (2, "3")}


def test_as_tuple_strategy_unstructures_attrs_class_to_tuple():
    @define
    class Model:
        count: int
        labels: list[int]

    converter = Converter(unstruct_strat=UnstructureStrategy.AS_TUPLE)

    assert converter.unstructure(Model(1, [2])) == (1, [2])


def test_deque_unstructures_to_list_with_converter():
    assert Converter().unstructure(deque([1, 2, 3])) == [1, 2, 3]


def test_unstructure_as_uses_target_type_hooks_for_nested_values():
    @define
    class Model:
        value: int

    converter = Converter()
    converter.register_unstructure_hook(int, lambda value: f"i:{value}")

    assert converter.unstructure(Model(3), unstructure_as=Model) == {"value": "i:3"}


def test_explicit_structure_hook_overrides_default_for_type():
    converter = Converter()
    converter.register_structure_hook(int, lambda value, _: int(value) + 10)

    assert converter.structure("5", int) == 15


def test_explicit_unstructure_hook_overrides_default_for_type():
    converter = Converter()
    converter.register_unstructure_hook(int, lambda value: f"int:{value}")

    assert converter.unstructure(4) == "int:4"


def test_structure_hook_decorator_infers_return_type():
    converter = Converter()

    @converter.register_structure_hook
    def parse_int(value, _) -> int:
        return int(value) + 1

    assert converter.structure("4", int) == 5


def test_unstructure_hook_decorator_infers_first_argument_type():
    converter = Converter()

    @converter.register_unstructure_hook
    def dump_int(value: int) -> str:
        return f"dump:{value}"

    assert converter.unstructure(9) == "dump:9"


def test_structure_hook_func_applies_predicate_rule():
    UserId = NewType("UserId", int)
    converter = Converter()
    converter.register_structure_hook_func(
        lambda target: target is UserId, lambda value, _: UserId(int(value) + 1)
    )

    assert converter.structure("41", UserId) == UserId(42)


def test_unstructure_hook_func_applies_predicate_rule():
    UserId = NewType("UserId2", int)
    converter = Converter()
    converter.register_unstructure_hook_func(
        lambda target: target is UserId, lambda value: f"user:{int(value)}"
    )

    assert converter.unstructure(UserId(7), unstructure_as=UserId) == "user:7"


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


def test_override_omit_skips_field_when_unstructuring():
    @define
    class Model:
        value: int

    converter = Converter()
    converter.register_unstructure_hook(
        Model, make_dict_unstructure_fn(Model, converter, value=override(omit=True))
    )

    assert converter.unstructure(Model(5)) == {}


def test_override_omit_skips_input_field_when_default_exists():
    @define
    class Model:
        value: int = 3

    converter = Converter()
    converter.register_structure_hook(
        Model, make_dict_structure_fn(Model, converter, value=override(omit=True))
    )

    assert converter.structure({"value": "99"}, Model) == Model(3)


def test_omit_if_default_skips_default_factory_value():
    @define
    class Model:
        value: int
        tags: list[int] = Factory(list)

    converter = Converter()
    converter.register_unstructure_hook(
        Model,
        make_dict_unstructure_fn(
            Model, converter, tags=override(omit_if_default=True)
        ),
    )

    assert converter.unstructure(Model(1)) == {"value": 1}
    assert converter.unstructure(Model(1, [2])) == {"value": 1, "tags": [2]}


def test_class_level_omit_if_default_can_be_disabled_per_field():
    @define
    class Model:
        value: int = 1
        keep: int = 2

    converter = Converter()
    converter.register_unstructure_hook(
        Model,
        make_dict_unstructure_fn(
            Model,
            converter,
            _cattrs_omit_if_default=True,
            keep=override(omit_if_default=False),
        ),
    )

    assert converter.unstructure(Model()) == {"keep": 2}


def test_converter_omit_if_default_sets_generated_default_behavior():
    @define
    class Model:
        value: int = 1
        tags: list[int] = Factory(list)

    converter = Converter(omit_if_default=True)

    assert converter.unstructure(Model()) == {}
    assert converter.unstructure(Model(2, [])) == {"value": 2}


def test_override_struct_hook_controls_single_field():
    @define
    class Model:
        value: int

    converter = Converter()
    converter.register_structure_hook(
        Model,
        make_dict_structure_fn(
            Model, converter, value=override(struct_hook=lambda value, _: int(value) + 4)
        ),
    )

    assert converter.structure({"value": "6"}, Model) == Model(10)


def test_override_unstruct_hook_controls_single_field():
    @define
    class Model:
        value: int

    converter = Converter()
    converter.register_unstructure_hook(
        Model,
        make_dict_unstructure_fn(
            Model, converter, value=override(unstruct_hook=lambda value: value + 4)
        ),
    )

    assert converter.unstructure(Model(6)) == {"value": 10}


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


def test_non_detailed_validation_raises_first_underlying_error():
    @define
    class Model:
        value: int

    converter = Converter(detailed_validation=False)

    with pytest.raises(ValueError):
        converter.structure({"value": "not-an-int"}, Model)


def test_iterable_validation_error_is_public_error_group():
    with pytest.raises(IterableValidationError) as exc:
        cattrs.structure(["x"], list[int])

    assert isinstance(exc.value, BaseValidationError)


def test_mapping_validation_error_transform_path_contains_key():
    with pytest.raises(IterableValidationError) as exc:
        cattrs.structure({"bad": "x"}, dict[str, int])

    assert "invalid value for type, expected int @ $['bad']" in transform_error(
        exc.value
    )


def test_forbidden_extra_key_error_exposes_class_and_extra_fields():
    @define
    class Model:
        value: int

    converter = Converter(forbid_extra_keys=True)

    with pytest.raises(ClassValidationError) as exc:
        converter.structure({"value": 1, "extra": 2}, Model)

    [extra] = [sub for sub in exc.value.exceptions if isinstance(sub, ForbiddenExtraKeysError)]
    assert extra.cl is Model
    assert extra.extra_fields == {"extra"}


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


def test_missing_structure_handler_raises_public_exception():
    class Unsupported:
        pass

    converter = Converter()

    with pytest.raises(StructureHandlerNotFoundError):
        converter.get_structure_hook(Unsupported)


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
