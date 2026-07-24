"""Integration tests for marshmallow-schema-fullrepro-001.

Each test crosses ≥2 public API boundaries.
IMPORTANT: This task had -11.7pp gap. Integration tests must truly cross
module boundaries (schema + fields + hooks + validators + nested).
"""

from __future__ import annotations

import datetime as dt
import decimal
import enum
import json
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


# --- State Consistency: dump ↔ load ↔ JSON agreement ---


def test_dumps_and_loads_agree_with_dump_and_load():
    """Seam: state consistency between JSON and direct projections."""
    class S(Schema):
        name = fields.Str()
        age = fields.Int()

    schema = S()
    obj = {"name": "Grace", "age": 85}

    assert json.loads(schema.dumps(obj)) == schema.dump(obj)
    assert schema.loads('{"name": "Grace", "age": "85"}') == schema.load({"name": "Grace", "age": "85"})


def test_data_key_consistent_across_dump_load_error():
    """Seam: state consistency between data_key in dump, load, and errors."""
    class S(Schema):
        email = fields.Email(data_key="emailAddr")

    schema = S()

    assert schema.dump({"email": "ada@example.com"}) == {"emailAddr": "ada@example.com"}
    assert schema.load({"emailAddr": "ada@example.com"}) == {"email": "ada@example.com"}
    with pytest.raises(ValidationError) as exc:
        schema.load({"emailAddr": "bad"})
    assert "emailAddr" in exc.value.messages


def test_load_validate_and_loads_agree_on_unknown_errors():
    """Seam: state consistency between load, validate, and loads error reporting."""
    class S(Schema):
        name = fields.Str()

    schema = S()
    try:
        schema.load({"name": "Ada", "extra": "x"})
    except ValidationError as e:
        load_errors = e.messages

    assert load_errors == schema.validate({"name": "Ada", "extra": "x"})
    with pytest.raises(ValidationError) as exc:
        schema.loads('{"name": "Ada", "extra": "x"}')
    assert exc.value.messages == load_errors


def test_json_projection_preserves_data_key_and_defaults():
    """Seam: state consistency between JSON ops and key/default config."""
    class S(Schema):
        name = fields.Str(data_key="displayName", required=True)
        age = fields.Int(load_default=0)

    schema = S()
    loaded = schema.loads('{"displayName": "Ada"}')
    assert loaded == {"name": "Ada", "age": 0}
    assert json.loads(schema.dumps(loaded)) == {"displayName": "Ada", "age": 0}


# --- Config Interaction: unknown policies ---


def test_unknown_raise_rejects_extra_keys():
    """Seam: config interaction between RAISE policy and load validation."""
    class S(Schema):
        name = fields.Str()

    with pytest.raises(ValidationError) as exc:
        S().load({"name": "Ada", "extra": "v"})
    assert "extra" in exc.value.messages


def test_unknown_exclude_drops_extra_keys():
    """Seam: config interaction between EXCLUDE policy and loaded output."""
    class S(Schema):
        name = fields.Str()

    assert S(unknown=EXCLUDE).load({"name": "Ada", "extra": "v"}) == {"name": "Ada"}


def test_unknown_include_preserves_extra_keys():
    """Seam: config interaction between INCLUDE policy and loaded output."""
    class S(Schema):
        name = fields.Str()

    assert S(unknown=INCLUDE).load({"name": "Ada", "extra": "v"}) == {
        "name": "Ada", "extra": "v"
    }


def test_load_unknown_arg_overrides_instance_policy():
    """Seam: config interaction between per-call and instance-level policy."""
    class S(Schema):
        name = fields.Str()

    schema = S(unknown=RAISE)
    assert schema.load({"name": "Ada", "extra": "v"}, unknown=EXCLUDE) == {"name": "Ada"}


def test_instance_unknown_overrides_meta_policy():
    """Seam: config interaction between instance and Meta unknown."""
    class S(Schema):
        name = fields.Str()

        class Meta:
            unknown = INCLUDE

    assert S(unknown=EXCLUDE).load({"name": "Ada", "extra": "v"}) == {"name": "Ada"}


