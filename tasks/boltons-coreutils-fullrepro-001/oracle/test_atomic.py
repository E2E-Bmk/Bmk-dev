"""Atomic layer tests for boltons oracle suite.

Each test verifies ONE public API entry's ONE behavior.
Satisfies Independent Solvability: if only that one API is correctly
implemented (rest are stubs), the test passes.
"""
import pytest

# ---------------------------------------------------------------------------
# CACHE DOMAIN: LRI
# ---------------------------------------------------------------------------


class TestLRI:
    """Atomic tests for boltons.cacheutils.LRI."""

    def test_lri_invalid_max_size_zero_raises_valueerror(self):
        from boltons.cacheutils import LRI
        with pytest.raises(ValueError):
            LRI(max_size=0)

    def test_lri_invalid_max_size_negative_raises_valueerror(self):
        from boltons.cacheutils import LRI
        with pytest.raises(ValueError):
            LRI(max_size=-3)

    def test_lri_non_callable_on_miss_raises_typeerror(self):
        from boltons.cacheutils import LRI
        with pytest.raises(TypeError):
            LRI(max_size=5, on_miss="not_callable")

    def test_lri_insert_and_retrieve(self, lri_cache):
        lri_cache["alpha"] = 42
        assert lri_cache["alpha"] == 42

    def test_lri_evicts_oldest_by_insertion_order(self):
        from boltons.cacheutils import LRI
        c = LRI(max_size=3)
        c["m"] = 10
        c["n"] = 20
        c["o"] = 30
        c["p"] = 40
        assert "m" not in c
        assert c["p"] == 40
        assert len(c) == 3

    def test_lri_reassign_updates_insertion_recency(self):
        from boltons.cacheutils import LRI
        c = LRI(max_size=3)
        c["x"] = 1
        c["y"] = 2
        c["z"] = 3
        c["x"] = 99  # x becomes newly inserted
        c["w"] = 4   # y should be evicted (oldest after x reassign)
        assert "y" not in c
        assert c["x"] == 99

    def test_lri_on_miss_generates_value(self):
        from boltons.cacheutils import LRI
        from conftest import miss_handler
        c = LRI(max_size=5, on_miss=miss_handler)
        result = c["beta"]
        assert result == "generated_beta"
        assert "beta" in c

    def test_lri_get_returns_default_without_on_miss(self):
        from boltons.cacheutils import LRI
        c = LRI(max_size=5)
        result = c.get("nonexistent", "fallback_val")
        assert result == "fallback_val"

    def test_lri_missing_key_raises_keyerror(self):
        from boltons.cacheutils import LRI
        c = LRI(max_size=5)
        with pytest.raises(KeyError):
            _ = c["absent_key"]

    def test_lri_pop_removes_key(self):
        from boltons.cacheutils import LRI
        c = LRI(max_size=5)
        c["item"] = 77
        val = c.pop("item")
        assert val == 77
        assert "item" not in c

    def test_lri_clear_empties_cache(self):
        from boltons.cacheutils import LRI
        c = LRI(max_size=5)
        c["a1"] = 1
        c["b1"] = 2
        c.clear()
        assert len(c) == 0


# ---------------------------------------------------------------------------
# CACHE DOMAIN: LRU
# ---------------------------------------------------------------------------


class TestLRU:
    """Atomic tests for boltons.cacheutils.LRU."""

    def test_lru_invalid_max_size_raises_valueerror(self):
        from boltons.cacheutils import LRU
        with pytest.raises(ValueError):
            LRU(max_size=0)

    def test_lru_non_callable_on_miss_raises_typeerror(self):
        from boltons.cacheutils import LRU
        with pytest.raises(TypeError):
            LRU(max_size=5, on_miss=12345)

    def test_lru_access_updates_recency(self):
        from boltons.cacheutils import LRU
        c = LRU(max_size=3)
        c["k1"] = 10
        c["k2"] = 20
        c["k3"] = 30
        _ = c["k1"]  # k1 becomes most recently used
        c["k4"] = 40  # k2 should be evicted (LRU)
        assert "k2" not in c
        assert c["k1"] == 10

    def test_lru_evicts_least_recently_used(self):
        from boltons.cacheutils import LRU
        c = LRU(max_size=2)
        c["first"] = 100
        c["second"] = 200
        c["third"] = 300  # "first" is LRU
        assert "first" not in c
        assert c["second"] == 200
        assert c["third"] == 300

    def test_lru_missing_key_raises_keyerror(self):
        from boltons.cacheutils import LRU
        c = LRU(max_size=5)
        with pytest.raises(KeyError):
            _ = c["ghost"]

    def test_lru_replace_updates_value_and_recency(self):
        from boltons.cacheutils import LRU
        c = LRU(max_size=3)
        c["aa"] = 1
        c["bb"] = 2
        c["cc"] = 3
        c["aa"] = 111  # aa updated, becomes most recent
        c["dd"] = 4    # bb should be evicted
        assert "bb" not in c
        assert c["aa"] == 111

    def test_lru_get_returns_default_without_on_miss(self):
        from boltons.cacheutils import LRU
        c = LRU(max_size=5)
        assert c.get("missing", "sentinel") == "sentinel"

    def test_lru_on_miss_stores_and_returns(self):
        from boltons.cacheutils import LRU
        from conftest import miss_handler
        c = LRU(max_size=5, on_miss=miss_handler)
        result = c["gamma"]
        assert result == "generated_gamma"
        assert c["gamma"] == "generated_gamma"


