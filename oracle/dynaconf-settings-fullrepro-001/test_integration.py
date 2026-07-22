# Spec2Repo oracle - integration tests for dynaconf-settings-fullrepro-001
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

import dynaconf
from dynaconf import Dynaconf, LazySettings, ValidationError, Validator
from dynaconf import add_converter, get_history, inspect_settings, post_hook, settings


def _write(path: Path, text: str) -> Path:
    path.write_text(textwrap.dedent(text).strip() + "\n", encoding="utf-8")
    return path


def _run_dynaconf_cli(tmp_path: Path, *args: str, env=None, input_text=None):
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "dynaconf", *args],
        cwd=tmp_path,
        env=run_env,
        text=True,
        capture_output=True,
        input=input_text,
        timeout=60,
    )


def test_envvar_overrides_file_and_casts_to_int(tmp_path, monkeypatch):
    settings_file = _write(
        tmp_path / "settings.toml",
        """
        PORT = 8000
        NAME = "from-file"
        """,
    )
    monkeypatch.setenv("TB_PORT", "9900")

    settings = Dynaconf(
        envvar_prefix="TB",
        settings_files=[str(settings_file)],
        environments=False,
    )

    assert settings.PORT == 9900
    assert isinstance(settings.PORT, int)
    assert settings.NAME == "from-file"
    assert settings.as_dict()["PORT"] == 9900


def test_local_file_overrides_base_file(tmp_path):
    base = _write(tmp_path / "settings.toml", 'COLOR = "blue"\nSIZE = "small"')
    _write(tmp_path / "settings.local.toml", 'COLOR = "green"')

    settings = Dynaconf(
        envvar_prefix="TBLOCAL",
        root_path=str(tmp_path),
        settings_files=[str(base)],
        environments=False,
    )

    assert settings.COLOR == "green"
    assert settings.SIZE == "small"


def test_includes_load_after_regular_settings(tmp_path):
    base = _write(
        tmp_path / "settings.toml",
        """
        LEVEL = "base"
        SHARED = "base"
        """,
    )
    include = _write(
        tmp_path / "included.toml",
        """
        LEVEL = "include"
        EXTRA = "included"
        """,
    )

    settings = Dynaconf(
        envvar_prefix="TBINCLUDE",
        root_path=str(tmp_path),
        settings_files=[str(base)],
        includes=[str(include)],
        environments=False,
    )

    assert settings.LEVEL == "include"
    assert settings.SHARED == "base"
    assert settings.EXTRA == "included"


def test_nested_access_as_dict_and_env_dunder_merge(tmp_path, monkeypatch):
    settings_file = _write(
        tmp_path / "settings.toml",
        """
        [database]
        host = "db.local"
        ports = [5432]
        """,
    )
    monkeypatch.setenv("TBNEST_DATABASE__ARGS__TIMEOUT", "30")

    settings = Dynaconf(
        envvar_prefix="TBNEST",
        settings_files=[str(settings_file)],
        environments=False,
    )

    assert settings.DATABASE.HOST == "db.local"
    assert settings["database.host"] == "db.local"
    assert settings.get("database.args.timeout") == 30
    assert settings.DATABASE.ARGS.TIMEOUT == 30
    assert settings.as_dict()["DATABASE"]["ARGS"]["TIMEOUT"] == 30


def test_merge_marker_combines_environment_dictionary(tmp_path, monkeypatch):
    settings_file = _write(
        tmp_path / "settings.toml",
        """
        [database]
        host = "db.local"
        [database.args]
        retries = 2
        """,
    )
    monkeypatch.setenv("TBMERGE_DATABASE", '@merge {password="secret"}')

    settings = Dynaconf(
        envvar_prefix="TBMERGE",
        settings_files=[str(settings_file)],
        environments=False,
    )

    assert settings.get("database.host") == "db.local"
    assert settings.get("database.args.retries") == 2
    assert settings.get("database.password") == "secret"
    assert "dynaconf_merge" not in settings.as_dict()["DATABASE"]


