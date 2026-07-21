import json
import sys
import types
import warnings

import pytest

import jsonpickle
from jsonpickle.backend import JSONBackend
from jsonpickle.errors import ClassNotFoundError
from jsonpickle.handlers import BaseHandler


class SimpleThing:
    def __init__(self, name="thing"):
        self.name = name
        self.child = None


class SlotThing:
    __slots__ = ("alpha", "beta")

    def __init__(self, alpha, beta):
        self.alpha = alpha
        self.beta = beta


class StateThing:
    def __init__(self, value):
        self.value = value
        self.loaded = False

    def __getstate__(self):
        return {"value": self.value + 1}

    def __setstate__(self, state):
        self.value = state["value"]
        self.loaded = True


class StateOnlyList:
    def __init__(self):
        self.values = [1, 2]

    def __getstate__(self):
        return list(self.values)


class NewArgsThing(tuple):
    def __new__(cls, label, count=1):
        return tuple.__new__(cls, (label, count))

    def __getnewargs__(self):
        return (self[0], self[1])


class NewArgsExThing(tuple):
    def __new__(cls, label="original", count=1):
        return tuple.__new__(cls, (label, count))

    def __getnewargs__(self):
        raise RuntimeError("wrong construction path")

    def __getnewargs_ex__(self):
        return (("from-ex",), {"count": 7})


class InitArgsThing:
    def __init__(self, value):
        self.value = value

    def __getinitargs__(self):
        return (self.value,)


class ReduceListItems:
    def __init__(self):
        self.items = []

    def append(self, item):
        self.items.append(item)

    def __reduce__(self):
        return (ReduceListItems, (), {}, iter(["a", "b"]), None)


class ExcludedAttrs:
    _jsonpickle_exclude = {"secret"}

    def __init__(self):
        self.visible = "yes"
        self.secret = "no"


class PropertyThing:
    def __init__(self):
        self.items = [1, 2, 3]

    @property
    def size(self):
        return len(self.items)


class ReadOnlySafeData:
    __slots__ = ()


class ReadOnlySafeString(str, ReadOnlySafeData):
    __slots__ = ()


class LocalOld:
    def __init__(self, value):
        self.value = value


class LocalNew:
    def __init__(self):
        self.value = "unset"


class HandlerTarget:
    def __init__(self, name):
        self.name = name


class HandlerChild(HandlerTarget):
    pass


class HandlerGrandChild(HandlerChild):
    pass


class NameHandler(BaseHandler):
    def flatten(self, obj, data):
        data["name"] = obj.name.upper()
        return data

    def restore(self, data):
        return HandlerTarget(data["name"].lower())


class ContextHandler(BaseHandler):
    def flatten(self, obj, data, handler_context):
        data["name"] = f"{obj.name}-{handler_context['encode']}"
        return data

    def restore(self, data, handler_context):
        return HandlerTarget(f"{data['name']}-{handler_context['decode']}")


class BaseNameHandler(BaseHandler):
    def flatten(self, obj, data):
        data["name"] = "base"
        return data

    def restore(self, data):
        return HandlerChild(data["name"])


class ChildNameHandler(BaseHandler):
    def flatten(self, obj, data):
        data["name"] = "child"
        return data

    def restore(self, data):
        return HandlerGrandChild(data["name"])


def helper_function(value):
    return f"seen:{value}"


helper_function.__test__ = False


@pytest.fixture(autouse=True)
def _reset_jsonpickle_globals():
    yield
    for cls in [
        HandlerTarget,
        HandlerChild,
        HandlerGrandChild,
    ]:
        jsonpickle.unregister(cls)
    for backend in [
        "stage3_fake_backend",
        "stage3_fail_backend_one",
        "stage3_fail_backend_two",
        "stage3_no_components",
    ]:
        jsonpickle.remove_backend(backend)
        sys.modules.pop(backend, None)
    try:
        jsonpickle.set_preferred_backend("json")
    except AssertionError:
        jsonpickle.load_backend("json")
        jsonpickle.set_preferred_backend("json")
    jsonpickle.set_encoder_options("json", sort_keys=False)
    jsonpickle.set_decoder_options("json")


def test_import_surface_and_aliases_are_available():
    assert jsonpickle.dumps is jsonpickle.encode
    assert jsonpickle.loads is jsonpickle.decode
    assert callable(jsonpickle.Pickler)
    assert callable(jsonpickle.Unpickler)
    assert callable(jsonpickle.JSONBackend)
    assert callable(jsonpickle.register)
    assert callable(jsonpickle.unregister)
    assert callable(jsonpickle.set_preferred_backend)


