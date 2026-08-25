from tests.federation_support import raises, stores


def test_a09(tmp_path):
    policies, *_ = stores(); item = policies.define("base", 1, (("Demo_Pkg", ">=1", None),)); assert item.rules == (("demo-pkg", ">=1", None),); assert policies.define("base", 1, item.rules) is item

def test_a10(tmp_path):
    policies, *_ = stores(); policies.define("base", 1, (("demo", ">=1", None),)); policies.define("urgent", 9, (("demo", ">=2", None),)); assert dict(policies.project({})) == {"demo":">=2"}

def test_a11(tmp_path):
    policies, *_ = stores(); policies.define("platform", 1, (("demo", ">=2", "os_name == 'posix'"),)); assert dict(policies.project({"os_name":"nt"})) == {}; assert dict(policies.project({"os_name":"posix"})) == {"demo":">=2"}

def test_a12(tmp_path):
    policies, *_ = stores(); policies.define("base", 1, (("demo", ">=1,<3", None),)); lease = policies.lease("l", "o", {}, {"demo":("1.0","2.5","3.0")}); assert lease.selected == (("demo","2.5"),) and policies.valid("l","o")

def test_a13(tmp_path):
    _, witnesses, *_ = stores(); root = witnesses.add("src","o","src","d0","s"); leaf = witnesses.add("leaf","o","a.whl","d1","b1",(root.claim_id,)); assert witnesses.closure("leaf","o") == (root,leaf)

def test_a14(tmp_path):
    _, witnesses, *_ = stores(); witnesses.add("a","o","x","d","s1"); witnesses.add("b","o","x","d","s2"); assert {x.signer for x in witnesses.quorum("x","o",2)} == {"s1","s2"}

def test_a15(tmp_path):
    _, _, mirrors, *_ = stores(); first = mirrors.observe("o","m",1,{"x":"d"}); assert mirrors.observe("o","m",1,{"x":"d"}) is first; raises(ValueError, lambda: mirrors.observe("o","m",1,{"x":"other"}))

def test_a16(tmp_path):
    from packaging.federation import TransparencyLog
    log = TransparencyLog(); one = log.append("o","a","d1"); two = log.append("o","b","d2"); assert one.index == 0 and two.previous == one.entry_hash and log.checkpoint() == two.entry_hash
