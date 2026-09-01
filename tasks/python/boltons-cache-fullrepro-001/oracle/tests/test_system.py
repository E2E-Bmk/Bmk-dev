from __future__ import annotations

from tests.support import begin,fabric,fails,put,unchanged


def test_s03(tmp_path):
    c=fabric();c.subscribe("sink");put(c,"base",1);begin(c);c.stage("tx","base",2,layer="tenant");c.stage("tx","child",3,layer="base",depends_on=("base",));plan=c.plan("tx");committed=c.commit("tx",plan["digest"],operation_id="commit")
    c.compensate(committed["revision"],reason="undo batch",owner="alice",expected_generation=1,expected_revision=c.revision(),operation_id="comp")
    assert [e["key"] for e in c.entries()["s0"]]==["base"] and c.entries()["s0"][0]["value"]==1 and len(c.deliveries())==3 and c.verify()


def test_s04(tmp_path):
    c=fabric(attempts=3);c.subscribe("sink");put(c,"a",1);token=c.deliveries()[0]["token"];c.deliver(token,"sink");c.retry(token,"sink",reason="offline",operation_id="retry");reopened=type(c).from_snapshot(c.snapshot());reopened.deliver(token,"sink");reopened.ack(token,"sink",operation_id="ack")
    assert reopened.deliveries()[0]["state"]=="acknowledged" and reopened.deliveries()[0]["attempts"]==2 and reopened.verify()


def test_s05(tmp_path):
    c=fabric(shards=("a","b"),capacity=10);[put(c,f"k{i}",i) for i in range(10)];c.reconfigure(shards=("a","b","c"),expected_generation=1,expected_revision=c.revision());reopened=type(c).from_snapshot(c.snapshot())
    assert reopened.topology()["generation"]==2 and all(reopened.route(e["key"])["shard"]==s for s,items in reopened.entries().items() for e in items) and reopened.verify()


def test_s06(tmp_path):
    c=fabric(capacity=2);put(c,"a",1);put(c,"b",2);snap=c.snapshot();reopened=type(c).from_snapshot(snap);put(reopened,"c",3);put(reopened,"d",4)
    history=reopened.history();assert all(history[i]["previous_digest"]==history[i-1]["digest"] for i in range(1,len(history))) and reopened.verify()


def test_s07(tmp_path):
    source=fabric();source.subscribe("sink");put(source,"a",1);target=type(source).from_snapshot(source.snapshot());token=source.deliveries()[0]["token"];source.deliver(token,"sink");source.ack(token,"sink",operation_id="ack");doc=source.export(owner="source")
    result=target.reconcile(doc,owner="source",expected_generation=1,expected_revision=target.revision(),operation_id="sync")
    assert result["suppressed"]>=1 and any(d["state"]=="acknowledged" for d in target.deliveries()) and target.verify()


def test_s08(tmp_path):
    base=fabric();put(base,"a",1,owner="alice");left=type(base).from_snapshot(base.snapshot());right=type(base).from_snapshot(base.snapshot());put(left,"a",2,layer="hot",owner="alice");put(right,"a",3,layer="tenant",owner="alice");doc=left.export(owner="alice")
    unchanged(right,RuntimeError,lambda:right.reconcile(doc,owner="alice",expected_generation=1,expected_revision=right.revision(),operation_id="conflict"));right.reconcile(doc,owner="alice",expected_generation=1,expected_revision=right.revision(),replace=True,operation_id="replace")
    reopened=type(right).from_snapshot(right.snapshot());assert reopened.entries()["s0"][0]["value"]==2 and reopened.entries()["s0"][0]["owner"]=="alice" and reopened.verify()
