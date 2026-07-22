# Spec2Repo oracle - integration tests for boltons-coreutils-fullrepro-001
"""Track B generated tests for boltons.iterutils and boltons.urlutils."""
import pytest
from boltons.iterutils import is_iterable, is_scalar, is_collection, split, split_iter, lstrip, lstrip_iter, rstrip, rstrip_iter, strip, chunked, chunked_iter, chunk_ranges, pairwise, pairwise_iter, windowed, windowed_iter, xfrange, frange, backoff, backoff_iter, bucketize, partition, unique, unique_iter, redundant, one, first, same, flatten, flatten_iter, remap, get_path, research, default_visit, default_enter, default_exit, PathAccessError, GUIDerator, SequentialGUIDerator, soft_sorted, untyped_sorted
from boltons.urlutils import URL, QueryParamDict, URLParseError, parse_url, find_all_links, quote_path_part, quote_query_part, quote_fragment_part, quote_userinfo_part, unquote, unquote_to_bytes, parse_host, parse_qsl, resolve_path_parts, register_scheme, to_unicode
from boltons.cacheutils import make_cache_key
from boltons.dictutils import FrozenDict, FrozenHashError
import string
import sys
from abc import abstractmethod, ABCMeta
import pytest
from boltons.cacheutils import LRU, LRI, cached, cachedmethod, cachedproperty, MinIDMap, ThresholdCounter

class CountingCallable:

    def __init__(self):
        self.call_count = 0

    def __call__(self, *a, **kw):
        self.call_count += 1
        return self.call_count

def _test_linkage(dll, max_count=10000, prev_idx=0, next_idx=1):
    """A function to test basic invariants of doubly-linked lists (with
    links made of Python lists).

    1. Test that the list is not longer than a certain length
    2. That the forward links (indicated by `next_idx`) correspond to
    the backward links (indicated by `prev_idx`).

    The `dll` parameter is the root/anchor link of the list.
    """
    start = cur = dll
    i = 0
    prev = None
    while 1:
        if i > max_count:
            raise Exception('did not return to anchor link after %r rounds' % max_count)
        if prev is not None and cur is start:
            break
        prev = cur
        cur = cur[next_idx]
        if cur[prev_idx] is not prev:
            raise Exception('prev_idx does not point to prev at i = %r' % i)
        i += 1
    return True
import sys
import pytest
from boltons.dictutils import OMD, OneToOne, ManyToMany, FrozenDict, subdict, FrozenHashError
_ITEMSETS = [[], [('a', 1), ('b', 2), ('c', 3)], [('A', 'One'), ('A', 'One'), ('A', 'One')], [('Z', -1), ('Y', -2), ('Y', -2)], [('a', 1), ('b', 2), ('a', 3), ('c', 4)]]
import string

def test_frozendict_mapping_and_updated_copy():
    fd = FrozenDict({'a': 'A', 'b': 'B'})
    newer = fd.updated({'b': 'Bee', 'c': 'C'})
    assert fd['b'] == 'B'
    assert newer == {'a': 'A', 'b': 'Bee', 'c': 'C'}

def test_remap_basic():
    result = remap({'a': 1, 'b': {'c': 2}})
    assert result == {'a': 1, 'b': {'c': 2}}

def test_research_basic():
    data = {'a': 1, 'b': {'c': 2, 'd': 3}}
    results = research(data, query=lambda p, k, v: v == 2)
    assert len(results) == 1
    assert results[0][1] == 2

def test_url_basic_parse():
    u = URL('http://example.com/path?q=1#frag')
    assert u.scheme == 'http'
    assert u.host == 'example.com'
    assert u.path == '/path'
    assert u.fragment == 'frag'

def test_url_normalize():
    u = URL('HTTP://Example.COM/./foo/../bar')
    u.normalize()
    assert u.scheme == 'http'
    assert u.host == 'example.com'

def test_url_navigate_relative():
    u = URL('http://example.com/a/b/c')
    result = u.navigate('../d')
    assert '/a/d' in result.to_text()

def test_url_from_parts():
    u = URL.from_parts(scheme='https', host='example.com', path_parts=('', 'foo'))
    assert 'example.com' in u.to_text()
    assert '/foo' in u.to_text()

def test_query_param_dict_from_text():
    qp = QueryParamDict.from_text('a=1&b=2&a=3')
    assert qp.getlist('a') == ['1', '3']

def test_find_all_links_basic():
    text = 'Visit http://example.com and http://other.org today.'
    links = find_all_links(text)
    assert len(links) == 2
    assert all((isinstance(u, URL) for u in links))

