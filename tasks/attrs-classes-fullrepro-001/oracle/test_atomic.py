"""Atomic tests for attrs-classes-fullrepro-001.

Each test verifies ONE public API entry point, ONE behavior.
"""

import enum
import inspect
import typing

import pytest

import attr
import attrs


# --- attrs.define / field collection ---


def test_define_creates_class_from_annotated_attributes():
    @attrs.define
    class Coord:
        x: int
        y: int

    assert Coord(3, 7).x == 3
    assert Coord(3, 7).y == 7


def test_classvar_annotations_are_excluded_from_fields():
    @attrs.define
    class Config:
        version: typing.ClassVar[str] = "1.0"
        port: int = 8080

    assert [f.name for f in attrs.fields(Config)] == ["port"]
    assert Config.version == "1.0"


def test_unannotated_field_triggers_explicit_collection():
    @attrs.define
    class Record:
        ignored: int
        tracked = attrs.field()

    assert [f.name for f in attrs.fields(Record)] == ["tracked"]


def test_required_after_default_in_same_group_raises_value_error():
    with pytest.raises(ValueError):

        @attrs.define
        class BadOrder:
            opt: int = 5
            req: int


# --- attrs.fields / fields_dict / has ---


def test_fields_supports_index_and_named_access():
    @attrs.define
    class Item:
        name: str
        qty: int

    f = attrs.fields(Item)
    assert f[0].name == "name"
    assert f.qty is f[1]


def test_fields_accepts_instance_and_returns_same_as_class():
    @attrs.define
    class Box:
        size: int

    assert attrs.fields(Box(1)) is attrs.fields(Box)


def test_fields_dict_returns_ordered_mapping():
    @attrs.define
    class Pair:
        left: int
        right: int

    d = attrs.fields_dict(Pair)
    assert list(d) == ["left", "right"]
    assert d["left"] is attrs.fields(Pair).left


def test_has_returns_true_for_attrs_class_and_instance():
    @attrs.define
    class Thing:
        pass

    assert attrs.has(Thing) is True
    assert attrs.has(Thing()) is True
    assert attrs.has(dict) is False


def test_fields_on_non_attrs_class_raises_not_attrs_class_error():
    with pytest.raises(attrs.exceptions.NotAnAttrsClassError):
        attrs.fields(list)


# --- Initialization and defaults ---


def test_private_field_strips_underscore_in_init():
    @attrs.define
    class Secret:
        _token: str

    sig = inspect.signature(Secret.__init__)
    assert "token" in sig.parameters
    assert "_token" not in sig.parameters


def test_field_alias_overrides_init_argument_name():
    @attrs.define
    class Entry:
        _key: str = attrs.field(alias="_key")
        label: str = attrs.field(alias="lbl")

    sig = inspect.signature(Entry.__init__)
    assert "_key" in sig.parameters
    assert "lbl" in sig.parameters


def test_kw_only_field_requires_keyword_argument():
    @attrs.define
    class Params:
        name: str
        limit: int = attrs.field(kw_only=True)

    with pytest.raises(TypeError):
        Params("test", 10)
    assert Params("test", limit=10).limit == 10


def test_class_level_kw_only_applies_to_all_fields():
    @attrs.define(kw_only=True)
    class Opts:
        host: str
        port: int

    with pytest.raises(TypeError):
        Opts("localhost", 8080)
    assert Opts(host="localhost", port=8080).host == "localhost"


def test_init_false_field_not_accepted_as_argument():
    @attrs.define
    class Derived:
        x: int
        computed: int = attrs.field(init=False, default=0)

    with pytest.raises(TypeError):
        Derived(1, computed=2)
    assert Derived(1).computed == 0


def test_decorator_default_receives_partially_initialized_instance():
    @attrs.define
    class Derived:
        base: int = 3
        doubled: int = attrs.field()

        @doubled.default
        def make_doubled(self):
            return self.base * 2

    assert Derived().doubled == 6


def test_factory_creates_fresh_value_per_instance():
    @attrs.define
    class Bag:
        items: list = attrs.field(factory=list)

    a = Bag()
    b = Bag()
    a.items.append(1)
    assert b.items == []


def test_both_default_and_factory_raises_error():
    with pytest.raises(ValueError):
        attrs.field(default=1, factory=list)


