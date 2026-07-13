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
from marshmallow.experimental.context import Context


@dataclass
class User:
    name: str
    email: str
    age: int = 0
    created_at: dt.datetime | None = None


def test_top_level_exports_are_importable():
    import marshmallow

    assert marshmallow.Schema is Schema
    assert marshmallow.fields is fields
    assert {EXCLUDE, INCLUDE, RAISE} == {"exclude", "include", "raise"}


def test_schema_declared_fields_dump_mapping_and_object():
    class UserSchema(Schema):
        name = fields.Str()
        age = fields.Int()

    schema = UserSchema()
    assert schema.dump({"name": "Ada", "age": 37}) == {"name": "Ada", "age": 37}
    assert schema.dump(User("Ada", "ada@example.com", 37)) == {"name": "Ada", "age": 37}


def test_schema_from_dict_creates_usable_schema_class():
    Generated = Schema.from_dict({"name": fields.Str(), "age": fields.Int()})

    result = Generated().load({"name": "Ada", "age": "37"})

    assert result == {"name": "Ada", "age": 37}


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


def test_unknown_field_rejected_by_default():
    class UserSchema(Schema):
        name = fields.Str()

    with pytest.raises(ValidationError) as excinfo:
        UserSchema().load({"name": "Ada", "extra": "value"})

    assert "extra" in excinfo.value.messages


def test_unknown_exclude_omits_extra_input():
    class UserSchema(Schema):
        name = fields.Str()

    assert UserSchema(unknown=EXCLUDE).load({"name": "Ada", "extra": "value"}) == {
        "name": "Ada"
    }


def test_unknown_include_preserves_extra_input():
    class UserSchema(Schema):
        name = fields.Str()

    assert UserSchema(unknown=INCLUDE).load({"name": "Ada", "extra": "value"}) == {
        "name": "Ada",
        "extra": "value",
    }


def test_load_unknown_argument_overrides_instance_policy():
    class UserSchema(Schema):
        name = fields.Str()

    schema = UserSchema(unknown=RAISE)

    assert schema.load({"name": "Ada", "extra": "value"}, unknown=EXCLUDE) == {
        "name": "Ada"
    }


def test_instance_unknown_overrides_meta_policy():
    class UserSchema(Schema):
        name = fields.Str()

        class Meta:
            unknown = INCLUDE

    schema = UserSchema(unknown=EXCLUDE)

    assert schema.load({"name": "Ada", "extra": "value"}) == {"name": "Ada"}


def test_required_field_error_skipped_by_partial_true():
    class UserSchema(Schema):
        name = fields.Str(required=True)
        age = fields.Int(required=True)

    assert UserSchema().load({"age": 37}, partial=True) == {"age": 37}


def test_partial_tuple_skips_only_named_required_fields():
    class UserSchema(Schema):
        name = fields.Str(required=True)
        age = fields.Int(required=True)

    assert UserSchema().load({"age": 37}, partial=("name",)) == {"age": 37}
    with pytest.raises(ValidationError) as excinfo:
        UserSchema().load({"name": "Ada"}, partial=("name",))
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


def test_data_key_changes_external_key_and_error_key():
    class UserSchema(Schema):
        email = fields.Email(data_key="emailAddress")

    schema = UserSchema()

    assert schema.dump({"email": "ada@example.com"}) == {"emailAddress": "ada@example.com"}
    assert schema.load({"emailAddress": "ada@example.com"}) == {"email": "ada@example.com"}
    with pytest.raises(ValidationError) as excinfo:
        schema.load({"emailAddress": "bad"})
    assert "emailAddress" in excinfo.value.messages


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


def test_many_instance_dumps_and_loads_collections():
    class UserSchema(Schema):
        name = fields.Str()
        age = fields.Int()

    schema = UserSchema(many=True)

    assert schema.dump([User("Ada", "a@example.com", 37), User("Grace", "g@example.com", 85)]) == [
        {"name": "Ada", "age": 37},
        {"name": "Grace", "age": 85},
    ]
    assert schema.load([{"name": "Ada", "age": "37"}, {"name": "Grace", "age": 85}]) == [
        {"name": "Ada", "age": 37},
        {"name": "Grace", "age": 85},
    ]


def test_dump_and_load_accept_many_argument():
    class UserSchema(Schema):
        name = fields.Str()

    schema = UserSchema()

    assert schema.dump([{"name": "Ada"}, {"name": "Grace"}], many=True) == [
        {"name": "Ada"},
        {"name": "Grace"},
    ]
    assert schema.load([{"name": "Ada"}, {"name": "Grace"}], many=True) == [
        {"name": "Ada"},
        {"name": "Grace"},
    ]


