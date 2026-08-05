from __future__ import annotations

import json

import pytest


@pytest.mark.depends_on(
    "test_group_registration_projects_attribute_mapping",
    "test_group_ini_values_are_typed",
)
def test_quickstart_grouped_config_uses_file_and_default(tmp_path):
    from oslo_config import cfg
    from conftest import write_ini

    conf = cfg.ConfigOpts()
    group = cfg.OptGroup("mygroup")
    conf.register_group(group)
    conf.register_opts([cfg.StrOpt("option1"), cfg.IntOpt("option2", default=42)], group=group)
    path = write_ini(tmp_path / "quickstart.conf", "[mygroup]\noption1 = foo")
    conf(["--config-file", str(path)], use_env=False)
    assert conf.mygroup.option1 == "foo"
    assert conf.mygroup.option2 == 42


@pytest.mark.depends_on(
    "test_command_line_value_precedes_config_file",
    "test_config_file_precedes_set_default",
)
def test_precedence_chain_default_file_then_cli(tmp_path):
    from conftest import base_conf, write_ini

    conf = base_conf()
    conf.set_default("workers", 3)
    path = write_ini(tmp_path / "sample.conf", "[DEFAULT]\nworkers = 4")
    conf(["--config-file", str(path), "--workers", "7"], use_env=False)
    assert conf.workers == 7


@pytest.mark.depends_on(
    "test_set_override_precedes_config_file",
    "test_export_import_state_preserves_values_and_groups",
)
def test_override_survives_state_export_and_import(tmp_path):
    from oslo_config import cfg
    from conftest import configured_conf

    conf, _ = configured_conf(tmp_path, "[DEFAULT]\nworkers = 4")
    conf.set_override("workers", 12)
    restored = cfg.ConfigOpts.import_state(conf.export_state())
    assert restored.workers == 12
    assert restored.get_location("workers").location == cfg.Locations.set_override


@pytest.mark.depends_on(
    "test_clear_override_restores_config_file_value",
    "test_config_file_location_is_user_controlled",
)
def test_clearing_override_restores_user_location(tmp_path):
    from oslo_config import cfg
    from conftest import configured_conf

    conf, _ = configured_conf(tmp_path, "[DEFAULT]\nworkers = 4")
    conf.set_override("workers", 11)
    conf.clear_override("workers")
    assert conf.workers == 4
    assert conf.get_location("workers").location == cfg.Locations.user


@pytest.mark.depends_on(
    "test_grouped_cli_option_uses_group_prefix",
    "test_command_line_location_is_user_controlled",
)
def test_grouped_cli_value_projects_location_and_value():
    from oslo_config import cfg
    from conftest import base_conf

    conf = base_conf()
    conf(["--api-listen-port", "9443"], use_env=False)
    assert conf.api.listen_port == 9443
    assert conf.get_location("listen_port", group="api").location == cfg.Locations.command_line


@pytest.mark.depends_on(
    "test_list_option_parses_comma_separated_ini_value",
    "test_dict_option_parses_key_value_ini_value",
    "test_multistr_option_preserves_repeated_ini_values",
)
def test_collection_options_round_trip_through_state(tmp_path):
    from oslo_config import cfg
    from conftest import configured_conf

    conf, _ = configured_conf(
        tmp_path,
        """
        [DEFAULT]
        hosts = alpha,beta
        labels = role:api,zone:west
        path = /srv/one
        path = /srv/two
        """,
    )
    restored = cfg.ConfigOpts.import_state(conf.export_state())
    assert restored.hosts == ["alpha", "beta"]
    assert restored.labels == {"role": "api", "zone": "west"}
    assert restored.path == ["/srv/one", "/srv/two"]


@pytest.mark.depends_on(
    "test_default_ini_values_are_typed",
    "test_list_all_sections_reports_parsed_sections",
)
def test_config_dir_files_override_config_file_in_sorted_order(tmp_path):
    from conftest import base_conf, write_ini

    config_file = write_ini(tmp_path / "base.conf", "[DEFAULT]\nworkers = 3")
    config_dir = tmp_path / "conf.d"
    config_dir.mkdir()
    write_ini(config_dir / "10-first.conf", "[DEFAULT]\nworkers = 5")
    write_ini(config_dir / "20-second.conf", "[DEFAULT]\nworkers = 8")
    conf = base_conf()
    conf(["--config-file", str(config_file), "--config-dir", str(config_dir)], use_env=False)
    assert conf.workers == 8


