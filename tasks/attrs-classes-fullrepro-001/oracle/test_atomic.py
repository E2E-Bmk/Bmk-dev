# Spec2Repo oracle - atomic tests for attrs-classes-fullrepro-001
import enum
import inspect
import typing

import pytest

import attr
import attrs


def test_empty_attrs_classes_compare_by_class_and_fields():
    @attrs.define
    class Empty:
        pass

    @attrs.define
    class OtherEmpty:
        pass

    assert Empty() == Empty()
    assert Empty() != OtherEmpty()


def test_unannotated_field_switches_to_explicit_field_collection():
    @attrs.define
    class Record:
        ignored: int
        kept = attrs.field()

    assert [field.name for field in attrs.fields(Record)] == ["kept"]
    assert Record(3).kept == 3
    assert not hasattr(Record(3), "ignored")


def test_classvar_annotations_are_not_fields():
    @attrs.define
    class WithClassVar:
        marker: typing.ClassVar[int] = 10
        value: int = 4

    assert [field.name for field in attrs.fields(WithClassVar)] == ["value"]
    assert WithClassVar.marker == 10
    assert WithClassVar().value == 4


def test_fields_support_tuple_index_and_attribute_lookup():
    @attrs.define
    class Item:
        sku: str
        count: int

    fields = attrs.fields(Item)
    assert fields[0].name == "sku"
    assert fields.count is fields[1]
    assert attrs.fields(Item("a", 2)) is fields


def test_has_identifies_attrs_classes_only():
    @attrs.define
    class Thing:
        pass

    assert attrs.has(Thing) is True
    assert attrs.has(Thing()) is True
    assert attrs.has(object) is False


def test_private_attribute_default_alias_strips_leading_underscore():
    @attrs.define
    class Token:
        _value: int

    sig = inspect.signature(Token.__init__)
    assert "value" in sig.parameters
    assert "_value" not in sig.parameters
    assert attrs.asdict(Token(4)) == {"_value": 4}


def test_field_alias_overrides_initializer_argument_name():
    @attrs.define
    class Token:
        _value: int = attrs.field(alias="_value")
        label: str = attrs.field(alias="public_label")

    sig = inspect.signature(Token.__init__)
    assert "_value" in sig.parameters
    assert "public_label" in sig.parameters
    assert attrs.asdict(Token(_value=3, public_label="x")) == {"_value": 3, "label": "x"}


def test_keyword_only_fields_require_keywords():
    @attrs.define
    class Params:
        name: str
        limit: int = attrs.field(kw_only=True)

    with pytest.raises(TypeError):
        Params("jobs", 3)
    assert Params("jobs", limit=3).limit == 3


def test_class_level_keyword_only_applies_to_all_fields():
    @attrs.define(kw_only=True)
    class Params:
        name: str
        limit: int

    with pytest.raises(TypeError):
        Params("jobs", 3)
    assert Params(name="jobs", limit=3).name == "jobs"


def test_keyword_only_subclass_field_is_allowed_after_base_default():
    @attrs.define
    class Base:
        retries: int = 2

    @attrs.define
    class Child(Base):
        endpoint: str = attrs.field(kw_only=True)

    assert attrs.asdict(Child(endpoint="api")) == {"retries": 2, "endpoint": "api"}


def test_required_positional_field_after_default_raises_value_error():
    with pytest.raises(ValueError):

        @attrs.define
        class BadOrder:
            optional: int = 1
            required: int


def test_decorator_default_uses_earlier_field_value():
    @attrs.define
    class Derived:
        x: int = 4
        y: int = attrs.field()

        @y.default
        def make_y(self):
            return self.x + 1

    assert attrs.asdict(Derived()) == {"x": 4, "y": 5}


def test_init_false_field_gets_default_and_is_not_init_argument():
    @attrs.define
    class Counter:
        value: int
        doubled: int = attrs.field(init=False)

        @doubled.default
        def make_doubled(self):
            return self.value * 2

    assert Counter(5).doubled == 10
    with pytest.raises(TypeError):
        Counter(5, doubled=12)


def test_repr_omits_fields_marked_repr_false():
    @attrs.define
    class Credentials:
        user: str
        password: str = attrs.field(repr=False)

    rendered = repr(Credentials("me", "secret"))
    assert "Credentials" in rendered
    assert "user" in rendered
    assert "secret" not in rendered
    assert "password" not in rendered


