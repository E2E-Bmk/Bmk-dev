from __future__ import annotations

from tests.workspace_support import api, leased, model_class, publish, raises, workspace


def test_s03(tmp_path):
    c = workspace(tmp_path); base = c.snapshot()
    revision, lease, _ = publish(c, [("api", {"raw": 6, "title": "changed"})])
    current = c.refresh(lease, "alice", operation_id="refresh")
    compensation = c.compensate(revision, current, "alice", "restore", operation_id="comp")
    tip = c.snapshot(base); c.close(); reopened = workspace(tmp_path, model_class()())
    assert reopened.values() == dict(base.values) and reopened.generation == 2
    assert len(reopened.history()) == 2 and reopened.compensations() == (compensation,)
    assert tip.parent_digest == base.digest and reopened.verify().stable


def test_s04(tmp_path):
    c = workspace(tmp_path); observed = []
    c.subscribe("audit", lambda revision, values, delivery: observed.append((revision.digest, values["title"], delivery.payload_digest)))
    lease = leased(c); plan = c.plan("layered", [("defaults", {"raw": 2, "normalized": 4, "title": "d"}), ("tenant", {"raw": 8})], lease=lease)
    revision = c.commit(plan, lease, "alice", operation_id="publish")
    delivery = c.delivery(revision.deliveries[0]); snapshot = c.snapshot()
    assert [node.name for node in plan.nodes] == ["raw", "normalized", "title"]
    assert c.provenance_view()["raw"] == "tenant" and dict(snapshot.provenance)["title"] == "defaults"
    assert observed == [(revision.digest, "d", revision.values_digest)]
    assert delivery.revision_digest == revision.digest and delivery.payload_digest == snapshot.content_digest


def test_s05(tmp_path):
    c = workspace(tmp_path); attempts = []
    def offline(*args): attempts.append(args[2].attempt); raise RuntimeError("offline")
    c.subscribe("remote", offline, max_attempts=3)
    base = c.snapshot(); revision, _, _ = publish(c, [("site", {"title": "queued"})]); token = revision.deliveries[0]
    child = c.snapshot(base); c.close()
    reopened = workspace(tmp_path, model_class()()); reopened.subscribe("remote", lambda *args: attempts.append(args[2].attempt), max_attempts=3)
    retried = reopened.retry_delivery(token, "remote", operation_id="retry")
    acknowledged = reopened.ack(token, "remote", operation_id="ack")
    assert attempts == [1, 2] and retried.state == "delivered" and acknowledged.state == "acknowledged"
    assert child.parent_digest == base.digest and reopened.snapshot().deliveries[0].state == "acknowledged"
    assert reopened.verify().stable


def test_s06(tmp_path):
    E = api(); c = workspace(tmp_path); old = leased(c, owner="alice")
    pending = c.plan("old-plan", [("api", {"raw": 5})], lease=old)
    handed = c.handoff(old, "alice", "bob", operation_id="handoff")
    raises(E.OwnershipError, lambda: c.commit(pending, old, "alice", operation_id="stale"))
    fresh_plan = c.plan("bob-plan", [("site", {"raw": 7, "title": "bob"})], lease=handed)
    revision = c.commit(fresh_plan, handed, "bob", operation_id="bob-commit")
    current = c.refresh(handed, "bob", operation_id="refresh")
    compensation = c.compensate(revision, current, "bob", "undo", operation_id="undo")
    assert c.values()["raw"] == 1 and c.values()["title"] == "base"
    assert compensation.generation == 2 and c.verify().stable


def test_s07(tmp_path):
    c = workspace(tmp_path); calls = []; c.subscribe("sink", lambda *args: calls.append(1))
    base = c.snapshot(); lease = leased(c); plan = c.plan("bad", [("api", {"raw": 9, "normalized": 9})], lease=lease)
    c.owner.ceiling = 5
    raises(Exception, lambda: c.commit(plan, lease, "alice", operation_id="bad-commit"))
    child = c.snapshot(base); c.close(); reopened = workspace(tmp_path, model_class()())
    assert reopened.generation == 0 and reopened.values()["raw"] == 1 and reopened.deliveries() == ()
    assert child.values == () and child.revisions == () and calls == [] and reopened.verify().stable


def test_s08(tmp_path):
    c = workspace(tmp_path); c.subscribe("sink", lambda *args: None)
    base = c.snapshot(); first, first_lease, _ = publish(c, [("api", {"raw": 4})], plan_id="one", lease_id="l1", commit_id="c1")
    c.ack(first.deliveries[0], "sink", operation_id="ack-one"); middle = c.snapshot(base)
    second_lease = leased(c, operation_id="l2"); second = c.commit(c.plan("two", [("site", {"title": "second"})], lease=second_lease), second_lease, "alice", operation_id="c2")
    current = c.refresh(second_lease, "alice", operation_id="refresh"); c.compensate(second, current, "alice", "undo-two", operation_id="comp")
    tip = c.snapshot(middle); c.close(); reopened = workspace(tmp_path, model_class()())
    replay_lease = leased(reopened, operation_id="replay-lease"); replay_plan = reopened.plan("one", [("api", {"raw": 4})], lease=replay_lease)
    replay = reopened.commit(replay_plan, replay_lease, "alice", operation_id="replay")
    assert replay.replayed and replay.digest == first.digest and reopened.values()["raw"] == 4 and reopened.values()["title"] == "base"
    assert reopened.delivery(first.deliveries[0]).state == "acknowledged"
    assert tip.parent_digest == middle.digest and len(reopened.history()) == 3 and reopened.verify().stable
