from __future__ import annotations

import pickle

import pytest


def test_opt_exposes_public_metadata():
    from oslo_config import cfg

    opt = cfg.StrOpt(
        "service-name",
        dest="service_name",
        default="api",
        help="Service name.",
        secret=True,
        mutable=True,
        advanced=True,
    )
    assert opt.name == "service-name"
    assert opt.dest == "service_name"
    assert opt.default == "api"
    assert opt.help == "Service name."
    assert opt.secret is True
    assert opt.mutable is True
    assert opt.advanced is True


def test_opt_group_exposes_public_metadata():
    from oslo_config import cfg

    group = cfg.OptGroup("api", title="API options", help="API help.")
    assert group.name == "api"
    assert group.title == "API options"
    assert group.help == "API help."


def test_default_group_registration_projects_default_value():
    from oslo_config import cfg

    conf = cfg.ConfigOpts()
    assert conf.register_opt(cfg.StrOpt("name", default="aurora")) is True
    conf([], use_env=False)
    assert conf.name == "aurora"
    assert conf["name"] == "aurora"


def test_group_registration_projects_attribute_mapping():
    from oslo_config import cfg

    conf = cfg.ConfigOpts()
    conf.register_group(cfg.OptGroup("api"))
    conf.register_opt(cfg.IntOpt("workers", default=3), group="api")
    conf([], use_env=False)
    assert conf.api.workers == 3
    assert conf["api"]["workers"] == 3


def test_cli_bool_option_sets_true():
    from oslo_config import cfg

    conf = cfg.ConfigOpts()
    conf.register_cli_opt(cfg.BoolOpt("debug", default=False))
    conf(["--debug"], use_env=False)
    assert conf.debug is True


def test_cli_bool_inverse_sets_false():
    from oslo_config import cfg

    conf = cfg.ConfigOpts()
    conf.register_cli_opt(cfg.BoolOpt("enabled", default=True))
    conf(["--noenabled"], use_env=False)
    assert conf.enabled is False


def test_grouped_cli_option_uses_group_prefix():
    from oslo_config import cfg

    conf = cfg.ConfigOpts()
    conf.register_cli_opt(cfg.PortOpt("listen-port", default=8774), group="api")
    conf(["--api-listen-port", "9443"], use_env=False)
    assert conf.api.listen_port == 9443


def test_default_ini_values_are_typed(tmp_path):
    from conftest import configured_conf

    conf, _ = configured_conf(
        tmp_path,
        """
        [DEFAULT]
        name = config-name
        workers = 5
        enabled = false
        """,
    )
    assert (conf.name, conf.workers, conf.enabled) == ("config-name", 5, False)


def test_group_ini_values_are_typed(tmp_path):
    from conftest import configured_conf

    conf, _ = configured_conf(
        tmp_path,
        """
        [api]
        listen_port = 9444
        mode = admin
        """,
    )
    assert conf.api.listen_port == 9444
    assert conf.api.mode == "admin"


def test_command_line_value_precedes_config_file(tmp_path):
    from conftest import configured_conf

    conf, _ = configured_conf(
        tmp_path,
        """
        [DEFAULT]
        workers = 4
        """,
        ["--workers", "9"],
    )
    assert conf.workers == 9


def test_set_default_changes_application_default():
    from oslo_config import cfg

    conf = cfg.ConfigOpts()
    conf.register_opt(cfg.IntOpt("workers", default=2))
    conf.set_default("workers", 6)
    conf([], use_env=False)
    assert conf.workers == 6


def test_config_file_precedes_set_default(tmp_path):
    from conftest import base_conf, write_ini

    conf = base_conf()
    conf.set_default("workers", 6)
    path = write_ini(tmp_path / "sample.conf", "[DEFAULT]\nworkers = 4")
    conf(["--config-file", str(path)], use_env=False)
    assert conf.workers == 4


def test_set_override_precedes_config_file(tmp_path):
    from conftest import configured_conf

    conf, _ = configured_conf(tmp_path, "[DEFAULT]\nworkers = 4")
    conf.set_override("workers", 10)
    assert conf.workers == 10


def test_clear_override_restores_config_file_value(tmp_path):
    from conftest import configured_conf

    conf, _ = configured_conf(tmp_path, "[DEFAULT]\nworkers = 4")
    conf.set_override("workers", 10)
    conf.clear_override("workers")
    assert conf.workers == 4


