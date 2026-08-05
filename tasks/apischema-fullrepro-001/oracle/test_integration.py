from __future__ import annotations

import base64
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any, Literal, Mapping, NewType
from uuid import UUID

import pytest

from apischema import (
    Undefined,
    UndefinedType,
    ValidationError,
    alias,
    deserialize,
    deserialization_method,
    order,
    schema,
    serialize,
    serialization_method,
    serialized,
    type_name,
)
from apischema.conversions import as_names
from apischema.json_schema import (
    definitions_schema,
    deserialization_schema,
    serialization_schema,
)

from conftest import Address, Defaults, User, UserWithAddress


@dataclass
class AliasedRecord:
    record_id: int = field(metadata=alias("recordId"))
    label: str = "new"


@dataclass
class NumericPair:
    left: int
    right: float


@as_names
class NamedState(Enum):
    READY = object()
    PAUSED = object()


class ValueState(Enum):
    READY = "ready"
    PAUSED = "paused"


@dataclass
class NamedStateRecord:
    state: NamedState


@dataclass
class ValueStateRecord:
    state: ValueState


@type_name("CatalogEntry")
@dataclass
class NamedEntry:
    value: int


@dataclass
class ComputedEntry:
    value: int

    @serialized
    def doubled(self) -> int:
        return self.value * 2


@order(["third", "first", "second"])
@dataclass
class OrderedEntry:
    first: int
    second: int
    third: int


@schema(min=1, max=10)
class Rating(int):
    pass


@dataclass
class RatedEntry:
    rating: Rating


@dataclass
class WireValues:
    day: date
    identifier: UUID
    payload: bytes


@dataclass
class LiteralEntry:
    state: Literal["new", "done"]


TicketId = NewType("TicketId", int)


@dataclass
class Ticket:
    ticket_id: TicketId


@dataclass
class TupleEntry:
    pair: tuple[int, str]


@dataclass
class OptionalEntry:
    value: int | None


@dataclass
class MappingEntry:
    values: Mapping[int, str]


@dataclass
class PatchEntry:
    value: int | UndefinedType = Undefined


@dataclass
class SetEntry:
    values: set[int]


@dataclass
class AnyEntry:
    payload: Any


@pytest.mark.depends_on(
    "test_deserialize_additional_properties_accepts_unknown_keys",
    "test_serialize_any_recurses_through_runtime_mapping",
)
def test_user_round_trip_connects_deserialization_and_serialization(user_data, user):
    structured = deserialize(User, user_data)

    assert structured == user
    assert serialize(User, structured) == user_data


@pytest.mark.depends_on("test_deserialize_list_structures_each_element")
def test_nested_dataclass_round_trip_preserves_both_object_levels(nested_data):
    structured = deserialize(UserWithAddress, nested_data)

    assert structured.user.name == "Nia"
    assert structured.address == Address("Oslo", 4481)
    assert serialize(UserWithAddress, structured) == nested_data


@pytest.mark.depends_on("test_deserialize_list_structures_each_element")
def test_list_of_dataclasses_round_trip_preserves_order(user_data):
    payload = [user_data, {**user_data, "user_id": 18, "name": "Ivo"}]

    structured = deserialize(list[User], payload)

    assert [item.user_id for item in structured] == [17, 18]
    assert serialize(list[User], structured) == payload


@pytest.mark.depends_on("test_deserialize_mapping_structures_keys_and_values")
def test_mapping_of_dataclasses_round_trip_preserves_mapping_keys(user_data):
    payload = {"primary": user_data}

    structured = deserialize(dict[str, User], payload)

    assert structured["primary"].name == "Nia"
    assert serialize(dict[str, User], structured) == payload


@pytest.mark.depends_on("test_serialize_exclude_defaults_removes_default_fields")
def test_absent_default_fields_deserialize_and_serialize_consistently():
    structured = deserialize(Defaults, {})

    assert structured == Defaults()
    assert serialize(Defaults, structured) == {"count": 0, "note": None}


@pytest.mark.depends_on("test_serialize_exclude_none_removes_none_fields")
def test_exclude_none_output_deserializes_back_to_default():
    payload = serialize(Defaults, Defaults(), exclude_none=True)

    assert payload == {"count": 0}
    assert deserialize(Defaults, payload) == Defaults()


@pytest.mark.depends_on("test_serialize_exclude_defaults_removes_default_fields")
def test_exclude_defaults_output_deserializes_back_to_defaults():
    payload = serialize(Defaults, Defaults(), exclude_defaults=True)

    assert payload == {}
    assert deserialize(Defaults, payload) == Defaults()