def test_dumps_and_loads_match_dump_and_load():
    class UserSchema(Schema):
        name = fields.Str()
        age = fields.Int()

    schema = UserSchema()
    obj = {"name": "Ada", "age": 37}

    assert json.loads(schema.dumps(obj)) == schema.dump(obj)
    assert schema.loads('{"name": "Ada", "age": "37"}') == {"name": "Ada", "age": 37}


def test_schema_validate_returns_errors_without_raising():
    class UserSchema(Schema):
        email = fields.Email(required=True)

    errors = UserSchema().validate({"email": "not-an-email"})

    assert "email" in errors


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


def test_enum_field_by_value_loads_and_dumps():
    class Color(enum.Enum):
        RED = "red"
        BLUE = "blue"

    class ColorSchema(Schema):
        color = fields.Enum(Color, by_value=True)

    schema = ColorSchema()

    assert schema.load({"color": "red"}) == {"color": Color.RED}
    assert schema.dump({"color": Color.BLUE}) == {"color": "blue"}


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


def test_validates_decorator_validates_multiple_fields():
    class NameSchema(Schema):
        first = fields.Str(required=True)
        last = fields.Str(required=True)

        @validates("first", "last")
        def validate_name(self, value, data_key, **kwargs):
            if len(value) < 2:
                raise ValidationError("short")

    with pytest.raises(ValidationError) as excinfo:
        NameSchema().load({"first": "A", "last": "B"})

    assert set(excinfo.value.messages) == {"first", "last"}


def test_validates_schema_reports_schema_key_by_default():
    class RangeSchema(Schema):
        low = fields.Int(required=True)
        high = fields.Int(required=True)

        @validates_schema
        def validate_order(self, data, **kwargs):
            if data["low"] >= data["high"]:
                raise ValidationError("bad order")

    with pytest.raises(ValidationError) as excinfo:
        RangeSchema().load({"low": 5, "high": 2})

    assert "_schema" in excinfo.value.messages


def test_validates_schema_can_report_field_errors():
    class RangeSchema(Schema):
        low = fields.Int(required=True)
        high = fields.Int(required=True)

        @validates_schema
        def validate_order(self, data, **kwargs):
            if data["low"] >= data["high"]:
                raise ValidationError({"high": ["too small"]})

    with pytest.raises(ValidationError) as excinfo:
        RangeSchema().load({"low": 5, "high": 2})

    assert "high" in excinfo.value.messages


def test_schema_validator_skips_when_field_errors_exist_by_default():
    calls = {"schema": 0}

    class RangeSchema(Schema):
        low = fields.Int(required=True)
        high = fields.Int(required=True)

        @validates_schema
        def validate_order(self, data, **kwargs):
            calls["schema"] += 1

    with pytest.raises(ValidationError):
        RangeSchema().load({"low": "not-int", "high": 2})

    assert calls["schema"] == 0


def test_schema_validator_can_run_when_field_errors_exist():
    calls = {"schema": 0}

    class RangeSchema(Schema):
        low = fields.Int(required=True)
        high = fields.Int(required=True)

        @validates_schema(skip_on_field_errors=False)
        def validate_order(self, data, **kwargs):
            calls["schema"] += 1

    with pytest.raises(ValidationError):
        RangeSchema().load({"low": "not-int", "high": 2})

    assert calls["schema"] == 1


def test_pre_load_and_post_load_transform_data():
    class UserSchema(Schema):
        name = fields.Str()

        @pre_load
        def unwrap(self, data, **kwargs):
            return data["user"]

        @post_load
        def make_user(self, data, **kwargs):
            return User(name=data["name"], email="generated@example.com")

    loaded = UserSchema().load({"user": {"name": "Ada"}})

    assert loaded == User("Ada", "generated@example.com")


def test_pre_dump_and_post_dump_transform_data():
    class UserSchema(Schema):
        name = fields.Str()

        @pre_dump
        def normalize(self, obj, **kwargs):
            return {"name": obj.name.title()}

        @post_dump
        def envelope(self, data, **kwargs):
            return {"user": data}

    assert UserSchema().dump(User("ada", "ada@example.com")) == {"user": {"name": "Ada"}}


def test_pass_collection_hooks_receive_whole_collection():
    class UserSchema(Schema):
        name = fields.Str()

        @pre_load(pass_collection=True)
        def unwrap(self, data, many, **kwargs):
            key = "users" if many else "user"
            return data[key]

        @post_dump(pass_collection=True)
        def wrap(self, data, many, **kwargs):
            key = "users" if many else "user"
            return {key: data}

    schema = UserSchema(many=True)

    assert schema.load({"users": [{"name": "Ada"}, {"name": "Grace"}]}) == [
        {"name": "Ada"},
        {"name": "Grace"},
    ]
    assert schema.dump([{"name": "Ada"}, {"name": "Grace"}]) == {
        "users": [{"name": "Ada"}, {"name": "Grace"}]
    }


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


