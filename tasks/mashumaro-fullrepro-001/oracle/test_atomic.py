# Spec2Repo oracle - atomic tests for mashumaro-fullrepro-001
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum, IntEnum
from typing import Any, NamedTuple
from uuid import UUID

import pytest
from typing_extensions import Annotated

from mashumaro import DataClassDictMixin, MissingField, field_options, pass_through
from mashumaro.codecs.basic import BasicDecoder, BasicEncoder
from mashumaro.codecs.json import JSONDecoder, JSONEncoder, json_decode, json_encode
from mashumaro.config import BaseConfig
from mashumaro.exceptions import ExtraKeysError, InvalidFieldValue
from mashumaro.jsonschema import build_json_schema
from mashumaro.jsonschema.annotations import MaxItems, Maximum, MinLength
from mashumaro.types import Alias, Discriminator, RoundedDecimal, SerializationStrategy

from conftest import (
    Coordinate,
    DateBox,
    DateBoxStrategy,
    DecimalAsCents,
    EnumNameStrategy,
    Leaf,
    Point,
    PrimitiveBox,
    Priority,
    SerializableCoordinate,
    Tone,
)


def test_field_options_preserves_standard_and_extra_metadata():
    options = field_options(serialize=str, deserialize=int, alias="publicName", custom_flag=True)
    assert options["serialize"] is str
    assert options["deserialize"] is int
    assert options["alias"] == "publicName"
    assert options["custom_flag"] is True


def test_pass_through_strategy_returns_original_objects():
    marker = {"k": ["v"]}
    assert pass_through.serialize(marker) is marker
    assert pass_through.deserialize(marker) is marker


def test_rounded_decimal_quantizes_and_deserializes_strings():
    strategy = RoundedDecimal(places=2, rounding=ROUND_HALF_UP)
    assert strategy.serialize(Decimal("7.235")) == "7.24"
    assert strategy.deserialize("11.50") == Decimal("11.50")


def test_discriminator_requires_at_least_one_inclusion_direction():
    with pytest.raises(ValueError):
        Discriminator(field="kind")
    disc = Discriminator(field="kind", include_subtypes=True)
    assert disc.field == "kind"
    assert disc.include_subtypes is True


def test_alias_compares_by_name_and_hashes_by_name():
    assert Alias("external") == Alias("external")
    assert Alias("external") != Alias("other")
    assert len({Alias("external"), Alias("external")}) == 1


def test_to_dict_serializes_primitive_dataclass_fields():
    assert PrimitiveBox(flag=True, total=42, label="north").to_dict() == {
        "flag": True,
        "total": 42,
        "label": "north",
    }


def test_from_dict_deserializes_primitive_dataclass_fields():
    assert PrimitiveBox.from_dict({"flag": False, "total": 9, "label": "south"}) == PrimitiveBox(
        flag=False, total=9, label="south"
    )


def test_from_dict_missing_required_field_raises_missing_field():
    with pytest.raises(MissingField) as exc_info:
        PrimitiveBox.from_dict({"flag": True, "total": 1})
    assert exc_info.value.field_name == "label"
    assert exc_info.value.holder_class is PrimitiveBox


def test_from_dict_invalid_integer_value_raises_invalid_field_value():
    with pytest.raises(InvalidFieldValue) as exc_info:
        PrimitiveBox.from_dict({"flag": True, "total": "not-an-int", "label": "bad"})
    assert exc_info.value.field_name == "total"


def test_nested_dataclass_to_dict_serializes_nested_public_shape():
    @dataclass
    class Box(DataClassDictMixin):
        leaf: Leaf
        label: str

    assert Box(Leaf("birch", 3), "tree").to_dict() == {
        "leaf": {"code": "birch", "count": 3},
        "label": "tree",
    }


def test_nested_dataclass_from_dict_builds_nested_objects():
    @dataclass
    class Box(DataClassDictMixin):
        leaf: Leaf
        label: str

    assert Box.from_dict({"leaf": {"code": "maple", "count": 5}, "label": "tree"}) == Box(
        Leaf("maple", 5), "tree"
    )


def test_list_of_dataclasses_rounds_through_basic_form():
    @dataclass
    class Forest(DataClassDictMixin):
        leaves: list[Leaf]

    forest = Forest([Leaf("oak", 2), Leaf("pine", 4)])
    assert forest.to_dict() == {"leaves": [{"code": "oak", "count": 2}, {"code": "pine", "count": 4}]}


def test_datetime_and_date_values_use_iso_basic_form():
    @dataclass
    class Event(DataClassDictMixin):
        day: date
        at: datetime

    event = Event(date(2026, 8, 4), datetime(2026, 8, 4, 12, 30, tzinfo=timezone.utc))
    assert event.to_dict() == {"day": "2026-08-04", "at": "2026-08-04T12:30:00+00:00"}


