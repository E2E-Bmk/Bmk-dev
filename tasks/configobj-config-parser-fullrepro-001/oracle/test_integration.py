from __future__ import annotations

from io import StringIO

import pytest

from conftest import as_plain, make_config, validation_spec, write_config


@pytest.mark.depends_on("test_constructor_parses_scalar_and_list_values")
def test_parse_nested_list_and_write_round_trip_preserves_structure(parsed_config):
    from configobj import ConfigObj

    written = parsed_config.write()
    reread = ConfigObj(written)
    assert as_plain(reread) == as_plain(parsed_config)
    assert reread["service"]["limits"]["high"] == "5"


@pytest.mark.depends_on("test_comments_and_order_are_recorded", "test_write_returns_ordered_lines_and_keeps_semantics")
def test_comments_order_and_sections_survive_local_file_round_trip(tmp_path, local_config_lines):
    from configobj import ConfigObj

    path = write_config(tmp_path / "config.ini", local_config_lines)
    first = ConfigObj(path)
    first.filename = str(tmp_path / "written.ini")
    first.write()
    second = ConfigObj(first.filename)
    assert second.keys() == ["title", "items", "server"]
    assert second["server"].keys() == ["host", "port", "tls"]
    assert second["server"].inline_comments["host"] == "# inline host"
    assert second.dict() == first.dict()


@pytest.mark.depends_on("test_interpolation_resolves_parent_and_default_sections", "test_interpolation_can_be_disabled")
def test_interpolation_modes_project_same_source_differently():
    from configobj import ConfigObj

    lines = ["base = root", "path = %(base)s/data"]
    enabled = ConfigObj(lines)
    disabled = ConfigObj(lines, interpolation=False)
    assert enabled["path"] == "root/data"
    assert disabled["path"] == "%(base)s/data"
    disabled.interpolation = True
    assert disabled["path"] == "root/data"


@pytest.mark.depends_on("test_template_interpolation_uses_documented_syntax", "test_unrepr_preserves_basic_python_types")
def test_template_and_unrepr_workflows_keep_independent_semantics():
    from configobj import ConfigObj

    template = ConfigObj(["root = /srv", "path = ${root}/data"], interpolation="template")
    typed = ConfigObj(["items = [1, 2]", "active = False"], unrepr=True)
    assert template["path"] == "/srv/data"
    assert ConfigObj(template.write(), interpolation="template")["path"] == "/srv/data"
    typed_again = ConfigObj(typed.write(), unrepr=True)
    assert typed_again["items"] == [1, 2]
    assert typed_again["active"] is False


@pytest.mark.depends_on("test_list_interpolation_returns_resolved_copy", "test_list_values_false_keeps_commas_in_scalar")
def test_list_interpolation_and_literal_comma_modes_are_distinct():
    from configobj import ConfigObj

    interpolated = ConfigObj(["base = root", "parts = %(base)s, fixed"])
    literal = ConfigObj(["base = root", "parts = %(base)s, fixed"], list_values=False)
    assert interpolated["parts"] == ["root", "fixed"]
    assert literal["parts"] == "root, fixed"
    reparsed = ConfigObj(interpolated.write())
    assert reparsed["parts"] == ["root", "fixed"]


@pytest.mark.depends_on("test_utf8_file_encoding_round_trip", "test_utf8_bom_is_detected_and_decoded")
def test_utf8_and_utf8_bom_local_files_decode_to_same_semantic_value(tmp_path):
    from configobj import ConfigObj

    utf8 = tmp_path / "utf8.ini"
    utf8_bom = tmp_path / "utf8-bom.ini"
    utf8.write_bytes("label = café\n".encode("utf-8"))
    utf8_bom.write_bytes(b"\xef\xbb\xbf" + "label = café\n".encode("utf-8"))
    left = ConfigObj(utf8, encoding="utf-8")
    right = ConfigObj(utf8_bom)
    assert left.dict() == right.dict() == {"label": "café"}
    assert right.BOM is True


@pytest.mark.depends_on("test_as_bool_as_int_as_float_and_as_list_helpers", "test_reset_returns_config_to_empty_state")
def test_section_helpers_and_reset_support_reusable_config_lifecycle():
    config = make_config(["enabled = on", "count = 2", "name = demo"])
    assert config.as_bool("enabled") is True
    assert config.as_int("count") == 2
    config.reset()
    config["enabled"] = "off"
    assert config.as_bool("enabled") is False
    assert config.keys() == ["enabled"]


