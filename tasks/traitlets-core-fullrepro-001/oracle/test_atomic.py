import json

import os

import textwrap

import pytest

from traitlets import (
    Any,
    Bool,
    CBool,
    CBytes,
    CFloat,
    CInt,
    CRegExp,
    CUnicode,
    Callable,
    CaselessStrEnum,
    Complex,
    Dict,
    DottedObjectName,
    Enum,
    Float,
    FuzzyEnum,
    HasTraits,
    Instance,
    Int,
    Integer,
    List,
    ObjectName,
    Set,
    TCPAddress,
    This,
    TraitError,
    Tuple,
    Type,
    Unicode,
    Union,
    Bunch,
    default,
    directional_link,
    import_item,
    link,
    observe,
    signature_has_traits,
    validate,
)

from traitlets.config import Application, Config, Configurable, MultipleInstanceError

from traitlets.config.application import boolean_flag

from traitlets.config.loader import (
    ArgumentError,
    ConfigFileNotFound,
    JSONFileConfigLoader,
    KVArgParseConfigLoader,
    LazyConfigValue,
    PyFileConfigLoader,
)

def clear_application_singletons():
    _clear_application_tree()
    yield
    _clear_application_tree()

def _clear_application_tree(cls=Application):
    cls.clear_instance()
    for subclass in cls.__subclasses__():
        _clear_application_tree(subclass)

class IntegerModel(HasTraits):
    value = Integer()

class Worker(Configurable):
    enabled = Bool(False, help="enable worker").tag(config=True)
    label = Unicode("default", help="worker label").tag(config=True)
    count = Int(0, help="worker count").tag(config=True)
    plain = Unicode("plain")

class MiniApp(Application):
    classes = [Worker]
    aliases = {"label": "Worker.label", "count": "Worker.count"}
    flags = {"enable-worker": ({"Worker": {"enabled": True}}, "enable worker")}


def test_top_level_installable_surface_exports_core_names():
    import traitlets

    assert traitlets.HasTraits is HasTraits
    assert traitlets.TraitError is TraitError
    assert traitlets.Unicode is Unicode
    assert traitlets.HasTraits().trait_values() == {}

def test_config_installable_surface_exports_core_names():
    import traitlets.config as config

    assert config.Application is Application
    assert config.Configurable is Configurable
    assert config.Config is Config
    cfg = config.Config()
    cfg.Section.value = 1
    assert cfg["Section"]["value"] == 1

def test_loader_installable_surface_exports_loader_names():
    import traitlets.config.loader as loader

    assert loader.JSONFileConfigLoader is JSONFileConfigLoader
    assert loader.PyFileConfigLoader is PyFileConfigLoader
    assert loader.KVArgParseConfigLoader is KVArgParseConfigLoader
    assert issubclass(loader.ConfigFileNotFound, Exception)

def test_trait_constructor_keyword_sets_public_value():
    obj = IntegerModel(value=5)
    assert obj.value == 5
    assert obj.trait_values()["value"] == 5

def test_trait_constructor_accepts_multiple_known_keywords():
    class Model(HasTraits):
        left = Int()
        right = Unicode()

    obj = Model(left=1, right="ok")
    assert obj.left == 1
    assert obj.right == "ok"

def test_rejected_assignment_preserves_previous_value():
    obj = IntegerModel(value=3)
    with pytest.raises(TraitError):
        obj.value = "bad"
    assert obj.value == 3

def test_trait_metadata_tag_visible_through_trait_metadata():
    class Model(HasTraits):
        name = Unicode().tag(config=True, label="public")

    obj = Model()
    assert obj.trait_metadata("name", "config") is True
    assert obj.trait_metadata("name", "label") == "public"
    assert obj.trait_metadata("name", "missing", "fallback") == "fallback"

def test_tag_returns_same_trait_object():
    trait = Unicode()
    tagged = trait.tag(config=True)
    assert tagged is trait

def test_integer_accepts_int_and_rejects_string():
    obj = IntegerModel()
    obj.value = 12
    assert obj.value == 12
    with pytest.raises(TraitError):
        obj.value = "12"

def test_float_accepts_int_and_float_rejects_text():
    class Model(HasTraits):
        value = Float()

    obj = Model()
    obj.value = 3
    assert obj.value == 3.0
    obj.value = 2.5
    assert obj.value == 2.5
    with pytest.raises(TraitError):
        obj.value = "bad"

def test_coercing_numeric_traits_convert_strings():
    class Model(HasTraits):
        i = CInt()
        f = CFloat()

    obj = Model()
    obj.i = "7"
    obj.f = "2.5"
    assert obj.i == 7
    assert obj.f == 2.5

def test_unicode_bytes_and_coercing_string_traits():
    class Model(HasTraits):
        text = Unicode()
        data = CBytes()
        coerced = CUnicode()

    obj = Model()
    obj.text = "hello"
    obj.data = b"abc"
    obj.coerced = 123
    assert obj.text == "hello"
    assert obj.data == b"abc"
    assert obj.coerced == "123"
    with pytest.raises(TraitError):
        obj.data = "text"

def test_bool_and_cbool_store_boolean_values():
    class Model(HasTraits):
        strict = Bool()
        coerced = CBool()

    obj = Model()
    obj.strict = True
    obj.coerced = []
    assert obj.strict is True
    assert obj.coerced is False
    with pytest.raises(TraitError):
        obj.strict = "true"

def test_enum_and_caseless_enum_validation():
    class Model(HasTraits):
        color = Enum(["red", "blue"])
        mode = CaselessStrEnum(["fast", "slow"])

    obj = Model(color="red", mode="FAST")
    assert obj.color == "red"
    assert obj.mode == "fast"
    with pytest.raises(TraitError):
        obj.color = "green"

