from __future__ import annotations

import shutil

import pytest

from griffe import (
    ArtifactPublisher,
    CompatibilityLedger,
    ConflictError,
    OwnershipError,
    SnapshotStore,
)

from .workflow_support import admit, admit_snapshot, second_revision


def test_a09_workspace_source_identity_survives_relocation(tmp_path) -> None:
    workspace, first, source = admit(tmp_path / "one")
    relocated = tmp_path / "relocated" / source.name
    relocated.parent.mkdir(parents=True)
    shutil.copytree(source, relocated)
    reopened = type(workspace)(tmp_path / "one" / "workspace")
    same = reopened.admit(first.package, relocated, operation_id="relocated")
    assert same.source_id == first.source_id
    assert same.id == first.id
    assert same.generation == 1


def test_a10_workspace_operation_is_idempotent_and_conflict_atomic(tmp_path) -> None:
    workspace, first, source = admit(tmp_path, operation="stable-op")
    repeated = workspace.admit(first.package, source, operation_id="stable-op")
    assert repeated == first
    (source / "__init__.py").write_text("def changed(): ...\n", encoding="utf-8")
    with pytest.raises(ConflictError):
        workspace.admit(first.package, source, operation_id="stable-op")
    assert workspace.current(first.package) == first
    assert len(workspace.history(first.package)) == 1


def test_a11_snapshot_prepare_is_invisible_but_readable_by_receipt(tmp_path) -> None:
    workspace, revision, _ = admit(tmp_path)
    store = SnapshotStore(tmp_path / "snapshots")
    receipt = store.prepare(revision, workspace.open(revision), operation_id="prepare")
    with pytest.raises(KeyError):
        store.current(revision.package)
    assert store.read(receipt)["call"].parent.path == revision.package


def test_a12_snapshot_promotion_is_fenced_and_preserves_current(tmp_path) -> None:
    workspace, revision, store, receipt, _ = admit_snapshot(tmp_path)
    with pytest.raises(OwnershipError):
        store.promote(receipt, owner_token="stale-owner")
    assert store.current(revision.package) == receipt
    assert store.promote(receipt, owner_token=revision.owner_token) == receipt


def test_a13_compatibility_prepare_has_stable_set_identity(tmp_path) -> None:
    workspace, first, store, old_snapshot, source = admit_snapshot(tmp_path)
    second = second_revision(
        workspace,
        source,
        first.package,
        "def call(value):\n    return value\n",
    )
    new_snapshot = store.prepare(second, workspace.open(second), operation_id="new-snapshot")
    store.promote(new_snapshot, owner_token=second.owner_token)
    ledger = CompatibilityLedger(tmp_path / "ledger")
    prepared = ledger.prepare(old_snapshot, new_snapshot, operation_id="compare")
    repeated = ledger.prepare(old_snapshot, new_snapshot, operation_id="compare")
    assert repeated == prepared
    assert prepared.breakage_digest
    assert ledger.pending() == []


def test_a14_committed_comparison_reopens_pending_until_ack(tmp_path) -> None:
    workspace, first, store, old_snapshot, source = admit_snapshot(tmp_path)
    second = second_revision(workspace, source, first.package, "def call(value): ...\n")
    new_snapshot = store.prepare(second, workspace.open(second), operation_id="snapshot-2")
    store.promote(new_snapshot, owner_token=second.owner_token)
    ledger = CompatibilityLedger(tmp_path / "ledger")
    receipt = ledger.prepare(old_snapshot, new_snapshot, operation_id="comparison")
    ledger.commit(receipt, owner_token=second.owner_token)
    reopened = CompatibilityLedger(tmp_path / "ledger")
    assert reopened.pending() == [receipt]
    assert reopened.replay(receipt)["acknowledged"] is False
    reopened.acknowledge(receipt)
    reopened.acknowledge(receipt)
    assert reopened.pending() == []


def test_a15_publication_prepare_is_invisible_and_owner_bound(tmp_path) -> None:
    _, revision, _, snapshot, _ = admit_snapshot(tmp_path)
    publisher = ArtifactPublisher(tmp_path / "publisher")
    receipt = publisher.prepare(
        [snapshot],
        tmp_path / "site",
        operation_id="release",
        owner_token=revision.owner_token,
    )
    with pytest.raises(KeyError):
        publisher.current(tmp_path / "site")
    with pytest.raises(OwnershipError):
        publisher.promote(receipt, owner_token="foreign")


def test_a16_promoted_publication_is_pending_until_ack(tmp_path) -> None:
    _, revision, _, snapshot, _ = admit_snapshot(tmp_path)
    publisher = ArtifactPublisher(tmp_path / "publisher")
    receipt = publisher.prepare(
        [snapshot],
        tmp_path / "site",
        operation_id="release",
        owner_token=revision.owner_token,
    )
    publisher.promote(receipt, owner_token=revision.owner_token)
    reopened = ArtifactPublisher(tmp_path / "publisher")
    assert reopened.current(tmp_path / "site") == receipt
    assert reopened.pending() == [receipt]
    assert "manifest.json" in reopened.read(tmp_path / "site")
    reopened.acknowledge(receipt)
    reopened.acknowledge(receipt)
    assert reopened.pending() == []