# ---------------------------------------------------------------------------
# CACHE DOMAIN: make_cache_key
# ---------------------------------------------------------------------------


class TestMakeCacheKey:
    """Atomic tests for boltons.cacheutils.make_cache_key."""

    def test_typed_true_distinguishes_int_from_float(self):
        from boltons.cacheutils import make_cache_key
        key_int = make_cache_key((7,), {}, typed=True)
        key_float = make_cache_key((7.0,), {}, typed=True)
        assert key_int != key_float

    def test_typed_false_same_key_for_equivalent_args(self):
        from boltons.cacheutils import make_cache_key
        k1 = make_cache_key((5, "hello"), {"flag": True}, typed=False)
        k2 = make_cache_key((5, "hello"), {"flag": True}, typed=False)
        assert k1 == k2

    def test_different_kwargs_produce_different_keys(self):
        from boltons.cacheutils import make_cache_key
        k1 = make_cache_key((1,), {"mode": "fast"}, typed=False)
        k2 = make_cache_key((1,), {"mode": "slow"}, typed=False)
        assert k1 != k2


# ---------------------------------------------------------------------------
# CACHE DOMAIN: cached
# ---------------------------------------------------------------------------


class TestCached:
    """Atomic tests for boltons.cacheutils.cached."""

    def test_cached_stores_return_value(self):
        from boltons.cacheutils import cached
        store = {}
        call_count = [0]

        @cached(store)
        def compute(n):
            call_count[0] += 1
            return n ** 2 + 3

        r1 = compute(4)
        r2 = compute(4)
        assert r1 == 19
        assert r2 == 19
        assert call_count[0] == 1

    def test_cached_invalid_cache_raises_typeerror(self):
        from boltons.cacheutils import cached
        with pytest.raises(TypeError):
            @cached(12345)
            def noop(x):
                return x

    def test_cached_callable_cache_provider(self):
        from boltons.cacheutils import cached
        backing = {}

        @cached(lambda: backing)
        def add_five(x):
            return x + 5

        assert add_five(10) == 15
        assert len(backing) >= 1

    def test_cached_typed_true_separates_types(self):
        from boltons.cacheutils import cached
        store = {}
        call_count = [0]

        @cached(store, typed=True)
        def identity(val):
            call_count[0] += 1
            return val

        identity(3)
        identity(3.0)
        assert call_count[0] == 2


# ---------------------------------------------------------------------------
# CACHE DOMAIN: cachedmethod
# ---------------------------------------------------------------------------


class TestCachedMethod:
    """Atomic tests for boltons.cacheutils.cachedmethod."""

    def test_cachedmethod_caches_result(self):
        from boltons.cacheutils import cachedmethod

        class Svc:
            def __init__(self):
                self._cache = {}
                self._calls = 0

            @cachedmethod("_cache")
            def fetch(self, key):
                self._calls += 1
                return key.upper()

        s = Svc()
        r1 = s.fetch("word")
        r2 = s.fetch("word")
        assert r1 == "WORD"
        assert r2 == "WORD"
        assert s._calls == 1

    def test_cachedmethod_invalid_cache_raises_typeerror(self):
        from boltons.cacheutils import cachedmethod
        with pytest.raises(TypeError):
            @cachedmethod(999)
            def method(self, x):
                return x

    def test_cachedmethod_callable_cache_provider(self):
        from boltons.cacheutils import cachedmethod

        class Worker:
            def __init__(self):
                self.store = {}
                self.invocations = 0

            @cachedmethod(lambda self: self.store)
            def process(self, val):
                self.invocations += 1
                return val * 3

        w = Worker()
        assert w.process(7) == 21
        assert w.process(7) == 21
        assert w.invocations == 1


# ---------------------------------------------------------------------------
# CACHE DOMAIN: cachedproperty
# ---------------------------------------------------------------------------


