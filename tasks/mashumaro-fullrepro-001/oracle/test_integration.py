# Spec2Repo oracle - integration tests for mashumaro-fullrepro-001
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

import pytest
from typing_extensions import Annotated

from mashumaro import DataClassDictMixin, field_options
from mashumaro.codecs.basic import BasicDecoder, BasicEncoder
from mashumaro.codecs.json import JSONDecoder, JSONEncoder
from mashumaro.config import (
    ADD_DIALECT_SUPPORT,
    ADD_SERIALIZATION_CONTEXT,
    BaseConfig,
    TO_DICT_ADD_BY_ALIAS_FLAG,
    TO_DICT_ADD_OMIT_NONE_FLAG,
)
from mashumaro.dialect import Dialect
from mashumaro.exceptions import ExtraKeysError, InvalidFieldValue, MissingField
from mashumaro.jsonschema import JSONSchemaBuilder, OPEN_API_3_1, build_json_schema
from mashumaro.jsonschema.annotations import Maximum
from mashumaro.jsonschema.models import JSONSchema
from mashumaro.mixins.json import DataClassJSONMixin
from mashumaro.mixins.msgpack import DataClassMessagePackMixin
from mashumaro.mixins.toml import DataClassTOMLMixin
from mashumaro.mixins.yaml import DataClassYAMLMixin
from mashumaro.types import SerializationStrategy

from conftest import Account, DateAsCompactString, DecimalAsCents, Leaf, Metric, Point, Tone, User


@pytest.mark.depends_on("test_to_dict_serializes_primitive_dataclass_fields", "test_from_dict_deserializes_primitive_dataclass_fields")
def test_dict_round_trip_preserves_nested_dataclass_values():
    """Seam: state consistency between to_dict output and from_dict input."""
    @dataclass
    class Bundle(DataClassDictMixin):
        leaf: Leaf
        dates: list[date]

    original = Bundle(Leaf("spruce", 12), [date(2026, 8, 4), date(2026, 8, 7)])
    dumped = original.to_dict()
    assert dumped == {"leaf": {"code": "spruce", "count": 12}, "dates": ["2026-08-04", "2026-08-07"]}
    assert Bundle.from_dict(dumped) == original


@pytest.mark.depends_on("test_config_aliases_and_serialize_by_alias_control_output_keys", "test_field_option_alias_controls_input_key")
def test_alias_config_round_trip_uses_external_key_projection():
    """Seam: state consistency between alias-aware serialization and deserialization."""
    @dataclass
    class Contact(DataClassDictMixin):
        given_name: str = field(metadata=field_options(alias="givenName"))
        family_name: str = field(metadata=field_options(alias="familyName"))

        class Config(BaseConfig):
            serialize_by_alias = True

    dumped = Contact("Ada", "Lovelace").to_dict()
    assert dumped == {"givenName": "Ada", "familyName": "Lovelace"}
    assert Contact.from_dict(dumped) == Contact("Ada", "Lovelace")


@pytest.mark.depends_on("test_omit_none_config_removes_none_fields_from_output", "test_omit_default_config_removes_default_equal_fields")
def test_omit_none_and_default_config_compose_in_single_projection():
    """Seam: config interaction between omit_none and omit_default."""
    @dataclass
    class Settings(DataClassDictMixin):
        retries: int = 3
        note: str | None = None
        tag: str = "active"

        class Config(BaseConfig):
            omit_none = True
            omit_default = True

    assert Settings().to_dict() == {}
    assert Settings(retries=4, note=None, tag="active").to_dict() == {"retries": 4}


