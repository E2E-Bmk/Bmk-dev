"""Atomic public-behavior checks for the documented PyYAML surface."""

from __future__ import annotations

import datetime
import importlib
import io
import math

import pytest


def yaml_module():
    return importlib.import_module("yaml")


def test_package_exposes_numeric_version():
    yaml = yaml_module()
    assert isinstance(yaml.__version__, str)
    assert yaml.__version__[0].isdigit()


def test_libyaml_capability_flag_is_boolean():
    yaml = yaml_module()
    assert isinstance(yaml.__with_libyaml__, bool)


def test_public_loader_classes_are_types():
    yaml = yaml_module()
    for name in ("BaseLoader", "SafeLoader", "FullLoader", "Loader", "UnsafeLoader"):
        assert isinstance(getattr(yaml, name), type)


def test_public_dumper_classes_are_types():
    yaml = yaml_module()
    for name in ("BaseDumper", "SafeDumper", "Dumper"):
        assert isinstance(getattr(yaml, name), type)


def test_public_node_classes_are_types():
    yaml = yaml_module()
    for name in ("ScalarNode", "SequenceNode", "MappingNode"):
        assert isinstance(getattr(yaml, name), type)


def test_yaml_error_is_exception_type():
    yaml = yaml_module()
    assert issubclass(yaml.YAMLError, Exception)
    assert issubclass(yaml.MarkedYAMLError, yaml.YAMLError)


def test_specialized_errors_share_yaml_error_base():
    yaml = yaml_module()
    errors = (
        ("constructor", "ConstructorError"),
        ("representer", "RepresenterError"),
        ("resolver", "ResolverError"),
        ("reader", "ReaderError"),
        ("scanner", "ScannerError"),
        ("parser", "ParserError"),
        ("composer", "ComposerError"),
        ("emitter", "EmitterError"),
        ("serializer", "SerializerError"),
    )
    for module_name, class_name in errors:
        module = importlib.import_module(f"yaml.{module_name}")
        assert issubclass(getattr(module, class_name), yaml.YAMLError)


def test_safe_load_empty_string_returns_none():
    assert yaml_module().safe_load("") is None


def test_safe_load_comment_only_returns_none():
    assert yaml_module().safe_load("# only a comment\n") is None


def test_safe_load_null_spellings():
    yaml = yaml_module()
    assert [yaml.safe_load(value) for value in ("~", "null", "Null", "NULL")] == [None] * 4


def test_safe_load_boolean_true_spellings():
    yaml = yaml_module()
    assert [yaml.safe_load(value) for value in ("true", "True", "TRUE")] == [True] * 3


def test_safe_load_boolean_false_spellings():
    yaml = yaml_module()
    assert [yaml.safe_load(value) for value in ("false", "False", "FALSE")] == [False] * 3


def test_safe_load_decimal_integer():
    value = yaml_module().safe_load("12345")
    assert value == 12345 and type(value) is int


def test_safe_load_negative_integer():
    assert yaml_module().safe_load("-42") == -42


def test_safe_load_binary_integer():
    assert yaml_module().safe_load("0b101101") == 45


def test_safe_load_octal_integer():
    assert yaml_module().safe_load("052") == 42


def test_safe_load_hexadecimal_integer():
    assert yaml_module().safe_load("0x2A") == 42


def test_safe_load_decimal_float():
    value = yaml_module().safe_load("3.125")
    assert value == 3.125 and type(value) is float


def test_safe_load_exponent_float():
    assert yaml_module().safe_load("1.25e+2") == 125.0


def test_safe_load_positive_infinity():
    value = yaml_module().safe_load(".inf")
    assert math.isinf(value) and value > 0


def test_safe_load_negative_infinity():
    value = yaml_module().safe_load("-.Inf")
    assert math.isinf(value) and value < 0


def test_safe_load_nan():
    assert math.isnan(yaml_module().safe_load(".NaN"))


def test_safe_load_date():
    value = yaml_module().safe_load("2026-07-20")
    assert value == datetime.date(2026, 7, 20) and type(value) is datetime.date


def test_safe_load_datetime():
    value = yaml_module().safe_load("2026-07-20T12:34:56Z")
    assert isinstance(value, datetime.datetime)
    assert value.utcoffset() == datetime.timedelta(0)


def test_safe_load_plain_string():
    assert yaml_module().safe_load("hello world") == "hello world"


def test_safe_load_single_quoted_string():
    assert yaml_module().safe_load("'it''s yaml'") == "it's yaml"


def test_safe_load_double_quoted_escapes():
    assert yaml_module().safe_load('"line\\nvalue"') == "line\nvalue"


