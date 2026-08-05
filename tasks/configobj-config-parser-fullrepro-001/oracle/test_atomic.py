from __future__ import annotations

from io import StringIO

import pytest

from conftest import make_config_with_spec, validation_spec


def test_constructor_parses_scalar_and_list_values():
    from configobj import ConfigObj

    config = ConfigObj(["name = Ada", "ports = 80, 443, 8080"])
    assert config["name"] == "Ada"
    assert config["ports"] == ["80", "443", "8080"]


def test_constructor_builds_nested_sections():
    from configobj import ConfigObj

    config = ConfigObj(["[outer]", "value = x", "[[inner]]", "flag = yes"])
    assert config["outer"]["value"] == "x"
    assert config["outer"]["inner"]["flag"] == "yes"
    assert config["outer"].depth == 1
    assert config["outer"]["inner"].depth == 2


def test_constructor_accepts_mapping_and_preserves_member_order():
    from configobj import ConfigObj

    config = ConfigObj({"first": "1", "section": {"second": "2"}, "third": "3"})
    assert config.keys() == ["first", "third", "section"]
    assert config["section"].keys() == ["second"]


def test_constructor_accepts_file_like_text():
    from configobj import ConfigObj

    config = ConfigObj(StringIO("alpha = one\n[child]\nbeta = two\n"))
    assert config.dict() == {"alpha": "one", "child": {"beta": "two"}}


def test_comments_and_order_are_recorded(parsed_config):
    assert parsed_config.keys() == ["name", "ports", "service"]
    assert parsed_config.initial_comment == ["# application settings"]
    assert parsed_config["service"].keys() == ["enabled", "limits"]
    assert parsed_config["service"]["limits"].keys() == ["low", "high"]


def test_inline_and_member_comments_are_preserved(local_config_lines):
    from configobj import ConfigObj

    config = ConfigObj(local_config_lines)
    assert config.inline_comments["server"] == "# server settings"
    assert config["server"].comments["host"] == ["# host comment"]
    assert config["server"].inline_comments["host"] == "# inline host"


def test_write_returns_ordered_lines_and_keeps_semantics(local_config_lines):
    from configobj import ConfigObj

    config = ConfigObj(local_config_lines)
    lines = config.write()
    reread = ConfigObj(lines)
    assert reread.dict() == config.dict()
    assert reread.keys() == config.keys()


def test_section_dict_returns_detached_plain_mapping(parsed_config):
    plain = parsed_config.dict()
    plain["service"]["enabled"] = "no"
    assert parsed_config["service"]["enabled"] == "yes"
    assert not isinstance(plain["service"], type(parsed_config["service"]))


def test_section_get_and_items_follow_interpolation():
    from configobj import ConfigObj

    config = ConfigObj(["base = root", "path = %(base)s/data"])
    assert config.get("path") == "root/data"
    assert config.items() == [("base", "root"), ("path", "root/data")]


def test_interpolation_resolves_parent_and_default_sections():
    from configobj import ConfigObj

    config = ConfigObj(
        ["root = /srv", "[DEFAULT]", "suffix = logs", "[child]", "path = %(root)s/%(suffix)s"]
    )
    assert config["child"]["path"] == "/srv/logs"


def test_interpolation_can_be_disabled():
    from configobj import ConfigObj

    config = ConfigObj(["base = root", "path = %(base)s/data"], interpolation=False)
    assert config["path"] == "%(base)s/data"
    assert config.interpolation is False


def test_template_interpolation_uses_documented_syntax():
    from configobj import ConfigObj

    config = ConfigObj(["base = root", "path = ${base}/data"], interpolation="template")
    assert config["path"] == "root/data"


def test_list_interpolation_returns_resolved_copy():
    from configobj import ConfigObj

    config = ConfigObj(["base = root", "parts = %(base)s, fixed"])
    values = config["parts"]
    values.append("extra")
    assert values == ["root", "fixed", "extra"]
    assert config["parts"] == ["root", "fixed"]


def test_unrepr_preserves_basic_python_types():
    from configobj import ConfigObj

    config = ConfigObj(
        ["count = 3", "enabled = True", "items = [1, 2, 'x']", "mapping = {'a': 1}"],
        unrepr=True,
    )
    assert config.dict() == {
        "count": 3,
        "enabled": True,
        "items": [1, 2, "x"],
        "mapping": {"a": 1},
    }


