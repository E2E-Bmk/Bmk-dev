# Spec2Repo oracle - atomic tests for cattrs-converters-fullrepro-001
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

    with pytest.raises(Exception):
        cattrs.structure("green", Literal["red", "blue"])


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


def test_forbidden_extra_key_error_exposes_class_and_extra_fields():
    @define
    class Model:
        value: int

    converter = Converter(forbid_extra_keys=True)

    with pytest.raises(ClassValidationError) as exc:
        converter.structure({"value": 1, "extra": 2}, Model)

    assert any(isinstance(sub, ForbiddenExtraKeysError) for sub in exc.value.exceptions)


def test_missing_structure_handler_raises_public_exception():
    class Unsupported:
        pass

    converter = Converter()

    with pytest.raises(StructureHandlerNotFoundError):
        converter.get_structure_hook(Unsupported)
