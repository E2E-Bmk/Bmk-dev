"""Atomic tests for marshmallow-schema-fullrepro-001.

Each test verifies ONE public API entry point, ONE behavior.
IMPORTANT: This task had -11.7pp gap. Atomic tests must be truly single-API.
No cross-module tests (e.g., no load→dump consistency checks here).
"""

from __future__ import annotations

import datetime as dt
import decimal
import enum
import ipaddress
import uuid
from dataclasses import dataclass

import pytest

from marshmallow import (
    EXCLUDE,
    INCLUDE,
    RAISE,
    Schema,
    SchemaOpts,
    ValidationError,
    fields,
    validate,
    validates,
    validates_schema,
)


@dataclass
class Person:
    name: str
    email: str
    age: int = 0


# --- Schema.load: single field type conversions ---


def test_load_str_field_accepts_string():
    class S(Schema):
        name = fields.Str()

    assert S().load({"name": "Ada"}) == {"name": "Ada"}


def test_load_int_field_coerces_string_to_int():
    class S(Schema):
        count = fields.Int()

    assert S().load({"count": "7"}) == {"count": 7}


def test_load_float_field_coerces_string_to_float():
    class S(Schema):
        ratio = fields.Float()

    assert S().load({"ratio": "2.5"}) == {"ratio": 2.5}


def test_load_decimal_field_coerces_string():
    class S(Schema):
        amount = fields.Decimal()

    loaded = S().load({"amount": "3.14"})
    assert loaded["amount"] == decimal.Decimal("3.14")


def test_load_bool_field_recognizes_truthy_falsy():
    class S(Schema):
        active = fields.Bool()

    assert S().load({"active": "true"}) == {"active": True}
    assert S().load({"active": "false"}) == {"active": False}


def test_load_date_field():
    class S(Schema):
        day = fields.Date()

    assert S().load({"day": "2024-03-15"}) == {"day": dt.date(2024, 3, 15)}


def test_load_datetime_field():
    class S(Schema):
        ts = fields.DateTime()

    loaded = S().load({"ts": "2024-03-15T10:30:00+00:00"})
    assert loaded["ts"].hour == 10


def test_load_time_field():
    class S(Schema):
        clock = fields.Time()

    assert S().load({"clock": "14:30:00"}) == {"clock": dt.time(14, 30, 0)}


def test_load_timedelta_field_seconds_precision():
    class S(Schema):
        delta = fields.TimeDelta(precision="seconds")

    assert S().load({"delta": 120}) == {"delta": dt.timedelta(seconds=120)}


def test_load_uuid_field():
    uid = uuid.UUID("abcdef12-3456-7890-abcd-ef1234567890")

    class S(Schema):
        id = fields.UUID()

    assert S().load({"id": str(uid)}) == {"id": uid}


def test_load_ip_field():
    class S(Schema):
        addr = fields.IP()

    assert S().load({"addr": "10.0.0.1"}) == {"addr": ipaddress.ip_address("10.0.0.1")}


def test_load_url_field_validates():
    class S(Schema):
        link = fields.Url()

    assert S().load({"link": "https://example.com/path"}) == {"link": "https://example.com/path"}


def test_load_email_field_validates():
    class S(Schema):
        email = fields.Email()

    assert S().load({"email": "ada@example.com"}) == {"email": "ada@example.com"}


def test_load_list_field():
    class S(Schema):
        tags = fields.List(fields.Str())

    assert S().load({"tags": ["a", "b"]}) == {"tags": ["a", "b"]}


def test_load_tuple_field():
    class S(Schema):
        point = fields.Tuple((fields.Int(), fields.Int()))

    assert S().load({"point": ["3", "4"]}) == {"point": (3, 4)}


def test_load_dict_field():
    class S(Schema):
        prefs = fields.Dict(keys=fields.Str(), values=fields.Int())

    assert S().load({"prefs": {"a": "1"}}) == {"prefs": {"a": 1}}


def test_load_raw_field_passes_through():
    class S(Schema):
        payload = fields.Raw()

    data = {"nested": [1, None]}
    assert S().load({"payload": data}) == {"payload": data}