@pytest.mark.depends_on(
    "test_ini_substitution_uses_previously_defined_values",
    "test_list_option_parses_comma_separated_ini_value",
)
def test_substitution_feeds_typed_list_projection(tmp_path):
    from oslo_config import cfg
    from conftest import write_ini

    conf = cfg.ConfigOpts()
    conf.register_opt(cfg.StrOpt("host"))
    conf.register_opt(cfg.PortOpt("port"))
    conf.register_opt(cfg.ListOpt("endpoints"))
    path = write_ini(
        tmp_path / "substitution.conf",
        """
        [DEFAULT]
        host = controller
        port = 5672
        endpoints = $host:$port,backup:$port
        """,
    )
    conf(["--config-file", str(path)], use_env=False)
    assert conf.endpoints == ["controller:5672", "backup:5672"]


@pytest.mark.depends_on(
    "test_default_location_is_application_default",
    "test_config_file_location_is_user_controlled",
    "test_set_override_location_is_application_managed",
)
def test_location_projection_changes_with_source_precedence(tmp_path):
    from oslo_config import cfg
    from conftest import configured_conf

    conf, _ = configured_conf(tmp_path, "[DEFAULT]\nworkers = 4")
    assert conf.get_location("workers").location == cfg.Locations.user
    conf.set_override("workers", 9)
    assert conf.get_location("workers").location == cfg.Locations.set_override
    conf.clear_override("workers")
    assert conf.get_location("workers").location == cfg.Locations.user


@pytest.mark.depends_on(
    "test_pickled_configopts_uses_exported_state",
    "test_group_ini_values_are_typed",
)
def test_pickled_grouped_config_can_be_accessed_after_restore(tmp_path):
    import pickle
    from conftest import configured_conf

    conf, _ = configured_conf(tmp_path, "[api]\nlisten_port = 9443\nmode = admin")
    restored = pickle.loads(pickle.dumps(conf))
    assert restored.api.listen_port == 9443
    assert restored.api.mode == "admin"


@pytest.mark.depends_on(
    "test_generator_cli_writes_machine_readable_json",
    "test_generator_json_contains_option_metadata",
)
def test_generator_json_and_yaml_share_option_names(tmp_path):
    from conftest import generate_sample, load_json_sample, load_yaml_sample

    json_path, _ = generate_sample(tmp_path / "json", "json")
    yaml_path, _ = generate_sample(tmp_path / "yaml", "yaml")
    json_names = {opt["name"] for opt in load_json_sample(json_path)["options"]["api"]["opts"]}
    yaml_names = {opt["name"] for opt in load_yaml_sample(yaml_path)["options"]["api"]["opts"]}
    assert json_names == yaml_names


@pytest.mark.depends_on(
    "test_generator_cli_writes_machine_readable_yaml",
    "test_validator_cli_accepts_config_matching_opt_data",
)
def test_generated_yaml_opt_data_validates_matching_config(tmp_path):
    from conftest import generate_sample, run_module, write_ini

    opt_data, entry_root = generate_sample(tmp_path, "yaml")
    config = write_ini(tmp_path / "service.conf", "[DEFAULT]\npath = /srv/api\n[api]\nworkers = 2")
    result = run_module(
        "oslo_config.validator",
        ["--opt-data", str(opt_data), "--input-file", str(config)],
        entry_root,
    )
    assert result.returncode == 0


@pytest.mark.depends_on(
    "test_generator_cli_writes_machine_readable_yaml",
    "test_validator_cli_accepts_config_matching_opt_data",
)
def test_validator_rejects_unknown_local_option(tmp_path):
    from conftest import generate_sample, run_module, write_ini

    opt_data, entry_root = generate_sample(tmp_path, "yaml")
    config = write_ini(tmp_path / "bad.conf", "[api]\nworkers = 2\nunknown = value")
    result = run_module(
        "oslo_config.validator",
        ["--opt-data", str(opt_data), "--input-file", str(config)],
        entry_root,
    )
    assert result.returncode == 1


