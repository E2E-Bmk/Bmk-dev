# Spec2Repo oracle - integration tests for diskcache-cache-fullrepro-001
import collections
import os
import time

import pytest

import diskcache as dc


def test_import_surface_core_exports():
    for name in [
        "Averager",
        "BoundedSemaphore",
        "Cache",
        "DEFAULT_SETTINGS",
        "Deque",
        "Disk",
        "ENOVAL",
        "EVICTION_POLICY",
        "EmptyDirWarning",
        "FanoutCache",
        "Index",
        "JSONDisk",
        "Lock",
        "RLock",
        "Timeout",
        "UNKNOWN",
        "UnknownFileWarning",
        "barrier",
        "memoize_stampede",
        "throttle",
    ]:
        assert hasattr(dc, name)


def test_cache_mapping_roundtrip_and_membership(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    cache["alpha"] = {"count": 1}
    assert cache["alpha"] == {"count": 1}
    assert "alpha" in cache
    assert len(cache) == 1
    del cache["alpha"]
    assert "alpha" not in cache


def test_cache_metadata_tuple_get_and_pop(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    cache.set("k", "v", expire=None, tag="group")
    value, expire_time, tag = cache.get("k", expire_time=True, tag=True)
    assert (value, expire_time, tag) == ("v", None, "group")
    cache.set("k", "v", expire=None, tag="group")
    value, expire_time, tag = cache.pop("k", expire_time=True, tag=True)
    assert (value, expire_time, tag) == ("v", None, "group")


def test_cache_expire_removes_expired_items(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    cache.reset("cull_limit", 0)
    cache.set("old", "v", expire=0.001)
    time.sleep(0.01)
    assert cache.expire() >= 1
    assert cache.get("old") is None


def test_cache_evict_removes_matching_tag(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    cache.set("a", 1, tag="keep")
    cache.set("b", 2, tag="drop")
    cache.set("c", 3, tag="drop")
    assert cache.evict("drop") == 2
    assert cache.get("a") == 1
    assert cache.get("b") is None


def test_cache_iteration_insertion_order_and_sorted_iterkeys(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    for key in "cab":
        cache[key] = key.upper()
    assert list(cache) == ["c", "a", "b"]
    assert list(cache.iterkeys()) == ["a", "b", "c"]
    assert list(reversed(cache)) == ["b", "a", "c"]


def test_cache_queue_push_pull_back_and_front(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    first = cache.push("first")
    second = cache.push("second")
    zeroth = cache.push("zeroth", side="front")
    assert (first, second, zeroth) == (
        500000000000000,
        500000000000001,
        499999999999999,
    )
    assert cache.peek() == (zeroth, "zeroth")
    assert cache.pull() == (zeroth, "zeroth")
    assert cache.pull(side="back") == (second, "second")


def test_cache_stats_count_hits_and_misses(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    cache.stats(enable=True, reset=True)
    cache["a"] = 1
    assert cache.get("a") == 1
    assert cache.get("b") is None
    assert cache.stats(enable=False, reset=True) == (1, 1)


def test_cache_persists_across_reopened_objects(tmp_path):
    directory = tmp_path / "cache"
    first = dc.Cache(directory)
    first["a"] = {"x": 1}
    first.close()
    second = dc.Cache(directory)
    assert second["a"] == {"x": 1}


def test_cache_closed_object_reopens_on_access(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    cache["a"] = 1
    cache.close()
    assert cache.get("a") == 1


def test_cache_transaction_groups_writes(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    with cache.transact():
        cache["total"] = cache.get("total", 0) + 3
        cache["count"] = cache.get("count", 0) + 1
    assert (cache["total"], cache["count"]) == (3, 1)


def test_cache_memoize_caches_by_arguments(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    calls = {"count": 0}

    @cache.memoize()
    def add(a, b=0):
        calls["count"] += 1
        return a + b

    assert add(2, b=3) == 5
    assert add(2, b=3) == 5
    assert calls["count"] == 1
    assert cache[add.__cache_key__(2, b=3)] == 5


def test_fanout_mapping_roundtrip_and_membership(tmp_path):
    cache = dc.FanoutCache(tmp_path / "fanout", shards=4, timeout=1)
    cache["a"] = 1
    assert cache["a"] == 1
    assert cache.get("a") == 1
    assert "a" in cache
    del cache["a"]
    assert "a" not in cache


def test_fanout_persists_across_reopened_objects(tmp_path):
    directory = tmp_path / "fanout"
    first = dc.FanoutCache(directory, shards=4, timeout=1)
    first.set("k", "v")
    first.close()
    second = dc.FanoutCache(directory, shards=4, timeout=1)
    assert second.get("k") == "v"


def test_fanout_named_cache_view_persists_by_name(tmp_path):
    fanout = dc.FanoutCache(tmp_path / "fanout", timeout=1)
    fanout.cache("jobs").set("status", "ready")
    assert fanout.cache("jobs").get("status") == "ready"
    assert fanout.cache("other").get("status") is None


def test_fanout_named_deque_view_persists_by_name(tmp_path):
    fanout = dc.FanoutCache(tmp_path / "fanout", timeout=1)
    fanout.deque("queue").append("job-1")
    assert list(fanout.deque("queue")) == ["job-1"]
    assert list(fanout.deque("other")) == []


def test_fanout_named_index_view_persists_by_name(tmp_path):
    fanout = dc.FanoutCache(tmp_path / "fanout", timeout=1)
    fanout.index("results")["job-1"] = "queued"
    assert fanout.index("results")["job-1"] == "queued"
    assert "job-1" not in fanout.index("other")


def test_fanout_transact_groups_writes(tmp_path):
    cache = dc.FanoutCache(tmp_path / "fanout", timeout=1)
    with cache.transact():
        cache.incr("total", 3)
        cache.incr("count", 1)
    assert (cache["total"], cache["count"]) == (3, 1)


def test_fanout_expire_evict_clear_across_shards(tmp_path):
    cache = dc.FanoutCache(tmp_path / "fanout", shards=4, timeout=1)
    cache.set("a", 1, tag="drop")
    cache.set("b", 2, tag="drop")
    assert cache.evict("drop") == 2
    cache.set("c", 3)
    assert cache.clear() == 1


def test_deque_initialization_and_persistence(tmp_path):
    directory = tmp_path / "deque"
    deque = dc.Deque(range(3), directory=directory)
    deque.append(3)
    deque.appendleft(-1)
    assert list(deque) == [-1, 0, 1, 2, 3]
    assert list(dc.Deque(directory=directory)) == [-1, 0, 1, 2, 3]


def test_deque_remove_reverse_rotate_and_count(tmp_path):
    deque = dc.Deque(["a", "b", "a", "c"], directory=tmp_path / "deque")
    assert deque.count("a") == 2
    deque.remove("a")
    assert list(deque) == ["b", "a", "c"]
    deque.reverse()
    assert list(deque) == ["c", "a", "b"]
    deque.rotate(1)
    assert list(deque) == ["b", "c", "a"]
    with pytest.raises(ValueError):
        deque.remove("missing")


def test_deque_copy_shares_persistent_state(tmp_path):
    deque = dc.Deque([1, 2], directory=tmp_path / "deque")
    copied = deque.copy()
    assert list(copied) == [1, 2]
    copied.append(3)
    assert list(deque) == [1, 2, 3]


def test_deque_fromcache_exposes_same_cache(tmp_path):
    cache = dc.Cache(tmp_path / "cache", eviction_policy="none")
    deque = dc.Deque.fromcache(cache, [1, 2])
    assert deque.cache is cache
    assert list(deque) == [1, 2]


def test_index_initialization_and_persistence(tmp_path):
    directory = tmp_path / "index"
    index = dc.Index(str(directory), [("a", 1)], b=2)
    assert list(index) == ["a", "b"]
    assert dc.Index(str(directory))["b"] == 2


def test_index_queue_helpers(tmp_path):
    index = dc.Index(directory=tmp_path / "index")
    first = index.push("first")
    second = index.push("second")
    assert (first, second) == (500000000000000, 500000000000001)
    assert index.pull() == (first, "first")
    prefixed = index.push("job", prefix="jobs")
    assert prefixed == "jobs-500000000000000"
    assert index.pull(prefix="jobs") == (prefixed, "job")


def test_index_views_and_equality(tmp_path):
    pairs = [("a", 1), ("b", 2), ("c", 3)]
    index = dc.Index(str(tmp_path / "index"), pairs)
    assert list(index.keys()) == ["a", "b", "c"]
    assert list(index.values()) == [1, 2, 3]
    assert list(index.items()) == pairs
    assert index == {"c": 3, "b": 2, "a": 1}
    assert index == collections.OrderedDict(pairs)
    assert index != collections.OrderedDict(reversed(pairs))


def test_index_fromcache_exposes_same_cache(tmp_path):
    cache = dc.Cache(tmp_path / "cache", eviction_policy="none")
    index = dc.Index.fromcache(cache, {"a": 1})
    assert index.cache is cache
    assert index["a"] == 1


def test_index_memoize_caches_function_result(tmp_path):
    index = dc.Index(directory=tmp_path / "index")
    calls = {"count": 0}

    @index.memoize()
    def double(value):
        calls["count"] += 1
        return value * 2

    assert double(4) == 8
    assert double(4) == 8
    assert calls["count"] == 1


def test_lock_context_and_locked_status(tmp_path):
    cache = dc.Cache(tmp_path / "cache", eviction_policy="none")
    lock = dc.Lock(cache, "lock")
    assert lock.locked() is False
    with lock:
        assert lock.locked() is True
    assert lock.locked() is False


def test_barrier_preserves_return_value(tmp_path):
    cache = dc.Cache(tmp_path / "cache", eviction_policy="none")

    @dc.barrier(cache, dc.Lock)
    def work(value):
        return value + 1

    assert work(4) == 5


def test_throttle_preserves_return_value_with_injected_clock(tmp_path):
    cache = dc.Cache(tmp_path / "cache", eviction_policy="none")
    clock = {"now": 0.0, "slept": 0.0}

    def time_func():
        return clock["now"]

    def sleep_func(seconds):
        clock["slept"] += seconds
        clock["now"] += seconds

    calls = []

    @dc.throttle(cache, 1, 1, time_func=time_func, sleep_func=sleep_func)
    def work(value):
        calls.append(value)
        return value * 2

    assert work(3) == 6
    assert work(4) == 8
    assert calls == [3, 4]
    assert clock["slept"] >= 0


def test_memoize_stampede_caches_result_and_exposes_key(tmp_path):
    cache = dc.Cache(tmp_path / "cache", eviction_policy="none")
    calls = {"count": 0}

    @dc.memoize_stampede(cache, expire=60)
    def triple(value):
        calls["count"] += 1
        return value * 3

    assert triple(5) == 15
    assert triple(5) == 15
    assert calls["count"] == 1
    cached_result, elapsed = cache[triple.__cache_key__(5)]
    assert cached_result == 15
    assert elapsed >= 0
