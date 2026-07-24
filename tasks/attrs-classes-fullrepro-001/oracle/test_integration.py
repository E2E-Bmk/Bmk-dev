"""Integration tests for attrs-classes-fullrepro-001.

Each test crosses ≥2 public API boundaries.
"""

import typing

import pytest

import attr
import attrs


# --- State Consistency: init → fields → asdict/astuple ---


def test_init_values_visible_through_fields_asdict_astuple():
    """Seam: state consistency across init, fields, asdict, astuple."""
    @attrs.define
    class Record:
        name: str
        count: int = attrs.field(converter=int)

    inst = Record("alpha", "3")
    assert attrs.fields(Record)[0].name == "name"
    assert attrs.asdict(inst) == {"name": "alpha", "count": 3}
    assert attrs.astuple(inst) == ("alpha", 3)


def test_fields_dict_same_objects_as_fields():
    """Seam: state consistency between fields() and fields_dict()."""
    @attrs.define
    class Pair:
        left: int
        right: int

    assert attrs.fields_dict(Pair)["left"] is attrs.fields(Pair).left
    assert attrs.fields_dict(Pair)["right"] is attrs.fields(Pair).right


def test_converter_result_visible_in_all_projections():
    """Seam: converter result consistent across attribute access, asdict, equality."""
    @attrs.define
    class Num:
        v: int = attrs.field(converter=int)

    inst = Num("42")
    assert inst.v == 42
    assert attrs.asdict(inst) == {"v": 42}
    assert inst == Num(42)


def test_validator_failure_prevents_storage():
    """Seam: validator interacts with init to prevent bad state."""
    @attrs.define
    class Pos:
        n: int = attrs.field(validator=attrs.validators.gt(0))

    with pytest.raises(ValueError):
        Pos(0)


# --- Protocol Handoff: converter → validator → stored value ---


def test_converter_then_validator_pipeline_on_init():
    """Seam: protocol handoff between converter output and validator input."""
    @attrs.define
    class Port:
        value: int = attrs.field(converter=int, validator=attrs.validators.ge(1))

    assert Port("8080").value == 8080
    with pytest.raises(ValueError):
        Port("0")


def test_modern_assignment_runs_converter_then_validator():
    """Seam: protocol handoff on assignment for modern classes."""
    @attrs.define
    class Num:
        v: int = attrs.field(converter=int, validator=attrs.validators.ge(0))

    inst = Num("5")
    inst.v = "10"
    assert inst.v == 10
    with pytest.raises(ValueError):
        inst.v = "-1"


def test_setters_pipe_converts_then_validates():
    """Seam: protocol handoff using explicit setters.pipe."""
    @attrs.define(on_setattr=attrs.setters.pipe(attrs.setters.convert, attrs.setters.validate))
    class Num:
        v: int = attrs.field(converter=int, validator=attrs.validators.gt(0))

    inst = Num("3")
    inst.v = "7"
    assert inst.v == 7
    with pytest.raises(ValueError):
        inst.v = "0"


def test_no_op_setter_skips_converter_on_assignment():
    """Seam: config interaction between NO_OP setter and converter."""
    @attrs.define
    class Mixed:
        checked: int = attrs.field(converter=int)
        raw: object = attrs.field(converter=int, on_setattr=attrs.setters.NO_OP)

    inst = Mixed("1", "2")
    inst.checked = "3"
    inst.raw = "not-converted"
    assert inst.checked == 3
    assert inst.raw == "not-converted"


# --- Lifecycle: evolve ---


def test_evolve_produces_new_instance_with_unchanged_fields():
    """Seam: lifecycle - evolve preserves original and creates modified copy."""
    @attrs.define
    class Config:
        host: str
        port: int = attrs.field(converter=int)

    original = Config("localhost", "8080")
    evolved = attrs.evolve(original, port="9090")

    assert original.port == 8080
    assert evolved.port == 9090
    assert evolved.host == "localhost"


def test_evolve_runs_converters_and_validators():
    """Seam: protocol handoff - evolve goes through init pipeline."""
    @attrs.define
    class Bounded:
        v: int = attrs.field(converter=int, validator=attrs.validators.ge(1))

    inst = Bounded("5")
    evolved = attrs.evolve(inst, v="3")
    assert evolved.v == 3
    with pytest.raises(ValueError):
        attrs.evolve(inst, v="0")


def test_evolve_uses_stripped_alias_for_private_field():
    """Seam: protocol handoff between field naming and evolve argument."""
    @attrs.define
    class Secret:
        _value: int

    changed = attrs.evolve(Secret(1), value=2)
    assert attrs.asdict(changed) == {"_value": 2}


