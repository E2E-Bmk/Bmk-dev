from __future__ import annotations

from tests.recovery_support import completed, lane_state, new_state, raises, submitted


def test_i05(tmp_path):
    state = lane_state(two=True)
    state.define_lane("archive", owner="gamma", parents=("ingest", "publish"), artifacts=("tar",))
    assert state.lane("archive")["parents"] == ("ingest", "publish")
    assert [item["lane_id"] for item in state.lanes()] == ["ingest", "publish", "archive"]


def test_i06(tmp_path):
    state = new_state()
    left = state.define_lane("left", owner="alpha", artifacts=("raw",))
    right = state.define_lane("right", owner="beta", artifacts=("raw",))
    assert left["owner"] == "alpha" and right["owner"] == "beta" and state.lane("left") != state.lane("right")


def test_i07(tmp_path):
    state = submitted()
    first = state.acquire("d1", worker="w", now=2, ttl=5)
    renewed = state.renew("d1", first["token"], now=4, ttl=9)
    assert renewed["token"] == first["token"] and renewed["generation"] == 1 and renewed["expires_at"] == 13


def test_i08(tmp_path):
    state = submitted()
    first = state.acquire("d1", worker="w", now=2, ttl=5)
    assert state.release("d1", first["token"], now=3)["state"] == "pending"
    second = state.acquire("d1", worker="w", now=3, ttl=5)
    assert second["generation"] == 2 and second["token"] != first["token"]


def test_i09(tmp_path):
    state = submitted()
    old = state.acquire("d1", worker="w", now=1, ttl=2)
    fresh = state.acquire("d1", worker="x", now=3, ttl=5)
    raises(RuntimeError, lambda: state.renew("d1", old["token"], now=3, ttl=1))
    raises(RuntimeError, lambda: state.release("d1", old["token"], now=3))
    record = state.record_outcome("d1", fresh["token"], outcome="success", finished_at=4, artifacts=("raw",))
    assert record["generation"] == 2


def test_i10(tmp_path):
    state = lane_state(two=True)
    state.submit("a", lane_id="ingest", scheduled_for=1, payload_digest="a")
    state.submit("b", lane_id="publish", scheduled_for=2, payload_digest="b")
    completed(state, dispatch_id="a", artifacts=("raw",), now=2)
    completed(state, dispatch_id="b", lane_id="publish", artifacts=("bundle",), now=4)
    assert [item["sequence"] for item in state.journal()] == [1, 2]
    assert [item["dispatch_id"] for item in state.journal(owner="beta")] == ["b"]


def test_i11(tmp_path):
    state = submitted()
    lease = state.acquire("d1", worker="w", now=1, ttl=10)
    raises(ValueError, lambda: state.record_outcome("d1", lease["token"], outcome="success", finished_at=2, artifacts=("unknown",)))
    assert state.dispatch("d1")["state"] == "leased" and state.journal() == []
    assert state.record_outcome("d1", lease["token"], outcome="success", finished_at=2, artifacts=("raw",))["artifacts"] == ("raw",)


def test_i12(tmp_path):
    state, lease, record = completed()
    before = state.snapshot()
    raises(RuntimeError, lambda: state.record_outcome("d1", lease["token"], outcome="success", finished_at=12, artifacts=("raw",)))
    assert state.snapshot() == before and state.journal() == [record]


def test_i13(tmp_path):
    state = lane_state()
    for name in ("a", "b"):
        state.submit(name, lane_id="ingest", scheduled_for=1, payload_digest=name)
        completed(state, dispatch_id=name, now=2, artifacts=("raw",))
    state.register_consumer("c")
    assert [item["sequence"] for item in state.deliver("c", limit=1)] == [1]
    assert state.consumer("c") == {"consumer_id": "c", "delivered": 1, "acknowledged": 0}
    assert [item["sequence"] for item in state.deliver("c")] == [2]


def test_i14(tmp_path):
    state, _, _ = completed()
    state.register_consumer("left"); state.register_consumer("right")
    state.deliver("left")
    assert state.consumer("left") == {"consumer_id": "left", "delivered": 1, "acknowledged": 0}
    assert state.consumer("right") == {"consumer_id": "right", "delivered": 0, "acknowledged": 0}