@pytest.mark.depends_on("test_merge_recursively_updates_existing_sections", "test_rename_preserves_position")
def test_merge_then_rename_keeps_recursive_state_and_order():
    base = make_config(["first = one", "[service]", "host = old"])
    update = make_config(["[service]", "port = 80"])
    base.merge(update)
    base.rename("first", "renamed")
    assert base.keys() == ["renamed", "service"]
    assert base["service"].dict() == {"host": "old", "port": "80"}


@pytest.mark.depends_on("test_walk_transforms_scalar_values_and_returns_projection", "test_walk_can_collect_sections_and_scalars")
def test_walk_transformation_then_plain_projection_is_consistent():
    config = make_config(["first = one", "[section]", "second = two"])

    def upper(section, key):
        value = section[key]
        section[key] = value.upper()
        return section[key]

    projection = config.walk(upper)
    assert projection == as_plain(config)
    assert config.dict() == {"first": "ONE", "section": {"second": "TWO"}}


@pytest.mark.depends_on("test_reload_reads_updated_local_file", "test_reload_without_filename_raises_public_error")
def test_reload_workflow_refreshes_file_and_preserves_filename_contract(tmp_path):
    from configobj import ConfigObj

    path = tmp_path / "settings.ini"
    path.write_text("value = first\n", encoding="utf-8")
    config = ConfigObj(path)
    path.write_text("value = second\nnew = yes\n", encoding="utf-8")
    config.reload()
    assert config.dict() == {"value": "second", "new": "yes"}
    assert config.filename == str(path)


@pytest.mark.depends_on("test_missing_interpolation_raises_public_error", "test_invalid_syntax_raises_parse_error")
def test_public_parse_errors_are_distinguishable_from_interpolation_errors():
    from configobj import ConfigObj, ConfigObjError, MissingInterpolationOption, ParseError

    with pytest.raises(MissingInterpolationOption):
        ConfigObj(["value = %(missing)s"])["value"]
    with pytest.raises(ParseError):
        ConfigObj(["broken line"], raise_errors=True)
    assert issubclass(MissingInterpolationOption, ConfigObjError)
    assert issubclass(ParseError, ConfigObjError)


@pytest.mark.depends_on("test_stringify_false_rejects_non_string_values", "test_validator_check_converts_standard_values")
def test_stringify_policy_and_validator_conversion_define_assignment_boundary():
    from configobj import ConfigObj
    from configobj.validate import Validator

    config = ConfigObj(["value = 4"], configspec=["value = integer"], stringify=False)
    assert config.validate(Validator()) is True
    assert config["value"] == "4"
    strict = ConfigObj(stringify=False)
    with pytest.raises(TypeError):
        strict["value"] = 4


@pytest.mark.depends_on("test_validator_check_supports_lists_and_bounds", "test_direct_validation_converts_values_and_records_defaults")
def test_validation_converts_nested_values_and_preserves_default_markers():
    from configobj import ConfigObj
    from configobj.validate import Validator

    config = ConfigObj(
        ["labels = one, two", "[database]", "retries = 3"],
        configspec=validation_spec(),
    )
    assert config.validate(Validator()) is True
    assert config["labels"] == ["one", "two"]
    assert config["port"] == 8080
    assert config["database"]["host"] == "localhost"
    assert "port" in config.defaults
    assert "host" in config["database"].defaults


@pytest.mark.depends_on("test_validator_defaults_and_custom_function", "test_validation_copy_fills_missing_values_for_writing")
def test_custom_validator_and_copy_mode_create_a_complete_local_config():
    from configobj import ConfigObj
    from configobj.validate import Validator

    validator = Validator({"even": lambda value: int(value) if int(value) % 2 == 0 else 0})
    config = ConfigObj([], configspec=["count = even(default=4)", "name = string(default='guest')"])
    assert config.validate(validator, copy=True) is True
    assert config.dict() == {"count": 4, "name": "guest"}
    assert config.defaults == []
    assert config.write() == ["count = 4", "name = guest"]


@pytest.mark.depends_on("test_validation_preserve_errors_and_flatten_errors", "test_extra_values_are_reported_after_validation")
def test_validation_error_projection_and_extra_value_projection_are_composable():
    from configobj import ConfigObj, flatten_errors, get_extra_values
    from configobj.validate import Validator

    config = ConfigObj(
        ["port = bad", "extra = present"],
        configspec=["port = integer(1, 5)"],
    )
    result = config.validate(Validator(), preserve_errors=True)
    failures = flatten_errors(config, result)
    assert any(entry[1] == "port" for entry in failures)
    assert get_extra_values(config) == [((), "extra")]