@pytest.mark.depends_on("test_field_alias_appears_in_schema_properties")
def test_field_alias_is_shared_by_round_trip_and_schema():
    payload = {"recordId": 7, "label": "ready"}

    structured = deserialize(AliasedRecord, payload)
    generated = deserialization_schema(AliasedRecord)

    assert structured == AliasedRecord(7, "ready")
    assert serialize(AliasedRecord, structured) == payload
    assert set(generated["properties"]) == {"recordId", "label"}
    assert generated["required"] == ["recordId"]


@pytest.mark.depends_on("test_serialize_aliaser_changes_dataclass_keys")
def test_runtime_aliaser_is_shared_by_deserialization_serialization_and_schema(user):
    payload = {
        "USER_ID": 17,
        "NAME": "Nia",
        "ACTIVE": False,
        "TAGS": ["green", "edge"],
    }

    assert deserialize(User, payload, aliaser=str.upper) == user
    assert serialize(User, user, aliaser=str.upper) == payload
    assert set(deserialization_schema(User, aliaser=str.upper)["properties"]) == set(payload)


@pytest.mark.depends_on("test_deserialization_schema_exposes_dataclass_properties")
def test_user_schema_properties_match_serialized_keys(user):
    payload = serialize(User, user)
    input_schema = deserialization_schema(User)
    output_schema = serialization_schema(User)

    assert set(output_schema["properties"]) == set(payload)
    assert set(output_schema["required"]) == set(payload)
    assert set(input_schema["required"]) == {"user_id", "name"}
    assert output_schema["properties"]["tags"]["type"] == "array"


@pytest.mark.depends_on("test_deserialization_schema_exposes_dataclass_properties")
def test_nested_schema_and_serialization_share_child_property_names(nested_data):
    structured = deserialize(UserWithAddress, nested_data)
    payload = serialize(UserWithAddress, structured)
    generated = deserialization_schema(UserWithAddress)

    assert set(generated["properties"]) == set(payload) == {"user", "address"}
    assert set(generated["properties"]["address"]["properties"]) == set(payload["address"])


@pytest.mark.depends_on("test_validation_error_exposes_public_error_locations")
def test_nested_validation_error_location_matches_model_path(nested_data):
    invalid = {**nested_data, "address": {"city": "Oslo", "postal_code": "bad"}}

    with pytest.raises(ValidationError) as caught:
        deserialize(UserWithAddress, invalid)

    assert caught.value.errors[0]["loc"] == ["address", "postal_code"]


@pytest.mark.depends_on("test_validation_error_exposes_public_error_locations")
def test_default_strictness_rejects_unknown_property_and_schema_disallows_it(user_data):
    with pytest.raises(ValidationError) as caught:
        deserialize(User, {**user_data, "extra": 1})

    assert caught.value.errors
    assert deserialization_schema(User)["additionalProperties"] is False


@pytest.mark.depends_on("test_deserialize_additional_properties_accepts_unknown_keys")
def test_additional_properties_mode_accepts_input_but_serializes_known_model(user_data, user):
    structured = deserialize(User, {**user_data, "extra": "ignored"}, additional_properties=True)

    assert structured == user
    assert serialize(User, structured) == user_data
    assert "additionalProperties" not in deserialization_schema(User, additional_properties=True)


@pytest.mark.depends_on("test_deserialize_with_coerce_converts_string_integer")
def test_coercion_flows_through_dataclass_then_serializes_typed_values():
    structured = deserialize(NumericPair, {"left": "12", "right": "2.5"}, coerce=True)

    assert structured == NumericPair(12, 2.5)
    assert serialize(NumericPair, structured) == {"left": 12, "right": 2.5}


@pytest.mark.depends_on(
    "test_deserialization_method_returns_callable_for_repeated_use",
    "test_serialization_method_returns_callable_for_repeated_use",
)
def test_reusable_methods_round_trip_multiple_dataclass_values():
    load = deserialization_method(NumericPair)
    dump = serialization_method(NumericPair)

    first = load({"left": 1, "right": 2.0})
    second = load({"left": 3, "right": 4.5})

    assert [dump(first), dump(second)] == [
        {"left": 1, "right": 2.0},
        {"left": 3, "right": 4.5},
    ]


@pytest.mark.depends_on("test_as_names_uses_enum_names_for_both_projections")
def test_named_enum_round_trip_and_schema_use_member_names():
    structured = deserialize(NamedStateRecord, {"state": "READY"})
    generated = deserialization_schema(NamedStateRecord)

    assert structured.state is NamedState.READY
    assert serialize(NamedStateRecord, structured) == {"state": "READY"}
    assert generated["properties"]["state"]["enum"] == ["READY", "PAUSED"]


