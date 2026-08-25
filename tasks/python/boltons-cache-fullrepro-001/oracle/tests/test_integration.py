from __future__ import annotations

import copy
from tests.support import begin,fabric,fails,key_for,put,unchanged


def test_i05(tmp_path):
    c=fabric(shards=("a","b"),capacity=10);[put(c,f"k{i}",i) for i in range(8)]
    c.reconfigure(shards=("a","b","c"),expected_generation=1,expected_revision=c.revision())
    assert sum(len(v) for v in c.entries().values())==8
    assert all(c.route(e["key"])["shard"]==s for s,items in c.entries().items() for e in items)


def test_i06(tmp_path):
    c=fabric(shards=("a","b"));begin(c);c.stage("tx","x",1,layer="base");plan=c.plan("tx")
    c.reconfigure(shards=("a","b","c"),expected_generation=1,expected_revision=c.revision())
    unchanged(c,RuntimeError,lambda:c.commit("tx",plan["digest"],operation_id="old"))


def test_i07(tmp_path):
    c=fabric(shards=("a","b","c"));routes={f"k{i}":c.route(f"k{i}")["shard"] for i in range(20)};reopened=type(c).from_snapshot(c.snapshot())
    assert routes=={key:reopened.route(key)["shard"] for key in routes}


def test_i08(tmp_path):
    c=fabric();put(c,"root",0);put(c,"left",1,depends_on=("root",));put(c,"right",2,depends_on=("root",));put(c,"tip",3,depends_on=("left","right"))
    removed=c.invalidate(["root"],owner="a",expected_generation=1,expected_revision=c.revision())["removed"]
    assert [e["key"] for e in removed]==["root","left","right","tip"]


def test_i09(tmp_path):
    c=fabric();put(c,"dependent",1,depends_on=("missing",));result=c.invalidate(["missing"],owner="a",expected_generation=1,expected_revision=c.revision())
    assert [e["key"] for e in result["removed"]]==["dependent"]


def test_i10(tmp_path):
    c=fabric();put(c,"a",1);put(c,"b",2);put(c,"child",3,depends_on=("a",));put(c,"child",4,depends_on=("b",),layer="tenant")
    c.invalidate(["a"],owner="a",expected_generation=1,expected_revision=c.revision());assert [e["key"] for e in c.entries()["s0"]]==["b","child"]


def test_i11(tmp_path):
    c=fabric(admission=3);put(c,"a",1,cost=3);unchanged(c,RuntimeError,lambda:put(c,"b",2))
    result=c.replenish("s0",admission=2,expected_revision=c.revision());assert result["admission"]==2;put(c,"b",2)


def test_i12(tmp_path):
    c=fabric(admission=2);begin(c);c.stage("tx","a",1,layer="base",cost=2);c.stage("tx","b",2,layer="base",cost=1);plan=c.plan("tx")
    unchanged(c,RuntimeError,lambda:c.commit("tx",plan["digest"],operation_id="budget"));assert c.entries()["s0"]==[]


def test_i13(tmp_path):
    c=fabric(shards=("a","b"),capacity=1,admission=10,eviction=1)
    keys=[key_for(c,"a",f"x{i}") for i in range(3)];put(c,keys[0],0);put(c,keys[1],1)
    before=c.snapshot();
    try:c.reconfigure(shards=("a",),expected_generation=1,expected_revision=c.revision())
    except RuntimeError:assert c.snapshot()==before
    else:assert c.verify()


def test_i14(tmp_path):
    c=fabric();begin(c);c.stage("tx","a",1,layer="base");plan=c.plan("tx");first=c.commit("tx",plan["digest"],operation_id="commit");second=c.commit("tx",plan["digest"],operation_id="commit")
    assert first==second and len(c.history())==1