@pytest.mark.depends_on("test_default_restore_methods_restore_nested_values", "test_direct_validation_converts_values_and_records_defaults")
def test_restore_defaults_after_user_edits_reestablishes_validated_projection():
    from configobj import ConfigObj
    from configobj.validate import Validator

    config = ConfigObj([], configspec=["[service]", "host = string(default='localhost')", "port = integer(default=80)"])
    assert config.validate(Validator()) is True
    config["service"]["host"] = "custom"
    config["service"]["port"] = 9090
    config["service"].restore_defaults()
    assert config["service"].dict() == {"host": "localhost", "port": 80}
    assert set(config["service"].defaults) == {"host", "port"}


@pytest.mark.depends_on("test_simpleval_checks_presence_against_spec", "test_write_empty_values_flag_changes_empty_value_projection")
def test_simpleval_presence_and_empty_value_writing_form_a_complete_file():
    from configobj import ConfigObj, SimpleVal

    config = ConfigObj(["present = yes", "empty ="], configspec=["present = ", "empty = "])
    assert config.validate(SimpleVal()) is True
    config.write_empty_values = True
    assert "empty = " in config.write()


@pytest.mark.depends_on("test_constructor_accepts_mapping_and_preserves_member_order", "test_section_dict_returns_detached_plain_mapping")
def test_mapping_construction_then_mutation_keeps_section_isolation():
    source = {"name": "one", "child": {"value": "two"}}
    config = make_config(source)
    source["child"]["value"] = "changed"
    config["child"]["new"] = "entry"
    assert config["child"].dict() == {"value": "two", "new": "entry"}
    assert config.keys() == ["name", "child"]


@pytest.mark.depends_on("test_constructor_accepts_file_like_text", "test_write_returns_ordered_lines_and_keeps_semantics")
def test_file_like_input_and_in_memory_output_round_trip():
    from configobj import ConfigObj

    source = ConfigObj(StringIO("a = 1\n[b]\nc = 3, 4\n"))
    output = source.write()
    result = ConfigObj(StringIO("\n".join(output) + "\n"))
    assert result.dict() == source.dict()


@pytest.mark.depends_on("test_indent_type_and_newline_attributes_are_documented", "test_comments_and_order_are_recorded")
def test_custom_indent_and_comments_project_without_changing_data():
    from configobj import ConfigObj

    config = ConfigObj(["# top", "[outer]", "[[inner]]", "value = x"], indent_type="  ")
    output = config.write()
    reread = ConfigObj(output)
    assert reread.dict() == config.dict()
    assert any(line.startswith("  [[inner]]") for line in output)


@pytest.mark.depends_on("test_unrepr_write_round_trip_preserves_types", "test_utf8_file_encoding_round_trip")
def test_unrepr_and_encoded_file_write_can_be_chained(tmp_path):
    from configobj import ConfigObj

    config = ConfigObj(["label = 'café'", "numbers = [1, 2]"], unrepr=True, encoding="utf-8")
    config.filename = str(tmp_path / "typed.ini")
    config.write()
    reread = ConfigObj(config.filename, unrepr=True, encoding="utf-8")
    assert reread["label"] == "café"
    assert reread["numbers"] == [1, 2]


@pytest.mark.depends_on("test_validator_check_converts_standard_values", "test_invalid_syntax_raises_parse_error")
def test_validator_conversion_happens_only_after_successful_parse():
    from configobj import ConfigObj
    from configobj.validate import Validator

    config = ConfigObj(["count = 4"], configspec=["count = integer(0, 9)"])
    assert config.validate(Validator()) is True
    assert config["count"] == 4
    from configobj import ParseError

    with pytest.raises(ParseError):
        ConfigObj(["count = 4", "broken"], raise_errors=True)


@pytest.mark.depends_on("test_interpolation_resolves_parent_and_default_sections", "test_list_interpolation_returns_resolved_copy")
def test_interpolation_composes_across_nested_sections_and_lists():
    from configobj import ConfigObj

    config = ConfigObj(
        ["root = /srv", "parts = %(root)s, shared", "[child]", "path = %(root)s/app"],
    )
    assert config["child"]["path"] == "/srv/app"
    assert config["parts"] == ["/srv", "shared"]