@pytest.mark.depends_on('test_namedtuple_as_dict_config_uses_keyed_representation', 'test_to_dict_serializes_primitive_dataclass_fields', 'test_from_dict_deserializes_primitive_dataclass_fields')
def test_namedtuple_as_dict_round_trip_inside_nested_collection():
    """Seam: protocol handoff between named tuple policy and nested collection conversion."""
    @dataclass
    class Route(DataClassDictMixin):
        points: list[Point]

        class Config(BaseConfig):
            namedtuple_as_dict = True

    data = {"points": [{"x": 1, "y": 2}, {"x": 3, "y": 5}]}
    route = Route.from_dict(data)
    assert route == Route([Point(1, 2), Point(3, 5)])
    assert route.to_dict() == data


@pytest.mark.depends_on("test_config_serialization_strategy_applies_to_registered_type", "test_basic_encoder_serializes_typed_shape_to_basic_form")
def test_config_strategy_applies_through_basic_codec_encoder_and_decoder():
    """Seam: protocol handoff between dataclass Config strategies and BasicEncoder."""
    @dataclass
    class Invoice(DataClassDictMixin):
        amount: Decimal

        class Config(BaseConfig):
            serialization_strategy = {Decimal: DecimalAsCents()}

    encoded = BasicEncoder(Invoice).encode(Invoice(Decimal("8.25")))
    assert encoded == {"amount": 825}
    assert BasicDecoder(Invoice).decode(encoded) == Invoice(Decimal("8.25"))


@pytest.mark.depends_on("test_json_encoder_and_decoder_handle_dataclass_lists", "test_field_option_alias_controls_input_key")
def test_json_codec_round_trip_respects_dataclass_field_aliases():
    """Seam: protocol handoff between JSON codec text and dataclass alias metadata."""
    @dataclass
    class Event(DataClassDictMixin):
        public_id: int = field(metadata=field_options(alias="id"))
        when: date = field(metadata=field_options(alias="eventDate"))

        class Config(BaseConfig):
            serialize_by_alias = True

    encoded = JSONEncoder(list[Event]).encode([Event(7, date(2026, 8, 4))])
    assert encoded == '[{"id": 7, "eventDate": "2026-08-04"}]'
    assert JSONDecoder(list[Event]).decode(encoded) == [Event(7, date(2026, 8, 4))]


@pytest.mark.depends_on("test_json_convenience_functions_encode_and_decode_typed_values", "test_config_aliases_and_serialize_by_alias_control_output_keys")
def test_json_mixin_round_trip_uses_to_dict_and_from_dict_rules():
    """Seam: state consistency between DataClassJSONMixin and DataClassDictMixin."""
    @dataclass
    class Contact(DataClassJSONMixin):
        given_name: str = field(metadata=field_options(alias="givenName"))

        class Config(BaseConfig):
            serialize_by_alias = True

    encoded = Contact("Grace").to_json()
    assert encoded == '{"givenName": "Grace"}'
    assert Contact.from_json(encoded) == Contact("Grace")


@pytest.mark.depends_on("test_datetime_and_date_values_use_iso_basic_form", "test_datetime_and_date_values_deserialize_from_iso_strings")
def test_json_mixin_custom_encoder_decoder_still_wraps_dict_conversion():
    """Seam: protocol handoff between custom JSON callables and dict conversion."""
    @dataclass
    class Event(DataClassJSONMixin):
        when: date

    encoded = Event(date(2026, 8, 4)).to_json(encoder=lambda data: {"wrapped": data})
    assert encoded == {"wrapped": {"when": "2026-08-04"}}
    assert Event.from_json({"wrapped": {"when": "2026-08-05"}}, decoder=lambda data: data["wrapped"]) == Event(
        date(2026, 8, 5)
    )


@pytest.mark.depends_on("test_datetime_and_date_values_use_iso_basic_form", "test_datetime_and_date_values_deserialize_from_iso_strings")
def test_yaml_mixin_round_trip_preserves_date_conversion():
    """Seam: protocol handoff between YAML bytes/text and dataclass conversion."""
    @dataclass
    class Event(DataClassYAMLMixin):
        name: str
        when: date

    encoded = Event("review", date(2026, 8, 4)).to_yaml()
    assert Event.from_yaml(encoded) == Event("review", date(2026, 8, 4))


