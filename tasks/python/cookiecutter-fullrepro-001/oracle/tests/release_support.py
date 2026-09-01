from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
import threading

from tests.support import GATE, api, assert_raises, candidate_root, file_tree, isolated_environment, make_template, process_env, workspace, write_config


def _surface():
    from cookiecutter.release import ArtifactCatalog, ChannelRegistry

    return ArtifactCatalog, ChannelRegistry


def _project(root: Path, name: str = "project", body: bytes = b"body-one") -> Path:
    project = root / name
    (project / "docs").mkdir(parents=True)
    (project / "docs" / "guide.txt").write_bytes(body)
    (project / "meta.json").write_text(json.dumps({"name": name, "rank": 17}), encoding="utf-8")
    return project


def _catalog(root: Path):
    ArtifactCatalog, _ = _surface()
    return ArtifactCatalog(root / "catalog")


def _registry(root: Path, catalog):
    _, ChannelRegistry = _surface()
    return ChannelRegistry(root / "channels", catalog)


def _managed_template(root: Path, *, value: str = "first", hook: str | None = None) -> tuple[Path, Path, Path, Path]:
    hooks = {"post_gen_project.py": hook} if hook is not None else None
    template = make_template(
        root / "managed-template",
        {"slug":"managed-project","value":value,"_publish_channel":"preview/blue"},
        {"{{cookiecutter.slug}}/value.txt":"{{cookiecutter.value}}","{{cookiecutter.slug}}/fixed.bin":b"\x00managed\xff"},
        hooks,
    )
    replay_dir = root / "replays"
    catalog_dir = root / "artifact-catalog"
    registry_dir = root / "channel-registry"
    config = write_config(
        root / "config.yml",
        replay_dir,
        artifact_catalog_dir=catalog_dir,
        publication_registry_dir=registry_dir,
    )
    return template, config, catalog_dir, registry_dir


def _managed_generate(root: Path, template: Path, config: Path, value: str, *, overwrite: bool = False) -> Path:
    with isolated_environment(root):
        return Path(api()(
            str(template),
            no_input=True,
            extra_context={"value": value},
            overwrite_if_exists=overwrite,
            output_dir=str(root / "output"),
            config_file=str(config),
        ))


def _a21_catalog_seal_inspect() -> None:
    with workspace() as root:
        catalog = _catalog(root)
        record = catalog.seal(_project(root), context={"flavor":"cobalt","rank":17}, owner="owner-a")
        observed = catalog.inspect(record.artifact_id)
        assert len(record.artifact_id) == 64
        assert observed == record and record.owner == "owner-a"
        assert record.file_count == 2 and record.total_bytes > 10
        assert catalog.list_artifacts() == [record]


def _a22_catalog_restore() -> None:
    with workspace() as root:
        source = _project(root, body=b"sealed\x00bytes")
        original = file_tree(source)
        catalog = _catalog(root)
        record = catalog.seal(source, context={"edition":"north"}, owner="owner-b")
        (source / "docs" / "guide.txt").write_bytes(b"changed")
        restored = Path(catalog.restore(record.artifact_id, root / "restored"))
        assert file_tree(restored) == original
        (restored / "docs" / "guide.txt").write_bytes(b"local-change")
        assert catalog.inspect(record.artifact_id) == record


def _a23_channel_activation() -> None:
    with workspace() as root:
        catalog = _catalog(root)
        artifact = catalog.seal(_project(root), context={"release":"one"}, owner="builder")
        registry = _registry(root, catalog)
        assert registry.current("stable") is None
        reservation = registry.reserve("stable", artifact.artifact_id, expected_epoch=0, owner="publisher")
        assert reservation.base_epoch == 0 and reservation.next_epoch == 1
        committed = registry.commit(reservation)
        assert committed.epoch == 1 and committed.artifact_id == artifact.artifact_id
        assert registry.current("stable") == committed


def _a24_channel_abort() -> None:
    from cookiecutter import exceptions

    with workspace() as root:
        catalog = _catalog(root)
        artifact = catalog.seal(_project(root), context={"release":"abort"}, owner="builder")
        registry = _registry(root, catalog)
        reservation = registry.reserve("candidate", artifact.artifact_id, expected_epoch=0, owner="publisher")
        registry.abort(reservation)
        assert registry.current("candidate") is None and registry.history("candidate") == []
        assert_raises(exceptions.ChannelConflictException, registry.abort, reservation)


