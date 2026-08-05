import io
from dataclasses import dataclass, field
from typing import Dict, List, Literal

import pytest

from conftest import AppConfig, CollectionConfig, Color, EnumConfig
from omegaconf import (
    DictConfig,
    ListConfig,
    ListMergeMode,
    OmegaConf,
    ReadonlyConfigError,
    SCMode,
    ValidationError,
    open_dict,
    read_write,
)


@pytest.mark.depends_on(
    "test_from_dotlist_builds_nested_paths",
    "test_select_supports_dot_and_bracket_paths",
)
def test_dotlist_to_merge_to_select_pipeline():
    base = OmegaConf.create({"service": {"host": "localhost", "port": 80}})
    override = OmegaConf.from_dotlist(["service.port=443", "service.tls=true"])
    merged = OmegaConf.merge(base, override)
    OmegaConf.update(merged, "service.host", "example")

    assert OmegaConf.select(merged, "service.host") == "example"
    assert OmegaConf.select(merged, "service.port") == 443
    assert merged.service.tls is True


@pytest.mark.depends_on(
    "test_from_cli_accepts_explicit_arguments",
    "test_merge_replaces_lists_by_default",
)
def test_cli_override_merges_with_base_config():
    base = OmegaConf.create({"server": {"port": 80}, "users": ["one", "two"]})
    cli = OmegaConf.from_cli(["server.port=82", "users=[three]"])
    merged = OmegaConf.merge(base, cli)

    assert merged.server.port == 82
    assert merged.users == ["three"]
    assert base.server.port == 80


@pytest.mark.depends_on(
    "test_create_yaml_string_parses_scalars",
    "test_to_container_preserves_unresolved_and_resolves_option",
)
def test_yaml_string_round_trip_preserves_interpolation_projection(tmp_path):
    source = (
        "name: demo\n"
        "port: 8080\n"
        "endpoint: http://${name}:${port}\n"
    )
    config = OmegaConf.create(source)
    raw_yaml = OmegaConf.to_yaml(config)
    resolved_yaml = OmegaConf.to_yaml(config, resolve=True)
    path = tmp_path / "roundtrip.yaml"
    path.write_text(raw_yaml, encoding="utf-8")
    loaded = OmegaConf.load(path)

    assert "endpoint: http://${name}:${port}" in raw_yaml
    assert "endpoint: http://demo:8080" in resolved_yaml
    assert loaded.endpoint == "http://demo:8080"


@pytest.mark.depends_on(
    "test_save_and_load_path_round_trip",
    "test_save_accepts_file_object",
)
def test_save_load_file_object_and_path_agree(tmp_path):
    config = OmegaConf.create({"name": "demo", "nested": {"value": 7}})
    path = tmp_path / "config.yaml"
    OmegaConf.save(config, path)
    from_path = OmegaConf.load(path)

    stream = io.StringIO()
    OmegaConf.save(config, stream)
    stream.seek(0)
    from_stream = OmegaConf.load(stream)

    assert OmegaConf.to_container(from_path) == OmegaConf.to_container(from_stream)


@pytest.mark.depends_on("test_to_yaml_emits_sorted_yaml_projection")
def test_yaml_flow_style_and_sorted_keys_are_public_options():
    config = OmegaConf.create({"z": [1, 2], "a": {"b": 3}})

    rendered = OmegaConf.to_yaml(
        config, sort_keys=True, default_flow_style=None
    )

    assert rendered.index("a:") < rendered.index("z:")
    assert "[1, 2]" in rendered


@pytest.mark.depends_on("test_create_list_config_preserves_nested_values")
def test_yaml_load_list_root_round_trips_as_list_config(tmp_path):
    path = tmp_path / "items.yaml"
    path.write_text("- one\n- two\n", encoding="utf-8")

    config = OmegaConf.load(path)
    output = tmp_path / "items-copy.yaml"
    OmegaConf.save(config, output)
    loaded = OmegaConf.load(output)

    assert isinstance(config, ListConfig)
    assert isinstance(loaded, ListConfig)
    assert list(loaded) == ["one", "two"]


