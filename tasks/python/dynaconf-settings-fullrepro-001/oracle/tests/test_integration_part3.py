from __future__ import annotations

import json
import sys
import threading
from pathlib import Path

import pytest

from gate_helpers import environment_file, patched_environ, public_files, run_module, write_json, write_text


def configured(prefix: str, **kwargs):
    from dynaconf import Dynaconf

    options = {"envvar_prefix": prefix, "environments": False, "settings_files": []}
    options.update(kwargs)
    return Dynaconf(**options)


def test_s01_multisource_derived_validation_runtime_and_inspection(tmp_path: Path):
    from dynaconf import Validator, get_history, inspect_settings

    preload = write_text(tmp_path / "preload.toml", '[default]\nBASE = "preload"\n[production]\nPORT = 7001')
    source = write_text(tmp_path / "settings.toml", '[default]\nSHARED = "base"\n[production]\nPORT = 7002\nMODE = "production"')
    include = write_json(tmp_path / "include.json", {"production": {"INCLUDED": True}})
    with patched_environ({"S2R3S01_PORT": "7003"}):
        parent = configured(
            "S2R3S01",
            environments=True,
            env="production",
            preload=[str(preload)],
            settings_files=[str(source)],
            includes=[str(include)],
        )
        parent.validators.register(Validator("PORT", gt=7000), Validator("MODE", eq="production"))
        parent.validators.validate()
        child = parent.from_env("production", keep=True)
        child.set("RUNTIME", "child")
        assert parent.PORT == child.PORT == 7003
        assert parent.BASE == "preload" and parent.INCLUDED is True
        assert parent.get("RUNTIME") is None and child.RUNTIME == "child"
        report = inspect_settings(parent, key="PORT")
        assert report["current"] == 7003 and get_history(parent, key="PORT")


def test_s02_failed_validation_then_corrected_library_artifact_generation(tmp_path: Path):
    from dynaconf import ValidationError, Validator, inspect_settings

    value = configured("S2R3S02")
    value.update({"PORT": 7101, "DATABASE": {"HOST": "before"}})
    value.validators.register(Validator("PORT", gt=7000), Validator("DATABASE.HOST", eq="after"))
    baseline = value.snapshot()
    with pytest.raises(ValidationError):
        with value.transaction(validate=True) as staged:
            staged.update({"PORT": 2, "DATABASE": {"HOST": "attempt"}})
    assert value.as_dict() == baseline.as_dict()
    with value.transaction(validate=True) as staged:
        staged.update({"PORT": 7201, "DATABASE": {"HOST": "after"}})
    destination = tmp_path / "publication"
    receipt = value.publish_artifacts(destination, value.as_dict(), {"TOKEN": "redacted"})
    assert receipt.committed and json.loads((destination / "settings.json").read_text(encoding="utf-8"))["PORT"] == 7201
    assert inspect_settings(value, key="PORT")["generation"] == value.snapshot().generation


def test_s03_valid_malformed_corrected_reload_with_snapshot_and_validation(tmp_path: Path):
    from dynaconf import Validator, inspect_settings

    source = write_text(tmp_path / "settings.toml", '[default]\nVALUE = "one"\nPORT = 7301\n[production]\nVALUE = "prod-one"')
    value = configured("S2R3S03", environments=True, env="production", settings_files=[str(source)])
    value.validators.register(Validator("PORT", gt=7000))
    value.validators.validate()
    before = value.snapshot()
    write_text(source, "[default]\nVALUE =")
    with pytest.raises(Exception):
        value.reload_generation(silent=False)
    assert value.VALUE == "prod-one" and value.snapshot().as_dict() == before.as_dict()
    write_text(source, '[default]\nVALUE = "two"\nPORT = 7302\n[production]\nVALUE = "prod-two"')
    receipt = value.reload_generation(silent=False)
    value.validators.validate()
    assert receipt.committed and value.VALUE == "prod-two" and value.PORT == 7302
    assert inspect_settings(value, key="VALUE")["generation"] == receipt.generation
    assert before.get("VALUE") == "prod-one"


