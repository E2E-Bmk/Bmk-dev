from __future__ import annotations

import copy

from tests.delivery_support import api, raises


def test_s05(tmp_path):
    from tests.delivery_support import processor, sink
    state = api()()
    state.prepare("blue", processors=[processor("normalize"), processor("render", "normalize")], sinks=[sink("console")])
    state.activate("blue", expected_active=None)
    token = state.open_context("request", {"trace": "t1"})["token"]
    state.begin("before-switch", context=token, fields={"event": "before"})
    state.stage("before-switch", "normalize", patch={"normalized": True})
    state.prepare("green", processors=[processor("redact")], sinks=[sink("archive")], parent="blue")
    snapshot = state.snapshot()
    raises(RuntimeError, state.activate, "green", expected_active=None)
    assert state.snapshot() == snapshot
    state.activate("green", expected_active="blue")
    state.stage("before-switch", "render", patch={"rendered": "before"}); state.commit("before-switch")
    state.begin("after-switch", context=token, fields={"event": "after"})
    state.stage("after-switch", "redact", patch={"redacted": True}); state.commit("after-switch")
    assert [(row["event_id"], row["generation"], row["sink"]) for row in state.deliveries()] == [
        ("before-switch", "blue", "console"), ("after-switch", "green", "archive")]
    assert state.configuration("blue")["state"] == "retired"


def test_s06(tmp_path):
    from tests.delivery_support import committed, configured, sink
    state, token = configured(processors=[], sinks=[sink("primary", 1, 2), sink("audit", 1, 0)])
    committed(state, token, "e1"); committed(state, token, "e2")
    primary = state.claim("primary", "e1", worker="p", now=0, ttl=2)
    audit = state.claim("audit", "e1", worker="a", now=0, ttl=2)
    state.fail("primary", "e1", primary["token"], reason="network", retryable=True, now=1, backoff=2)
    poison = state.fail("audit", "e1", audit["token"], reason="schema", retryable=True, now=1)
    assert poison["status"] == "poisoned"
    state.compensate("audit", "e1", reason="quarantine")
    assert [row["event_id"] for row in state.reconcile(now=2)["ready"]] == ["e2", "e2"]
    retry = state.claim("primary", "e1", worker="p2", now=3, ttl=2)
    state.acknowledge("primary", "e1", retry["token"], now=4)
    statuses = {(row["sink"], row["event_id"]): row["status"] for row in state.deliveries()}
    assert statuses[("primary", "e1")] == "delivered" and statuses[("audit", "e1")] == "compensated"
    assert statuses[("primary", "e2")] == statuses[("audit", "e2")] == "pending"


def test_s07(tmp_path):
    from tests.delivery_support import committed, configured, sink
    state, token = configured(processors=[], sinks=[sink("out", 1, 0)])
    committed(state, token)
    lease = state.claim("out", "e1", worker="w", now=0, ttl=2)
    state.fail("out", "e1", lease["token"], reason="permanent", retryable=False, now=1)
    state.compensate("out", "e1", reason="stored")
    kinds = [row["kind"] for row in state.audit()]
    assert kinds == ["activate", "commit", "fail", "compensate"] and state.verify_audit()
    document = state.snapshot(); document["audit"][1]["detail"]["fields"]["event"] = "forged"
    raises(ValueError, api().from_snapshot, document)
    assert state.verify_audit() and state.event("e1")["fields"]["event"] == "created"


def test_s08(tmp_path):
    from tests.delivery_support import processor, sink
    state = api()()
    state.prepare(
        "g1",
        processors=[processor("normalize"), processor("render", "normalize")],
        sinks=[sink("primary", 1, 1), sink("archive", 1, 0)],
    )
    state.activate("g1", expected_active=None)
    token = state.open_context("request", {"request_id": "r-1", "shared": "parent"})["token"]
    handoff = state.handoff_context(token)
    worker = state.accept_handoff(handoff, owner="worker", values={"attempt": 1, "shared": "worker"})
    state.begin("legacy", context=worker["token"], fields={"event": "before-restart"})
    state.stage("legacy", "normalize", patch={"normalized": True})
    state.prepare("g2", processors=[processor("redact")], sinks=[sink("cold")], parent="g1")
    state.activate("g2", expected_active="g1")
    state.stage("legacy", "render", patch={"rendered": "legacy"})
    state.commit("legacy")
    lease = state.claim("primary", "legacy", worker="node-a", now=0, ttl=2)
    archive = state.claim("archive", "legacy", worker="archive-a", now=0, ttl=2)
    state.acknowledge("archive", "legacy", archive["token"], now=1)
    state.begin("current", context=worker["token"], fields={"event": "after-restart"})
    state.stage("current", "redact", patch={"safe": True})
    state.commit("current")
    before = state.audit()
    snapshot = state.snapshot()
    forged = copy.deepcopy(snapshot)
    forged["leases"][0]["generation"] += 1
    raises(ValueError, api().from_snapshot, forged)
    reopened = api().from_snapshot(snapshot)
    assert reopened.context(worker["token"])["provenance"]["request_id"] == token
    assert reopened.context(worker["token"])["provenance"]["shared"] == worker["token"]
    assert reopened.active_generation() == "g2"
    assert reopened.event("legacy")["generation"] == "g1"
    assert reopened.event("current")["generation"] == "g2"
    ready = [(row["sink"], row["event_id"]) for row in reopened.reconcile(now=2)["ready"]]
    assert ready == [("primary", "legacy"), ("cold", "current")]
    raises(RuntimeError, reopened.acknowledge, "primary", "legacy", lease["token"], now=2)
    next_lease = reopened.claim("primary", "legacy", worker="node-b", now=2, ttl=2)
    assert next_lease["generation"] == lease["generation"] + 1
    reopened.fail("primary", "legacy", next_lease["token"], reason="retired route", retryable=False, now=3)
    reopened.compensate("primary", "legacy", reason="archived")
    after = reopened.audit()
    assert after[len(before)]["kind"] == "expire"
    assert after[len(before)]["previous_hash"] == before[-1]["hash"]
    statuses = {(row["sink"], row["event_id"]): row["status"] for row in reopened.deliveries()}
    assert statuses[("primary", "legacy")] == "compensated"
    assert statuses[("archive", "legacy")] == "delivered"
    assert statuses[("cold", "current")] == "pending"
    assert reopened.verify_audit()
