"""Atomic public-behavior conformance checks."""

# Spec2Repo oracle candidates rewritten from upstream public-behavior tests.
import datetime
import decimal
import uuid

import pytest

from schematics import Model
from schematics.exceptions import ConversionError, DataError, UnknownFieldError, ValidationError
from schematics.transforms import blacklist, whitelist
from schematics.types import (
    BooleanType, DateTimeType, DateType, DecimalType, DictType, EmailType,
    GeoPointType, IntType, IPv4Type, ListType, MD5Type, ModelType,
    StringType, TimedeltaType, UUIDType, URLType,
)


class Child(Model):
    count = IntType(required=True)


class Record(Model):
    name = StringType(required=True, serialized_name="label")
    count = IntType(default=3)
    amount = DecimalType()

def test_boolean_accepts_false_digit():
    assert BooleanType().to_native("0") is False

def test_boolean_accepts_true_text():
    assert BooleanType().to_native("true") is True

def test_boolean_rejects_unrecognized_text():
    with pytest.raises(ConversionError):
        BooleanType().to_native("sometimes")

def test_date_has_iso_primitive_value():
    value = DateType().to_native("2024-02-03")
    assert value == datetime.date(2024, 2, 3)
    assert DateType().to_primitive(value) == "2024-02-03"

def test_datetime_rejects_invalid_text():
    with pytest.raises(ConversionError):
        DateTimeType().to_native("not-a-date")

def test_decimal_has_native_decimal_and_primitive_text():
    field = DecimalType()
    native = field.to_native("1.25")
    assert native == decimal.Decimal("1.25")
    assert field.to_primitive(native) == "1.25"

def test_dict_type_converts_each_value():
    assert DictType(IntType()).to_native({"a": "1"}) == {"a": 1}

def test_dict_type_rejects_non_mapping_input():
    with pytest.raises(ConversionError):
        DictType(IntType()).validate([("a", 1)])

def test_email_rejects_malformed_value():
    with pytest.raises((ConversionError, ValidationError)):
        EmailType().validate("not-an-address")

def test_geopoint_rejects_out_of_range_coordinate():
    with pytest.raises(ValidationError):
        GeoPointType().validate([100, 20])

def test_int_converts_decimal_text():
    assert IntType().to_native("12") == 12

def test_int_rejects_out_of_range_value():
    with pytest.raises(ValidationError):
        IntType(min_value=1).validate(0)

def test_ipv4_rejects_malformed_value():
    with pytest.raises((ConversionError, ValidationError)):
        IPv4Type().validate("999.1.1.1")

def test_list_type_converts_each_element():
    assert ListType(IntType()).to_native(["1", 2]) == [1, 2]

def test_list_type_enforces_maximum_size():
    with pytest.raises(ValidationError):
        ListType(IntType(), max_size=1).validate([1, 2])

def test_md5_rejects_wrong_digest_length():
    with pytest.raises((ConversionError, ValidationError)):
        MD5Type().to_native("abc")

def test_string_converts_integer_to_text():
    assert StringType().to_native(7) == "7"

def test_string_min_length_rejects_short_value():
    with pytest.raises(ValidationError):
        StringType(min_length=2).validate("x")

def test_string_regex_rejects_nonmatching_value():
    with pytest.raises(ValidationError):
        StringType(regex=r"^[A-Z]+$").validate("lower")

def test_timedelta_converts_seconds():
    assert TimedeltaType().to_native(90) == datetime.timedelta(seconds=90)

def test_url_rejects_malformed_value():
    with pytest.raises((ConversionError, ValidationError)):
        URLType().validate("not a url")

def test_uuid_has_text_primitive_value():
    value = uuid.UUID("12345678-1234-5678-1234-567812345678")
    assert UUIDType().to_primitive(value) == str(value)

def test_uuid_has_uuid_native_value():
    value = UUIDType().to_native("12345678-1234-5678-1234-567812345678")
    assert value == uuid.UUID("12345678-1234-5678-1234-567812345678")
