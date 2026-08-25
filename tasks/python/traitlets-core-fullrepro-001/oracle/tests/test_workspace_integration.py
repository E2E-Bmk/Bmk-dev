from __future__ import annotations

from tests.workspace_support import api, leased, model_class, publish, raises, workspace


def test_i05(tmp_path):
    c = workspace(tmp_path); lease = leased(c)
    plan = c.plan("layers", [("defaults", {"raw": 2, "normalized": 4, "title": "d"}), ("site", {"raw": 9})], lease=lease)
    assert [(n.name, n.depends_on, n.source) for n in plan.nodes] == [
        ("raw", (), "site"), ("normalized", ("raw",), "defaults"), ("title", ("normalized",), "defaults")]
    revision = c.commit(plan, lease, "alice", operation_id="publish")
    assert c.provenance_view()["raw"] == "site" and c.provenance_view()["title"] == "defaults"
    assert [(n.name, n.source) for n in revision.changes] == [(n.name, n.source) for n in plan.nodes]


def test_i06(tmp_path):
    E = api(); c = workspace(tmp_path)
    old = leased(c, operation_id="old"); pending = c.plan("pending", [("api", {"raw": 7})], lease=old)
    other = leased(c, operation_id="other"); c.commit(c.plan("advance", [("site", {"title": "new"})], lease=other), other, "alice", operation_id="advance-commit")
    before = (c.values(), c.generation, c.history())
    raises((E.ConflictError, E.OwnershipError), lambda: c.commit(pending, old, "alice", operation_id="stale-commit"))
    assert (c.values(), c.generation, c.history()) == before


def test_i07(tmp_path):
    c = workspace(tmp_path); seen = []
    c.owner.observe(lambda change: seen.append((change.name, c.owner.raw, c.owner.normalized, c.owner.title)), names=["raw", "normalized", "title"])
    revision, lease, plan = publish(c, [("api", {"raw": 4, "normalized": 6, "title": "ready"})])
    assert revision.generation == c.generation == 1 and revision.changed
    assert c.values()["title"] == c.config_view()["title"] == "ready" and c.provenance_view()["title"] == "api"
    assert len(seen) == 3 and all(row[1:] == (4, 6, "ready") for row in seen)
    assert c.history() == (revision,) and revision.predecessor_digest


def test_i08(tmp_path):
    E = api(); c = workspace(tmp_path); called = []
    c.subscribe("sink", lambda *args: called.append(1))
    lease = leased(c); plan = c.plan("bad", [("api", {"raw": 8, "normalized": 20})], lease=lease)
    before = (c.values(), c.config_view(), c.provenance_view(), c.generation, c.history(), c.deliveries())
    c.owner.ceiling = 10
    raises(Exception, lambda: c.commit(plan, lease, "alice", operation_id="bad-commit"))
    assert (c.values(), c.config_view(), c.provenance_view(), c.generation, c.history(), c.deliveries()) == before
    assert called == []


def test_i09(tmp_path):
    c = workspace(tmp_path); before = c.snapshot()
    revision, lease, _ = publish(c, [("api", {"raw": 8, "title": "changed"})])
    current = c.refresh(lease, "alice", operation_id="refresh")
    compensation = c.compensate(revision, current, "alice", "rollback", operation_id="compensate")
    assert c.values() == dict(before.values) and c.provenance_view() == dict(before.provenance)
    assert c.generation == compensation.generation == 2 and compensation.revision_digest == revision.digest
    assert len(c.history()) == 2 and c.history()[-1].compensation_of == revision.digest


