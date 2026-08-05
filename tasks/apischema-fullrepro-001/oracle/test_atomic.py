from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any, Literal, Mapping, NewType, Optional
from uuid import UUID

import pytest

from apischema import Undefined, UndefinedType, serialized


@dataclass
class SerializedItem:
    value: int

    @serialized
    def doubled(self) -> int:
        return self.value * 2


def test_deserialize_int_accepts_integer_data():
    from apischema import deserialize

    assert deserialize(int, 27) == 27


def test_deserialize_float_coerces_integer_value():
    from apischema import deserialize

    result = deserialize(float, 27)
    assert result == 27.0
    assert type(result) is float


def test_deserialize_optional_none_returns_none():
    from apischema import deserialize

    assert deserialize(Optional[int], None) is None


def test_deserialize_list_structures_each_element():
    from apischema import deserialize

    assert deserialize(list[int], [3, 5, 8]) == [3, 5, 8]


def test_deserialize_fixed_tuple_uses_position_types():
    from apischema import deserialize

    assert deserialize(tuple[int, str], [9, "nine"]) == (9, "nine")


def test_deserialize_mapping_structures_keys_and_values():
    from apischema import deserialize

    result = deserialize(Mapping[int, list[str]], {"7": [1, "two"]}, coerce=True)
    assert result == {7: ["1", "two"]}


def test_deserialize_literal_accepts_declared_value():
    from apischema import deserialize

    assert deserialize(Literal["draft", "published"], "draft") == "draft"


def test_deserialize_enum_uses_member_value():
    from apischema import deserialize

    class State(Enum):
        READY = "ready"
        PAUSED = "paused"

    assert deserialize(State, "paused") is State.PAUSED


def test_deserialize_new_type_uses_base_type():
    from apischema import deserialize

    UserId = NewType("UserId", int)
    assert deserialize(UserId, 41) == 41


def test_deserialize_bytes_uses_base64_text():
    from apischema import deserialize

    encoded = base64.b64encode(b"hello").decode()
    assert deserialize(bytes, encoded) == b"hello"


def test_deserialize_date_uses_iso_text():
    from apischema import deserialize

    assert deserialize(date, "2024-02-29") == date(2024, 2, 29)


def test_deserialize_uuid_uses_string_form():
    from apischema import deserialize

    value = UUID("6f1f5d2b-6c61-4f2c-8f02-1a12ae9c8c22")
    assert deserialize(UUID, str(value)) == value


def test_deserialize_any_returns_original_object():
    from apischema import deserialize

    value = {"items": [1, object()]}
    assert deserialize(Any, value) is value


def test_deserialize_with_coerce_converts_string_integer():
    from apischema import deserialize

    assert deserialize(int, "42", coerce=True) == 42


def test_deserialize_additional_properties_accepts_unknown_keys():
    from apischema import deserialize

    @dataclass
    class Item:
        value: int

    assert deserialize(Item, {"value": 5, "extra": "kept"}, additional_properties=True) == Item(5)


def test_serialize_fixed_tuple_as_json_list():
    from apischema import serialize

    assert serialize(tuple[int, str], (4, "four")) == [4, "four"]


def test_serialize_any_recurses_through_runtime_mapping():
    from apischema import serialize

    assert serialize(Any, {"point": (2, 6)}) == {"point": [2, 6]}


def test_serialize_aliaser_changes_dataclass_keys():
    from apischema import serialize

    @dataclass
    class Item:
        item_id: int

    assert serialize(Item, Item(8), aliaser=str.upper) == {"ITEM_ID": 8}


def test_serialize_exclude_none_removes_none_fields():
    from apischema import serialize

    @dataclass
    class Item:
        value: int = 0
        note: str | None = None

    assert serialize(Item, Item(), exclude_none=True) == {"value": 0}


def test_serialize_exclude_defaults_removes_default_fields():
    from apischema import serialize

    @dataclass
    class Item:
        value: int = 0
        note: str = "base"

    assert serialize(Item, Item(), exclude_defaults=True) == {}


def test_serialize_no_copy_can_return_original_mapping():
    from apischema import serialize

    value = {"left": 1, "right": 2}
    assert serialize(dict[str, int], value, no_copy=True) is value