@pytest.mark.depends_on("test_omit_none_config_removes_none_fields_from_output", "test_datetime_and_date_values_use_iso_basic_form")
def test_toml_mixin_omits_none_and_round_trips_date_values():
    """Seam: config interaction between TOML dialect defaults and dataclass fields."""
    @dataclass
    class ConfigFile(DataClassTOMLMixin):
        name: str
        released: date
        comment: str | None = None

    encoded = ConfigFile("artifact", date(2026, 8, 4), None).to_toml()
    assert "comment" not in encoded
    assert ConfigFile.from_toml(encoded) == ConfigFile("artifact", date(2026, 8, 4), None)


@pytest.mark.depends_on('test_tuple_and_set_fields_use_basic_collection_forms', 'test_to_dict_serializes_primitive_dataclass_fields', 'test_from_dict_deserializes_primitive_dataclass_fields')
def test_messagepack_mixin_round_trip_preserves_binary_fields():
    """Seam: protocol handoff between MessagePack bytes and dataclass conversion."""
    @dataclass
    class Blob(DataClassMessagePackMixin):
        name: str
        payload: bytes
        mutable: bytearray

    original = Blob("packet", b"\x01\x02", bytearray(b"\x03\x04"))
    encoded = original.to_msgpack()
    assert isinstance(encoded, bytes)
    assert Blob.from_msgpack(encoded) == original


@pytest.mark.depends_on("test_field_option_alias_controls_input_key", "test_config_aliases_and_serialize_by_alias_control_output_keys")
def test_field_alias_takes_precedence_over_config_alias():
    """Seam: config interaction between field metadata and Config aliases."""
    @dataclass
    class Record(DataClassDictMixin):
        value: int = field(metadata=field_options(alias="fieldWire"))

        class Config(BaseConfig):
            aliases = {"value": "configWire"}
            serialize_by_alias = True

    assert Record(5).to_dict() == {"fieldWire": 5}
    assert Record.from_dict({"fieldWire": 6}) == Record(6)


@pytest.mark.depends_on("test_allow_deserialization_not_by_alias_accepts_field_names", "test_field_option_alias_controls_input_key")
def test_alias_input_mode_accepts_alias_and_field_name_but_still_requires_one():
    """Seam: error propagation between alias fallback and missing-field detection."""
    @dataclass
    class Record(DataClassDictMixin):
        value: int = field(metadata=field_options(alias="wireValue"))

        class Config(BaseConfig):
            allow_deserialization_not_by_alias = True

    assert Record.from_dict({"wireValue": 10}) == Record(10)
    assert Record.from_dict({"value": 11}) == Record(11)
    with pytest.raises(MissingField):
        Record.from_dict({"other": 12})


@pytest.mark.depends_on("test_forbid_extra_keys_config_raises_extra_keys_error", "test_field_option_alias_controls_input_key")
def test_forbid_extra_keys_checks_alias_aware_input_projection():
    """Seam: error propagation between extra-key checking and alias mapping."""
    @dataclass
    class Strict(DataClassDictMixin):
        value: int = field(metadata=field_options(alias="wireValue"))

        class Config(BaseConfig):
            forbid_extra_keys = True

    with pytest.raises(ExtraKeysError) as exc_info:
        Strict.from_dict({"wireValue": 3, "value": 4})
    assert exc_info.value.extra_keys == {"value"}


