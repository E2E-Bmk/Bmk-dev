from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import dynaconf as _dynaconf


class _MissingSurface:
    def __init__(self, *args, **kwargs):
        raise AssertionError("required recoverable publication surface is missing")


PublicationCoordinator = getattr(_dynaconf, "PublicationCoordinator", _MissingSurface)
PublicationConflict = getattr(_dynaconf, "PublicationConflict", RuntimeError)
StaleLineageError = getattr(_dynaconf, "StaleLineageError", RuntimeError)
LineageJournal = getattr(_dynaconf, "LineageJournal", _MissingSurface)


def _paths(root: Path) -> dict[str, str]:
    return {
        "root": str(root / "protocol"),
        "store_root": str(root / "store"),
        "lineage_path": str(root / "lineage.jsonl"),
        "outbox_root": str(root / "outbox"),
        "sink_root": str(root / "sink"),
    }


def _coordinator(root: Path):
    paths = _paths(root)
    return PublicationCoordinator(
        paths.pop("root"),
        store_root=paths["store_root"],
        lineage_path=paths["lineage_path"],
        outbox_root=paths["outbox_root"],
        sink_root=paths["sink_root"],
    )


def _journal(root: Path):
    return LineageJournal(root / "lineage.jsonl")


def _prepare(root: Path, owner="writer", *, cursor=None, generation=None, values=None, key="live/config.json", idem="publication-1"):
    journal = _journal(root)
    store = json.loads((root / "store/state.json").read_text(encoding="utf-8")) if (root / "store/state.json").exists() else {"generation": 0}
    return _coordinator(root).prepare(
        owner,
        source_cursor=journal.cursor if cursor is None else cursor,
        expected_generation=store["generation"] if generation is None else generation,
        values=journal.project() if values is None else values,
        key=key,
        idempotency_key=idem,
    )


def _fresh(root: Path, operation: str, token: str, owner="recovery"):
    payload = json.dumps({"paths": _paths(root), "operation": operation, "token": token, "owner": owner})
    code = (
        "import json,sys; from dynaconf import PublicationCoordinator; "
        "p=json.loads(sys.argv[1]); q=p.pop('paths'); "
        "c=PublicationCoordinator(q.pop('root'),**q); "
        "r=(c.recover(p['token'],owner=p['owner']) if p['operation']=='recover' "
        "else getattr(c,p['operation'])(p['token'])); "
        "print(json.dumps(r.__dict__,sort_keys=True))"
    )
    completed = subprocess.run(
        [sys.executable, "-B", "-c", code, payload],
        env=os.environ.copy(), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, timeout=20, check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "strict")
    return json.loads(completed.stdout.decode("utf-8", "strict"))


def _seed(root: Path, source="tenant", value=None):
    return _journal(root).append(source, "upsert", payload={"value": 1} if value is None else value)


def test_s17_prepared_generation_survives_reopen_without_early_visibility(tmp_path: Path):
    _seed(tmp_path, value={"mode": "prepared"})
    prepared = _prepare(tmp_path)
    reopened = _coordinator(tmp_path).status(prepared.token)
    store = json.loads((tmp_path / "store/state.json").read_text(encoding="utf-8"))
    assert reopened == prepared and reopened.state == "prepared"
    assert store["generation"] == 0 and not (tmp_path / "sink/live/config.json").exists()


def test_s18_stale_watcher_cursor_aborts_before_store_or_artifact_commit(tmp_path: Path):
    _seed(tmp_path, value={"revision": 1})
    prepared = _prepare(tmp_path)
    _seed(tmp_path, "overlay", {"revision": 2})
    with pytest.raises(StaleLineageError):
        _coordinator(tmp_path).commit(prepared.token)
    assert _coordinator(tmp_path).status(prepared.token).state == "rolled-back"
    assert json.loads((tmp_path / "store/state.json").read_text(encoding="utf-8"))["generation"] == 0


def test_s19_commit_then_crash_recovery_writes_compensating_generation(tmp_path: Path):
    _seed(tmp_path, value={"limit": 23})
    prepared = _prepare(tmp_path)
    _fresh(tmp_path, "commit", prepared.token)
    assert json.loads((tmp_path / "store/state.json").read_text(encoding="utf-8"))["generation"] == 1
    recovered = _fresh(tmp_path, "recover", prepared.token, "replacement")
    store = json.loads((tmp_path / "store/state.json").read_text(encoding="utf-8"))
    assert recovered["state"] == "rolled-back" and store == {"generation": 2, "values": {}, "fence": 2}


def test_s20_delivered_unacked_recovery_restores_artifact_and_store(tmp_path: Path):
    sink = tmp_path / "sink/live/config.json"
    sink.parent.mkdir(parents=True)
    sink.write_text(json.dumps({"stable": True}), encoding="utf-8")
    _seed(tmp_path, value={"feature": "next"})
    prepared = _prepare(tmp_path)
    _fresh(tmp_path, "commit", prepared.token)
    _fresh(tmp_path, "deliver", prepared.token)
    assert json.loads(sink.read_text(encoding="utf-8"))["generation"] == 1
    _fresh(tmp_path, "recover", prepared.token, "successor")
    assert json.loads(sink.read_text(encoding="utf-8")) == {"stable": True}
    assert json.loads((tmp_path / "store/state.json").read_text(encoding="utf-8"))["values"] == {}


