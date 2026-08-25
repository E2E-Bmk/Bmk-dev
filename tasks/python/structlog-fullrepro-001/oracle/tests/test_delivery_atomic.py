from __future__ import annotations

import copy
import json

from tests.delivery_support import api, committed, configured, processor, public_views, raises, sink


def test_a07(tmp_path):
    state = api()()
    supplied = [processor("render", "merge"), processor("merge"), processor("sign", "merge")]
    result = state.prepare("g1", processors=supplied, sinks=[sink("out")])
    assert result["order"] == ("merge", "render", "sign")
    supplied[0]["after"] = ()
    result["processors"][0]["after"] = ()
    assert state.configuration("g1")["processors"][0]["after"] == ("merge",)


def test_a08(tmp_path):
    state = api()()
    values = {"request": "r1", "nested": {"value": 1}}
    context = state.open_context("api", values)
    values["nested"]["value"] = 9
    context["values"]["request"] = "changed"
    stored = state.context(context["token"])
    assert stored["owner"] == "api"
    assert stored["values"] == {"request": "r1", "nested": {"value": 1}}
    assert stored["provenance"] == {"request": context["token"], "nested": context["token"]}


def test_a09(tmp_path):
    state, token = configured(processors=[], sinks=[sink("limited", 1, 1)])
    committed(state, token, "e1"); committed(state, token, "e2")
    lease = state.claim("limited", "e1", worker="w1", now=0, ttl=10)
    raises(RuntimeError, state.claim, "limited", "e2", worker="w2", now=1, ttl=10)
    assert state.deliveries(status="leased") == [{**state.deliveries(sink="limited")[0]}]
    assert lease["generation"] == 1


def test_a10(tmp_path):
    state, token = configured(processors=[], sinks=[sink("out")])
    committed(state, token)
    first = state.claim("out", "e1", worker="one", now=0, ttl=2)
    second = state.claim("out", "e1", worker="two", now=2, ttl=2)
    assert second["generation"] == first["generation"] + 1 and second["token"] != first["token"]
    before = state.deliveries()
    raises(RuntimeError, state.acknowledge, "out", "e1", first["token"], now=2.5)
    assert state.deliveries() == before


def test_a11(tmp_path):
    state, token = configured(processors=[], sinks=[sink("out", 1, 1)])
    committed(state, token)
    first = state.claim("out", "e1", worker="w", now=0, ttl=5)
    retry = state.fail("out", "e1", first["token"], reason="temporary", retryable=True, now=1, backoff=2)
    assert retry["status"] == "retry" and retry["attempts"] == 1 and retry["next_ready"] == 3
    second = state.claim("out", "e1", worker="w", now=3, ttl=5)
    poison = state.fail("out", "e1", second["token"], reason="again", retryable=True, now=4)
    assert poison["status"] == "poisoned" and poison["attempts"] == 2


def test_a12(tmp_path):
    state, token = configured(processors=[])
    committed(state, token)
    rows = state.audit()
    assert [row["sequence"] for row in rows] == list(range(1, len(rows) + 1))
    assert rows[0]["previous_hash"] == "0" * 64
    assert all(len(row["hash"]) == 64 for row in rows)
    assert all(rows[index]["previous_hash"] == rows[index - 1]["hash"] for index in range(1, len(rows)))
    assert state.verify_audit() is True


def test_a13(tmp_path):
    state, token = configured(processors=[processor("first"), processor("second", "first")], sinks=[])
    state.begin("e1", context=token, fields={"event": "x"})
    before = public_views(state)
    raises(RuntimeError, state.stage, "e1", "second", patch={"bad": True})
    assert public_views(state) == before
    staged = state.stage("e1", "first", patch={"value": 1})
    assert staged["completed"] == ("first",) and staged["provenance"]["value"] == "processor:first"


def test_a14(tmp_path):
    state, token = configured(processors=[processor("render")], sinks=[sink("one"), sink("two")])
    state.begin("e1", context=token); state.stage("e1", "render", patch={"rendered": True})
    event = state.commit("e1")
    deliveries = state.deliveries()
    assert event["state"] == "committed" and [row["sink"] for row in deliveries] == ["one", "two"]
    assert all(row["event_id"] == "e1" and row["status"] == "pending" for row in deliveries)


def test_a15(tmp_path):
    state, token = configured(processors=[])
    committed(state, token)
    document = state.snapshot(); json.dumps(document, sort_keys=True)
    reopened = api().from_snapshot(document)
    assert reopened.snapshot() == document
    document["contexts"][0]["values"]["request_id"] = "tampered"
    assert reopened.context(token)["values"]["request_id"] == "r-1"


def test_a16(tmp_path):
    state, token = configured(processors=[])
    committed(state, token)
    base = state.snapshot()
    wrong_active = copy.deepcopy(base); wrong_active["active_generation"] = "missing"
    raises(ValueError, api().from_snapshot, wrong_active)
    broken_audit = copy.deepcopy(base); broken_audit["audit"][-1]["hash"] = "0" * 64
    raises(ValueError, api().from_snapshot, broken_audit)
    duplicate = copy.deepcopy(base); duplicate["events"].append(copy.deepcopy(duplicate["events"][0]))
    raises(ValueError, api().from_snapshot, duplicate)