def test_excluded_field_treated_as_unknown_when_in_input():
    """Seam: config interaction between exclude and unknown policy."""
    class S(Schema):
        name = fields.Str()
        age = fields.Int()

    schema = S(exclude=("age",))
    with pytest.raises(ValidationError) as exc:
        schema.load({"name": "Ada", "age": 37})
    assert "age" in exc.value.messages


# --- Config Interaction: partial loading ---


def test_partial_true_skips_all_required_checks():
    """Seam: config interaction between partial and required."""
    class S(Schema):
        name = fields.Str(required=True)
        age = fields.Int(required=True)

    assert S().load({"age": 25}, partial=True) == {"age": 25}


def test_partial_tuple_skips_named_fields_only():
    """Seam: config interaction between partial names and field validation."""
    class S(Schema):
        name = fields.Str(required=True)
        age = fields.Int(required=True)

    assert S().load({"age": 25}, partial=("name",)) == {"age": 25}
    with pytest.raises(ValidationError) as exc:
        S().load({"name": "Ada"}, partial=("name",))
    assert "age" in exc.value.messages


# --- Protocol Handoff: pre/post hooks ---


def test_pre_load_transforms_input_for_field_processing():
    """Seam: protocol handoff between pre_load hook and field deserialization."""
    class S(Schema):
        name = fields.Str()

        @pre_load
        def unwrap(self, data, **kwargs):
            return data["user"]

    assert S().load({"user": {"name": "Ada"}}) == {"name": "Ada"}


def test_post_load_transforms_loaded_data():
    """Seam: protocol handoff between field loading and post_load hook."""
    class S(Schema):
        name = fields.Str()

        @post_load
        def make_user(self, data, **kwargs):
            return User(name=data["name"], email="gen@example.com")

    assert S().load({"name": "Ada"}) == User("Ada", "gen@example.com")


def test_pre_dump_transforms_object_for_field_serialization():
    """Seam: protocol handoff between pre_dump and field serialization."""
    class S(Schema):
        name = fields.Str()

        @pre_dump
        def normalize(self, obj, **kwargs):
            return {"name": obj.name.upper()}

    assert S().dump(User("ada", "a@e.com")) == {"name": "ADA"}


def test_post_dump_transforms_serialized_output():
    """Seam: protocol handoff between field dump and post_dump."""
    class S(Schema):
        name = fields.Str()

        @post_dump
        def envelope(self, data, **kwargs):
            return {"user": data}

    assert S().dump({"name": "Ada"}) == {"user": {"name": "Ada"}}


def test_post_load_pass_original_receives_input():
    """Seam: protocol handoff between load pipeline and hook argument."""
    class S(Schema):
        name = fields.Str()

        @post_load(pass_original=True)
        def annotate(self, data, original, **kwargs):
            data["keys"] = sorted(original)
            return data

    assert S(unknown=EXCLUDE).load({"name": "Ada", "extra": "x"}) == {
        "name": "Ada", "keys": ["extra", "name"]
    }


def test_post_dump_pass_original_receives_object():
    """Seam: protocol handoff between dump pipeline and hook argument."""
    class S(Schema):
        name = fields.Str()

        @post_dump(pass_original=True)
        def annotate(self, data, original, **kwargs):
            data["src"] = original["name"]
            return data

    assert S().dump({"name": "Ada"}) == {"name": "Ada", "src": "Ada"}


def test_pass_collection_hooks_receive_full_list():
    """Seam: protocol handoff between many=True and pass_collection hooks."""
    class S(Schema):
        name = fields.Str()

        @pre_load(pass_collection=True)
        def unwrap(self, data, many, **kwargs):
            return data["items"] if many else data

        @post_dump(pass_collection=True)
        def wrap(self, data, many, **kwargs):
            return {"items": data} if many else data

    schema = S(many=True)
    assert schema.load({"items": [{"name": "A"}, {"name": "B"}]}) == [
        {"name": "A"}, {"name": "B"}
    ]
    assert schema.dump([{"name": "A"}]) == {"items": [{"name": "A"}]}


# --- Protocol Handoff: validates / validates_schema ---