def test_i10(tmp_path):
    E = api(); c = workspace(tmp_path)
    first, first_lease, _ = publish(c, [("api", {"raw": 2})], plan_id="p1", lease_id="l1", commit_id="c1")
    lease2 = leased(c, operation_id="l2"); lease2 = c.refresh(lease2, "alice", operation_id="l2-refresh") if lease2.generation != c.generation else lease2
    second = c.commit(c.plan("p2", [("api", {"title": "two"})], lease=lease2), lease2, "alice", operation_id="c2")
    current = c.refresh(lease2, "alice", operation_id="current")
    before = (c.generation, c.values(), c.history())
    raises(E.ConflictError, lambda: c.compensate(first, current, "alice", "stale", operation_id="stale-comp"))
    raises(E.OwnershipError, lambda: c.compensate(second, current, "mallory", "foreign", operation_id="foreign-comp"))
    compensation = c.compensate(second, current, "alice", "valid", operation_id="valid-comp")
    newer = c.refresh(current, "alice", operation_id="after-comp")
    raises(E.ConflictError, lambda: c.compensate(second, newer, "alice", "duplicate", operation_id="duplicate-comp"))
    assert c.generation == before[0] + 1 and compensation.generation == c.generation


def test_i11(tmp_path):
    c = workspace(tmp_path); publish(c, [("z", {"title": "x", "raw": 3}), ("a", {"mode": "hot"})])
    snapshot = c.snapshot(); transport = snapshot.to_dict()
    transport["values"] = {key: transport["values"][key] for key in reversed(list(transport["values"]))}
    transport["provenance"] = {key: transport["provenance"][key] for key in reversed(list(transport["provenance"]))}
    assert api().WorkspaceSnapshot.from_dict(transport).digest == snapshot.digest
    assert len(snapshot.digest) == 64 and snapshot.base and snapshot.parent_digest is None


def test_i12(tmp_path):
    c = workspace(tmp_path); base = c.snapshot()
    publish(c, [("api", {"title": "delta"})])
    child = c.snapshot(base)
    assert not child.base and child.parent_digest == base.digest
    assert dict(child.values) == {"title": "delta"} and dict(child.provenance) == {"title": "api"}
    assert len(child.revisions) == 1


def test_i13(tmp_path):
    owner = model_class()(); c = workspace(tmp_path, owner)
    publish(c, [("site", {"raw": 7, "mode": "hot"})])
    identity = c.workspace_id; c.close()
    reopened = workspace(tmp_path, model_class()(), identity)
    assert reopened.values() == c.values() and reopened.config_view() == c.config_view()
    assert reopened.provenance_view() == c.provenance_view() and reopened.generation == 1
    assert reopened.verify().stable


