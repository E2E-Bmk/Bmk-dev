from __future__ import annotations

from dataclasses import replace
import hashlib
import importlib
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable


def expect(error: type[BaseException], function: Callable[[], Any]) -> BaseException:
    try:
        function()
    except error as exc:
        return exc
    raise AssertionError("expected " + error.__name__)

def workflow() -> Any:
    module = importlib.import_module("vcr.workflow")
    return SimpleNamespace(
        RecoveryError=module.RecoveryError,
        IntegrityError=module.IntegrityError,
        OwnershipError=module.OwnershipError,
        StaleGenerationError=module.StaleGenerationError,
        IncompleteExchangeError=module.IncompleteReplayError,
        OwnerReceipt=module.OwnerReceipt,
        MatchPolicySnapshot=module.CassetteMatchPolicySnapshot,
        MatchPolicyCatalog=module.CassetteMatchPolicyCatalog,
        RoutePolicyCatalog=module.CassettePlanCatalog,
        CapacityLeaseRegistry=module.PlaybackSessionRegistry,
        ExchangeJournal=module.InteractionJournal,
        WireArtifactIndex=module.CassetteArtifactIndex,
        RetirementObligationLedger=module.PatchObligationLedger,
        ExchangeEventOutbox=module.ReplayEventOutbox,
        ReplayCheckpointLedger=getattr(module, "ReplayCheckpointLedger", None),
        RecoverableExchangeCoordinator=module.DurableReplayCoordinator,
    )


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def atomic_case(root_id: str, tmp_path: Path) -> None:
    w = workflow()
    if root_id == "A09":
        store = w.MatchPolicyCatalog(tmp_path / "policy")
        receipt = store.prepare("private", ("method", "host", "query"), ignored_query=("token",), owner="alice", operation_id="p1")
        assert receipt.state == "prepared"; expect(KeyError, lambda: store.current("private"))
        snapshot = store.commit(receipt); reopened = w.MatchPolicyCatalog(tmp_path / "policy").current("private")
        assert snapshot == reopened and snapshot.match_on == ("method", "host", "query") and snapshot.ignored_query == ("token",) and snapshot.generation == 1
    elif root_id == "A10":
        store = w.MatchPolicyCatalog(tmp_path / "policy")
        active = store.commit(store.prepare("private", ("method", "query"), owner="alice", operation_id="p1"))
        quarantined = store.quarantine(active, reason="query identity was unsafe", owner="alice", operation_id="q1")
        assert quarantined.state == "quarantined" and store.recover("q1", owner="alice") == quarantined
        expect(KeyError, lambda: store.current("private"))
        repaired = store.compensate(quarantined, ("method", "host", "query"), ignored_query=("token",), owner="alice", operation_id="c1")
        assert repaired.state == "active" and repaired.generation == 2 and store.current("private") == repaired
        expect(w.StaleGenerationError, lambda: store.compensate(quarantined, ("method",), owner="alice", operation_id="c2"))
    elif root_id == "A11":
        registry = w.CapacityLeaseRegistry(tmp_path / "selection")
        plan = registry.acquire("run-1", ["build"], {"base": [], "build": ["base"]}, owner="alice", operation_id="s1")
        assert plan.selected == ("base", "build") and plan.generation == 1 and registry.current("run-1") == plan
    elif root_id == "A12":
        registry = w.CapacityLeaseRegistry(tmp_path / "selection")
        old = registry.acquire("run", ["x"], {"x": []}, owner="alice", operation_id="s1")
        new = registry.handoff(old, new_owner="bob", operation_id="s2")
        expect(w.StaleGenerationError, lambda: registry.release(old, operation_id="s3")); assert new.selected == old.selected and registry.current("run").owner == "bob"
    elif root_id == "A13":
        journal = w.ExchangeJournal(tmp_path / "journal")
        attempt = journal.begin("build", owner="alice", operation_id="j1")
        completed = journal.complete(attempt, result="ok", values={"x": 1})
        acknowledged = journal.acknowledge(completed, owner="alice", operation_id="j2")
        assert (attempt.state, completed.state, acknowledged.state) == ("prepared", "completed", "acknowledged") and journal.current("build") == acknowledged
    elif root_id == "A14":
        index = w.WireArtifactIndex(tmp_path / "targets")
        receipt = index.prepare("build", {"a.txt": "héllo", "b.bin": b"\x00\xff"}, owner="alice", operation_id="t1")
        expect(KeyError, lambda: index.current("build")); snapshot = index.publish(receipt)
        assert index.read("build", "a.txt") == "héllo".encode() and index.read("build", "b.bin") == b"\x00\xff" and index.verify(snapshot)
    elif root_id == "A15":
        ledger = w.RetirementObligationLedger(tmp_path / "life")
        item = ledger.open("build", ("one", "two"), ("one", "two"), owner="alice", operation_id="l1")
        item = ledger.setup(item, "one"); item = ledger.setup(item, "two"); item = ledger.body(item, "success")
        item = ledger.teardown(item, "two"); item = ledger.teardown(item, "one"); item = ledger.close(item)
        assert item.state == "closed" and item.completed_teardowns == ("two", "one")
    elif root_id == "A16":
        ledger = w.ReplayCheckpointLedger(tmp_path / "checkpoint")
        one, two = _sha("one"), _sha("two")
        opened = ledger.open("run", "cassette", (one, two), owner="alice", operation_id="c1")
        expect(w.RecoveryError, lambda: ledger.advance(opened, two, owner="alice", operation_id="bad"))
        first = ledger.advance(opened, one, owner="alice", operation_id="c2")
        assert first.position == 1 and w.ReplayCheckpointLedger(tmp_path / "checkpoint").current("run", "cassette") == first
        expect(w.IncompleteExchangeError, lambda: ledger.complete(first, owner="alice", operation_id="early"))
        second = ledger.advance(first, two, owner="alice", operation_id="c3")
        completed = ledger.complete(second, owner="alice", operation_id="c4")
        assert completed.position == 2 and completed.state == "completed" and ledger.recover("c4", owner="alice") == completed
    else:
        raise KeyError(root_id)