def test_load_constant_field_ignores_input():
    class S(Schema):
        kind = fields.Constant("fixed")

    assert S().load({"kind": "anything"}) == {"kind": "fixed"}


def test_load_enum_field_by_value():
    class Color(enum.Enum):
        RED = "red"
        BLUE = "blue"

    class S(Schema):
        c = fields.Enum(Color, by_value=True)

    assert S().load({"c": "red"}) == {"c": Color.RED}


# --- Schema.load: defaults ---


def test_load_default_applied_when_field_absent():
    class S(Schema):
        name = fields.Str(load_default="anon")

    assert S().load({}) == {"name": "anon"}


def test_callable_load_default_called_each_time():
    counter = {"n": 0}

    def next_val():
        counter["n"] += 1
        return counter["n"]

    class S(Schema):
        v = fields.Int(load_default=next_val)

    schema = S()
    assert schema.load({}) == {"v": 1}
    assert schema.load({}) == {"v": 2}


def test_load_default_none_allows_none():
    class S(Schema):
        v = fields.Str(load_default=None)

    assert S().load({}) == {"v": None}
    assert S().load({"v": None}) == {"v": None}


def test_allow_none_false_rejects_none():
    class S(Schema):
        v = fields.Str(load_default="x", allow_none=False)

    with pytest.raises(ValidationError) as exc:
        S().load({"v": None})
    assert "v" in exc.value.messages


# --- Schema.load: required / validation errors ---


def test_required_field_missing_raises_validation_error():
    class S(Schema):
        email = fields.Email(required=True)

    with pytest.raises(ValidationError) as exc:
        S().load({})
    assert "email" in exc.value.messages


def test_validation_error_exposes_valid_data():
    class S(Schema):
        name = fields.Str()
        email = fields.Email(required=True)

    with pytest.raises(ValidationError) as exc:
        S().load({"name": "Ada", "email": "bad"})
    assert exc.value.valid_data == {"name": "Ada"}


def test_collection_errors_keyed_by_index():
    class S(Schema):
        v = fields.Int(required=True)

    with pytest.raises(ValidationError) as exc:
        S(many=True).load([{"v": 1}, {"v": "bad"}, {}])
    assert 1 in exc.value.messages or 2 in exc.value.messages


# --- Schema.dump: single operations ---


def test_dump_reads_from_dict():
    class S(Schema):
        name = fields.Str()
        age = fields.Int()

    assert S().dump({"name": "Ada", "age": 37}) == {"name": "Ada", "age": 37}


def test_dump_reads_from_object_attributes():
    class S(Schema):
        name = fields.Str()
        age = fields.Int()

    assert S().dump(Person("Ada", "a@example.com", 37)) == {"name": "Ada", "age": 37}


def test_dump_default_applied_when_attribute_absent():
    class S(Schema):
        created = fields.Date(dump_default=dt.date(2023, 1, 1))

    assert S().dump({}) == {"created": "2023-01-01"}


def test_dump_does_not_run_validators():
    def reject(v):
        raise ValidationError("invalid")

    class S(Schema):
        age = fields.Int(validate=reject)

    assert S().dump({"age": 5}) == {"age": 5}


def test_decimal_as_string_serializes_to_string():
    class S(Schema):
        v = fields.Decimal(as_string=True)

    assert S().dump({"v": decimal.Decimal("3.14")}) == {"v": "3.14"}


def test_enum_field_dumps_value():
    class Color(enum.Enum):
        RED = "red"

    class S(Schema):
        c = fields.Enum(Color, by_value=True)

    assert S().dump({"c": Color.RED}) == {"c": "red"}


# --- Schema.validate ---


def test_validate_returns_errors_without_raising():
    class S(Schema):
        email = fields.Email(required=True)

    errors = S().validate({"email": "bad"})
    assert "email" in errors


# --- Built-in validators ---


def test_range_validator_rejects_out_of_bounds():
    class S(Schema):
        n = fields.Int(validate=validate.Range(min=5, max=10))

    assert S().load({"n": 7}) == {"n": 7}
    with pytest.raises(ValidationError):
        S().load({"n": 3})