@pytest.mark.depends_on(
    "test_structured_creates_dictconfig_and_type",
    "test_merge_replaces_lists_by_default",
)
def test_merge_structured_schema_validates_plain_yaml():
    schema = OmegaConf.structured(AppConfig)
    values = OmegaConf.create(
        {
            "server": {"host": "example", "port": 443},
            "tags": ["prod"],
            "enabled": False,
            "mode": "prod",
            "required": "configured",
        }
    )

    merged = OmegaConf.merge(schema, values)

    assert OmegaConf.get_type(merged) is AppConfig
    assert merged.server.host == "example"
    assert merged.server.port == 443
    assert merged.tags == ["prod"]


@pytest.mark.depends_on("test_structured_rejects_invalid_scalar_type")
def test_merge_structured_schema_rejects_wrong_type():
    schema = OmegaConf.structured(AppConfig)
    values = OmegaConf.create({"server": {"port": "not-a-port"}})

    with pytest.raises(ValidationError):
        OmegaConf.merge(schema, values)


@pytest.mark.depends_on(
    "test_structured_creates_dictconfig_and_type",
    "test_to_object_instantiates_structured_dataclass",
)
def test_structured_nested_to_container_modes_agree():
    root = OmegaConf.create({"app": AppConfig(required="configured")})

    as_dict = OmegaConf.to_container(root, structured_config_mode=SCMode.DICT)
    as_dict_config = OmegaConf.to_container(
        root, structured_config_mode=SCMode.DICT_CONFIG
    )
    as_object = OmegaConf.to_container(
        root, structured_config_mode=SCMode.INSTANTIATE
    )

    assert as_dict["app"]["server"]["port"] == 80
    assert isinstance(as_dict_config["app"], DictConfig)
    assert isinstance(as_object["app"], AppConfig)
    assert as_object["app"].required == "configured"


@pytest.mark.depends_on(
    "test_to_object_instantiates_structured_dataclass",
    "test_interpolation_resolves_lazily",
)
def test_to_object_resolves_structured_interpolation():
    @dataclass
    class Interpolated:
        port: int = 80
        alias: int = "${port}"

    config = OmegaConf.structured(Interpolated)
    result = OmegaConf.to_object(config)

    assert isinstance(result, Interpolated)
    assert result.alias == 80


@pytest.mark.depends_on(
    "test_structured_coerces_assignable_scalar",
    "test_structured_rejects_invalid_scalar_type",
)
def test_structured_list_and_dict_types_validate_updates():
    config = OmegaConf.structured(CollectionConfig)
    config.numbers.append("2")
    config.mapping["two"] = "2"

    assert config.numbers == [1, 2]
    assert config.mapping["two"] == 2
    with pytest.raises(ValidationError):
        config.numbers.append("bad")


@pytest.mark.depends_on("test_structured_rejects_invalid_scalar_type")
def test_structured_literal_and_enum_values_round_trip():
    @dataclass
    class LiteralConfig:
        mode: Literal["dev", "prod"] = "dev"

    literal = OmegaConf.structured(LiteralConfig)
    literal.mode = "prod"
    enum_config = OmegaConf.structured(EnumConfig)
    enum_config.color = "BLUE"

    assert literal.mode == "prod"
    assert enum_config.color is Color.BLUE
    assert OmegaConf.to_container(enum_config, enum_to_str=True)["color"] == "BLUE"
    with pytest.raises(ValidationError):
        literal.mode = "debug"