def test_find_all_links_with_text():
    text = 'See http://example.com for details.'
    tokens = find_all_links(text, with_text=True)
    assert any((isinstance(t, URL) for t in tokens))
    assert any((isinstance(t, str) for t in tokens))

def test_lru_add():
    cache = LRU(max_size=3)
    for i in range(4):
        cache[i] = i
    assert len(cache) == 3
    assert 0 not in cache

def test_lri():
    cache_size = 10
    bc = LRI(cache_size, on_miss=lambda k: k.upper())
    for idx, char in enumerate(string.ascii_letters):
        x = bc[char]
        assert x == char.upper()
        least_recent_insert_index = idx - cache_size
        if least_recent_insert_index >= 0:
            assert len(bc) == cache_size
            for char in string.ascii_letters[least_recent_insert_index + 1:idx]:
                assert char in bc
    bc[string.ascii_letters[-cache_size + 1]] = 'new value'
    least_recently_inserted_key = string.ascii_letters[-cache_size + 2]
    bc['unreferenced_key'] = 'value'
    keys_in_cache = [string.ascii_letters[i] for i in range(-cache_size + 1, 0) if string.ascii_letters[i] != least_recently_inserted_key]
    keys_in_cache.append('unreferenced_key')
    assert len(bc) == cache_size
    for k in keys_in_cache:
        assert k in bc

def test_lru_basic():
    lru = LRU(max_size=1)
    lru['hi'] = 0
    lru['bye'] = 1
    assert len(lru) == 1
    lru['bye']
    assert lru.get('hi') is None
    del lru['bye']
    assert 'bye' not in lru
    assert len(lru) == 0
    assert not lru
    try:
        lru.pop('bye')
    except KeyError:
        pass
    else:
        assert False
    default = object()
    assert lru.pop('bye', default) is default
    try:
        lru.popitem()
    except KeyError:
        pass
    else:
        assert False
    lru['another'] = 1
    assert lru.popitem() == ('another', 1)
    lru['yet_another'] = 2
    assert lru.pop('yet_another') == 2
    lru['yet_another'] = 3
    assert lru.pop('yet_another', default) == 3
    lru['yet_another'] = 4
    lru.clear()
    assert not lru
    lru['yet_another'] = 5
    second_lru = LRU(max_size=1)
    assert lru.copy() == lru
    second_lru['yet_another'] = 5
    assert second_lru == lru
    assert lru == second_lru
    lru.update(LRU(max_size=2, values=[('a', 1), ('b', 2)]))
    assert len(lru) == 1
    assert 'yet_another' not in lru
    lru.setdefault('x', 2)
    assert dict(lru) == {'x': 2}
    lru.setdefault('x', 3)
    assert dict(lru) == {'x': 2}
    assert lru != second_lru
    assert second_lru != lru

@pytest.mark.parametrize('lru_class', [LRU, LRI])
def test_lru_dict_replacement(lru_class):
    cache = lru_class()
    cache['a'] = 1
    assert cache['a'] == 1
    assert dict(cache) == {'a': 1}
    assert list(cache.values())[0] == 1
    cache['a'] = 200
    assert cache['a'] == 200
    assert dict(cache) == {'a': 200}
    assert list(cache.values())[0] == 200

def test_cached_dec():
    lru = LRU()
    inner_func = CountingCallable()
    func = cached(lru)(inner_func)
    assert inner_func.call_count == 0
    func()
    assert inner_func.call_count == 1
    func()
    assert inner_func.call_count == 1
    func('man door hand hook car door')
    assert inner_func.call_count == 2
    return

def test_unscoped_cached_dec():
    lru = LRU()
    inner_func = CountingCallable()
    func = cached(lru)(inner_func)
    other_inner_func = CountingCallable()
    other_func = cached(lru)(other_inner_func)
    assert inner_func.call_count == 0
    func('a')
    assert inner_func.call_count == 1
    func('a')
    other_func('a')
    assert other_inner_func.call_count == 0
    return

def test_callable_cached_dec():
    lru = LRU()
    get_lru = lambda: lru
    inner_func = CountingCallable()
    func = cached(get_lru)(inner_func)
    assert inner_func.call_count == 0
    func()
    assert inner_func.call_count == 1
    func()
    assert inner_func.call_count == 1
    lru.clear()
    func()
    assert inner_func.call_count == 2
    func()
    assert inner_func.call_count == 2