def test_encode_decode_roundtrip_simple_object_state():
    obj = SimpleThing("root")
    obj.child = SimpleThing("leaf")
    clone = jsonpickle.decode(jsonpickle.encode(obj))
    assert type(clone) is SimpleThing
    assert clone.name == "root"
    assert clone.child.name == "leaf"


def test_dumps_loads_aliases_roundtrip_container():
    payload = jsonpickle.dumps({"a": [1, True, None], "b": "text"})
    assert jsonpickle.loads(payload) == {"a": [1, True, None], "b": "text"}


def test_unpicklable_false_returns_plain_json_data():
    obj = SimpleThing("plain")
    decoded = jsonpickle.decode(jsonpickle.encode(obj, unpicklable=False))
    assert decoded == {"name": "plain", "child": None}
    assert not isinstance(decoded, SimpleThing)


def test_primitives_lists_dicts_tuples_and_sets_roundtrip():
    value = {"items": [1, 2.5, "x", False, None], "tuple": (1, 2), "set": {3, 4}}
    clone = jsonpickle.decode(jsonpickle.encode(value))
    assert clone["items"] == [1, 2.5, "x", False, None]
    assert clone["tuple"] == (1, 2)
    assert clone["set"] == {3, 4}


def test_tuple_and_set_become_lists_when_not_unpicklable():
    decoded = jsonpickle.decode(jsonpickle.encode({"t": (1, 2), "s": {3}}, unpicklable=False))
    assert decoded["t"] == [1, 2]
    assert decoded["s"] == [3]


def test_pickler_flatten_and_unpickler_restore_match_encode_decode():
    obj = SimpleThing("flat")
    flattened = jsonpickle.Pickler().flatten(obj)
    restored = jsonpickle.Unpickler().restore(flattened)
    decoded = jsonpickle.decode(jsonpickle.encode(obj))
    assert restored.name == decoded.name == "flat"
    assert type(restored) is type(decoded) is SimpleThing


def test_unpickler_reset_false_preserves_reference_state():
    shared = SimpleThing("shared")
    flattened = jsonpickle.Pickler().flatten([shared, shared])
    unpickler = jsonpickle.Unpickler()
    restored = unpickler.restore(flattened, reset=True)
    again = unpickler.restore({"py/id": 1}, reset=False)
    assert restored[0] is restored[1]
    assert again is restored[0]


def test_repeated_object_reference_is_shared_after_decode():
    child = SimpleThing("shared")
    decoded = jsonpickle.decode(jsonpickle.encode([child, child]))
    assert decoded[0] is decoded[1]
    assert decoded[0].name == "shared"


def test_object_cycle_roundtrips_to_restored_cycle():
    root = SimpleThing("root")
    root.child = root
    clone = jsonpickle.decode(jsonpickle.encode(root))
    assert clone.child is clone


def test_list_cycle_roundtrips_to_restored_cycle():
    items = []
    items.append(items)
    clone = jsonpickle.decode(jsonpickle.encode(items))
    assert clone[0] is clone


def test_dictionary_identity_is_preserved_in_current_format():
    shared = {"value": 1}
    clone = jsonpickle.decode(jsonpickle.encode([shared, shared]))
    assert clone[0] is clone[1]
    clone[0]["value"] = 2
    assert clone[1]["value"] == 2


def test_make_refs_false_expands_repeated_objects():
    shared = SimpleThing("copy")
    clone = jsonpickle.decode(jsonpickle.encode([shared, shared], make_refs=False))
    assert clone[0].name == "copy"
    assert clone[1].name == "copy"
    assert clone[0] is not clone[1]


def test_unpicklable_false_breaks_cycles_with_none():
    root = SimpleThing("root")
    root.child = root
    decoded = jsonpickle.decode(jsonpickle.encode(root, unpicklable=False))
    assert decoded["name"] == "root"
    assert decoded["child"] is None


def test_make_refs_false_breaks_cycle_with_repr_string():
    root = SimpleThing("root")
    root.child = root
    decoded = jsonpickle.decode(jsonpickle.encode(root, make_refs=False))
    assert decoded.name == "root"
    assert isinstance(decoded.child, str)


def test_non_string_keys_default_to_strings():
    decoded = jsonpickle.decode(jsonpickle.encode({1000: "int", (1, 2): "tuple", None: "none"}))
    assert decoded == {"1000": "int", "(1, 2)": "tuple", "null": "none"}