def _i29_catalog_deduplication() -> None:
    with workspace() as root:
        catalog = _catalog(root)
        first = catalog.seal(_project(root, "one"), context={"track":"same"}, owner="one")
        second_source = _project(root, "two")
        (second_source / "meta.json").write_text(json.dumps({"name":"one","rank":17}), encoding="utf-8")
        second = catalog.seal(second_source, context={"track":"same"}, owner="two")
        assert first.artifact_id == second.artifact_id
        (second_source / "docs" / "guide.txt").write_bytes(b"different")
        third = catalog.seal(second_source, context={"track":"same"}, owner="two")
        assert third.artifact_id != first.artifact_id and len(catalog.list_artifacts()) == 2


def _i30_restore_conflict_preserves_destination() -> None:
    from cookiecutter import exceptions

    with workspace() as root:
        catalog = _catalog(root)
        artifact = catalog.seal(_project(root), context={"track":"conflict"}, owner="builder")
        destination = _project(root, "destination", b"user-bytes")
        before = file_tree(destination)
        assert_raises(exceptions.ArtifactConflictException, catalog.restore, artifact.artifact_id, destination)
        assert file_tree(destination) == before
        catalog.restore(artifact.artifact_id, destination, overwrite=True)
        assert (destination / "docs" / "guide.txt").read_bytes() == b"body-one"


def _i31_context_partitions_artifact_identity() -> None:
    with workspace() as root:
        source = _project(root)
        catalog = _catalog(root)
        first = catalog.seal(source, context={"region":"east"}, owner="builder")
        second = catalog.seal(source, context={"region":"west"}, owner="builder")
        assert first.artifact_id != second.artifact_id
        assert first.context_digest != second.context_digest
        assert file_tree(Path(catalog.restore(first.artifact_id, root / "east"))) == file_tree(Path(catalog.restore(second.artifact_id, root / "west")))


def _i32_concurrent_seal_converges() -> None:
    with workspace() as root:
        source = _project(root)
        catalog = _catalog(root)
        results = []
        failures = []

        def seal(owner: str) -> None:
            try:
                results.append(catalog.seal(source, context={"lane":"shared"}, owner=owner))
            except BaseException as exc:
                failures.append(exc)

        threads = [threading.Thread(target=seal, args=(owner,)) for owner in ("alpha", "beta")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=8)
        assert not failures and all(not thread.is_alive() for thread in threads)
        assert len(results) == 2 and results[0].artifact_id == results[1].artifact_id
        assert len(catalog.list_artifacts()) == 1


def _i33_channel_compare_and_swap() -> None:
    from cookiecutter import exceptions

    with workspace() as root:
        catalog = _catalog(root)
        one = catalog.seal(_project(root, "one"), context={"version":1}, owner="builder")
        two = catalog.seal(_project(root, "two", b"version-two"), context={"version":2}, owner="builder")
        registry = _registry(root, catalog)
        registry.commit(registry.reserve("stable", one.artifact_id, expected_epoch=0, owner="publisher"))
        assert_raises(exceptions.ChannelConflictException, registry.reserve, "stable", two.artifact_id, expected_epoch=0, owner="stale-writer")
        assert registry.current("stable").artifact_id == one.artifact_id


def _i34_reservation_binding_and_single_use() -> None:
    from cookiecutter import exceptions

    with workspace() as root:
        catalog = _catalog(root)
        artifact = catalog.seal(_project(root), context={"version":3}, owner="builder")
        registry = _registry(root, catalog)
        reservation = registry.reserve("edge", artifact.artifact_id, expected_epoch=0, owner="owner-one")
        borrowed = replace(reservation, owner="owner-two")
        assert_raises(exceptions.ChannelConflictException, registry.commit, borrowed)
        committed = registry.commit(reservation)
        assert committed.owner == "owner-one"
        assert_raises(exceptions.ChannelConflictException, registry.commit, reservation)