def test_length_validator_rejects_short_and_long():
    class S(Schema):
        s = fields.Str(validate=validate.Length(min=2, max=5))

    assert S().load({"s": "abc"}) == {"s": "abc"}
    with pytest.raises(ValidationError):
        S().load({"s": "a"})
    with pytest.raises(ValidationError):
        S().load({"s": "abcdef"})


def test_oneof_validator_rejects_invalid_choice():
    class S(Schema):
        role = fields.Str(validate=validate.OneOf(["admin", "user"]))

    assert S().load({"role": "admin"}) == {"role": "admin"}
    with pytest.raises(ValidationError):
        S().load({"role": "guest"})


def test_noneof_validator_rejects_forbidden():
    class S(Schema):
        name = fields.Str(validate=validate.NoneOf(["root", "admin"]))

    assert S().load({"name": "alice"}) == {"name": "alice"}
    with pytest.raises(ValidationError):
        S().load({"name": "root"})


def test_regexp_validator():
    class S(Schema):
        code = fields.Str(validate=validate.Regexp(r"^[A-Z]{3}$"))

    assert S().load({"code": "ABC"}) == {"code": "ABC"}
    with pytest.raises(ValidationError):
        S().load({"code": "ab"})


def test_equal_validator():
    class S(Schema):
        v = fields.Int(validate=validate.Equal(42))

    assert S().load({"v": 42}) == {"v": 42}
    with pytest.raises(ValidationError):
        S().load({"v": 41})


def test_and_validator_collects_all_failures():
    class S(Schema):
        v = fields.Str(validate=validate.And(
            validate.Length(min=3), validate.Regexp(r"^[A-Z]+$")
        ))

    with pytest.raises(ValidationError) as exc:
        S().load({"v": "a"})
    assert len(exc.value.messages["v"]) >= 2


def test_multiple_validators_collect_failures():
    class S(Schema):
        n = fields.Int(validate=[validate.Range(min=10), validate.Range(max=5)])

    with pytest.raises(ValidationError) as exc:
        S().load({"n": 7})
    assert len(exc.value.messages["n"]) >= 2


# --- only / exclude ---


def test_only_limits_fields():
    class S(Schema):
        name = fields.Str()
        email = fields.Email()
        age = fields.Int()

    schema = S(only=("name",))
    assert set(schema.fields) == {"name"}


def test_exclude_removes_fields():
    class S(Schema):
        name = fields.Str()
        age = fields.Int()

    schema = S(exclude=("age",))
    assert "age" not in schema.fields


def test_invalid_only_field_raises_at_construction():
    class S(Schema):
        name = fields.Str()

    with pytest.raises(ValueError):
        S(only=("nonexistent",))


# --- attribute / data_key ---


def test_attribute_reads_different_name_on_dump():
    class S(Schema):
        display_name = fields.Str(attribute="name")

    assert S().dump(Person("Ada", "a@e.com")) == {"display_name": "Ada"}


def test_dump_only_omitted_from_load():
    class S(Schema):
        name = fields.Str()
        secret = fields.Str(dump_only=True)

    schema = S(unknown=EXCLUDE)
    assert schema.load({"name": "Ada", "secret": "x"}) == {"name": "Ada"}


def test_load_only_omitted_from_dump():
    class S(Schema):
        name = fields.Str()
        password = fields.Str(load_only=True)

    assert S().dump({"name": "Ada", "password": "x"}) == {"name": "Ada"}


# --- Function / Method fields ---


def test_function_field_computes_on_dump():
    class S(Schema):
        name = fields.Str()
        upper = fields.Function(lambda obj: obj["name"].upper())

    assert S().dump({"name": "ada"}) == {"name": "ada", "upper": "ADA"}


def test_method_field_calls_schema_method():
    class S(Schema):
        name = fields.Str()
        label = fields.Method("make_label")

        def make_label(self, obj):
            return f"label:{obj['name']}"

    assert S().dump({"name": "ada"}) == {"name": "ada", "label": "label:ada"}