class TestCachedProperty:
    """Atomic tests for boltons.cacheutils.cachedproperty."""

    def test_cachedproperty_computes_once(self):
        from boltons.cacheutils import cachedproperty

        class Expensive:
            def __init__(self):
                self._counter = 0

            @cachedproperty
            def result(self):
                self._counter += 1
                return 42 * 3

        obj = Expensive()
        assert obj.result == 126
        assert obj.result == 126
        assert obj._counter == 1

    def test_cachedproperty_class_access_returns_descriptor(self):
        from boltons.cacheutils import cachedproperty

        class Sample:
            @cachedproperty
            def val(self):
                return "computed"

        assert isinstance(Sample.__dict__["val"], cachedproperty)
        assert Sample.__dict__["val"].func.__name__ == "val"

    def test_cachedproperty_delete_clears_cache(self):
        from boltons.cacheutils import cachedproperty

        class Recomputable:
            def __init__(self):
                self._count = 0

            @cachedproperty
            def data(self):
                self._count += 1
                return self._count * 10

        obj = Recomputable()
        assert obj.data == 10
        del obj.__dict__["data"]
        assert obj.data == 20


# ---------------------------------------------------------------------------
# CACHE DOMAIN: ThresholdCounter
# ---------------------------------------------------------------------------


class TestThresholdCounter:
    """Atomic tests for boltons.cacheutils.ThresholdCounter."""

    def test_threshold_invalid_above_one_raises_valueerror(self):
        from boltons.cacheutils import ThresholdCounter
        with pytest.raises(ValueError):
            ThresholdCounter(threshold=1.5)

    def test_threshold_invalid_negative_raises_valueerror(self):
        from boltons.cacheutils import ThresholdCounter
        with pytest.raises(ValueError):
            ThresholdCounter(threshold=-0.1)

    def test_threshold_add_increments(self, threshold_counter):
        threshold_counter.add("apple")
        threshold_counter.add("apple")
        threshold_counter.add("apple")
        threshold_counter.add("banana")
        common = threshold_counter.most_common()
        keys_in_common = [k for k, _ in common]
        assert "apple" in keys_in_common

    def test_threshold_missing_key_raises_keyerror(self, threshold_counter):
        with pytest.raises(KeyError):
            _ = threshold_counter["never_added_key"]

    def test_threshold_get_returns_default_for_missing(self, threshold_counter):
        result = threshold_counter.get("absent_item", 0)
        assert result == 0


# ---------------------------------------------------------------------------
# CACHE DOMAIN: MinIDMap
# ---------------------------------------------------------------------------


class TestMinIDMap:
    """Atomic tests for boltons.cacheutils.MinIDMap."""

    def test_minidmap_stable_id(self):
        from boltons.cacheutils import MinIDMap
        m = MinIDMap()
        obj = object()
        id1 = m.get(obj)
        id2 = m.get(obj)
        assert id1 == id2
        assert isinstance(id1, int)

    def test_minidmap_drop_removes(self):
        from boltons.cacheutils import MinIDMap
        m = MinIDMap()
        obj = object()
        m.get(obj)
        assert obj in m
        m.drop(obj)
        assert obj not in m

    def test_minidmap_len_tracks_objects(self):
        from boltons.cacheutils import MinIDMap
        m = MinIDMap()
        objs = [object() for _ in range(5)]
        for o in objs:
            m.get(o)
        assert len(m) == 5


# ---------------------------------------------------------------------------
# CACHE DOMAIN: GUIDerator
# ---------------------------------------------------------------------------


class TestGUIDerator:
    """Atomic tests for boltons.iterutils.GUIDerator."""

    def test_guiderator_invalid_size_too_small_raises_valueerror(self):
        from boltons.iterutils import GUIDerator
        with pytest.raises(ValueError):
            GUIDerator(size=15)

    def test_guiderator_invalid_size_too_large_raises_valueerror(self):
        from boltons.iterutils import GUIDerator
        with pytest.raises(ValueError):
            GUIDerator(size=37)

    def test_guiderator_yields_correct_length(self):
        from boltons.iterutils import GUIDerator
        g = GUIDerator(size=28)
        guid = next(g)
        assert len(guid) == 28
        assert isinstance(guid, str)

    def test_sequential_guiderator_yields_correct_length(self):
        from boltons.iterutils import SequentialGUIDerator
        sg = SequentialGUIDerator(size=24)
        sid = next(sg)
        assert len(sid) == 24


# ---------------------------------------------------------------------------
# ORDERED MAPPING DOMAIN: OrderedMultiDict
# ---------------------------------------------------------------------------