def test_s04_ordered_sources_all_hook_forms_and_semantic_history(tmp_path: Path):
    from dynaconf import Dynaconf, get_history, inspect_settings

    root = tmp_path / "application"
    source = write_text(
        root / "settings.py",
        """
        TRACE = "source"
        DATABASE = {"HOST": "db.local", "PORT": 7401}
        from dynaconf import post_hook

        @post_hook
        def decorated(settings):
            return {"TRACE": settings.TRACE + "|decorated"}
        """,
    )
    write_text(root / "dynaconf_hooks.py", 'def post(settings):\n    return {"TRACE": settings.TRACE + "|discovered"}')

    def constructor(settings):
        return {"TRACE": settings.TRACE + "|constructor", "DATABASE": {"USER": "svc", "dynaconf_merge": True}}

    sys.modules.pop("dynaconf_hooks", None)
    try:
        value = Dynaconf(
            envvar_prefix="S2R3S04",
            root_path=str(root),
            settings_files=[str(source)],
            post_hooks=[constructor],
            environments=False,
        )
        assert value.TRACE == "source|discovered|constructor|decorated"
        assert value.get("database.host") == "db.local" and value.get("database.user") == "svc"
        assert inspect_settings(value, key="TRACE")["current"] == value.TRACE
        assert get_history(value, key="TRACE")
    finally:
        sys.modules.pop("dynaconf_hooks", None)


def test_s05_hook_pipeline_failure_cleanup_then_new_generation():
    from dynaconf import inspect_settings

    value = configured("S2R3S05")
    value.update({"TRACE": "base", "RESOURCE": "closed"})
    before = value.snapshot()

    def allocate(settings):
        return {"TRACE": settings.TRACE + "|allocated", "RESOURCE": "open"}

    def fail(settings):
        assert settings.RESOURCE == "open"
        raise RuntimeError("hook-failure")

    with pytest.raises(RuntimeError, match="hook-failure"):
        value.run_hooks([allocate, fail])
    assert value.as_dict() == before.as_dict()

    def finish(settings):
        return {"TRACE": settings.TRACE + "|finished", "RESOURCE": "closed"}

    receipt = value.run_hooks([allocate, finish])
    assert receipt.committed and value.TRACE == "base|allocated|finished" and value.RESOURCE == "closed"
    assert inspect_settings(value, key="TRACE")["generation"] == receipt.generation


def test_s06_artifact_bundle_late_failure_preserves_prior_generation(tmp_path: Path):
    value = configured("S2R3S06")
    destination = tmp_path / "bundle"
    value.publish_artifacts(destination, {"PORT": 7501}, {"TOKEN": "first"})
    before = public_files(destination)

    def fail(stage: Path) -> None:
        assert (stage / "settings.json").is_file() and (stage / ".secrets.json").is_file()
        raise OSError("controlled-late-failure")

    with pytest.raises(OSError, match="controlled-late-failure"):
        value.publish_artifacts(destination, {"PORT": 7502}, {"TOKEN": "second"}, before_commit=fail)
    assert public_files(destination) == before
    receipt = value.publish_artifacts(destination, {"PORT": 7503}, {"TOKEN": "third"})
    assert receipt.committed
    assert json.loads((destination / "settings.json").read_text(encoding="utf-8"))["PORT"] == 7503
    assert not list(destination.parent.glob(f".{destination.name}-stage-*"))


def test_s07_atomic_redacted_report_export_and_retry(tmp_path: Path):
    from dynaconf import ArtifactPublisher

    publisher = ArtifactPublisher()
    destination = tmp_path / "report.json"
    first = {"current": {"PORT": 7601}, "history": [{"loader": "file"}], "redacted": True}
    publisher.publish_report(destination, first)
    before = destination.read_bytes()

    def fail(stage: Path) -> None:
        assert json.loads(stage.read_text(encoding="utf-8"))["current"]["PORT"] == 7602
        raise PermissionError("replace-blocked")

    with pytest.raises(PermissionError):
        publisher.publish_report(destination, {"current": {"PORT": 7602}, "redacted": True}, before_commit=fail)
    assert destination.read_bytes() == before
    receipt = publisher.publish_report(destination, {"current": {"PORT": 7603}, "redacted": True})
    assert receipt.committed and json.loads(destination.read_text(encoding="utf-8"))["current"]["PORT"] == 7603


