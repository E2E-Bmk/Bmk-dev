from __future__ import annotations

from importlib import metadata
from pathlib import Path

import pytest

from gate_helpers import environment_file, patched_environ, public_files, write_json, write_text


def fresh(prefix: str):
    from dynaconf import Dynaconf

    return Dynaconf(envvar_prefix=prefix, environments=False, settings_files=[])


def test_a01_public_surface_and_distribution_metadata():
    from dynaconf import (
        Dynaconf,
        LazySettings,
        ValidationError,
        Validator,
        add_converter,
        get_history,
        inspect_settings,
        post_hook,
        settings,
    )

    assert Dynaconf is LazySettings
    assert isinstance(settings, LazySettings)
    assert issubclass(ValidationError, Exception)
    assert isinstance(Validator, type)
    assert all(callable(item) for item in (add_converter, get_history, inspect_settings, post_hook))
    distribution = metadata.distribution("dynaconf")
    assert distribution.version == "3.3.0.dev0"
    entries = [item for item in distribution.entry_points if item.group == "console_scripts" and item.name == "dynaconf"]
    assert len(entries) == 1 and entries[0].value


def test_a02_independent_runtime_owners():
    first = fresh("S2R_V3_A02_FIRST")
    second = fresh("S2R_V3_A02_SECOND")
    first.set("ONLY_FIRST", {"value": 11})
    second.set("ONLY_SECOND", 12)
    assert first.get("only_first.value") == 11
    assert first.get("ONLY_SECOND") is None
    assert second.get("ONLY_SECOND") == 12
    assert second.get("ONLY_FIRST") is None


def test_a03_case_dotted_literal_and_callable_views(tmp_path: Path):
    settings_file = write_text(
        tmp_path / "settings.toml",
        """
        dynaconf_dotted_lookup = false
        "SERVICE.HOST" = "literal.example"
        [SERVICE]
        HOST = "nested.example"
        [DATABASE]
        HOST = "db.example"
        """,
    )
    from dynaconf import Dynaconf

    configured = Dynaconf(envvar_prefix="S2R_V3_A03", environments=False, settings_files=[str(settings_file)])
    assert configured.database.host == configured["database.host"] == "db.example"
    assert configured.get("SERVICE.HOST") == "nested.example"
    assert configured.get("SERVICE.HOST", dotted_lookup=False) == "literal.example"
    assert configured("database.host") == "db.example"
    assert configured.get("ABSENT", "fallback") == "fallback"
    with pytest.raises(AttributeError):
        _ = configured.S2R_V3_A03_ABSENT


def test_a04_set_update_dotted_and_dictionary_projection():
    configured = fresh("S2R_V3_A04")
    configured.update({"ALPHA": 1, "DATABASE": {"HOST": "db.local", "TLS": True}})
    configured.set("ALPHA", 2)
    configured.set("DATABASE.PORT", 5544)
    assert configured.ALPHA == configured["alpha"] == configured.get("ALPHA") == 2
    assert configured.get("database.host") == "db.local"
    assert configured.as_dict()["DATABASE"] == {"HOST": "db.local", "TLS": True, "PORT": 5544}
    assert not any(str(key).endswith("_FOR_DYNACONF") for key in configured.as_dict())


def test_a05_toml_json_python_types_and_supplied_order(tmp_path: Path):
    toml = write_text(tmp_path / "first.toml", 'PORT = 7011\nUNIQUE_TOML = true')
    json_file = write_json(tmp_path / "second.json", {"PORT": 7012, "NESTED": {"items": [1, 2]}})
    python_file = write_text(tmp_path / "third.py", 'PORT = 7013\nUPPER_ONLY = "yes"\nlower_helper = "no"')
    from dynaconf import Dynaconf

    configured = Dynaconf(
        envvar_prefix="S2R_V3_A05",
        environments=False,
        settings_files=[str(toml), str(json_file), str(python_file)],
    )
    assert configured.PORT == 7013
    assert configured.UNIQUE_TOML is True
    assert list(configured.get("nested.items")) == [1, 2]
    assert configured.UPPER_ONLY == "yes"
    assert configured.get("lower_helper") is None