def _i35_stale_reservation_recovery() -> None:
    with workspace() as root:
        catalog = _catalog(root)
        artifact = catalog.seal(_project(root), context={"version":4}, owner="builder")
        registry_root = root / "channels"
        script = f"""
import os,sys
sys.path.insert(0, {str(GATE)!r})
sys.path.insert(1, {str(candidate_root())!r})
if os.environ.get('COOKIECUTTER_SYNTHETIC_PROFILE'):
 from reference_patch import apply
 apply()
from cookiecutter.release import ArtifactCatalog,ChannelRegistry
catalog=ArtifactCatalog({str(root / 'catalog')!r})
registry=ChannelRegistry({str(registry_root)!r},catalog)
registry.reserve('nightly',{artifact.artifact_id!r},expected_epoch=0,owner='departed')
"""
        process = subprocess.run([sys.executable, "-c", script], cwd=root, env=process_env(root), text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=12, check=False)
        assert process.returncode == 0, process.stdout + process.stderr
        _, ChannelRegistry = _surface()
        restarted = ChannelRegistry(registry_root, catalog)
        assert restarted.recover() == 1 and restarted.current("nightly") is None
        state = restarted.commit(restarted.reserve("nightly", artifact.artifact_id, expected_epoch=0, owner="replacement"))
        assert state.epoch == 1 and state.owner == "replacement"


def _i36_channel_history_and_rollback() -> None:
    with workspace() as root:
        catalog = _catalog(root)
        first = catalog.seal(_project(root, "one"), context={"version":1}, owner="builder")
        second = catalog.seal(_project(root, "two", b"version-two"), context={"version":2}, owner="builder")
        registry = _registry(root, catalog)
        registry.commit(registry.reserve("stable", first.artifact_id, expected_epoch=0, owner="one"))
        registry.commit(registry.reserve("stable", second.artifact_id, expected_epoch=1, owner="two"))
        restored = registry.rollback("stable", first.artifact_id, expected_epoch=2, owner="rollback")
        history = registry.history("stable")
        assert [item.epoch for item in history] == [1, 2, 3]
        assert restored.epoch == 3 and restored.artifact_id == first.artifact_id
        assert restored.parent_artifact_id == second.artifact_id


def _s09_managed_generation_consistency() -> None:
    with workspace() as root:
        template, config, catalog_dir, registry_dir = _managed_template(root)
        result = _managed_generate(root, template, config, "lapis")
        ArtifactCatalog, ChannelRegistry = _surface()
        catalog = ArtifactCatalog(catalog_dir)
        registry = ChannelRegistry(registry_dir, catalog)
        state = registry.current("preview/blue")
        replay = json.loads((root / "replays" / "managed-template.json").read_text(encoding="utf-8"))
        publication = replay["_cookiecutter_publication"]
        restored = Path(catalog.restore(state.artifact_id, root / "restored"))
        assert state.epoch == 1 and publication["artifact_id"] == state.artifact_id
        assert publication["epoch"] == state.epoch and publication["channel"] == state.channel
        assert file_tree(restored) == file_tree(result)
        assert replay["cookiecutter"]["value"] == (result / "value.txt").read_text(encoding="utf-8") == "lapis"


def _s10_failed_generation_does_not_activate() -> None:
    from cookiecutter import exceptions

    with workspace() as root:
        template, config, catalog_dir, registry_dir = _managed_template(root)
        result = _managed_generate(root, template, config, "committed")
        old_tree = file_tree(result)
        replay_path = root / "replays" / "managed-template.json"
        old_replay = replay_path.read_bytes()
        (template / "hooks").mkdir(exist_ok=True)
        (template / "hooks" / "post_gen_project.py").write_text("raise SystemExit(29)\n", encoding="utf-8")
        with isolated_environment(root):
            assert_raises(exceptions.FailedHookException, api(), str(template), no_input=True, extra_context={"value":"rejected"}, overwrite_if_exists=True, output_dir=str(root / "output"), config_file=str(config))
        ArtifactCatalog, ChannelRegistry = _surface()
        catalog = ArtifactCatalog(catalog_dir)
        state = ChannelRegistry(registry_dir, catalog).current("preview/blue")
        assert state.epoch == 1 and len(catalog.list_artifacts()) == 1
        assert file_tree(result) == old_tree and replay_path.read_bytes() == old_replay