class TestOrderedMultiDict:
    """Atomic tests for boltons.dictutils.OrderedMultiDict."""

    def test_omd_getlist_returns_all_values(self, omd_instance):
        result = omd_instance.getlist("color")
        assert result == ["red", "blue", "green"]

    def test_omd_subscript_returns_most_recent(self, omd_instance):
        assert omd_instance["color"] == "green"

    def test_omd_add_appends_without_replacing(self, omd_instance):
        omd_instance.add("size", "small")
        assert omd_instance.getlist("size") == ["large", "small"]

    def test_omd_assignment_replaces_all_values(self, omd_instance):
        omd_instance["color"] = "purple"
        assert omd_instance.getlist("color") == ["purple"]

    def test_omd_len_counts_unique_keys(self, omd_instance):
        assert len(omd_instance) == 3  # color, size, weight

    def test_omd_poplast_missing_key_raises_keyerror(self):
        from boltons.dictutils import OrderedMultiDict
        omd = OrderedMultiDict([("x", 1)])
        with pytest.raises(KeyError):
            omd.poplast("nonexistent")

    def test_omd_get_returns_default_for_missing(self, omd_instance):
        assert omd_instance.get("missing_key", "default_v") == "default_v"

    def test_omd_setdefault_stores_and_returns(self):
        from boltons.dictutils import OrderedMultiDict
        omd = OrderedMultiDict()
        val = omd.setdefault("new_key", "initial")
        assert val == "initial"
        assert omd["new_key"] == "initial"

    def test_omd_aliases_exist(self):
        from boltons.dictutils import OMD, MultiDict, OrderedMultiDict
        assert OMD is OrderedMultiDict
        assert MultiDict is OrderedMultiDict


# ---------------------------------------------------------------------------
# ORDERED MAPPING DOMAIN: FastIterOrderedMultiDict
# ---------------------------------------------------------------------------


class TestFastIterOMD:
    """Atomic tests for boltons.dictutils.FastIterOrderedMultiDict."""

    def test_fast_iter_omd_getlist(self):
        from boltons.dictutils import FastIterOrderedMultiDict
        fiomd = FastIterOrderedMultiDict([("tag", "a"), ("tag", "b"), ("id", "1")])
        assert fiomd.getlist("tag") == ["a", "b"]

    def test_fast_iter_omd_subscript(self):
        from boltons.dictutils import FastIterOrderedMultiDict
        fiomd = FastIterOrderedMultiDict([("k", "v1"), ("k", "v2")])
        assert fiomd["k"] == "v2"


# ---------------------------------------------------------------------------
# ORDERED MAPPING DOMAIN: OneToOne
# ---------------------------------------------------------------------------


class TestOneToOne:
    """Atomic tests for boltons.dictutils.OneToOne."""

    def test_onetoone_assignment_maintains_bijection(self):
        from boltons.dictutils import OneToOne
        oto = OneToOne({"cat": "meow", "dog": "bark"})
        oto["bird"] = "chirp"
        assert oto["bird"] == "chirp"
        assert oto.inv["chirp"] == "bird"

    def test_onetoone_reassign_value_removes_old_key(self):
        from boltons.dictutils import OneToOne
        oto = OneToOne({"a": 1, "b": 2})
        oto["c"] = 1  # value 1 was mapped by "a"
        assert "a" not in oto
        assert oto["c"] == 1

    def test_onetoone_unique_raises_on_duplicate_values(self):
        from boltons.dictutils import OneToOne
        with pytest.raises(ValueError):
            OneToOne.unique({"x": 10, "y": 10})

    def test_onetoone_inv_assignment_updates_forward(self):
        from boltons.dictutils import OneToOne
        oto = OneToOne({"sun": "star"})
        oto.inv["planet"] = "earth"
        assert oto["earth"] == "planet"

    def test_onetoone_pop_updates_inv(self):
        from boltons.dictutils import OneToOne
        oto = OneToOne({"key1": "val1"})
        oto.pop("key1")
        assert "val1" not in oto.inv


# ---------------------------------------------------------------------------
# ORDERED MAPPING DOMAIN: ManyToMany
# ---------------------------------------------------------------------------


class TestManyToMany:
    """Atomic tests for boltons.dictutils.ManyToMany."""

    def test_manytomany_add_creates_link(self):
        from boltons.dictutils import ManyToMany
        mm = ManyToMany()
        mm.add("course", "student_a")
        assert "student_a" in mm["course"]

    def test_manytomany_returns_frozenset(self):
        from boltons.dictutils import ManyToMany
        mm = ManyToMany([("g1", "m1"), ("g1", "m2")])
        vals = mm["g1"]
        assert isinstance(vals, frozenset)
        assert vals == frozenset({"m1", "m2"})

    def test_manytomany_remove_deletes_link(self):
        from boltons.dictutils import ManyToMany
        mm = ManyToMany([("team", "player1"), ("team", "player2")])
        mm.remove("team", "player1")
        assert "player1" not in mm["team"]

    def test_manytomany_del_removes_all_links(self):
        from boltons.dictutils import ManyToMany
        mm = ManyToMany([("bucket", "item1"), ("bucket", "item2")])
        del mm["bucket"]
        assert "bucket" not in mm


