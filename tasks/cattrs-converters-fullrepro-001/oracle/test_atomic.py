"""Atomic tests for cattrs-converters-fullrepro-001.

Each test verifies ONE public API entry point, ONE behavior.
"""

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


# --- Primitive structuring ---


def test_structure_int_from_string():
    assert cattrs.structure("12", int) == 12


def test_structure_float_from_string():
    assert cattrs.structure("3.14", float) == 3.14


def test_structure_str_from_int():
    assert cattrs.structure(99, str) == "99"


def test_structure_invalid_int_raises_value_error():
    with pytest.raises(ValueError):
        cattrs.structure("not-a-number", int)


# --- Any / Optional / Literal ---


def test_structure_any_returns_unchanged():
    payload = {"nested": [1, 2]}
    assert cattrs.structure(payload, Any) is payload


def test_structure_optional_none():
    assert cattrs.structure(None, Optional[int]) is None


def test_structure_optional_value():
    assert cattrs.structure("7", Optional[int]) == 7


def test_structure_union_none_syntax():
    assert cattrs.structure(None, int | None) is None
    assert cattrs.structure("5", int | None) == 5


def test_structure_literal_accepted_value():
    assert cattrs.structure("active", Literal["active", "inactive"]) == "active"


def test_structure_literal_rejected_value():
    with pytest.raises((ValueError, TypeError, ClassValidationError)):
        cattrs.structure("unknown", Literal["active", "inactive"])


# --- Collections ---


def test_structure_list_from_tuple_input():
    assert cattrs.structure(("1", 2, 3.0), list[int]) == [1, 2, 3]


def test_structure_homogeneous_tuple():
    assert cattrs.structure(["1", "2", "3"], tuple[int, ...]) == (1, 2, 3)


def test_structure_heterogeneous_tuple():
    assert cattrs.structure(["1", 2, "3.5"], tuple[int, str, float]) == (1, "2", 3.5)


def test_structure_heterogeneous_tuple_length_mismatch():
    with pytest.raises(IterableValidationError):
        cattrs.structure(["1"], tuple[int, str])


def test_structure_set_deduplicates():
    assert cattrs.structure(["1", "2", "2"], set[int]) == {1, 2}


def test_structure_frozenset():
    assert cattrs.structure(["3", "4"], frozenset[int]) == frozenset({3, 4})


def test_structure_mapping_converts_keys_and_values():
    result = cattrs.structure(OrderedDict([(1, "2"), (3, "4")]), dict[str, int])
    assert result == {"1": 2, "3": 4}


# --- Enum ---


def test_structure_enum_from_value():
    class Status(Enum):
        ACTIVE = "active"
        PAUSED = "paused"

    assert cattrs.structure("active", Status) is Status.ACTIVE


def test_unstructure_enum_to_value():
    class Status(Enum):
        ACTIVE = "active"
        PAUSED = "paused"

    assert cattrs.unstructure(Status.PAUSED) == "paused"


# --- Class structuring ---


def test_structure_attrs_class_from_dict():
    @define
    class Item:
        count: int

    assert cattrs.structure({"count": "5"}, Item) == Item(5)


def test_structure_missing_required_field_raises_class_validation_error():
    @define
    class Item:
        required: int

    with pytest.raises(ClassValidationError):
        cattrs.structure({}, Item)


def test_structure_ignores_unknown_keys_by_default():
    @define
    class Item:
        v: int = 1

    assert cattrs.structure({"v": "2", "extra": "x"}, Item) == Item(2)


def test_structure_attrs_fromtuple():
    @define
    class Pair:
        a: int
        b: str

    assert cattrs.structure_attrs_fromtuple(["7", 8], Pair) == Pair(7, "8")


def test_structure_dataclass_from_dict():
    @dataclass
    class Record:
        count: int
        label: str

    assert cattrs.structure({"count": "3", "label": 4}, Record) == Record(3, "4")


# --- Unstructuring ---


def test_unstructure_attrs_class_to_dict():
    @define
    class Item:
        value: int
        tags: list[int]

    assert cattrs.unstructure(Item(1, [2, 3])) == {"value": 1, "tags": [2, 3]}


def test_unstructure_dataclass_to_dict():
    @dataclass
    class Item:
        value: int

    assert cattrs.unstructure(Item(5)) == {"value": 5}


def test_unstructure_as_tuple_strategy():
    @define
    class Item:
        a: int
        b: str

    converter = Converter(unstruct_strat=UnstructureStrategy.AS_TUPLE)
    assert converter.unstructure(Item(1, "x")) == (1, "x")


def test_unstructure_deque_to_list():
    assert Converter().unstructure(deque([1, 2, 3])) == [1, 2, 3]


# --- Hook registration ---


def test_register_structure_hook_overrides_default():
    converter = Converter()
    converter.register_structure_hook(int, lambda v, _: int(v) + 50)

    assert converter.structure("3", int) == 53


