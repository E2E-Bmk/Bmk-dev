"""Integration and cross-view checks for the documented PyYAML surface."""

from __future__ import annotations

import datetime
import importlib
import io
import math
import re

import pytest


def yaml_module():
    return importlib.import_module("yaml")


def assert_nodes_equivalent(left, right):
    yaml = yaml_module()
    assert type(left) is type(right)
    assert left.tag == right.tag
    if isinstance(left, yaml.ScalarNode):
        assert left.value == right.value
        return
    if isinstance(left, yaml.SequenceNode):
        assert len(left.value) == len(right.value)
        for left_child, right_child in zip(left.value, right.value):
            assert_nodes_equivalent(left_child, right_child)
        return
    assert isinstance(left, yaml.MappingNode)
    assert len(left.value) == len(right.value)
    for (left_key, left_value), (right_key, right_value) in zip(left.value, right.value):
        assert_nodes_equivalent(left_key, right_key)
        assert_nodes_equivalent(left_value, right_value)


def test_safe_round_trip_nested_configuration():
    yaml = yaml_module()
    data = {
        "name": "service",
        "enabled": True,
        "retries": 3,
        "ports": [80, 443],
        "metadata": {"owner": None, "ratio": 1.5},
    }
    rendered = yaml.safe_dump(data, sort_keys=False)
    assert yaml.safe_load(rendered) == data


def test_safe_round_trip_unicode_and_multiline_text():
    yaml = yaml_module()
    data = {"message": "你好, YAML", "lines": "first\nsecond\n"}
    rendered = yaml.safe_dump(data, allow_unicode=True)
    assert yaml.safe_load(rendered) == data


def test_safe_round_trip_dates_binary_and_set():
    yaml = yaml_module()
    data = {
        "date": datetime.date(2026, 7, 20),
        "instant": datetime.datetime(2026, 7, 20, 12, 0, 0),
        "payload": b"\x00payload\xff",
        "labels": {"one", "two"},
    }
    assert yaml.safe_load(yaml.safe_dump(data)) == data


def test_dump_all_and_safe_load_all_round_trip():
    yaml = yaml_module()
    documents = [{"a": 1}, [2, 3], None, "tail"]
    rendered = yaml.safe_dump_all(documents, explicit_start=True)
    assert list(yaml.safe_load_all(rendered)) == documents


def test_dump_all_to_binary_stream_round_trip():
    yaml = yaml_module()
    stream = io.BytesIO()
    result = yaml.safe_dump_all([{"a": 1}, {"b": 2}], stream=stream, encoding="utf-8")
    assert result is None
    assert list(yaml.safe_load_all(stream.getvalue())) == [{"a": 1}, {"b": 2}]


def test_compose_serialize_compose_preserves_node_tree():
    yaml = yaml_module()
    source = "root:\n  items: [1, two, true]\n  nested: {x: null}\n"
    first = yaml.compose(source, Loader=yaml.SafeLoader)
    rendered = yaml.serialize(first, Dumper=yaml.SafeDumper)
    second = yaml.compose(rendered, Loader=yaml.SafeLoader)
    assert_nodes_equivalent(first, second)


def test_compose_all_serialize_all_preserves_document_count():
    yaml = yaml_module()
    nodes = list(yaml.compose_all("---\na: 1\n---\n- two\n- three\n", Loader=yaml.SafeLoader))
    rendered = yaml.serialize_all(nodes, Dumper=yaml.SafeDumper, explicit_start=True)
    rebuilt = list(yaml.compose_all(rendered, Loader=yaml.SafeLoader))
    assert len(rebuilt) == 2
    for left, right in zip(nodes, rebuilt):
        assert_nodes_equivalent(left, right)


def test_parse_emit_parse_preserves_event_kinds_and_values():
    yaml = yaml_module()
    source = "name: service\nitems: [one, two]\n"
    first = list(yaml.parse(source, Loader=yaml.SafeLoader))
    rendered = yaml.emit(first, Dumper=yaml.SafeDumper)
    second = list(yaml.parse(rendered, Loader=yaml.SafeLoader))
    assert [type(event) for event in first] == [type(event) for event in second]
    first_values = [event.value for event in first if isinstance(event, yaml.ScalarEvent)]
    second_values = [event.value for event in second if isinstance(event, yaml.ScalarEvent)]
    assert first_values == second_values


def test_emit_to_stream_returns_none_and_writes_yaml():
    yaml = yaml_module()
    events = list(yaml.parse("items: [1, 2]\n"))
    stream = io.StringIO()
    result = yaml.emit(events, stream=stream)
    assert result is None
    assert yaml.safe_load(stream.getvalue()) == {"items": [1, 2]}