def test_fuzzy_enum_accepts_unambiguous_prefix():
    class Model(HasTraits):
        value = FuzzyEnum(["alpha", "beta", "alphabet"], case_sensitive=True)

    obj = Model(value="bet")
    assert obj.value == "beta"
    with pytest.raises(TraitError):
        obj.value = "alp"

def test_object_name_and_dotted_object_name_validation():
    class Model(HasTraits):
        name = ObjectName()
        dotted = DottedObjectName()

    obj = Model(name="valid_name", dotted="pkg.module_name")
    assert obj.name == "valid_name"
    assert obj.dotted == "pkg.module_name"
    with pytest.raises(TraitError):
        obj.name = "not valid"

def test_tcp_address_validates_host_and_port():
    class Model(HasTraits):
        addr = TCPAddress()

    obj = Model(addr=("localhost", 8888))
    assert obj.addr == ("localhost", 8888)
    with pytest.raises(TraitError):
        obj.addr = ("localhost", 70000)

def test_instance_type_this_and_callable_traits():
    class Child:
        pass

    class Model(HasTraits):
        child = Instance(Child, args=())
        klass = Type(default_value=Child, klass=Child)
        callback = Callable()
        peer = This(allow_none=True)

    obj = Model(callback=lambda: "ok")
    assert isinstance(obj.child, Child)
    assert obj.klass is Child
    assert obj.callback() == "ok"
    obj.peer = obj
    assert obj.peer is obj
    with pytest.raises(TraitError):
        obj.callback = 1

def test_container_traits_validate_elements_and_lengths():
    class Model(HasTraits):
        numbers = List(Int(), minlen=1, maxlen=3)
        tags = Set(Unicode())
        pair = Tuple(Unicode(), Int())
        mapping = Dict(value_trait=Int(), key_trait=Unicode())

    obj = Model(numbers=[1, 2], tags={"a"}, pair=("x", 1), mapping={"a": 1})
    assert obj.numbers == [1, 2]
    assert obj.tags == {"a"}
    assert obj.pair == ("x", 1)
    assert obj.mapping == {"a": 1}
    with pytest.raises(TraitError):
        obj.numbers = []
    with pytest.raises(TraitError):
        obj.mapping = {1: 2}

def test_union_any_callable_and_regexp_traits():
    class Model(HasTraits):
        value = Union([Int(), Unicode()])
        anything = Any()
        callback = Callable()
        pattern = CRegExp()

    obj = Model(value="x", anything=None, callback=str, pattern="a+")
    assert obj.value == "x"
    obj.value = 4
    assert obj.value == 4
    assert obj.callback(3) == "3"
    assert obj.pattern.search("aa") is not None
    with pytest.raises(TraitError):
        obj.value = 1.5

def test_trait_from_string_and_list_from_string_list():
    assert Int().from_string("5") == 5
    assert Float().from_string("2.5") == 2.5
    assert Bool().from_string("true") is True
    assert List(Int()).from_string_list(["1", "2"]) == [1, 2]

def test_dict_from_string_list_parses_key_value_pairs():
    parsed = Dict(value_trait=Int()).from_string_list(["a=1", "b=2"])
    assert parsed == {"a": 1, "b": 2}
    with pytest.raises(Exception):
        Dict().from_string_list(["missing-separator"])

def test_trait_introspection_methods_reflect_metadata_and_values():
    class Model(HasTraits):
        name = Unicode("x").tag(config=True)
        count = Int(2)

    obj = Model()
    assert obj.has_trait("name") is True
    assert "name" in obj.trait_names(config=True)
    assert "name" in obj.traits(config=True)
    assert obj.trait_defaults("count") == 2
    assert obj.trait_values()["name"] == "x"

def test_add_traits_and_set_trait_use_validation_path():
    obj = HasTraits()
    obj.add_traits(value=Int())
    obj.set_trait("value", 8)
    assert obj.value == 8
    with pytest.raises(TraitError):
        obj.set_trait("value", "bad")

def test_class_trait_views_expose_declared_traits():
    class Model(HasTraits):
        name = Unicode()

    assert "name" in Model.class_trait_names()
    assert "name" in Model.class_traits()
    assert "name" in Model.class_own_traits()

def test_bunch_attribute_and_item_views_match():
    bunch = Bunch()
    bunch.answer = 42
    assert bunch["answer"] == 42
    bunch["answer"] = 43
    assert bunch.answer == 43

def test_import_item_imports_modules_and_attributes():
    assert import_item("json") is json
    assert import_item("json.dumps") is json.dumps
    with pytest.raises(ImportError):
        import_item("json.no_such_attribute")

def test_signature_has_traits_allows_trait_keywords():
    @signature_has_traits
    class Model(HasTraits):
        name = Unicode("x")

    obj = Model(name="custom")
    assert obj.name == "custom"

def test_error_semantics_invalid_trait_and_import_item():
    obj = IntegerModel(value=1)
    with pytest.raises(TraitError):
        obj.value = object()
    with pytest.raises(ImportError):
        import_item("not_a_real_traitlets_module.item")

def test_error_semantics_invalid_config_value_raises_trait_error():
    cfg = Config({"Worker": {"count": "not-int"}})
    with pytest.raises(TraitError):
        Worker(config=cfg)

def test_error_semantics_bad_cli_option_exits_or_raises():
    class CliApp(MiniApp):
        pass

    CliApp.clear_instance()
    app = CliApp.instance()
    with pytest.raises((SystemExit, ArgumentError, TraitError)):
        app.initialize(["--not-a-known-option=1"])
    CliApp.clear_instance()