def test_keys_true_roundtrips_tuple_int_and_none_keys():
    data = {(1, 2): "tuple", 7: "int", None: "none"}
    assert jsonpickle.decode(jsonpickle.encode(data, keys=True), keys=True) == data


def test_keys_true_roundtrips_object_keys_and_value_refs():
    key = SimpleThing("key")
    data = {key: [key, key]}
    clone = jsonpickle.decode(jsonpickle.encode(data, keys=True), keys=True)
    restored_key = next(iter(clone))
    assert restored_key.name == "key"
    assert clone[restored_key][0] is restored_key
    assert clone[restored_key][1] is restored_key


def test_keys_true_preserves_reserved_tag_string_keys_as_user_data():
    data = {"py/object": "value", "json://x": "escaped"}
    clone = jsonpickle.decode(jsonpickle.encode(data, keys=True), keys=True)
    assert clone == data


def test_keys_true_decoded_without_keys_returns_escaped_strings():
    payload = jsonpickle.encode({(1, 2): "tuple"}, keys=True)
    decoded = jsonpickle.decode(payload, keys=False)
    assert list(decoded.values()) == ["tuple"]
    assert next(iter(decoded)).startswith("json://")


def test_numeric_keys_preserves_numeric_keys_in_flattened_projection():
    flattened = jsonpickle.Pickler(numeric_keys=True).flatten({1: "one", 2.5: "two"})
    assert flattened[1] == "one"
    assert flattened[2.5] == "two"


def test_class_metadata_wire_tags_are_semantically_recognized():
    payload = jsonpickle.encode(SimpleThing("tagged"))
    data = json.loads(payload)
    assert data["py/object"].endswith(".SimpleThing")
    clone = jsonpickle.decode(payload)
    assert type(clone) is SimpleThing
    assert clone.name == "tagged"


def test_type_and_function_metadata_roundtrip():
    assert jsonpickle.decode(jsonpickle.encode(SimpleThing)) is SimpleThing
    restored_fn = jsonpickle.decode(jsonpickle.encode(helper_function))
    assert restored_fn("x") == "seen:x"


def test_classes_mapping_restores_renamed_class():
    payload = jsonpickle.encode(LocalOld("saved"))
    old_name = f"{LocalOld.__module__}.{LocalOld.__qualname__}"
    restored = jsonpickle.decode(payload, classes={old_name: LocalNew})
    assert type(restored) is LocalNew
    assert restored.value == "saved"


def test_classes_accept_single_sequence_and_dict_forms():
    class Hidden:
        def __init__(self, value):
            self.value = value

    payload = jsonpickle.encode(Hidden("ok"))
    assert jsonpickle.decode(payload, classes=Hidden).value == "ok"
    assert jsonpickle.decode(payload, classes=[Hidden]).value == "ok"
    assert jsonpickle.decode(payload, classes={f"{Hidden.__module__}.{Hidden.__qualname__}": Hidden}).value == "ok"


def test_missing_class_ignore_warn_error_and_callback_behaviors():
    payload = '{"py/object": "missing.module.Type", "value": 3}'
    assert jsonpickle.decode(payload, on_missing="ignore") == {"py/object": "missing.module.Type", "value": 3}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert jsonpickle.decode(payload, on_missing="warn")["value"] == 3
        assert caught
    seen = []
    assert jsonpickle.decode(payload, on_missing=lambda name: seen.append(name))["value"] == 3
    assert seen == ["missing.module.Type"]
    with pytest.raises(ClassNotFoundError):
        jsonpickle.decode(payload, on_missing="error")


def test_invalid_on_missing_value_warns_and_ignores():
    payload = '{"py/object": "missing.module.Type", "value": 4}'
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = jsonpickle.decode(payload, on_missing=object())
    assert result["value"] == 4
    assert caught


def test_v1_decode_uses_legacy_reference_numbering_for_dicts():
    payload = '[{"value": 1}, {"py/id": 1}]'
    current = jsonpickle.decode(payload, v1_decode=False)
    legacy = jsonpickle.decode(payload, v1_decode=True)
    assert current[0] is current[1]
    assert legacy == [{"value": 1}, None]


def test_getstate_and_setstate_are_used_for_object_state():
    restored = jsonpickle.decode(jsonpickle.encode(StateThing(4)))
    assert type(restored) is StateThing
    assert restored.value == 5
    assert restored.loaded is True