def test_custom_constructor_on_private_loader():
    yaml = yaml_module()

    class DiceLoader(yaml.SafeLoader):
        pass

    def construct_dice(loader, node):
        return ("dice", loader.construct_scalar(node))

    yaml.add_constructor("!dice", construct_dice, Loader=DiceLoader)
    assert yaml.load("roll: !dice 2d6\n", Loader=DiceLoader) == {"roll": ("dice", "2d6")}
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load("roll: !dice 2d6\n")


def test_custom_multi_constructor_receives_tag_suffix():
    yaml = yaml_module()

    class EnvLoader(yaml.SafeLoader):
        pass

    def construct_env(loader, suffix, node):
        return (suffix, loader.construct_scalar(node))

    yaml.add_multi_constructor("!env:", construct_env, Loader=EnvLoader)
    assert yaml.load("!env:prod database", Loader=EnvLoader) == ("prod", "database")


def test_custom_fallback_multi_constructor_handles_unknown_tag():
    yaml = yaml_module()

    class FallbackLoader(yaml.SafeLoader):
        pass

    def construct_unknown(loader, suffix, node):
        return {"tag": suffix, "value": loader.construct_scalar(node)}

    yaml.add_multi_constructor(None, construct_unknown, Loader=FallbackLoader)
    value = yaml.load("!custom payload", Loader=FallbackLoader)
    assert value == {"tag": "!custom", "value": "payload"}


def test_custom_representer_round_trip():
    yaml = yaml_module()

    class Dice:
        def __init__(self, value):
            self.value = value

        def __eq__(self, other):
            return isinstance(other, Dice) and self.value == other.value

    class DiceLoader(yaml.SafeLoader):
        pass

    class DiceDumper(yaml.SafeDumper):
        pass

    yaml.add_constructor("!dice", lambda loader, node: Dice(loader.construct_scalar(node)), Loader=DiceLoader)
    yaml.add_representer(Dice, lambda dumper, value: dumper.represent_scalar("!dice", value.value), Dumper=DiceDumper)
    rendered = yaml.dump({"roll": Dice("2d6")}, Dumper=DiceDumper)
    assert "!dice" in rendered
    assert yaml.load(rendered, Loader=DiceLoader) == {"roll": Dice("2d6")}


def test_custom_multi_representer_handles_subclass():
    yaml = yaml_module()

    class Label:
        def __init__(self, text):
            self.text = text

    class SpecialLabel(Label):
        pass

    class LabelDumper(yaml.SafeDumper):
        pass

    yaml.add_multi_representer(
        Label,
        lambda dumper, value: dumper.represent_scalar("tag:yaml.org,2002:str", value.text),
        Dumper=LabelDumper,
    )
    rendered = yaml.dump(SpecialLabel("visible"), Dumper=LabelDumper)
    assert yaml.safe_load(rendered) == "visible"


def test_custom_implicit_resolver_changes_compose_and_load():
    yaml = yaml_module()

    class DiceLoader(yaml.SafeLoader):
        pass

    yaml.add_implicit_resolver("!dice", re.compile(r"^\d+d\d+$"), list("0123456789"), Loader=DiceLoader)
    yaml.add_constructor("!dice", lambda loader, node: ("dice", loader.construct_scalar(node)), Loader=DiceLoader)
    node = yaml.compose("2d6", Loader=DiceLoader)
    assert node.tag == "!dice"
    assert yaml.load("2d6", Loader=DiceLoader) == ("dice", "2d6")


def test_custom_wildcard_implicit_resolver():
    yaml = yaml_module()

    class WildLoader(yaml.SafeLoader):
        pass

    yaml.add_implicit_resolver("!caps", re.compile(r"^[A-Z]{3}$"), None, Loader=WildLoader)
    yaml.add_constructor("!caps", lambda loader, node: loader.construct_scalar(node).lower(), Loader=WildLoader)
    assert yaml.load("ABC", Loader=WildLoader) == "abc"
    assert yaml.compose("ABC", Loader=WildLoader).tag == "!caps"


def test_custom_path_resolver_tags_selected_mapping_value():
    yaml = yaml_module()

    class PathLoader(yaml.SafeLoader):
        pass

    yaml.add_path_resolver("!port", ["service", "port"], str, Loader=PathLoader)
    yaml.add_constructor("!port", lambda loader, node: int(loader.construct_scalar(node)), Loader=PathLoader)
    value = yaml.load("service:\n  port: '8080'\n  name: api\n", Loader=PathLoader)
    assert value == {"service": {"port": 8080, "name": "api"}}


def test_invalid_path_resolver_declaration_raises_resolver_error():
    yaml = yaml_module()
    resolver = importlib.import_module("yaml.resolver")

    class PathLoader(yaml.SafeLoader):
        pass

    with pytest.raises(resolver.ResolverError):
        yaml.add_path_resolver("!bad", [(object(), object())], Loader=PathLoader)


