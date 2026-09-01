from __future__ import annotations

import threading
from pathlib import Path

import pytest

from gate_helpers import environment_file, patched_environ, write_json, write_text


def configured(prefix: str, **kwargs):
    from dynaconf import Dynaconf

    options = {"envvar_prefix": prefix, "environments": False, "settings_files": []}
    options.update(kwargs)
    return Dynaconf(**options)


def test_i01_total_source_order_and_committed_projection(tmp_path: Path):
    preload = write_text(tmp_path / "preload.toml", 'TRACE = "preload"\nPRELOAD_ONLY = 1')
    regular = write_text(tmp_path / "settings.toml", 'TRACE = "regular"\nREGULAR_ONLY = 2')
    local = write_text(tmp_path / "settings.local.toml", 'TRACE = "local"\nLOCAL_ONLY = 3')
    include = write_json(tmp_path / "include.json", {"TRACE": "include", "INCLUDE_ONLY": 4})
    with patched_environ({"S2R3I01_TRACE": "environment"}):
        value = configured(
            "S2R3I01",
            preload=[str(preload)],
            settings_files=[str(regular)],
            includes=[str(include)],
        )
        value.set("TRACE", "runtime")
        assert value.TRACE == "runtime"
        assert [value.PRELOAD_ONLY, value.REGULAR_ONLY, value.LOCAL_ONLY, value.INCLUDE_ONLY] == [1, 2, 3, 4]
        assert value.as_dict()["TRACE"] == "runtime"


def test_i02_optional_to_malformed_to_corrected_generation(tmp_path: Path):
    declaring = write_text(tmp_path / "declaring.toml", 'BASE = "kept"')
    broken = write_text(tmp_path / "matched.toml", "VALUE =")
    value = configured("S2R3I02")
    optional = value.load_file(path=str(tmp_path / "absent-*.toml"), silent=False)
    assert optional.committed and optional.resources
    with pytest.raises(Exception):
        value.load_file(path=[str(declaring), str(broken)], silent=False)
    assert value.get("BASE") is None and value.get("VALUE") is None
    write_text(broken, 'VALUE = "recovered"')
    receipt = value.load_file(path=[str(declaring), str(broken)], silent=False)
    assert receipt.committed and value.BASE == "kept" and value.VALUE == "recovered"


def test_i03_environment_process_merge_and_fallback(tmp_path: Path):
    source = write_text(
        tmp_path / "settings.toml",
        """
        [default]
        [default.SERVICE]
        HOST = "base"
        PORT = 5001
        [production]
        [production.SERVICE]
        HOST = "production"
        """,
    )
    with patched_environ(
        {
            "S2R3I03_SERVICE__PORT": "5002",
            "S2R3I03_FALLBACK": "from-process",
        }
    ):
        value = configured(
            "S2R3I03",
            environments=True,
            env="production",
            settings_files=[str(source)],
            merge_enabled=True,
            sysenv_fallback=["S2R3I03_FALLBACK"],
        )
        assert value.get("service.host") == "production"
        assert value.get("service.port") == 5002
        assert value.get("S2R3I03_FALLBACK") == "from-process"
        assert "dynaconf_merge" not in str(value.as_dict()).casefold()


def test_i04_parent_multiple_views_and_snapshot_ownership(tmp_path: Path):
    source = environment_file(tmp_path)
    parent = configured("S2R3I04", environments=True, env="alpha", settings_files=[str(source)])
    beta = parent.from_env("beta", keep=True)
    gamma = parent.from_env("gamma", keep=True)
    beta.set("LOCAL", "beta")
    gamma.set("LOCAL", "gamma")
    beta_snapshot = beta.snapshot()
    gamma_snapshot = gamma.snapshot()
    parent.setenv("delta")
    assert beta_snapshot.get("VALUE") == "beta" and beta_snapshot.get("LOCAL") == "beta"
    assert gamma_snapshot.get("VALUE") == "gamma" and gamma_snapshot.get("LOCAL") == "gamma"
    assert beta_snapshot is not gamma_snapshot
    assert beta_snapshot.snapshot_id and gamma_snapshot.snapshot_id
    assert parent.VALUE == "delta"


def test_i05_nested_environment_scopes_strict_lifo(tmp_path: Path):
    source = environment_file(tmp_path)
    value = configured("S2R3I05", environments=True, env="alpha", settings_files=[str(source)])
    value.setenv("beta")
    with value.using_env("gamma") as outer:
        assert outer is not None and outer.VALUE == "gamma"
        with value.using_env("delta") as inner:
            assert inner is not None and inner.VALUE == "delta"
        assert outer.VALUE == "gamma"
    assert value.VALUE == "beta"