@pytest.mark.depends_on("test_config_serialization_strategy_applies_to_registered_type", "test_serializable_type_with_annotations_transforms_nested_values")
def test_strategy_annotations_convert_before_custom_deserialize_and_after_serialize():
    """Seam: protocol handoff between strategy annotations and field conversion."""
    class TimestampStrategy(SerializationStrategy, use_annotations=True):
        def serialize(self, value: datetime) -> float:
            return value.timestamp()

        def deserialize(self, value: float) -> datetime:
            return datetime.fromtimestamp(value, timezone.utc)

    @dataclass
    class Stamp(DataClassDictMixin):
        when: datetime

        class Config(BaseConfig):
            serialization_strategy = {datetime: TimestampStrategy()}

    loaded = Stamp.from_dict({"when": "1783296000"})
    assert loaded == Stamp(datetime(2026, 7, 6, tzinfo=timezone.utc))
    assert loaded.to_dict() == {"when": 1783296000.0}


@pytest.mark.depends_on("test_serialization_strategy_match_subclasses_handles_enum_subclass", "test_config_serialization_strategy_applies_to_registered_type")
def test_more_specific_strategy_overrides_matching_base_strategy():
    """Seam: config interaction between subclass matching and exact-type strategy lookup."""
    class BaseEnumStrategy(SerializationStrategy, match_subclasses=True):
        def serialize(self, value: Enum) -> str:
            return f"base:{value.name}"

        def deserialize(self, value: str) -> Enum:
            return Tone[value.removeprefix("base:")]

    class ToneValueStrategy(SerializationStrategy):
        def serialize(self, value: Tone) -> str:
            return value.value

        def deserialize(self, value: str) -> Tone:
            return Tone(value)

    @dataclass
    class Choice(DataClassDictMixin):
        tone: Tone

        class Config(BaseConfig):
            serialization_strategy = {Enum: BaseEnumStrategy(), Tone: ToneValueStrategy()}

    assert Choice(Tone.bright).to_dict() == {"tone": "bright"}
    assert Choice.from_dict({"tone": "calm"}) == Choice(Tone.calm)


@pytest.mark.depends_on("test_omit_none_config_removes_none_fields_from_output", "test_basic_encoder_serializes_typed_shape_to_basic_form")
def test_dialect_argument_overrides_config_when_code_generation_option_enabled():
    """Seam: config interaction between default Config and per-call dialect."""
    class KeepNone(Dialect):
        omit_none = False

    class DropNone(Dialect):
        omit_none = True

    @dataclass
    class Maybe(DataClassDictMixin):
        value: int | None

        class Config(BaseConfig):
            code_generation_options = [ADD_DIALECT_SUPPORT]
            dialect = KeepNone

    assert Maybe(None).to_dict() == {"value": None}
    assert Maybe(None).to_dict(dialect=DropNone) == {}


@pytest.mark.depends_on("test_config_aliases_and_serialize_by_alias_control_output_keys", "test_field_option_alias_controls_input_key")
def test_by_alias_keyword_overrides_config_when_option_enabled():
    """Seam: config interaction between generated keyword arguments and alias policy."""
    @dataclass
    class Record(DataClassDictMixin):
        public_name: str = field(metadata=field_options(alias="publicName"))

        class Config(BaseConfig):
            code_generation_options = [TO_DICT_ADD_BY_ALIAS_FLAG]
            serialize_by_alias = False

    assert Record("Ada").to_dict() == {"public_name": "Ada"}
    assert Record("Ada").to_dict(by_alias=True) == {"publicName": "Ada"}


@pytest.mark.depends_on("test_omit_none_config_removes_none_fields_from_output", "test_omit_default_config_removes_default_equal_fields")
def test_omit_none_keyword_overrides_config_when_option_enabled():
    """Seam: config interaction between generated omit_none keyword and field projection."""
    @dataclass
    class Maybe(DataClassDictMixin):
        value: int | None

        class Config(BaseConfig):
            code_generation_options = [TO_DICT_ADD_OMIT_NONE_FLAG]
            omit_none = False

    assert Maybe(None).to_dict() == {"value": None}
    assert Maybe(None).to_dict(omit_none=True) == {}


