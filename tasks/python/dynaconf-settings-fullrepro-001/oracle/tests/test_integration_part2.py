from __future__ import annotations

import sys
from pathlib import Path

import pytest

from gate_helpers import environment_file, write_text


def configured(prefix: str, **kwargs):
    from dynaconf import Dynaconf

    options = {"envvar_prefix": prefix, "environments": False, "settings_files": []}
    options.update(kwargs)
    return Dynaconf(**options)


def test_i12_callable_defaults_and_ordered_casts_by_environment(tmp_path: Path):
    from dynaconf import Validator

    source = environment_file(tmp_path)
    calls: list[str] = []

    def contextual(settings, validator):
        del validator
        calls.append(str(settings.current_env).casefold())
        return "41" if str(settings.current_env).casefold() == "alpha" else "51"

    value = configured("S2R3I12", environments=True, env="alpha", settings_files=[str(source)])
    value.validators.register(Validator("DERIVED", default=contextual, cast=lambda item: int(item) + 1))
    value.validators.validate()
    assert value.DERIVED == 42
    value.setenv("beta")
    value.validators.register(Validator("SECOND", default=contextual, cast=lambda item: int(item) + 1))
    value.validators.validate()
    assert value.SECOND == 52
    assert calls[0] == "alpha" and calls[1:] and set(calls[1:]) == {"beta"}


def test_i13_multikey_validation_transaction_rolls_back_complete_generation():
    from dynaconf import ValidationError, Validator

    value = configured("S2R3I13")
    value.update({"DATABASE": {"HOST": "before", "PORT": 5001}, "MODE": "safe"})
    value.validators.register(Validator("DATABASE.PORT", gt=1000), Validator("MODE", eq="safe"))
    before = value.snapshot()
    with pytest.raises(ValidationError):
        with value.transaction(validate=True) as staged:
            staged.set("DATABASE.HOST", "attempt")
            staged.set("DATABASE.PORT", 10)
            staged.set("MODE", "unsafe")
    assert value.as_dict() == before.as_dict()
    with value.transaction(validate=True) as staged:
        staged.update({"DATABASE": {"HOST": "after", "PORT": 6001}, "MODE": "safe"})
    assert value.get("database.host") == "after" and value.get("database.port") == 6001


def test_i14_failed_transaction_provenance_then_one_commit():
    from dynaconf import ValidationError, Validator, get_history, inspect_settings

    value = configured("S2R3I14")
    value.set("PORT", 5201)
    value.validators.register(Validator("PORT", gt=1000))
    initial = inspect_settings(value, key="PORT")
    with pytest.raises(ValidationError):
        with value.transaction(validate=True) as staged:
            staged.set("PORT", 12)
    failed = inspect_settings(value, key="PORT")
    assert failed["current"] == 5201 and failed["generation"] == initial["generation"]
    with value.transaction(validate=True) as staged:
        staged.set("PORT", 6201)
    committed = inspect_settings(value, key="PORT")
    assert committed["current"] == 6201 and committed["generation"] == initial["generation"] + 1
    assert all(item["generation"] == committed["generation"] for item in get_history(value, key="PORT"))


def test_i15_fresh_reload_preserves_older_snapshot_and_runtime_peer(tmp_path: Path):
    source = write_text(tmp_path / "settings.toml", 'VALUE = "first"\nPEER = "source"')
    value = configured("S2R3I15", settings_files=[str(source)], fresh_vars=["VALUE"])
    value.set("RUNTIME", "kept")
    before = value.snapshot()
    write_text(source, 'VALUE = "second"\nPEER = "changed"')
    assert value.VALUE == "second" and value.RUNTIME == "kept"
    assert before.get("VALUE") == "first" and before.get("RUNTIME") == "kept"
    assert value.snapshot().get("VALUE") == "second"


def test_i16_corrected_explicit_source_retries_same_object(tmp_path: Path):
    source = write_text(tmp_path / "settings.toml", 'VALUE = "first"')
    value = configured("S2R3I16")
    receipt = value.load_file(path=str(source), silent=False)
    assert receipt.committed and value.VALUE == "first"
    write_text(source, "VALUE =")
    with pytest.raises(Exception):
        value.load_file(path=str(source), silent=False)
    assert value.VALUE == "first"
    write_text(source, 'VALUE = "corrected"')
    corrected = value.load_file(path=str(source), silent=False)
    assert corrected.generation > receipt.generation and value.VALUE == "corrected"