def test_environment_default_global_and_active_values(tmp_path):
    settings_file = _write(
        tmp_path / "envs.toml",
        """
        [default]
        size = "medium"
        color = "blue"
        [global]
        region = "all"
        [development]
        color = "green"
        [production]
        color = "red"
        """,
    )

    settings = Dynaconf(
        envvar_prefix="TBENV",
        settings_files=[str(settings_file)],
        environments=True,
        env="development",
    )

    assert settings.COLOR == "green"
    assert settings.SIZE == "medium"
    assert settings.REGION == "all"


def test_from_env_returns_isolated_settings_without_changing_original(tmp_path):
    settings_file = _write(
        tmp_path / "envs.toml",
        """
        [default]
        token = "base"
        [development]
        token = "dev"
        [production]
        token = "prod"
        """,
    )
    settings = Dynaconf(
        envvar_prefix="TBFROMENV",
        settings_files=[str(settings_file)],
        environments=True,
        env="development",
    )

    production = settings.from_env("production")

    assert production.TOKEN == "prod"
    assert settings.TOKEN == "dev"


def test_setenv_and_using_env_restore_active_environment(tmp_path):
    settings_file = _write(
        tmp_path / "envs.toml",
        """
        [development]
        flag = "dev"
        [production]
        flag = "prod"
        [testing]
        flag = "test"
        """,
    )
    settings = Dynaconf(
        envvar_prefix="TBSETENV",
        settings_files=[str(settings_file)],
        environments=True,
        env="development",
    )

    settings.setenv("production")
    assert settings.FLAG == "prod"
    with settings.using_env("testing"):
        assert settings.FLAG == "test"
    assert settings.FLAG == "prod"


def test_validate_on_update_rejects_invalid_runtime_value():
    settings = Dynaconf(
        envvar_prefix="TBUPDATE",
        validate_on_update=True,
        validators=[Validator("PORT", gt=1000)],
    )

    with pytest.raises(ValidationError):
        settings.set("PORT", 10)
    settings.set("PORT", 1001)

    assert settings.PORT == 1001


def test_history_and_inspect_report_file_and_env_sources(tmp_path, monkeypatch):
    settings_file = _write(tmp_path / "settings.toml", "PORT = 8000")
    monkeypatch.setenv("TBHIST_PORT", "9900")
    settings = Dynaconf(
        envvar_prefix="TBHIST",
        settings_files=[str(settings_file)],
        environments=False,
    )

    history = get_history(settings, key="PORT")
    report = inspect_settings(settings, key="PORT")

    assert report["current"] == 9900
    assert any(entry["loader"] == "toml" and entry["value"] == 8000 for entry in history)
    assert any(entry["loader"] == "env_global" and entry["value"] == 9900 for entry in history)
    assert any(entry["loader"] == "env_global" for entry in report["history"])


def test_cli_get_list_and_inspect_observe_configured_instance(tmp_path):
    _write(
        tmp_path / "settings.toml",
        """
        [default]
        PORT = 8000
        [development]
        PORT = 8100
        NAME = "api"
        [production]
        PORT = 8200
        """,
    )
    _write(
        tmp_path / "app_settings.py",
        """
        from dynaconf import Dynaconf
        settings = Dynaconf(
            envvar_prefix="TBCLI",
            settings_files=["settings.toml"],
            environments=True,
            env="development",
        )
        """,
    )

    get_dev = _run_dynaconf_cli(tmp_path, "-i", "app_settings.settings", "get", "PORT")
    get_prod = _run_dynaconf_cli(
        tmp_path,
        "-i",
        "app_settings.settings",
        "get",
        "PORT",
        "--env",
        "production",
    )
    listed = _run_dynaconf_cli(
        tmp_path, "-i", "app_settings.settings", "list", "--json"
    )
    inspected = _run_dynaconf_cli(
        tmp_path,
        "-i",
        "app_settings.settings",
        "inspect",
        "--key",
        "PORT",
        "--format",
        "json-compact",
    )

    assert get_dev.returncode == 0, get_dev.stderr
    assert get_dev.stdout.strip() == "8100"
    assert get_prod.returncode == 0, get_prod.stderr
    assert get_prod.stdout.strip() == "8200"
    assert listed.returncode == 0, listed.stderr
    assert json.loads(listed.stdout)["PORT"] == 8100
    assert inspected.returncode == 0, inspected.stderr
    assert json.loads(inspected.stdout)["current"] == 8100


