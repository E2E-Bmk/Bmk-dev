"""Atomic tests for diskcache-cache-fullrepro-001.

Each test verifies ONE public API entry point, ONE behavior.
"""

import os
import time

import pytest

import diskcache as dc


# --- Cache.set / get / mapping ---


def test_cache_set_returns_true_on_success(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    assert cache.set("alpha", {"v": 42}) is True


def test_cache_set_overwrites_existing_value(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    cache.set("k", "first")
    cache.set("k", "second")
    assert cache.get("k") == "second"


def test_cache_get_returns_default_for_missing_key(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    assert cache.get("absent", default="fallback") == "fallback"


def test_cache_mapping_read_raises_keyerror_for_missing(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    with pytest.raises(KeyError):
        _ = cache["nonexistent"]


def test_cache_mapping_delete_raises_keyerror_for_missing(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    with pytest.raises(KeyError):
        del cache["nonexistent"]


def test_cache_add_only_inserts_when_key_absent(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    assert cache.add("k", 10) is True
    assert cache.add("k", 20) is False
    assert cache["k"] == 10


def test_cache_touch_returns_true_for_existing_false_for_missing(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    cache["exists"] = "v"
    assert cache.touch("exists") is True
    assert cache.touch("absent") is False


def test_cache_delete_returns_true_for_existing_false_for_missing(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    cache["k"] = "v"
    assert cache.delete("k") is True
    assert cache.delete("k") is False


def test_cache_pop_removes_and_returns_value(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    cache["k"] = "val"
    assert cache.pop("k") == "val"
    assert cache.get("k") is None


def test_cache_pop_returns_default_for_missing(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    assert cache.pop("absent", default=99) == 99


# --- incr / decr ---


def test_cache_incr_creates_key_from_default(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    assert cache.incr("counter") == 1
    assert cache.incr("counter", 4) == 5


def test_cache_decr_subtracts_delta(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    cache["n"] = 20
    assert cache.decr("n", 7) == 13


def test_cache_incr_missing_with_none_default_raises_keyerror(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    with pytest.raises(KeyError):
        cache.incr("absent", default=None)


# --- clear / expire / evict ---


def test_cache_clear_returns_count_of_removed_items(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)
    assert cache.clear() == 3
    assert len(cache) == 0


def test_cache_expire_with_explicit_now_removes_expired(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    cache.set("short", "s", expire=10)
    cache.set("long", "l")
    removed = cache.expire(now=time.time() + 60)
    assert removed == 1
    assert cache.get("short") is None
    assert cache.get("long") == "l"


def test_cache_evict_removes_matching_tag(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    cache.set("a", 1, tag="group-x")
    cache.set("b", 2, tag="group-x")
    cache.set("c", 3, tag="group-y")
    assert cache.evict("group-x") == 2
    assert cache.get("c") == 3


# --- peekitem ---


def test_cache_peekitem_returns_insertion_edges(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    for k in ["alpha", "beta", "gamma"]:
        cache[k] = k.upper()
    assert cache.peekitem(last=False) == ("alpha", "ALPHA")
    assert cache.peekitem(last=True) == ("gamma", "GAMMA")


def test_cache_peekitem_empty_raises_keyerror(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    with pytest.raises(KeyError):
        cache.peekitem()


# --- Queue operations ---


def test_cache_push_front_and_back_keys(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    back = cache.push("back-item")
    front = cache.push("front-item", side="front")
    assert back == 500000000000000
    assert front == 499999999999999


def test_cache_push_with_prefix_uses_string_format(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    key = cache.push("task", prefix="queue")
    assert key == "queue-500000000000000"


def test_cache_pull_empty_returns_default(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    assert cache.pull(default=("empty", None)) == ("empty", None)


def test_cache_peek_empty_returns_default(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    assert cache.peek(default=("none", 0)) == ("none", 0)


# --- read ---


def test_cache_read_returns_file_like_object(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    payload_file = tmp_path / "blob.bin"
    payload_file.write_bytes(b"binary-content")
    with payload_file.open("rb") as f:
        cache.set("blob", f, read=True)
    with cache.read("blob") as reader:
        assert reader.read() == b"binary-content"


def test_cache_read_missing_raises_keyerror(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    with pytest.raises(KeyError):
        cache.read("missing")


# --- Settings and constants ---


def test_default_settings_contains_eviction_policy():
    assert dc.DEFAULT_SETTINGS["eviction_policy"] == "least-recently-stored"


def test_eviction_policy_covers_all_documented_choices():
    documented = {"least-recently-stored", "least-recently-used",
                  "least-frequently-used", "none"}
    assert documented <= set(dc.EVICTION_POLICY)


def test_cache_reset_returns_previous_and_updates_setting(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    prev = cache.reset("cull_limit", 0)
    assert isinstance(prev, int)
    assert cache.cull_limit == 0


def test_cache_tag_index_toggle(tmp_path):
    cache = dc.Cache(tmp_path / "c", tag_index=True)
    assert cache.tag_index == 1
    cache.drop_tag_index()
    assert cache.tag_index == 0
    cache.create_tag_index()
    assert cache.tag_index == 1


# --- volume / check ---


def test_cache_volume_returns_integer(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    cache["data"] = "x" * 100
    assert isinstance(cache.volume(), int)
    assert cache.volume() > 0


def test_cache_check_returns_list(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    result = cache.check()
    assert isinstance(result, list)
    assert result == []


# --- memoize ---


def test_cache_memoize_rejects_bare_callable(tmp_path):
    cache = dc.Cache(tmp_path / "c")
    with pytest.raises(TypeError):
        cache.memoize(lambda: None)


# --- disk validation ---


def test_cache_rejects_invalid_disk_argument(tmp_path):
    with pytest.raises(ValueError):
        dc.Cache(tmp_path / "c", disk=object)


# --- directory creation ---


def test_cache_creates_directory_on_construction(tmp_path):
    directory = tmp_path / "new_cache"
    cache = dc.Cache(directory)
    assert os.path.isdir(cache.directory)
    cache.close()


# --- Deque atomic ---


def test_deque_empty_pop_raises_indexerror(tmp_path):
    deque = dc.Deque(directory=tmp_path / "d")
    with pytest.raises(IndexError):
        deque.pop()


def test_deque_empty_popleft_raises_indexerror(tmp_path):
    deque = dc.Deque(directory=tmp_path / "d")
    with pytest.raises(IndexError):
        deque.popleft()


def test_deque_empty_peek_raises_indexerror(tmp_path):
    deque = dc.Deque(directory=tmp_path / "d")
    with pytest.raises(IndexError):
        deque.peek()


def test_deque_empty_peekleft_raises_indexerror(tmp_path):
    deque = dc.Deque(directory=tmp_path / "d")
    with pytest.raises(IndexError):
        deque.peekleft()


def test_deque_bounded_maxlen_discards_opposite_end(tmp_path):
    deque = dc.Deque("xyz", directory=tmp_path / "d", maxlen=3)
    deque.append("w")
    assert list(deque) == ["y", "z", "w"]


def test_deque_indexing_and_out_of_range_raises(tmp_path):
    deque = dc.Deque(["a", "b", "c"], directory=tmp_path / "d")
    assert deque[0] == "a"
    assert deque[-1] == "c"
    with pytest.raises(IndexError):
        _ = deque[10]


def test_deque_remove_absent_raises_valueerror(tmp_path):
    deque = dc.Deque(["a", "b"], directory=tmp_path / "d")
    with pytest.raises(ValueError):
        deque.remove("missing")


# --- Index atomic ---


def test_index_missing_read_raises_keyerror(tmp_path):
    index = dc.Index(directory=tmp_path / "idx")
    with pytest.raises(KeyError):
        _ = index["absent"]


def test_index_pop_missing_no_default_raises_keyerror(tmp_path):
    index = dc.Index(directory=tmp_path / "idx")
    with pytest.raises(KeyError):
        index.pop("absent")


def test_index_empty_popitem_raises_keyerror(tmp_path):
    index = dc.Index(directory=tmp_path / "idx")
    with pytest.raises(KeyError):
        index.popitem()


def test_index_empty_peekitem_raises_keyerror(tmp_path):
    index = dc.Index(directory=tmp_path / "idx")
    with pytest.raises(KeyError):
        index.peekitem()


def test_index_setdefault_inserts_only_for_missing(tmp_path):
    index = dc.Index(directory=tmp_path / "idx")
    assert index.setdefault("k", 10) == 10
    assert index.setdefault("k", 20) == 10


# --- Recipe atomic ---


def test_averager_get_returns_none_with_no_values(tmp_path):
    cache = dc.Cache(tmp_path / "c", eviction_policy="none")
    avg = dc.Averager(cache, "metric")
    assert avg.get() is None


def test_rlock_release_without_acquire_raises_assertion(tmp_path):
    cache = dc.Cache(tmp_path / "c", eviction_policy="none")
    lock = dc.RLock(cache, "rlock-key")
    with pytest.raises(AssertionError):
        lock.release()


def test_bounded_semaphore_over_release_raises_assertion(tmp_path):
    cache = dc.Cache(tmp_path / "c", eviction_policy="none")
    sem = dc.BoundedSemaphore(cache, "sem-key", value=1)
    sem.acquire()
    sem.release()
    with pytest.raises(AssertionError):
        sem.release()