@pytest.mark.depends_on('test_field_option_serialize_callable_controls_output_value', 'test_to_dict_serializes_primitive_dataclass_fields', 'test_from_dict_deserializes_primitive_dataclass_fields')
def test_serialization_context_reaches_pre_and_post_hooks_when_enabled():
    """Seam: protocol handoff between generated context argument and serialization hooks."""
    @dataclass
    class Message(DataClassDictMixin):
        text: str

        class Config(BaseConfig):
            code_generation_options = [ADD_SERIALIZATION_CONTEXT]

        def __pre_serialize__(self, context: dict[str, str] | None = None) -> "Message":
            prefix = "" if context is None else context["prefix"]
            return Message(prefix + self.text)

        def __post_serialize__(self, data: dict[Any, Any], context: dict[str, str] | None = None) -> dict[Any, Any]:
            data["suffix"] = "" if context is None else context["suffix"]
            return data

    assert Message("body").to_dict(context={"prefix": "pre-", "suffix": "-post"}) == {
        "text": "pre-body",
        "suffix": "-post",
    }


@pytest.mark.depends_on("test_nested_dataclass_from_dict_builds_nested_objects", "test_nested_dataclass_to_dict_serializes_nested_public_shape")
def test_deserialization_and_serialization_hooks_wrap_nested_conversion():
    """Seam: lifecycle crossing through pre/post deserialization and serialization hooks."""
    @dataclass
    class Wrapped(DataClassDictMixin):
        leaf: Leaf

        @classmethod
        def __pre_deserialize__(cls, data: dict[Any, Any]) -> dict[Any, Any]:
            return {"leaf": data["payload"]}

        @classmethod
        def __post_deserialize__(cls, obj: "Wrapped") -> "Wrapped":
            return Wrapped(Leaf(obj.leaf.code.upper(), obj.leaf.count))

        def __post_serialize__(self, data: dict[Any, Any]) -> dict[Any, Any]:
            return {"payload": data["leaf"]}

    obj = Wrapped.from_dict({"payload": {"code": "ash", "count": 2}})
    assert obj == Wrapped(Leaf("ASH", 2))
    assert obj.to_dict() == {"payload": {"code": "ASH", "count": 2}}


@pytest.mark.depends_on("test_json_schema_for_dataclass_includes_properties_and_required_fields", "test_json_schema_for_primitive_types_uses_expected_type_names")
def test_schema_builder_builds_refs_and_later_definitions_from_same_context():
    """Seam: state consistency between JSONSchemaBuilder.build and get_definitions."""
    builder = JSONSchemaBuilder(OPEN_API_3_1)
    User.__annotations__["id"] = UUID
    schema = builder.build(list[User]).to_dict()
    definitions = builder.get_definitions().to_dict()
    assert schema == {"type": "array", "items": {"$ref": "#/components/schemas/User"}}
    assert definitions["User"]["properties"]["id"] == {"type": "string", "format": "uuid"}


@pytest.mark.depends_on("test_json_schema_annotations_apply_validation_keywords", "test_json_schema_for_dataclass_includes_properties_and_required_fields")
def test_schema_generation_combines_dataclass_fields_and_annotated_constraints():
    """Seam: protocol handoff between dataclass introspection and Annotated schema metadata."""
    @dataclass
    class Limits:
        score: Annotated[int, Maximum(99)]

    schema = build_json_schema(Limits).to_dict()
    assert schema["properties"]["score"] == {"type": "integer", "maximum": 99}
    assert schema["required"] == ["score"]


@pytest.mark.depends_on("test_json_schema_for_dataclass_includes_properties_and_required_fields", "test_json_schema_field_metadata_adds_descriptions_and_constraints")
def test_schema_overlay_keeps_regular_type_and_adds_content_keywords():
    """Seam: protocol handoff between automatic schema and JSONSchema overlay."""
    @dataclass
    class Upload:
        payload: Annotated[
            bytes,
            JSONSchema(contentEncoding="base64", contentMediaType="application/octet-stream"),
        ]

    schema = build_json_schema(Upload).to_dict()
    assert schema["properties"]["payload"] == {
        "type": "string",
        "format": "base64",
        "contentEncoding": "base64",
        "contentMediaType": "application/octet-stream",
    }