def test_cachedmethod():

    class Car:

        def __init__(self, cache=None):
            self.h_cache = LRI() if cache is None else cache
            self.door_count = 0
            self.hook_count = 0
            self.hand_count = 0

        @cachedmethod('h_cache')
        def hand(self, *a, **kw):
            self.hand_count += 1

        @cachedmethod(lambda obj: obj.h_cache)
        def hook(self, *a, **kw):
            self.hook_count += 1

        @cachedmethod('h_cache', scoped=False)
        def door(self, *a, **kw):
            self.door_count += 1
    car = Car()
    assert car.hand_count == 0
    car.hand('h', a='nd')
    assert car.hand_count == 1
    car.hand('h', a='nd')
    assert car.hand_count == 1
    assert car.hook_count == 0
    car.hook()
    assert car.hook_count == 1
    car.hook()
    assert car.hook_count == 1
    lru = LRU()
    car_one = Car(cache=lru)
    assert car_one.door_count == 0
    car_one.door('bob')
    assert car_one.door_count == 1
    car_one.door('bob')
    assert car_one.door_count == 1
    car_two = Car(cache=lru)
    assert car_two.door_count == 0
    car_two.door('bob')
    assert car_two.door_count == 0
    Car.door(Car(), 'bob')

def test_cachedmethod_maintains_func_abstraction():
    ABC = ABCMeta('ABC', (object,), {})

    class Car(ABC):

        def __init__(self, cache=None):
            self.h_cache = LRI() if cache is None else cache
            self.hand_count = 0

        @cachedmethod('h_cache')
        @abstractmethod
        def hand(self, *a, **kw):
            self.hand_count += 1
    with pytest.raises(TypeError):
        Car()

def test_cachedproperty():

    class Proper:

        def __init__(self):
            self.expensive_func = CountingCallable()

        @cachedproperty
        def useful_attr(self):
            """Useful DocString"""
            return self.expensive_func()
    prop = Proper()
    assert prop.expensive_func.call_count == 0
    assert prop.useful_attr == 1
    assert prop.expensive_func.call_count == 1
    assert prop.useful_attr == 1
    assert prop.expensive_func.call_count == 1
    assert Proper.useful_attr.__doc__ == 'Useful DocString'
    prop.useful_attr += 1
    assert prop.useful_attr == 2
    delattr(prop, 'useful_attr')
    assert prop.expensive_func.call_count == 1
    assert prop.useful_attr
    assert prop.expensive_func.call_count == 2

def test_cachedproperty_maintains_func_abstraction():
    ABC = ABCMeta('ABC', (object,), {})

    class AbstractExpensiveCalculator(ABC):

        @cachedproperty
        @abstractmethod
        def calculate(self):
            pass
    with pytest.raises(TypeError):
        AbstractExpensiveCalculator()

def test_min_id_map():
    import sys
    if '__pypy__' in sys.builtin_module_names:
        return
    midm = MinIDMap()

    class Foo:

        def __init__(self, val):
            self.val = val
    ref_wheel = [None, None, None]
    for i in range(1000):
        nxt = Foo(i)
        ref_wheel[i % len(ref_wheel)] = nxt
        assert midm.get(nxt) <= len(ref_wheel)
        if i % 10 == 0:
            midm.drop(nxt)
    assert sorted([f.val for f in list(midm)[:10]]) == list(range(1000 - len(ref_wheel), 1000))
    items = list(midm.iteritems())
    assert isinstance(items[0][0], Foo)
    assert sorted((item[1] for item in items)) == list(range(0, len(ref_wheel)))

def test_threshold_counter():
    tc = ThresholdCounter(threshold=0.1)
    tc.add(1)
    assert tc.items() == [(1, 1)]
    tc.update([2] * 10)
    assert tc.get(1) == 0
    tc.add(5)
    assert 5 in tc
    assert len(list(tc.elements())) == 11
    assert tc.threshold == 0.1
    assert tc.get_common_count() == 11
    assert tc.get_uncommon_count() == 1
    assert round(tc.get_commonality(), 2) == 0.92
    assert tc.most_common(2) == [(2, 10), (5, 1)]
    assert list(tc.elements()) == [2] * 10 + [5]
    assert tc[2] == 10
    assert len(tc) == 2
    assert sorted(tc.keys()) == [2, 5]
    assert sorted(tc.values()) == [1, 10]
    assert sorted(tc.items()) == [(2, 10), (5, 1)]