# ---------------------------------------------------------------------------
# ORDERED MAPPING DOMAIN: FrozenDict
# ---------------------------------------------------------------------------


class TestFrozenDict:
    """Atomic tests for boltons.dictutils.FrozenDict."""

    def test_frozendict_setitem_raises_typeerror(self):
        from boltons.dictutils import FrozenDict
        fd = FrozenDict({"stable": 1})
        with pytest.raises(TypeError):
            fd["new"] = 2

    def test_frozendict_delitem_raises_typeerror(self):
        from boltons.dictutils import FrozenDict
        fd = FrozenDict({"key": "val"})
        with pytest.raises(TypeError):
            del fd["key"]

    def test_frozendict_clear_raises_typeerror(self):
        from boltons.dictutils import FrozenDict
        fd = FrozenDict({"a": 1})
        with pytest.raises(TypeError):
            fd.clear()

    def test_frozendict_unhashable_raises_frozenhasherror(self):
        from boltons.dictutils import FrozenDict, FrozenHashError
        fd = FrozenDict({"data": [1, 2, 3]})
        with pytest.raises(FrozenHashError):
            hash(fd)

    def test_frozendict_hashable_values_can_hash(self):
        from boltons.dictutils import FrozenDict
        fd = FrozenDict({"x": 10, "y": 20})
        h = hash(fd)
        assert isinstance(h, int)
        assert h == hash(FrozenDict({"x": 10, "y": 20}))

    def test_frozendict_updated_returns_new(self):
        from boltons.dictutils import FrozenDict
        fd = FrozenDict({"a": 1, "b": 2})
        fd2 = fd.updated(b=99, c=3)
        assert fd2["b"] == 99
        assert fd2["c"] == 3
        assert fd["b"] == 2  # original unchanged


# ---------------------------------------------------------------------------
# ORDERED MAPPING DOMAIN: subdict
# ---------------------------------------------------------------------------


class TestSubdict:
    """Atomic tests for boltons.dictutils.subdict."""

    def test_subdict_keep_filters(self):
        from boltons.dictutils import subdict
        d = {"alpha": 1, "beta": 2, "gamma": 3, "delta": 4}
        result = subdict(d, keep=["alpha", "gamma"])
        assert result == {"alpha": 1, "gamma": 3}

    def test_subdict_drop_excludes(self):
        from boltons.dictutils import subdict
        d = {"alpha": 1, "beta": 2, "gamma": 3}
        result = subdict(d, drop=["beta"])
        assert "beta" not in result
        assert result == {"alpha": 1, "gamma": 3}

    def test_subdict_keep_then_drop(self):
        from boltons.dictutils import subdict
        d = {"a": 1, "b": 2, "c": 3, "d": 4}
        result = subdict(d, keep=["a", "b", "c"], drop=["b"])
        assert result == {"a": 1, "c": 3}

    def test_subdict_does_not_mutate_original(self):
        from boltons.dictutils import subdict
        d = {"x": 10, "y": 20, "z": 30}
        _ = subdict(d, keep=["x"])
        assert d == {"x": 10, "y": 20, "z": 30}


# ---------------------------------------------------------------------------
# ITERABLE DOMAIN: Type Checks
# ---------------------------------------------------------------------------


class TestTypeChecks:
    """Atomic tests for boltons.iterutils type-check functions."""

    def test_is_iterable_true_for_list(self):
        from boltons.iterutils import is_iterable
        assert is_iterable([1, 2, 3]) is True

    def test_is_iterable_false_for_int(self):
        from boltons.iterutils import is_iterable
        assert is_iterable(42) is False

    def test_is_scalar_true_for_string(self):
        from boltons.iterutils import is_scalar
        assert is_scalar("hello") is True

    def test_is_scalar_false_for_list(self):
        from boltons.iterutils import is_scalar
        assert is_scalar([1, 2]) is False


# ---------------------------------------------------------------------------
# ITERABLE DOMAIN: split
# ---------------------------------------------------------------------------


class TestSplit:
    """Atomic tests for boltons.iterutils.split."""

    def test_split_non_iterable_raises_typeerror(self):
        from boltons.iterutils import split
        with pytest.raises(TypeError):
            split(12345)

    def test_split_on_none_default(self):
        from boltons.iterutils import split
        result = split([1, 2, None, 3, None, 4])
        assert result == [[1, 2], [3], [4]]

    def test_split_on_specific_separator(self):
        from boltons.iterutils import split
        result = split([10, 0, 20, 0, 30], sep=0)
        assert result == [[10], [20], [30]]

    def test_split_with_maxsplit(self):
        from boltons.iterutils import split
        result = split(["a", "|", "b", "|", "c"], sep="|", maxsplit=1)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# ITERABLE DOMAIN: chunked
# ---------------------------------------------------------------------------