def test_yaml_object_default_round_trip():
    yaml = yaml_module()

    class Person(yaml.YAMLObject):
        yaml_tag = "!person"
        yaml_loader = yaml.SafeLoader
        yaml_dumper = yaml.SafeDumper

        def __init__(self, name=None):
            self.name = name

        def __eq__(self, other):
            return isinstance(other, Person) and self.name == other.name

    rendered = yaml.dump(Person("Ada"), Dumper=yaml.SafeDumper)
    assert "!person" in rendered
    assert yaml.load(rendered, Loader=yaml.SafeLoader) == Person("Ada")


def test_yaml_object_custom_hooks_receive_loader_and_dumper():
    yaml = yaml_module()
    calls = []

    class Point(yaml.YAMLObject):
        yaml_tag = "!point"
        yaml_loader = yaml.SafeLoader
        yaml_dumper = yaml.SafeDumper

        def __init__(self, x, y):
            self.x, self.y = x, y

        @classmethod
        def from_yaml(cls, loader, node):
            calls.append(type(loader).__name__)
            values = loader.construct_sequence(node, deep=True)
            return cls(*values)

        @classmethod
        def to_yaml(cls, dumper, value):
            calls.append(type(dumper).__name__)
            return dumper.represent_sequence(cls.yaml_tag, [value.x, value.y])

    rendered = yaml.dump(Point(2, 3), Dumper=yaml.SafeDumper)
    loaded = yaml.load(rendered, Loader=yaml.SafeLoader)
    assert (loaded.x, loaded.y) == (2, 3)
    assert any("Dumper" in name for name in calls) and any("Loader" in name for name in calls)


def test_loader_construct_helpers_validate_node_kinds():
    yaml = yaml_module()
    errors = []

    class ProbeLoader(yaml.SafeLoader):
        pass

    def construct_probe(loader, node):
        for method in (loader.construct_sequence, loader.construct_mapping, loader.construct_pairs):
            try:
                method(node)
            except yaml.YAMLError as exc:
                errors.append(type(exc).__name__)
        return loader.construct_scalar(node)

    yaml.add_constructor("!probe", construct_probe, Loader=ProbeLoader)
    assert yaml.load("!probe scalar", Loader=ProbeLoader) == "scalar"
    assert len(errors) == 3


def test_dumper_represent_helpers_create_public_nodes():
    yaml = yaml_module()

    class Payload:
        pass

    class PayloadDumper(yaml.SafeDumper):
        pass

    def represent_payload(dumper, value):
        scalar = dumper.represent_scalar("tag:yaml.org,2002:str", "scalar")
        sequence = dumper.represent_sequence("tag:yaml.org,2002:seq", [1, 2])
        mapping = dumper.represent_mapping("tag:yaml.org,2002:map", {"k": "v"})
        assert isinstance(scalar, yaml.ScalarNode)
        assert isinstance(sequence, yaml.SequenceNode)
        assert isinstance(mapping, yaml.MappingNode)
        return mapping

    yaml.add_representer(Payload, represent_payload, Dumper=PayloadDumper)
    assert yaml.safe_load(yaml.dump(Payload(), Dumper=PayloadDumper)) == {"k": "v"}


def test_mark_snippet_places_caret_under_pointer():
    yaml = yaml_module()
    mark = yaml.Mark("config.yaml", 7, 0, 7, "key: value\0", 7)
    snippet = mark.get_snippet()
    assert "key: value" in snippet
    assert "^" in snippet
    assert snippet.splitlines()[-1].index("^") >= 7


def test_mark_without_buffer_has_no_snippet():
    yaml = yaml_module()
    mark = yaml.Mark("input", 0, 2, 4, None, None)
    assert mark.get_snippet() is None


def test_mark_string_uses_one_based_line_and_column():
    yaml = yaml_module()
    mark = yaml.Mark("config.yaml", 0, 2, 4, None, None)
    text = str(mark)
    assert "config.yaml" in text and "line 3" in text and "column 5" in text


def test_marked_yaml_error_string_includes_context_problem_and_note():
    yaml = yaml_module()
    first = yaml.Mark("input", 0, 0, 0, "bad\0", 0)
    second = yaml.Mark("input", 1, 0, 1, "bad\0", 1)
    error = yaml.MarkedYAMLError("while parsing", first, "unexpected token", second, "check syntax")
    text = str(error)
    assert "while parsing" in text
    assert "unexpected token" in text
    assert "check syntax" in text


def test_malformed_flow_sequence_raises_yaml_error():
    yaml = yaml_module()
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load("[one, two")