def _owners(tmp_path: Path) -> tuple[Any, Any, Any, Any, Any, Any]:
    w = workflow()
    return (w.RoutePolicyCatalog(tmp_path / "d"), w.CapacityLeaseRegistry(tmp_path / "s"), w.ExchangeJournal(tmp_path / "j"),
            w.WireArtifactIndex(tmp_path / "t"), w.RetirementObligationLedger(tmp_path / "l"), w.ExchangeEventOutbox(tmp_path / "o"))


def integration_case(root_id: str, tmp_path: Path) -> None:
    w = workflow(); definitions, selections, journal, targets, lifecycle, outbox = _owners(tmp_path)
    definition = definitions.commit(definitions.prepare("build", {"kind": "direct", "destination": "build.test", "deps": [], "artifacts": ["out"]}, owner="alice", operation_id="d1"))
    plan = selections.acquire("run", ["build"], {"build": []}, owner="alice", operation_id="s1")
    if root_id == "I05":
        import vcr
        policies = w.MatchPolicyCatalog(tmp_path / "policy")
        policy = policies.commit(policies.prepare("private", ("method", "host", "path", "query"), ignored_query=("token",), owner="alice", operation_id="p1"))
        left = vcr.request.Request("GET", "http://example.test/items?keep=1&token=old", None, {})
        right = vcr.request.Request("GET", "http://example.test/items?token=new&keep=1", None, {})
        other = vcr.request.Request("GET", "http://example.test/other?keep=1&token=new", None, {})
        assert policies.equivalent(policy, left, right) and not policies.equivalent(policy, left, other)
        assert policies.request_key(policy, left) == policies.request_key(policy, right)
    elif root_id == "I06":
        policies = w.MatchPolicyCatalog(tmp_path / "policy")
        unsafe = policies.commit(policies.prepare("private", ("method", "query"), owner="alice", operation_id="p1"))
        quarantined = policies.quarantine(unsafe, reason="redaction change", owner="alice", operation_id="q1")
        repaired = policies.compensate(quarantined, ("method", "host", "query"), ignored_query=("token",), owner="alice", operation_id="c1")
        attempt = journal.begin("build", owner="alice", operation_id="j1", prerequisites=(repaired.receipt,))
        assert repaired.receipt.digest in attempt.receipt.prerequisites and policies.recover("q1", owner="alice") == quarantined
    elif root_id == "I07":
        policies = w.MatchPolicyCatalog(tmp_path / "policy")
        first = policies.commit(policies.prepare("private", ("method", "query"), owner="alice", operation_id="p1"))
        quarantined = policies.quarantine(first, reason="matcher revision", owner="alice", operation_id="q1")
        repaired = policies.compensate(quarantined, ("method", "host", "query"), owner="alice", operation_id="c1")
        snapshot = targets.seal("build", {"cassette.yaml": b"exact\x00bytes"}, owner="alice", operation_id="t1", prerequisites=(repaired.receipt,))
        reopened = w.MatchPolicyCatalog(tmp_path / "policy").current("private")
        assert reopened == repaired and repaired.receipt.digest in snapshot.receipt.prerequisites and targets.read("build", "cassette.yaml") == b"exact\x00bytes"
    elif root_id == "I08":
        closure = selections.acquire("run-2", ["left", "right", "left"], {"base": [], "left": ["base"], "right": ["base"]}, owner="alice", operation_id="s2")
        assert closure.selected == ("base", "left", "right") and len(closure.selected) == len(set(closure.selected))
    elif root_id == "I09":
        moved = selections.handoff(plan, new_owner="bob", operation_id="s2"); expect(w.StaleGenerationError, lambda: selections.release(plan, operation_id="s3"))
        attempt = journal.begin("build", owner=moved.owner, operation_id="j1", prerequisites=(moved.receipt,)); assert attempt.owner == "bob"
    elif root_id == "I10":
        moved = selections.handoff(plan, new_owner="bob", operation_id="s2")
        receipt = outbox.prepare("run", ({"selected": list(moved.selected)},), owner=moved.owner, operation_id="o1", prerequisites=(moved.receipt,))
        assert outbox.publish(receipt).owner == "bob" and selections.current("run").selected == ("build",)
    elif root_id == "I11":
        expect(w.RecoveryError, lambda: selections.acquire("bad", ["missing"], {"build": []}, owner="alice", operation_id="s2"))
        attempt = journal.begin(plan.selected[0], owner="alice", operation_id="j1", prerequisites=(plan.receipt,)); assert attempt.task == "build"
    elif root_id == "I12":
        attempt = journal.begin("build", owner="alice", operation_id="j1"); failed = journal.fail(attempt, category="failure", detail="bad")
        item = lifecycle.open("build", ("one",), ("one",), owner="alice", operation_id="l1", prerequisites=(failed.receipt,))
        item = lifecycle.setup(item, "one"); item = lifecycle.body(item, "failure"); item = lifecycle.teardown(item, "one"); assert lifecycle.close(item).state == "closed"
        expect(w.IncompleteExchangeError, lambda: journal.acknowledge(failed, owner="alice", operation_id="j2")); expect(KeyError, lambda: journal.current("build"))
    elif root_id == "I13":
        attempt = journal.begin("build", owner="alice", operation_id="j1"); completed = journal.complete(attempt, result="ok")
        snapshot = targets.seal("build", {"out": "ok"}, owner="alice", operation_id="t1", prerequisites=(completed.receipt,)); assert targets.verify(snapshot)
        acknowledged = journal.acknowledge(completed, owner="alice", operation_id="j2"); assert journal.current("build") == acknowledged
    elif root_id == "I14":
        attempt = journal.begin("build", owner="alice", operation_id="j1"); failed = journal.fail(attempt, category="error")
        receipt = outbox.prepare("failure", ({"state": "failed"},), owner="alice", operation_id="o1", prerequisites=(failed.receipt,)); batch = outbox.publish(receipt)
        expect(w.IncompleteExchangeError, lambda: journal.acknowledge(failed, owner="alice", operation_id="j2")); assert dict(outbox.events(batch.batch_id)[0])["state"] == "failed"
    elif root_id == "I15":
        snapshot = targets.seal("build", {"out": "one"}, owner="alice", operation_id="t1", prerequisites=(definition.receipt,)); assert definition.receipt.digest in snapshot.receipt.prerequisites
    elif root_id == "I16":
        prepared = targets.prepare("build", {"out": "new"}, owner="alice", operation_id="t1"); expect(KeyError, lambda: targets.current("build"))
        recovered = targets.recover("t1", owner="alice"); assert recovered == prepared and targets.publish(recovered).targets == (("out", "6e6577"),)
    elif root_id == "I17":
        one = targets.seal("one", {"one": "1"}, owner="alice", operation_id="t1"); two = targets.seal("two", {"two": "2"}, owner="alice", operation_id="t2")
        changed = targets.seal("one", {"one": "new"}, owner="alice", operation_id="t3"); assert changed.generation == one.generation + 1 and targets.current("two") == two
    elif root_id == "I18":
        snapshot = targets.seal("build", {"out": "ok"}, owner="alice", operation_id="t1")
        altered = replace(snapshot, receipt=replace(snapshot.receipt, digest="0" * 64)); expect(w.IntegrityError, lambda: targets.verify(altered))
        assert targets.read("build", "out") == b"ok" and outbox.pending() == ()
    elif root_id == "I19":
        item = lifecycle.open("build", ("setup",), ("teardown",), owner="alice", operation_id="l1", prerequisites=(plan.receipt,)); assert plan.receipt.digest in item.receipt.prerequisites
    elif root_id == "I20":
        item = lifecycle.open("build", ("outer", "inner"), ("outer", "inner"), owner="alice", operation_id="l1")
        item = lifecycle.setup(item, "outer"); item = lifecycle.setup(item, "inner"); item = lifecycle.body(item, "failure")
        item = lifecycle.teardown(item, "inner"); item = lifecycle.teardown(item, "outer"); assert lifecycle.close(item).completed_teardowns == ("inner", "outer")
    elif root_id == "I21":
        old = targets.seal("build", {"out": "old"}, owner="alice", operation_id="t1")
        item = lifecycle.open("build", ("setup",), ("teardown",), owner="alice", operation_id="l1"); item = lifecycle.setup(item, "setup")
        expect(w.IncompleteExchangeError, lambda: lifecycle.close(item)); assert targets.current("build") == old
    elif root_id == "I22":
        item = lifecycle.open("build", ("setup",), ("teardown",), owner="alice", operation_id="l1"); item = lifecycle.setup(item, "setup"); item = lifecycle.body(item, "success"); item = lifecycle.teardown(item, "teardown"); closed = lifecycle.close(item)
        batch = outbox.publish(outbox.prepare("life", ({"state": "setup"}, {"state": "body"}, {"state": "teardown"}), owner="alice", operation_id="o1", prerequisites=(closed.receipt,)))
        assert [dict(event)["state"] for event in batch.events] == ["setup", "body", "teardown"]
    elif root_id == "I23":
        attempt = journal.begin("build", owner="alice", operation_id="j1"); acknowledged = journal.acknowledge(journal.complete(attempt), owner="alice", operation_id="j2")
        batch = outbox.publish(outbox.prepare("done", ({"task": "build"},), owner="alice", operation_id="o1", prerequisites=(acknowledged.receipt,)))
        claimed = outbox.claim("done", owner="worker", operation_id="o2"); assert outbox.acknowledge(claimed, owner="worker", operation_id="o3").state == "acknowledged" and outbox.pending() == ()
    elif root_id == "I24":
        moved = selections.handoff(plan, new_owner="bob", operation_id="s2")
        ledger = w.ReplayCheckpointLedger(tmp_path / "checkpoint"); one, two = _sha("one"), _sha("two")
        checkpoint = ledger.open("run", "build", (one, two), owner="bob", operation_id="c1", prerequisites=(moved.receipt,))
        checkpoint = ledger.advance(checkpoint, one, owner="bob", operation_id="c2")
        assert outbox.pending() == ()
        checkpoint = ledger.complete(ledger.advance(checkpoint, two, owner="bob", operation_id="c3"), owner="bob", operation_id="c4")
        event_receipt = outbox.prepare("done", ({"digest": one}, {"digest": two}), owner="bob", operation_id="o1", prerequisites=(checkpoint.receipt,))
        batch = outbox.publish(event_receipt)
        assert [dict(event)["digest"] for event in batch.events] == [one, two]
        assert checkpoint.receipt.digest in event_receipt.prerequisites and event_receipt.digest in batch.receipt.prerequisites
        assert ledger.current("run", "build") == checkpoint
    else:
        raise KeyError(root_id)