def test_safe_load_literal_block_scalar():
    assert yaml_module().safe_load("|\n  alpha\n  beta\n") == "alpha\nbeta\n"


def test_safe_load_folded_block_scalar():
    assert yaml_module().safe_load(">\n  alpha\n  beta\n") == "alpha beta\n"


def test_safe_load_block_sequence():
    assert yaml_module().safe_load("- one\n- two\n- three\n") == ["one", "two", "three"]


def test_safe_load_flow_sequence():
    assert yaml_module().safe_load("[1, true, null, text]") == [1, True, None, "text"]


def test_safe_load_block_mapping():
    assert yaml_module().safe_load("name: service\nenabled: true\n") == {"name": "service", "enabled": True}


def test_safe_load_flow_mapping():
    assert yaml_module().safe_load("{name: service, retries: 3}") == {"name": "service", "retries": 3}


def test_safe_load_nested_collections():
    text = "service:\n  ports: [80, 443]\n  flags:\n    enabled: true\n"
    assert yaml_module().safe_load(text) == {
        "service": {"ports": [80, 443], "flags": {"enabled": True}}
    }


def test_safe_load_binary_value():
    assert yaml_module().safe_load("!!binary SGVsbG8=") == b"Hello"


def test_safe_load_set_value():
    assert yaml_module().safe_load("!!set\n? red\n? blue\n") == {"red", "blue"}


def test_safe_load_ordered_map_value():
    value = yaml_module().safe_load("!!omap\n- first: 1\n- second: 2\n")
    assert value == [("first", 1), ("second", 2)]


def test_safe_load_pairs_value():
    value = yaml_module().safe_load("!!pairs\n- first: 1\n- second: 2\n")
    assert value == [("first", 1), ("second", 2)]


def test_safe_load_merge_key():
    text = "defaults: &defaults\n  enabled: true\n  retries: 2\nservice:\n  <<: *defaults\n  retries: 5\n"
    value = yaml_module().safe_load(text)
    assert value["service"] == {"enabled": True, "retries": 5}


def test_safe_load_alias_preserves_identity():
    value = yaml_module().safe_load("base: &base {x: 1}\ncopy: *base\n")
    assert value["base"] is value["copy"]


def test_base_loader_keeps_scalar_values_as_strings():
    yaml = yaml_module()
    value = yaml.load("count: 3\nenabled: true\n", Loader=yaml.BaseLoader)
    assert value == {"count": "3", "enabled": "true"}


def test_full_load_python_tuple():
    assert yaml_module().full_load("!!python/tuple [1, two]") == (1, "two")


def test_full_load_python_name():
    assert yaml_module().full_load("!!python/name:builtins.len ''") is len


def test_safe_load_rejects_python_tuple_tag():
    yaml = yaml_module()
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load("!!python/tuple [1, 2]")


def test_load_requires_explicit_loader():
    yaml = yaml_module()
    with pytest.raises(TypeError):
        yaml.load("value")


def test_load_all_returns_iterator_of_documents():
    yaml = yaml_module()
    docs = yaml.load_all("---\na: 1\n---\nb: 2\n", Loader=yaml.SafeLoader)
    assert iter(docs) is docs
    assert list(docs) == [{"a": 1}, {"b": 2}]


def test_safe_load_all_preserves_empty_document():
    assert list(yaml_module().safe_load_all("---\n---\nvalue\n")) == [None, "value"]


def test_safe_dump_round_trips_simple_mapping():
    yaml = yaml_module()
    data = {"name": "service", "enabled": True, "retries": 3}
    assert yaml.safe_load(yaml.safe_dump(data)) == data


def test_safe_dump_sorts_keys_by_default():
    rendered = yaml_module().safe_dump({"z": 1, "a": 2})
    assert rendered.index("a:") < rendered.index("z:")


def test_safe_dump_can_preserve_mapping_order():
    rendered = yaml_module().safe_dump({"z": 1, "a": 2}, sort_keys=False)
    assert rendered.index("z:") < rendered.index("a:")


def test_safe_dump_block_style_option():
    rendered = yaml_module().safe_dump({"items": [1, 2]}, default_flow_style=False)
    assert "items:" in rendered and "- 1" in rendered and "- 2" in rendered


def test_safe_dump_flow_style_option():
    rendered = yaml_module().safe_dump({"items": [1, 2]}, default_flow_style=True)
    assert rendered.lstrip().startswith("{") and "[1, 2]" in rendered


def test_safe_dump_explicit_start_marker():
    assert yaml_module().safe_dump({"a": 1}, explicit_start=True).startswith("---")


def test_safe_dump_explicit_end_marker():
    assert yaml_module().safe_dump({"a": 1}, explicit_end=True).rstrip().endswith("...")