def test_dict_init():
    d = dict(_ITEMSETS[1])
    omd = OMD(d)
    assert omd['a'] == 1
    assert omd['b'] == 2
    assert omd['c'] == 3
    assert len(omd) == 3
    assert omd.getlist('a') == [1]
    assert omd == d

def test_todict():
    omd = OMD(_ITEMSETS[2])
    assert len(omd) == 1
    assert omd['A'] == 'One'
    d = omd.todict(multi=True)
    assert len(d) == 1
    assert d['A'] == ['One', 'One', 'One']
    flat = omd.todict()
    assert flat['A'] == 'One'
    for itemset in _ITEMSETS:
        omd = OMD(itemset)
        d = dict(itemset)
        flat = omd.todict()
        assert flat == d
    return

def test_eq():
    omd = OMD(_ITEMSETS[3])
    assert omd == omd
    assert not omd != omd
    omd2 = OMD(_ITEMSETS[3])
    assert omd == omd2
    assert omd2 == omd
    assert not omd != omd2
    d = dict(_ITEMSETS[3])
    assert d == omd
    omd3 = OMD(d)
    assert omd != omd3

def test_copy():
    for itemset in _ITEMSETS:
        omd = OMD(itemset)
        omd_c = omd.copy()
        assert omd == omd_c
        if omd_c:
            omd_c.pop(itemset[0][0])
            assert omd != omd_c
    return

def test_omd_pickle():
    import pickle
    empty = OMD()
    pickled = pickle.dumps(empty)
    roundtripped = pickle.loads(pickled)
    assert roundtripped == empty
    nonempty = OMD([('a', 1), ('b', 2), ('b', 3)])
    roundtripped = pickle.loads(pickle.dumps(nonempty))
    assert roundtripped == nonempty
    assert roundtripped.getlist('b') == [2, 3]

def test_clear():
    for itemset in _ITEMSETS:
        omd = OMD(itemset)
        omd.clear()
        assert len(omd) == 0
        assert not omd
        omd.clear()
        assert not omd
        omd['a'] = 22
        assert omd
        omd.clear()
        assert not omd