def test_datetime_and_date_values_deserialize_from_iso_strings():
    @dataclass
    class Event(DataClassDictMixin):
        day: date
        at: datetime

    assert Event.from_dict({"day": "2026-08-05", "at": "2026-08-05T06:15:00+00:00"}) == Event(
        date(2026, 8, 5), datetime(2026, 8, 5, 6, 15, tzinfo=timezone.utc)
    )


def test_enum_fields_serialize_and_deserialize_by_value():
    @dataclass
    class Swatch(DataClassDictMixin):
        tone: Tone
        priority: Priority

    assert Swatch(Tone.bright, Priority.high).to_dict() == {"tone": "bright", "priority": 9}
    assert Swatch.from_dict({"tone": "calm", "priority": 1}) == Swatch(Tone.calm, Priority.low)


def test_tuple_and_set_fields_use_basic_collection_forms():
    @dataclass
    class Collections(DataClassDictMixin):
        coords: tuple[int, str]
        labels: set[str]

    result = Collections((8, "east"), {"blue", "red"}).to_dict()
    assert result["coords"] == [8, "east"]
    assert sorted(result["labels"]) == ["blue", "red"]


def test_namedtuple_defaults_to_list_representation():
    @dataclass
    class Shape(DataClassDictMixin):
        point: Point

    assert Shape(Point(4, 6)).to_dict() == {"point": [4, 6]}
    assert Shape.from_dict({"point": [1, 2]}) == Shape(Point(1, 2))


def test_namedtuple_as_dict_config_uses_keyed_representation():
    @dataclass
    class Shape(DataClassDictMixin):
        point: Point

        class Config(BaseConfig):
            namedtuple_as_dict = True

    assert Shape(Point(10, 11)).to_dict() == {"point": {"x": 10, "y": 11}}
    assert Shape.from_dict({"point": {"x": 12, "y": 13}}) == Shape(Point(12, 13))


def test_field_option_alias_controls_input_key():
    @dataclass
    class Renamed(DataClassDictMixin):
        value: int = field(metadata=field_options(alias="wireValue"))

    assert Renamed.from_dict({"wireValue": 33}) == Renamed(33)


def test_field_option_serialize_callable_controls_output_value():
    @dataclass
    class Product(DataClassDictMixin):
        sku: int = field(metadata=field_options(serialize=lambda value: f"SKU-{value}"))

    assert Product(314).to_dict() == {"sku": "SKU-314"}


def test_field_option_deserialize_callable_controls_input_value():
    @dataclass
    class Product(DataClassDictMixin):
        sku: int = field(metadata=field_options(deserialize=lambda value: int(value.removeprefix("SKU-"))))

    assert Product.from_dict({"sku": "SKU-271"}) == Product(271)


def test_config_aliases_and_serialize_by_alias_control_output_keys():
    @dataclass
    class Record(DataClassDictMixin):
        given_name: str

        class Config(BaseConfig):
            aliases = {"given_name": "givenName"}
            serialize_by_alias = True

    assert Record("Ada").to_dict() == {"givenName": "Ada"}


def test_allow_deserialization_not_by_alias_accepts_field_names():
    @dataclass
    class Record(DataClassDictMixin):
        given_name: str = field(metadata=field_options(alias="givenName"))

        class Config(BaseConfig):
            allow_deserialization_not_by_alias = True

    assert Record.from_dict({"given_name": "Grace"}) == Record("Grace")


def test_omit_none_config_removes_none_fields_from_output():
    @dataclass
    class Maybe(DataClassDictMixin):
        value: int | None
        note: str | None

        class Config(BaseConfig):
            omit_none = True

    assert Maybe(None, "kept").to_dict() == {"note": "kept"}


def test_omit_default_config_removes_default_equal_fields():
    @dataclass
    class Defaults(DataClassDictMixin):
        count: int = 5
        labels: list[str] = field(default_factory=lambda: ["seed"])

        class Config(BaseConfig):
            omit_default = True

    assert Defaults().to_dict() == {}
    assert Defaults(count=6).to_dict() == {"count": 6}


def test_sort_keys_config_orders_serialized_mapping_keys():
    @dataclass
    class SortedRecord(DataClassDictMixin):
        zebra: int
        amber: int

        class Config(BaseConfig):
            sort_keys = True

    assert list(SortedRecord(1, 2).to_dict()) == ["amber", "zebra"]


