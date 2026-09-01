from __future__ import annotations

import io
import json
import shutil
import threading

import pytest

from griffe import (
    AnalysisWorkspace,
    ArtifactPublisher,
    CompatibilityLedger,
    ExtensionPipeline,
    PrerequisiteError,
    ReceiptClosure,
    SnapshotStore,
    dump,
)

from .workflow_support import AddMarker, FailAfterMarker, admit_snapshot, second_revision


def _comparison_chain(root):
    workspace, first, snapshots, old_snapshot, source = admit_snapshot(root)
    second = second_revision(workspace, source, first.package, "def call(value): ...\n")
    new_snapshot = snapshots.prepare(second, workspace.open(second), operation_id="snapshot-new")
    snapshots.promote(new_snapshot, owner_token=second.owner_token)
    ledger = CompatibilityLedger(root / "ledger")
    comparison = ledger.prepare(old_snapshot, new_snapshot, operation_id="compare")
    ledger.commit(comparison, owner_token=second.owner_token)
    return workspace, first, second, snapshots, old_snapshot, new_snapshot, ledger, comparison, source


def _publish(root, revision, inputs, operation="release"):
    publisher = ArtifactPublisher(root / "publisher")
    publication = publisher.prepare(
        inputs,
        root / "site",
        operation_id=operation,
        owner_token=revision.owner_token,
    )
    publisher.promote(publication, owner_token=revision.owner_token)
    return publisher, publication


def test_s01_full_analysis_snapshot_comparison_publication_closure(tmp_path) -> None:
    chain = _comparison_chain(tmp_path)
    workspace, first, second, snapshots, old_snapshot, new_snapshot, ledger, comparison, _ = chain
    publisher, publication = _publish(tmp_path, second, [new_snapshot, comparison])
    closure = ReceiptClosure.verify([first, second, old_snapshot, new_snapshot, comparison, publication])
    assert closure["valid"]
    assert publisher.read(publication)["manifest.json"]
    assert ledger.read(comparison)["breakages"]
    assert workspace.open(second)["call"].parameters["value"].required


def test_s02_failed_effect_then_promoted_unacked_release_recovers_once(tmp_path) -> None:
    workspace, revision, snapshots, original_snapshot, _ = admit_snapshot(tmp_path)
    pipeline = ExtensionPipeline(tmp_path / "pipeline", workspace)
    with pytest.raises(RuntimeError):
        pipeline.run(revision, [FailAfterMarker()], operation_id="effect")
    output, effect = pipeline.run(revision, [AddMarker()], operation_id="effect")
    effect_snapshot = snapshots.prepare(output, workspace.open(output), operation_id="effect-snapshot")
    snapshots.promote(effect_snapshot, owner_token=output.owner_token)
    publisher, publication = _publish(tmp_path, output, [effect_snapshot, effect])
    reopened = ArtifactPublisher(tmp_path / "publisher")
    assert reopened.recover() == [publication]
    assert reopened.current(tmp_path / "site") == publication
    reopened.acknowledge(publication)
    assert reopened.recover() == []
    assert snapshots.read(original_snapshot)["call"].parent.path == revision.package


def test_s03_relocated_source_reopens_same_cross_owner_identities(tmp_path) -> None:
    workspace, revision, snapshots, snapshot, source = admit_snapshot(tmp_path / "original")
    publisher, publication = _publish(tmp_path, revision, [snapshot])
    relocated = tmp_path / "relocated" / source.name
    relocated.parent.mkdir(parents=True)
    shutil.copytree(source, relocated)
    reopened_workspace = AnalysisWorkspace(tmp_path / "original" / "workspace")
    same = reopened_workspace.admit(revision.package, relocated, operation_id="relocated")
    assert same == revision
    assert SnapshotStore(tmp_path / "original" / "snapshots").current(revision.package) == snapshot
    assert ArtifactPublisher(tmp_path / "publisher").current(tmp_path / "site") == publication
    assert publisher.read(publication) == ArtifactPublisher(tmp_path / "publisher").read(publication)


