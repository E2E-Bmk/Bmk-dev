from __future__ import annotations
import importlib
import json
from pathlib import Path
from typing import Any, Callable


def api() -> Any: return importlib.import_module("networkx.workspace")


def expect(error: type[BaseException], call: Callable[[], Any]) -> BaseException:
    try: call()
    except error as exc: return exc
    raise AssertionError("expected " + error.__name__)


def workspace(path: Path, *, directed: bool = False) -> Any:
    return api().GraphWorkspace(path / "store", directed=directed, multigraph=True)


def commit_graph(store: Any, operation: str, *, owner: str = "alice", branch: str = "main",
                 nodes: tuple[tuple[Any, dict[str, Any]], ...] = (),
                 edges: tuple[tuple[Any, Any, Any, dict[str, Any]], ...] = (),
                 graph: tuple[tuple[str, Any], ...] = ()) -> Any:
    tx = store.begin(owner, branch=branch, operation_id=operation + ":begin")
    for node, attrs in nodes: store.add_node(tx, node, **attrs)
    for u, v, key, attrs in edges: store.add_edge(tx, u, v, key, **attrs)
    for name, value in graph: store.set_graph_attr(tx, name, value)
    return store.commit(tx, operation_id=operation)


def seeded(path: Path, *, directed: bool = False) -> tuple[Any, Any]:
    store = workspace(path, directed=directed)
    revision = commit_graph(store, "seed", nodes=(("a", {"role":"root"}), ("b", {}), ("c", {})),
                            edges=(("a","b","ab",{"weight":1}), ("b","c","bc",{"weight":2})), graph=(("name","seed"),))
    return store, revision


def branch_change(store: Any, branch: str, operation: str, node: str, value: Any) -> Any:
    tx = store.begin("alice", branch=branch, operation_id=operation + ":begin")
    store.add_node(tx, node, color=value)
    return store.commit(tx, operation_id=operation)


def atomic_case(root_id: str, tmp_path: Path) -> None:
    w = api()
    if root_id == "A07":
        store = workspace(tmp_path); tx = store.begin("alice", operation_id="begin")
        store.add_node(tx,"x",rank=1); store.add_edge(tx,"x","y",None,weight=2); revision = store.commit(tx,operation_id="commit")
        snap = store.snapshot(); assert revision.generation == 1 and snap.generation == 1 and len(snap.nodes) == 2 and snap.edges[0][2] == 0
    elif root_id == "A08":
        store, revision = seeded(tmp_path); before = store.snapshot(); tx = store.begin("alice",operation_id="abort")
        store.add_node(tx,"z"); store.abort(tx); assert store.current() == revision and store.snapshot() == before
        expect(w.ConflictError, lambda: store.commit(tx,operation_id="late"))
    elif root_id == "A09":
        store, _ = seeded(tmp_path); one = store.begin("alice",operation_id="one"); two = store.begin("bob",operation_id="two")
        store.add_node(one,"one"); first = store.commit(one,operation_id="first"); store.add_node(two,"two")
        expect(w.ConflictError, lambda: store.commit(two,operation_id="stale")); assert store.current() == first and "two" not in {n for n,_ in store.snapshot().nodes}
    elif root_id == "A10":
        store = workspace(tmp_path); tx = store.begin("alice",operation_id="empty"); zero = store.commit(tx,operation_id="empty-commit")
        assert zero.generation == 0 and store.history() == ()
        tx = store.begin("alice",operation_id="multi"); assert store.add_edge(tx,"a","b") == 0 and store.add_edge(tx,"a","b") == 1
        store.remove_edge(tx,"a","b",0); assert store.add_edge(tx,"a","b") == 0
    elif root_id == "A11":
        store, first = seeded(tmp_path); old = store.snapshot(first.generation)
        commit_graph(store,"later",nodes=(("z",{}),)); assert store.snapshot(first.generation) == old and store.snapshot().digest != old.digest
    elif root_id == "A12":
        left = workspace(tmp_path / "left"); right = workspace(tmp_path / "right")
        for store, order in ((left,(("b","a","k",{"z":2,"a":1}),)),(right,(("a","b","k",{"a":1,"z":2}),))):
            commit_graph(store,"same",nodes=(("b",{}),("a",{})),edges=order,graph=(("z",2),("a",1)))
        assert left.snapshot().digest == right.snapshot().digest and left.current().digest != right.current().digest
    elif root_id == "A13":
        store, _ = seeded(tmp_path,directed=True); lease = store.lease_view("alice",nodes=("a","b"),reverse=True,operation_id="lease")
        view = store.read_view(lease,owner="alice"); assert {(u,v,k) for u,v,k,_ in view.edges} == {("b","a","ab")} and {n for n,_ in view.nodes} == {"a","b"}
    elif root_id == "A14":
        store, _ = seeded(tmp_path); lease = store.lease_view("alice",operation_id="lease"); moved = store.handoff(lease,owner="alice",new_owner="bob",operation_id="move")
        assert moved.fence == lease.fence + 1 and moved.owner == "bob"
        expect(w.OwnershipError, lambda: store.read_view(lease,owner="alice")); expect(w.OwnershipError, lambda: store.read_view(moved,owner="alice"))
    elif root_id == "A15":
        store, _ = seeded(tmp_path); lease = store.lease_view("alice",operation_id="lease")
        one = store.run_algorithm(lease,"alice","shortest_path",parameters=(("source","a"),("target","c")),operation_id="path")
        two = store.run_algorithm(lease,"alice","shortest_path",parameters=(("target","c"),("source","a")),operation_id="path-again")
        assert one == two and one.value == ("a","b","c") and one.snapshot == store.read_view(lease,owner="alice").digest
    elif root_id == "A16":
        store, _ = seeded(tmp_path); commit_graph(store,"second",nodes=(("d",{}),),edges=(("c","d","cd",{}),))
        audit = store.verify(); assert audit.valid and audit.generation_count == 3 and audit.head_digest
    else: raise KeyError(root_id)


