# Spec2Repo oracle - integration tests for marshmallow-schema-fullrepro-001
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


def test_data_key_changes_external_key_and_error_key():
    class UserSchema(Schema):
        email = fields.Email(data_key="emailAddress")

    schema = UserSchema()

    assert schema.dump({"email": "ada@example.com"}) == {"emailAddress": "ada@example.com"}
    assert schema.load({"emailAddress": "ada@example.com"}) == {"email": "ada@example.com"}
    with pytest.raises(ValidationError) as excinfo:
        schema.load({"emailAddress": "bad"})
    assert "emailAddress" in excinfo.value.messages


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


def test_enum_field_by_value_loads_and_dumps():
    class Color(enum.Enum):
        RED = "red"
        BLUE = "blue"

    class ColorSchema(Schema):
        color = fields.Enum(Color, by_value=True)

    schema = ColorSchema()

    assert schema.load({"color": "red"}) == {"color": Color.RED}
    assert schema.dump({"color": Color.BLUE}) == {"color": "blue"}


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


def test_missing_required_and_unknown_errors_can_coexist():
    class UserSchema(Schema):
        name = fields.Str(required=True)

    with pytest.raises(ValidationError) as excinfo:
        UserSchema().load({"extra": "x"})

    assert set(excinfo.value.messages) == {"name", "extra"}


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
