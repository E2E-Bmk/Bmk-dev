"""Filtered public DiskCache oracle tests.

The scorer supplies the reference source tree on PYTHONPATH. These wrappers
expose only the retained upstream public-behavior tests under stable oracle
nodeids.
"""

from __future__ import annotations

import inspect

import pytest

from tests import test_core as _core
from tests import test_djangocache as _djangocache
from tests import test_fanout as _fanout
from tests import test_index as _index
from tests import test_recipes as _recipes

@pytest.fixture
def core_cache():
    yield from _core.cache.__wrapped__()

@pytest.fixture
def fanout_cache():
    yield from _fanout.cache.__wrapped__()

@pytest.fixture
def index_fixture():
    yield from _index.index.__wrapped__()

@pytest.fixture
def recipes_cache():
    yield from _recipes.cache.__wrapped__()

def _invoke(test, fixture):
    if inspect.signature(test).parameters:
        test(fixture)
    else:
        test()


class TestDjangoCache(_djangocache.DiskCacheTests):
    pass

for _name in dir(_djangocache.DiskCacheTests):
    if _name.startswith("test_"):
        setattr(TestDjangoCache, _name, None)

for _name in ["test_prefix","test_expiration","test_touch","test_set_many_expiration","test_long_timeout","test_forever_timeout","test_zero_timeout","test_float_timeout","test_cache_versioning_get_set","test_cache_versioning_add","test_cache_versioning_has_key","test_cache_versioning_delete","test_cache_versioning_incr_decr","test_cache_versioning_get_set_many","test_incr_version","test_decr_version","test_custom_key_func","test_creates_cache_dir_if_nonexistent","test_clear_does_not_remove_cache_dir","test_read","test_expire","test_evict","test_pop","test_memoize"]:
    setattr(
        TestDjangoCache,
        "test_djangocache__" + _name.removeprefix("test_"),
        getattr(_djangocache.DiskCacheTests, _name),
    )

del _name

def test_core__custom_disk(core_cache):
    _invoke(_core.test_custom_disk, core_cache)

def test_core__read(core_cache):
    _invoke(_core.test_read, core_cache)

def test_core__get_expired_fast_path(core_cache):
    _invoke(_core.test_get_expired_fast_path, core_cache)

def test_core__get_expired_slow_path(core_cache):
    _invoke(_core.test_get_expired_slow_path, core_cache)

def test_core__stats(core_cache):
    _invoke(_core.test_stats, core_cache)

def test_core__path(core_cache):
    _invoke(_core.test_path, core_cache)

def test_core__expire_rows(core_cache):
    _invoke(_core.test_expire_rows, core_cache)

def test_core__least_recently_stored(core_cache):
    _invoke(_core.test_least_recently_stored, core_cache)

def test_core__least_recently_used(core_cache):
    _invoke(_core.test_least_recently_used, core_cache)

def test_core__least_frequently_used(core_cache):
    _invoke(_core.test_least_frequently_used, core_cache)

def test_core__expire(core_cache):
    _invoke(_core.test_expire, core_cache)

def test_core__evict(core_cache):
    _invoke(_core.test_evict, core_cache)

def test_core__tag(core_cache):
    _invoke(_core.test_tag, core_cache)

def test_core__with(core_cache):
    _invoke(_core.test_with, core_cache)

def test_core__iter_expire(core_cache):
    _invoke(_core.test_iter_expire, core_cache)

def test_core__push_pull(core_cache):
    _invoke(_core.test_push_pull, core_cache)

def test_core__push_pull_prefix(core_cache):
    _invoke(_core.test_push_pull_prefix, core_cache)

def test_core__iterkeys(core_cache):
    _invoke(_core.test_iterkeys, core_cache)

def test_core__pickle(core_cache):
    _invoke(_core.test_pickle, core_cache)

def test_core__size_limit_with_files(core_cache):
    _invoke(_core.test_size_limit_with_files, core_cache)

def test_core__size_limit_with_database(core_cache):
    _invoke(_core.test_size_limit_with_database, core_cache)

def test_core__cull_eviction_policy_none(core_cache):
    _invoke(_core.test_cull_eviction_policy_none, core_cache)

def test_core__cull_size_limit_0(core_cache):
    _invoke(_core.test_cull_size_limit_0, core_cache)

def test_core__key_roundtrip(core_cache):
    _invoke(_core.test_key_roundtrip, core_cache)

def test_core__copy(core_cache):
    _invoke(_core.test_copy, core_cache)

def test_core__lru_incr(core_cache):
    _invoke(_core.test_lru_incr, core_cache)

def test_core__memoize(core_cache):
    _invoke(_core.test_memoize, core_cache)

def test_core__memoize_kwargs(core_cache):
    _invoke(_core.test_memoize_kwargs, core_cache)

def test_core__memoize_ignore(core_cache):
    _invoke(_core.test_memoize_ignore, core_cache)

def test_core__memoize_iter(core_cache):
    _invoke(_core.test_memoize_iter, core_cache)

def test_fanout__set_get_delete(fanout_cache):
    _invoke(_fanout.test_set_get_delete, fanout_cache)

def test_fanout__add_concurrent(fanout_cache):
    _invoke(_fanout.test_add_concurrent, fanout_cache)

def test_fanout__incr_concurrent(fanout_cache):
    _invoke(_fanout.test_incr_concurrent, fanout_cache)

def test_fanout__getsetdel(fanout_cache):
    _invoke(_fanout.test_getsetdel, fanout_cache)

def test_fanout__tag_index(fanout_cache):
    _invoke(_fanout.test_tag_index, fanout_cache)

def test_fanout__read(fanout_cache):
    _invoke(_fanout.test_read, fanout_cache)

def test_fanout__expire(fanout_cache):
    _invoke(_fanout.test_expire, fanout_cache)

def test_fanout__evict(fanout_cache):
    _invoke(_fanout.test_evict, fanout_cache)

def test_fanout__size_limit_with_files(fanout_cache):
    _invoke(_fanout.test_size_limit_with_files, fanout_cache)

def test_fanout__size_limit_with_database(fanout_cache):
    _invoke(_fanout.test_size_limit_with_database, fanout_cache)

def test_fanout__stats(fanout_cache):
    _invoke(_fanout.test_stats, fanout_cache)

def test_fanout__iter_expire(fanout_cache):
    _invoke(_fanout.test_iter_expire, fanout_cache)

def test_fanout__pickle(fanout_cache):
    _invoke(_fanout.test_pickle, fanout_cache)

def test_fanout__memoize(fanout_cache):
    _invoke(_fanout.test_memoize, fanout_cache)

def test_fanout__copy(fanout_cache):
    _invoke(_fanout.test_copy, fanout_cache)

def test_index__init(index_fixture):
    _invoke(_index.test_init, index_fixture)

def test_index__state(index_fixture):
    _invoke(_index.test_state, index_fixture)

def test_recipes__lock(recipes_cache):
    _invoke(_recipes.test_lock, recipes_cache)

def test_recipes__rlock(recipes_cache):
    _invoke(_recipes.test_rlock, recipes_cache)

def test_recipes__semaphore(recipes_cache):
    _invoke(_recipes.test_semaphore, recipes_cache)