def test_evolve_rejects_init_false_field():
    """Seam: config interaction between init=False and evolve."""
    @attrs.define
    class Derived:
        x: int
        y: int = attrs.field(init=False, default=10)

    with pytest.raises(TypeError):
        attrs.evolve(Derived(1), y=3)


# --- Collection Conversion: asdict/astuple with nesting ---


def test_asdict_recurses_nested_attrs_in_lists():
    """Seam: state consistency between asdict recursion and nested instances."""
    @attrs.define
    class Point:
        x: int
        y: int

    @attrs.define
    class Shape:
        points: list

    shape = Shape([Point(1, 2), Point(3, 4)])
    assert attrs.asdict(shape) == {"points": [{"x": 1, "y": 2}, {"x": 3, "y": 4}]}


def test_asdict_recurse_false_preserves_instances():
    """Seam: config interaction between recurse=False and nested values."""
    @attrs.define
    class Inner:
        v: int

    @attrs.define
    class Outer:
        child: Inner

    inner = Inner(5)
    assert attrs.asdict(Outer(inner), recurse=False) == {"child": inner}


def test_astuple_returns_values_in_field_order_recursive():
    """Seam: state consistency between field order and astuple output."""
    @attrs.define
    class Point:
        x: int
        y: int

    @attrs.define
    class Line:
        start: Point
        end: Point

    assert attrs.astuple(Line(Point(0, 0), Point(1, 1))) == ((0, 0), (1, 1))


# --- Filters ---


def test_include_filter_selects_by_name_and_type():
    """Seam: config interaction between filter and asdict output."""
    @attrs.define
    class User:
        name: str
        age: int
        password: str

    user = User("jane", 30, "secret")
    assert attrs.asdict(user, filter=attrs.filters.include(int)) == {"age": 30}
    assert attrs.asdict(user, filter=attrs.filters.include("name")) == {"name": "jane"}


def test_exclude_filter_removes_matching_fields():
    """Seam: config interaction between filter and asdict output."""
    @attrs.define
    class User:
        name: str
        password: str
        id: int

    user = User("jane", "secret", 7)
    assert attrs.asdict(user, filter=attrs.filters.exclude("password", int)) == {"name": "jane"}


def test_value_serializer_transforms_output_values():
    """Seam: protocol handoff between asdict iteration and serializer."""
    @attrs.define
    class Event:
        name: str
        count: int

    def serialize(inst, attribute, value):
        return f"x:{value}" if attribute.name == "count" else value

    assert attrs.asdict(Event("run", 5), value_serializer=serialize) == {
        "name": "run", "count": "x:5"
    }


# --- Pre/post init hooks ---


def test_pre_and_post_init_run_in_order():
    """Seam: lifecycle crossing between hooks and field initialization."""
    events = []

    @attrs.define
    class Hooked:
        x: int
        y: int = attrs.field(init=False)

        def __attrs_pre_init__(self):
            events.append("pre")

        def __attrs_post_init__(self):
            events.append("post")
            self.y = self.x + 100

    inst = Hooked(5)
    assert inst.y == 105
    assert events == ["pre", "post"]


def test_custom_init_delegates_to_attrs_init():
    """Seam: protocol handoff between custom __init__ and __attrs_init__."""
    @attrs.define
    class Manual:
        v: int

        def __init__(self, v: int = 99):
            self.__attrs_init__(v)

    assert Manual().v == 99
    assert Manual(7).v == 7


def test_attrs_init_subclass_hook_called():
    """Seam: lifecycle crossing between define and subclass hook."""
    registry = []

    class Base:
        @classmethod
        def __attrs_init_subclass__(cls):
            registry.append(cls)

    @attrs.define
    class Child(Base):
        v: int = 0

    assert Child in registry


# --- make_class ---


def test_make_class_from_names_produces_correct_fields():
    """Seam: state consistency between make_class and fields/asdict."""
    Coord = attrs.make_class("Coord", ["x", "y"])
    p = Coord(3, 4)
    assert attrs.asdict(p) == {"x": 3, "y": 4}
    assert [f.name for f in attrs.fields(Coord)] == ["x", "y"]


def test_make_class_with_mapping_and_bases():
    """Seam: config interaction between make_class options and inheritance."""
    class Marker:
        def tag(self):
            return "marked"

    Dynamic = attrs.make_class(
        "Dynamic", {"v": attrs.field(default=0)}, bases=(Marker,)
    )
    assert isinstance(Dynamic(), Marker)
    assert Dynamic().tag() == "marked"


def test_these_argument_defines_fields_for_existing_class():
    """Seam: protocol handoff between external class and attrs field system."""
    class External:
        def __init__(self, value):
            self.value = value

    External = attrs.define(these={"value": attrs.field()}, init=False)(External)
    inst = External(7)
    assert attrs.has(External)
    assert attrs.asdict(inst) == {"value": 7}


# --- Classic namespace interop ---