def test_callable_repr_formats_field_value():
    @attrs.define
    class Credentials:
        user: str
        password: str = attrs.field(repr=lambda value: "***")

    rendered = repr(Credentials("me", "secret"))
    assert "***" in rendered
    assert "secret" not in rendered


def test_eq_false_field_is_ignored_for_equality():
    @attrs.define
    class Measurement:
        name: str
        cached: int = attrs.field(eq=False)

    assert Measurement("temp", 1) == Measurement("temp", 99)


def test_order_uses_participating_fields_in_order():
    @attrs.define(order=True)
    class Version:
        major: int
        minor: int

    assert Version(1, 2) < Version(1, 3)
    assert Version(2, 0) > Version(1, 99)


def test_order_false_field_is_ignored_for_ordering():
    @attrs.define(order=True)
    class Version:
        major: int
        build: int = attrs.field(order=False)

    assert not (Version(1, 10) < Version(1, 1))
    assert not (Version(1, 10) > Version(1, 1))


def test_frozen_value_class_is_hashable_and_mutable_value_class_is_not():
    @attrs.frozen
    class Frozen:
        value: int

    @attrs.define
    class Mutable:
        value: int

    assert hash(Frozen(1)) == hash(Frozen(1))
    with pytest.raises(TypeError):
        hash(Mutable(1))


def test_slots_default_removes_instance_dict_and_slots_false_keeps_it():
    @attrs.define
    class Slotted:
        value: int

    @attrs.define(slots=False)
    class DictBacked:
        value: int

    assert not hasattr(Slotted(1), "__dict__")
    assert hasattr(DictBacked(1), "__dict__")


def test_match_args_excludes_keyword_only_fields():
    @attrs.define
    class Pattern:
        x: int
        y: int = attrs.field(kw_only=True)

    assert Pattern.__match_args__ == ("x",)


def test_frozen_class_rejects_assignment_with_frozen_instance_error():
    @attrs.frozen
    class Config:
        value: int

    inst = Config(1)
    with pytest.raises(attrs.exceptions.FrozenInstanceError):
        inst.value = 2
    assert inst.value == 1


def test_field_level_frozen_setter_rejects_only_that_field():
    @attrs.define(on_setattr=attrs.setters.NO_OP)
    class Config:
        locked: int = attrs.field(on_setattr=attrs.setters.frozen)
        open_value: int = 0

    inst = Config(1)
    with pytest.raises(attrs.exceptions.FrozenAttributeError):
        inst.locked = 2
    inst.open_value = 3
    assert attrs.asdict(inst) == {"locked": 1, "open_value": 3}


def test_no_op_setter_disables_class_wide_assignment_hooks_for_field():
    @attrs.define
    class Mixed:
        checked: int = attrs.field(converter=int)
        raw: object = attrs.field(converter=int, on_setattr=attrs.setters.NO_OP)

    inst = Mixed("1", "2")
    inst.checked = "3"
    inst.raw = "4"
    assert inst.checked == 3
    assert inst.raw == "4"


def test_validate_runs_validators_against_current_values():
    @attrs.define(on_setattr=attrs.setters.NO_OP)
    class Number:
        value: int = attrs.field(validator=attrs.validators.instance_of(int))

    inst = Number(1)
    inst.value = "bad"
    with pytest.raises(TypeError):
        attrs.validate(inst)


def test_validator_list_and_decorator_validator_both_run():
    @attrs.define
    class Byte:
        value: int = attrs.field(validator=attrs.validators.instance_of(int))

        @value.validator
        def fits_byte(self, attribute, value):
            if not 0 <= value < 256:
                raise ValueError("out of range")

    assert Byte(128).value == 128
    with pytest.raises(TypeError):
        Byte("128")
    with pytest.raises(ValueError):
        Byte(256)


def test_comparison_validators_accept_and_reject_values():
    @attrs.define
    class Limits:
        low: int = attrs.field(validator=attrs.validators.ge(1))
        high: int = attrs.field(validator=attrs.validators.lt(10))

    assert attrs.asdict(Limits(1, 9)) == {"low": 1, "high": 9}
    with pytest.raises(ValueError):
        Limits(0, 9)
    with pytest.raises(ValueError):
        Limits(1, 10)


