from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import dynaconf as _dynaconf


class _MissingSurface:
    def __init__(self, *args, **kwargs):
        raise AssertionError("required durable public surface is missing")


ArtifactTransport = getattr(_dynaconf, "ArtifactTransport", _MissingSurface)
DurableSettingsStore = getattr(_dynaconf, "DurableSettingsStore", _MissingSurface)
LineageJournal = getattr(_dynaconf, "LineageJournal", _MissingSurface)
SourceWatcher = getattr(_dynaconf, "SourceWatcher", _MissingSurface)
OwnershipError = getattr(_dynaconf, "OwnershipError", RuntimeError)
ProtocolError = getattr(_dynaconf, "ProtocolError", RuntimeError)
StaleFenceError = getattr(_dynaconf, "StaleFenceError", RuntimeError)


def _json(path: Path, value) -> None:
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def _crashed_lease(root: Path, owner="worker") -> None:
    code = (
        "import os,sys; from dynaconf import DurableSettingsStore; "
        "DurableSettingsStore(sys.argv[1]).claim(sys.argv[2]); os._exit(0)"
    )
    completed = subprocess.run(
        [sys.executable, "-B", "-c", code, str(root), owner],
        env=os.environ.copy(), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, timeout=20, check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "strict")


def test_a17_durable_store_initial_generation_and_owned_copy(tmp_path: Path):
    store = DurableSettingsStore(tmp_path / "store")
    first = store.snapshot()
    first["values"]["changed"] = True
    assert first["generation"] == 0
    assert store.snapshot() == {"generation": 0, "values": {}, "fence": 0}


def test_a18_claim_receipt_release_and_reclaim(tmp_path: Path):
    store = DurableSettingsStore(tmp_path / "store")
    first = store.claim("alpha")
    assert (first.receipt.owner, first.receipt.fence, first.receipt.adopted) == ("alpha", 1, False)
    first.release()
    second = store.claim("beta")
    assert second.receipt.fence == 2 and second.receipt.token != first.receipt.token


def test_a19_retired_fence_cannot_commit(tmp_path: Path):
    store = DurableSettingsStore(tmp_path / "store")
    old = store.claim("old")
    old.release()
    current = store.claim("current")
    with pytest.raises(StaleFenceError):
        old.commit({"value": "stale"})
    assert current.commit({"value": "fresh"}).generation == 1


def test_a20_append_only_lineage_cursor_and_reopen(tmp_path: Path):
    path = tmp_path / "lineage.jsonl"
    journal = LineageJournal(path)
    one = journal.append("primary", "upsert", payload={"port": 7311})
    two = journal.append("overlay", "upsert", payload={"debug": True})
    assert (one.sequence, two.sequence, journal.cursor) == (1, 2, 2)
    assert [event.source for event in LineageJournal(path).changes(1)] == ["overlay"]


def test_a21_watcher_rejects_bad_bytes_and_recovers(tmp_path: Path):
    source = tmp_path / "source.json"
    journal = LineageJournal(tmp_path / "lineage.jsonl")
    watcher = SourceWatcher(journal, [source])
    source.write_bytes(b"\xff")
    assert watcher.poll()[0].accepted is False and journal.project() == {}
    _json(source, {"mode": "recovered"})
    assert watcher.poll()[0].accepted is True
    assert journal.project()[str(source.resolve())] == {"mode": "recovered"}


def test_a22_transport_requires_delivery_before_ack(tmp_path: Path):
    transport = ArtifactTransport(tmp_path / "outbox", tmp_path / "sink")
    staged = transport.stage("bundle/config.json", {"generation": 7}, generation=7)
    with pytest.raises(ProtocolError):
        transport.ack(staged.token)
    assert transport.deliver(staged.token).state == "delivered"
    assert transport.ack(staged.token).state == "acked"


def test_i23_crashed_owner_requires_explicit_adoption(tmp_path: Path):
    root = tmp_path / "store"
    _crashed_lease(root)
    store = DurableSettingsStore(root)
    with pytest.raises(OwnershipError):
        store.claim("recovery")
    recovered = store.claim("recovery", adopt_stale=True)
    assert recovered.receipt.adopted and recovered.receipt.fence == 2