def test_default_already_set_raises_error():
    f = attrs.field(default=1)
    with pytest.raises(attrs.exceptions.DefaultAlreadySetError):

        @f.default
        def make(self):
            return 2


# --- Generated methods ---


def test_equality_compares_same_class_field_values():
    @attrs.define
    class Vec:
        x: int
        y: int

    assert Vec(1, 2) == Vec(1, 2)
    assert Vec(1, 2) != Vec(1, 3)


def test_different_classes_not_equal_even_with_same_values():
    @attrs.define
    class A:
        v: int

    @attrs.define
    class B:
        v: int

    assert A(1) != B(1)


def test_eq_false_field_excluded_from_equality():
    @attrs.define
    class Measure:
        name: str
        cached: int = attrs.field(eq=False)

    assert Measure("x", 1) == Measure("x", 99)


def test_ordering_uses_fields_in_order():
    @attrs.define(order=True)
    class Version:
        major: int
        minor: int

    assert Version(1, 9) < Version(2, 0)
    assert Version(2, 1) > Version(2, 0)


def test_order_false_field_excluded_from_comparisons():
    @attrs.define(order=True)
    class Priority:
        level: int
        label: str = attrs.field(order=False)

    assert not (Priority(1, "z") < Priority(1, "a"))
    assert not (Priority(1, "z") > Priority(1, "a"))


def test_frozen_class_is_hashable():
    @attrs.frozen
    class Token:
        value: int

    assert hash(Token(42)) == hash(Token(42))


def test_mutable_class_is_not_hashable():
    @attrs.define
    class Mutable:
        value: int

    with pytest.raises(TypeError):
        hash(Mutable(1))


def test_frozen_class_rejects_assignment():
    @attrs.frozen
    class Immutable:
        data: int

    obj = Immutable(5)
    with pytest.raises(attrs.exceptions.FrozenInstanceError):
        obj.data = 6


def test_field_level_frozen_setter():
    @attrs.define(on_setattr=attrs.setters.NO_OP)
    class Mixed:
        locked: int = attrs.field(on_setattr=attrs.setters.frozen)
        open: int = 0

    obj = Mixed(1)
    with pytest.raises(attrs.exceptions.FrozenAttributeError):
        obj.locked = 2
    obj.open = 9
    assert obj.open == 9


# --- Validators ---


def test_instance_of_validator_rejects_wrong_type():
    @attrs.define
    class Typed:
        value: int = attrs.field(validator=attrs.validators.instance_of(int))

    assert Typed(5).value == 5
    with pytest.raises(TypeError):
        Typed("5")


def test_ge_validator_rejects_too_small():
    @attrs.define
    class Bounded:
        n: int = attrs.field(validator=attrs.validators.ge(10))

    assert Bounded(10).n == 10
    with pytest.raises(ValueError):
        Bounded(9)


def test_lt_validator_rejects_too_large():
    @attrs.define
    class Capped:
        n: int = attrs.field(validator=attrs.validators.lt(100))

    assert Capped(99).n == 99
    with pytest.raises(ValueError):
        Capped(100)


def test_min_len_and_max_len_validators():
    @attrs.define
    class Bounded:
        s: str = attrs.field(validator=[attrs.validators.min_len(2), attrs.validators.max_len(5)])

    assert Bounded("abc").s == "abc"
    with pytest.raises(ValueError):
        Bounded("a")
    with pytest.raises(ValueError):
        Bounded("abcdef")


def test_in_validator_with_enum():
    class Color(enum.Enum):
        RED = "red"
        BLUE = "blue"

    @attrs.define
    class Pick:
        c: Color = attrs.field(validator=attrs.validators.in_(Color))

    assert Pick(Color.RED).c is Color.RED
    with pytest.raises(ValueError):
        Pick("red")


def test_optional_validator_accepts_none():
    @attrs.define
    class Maybe:
        v: typing.Optional[int] = attrs.field(
            validator=attrs.validators.optional(attrs.validators.instance_of(int))
        )

    assert Maybe(None).v is None
    assert Maybe(7).v == 7
    with pytest.raises(TypeError):
        Maybe("7")


def test_is_callable_validator():
    @attrs.define
    class Hook:
        fn: object = attrs.field(validator=attrs.validators.is_callable())

    assert Hook(print).fn is print
    with pytest.raises(attrs.exceptions.NotCallableError):
        Hook(42)