@pytest.mark.depends_on("test_deserialize_enum_uses_member_value")
def test_value_enum_round_trip_and_schema_use_member_values():
    structured = deserialize(ValueStateRecord, {"state": "paused"})
    generated = serialization_schema(ValueStateRecord)

    assert structured.state is ValueState.PAUSED
    assert serialize(ValueStateRecord, structured) == {"state": "paused"}
    assert generated["properties"]["state"]["enum"] == ["ready", "paused"]


@pytest.mark.depends_on(
    "test_type_name_changes_schema_reference_name",
    "test_definitions_schema_returns_referenced_definition",
)
def test_named_type_reference_and_definition_describe_round_trip_model():
    generated = deserialization_schema(NamedEntry, all_refs=True)
    definitions = definitions_schema(
        deserialization=[NamedEntry],
        serialization=[NamedEntry],
        all_refs=True,
    )
    structured = deserialize(NamedEntry, {"value": 5})

    assert generated["$ref"] == "#/$defs/CatalogEntry"
    assert "CatalogEntry" in definitions
    assert serialize(NamedEntry, structured) == {"value": 5}


@pytest.mark.depends_on("test_serialized_property_is_added_to_output")
def test_serialized_method_is_present_only_in_output_projection():
    payload = serialize(ComputedEntry, ComputedEntry(6))
    input_schema = deserialization_schema(ComputedEntry)
    output_schema = serialization_schema(ComputedEntry)

    assert payload == {"value": 6, "doubled": 12}
    assert "doubled" not in input_schema["properties"]
    assert output_schema["properties"]["doubled"] == {"type": "integer"}
    assert "doubled" in output_schema["required"]


@pytest.mark.depends_on("test_order_decorator_controls_serialized_key_order")
def test_declared_order_controls_payload_and_output_schema_property_order():
    payload = serialize(OrderedEntry, OrderedEntry(1, 2, 3))
    generated = serialization_schema(OrderedEntry)

    assert list(payload) == ["third", "first", "second"]
    assert list(generated["properties"]) == ["third", "first", "second"]


@pytest.mark.depends_on("test_schema_constraint_appears_in_json_schema")
def test_constrained_field_accepts_valid_data_and_projects_schema_bounds():
    structured = deserialize(RatedEntry, {"rating": 7})
    generated = deserialization_schema(RatedEntry)

    assert int(structured.rating) == 7
    assert serialize(RatedEntry, structured) == {"rating": 7}
    assert generated["properties"]["rating"]["minimum"] == 1
    assert generated["properties"]["rating"]["maximum"] == 10


@pytest.mark.depends_on("test_validation_error_exposes_public_error_locations")
def test_constrained_field_rejects_out_of_range_data_at_field_location():
    with pytest.raises(ValidationError) as caught:
        deserialize(RatedEntry, {"rating": 11})

    assert caught.value.errors[0]["loc"] == ["rating"]


@pytest.mark.depends_on(
    "test_deserialize_bytes_uses_base64_text",
    "test_deserialize_date_uses_iso_text",
    "test_deserialize_uuid_uses_string_form",
)
def test_standard_wire_types_round_trip_through_one_model():
    identifier = UUID("6f1f5d2b-6c61-4f2c-8f02-1a12ae9c8c22")
    payload = {
        "day": "2024-02-29",
        "identifier": str(identifier),
        "payload": base64.b64encode(b"hello").decode(),
    }

    structured = deserialize(WireValues, payload)

    assert structured == WireValues(date(2024, 2, 29), identifier, b"hello")
    assert serialize(WireValues, structured) == payload


@pytest.mark.depends_on("test_deserialization_schema_exposes_dataclass_properties")
def test_standard_wire_type_schema_matches_string_payload_projection():
    generated = deserialization_schema(WireValues)
    structured = WireValues(
        date(2024, 2, 29),
        UUID("6f1f5d2b-6c61-4f2c-8f02-1a12ae9c8c22"),
        b"hello",
    )
    payload = serialize(WireValues, structured)

    assert all(item["type"] == "string" for item in generated["properties"].values())
    assert all(isinstance(value, str) for value in payload.values())


