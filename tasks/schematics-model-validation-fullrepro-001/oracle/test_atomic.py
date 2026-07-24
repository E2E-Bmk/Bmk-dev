"""Atomic public-API behavioral tests for schematics.

Each test exercises a single public API entry point and a single behavior.
"""
import datetime
import decimal
import uuid

import pytest

from schematics.models import Model
from schematics.exceptions import ConversionError, DataError, ValidationError
from schematics.types import (
    BooleanType, DateTimeType, DateType, DecimalType, DictType, EmailType,
    FloatType, GeoPointType, IntType, IPv4Type, ListType, LongType, MD5Type,
    ModelType, SHA1Type, StringType, TimedeltaType, UTCDateTimeType, UUIDType,
    URLType,
)


# ── StringType ────────────────────────────────────────────────────

def test_string_converts_integer_to_text():
    assert StringType().to_native(7) == "7"


def test_string_min_length_rejects_short_value():
    with pytest.raises(ValidationError):
        StringType(min_length=2).validate("x")


def test_string_regex_rejects_nonmatching_value():
    with pytest.raises(ValidationError):
        StringType(regex=r"^[A-Z]+$").validate("lower")


def test_string_max_length_rejects_long_value():
    with pytest.raises(ValidationError):
        StringType(max_length=3).validate("toolong")


# ── IntType / LongType / FloatType ────────────────────────────────

def test_int_converts_decimal_text():
    assert IntType().to_native("12") == 12


def test_int_rejects_out_of_range_value():
    with pytest.raises(ValidationError):
        IntType(min_value=1).validate(0)


def test_int_rejects_above_max():
    with pytest.raises(ValidationError):
        IntType(max_value=10).validate(11)


def test_float_converts_numeric_text():
    assert FloatType().to_native("2.5") == 2.5


def test_long_behaves_as_integer_variant():
    assert LongType().to_native("12") == 12


# ── DecimalType ──────────────────────────────────────────────────

def test_decimal_has_native_decimal_and_primitive_text():
    field = DecimalType()
    native = field.to_native("1.25")
    assert native == decimal.Decimal("1.25")
    assert field.to_primitive(native) == "1.25"


# ── BooleanType ──────────────────────────────────────────────────

def test_boolean_accepts_false_digit():
    assert BooleanType().to_native("0") is False


def test_boolean_accepts_true_text():
    assert BooleanType().to_native("true") is True


def test_boolean_accepts_integer_forms():
    assert (BooleanType().to_native(1), BooleanType().to_native(0)) == (True, False)


def test_boolean_accepts_documented_string_forms():
    assert (BooleanType().to_native("True"), BooleanType().to_native("false")) == (True, False)


def test_boolean_rejects_unrecognized_text():
    with pytest.raises(ConversionError):
        BooleanType().to_native("sometimes")


# ── DateType ──────────────────────────────────────────────────────

def test_date_has_iso_primitive_value():
    value = DateType().to_native("2024-02-03")
    assert value == datetime.date(2024, 2, 3)
    assert DateType().to_primitive(value) == "2024-02-03"


def test_date_rejects_unparseable_value():
    with pytest.raises(ConversionError):
        DateType().to_native("not-a-date")


# ── DateTimeType ──────────────────────────────────────────────────

def test_datetime_to_native_parses_iso_text():
    value = DateTimeType().to_native("2024-02-03T04:05:06")
    assert value == datetime.datetime(2024, 2, 3, 4, 5, 6)


def test_datetime_primitive_round_trips_through_to_native():
    field = DateTimeType()
    value = datetime.datetime(2024, 2, 3, 4, 5, 6)
    assert field.to_native(field.to_primitive(value)) == value


def test_datetime_rejects_invalid_text():
    with pytest.raises(ConversionError):
        DateTimeType().to_native("not-a-date")


# ── UTCDateTimeType ──────────────────────────────────────────────

