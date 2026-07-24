# Spec2Repo oracle - atomic tests for boltons-coreutils-fullrepro-001
"""Track B generated tests for boltons.iterutils and boltons.urlutils."""
import pytest
from boltons.iterutils import is_iterable, is_scalar, is_collection, split, split_iter, lstrip, lstrip_iter, rstrip, rstrip_iter, strip, chunked, chunked_iter, chunk_ranges, pairwise, pairwise_iter, windowed, windowed_iter, xfrange, frange, backoff, backoff_iter, bucketize, partition, unique, unique_iter, redundant, one, first, same, flatten, flatten_iter, remap, get_path, research, default_visit, default_enter, default_exit, PathAccessError, GUIDerator, SequentialGUIDerator, soft_sorted, untyped_sorted
from boltons.urlutils import URL, QueryParamDict, URLParseError, parse_url, find_all_links, quote_path_part, quote_query_part, quote_fragment_part, quote_userinfo_part, unquote, unquote_to_bytes, parse_host, parse_qsl, resolve_path_parts, register_scheme, to_unicode
from boltons.cacheutils import make_cache_key
from boltons.dictutils import FrozenDict, FrozenHashError

def test_make_cache_key_single_fast_arg():
    assert make_cache_key(('alpha',), {}) == 'alpha'

def test_make_cache_key_kwargs_are_order_independent():
    assert make_cache_key((), {'b': 2, 'a': 1}) == make_cache_key((), {'a': 1, 'b': 2})

def test_make_cache_key_typed_distinguishes_equal_values():
    assert make_cache_key((3,), {}, typed=True) != make_cache_key((3.0,), {}, typed=True)

def test_frozendict_rejects_mutation():
    fd = FrozenDict({'a': 'A'})
    with pytest.raises(TypeError):
        fd['b'] = 'B'

def test_frozendict_hash_error_for_unhashable_values():
    fd = FrozenDict({'a': []})
    with pytest.raises(FrozenHashError):
        hash(fd)

def test_is_iterable_list():
    assert is_iterable([1, 2, 3])

def test_is_scalar_string():
    assert is_scalar('hello')

def test_is_collection_list():
    assert is_collection([1, 2])

def test_split_basic_sep():
    assert split([1, 2, 0, 3, 4], sep=0) == [[1, 2], [3, 4]]

def test_split_callable_sep():
    result = split([1, 2, 3, 4, 5], sep=lambda x: x % 2 == 0)
    assert result == [[1], [3], [5]]

def test_lstrip_removes_leading():
    assert list(lstrip_iter([None, None, 1, 2, None])) == [1, 2, None]

def test_strip_both_ends():
    assert list(strip([None, 1, 2, None], strip_value=None)) == [1, 2]

def test_chunked_basic():
    assert chunked([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]

def test_chunk_ranges_basic():
    result = list(chunk_ranges(10, 3))
    assert result == [(0, 3), (3, 6), (6, 9), (9, 10)]

def test_pairwise_basic():
    result = pairwise([1, 2, 3, 4])
    assert list(result) == [(1, 2), (2, 3), (3, 4)]

def test_windowed_basic():
    result = windowed([1, 2, 3, 4], 3)
    assert list(result) == [(1, 2, 3), (2, 3, 4)]

def test_xfrange_basic():
    result = list(xfrange(3.0))
    assert result[0] == 0.0
    assert len(result) == 3

def test_frange_basic():
    result = frange(4.0)
    assert result[0] == 0.0
    assert len(result) == 4

def test_backoff_basic():
    result = backoff(1, 10)
    assert result[0] == 1.0
    assert result[-1] == 10.0

def test_bucketize_basic():
    result = bucketize([1, 2, 3, 4], key=lambda x: x % 2)
    assert set(result.keys()) == {0, 1}

def test_partition_multiple_keys():
    pos, neg, other = partition([-1, 0, 1, 2], lambda x: x > 0, lambda x: x < 0)
    assert pos == [1, 2]
    assert neg == [-1]
    assert other == [0]

def test_unique_basic():
    assert unique([1, 2, 1, 3, 2]) == [1, 2, 3]

def test_redundant_basic():
    result = redundant([1, 2, 1, 3, 2])
    assert set(result) == {1, 2}

def test_one_single_match():
    assert one([1, 2, 3], key=lambda x: x == 2) == 2

def test_same_not_equal():
    assert same([1, 2, 3]) is False

def test_flatten_nested():
    assert flatten([1, [2, [3, 4]], 5]) == [1, 2, 3, 4, 5]

def test_get_path_nested_dict():
    data = {'a': {'b': {'c': 42}}}
    assert get_path(data, ('a', 'b', 'c')) == 42

def test_guiderator_yields_strings():
    g = GUIDerator()
    val = next(g)
    assert isinstance(val, str)
    assert len(val) == 24

def test_sequential_guiderator_deterministic():
    g = SequentialGUIDerator()
    v1 = next(g)
    g.reseed()
    v2 = next(g)
    assert isinstance(v1, str)
    assert isinstance(v2, str)

def test_url_parse_error():
    with pytest.raises(URLParseError):
        URL('http://example.com:notaport/')

def test_query_param_dict_to_text():
    qp = QueryParamDict.from_text('a=1&b=2')
    text = qp.to_text()
    assert 'a=1' in text

def test_parse_url_basic():
    result = parse_url('http://example.com/path?q=1')
    assert result['scheme'] == 'http'
    assert result['host'] == 'example.com'

def test_quote_path_part_basic():
    result = quote_path_part('hello world')
    assert ' ' not in result

def test_unquote_basic():
    assert unquote('abc%20def') == 'abc def'

def test_parse_host_plain():
    import socket
    family, host = parse_host('example.com')
    assert family is None
    assert host == 'example.com'

def test_parse_qsl_basic():
    result = parse_qsl('a=1&b=2')
    assert ('a', '1') in result
    assert ('b', '2') in result

def test_resolve_path_parts_dot():
    result = resolve_path_parts(['', 'a', '.', 'b'])
    assert '.' not in result

def test_to_unicode_bytes():
    result = to_unicode(b'hello')
    assert isinstance(result, str)