def test_a06_optional_match_parse_failure_and_load_receipt(tmp_path: Path):
    valid = write_text(tmp_path / "valid.toml", 'VALUE = "accepted"')
    malformed = write_text(tmp_path / "broken.toml", "VALUE =")
    configured = fresh("S2R_V3_A06")
    assert configured.load_file(path=str(tmp_path / "missing-*.toml"), silent=False).committed
    with pytest.raises(Exception):
        configured.load_file(path=[str(valid), str(malformed)], silent=False)
    assert configured.get("VALUE") is None
    write_text(malformed, 'RECOVERED = "yes"')
    receipt = configured.load_file(path=[str(valid), str(malformed)], silent=False)
    assert receipt.committed and len(receipt.resources) == 2
    assert configured.VALUE == "accepted" and configured.RECOVERED == "yes"


def test_a07_default_global_selected_and_ordered_environments(tmp_path: Path):
    source = write_text(
        tmp_path / "envs.toml",
        """
        [default]
        COMMON = "default"
        COLLISION = "default"
        [global]
        GLOBAL_ONLY = "visible"
        [alpha]
        ALPHA_ONLY = 1
        COLLISION = "alpha"
        [beta]
        BETA_ONLY = 2
        COLLISION = "beta"
        """,
    )
    from dynaconf import Dynaconf

    configured = Dynaconf(envvar_prefix="S2R_V3_A07", environments=True, env="alpha,beta", settings_files=[str(source)])
    assert configured.COMMON == "default"
    assert configured.GLOBAL_ONLY == "visible"
    assert configured.ALPHA_ONLY == 1 and configured.BETA_ONLY == 2
    assert configured.COLLISION == "beta"


def test_a08_owned_snapshot_and_independent_derived_view(tmp_path: Path):
    source = environment_file(tmp_path)
    from dynaconf import Dynaconf

    parent = Dynaconf(envvar_prefix="S2R_V3_A08", environments=True, env="alpha", settings_files=[str(source)])
    parent.set("RUNTIME", "parent")
    child = parent.from_env("beta", keep=True)
    snapshot = child.snapshot()
    child.set("RUNTIME", "child")
    parent.setenv("gamma")
    assert snapshot.get("VALUE") == "beta"
    assert snapshot.get("RUNTIME") == "parent"
    assert snapshot.snapshot_id and snapshot.generation >= 0
    assert child.RUNTIME == "child" and parent.VALUE == "gamma"


def test_a09_prefix_selector_unknown_and_fallback_policy():
    from dynaconf import Dynaconf

    with patched_environ(
        {
            "S2R3A09_PORT": "8021",
            "S2R3A09_UNKNOWN": "hidden",
            "S2R3A09_FALLBACK": "fallback",
            "S2R3A09X_PORT": "9999",
        }
    ):
        configured = Dynaconf(
            envvar_prefix="S2R3A09",
            environments=False,
            settings_files=[],
            ignore_unknown_envvars=True,
            sysenv_fallback=["S2R3A09_FALLBACK"],
            PORT=1,
        )
        assert configured.PORT == 8021
        assert configured.get("UNKNOWN") is None
        assert configured.get("S2R3A09_FALLBACK") == "fallback"
        assert configured.get("S2R3A09X_PORT") is None


def test_a10_bound_file_dependency_re_evaluates_current_bytes(tmp_path: Path):
    dependency = write_text(tmp_path / "port.txt", "8101")
    configured = fresh("S2R_V3_A10")
    configured.bind_file("PORT", dependency, converter=lambda value: int(value.strip()))
    assert configured.PORT == 8101
    write_text(dependency, "8102")
    assert configured.get("PORT") == 8102
    dependency.unlink()
    with pytest.raises(FileNotFoundError):
        configured.get("PORT")
    write_text(dependency, "8103")
    assert configured.PORT == 8103