@pytest.mark.depends_on("test_deserialize_literal_accepts_declared_value")
def test_literal_field_round_trip_and_schema_share_allowed_values():
    structured = deserialize(LiteralEntry, {"state": "done"})
    generated = deserialization_schema(LiteralEntry)

    assert serialize(LiteralEntry, structured) == {"state": "done"}
    assert generated["properties"]["state"]["enum"] == ["new", "done"]


@pytest.mark.depends_on("test_deserialize_new_type_uses_base_type")
def test_newtype_field_round_trip_and_schema_use_underlying_integer():
    structured = deserialize(Ticket, {"ticket_id": 41})
    generated = deserialization_schema(Ticket)

    assert structured == Ticket(41)
    assert serialize(Ticket, structured) == {"ticket_id": 41}
    assert generated["properties"]["ticket_id"] == {"type": "integer"}


@pytest.mark.depends_on("test_deserialize_fixed_tuple_uses_position_types")
def test_fixed_tuple_field_round_trip_and_schema_preserve_positions():
    structured = deserialize(TupleEntry, {"pair": [9, "nine"]})
    generated = deserialization_schema(TupleEntry)["properties"]["pair"]

    assert structured == TupleEntry((9, "nine"))
    assert serialize(TupleEntry, structured) == {"pair": [9, "nine"]}
    assert generated["type"] == "array"
    assert generated["minItems"] == generated["maxItems"] == 2


@pytest.mark.depends_on("test_deserialize_optional_none_returns_none")
def test_optional_field_round_trips_none_and_integer_and_schema_allows_null():
    none_value = deserialize(OptionalEntry, {"value": None})
    int_value = deserialize(OptionalEntry, {"value": 3})
    generated = deserialization_schema(OptionalEntry)["properties"]["value"]

    assert serialize(OptionalEntry, none_value) == {"value": None}
    assert serialize(OptionalEntry, int_value) == {"value": 3}
    assert generated["type"] == ["integer", "null"]


@pytest.mark.depends_on("test_deserialize_mapping_structures_keys_and_values")
def test_integer_key_mapping_coerces_input_and_preserves_typed_output_keys():
    structured = deserialize(MappingEntry, {"values": {"7": "seven"}}, coerce=True)

    assert structured == MappingEntry({7: "seven"})
    assert serialize(MappingEntry, structured) == {"values": {7: "seven"}}


@pytest.mark.depends_on("test_undefined_default_is_omitted_from_serialization")
def test_undefined_field_round_trip_preserves_absence():
    structured = deserialize(PatchEntry, {})

    assert structured.value is Undefined
    assert serialize(PatchEntry, structured) == {}
    assert "value" not in deserialization_schema(PatchEntry).get("required", [])


@pytest.mark.depends_on("test_deserialize_list_structures_each_element")
def test_set_field_round_trip_and_schema_require_unique_items():
    structured = deserialize(SetEntry, {"values": [3, 1, 3]})
    payload = serialize(SetEntry, structured)
    generated = deserialization_schema(SetEntry)["properties"]["values"]

    assert structured.values == {1, 3}
    assert set(payload["values"]) == {1, 3}
    assert generated["uniqueItems"] is True


@pytest.mark.depends_on("test_deserialize_any_returns_original_object")
def test_any_field_preserves_json_shape_across_both_projections():
    payload = {"payload": {"items": [1, True, None], "name": "sample"}}

    structured = deserialize(AnyEntry, payload)

    assert structured.payload is payload["payload"]
    assert serialize(AnyEntry, structured) == payload
    assert deserialization_schema(AnyEntry)["properties"]["payload"] == {}


@pytest.mark.depends_on("test_serialize_exclude_defaults_removes_default_fields")
def test_fall_back_on_default_recovers_invalid_field_then_serializes_default():
    structured = deserialize(Defaults, {"count": "bad"}, fall_back_on_default=True)

    assert structured == Defaults()
    assert serialize(Defaults, structured, exclude_defaults=True) == {}


@pytest.mark.depends_on("test_deserialization_schema_exposes_dataclass_properties")
def test_input_and_output_schema_share_shape_with_directional_required_fields():
    input_schema = deserialization_schema(UserWithAddress)
    output_schema = serialization_schema(UserWithAddress)

    assert set(input_schema["properties"]) == set(output_schema["properties"])
    assert input_schema["properties"]["address"] == output_schema["properties"]["address"]
    assert set(input_schema["properties"]["user"]["properties"]) == set(
        output_schema["properties"]["user"]["properties"]
    )
    assert input_schema["properties"]["user"]["required"] == ["user_id", "name"]
    assert output_schema["properties"]["user"]["required"] == ["user_id", "name", "active", "tags"]