def test_validates_decorator_validates_multiple_fields():
    """Seam: protocol handoff between field load and validator method."""
    class S(Schema):
        first = fields.Str(required=True)
        last = fields.Str(required=True)

        @validates("first", "last")
        def check_len(self, value, data_key, **kwargs):
            if len(value) < 2:
                raise ValidationError("too short")

    with pytest.raises(ValidationError) as exc:
        S().load({"first": "A", "last": "B"})
    assert set(exc.value.messages) == {"first", "last"}


def test_validates_schema_reports_under_schema_key():
    """Seam: protocol handoff between field validation and schema-level validator."""
    class S(Schema):
        low = fields.Int(required=True)
        high = fields.Int(required=True)

        @validates_schema
        def check_order(self, data, **kwargs):
            if data["low"] >= data["high"]:
                raise ValidationError("order wrong")

    with pytest.raises(ValidationError) as exc:
        S().load({"low": 10, "high": 3})
    assert "_schema" in exc.value.messages


def test_validates_schema_can_report_field_errors():
    """Seam: protocol handoff between schema validator and field error dict."""
    class S(Schema):
        low = fields.Int(required=True)
        high = fields.Int(required=True)

        @validates_schema
        def check_order(self, data, **kwargs):
            if data["low"] >= data["high"]:
                raise ValidationError({"high": ["must exceed low"]})

    with pytest.raises(ValidationError) as exc:
        S().load({"low": 10, "high": 3})
    assert "high" in exc.value.messages


def test_validates_schema_skips_on_field_errors_by_default():
    """Seam: config interaction between field errors and schema validator skip."""
    calls = {"n": 0}

    class S(Schema):
        v = fields.Int(required=True)

        @validates_schema
        def count(self, data, **kwargs):
            calls["n"] += 1

    with pytest.raises(ValidationError):
        S().load({"v": "bad"})
    assert calls["n"] == 0


def test_validates_schema_runs_when_skip_disabled():
    """Seam: config interaction between skip_on_field_errors and execution."""
    calls = {"n": 0}

    class S(Schema):
        v = fields.Int(required=True)

        @validates_schema(skip_on_field_errors=False)
        def count(self, data, **kwargs):
            calls["n"] += 1

    with pytest.raises(ValidationError):
        S().load({"v": "bad"})
    assert calls["n"] == 1


def test_validates_receives_external_data_key():
    """Seam: protocol handoff between data_key config and validator arg."""
    seen = {}

    class S(Schema):
        email = fields.Email(data_key="emailAddr")

        @validates("email")
        def record(self, value, data_key, **kwargs):
            seen["key"] = data_key

    S().load({"emailAddr": "ada@example.com"})
    assert seen["key"] == "emailAddr"


# --- Nested schemas ---


def test_nested_schema_dumps_and_loads():
    """Seam: protocol handoff between parent schema and nested schema."""
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


def test_list_of_nested_reports_indexed_errors():
    """Seam: error propagation through nested list schema."""
    class UserSchema(Schema):
        email = fields.Email(required=True)

    class GroupSchema(Schema):
        members = fields.List(fields.Nested(UserSchema))

    with pytest.raises(ValidationError) as exc:
        GroupSchema().load({"members": [{"email": "ok@e.com"}, {"email": "bad"}]})
    assert "members" in exc.value.messages
    assert 1 in exc.value.messages["members"]


def test_pluck_dumps_scalar_loads_nested():
    """Seam: protocol handoff between Pluck field and nested schema."""
    class UserSchema(Schema):
        name = fields.Str()
        email = fields.Email()

    class BlogSchema(Schema):
        author = fields.Pluck(UserSchema, "name")

    assert BlogSchema().dump({"author": User("Ada", "ada@e.com")}) == {"author": "Ada"}
    assert BlogSchema().load({"author": "Ada"}) == {"author": {"name": "Ada"}}


def test_pluck_many_dumps_list():
    """Seam: protocol handoff between Pluck many and nested schema."""
    class UserSchema(Schema):
        name = fields.Str()

    class GroupSchema(Schema):
        members = fields.Pluck(UserSchema, "name", many=True)

    assert GroupSchema().dump({"members": [{"name": "Ada"}, {"name": "Grace"}]}) == {
        "members": ["Ada", "Grace"]
    }
    assert GroupSchema().load({"members": ["Ada", "Grace"]}) == {
        "members": [{"name": "Ada"}, {"name": "Grace"}]
    }


