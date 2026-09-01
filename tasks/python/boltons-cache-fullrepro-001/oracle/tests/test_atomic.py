from __future__ import annotations

import copy
from tests.support import api,begin,fabric,fails,key_for,put,unchanged


def test_a09(tmp_path):
    c=fabric(shards=("a","b","c")); key={"x":[1,{"z":2}]}
    assert api().canonical_key(key)==api().canonical_key({"x":[1.0,{"z":2.0}]})
    assert c.route(key)==c.route(copy.deepcopy(key)) and c.route(key)["shard"] in c.topology()["shards"]


def test_a10(tmp_path):
    c=fabric(shards=("a","b")); old=c.route("x");rev=c.revision();result=c.reconfigure(shards=("a","b","c"),expected_generation=1,expected_revision=rev)
    assert result["topology"]["generation"]==2
    fails(RuntimeError,lambda:c.route("x",expected_generation=old["generation"]))


def test_a11(tmp_path):
    c=fabric();put(c,"a",1,depends_on=("b",))
    unchanged(c,ValueError,lambda:put(c,"b",2,depends_on=("a",)))


def test_a12(tmp_path):
    c=fabric();put(c,"a",1);put(c,"b",2,depends_on=("a",));put(c,"c",3,depends_on=("b",))
    result=c.invalidate(["a"],owner="alice",expected_generation=1,expected_revision=c.revision())
    assert [e["key"] for e in result["removed"]]==["a","b","c"] and c.entries()["s0"]==[]


def test_a13(tmp_path):
    c=fabric(admission=2);put(c,"a",1,cost=2)
    unchanged(c,RuntimeError,lambda:put(c,"b",2,cost=1))


def test_a14(tmp_path):
    c=fabric(capacity=1,admission=4,eviction=1);put(c,"a",1);before=c.budgets()["s0"];result=put(c,"b",2)
    assert [e["key"] for e in result["evicted"]]==["a"] and c.budgets()["s0"]["eviction"]==before["eviction"]-1


def test_a15(tmp_path):
    c=fabric();begin(c);c.stage("tx","k","low",layer="base");c.stage("tx","k","high",layer="hot");c.stage("tx","k","new-high",layer="hot")
    plan=c.plan("tx");assert len(plan["operations"])==1 and plan["operations"][0]["value"]=="new-high" and len(plan["digest"])==64


def test_a16(tmp_path):
    c=fabric(attempts=2);c.subscribe("sink");put(c,"a",1);item=c.deliveries()[0];delivered=c.deliver(item["token"],"sink");retried=c.retry(item["token"],"sink",reason="offline",operation_id="retry")
    assert delivered["attempts"]==1 and retried["state"]=="retryable"

