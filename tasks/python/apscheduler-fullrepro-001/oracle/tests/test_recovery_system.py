from __future__ import annotations

from tests.recovery_support import completed, lane_state, new_state, raises


def test_s03(tmp_path):
    state = new_state()
    state.define_lane("source", owner="alpha", artifacts=("raw",))
    state.define_lane("left", owner="alpha", parents=("source",), artifacts=("bundle",))
    state.define_lane("right", owner="beta", parents=("source",), artifacts=("bundle",))
    assert [(item["lane_id"], item["owner"], item["parents"]) for item in state.lanes()] == [
        ("source", "alpha", ()), ("left", "alpha", ("source",)), ("right", "beta", ("source",))]


def test_s04(tmp_path):
    state = lane_state(); state.submit("d", lane_id="ingest", scheduled_for=0, payload_digest="p")
    one = state.acquire("d", worker="a", now=0, ttl=5)
    state.renew("d", one["token"], now=1, ttl=5); state.release("d", one["token"], now=2)
    two = state.acquire("d", worker="b", now=2, ttl=2); assert state.expire(now=4) == ["d"]
    three = state.acquire("d", worker="c", now=4, ttl=5)
    record = state.record_outcome("d", three["token"], outcome="success", finished_at=5, artifacts=("raw",))
    assert (one["generation"], two["generation"], three["generation"], record["generation"]) == (1, 2, 3, 3)


def test_s05(tmp_path):
    state = lane_state(two=True)
    state.submit("a", lane_id="ingest", scheduled_for=0, payload_digest="a")
    state.submit("b", lane_id="publish", scheduled_for=0, payload_digest="b", dependencies=("a",))
    completed(state, dispatch_id="a", now=0, artifacts=("raw",)); completed(state, dispatch_id="b", lane_id="publish", now=2, artifacts=("bundle",))
    assert [(item["sequence"], item["owner"], item["artifacts"]) for item in state.journal()] == [(1, "alpha", ("raw",)), (2, "beta", ("bundle",))]
    assert [item["sequence"] for item in state.journal(after=1, owner="beta")] == [2]


def test_s06(tmp_path):
    state = lane_state()
    for index in range(3):
        name = f"d{index}"; state.submit(name, lane_id="ingest", scheduled_for=index, payload_digest=name)
        completed(state, dispatch_id=name, now=index, artifacts=("raw",))
    state.register_consumer("c")
    assert [item["sequence"] for item in state.deliver("c", limit=2)] == [1, 2]
    assert state.consumer("c")["acknowledged"] == 0
    state.acknowledge("c", 1)
    from apscheduler.recovery import RecoveryState
    restored = RecoveryState.from_snapshot(state.snapshot())
    assert [item["sequence"] for item in restored.deliver("c")] == [3]
    assert restored.consumer("c") == {"consumer_id": "c", "delivered": 3, "acknowledged": 1}


def test_s07(tmp_path):
    state = lane_state()
    for name in ("a", "b"):
        state.submit(name, lane_id="ingest", scheduled_for=0, payload_digest=name); completed(state, dispatch_id=name, now=0, artifacts=("raw",))
    state.register_consumer("c"); state.deliver("c"); state.acknowledge("c", 2)
    assert state.compact() == [1, 2]
    from apscheduler.recovery import RecoveryState
    restored = RecoveryState.from_snapshot(state.snapshot())
    restored.submit("c", lane_id="ingest", scheduled_for=0, payload_digest="c")
    _, _, record = completed(restored, dispatch_id="c", now=0, artifacts=("raw",))
    assert record["sequence"] == 3 and restored.deliver("c") == [record]


def test_s08(tmp_path):
    state = lane_state()
    state.submit("one", lane_id="ingest", scheduled_for=0, payload_digest="1")
    state.submit("two", lane_id="ingest", scheduled_for=0, payload_digest="2", dependencies=("one",))
    state.submit("three", lane_id="ingest", scheduled_for=0, payload_digest="3", dependencies=("two",))
    completed(state, dispatch_id="one", now=0, artifacts=("raw",))
    assert state.reconcile(now=2)["ready"] == ("two",)
    lease = state.acquire("two", worker="w", now=2, ttl=2)
    report = state.reconcile(now=4)
    assert report["expired"] == ("two",) and report["ready"] == ("two",)
    fresh = state.acquire("two", worker="x", now=4, ttl=4)
    raises(RuntimeError, lambda: state.release("two", lease["token"], now=5))
    state.record_outcome("two", fresh["token"], outcome="success", finished_at=5, artifacts=("raw",))
    assert state.reconcile(now=6)["ready"] == ("three",)
