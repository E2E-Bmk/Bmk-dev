# Spec2Repo oracle - atomic tests for marshmallow-schema-fullrepro-001
from __future__ import annotations

import datetime as dt
import decimal
import enum
import ipaddress
import json
import uuid
from dataclasses import dataclass

import pytest

from marshmallow import (
    EXCLUDE,
    INCLUDE,
    RAISE,
    Schema,
    ValidationError,
    fields,
    post_dump,
    post_load,
    pre_dump,
    pre_load,
    validate,
    validates,
    validates_schema,
)


@dataclass
class User:
    name: str
    email: str
    age: int = 0
    created_at: dt.datetime | None = None


def test_only_limits_dump_and_load_views():
    class UserSchema(Schema):
        name = fields.Str()
        email = fields.Email()
        age = fields.Int()

    schema = UserSchema(only=("name", "email"))

    assert schema.dump(User("Ada", "ada@example.com", 37)) == {
        "name": "Ada",
        "email": "ada@example.com",
    }
    assert schema.load({"name": "Ada", "email": "ada@example.com"}) == {
        "name": "Ada",
        "email": "ada@example.com",
    }
    with pytest.raises(ValidationError) as excinfo:
        schema.load({"name": "Ada", "email": "ada@example.com", "age": 37})
    assert "age" in excinfo.value.messages


def test_exclude_removes_fields_from_dump_and_load():
    class UserSchema(Schema):
        name = fields.Str()
        email = fields.Email()
        age = fields.Int()

    schema = UserSchema(exclude=("age",))

    assert schema.dump(User("Ada", "ada@example.com", 37)) == {
        "name": "Ada",
        "email": "ada@example.com",
    }
    assert schema.load({"name": "Ada", "email": "ada@example.com"}) == {
        "name": "Ada",
        "email": "ada@example.com",
    }
    with pytest.raises(ValidationError) as excinfo:
        schema.load({"name": "Ada", "email": "ada@example.com", "age": 37})
    assert "age" in excinfo.value.messages


def test_load_default_and_dump_default_are_applied():
    class UserSchema(Schema):
        name = fields.Str(load_default="anonymous")
        created = fields.Date(dump_default=dt.date(2020, 1, 2))

    schema = UserSchema()

    assert schema.load({}) == {"name": "anonymous"}
    assert schema.dump({}) == {"created": "2020-01-02"}


def test_callable_load_default_runs_for_each_load():
    calls = {"count": 0}

    def next_value():
        calls["count"] += 1
        return calls["count"]

    class CounterSchema(Schema):
        value = fields.Int(load_default=next_value)

    schema = CounterSchema()

    assert schema.load({}) == {"value": 1}
    assert schema.load({}) == {"value": 2}


def test_load_default_none_allows_none_by_default():
    class UserSchema(Schema):
        nickname = fields.Str(load_default=None)

    schema = UserSchema()

    assert schema.load({}) == {"nickname": None}
    assert schema.load({"nickname": None}) == {"nickname": None}


def test_allow_none_false_rejects_none_even_with_default():
    class UserSchema(Schema):
        nickname = fields.Str(load_default="n/a", allow_none=False)

    with pytest.raises(ValidationError) as excinfo:
        UserSchema().load({"nickname": None})

    assert "nickname" in excinfo.value.messages


def test_attribute_reads_different_internal_name_on_dump():
    class UserSchema(Schema):
        display_name = fields.Str(attribute="name")

    assert UserSchema().dump(User("Ada", "ada@example.com")) == {"display_name": "Ada"}


def test_dump_only_is_omitted_from_load_and_load_only_from_dump():
    class UserSchema(Schema):
        name = fields.Str()
        password = fields.Str(load_only=True)
        created = fields.Str(dump_only=True)

    schema = UserSchema(unknown=EXCLUDE)

    assert schema.dump({"name": "Ada", "password": "secret", "created": "today"}) == {
        "name": "Ada",
        "created": "today",
    }
    assert schema.load({"name": "Ada", "password": "secret", "created": "today"}) == {
        "name": "Ada",
        "password": "secret",
    }