def test_list_option_parses_comma_separated_ini_value(tmp_path):
    from conftest import configured_conf

    conf, _ = configured_conf(tmp_path, "[DEFAULT]\nhosts = alpha,beta,gamma")
    assert conf.hosts == ["alpha", "beta", "gamma"]


def test_dict_option_parses_key_value_ini_value(tmp_path):
    from conftest import configured_conf

    conf, _ = configured_conf(tmp_path, "[DEFAULT]\nlabels = role:api,zone:west")
    assert conf.labels == {"role": "api", "zone": "west"}


def test_multistr_option_preserves_repeated_ini_values(tmp_path):
    from conftest import configured_conf

    conf, _ = configured_conf(
        tmp_path,
        """
        [DEFAULT]
        path = /srv/one
        path = /srv/two
        """,
    )
    assert conf.path == ["/srv/one", "/srv/two"]


def test_quoted_string_option_strips_config_quotes(tmp_path):
    from conftest import configured_conf

    conf, _ = configured_conf(tmp_path, "[api]\nquoted = 'api value'")
    assert conf.api.quoted == "api value"


def test_ini_substitution_uses_previously_defined_values(tmp_path):
    from oslo_config import cfg
    from conftest import write_ini

    conf = cfg.ConfigOpts()
    conf.register_opt(cfg.StrOpt("rabbit_host"))
    conf.register_opt(cfg.PortOpt("rabbit_port"))
    conf.register_opt(cfg.ListOpt("rabbit_hosts"))
    path = write_ini(
        tmp_path / "sample.conf",
        """
        [DEFAULT]
        rabbit_host = controller
        rabbit_port = 5672
        rabbit_hosts = $rabbit_host:$rabbit_port
        """,
    )
    conf(["--config-file", str(path)], use_env=False)
    assert conf.rabbit_hosts == ["controller:5672"]


def test_required_option_missing_raises_required_opt_error():
    from oslo_config import cfg

    conf = cfg.ConfigOpts()
    conf.register_opt(cfg.StrOpt("image_id", required=True))
    with pytest.raises(cfg.RequiredOptError):
        conf([], use_env=False)


def test_port_type_rejects_value_outside_bounds():
    from oslo_config import cfg

    opt = cfg.PortOpt("api-port", min=10, max=20)
    assert opt.type("10") == 10
    with pytest.raises(ValueError):
        opt.type("21")


def test_uri_type_enforces_allowed_schemes():
    from oslo_config import cfg

    opt = cfg.URIOpt("endpoint", schemes=["https"])
    assert opt.type("https://example.test/v1") == "https://example.test/v1"
    with pytest.raises(ValueError):
        opt.type("ftp://example.test/v1")


def test_host_address_option_accepts_hostnames_and_ip_addresses():
    from oslo_config import cfg

    opt = cfg.HostAddressOpt("host")
    assert opt.type("controller.example.test") == "controller.example.test"
    assert opt.type("192.0.2.10") == "192.0.2.10"


def test_choice_option_rejects_unlisted_value():
    from oslo_config import cfg

    opt = cfg.StrOpt("mode", choices=["public", "admin"])
    assert opt.type("admin") == "admin"
    with pytest.raises(ValueError):
        opt.type("private")


def test_default_location_is_application_default():
    from oslo_config import cfg

    conf = cfg.ConfigOpts()
    conf.register_opt(cfg.StrOpt("name", default="aurora"))
    conf([], use_env=False)
    location = conf.get_location("name")
    assert location.location == cfg.Locations.opt_default
    assert location.location.is_user_controlled is False


def test_set_default_location_is_application_managed():
    from oslo_config import cfg

    conf = cfg.ConfigOpts()
    conf.register_opt(cfg.IntOpt("workers", default=2))
    conf.set_default("workers", 5)
    conf([], use_env=False)
    location = conf.get_location("workers")
    assert location.location == cfg.Locations.set_default
    assert location.location.is_user_controlled is False


def test_set_override_location_is_application_managed():
    from oslo_config import cfg

    conf = cfg.ConfigOpts()
    conf.register_opt(cfg.IntOpt("workers", default=2))
    conf([], use_env=False)
    conf.set_override("workers", 5)
    location = conf.get_location("workers")
    assert location.location == cfg.Locations.set_override
    assert location.location.is_user_controlled is False


