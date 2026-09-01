from __future__ import annotations


def test_a01(tmp_path):
    from boltons.cacheutils import LRI
    c=LRI(max_size=2);c["a"]=1;c["b"]=2;assert c["a"]==1;c["c"]=3
    assert list(c)==["b","c"]


def test_a02(tmp_path):
    from boltons.cacheutils import LRI
    c=LRI(max_size=2);c["a"]=1;c["b"]=2;c["a"]=3;c["c"]=4
    assert list(c)==["a","c"] and c["a"]==3


def test_a03(tmp_path):
    from boltons.cacheutils import LRU
    c=LRU(max_size=2);c["a"]=1;c["b"]=2;assert c["a"]==1;c["c"]=3
    assert list(c)==["a","c"]


def test_a04(tmp_path):
    from boltons.cacheutils import LRI
    c=LRI(max_size=1);c["a"]=1;assert c["a"]==1
    try:c["missing"]
    except KeyError:pass
    assert c.hit_count==1 and c.miss_count==1


def test_a05(tmp_path):
    from boltons.cacheutils import make_cache_key
    assert make_cache_key((1,),{"b":2,"a":3})==make_cache_key((1,),{"a":3,"b":2})


def test_a06(tmp_path):
    from boltons.cacheutils import make_cache_key
    assert make_cache_key((1,),{},typed=False)==make_cache_key((1,),{},typed=False)
    assert make_cache_key((1,),{},typed=True)!=make_cache_key((1.0,),{},typed=True)


def test_a07(tmp_path):
    from boltons.cacheutils import cached
    cache={};calls=[]
    @cached(cache)
    def f(value):calls.append(value);return value*2
    assert f(4)==8 and f(4)==8 and calls==[4]


def test_a08(tmp_path):
    from boltons.cacheutils import LRU,cached
    cache=LRU(max_size=1);calls=[]
    @cached(cache)
    def f(value):calls.append(value);return value*2
    f(1);f(2);f(1);assert calls==[1,2,1]


def test_i01(tmp_path):
    from boltons.cacheutils import LRI
    c=LRI(max_size=3)
    for i in range(20):c[i]=i
    assert list(c)==[17,18,19] and len(c)==3


def test_i02(tmp_path):
    from boltons.cacheutils import LRU
    c=LRU(max_size=3);c.update((i,i) for i in range(3));_=c[0];_=c[1];c[3]=3
    assert list(c)==[0,1,3]


def test_i03(tmp_path):
    from boltons.cacheutils import cachedmethod
    class Model:
        def __init__(self):self.cache={};self.calls=0
        @cachedmethod(lambda obj:obj.cache)
        def f(self,value):self.calls+=1;return value+1
    a=Model();b=Model();assert a.f(2)==a.f(2)==3 and b.f(2)==3 and a.calls==1 and b.calls==1


def test_i04(tmp_path):
    from boltons.cacheutils import cached
    cache={};calls=[]
    @cached(cache)
    def f(value):calls.append(value);return value
    f(1);cache.clear();f(1);assert calls==[1,1]


def test_s01(tmp_path):
    from boltons.cacheutils import LRI,LRU
    lri=LRI(max_size=2);lru=LRU(max_size=2)
    for c in (lri,lru):c["a"]=1;c["b"]=2
    _=lri["a"];_=lru["a"];lri["c"]=3;lru["c"]=3
    assert list(lri)==["b","c"] and list(lru)==["a","c"]


def test_s02(tmp_path):
    from boltons.cacheutils import LRU,cached
    cache=LRU(max_size=2);calls=[]
    @cached(cache,typed=True)
    def f(value,scale=1):calls.append((value,scale));return value*scale
    assert f(1,scale=2)==2 and f(1,scale=2)==2 and f(1.0,scale=2)==2.0 and len(calls)==2