class TestChunked:
    """Atomic tests for boltons.iterutils.chunked."""

    def test_chunked_non_iterable_raises_typeerror(self):
        from boltons.iterutils import chunked
        with pytest.raises(TypeError):
            chunked(None, size=2)

    def test_chunked_non_positive_size_raises_valueerror(self):
        from boltons.iterutils import chunked
        with pytest.raises(ValueError):
            chunked([1, 2, 3], size=0)

    def test_chunked_negative_size_raises_valueerror(self):
        from boltons.iterutils import chunked
        with pytest.raises(ValueError):
            chunked([1, 2, 3], size=-1)

    def test_chunked_unknown_kwargs_raises_valueerror(self):
        from boltons.iterutils import chunked
        with pytest.raises(ValueError):
            chunked([1, 2, 3], size=2, bogus_param=True)

    def test_chunked_produces_correct_chunks(self):
        from boltons.iterutils import chunked
        result = chunked([10, 20, 30, 40, 50], size=2)
        assert result == [[10, 20], [30, 40], [50]]

    def test_chunked_with_fill(self):
        from boltons.iterutils import chunked
        result = chunked([1, 2, 3, 4, 5], size=3, fill=None)
        assert result[-1] == [4, 5, None]

    def test_chunked_string_preserves_type(self):
        from boltons.iterutils import chunked
        result = chunked("abcdef", size=3)
        assert result == ["abc", "def"]


# ---------------------------------------------------------------------------
# ITERABLE DOMAIN: windowed
# ---------------------------------------------------------------------------


class TestWindowed:
    """Atomic tests for boltons.iterutils.windowed."""

    def test_windowed_basic(self):
        from boltons.iterutils import windowed
        result = windowed([1, 2, 3, 4, 5], size=3)
        assert result == [(1, 2, 3), (2, 3, 4), (3, 4, 5)]

    def test_windowed_size_equals_input(self):
        from boltons.iterutils import windowed
        result = windowed([7, 8, 9], size=3)
        assert result == [(7, 8, 9)]


# ---------------------------------------------------------------------------
# ITERABLE DOMAIN: xfrange / frange
# ---------------------------------------------------------------------------


class TestXfrange:
    """Atomic tests for boltons.iterutils.xfrange."""

    def test_xfrange_zero_step_raises_valueerror(self):
        from boltons.iterutils import xfrange
        with pytest.raises(ValueError):
            list(xfrange(0.0, 5.0, 0.0))

    def test_xfrange_basic_range(self):
        from boltons.iterutils import xfrange
        result = list(xfrange(0.0, 1.0, 0.25))
        assert len(result) == 4
        assert abs(result[0] - 0.0) < 1e-9
        assert abs(result[-1] - 0.75) < 1e-9

    def test_xfrange_start_omitted_starts_at_zero(self):
        from boltons.iterutils import xfrange
        result = list(xfrange(1.0, 0.5))
        assert abs(result[0] - 0.0) < 1e-9


# ---------------------------------------------------------------------------
# ITERABLE DOMAIN: backoff
# ---------------------------------------------------------------------------


class TestBackoff:
    """Atomic tests for boltons.iterutils.backoff."""

    def test_backoff_count_repeat_raises_valueerror(self):
        from boltons.iterutils import backoff
        with pytest.raises(ValueError):
            backoff(start=1, stop=60, count="repeat")

    def test_backoff_negative_start_raises_valueerror(self):
        from boltons.iterutils import backoff
        with pytest.raises(ValueError):
            backoff(start=-1, stop=60)

    def test_backoff_stop_less_than_start_raises_valueerror(self):
        from boltons.iterutils import backoff
        with pytest.raises(ValueError):
            backoff(start=10, stop=5)

    def test_backoff_factor_below_one_raises_valueerror(self):
        from boltons.iterutils import backoff
        with pytest.raises(ValueError):
            backoff(start=1, stop=60, factor=0.5)

    def test_backoff_generates_increasing_delays(self):
        from boltons.iterutils import backoff
        delays = backoff(start=1, stop=64, factor=2.0, count=5, jitter=False)
        assert len(delays) == 5
        for i in range(1, len(delays)):
            assert delays[i] >= delays[i - 1]

    def test_backoff_never_exceeds_stop(self):
        from boltons.iterutils import backoff
        delays = backoff(start=1, stop=10, factor=3.0, count=8, jitter=False)
        for d in delays:
            assert d <= 10


# ---------------------------------------------------------------------------
# ITERABLE DOMAIN: bucketize
# ---------------------------------------------------------------------------