def test_unrepr_write_round_trip_preserves_types():
    from configobj import ConfigObj

    original = ConfigObj(["value = (1, 2)", "none = None"], unrepr=True)
    reread = ConfigObj(original.write(), unrepr=True)
    assert reread["value"] == (1, 2)
    assert reread["none"] is None


def test_list_values_false_keeps_commas_in_scalar():
    from configobj import ConfigObj

    config = ConfigObj(["value = one, two"], list_values=False)
    assert config["value"] == "one, two"
    assert config.list_values is False


def test_write_empty_values_flag_changes_empty_value_projection():
    from configobj import ConfigObj

    config = ConfigObj(["empty ="])
    assert config["empty"] == ""
    assert config.write() == ['empty = ""']
    config.write_empty_values = True
    assert config.write() == ["empty = "]


def test_indent_type_and_newline_attributes_are_documented():
    from configobj import ConfigObj

    config = ConfigObj(["[section]", "[[child]]", "value = x"])
    assert config.indent_type == ""
    assert config.newlines is None
    output = config.write()
    assert output[0].startswith("[section]")
    assert output[1].startswith("[[child]]")


def test_utf8_file_encoding_round_trip(tmp_path):
    from configobj import ConfigObj

    path = tmp_path / "unicode.ini"
    path.write_bytes("label = café\n".encode("utf-8"))
    config = ConfigObj(path, encoding="utf-8")
    assert config["label"] == "café"
    config.filename = str(tmp_path / "unicode-out.ini")
    config.write()
    assert ConfigObj(config.filename, encoding="utf-8")["label"] == "café"


def test_utf8_bom_is_detected_and_decoded(tmp_path):
    from configobj import ConfigObj

    path = tmp_path / "utf8-bom.ini"
    path.write_bytes(b"\xef\xbb\xbf" + "label = café\n".encode("utf-8"))
    config = ConfigObj(path)
    assert config.BOM is True
    assert config["label"] == "café"


def test_as_bool_as_int_as_float_and_as_list_helpers():
    from configobj import ConfigObj

    config = ConfigObj(["truth = yes", "number = 7", "ratio = 1.5", "single = item"])
    assert config.as_bool("truth") is True
    assert config.as_int("number") == 7
    assert config.as_float("ratio") == 1.5
    assert config.as_list("single") == ["item"]


def test_merge_recursively_updates_existing_sections():
    from configobj import ConfigObj

    base = ConfigObj(["[service]", "host = old", "port = 80"])
    update = ConfigObj(["[service]", "host = new", "[[tls]]", "enabled = yes"])
    base.merge(update)
    assert base["service"].dict() == {
        "host": "new",
        "port": "80",
        "tls": {"enabled": "yes"},
    }


def test_rename_preserves_position():
    from configobj import ConfigObj

    config = ConfigObj(["first = 1", "second = 2", "[section]"])
    config.rename("second", "renamed")
    assert config.keys() == ["first", "renamed", "section"]
    assert config["renamed"] == "2"


def test_walk_transforms_scalar_values_and_returns_projection():
    from configobj import ConfigObj

    config = ConfigObj(["first = one", "[section]", "second = two"])

    def upper(section, key):
        value = section[key]
        section[key] = value.upper()
        return section[key]

    result = config.walk(upper)
    assert config["first"] == "ONE"
    assert config["section"]["second"] == "TWO"
    assert result == {"first": "ONE", "section": {"second": "TWO"}}


def test_walk_can_collect_sections_and_scalars():
    from configobj import ConfigObj

    config = ConfigObj(["one = 1", "[section]", "two = 2"])
    seen = []

    def collect(section, key):
        seen.append((section.depth, key))
        return section[key]

    config.walk(collect, call_on_sections=True)
    assert seen == [(0, "one"), (0, "section"), (1, "two")]


def test_reset_returns_config_to_empty_state(parsed_config):
    parsed_config.reset()
    assert parsed_config.dict() == {}
    assert parsed_config.keys() == []
    assert parsed_config.filename is None


def test_reload_reads_updated_local_file(tmp_path):
    from configobj import ConfigObj

    path = tmp_path / "reload.ini"
    path.write_text("value = old\n", encoding="utf-8")
    config = ConfigObj(path)
    path.write_text("value = new\n", encoding="utf-8")
    config.reload()
    assert config["value"] == "new"


def test_reload_without_filename_raises_public_error():
    from configobj import ConfigObj, ReloadError

    with pytest.raises(ReloadError):
        ConfigObj(["value = x"]).reload()