def test_forbid_extra_keys_config_raises_extra_keys_error():
    @dataclass
    class StrictRecord(DataClassDictMixin):
        name: str

        class Config(BaseConfig):
            forbid_extra_keys = True

    with pytest.raises(ExtraKeysError) as exc_info:
        StrictRecord.from_dict({"name": "Mira", "spare": True})
    assert exc_info.value.extra_keys == {"spare"}


def test_config_serialization_strategy_applies_to_registered_type():
    @dataclass
    class Price(DataClassDictMixin):
        amount: Decimal

        class Config(BaseConfig):
            serialization_strategy = {Decimal: DecimalAsCents()}

    assert Price(Decimal("12.34")).to_dict() == {"amount": 1234}
    assert Price.from_dict({"amount": 987}) == Price(Decimal("9.87"))


def test_serialization_strategy_match_subclasses_handles_enum_subclass():
    @dataclass
    class Choice(DataClassDictMixin):
        tone: Tone

        class Config(BaseConfig):
            serialization_strategy = {Enum: EnumNameStrategy()}

    assert Choice(Tone.calm).to_dict() == {"tone": "calm"}
    assert Choice.from_dict({"tone": "bright"}) == Choice(Tone.bright)


def test_serializable_type_uses_custom_serialize_deserialize_methods():
    @dataclass
    class Marker(DataClassDictMixin):
        coordinate: Coordinate

        class Config(BaseConfig):
            serialization_strategy = {Coordinate: SerializableCoordinate()}

    assert Marker(Coordinate(2, 9)).to_dict() == {"coordinate": [2, 9]}
    assert Marker.from_dict({"coordinate": [3, 8]}) == Marker(Coordinate(3, 8))


def test_serializable_type_with_annotations_transforms_nested_values():
    @dataclass
    class Wrapped(DataClassDictMixin):
        box: DateBox

        class Config(BaseConfig):
            serialization_strategy = {DateBox: DateBoxStrategy()}

    assert Wrapped.from_dict({"box": "2026-08-04"}) == Wrapped(DateBox(date(2026, 8, 4)))
    assert Wrapped(DateBox(date(2026, 8, 5))).to_dict() == {"box": "2026-08-05"}


def test_basic_encoder_serializes_typed_shape_to_basic_form():
    encoder = BasicEncoder(list[date])
    assert encoder.encode([date(2026, 8, 4), date(2026, 8, 6)]) == ["2026-08-04", "2026-08-06"]


def test_basic_decoder_deserializes_typed_shape_from_basic_form():
    decoder = BasicDecoder(list[date])
    assert decoder.decode(["2026-08-04", "2026-08-06"]) == [date(2026, 8, 4), date(2026, 8, 6)]


def test_json_encoder_and_decoder_handle_dataclass_lists():
    @dataclass
    class Entry:
        name: str
        when: date

    encoded = JSONEncoder(list[Entry]).encode([Entry("launch", date(2026, 8, 4))])
    assert encoded == '[{"name": "launch", "when": "2026-08-04"}]'
    assert JSONDecoder(list[Entry]).decode(encoded) == [Entry("launch", date(2026, 8, 4))]


def test_json_convenience_functions_encode_and_decode_typed_values():
    payload = json_encode({"alpha": [date(2026, 8, 4)]}, dict[str, list[date]])
    assert payload == '{"alpha": ["2026-08-04"]}'
    assert json_decode(payload, dict[str, list[date]]) == {"alpha": [date(2026, 8, 4)]}


def test_json_schema_for_primitive_types_uses_expected_type_names():
    assert build_json_schema(str).to_dict() == {"type": "string"}
    assert build_json_schema(int).to_dict() == {"type": "integer"}


def test_json_schema_for_dataclass_includes_properties_and_required_fields():
    @dataclass
    class Account:
        id: UUID
        name: str

    schema = build_json_schema(Account).to_dict()
    assert schema["type"] == "object"
    assert schema["title"] == "Account"
    assert schema["properties"]["id"] == {"type": "string", "format": "uuid"}
    assert schema["required"] == ["id", "name"]


def test_json_schema_annotations_apply_validation_keywords():
    schema = build_json_schema(Annotated[list[Annotated[int, Maximum(7)]], MaxItems(3)]).to_dict()
    assert schema["items"] == {"type": "integer", "maximum": 7}
    assert schema["maxItems"] == 3


def test_json_schema_field_metadata_adds_descriptions_and_constraints():
    @dataclass
    class Account:
        name: Annotated[str, MinLength(2)] = field(metadata={"description": "Display name"})

    schema = build_json_schema(Account).to_dict()
    assert schema["properties"]["name"]["description"] == "Display name"
    assert schema["properties"]["name"]["minLength"] == 2