def test_s21_each_protocol_phase_may_run_in_a_fresh_process(tmp_path: Path):
    _seed(tmp_path, value={"region": "west", "replicas": 3})
    prepared = _prepare(tmp_path, owner="planner")
    committed = _fresh(tmp_path, "commit", prepared.token)
    delivered = _fresh(tmp_path, "deliver", prepared.token)
    acknowledged = _fresh(tmp_path, "acknowledge", prepared.token)
    artifact = json.loads((tmp_path / "sink/live/config.json").read_text(encoding="utf-8"))
    assert [committed["state"], delivered["state"], acknowledged["state"]] == ["committed", "delivered", "acked"]
    assert artifact["generation"] == acknowledged["generation"] == 1
    assert artifact["values"] == _journal(tmp_path).project()


def test_s22_duplicate_delivery_and_ack_are_durable_idempotent_events(tmp_path: Path):
    _seed(tmp_path, value={"epoch": 8})
    prepared = _prepare(tmp_path)
    _fresh(tmp_path, "commit", prepared.token)
    first_delivery = _fresh(tmp_path, "deliver", prepared.token)
    second_delivery = _fresh(tmp_path, "deliver", prepared.token)
    first_ack = _fresh(tmp_path, "acknowledge", prepared.token)
    second_ack = _fresh(tmp_path, "acknowledge", prepared.token)
    events = _coordinator(tmp_path).events()
    assert first_delivery == second_delivery and first_ack == second_ack
    assert [e["operation"] for e in events].count("deliver") == 1
    assert [e["operation"] for e in events].count("acknowledge") == 1


def test_s23_concurrent_publisher_is_blocked_until_owner_recovery(tmp_path: Path):
    _seed(tmp_path, value={"tenant": "a"})
    first = _prepare(tmp_path, owner="first", idem="first")
    with pytest.raises(PublicationConflict):
        _prepare(tmp_path, owner="second", values={"tenant": "b"}, idem="second")
    _fresh(tmp_path, "recover", first.token, "adopter")
    second = _prepare(tmp_path, owner="second", values={"tenant": "b"}, idem="second")
    assert second.fence > first.fence and second.owner == "second"


def test_s24_prepare_idempotency_does_not_alias_changed_payload(tmp_path: Path):
    _seed(tmp_path, value={"quota": 10})
    first = _prepare(tmp_path, values={"quota": 10}, idem="request-7")
    duplicate = _prepare(tmp_path, values={"quota": 10}, idem="request-7")
    assert duplicate == first
    with pytest.raises(PublicationConflict):
        _prepare(tmp_path, values={"quota": 11}, idem="request-7")


def test_s25_recovery_retires_precrash_token_and_preserves_protocol_ledger(tmp_path: Path):
    _seed(tmp_path, value={"color": "amber"})
    prepared = _prepare(tmp_path)
    committed = _fresh(tmp_path, "commit", prepared.token)
    recovered = _fresh(tmp_path, "recover", prepared.token, "new-owner")
    with pytest.raises(Exception):
        _coordinator(tmp_path).deliver(prepared.token)
    events = _coordinator(tmp_path).events()
    assert recovered["fence"] > committed["fence"]
    assert [event["operation"] for event in events] == ["prepare", "commit", "recover-rollback"]


def test_s26_lineage_store_divergence_reconciles_without_rewriting_history(tmp_path: Path):
    journal = _journal(tmp_path)
    journal.append("base", "upsert", payload={"mode": "safe"})
    before = (tmp_path / "lineage.jsonl").read_bytes()
    receipt = _coordinator(tmp_path).reconcile("reconciler", key="state.json", idempotency_key="reconcile-1")
    after = (tmp_path / "lineage.jsonl").read_bytes()
    store = json.loads((tmp_path / "store/state.json").read_text(encoding="utf-8"))
    artifact = json.loads((tmp_path / "sink/state.json").read_text(encoding="utf-8"))
    assert receipt.state == "acked" and after == before
    assert store == artifact and store["values"] == journal.project()


def test_s27_stale_prepare_then_reconcile_converges_to_all_source_owners(tmp_path: Path):
    journal = _journal(tmp_path)
    journal.append("base", "upsert", payload={"port": 7107})
    stale = _prepare(tmp_path, idem="stale")
    journal.append("tenant", "upsert", payload={"debug": True})
    with pytest.raises(StaleLineageError):
        _coordinator(tmp_path).commit(stale.token)
    final = _coordinator(tmp_path).reconcile("replacement", key="bundle.json", idempotency_key="final")
    artifact = json.loads((tmp_path / "sink/bundle.json").read_text(encoding="utf-8"))
    assert final.state == "acked" and artifact["values"] == journal.project()
    assert set(artifact["values"]) == {"base", "tenant"}


def test_s28_rollback_retry_uses_new_generation_fence_and_acknowledged_visibility(tmp_path: Path):
    _seed(tmp_path, value={"phase": "first"})
    first = _prepare(tmp_path, idem="attempt-1")
    _fresh(tmp_path, "commit", first.token)
    _fresh(tmp_path, "deliver", first.token)
    _fresh(tmp_path, "recover", first.token, "recovery")
    second = _prepare(tmp_path, owner="publisher-2", values={"phase": "second"}, idem="attempt-2")
    _fresh(tmp_path, "commit", second.token)
    _fresh(tmp_path, "deliver", second.token)
    final = _fresh(tmp_path, "acknowledge", second.token)
    artifact = json.loads((tmp_path / "sink/live/config.json").read_text(encoding="utf-8"))
    assert second.fence > first.fence and final["generation"] == 3
    assert artifact == {"fence": second.fence, "generation": 3, "values": {"phase": "second"}}