@pytest.mark.depends_on("test_json_schema_for_dataclass_includes_properties_and_required_fields", "test_json_encoder_and_decoder_handle_dataclass_lists")
def test_schema_and_json_codec_project_same_dataclass_field_names():
    """CVI-1: dataclass field names must agree across JSON codec and JSON Schema projections."""
    @dataclass
    class Device:
        id: UUID
        label: str

    schema = build_json_schema(Device).to_dict()
    encoded = JSONEncoder(Device).encode(Device(UUID("12345678-1234-5678-1234-567812345678"), "sensor"))
    assert sorted(schema["properties"]) == ["id", "label"]
    assert encoded == '{"id": "12345678-1234-5678-1234-567812345678", "label": "sensor"}'


@pytest.mark.depends_on("test_config_serialization_strategy_applies_to_registered_type", "test_json_schema_for_dataclass_includes_properties_and_required_fields")
def test_custom_strategy_changes_dict_and_json_but_schema_keeps_declared_type():
    """CVI-2: serialization strategy must affect value projection while schema reflects declared field type."""
    @dataclass
    class Invoice(DataClassDictMixin):
        amount: Decimal

        class Config(BaseConfig):
            serialization_strategy = {Decimal: DecimalAsCents()}

    assert Invoice(Decimal("4.20")).to_dict() == {"amount": 420}
    assert JSONEncoder(Invoice).encode(Invoice(Decimal("4.20"))) == '{"amount": 420}'
    assert build_json_schema(Invoice).to_dict()["properties"]["amount"] == {"type": "integer"}


@pytest.mark.depends_on("test_basic_encoder_serializes_typed_shape_to_basic_form", "test_basic_decoder_deserializes_typed_shape_from_basic_form")
def test_basic_codec_and_dict_mixin_agree_on_nested_basic_form():
    """CVI-3: BasicEncoder and DataClassDictMixin must expose the same basic form."""
    @dataclass
    class Bundle(DataClassDictMixin):
        leaf: Leaf
        when: date

    obj = Bundle(Leaf("elm", 6), date(2026, 8, 4))
    encoded = BasicEncoder(Bundle).encode(obj)
    assert encoded == obj.to_dict()
    assert BasicDecoder(Bundle).decode(encoded) == Bundle.from_dict(encoded)


@pytest.mark.depends_on('test_json_convenience_functions_encode_and_decode_typed_values', 'test_config_aliases_and_serialize_by_alias_control_output_keys', 'test_field_option_alias_controls_input_key')
def test_json_mixin_and_dict_mixin_agree_on_alias_projection():
    """CVI-4: JSON mixin and dict mixin must use the same alias-aware projection."""
    @dataclass
    class Contact(DataClassJSONMixin):
        public_name: str = field(metadata=field_options(alias="publicName"))

        class Config(BaseConfig):
            serialize_by_alias = True

    obj = Contact("Katherine")
    assert obj.to_dict() == {"publicName": "Katherine"}
    assert obj.to_json() == '{"publicName": "Katherine"}'
    assert Contact.from_json(obj.to_json()) == Contact.from_dict(obj.to_dict())


@pytest.mark.depends_on('test_omit_none_config_removes_none_fields_from_output', 'test_basic_encoder_serializes_typed_shape_to_basic_form', 'test_config_serialization_strategy_applies_to_registered_type')
def test_dialect_merge_combines_strategy_and_omit_policy():
    """Seam: config interaction between Dialect.merge strategy and omit policies."""
    class AmountDialect(Dialect):
        serialization_strategy = {Decimal: DecimalAsCents()}
        omit_none = False

    class DropNoneDialect(Dialect):
        omit_none = True

    merged = AmountDialect.merge(DropNoneDialect)

    @dataclass
    class Invoice(DataClassDictMixin):
        amount: Decimal
        note: str | None

        class Config(BaseConfig):
            code_generation_options = [ADD_DIALECT_SUPPORT]

    assert Invoice(Decimal("6.70"), None).to_dict(dialect=merged) == {"amount": 670}


