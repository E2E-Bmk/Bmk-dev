import io

import pytest

from conftest import AppConfig, CollectionConfig, EnumConfig, OptionalConfig, ServerConfig
from omegaconf import (
    DictConfig,
    ListConfig,
    ListMergeMode,
    MissingMandatoryValue,
    OmegaConf,
    ReadonlyConfigError,
    ValidationError,
    open_dict,
    read_write,
)
from omegaconf.errors import ConfigAttributeError, ConfigKeyError


def test_create_empty_dict_config():
    config = OmegaConf.create()

    assert isinstance(config, DictConfig)
    assert OmegaConf.to_container(config) == {}


def test_create_list_config_preserves_nested_values():
    config = OmegaConf.create([1, {"label": "item"}])

    assert isinstance(config, ListConfig)
    assert config[0] == 1
    assert config[1].label == "item"
    assert OmegaConf.to_container(config) == [1, {"label": "item"}]


def test_create_yaml_string_parses_scalars():
    config = OmegaConf.create(
        "active: true\n"
        "count: 7\n"
        "ratio: 1.5\n"
        "nothing: null\n"
    )

    assert config.active is True
    assert config.count == 7
    assert config.ratio == 1.5
    assert config.nothing is None


def test_attribute_and_item_access_agree(base_config):
    assert base_config.app.name == base_config["app"]["name"]
    assert base_config.database.ports[1] == base_config["database"]["ports"][1]


def test_default_get_returns_fallback(base_config):
    assert base_config.get("not_present", "fallback") == "fallback"
    assert base_config.get("app") == base_config.app


def test_missing_sentinel_is_reported_publicly(base_config):
    assert OmegaConf.is_missing(base_config, "missing")

    with pytest.raises(MissingMandatoryValue):
        _ = base_config.missing


def test_interpolation_resolves_lazily(base_config):
    unresolved = OmegaConf.to_container(base_config)

    assert unresolved["alias"] == "${app.name}"
    assert base_config.alias == "demo"


def test_is_interpolation_and_is_config_views(base_config):
    list_config = OmegaConf.create([1, 2])

    assert OmegaConf.is_config(base_config)
    assert OmegaConf.is_dict(base_config)
    assert not OmegaConf.is_list(base_config)
    assert OmegaConf.is_config(list_config)
    assert OmegaConf.is_list(list_config)
    assert not OmegaConf.is_dict(list_config)
    assert OmegaConf.is_interpolation(base_config, "alias")
    assert not OmegaConf.is_interpolation(base_config, "app")


def test_from_dotlist_builds_nested_paths():
    config = OmegaConf.from_dotlist(
        ["server.port=8080", "features.debug=true", "items=[one,two]"]
    )

    assert config.server.port == 8080
    assert config.features.debug is True
    assert config["items"] == ["one", "two"]


def test_from_dotlist_escapes_literal_key_delimiters():
    config = OmegaConf.from_dotlist([r"a\.b\=c=42"])

    assert config["a.b=c"] == 42
    assert OmegaConf.select(config, r"a\.b\=c") == 42


def test_from_cli_accepts_explicit_arguments():
    config = OmegaConf.from_cli(["server.host=example", "server.port=443"])

    assert config.server.host == "example"
    assert config.server.port == 443


def test_select_supports_dot_and_bracket_paths():
    config = OmegaConf.create(
        {"foo": {"bar": {"value": 3}}, "items": [{"value": 4}]}
    )

    assert OmegaConf.select(config, "foo.bar.value") == 3
    assert OmegaConf.select(config, "foo[bar][value]") == 3
    assert OmegaConf.select(config, "items[0].value") == 4


def test_select_returns_default_for_absent_path():
    config = OmegaConf.create({"present": 10})

    assert OmegaConf.select(config, "absent") is None
    assert OmegaConf.select(config, "absent", default=99) == 99


def test_can_select_distinguishes_missing_and_none():
    config = OmegaConf.create(
        {"present": 10, "none": None, "missing": "???", "bad": "${unknown}"}
    )

    assert OmegaConf.can_select(config, "present")
    assert OmegaConf.can_select(config, "none")
    assert not OmegaConf.can_select(config, "missing")
    assert not OmegaConf.can_select(config, "absent")
    assert not OmegaConf.can_select(config, "bad")


def test_update_changes_scalar_path():
    config = OmegaConf.create({"server": {"port": 80}})

    OmegaConf.update(config, "server.port", 443)

    assert config.server.port == 443


def test_update_merges_or_replaces_mapping():
    config = OmegaConf.create({"section": {"a": 1}})

    OmegaConf.update(config, "section", {"b": 2}, merge=True)
    assert OmegaConf.to_container(config.section) == {"a": 1, "b": 2}

    OmegaConf.update(config, "section", {"c": 3}, merge=False)
    assert OmegaConf.to_container(config.section) == {"c": 3}