class TestBucketize:
    """Atomic tests for boltons.iterutils.bucketize."""

    def test_bucketize_by_callable(self):
        from boltons.iterutils import bucketize
        data = [1, 2, 3, 4, 5, 6, 7, 8]
        result = bucketize(data, key=lambda x: x % 3)
        assert set(result[0]) == {3, 6}
        assert set(result[1]) == {1, 4, 7}
        assert set(result[2]) == {2, 5, 8}

    def test_bucketize_with_value_transform(self):
        from boltons.iterutils import bucketize
        items = [("fruit", "apple"), ("veggie", "carrot"), ("fruit", "pear")]
        result = bucketize(items, key=lambda x: x[0], value_transform=lambda x: x[1])
        assert "apple" in result["fruit"]
        assert "carrot" in result["veggie"]


# ---------------------------------------------------------------------------
# ITERABLE DOMAIN: unique
# ---------------------------------------------------------------------------


class TestUnique:
    """Atomic tests for boltons.iterutils.unique."""

    def test_unique_preserves_first_occurrence(self):
        from boltons.iterutils import unique
        result = unique([5, 3, 5, 1, 3, 7, 1])
        assert result == [5, 3, 1, 7]

    def test_unique_empty_input(self):
        from boltons.iterutils import unique
        assert unique([]) == []


# ---------------------------------------------------------------------------
# ITERABLE DOMAIN: flatten
# ---------------------------------------------------------------------------


class TestFlatten:
    """Atomic tests for boltons.iterutils.flatten."""

    def test_flatten_nested_lists(self):
        from boltons.iterutils import flatten
        result = flatten([[1, 2], [3, [4, 5]], 6])
        assert result == [1, 2, 3, 4, 5, 6]

    def test_flatten_already_flat(self):
        from boltons.iterutils import flatten
        result = flatten([10, 20, 30])
        assert result == [10, 20, 30]


# ---------------------------------------------------------------------------
# ITERABLE DOMAIN: remap
# ---------------------------------------------------------------------------


class TestRemap:
    """Atomic tests for boltons.iterutils.remap."""

    def test_remap_non_callable_visit_raises_typeerror(self):
        from boltons.iterutils import remap
        with pytest.raises(TypeError):
            remap({"a": 1}, visit="not_a_func")

    def test_remap_non_callable_enter_raises_typeerror(self):
        from boltons.iterutils import remap
        with pytest.raises(TypeError):
            remap({"a": 1}, enter=123)

    def test_remap_non_callable_exit_raises_typeerror(self):
        from boltons.iterutils import remap
        with pytest.raises(TypeError):
            remap({"a": 1}, exit=456)

    def test_remap_unexpected_kwargs_raises_typeerror(self):
        from boltons.iterutils import remap
        with pytest.raises(TypeError):
            remap({"a": 1}, phantom_kwarg=True)

    def test_remap_identity_preserves_structure(self):
        from boltons.iterutils import remap
        data = {"x": [1, 2, {"y": 3}]}
        result = remap(data)
        assert result == data

    def test_remap_visit_drops_items(self):
        from boltons.iterutils import remap
        data = {"keep_me": 100, "drop_me": 200, "also_keep": 300}

        def visitor(path, key, value):
            if key == "drop_me":
                return False
            return True

        result = remap(data, visit=visitor)
        assert "keep_me" in result
        assert "drop_me" not in result


# ---------------------------------------------------------------------------
# ITERABLE DOMAIN: get_path
# ---------------------------------------------------------------------------


class TestGetPath:
    """Atomic tests for boltons.iterutils.get_path."""

    def test_get_path_missing_raises_path_access_error(self):
        from boltons.iterutils import get_path, PathAccessError
        data = {"a": {"b": 10}}
        with pytest.raises(PathAccessError):
            get_path(data, ("a", "c"))

    def test_get_path_indexes_nested(self):
        from boltons.iterutils import get_path
        data = {"lvl1": {"lvl2": [100, 200, 300]}}
        assert get_path(data, ("lvl1", "lvl2", 1)) == 200

    def test_get_path_with_default(self):
        from boltons.iterutils import get_path
        data = {"only": "one_level"}
        result = get_path(data, ("only", "deeper"), default="safe")
        assert result == "safe"

    def test_get_path_string_path(self):
        from boltons.iterutils import get_path
        data = {"first": {"second": "target_val"}}
        result = get_path(data, "first.second")
        assert result == "target_val"


# ---------------------------------------------------------------------------
# ITERABLE DOMAIN: research
# ---------------------------------------------------------------------------


class TestResearch:
    """Atomic tests for boltons.iterutils.research."""

    def test_research_finds_matching_paths(self):
        from boltons.iterutils import research
        data = {"a": 1, "b": {"c": 2, "d": 3}}
        matches = research(data, query=lambda p, k, v: v == 2)
        paths = [m[0] for m in matches]
        assert any("c" in p for p in paths)

    def test_research_no_match_returns_empty(self):
        from boltons.iterutils import research
        data = {"x": 10, "y": 20}
        matches = research(data, query=lambda p, k, v: v > 100)
        assert matches == []