def test_i24_live_owner_blocks_a_second_store_instance(tmp_path: Path):
    root = tmp_path / "store"
    owner = DurableSettingsStore(root).claim("live")
    with pytest.raises(OwnershipError):
        DurableSettingsStore(root).claim("contender", adopt_stale=True)
    owner.release()


def test_i25_adoption_advances_fence_without_rewriting_values(tmp_path: Path):
    root = tmp_path / "store"
    seed = DurableSettingsStore(root).claim("seed")
    seed.commit({"region": "north"})
    seed.release()
    _crashed_lease(root)
    adopted = DurableSettingsStore(root).claim("next", adopt_stale=True)
    assert adopted.receipt.fence == 3
    assert adopted.store.snapshot()["values"] == {"region": "north"}


def test_i26_compare_generation_rejects_lost_update(tmp_path: Path):
    lease = DurableSettingsStore(tmp_path / "store").claim("writer")
    first = lease.commit({"revision": 1}, expected_generation=0)
    assert first.generation == 1
    with pytest.raises(StaleFenceError):
        lease.commit({"revision": 2}, expected_generation=0)
    assert lease.store.snapshot()["values"] == {"revision": 1}


def test_i27_fresh_process_observes_committed_generation(tmp_path: Path):
    root = tmp_path / "store"
    lease = DurableSettingsStore(root).claim("writer")
    lease.commit({"endpoint": "tcp://node-9"})
    code = "import json,sys; from dynaconf import DurableSettingsStore; print(json.dumps(DurableSettingsStore(sys.argv[1]).snapshot(),sort_keys=True))"
    completed = subprocess.run([sys.executable, "-B", "-c", code, str(root)], env=os.environ.copy(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20, check=False)
    assert completed.returncode == 0
    assert json.loads(completed.stdout)["values"]["endpoint"] == "tcp://node-9"


def test_i28_precrash_token_is_fenced_after_adoption(tmp_path: Path):
    root = tmp_path / "store"
    _crashed_lease(root, "departed")
    stale_record = json.loads((root / "lease.json").read_text(encoding="utf-8"))
    current = DurableSettingsStore(root).claim("adopter", adopt_stale=True)
    assert current.receipt.fence > stale_record["fence"]
    assert current.commit({"owner": "adopter"}).fence == current.receipt.fence


def test_i29_lineage_is_byte_append_only_across_reopen(tmp_path: Path):
    path = tmp_path / "lineage.jsonl"
    journal = LineageJournal(path)
    journal.append("a", "upsert", payload={"x": 1})
    before = path.read_bytes()
    LineageJournal(path).append("a", "upsert", payload={"x": 2})
    after = path.read_bytes()
    assert after.startswith(before) and len(after) > len(before)


def test_i30_watcher_deduplicates_unchanged_observations(tmp_path: Path):
    source = tmp_path / "settings.json"
    _json(source, {"workers": 3})
    watcher = SourceWatcher(LineageJournal(tmp_path / "journal"), [source])
    assert len(watcher.poll()) == 1
    assert watcher.poll() == []
    _json(source, {"workers": 4})
    assert len(watcher.poll()) == 1


def test_i31_rejected_revision_preserves_last_good_projection(tmp_path: Path):
    source = tmp_path / "settings.json"
    journal = LineageJournal(tmp_path / "journal")
    watcher = SourceWatcher(journal, [source])
    _json(source, {"color": "blue"}); watcher.poll()
    source.write_text("{bad", encoding="utf-8"); watcher.poll()
    assert journal.project()[str(source.resolve())] == {"color": "blue"}
    _json(source, {"color": "green"}); watcher.poll()
    assert [e.accepted for e in journal.changes()] == [True, False, True]


def test_i32_delete_and_recreate_are_distinct_lineage_events(tmp_path: Path):
    source = tmp_path / "settings.json"
    journal = LineageJournal(tmp_path / "journal")
    watcher = SourceWatcher(journal, [source])
    _json(source, {"epoch": 1}); watcher.poll()
    source.unlink(); watcher.poll()
    _json(source, {"epoch": 2}); watcher.poll()
    assert [e.operation for e in journal.changes()] == ["upsert", "delete", "upsert"]
    assert journal.project()[str(source.resolve())]["epoch"] == 2


def test_i33_multiple_sources_keep_independent_materialized_facts(tmp_path: Path):
    sources = [tmp_path / "base.json", tmp_path / "local.json"]
    _json(sources[0], {"port": 5001}); _json(sources[1], {"debug": True})
    journal = LineageJournal(tmp_path / "journal")
    watcher = SourceWatcher(journal, sources)
    watcher.poll(); sources[0].unlink(); watcher.poll()
    view = journal.project()
    assert str(sources[0].resolve()) not in view
    assert view[str(sources[1].resolve())] == {"debug": True}


def test_i34_cursor_resume_returns_only_later_source_changes(tmp_path: Path):
    journal = LineageJournal(tmp_path / "journal")
    journal.append("base", "upsert", payload={"a": 1})
    cursor = journal.cursor
    journal.append("tenant", "upsert", payload={"b": 2})
    journal.append("base", "delete")
    assert [(e.source, e.operation) for e in journal.changes(cursor)] == [("tenant", "upsert"), ("base", "delete")]


def test_i35_transport_rollback_restores_previous_bytes(tmp_path: Path):
    sink = tmp_path / "sink"; target = sink / "bundle.json"
    target.parent.mkdir(); target.write_bytes(b"previous")
    transport = ArtifactTransport(tmp_path / "outbox", sink)
    item = transport.stage("bundle.json", {"next": True}, generation=2)
    transport.deliver(item.token); transport.rollback(item.token)
    assert target.read_bytes() == b"previous" and transport.pending() == []


def test_i36_pending_delivery_replays_after_transport_reopen(tmp_path: Path):
    root, sink = tmp_path / "outbox", tmp_path / "sink"
    item = ArtifactTransport(root, sink).stage("state.json", {"rev": 9}, generation=9)
    reopened = ArtifactTransport(root, sink)
    assert reopened.pending() == [item.token]
    reopened.deliver(item.token); reopened.ack(item.token)
    assert json.loads((sink / "state.json").read_text(encoding="utf-8")) == {"rev": 9}


def test_i37_acknowledgement_is_idempotent_after_restart(tmp_path: Path):
    root, sink = tmp_path / "outbox", tmp_path / "sink"
    transport = ArtifactTransport(root, sink)
    item = transport.stage("state.json", {"ok": True}, generation=1)
    transport.deliver(item.token); first = transport.ack(item.token)
    second = ArtifactTransport(root, sink).ack(item.token)
    assert first == second and second.state == "acked"


def test_i38_transport_digest_covers_canonical_payload_and_nested_key(tmp_path: Path):
    transport = ArtifactTransport(tmp_path / "outbox", tmp_path / "sink")
    item = transport.stage("tenant/a/config.json", {"z": 2, "a": 1}, generation=4)
    expected = hashlib.sha256(json.dumps({"a": 1, "z": 2}, sort_keys=True).encode()).hexdigest()
    transport.deliver(item.token); transport.ack(item.token)
    assert item.digest == expected and (tmp_path / "sink/tenant/a/config.json").is_file()


def test_i39_unacknowledged_delivery_can_be_rolled_back_after_reopen(tmp_path: Path):
    root, sink = tmp_path / "outbox", tmp_path / "sink"
    item = ArtifactTransport(root, sink).stage("live.json", {"temp": 1}, generation=1)
    ArtifactTransport(root, sink).deliver(item.token)
    ArtifactTransport(root, sink).rollback(item.token)
    assert not (sink / "live.json").exists()


def test_i40_independent_delivery_keys_ack_and_rollback_separately(tmp_path: Path):
    transport = ArtifactTransport(tmp_path / "outbox", tmp_path / "sink")
    a = transport.stage("a.json", {"a": 1}, generation=1)
    b = transport.stage("b.json", {"b": 1}, generation=1)
    transport.deliver(a.token); transport.ack(a.token)
    transport.deliver(b.token); transport.rollback(b.token)
    assert (tmp_path / "sink/a.json").exists() and not (tmp_path / "sink/b.json").exists()


def test_s11_watched_projection_commits_under_a_durable_lease(tmp_path: Path):
    source = tmp_path / "source.json"; _json(source, {"limit": 17})
    journal = LineageJournal(tmp_path / "lineage")
    SourceWatcher(journal, [source]).poll()
    lease = DurableSettingsStore(tmp_path / "store").claim("watch-applier")
    receipt = lease.commit(journal.project())
    assert receipt.generation == 1 and lease.store.snapshot()["values"][str(source.resolve())]["limit"] == 17


def test_s12_committed_generation_is_acknowledged_as_an_artifact(tmp_path: Path):
    store = DurableSettingsStore(tmp_path / "store")
    lease = store.claim("publisher"); commit = lease.commit({"feature": "on"})
    transport = ArtifactTransport(tmp_path / "outbox", tmp_path / "sink")
    delivery = transport.stage("configuration.json", store.snapshot(), generation=commit.generation)
    transport.deliver(delivery.token); transport.ack(delivery.token)
    assert json.loads((tmp_path / "sink/configuration.json").read_text(encoding="utf-8"))["generation"] == commit.generation


def test_s13_watch_commit_publish_crosses_all_resource_owners(tmp_path: Path):
    source = tmp_path / "tenant.json"; _json(source, {"quota": 31})
    journal = LineageJournal(tmp_path / "lineage"); SourceWatcher(journal, [source]).poll()
    store = DurableSettingsStore(tmp_path / "store"); lease = store.claim("coordinator")
    commit = lease.commit(journal.project())
    transport = ArtifactTransport(tmp_path / "outbox", tmp_path / "sink")
    item = transport.stage("tenant.json", store.snapshot(), generation=commit.generation)
    transport.deliver(item.token); transport.ack(item.token)
    assert journal.cursor == 1 and not transport.pending() and json.loads((tmp_path / "sink/tenant.json").read_text(encoding="utf-8"))["values"] == journal.project()


def test_s14_crash_adoption_records_new_owner_without_losing_generation(tmp_path: Path):
    root = tmp_path / "store"
    initial = DurableSettingsStore(root).claim("seed"); initial.commit({"epoch": 1}); initial.release()
    _crashed_lease(root, "crashed")
    recovered = DurableSettingsStore(root).claim("recovered", adopt_stale=True)
    journal = LineageJournal(tmp_path / "lineage")
    journal.append("ownership", "upsert", payload={"fence": recovered.receipt.fence, "generation": recovered.store.snapshot()["generation"]})
    assert journal.project()["ownership"] == {"fence": 3, "generation": 1}


def test_s15_failed_publication_rolls_back_artifact_not_committed_state(tmp_path: Path):
    store = DurableSettingsStore(tmp_path / "store"); lease = store.claim("writer")
    lease.commit({"stable": True})
    sink = tmp_path / "sink"; sink.mkdir(); (sink / "config.json").write_text("old", encoding="utf-8")
    transport = ArtifactTransport(tmp_path / "outbox", sink)
    item = transport.stage("config.json", store.snapshot(), generation=1)
    transport.deliver(item.token); transport.rollback(item.token)
    assert (sink / "config.json").read_text(encoding="utf-8") == "old"
    assert store.snapshot()["values"] == {"stable": True}


def test_s16_restart_replays_pending_artifact_with_generation_agreement(tmp_path: Path):
    source = tmp_path / "source.json"; _json(source, {"mode": "safe"})
    journal_path = tmp_path / "lineage"; journal = LineageJournal(journal_path)
    SourceWatcher(journal, [source]).poll()
    store_path = tmp_path / "store"; lease = DurableSettingsStore(store_path).claim("first")
    commit = lease.commit(journal.project()); lease.release()
    outbox, sink = tmp_path / "outbox", tmp_path / "sink"
    item = ArtifactTransport(outbox, sink).stage("snapshot.json", DurableSettingsStore(store_path).snapshot(), generation=commit.generation)
    restarted = ArtifactTransport(outbox, sink)
    assert restarted.pending() == [item.token]
    restarted.deliver(item.token); restarted.ack(item.token)
    artifact = json.loads((sink / "snapshot.json").read_text(encoding="utf-8"))
    assert artifact["generation"] == commit.generation == 1
    assert artifact["values"] == LineageJournal(journal_path).project()
