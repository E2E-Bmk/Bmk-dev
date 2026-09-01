from __future__ import annotations

from tests.recovery_support import completed, lane_state, new_state, raises, submitted


def test_a09(tmp_path):
    state = lane_state(two=True)
    item = state.lane("ingest")
    item["owner"] = "changed"
    assert [row["lane_id"] for row in state.lanes()] == ["ingest", "publish"]
    assert state.lane("ingest")["owner"] == "alpha" and state.lane("publish")["parents"] == ("ingest",)


def test_a10(tmp_path):
    state = lane_state()
    before = state.lanes()
    raises(KeyError, lambda: state.define_lane("bad", owner="x", parents=("missing",)))
    raises(ValueError, lambda: state.define_lane("bad", owner="x", artifacts=("raw", "raw")))
    assert state.lanes() == before


def test_a11(tmp_path):
    state = submitted()
    lease = state.acquire("d1", worker="w1", now=10, ttl=5)
    raises(RuntimeError, lambda: state.acquire("d1", worker="w1", now=11, ttl=5))
    assert lease["token"] and lease["generation"] == 1 and state.dispatch("d1")["state"] == "leased"


def test_a12(tmp_path):
    state = submitted()
    lease = state.acquire("d1", worker="w", now=10, ttl=10)
    first = state.record_outcome("d1", lease["token"], outcome="success", finished_at=11, artifacts=("raw",))
    again = state.record_outcome("d1", lease["token"], outcome="success", finished_at=11, artifacts=("raw",))
    raises(RuntimeError, lambda: state.record_outcome("d1", lease["token"], outcome="error", finished_at=11, artifacts=("raw",)))
    assert first == again and len(state.journal()) == 1


def test_a13(tmp_path):
    state, _, record = completed()
    state.register_consumer("c")
    assert state.deliver("c") == [record]
    assert state.consumer("c") == {"consumer_id": "c", "delivered": 1, "acknowledged": 0}
    state.acknowledge("c", 1)
    assert state.consumer("c")["acknowledged"] == 1


def test_a14(tmp_path):
    state, _, _ = completed()
    state.register_consumer("fast"); state.register_consumer("slow")
    state.deliver("fast"); state.deliver("slow"); state.acknowledge("fast", 1)
    assert state.compact() == []
    state.acknowledge("slow", 1)
    assert state.compact() == [1] and state.journal() == []


def test_a15(tmp_path):
    state = submitted()
    first = state.acquire("d1", worker="w", now=1, ttl=4)
    assert state.expire(now=4.999) == [] and state.expire(now=5) == ["d1"]
    second = state.acquire("d1", worker="w2", now=5, ttl=4)
    assert first["token"] != second["token"] and second["generation"] == 2


def test_a16(tmp_path):
    state, _, _ = completed()
    state.register_consumer("c"); state.deliver("c")
    from apscheduler.recovery import RecoveryState
    restored = RecoveryState.from_snapshot(state.snapshot())
    restored.acknowledge("c", 1)
    assert state.consumer("c")["acknowledged"] == 0 and restored.journal() == state.journal()
