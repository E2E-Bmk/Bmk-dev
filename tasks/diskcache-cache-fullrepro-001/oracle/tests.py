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


def test_cache_creates_directory(tmp_path):
    directory = tmp_path / "cache"
    cache = dc.Cache(directory)
    assert os.path.isdir(cache.directory)
    cache.close()


def test_cache_rejects_invalid_disk(tmp_path):
    with pytest.raises(ValueError):
        dc.Cache(tmp_path / "cache", disk=object)


def test_cache_mapping_roundtrip_and_membership(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    cache["alpha"] = {"count": 1}
    assert cache["alpha"] == {"count": 1}
    assert "alpha" in cache
    assert len(cache) == 1
    del cache["alpha"]
    assert "alpha" not in cache


def test_cache_missing_mapping_read_raises_keyerror(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    with pytest.raises(KeyError):
        _ = cache["missing"]


def test_cache_missing_mapping_delete_raises_keyerror(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    with pytest.raises(KeyError):
        del cache["missing"]


def test_cache_get_default_for_missing_key(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    assert cache.get("missing", default="fallback") == "fallback"


def test_cache_set_overwrites_existing_value(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    assert cache.set("k", "one") is True
    assert cache.set("k", "two") is True
    assert cache.get("k") == "two"


def test_cache_add_only_inserts_when_absent(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    assert cache.add("k", 1) is True
    assert cache.add("k", 2) is False
    assert cache["k"] == 1


def test_cache_touch_updates_existing_and_reports_missing(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    cache["k"] = "v"
    assert cache.touch("k", expire=None) is True
    assert cache.touch("missing", expire=1) is False


def test_cache_delete_boolean_contract(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    cache["k"] = "v"
    assert cache.delete("k") is True
    assert cache.delete("k") is False


def test_cache_pop_removes_and_returns_value(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    cache["k"] = "v"
    assert cache.pop("k") == "v"
    assert cache.get("k") is None


def test_cache_pop_default_for_missing_key(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    assert cache.pop("missing", default=17) == 17


def test_cache_metadata_tuple_get_and_pop(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    cache.set("k", "v", expire=None, tag="group")
    value, expire_time, tag = cache.get("k", expire_time=True, tag=True)
    assert (value, expire_time, tag) == ("v", None, "group")
    cache.set("k", "v", expire=None, tag="group")
    value, expire_time, tag = cache.pop("k", expire_time=True, tag=True)
    assert (value, expire_time, tag) == ("v", None, "group")


def test_cache_read_returns_file_like_object(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    with open(__file__, "rb") as reader:
        cache.set("blob", reader, read=True)
    with cache.read("blob") as reader:
        assert reader.read(6)


def test_cache_read_missing_key_raises_keyerror(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    with pytest.raises(KeyError):
        cache.read("missing")


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


def test_cache_clear_removes_all_items(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    cache.set("a", 1)
    cache.set("b", 2)
    assert cache.clear() == 2
    assert len(cache) == 0


def test_cache_incr_and_decr_existing_key(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    cache["n"] = 10
    assert cache.incr("n", 5) == 15
    assert cache.decr("n", 3) == 12
    assert cache["n"] == 12


def test_cache_incr_decr_missing_default_contract(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    assert cache.incr("a") == 1
    assert cache.decr("b", default=-9) == -10
    with pytest.raises(KeyError):
        cache.incr("c", default=None)


def test_cache_iteration_insertion_order_and_sorted_iterkeys(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    for key in "cab":
        cache[key] = key.upper()
    assert list(cache) == ["c", "a", "b"]
    assert list(cache.iterkeys()) == ["a", "b", "c"]
    assert list(reversed(cache)) == ["b", "a", "c"]


def test_cache_peekitem_reads_insertion_edges(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    for key in "abc":
        cache[key] = key.upper()
    assert cache.peekitem(last=False) == ("a", "A")
    assert cache.peekitem(last=True) == ("c", "C")


def test_cache_peekitem_empty_raises_keyerror(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    with pytest.raises(KeyError):
        cache.peekitem()


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


def test_cache_queue_prefix_uses_string_keys(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    key = cache.push("job", prefix="jobs")
    assert key == "jobs-500000000000000"
    assert cache.pull(prefix="jobs") == (key, "job")


def test_cache_queue_empty_returns_default(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    assert cache.pull(default=("none", None)) == ("none", None)
    assert cache.peek(default=("none", None)) == ("none", None)


def test_cache_stats_count_hits_and_misses(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    cache.stats(enable=True, reset=True)
    cache["a"] = 1
    assert cache.get("a") == 1
    assert cache.get("b") is None
    assert cache.stats(enable=False, reset=True) == (1, 1)


def test_cache_tag_index_toggle_setting(tmp_path):
    cache = dc.Cache(tmp_path / "cache", tag_index=True)
    assert cache.tag_index == 1
    cache.drop_tag_index()
    assert cache.tag_index == 0
    cache.create_tag_index()
    assert cache.tag_index == 1


def test_cache_reset_returns_previous_value_and_updates_setting(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    previous = cache.reset("cull_limit", 0)
    assert isinstance(previous, int)
    assert cache.cull_limit == 0


def test_cache_volume_and_check_public_shapes(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    cache["a"] = "b"
    assert isinstance(cache.volume(), int)
    assert isinstance(cache.check(), list)


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


def test_cache_memoize_rejects_bare_decorator_usage(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    with pytest.raises(TypeError):
        cache.memoize(lambda: None)


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


def test_fanout_transact_not_supported(tmp_path):
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


def test_deque_bounded_discards_opposite_end(tmp_path):
    deque = dc.Deque("abc", directory=tmp_path / "deque", maxlen=3)
    deque.append("d")
    assert list(deque) == ["b", "c", "d"]
    deque.appendleft("a")
    assert list(deque) == ["a", "b", "c"]


def test_deque_pop_peek_endpoint_contracts(tmp_path):
    deque = dc.Deque([1, 2, 3], directory=tmp_path / "deque")
    assert deque.peek() == 3
    assert deque.peekleft() == 1
    assert deque.pop() == 3
    assert deque.popleft() == 1
    assert list(deque) == [2]


def test_deque_empty_endpoint_errors(tmp_path):
    deque = dc.Deque(directory=tmp_path / "deque")
    for method in (deque.pop, deque.popleft, deque.peek, deque.peekleft):
        with pytest.raises(IndexError):
            method()


def test_deque_indexing_assignment_and_deletion(tmp_path):
    deque = dc.Deque(["a", "b", "c"], directory=tmp_path / "deque")
    assert deque[0] == "a"
    assert deque[-1] == "c"
    deque[1] = "B"
    del deque[0]
    assert list(deque) == ["B", "c"]
    with pytest.raises(IndexError):
        _ = deque[9]


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


def test_deque_copy_is_independent(tmp_path):
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


def test_index_mapping_operations(tmp_path):
    index = dc.Index(directory=tmp_path / "index")
    index["a"] = 1
    index["b"] = 2
    assert index.get("a") == 1
    assert index.get("missing", 9) == 9
    assert "b" in index
    del index["b"]
    assert "b" not in index
    with pytest.raises(KeyError):
        _ = index["b"]


def test_index_setdefault_and_pop_contract(tmp_path):
    index = dc.Index(directory=tmp_path / "index")
    assert index.setdefault("a", 1) == 1
    assert index.setdefault("a", 2) == 1
    assert index.pop("a") == 1
    assert index.pop("missing", default=3) == 3
    with pytest.raises(KeyError):
        index.pop("missing")


def test_index_peekitem_and_popitem_sides(tmp_path):
    index = dc.Index(str(tmp_path / "index"), [("a", 1), ("b", 2), ("c", 3)])
    assert index.peekitem(last=False) == ("a", 1)
    assert index.popitem(last=True) == ("c", 3)
    assert index.popitem(last=False) == ("a", 1)


def test_index_empty_peekitem_and_popitem_raise_keyerror(tmp_path):
    index = dc.Index(str(tmp_path / "index"))
    with pytest.raises(KeyError):
        index.peekitem()
    with pytest.raises(KeyError):
        index.popitem()


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


def test_averager_get_and_pop(tmp_path):
    cache = dc.Cache(tmp_path / "cache", eviction_policy="none")
    averager = dc.Averager(cache, "latency")
    assert averager.get() is None
    averager.add(0.08)
    averager.add(0.12)
    assert averager.get() == pytest.approx(0.10)
    assert averager.pop() == pytest.approx(0.10)
    assert averager.get() is None


def test_lock_context_and_locked_status(tmp_path):
    cache = dc.Cache(tmp_path / "cache", eviction_policy="none")
    lock = dc.Lock(cache, "lock")
    assert lock.locked() is False
    with lock:
        assert lock.locked() is True
    assert lock.locked() is False


def test_rlock_reentrant_release_contract(tmp_path):
    cache = dc.Cache(tmp_path / "cache", eviction_policy="none")
    lock = dc.RLock(cache, "rlock")
    lock.acquire()
    lock.acquire()
    lock.release()
    lock.release()
    with pytest.raises(AssertionError):
        lock.release()


def test_bounded_semaphore_release_contract(tmp_path):
    cache = dc.Cache(tmp_path / "cache", eviction_policy="none")
    semaphore = dc.BoundedSemaphore(cache, "sem", value=2)
    semaphore.acquire()
    semaphore.acquire()
    semaphore.release()
    semaphore.release()
    with pytest.raises(AssertionError):
        semaphore.release()


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