def test_missing_interpolation_raises_public_error():
    from configobj import ConfigObj, MissingInterpolationOption

    config = ConfigObj(["value = %(missing)s"])
    with pytest.raises(MissingInterpolationOption):
        config["value"]


def test_invalid_syntax_raises_parse_error():
    from configobj import ConfigObj, ParseError

    with pytest.raises(ParseError):
        ConfigObj(["this is not a setting"], raise_errors=True)


def test_non_string_key_is_rejected():
    from configobj import ConfigObj

    with pytest.raises(ValueError):
        ConfigObj({1: "value"})


def test_stringify_false_rejects_non_string_values():
    from configobj import ConfigObj

    config = ConfigObj(stringify=False)
    with pytest.raises(TypeError):
        config["count"] = 3


def test_validator_check_converts_standard_values():
    from configobj.validate import Validator

    validator = Validator()
    assert validator.check("integer(1, 9)", "4") == 4
    assert validator.check("float(min=1)", "1.5") == 1.5
    assert validator.check("boolean", "yes") is True
    assert validator.check("option('safe', 'fast')", "fast") == "fast"


def test_validator_check_supports_lists_and_bounds():
    from configobj.validate import Validator, VdtValueTooSmallError

    validator = Validator()
    assert validator.check("int_list(min=2, max=3)", ["1", "2"]) == [1, 2]
    assert validator.check("string_list", ["one", "two"]) == ["one", "two"]
    with pytest.raises(VdtValueTooSmallError) as caught:
        validator.check("integer(5, 9)", "3")
    assert caught.type is VdtValueTooSmallError


def test_validator_defaults_and_custom_function():
    from configobj.validate import Validator

    validator = Validator({"even": lambda value: int(value) if int(value) % 2 == 0 else (_ for _ in ()).throw(ValueError())})
    assert validator.check("integer(default=7)", "", missing=True) == 7
    assert validator.get_default_value("option('a', 'b', default='b')") == "b"
    assert validator.check("even", "4") == 4


def test_direct_validation_converts_values_and_records_defaults():
    from configobj.validate import Validator

    config = make_config_with_spec(["port = 12"], validation_spec())
    assert config.validate(Validator()) is True
    assert config["port"] == 12
    assert config["enabled"] is True
    assert config.defaults == ["enabled", "mode", "labels"]
    assert config["database"].defaults == ["host", "retries"]


def test_validation_preserve_errors_and_flatten_errors():
    from configobj import ConfigObj, flatten_errors
    from configobj.validate import Validator

    config = ConfigObj(
        ["port = not-a-number", "[database]", "retries = 9"],
        configspec=["port = integer(1, 10)", "[database]", "retries = integer(0, 5)"],
    )
    result = config.validate(Validator(), preserve_errors=True)
    failures = flatten_errors(config, result)
    assert result is not True
    assert ("port" in [entry[1] for entry in failures])
    assert any(entry[1] == "retries" for entry in failures)


def test_validation_copy_fills_missing_values_for_writing():
    from configobj import ConfigObj
    from configobj.validate import Validator

    config = ConfigObj([], configspec=["name = string(default='guest')"])
    assert config.validate(Validator(), copy=True) is True
    assert config["name"] == "guest"
    assert config.defaults == []
    assert config.write() == ["name = guest"]


def test_simpleval_checks_presence_against_spec():
    from configobj import ConfigObj, SimpleVal

    config = ConfigObj(["present = yes"], configspec=["present = ", "missing = "])
    result = config.validate(SimpleVal())
    assert result == {"present": True, "missing": False}


def test_extra_values_are_reported_after_validation():
    from configobj import ConfigObj, get_extra_values
    from configobj.validate import Validator

    config = ConfigObj(
        ["known = yes", "extra = value"],
        configspec=["known = boolean"],
    )
    assert config.validate(Validator()) is True
    assert get_extra_values(config) == [((), "extra")]


def test_default_restore_methods_restore_nested_values():
    from configobj import ConfigObj
    from configobj.validate import Validator

    config = ConfigObj(
        ["[database]", "host = custom"],
        configspec=["[database]", "host = string(default='localhost')", "port = integer(default=5432)"],
    )
    assert config.validate(Validator()) is True
    config["database"]["host"] = "changed"
    config["database"].restore_default("host")
    assert config["database"]["host"] == "localhost"
    config["database"]["port"] = 1
    config.restore_defaults()
    assert config["database"]["port"] == 5432