def test_preload_regular_file_and_include_order(tmp_path):
    preload = _write(tmp_path / "pre.toml", 'VALUE = "pre"\nPRE = true')
    base = _write(tmp_path / "settings.toml", 'VALUE = "base"\nBASE = true')
    include = _write(tmp_path / "include.toml", 'VALUE = "include"\nINCLUDED = true')

    settings = Dynaconf(
        envvar_prefix="TBORDER",
        root_path=str(tmp_path),
        preload=[str(preload)],
        settings_file=str(base),
        includes=[str(include)],
        environments=False,
    )

    assert settings.VALUE == "include"
    assert settings.PRE is True
    assert settings.BASE is True
    assert settings.INCLUDED is True


def test_file_declared_dynaconf_include_loads_relative_file(tmp_path):
    _write(tmp_path / "child.toml", 'CHILD = "yes"')
    settings_file = _write(
        tmp_path / "settings.toml",
        """
        ROOT = "yes"
        dynaconf_include = "child.toml"
        """,
    )

    settings = Dynaconf(
        envvar_prefix="TBINFILE",
        root_path=str(tmp_path),
        settings_files=[str(settings_file)],
        environments=False,
    )

    assert settings.ROOT == "yes"
    assert settings.CHILD == "yes"


def test_settings_files_accepts_semicolon_separated_paths(tmp_path):
    first = _write(tmp_path / "first.toml", 'VALUE = "first"\nONLY_FIRST = true')
    second = _write(tmp_path / "second.toml", 'VALUE = "second"\nONLY_SECOND = true')

    settings = Dynaconf(
        envvar_prefix="TBMULTI",
        settings_files=f"{first};{second}",
        environments=False,
    )

    assert settings.VALUE == "second"
    assert settings.ONLY_FIRST is True
    assert settings.ONLY_SECOND is True


def test_python_settings_file_loads_only_uppercase_names(tmp_path):
    settings_file = _write(
        tmp_path / "settings.py",
        """
        PUBLIC_VALUE = "visible"
        private_value = "hidden"
        """,
    )

    settings = Dynaconf(
        envvar_prefix="TBPY",
        settings_files=[str(settings_file)],
        environments=False,
    )

    assert settings.PUBLIC_VALUE == "visible"
    assert settings.get("private_value") is None


def test_multiple_envvar_prefixes_are_loaded(monkeypatch):
    monkeypatch.setenv("TBPX1_ALPHA", "1")
    monkeypatch.setenv("TBPX2_BETA", "2")

    settings = Dynaconf(envvar_prefix="TBPX1,TBPX2", environments=False)

    assert settings.ALPHA == 1
    assert settings.BETA == 2


def test_unprefixed_environment_variables_can_be_settings(monkeypatch):
    monkeypatch.setenv("TBUNPREFIXED_VALUE", "42")

    settings = Dynaconf(envvar_prefix=False, environments=False)

    assert settings.TBUNPREFIXED_VALUE == 42


def test_ignore_unknown_envvars_keeps_only_preexisting_keys(tmp_path, monkeypatch):
    settings_file = _write(tmp_path / "settings.toml", "KNOWN = 1")
    monkeypatch.setenv("TBIGNORE_KNOWN", "2")
    monkeypatch.setenv("TBIGNORE_UNKNOWN", "3")

    settings = Dynaconf(
        envvar_prefix="TBIGNORE",
        settings_files=[str(settings_file)],
        ignore_unknown_envvars=True,
        environments=False,
    )

    assert settings.KNOWN == 2
    assert settings.get("UNKNOWN") is None


def test_sysenv_fallback_reads_unprefixed_missing_key(monkeypatch):
    monkeypatch.setenv("TBFALLBACK_ONLY", "visible")

    settings = Dynaconf(
        envvar_prefix="TBFALLBACK_PREFIX",
        sysenv_fallback=True,
        environments=False,
    )

    assert settings.get("TBFALLBACK_ONLY") == "visible"