def test_merge_replaces_lists_by_default():
    first = OmegaConf.create({"items": [1, 2]})
    second = OmegaConf.create({"items": [3]})

    merged = OmegaConf.merge(first, second)

    assert merged["items"] == [3]
    assert first["items"] == [1, 2]


def test_merge_extends_lists_with_public_mode():
    merged = OmegaConf.merge(
        {"items": [1, 2]},
        {"items": [3]},
        list_merge_mode=ListMergeMode.EXTEND,
    )

    assert merged["items"] == [1, 2, 3]


def test_merge_extends_unique_lists():
    merged = OmegaConf.merge(
        {"items": [1, 2]},
        {"items": [2, 3]},
        list_merge_mode=ListMergeMode.EXTEND_UNIQUE,
    )

    assert merged["items"] == [1, 2, 3]


def test_structured_creates_dictconfig_and_type(app_config):
    assert isinstance(app_config, DictConfig)
    assert OmegaConf.get_type(app_config) is AppConfig
    assert app_config.server.port == 80
    assert app_config.enabled is True


def test_structured_coerces_assignable_scalar(app_config):
    app_config.server.port = "443"

    assert app_config.server.port == 443
    assert isinstance(app_config.server.port, int)


def test_structured_rejects_invalid_scalar_type(app_config):
    with pytest.raises(ValidationError):
        app_config.server.port = "not-a-port"


def test_structured_optional_accepts_none():
    config = OmegaConf.structured(OptionalConfig)

    config.count = None

    assert config.count is None


def test_structured_missing_field_requires_assignment(app_config):
    assert OmegaConf.is_missing(app_config, "required")

    with pytest.raises(MissingMandatoryValue):
        _ = app_config.required

    app_config.required = "configured"
    assert app_config.required == "configured"


def test_set_struct_reports_state_and_blocks_new_key():
    config = OmegaConf.create({"known": 1})
    OmegaConf.set_struct(config, True)

    assert OmegaConf.is_struct(config) is True
    with pytest.raises((ConfigAttributeError, ConfigKeyError)):
        config.new_key = 2


def test_open_dict_temporarily_allows_new_keys():
    config = OmegaConf.create({"known": 1})
    OmegaConf.set_struct(config, True)

    with open_dict(config):
        config.new_key = 2

    assert config.new_key == 2
    assert OmegaConf.is_struct(config) is True


def test_set_readonly_blocks_mutation():
    config = OmegaConf.create({"value": 1})
    OmegaConf.set_readonly(config, True)

    assert OmegaConf.is_readonly(config) is True
    with pytest.raises(ReadonlyConfigError):
        config.value = 2


def test_read_write_temporarily_allows_mutation():
    config = OmegaConf.create({"value": 1})
    OmegaConf.set_readonly(config, True)

    with read_write(config):
        config.value = 2

    assert config.value == 2
    assert OmegaConf.is_readonly(config) is True


def test_to_container_preserves_unresolved_and_resolves_option():
    config = OmegaConf.create({"source": 10, "copy": "${source}"})

    assert OmegaConf.to_container(config)["copy"] == "${source}"
    assert OmegaConf.to_container(config, resolve=True)["copy"] == 10


def test_to_object_instantiates_structured_dataclass():
    config = OmegaConf.structured(AppConfig(required="configured"))

    result = OmegaConf.to_object(config)

    assert isinstance(result, AppConfig)
    assert result.server.port == 80
    assert result.required == "configured"


def test_to_yaml_emits_sorted_yaml_projection():
    config = OmegaConf.create({"z": 1, "a": 2})

    rendered = OmegaConf.to_yaml(config, sort_keys=True)

    assert rendered.index("a:") < rendered.index("z:")
    assert "a: 2" in rendered
    assert "z: 1" in rendered


def test_register_resolver_evaluates_and_has_resolver():
    OmegaConf.register_resolver("double", lambda value: value * 2)
    config = OmegaConf.create({"value": "${double:21}"})

    assert OmegaConf.has_resolver("double")
    assert config.value == 42


def test_save_and_load_path_round_trip(tmp_path):
    config = OmegaConf.create({"name": "demo", "items": [1, 2]})
    path = tmp_path / "config.yaml"

    OmegaConf.save(config, path)
    loaded = OmegaConf.load(path)

    assert OmegaConf.structural_equality(config, loaded)
    assert loaded["items"] == [1, 2]


def test_save_accepts_file_object():
    config = OmegaConf.create({"name": "demo", "port": 8080})
    stream = io.StringIO()

    OmegaConf.save(config, stream)
    stream.seek(0)
    loaded = OmegaConf.load(stream)

    assert OmegaConf.to_container(loaded) == {"name": "demo", "port": 8080}