def integration_case(root_id: str, tmp_path: Path) -> None:
    w = api()
    if root_id == "I06":
        store, seed = seeded(tmp_path); before = store.snapshot(); tx = store.begin("alice",operation_id="bad")
        expect(w.ConflictError, lambda: store.remove_node(tx,"missing")); store.abort(tx)
        assert store.current() == seed and store.snapshot() == before and len(store.history()) == 1
    elif root_id == "I07":
        store, _ = seeded(tmp_path); tx = store.begin("alice",operation_id="bad-edge"); before = store.snapshot()
        expect(w.ConflictError, lambda: store.remove_edge(tx,"a","c","missing")); store.abort(tx); assert store.snapshot() == before
    elif root_id == "I08":
        store, _ = seeded(tmp_path); tx = store.begin("alice",operation_id="first"); store.add_node(tx,"x"); store.commit(tx,operation_id="unique")
        other = store.begin("alice",operation_id="other"); store.add_node(other,"y")
        expect(w.ConflictError, lambda: store.commit(other,operation_id="unique")); store.abort(other); assert store.current().generation == 2
    elif root_id == "I09":
        store, _ = seeded(tmp_path); store.fork("feature",operation_id="fork")
        branch_change(store,"feature","feature-change","x",1); assert store.current("main").generation == 1 and store.current("feature").generation == 2
        assert "x" not in {n for n,_ in store.snapshot(branch="main").nodes} and "x" in {n for n,_ in store.snapshot(branch="feature").nodes}
    elif root_id == "I10":
        store, _ = seeded(tmp_path); old = store.snapshot(); commit_graph(store,"two",nodes=(("d",{}),)); commit_graph(store,"three",edges=(("c","d","cd",{}),))
        assert store.snapshot(1) == old and [revision.generation for revision in store.history()] == [1,2,3] and store.verify().valid
    elif root_id == "I11":
        store, _ = seeded(tmp_path); old = store.snapshot(); store.fork("feature",generation=old.generation,operation_id="fork")
        branch_change(store,"feature","feature","z",2); assert store.snapshot(old.generation,branch="feature").digest == old.digest
        assert store.snapshot(branch="feature").digest != store.snapshot(branch="main").digest
    elif root_id == "I12":
        store, _ = seeded(tmp_path,directed=True); lease = store.lease_view("alice",nodes=("a","b"),reverse=True,operation_id="lease")
        revision, fresh = store.apply_view(lease,"alice",(("add_edge","b","a","second",(("weight",3),)),),operation_id="apply")
        assert revision.generation == 2 and fresh.generation == 2 and fresh.fence == 2
        assert {key for u,v,key,_ in store.snapshot().edges if (u,v)==("a","b")} == {"ab","second"}
    elif root_id == "I13":
        store, _ = seeded(tmp_path); lease = store.lease_view("alice",nodes=("a","b"),operation_id="lease"); before = store.snapshot()
        expect(w.OwnershipError, lambda: store.apply_view(lease,"alice",(("add_node","outside",()),),operation_id="outside"))
        assert store.snapshot() == before and store.current().generation == 1
    elif root_id == "I14":
        store, _ = seeded(tmp_path); lease = store.lease_view("alice",operation_id="lease"); commit_graph(store,"advance",nodes=(("z",{}),)); before = store.snapshot()
        expect(w.ConflictError, lambda: store.apply_view(lease,"alice",(("add_node","late",()),),operation_id="late"))
        assert store.snapshot() == before and "late" not in {n for n,_ in before.nodes}
    elif root_id == "I15":
        store, _ = seeded(tmp_path); lease = store.lease_view("alice",operation_id="lease"); moved = store.handoff(lease,owner="alice",new_owner="bob",operation_id="move")
        before = store.snapshot(); expect(w.OwnershipError, lambda: store.apply_view(moved,"alice",(("add_node","bad",()),),operation_id="bad"))
        assert store.snapshot() == before
    elif root_id == "I16":
        store, _ = seeded(tmp_path); store.fork("red",operation_id="fork-red"); store.fork("blue",operation_id="fork-blue")
        branch_change(store,"red","red-change","r",1); branch_change(store,"blue","blue-change","b",2)
        merged = store.merge("main",("blue","red"),owner="alice",policy="strict",operation_id="merge")
        assert {"r","b"}.issubset({n for n,_ in store.snapshot().nodes}) and merged.sources == (("blue",3),("red",2))
    elif root_id == "I17":
        store, _ = seeded(tmp_path); store.fork("feature",operation_id="fork")
        branch_change(store,"main","main-change","a","main"); branch_change(store,"feature","feature-change","a","feature")
        merged = store.merge("main",("feature",),owner="alice",policy="ours",operation_id="merge")
        attrs = dict(dict(store.snapshot().nodes)["a"]); assert attrs["color"] == "main" and merged.resolutions
    elif root_id == "I18":
        store, _ = seeded(tmp_path); store.fork("feature",operation_id="fork")
        branch_change(store,"main","main-change","a","main"); branch_change(store,"feature","feature-change","a","feature"); before = store.snapshot()
        expect(w.ConflictError, lambda: store.merge("main",("feature",),owner="alice",policy="strict",operation_id="merge"))
        assert store.snapshot() == before and store.current().generation == before.generation
    elif root_id == "I19":
        store, _ = seeded(tmp_path); store.fork("feature",operation_id="fork"); branch_change(store,"main","main","a","main"); branch_change(store,"feature","feature","a","feature")
        merged = store.merge("main",("feature",),owner="alice",policy="theirs",operation_id="merge")
        assert dict(dict(store.snapshot().nodes)["a"])["color"] == "feature" and any("theirs" in item for item in merged.resolutions)
    elif root_id == "I20":
        store, _ = seeded(tmp_path); pre = store.snapshot(); store.fork("feature",operation_id="fork"); branch_change(store,"feature","change","z",1)
        merged = store.merge("main",("feature",),owner="alice",policy="strict",operation_id="merge")
        compensated = store.compensate(merged,owner="alice",reason="rollback",operation_id="comp")
        assert store.snapshot().digest == pre.digest and compensated.generation > merged.generation and store.verify().valid
    elif root_id == "I21":
        store, _ = seeded(tmp_path); store.fork("feature",operation_id="fork"); branch_change(store,"feature","change","z",1)
        merged = store.merge("main",("feature",),owner="alice",policy="strict",operation_id="merge"); before = store.snapshot()
        expect(w.OwnershipError, lambda: store.compensate(merged,owner="mallory",reason="bad",operation_id="bad")); assert store.snapshot() == before
    elif root_id == "I22":
        store, _ = seeded(tmp_path,directed=True); forward = store.lease_view("alice",operation_id="forward"); reverse = store.lease_view("alice",reverse=True,operation_id="reverse")
        f = store.run_algorithm(forward,"alice","reachable",parameters=(("source","a"),),operation_id="f")
        r = store.run_algorithm(reverse,"alice","reachable",parameters=(("source","c"),),operation_id="r")
        assert f.value == ("a","b","c") and r.value == ("a","b","c") and f.digest != r.digest
    elif root_id == "I23":
        store, _ = seeded(tmp_path); lease = store.lease_view("alice",nodes=("a","b"),operation_id="lease")
        old = store.run_algorithm(lease,"alice","degree",operation_id="old"); commit_graph(store,"advance",edges=(("a","b","extra",{}),))
        fresh = store.refresh(lease,owner="alice",operation_id="refresh"); new = store.run_algorithm(fresh,"alice","degree",operation_id="new")
        assert old.value != new.value and old.digest != new.digest and old.snapshot != new.snapshot
    elif root_id == "I24":
        store, _ = seeded(tmp_path); lease = store.lease_view("alice",operation_id="lease"); result = store.run_algorithm(lease,"alice","degree",operation_id="degree")
        reopened = w.GraphWorkspace(tmp_path / "store",directed=False,multigraph=True); audit = reopened.verify(); reread = reopened.read_view(lease,owner="alice")
        assert audit.valid and reread.digest == store.read_view(lease,owner="alice").digest and result.digest
    else: raise KeyError(root_id)


