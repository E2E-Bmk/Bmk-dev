from __future__ import annotations

import concurrent.futures
import copy

from tests.delivery_support import api, committed, configured, processor, public_views, raises, sink


def test_i05(tmp_path):
    state = api()()
    raises(ValueError, state.prepare, "unknown", processors=[processor("render", "missing")], sinks=[sink("out")])
    assert state.configurations() == []
    raises(ValueError, state.prepare, "cycle", processors=[processor("a", "b"), processor("b", "a")], sinks=[sink("out")])
    assert state.configurations() == [] and state.active_generation() is None


def test_i06(tmp_path):
    state = api()()
    state.prepare("g1", processors=[], sinks=[]); state.prepare("g2", processors=[], sinks=[])
    state.activate("g1", expected_active=None)
    before = public_views(state)
    raises(RuntimeError, state.activate, "g2", expected_active=None)
    assert public_views(state) == before
    state.activate("g2", expected_active="g1")
    assert state.configuration("g1")["state"] == "retired" and state.configuration("g2")["state"] == "active"


def test_i07(tmp_path):
    state = api()()
    state.prepare("g1", processors=[processor("old")], sinks=[sink("old-sink")])
    state.activate("g1", expected_active=None)
    token = state.open_context("api")["token"]
    state.begin("old-event", context=token); state.stage("old-event", "old")
    state.prepare("g2", processors=[processor("new")], sinks=[sink("new-sink")], parent="g1")
    state.activate("g2", expected_active="g1")
    state.commit("old-event")
    state.begin("new-event", context=token); state.stage("new-event", "new"); state.commit("new-event")
    assert [(row["event_id"], row["sink"], row["generation"]) for row in state.deliveries()] == [
        ("old-event", "old-sink", "g1"), ("new-event", "new-sink", "g2")]


def test_i08(tmp_path):
    state = api()()
    root = state.open_context("root", {"trace": "t", "shared": "root", "secret": "x"})
    child = state.fork_context(root["token"], owner="worker", inherit=("trace", "shared"), values={"shared": "child", "local": 1})
    grand = state.fork_context(child["token"], owner="sink", inherit=("trace", "shared", "local"))
    assert child["values"] == {"trace": "t", "shared": "child", "local": 1}
    assert child["provenance"] == {"trace": root["token"], "shared": child["token"], "local": child["token"]}
    assert grand["provenance"] == child["provenance"] and "secret" not in grand["values"]


def test_i09(tmp_path):
    state = api()()
    token = state.open_context("api", {"request": "r1"})["token"]
    document = state.handoff_context(token)
    document["values"]["request"] = "forged"
    before = state.contexts()
    raises(ValueError, state.accept_handoff, document, owner="worker")
    assert state.contexts() == before


def test_i10(tmp_path):
    state = api()()
    source = state.open_context("api", {"request": "r1", "shared": "source"})
    document = state.handoff_context(source["token"])
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        copied = pool.submit(copy.deepcopy, document).result()
    accepted = state.accept_handoff(copied, owner="worker", values={"shared": "worker", "attempt": 1})
    copied["values"]["request"] = "changed"
    assert accepted["owner"] == "worker" and accepted["parent"] == source["token"]
    assert state.context(accepted["token"])["values"] == {"request": "r1", "shared": "worker", "attempt": 1}
    assert state.context(source["token"])["values"]["shared"] == "source"


def test_i11(tmp_path):
    state, token = configured(processors=[processor("normalize")], sinks=[])
    event = state.begin("e1", context=token, fields={"shared": "call", "event": "x"})
    assert event["provenance"]["request_id"] == token and event["provenance"]["shared"] == "call"
    event = state.stage("e1", "normalize", patch={"shared": "processor", "normalized": True}, remove=("event",))
    assert event["fields"]["shared"] == "processor" and event["provenance"]["shared"] == "processor:normalize"
    assert "event" not in event["fields"] and "event" not in event["provenance"]


def test_i12(tmp_path):
    state, token = configured(processors=[], sinks=[sink("primary", 1), sink("archive", 2)])
    for event_id in ("e1", "e2", "e3"): committed(state, token, event_id)
    state.claim("primary", "e1", worker="p", now=0, ttl=10)
    raises(RuntimeError, state.claim, "primary", "e2", worker="p", now=0, ttl=10)
    state.claim("archive", "e1", worker="a1", now=0, ttl=10)
    state.claim("archive", "e2", worker="a2", now=0, ttl=10)
    raises(RuntimeError, state.claim, "archive", "e3", worker="a3", now=0, ttl=10)


def test_i13(tmp_path):
    state, token = configured(processors=[], sinks=[sink("out", 2)])
    committed(state, token, "e1"); committed(state, token, "e2")
    first = state.claim("out", "e1", worker="one", now=1, ttl=2)
    sibling = state.claim("out", "e2", worker="two", now=1, ttl=5)
    expired = state.expire(now=3)
    assert [row["event_id"] for row in expired] == ["e1"]
    raises(RuntimeError, state.acknowledge, "out", "e1", first["token"], now=3)
    state.acknowledge("out", "e2", sibling["token"], now=3)
    assert state.deliveries(sink="out", status="delivered")[0]["event_id"] == "e2"