def test_sysenv_fallback_list_restricts_allowed_names(monkeypatch):
    monkeypatch.setenv("TB_ALLOWED_SYS", "yes")
    monkeypatch.setenv("TB_BLOCKED_SYS", "no")

    settings = Dynaconf(
        envvar_prefix="TBNOPE",
        sysenv_fallback=["TB_ALLOWED_SYS"],
        environments=False,
    )

    assert settings.get("TB_ALLOWED_SYS") == "yes"
    assert settings.get("TB_BLOCKED_SYS") is None


def test_comma_separated_active_envs_load_in_order(tmp_path):
    settings_file = _write(
        tmp_path / "envs.toml",
        """
        [default]
        value = "default"
        [development]
        value = "development"
        dev_only = true
        [staging]
        value = "staging"
        staging_only = true
        """,
    )

    settings = Dynaconf(
        envvar_prefix="TBENVLIST",
        settings_files=[str(settings_file)],
        environments=True,
        env="development,staging",
    )

    assert settings.VALUE == "staging"
    assert settings.DEV_ONLY is True
    assert settings.STAGING_ONLY is True


def test_from_env_keep_chains_existing_values(tmp_path):
    settings_file = _write(
        tmp_path / "envs.toml",
        """
        [default]
        shared = "base"
        [development]
        dev_only = "dev"
        [production]
        prod_only = "prod"
        """,
    )
    settings = Dynaconf(
        envvar_prefix="TBKEEP",
        settings_files=[str(settings_file)],
        environments=True,
        env="development",
    )

    production = settings.from_env("production", keep=True)

    assert production.SHARED == "base"
    assert production.DEV_ONLY == "dev"
    assert production.PROD_ONLY == "prod"


def test_plain_envvar_scalar_parses_when_auto_cast_false(monkeypatch):
    monkeypatch.setenv("TBNOCAST_PORT", "9900")

    settings = Dynaconf(
        envvar_prefix="TBNOCAST",
        auto_cast=False,
        environments=False,
    )

    assert settings.PORT == 9900


def test_auto_cast_false_leaves_envvar_tokens_as_strings(monkeypatch):
    monkeypatch.setenv("TBNOCAST_MARKED", "@int 9900")

    settings = Dynaconf(
        envvar_prefix="TBNOCAST",
        auto_cast=False,
        environments=False,
    )

    assert settings.MARKED == "@int 9900"


def test_insert_token_adds_list_item_at_requested_position(tmp_path, monkeypatch):
    settings_file = _write(tmp_path / "settings.toml", 'PLUGINS = ["a", "c"]')
    monkeypatch.setenv("TBINSERT_PLUGINS", "@insert 1 b")

    settings = Dynaconf(
        envvar_prefix="TBINSERT",
        settings_files=[str(settings_file)],
        environments=False,
    )

    assert settings.PLUGINS == ["a", "b", "c"]


def test_del_token_removes_nested_envvar_value(tmp_path, monkeypatch):
    settings_file = _write(
        tmp_path / "settings.toml",
        """
        [database]
        host = "db.local"
        port = 5432
        """,
    )
    monkeypatch.setenv("TBDEL_DATABASE__PORT", "@del")

    settings = Dynaconf(
        envvar_prefix="TBDEL",
        settings_files=[str(settings_file)],
        environments=False,
    )

    assert settings.get("database.host") == "db.local"
    assert settings.get("database.port") is None


def test_global_merge_enabled_merges_later_dictionaries_and_lists(tmp_path, monkeypatch):
    settings_file = _write(
        tmp_path / "settings.toml",
        """
        [database]
        host = "db.local"
        plugins = ["file"]
        """,
    )
    monkeypatch.setenv("TBMERGEGLOBAL_DATABASE", '{password="secret", plugins=["env"]}')

    settings = Dynaconf(
        envvar_prefix="TBMERGEGLOBAL",
        settings_files=[str(settings_file)],
        merge_enabled=True,
        environments=False,
    )

    assert settings.get("database.host") == "db.local"
    assert settings.get("database.password") == "secret"
    assert "file" in settings.get("database.plugins")
    assert "env" in settings.get("database.plugins")