def system_case(root_id: str, tmp_path: Path) -> None:
    w = api()
    if root_id == "S04":
        store, _ = seeded(tmp_path); old = store.snapshot(); lease = store.lease_view("alice",operation_id="lease")
        commit_graph(store,"advance",nodes=(("z",{}),)); reopened = w.GraphWorkspace(tmp_path / "store")
        assert reopened.snapshot(old.generation) == old and reopened.current().generation == 2
        expect(w.OwnershipError, lambda: reopened.read_view(lease,owner="mallory")); assert reopened.verify().valid
    elif root_id == "S05":
        store, _ = seeded(tmp_path); pre = store.snapshot(); store.fork("red",operation_id="red"); store.fork("blue",operation_id="blue")
        branch_change(store,"red","r","r",1); branch_change(store,"blue","b","b",2); merged = store.merge("main",("red","blue"),owner="alice",policy="strict",operation_id="merge")
        lease = store.lease_view("alice",operation_id="lease"); assert {"r","b"}.issubset(set(store.run_algorithm(lease,"alice","reachable",parameters=(("source","a"),),operation_id="reach").value)) is False
        store.compensate(merged,owner="alice",reason="cancel federation",operation_id="comp"); assert store.snapshot().digest == pre.digest
    elif root_id == "S06":
        store, _ = seeded(tmp_path); store.fork("feature",operation_id="fork"); branch_change(store,"main","m","a","m"); branch_change(store,"feature","f","a","f")
        merged = store.merge("main",("feature",),owner="alice",policy="theirs",operation_id="merge"); store.compensate(merged,owner="alice",reason="revert",operation_id="comp")
        reopened = w.GraphWorkspace(tmp_path / "store"); assert dict(dict(reopened.snapshot().nodes)["a"])["color"] == "m" and reopened.verify().compensation_count == 1
    elif root_id == "S07":
        store, _ = seeded(tmp_path,directed=True); lease = store.lease_view("alice",nodes=("a","b","c"),reverse=True,operation_id="lease")
        _, fresh = store.apply_view(lease,"alice",(("add_edge","c","a","ca",()),),operation_id="view-change")
        result = store.run_algorithm(fresh,"alice","shortest_path",parameters=(("source","c"),("target","a")),operation_id="path")
        store.fork("feature",operation_id="fork"); branch_change(store,"feature","feature","z",1); merged = store.merge("main",("feature",),owner="alice",policy="strict",operation_id="merge")
        store.compensate(merged,owner="alice",reason="rollback",operation_id="comp"); reopened = w.GraphWorkspace(tmp_path / "store",directed=True)
        assert result.value == ("c","a") and reopened.verify().valid and "z" not in {n for n,_ in reopened.snapshot().nodes}
    elif root_id == "S08":
        store, _ = seeded(tmp_path); lease = store.lease_view("alice",nodes=("a","b"),operation_id="lease")
        old = store.run_algorithm(lease,"alice","degree",operation_id="old"); _, fresh = store.apply_view(lease,"alice",(("add_edge","a","b","two",()),),operation_id="apply")
        new = store.run_algorithm(fresh,"alice","degree",operation_id="new"); moved = store.handoff(fresh,owner="alice",new_owner="bob",operation_id="move")
        reopened = w.GraphWorkspace(tmp_path / "store"); assert old.digest != new.digest and reopened.read_view(moved,owner="bob").generation == 2
        expect(w.OwnershipError, lambda: reopened.read_view(fresh,owner="alice")); assert reopened.verify().algorithm_count == 2
    else: raise KeyError(root_id)
