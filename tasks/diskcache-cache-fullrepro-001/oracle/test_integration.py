"""Integration tests for diskcache-cache-fullrepro-001.

Each test crosses ≥2 public API boundaries. Tests target composition seams.
"""

import collections
import time

import pytest

import diskcache as dc


# --- State Consistency: write → read across projections ---


def test_mapping_write_visible_via_get_contains_iteration_len(tmp_path):
    """Seam: state consistency across multiple read projections."""
    cache = dc.Cache(tmp_path / "c")
    cache["alpha"] = {"data": 99}

    assert cache.get("alpha") == {"data": 99}
    assert "alpha" in cache
    assert len(cache) == 1
    assert "alpha" in list(cache)


def test_set_with_tag_removable_via_evict(tmp_path):
    """Seam: state consistency between set(tag=) and evict(tag)."""
    cache = dc.Cache(tmp_path / "c")
    cache.set("item-a", 1, tag="batch")
    cache.set("item-b", 2, tag="batch")
    cache.set("item-c", 3, tag="other")

    removed = cache.evict("batch")

    assert removed == 2
    assert cache.get("item-a") is None
    assert cache.get("item-c") == 3


def test_get_with_metadata_flags_returns_correct_tuple(tmp_path):
    """Seam: state consistency between set metadata and get metadata flags."""
    cache = dc.Cache(tmp_path / "c")
    cache.set("k", "payload", expire=None, tag="grp")

    value, expire_time, tag = cache.get("k", expire_time=True, tag=True)

    assert value == "payload"
    assert expire_time is None
    assert tag == "grp"


def test_pop_with_metadata_flags_removes_and_returns_tuple(tmp_path):
    """Seam: state consistency between set and pop with metadata."""
    cache = dc.Cache(tmp_path / "c")
    cache.set("k", "popped", tag="meta")

    value, expire_time, tag = cache.pop("k", expire_time=True, tag=True)

    assert value == "popped"
    assert tag == "meta"
    assert cache.get("k") is None


# --- Lifecycle Crossing: close → reopen ---


def test_cache_persists_across_close_and_reopen(tmp_path):
    """Seam: lifecycle crossing - data survives close/reopen."""
    directory = tmp_path / "persist"
    first = dc.Cache(directory)
    first["config"] = {"host": "localhost", "port": 8080}
    first.close()

    second = dc.Cache(directory)
    assert second["config"] == {"host": "localhost", "port": 8080}
    second.close()


def test_cache_auto_reopens_after_close(tmp_path):
    """Seam: lifecycle crossing - closed cache reopens on access."""
    cache = dc.Cache(tmp_path / "c")
    cache["k"] = "auto"
    cache.close()

    assert cache.get("k") == "auto"


def test_fanout_persists_across_close_and_reopen(tmp_path):
    """Seam: lifecycle crossing - FanoutCache survives close/reopen."""
    directory = tmp_path / "fanout"
    first = dc.FanoutCache(directory, shards=4, timeout=1)
    first.set("shared", "value")
    first.close()

    second = dc.FanoutCache(directory, shards=4, timeout=1)
    assert second.get("shared") == "value"
    second.close()


# --- Protocol Handoff: queue keys → lookup ---


def test_queue_push_pull_back_and_front_ordering(tmp_path):
    """Seam: protocol handoff between push key generation and pull retrieval."""
    cache = dc.Cache(tmp_path / "c")
    k1 = cache.push("first")
    k2 = cache.push("second")
    k0 = cache.push("zeroth", side="front")

    assert cache.peek() == (k0, "zeroth")
    assert cache.pull() == (k0, "zeroth")
    assert cache.pull(side="back") == (k2, "second")


def test_queue_prefix_key_visible_via_mapping_lookup(tmp_path):
    """Seam: protocol handoff between push(prefix=) and mapping get."""
    cache = dc.Cache(tmp_path / "c")
    key = cache.push("task-data", prefix="jobs")

    assert cache[key] == "task-data"
    assert cache.pull(prefix="jobs") == (key, "task-data")


# --- Config Interaction: stats ---


def test_stats_counts_hits_and_misses(tmp_path):
    """Seam: config interaction between stats enable and get operations."""
    cache = dc.Cache(tmp_path / "c")
    cache.stats(enable=True, reset=True)
    cache["k"] = "v"

    cache.get("k")
    cache.get("missing")

    hits, misses = cache.stats(enable=False, reset=True)
    assert hits == 1
    assert misses == 1


# --- Iteration ---


def test_iteration_follows_insertion_order(tmp_path):
    """Seam: state consistency between insertion order and iteration."""
    cache = dc.Cache(tmp_path / "c")
    for key in ["gamma", "alpha", "beta"]:
        cache[key] = key.upper()

    assert list(cache) == ["gamma", "alpha", "beta"]
    assert list(reversed(cache)) == ["beta", "alpha", "gamma"]