def test_utc_datetime_normalizes_offset_to_naive_utc():
    value = UTCDateTimeType().to_native("2024-02-03T04:05:06+02:00")
    assert value == datetime.datetime(2024, 2, 3, 2, 5, 6)
    assert UTCDateTimeType().to_primitive(value).endswith("Z")


# ── TimedeltaType ─────────────────────────────────────────────────

def test_timedelta_converts_seconds():
    assert TimedeltaType().to_native(90) == datetime.timedelta(seconds=90)


def test_timedelta_precision_selects_documented_unit():
    assert TimedeltaType(precision="minutes").to_native(2) == datetime.timedelta(minutes=2)
    assert TimedeltaType(precision="days").to_native(1) == datetime.timedelta(days=1)


# ── UUIDType ──────────────────────────────────────────────────────

def test_uuid_has_uuid_native_value():
    value = UUIDType().to_native("12345678-1234-5678-1234-567812345678")
    assert value == uuid.UUID("12345678-1234-5678-1234-567812345678")


def test_uuid_has_text_primitive_value():
    value = uuid.UUID("12345678-1234-5678-1234-567812345678")
    assert UUIDType().to_primitive(value) == str(value)


# ── Hash types ────────────────────────────────────────────────────

def test_md5_accepts_correct_digest_length():
    digest = "d41d8cd98f00b204e9800998ecf8427e"
    assert MD5Type().to_native(digest) == digest


def test_md5_rejects_wrong_digest_length():
    with pytest.raises((ConversionError, ValidationError)):
        MD5Type().to_native("abc")


def test_sha1_rejects_wrong_digest_length():
    with pytest.raises((ConversionError, ValidationError)):
        SHA1Type().to_native("tooshort")


# ── GeoPointType ──────────────────────────────────────────────────

def test_geopoint_accepts_two_element_numeric_pair():
    assert GeoPointType().to_native((45.0, -122.5)) == (45.0, -122.5)


def test_geopoint_rejects_out_of_range_coordinate():
    with pytest.raises(ValidationError):
        GeoPointType().validate([100, 20])


# ── Network/address types ────────────────────────────────────────

def test_ipv4_rejects_malformed_value():
    with pytest.raises((ConversionError, ValidationError)):
        IPv4Type().validate("999.1.1.1")


def test_email_rejects_malformed_value():
    with pytest.raises((ConversionError, ValidationError)):
        EmailType().validate("not-an-address")


def test_url_rejects_malformed_value():
    with pytest.raises((ConversionError, ValidationError)):
        URLType().validate("not a url")


# ── Compound types ────────────────────────────────────────────────

def test_list_type_converts_each_element():
    assert ListType(IntType()).to_native(["1", 2]) == [1, 2]


def test_list_type_enforces_maximum_size():
    with pytest.raises(ValidationError):
        ListType(IntType(), max_size=1).validate([1, 2])


def test_dict_type_converts_each_value():
    assert DictType(IntType()).to_native({"a": "1"}) == {"a": 1}


def test_dict_type_rejects_non_mapping_input():
    with pytest.raises(ConversionError):
        DictType(IntType()).validate([("a", 1)])


# ── Model instance access ────────────────────────────────────────

def test_model_instance_exposes_converted_field_values():
    class Item(Model):
        name = StringType()
        quantity = IntType()

    item = Item({"name": "pen", "quantity": "5"})
    assert (item.name, item.quantity) == ("pen", 5)


def test_model_keys_and_items_follow_declaration_order():
    class Item(Model):
        name = StringType()
        quantity = IntType()

    item = Item({"name": "pen", "quantity": "5"})
    assert list(item.keys()) == ["name", "quantity"]
    assert list(item.items()) == [("name", "pen"), ("quantity", 5)]


def test_model_exports_native_and_primitive_mappings():
    class Priced(Model):
        name = StringType()
        amount = DecimalType()

    priced = Priced({"name": "pen", "amount": "1.25"})
    assert priced.to_native() == {"name": "pen", "amount": decimal.Decimal("1.25")}
    assert priced.to_primitive() == {"name": "pen", "amount": "1.25"}