def test_s08_instances_snapshots_scopes_and_threads_return_to_prior_views(tmp_path: Path):
    source = environment_file(tmp_path)
    first = configured("S2R3S08_FIRST", environments=True, env="alpha", settings_files=[str(source)])
    second = configured("S2R3S08_SECOND", environments=True, env="beta", settings_files=[str(source)])
    first_snapshot = first.snapshot()
    second_snapshot = second.snapshot()
    barrier = threading.Barrier(2)
    observed: list[str] = []

    def worker(settings, env: str) -> None:
        with settings.using_env(env) as owner:
            barrier.wait(timeout=5)
            observed.append("missing-owner" if owner is None else owner.VALUE)

    threads = [threading.Thread(target=worker, args=(first, "gamma")), threading.Thread(target=worker, args=(second, "delta"))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
        assert not thread.is_alive()
    assert sorted(observed) == ["delta", "gamma"]
    assert first.VALUE == first_snapshot.get("VALUE") == "alpha"
    assert second.VALUE == second_snapshot.get("VALUE") == "beta"


def test_s09_library_fresh_process_and_export_generation_agree(tmp_path: Path):
    from dynaconf import ArtifactPublisher, inspect_settings

    source = write_text(tmp_path / "settings.toml", 'VALUE = "library"')
    value = configured("S2R3S09", settings_files=[str(source)])
    report = inspect_settings(value, key="VALUE")
    destination = tmp_path / "inspection.json"
    ArtifactPublisher().publish_report(destination, report)
    exported = json.loads(destination.read_text(encoding="utf-8"))
    process = run_module(tmp_path, "dynaconf", "--version")
    assert process.returncode == 0 and "3.3.0" in (process.stdout + process.stderr)
    assert exported["current"] == value.VALUE == "library"
    assert exported["committed"] is True and exported["generation"] == report["generation"]


def test_s10_failure_matrix_keeps_sibling_and_corrected_retries(tmp_path: Path):
    from dynaconf import ValidationError, Validator

    source = write_text(tmp_path / "settings.toml", 'VALUE = "accepted"')
    dependency = write_text(tmp_path / "dependency.txt", "payload")
    value = configured("S2R3S10", settings_files=[str(source)])
    sibling = configured("S2R3S10_SIBLING", settings_files=[str(source)])
    value.bind_file("DEPENDENCY", dependency)
    value.validators.register(Validator("PORT", gt=7000))
    baseline = value.snapshot()
    assert sibling.VALUE == "accepted"

    write_text(source, "VALUE =")
    with pytest.raises(Exception):
        value.reload_generation(silent=False)
    value.bind_file("DEPENDENCY", dependency)
    dependency.unlink()
    with pytest.raises(FileNotFoundError):
        value.get("DEPENDENCY")
    with pytest.raises(ValidationError):
        with value.transaction(validate=True) as staged:
            staged.set("PORT", 1)
    with pytest.raises(RuntimeError):
        value.run_hooks([lambda settings: {"STAGED": True}, lambda settings: (_ for _ in ()).throw(RuntimeError("hook"))])
    assert value.snapshot().as_dict() == baseline.as_dict()
    assert sibling.VALUE == "accepted"

    write_text(source, 'VALUE = "recovered"')
    write_text(dependency, "restored")
    value.reload_generation(silent=False)
    value.bind_file("DEPENDENCY", dependency)
    with value.transaction(validate=True) as staged:
        staged.set("PORT", 7701)
    value.run_hooks([lambda settings: {"HOOKED": "yes"}])
    assert value.VALUE == "recovered" and value.DEPENDENCY.strip() == "restored"
    assert value.PORT == 7701 and value.HOOKED == "yes" and sibling.VALUE == "accepted"