def test_nested_only_limits_nested_fields():
    """Seam: config interaction between nested only and dump output."""
    class UserSchema(Schema):
        name = fields.Str()
        email = fields.Email()

    class BlogSchema(Schema):
        author = fields.Nested(UserSchema(only=("email",)))

    assert BlogSchema().dump({"author": User("Ada", "ada@e.com")}) == {
        "author": {"email": "ada@e.com"}
    }


def test_dotted_only_limits_nested_output():
    """Seam: config interaction between dotted only path and nested output."""
    class UserSchema(Schema):
        name = fields.Str()
        email = fields.Email()

    class BlogSchema(Schema):
        title = fields.Str()
        author = fields.Nested(UserSchema)

    schema = BlogSchema(only=("author.email",))
    assert schema.dump({"title": "X", "author": User("Ada", "ada@e.com")}) == {
        "author": {"email": "ada@e.com"}
    }


def test_nested_partial_dotted_path():
    """Seam: config interaction between partial dotted path and nested required."""
    class UserSchema(Schema):
        name = fields.Str(required=True)
        email = fields.Email(required=True)

    class BlogSchema(Schema):
        title = fields.Str(required=True)
        author = fields.Nested(UserSchema, required=True)

    result = BlogSchema().load(
        {"title": "X", "author": {"name": "Ada"}},
        partial=("author.email",),
    )
    assert result == {"title": "X", "author": {"name": "Ada"}}


def test_nested_unknown_policy_applies_inside():
    """Seam: config interaction between nested schema's unknown policy."""
    class UserSchema(Schema):
        name = fields.Str()

        class Meta:
            unknown = EXCLUDE

    class BlogSchema(Schema):
        author = fields.Nested(UserSchema)

    assert BlogSchema().load({"author": {"name": "Ada", "extra": "x"}}) == {
        "author": {"name": "Ada"}
    }


# --- many instance ---


def test_many_instance_processes_collections():
    """Seam: state consistency between many=True instance and list processing."""
    class S(Schema):
        name = fields.Str()

    schema = S(many=True)
    assert schema.dump([{"name": "A"}, {"name": "B"}]) == [{"name": "A"}, {"name": "B"}]
    assert schema.load([{"name": "A"}, {"name": "B"}]) == [{"name": "A"}, {"name": "B"}]


# --- Schema.from_dict ---


def test_from_dict_creates_usable_schema():
    """Seam: state consistency between from_dict and resulting schema."""
    Generated = Schema.from_dict({"name": fields.Str(), "age": fields.Int()})
    assert Generated().load({"name": "Ada", "age": "37"}) == {"name": "Ada", "age": 37}


# --- field_views reflect projection ---


def test_schema_fields_reflect_only_and_exclude():
    """Seam: state consistency between only/exclude and field views."""
    class S(Schema):
        name = fields.Str()
        email = fields.Email()
        age = fields.Int()

    schema = S(only=("name", "email"), exclude=("email",))
    assert set(schema.fields) == {"name"}
    assert set(schema.dump_fields) == {"name"}
    assert set(schema.load_fields) == {"name"}


# --- validate agrees with load on exclude ---


def test_validate_with_exclude_unknown_returns_no_errors():
    """Seam: state consistency between validate and unknown=EXCLUDE."""
    class S(Schema):
        name = fields.Str()

    assert S(unknown=EXCLUDE).validate({"name": "Ada", "extra": "x"}) == {}


# --- Field-level processors ---


def test_field_pre_and_post_load_processors():
    """Seam: protocol handoff between field processors and field deserialization."""
    class S(Schema):
        name = fields.Str(pre_load=str.strip, post_load=str.title)

    assert S().load({"name": "  ada lovelace  "}) == {"name": "Ada Lovelace"}


def test_field_processor_error_attaches_to_field():
    """Seam: error propagation from field processor to error dict."""
    def reject_blank(v):
        if not v.strip():
            raise ValidationError("blank")
        return v

    class S(Schema):
        name = fields.Str(pre_load=reject_blank)

    with pytest.raises(ValidationError) as exc:
        S().load({"name": "   "})
    assert "name" in exc.value.messages