def test_i15(tmp_path):
    state, _, _ = completed()
    state.register_consumer("c"); state.deliver("c")
    assert state.consumer("c")["acknowledged"] == 0
    raises(RuntimeError, lambda: state.acknowledge("c", 2))
    state.acknowledge("c", 1); state.acknowledge("c", 1)
    raises(RuntimeError, lambda: state.acknowledge("c", 0))


def test_i16(tmp_path):
    state, _, _ = completed()
    state.register_consumer("fast"); state.register_consumer("slow")
    state.deliver("fast"); state.acknowledge("fast", 1); state.deliver("slow")
    assert state.compact() == [] and [item["sequence"] for item in state.journal()] == [1]


def test_i17(tmp_path):
    state, _, _ = completed()
    assert state.compact() == [] and [item["sequence"] for item in state.journal()] == [1]


def test_i18(tmp_path):
    state = lane_state()
    state.submit("a", lane_id="ingest", scheduled_for=1, payload_digest="a")
    completed(state, dispatch_id="a", now=1, artifacts=("raw",))
    state.register_consumer("c"); state.deliver("c"); state.acknowledge("c", 1); assert state.compact() == [1]
    state.submit("b", lane_id="ingest", scheduled_for=2, payload_digest="b")
    _, _, record = completed(state, dispatch_id="b", now=2, artifacts=("raw",))
    assert record["sequence"] == 2


def test_i19(tmp_path):
    state = lane_state()
    state.submit("parent", lane_id="ingest", scheduled_for=1, payload_digest="p")
    state.submit("child", lane_id="ingest", scheduled_for=1, payload_digest="c", dependencies=("parent",))
    assert [item["dispatch_id"] for item in state.ready(now=1)] == ["parent"] and state.blocked("child") == ("parent",)
    completed(state, dispatch_id="parent", now=1, artifacts=("raw",))
    assert [item["dispatch_id"] for item in state.ready(now=2)] == ["child"]


def test_i20(tmp_path):
    state = lane_state()
    state.submit("later", lane_id="ingest", scheduled_for=2, payload_digest="l")
    state.submit("first", lane_id="ingest", scheduled_for=1, payload_digest="f")
    state.submit("second", lane_id="ingest", scheduled_for=1, payload_digest="s")
    assert [item["dispatch_id"] for item in state.ready(now=3)] == ["first", "second", "later"]


def test_i21(tmp_path):
    state = lane_state()
    state.submit("parent", lane_id="ingest", scheduled_for=1, payload_digest="p")
    state.submit("child", lane_id="ingest", scheduled_for=1, payload_digest="c", dependencies=("parent",))
    state.abandon("parent", reason="retired", now=2)
    report = state.reconcile(now=3)
    assert report["ready"] == () and report["blocked"] == {"child": ("parent",)}


def test_i22(tmp_path):
    state = submitted()
    lease = state.acquire("d1", worker="w", now=1, ttl=10)
    from apscheduler.recovery import RecoveryState
    restored = RecoveryState.from_snapshot(state.snapshot())
    renewed = restored.renew("d1", lease["token"], now=2, ttl=20)
    assert renewed["expires_at"] == 22 and state.dispatch("d1")["state"] == "leased"


def test_i23(tmp_path):
    state, _, _ = completed()
    state.register_consumer("c"); state.deliver("c"); state.acknowledge("c", 1)
    from apscheduler.recovery import RecoveryState
    restored = RecoveryState.from_snapshot(state.snapshot())
    assert restored.consumer("c") == {"consumer_id": "c", "delivered": 1, "acknowledged": 1}


def test_i24(tmp_path):
    state, _, _ = completed()
    document = state.snapshot()
    from apscheduler.recovery import RecoveryState
    missing = dict(document); missing.pop("lanes")
    raises(ValueError, lambda: RecoveryState.from_snapshot(missing))
    bad = state.snapshot(); bad["next_sequence"] = 1
    raises(ValueError, lambda: RecoveryState.from_snapshot(bad))
    dangling = state.snapshot(); dangling["journal"][0]["lane_id"] = "missing"
    raises(ValueError, lambda: RecoveryState.from_snapshot(dangling))
