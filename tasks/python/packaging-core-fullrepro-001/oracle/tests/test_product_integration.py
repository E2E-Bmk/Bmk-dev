from dataclasses import replace
from tests.federation_support import raises, seeded, stores


def test_i05(tmp_path):
    p,*_=stores(); p.define("base",1,(("x",">=1",None),)); raises(ValueError,lambda:p.define("base",1,(("x",">=2",None),)))

def test_i06(tmp_path):
    p,*_=stores(); p.define("base",1,(("x",">=2",None),)); raises(ValueError,lambda:p.lease("l","o",{}, {"x":("1",)})); raises(ValueError,lambda:p.lease("l2","o",{}, {"x":("2",),"y":("1",)}))

def test_i07(tmp_path):
    p,*_=stores(); p.define("base",1,(("x",">=1",None),)); p.lease("l","o",{}, {"x":("1",)}); p.define("new",2,(("x",">=2",None),)); assert not p.valid("l","o")

def test_i08(tmp_path):
    p,*_=stores(); p.define("base",1,(("x",">=1",None),)); p.lease("l","o",{}, {"x":("1",)}); assert p.revoke("l","o").state=="revoked" and not p.valid("l","o")

def test_i09(tmp_path):
    _,w,*_=stores(); raises(KeyError,lambda:w.add("leaf","o","x","d","s",("absent",)))

def test_i10(tmp_path):
    _,w,*_=stores(); w.add("a","o","x","d1","s"); raises(ValueError,lambda:w.add("b","o","x","d2","s"))

def test_i11(tmp_path):
    _,w,*_=stores(); w.add("a","o","x","d1","s1"); w.add("b","o","x","d2","s2"); raises(ValueError,lambda:w.quorum("x","o",2))

def test_i12(tmp_path):
    _,w,*_=stores(); w.add("a","left","x","d","s1"); w.add("b","left","x","d","s2"); w.add("a","right","x","d2","s1"); w.add("b","right","x","d2","s2"); assert {x.digest for x in w.quorum("x","left")}=={"d"}

def test_i13(tmp_path):
    _,_,m,*_=stores(); m.observe("o","old",3,{"x":"d"}); m.observe("o","new",8,{"x":"d"}); raises(ValueError,lambda:m.agree("o",{"x":"d"},2,2)); assert len(m.agree("o",{"x":"d"},2,5))==2

def test_i14(tmp_path):
    _,_,m,*_=stores(); m.observe("o","a",1,{"x":"d"}); m.observe("o","b",1,{"x":"other"}); raises(ValueError,lambda:m.agree("o",{"x":"d"},2,0))

def test_i15(tmp_path):
    _,_,m,*_=stores(); m.observe("o","a",1,{"x":"old"}); m.observe("o","a",2,{"x":"new"}); assert m.current("o")[0].artifacts == (("x","new"),)

def test_i16(tmp_path):
    _,_,m,*_=stores(); m.observe("left","a",4,{"x":"d"}); m.observe("right","b",4,{"x":"d"}); raises(ValueError,lambda:m.agree("left",{"x":"d"},2,0))

def test_i17(tmp_path):
    from packaging.federation import TransparencyLog
    log=TransparencyLog(); a=log.append("o","a","d"); b=log.append("o","b","e"); bad=(replace(a,digest="evil"),b); assert not log.verify(b,bad,log.checkpoint())

def test_i18(tmp_path):
    from packaging.federation import TransparencyLog
    log=TransparencyLog(); a=log.append("o","a","d"); b=log.append("o","b","e"); assert not log.verify(a,log.inclusion(a.index),log.checkpoint()); assert log.verify(b,log.inclusion(b.index),log.checkpoint())

def test_i19(tmp_path):
    *_,j,_=stores(); j.plan("p","o",(("erase",()),("invalidate",("erase",)))); raises(ValueError,lambda:j.complete("p","o","invalidate")); j.complete("p","o","erase"); assert j.complete("p","o","invalidate").completed==("erase","invalidate")

def test_i20(tmp_path):
    *_,j,_=stores(); j.plan("p","o",(("a",()),("b",("a",)),("c",("b",)),("side",()))); [j.complete("p","o",x) for x in ("a","b","c","side")]; j.seal("p","o"); item=j.reopen("p","o","b"); assert item.generation==1 and item.completed==("a","side") and item.state=="open"

def test_i21(tmp_path):
    *_,c,artifacts,digests=seeded(); item=c.attest("r1","acme",digests); assert item.state=="attested" and item.revision==1

def test_i22(tmp_path):
    *_,c,artifacts,digests=seeded(); c.attest("r1","acme",digests); item=c.publish("r1","acme",digests); assert item.state=="published" and len(item.audit)==1

def test_i23(tmp_path):
    *_,c,artifacts,digests=seeded(); c.attest("r1","acme",digests); c.publish("r1","acme",digests); assert c.audit("r1","acme",digests,c.log.checkpoint()); assert not c.audit("r1","acme",{**digests,"core.whl":"bad"},c.log.checkpoint())

def test_i24(tmp_path):
    p,_,_,_,_,c,artifacts,digests=seeded(); c.attest("r1","acme",digests); p.define("emergency",99,(("core-lib",">=9",None),)); raises(ValueError,lambda:c.publish("r1","acme",digests))