def test_length_validators_accept_and_reject_values():
    @attrs.define
    class Name:
        value: str = attrs.field(validator=[attrs.validators.min_len(2), attrs.validators.max_len(4)])

    assert Name("abcd").value == "abcd"
    with pytest.raises(ValueError):
        Name("a")
    with pytest.raises(ValueError):
        Name("abcde")


def test_in_validator_accepts_enum_members_and_list_members():
    class State(enum.Enum):
        ON = "on"
        OFF = "off"

    @attrs.define
    class Choice:
        state: State = attrs.field(validator=attrs.validators.in_(State))
        number: int = attrs.field(validator=attrs.validators.in_([1, 2, 3]))

    assert Choice(State.ON, 2).state is State.ON
    with pytest.raises(ValueError):
        Choice("on", 2)
    with pytest.raises(ValueError):
        Choice(State.ON, 4)


def test_optional_validator_accepts_none_and_validates_non_none():
    @attrs.define
    class Maybe:
        value: int | None = attrs.field(validator=attrs.validators.optional(attrs.validators.instance_of(int)))

    assert Maybe(None).value is None
    assert Maybe(3).value == 3
    with pytest.raises(TypeError):
        Maybe("3")


def test_is_callable_validator_raises_not_callable_error():
    @attrs.define
    class Callback:
        fn: object = attrs.field(validator=attrs.validators.is_callable())

    assert Callback(len).fn is len
    with pytest.raises(attrs.exceptions.NotCallableError):
        Callback("len")


def test_matches_re_validator_checks_regular_expression():
    @attrs.define
    class User:
        email: str = attrs.field(validator=attrs.validators.matches_re(r"^[^@]+@[^@]+$"))

    assert User("a@example.invalid").email == "a@example.invalid"
    with pytest.raises(ValueError):
        User("not-an-email")


def test_deep_iterable_validates_container_and_members():
    @attrs.define
    class Numbers:
        values: list[int] = attrs.field(
            validator=attrs.validators.deep_iterable(
                member_validator=attrs.validators.instance_of(int),
                iterable_validator=attrs.validators.instance_of(list),
            )
        )

    assert Numbers([1, 2, 3]).values == [1, 2, 3]
    with pytest.raises(TypeError):
        Numbers({1, 2, 3})
    with pytest.raises(TypeError):
        Numbers([1, "2"])


def test_deep_mapping_validates_mapping_keys_and_values():
    @attrs.define
    class Scores:
        values: dict[str, int] = attrs.field(
            validator=attrs.validators.deep_mapping(
                key_validator=attrs.validators.instance_of(str),
                value_validator=attrs.validators.instance_of(int),
                mapping_validator=attrs.validators.instance_of(dict),
            )
        )

    assert Scores({"a": 1}).values == {"a": 1}
    with pytest.raises(TypeError):
        Scores(None)
    with pytest.raises(TypeError):
        Scores({1: 2})
    with pytest.raises(TypeError):
        Scores({"a": 1.5})


def test_or_validator_accepts_first_successful_validator():
    @attrs.define
    class Value:
        value: object = attrs.field(
            validator=attrs.validators.or_(
                attrs.validators.instance_of(int),
                attrs.validators.deep_iterable(attrs.validators.instance_of(int)),
            )
        )

    assert Value(3).value == 3
    assert Value([1, 2]).value == [1, 2]
    with pytest.raises(ValueError):
        Value("3")


def test_not_validator_rejects_values_accepted_by_wrapped_validator():
    reserved = {"id", "source"}

    @attrs.define
    class Tag:
        name: str = attrs.field(validator=attrs.validators.not_(attrs.validators.in_(reserved)))

    assert Tag("custom").name == "custom"
    with pytest.raises(ValueError):
        Tag("id")


def test_validator_disable_context_manager_restores_previous_state():
    @attrs.define
    class Number:
        value: int = attrs.field(validator=attrs.validators.instance_of(int))

    with attrs.validators.disabled():
        assert Number("1").value == "1"
    with pytest.raises(TypeError):
        Number("1")


def test_global_validator_disable_switch_controls_validation():
    @attrs.define
    class Number:
        value: int = attrs.field(validator=attrs.validators.instance_of(int))

    try:
        attrs.validators.set_disabled(True)
        assert Number("1").value == "1"
    finally:
        attrs.validators.set_disabled(False)
    with pytest.raises(TypeError):
        Number("1")