@pytest.mark.depends_on(
    "test_generator_cli_writes_machine_readable_yaml",
    "test_validator_cli_accepts_config_matching_opt_data",
)
def test_validator_exclude_group_ignores_dynamic_group(tmp_path):
    from conftest import generate_sample, run_module, write_ini

    opt_data, entry_root = generate_sample(tmp_path, "yaml")
    config = write_ini(tmp_path / "dynamic.conf", "[api]\nworkers = 2\n[backend-a]\nurl = local")
    result = run_module(
        "oslo_config.validator",
        ["--opt-data", str(opt_data), "--input-file", str(config), "--exclude-group", "backend-a"],
        entry_root,
    )
    assert result.returncode == 0


@pytest.mark.depends_on(
    "test_generator_cli_writes_machine_readable_json",
    "test_generator_cli_writes_ini_sample",
)
def test_generator_ini_and_json_agree_on_sample_default(tmp_path):
    from conftest import generate_sample, load_json_sample

    json_path, _ = generate_sample(tmp_path / "json", "json")
    ini_path, _ = generate_sample(tmp_path / "ini", "ini")
    api_opts = load_json_sample(json_path)["options"]["api"]["opts"]
    port = next(opt for opt in api_opts if opt["name"] == "listen-port")
    assert port["sample_default"] == "9000"
    assert "listen_port = 9000" in ini_path.read_text(encoding="utf-8")


@pytest.mark.depends_on(
    "test_generator_json_contains_option_metadata",
    "test_choice_option_rejects_unlisted_value",
)
def test_generator_records_choices_and_typed_bounds(tmp_path):
    from conftest import generate_sample, load_json_sample

    output, _ = generate_sample(tmp_path, "json")
    by_name = {opt["name"]: opt for opt in load_json_sample(output)["options"]["api"]["opts"]}
    assert by_name["mode"]["choices"] == [["public", "Public API"], ["admin", "Admin API"]]
    assert by_name["listen-port"]["min"] == 1
    assert by_name["listen-port"]["max"] == 65535


@pytest.mark.depends_on(
    "test_generator_json_contains_option_metadata",
    "test_opt_exposes_public_metadata",
)
def test_generator_records_secret_and_advanced_flags(tmp_path):
    from conftest import generate_sample, load_json_sample

    output, _ = generate_sample(tmp_path, "json")
    default_opts = {opt["name"]: opt for opt in load_json_sample(output)["options"]["DEFAULT"]["opts"]}
    api_opts = {opt["name"]: opt for opt in load_json_sample(output)["options"]["api"]["opts"]}
    assert default_opts["token"]["secret"] is True
    assert api_opts["tuning"]["advanced"] is True


@pytest.mark.depends_on(
    "test_generator_cli_writes_machine_readable_json",
    "test_opt_exposes_public_metadata",
)
def test_generator_records_deprecated_replacement_projection(tmp_path):
    from conftest import generate_sample, load_json_sample

    output, _ = generate_sample(tmp_path, "json")
    deprecated = load_json_sample(output)["deprecated_options"]["api"]
    assert deprecated == [
        {"name": "old_name", "replacement_name": "new-name", "replacement_group": "api"}
    ]


@pytest.mark.depends_on(
    "test_validator_cli_accepts_config_matching_opt_data",
    "test_generator_json_contains_option_metadata",
)
def test_validator_accepts_dest_name_for_hyphenated_option(tmp_path):
    from conftest import generate_sample, run_module, write_ini

    opt_data, entry_root = generate_sample(tmp_path, "yaml")
    config = write_ini(tmp_path / "service.conf", "[api]\nlisten_port = 9000")
    result = run_module(
        "oslo_config.validator",
        ["--opt-data", str(opt_data), "--input-file", str(config)],
        entry_root,
    )
    assert result.returncode == 0


@pytest.mark.depends_on(
    "test_generator_cli_writes_machine_readable_yaml",
    "test_validator_cli_accepts_config_matching_opt_data",
)
def test_validator_check_defaults_accepts_matching_defaults(tmp_path):
    from conftest import generate_sample, run_module, write_ini

    opt_data, entry_root = generate_sample(tmp_path, "yaml")
    config = write_ini(
        tmp_path / "defaults.conf",
        """
        [DEFAULT]
        enabled = True
        path = /srv/api
        [api]
        workers = 2
        mode = public
        tags = blue,green
        """,
    )
    result = run_module(
        "oslo_config.validator",
        ["--opt-data", str(opt_data), "--input-file", str(config), "--check-defaults"],
        entry_root,
    )
    assert result.returncode == 0