def test_malformed_flow_mapping_raises_yaml_error():
    yaml = yaml_module()
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load("{name: value")


def test_invalid_escape_raises_yaml_error():
    yaml = yaml_module()
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load('"bad\\qescape"')


def test_duplicate_yaml_directive_raises_yaml_error():
    yaml = yaml_module()
    text = "%YAML 1.1\n%YAML 1.1\n---\nvalue\n"
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load(text)


def test_invalid_binary_value_raises_yaml_error():
    yaml = yaml_module()
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load("!!binary not-base64***")


def test_unhashable_mapping_key_raises_yaml_error():
    yaml = yaml_module()
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load("? [one, two]\n: value\n")


def test_unsupported_tag_raises_yaml_error():
    yaml = yaml_module()
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load("!unknown value")


def test_single_document_load_rejects_multiple_documents():
    yaml = yaml_module()
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load("---\none\n---\ntwo\n")


def test_invalid_utf8_byte_stream_raises_yaml_error():
    yaml = yaml_module()
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load(b"\x80\x81\x82")


def test_safe_loader_rejects_python_object_apply():
    yaml = yaml_module()
    source = "!!python/object/apply:builtins.str [unsafe]"
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load(source)


def test_full_loader_rejects_arbitrary_object_apply():
    yaml = yaml_module()
    source = "!!python/object/apply:builtins.str [unsafe]"
    with pytest.raises(yaml.YAMLError):
        yaml.full_load(source)


def test_unsafe_loader_supports_python_object_apply():
    assert yaml_module().unsafe_load("!!python/object/apply:builtins.str [value]") == "value"


def test_recursive_alias_round_trip_preserves_cycle():
    yaml = yaml_module()
    value = yaml.safe_load("&root [*root]")
    assert value[0] is value
    rendered = yaml.safe_dump(value)
    rebuilt = yaml.safe_load(rendered)
    assert rebuilt[0] is rebuilt


def test_mapping_with_incomparable_keys_dumps_without_sort_failure():
    yaml = yaml_module()
    data = {1: "number", "two": "string"}
    rendered = yaml.safe_dump(data, sort_keys=True)
    assert yaml.safe_load(rendered) == data


def test_safe_configuration_workflow_preserves_public_values():
    yaml = yaml_module()
    text = "name: service\nenabled: true\nretries: 3\nstarted: 2026-07-20\n"
    data = yaml.safe_load(text)
    assert data["enabled"] is True
    assert data["started"].isoformat() == "2026-07-20"
    assert yaml.safe_load(yaml.safe_dump(data, sort_keys=False)) == data


def test_custom_tag_workflow_round_trip():
    yaml = yaml_module()

    class DiceLoader(yaml.SafeLoader):
        pass

    class DiceDumper(yaml.SafeDumper):
        pass

    yaml.add_implicit_resolver("!dice", re.compile(r"^\d+d\d+$"), list("0123456789"), Loader=DiceLoader, Dumper=DiceDumper)
    yaml.add_constructor("!dice", lambda loader, node: ("dice", loader.construct_scalar(node)), Loader=DiceLoader)
    yaml.add_representer(tuple, lambda dumper, value: dumper.represent_scalar("!dice", value[1]), Dumper=DiceDumper)
    loaded = yaml.load("roll: 2d6\n", Loader=DiceLoader)
    assert loaded == {"roll": ("dice", "2d6")}
    rendered = yaml.dump(loaded, Dumper=DiceDumper)
    assert yaml.load(rendered, Loader=DiceLoader) == loaded


def test_intermediate_representation_workflow():
    yaml = yaml_module()
    node = yaml.compose("items: [1, 2]\n")
    assert isinstance(node, yaml.MappingNode)
    events = list(yaml.parse("items: [1, 2]\n"))
    rendered = yaml.emit(events)
    assert yaml.safe_load(rendered) == {"items": [1, 2]}


def test_load_dump_compose_views_agree_on_scalar_types():
    yaml = yaml_module()
    source = "null_value: null\nbool_value: true\nint_value: 3\nfloat_value: 1.5\n"
    loaded = yaml.safe_load(source)
    rendered = yaml.safe_dump(loaded, sort_keys=False)
    node = yaml.compose(rendered, Loader=yaml.SafeLoader)
    tags = {key.value: value.tag for key, value in node.value}
    assert tags == {
        "null_value": "tag:yaml.org,2002:null",
        "bool_value": "tag:yaml.org,2002:bool",
        "int_value": "tag:yaml.org,2002:int",
        "float_value": "tag:yaml.org,2002:float",
    }


def test_warnings_compatibility_function_returns_empty_mapping():
    yaml = yaml_module()
    assert yaml.warnings() == {}