def test_local_file_top_level_merge_marker_merges_environment_section(tmp_path):
    _write(
        tmp_path / "settings.toml",
        """
        [default.database]
        host = "db.local"
        port = 5432
        """,
    )
    base = tmp_path / "settings.toml"
    _write(
        tmp_path / "settings.local.toml",
        """
        [default]
        dynaconf_merge = true
        [default.database]
        password = "secret"
        """,
    )

    settings = Dynaconf(
        envvar_prefix="TBLOCALMERGE",
        root_path=str(tmp_path),
        settings_files=[str(base)],
        environments=True,
        env="default",
    )

    assert settings.get("database.host") == "db.local"
    assert settings.get("database.password") == "secret"


def test_runtime_set_creates_nested_value_visible_in_all_views():
    settings = Dynaconf(envvar_prefix="TBRUNTIME", environments=False)

    settings.set("DATABASE.PORT", 5432)

    assert settings.DATABASE.PORT == 5432
    assert settings.get("database.port") == 5432
    assert settings.as_dict()["DATABASE"]["PORT"] == 5432


def test_load_file_adds_runtime_values_and_history(tmp_path):
    later = _write(tmp_path / "later.toml", "LATER = 42")
    settings = Dynaconf(envvar_prefix="TBLOADFILE", environments=False)

    settings.load_file(path=str(later))

    assert settings.LATER == 42
    assert any(entry["value"] == 42 for entry in get_history(settings, key="LATER"))


def test_load_file_env_false_loads_top_level_without_environment_sections(tmp_path):
    later = _write(
        tmp_path / "later.toml",
        """
        TOP = "top"
        [development]
        VALUE = "dev"
        """,
    )
    settings = Dynaconf(envvar_prefix="TBLOADENV", environments=True, env="development")

    settings.load_file(path=str(later), env=False)

    assert settings.get("development.value") == "dev"
    assert settings.get("top") == "top"


def test_fresh_var_reloads_source_on_access(tmp_path):
    settings_file = _write(tmp_path / "settings.toml", 'VALUE = "one"')
    settings = Dynaconf(
        envvar_prefix="TBFRESH",
        settings_files=[str(settings_file)],
        fresh_vars=["VALUE"],
        environments=False,
    )

    assert settings.VALUE == "one"
    settings_file.write_text('VALUE = "two"\n', encoding="utf-8")

    assert settings.VALUE == "two"


def test_constructor_post_hook_merges_returned_data(tmp_path):
    settings_file = _write(tmp_path / "settings.toml", 'BASE = "base"')

    def hook(settings):
        return {"HOOKED": settings.BASE + "-hook"}

    settings = Dynaconf(
        envvar_prefix="TBPOST",
        settings_files=[str(settings_file)],
        post_hooks=[hook],
        environments=False,
    )

    assert settings.HOOKED == "base-hook"


def test_dynaconf_hooks_file_contributes_post_data(tmp_path):
    _write(
        tmp_path / "dynaconf_hooks.py",
        """
        def post(settings):
            return {"HOOK_FILE_VALUE": settings.BASE + "-hook"}
        """,
    )
    settings_file = _write(tmp_path / "settings.toml", 'BASE = "base"')

    settings = Dynaconf(
        envvar_prefix="TBHOOKFILE",
        root_path=str(tmp_path),
        settings_files=[str(settings_file)],
        environments=False,
    )

    assert settings.HOOK_FILE_VALUE == "base-hook"


def test_python_settings_post_hook_runs_when_file_loads(tmp_path):
    settings_file = _write(
        tmp_path / "settings.py",
        """
        BASE = "base"
        from dynaconf import post_hook

        @post_hook
        def hook(settings):
            return {"PY_HOOK_VALUE": settings.BASE + "-py"}
        """,
    )

    settings = Dynaconf(
        envvar_prefix="TBPYHOOK",
        settings_files=[str(settings_file)],
        environments=False,
    )

    assert settings.PY_HOOK_VALUE == "base-py"