@pytest.mark.depends_on(
    "test_generator_cli_writes_machine_readable_json",
    "test_default_group_registration_projects_default_value",
)
def test_generated_defaults_can_seed_configopts_registration(tmp_path):
    from oslo_config import cfg
    from conftest import generate_sample, load_json_sample

    output, _ = generate_sample(tmp_path, "json")
    token_opt = next(
        opt for opt in load_json_sample(output)["options"]["DEFAULT"]["opts"] if opt["name"] == "token"
    )
    conf = cfg.ConfigOpts()
    conf.register_opt(cfg.StrOpt(token_opt["name"], default=token_opt["default"]))
    conf([], use_env=False)
    assert conf.token is None


@pytest.mark.depends_on(
    "test_generator_json_contains_option_metadata",
    "test_group_registration_projects_attribute_mapping",
)
def test_generated_group_metadata_matches_registered_group_access(tmp_path):
    from oslo_config import cfg
    from conftest import generate_sample, load_json_sample

    output, _ = generate_sample(tmp_path, "json")
    group_data = load_json_sample(output)["options"]["api"]
    conf = cfg.ConfigOpts()
    conf.register_group(cfg.OptGroup("api", help=group_data["help"]))
    conf.register_opt(cfg.IntOpt("workers", default=2), group="api")
    conf([], use_env=False)
    assert conf.api.workers == 2
    assert group_data["help"] == "Options for the generated local API service."


@pytest.mark.depends_on(
    "test_list_all_sections_reports_parsed_sections",
    "test_validator_cli_accepts_config_matching_opt_data",
)
def test_configopts_sections_and_validator_exclusion_agree_for_dynamic_group(tmp_path):
    from conftest import base_conf, generate_sample, run_module, write_ini

    opt_data, entry_root = generate_sample(tmp_path, "yaml")
    config = write_ini(tmp_path / "dynamic.conf", "[api]\nworkers = 2\n[extra]\nvalue = local")
    conf = base_conf()
    conf(["--config-file", str(config)], use_env=False)
    result = run_module(
        "oslo_config.validator",
        ["--opt-data", str(opt_data), "--input-file", str(config), "--exclude-group", "extra"],
        entry_root,
    )
    assert "extra" in conf.list_all_sections()
    assert result.returncode == 0


@pytest.mark.depends_on(
    "test_export_import_state_preserves_values_and_groups",
    "test_generator_cli_writes_machine_readable_json",
)
def test_state_and_generator_views_share_registered_group_names(tmp_path):
    from oslo_config import cfg
    from conftest import configured_conf, generate_sample, load_json_sample

    conf, _ = configured_conf(tmp_path / "state", "[api]\nmode = admin")
    restored = cfg.ConfigOpts.import_state(conf.export_state())
    output, _ = generate_sample(tmp_path / "generator", "json")
    assert "api" in restored.list_all_sections()
    assert "api" in load_json_sample(output)["options"]


@pytest.mark.depends_on(
    "test_generator_cli_writes_machine_readable_json",
    "test_generator_cli_writes_machine_readable_yaml",
)
def test_machine_readable_outputs_are_stable_for_same_generated_namespace(tmp_path):
    from conftest import generate_sample

    json_one, _ = generate_sample(tmp_path / "json1", "json")
    json_two, _ = generate_sample(tmp_path / "json2", "json")
    yaml_one, _ = generate_sample(tmp_path / "yaml1", "yaml")
    yaml_two, _ = generate_sample(tmp_path / "yaml2", "yaml")
    first_json = json.loads(json_one.read_text(encoding="utf-8"))
    second_json = json.loads(json_two.read_text(encoding="utf-8"))
    first_yaml = yaml_one.read_text(encoding="utf-8").replace(str(yaml_one), "<output>")
    second_yaml = yaml_two.read_text(encoding="utf-8").replace(str(yaml_two), "<output>")
    first_json["generator_options"]["output_file"] = "<output>"
    second_json["generator_options"]["output_file"] = "<output>"
    assert first_json == second_json
    assert first_yaml == second_yaml