def test_classic_attr_s_creates_attrs_class():
    """Seam: state consistency between classic API and modern introspection."""
    @attr.s
    class Classic:
        v = attr.ib()

    assert attr.has(Classic)
    assert attrs.has(Classic)
    assert attr.asdict(Classic(5)) == {"v": 5}


def test_classic_and_modern_share_validators_exceptions():
    """Seam: protocol handoff between namespaces."""
    @attrs.define
    class Modern:
        v: int = attrs.field(
            converter=attr.converters.optional(int),
            validator=attr.validators.optional(attr.validators.ge(0)),
        )

    assert Modern("5").v == 5
    assert Modern(None).v is None
    with pytest.raises(ValueError):
        Modern("-1")


def test_classic_set_run_validators_controls_validation():
    """Seam: config interaction between classic switch and validation."""
    @attr.s
    class C:
        v = attr.ib(validator=attr.validators.instance_of(int))

    try:
        attr.set_run_validators(False)
        assert C("bad").v == "bad"
    finally:
        attr.set_run_validators(True)
    with pytest.raises(TypeError):
        C("bad")


def test_attr_dataclass_uses_auto_attribs():
    """Seam: protocol handoff between dataclass decorator and field system."""
    @attr.dataclass
    class Data:
        x: int
        y: str = "default"

    assert attr.asdict(Data(7)) == {"x": 7, "y": "default"}


# --- validate / resolve_types ---


def test_validate_reruns_validators_on_current_state():
    """Seam: state consistency between attribute state and validate()."""
    @attrs.define(on_setattr=attrs.setters.NO_OP)
    class Checked:
        v: int = attrs.field(validator=attrs.validators.instance_of(int))

    inst = Checked(1)
    inst.v = "bad"
    with pytest.raises(TypeError):
        attrs.validate(inst)


def test_resolve_types_resolves_forward_references():
    """Seam: protocol handoff between string annotations and type metadata."""
    @attrs.define
    class Node:
        child: "Leaf"

    @attrs.define
    class Leaf:
        v: int

    assert attrs.fields(Node).child.type == "Leaf"
    attrs.resolve_types(Node, globals(), locals())
    assert attrs.fields(Node).child.type is Leaf


# --- Subclass field ordering ---


def test_subclass_fields_ordered_base_first():
    """Seam: state consistency between inheritance and field order."""
    @attrs.define
    class Base:
        a: int
        b: int = 0

    @attrs.define
    class Child(Base):
        c: int = attrs.field(kw_only=True)

    names = [f.name for f in attrs.fields(Child)]
    assert names == ["a", "b", "c"]
    inst = Child(1, b=2, c=3)
    assert attrs.asdict(inst) == {"a": 1, "b": 2, "c": 3}
    assert attrs.astuple(inst) == (1, 2, 3)


# --- Frozen evolve roundtrip ---


def test_frozen_evolve_preserves_immutability():
    """Seam: lifecycle crossing between frozen constraint and evolve."""
    @attrs.frozen
    class Config:
        host: str
        port: int = attrs.field(converter=int)

    original = Config("localhost", "443")
    evolved = attrs.evolve(original, port="8443")
    assert evolved.port == 8443
    with pytest.raises(attrs.exceptions.FrozenInstanceError):
        evolved.host = "other"


# --- Deep validators with nested attrs ---


def test_deep_iterable_validates_then_asdict_recurses():
    """Seam: state consistency between deep validator and recursive asdict."""
    @attrs.define
    class Item:
        name: str

    @attrs.define
    class Container:
        items: list = attrs.field(
            factory=list,
            validator=attrs.validators.deep_iterable(
                member_validator=attrs.validators.instance_of(Item),
            ),
        )

    c = Container([Item("a"), Item("b")])
    assert attrs.asdict(c) == {"items": [{"name": "a"}, {"name": "b"}]}
    with pytest.raises(TypeError):
        Container(["not-item"])


# --- Converter wrapper with self and field ---


def test_converter_wrapper_receives_instance_and_field():
    """Seam: protocol handoff between Converter wrapper and init pipeline."""
    def convert(value, instance, field):
        return int(value) * instance.multiplier + field.metadata["offset"]

    @attrs.define
    class Scaled:
        multiplier = 3
        v: int = attrs.field(
            metadata={"offset": 1},
            converter=attrs.Converter(convert, takes_self=True, takes_field=True),
        )

    assert Scaled("4").v == 13


# --- Factory takes_self ---


def test_factory_takes_self_uses_partial_instance():
    """Seam: protocol handoff between Factory and partial initialization."""
    @attrs.define
    class Pair:
        left: list = attrs.Factory(list)
        right: set = attrs.Factory(lambda self: set(self.left), takes_self=True)

    assert Pair([1, 2, 2]).right == {1, 2}
