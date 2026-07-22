# Spec2Repo oracle - atomic tests for dynaconf-settings-fullrepro-001
from pathlib import Path

import pytest

from dynaconf import Dynaconf, LazySettings, ValidationError, Validator
from dynaconf import add_converter, get_history, inspect_settings, post_hook, settings

from conftest import _write, _run_dynaconf_cli


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
        FALLBACK = "@get MISSING fallback-value"
        """,
    )

    settings = Dynaconf(
        envvar_prefix="TBGET",
        settings_files=[str(settings_file)],
        environments=False,
    )

    assert settings.ALIAS == 42
    assert settings.FALLBACK == "fallback-value"


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
        validators=[Validator("VALUE", default="fallback")],
        apply_default_on_none=True,
        environments=False,
    )
    settings.set("VALUE", None)

    settings.validators.validate()

    assert settings.VALUE == "fallback"


def test_validator_or_and_and_composition():
    settings = Dynaconf(
        envvar_prefix="TBCOMPOSE",
        environments=False,
    )
    settings.update({"MODE": "dev", "PORT": 15})
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
        environments=False,
    )
    settings.set("HOST", "example.test")
    settings.validators.register(
        Validator("URL", default=lambda settings, validator: "https://" + settings.HOST)
    )

    settings.validators.validate()

    assert settings.URL == "https://example.test"


def test_validator_casts_are_ordered_and_mutate_state():
    settings = Dynaconf(
        envvar_prefix="TBCASTVALID",
        environments=False,
    )
    settings.set("PORT", "8000")
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


def test_public_dynaconf_constructor_supports_runtime_state():
    configured = Dynaconf(envvar_prefix="TBGAPDYNA", environments=False)
    configured.set("PUBLIC_VALUE", 11)
    assert configured.get("PUBLIC_VALUE") == 11


def test_public_lazysettings_constructor_supports_runtime_state():
    configured = LazySettings(envvar_prefix="TBGAPLAZY", environments=False)
    configured.set("PUBLIC_VALUE", 12)
    assert configured.get("PUBLIC_VALUE") == 12


def test_public_global_settings_object_supports_runtime_state():
    settings.set("TBGAP_GLOBAL_PUBLIC_VALUE", 13)
    assert settings.get("TBGAP_GLOBAL_PUBLIC_VALUE") == 13


def test_settings_object_call_reads_dotted_value():
    configured = Dynaconf(envvar_prefix="TBGAPCALL", environments=False)
    configured.set("DATABASE", {"HOST": "call.example"})
    assert configured("database.host") == "call.example"


def test_get_without_dotted_lookup_reads_literal_dot_key(tmp_path):
    settings_file = _write(
        tmp_path / "settings.toml",
        """
        dynaconf_dotted_lookup = false
        "SERVICE.HOST" = "literal.example"
        [SERVICE]
        HOST = "nested.example"
        """,
    )
    configured = Dynaconf(
        envvar_prefix="TBGAPLITERAL",
        settings_files=[str(settings_file)],
        environments=False,
    )
    assert configured.get("SERVICE.HOST") == "nested.example"
    assert configured.get("SERVICE.HOST", dotted_lookup=False) == "literal.example"


def test_validator_is_type_of_rejects_wrong_type():
    configured = Dynaconf(envvar_prefix="TBISTYPE", environments=False)
    configured.set("PORT", "not-a-number")
    configured.validators.register(Validator("PORT", is_type_of=int))

    with pytest.raises(ValidationError):
        configured.validators.validate()


def test_validator_when_conditional_activates_on_matching_condition():
    configured = Dynaconf(envvar_prefix="TBWHEN", environments=False)
    configured.update({"MODE": "prod", "DEBUG": True})
    configured.validators.register(
        Validator("DEBUG", eq=False, when=Validator("MODE", eq="prod"))
    )

    with pytest.raises(ValidationError):
        configured.validators.validate()