# ---------------------------------------------------------------------------
# URL DOMAIN: URL
# ---------------------------------------------------------------------------


class TestURL:
    """Atomic tests for boltons.urlutils.URL."""

    def test_url_parses_scheme(self, url_instance):
        assert url_instance.scheme == "https"

    def test_url_parses_host(self, url_instance):
        assert url_instance.host == "portal.example.test"

    def test_url_parses_port(self, url_instance):
        assert url_instance.port == 8443

    def test_url_parses_path(self, url_instance):
        assert "/api/v2" in url_instance.path

    def test_url_parses_fragment(self, url_instance):
        assert url_instance.fragment == "section"

    def test_url_malformed_raises_urlparseerror(self):
        from boltons.urlutils import URL, URLParseError
        with pytest.raises(URLParseError):
            URL("http://[invalid:ipv6:::")

    def test_url_navigate_relative(self, url_instance):
        u2 = url_instance.navigate("../other/page")
        assert "other" in u2.path

    def test_url_normalize_removes_default_port(self):
        from boltons.urlutils import URL
        u = URL("https://host.example.test:443/path")
        u.normalize()
        assert u.port is None or ":443" not in u.to_text()

    def test_url_from_bytes(self):
        from boltons.urlutils import URL
        u = URL(b"http://bytes.example.test/resource")
        assert u.host == "bytes.example.test"

    def test_url_equality_same_components(self):
        from boltons.urlutils import URL
        u1 = URL("http://eq.example.test/path?k=v")
        u2 = URL("http://eq.example.test/path?k=v")
        assert u1 == u2


# ---------------------------------------------------------------------------
# URL DOMAIN: parse_url
# ---------------------------------------------------------------------------


class TestParseUrl:
    """Atomic tests for boltons.urlutils.parse_url."""

    def test_parse_url_non_integer_port_raises_urlparseerror(self):
        from boltons.urlutils import parse_url, URLParseError
        with pytest.raises(URLParseError):
            parse_url("http://host.example.test:abc/path")

    def test_parse_url_extracts_components(self):
        from boltons.urlutils import parse_url
        parts = parse_url("https://user:pw@srv.example.test:9090/dir?q=1#f")
        assert parts["scheme"] == "https"
        assert parts["host"] == "srv.example.test"
        assert parts["port"] == 9090
        assert parts["fragment"] == "f"


# ---------------------------------------------------------------------------
# URL DOMAIN: parse_host
# ---------------------------------------------------------------------------


class TestParseHost:
    """Atomic tests for boltons.urlutils.parse_host."""

    def test_parse_host_invalid_ipv6_raises_urlparseerror(self):
        from boltons.urlutils import parse_host, URLParseError
        with pytest.raises(URLParseError):
            parse_host("[::not::valid::ipv6")

    def test_parse_host_returns_family_and_text(self):
        import socket
        from boltons.urlutils import parse_host
        family, host_text = parse_host("192.168.1.1")
        assert family == socket.AF_INET
        assert host_text == "192.168.1.1"


# ---------------------------------------------------------------------------
# URL DOMAIN: QueryParamDict
# ---------------------------------------------------------------------------


class TestQueryParamDict:
    """Atomic tests for boltons.urlutils.QueryParamDict."""

    def test_qpd_from_text_parses(self):
        from boltons.urlutils import QueryParamDict
        qp = QueryParamDict.from_text("lang=py&ver=3&lang=rs")
        assert qp["lang"] == "rs"
        assert qp.getlist("lang") == ["py", "rs"]

    def test_qpd_to_text_serializes(self):
        from boltons.urlutils import QueryParamDict
        qp = QueryParamDict.from_text("item=book&qty=5")
        text = qp.to_text()
        assert "item=book" in text
        assert "qty=5" in text


# ---------------------------------------------------------------------------
# URL DOMAIN: find_all_links
# ---------------------------------------------------------------------------


class TestFindAllLinks:
    """Atomic tests for boltons.urlutils.find_all_links."""

    def test_find_all_links_extracts_urls(self):
        from boltons.urlutils import find_all_links
        text = "Check https://docs.example.test/guide and http://api.example.test/v1 for info."
        links = find_all_links(text)
        assert len(links) >= 2

    def test_find_all_links_with_schemes_filter(self):
        from boltons.urlutils import find_all_links
        text = "Visit https://secure.example.test or ftp://files.example.test/pub"
        links = find_all_links(text, schemes=["https"])
        hosts = [l.host for l in links]
        assert "secure.example.test" in hosts
        assert "files.example.test" not in hosts

    def test_find_all_links_trims_punctuation(self):
        from boltons.urlutils import find_all_links
        text = "(see https://ref.example.test/page)."
        links = find_all_links(text)
        assert len(links) >= 1
        url_text = links[0].to_text()
        assert not url_text.endswith(").")
