from tests.federation_support import raises, seeded


def test_s03(tmp_path):
    p,w,m,log,j,c,artifacts,digests=seeded(); c.attest("r1","acme",digests); published=c.publish("r1","acme",digests); assert c.audit("r1","acme",digests,log.checkpoint()) and published.audit[-1]==log.checkpoint()

def test_s04(tmp_path):
    p,w,m,log,j,c,artifacts,digests=seeded(); c.attest("r1","acme",digests); m.observe("acme","m1",8,{**digests,"core.whl":"evil"}); raises(ValueError,lambda:c.publish("r1","acme",digests,2,0)); assert c.get("r1","acme").state=="attested"

def test_s05(tmp_path):
    p,w,m,log,j,c,artifacts,digests=seeded(); c.attest("r1","acme",digests); c.publish("r1","acme",digests); plan=c.compensate("r1","acme",(("unlist",()),("purge",("unlist",)))); j.complete(plan.plan_id,"acme","unlist"); raises(ValueError,lambda:c.recover("r1","acme")); j.complete(plan.plan_id,"acme","purge"); j.seal(plan.plan_id,"acme"); assert c.recover("r1","acme").state=="recovered"

def test_s06(tmp_path):
    p,w,m,log,j,c,artifacts,digests=seeded(); c.attest("r1","acme",digests); c.publish("r1","acme",digests); plan=c.compensate("r1","acme",(("a",()),("b",("a",)))); j.complete(plan.plan_id,"acme","a"); j.complete(plan.plan_id,"acme","b"); j.seal(plan.plan_id,"acme"); j.reopen(plan.plan_id,"acme","a"); raises(ValueError,lambda:c.recover("r1","acme"))

def test_s07(tmp_path):
    p,w,m,log,j,c,artifacts,digests=seeded(); p2,w2,m2,log2,j2,c2,arts2,dig2=seeded("other","r2"); c.attest("r1","acme",digests); c2.attest("r2","other",dig2); assert c.get("r1","acme").owner=="acme" and c2.get("r2","other").owner=="other"

def test_s08(tmp_path):
    p,w,m,log,j,c,artifacts,digests=seeded(); c.attest("r1","acme",digests); c.publish("r1","acme",digests); before=c.snapshot("acme"); assert c.audit("r1","acme",digests,log.checkpoint()); after=c.snapshot("acme"); assert before==after and after[0].revision==2