def test_cli_inspect_prints_json_report(tmp_path):
    _write(
        tmp_path / "settings.toml",
        "PORT = 8000",
    )
    _write(
        tmp_path / "app_settings.py",
        """
        from dynaconf import Dynaconf
        settings = Dynaconf(
            envvar_prefix="TBCLIINSPECT",
            settings_files=["settings.toml"],
            environments=False,
        )
        """,
    )

    proc = _run_dynaconf_cli(
        tmp_path,
        "-i",
        "app_settings.settings",
        "inspect",
        "--key",
        "PORT",
        "--format",
        "json-compact",
    )

    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["current"] == 8000


def test_constructor_option_from_environment_selects_prefix(monkeypatch):
    monkeypatch.setenv("ENVVAR_PREFIX_FOR_DYNACONF", "TBGAPOPT")
    monkeypatch.setenv("TBGAPOPT_PORT", "8123")
    configured = Dynaconf(settings_files=[], environments=False)
    assert configured.PORT == 8123


def test_settings_files_accepts_comma_separated_paths(tmp_path):
    first = _write(tmp_path / "first.toml", 'VALUE = "first"\nFIRST = true')
    second = _write(tmp_path / "second.toml", 'VALUE = "second"\nSECOND = true')
    configured = Dynaconf(
        envvar_prefix="TBGAPCOMMA",
        settings_files=f"{first},{second}",
        environments=False,
    )
    assert configured.VALUE == "second"
    assert configured.FIRST is True
    assert configured.SECOND is True


def test_json_settings_file_loads_nested_values(tmp_path):
    settings_file = _write(
        tmp_path / "settings.json",
        json.dumps({"SERVICE": {"HOST": "json.example", "PORT": 9000}}),
    )
    configured = Dynaconf(
        envvar_prefix="TBGAPJSON",
        settings_files=[str(settings_file)],
        environments=False,
    )
    assert configured.get("service.host") == "json.example"
    assert configured.get("service.port") == 9000


def test_constructor_post_hooks_accepts_single_callable(tmp_path):
    settings_file = _write(tmp_path / "settings.toml", 'BASE = "loaded"')

    def contribute(configured):
        return {"HOOK_VALUE": configured.BASE + "-single"}

    configured = Dynaconf(
        envvar_prefix="TBGAPSINGLEHOOK",
        settings_files=[str(settings_file)],
        post_hooks=contribute,
        environments=False,
    )
    assert configured.HOOK_VALUE == "loaded-single"


def test_get_history_reports_runtime_set_contribution():
    configured = Dynaconf(envvar_prefix="TBGAPHISTORY", environments=False)
    configured.set("MODE", "runtime")
    history = get_history(configured, key="MODE")
    assert any(
        entry["loader"] == "set_method" and entry["value"] == "runtime"
        for entry in history
    )


def test_inspect_settings_writes_json_report(tmp_path):
    configured = Dynaconf(envvar_prefix="TBGAPREPORT", environments=False)
    configured.set("MODE", "written")
    report_path = tmp_path / "inspection.json"
    report = inspect_settings(
        configured,
        key="MODE",
        dumper="json",
        to_file=str(report_path),
    )
    written = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["current"] == "written"
    assert written["current"] == "written"
    assert any(entry["loader"] == "set_method" for entry in written["history"])


def test_cli_init_writes_json_settings_secrets_and_gitignore(tmp_path):
    proc = _run_dynaconf_cli(
        tmp_path,
        "init",
        "--format",
        "json",
        "--vars",
        "PORT=8000",
        "--secrets",
        "TOKEN=secret",
        input_text="y\n",
    )
    assert proc.returncode == 0, proc.stderr
    settings_data = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
    secrets_data = json.loads((tmp_path / ".secrets.json").read_text(encoding="utf-8"))
    gitignore = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert str(settings_data["PORT"]) == "8000"
    assert secrets_data["TOKEN"] == "secret"
    assert ".secrets" in gitignore