def test_i14(tmp_path):
    state, token = configured(processors=[], sinks=[sink("primary"), sink("archive")])
    committed(state, token)
    first = state.claim("primary", "e1", worker="p", now=0, ttl=5)
    second = state.claim("archive", "e1", worker="a", now=0, ttl=5)
    state.fail("primary", "e1", first["token"], reason="permanent", retryable=False, now=1)
    assert state.deliveries(sink="primary")[0]["status"] == "poisoned"
    assert state.deliveries(sink="archive")[0]["status"] == "leased"
    state.acknowledge("archive", "e1", second["token"], now=1)


def test_i15(tmp_path):
    state, token = configured(processors=[], sinks=[sink("out", 1, 2)])
    committed(state, token)
    lease = state.claim("out", "e1", worker="w", now=0, ttl=5)
    state.fail("out", "e1", lease["token"], reason="later", retryable=True, now=1, backoff=5)
    assert state.reconcile(now=5)["ready"] == []
    raises(RuntimeError, state.claim, "out", "e1", worker="w", now=5, ttl=2)
    assert [row["event_id"] for row in state.reconcile(now=6)["ready"]] == ["e1"]


def test_i16(tmp_path):
    state, token = configured(processors=[], sinks=[sink("out", 1, 2)])
    committed(state, token)
    for attempt in range(1, 4):
        lease = state.claim("out", "e1", worker="w", now=attempt * 2, ttl=1)
        row = state.fail("out", "e1", lease["token"], reason=f"failure-{attempt}", retryable=True, now=attempt * 2 + 0.5)
    assert row["attempts"] == 3 and row["status"] == "poisoned"
    raises(RuntimeError, state.claim, "out", "e1", worker="w", now=20, ttl=1)


def test_i17(tmp_path):
    state, token = configured(processors=[], sinks=[sink("out", 1, 0)])
    committed(state, token)
    raises(RuntimeError, state.compensate, "out", "e1", reason="too early")
    lease = state.claim("out", "e1", worker="w", now=0, ttl=2)
    state.fail("out", "e1", lease["token"], reason="poison", retryable=True, now=1)
    row = state.compensate("out", "e1", reason="written elsewhere")
    assert row["status"] == "compensated" and row["compensation_reason"] == "written elsewhere"


def test_i18(tmp_path):
    state = api()()
    state.prepare("g1", processors=[], sinks=[]); state.activate("g1", expected_active=None)
    state.prepare("g2", processors=[], sinks=[], parent="g1"); state.activate("g2", expected_active="g1")
    rows = state.audit()
    assert [row["kind"] for row in rows] == ["activate", "activate"]
    assert rows[1]["detail"] == {"previous": "g1"} and state.verify_audit()


def test_i19(tmp_path):
    state, token = configured(processors=[], sinks=[sink("out", 1, 2)])
    committed(state, token)
    lease = state.claim("out", "e1", worker="w", now=0, ttl=1)
    state.expire(now=1)
    lease = state.claim("out", "e1", worker="w", now=1, ttl=2)
    state.fail("out", "e1", lease["token"], reason="temporary", retryable=True, now=2)
    tail = state.audit(after=2)
    assert [row["kind"] for row in tail] == ["expire", "fail"]
    assert tail[-1]["detail"]["status"] == "retry" and state.verify_audit()


def test_i20(tmp_path):
    state, token = configured(processors=[])
    committed(state, token)
    rows = state.audit(); rows[0]["previous_hash"] = "forged"; rows[-1]["detail"]["x"] = 1
    assert state.verify_audit() is True
    assert state.audit()[0]["previous_hash"] == "0" * 64 and "x" not in state.audit()[-1]["detail"]


def test_i21(tmp_path):
    state, token = configured(processors=[processor("one"), processor("two", "one")])
    state.begin("e1", context=token, fields={"keep": 1})
    before = public_views(state)
    raises(ValueError, state.stage, "e1", "one", patch={"keep": 2}, remove=("keep",))
    assert public_views(state) == before
    raises(KeyError, state.stage, "e1", "one", remove=("missing",))
    assert public_views(state) == before


def test_i22(tmp_path):
    state, token = configured(processors=[processor("one")])
    state.begin("abort", context=token); state.stage("abort", "one")
    event = state.rollback("abort", reason="cancelled")
    assert event["state"] == "rolled_back" and state.deliveries() == []
    raises(RuntimeError, state.commit, "abort")
    assert state.audit()[-1]["kind"] == "rollback"


def test_i23(tmp_path):
    state, token = configured(processors=[], sinks=[sink("first", 2), sink("second", 2)])
    committed(state, token, "e1"); committed(state, token, "e2")
    lease = state.claim("first", "e1", worker="w", now=0, ttl=2)
    state.claim("second", "e2", worker="w", now=0, ttl=10)
    view = state.reconcile(now=2)
    assert [(row["event_id"], row["sink"]) for row in view["ready"]] == [("e1", "first"), ("e1", "second"), ("e2", "first")]
    assert [(row["event_id"], row["sink"]) for row in view["leased"]] == [("e2", "second")]
    raises(RuntimeError, state.acknowledge, "first", "e1", lease["token"], now=2)


def test_i24(tmp_path):
    state, token = configured(processors=[], sinks=[sink("out")])
    committed(state, token)
    lease = state.claim("out", "e1", worker="w", now=0, ttl=5)
    reopened = api().from_snapshot(state.snapshot())
    assert reopened.deliveries()[0]["status"] == "leased"
    raises(RuntimeError, reopened.acknowledge, "out", "e1", "wrong", now=1)
    reopened.acknowledge("out", "e1", lease["token"], now=1)
    assert reopened.deliveries()[0]["status"] == "delivered" and reopened.verify_audit()