def test_safe_dump_allow_unicode_emits_text_directly():
    rendered = yaml_module().safe_dump({"message": "你好"}, allow_unicode=True)
    assert "你好" in rendered


def test_safe_dump_encoding_returns_bytes():
    rendered = yaml_module().safe_dump({"message": "hello"}, encoding="utf-8")
    assert isinstance(rendered, bytes)
    assert b"message" in rendered


def test_safe_dump_to_text_stream_returns_none():
    yaml = yaml_module()
    stream = io.StringIO()
    result = yaml.safe_dump({"a": 1}, stream=stream)
    assert result is None
    assert yaml.safe_load(stream.getvalue()) == {"a": 1}


def test_safe_dump_bytes_round_trip():
    yaml = yaml_module()
    data = b"\x00\x01binary\xff"
    assert yaml.safe_load(yaml.safe_dump(data)) == data


def test_safe_dump_date_round_trip():
    yaml = yaml_module()
    data = datetime.date(2026, 7, 20)
    assert yaml.safe_load(yaml.safe_dump(data)) == data


def test_safe_dump_datetime_round_trip():
    yaml = yaml_module()
    data = datetime.datetime(2026, 7, 20, 12, 34, 56)
    assert yaml.safe_load(yaml.safe_dump(data)) == data


def test_safe_dump_set_round_trip():
    yaml = yaml_module()
    data = {"alpha", "beta"}
    assert yaml.safe_load(yaml.safe_dump(data)) == data


def test_safe_dump_unsupported_object_raises_representer_error():
    yaml = yaml_module()

    class Unsupported:
        pass

    representer = importlib.import_module("yaml.representer")
    with pytest.raises(representer.RepresenterError):
        yaml.safe_dump(Unsupported())


def test_scan_returns_stream_boundary_tokens():
    yaml = yaml_module()
    tokens = list(yaml.scan("name: value\n"))
    assert isinstance(tokens[0], yaml.StreamStartToken)
    assert isinstance(tokens[-1], yaml.StreamEndToken)


def test_scan_mapping_exposes_key_value_and_scalar_tokens():
    yaml = yaml_module()
    tokens = list(yaml.scan("name: value\n"))
    assert any(isinstance(token, yaml.KeyToken) for token in tokens)
    assert any(isinstance(token, yaml.ValueToken) for token in tokens)
    assert [token.value for token in tokens if isinstance(token, yaml.ScalarToken)] == ["name", "value"]


def test_scan_tokens_expose_source_marks():
    tokens = list(yaml_module().scan("- item\n"))
    assert all(hasattr(token, "start_mark") and hasattr(token, "end_mark") for token in tokens)


def test_parse_returns_stream_boundary_events():
    yaml = yaml_module()
    events = list(yaml.parse("name: value\n"))
    assert isinstance(events[0], yaml.StreamStartEvent)
    assert isinstance(events[-1], yaml.StreamEndEvent)


def test_parse_mapping_event_sequence():
    yaml = yaml_module()
    events = list(yaml.parse("name: value\n"))
    classes = [type(event) for event in events]
    assert yaml.MappingStartEvent in classes
    assert yaml.MappingEndEvent in classes
    assert [event.value for event in events if isinstance(event, yaml.ScalarEvent)] == ["name", "value"]


def test_parse_scalar_event_exposes_public_attributes():
    yaml = yaml_module()
    event = next(event for event in yaml.parse("value") if isinstance(event, yaml.ScalarEvent))
    for name in ("anchor", "tag", "implicit", "value", "style"):
        assert hasattr(event, name)


def test_compose_mapping_returns_mapping_node():
    yaml = yaml_module()
    node = yaml.compose("name: value\n")
    assert isinstance(node, yaml.MappingNode)
    key_node, value_node = node.value[0]
    assert key_node.value == "name" and value_node.value == "value"


def test_compose_sequence_returns_sequence_node():
    yaml = yaml_module()
    node = yaml.compose("[1, 2, 3]")
    assert isinstance(node, yaml.SequenceNode)
    assert [child.value for child in node.value] == ["1", "2", "3"]


def test_compose_scalar_exposes_tag_and_marks():
    yaml = yaml_module()
    node = yaml.compose("42")
    assert isinstance(node, yaml.ScalarNode)
    assert node.tag == "tag:yaml.org,2002:int" and node.value == "42"
    assert node.start_mark is not None and node.end_mark is not None


def test_compose_empty_stream_returns_none():
    assert yaml_module().compose("") is None


def test_compose_all_returns_each_document_node():
    yaml = yaml_module()
    nodes = list(yaml.compose_all("---\none\n---\ntwo\n"))
    assert [node.value for node in nodes] == ["one", "two"]