def test_s04_extension_change_comparison_and_dual_ack_close(tmp_path) -> None:
    workspace, revision, snapshots, old_snapshot, _ = admit_snapshot(tmp_path)
    output, effect = ExtensionPipeline(tmp_path / "pipeline", workspace).run(
        revision, [AddMarker("new_public", "5")], operation_id="effect"
    )
    new_snapshot = snapshots.prepare(output, workspace.open(output), operation_id="new-snapshot")
    snapshots.promote(new_snapshot, owner_token=output.owner_token)
    ledger = CompatibilityLedger(tmp_path / "ledger")
    comparison = ledger.prepare(old_snapshot, new_snapshot, operation_id="compare")
    ledger.commit(comparison, owner_token=output.owner_token)
    publisher, publication = _publish(tmp_path, output, [new_snapshot, comparison, effect])
    publisher.acknowledge(publication)
    ledger.acknowledge(comparison)
    assert publisher.pending() == [] and ledger.pending() == []
    assert ReceiptClosure.verify([revision, output, old_snapshot, new_snapshot, effect, comparison, publication])["valid"]


def test_s05_failed_extension_and_invalid_closure_preserve_prior_graph(tmp_path) -> None:
    workspace, revision, snapshots, snapshot, _ = admit_snapshot(tmp_path)
    pipeline = ExtensionPipeline(tmp_path / "pipeline", workspace)
    with pytest.raises(RuntimeError):
        pipeline.run(revision, [FailAfterMarker()], operation_id="bad-effect")
    with pytest.raises(PrerequisiteError):
        ReceiptClosure.verify([snapshot])
    reopened_workspace = AnalysisWorkspace(tmp_path / "workspace")
    reopened_snapshots = SnapshotStore(tmp_path / "snapshots")
    assert reopened_workspace.current(revision.package) == revision
    assert "transient" not in reopened_workspace.open(revision).members
    assert reopened_snapshots.current(revision.package) == snapshot


def test_s06_concurrent_equivalent_publication_converges(tmp_path) -> None:
    _, revision, _, snapshot, _ = admit_snapshot(tmp_path)
    publisher = ArtifactPublisher(tmp_path / "publisher")
    barrier = threading.Barrier(2)
    results = []
    errors = []

    def prepare() -> None:
        try:
            barrier.wait(timeout=5)
            results.append(
                publisher.prepare(
                    [snapshot],
                    tmp_path / "site",
                    operation_id="same-release",
                    owner_token=revision.owner_token,
                )
            )
        except Exception as error:
            errors.append(error)

    threads = [threading.Thread(target=prepare) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert all(not thread.is_alive() for thread in threads)
    assert errors == [], [f"{type(error).__name__}: {error}" for error in errors]
    assert len(results) == 2
    assert results[0] == results[1]
    publisher.promote(results[0], owner_token=revision.owner_token)
    assert publisher.current(tmp_path / "site") == results[0]


def test_s07_committed_comparison_release_replays_without_duplicate_ack(tmp_path) -> None:
    chain = _comparison_chain(tmp_path)
    _, first, second, _, old_snapshot, new_snapshot, ledger, comparison, _ = chain
    publisher, publication = _publish(tmp_path, second, [new_snapshot, comparison])
    assert ledger.pending() == [comparison]
    assert publisher.pending() == [publication]
    replay_before = ledger.replay(comparison)
    ArtifactPublisher(tmp_path / "publisher").acknowledge(publication)
    CompatibilityLedger(tmp_path / "ledger").acknowledge(comparison)
    assert publisher.pending() == [] and ledger.pending() == []
    assert ledger.replay(comparison)["breakages"] == replay_before["breakages"]
    assert ReceiptClosure.verify([first, second, old_snapshot, new_snapshot, comparison, publication])["valid"]


def test_s08_dump_and_durable_views_describe_same_graph(tmp_path) -> None:
    workspace, revision, snapshots, snapshot, source = admit_snapshot(tmp_path)
    publisher, publication = _publish(tmp_path, revision, [snapshot])
    stream = io.StringIO()
    result = dump(
        [revision.package],
        output=stream,
        search_paths=[source.parent],
        full=False,
    )
    cli_graph = json.loads(stream.getvalue())[revision.package]
    snapshot_graph = json.loads(snapshots.read(snapshot).as_json(full=False))
    artifact_graph = json.loads(publisher.read(publication)[f"graphs/{revision.package}.json"])
    assert result == 0
    assert cli_graph == snapshot_graph == artifact_graph
    assert ReceiptClosure.verify([revision, snapshot, publication])["valid"]