def test_converter_runs_before_validator_on_initialization():
    @attrs.define
    class Number:
        value: int = attrs.field(converter=int, validator=attrs.validators.ge(0))

    assert Number("3").value == 3
    with pytest.raises(ValueError):
        Number("-1")


def test_converter_pipe_runs_converters_in_order():
    @attrs.define
    class Text:
        value: str = attrs.field(converter=attrs.converters.pipe(str.strip, str.upper))

    assert Text("  hello ").value == "HELLO"


def test_converter_list_behaves_like_pipe():
    @attrs.define
    class Text:
        value: str = attrs.field(converter=[str.strip, str.lower])

    assert Text("  HELLO ").value == "hello"


def test_optional_converter_leaves_none_and_converts_other_values():
    @attrs.define
    class MaybeNumber:
        value: int | None = attrs.field(converter=attrs.converters.optional(int))

    assert MaybeNumber(None).value is None
    assert MaybeNumber("5").value == 5


def test_to_bool_accepts_documented_truthy_and_falsy_values():
    assert attrs.converters.to_bool("yes") is True
    assert attrs.converters.to_bool("OFF") is False
    assert attrs.converters.to_bool(1) is True
    assert attrs.converters.to_bool(0) is False
    with pytest.raises(ValueError):
        attrs.converters.to_bool("norway")


def test_converter_wrapper_can_receive_self_and_field():
    def convert(value, instance, field):
        return int(value) * instance.factor + field.metadata["offset"]

    @attrs.define
    class Scaled:
        factor = 5
        value: int = attrs.field(
            metadata={"offset": 2},
            converter=attrs.Converter(convert, takes_self=True, takes_field=True),
        )

    assert Scaled("4").value == 22


def test_decorator_converter_can_use_instance_and_attribute():
    @attrs.define
    class Scaled:
        factor: typing.ClassVar[int] = 4
        value: int = attrs.field(metadata={"offset": 1})

        @value.converter
        def convert(self, attribute, value):
            return int(value) * self.factor + attribute.metadata["offset"]

    assert Scaled("3").value == 13


def test_field_metadata_is_read_only_and_visible_on_attribute():
    @attrs.define
    class Meta:
        value: int = attrs.field(metadata={"unit": "ms"})

    metadata = attrs.fields(Meta).value.metadata
    assert metadata["unit"] == "ms"
    with pytest.raises(TypeError):
        metadata["unit"] = "s"


def test_field_type_metadata_comes_from_annotation_and_field_type():
    @attrs.define
    class Annotated:
        value: int

    @attrs.define
    class Explicit:
        value = attrs.field(type=str)

    assert attrs.fields(Annotated).value.type is int
    assert attrs.fields(Explicit).value.type is str


def test_resolve_types_updates_forward_reference_types():
    @attrs.define
    class Node:
        child: "Leaf"

    @attrs.define
    class Leaf:
        value: int

    assert attrs.fields(Node).child.type == "Leaf"
    assert attrs.resolve_types(Node, globals(), locals()) is Node
    assert attrs.fields(Node).child.type is Leaf


def test_attr_dataclass_uses_annotations_as_fields():
    @attr.dataclass
    class ClassicData:
        value: int
        label: str = "x"

    assert attr.asdict(ClassicData(5)) == {"value": 5, "label": "x"}


def test_fields_on_non_attrs_class_raises_not_attrs_class_error():
    with pytest.raises(attrs.exceptions.NotAnAttrsClassError):
        attrs.fields(object)


def test_unknown_and_missing_initializer_arguments_raise_type_error():
    @attrs.define
    class Point:
        x: int
        y: int

    with pytest.raises(TypeError):
        Point(1)
    with pytest.raises(TypeError):
        Point(1, 2, 3)
    with pytest.raises(TypeError):
        Point(1, 2, z=3)


def test_mixing_auto_annotations_with_unannotated_field_raises():
    with pytest.raises(attrs.exceptions.UnannotatedAttributeError):

        @attr.s(auto_attribs=True)
        class Mixed:
            x: int
            y = attr.ib()


def test_setting_default_twice_raises_default_already_set():
    field = attrs.field(default=1)
    with pytest.raises(attrs.exceptions.DefaultAlreadySetError):

        @field.default
        def make_default(self):
            return 2