@pytest.mark.depends_on(
    "test_set_struct_reports_state_and_blocks_new_key",
    "test_set_readonly_blocks_mutation",
)
def test_readonly_and_struct_flags_interact_with_contexts():
    config = OmegaConf.create({"known": 1})
    OmegaConf.set_struct(config, True)
    OmegaConf.set_readonly(config, True)

    with pytest.raises(ReadonlyConfigError):
        config.known = 2

    from omegaconf.errors import ConfigAttributeError

    with pytest.raises(ConfigAttributeError):
        config.new = 3

    with read_write(config):
        config.known = 2
        with open_dict(config):
            config.new = 3

    assert config.known == 2
    assert config.new == 3
    assert OmegaConf.is_struct(config) is True
    assert OmegaConf.is_readonly(config) is True


@pytest.mark.depends_on("test_update_changes_scalar_path")
def test_update_force_add_respects_struct_context():
    config = OmegaConf.create({"known": 1})
    OmegaConf.set_struct(config, True)

    OmegaConf.update(config, "new.branch.value", 10, force_add=True)

    assert config.new.branch.value == 10
    assert OmegaConf.is_struct(config) is True


@pytest.mark.depends_on(
    "test_from_dotlist_escapes_literal_key_delimiters",
    "test_select_supports_dot_and_bracket_paths",
)
def test_select_and_update_share_escaped_key_paths():
    config = OmegaConf.create({"literal.key": {"item[0]": 1}})

    OmegaConf.update(config, r"literal\.key.item\[0\]", 2)

    assert OmegaConf.select(config, r"literal\.key.item\[0\]") == 2


@pytest.mark.depends_on("test_missing_sentinel_is_reported_publicly")
def test_missing_keys_matches_nested_plain_and_list_values():
    config = OmegaConf.create(
        {
            "foo": {"bar": "???"},
            "missing": "???",
            "items": ["ready", None, "???"],
        }
    )

    assert OmegaConf.missing_keys(config) == {"foo.bar", "missing", "items[2]"}


@pytest.mark.depends_on(
    "test_missing_sentinel_is_reported_publicly",
    "test_interpolation_resolves_lazily",
)
def test_missing_keys_follows_node_interpolations():
    config = OmegaConf.create({"required": "???", "reference": "${required}"})

    missing = OmegaConf.missing_keys(config)

    assert "required" in missing
    assert "reference" in missing


@pytest.mark.depends_on(
    "test_interpolation_resolves_lazily",
    "test_to_container_preserves_unresolved_and_resolves_option",
)
def test_resolve_and_to_container_views_agree():
    config = OmegaConf.create({"value": 10, "alias": "${value}"})
    before = OmegaConf.to_container(config)

    OmegaConf.resolve(config)
    after = OmegaConf.to_container(config)

    assert before["alias"] == "${value}"
    assert after["alias"] == 10
    assert config.alias == 10


@pytest.mark.depends_on("test_interpolation_resolves_lazily")
def test_relative_interpolations_follow_nested_scope():
    config = OmegaConf.create(
        {"port": 8080, "server": {"label": "${..port}"}}
    )

    assert config.server.label == 8080


@pytest.mark.depends_on("test_interpolation_resolves_lazily")
def test_nested_interpolation_reselects_after_source_change():
    config = OmegaConf.create(
        {
            "plans": {"A": "plan A", "B": "plan B"},
            "selected": "A",
            "plan": "${plans[${selected}]}",
        }
    )

    assert config.plan == "plan A"
    config.selected = "B"
    assert config.plan == "plan B"


@pytest.mark.depends_on("test_register_resolver_evaluates_and_has_resolver")
def test_custom_resolver_variadic_and_nested_arguments():
    OmegaConf.register_resolver(
        "joiner", lambda *values: "-".join(str(value) for value in values)
    )
    config = OmegaConf.create({"seed": 7, "joined": "${joiner:alpha,${seed}}"})

    assert config.joined == "alpha-7"


@pytest.mark.depends_on("test_register_resolver_evaluates_and_has_resolver")
def test_custom_resolver_cache_reuses_literal_arguments():
    calls = []

    def counted(value):
        calls.append(value)
        return len(calls)

    OmegaConf.register_resolver("counted", counted, use_cache=True)
    config = OmegaConf.create(
        {"first": "${counted:literal}", "second": "${counted:literal}"}
    )

    assert config.first == 1
    assert config.second == 1
    assert calls == ["literal"]