def test_nested_schema_dumps_and_loads_object():
    class UserSchema(Schema):
        name = fields.Str()
        email = fields.Email()

    class BlogSchema(Schema):
        title = fields.Str()
        author = fields.Nested(UserSchema)

    blog = {"title": "Notes", "author": User("Ada", "ada@example.com")}

    assert BlogSchema().dump(blog) == {
        "title": "Notes",
        "author": {"name": "Ada", "email": "ada@example.com"},
    }
    assert BlogSchema().load(
        {"title": "Notes", "author": {"name": "Ada", "email": "ada@example.com"}}
    ) == {"title": "Notes", "author": {"name": "Ada", "email": "ada@example.com"}}


def test_nested_only_uses_nested_field_subset():
    class UserSchema(Schema):
        name = fields.Str()
        email = fields.Email()

    class BlogSchema(Schema):
        title = fields.Str()
        author = fields.Nested(UserSchema(only=("email",)))

    assert BlogSchema().dump({"title": "Notes", "author": User("Ada", "ada@example.com")}) == {
        "title": "Notes",
        "author": {"email": "ada@example.com"},
    }


def test_dotted_only_limits_nested_output():
    class UserSchema(Schema):
        name = fields.Str()
        email = fields.Email()

    class BlogSchema(Schema):
        title = fields.Str()
        author = fields.Nested(UserSchema)

    schema = BlogSchema(only=("author.email",))

    assert schema.dump({"title": "Notes", "author": User("Ada", "ada@example.com")}) == {
        "author": {"email": "ada@example.com"}
    }


def test_list_of_nested_schemas_reports_indexed_errors():
    class UserSchema(Schema):
        email = fields.Email(required=True)

    class GroupSchema(Schema):
        members = fields.List(fields.Nested(UserSchema))

    with pytest.raises(ValidationError) as excinfo:
        GroupSchema().load({"members": [{"email": "ada@example.com"}, {"email": "bad"}]})

    assert "members" in excinfo.value.messages
    assert 1 in excinfo.value.messages["members"]


def test_pluck_dumps_scalar_and_loads_nested_dict():
    class UserSchema(Schema):
        name = fields.Str()
        email = fields.Email()

    class BlogSchema(Schema):
        author = fields.Pluck(UserSchema, "name")

    schema = BlogSchema()

    assert schema.dump({"author": User("Ada", "ada@example.com")}) == {"author": "Ada"}
    assert schema.load({"author": "Ada"}) == {"author": {"name": "Ada"}}


def test_pluck_many_dumps_list_and_loads_list_of_nested_dicts():
    class UserSchema(Schema):
        name = fields.Str()

    class GroupSchema(Schema):
        members = fields.Pluck(UserSchema, "name", many=True)

    assert GroupSchema().dump({"members": [User("Ada", "a@example.com"), User("Grace", "g@example.com")]}) == {
        "members": ["Ada", "Grace"]
    }
    assert GroupSchema().load({"members": ["Ada", "Grace"]}) == {
        "members": [{"name": "Ada"}, {"name": "Grace"}]
    }


def test_nested_partial_dotted_path_skips_required_child_field():
    class UserSchema(Schema):
        name = fields.Str(required=True)
        email = fields.Email(required=True)

    class BlogSchema(Schema):
        title = fields.Str(required=True)
        author = fields.Nested(UserSchema, required=True)

    schema = BlogSchema()

    assert schema.load(
        {"title": "Notes", "author": {"name": "Ada"}},
        partial=("author.email",),
    ) == {"title": "Notes", "author": {"name": "Ada"}}


def test_nested_self_schema_dumps_recursive_relationship():
    class NodeSchema(Schema):
        name = fields.Str()
        children = fields.List(fields.Nested(lambda: NodeSchema(exclude=("children",))))

    data = {"name": "root", "children": [{"name": "leaf", "children": []}]}

    assert NodeSchema().dump(data) == {"name": "root", "children": [{"name": "leaf"}]}


def test_context_get_returns_active_context_and_restores_default():
    UserContext = Context[dict[str, str]]

    assert UserContext.get({"suffix": "none"}) == {"suffix": "none"}
    with UserContext({"suffix": "!"}):
        assert UserContext.get() == {"suffix": "!"}
    assert UserContext.get({"suffix": "none"}) == {"suffix": "none"}