def test_getstate_without_setstate_returns_non_dict_state_when_no_newargs():
    restored = jsonpickle.decode(jsonpickle.encode(StateOnlyList()))
    assert restored == [1, 2]


def test_getnewargs_and_getnewargs_ex_restore_tuple_subclasses():
    assert jsonpickle.decode(jsonpickle.encode(NewArgsThing("a", 2))) == ("a", 2)
    assert jsonpickle.decode(jsonpickle.encode(NewArgsExThing("ignored", 3))) == ("from-ex", 7)


def test_getinitargs_roundtrip_visible_state():
    restored = jsonpickle.decode(jsonpickle.encode(InitArgsThing("init")))
    assert type(restored) is InitArgsThing
    assert restored.value == "init"


def test_reduce_listitems_restore_visible_mutation():
    restored = jsonpickle.decode(jsonpickle.encode(ReduceListItems()))
    assert type(restored) is ReduceListItems
    assert restored.items == ["a", "b"]


def test_excluded_attributes_are_not_synthesized_after_decode():
    restored = jsonpickle.decode(jsonpickle.encode(ExcludedAttrs()))
    assert restored.visible == "yes"
    assert not hasattr(restored, "secret")


def test_slots_instances_roundtrip_public_slot_values():
    restored = jsonpickle.decode(jsonpickle.encode(SlotThing("a", "b")))
    assert type(restored) is SlotThing
    assert (restored.alpha, restored.beta) == ("a", "b")


def test_bytes_default_and_base85_roundtrip():
    value = "PythoN!".encode("utf-8")
    assert jsonpickle.decode(jsonpickle.encode(value)) == value
    assert jsonpickle.decode(jsonpickle.encode(value, use_base85=True)) == value


def test_invalid_base64_and_base85_payloads_restore_empty_bytes():
    assert jsonpickle.Unpickler().restore({"py/b64": object()}) == b""
    assert jsonpickle.Unpickler().restore({"py/b85": object()}) == b""


def test_max_depth_uses_repr_for_deeper_values():
    decoded = jsonpickle.decode(jsonpickle.encode({"outer": [1, [2, 3]]}, max_depth=1))
    assert decoded == {"outer": "[1, [2, 3]]"}


def test_include_properties_adds_property_metadata_without_breaking_restore():
    payload = jsonpickle.encode(PropertyThing(), include_properties=True)
    data = json.loads(payload)
    assert data["py/property"]["size"] == 3
    restored = jsonpickle.decode(payload)
    assert restored.items == [1, 2, 3]
    assert restored.size == 3


def test_handle_readonly_roundtrips_string_subclass_with_empty_slots():
    value = ReadOnlySafeString("safe")
    restored = jsonpickle.decode(jsonpickle.encode(value, handle_readonly=True), handle_readonly=True)
    assert type(restored) is ReadOnlySafeString
    assert restored == "safe"


def test_fail_safe_replaces_failed_object_and_records_exception():
    class BadState:
        def __getstate__(self):
            raise ValueError("broken")

    seen = []
    payload = jsonpickle.encode([BadState(), "ok"], fail_safe=lambda exc: seen.append(type(exc).__name__) or "fallback")
    assert jsonpickle.decode(payload) == ["fallback", "ok"]
    assert seen == ["ValueError"]


def test_fail_safe_does_not_catch_keyboard_interrupt():
    class BadState:
        def __getstate__(self):
            raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        jsonpickle.encode(BadState(), fail_safe=lambda exc: "fallback")


def test_warn_true_emits_warning_for_unpicklable_file_object(tmp_path):
    path = tmp_path / "data.txt"
    path.write_text("x", encoding="utf-8")
    with path.open("r", encoding="utf-8") as handle:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            payload = jsonpickle.encode(handle, warn=True)
    assert jsonpickle.decode(payload) is None
    assert caught


def test_decode_invalid_json_raises_backend_exception():
    with pytest.raises(ValueError):
        jsonpickle.decode("{not-json")


def test_register_rejects_non_class_and_base_handler_methods_raise():
    with pytest.raises(TypeError):
        jsonpickle.register("not-a-class", NameHandler)
    handler = BaseHandler(None)
    with pytest.raises(NotImplementedError):
        handler.flatten(object(), {})
    with pytest.raises(NotImplementedError):
        handler.restore({})


def test_custom_handler_roundtrip_and_unregister_restores_default_behavior():
    jsonpickle.register(HandlerTarget, NameHandler)
    restored = jsonpickle.decode(jsonpickle.encode(HandlerTarget("ALPHA")))
    assert type(restored) is HandlerTarget
    assert restored.name == "alpha"
    jsonpickle.unregister(HandlerTarget)
    normal = jsonpickle.decode(jsonpickle.encode(HandlerTarget("ALPHA")))
    assert normal.name == "ALPHA"