def test_a11_validator_relations_composition_defaults_and_details():
    from dynaconf import ValidationError, Validator

    configured = fresh("S2R_V3_A11")
    configured.update({"MODE": "prod", "PORT": 18, "LABEL": "service-api"})
    configured.validators.register(
        Validator("MODE", is_in=["prod", "dev"]),
        Validator("PORT", gt=10, lt=20),
        Validator("LABEL", startswith="service", endswith="api"),
        Validator("TOKEN", default="created"),
    )
    configured.validators.validate()
    assert configured.TOKEN == "created"
    configured.set("PORT", 30)
    with pytest.raises(ValidationError) as error:
        configured.validators.validate_all()
    assert error.value.details


def test_a12_environment_scope_returns_owner_and_restores_saved_frame(tmp_path: Path):
    source = environment_file(tmp_path)
    from dynaconf import Dynaconf

    configured = Dynaconf(envvar_prefix="S2R_V3_A12", environments=True, env="alpha", settings_files=[str(source)])
    configured.setenv("beta")
    with configured.using_env("gamma") as active:
        assert active is not None and active.VALUE == "gamma"
        active.setenv("delta")
        assert active.VALUE == "delta"
    assert configured.VALUE == "beta"
    assert str(configured.current_env).casefold() == "beta"


def test_a13_fresh_value_observes_rewritten_source(tmp_path: Path):
    source = write_text(tmp_path / "fresh.toml", 'VALUE = "first"\nSTABLE = "source"')
    from dynaconf import Dynaconf

    configured = Dynaconf(envvar_prefix="S2R_V3_A13", environments=False, settings_files=[str(source)], fresh_vars=["VALUE"])
    configured.set("RUNTIME", "kept")
    assert configured.VALUE == "first"
    write_text(source, 'VALUE = "second"\nSTABLE = "source"')
    assert configured.VALUE == "second"
    assert configured.RUNTIME == "kept"


def test_a14_constructor_hooks_order_and_marked_merge(tmp_path: Path):
    source = write_text(tmp_path / "settings.toml", '[DATABASE]\nHOST = "db.local"\nPORT = 9001')

    def first(settings):
        return {"TRACE": settings.get("TRACE", "source") + "|first"}

    def second(settings):
        return {"TRACE": settings.TRACE + "|second", "DATABASE": {"USER": "svc", "dynaconf_merge": True}}

    from dynaconf import Dynaconf

    configured = Dynaconf(envvar_prefix="S2R_V3_A14", environments=False, settings_files=[str(source)], post_hooks=[first, second])
    assert configured.TRACE == "source|first|second"
    assert configured.get("database.host") == "db.local"
    assert configured.get("database.user") == "svc"
    assert "dynaconf_merge" not in {str(key).casefold() for key in configured.as_dict()["DATABASE"]}


def test_a15_committed_generation_history_and_inspection():
    from dynaconf import get_history, inspect_settings

    configured = fresh("S2R_V3_A15")
    configured.set("VALUE", "first")
    with configured.transaction(validate=False):
        configured.set("VALUE", "second")
    report = inspect_settings(configured, key="VALUE")
    history = get_history(configured, key="VALUE")
    assert report["current"] == "second"
    assert report["committed"] is True and report["generation"] >= 1
    assert history and all(item["committed"] is True for item in history)
    assert all(item["generation"] == report["generation"] for item in history)


def test_a16_atomic_artifact_publication_receipt(tmp_path: Path):
    configured = fresh("S2R_V3_A16")
    destination = tmp_path / "bundle"
    receipt = configured.publish_artifacts(destination, {"PORT": 9101}, {"TOKEN": "secret"})
    assert receipt.committed and set(receipt.resources) == {"settings.json", ".secrets.json", ".gitignore"}
    assert public_files(destination)["settings.json"]
    assert "TOKEN" not in (destination / "settings.json").read_text(encoding="utf-8")
    assert "secret" in (destination / ".secrets.json").read_text(encoding="utf-8")