@pytest.mark.depends_on("test_constructor_parses_scalar_and_list_values", "test_as_bool_as_int_as_float_and_as_list_helpers")
def test_parsed_values_and_section_helpers_agree_on_scalar_projection():
    config = make_config(["enabled = yes", "count = 3", "ratio = 2.5", "tags = a, b"])
    assert config.as_bool("enabled") is True
    assert config.as_int("count") == int(config["count"])
    assert config.as_float("ratio") == float(config["ratio"])
    assert config.as_list("tags") == config["tags"]


@pytest.mark.depends_on("test_merge_recursively_updates_existing_sections", "test_write_returns_ordered_lines_and_keeps_semantics")
def test_merge_then_write_reparse_preserves_recursive_updates():
    from configobj import ConfigObj

    base = ConfigObj(["name = base", "[service]", "host = old"])
    base.merge(ConfigObj(["[service]", "host = new", "port = 8080"]))
    reread = ConfigObj(base.write())
    assert reread.dict() == {"name": "base", "service": {"host": "new", "port": "8080"}}


@pytest.mark.depends_on("test_validation_copy_fills_missing_values_for_writing", "test_utf8_file_encoding_round_trip")
def test_validated_defaults_write_to_an_encoded_local_file(tmp_path):
    from configobj import ConfigObj
    from configobj.validate import Validator

    config = ConfigObj([], configspec=["label = string(default='café')"], encoding="utf-8")
    assert config.validate(Validator(), copy=True) is True
    config.encoding = "utf-8"
    config.filename = str(tmp_path / "defaults.ini")
    config.write()
    reread = ConfigObj(config.filename, encoding="utf-8")
    assert reread["label"] == "café"


@pytest.mark.depends_on("test_validation_preserve_errors_and_flatten_errors", "test_default_restore_methods_restore_nested_values")
def test_failed_validation_then_default_restore_keeps_nested_sections_auditable():
    from configobj import ConfigObj, flatten_errors
    from configobj.validate import Validator

    config = ConfigObj(
        ["[service]", "port = bad"],
        configspec=["[service]", "port = integer(default=80)", "host = string(default='localhost')"],
    )
    result = config.validate(Validator(), preserve_errors=True)
    assert any(entry[0] == ["service"] and entry[1] == "port" for entry in flatten_errors(config, result))
    config["service"].restore_default("port")
    assert config["service"]["port"] == 80


@pytest.mark.depends_on("test_extra_values_are_reported_after_validation", "test_reset_returns_config_to_empty_state")
def test_extra_value_inventory_is_cleared_by_reset():
    from configobj import ConfigObj, get_extra_values
    from configobj.validate import Validator

    config = ConfigObj(["known = yes", "extra = value"], configspec=["known = boolean"])
    config.validate(Validator())
    assert get_extra_values(config) == [((), "extra")]
    config.reset()
    assert get_extra_values(config) == []


@pytest.mark.depends_on("test_invalid_syntax_raises_parse_error")
def test_local_file_error_flag_rejects_missing_path(tmp_path):
    from configobj import ConfigObj

    with pytest.raises(IOError):
        ConfigObj(tmp_path / "missing.ini", file_error=True)


@pytest.mark.depends_on("test_utf8_file_encoding_round_trip", "test_reload_reads_updated_local_file")
def test_reload_after_encoded_write_preserves_unicode_value(tmp_path):
    from configobj import ConfigObj

    path = tmp_path / "unicode.ini"
    config = ConfigObj(["label = café"], encoding="utf-8")
    config.filename = str(path)
    config.write()
    reloaded = ConfigObj(path, encoding="utf-8")
    path.write_bytes("label = crème\n".encode("utf-8"))
    reloaded.reload()
    assert reloaded["label"] == "crème"


@pytest.mark.depends_on("test_validator_check_supports_lists_and_bounds", "test_validation_copy_fills_missing_values_for_writing")
def test_validated_list_defaults_are_typed_and_written_as_lists():
    from configobj import ConfigObj
    from configobj.validate import Validator

    config = ConfigObj([], configspec=["labels = string_list(default=list('a', 'b'))"])
    assert config.validate(Validator(), copy=True) is True
    assert config["labels"] == ["a", "b"]
    assert config.write() == ["labels = a, b"]