def test_i14(tmp_path):
    E = api(); c = workspace(tmp_path); publish(c, [("api", {"raw": 4})]); c.close()
    files = [path for path in tmp_path.rglob("*") if path.is_file()]
    assert files
    target = max(files, key=lambda path: path.stat().st_size); data = target.read_bytes()
    target.write_bytes(data[: max(1, len(data) // 2)])
    raises(E.IntegrityError, lambda: workspace(tmp_path, model_class()()))


def test_i15(tmp_path):
    c = workspace(tmp_path); base = c.snapshot(); detached = base.to_dict(); detached["values"]["raw"] = 99
    publish(c, [("api", {"raw": 8})]); c.close(); reopened = workspace(tmp_path, model_class()())
    assert dict(base.values)["raw"] == 1 and reopened.values()["raw"] == 8
    assert reopened.snapshot().digest != base.digest and base.generation == 0


def test_i16(tmp_path):
    c = workspace(tmp_path); calls = []
    c.subscribe("sink", lambda revision, values, delivery: calls.append((revision.generation, values["raw"], delivery.state)))
    revision, _, _ = publish(c, [("api", {"raw": 6})])
    delivery = c.delivery(revision.deliveries[0])
    assert calls == [(1, 6, "delivering")] and delivery.state == "delivered" and delivery.attempt == 1
    assert delivery.payload_digest == revision.values_digest


def test_i17(tmp_path):
    E = api(); c = workspace(tmp_path); c.subscribe("sink", lambda *args: None)
    revision, _, _ = publish(c, [("api", {"raw": 3})]); token = revision.deliveries[0]
    raises(E.DeliveryError, lambda: c.ack(token, "other", operation_id="wrong"))
    acknowledged = c.ack(token, "sink", operation_id="ack")
    assert acknowledged.state == "acknowledged" and c.ack(token, "sink", operation_id="ack") == acknowledged
    raises(E.DeliveryError, lambda: c.retry_delivery(token, "sink", operation_id="retry-acked"))


def test_i18(tmp_path):
    c = workspace(tmp_path); attempts = []
    def flaky(*args):
        attempts.append(args[2].attempt)
        if len(attempts) == 1: raise RuntimeError("offline")
    c.subscribe("worker", flaky, max_attempts=3)
    revision, _, _ = publish(c, [("api", {"raw": 5})]); token = revision.deliveries[0]
    assert c.delivery(token).state == "retryable"
    retried = c.retry_delivery(token, "worker", operation_id="retry")
    assert retried.state == "delivered" and retried.attempt == 2 and attempts == [1, 2]
    assert c.ack(token, "worker", operation_id="ack").state == "acknowledged"


def test_i19(tmp_path):
    E = api(); c = workspace(tmp_path); c.subscribe("dead", lambda *args: (_ for _ in ()).throw(RuntimeError()), max_attempts=2); c.subscribe("good", lambda *args: None)
    revision, _, _ = publish(c, [("api", {"raw": 4})]); dead, good = revision.deliveries
    assert c.delivery(dead).state == "retryable" and c.delivery(good).state == "delivered"
    assert c.retry_delivery(dead, "dead", operation_id="retry").state == "poison"
    raises(E.DeliveryError, lambda: c.retry_delivery(dead, "dead", operation_id="again"))


def test_i20(tmp_path):
    c = workspace(tmp_path); c.subscribe("worker", lambda *args: (_ for _ in ()).throw(RuntimeError()), max_attempts=3)
    revision, _, _ = publish(c, [("api", {"title": "queued"})]); token = revision.deliveries[0]; c.close()
    reopened = workspace(tmp_path, model_class()()); calls = []
    reopened.subscribe("worker", lambda *args: calls.append(args[2].attempt), max_attempts=3)
    assert reopened.delivery(token).state == "retryable"
    assert reopened.retry_delivery(token, "worker", operation_id="resume").state == "delivered" and calls == [2]


def test_i21(tmp_path):
    c = workspace(tmp_path, model_class()(secret="keep")); lease = leased(c)
    plan = c.plan("filter", [("base", {"raw": 2, "secret": "leak", "unknown": 9}), ("tenant", {"raw": 8, "mode": "hot"})], lease=lease)
    revision = c.commit(plan, lease, "alice", operation_id="commit")
    assert c.owner.secret == "keep" and c.owner.raw == 8 and c.owner.mode == "hot"
    assert {node.name: node.source for node in revision.changes} == {"raw": "tenant", "mode": "tenant"}
    assert c.provenance_view()["raw"] == "tenant"


def test_i22(tmp_path):
    c = workspace(tmp_path); lease = leased(c); plan = c.plan("dag", [("api", {"title": "ready", "normalized": 7, "raw": 3})], lease=lease)
    revision = c.commit(plan, lease, "alice", operation_id="txn")
    assert revision.generation == 1 and revision.plan_digest == plan.digest and revision.lease_fence == lease.fence
    assert tuple(node.name for node in revision.changes) == ("raw", "normalized", "title")
    assert revision.values_digest == c.snapshot().content_digest


def test_i23(tmp_path):
    c = workspace(tmp_path); layers = [("api", {"raw": 7})]; revision, _, _ = publish(c, layers, plan_id="durable", commit_id="first"); c.close()
    reopened = workspace(tmp_path, model_class()()); lease = leased(reopened, operation_id="replay-lease")
    replay_plan = reopened.plan("durable", layers, lease=lease)
    replay = reopened.commit(replay_plan, lease, "alice", operation_id="replay-commit")
    assert replay_plan.replayed and replay.replayed and replay.digest == revision.digest
    assert reopened.generation == 1 and len(reopened.history()) == 1


def test_i24(tmp_path):
    c = workspace(tmp_path); c.subscribe("sink", lambda *args: None)
    revision, _, _ = publish(c, [("api", {"raw": 9})]); delivery = c.delivery(revision.deliveries[0]); snapshot = c.snapshot()
    assert delivery.revision_digest == revision.digest
    assert delivery.payload_digest == revision.values_digest == snapshot.content_digest
    assert snapshot.deliveries[0].digest == delivery.digest and snapshot.revisions[0] == revision.digest