def test_custom_handler_decorator_registration():
    @jsonpickle.register(HandlerTarget)
    class DecoratedHandler(NameHandler):
        pass

    restored = jsonpickle.decode(jsonpickle.encode(HandlerTarget("BRAVO")))
    assert restored.name == "bravo"


def test_base_handler_applies_to_subclasses_until_specific_handler_overrides():
    jsonpickle.register(HandlerChild, BaseNameHandler, base=True)
    assert jsonpickle.decode(jsonpickle.encode(HandlerGrandChild("x"))).name == "base"
    jsonpickle.register(HandlerGrandChild, ChildNameHandler)
    restored = jsonpickle.decode(jsonpickle.encode(HandlerGrandChild("x")))
    assert type(restored) is HandlerGrandChild
    assert restored.name == "child"


def test_handler_context_passes_only_to_accepting_handlers():
    jsonpickle.register(HandlerTarget, ContextHandler)
    payload = jsonpickle.encode(HandlerTarget("name"), handler_context={"encode": "e"})
    restored = jsonpickle.decode(payload, handler_context={"decode": "d"})
    assert restored.name == "name-e-d"


def test_handler_can_share_reference_graph_with_context_reset_false():
    class Pair:
        def __init__(self, left, right):
            self.left = left
            self.right = right

    class PairHandler(BaseHandler):
        def flatten(self, obj, data):
            data["left"] = self.context.flatten(obj.left, reset=False)
            data["right"] = self.context.flatten(obj.right, reset=False)
            return data

        def restore(self, data):
            pair = Pair(None, None)
            pair.left = self.context.restore(data["left"], reset=False)
            pair.right = self.context.restore(data["right"], reset=False)
            return pair

    jsonpickle.register(Pair, PairHandler)
    shared = SimpleThing("shared")
    restored = jsonpickle.decode(jsonpickle.encode(Pair(shared, shared)))
    assert restored.left is restored.right


def _install_fake_join_backend():
    module = types.ModuleType("stage3_fake_backend")
    module.dumps = lambda obj, **kwargs: "|".join(obj)
    module.loads = lambda text, **kwargs: text.split("|")
    module.DecodeError = ValueError
    sys.modules[module.__name__] = module
    return module.__name__


def test_load_backend_and_preferred_backend_use_custom_module():
    name = _install_fake_join_backend()
    assert jsonpickle.load_backend(name, loads_exc="DecodeError")
    jsonpickle.set_preferred_backend(name)
    assert jsonpickle.encode(["a", "b"]) == "a|b"
    assert jsonpickle.decode("a|b") == ["a", "b"]


def test_load_backend_returns_false_for_missing_components():
    module = types.ModuleType("stage3_no_components")
    module.dumps = lambda obj, **kwargs: "x"
    sys.modules[module.__name__] = module
    assert jsonpickle.load_backend(module.__name__, loads="missing", loads_exc=ValueError) is False


def test_remove_backend_allows_absent_backend_and_preferred_unloaded_raises():
    jsonpickle.remove_backend("stage3_fake_backend")
    with pytest.raises(AssertionError):
        jsonpickle.set_preferred_backend("stage3_fake_backend")


def test_backend_encoder_decoder_options_persist_for_later_calls():
    jsonpickle.set_encoder_options("json", sort_keys=True)
    payload = jsonpickle.encode({"b": 1, "a": 2})
    assert payload.index('"a"') < payload.index('"b"')
    jsonpickle.set_decoder_options("json", parse_int=lambda value: f"int:{value}")
    assert jsonpickle.decode('{"n": 12}') == {"n": "int:12"}


def test_per_call_indent_and_separators_format_but_decode_same_projection():
    compact = jsonpickle.encode({"a": 1, "b": 2}, separators=(",", ":"))
    pretty = jsonpickle.encode({"a": 1, "b": 2}, indent=2, separators=(",", ": "))
    assert "\n" in pretty
    assert jsonpickle.decode(compact) == jsonpickle.decode(pretty) == {"a": 1, "b": 2}