def test_i17_reload_generation_invalid_then_corrected(tmp_path: Path):
    source = write_text(tmp_path / "settings.toml", 'VALUE = "accepted"')
    value = configured("S2R3I17", settings_files=[str(source)])
    assert value.VALUE == "accepted"
    before = value.snapshot()
    write_text(source, "VALUE =")
    with pytest.raises(Exception):
        value.reload_generation(silent=False)
    assert value.VALUE == "accepted" and value.snapshot().as_dict() == before.as_dict()
    write_text(source, 'VALUE = "recovered"')
    receipt = value.reload_generation(silent=False)
    assert receipt.committed and value.VALUE == "recovered"


def test_i18_reload_generation_provenance_and_sibling_snapshot(tmp_path: Path):
    from dynaconf import inspect_settings

    source = write_text(tmp_path / "settings.toml", 'VALUE = "one"')
    value = configured("S2R3I18", settings_files=[str(source)])
    sibling = configured("S2R3I18_SIBLING", settings_files=[str(source)])
    sibling_before = sibling.snapshot()
    report_before = inspect_settings(value, key="VALUE")
    write_text(source, 'VALUE = "two"')
    receipt = value.reload_generation(silent=False)
    report_after = inspect_settings(value, key="VALUE")
    assert value.VALUE == "two" and report_after["current"] == "two"
    assert report_after["generation"] == receipt.generation > report_before["generation"]
    assert sibling_before.get("VALUE") == "one" and sibling_before.as_dict() == sibling.snapshot().as_dict()


def test_i19_discovered_constructor_decorated_hook_order(tmp_path: Path):
    root = tmp_path / "hooks"
    settings_file = write_text(
        root / "settings.py",
        """
        TRACE = "source"
        from dynaconf import post_hook

        @post_hook
        def decorated(settings):
            return {"TRACE": settings.TRACE + "|decorated"}
        """,
    )
    write_text(root / "dynaconf_hooks.py", 'def post(settings):\n    return {"TRACE": settings.TRACE + "|discovered"}')

    def constructor(settings):
        return {"TRACE": settings.TRACE + "|constructor"}

    from dynaconf import Dynaconf

    sys.modules.pop("dynaconf_hooks", None)
    try:
        value = Dynaconf(
            envvar_prefix="S2R3I19",
            root_path=str(root),
            settings_files=[str(settings_file)],
            post_hooks=[constructor],
            environments=False,
        )
        assert value.TRACE == "source|discovered|constructor|decorated"
    finally:
        sys.modules.pop("dynaconf_hooks", None)


def test_i20_discovered_hook_modules_remain_directory_local(tmp_path: Path):
    from dynaconf import Dynaconf

    results = []
    for index, label in enumerate(("first", "second", "first")):
        root = tmp_path / f"root-{index}"
        source = write_text(root / "settings.toml", f'BASE = "{label}"')
        write_text(root / "dynaconf_hooks.py", f'def post(settings):\n    return {{"HOOKED": settings.BASE + "-{label}"}}')
        sys.modules.pop("dynaconf_hooks", None)
        value = Dynaconf(
            envvar_prefix=f"S2R3I20_{index}",
            root_path=str(root),
            settings_files=[str(source)],
            environments=False,
        )
        results.append(value.HOOKED)
        sys.modules.pop("dynaconf_hooks", None)
    assert results == ["first-first", "second-second", "first-first"]


def test_i21_late_hook_failure_restores_values_and_generation():
    from dynaconf import inspect_settings

    value = configured("S2R3I21")
    value.set("BASE", "before")
    before = value.snapshot()

    def first(settings):
        return {"BASE": settings.BASE + "|first", "STAGED": 1}

    def failing(settings):
        assert settings.STAGED == 1
        raise RuntimeError("late-hook")

    with pytest.raises(RuntimeError, match="late-hook"):
        value.run_hooks([first, failing])
    assert value.as_dict() == before.as_dict()
    assert inspect_settings(value, key="BASE")["generation"] == before.generation


def test_i22_hook_failure_correction_retry_without_stale_state():
    value = configured("S2R3I22")
    value.set("TRACE", "base")

    def first(settings):
        return {"TRACE": settings.TRACE + "|first"}

    def failing(settings):
        raise LookupError("controlled")

    with pytest.raises(LookupError):
        value.run_hooks([first, failing])
    assert value.TRACE == "base"

    def corrected(settings):
        return {"TRACE": settings.TRACE + "|corrected"}

    receipt = value.run_hooks([first, corrected])
    assert receipt.committed and value.TRACE == "base|first|corrected"