def test_i15(tmp_path):
    c=fabric();first=put(c,"a",1);changed=put(c,"a",2,layer="tenant");result=c.compensate(changed["revision"],reason="undo",owner="alice",expected_generation=1,expected_revision=c.revision(),operation_id="comp")
    assert c.entries()["s0"][0]["value"]==1 and result["revision"]>changed["revision"] and c.history()[-1]["kind"]=="compensate"


def test_i16(tmp_path):
    c=fabric();begin(c);c.stage("tx","a",1,layer="base");plan=c.plan("tx");put(c,"other",2);unchanged(c,RuntimeError,lambda:c.commit("tx",plan["digest"],operation_id="stale"))
    result=c.rollback("tx",reason="stale");assert result["status"]=="rolled_back" and [e["key"] for e in c.entries()["s0"]]==["other"]


def test_i17(tmp_path):
    c=fabric(attempts=2);c.subscribe("sink");put(c,"a",1);token=c.deliveries()[0]["token"];c.deliver(token,"sink");c.retry(token,"sink",reason="one",operation_id="r1");c.deliver(token,"sink");final=c.retry(token,"sink",reason="two",operation_id="r2")
    assert final["state"]=="exhausted" and final["attempts"]==2


def test_i18(tmp_path):
    c=fabric();c.subscribe("sink");put(c,"a",1);token=c.deliveries()[0]["token"];c.deliver(token,"sink");first=c.ack(token,"sink",operation_id="ack");second=c.ack(token,"sink",operation_id="ack")
    assert first==second and c.deliveries()[0]["state"]=="acknowledged"


def test_i19(tmp_path):
    c=fabric();c.subscribe("a");c.subscribe("b");put(c,"x",1);put(c,"y",2)
    assert [d["sequence"] for d in c.deliveries(sink="b",after=1)]==[2,4] and len({d["content_digest"] for d in c.deliveries()})==2


def test_i20(tmp_path):
    c=fabric();c.subscribe("sink");put(c,"a",{"x":[1]});doc=c.snapshot();doc["content"]["entries"]["s0"][0]["value"]["x"].append(2)
    assert c.entries()["s0"][0]["value"]=={"x":[1]} and c.verify()


def test_i21(tmp_path):
    c=fabric();put(c,"a",1);doc=c.snapshot();doc["digest"]="broken";fails(ValueError,lambda:type(c).from_snapshot(doc))
    doc=c.snapshot();doc["content"]["entries"]["s0"][0]["canonical_key"]="bad";doc["digest"]="also-bad";fails(ValueError,lambda:type(c).from_snapshot(doc))


def test_i22(tmp_path):
    c=fabric();c.subscribe("sink");begin(c);c.stage("tx","a",1,layer="base");plan=c.plan("tx");reopened=type(c).from_snapshot(c.snapshot());result=reopened.commit("tx",plan["digest"],operation_id="commit")
    assert result["status"]=="committed" and reopened.deliveries()[0]["sequence"]==1 and reopened.verify()


def test_i23(tmp_path):
    source=fabric();put(source,"a",1,owner="source");doc=source.export(owner="sender");target=fabric();result=target.reconcile(doc,owner="merge",expected_generation=1,expected_revision=target.revision(),operation_id="merge")
    replay=target.reconcile(doc,owner="merge",expected_generation=1,expected_revision=target.revision(),operation_id="merge")
    assert result==replay and target.entries()["s0"][0]["owner"]=="source"


def test_i24(tmp_path):
    source=fabric();put(source,"a","remote",owner="source");doc=source.export(owner="sender");target=fabric();put(target,"a","local",owner="alice");before=target.snapshot()
    unchanged(target,RuntimeError,lambda:target.reconcile(doc,owner="alice",expected_generation=1,expected_revision=target.revision(),operation_id="no-replace"))
    result=target.reconcile(doc,owner="alice",expected_generation=1,expected_revision=target.revision(),replace=True,operation_id="replace")
    assert result["replaced"]==1 and target.entries()["s0"][0]["owner"]=="alice"