def test_config_file_location_is_user_controlled(tmp_path):
    from oslo_config import cfg
    from conftest import write_ini

    conf = cfg.ConfigOpts()
    conf.register_opt(cfg.IntOpt("workers", default=2))
    path = write_ini(tmp_path / "sample.conf", "[DEFAULT]\nworkers = 4")
    conf(["--config-file", str(path)], use_env=False)
    location = conf.get_location("workers")
    assert location.location == cfg.Locations.user
    assert location.location.is_user_controlled is True
    assert location.detail.endswith("sample.conf")


def test_command_line_location_is_user_controlled():
    from oslo_config import cfg

    conf = cfg.ConfigOpts()
    conf.register_cli_opt(cfg.IntOpt("workers", default=2))
    conf(["--workers", "4"], use_env=False)
    location = conf.get_location("workers")
    assert location.location == cfg.Locations.command_line
    assert location.location.is_user_controlled is True
    assert location.detail == ""


def test_export_import_state_preserves_values_and_groups(tmp_path):
    from oslo_config import cfg
    from conftest import configured_conf

    conf, _ = configured_conf(tmp_path, "[DEFAULT]\nworkers = 4\n[api]\nmode = admin")
    conf.set_override("listen_port", 9443, group="api")
    restored = cfg.ConfigOpts.import_state(conf.export_state())
    assert restored.workers == 4
    assert restored.api.mode == "admin"
    assert restored.api.listen_port == 9443


def test_pickled_configopts_uses_exported_state(tmp_path):
    from conftest import configured_conf

    conf, _ = configured_conf(tmp_path, "[DEFAULT]\nname = pickled\n[api]\nlisten_port = 9443")
    restored = pickle.loads(pickle.dumps(conf))
    assert restored.name == "pickled"
    assert restored.api.listen_port == 9443


def test_list_all_sections_reports_parsed_sections(tmp_path):
    from conftest import configured_conf

    conf, _ = configured_conf(
        tmp_path,
        """
        [DEFAULT]
        name = configured
        [api]
        mode = admin
        [extra]
        value = present
        """,
    )
    assert conf.list_all_sections() == ["DEFAULT", "api", "extra"]


def test_generator_cli_writes_machine_readable_json(tmp_path):
    from conftest import generate_sample, load_json_sample

    output, _ = generate_sample(tmp_path, "json")
    data = load_json_sample(output)
    assert set(data) == {"deprecated_options", "generator_options", "options"}
    assert {"DEFAULT", "api"} <= set(data["options"])


def test_generator_json_contains_option_metadata(tmp_path):
    from conftest import generate_sample, load_json_sample

    output, _ = generate_sample(tmp_path, "json")
    api_opts = load_json_sample(output)["options"]["api"]["opts"]
    by_name = {opt["name"]: opt for opt in api_opts}
    assert by_name["listen-port"]["type"] == "port value"
    assert by_name["listen-port"]["sample_default"] == "9000"
    assert by_name["workers"]["min"] == 1
    assert by_name["workers"]["max"] == 8


def test_generator_cli_writes_machine_readable_yaml(tmp_path):
    from conftest import generate_sample, load_yaml_sample

    output, _ = generate_sample(tmp_path, "yaml")
    data = load_yaml_sample(output)
    assert data["generator_options"]["format_"] == "yaml"
    assert data["options"]["api"]["help"] == "Options for the generated local API service."


def test_generator_cli_writes_ini_sample(tmp_path):
    from conftest import generate_sample

    output, _ = generate_sample(tmp_path, "ini")
    text = output.read_text(encoding="utf-8")
    assert "[api]" in text
    assert "listen_port = 9000" in text
    assert "Advanced Option" in text


def test_validator_cli_accepts_config_matching_opt_data(tmp_path):
    from conftest import generate_sample, run_module, write_ini

    opt_data, entry_root = generate_sample(tmp_path, "yaml")
    config = write_ini(
        tmp_path / "valid.conf",
        """
        [DEFAULT]
        enabled = true
        [api]
        listen_port = 9000
        mode = admin
        """,
    )
    result = run_module(
        "oslo_config.validator",
        ["--opt-data", str(opt_data), "--input-file", str(config)],
        entry_root,
    )
    assert result.returncode == 0
