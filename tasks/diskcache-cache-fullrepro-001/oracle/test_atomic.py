# Spec2Repo oracle - atomic tests for diskcache-cache-fullrepro-001
import collections
import os
import time

import pytest

import diskcache as dc


def test_cache_creates_directory(tmp_path):
    directory = tmp_path / "cache"
    cache = dc.Cache(directory)
    assert os.path.isdir(cache.directory)
    cache.close()


def test_cache_rejects_invalid_disk(tmp_path):
    with pytest.raises(ValueError):
        dc.Cache(tmp_path / "cache", disk=object)


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


def test_cache_queue_prefix_uses_string_keys(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    key = cache.push("job", prefix="jobs")
    assert key == "jobs-500000000000000"
    assert cache.pull(prefix="jobs") == (key, "job")


def test_cache_queue_empty_returns_default(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    assert cache.pull(default=("none", None)) == ("none", None)
    assert cache.peek(default=("none", None)) == ("none", None)


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


def test_cache_memoize_rejects_bare_decorator_usage(tmp_path):
    cache = dc.Cache(tmp_path / "cache")
    with pytest.raises(TypeError):
        cache.memoize(lambda: None)


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


def test_averager_get_and_pop(tmp_path):
    cache = dc.Cache(tmp_path / "cache", eviction_policy="none")
    averager = dc.Averager(cache, "latency")
    assert averager.get() is None
    averager.add(0.08)
    averager.add(0.12)
    assert averager.get() == pytest.approx(0.10)
    assert averager.pop() == pytest.approx(0.10)
    assert averager.get() is None


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
