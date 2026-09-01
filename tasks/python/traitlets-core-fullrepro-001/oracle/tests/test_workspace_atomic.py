from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

from tests.workspace_support import DEPENDENCIES, NAMES, api, leased, model_class, raises, workspace


def test_a09(tmp_path):
    E = api(); owner = model_class()()
    raises(E.WorkspaceError, lambda: E.ConfigWorkspace(tmp_path / "unknown", owner, "x", NAMES, {"title": ("missing",)}))
    raises(E.WorkspaceError, lambda: E.ConfigWorkspace(tmp_path / "cycle", model_class()(), "y", NAMES, {"raw": ("title",), "title": ("raw",)}))
    assert not (tmp_path / "unknown").exists() or not list((tmp_path / "unknown").glob("*.json"))


def test_a10(tmp_path):
    c = workspace(tmp_path); lease = leased(c)
    layers = [("base", {"raw": 7})]
    plan = c.plan("p", layers, lease=lease); layers[0][1]["raw"] = 99
    assert c.owner.raw == 1 and plan.nodes[0].new == 7
    raises(FrozenInstanceError, lambda: setattr(plan, "operation_id", "other"))


def test_a11(tmp_path):
    c = workspace(tmp_path); lease = leased(c)
    plan = c.plan("ordered", [("defaults", {"title": "T", "normalized": 5, "raw": 3}), ("tenant", {"raw": 8})], lease=lease)
    assert [(node.name, node.source) for node in plan.nodes] == [("raw", "tenant"), ("normalized", "defaults"), ("title", "defaults")]
    assert [node.depends_on for node in plan.nodes] == [(), ("raw",), ("normalized",)]
    assert c.values()["raw"] == 1 and c.provenance_view()["raw"] == "initial"


def test_a12(tmp_path):
    left = workspace(tmp_path / "left", workspace_id="same")
    right = workspace(tmp_path / "right", workspace_id="same")
    a = left.plan("same", [("base", {"title": "T", "raw": 4}), ("site", {"mode": "hot"})], lease=leased(left, operation_id="l"))
    b = right.plan("same", [("base", {"raw": 4, "title": "T"}), ("site", {"mode": "hot"})], lease=leased(right, operation_id="l"))
    assert a.digest == b.digest and len(a.digest) == 64 and a.digest == a.digest.lower()


def test_a13(tmp_path):
    c = workspace(tmp_path); lease = leased(c, owner="alice", operation_id="owned")
    assert lease.workspace_id == "workspace" and lease.owner == "alice" and lease.generation == 0 and lease.fence == 1
    assert len(lease.digest) == 64
    raises(FrozenInstanceError, lambda: setattr(lease, "fence", 2))


def test_a14(tmp_path):
    c = workspace(tmp_path); lease = leased(c)
    plan = c.plan("empty", [], lease=lease)
    revision = c.commit(plan, lease, "alice", operation_id="empty-commit")
    assert not revision.changed and revision.generation == 0 and revision.changes == ()
    assert c.generation == 0 and c.history() == ()


def test_a15(tmp_path):
    E = api(); left = workspace(tmp_path / "left", workspace_id="left"); right = workspace(tmp_path / "right", workspace_id="right")
    lease = leased(left); plan = left.plan("x", [("api", {"raw": 4})], lease=lease)
    raises(E.OwnershipError, lambda: right.commit(plan, leased(right), "alice", operation_id="foreign"))
    raises(E.IntegrityError, lambda: left.commit(replace(plan, digest="0" * 64), lease, "alice", operation_id="tampered"))
    assert left.owner.raw == right.owner.raw == 1 and left.generation == right.generation == 0


def test_a16(tmp_path):
    E = api(); c = workspace(tmp_path); old = leased(c, owner="alice", operation_id="l")
    current = c.handoff(old, "alice", "bob", operation_id="handoff")
    assert current.owner == "bob" and current.fence == old.fence + 1 and current.generation == old.generation
    raises(E.OwnershipError, lambda: c.refresh(old, "alice", operation_id="stale"))
    assert c.refresh(current, "bob", operation_id="fresh").fence == current.fence + 1