def test_iterkeys_produces_sorted_order(tmp_path):
    """Seam: state consistency between set and iterkeys ordering."""
    cache = dc.Cache(tmp_path / "c")
    for key in ["gamma", "alpha", "beta"]:
        cache[key] = key

    assert list(cache.iterkeys()) == ["alpha", "beta", "gamma"]


# --- Transaction ---


def test_cache_transact_groups_writes(tmp_path):
    """Seam: config interaction between transact context and cache state."""
    cache = dc.Cache(tmp_path / "c")
    with cache.transact():
        cache["sum"] = cache.get("sum", 0) + 5
        cache["count"] = cache.get("count", 0) + 1

    assert cache["sum"] == 5
    assert cache["count"] == 1


def test_fanout_transact_groups_writes_across_shards(tmp_path):
    """Seam: config interaction between FanoutCache.transact and shard state."""
    fanout = dc.FanoutCache(tmp_path / "f", timeout=1)
    with fanout.transact():
        fanout.incr("total", 7)
        fanout.incr("ops", 1)

    assert fanout["total"] == 7
    assert fanout["ops"] == 1
    fanout.close()


# --- Memoize integration ---


def test_memoize_caches_result_by_arguments(tmp_path):
    """Seam: state consistency between memoize decorator and cache storage."""
    cache = dc.Cache(tmp_path / "c")
    calls = {"n": 0}

    @cache.memoize()
    def compute(x, y=0):
        calls["n"] += 1
        return x + y

    assert compute(3, y=4) == 7
    assert compute(3, y=4) == 7
    assert calls["n"] == 1
    assert cache[compute.__cache_key__(3, y=4)] == 7


# --- FanoutCache named views ---


def test_fanout_named_cache_isolates_entries(tmp_path):
    """Seam: state consistency between named cache views."""
    fanout = dc.FanoutCache(tmp_path / "f", timeout=1)
    fanout.cache("tasks").set("status", "active")

    assert fanout.cache("tasks").get("status") == "active"
    assert fanout.cache("other").get("status") is None
    fanout.close()


def test_fanout_named_deque_isolates_entries(tmp_path):
    """Seam: state consistency between named deque views."""
    fanout = dc.FanoutCache(tmp_path / "f", timeout=1)
    fanout.deque("q1").append("item-a")

    assert list(fanout.deque("q1")) == ["item-a"]
    assert list(fanout.deque("q2")) == []
    fanout.close()


def test_fanout_named_index_isolates_entries(tmp_path):
    """Seam: state consistency between named index views."""
    fanout = dc.FanoutCache(tmp_path / "f", timeout=1)
    fanout.index("results")["job-x"] = "done"

    assert fanout.index("results")["job-x"] == "done"
    assert "job-x" not in fanout.index("other")
    fanout.close()


def test_fanout_evict_clear_across_shards(tmp_path):
    """Seam: state consistency between fanout aggregate ops and shards."""
    fanout = dc.FanoutCache(tmp_path / "f", shards=4, timeout=1)
    fanout.set("x", 1, tag="rm")
    fanout.set("y", 2, tag="rm")
    fanout.set("z", 3, tag="keep")

    assert fanout.evict("rm") == 2
    assert fanout.get("z") == 3
    assert fanout.clear() == 1
    fanout.close()


# --- Deque persistence and operations ---


def test_deque_persists_across_reopen(tmp_path):
    """Seam: lifecycle crossing - Deque data survives reopen."""
    directory = tmp_path / "deque"
    first = dc.Deque(range(4), directory=directory)
    first.append(4)
    first.appendleft(-1)

    reopened = dc.Deque(directory=directory)
    assert list(reopened) == [-1, 0, 1, 2, 3, 4]


def test_deque_mutations_visible_through_iteration(tmp_path):
    """Seam: state consistency between deque mutations and iteration."""
    deque = dc.Deque(["a", "b", "c", "a"], directory=tmp_path / "d")
    assert deque.count("a") == 2
    deque.remove("a")
    assert list(deque) == ["b", "c", "a"]
    deque.reverse()
    assert list(deque) == ["a", "c", "b"]
    deque.rotate(1)
    assert list(deque) == ["b", "a", "c"]


def test_deque_copy_shares_persistent_state(tmp_path):
    """Seam: lifecycle crossing - copy shares same directory."""
    deque = dc.Deque([10, 20], directory=tmp_path / "d")
    copied = deque.copy()
    copied.append(30)

    assert list(deque) == [10, 20, 30]


def test_deque_fromcache_exposes_underlying_cache(tmp_path):
    """Seam: protocol handoff between Deque.fromcache and cache object."""
    cache = dc.Cache(tmp_path / "c", eviction_policy="none")
    deque = dc.Deque.fromcache(cache, [5, 6])
    assert deque.cache is cache
    assert list(deque) == [5, 6]