def test_matches_re_validator():
    @attrs.define
    class Code:
        value: str = attrs.field(validator=attrs.validators.matches_re(r"^[A-Z]{3}$"))

    assert Code("ABC").value == "ABC"
    with pytest.raises(ValueError):
        Code("ab")


def test_or_validator_accepts_any_passing():
    @attrs.define
    class Flexible:
        v: object = attrs.field(
            validator=attrs.validators.or_(
                attrs.validators.instance_of(int),
                attrs.validators.instance_of(str),
            )
        )

    assert Flexible(1).v == 1
    assert Flexible("x").v == "x"
    with pytest.raises(ValueError):
        Flexible([])


def test_not_validator_rejects_accepted_values():
    @attrs.define
    class Restricted:
        v: str = attrs.field(
            validator=attrs.validators.not_(attrs.validators.in_(["admin", "root"]))
        )

    assert Restricted("user").v == "user"
    with pytest.raises(ValueError):
        Restricted("admin")


def test_validators_disabled_context_skips_validation():
    @attrs.define
    class Strict:
        n: int = attrs.field(validator=attrs.validators.instance_of(int))

    with attrs.validators.disabled():
        assert Strict("not-int").n == "not-int"
    with pytest.raises(TypeError):
        Strict("not-int")


def test_set_disabled_globally_controls_validators():
    @attrs.define
    class Strict:
        n: int = attrs.field(validator=attrs.validators.instance_of(int))

    try:
        attrs.validators.set_disabled(True)
        assert Strict("bad").n == "bad"
    finally:
        attrs.validators.set_disabled(False)
    with pytest.raises(TypeError):
        Strict("bad")


# --- Converters ---


def test_converter_runs_before_validator():
    @attrs.define
    class Pos:
        n: int = attrs.field(converter=int, validator=attrs.validators.ge(0))

    assert Pos("7").n == 7
    with pytest.raises(ValueError):
        Pos("-1")


def test_pipe_converter_chains_in_order():
    @attrs.define
    class Clean:
        s: str = attrs.field(converter=attrs.converters.pipe(str.strip, str.lower))

    assert Clean("  HELLO  ").s == "hello"


def test_converter_list_behaves_like_pipe():
    @attrs.define
    class Clean:
        s: str = attrs.field(converter=[str.strip, str.upper])

    assert Clean("  world  ").s == "WORLD"


def test_optional_converter_passes_none_through():
    @attrs.define
    class MaybeNum:
        v: typing.Optional[int] = attrs.field(converter=attrs.converters.optional(int))

    assert MaybeNum(None).v is None
    assert MaybeNum("9").v == 9


def test_to_bool_converter_documented_values():
    assert attrs.converters.to_bool("yes") is True
    assert attrs.converters.to_bool("no") is False
    assert attrs.converters.to_bool(1) is True
    assert attrs.converters.to_bool("OFF") is False
    with pytest.raises(ValueError):
        attrs.converters.to_bool("maybe")


def test_default_if_none_replaces_none_only():
    @attrs.define
    class WithDefault:
        v: str = attrs.field(converter=attrs.converters.default_if_none("empty"))

    assert WithDefault(None).v == "empty"
    assert WithDefault("real").v == "real"


# --- Metadata ---


def test_field_metadata_is_read_only_mapping():
    @attrs.define
    class Tagged:
        v: int = attrs.field(metadata={"unit": "kg"})

    meta = attrs.fields(Tagged).v.metadata
    assert meta["unit"] == "kg"
    with pytest.raises(TypeError):
        meta["unit"] = "lb"


def test_field_type_from_annotation():
    @attrs.define
    class Typed:
        v: float

    assert attrs.fields(Typed).v.type is float


# --- Error semantics ---


def test_missing_required_argument_raises_type_error():
    @attrs.define
    class Point:
        x: int
        y: int

    with pytest.raises(TypeError):
        Point(1)


def test_extra_argument_raises_type_error():
    @attrs.define
    class Point:
        x: int

    with pytest.raises(TypeError):
        Point(1, 2)


def test_unannotated_in_auto_attribs_raises_unannotated_error():
    with pytest.raises(attrs.exceptions.UnannotatedAttributeError):

        @attr.s(auto_attribs=True)
        class Bad:
            x: int
            y = attr.ib()