def test_deserialization_schema_exposes_dataclass_properties():
    from apischema.json_schema import deserialization_schema

    @dataclass
    class Item:
        count: int
        label: str = "new"

    generated = deserialization_schema(Item)
    assert generated["type"] == "object"
    assert generated["properties"]["count"] == {"type": "integer"}
    assert generated["properties"]["label"]["default"] == "new"


def test_serialization_schema_exposes_array_items():
    from apischema.json_schema import serialization_schema

    generated = serialization_schema(list[int])
    assert generated["type"] == "array"
    assert generated["items"] == {"type": "integer"}


def test_schema_constraint_appears_in_json_schema():
    from apischema import schema
    from apischema.json_schema import deserialization_schema

    @schema(min=2, max=9)
    class Score(int):
        pass

    generated = deserialization_schema(Score)
    assert generated["minimum"] == 2
    assert generated["maximum"] == 9


def test_field_alias_appears_in_schema_properties():
    from apischema import alias
    from apischema.json_schema import deserialization_schema

    @dataclass
    class Item:
        internal_name: str = field(metadata=alias("externalName"))

    generated = deserialization_schema(Item)
    assert "externalName" in generated["properties"]
    assert generated["required"] == ["externalName"]


def test_json_schema_draft_seven_uses_definitions_keyword():
    from apischema.json_schema import JsonSchemaVersion, deserialization_schema

    @dataclass
    class Item:
        value: int

    generated = deserialization_schema(Item, version=JsonSchemaVersion.DRAFT_7)
    assert generated["$schema"].endswith("draft-07/schema#")
    assert generated["type"] == "object"


def test_type_name_changes_schema_reference_name():
    from apischema import type_name
    from apischema.json_schema import deserialization_schema

    @dataclass
    class Item:
        value: int

    type_name("CatalogItem")(Item)
    generated = deserialization_schema(Item, all_refs=True)
    assert "CatalogItem" in generated["$defs"]


def test_definitions_schema_returns_referenced_definition():
    from apischema.json_schema import definitions_schema

    @dataclass
    class Item:
        value: int

    definitions = definitions_schema(deserialization=[Item], all_refs=True)
    assert "Item" in definitions
    assert definitions["Item"]["properties"]["value"] == {"type": "integer"}


def test_undefined_default_is_omitted_from_serialization():
    from apischema import serialize

    @dataclass
    class Patch:
        value: int | UndefinedType = Undefined

    assert serialize(Patch, Patch()) == {}


def test_serialized_property_is_added_to_output():
    from apischema import serialize

    assert serialize(SerializedItem, SerializedItem(6)) == {"value": 6, "doubled": 12}


def test_order_decorator_controls_serialized_key_order():
    from apischema import order, serialize

    @order(["third", "first", "second"])
    @dataclass
    class Item:
        first: int
        second: int
        third: int

    assert list(serialize(Item, Item(1, 2, 3))) == ["third", "first", "second"]


def test_deserialization_method_returns_callable_for_repeated_use():
    from apischema import deserialization_method

    method = deserialization_method(list[int])
    assert method([4, 5]) == [4, 5]
    assert method([6]) == [6]


def test_serialization_method_returns_callable_for_repeated_use():
    from apischema import serialization_method

    method = serialization_method(tuple[int, str])
    assert method((3, "three")) == [3, "three"]


def test_validation_error_exposes_public_error_locations():
    from apischema import ValidationError, deserialize

    @dataclass
    class Item:
        count: int

    with pytest.raises(ValidationError) as exc_info:
        deserialize(Item, {"count": "bad"})
    assert isinstance(exc_info.value.errors, list)
    assert exc_info.value.errors
    assert exc_info.value.errors[0]["loc"] == ["count"]


def test_unsupported_class_raises_public_unsupported():
    from apischema import Unsupported, deserialize

    class UnsupportedModel:
        pass

    with pytest.raises(Unsupported):
        deserialize(UnsupportedModel, {})


def test_as_names_uses_enum_names_for_both_projections():
    from apischema import deserialize, serialize
    from apischema.conversions import as_names

    @as_names
    class State(Enum):
        READY = object()
        PAUSED = object()

    assert deserialize(State, "READY") is State.READY
    assert serialize(State, State.PAUSED) == "PAUSED"