def _install_failing_backends():
    one = types.ModuleType("stage3_fail_backend_one")
    two = types.ModuleType("stage3_fail_backend_two")

    class ErrorOne(ValueError):
        pass

    class ErrorTwo(ValueError):
        pass

    one.ErrorOne = ErrorOne
    two.ErrorTwo = ErrorTwo
    one.dumps = lambda obj, **kwargs: (_ for _ in ()).throw(ErrorOne("first"))
    two.dumps = lambda obj, **kwargs: (_ for _ in ()).throw(ErrorTwo("second"))
    one.loads = lambda text, **kwargs: (_ for _ in ()).throw(ErrorOne("first"))
    two.loads = lambda text, **kwargs: (_ for _ in ()).throw(ErrorTwo("second"))
    sys.modules[one.__name__] = one
    sys.modules[two.__name__] = two
    return one, two, ErrorOne, ErrorTwo


def test_jsonbackend_fallthrough_raises_last_exception_when_enabled():
    one, two, _error_one, error_two = _install_failing_backends()
    backend = JSONBackend()
    backend.remove_backend("simplejson")
    backend.remove_backend("json")
    backend.remove_backend("ujson")
    assert backend.load_backend(one.__name__, loads_exc="ErrorOne")
    assert backend.load_backend(two.__name__, loads_exc="ErrorTwo")
    with pytest.raises(error_two):
        backend.encode({"x": 1})
    with pytest.raises(error_two):
        backend.decode("x")


def test_jsonbackend_no_fallthrough_raises_first_exception():
    one, two, error_one, _error_two = _install_failing_backends()
    backend = JSONBackend(fallthrough=False)
    backend.remove_backend("simplejson")
    backend.remove_backend("json")
    backend.remove_backend("ujson")
    assert backend.load_backend(one.__name__, loads_exc="ErrorOne")
    assert backend.load_backend(two.__name__, loads_exc="ErrorTwo")
    with pytest.raises(error_one):
        backend.encode({"x": 1})
    with pytest.raises(error_one):
        backend.decode("x")


def test_jsonbackend_with_no_loaded_backend_raises_assertion():
    backend = JSONBackend()
    backend.remove_backend("simplejson")
    backend.remove_backend("json")
    backend.remove_backend("ujson")
    with pytest.raises(AssertionError):
        backend.encode({"x": 1})


def test_workflow_object_graph_file_style_roundtrip(tmp_path):
    root = SimpleThing("root")
    leaf = SimpleThing("leaf")
    root.children = [leaf, leaf]
    leaf.parent = root
    path = tmp_path / "graph.json"
    path.write_text(jsonpickle.encode(root), encoding="utf-8")
    clone = jsonpickle.decode(path.read_text(encoding="utf-8"))
    assert clone.children[0] is clone.children[1]
    assert clone.children[0].parent is clone


def test_workflow_keys_true_for_non_string_keyed_object_graph():
    key = SimpleThing("key")
    data = {(1, 2): key, key: (1, 2)}
    restored = jsonpickle.decode(jsonpickle.encode(data, keys=True), keys=True)
    restored_object_key = [k for k in restored if isinstance(k, SimpleThing)][0]
    assert restored[(1, 2)].name == "key"
    assert restored[restored_object_key] == (1, 2)


def test_workflow_custom_handler_with_backend_formatting():
    jsonpickle.register(HandlerTarget, ContextHandler)
    payload = jsonpickle.encode(
        {"ticket": HandlerTarget("ride")},
        handler_context={"encode": "usd"},
        indent=2,
    )
    restored = jsonpickle.decode(payload, handler_context={"decode": "eur"})
    assert "\n" in payload
    assert restored["ticket"].name == "ride-usd-eur"


def test_semantic_json_member_order_is_not_required_for_decode():
    first = '{"py/object": "%s", "name": "order", "child": null}' % (f"{SimpleThing.__module__}.{SimpleThing.__qualname__}")
    second = '{"child": null, "name": "order", "py/object": "%s"}' % (f"{SimpleThing.__module__}.{SimpleThing.__qualname__}")
    assert jsonpickle.decode(first).name == "order"
    assert jsonpickle.decode(second).name == "order"


def test_semantic_json_whitespace_is_not_required_for_decode():
    compact = '{"a":[1,2],"b":{"c":3}}'
    spaced = '{\n  "a": [1, 2],\n  "b": {"c": 3}\n}'
    assert jsonpickle.decode(compact) == jsonpickle.decode(spaced)


def test_no_optional_extension_is_needed_for_core_roundtrip():
    obj = SimpleThing("stdlib-only")
    restored = jsonpickle.decode(jsonpickle.encode(obj))
    assert restored.name == "stdlib-only"