def test_validation_error_exposes_messages_and_valid_data():
    class UserSchema(Schema):
        name = fields.Str()
        email = fields.Email(required=True)

    with pytest.raises(ValidationError) as excinfo:
        UserSchema().load({"name": "Ada", "email": "bad"})

    err = excinfo.value
    assert "email" in err.messages
    assert err.valid_data == {"name": "Ada"}


def test_collection_errors_are_keyed_by_index():
    class UserSchema(Schema):
        email = fields.Email(required=True)

    with pytest.raises(ValidationError) as excinfo:
        UserSchema(many=True).load([
            {"email": "ada@example.com"},
            {"email": "bad"},
            {},
        ])

    assert set(excinfo.value.messages) == {1, 2}


def test_string_integer_float_decimal_boolean_conversions():
    class ValueSchema(Schema):
        text = fields.Str()
        count = fields.Int()
        ratio = fields.Float()
        amount = fields.Decimal(as_string=True)
        active = fields.Bool()

    loaded = ValueSchema().load(
        {"text": "123", "count": "7", "ratio": "2.5", "amount": "4.20", "active": "true"}
    )

    assert loaded == {
        "text": "123",
        "count": 7,
        "ratio": 2.5,
        "amount": decimal.Decimal("4.20"),
        "active": True,
    }
    assert ValueSchema().dump({"amount": decimal.Decimal("4.20"), "active": False}) == {
        "amount": "4.20",
        "active": False,
    }


def test_date_time_datetime_and_timedelta_fields():
    class TimeSchema(Schema):
        day = fields.Date()
        moment = fields.DateTime()
        clock = fields.Time()
        delta = fields.TimeDelta(precision="seconds")

    loaded = TimeSchema().load(
        {
            "day": "2020-01-02",
            "moment": "2020-01-02T03:04:05+00:00",
            "clock": "03:04:05",
            "delta": 90,
        }
    )

    assert loaded["day"] == dt.date(2020, 1, 2)
    assert loaded["moment"].hour == 3
    assert loaded["clock"] == dt.time(3, 4, 5)
    assert loaded["delta"] == dt.timedelta(seconds=90)


def test_uuid_ip_url_and_email_fields():
    ident = uuid.UUID("12345678-1234-5678-1234-567812345678")

    class NetworkSchema(Schema):
        ident = fields.UUID()
        ip = fields.IP()
        url = fields.Url()
        email = fields.Email()

    loaded = NetworkSchema().load(
        {
            "ident": str(ident),
            "ip": "192.168.1.1",
            "url": "https://example.com/path",
            "email": "ada@example.com",
        }
    )

    assert loaded["ident"] == ident
    assert loaded["ip"] == ipaddress.ip_address("192.168.1.1")
    assert loaded["url"] == "https://example.com/path"
    assert loaded["email"] == "ada@example.com"


def test_list_tuple_dict_and_mapping_fields():
    class ContainerSchema(Schema):
        tags = fields.List(fields.Str())
        point = fields.Tuple((fields.Int(), fields.Int()))
        prefs = fields.Dict(keys=fields.Str(), values=fields.Int())

    assert ContainerSchema().load(
        {"tags": ["one", "two"], "point": ["3", 4], "prefs": {"a": "1"}}
    ) == {"tags": ["one", "two"], "point": (3, 4), "prefs": {"a": 1}}


def test_constant_field_returns_constant_on_dump_and_load():
    class ConstantSchema(Schema):
        kind = fields.Constant("user")

    schema = ConstantSchema()

    assert schema.dump({}) == {"kind": "user"}
    assert schema.load({"kind": "anything"}) == {"kind": "user"}


def test_function_and_method_fields_dump_computed_values():
    class UserSchema(Schema):
        name = fields.Str()
        upper = fields.Function(lambda obj: obj["name"].upper())
        label = fields.Method("make_label")

        def make_label(self, obj):
            return f"user:{obj['name']}"

    assert UserSchema().dump({"name": "ada"}) == {
        "name": "ada",
        "upper": "ADA",
        "label": "user:ada",
    }


