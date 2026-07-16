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

for _name in ["test_simple","test_default_used_when_none_is_set","test_add","test_non_existent","test_get_many","test_delete","test_delete_nonexistent","test_has_key","test_in","test_incr","test_decr","test_close","test_data_types","test_unicode","test_binary_string","test_set_many","test_set_many_returns_empty_list_on_success","test_delete_many","test_clear","test_add_fail_on_pickleerror","test_set_fail_on_pickleerror","test_get_or_set","test_get_or_set_callable","test_cache_write_unpicklable_type"]:
    setattr(
        TestDjangoCache,
        "test_djangocache__" + _name.removeprefix("test_"),
        getattr(_djangocache.DiskCacheTests, _name),
    )

del _name

def test_core__init(core_cache):
    _invoke(_core.test_init, core_cache)

def test_core__init_path(core_cache):
    _invoke(_core.test_init_path, core_cache)

def test_core__init_disk(core_cache):
    _invoke(_core.test_init_disk, core_cache)

def test_core__getsetdel(core_cache):
    _invoke(_core.test_getsetdel, core_cache)

def test_core__get_keyerror1(core_cache):
    _invoke(_core.test_get_keyerror1, core_cache)

def test_core__read_keyerror(core_cache):
    _invoke(_core.test_read_keyerror, core_cache)

def test_core__set_twice(core_cache):
    _invoke(_core.test_set_twice, core_cache)

def test_core__raw(core_cache):
    _invoke(_core.test_raw, core_cache)

def test_core__get(core_cache):
    _invoke(_core.test_get, core_cache)

def test_core__pop(core_cache):
    _invoke(_core.test_pop, core_cache)

def test_core__delete(core_cache):
    _invoke(_core.test_delete, core_cache)

def test_core__del(core_cache):
    _invoke(_core.test_del, core_cache)

def test_core__del_expired(core_cache):
    _invoke(_core.test_del_expired, core_cache)

def test_core__tag_index(core_cache):
    _invoke(_core.test_tag_index, core_cache)

def test_core__clear(core_cache):
    _invoke(_core.test_clear, core_cache)

def test_core__contains(core_cache):
    _invoke(_core.test_contains, core_cache)

def test_core__touch(core_cache):
    _invoke(_core.test_touch, core_cache)

def test_core__add(core_cache):
    _invoke(_core.test_add, core_cache)

def test_core__add_large_value(core_cache):
    _invoke(_core.test_add_large_value, core_cache)

def test_core__incr(core_cache):
    _invoke(_core.test_incr, core_cache)

def test_core__incr_insert_keyerror(core_cache):
    _invoke(_core.test_incr_insert_keyerror, core_cache)

def test_core__incr_update_keyerror(core_cache):
    _invoke(_core.test_incr_update_keyerror, core_cache)

def test_core__decr(core_cache):
    _invoke(_core.test_decr, core_cache)

def test_core__iter(core_cache):
    _invoke(_core.test_iter, core_cache)

def test_core__iter_error(core_cache):
    _invoke(_core.test_iter_error, core_cache)

def test_core__reversed(core_cache):
    _invoke(_core.test_reversed, core_cache)

def test_core__reversed_error(core_cache):
    _invoke(_core.test_reversed_error, core_cache)

def test_core__peekitem_extras(core_cache):
    _invoke(_core.test_peekitem_extras, core_cache)

def test_fanout__init(fanout_cache):
    _invoke(_fanout.test_init, fanout_cache)

def test_fanout__init_path(fanout_cache):
    _invoke(_fanout.test_init_path, fanout_cache)

def test_fanout__touch(fanout_cache):
    _invoke(_fanout.test_touch, fanout_cache)

def test_fanout__add(fanout_cache):
    _invoke(_fanout.test_add, fanout_cache)

def test_fanout__pop(fanout_cache):
    _invoke(_fanout.test_pop, fanout_cache)

def test_fanout__delitem(fanout_cache):
    _invoke(_fanout.test_delitem, fanout_cache)

def test_fanout__delitem_keyerror(fanout_cache):
    _invoke(_fanout.test_delitem_keyerror, fanout_cache)

def test_fanout__read_keyerror(fanout_cache):
    _invoke(_fanout.test_read_keyerror, fanout_cache)

def test_fanout__getitem_keyerror(fanout_cache):
    _invoke(_fanout.test_getitem_keyerror, fanout_cache)

def test_fanout__clear(fanout_cache):
    _invoke(_fanout.test_clear, fanout_cache)

def test_fanout__iter(fanout_cache):
    _invoke(_fanout.test_iter, fanout_cache)

def test_fanout__reversed(fanout_cache):
    _invoke(_fanout.test_reversed, fanout_cache)

def test_index__getsetdel(index_fixture):
    _invoke(_index.test_getsetdel, index_fixture)

def test_index__pop(index_fixture):
    _invoke(_index.test_pop, index_fixture)

def test_index__pop_keyerror(index_fixture):
    _invoke(_index.test_pop_keyerror, index_fixture)

def test_index__popitem(index_fixture):
    _invoke(_index.test_popitem, index_fixture)

def test_index__popitem_keyerror(index_fixture):
    _invoke(_index.test_popitem_keyerror, index_fixture)

def test_index__setdefault(index_fixture):
    _invoke(_index.test_setdefault, index_fixture)

def test_index__iter(index_fixture):
    _invoke(_index.test_iter, index_fixture)

def test_index__reversed(index_fixture):
    _invoke(_index.test_reversed, index_fixture)

def test_recipes__averager(recipes_cache):
    _invoke(_recipes.test_averager, recipes_cache)

def test_recipes__memoize_stampede(recipes_cache):
    _invoke(_recipes.test_memoize_stampede, recipes_cache)