def test_context_get_without_default_raises_when_missing():
    UserContext = Context[dict[str, str]]

    with pytest.raises(LookupError):
        UserContext.get()


def test_function_field_reads_current_context():
    UserContext = Context[dict[str, str]]

    class UserSchema(Schema):
        label = fields.Function(lambda obj: obj["name"] + UserContext.get()["suffix"])

    with UserContext({"suffix": "!"}):
        assert UserSchema().dump({"name": "Ada"}) == {"label": "Ada!"}


def test_load_validate_and_loads_agree_on_unknown_errors():
    class UserSchema(Schema):
        name = fields.Str()

    schema = UserSchema()

    load_errors = None
    try:
        schema.load({"name": "Ada", "extra": "x"})
    except ValidationError as err:
        load_errors = err.messages
    assert load_errors == schema.validate({"name": "Ada", "extra": "x"})
    with pytest.raises(ValidationError) as excinfo:
        schema.loads('{"name": "Ada", "extra": "x"}')
    assert excinfo.value.messages == load_errors


def test_dump_and_dumps_use_same_external_data_key():
    class UserSchema(Schema):
        email = fields.Email(data_key="emailAddress")

    schema = UserSchema()

    dumped = schema.dump({"email": "ada@example.com"})
    assert dumped == {"emailAddress": "ada@example.com"}
    assert json.loads(schema.dumps({"email": "ada@example.com"})) == dumped


def test_load_and_loads_apply_same_defaults_and_conversion():
    class UserSchema(Schema):
        name = fields.Str(load_default="anonymous")
        age = fields.Int(load_default=0)

    schema = UserSchema()

    assert schema.load({"age": "37"}) == schema.loads('{"age": "37"}')
    assert schema.loads("{}") == {"name": "anonymous", "age": 0}


def test_dump_does_not_run_field_validators():
    def reject(value):
        raise ValidationError("invalid")

    class UserSchema(Schema):
        age = fields.Int(validate=reject)

    assert UserSchema().dump({"age": 5}) == {"age": 5}


def test_unknown_exclude_validate_returns_no_errors():
    class UserSchema(Schema):
        name = fields.Str()

    assert UserSchema(unknown=EXCLUDE).validate({"name": "Ada", "extra": "x"}) == {}


def test_schema_fields_reflect_only_and_exclude_projection():
    class UserSchema(Schema):
        name = fields.Str()
        email = fields.Email()
        age = fields.Int()

    schema = UserSchema(only=("name", "email"), exclude=("email",))

    assert set(schema.fields) == {"name"}
    assert set(schema.dump_fields) == {"name"}
    assert set(schema.load_fields) == {"name"}


def test_invalid_only_field_raises_at_schema_creation():
    class UserSchema(Schema):
        name = fields.Str()

    with pytest.raises(Exception):
        UserSchema(only=("missing",))


def test_raw_field_passes_values_through():
    class RawSchema(Schema):
        payload = fields.Raw()

    value = {"nested": [1, "two", None]}

    assert RawSchema().dump({"payload": value}) == {"payload": value}
    assert RawSchema().load({"payload": value}) == {"payload": value}


def test_missing_required_and_unknown_errors_can_coexist():
    class UserSchema(Schema):
        name = fields.Str(required=True)

    with pytest.raises(ValidationError) as excinfo:
        UserSchema().load({"extra": "x"})

    assert set(excinfo.value.messages) == {"name", "extra"}


def test_post_dump_pass_original_receives_original_object():
    class UserSchema(Schema):
        name = fields.Str()

        @post_dump(pass_original=True)
        def add_seen_name(self, data, original, **kwargs):
            data["seen"] = original["name"]
            return data

    assert UserSchema().dump({"name": "Ada"}) == {"name": "Ada", "seen": "Ada"}


def test_validates_receives_external_data_key():
    seen = {}

    class UserSchema(Schema):
        email = fields.Email(data_key="emailAddress")

        @validates("email")
        def remember_key(self, value, data_key, **kwargs):
            seen["data_key"] = data_key

    assert UserSchema().load({"emailAddress": "ada@example.com"}) == {
        "email": "ada@example.com"
    }
    assert seen["data_key"] == "emailAddress"


def test_nested_unknown_policy_is_applied_inside_nested_schema():
    class UserSchema(Schema):
        name = fields.Str()

        class Meta:
            unknown = EXCLUDE

    class BlogSchema(Schema):
        author = fields.Nested(UserSchema)

    assert BlogSchema().load({"author": {"name": "Ada", "extra": "x"}}) == {
        "author": {"name": "Ada"}
    }