def test_field_pre_and_post_load_processors_transform_value():
    class UserSchema(Schema):
        name = fields.Str(pre_load=str.strip, post_load=str.title)

    assert UserSchema().load({"name": "  ada lovelace  "}) == {"name": "Ada Lovelace"}


def test_field_processor_validation_error_attaches_to_field():
    def reject_blank(value):
        if not value.strip():
            raise ValidationError("blank")
        return value

    class UserSchema(Schema):
        name = fields.Str(pre_load=reject_blank)

    with pytest.raises(ValidationError) as excinfo:
        UserSchema().load({"name": "   "})

    assert "name" in excinfo.value.messages


def test_range_length_and_oneof_validators_accept_valid_values():
    class UserSchema(Schema):
        name = fields.Str(validate=validate.Length(min=2, max=5))
        age = fields.Int(validate=validate.Range(min=18, max=99))
        role = fields.Str(validate=validate.OneOf(["admin", "user"]))

    assert UserSchema().load({"name": "Ada", "age": 37, "role": "admin"}) == {
        "name": "Ada",
        "age": 37,
        "role": "admin",
    }


def test_builtin_validators_report_field_errors():
    class UserSchema(Schema):
        name = fields.Str(validate=validate.Length(min=2))
        age = fields.Int(validate=validate.Range(min=18))
        role = fields.Str(validate=validate.OneOf(["admin", "user"]))

    with pytest.raises(ValidationError) as excinfo:
        UserSchema().load({"name": "A", "age": 17, "role": "guest"})

    assert set(excinfo.value.messages) == {"name", "age", "role"}


def test_noneof_contains_only_equal_regexp_predicate_and_and_validators():
    class ChoiceSchema(Schema):
        code = fields.Str(
            validate=validate.And(
                validate.NoneOf(["bad"]),
                validate.Regexp(r"^[A-Z]{2}$"),
            )
        )
        flags = fields.List(fields.Str(), validate=validate.ContainsOnly(["x", "y"]))
        exact = fields.Int(validate=validate.Equal(5))
        rounded = fields.Float(validate=validate.Predicate("is_integer"))

    assert ChoiceSchema().load(
        {"code": "OK", "flags": ["x", "y"], "exact": 5, "rounded": 2.0}
    ) == {"code": "OK", "flags": ["x", "y"], "exact": 5, "rounded": 2.0}


def test_multiple_validators_collect_multiple_failures_for_field():
    class ChoiceSchema(Schema):
        code = fields.Str(validate=[validate.Length(min=4), validate.Regexp(r"^[A-Z]+$")])

    with pytest.raises(ValidationError) as excinfo:
        ChoiceSchema().load({"code": "a"})

    assert len(excinfo.value.messages["code"]) >= 2


def test_post_load_pass_original_receives_original_input():
    class UserSchema(Schema):
        name = fields.Str()

        @post_load(pass_original=True)
        def add_original_keys(self, data, original, **kwargs):
            data["original_keys"] = sorted(original)
            return data

    assert UserSchema(unknown=EXCLUDE).load({"name": "Ada", "extra": "x"}) == {
        "name": "Ada",
        "original_keys": ["extra", "name"],
    }


def test_dump_does_not_run_field_validators():
    def reject(value):
        raise ValidationError("invalid")

    class UserSchema(Schema):
        age = fields.Int(validate=reject)

    assert UserSchema().dump({"age": 5}) == {"age": 5}


def test_raw_field_passes_values_through():
    class RawSchema(Schema):
        payload = fields.Raw()

    value = {"nested": [1, "two", None]}

    assert RawSchema().dump({"payload": value}) == {"payload": value}
    assert RawSchema().load({"payload": value}) == {"payload": value}


def test_post_dump_pass_original_receives_original_object():
    class UserSchema(Schema):
        name = fields.Str()

        @post_dump(pass_original=True)
        def add_seen_name(self, data, original, **kwargs):
            data["seen"] = original["name"]
            return data

    assert UserSchema().dump({"name": "Ada"}) == {"name": "Ada", "seen": "Ada"}