def _s11_channel_conflict_rolls_back_generation() -> None:
    from cookiecutter import exceptions

    with workspace() as root:
        template, config, catalog_dir, registry_dir = _managed_template(root)
        result = _managed_generate(root, template, config, "committed")
        old_tree = file_tree(result)
        replay_path = root / "replays" / "managed-template.json"
        old_replay = replay_path.read_bytes()
        ready, release = root / "hook-ready", root / "hook-release"
        (template / "hooks").mkdir(exist_ok=True)
        (template / "hooks" / "post_gen_project.py").write_text(
            f"from pathlib import Path\nimport time\nPath({str(ready)!r}).write_text('ready')\nwhile not Path({str(release)!r}).exists(): time.sleep(0.02)\n",
            encoding="utf-8",
        )
        failures = []

        def generate_conflicting() -> None:
            try:
                _managed_generate(root, template, config, "candidate", overwrite=True)
            except BaseException as exc:
                failures.append(exc)

        thread = threading.Thread(target=generate_conflicting)
        thread.start()
        deadline = __import__("time").monotonic() + 8
        while not ready.exists() and __import__("time").monotonic() < deadline:
            threading.Event().wait(0.02)
        assert ready.exists()
        try:
            ArtifactCatalog, ChannelRegistry = _surface()
            catalog = ArtifactCatalog(catalog_dir)
            registry = ChannelRegistry(registry_dir, catalog)
            competing = catalog.seal(_project(root, "competing", b"competing"), context={"value":"competing"}, owner="other-builder")
            registry.commit(registry.reserve("preview/blue", competing.artifact_id, expected_epoch=1, owner="other-publisher"))
        finally:
            release.write_text("go", encoding="utf-8")
            thread.join(timeout=10)
        assert not thread.is_alive() and len(failures) == 1 and isinstance(failures[0], exceptions.ChannelConflictException)
        assert registry.current("preview/blue").artifact_id == competing.artifact_id
        assert file_tree(result) == old_tree and replay_path.read_bytes() == old_replay


def _s12_committed_activation_recovery() -> None:
    with workspace() as root:
        template, config, catalog_dir, registry_dir = _managed_template(root)
        _managed_generate(root, template, config, "base")
        script = f"""
import os,sys
from pathlib import Path
sys.path.insert(0, {str(GATE)!r})
sys.path.insert(1, {str(candidate_root())!r})
if os.environ.get('COOKIECUTTER_SYNTHETIC_PROFILE'):
 from reference_patch import apply
 apply()
real_replace=os.replace
def crash_after_channel(source,destination):
 result=real_replace(source,destination)
 if Path(destination).parent.name == 'channels': os._exit(92)
 return result
os.replace=crash_after_channel
from cookiecutter.main import cookiecutter
cookiecutter({str(template)!r},no_input=True,extra_context={{'value':'committed-before-crash'}},overwrite_if_exists=True,output_dir={str(root / 'output')!r},config_file={str(config)!r})
"""
        process = subprocess.run([sys.executable, "-c", script], cwd=root, env=process_env(root), text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=20, check=False)
        assert process.returncode == 92, process.stdout + process.stderr
        ArtifactCatalog, ChannelRegistry = _surface()
        catalog = ArtifactCatalog(catalog_dir)
        registry = ChannelRegistry(registry_dir, catalog)
        state = registry.current("preview/blue")
        replay_path = root / "replays" / "managed-template.json"
        replay = json.loads(replay_path.read_text(encoding="utf-8"))
        assert state.epoch == 2 and replay["_cookiecutter_publication"]["artifact_id"] == state.artifact_id
        assert (root / "output" / "managed-project" / "value.txt").read_text(encoding="utf-8") == "committed-before-crash"
        result = _managed_generate(root, template, config, "after-recovery", overwrite=True)
        final = registry.current("preview/blue")
        assert final.epoch == 3 and (result / "value.txt").read_text(encoding="utf-8") == "after-recovery"


ATOMIC = {
    "A21": _a21_catalog_seal_inspect,
    "A22": _a22_catalog_restore,
    "A23": _a23_channel_activation,
    "A24": _a24_channel_abort,
}


COMPOSITION = {
    "I29": _i29_catalog_deduplication,
    "I30": _i30_restore_conflict_preserves_destination,
    "I31": _i31_context_partitions_artifact_identity,
    "I32": _i32_concurrent_seal_converges,
    "I33": _i33_channel_compare_and_swap,
    "I34": _i34_reservation_binding_and_single_use,
    "I35": _i35_stale_reservation_recovery,
    "I36": _i36_channel_history_and_rollback,
    "S09": _s09_managed_generation_consistency,
    "S10": _s10_failed_generation_does_not_activate,
    "S11": _s11_channel_conflict_rolls_back_generation,
    "S12": _s12_committed_activation_recovery,
}


def atomic_release(root_id: str) -> None:
    ATOMIC[root_id]()


def composition_release(root_id: str) -> None:
    COMPOSITION[root_id]()