def test_i06_exceptional_nested_environment_restoration(tmp_path: Path):
    source = environment_file(tmp_path)
    value = configured("S2R3I06", environments=True, env="alpha", settings_files=[str(source)])
    value.setenv("beta")
    with pytest.raises(RuntimeError, match="inner"):
        with value.using_env("gamma") as outer:
            assert outer is not None
            with value.using_env("delta") as inner:
                assert inner.VALUE == "delta"
                raise RuntimeError("inner")
    assert value.VALUE == "beta" and str(value.current_env).casefold() == "beta"


def test_i07_parent_derived_sibling_environment_owners(tmp_path: Path):
    source = environment_file(tmp_path)
    parent = configured("S2R3I07_PARENT", environments=True, env="alpha", settings_files=[str(source)])
    derived = parent.from_env("beta")
    sibling = configured("S2R3I07_SIBLING", environments=True, env="delta", settings_files=[str(source)])
    with parent.using_env("gamma") as active:
        assert active is not None and active.VALUE == "gamma"
        with derived.using_env("alpha") as derived_active:
            assert derived_active.VALUE == "alpha"
            assert sibling.VALUE == "delta"
        assert active.VALUE == "gamma" and sibling.VALUE == "delta"
    assert parent.VALUE == "alpha" and derived.VALUE == "beta" and sibling.VALUE == "delta"


def test_i08_threaded_separate_environment_owners(tmp_path: Path):
    source = environment_file(tmp_path)
    first = configured("S2R3I08_FIRST", environments=True, env="alpha", settings_files=[str(source)])
    second = configured("S2R3I08_SECOND", environments=True, env="beta", settings_files=[str(source)])
    barrier = threading.Barrier(2)
    observations: list[tuple[str, str]] = []

    def worker(settings, outer: str, inner: str) -> None:
        with settings.using_env(outer) as outer_owner:
            barrier.wait(timeout=5)
            if outer_owner is None:
                observations.append((outer, "missing-owner"))
                barrier.wait(timeout=5)
            else:
                with settings.using_env(inner) as inner_owner:
                    observations.append((outer, "missing-owner" if inner_owner is None else inner_owner.VALUE))
                    barrier.wait(timeout=5)
                observations.append((outer, outer_owner.VALUE))

    threads = [
        threading.Thread(target=worker, args=(first, "gamma", "delta")),
        threading.Thread(target=worker, args=(second, "delta", "gamma")),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
        assert not thread.is_alive()
    assert sorted(observations) == sorted([("gamma", "delta"), ("gamma", "gamma"), ("delta", "gamma"), ("delta", "delta")])
    assert first.VALUE == "alpha" and second.VALUE == "beta"


def test_i09_environment_alias_and_bound_file_changes(tmp_path: Path):
    dependency = write_text(tmp_path / "endpoint.txt", "alpha.example")
    value = configured("S2R3I09")
    value.set("PORT", 8301)
    value.bind_file("ENDPOINT", dependency, converter=lambda text: text.strip().casefold())
    value.set("ALIAS", "@get PORT", tomlfy=True)
    assert value.ENDPOINT == "alpha.example" and value.ALIAS == 8301
    write_text(dependency, "BETA.EXAMPLE")
    value.set("PORT", 8302)
    assert value.ENDPOINT == "beta.example" and value.ALIAS == 8302


def test_i10_dependency_missing_fallback_restored_and_sibling(tmp_path: Path):
    dependency = write_text(tmp_path / "payload.txt", "first")
    first = configured("S2R3I10_FIRST")
    sibling = configured("S2R3I10_SIBLING")
    first.bind_file("PAYLOAD", dependency)
    sibling.bind_file("PAYLOAD", dependency, fallback="fallback")
    assert first.PAYLOAD.strip() == sibling.PAYLOAD.strip() == "first"
    dependency.unlink()
    with pytest.raises(FileNotFoundError):
        first.get("PAYLOAD")
    assert sibling.PAYLOAD == "fallback"
    write_text(dependency, "restored")
    assert first.PAYLOAD.strip() == sibling.PAYLOAD.strip() == "restored"


def test_i11_current_validator_guard_boolean_and_details():
    from dynaconf import ValidationError, Validator

    value = configured("S2R3I11")
    value.update({"MODE": "development", "PORT": 18, "TOKEN": "svc-token"})
    value.validators.register(
        Validator("PORT", gt=10) & Validator("PORT", lt=20),
        Validator("MODE", eq="production") | Validator("MODE", eq="development"),
        Validator("TOKEN", startswith="svc"),
        Validator("TLS", eq=True, when=Validator("MODE", eq="production")),
    )
    value.validators.validate()
    value.update({"MODE": "production", "TLS": False})
    with pytest.raises(ValidationError) as error:
        value.validators.validate_all()
    assert error.value.details
    value.set("TLS", True)
    value.validators.validate_all()