@pytest.mark.depends_on('test_json_encoder_and_decoder_handle_dataclass_lists', 'test_field_option_alias_controls_input_key', 'test_omit_none_config_removes_none_fields_from_output', 'test_basic_encoder_serializes_typed_shape_to_basic_form')
def test_codec_default_dialect_applies_without_per_call_dialect():
    """Seam: protocol handoff between codec construction defaults and dataclass dialect support."""
    class CompactDateDialect(Dialect):
        serialization_strategy = {date: DateAsCompactString()}

    @dataclass
    class Event:
        when: date

    encoder = JSONEncoder(Event, default_dialect=CompactDateDialect)
    decoder = JSONDecoder(Event, default_dialect=CompactDateDialect)
    encoded = encoder.encode(Event(date(2026, 8, 4)))
    assert encoded == '{"when": "20260804"}'
    assert decoder.decode(encoded) == Event(date(2026, 8, 4))


@pytest.mark.depends_on("test_from_dict_invalid_integer_value_raises_invalid_field_value", "test_json_encoder_and_decoder_handle_dataclass_lists")
def test_json_decoder_propagates_field_conversion_errors():
    """Seam: error propagation from JSON decoder into dataclass field conversion."""
    @dataclass
    class Item:
        count: int

    with pytest.raises((InvalidFieldValue, ValueError)):
        JSONDecoder(Item).decode('{"count": "many"}')


@pytest.mark.depends_on("test_json_schema_for_dataclass_includes_properties_and_required_fields", "test_field_option_alias_controls_input_key")
def test_schema_generation_uses_alias_metadata_for_property_names():
    """CVI-5: field alias metadata must be visible in serialized data and schema properties."""
    @dataclass
    class Contact(DataClassDictMixin):
        public_name: str = field(metadata=field_options(alias="publicName"))

        class Config(BaseConfig):
            serialize_by_alias = True

    assert Contact("Ada").to_dict() == {"publicName": "Ada"}
    schema = build_json_schema(Contact).to_dict()
    assert sorted(schema["properties"]) == ["publicName"]


@pytest.mark.depends_on('test_forbid_extra_keys_config_raises_extra_keys_error', 'test_json_convenience_functions_encode_and_decode_typed_values', 'test_config_aliases_and_serialize_by_alias_control_output_keys')
def test_json_mixin_propagates_forbid_extra_keys_errors_from_dict_layer():
    """Seam: error propagation from JSON text into Config validation."""
    @dataclass
    class Strict(DataClassJSONMixin):
        name: str

        class Config(BaseConfig):
            forbid_extra_keys = True

    with pytest.raises(ExtraKeysError):
        Strict.from_json('{"name": "Ada", "unused": true}')


@pytest.mark.depends_on('test_sort_keys_config_orders_serialized_mapping_keys', 'test_json_convenience_functions_encode_and_decode_typed_values', 'test_config_aliases_and_serialize_by_alias_control_output_keys')
def test_sort_keys_config_is_reflected_in_json_output_order():
    """CVI-6: sorted dict projection must be the projection encoded by JSON mixins."""
    @dataclass
    class Sorted(DataClassJSONMixin):
        zebra: int
        amber: int

        class Config(BaseConfig):
            sort_keys = True

    assert list(Sorted(1, 2).to_dict()) == ["amber", "zebra"]
    assert Sorted(1, 2).to_json() == '{"amber": 2, "zebra": 1}'