def _definitions() -> dict[str, dict[str, Any]]:
    return {
        "base": {"kind": "direct", "destination": "base.test", "deps": [], "artifacts": ["base.wire"]},
        "build": {"kind": "proxy", "destination": "build.test", "deps": ["base"], "artifacts": ["build.wire"]},
    }


def system_case(root_id: str, tmp_path: Path) -> None:
    w = workflow(); coordinator = w.RecoverableExchangeCoordinator(tmp_path / "workflow")
    if root_id in {"S03", "S04", "S05", "S06", "S07", "S08"}:
        prepared = coordinator.plan(_definitions(), ["build"], invocation_id="run", owner="alice", operation_id="w1")
    if root_id == "S03":
        executed = coordinator.execute(prepared); published = coordinator.publish(executed, owner="alice", operation_id="publish")
        assert coordinator.verify(published) and set(coordinator.owner_generations("build")) == {"definition", "selection", "journal", "artifact", "lifecycle", "outbox"}
    elif root_id == "S04":
        first = coordinator.publish(coordinator.execute(prepared), owner="alice", operation_id="publish")
        retry = coordinator.plan(_definitions(), ["build"], invocation_id="run-2", owner="alice", operation_id="w2")
        failed = coordinator.execute(retry, runner=lambda task, definition: 5); expect(w.IncompleteExchangeError, lambda: coordinator.publish(failed, owner="alice", operation_id="bad"))
        assert coordinator.current("build") == first
    elif root_id == "S05":
        moved = coordinator.handoff("w1", current_owner="alice", new_owner="bob", transfer_operation_id="move")
        expect(w.OwnershipError, lambda: coordinator.execute(prepared)); published = coordinator.publish(coordinator.execute(moved), owner="bob", operation_id="publish")
        assert w.RecoverableExchangeCoordinator(tmp_path / "workflow").current("build") == published
    elif root_id == "S06":
        same = coordinator.plan(_definitions(), ["build"], invocation_id="run", owner="alice", operation_id="w1"); assert same == prepared
        expect(w.RecoveryError, lambda: coordinator.plan({"other": {"kind": "direct", "destination": "other.test", "deps": []}}, ["other"], invocation_id="run", owner="alice", operation_id="w1"))
        assert coordinator.verify(coordinator.recover("w1", owner="alice"))
    elif root_id == "S07":
        selections = w.CapacityLeaseRegistry(tmp_path / "checkpoint-flow" / "sessions")
        plan = selections.acquire("replay", ["build"], {"build": []}, owner="alice", operation_id="s1")
        moved = selections.handoff(plan, new_owner="bob", operation_id="s2")
        ledger = w.ReplayCheckpointLedger(tmp_path / "checkpoint-flow" / "checkpoints"); one, two = _sha("one"), _sha("two")
        opened = ledger.open("replay", "build", (one, two), owner="bob", operation_id="c1", prerequisites=(moved.receipt,))
        first = ledger.advance(opened, one, owner="bob", operation_id="c2")
        transferred = ledger.handoff(first, new_owner="carol", operation_id="c3")
        expect(w.StaleGenerationError, lambda: ledger.advance(first, two, owner="bob", operation_id="stale"))
        reopened = w.ReplayCheckpointLedger(tmp_path / "checkpoint-flow" / "checkpoints").current("replay", "build")
        completed = ledger.complete(ledger.advance(reopened, two, owner="carol", operation_id="c4"), owner="carol", operation_id="c5")
        journal = w.ExchangeJournal(tmp_path / "checkpoint-flow" / "journal")
        attempt = journal.begin("build", owner="carol", operation_id="j1", prerequisites=(completed.receipt,))
        acknowledged = journal.acknowledge(journal.complete(attempt, result="ok"), owner="carol", operation_id="j2")
        outbox = w.ExchangeEventOutbox(tmp_path / "checkpoint-flow" / "outbox")
        event_receipt = outbox.prepare("replayed", ({"digest": one}, {"digest": two}), owner="carol", operation_id="o1", prerequisites=(acknowledged.receipt,))
        batch = outbox.publish(event_receipt)
        claimed = outbox.claim(batch.batch_id, owner="worker", operation_id="o2"); outbox.acknowledge(claimed, owner="worker", operation_id="o3")
        assert transferred.generation == first.generation + 1 and completed.position == 2 and completed.state == "completed"
        assert completed.receipt.digest in attempt.receipt.prerequisites and acknowledged.receipt.digest in event_receipt.prerequisites
        assert event_receipt.digest in batch.receipt.prerequisites
        assert [dict(event)["digest"] for event in batch.events] == [one, two] and outbox.pending() == ()
    elif root_id == "S08":
        published = coordinator.publish(coordinator.execute(prepared), owner="alice", operation_id="publish")
        altered = replace(published, digest="f" * 64, prerequisites=(published.digest,)); expect(w.IntegrityError, lambda: coordinator.verify(altered))
        assert coordinator.current("build") == published
    else:
        raise KeyError(root_id)
