# Spec2Repo oracle - atomic tests for dynaconf-settings-fullrepro-001
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


def _run_dynaconf_cli(tmp_path: Path, *args: str, env=None):
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "dynaconf", *args],
        cwd=tmp_path,
        env=run_env,
        text=True,
        capture_output=True,
        timeout=20,
    )


def test_validator_default_and_cast_mutate_visible_state():
    settings = Dynaconf(
        envvar_prefix="TBVALID",
        validators=[
            Validator("PORT", default="8000", cast=int, gt=1024),
            Validator("SERVICE", default="api"),
        ],
    )

    settings.validators.validate()

    assert settings.PORT == 8000
    assert isinstance(settings.PORT, int)
    assert settings.SERVICE == "api"


def test_validate_all_accumulates_multiple_validation_errors():
    settings = Dynaconf(envvar_prefix="TBVALIDALL")
    settings.validators.register(
        Validator("PORT", must_exist=True),
        Validator("SERVICE", must_exist=True),
    )

    with pytest.raises(ValidationError) as exc_info:
        settings.validators.validate_all()

    details = getattr(exc_info.value, "details", [])
    assert len(details) >= 2


def test_custom_converter_composes_with_format_token(tmp_path, monkeypatch):
    monkeypatch.setenv("TBCONV_CHILD", "branch")
    settings_file = _write(
        tmp_path / "settings.toml",
        """
        DESTINATION = "@path @format {env[TBCONV_CHILD]}/leaf"
        """,
    )
    add_converter("path", Path)

    settings = Dynaconf(
        envvar_prefix="TBCONV",
        settings_files=[str(settings_file)],
        environments=False,
    )

    assert settings.DESTINATION == Path("branch/leaf")


def test_builtin_cast_tokens_from_file(tmp_path):
    settings_file = _write(
        tmp_path / "settings.toml",
        """
        PORT = "@int 8080"
        ENABLED = "@bool true"
        PAYLOAD = '@json {"name": "api", "ports": [1, 2]}'
        NOTHING = "@none"
        """,
    )

    settings = Dynaconf(
        envvar_prefix="TBCAST",
        settings_files=[str(settings_file)],
        environments=False,
    )

    assert settings.PORT == 8080
    assert settings.ENABLED is True
    assert settings.PAYLOAD == {"name": "api", "ports": [1, 2]}
    assert settings.NOTHING is None


def test_get_token_reads_another_setting_and_casts_default(tmp_path):
    settings_file = _write(
        tmp_path / "settings.toml",
        """
        SOURCE = 42
        ALIAS = "@get SOURCE"
        FALLBACK = "@get MISSING 7"
        """,
    )

    settings = Dynaconf(
        envvar_prefix="TBGET",
        settings_files=[str(settings_file)],
        environments=False,
    )

    assert settings.ALIAS == 42
    assert settings.FALLBACK == "7"


def test_read_file_token_reads_relative_file(tmp_path):
    _write(tmp_path / "secret.txt", "token-value")
    secret_path = (tmp_path / "secret.txt").as_posix()
    settings_file = _write(
        tmp_path / "settings.toml",
        f'SECRET = "@read_file {secret_path}"',
    )

    settings = Dynaconf(
        envvar_prefix="TBREAD",
        root_path=str(tmp_path),
        settings_files=[str(settings_file)],
        environments=False,
    )

    assert settings.SECRET.strip() == "token-value"


def test_string_utility_tokens_transform_values(tmp_path):
    settings_file = _write(
        tmp_path / "settings.toml",
        """
        UPPER = "@upper api"
        LOWER = "@lower API"
        STRIPPED = "@strip   padded   "
        SPLIT = "@split red green blue"
        """,
    )

    settings = Dynaconf(
        envvar_prefix="TBSTR",
        settings_files=[str(settings_file)],
        environments=False,
    )

    assert settings.UPPER == "API"
    assert settings.LOWER == "api"
    assert settings.STRIPPED == "padded"
    assert settings.SPLIT == ["red", "green", "blue"]


def test_runtime_update_validate_true_raises_first_error():
    settings = Dynaconf(
        envvar_prefix="TBUPDTRUE",
        validators=[Validator("PORT", gt=1000)],
        environments=False,
    )

    with pytest.raises(ValidationError):
        settings.update({"PORT": 10}, validate=True)


def test_validator_apply_default_on_none_sets_none_value():
    settings = Dynaconf(
        envvar_prefix="TBDEFNONE",
        VALUE=None,
        validators=[Validator("VALUE", default="fallback")],
        apply_default_on_none=True,
        environments=False,
    )

    settings.validators.validate()

    assert settings.VALUE == "fallback"


def test_validator_or_and_and_composition():
    settings = Dynaconf(
        envvar_prefix="TBCOMPOSE",
        MODE="dev",
        PORT=15,
        environments=False,
    )
    settings.validators.register(
        Validator("MODE", eq="prod") | Validator("MODE", eq="dev"),
        Validator("PORT", gt=10) & Validator("PORT", lt=20),
    )

    settings.validators.validate()

    assert settings.MODE == "dev"
    assert settings.PORT == 15


def test_validator_callable_default_can_read_settings_context():
    settings = Dynaconf(
        envvar_prefix="TBCALLDEF",
        HOST="example.test",
        environments=False,
    )
    settings.validators.register(
        Validator("URL", default=lambda settings, validator: "https://" + settings.HOST)
    )

    settings.validators.validate()

    assert settings.URL == "https://example.test"


def test_validator_casts_are_ordered_and_mutate_state():
    settings = Dynaconf(
        envvar_prefix="TBCASTVALID",
        PORT="8000",
        environments=False,
    )
    settings.validators.register(
        Validator("PORT", cast=int),
        Validator("PORT", cast=lambda value: value + 1),
    )

    settings.validators.validate()

    assert settings.PORT == 8001


def test_cli_get_missing_key_without_default_returns_nonzero(tmp_path):
    _write(
        tmp_path / "app_settings.py",
        """
        from dynaconf import Dynaconf
        settings = Dynaconf(envvar_prefix="TBCLIMISS", environments=False)
        """,
    )

    proc = _run_dynaconf_cli(tmp_path, "-i", "app_settings.settings", "get", "MISSING")

    assert proc.returncode == 1


def test_cli_get_missing_key_with_default_prints_default(tmp_path):
    _write(
        tmp_path / "app_settings.py",
        """
        from dynaconf import Dynaconf
        settings = Dynaconf(envvar_prefix="TBCLIDEF", environments=False)
        """,
    )

    proc = _run_dynaconf_cli(
        tmp_path,
        "-i",
        "app_settings.settings",
        "get",
        "MISSING",
        "--default",
        "fallback",
    )

    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "fallback"