def test_multi_correctness():
    size = 100
    redun = 5
    _rng = range(size)
    _rng_redun = list(range(size // redun)) * redun
    _pairs = zip(_rng_redun, _rng)
    omd = OMD(_pairs)
    for multi in (True, False):
        vals = [x[1] for x in omd.iteritems(multi=multi)]
        strictly_ascending = all([x < y for x, y in zip(vals, vals[1:])])
        assert strictly_ascending
    return

def test_kv_consistency():
    for itemset in _ITEMSETS:
        omd = OMD(itemset)
        for multi in (True, False):
            items = omd.items(multi=multi)
            keys = omd.keys(multi=multi)
            values = omd.values(multi=multi)
            assert keys == [x[0] for x in items]
            assert values == [x[1] for x in items]
    return

def test_update_basic():
    omd = OMD(_ITEMSETS[1])
    omd2 = OMD({'a': 10})
    omd.update(omd2)
    assert omd['a'] == 10
    assert omd.getlist('a') == [10]
    omd2_c = omd2.copy()
    omd2_c.pop('a')
    assert omd2 != omd2_c

def test_update_extend():
    for first, second in zip(_ITEMSETS, _ITEMSETS[1:] + [[]]):
        omd1 = OMD(first)
        omd2 = OMD(second)
        ref = dict(first)
        orig_keys = set(omd1)
        ref.update(second)
        omd1.update_extend(omd2)
        for k in omd2:
            assert len(omd1.getlist(k)) >= len(omd2.getlist(k))
        assert omd1.todict() == ref
        assert orig_keys <= set(omd1)

def test_invert():
    for items in _ITEMSETS:
        omd = OMD(items)
        iomd = omd.inverted()
        assert len(omd.items(multi=True)) == len(iomd.items(multi=True))
        for val in omd.values():
            assert val in iomd

def test_poplast():
    for items in _ITEMSETS[1:]:
        omd = OMD(items)
        assert omd.poplast() == items[-1][-1]

def test_pop():
    omd = OMD()
    omd.add('even', 0)
    omd.add('odd', 1)
    omd.add('even', 2)
    assert omd.pop('odd') == 1
    assert omd.pop('odd', 99) == 99
    try:
        omd.pop('odd')
        assert False
    except KeyError:
        pass
    assert len(omd) == 1
    assert len(omd.items(multi=True)) == 2

def test_addlist():
    omd = OMD()
    omd.addlist('a', [1, 2, 3])
    omd.addlist('b', [4, 5])
    assert omd.keys() == ['a', 'b']
    assert len(list(omd.iteritems(multi=True))) == 5
    e_omd = OMD()
    e_omd.addlist('a', [])
    assert e_omd.keys() == []
    assert len(list(e_omd.iteritems(multi=True))) == 0

def test_pop_all():
    omd = OMD()
    omd.add('even', 0)
    omd.add('odd', 1)
    omd.add('even', 2)
    assert omd.popall('odd') == [1]
    assert len(omd) == 1
    try:
        omd.popall('odd')
        assert False
    except KeyError:
        pass
    assert omd.popall('odd', None) is None
    assert omd.popall('even') == [0, 2]
    assert len(omd) == 0
    assert omd.popall('nope', None) is None
    assert OMD().popall('', None) is None

def test_reversed():
    from collections import OrderedDict
    for items in _ITEMSETS:
        omd = OMD(items)
        od = OrderedDict(items)
        for ik, ok in zip(reversed(od), reversed(omd)):
            assert ik == ok
    r100 = range(100)
    omd = OMD(zip(r100, r100))
    for i in r100:
        omd.add(i, i)
    r100 = list(reversed(r100))
    assert list(reversed(omd)) == r100
    omd = OMD()
    assert list(reversed(omd)) == list(reversed(omd.keys()))
    for i in range(20):
        for j in range(i):
            omd.add(i, i)
    assert list(reversed(omd)) == list(reversed(omd.keys()))

def test_setdefault():
    omd = OMD()
    empty_list = []
    x = omd.setdefault('1', empty_list)
    assert x is empty_list
    y = omd.setdefault('2')
    assert y is None
    assert omd.setdefault('1', None) is empty_list
    e_omd = OMD()
    e_omd.addlist(1, [])
    assert e_omd.popall(1, None) is None
    assert len(e_omd) == 0

def test_ior():
    omd_a = OMD(_ITEMSETS[1])
    omd_b = OMD(_ITEMSETS[2])
    omd_c = OMD(_ITEMSETS[1])
    omd_a_id = id(omd_a)
    omd_a |= omd_b
    omd_c.update(omd_b)
    assert omd_a_id == id(omd_a)
    assert omd_a == omd_c

def test_subdict():
    cap_map = {x: x.upper() for x in string.hexdigits}
    assert len(cap_map) == 22
    assert len(subdict(cap_map, drop=['a'])) == 21
    assert 'a' not in subdict(cap_map, drop=['a'])
    assert len(subdict(cap_map, keep=['a', 'b'])) == 2

def test_subdict_keep_type():
    omd = OMD({'a': 'A'})
    assert subdict(omd) == omd
    assert type(subdict(omd)) is OMD

def test_one_to_one():
    e = OneToOne({1: 2})

    def ck(val, inv):
        assert (e, e.inv) == (val, inv)
    ck({1: 2}, {2: 1})
    e[2] = 3
    ck({1: 2, 2: 3}, {3: 2, 2: 1})
    e.clear()
    ck({}, {})
    e[1] = 1
    ck({1: 1}, {1: 1})
    e[1] = 2
    ck({1: 2}, {2: 1})
    e[3] = 2
    ck({3: 2}, {2: 3})
    del e[3]
    ck({}, {})
    e[1] = 2
    e.inv[2] = 3
    ck({3: 2}, {2: 3})
    del e.inv[2]
    ck({}, {})
    assert OneToOne({1: 2, 3: 4}).copy().inv == {2: 1, 4: 3}
    e[1] = 2
    e.pop(1)
    ck({}, {})
    e[1] = 2
    e.inv.pop(2)
    ck({}, {})
    e[1] = 2
    e.popitem()
    ck({}, {})
    e.setdefault(1)
    ck({1: None}, {None: 1})
    e.inv.setdefault(2)
    ck({1: None, None: 2}, {None: 1, 2: None})
    e.clear()
    e.update({})
    ck({}, {})
    e.update({1: 2}, cat='dog')
    ck({1: 2, 'cat': 'dog'}, {2: 1, 'dog': 'cat'})
    oto = OneToOne({'a': 0, 'b': 0})
    assert len(oto) == len(oto.inv) == 1
    oto['c'] = 0
    assert len(oto) == len(oto.inv) == 1
    assert oto.inv[0] == 'c'
    oto.update({'z': 0, 'y': 0})
    assert len(oto) == len(oto.inv) == 1
    with pytest.raises(ValueError):
        OneToOne.unique({'a': 0, 'b': 0})
    return
