from __future__ import annotations

from pathlib import Path

from marshmallow import EXCLUDE, INCLUDE, RAISE, Schema, ValidationError, fields, post_dump, post_load, pre_dump, pre_load, validate, validates_schema


def raises_validation(function):
    try:
        function()
    except ValidationError as exc:
        return exc
    raise AssertionError("expected ValidationError")


def test_a01(tmp_path: Path) -> None:
    class User(Schema):
        name = fields.String(required=True)
        age = fields.Integer(load_default=0)
    schema = User()
    assert set(schema.fields) == {"name", "age"}
    assert fields.Str is fields.String and fields.Int is fields.Integer


def test_a02(tmp_path: Path) -> None:
    class User(Schema):
        name = fields.String()
        age = fields.Integer()
    schema = User()
    loaded = schema.load({"name": "Ada", "age": "37"})
    assert loaded == {"name": "Ada", "age": 37}
    assert schema.dump(loaded) == {"name": "Ada", "age": 37}


def test_a03(tmp_path: Path) -> None:
    class Item(Schema):
        value = fields.Integer()
    assert Item(unknown=EXCLUDE).load({"value": "2", "extra": 3}) == {"value": 2}
    assert Item(unknown=INCLUDE).load({"value": "2", "extra": 3}) == {"value": 2, "extra": 3}
    assert "extra" in raises_validation(lambda: Item(unknown=RAISE).load({"value": 2, "extra": 3})).messages


def test_a04(tmp_path: Path) -> None:
    class Entry(Schema):
        name = fields.String(required=True)
        rank = fields.Integer(load_default=7)
        secret = fields.String(load_only=True)
        label = fields.String(dump_only=True)
    schema = Entry()
    assert schema.load({"name": "x", "secret": "s", "label": "ignored"}, unknown=EXCLUDE) == {"name": "x", "rank": 7, "secret": "s"}
    assert schema.dump({"name": "x", "secret": "s", "label": "shown"}) == {"name": "x", "label": "shown"}


def test_a05(tmp_path: Path) -> None:
    class Score(Schema):
        value = fields.Integer(validate=[validate.Range(min=2, max=4), validate.OneOf([2, 3, 4])])
    assert Score().load({"value": "3"}) == {"value": 3}
    error = raises_validation(lambda: Score().load({"value": 9}))
    assert "value" in error.messages and len(error.messages["value"]) == 2


def test_a06(tmp_path: Path) -> None:
    class Child(Schema):
        ident = fields.UUID()
    class Parent(Schema):
        rows = fields.List(fields.Nested(Child()))
        pair = fields.Tuple((fields.Integer(), fields.String()))
    raw = {"rows": [{"ident": "abcdef12-3456-7890-abcd-ef1234567890"}], "pair": ["4", "north"]}
    loaded = Parent().load(raw)
    assert str(loaded["rows"][0]["ident"]) == raw["rows"][0]["ident"] and loaded["pair"] == (4, "north")


def test_a07(tmp_path: Path) -> None:
    trace = []
    class Hooks(Schema):
        value = fields.Integer()
        @pre_load
        def before(self, data, **kwargs): trace.append("pre-load"); return {**data, "value": str(data["value"])}
        @post_load
        def after(self, data, **kwargs): trace.append("post-load"); return {**data, "loaded": True}
        @pre_dump
        def before_dump(self, data, **kwargs): trace.append("pre-dump"); return data
        @post_dump
        def after_dump(self, data, **kwargs): trace.append("post-dump"); return data
    schema = Hooks(); assert schema.load({"value": 2}) == {"value": 2, "loaded": True}
    assert schema.dump({"value": 3}) == {"value": 3} and trace == ["pre-load", "post-load", "pre-dump", "post-dump"]


def test_a08(tmp_path: Path) -> None:
    class Pair(Schema):
        left = fields.Integer(required=True)
        right = fields.Integer(required=True)
    schema = Pair()
    assert schema.load({"left": "1"}, partial=("right",)) == {"left": 1}
    error = raises_validation(lambda: schema.load({"left": "bad"}, partial=("right",)))
    assert error.valid_data == {} and set(error.messages) == {"left"}


def test_i01(tmp_path: Path) -> None:
    class Address(Schema):
        city = fields.String(required=True)
        code = fields.Integer(required=True)
    class User(Schema):
        handle = fields.String(data_key="name")
        address = fields.Nested(Address(unknown=EXCLUDE), only=("city",))
    schema = User()
    loaded = schema.load({"name": "ada", "address": {"city": "Paris", "code": 7}})
    assert loaded == {"handle": "ada", "address": {"city": "Paris"}}
    assert schema.dump(loaded) == {"name": "ada", "address": {"city": "Paris"}}


def test_i02(tmp_path: Path) -> None:
    class Child(Schema):
        value = fields.Integer(required=True, validate=validate.Range(min=1))
    class Parent(Schema):
        children = fields.List(fields.Nested(Child()))
    error = raises_validation(lambda: Parent().load({"children": [{"value": "2"}, {"value": 0}, {"value": "bad"}]}))
    assert set(error.messages["children"]) == {1, 2}
    assert error.valid_data == {"children": [{"value": 2}, {}, {}]}


def test_i03(tmp_path: Path) -> None:
    trace = []
    class Batch(Schema):
        value = fields.Integer()
        @pre_load(pass_collection=True)
        def unwrap(self, data, many, **kwargs): trace.append(("pre", many)); return data["items"]
        @post_load(pass_collection=True)
        def summarize(self, data, many, **kwargs): trace.append(("post", many)); return {"rows": data, "count": len(data)}
    result = Batch(many=True).load({"items": [{"value": "1"}, {"value": "2"}]})
    assert result == {"rows": [{"value": 1}, {"value": 2}], "count": 2} and trace == [("pre", True), ("post", True)]


def test_i04(tmp_path: Path) -> None:
    class Upper(fields.Field):
        def _deserialize(self, value, attr, data, **kwargs): return str(value).upper()
        def _serialize(self, value, attr, obj, **kwargs): return str(value).lower()
    class Payload(Schema):
        label = Upper(required=True)
        @validates_schema
        def coherent(self, data, **kwargs):
            if data["label"] == "BLOCKED": raise ValidationError("blocked", field_name="label")
    schema = Payload(); assert schema.load({"label": "ok"}) == {"label": "OK"}
    assert schema.dump({"label": "LOUD"}) == {"label": "loud"}
    assert "label" in raises_validation(lambda: schema.load({"label": "blocked"})).messages


def test_s01(tmp_path: Path) -> None:
    Child = Schema.from_dict({"key": fields.String(required=True), "amount": fields.Decimal(as_string=True)})
    Parent = Schema.from_dict({"rows": fields.List(fields.Nested(Child())), "enabled": fields.Boolean(load_default=True)})
    schema = Parent()
    loaded = schema.load({"rows": [{"key": "a", "amount": "1.20"}, {"key": "b", "amount": "2.30"}]})
    assert schema.dump(loaded) == {"rows": [{"key": "a", "amount": "1.20"}, {"key": "b", "amount": "2.30"}], "enabled": True}


def test_s02(tmp_path: Path) -> None:
    class Node(Schema):
        name = fields.String(required=True)
        children = fields.List(fields.Nested(lambda: Node(exclude=("children",), unknown=EXCLUDE)), load_default=list)
    raw = {"name": "root", "children": [{"name": "leaf", "children": [{"name": "hidden"}]}]}
    loaded = Node().load(raw)
    assert loaded == {"name": "root", "children": [{"name": "leaf"}]}
    assert Node().dump(loaded) == {"name": "root", "children": [{"name": "leaf"}]}