def test_register_unstructure_hook_overrides_default():
    converter = Converter()
    converter.register_unstructure_hook(int, lambda v: f"n:{v}")

    assert converter.unstructure(7) == "n:7"


def test_structure_hook_decorator_infers_return_type():
    converter = Converter()

    @converter.register_structure_hook
    def hook(value, _) -> int:
        return int(value) + 1

    assert converter.structure("9", int) == 10


def test_unstructure_hook_decorator_infers_argument_type():
    converter = Converter()

    @converter.register_unstructure_hook
    def hook(value: int) -> str:
        return f"v:{value}"

    assert converter.unstructure(4) == "v:4"


def test_structure_hook_func_uses_predicate():
    UserId = NewType("UserId", int)
    converter = Converter()
    converter.register_structure_hook_func(
        lambda t: t is UserId, lambda v, _: UserId(int(v) + 5)
    )

    assert converter.structure("10", UserId) == UserId(15)


def test_unstructure_hook_func_uses_predicate():
    TagId = NewType("TagId", int)
    converter = Converter()
    converter.register_unstructure_hook_func(
        lambda t: t is TagId, lambda v: f"tag:{v}"
    )

    assert converter.unstructure(TagId(3), unstructure_as=TagId) == "tag:3"


# --- Hook lookup ---


def test_get_structure_hook_returns_callable():
    @define
    class Item:
        v: int

    hook = cattrs.get_structure_hook(Item)
    assert callable(hook)


def test_get_structure_hook_missing_type_raises():
    class Unknown:
        pass

    converter = Converter()
    with pytest.raises(StructureHandlerNotFoundError):
        converter.get_structure_hook(Unknown)


# --- Converter construction ---


def test_converter_default_strategy_is_as_dict():
    converter = Converter()
    assert converter.unstruct_strat is UnstructureStrategy.AS_DICT


def test_forbid_extra_keys_converter_raises_on_extra():
    @define
    class Item:
        v: int = 0

    converter = Converter(forbid_extra_keys=True)
    with pytest.raises(ClassValidationError) as exc:
        converter.structure({"v": 1, "extra": 2}, Item)

    assert any(isinstance(e, ForbiddenExtraKeysError) for e in exc.value.exceptions)


def test_non_detailed_validation_raises_first_error():
    @define
    class Item:
        v: int

    converter = Converter(detailed_validation=False)
    with pytest.raises(ValueError):
        converter.structure({"v": "bad"}, Item)


# --- Override in generated hooks ---


def test_override_omit_skips_field_during_unstructure():
    @define
    class Item:
        v: int

    converter = Converter()
    converter.register_unstructure_hook(
        Item, make_dict_unstructure_fn(Item, converter, v=override(omit=True))
    )

    assert converter.unstructure(Item(5)) == {}


def test_override_omit_skips_input_during_structure():
    @define
    class Item:
        v: int = 7

    converter = Converter()
    converter.register_structure_hook(
        Item, make_dict_structure_fn(Item, converter, v=override(omit=True))
    )

    assert converter.structure({"v": "99"}, Item) == Item(7)


def test_override_omit_if_default_skips_default_value():
    @define
    class Item:
        v: int
        tags: list[int] = Factory(list)

    converter = Converter()
    converter.register_unstructure_hook(
        Item, make_dict_unstructure_fn(Item, converter, tags=override(omit_if_default=True))
    )

    assert converter.unstructure(Item(1)) == {"v": 1}
    assert converter.unstructure(Item(1, [2])) == {"v": 1, "tags": [2]}


def test_override_struct_hook_per_field():
    @define
    class Item:
        v: int

    converter = Converter()
    converter.register_structure_hook(
        Item, make_dict_structure_fn(
            Item, converter, v=override(struct_hook=lambda v, _: int(v) + 7)
        )
    )

    assert converter.structure({"v": "3"}, Item) == Item(10)


def test_override_unstruct_hook_per_field():
    @define
    class Item:
        v: int

    converter = Converter()
    converter.register_unstructure_hook(
        Item, make_dict_unstructure_fn(
            Item, converter, v=override(unstruct_hook=lambda v: v * 2)
        )
    )

    assert converter.unstructure(Item(5)) == {"v": 10}


# --- Validation errors ---


def test_iterable_validation_error_is_base_validation_subclass():
    with pytest.raises(IterableValidationError) as exc:
        cattrs.structure(["bad"], list[int])

    assert isinstance(exc.value, BaseValidationError)
    assert len(transform_error(exc.value)) >= 1


def test_class_validation_error_is_base_validation_subclass():
    @define
    class Item:
        v: int

    with pytest.raises(ClassValidationError) as exc:
        cattrs.structure({"v": "bad"}, Item)

    assert isinstance(exc.value, BaseValidationError)
    assert any("$.v" in path for path in transform_error(exc.value))
