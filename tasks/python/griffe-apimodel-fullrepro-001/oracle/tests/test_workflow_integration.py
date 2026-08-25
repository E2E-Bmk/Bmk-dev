from __future__ import annotations

import shutil
import threading

import pytest

from griffe import (
    AnalysisWorkspace,
    ArtifactPublisher,
    CompatibilityLedger,
    ConflictError,
    ExtensionPipeline,
    OwnershipError,
    PrerequisiteError,
    ReceiptClosure,
    SnapshotStore,
)

from .workflow_support import (
    AddMarker,
    FailAfterMarker,
    RemoveCall,
    admit,
    admit_snapshot,
    package_source,
    second_revision,
)


def test_i07_workspace_reopen_preserves_detached_graph_and_revision(tmp_path) -> None:
    workspace, revision, _ = admit(tmp_path)
    first = workspace.open(revision)
    first["local_only"] = first["call"]
    reopened = AnalysisWorkspace(tmp_path / "workspace")
    second = reopened.open(revision)
    assert reopened.current(revision.package) == revision
    assert "local_only" not in second.members
    assert second["call"].parent is second


def test_i08_competing_operation_identity_commits_once(tmp_path) -> None:
    first_source = package_source(tmp_path / "first", "race_api", "value = 1\n")
    second_source = package_source(tmp_path / "second", "race_api", "value = 2\n")
    workspace = AnalysisWorkspace(tmp_path / "workspace")
    barrier = threading.Barrier(2)
    successes = []
    failures = []

    def writer(source) -> None:
        try:
            barrier.wait(timeout=5)
            successes.append(workspace.admit("race_api", source, operation_id="same-intent"))
        except Exception as error:
            failures.append(error)

    threads = [threading.Thread(target=writer, args=(source,)) for source in (first_source, second_source)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert all(not thread.is_alive() for thread in threads)
    assert len(successes) == len(failures) == 1
    assert isinstance(failures[0], ConflictError)
    assert workspace.current("race_api") == successes[0]
    assert len(workspace.history("race_api")) == 1


def test_i09_relocation_reuses_identity_and_changed_bytes_advance(tmp_path) -> None:
    workspace, first, source = admit(tmp_path / "owner")
    relocated = tmp_path / "copy" / source.name
    relocated.parent.mkdir(parents=True)
    shutil.copytree(source, relocated)
    same = workspace.admit(first.package, relocated, operation_id="copy")
    assert same == first
    (relocated / "__init__.py").write_text("def call(value=4): ...\n", encoding="utf-8")
    changed = workspace.admit(first.package, relocated, operation_id="changed")
    assert changed.source_id != first.source_id
    assert changed.generation == first.generation + 1


def test_i10_prepared_snapshot_is_complete_without_switching_current(tmp_path) -> None:
    workspace, first, store, old_snapshot, source = admit_snapshot(tmp_path)
    second = second_revision(workspace, source, first.package, "def call(value): ...\n")
    prepared = store.prepare(second, workspace.open(second), operation_id="second-snapshot")
    assert store.current(first.package) == old_snapshot
    assert store.read(prepared)["call"].parameters["value"].required
    assert store.read(old_snapshot)["call"].parameters["value"].required is False


def test_i11_promoted_snapshot_reopens_with_same_graph_identity(tmp_path) -> None:
    workspace, revision, store, snapshot, _ = admit_snapshot(tmp_path)
    reopened = SnapshotStore(tmp_path / "snapshots")
    assert reopened.current(revision.package) == snapshot
    assert reopened.read(revision.package).as_json(full=False) == store.read(snapshot).as_json(full=False)


def test_i12_older_snapshot_cannot_replace_newer_current(tmp_path) -> None:
    workspace, first, store, old_snapshot, source = admit_snapshot(tmp_path)
    second = second_revision(workspace, source, first.package, "def call(value): ...\n")
    new_snapshot = store.prepare(second, workspace.open(second), operation_id="new")
    store.promote(new_snapshot, owner_token=second.owner_token)
    with pytest.raises(OwnershipError):
        store.promote(old_snapshot, owner_token=first.owner_token)
    assert store.current(first.package) == new_snapshot


def test_i13_comparison_binds_ordered_snapshot_receipts_and_breakage_set(tmp_path) -> None:
    workspace, first, store, old_snapshot, source = admit_snapshot(tmp_path)
    second = second_revision(workspace, source, first.package, "def call(value): ...\n")
    new_snapshot = store.prepare(second, workspace.open(second), operation_id="new")
    store.promote(new_snapshot, owner_token=second.owner_token)
    ledger = CompatibilityLedger(tmp_path / "ledger")
    comparison = ledger.prepare(old_snapshot, new_snapshot, operation_id="compare")
    ledger.commit(comparison, owner_token=second.owner_token)
    payload = ledger.read(comparison)
    assert comparison.old_snapshot_id == old_snapshot.id
    assert comparison.new_snapshot_id == new_snapshot.id
    assert payload["breakages"]
    assert comparison.breakage_digest


def test_i14_replay_is_detached_and_preserves_comparison_identity(tmp_path) -> None:
    workspace, first, store, old_snapshot, source = admit_snapshot(tmp_path)
    second = second_revision(workspace, source, first.package, "def call(value): ...\n")
    new_snapshot = store.prepare(second, workspace.open(second), operation_id="new")
    store.promote(new_snapshot, owner_token=second.owner_token)
    ledger = CompatibilityLedger(tmp_path / "ledger")
    comparison = ledger.prepare(old_snapshot, new_snapshot, operation_id="compare")
    ledger.commit(comparison, owner_token=second.owner_token)
    first_read = ledger.replay(comparison)
    first_read["breakages"].clear()
    second_read = ledger.replay(comparison)
    assert second_read["receipt"]["id"] == comparison.id
    assert second_read["breakages"]


def test_i15_extension_effect_commits_to_workspace_and_navigation(tmp_path) -> None:
    workspace, revision, _ = admit(tmp_path)
    pipeline = ExtensionPipeline(tmp_path / "pipeline", workspace)
    output, effect = pipeline.run(revision, [AddMarker()], operation_id="effect")
    graph = workspace.open(output)
    assert graph["marker"].parent is graph
    assert effect.input_revision_id == revision.id
    assert effect.output_revision_id == output.id
    assert effect.affected_paths == (f"{revision.package}.marker",)


def test_i16_failed_extension_rolls_back_and_retry_is_single_effect(tmp_path) -> None:
    workspace, revision, _ = admit(tmp_path)
    pipeline = ExtensionPipeline(tmp_path / "pipeline", workspace)
    with pytest.raises(RuntimeError, match="extension failed"):
        pipeline.run(revision, [FailAfterMarker()], operation_id="retryable")
    assert workspace.current(revision.package) == revision
    assert len(workspace.history(revision.package)) == 1
    output, effect = pipeline.run(revision, [AddMarker()], operation_id="retryable")
    repeated_output, repeated_effect = pipeline.run(revision, [AddMarker()], operation_id="retryable")
    assert repeated_output == output
    assert repeated_effect == effect
    assert len(workspace.history(revision.package)) == 2


def test_i17_extension_effect_survives_snapshot_reopen(tmp_path) -> None:
    workspace, revision, _ = admit(tmp_path)
    output, effect = ExtensionPipeline(tmp_path / "pipeline", workspace).run(
        revision, [AddMarker("published_marker", "7")], operation_id="effect"
    )
    store = SnapshotStore(tmp_path / "snapshots")
    snapshot = store.prepare(output, workspace.open(output), operation_id="snapshot")
    store.promote(snapshot, owner_token=output.owner_token)
    reopened = SnapshotStore(tmp_path / "snapshots")
    assert str(reopened.read(output.package)["published_marker"].value) == "7"
    assert effect.output_revision_id == output.id


def test_i18_compatibility_attributes_extension_change_to_committed_revision(tmp_path) -> None:
    workspace, revision, store, old_snapshot, _ = admit_snapshot(tmp_path)
    output, effect = ExtensionPipeline(tmp_path / "pipeline", workspace).run(
        revision, [RemoveCall()], operation_id="effect"
    )
    new_snapshot = store.prepare(output, workspace.open(output), operation_id="effect-snapshot")
    store.promote(new_snapshot, owner_token=output.owner_token)
    ledger = CompatibilityLedger(tmp_path / "ledger")
    comparison = ledger.prepare(old_snapshot, new_snapshot, operation_id="compare")
    ledger.commit(comparison, owner_token=output.owner_token)
    assert comparison.new_snapshot_id == new_snapshot.id
    assert effect.output_revision_id == output.id
    assert ledger.read(comparison)["breakages"]


def test_i19_multi_package_publication_has_one_content_closure(tmp_path) -> None:
    _, first_revision, _, first_snapshot, _ = admit_snapshot(tmp_path / "one", name="first_api")
    _, second_revision, _, second_snapshot, _ = admit_snapshot(tmp_path / "two", name="second_api")
    publisher = ArtifactPublisher(tmp_path / "publisher")
    receipt = publisher.prepare(
        [first_snapshot, second_snapshot],
        tmp_path / "site",
        operation_id="multi",
        owner_token=second_revision.owner_token,
    )
    publisher.promote(receipt, owner_token=second_revision.owner_token)
    artifacts = publisher.read(receipt)
    assert set(artifacts) == {"graphs/first_api.json", "graphs/second_api.json", "manifest.json"}
    assert receipt.prerequisites == tuple(sorted([first_snapshot.id, second_snapshot.id]))


def test_i20_stale_publication_owner_cannot_change_visible_content(tmp_path) -> None:
    _, first_revision, _, first_snapshot, _ = admit_snapshot(tmp_path)
    publisher = ArtifactPublisher(tmp_path / "publisher")
    receipt = publisher.prepare(
        [first_snapshot], tmp_path / "site", operation_id="release", owner_token=first_revision.owner_token
    )
    publisher.promote(receipt, owner_token=first_revision.owner_token)
    before = publisher.read(receipt)
    with pytest.raises(OwnershipError):
        publisher.promote(receipt, owner_token="stale")
    assert publisher.read(tmp_path / "site") == before


def test_i21_receipt_closure_rejects_missing_workspace_prerequisite(tmp_path) -> None:
    _, revision, _, snapshot, _ = admit_snapshot(tmp_path)
    valid = ReceiptClosure.verify([revision, snapshot])
    assert valid["valid"]
    with pytest.raises(PrerequisiteError):
        ReceiptClosure.verify([snapshot])


def test_i22_reopened_snapshot_and_publication_share_content_identity(tmp_path) -> None:
    _, revision, _, snapshot, _ = admit_snapshot(tmp_path)
    publisher = ArtifactPublisher(tmp_path / "publisher")
    publication = publisher.prepare(
        [snapshot], tmp_path / "site", operation_id="release", owner_token=revision.owner_token
    )
    publisher.promote(publication, owner_token=revision.owner_token)
    reopened_snapshots = SnapshotStore(tmp_path / "snapshots")
    reopened_publisher = ArtifactPublisher(tmp_path / "publisher")
    assert reopened_snapshots.current(revision.package) == snapshot
    assert reopened_publisher.current(tmp_path / "site") == publication
    assert publication.prerequisites == (snapshot.id,)


def test_i23_comparison_and_publication_acknowledgements_close_independently(tmp_path) -> None:
    workspace, first, store, old_snapshot, source = admit_snapshot(tmp_path)
    second = second_revision(workspace, source, first.package, "def call(value): ...\n")
    new_snapshot = store.prepare(second, workspace.open(second), operation_id="new")
    store.promote(new_snapshot, owner_token=second.owner_token)
    ledger = CompatibilityLedger(tmp_path / "ledger")
    comparison = ledger.prepare(old_snapshot, new_snapshot, operation_id="compare")
    ledger.commit(comparison, owner_token=second.owner_token)
    publisher = ArtifactPublisher(tmp_path / "publisher")
    publication = publisher.prepare(
        [new_snapshot, comparison],
        tmp_path / "site",
        operation_id="release",
        owner_token=second.owner_token,
    )
    publisher.promote(publication, owner_token=second.owner_token)
    publisher.acknowledge(publication)
    assert publisher.pending() == []
    assert ledger.pending() == [comparison]
    ledger.acknowledge(comparison)
    assert ledger.pending() == []


def test_i24_recovery_preserves_completed_ids_and_reports_pending_phase(tmp_path) -> None:
    workspace, revision, store, snapshot, _ = admit_snapshot(tmp_path)
    publisher = ArtifactPublisher(tmp_path / "publisher")
    publication = publisher.prepare(
        [snapshot], tmp_path / "site", operation_id="release", owner_token=revision.owner_token
    )
    publisher.promote(publication, owner_token=revision.owner_token)
    assert workspace.recover() == [revision]
    assert store.current(revision.package) == snapshot
    assert publisher.recover() == [publication]
    assert publisher.current(tmp_path / "site") == publication