@pytest.mark.depends_on('test_serializable_type_uses_custom_serialize_deserialize_methods', 'test_basic_encoder_serializes_typed_shape_to_basic_form', 'test_basic_decoder_deserializes_typed_shape_from_basic_form')
def test_serializable_type_projection_is_shared_by_dict_and_basic_codec():
    """CVI-7: SerializableType hooks must feed both mixin and codec projections."""
    class Token(SerializationStrategy):
        def serialize(self, value: Decimal) -> str:
            return f"DEC:{value}"

        def deserialize(self, value: str) -> Decimal:
            return Decimal(value.removeprefix("DEC:"))

    @dataclass
    class Record(DataClassDictMixin):
        amount: Decimal

        class Config(BaseConfig):
            serialization_strategy = {Decimal: Token()}

    obj = Record(Decimal("3.14"))
    assert obj.to_dict() == {"amount": "DEC:3.14"}
    assert BasicEncoder(Record).encode(obj) == {"amount": "DEC:3.14"}
    assert BasicDecoder(Record).decode({"amount": "DEC:3.14"}) == obj


@pytest.mark.depends_on("test_json_schema_annotations_apply_validation_keywords", "test_json_schema_field_metadata_adds_descriptions_and_constraints")
def test_schema_builder_definitions_keep_annotation_constraints():
    """Seam: lifecycle crossing from repeated builder builds to accumulated definitions."""
    Metric.__annotations__["score"] = Annotated[int, Maximum(10)]
    builder = JSONSchemaBuilder(OPEN_API_3_1)
    assert builder.build(Metric).to_dict() == {"$ref": "#/components/schemas/Metric"}
    definitions = builder.get_definitions().to_dict()
    assert definitions["Metric"]["properties"]["score"] == {"type": "integer", "maximum": 10}


@pytest.mark.depends_on("test_json_schema_for_primitive_types_uses_expected_type_names", "test_json_schema_for_dataclass_includes_properties_and_required_fields")
def test_schema_with_dialect_uri_and_ref_prefix_controls_public_reference_view():
    """Seam: config interaction among dialect URI, all_refs, definitions, and ref_prefix."""
    Account.__annotations__["id"] = UUID
    schema = build_json_schema(
        list[Account],
        all_refs=True,
        with_definitions=False,
        with_dialect_uri=True,
        ref_prefix="#/components/examples",
    ).to_dict()
    assert schema == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "array",
        "items": {"$ref": "#/components/examples/Account"},
    }


@pytest.mark.depends_on("test_field_option_alias_controls_input_key", "test_json_schema_for_dataclass_includes_properties_and_required_fields")
def test_schema_required_list_tracks_alias_names_for_required_fields():
    """CVI-8: required-field schema names must match alias-aware external keys."""
    @dataclass
    class RequiredAliased:
        internal_name: int = field(metadata=field_options(alias="externalName"))

    schema = build_json_schema(RequiredAliased).to_dict()
    assert schema["required"] == ["externalName"]
    assert sorted(schema["properties"]) == ["externalName"]


@pytest.mark.depends_on('test_tuple_and_set_fields_use_basic_collection_forms', 'test_to_dict_serializes_primitive_dataclass_fields', 'test_from_dict_deserializes_primitive_dataclass_fields', 'test_json_convenience_functions_encode_and_decode_typed_values', 'test_config_aliases_and_serialize_by_alias_control_output_keys')
def test_binary_model_uses_format_specific_wire_types_consistently():
    """Seam: protocol handoff across dict, JSON-compatible, and MessagePack projections."""
    @dataclass
    class Blob(DataClassMessagePackMixin, DataClassJSONMixin):
        payload: bytes

    obj = Blob(b"stage-two")
    assert obj.to_dict() == {"payload": "c3RhZ2UtdHdv\n"}
    assert Blob.from_msgpack(obj.to_msgpack()) == obj
    assert Blob.from_json(obj.to_json()) == obj