@pytest.mark.depends_on("test_register_resolver_evaluates_and_has_resolver")
def test_custom_resolver_replace_and_clear_lifecycle():
    OmegaConf.register_resolver("marker", lambda: "first")
    with pytest.raises(ValueError):
        OmegaConf.register_resolver("marker", lambda: "second")

    OmegaConf.register_resolver("marker", lambda: "second", replace=True)
    assert OmegaConf.create({"value": "${marker:}"}).value == "second"
    assert OmegaConf.clear_resolver("marker") is True
    assert OmegaConf.has_resolver("marker") is False
    assert OmegaConf.clear_resolver("marker") is False


@pytest.mark.depends_on("test_register_resolver_evaluates_and_has_resolver")
def test_custom_resolver_parent_context_reads_sibling():
    def pick(name, *, _parent_):
        return _parent_.get(name, "fallback")

    OmegaConf.register_resolver("pick", pick)
    config = OmegaConf.create(
        {
            "node": {
                "value": 9,
                "found": "${pick:value}",
                "missing": "${pick:other}",
            }
        }
    )

    assert config.node.found == 9
    assert config.node.missing == "fallback"


@pytest.mark.depends_on("test_register_resolver_evaluates_and_has_resolver")
def test_builtin_select_resolver_supplies_default():
    config = OmegaConf.create({"message": "${oc.select:missing,default}"})

    assert config.message == "default"
    config.missing = "present"
    assert config.message == "present"


@pytest.mark.depends_on("test_register_resolver_evaluates_and_has_resolver")
def test_builtin_decode_resolver_parses_scalar_and_list():
    config = OmegaConf.create(
        {
            "count": "${oc.decode:'12'}",
            "enabled": "${oc.decode:'true'}",
            "items": "${oc.decode:'[alpha, beta]'}",
        }
    )

    assert config.count == 12
    assert config.enabled is True
    assert config["items"] == ["alpha", "beta"]


@pytest.mark.depends_on("test_register_resolver_evaluates_and_has_resolver")
def test_builtin_create_resolver_returns_config_container():
    config = OmegaConf.create(
        {"nested": "${oc.create:{a: 10, b: 20}}"}
    )

    assert isinstance(config.nested, DictConfig)
    assert config.nested.a == 10
    assert OmegaConf.to_container(config.nested) == {"a": 10, "b": 20}


@pytest.mark.depends_on("test_register_resolver_evaluates_and_has_resolver")
def test_builtin_dict_resolvers_project_keys_and_values():
    config = OmegaConf.create(
        {
            "workers": {"node3": "10.0.0.2", "node7": "10.0.0.9"},
            "names": "${oc.dict.keys:workers}",
            "addresses": "${oc.dict.values:workers}",
        }
    )

    assert isinstance(config.names, ListConfig)
    assert list(config.names) == ["node3", "node7"]
    assert list(config.addresses) == ["10.0.0.2", "10.0.0.9"]


@pytest.mark.depends_on("test_interpolation_resolves_lazily")
def test_escaped_interpolation_literal_is_not_resolved():
    config = OmegaConf.create({"directory": "tmp", "literal": r"\${directory}"})

    assert config.literal == "${directory}"


@pytest.mark.depends_on(
    "test_merge_extends_lists_with_public_mode",
    "test_save_and_load_path_round_trip",
)
def test_merged_config_serialization_matches_public_views(tmp_path):
    merged = OmegaConf.merge(
        {"items": [1, 2], "name": "demo"},
        {"items": [3], "port": 8080},
        list_merge_mode=ListMergeMode.EXTEND,
    )
    path = tmp_path / "merged.yaml"
    OmegaConf.save(merged, path)
    loaded = OmegaConf.load(path)

    assert OmegaConf.to_container(loaded) == {
        "items": [1, 2, 3],
        "name": "demo",
        "port": 8080,
    }
