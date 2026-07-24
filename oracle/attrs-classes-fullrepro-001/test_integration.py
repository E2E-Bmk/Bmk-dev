# Spec2Repo oracle - integration tests for attrs-classes-fullrepro-001
import enum
import inspect
import typing

import pytest

import attr
import attrs


def test_modern_and_classic_namespaces_import_shared_modules():
    assert attrs.validators.instance_of is attr.validators.instance_of
    assert attrs.converters.optional is attr.converters.optional
    assert attrs.filters.include is attr.filters.include
    assert attrs.setters.NO_OP is attr.setters.NO_OP
    assert attrs.exceptions.FrozenInstanceError is attr.exceptions.FrozenInstanceError


def test_define_builds_basic_value_class_with_positional_and_keyword_init():
    @attrs.define
    class Point:
        x: int
        y: int

    assert Point(1, 2) == Point(x=1, y=2)
    assert attrs.asdict(Point(1, 2)) == {"x": 1, "y": 2}


def test_fields_dict_uses_same_attribute_objects_as_fields():
    @attrs.define
    class Item:
        sku: str
        count: int

    fields = attrs.fields(Item)
    fields_dict = attrs.fields_dict(Item)
    assert list(fields_dict) == ["sku", "count"]
    assert fields_dict["sku"] is fields.sku
    assert fields_dict["count"] is fields.count


def test_factory_creates_fresh_mutable_value_per_instance():
    @attrs.define
    class Bag:
        values: list[int] = attrs.field(factory=list)

    first = Bag()
    second = Bag()
    first.values.append(1)
    assert first.values == [1]
    assert second.values == []


def test_factory_takes_self_uses_partially_initialized_instance():
    @attrs.define
    class Pair:
        left: list[int] = attrs.Factory(list)
        right: set[int] = attrs.Factory(lambda self: set(self.left), takes_self=True)

    assert Pair([1, 2, 2]).right == {1, 2}


def test_pre_and_post_init_hooks_run_in_initializer_order():
    events = []

    @attrs.define
    class Hooked:
        x: int
        y: int = attrs.field(init=False)

        def __attrs_pre_init__(self):
            events.append("pre")

        def __attrs_post_init__(self):
            events.append("post")
            self.y = self.x + 10

    assert Hooked(2).y == 12
    assert events == ["pre", "post"]


def test_custom_init_can_delegate_to_attrs_init():
    @attrs.define
    class Manual:
        value: int

        def __init__(self, value: int = 7):
            self.__attrs_init__(value)

    assert Manual().value == 7
    assert Manual(3).value == 3


def test_attrs_init_subclass_hook_runs_after_attrs_processing():
    registry = []

    class Base:
        @classmethod
        def __attrs_init_subclass__(cls):
            registry.append(cls)

    @attrs.define
    class Impl(Base):
        value: int = 1

    assert registry == [Impl]
    assert attrs.has(Impl)


def test_modern_assignment_runs_converter_and_validator_by_default():
    @attrs.define
    class Number:
        value: int = attrs.field(converter=int, validator=attrs.validators.ge(0))

    inst = Number("1")
    inst.value = "2"
    assert inst.value == 2
    with pytest.raises(ValueError):
        inst.value = "-1"
    assert inst.value == 2


def test_setters_pipe_converts_then_validates_on_assignment():
    @attrs.define(on_setattr=attrs.setters.pipe(attrs.setters.convert, attrs.setters.validate))
    class Number:
        value: int = attrs.field(converter=int, validator=attrs.validators.gt(0))

    inst = Number("1")
    inst.value = "2"
    assert inst.value == 2
    with pytest.raises(ValueError):
        inst.value = "0"


def test_classic_attr_s_does_not_validate_assignment_by_default():
    @attr.s
    class Classic:
        value = attr.ib(validator=attr.validators.instance_of(int))

    inst = Classic(1)
    inst.value = "not checked"
    assert inst.value == "not checked"


def test_default_if_none_uses_default_or_factory_only_for_none():
    @attrs.define
    class Defaults:
        text: str = attrs.field(converter=attrs.converters.default_if_none(""))
        items: list[int] = attrs.field(converter=attrs.converters.default_if_none(factory=list))

    first = Defaults(None, None)
    second = Defaults("x", None)
    first.items.append(1)
    assert first.text == ""
    assert second.text == "x"
    assert second.items == []


def test_asdict_recurses_into_nested_attrs_instances_and_collections():
    @attrs.define
    class Point:
        x: int
        y: int

    @attrs.define
    class Shape:
        points: list[Point]
        tags: tuple[Point, ...]

    shape = Shape([Point(1, 2)], (Point(3, 4),))
    assert attrs.asdict(shape) == {
        "points": [{"x": 1, "y": 2}],
        "tags": ({"x": 3, "y": 4},),
    }


def test_asdict_recurse_false_keeps_nested_instances():
    @attrs.define
    class Point:
        x: int

    @attrs.define
    class Box:
        point: Point

    point = Point(1)
    assert attrs.asdict(Box(point), recurse=False) == {"point": point}


def test_astuple_returns_values_in_field_order_and_recurses():
    @attrs.define
    class Point:
        x: int
        y: int

    @attrs.define
    class Box:
        point: Point
        label: str

    assert attrs.astuple(Box(Point(1, 2), "a")) == ((1, 2), "a")