# --- Index persistence and operations ---


def test_index_persists_across_reopen(tmp_path):
    """Seam: lifecycle crossing - Index data survives reopen."""
    directory = str(tmp_path / "idx")
    first = dc.Index(directory, [("x", 10), ("y", 20)])

    reopened = dc.Index(directory)
    assert reopened["x"] == 10
    assert reopened["y"] == 20


def test_index_views_and_ordered_equality(tmp_path):
    """Seam: state consistency between index operations and view objects."""
    pairs = [("x", 1), ("y", 2), ("z", 3)]
    index = dc.Index(str(tmp_path / "idx"), pairs)

    assert list(index.keys()) == ["x", "y", "z"]
    assert list(index.values()) == [1, 2, 3]
    assert list(index.items()) == pairs
    assert index == collections.OrderedDict(pairs)
    assert index != collections.OrderedDict(reversed(pairs))


def test_index_queue_helpers(tmp_path):
    """Seam: protocol handoff between Index.push/pull and key system."""
    index = dc.Index(directory=tmp_path / "idx")
    k1 = index.push("first")
    k2 = index.push("second")

    assert index.pull() == (k1, "first")
    pk = index.push("prefixed", prefix="p")
    assert pk == "p-500000000000000"
    assert index.pull(prefix="p") == (pk, "prefixed")


def test_index_fromcache_exposes_underlying_cache(tmp_path):
    """Seam: protocol handoff between Index.fromcache and cache object."""
    cache = dc.Cache(tmp_path / "c", eviction_policy="none")
    index = dc.Index.fromcache(cache, {"k": 42})
    assert index.cache is cache
    assert index["k"] == 42


def test_index_memoize_caches_function(tmp_path):
    """Seam: state consistency between Index.memoize and storage."""
    index = dc.Index(directory=tmp_path / "idx")
    calls = {"n": 0}

    @index.memoize()
    def square(v):
        calls["n"] += 1
        return v * v

    assert square(6) == 36
    assert square(6) == 36
    assert calls["n"] == 1


# --- Recipe integration ---


def test_lock_context_manager_acquires_and_releases(tmp_path):
    """Seam: state consistency between Lock acquire/release and locked()."""
    cache = dc.Cache(tmp_path / "c", eviction_policy="none")
    lock = dc.Lock(cache, "lk")

    assert lock.locked() is False
    with lock:
        assert lock.locked() is True
    assert lock.locked() is False


def test_rlock_reentrant_acquire_and_release(tmp_path):
    """Seam: config interaction between RLock reentrant state and release."""
    cache = dc.Cache(tmp_path / "c", eviction_policy="none")
    lock = dc.RLock(cache, "rlk")
    lock.acquire()
    lock.acquire()
    lock.release()
    lock.release()
    with pytest.raises(AssertionError):
        lock.release()


def test_averager_accumulates_and_pops(tmp_path):
    """Seam: state consistency between Averager add/get/pop and cache state."""
    cache = dc.Cache(tmp_path / "c", eviction_policy="none")
    avg = dc.Averager(cache, "latency")
    avg.add(0.1)
    avg.add(0.3)

    assert avg.get() == pytest.approx(0.2)
    assert avg.pop() == pytest.approx(0.2)
    assert avg.get() is None


def test_barrier_preserves_return_value(tmp_path):
    """Seam: state consistency between barrier lock and wrapped function."""
    cache = dc.Cache(tmp_path / "c", eviction_policy="none")

    @dc.barrier(cache, dc.Lock)
    def work(v):
        return v * 3

    assert work(5) == 15


def test_throttle_preserves_return_value(tmp_path):
    """Seam: config interaction between throttle rate tracking and function."""
    cache = dc.Cache(tmp_path / "c", eviction_policy="none")
    clock = {"now": 0.0, "slept": 0.0}

    @dc.throttle(
        cache, 1, 1,
        time_func=lambda: clock["now"],
        sleep_func=lambda s: (clock.update({"slept": clock["slept"] + s, "now": clock["now"] + s})),
    )
    def compute(v):
        return v + 1

    assert compute(4) == 5
    assert compute(7) == 8


def test_memoize_stampede_caches_with_elapsed_tuple(tmp_path):
    """Seam: state consistency between memoize_stampede and cache storage format."""
    cache = dc.Cache(tmp_path / "c", eviction_policy="none")
    calls = {"n": 0}

    @dc.memoize_stampede(cache, expire=120)
    def double(v):
        calls["n"] += 1
        return v * 2

    assert double(7) == 14
    assert double(7) == 14
    assert calls["n"] == 1
    cached_value, elapsed = cache[double.__cache_key__(7)]
    assert cached_value == 14
    assert elapsed >= 0