def test_filters_include_and_exclude_by_attribute_name_and_type():
    @attrs.define
    class User:
        login: str
        password: str
        id: int

    user = User("jane", "secret", 42)
    assert attrs.asdict(user, filter=attrs.filters.exclude("password", int)) == {"login": "jane"}
    assert attrs.asdict(user, filter=attrs.filters.include(str)) == {
        "login": "jane",
        "password": "secret",
    }
    assert attrs.asdict(user, filter=attrs.filters.include(attrs.fields(User).id)) == {"id": 42}


def test_asdict_value_serializer_transforms_included_values():
    @attrs.define
    class Event:
        name: str
        count: int

    def serialize(instance, attribute, value):
        if attribute.name == "count":
            return f"count={value}"
        return value

    assert attrs.asdict(Event("run", 3), value_serializer=serialize) == {
        "name": "run",
        "count": "count=3",
    }


def test_evolve_copies_instance_and_runs_converters_and_validators():
    @attrs.define
    class Number:
        value: int = attrs.field(converter=int, validator=attrs.validators.gt(0))
        label: str = "n"

    original = Number("1")
    changed = attrs.evolve(original, value="2")
    assert attrs.asdict(original) == {"value": 1, "label": "n"}
    assert attrs.asdict(changed) == {"value": 2, "label": "n"}
    with pytest.raises(ValueError):
        attrs.evolve(original, value="0")


def test_evolve_uses_initializer_alias_for_private_named_field():
    @attrs.define
    class Secret:
        _value: int

    changed = attrs.evolve(Secret(1), value=2)
    assert attrs.asdict(changed) == {"_value": 2}


def test_evolve_rejects_init_false_changes():
    @attrs.define
    class Derived:
        x: int
        y: int = attrs.field(init=False, default=10)

    with pytest.raises(Exception):
        attrs.evolve(Derived(1), y=3)


def test_make_class_from_names_creates_required_fields():
    Point = attrs.make_class("Point", ["x", "y"])
    point = Point(1, 2)
    assert attrs.asdict(point) == {"x": 1, "y": 2}
    assert [field.name for field in attrs.fields(Point)] == ["x", "y"]


def test_make_class_from_mapping_uses_field_options():
    Dynamic = attrs.make_class(
        "Dynamic",
        {"x": attrs.field(type=int), "items": attrs.field(factory=list)},
        repr=False,
    )
    inst = Dynamic(3)
    assert attrs.fields(Dynamic).x.type is int
    assert attrs.asdict(inst) == {"x": 3, "items": []}


def test_make_class_honors_bases_argument():
    class Base:
        def marker(self):
            return "base"

    Dynamic = attrs.make_class("Dynamic", {"value": attrs.field(default=1)}, bases=(Base,))
    assert isinstance(Dynamic(), Base)
    assert Dynamic().marker() == "base"


def test_these_argument_defines_fields_for_existing_class():
    class External:
        def __init__(self, value):
            self.value = value

    External = attrs.define(these={"value": attrs.field()}, init=False)(External)
    inst = External(4)
    assert attrs.has(External)
    assert attrs.asdict(inst) == {"value": 4}


def test_attr_s_and_attr_ib_create_classic_attrs_class():
    @attr.s
    class Classic:
        value = attr.ib()

    assert attr.has(Classic)
    assert attr.asdict(Classic(3)) == {"value": 3}


def test_classic_and_modern_fields_interoperate():
    @attr.s
    class Classic:
        value = attr.ib()

    @attrs.define
    class Modern:
        value: int

    assert attrs.fields(Classic).value.name == "value"
    assert attr.fields(Modern).value.name == "value"


def test_classic_validator_switch_interoperates_with_validation():
    @attr.s
    class Classic:
        value = attr.ib(validator=attr.validators.instance_of(int))

    try:
        attr.set_run_validators(False)
        assert Classic("1").value == "1"
    finally:
        attr.set_run_validators(True)
    with pytest.raises(TypeError):
        Classic("1")


def test_default_and_factory_on_same_field_raise_error():
    with pytest.raises(ValueError):
        attrs.field(default=1, factory=list)


def test_field_views_conversion_and_evolution_share_one_declared_state():
    @attrs.define
    class Record:
        count: int = attrs.field(converter=int)
        labels: list[str] = attrs.field(factory=list)

    original = Record("3", ["a"])
    evolved = attrs.evolve(original, count="4")

    assert [attribute.name for attribute in attrs.fields(Record)] == ["count", "labels"]
    assert attrs.asdict(original) == {"count": 3, "labels": ["a"]}
    assert attrs.astuple(original) == (3, ["a"])
    assert evolved == Record(4, ["a"])


def test_modern_class_workflow_converts_validates_and_serializes():
    @attrs.define
    class Service:
        port: int = attrs.field(converter=int, validator=attrs.validators.ge(1))
        tags: list[str] = attrs.field(factory=list)

    service = Service("8080")
    assert attrs.asdict(service) == {"port": 8080, "tags": []}
    with pytest.raises(ValueError):
        Service("0")


def test_validated_frozen_workflow_preserves_public_views():
    @attrs.frozen
    class Config:
        retries: int = attrs.field(converter=int, validator=attrs.validators.ge(0))

    config = Config("2")
    assert attrs.fields(Config).retries.name == "retries"
    assert attrs.astuple(config) == (2,)
    with pytest.raises(attrs.exceptions.FrozenInstanceError):
        config.retries = 3


def test_dynamic_class_workflow_matches_declared_fields_and_defaults():
    Point = attrs.make_class(
        "Point",
        {"x": attrs.field(type=int), "y": attrs.field(default=0)},
    )
    point = Point(3)
    assert attrs.fields(Point).x.type is int
    assert attrs.asdict(point) == {"x": 3, "y": 0}
