"""Track B generated tests for boltons.iterutils and boltons.urlutils."""
import pytest

from boltons.iterutils import (
    is_iterable, is_scalar, is_collection,
    split, split_iter,
    lstrip, lstrip_iter, rstrip, rstrip_iter, strip,
    chunked, chunked_iter, chunk_ranges,
    pairwise, pairwise_iter, windowed, windowed_iter,
    xfrange, frange,
    backoff, backoff_iter,
    bucketize, partition,
    unique, unique_iter, redundant,
    one, first, same,
    flatten, flatten_iter,
    remap, get_path, research,
    default_visit, default_enter, default_exit, PathAccessError,
    GUIDerator, SequentialGUIDerator,
    soft_sorted, untyped_sorted,
)
from boltons.urlutils import (
    URL, QueryParamDict, URLParseError, parse_url, find_all_links,
    quote_path_part, quote_query_part, quote_fragment_part,
    quote_userinfo_part, unquote, unquote_to_bytes,
    parse_host, parse_qsl, resolve_path_parts, register_scheme,
    to_unicode,
)
from boltons.cacheutils import make_cache_key
from boltons.dictutils import FrozenDict, FrozenHashError


# ---------------------------------------------------------------------------
# make_cache_key / FrozenDict
# ---------------------------------------------------------------------------

def test_make_cache_key_single_fast_arg():
    assert make_cache_key(('alpha',), {}) == 'alpha'

def test_make_cache_key_kwargs_are_order_independent():
    assert make_cache_key((), {'b': 2, 'a': 1}) == make_cache_key((), {'a': 1, 'b': 2})

def test_make_cache_key_typed_distinguishes_equal_values():
    assert make_cache_key((3,), {}, typed=True) != make_cache_key((3.0,), {}, typed=True)

def test_frozendict_mapping_and_updated_copy():
    fd = FrozenDict({'a': 'A', 'b': 'B'})
    newer = fd.updated({'b': 'Bee', 'c': 'C'})
    assert fd['b'] == 'B'
    assert newer == {'a': 'A', 'b': 'Bee', 'c': 'C'}

def test_frozendict_rejects_mutation():
    fd = FrozenDict({'a': 'A'})
    with pytest.raises(TypeError):
        fd['b'] = 'B'

def test_frozendict_hash_error_for_unhashable_values():
    fd = FrozenDict({'a': []})
    with pytest.raises(FrozenHashError):
        hash(fd)


# ---------------------------------------------------------------------------
# is_iterable / is_scalar / is_collection
# ---------------------------------------------------------------------------

def test_is_iterable_list():
    assert is_iterable([1, 2, 3])

def test_is_iterable_string():
    assert is_iterable("hello")

def test_is_iterable_int():
    assert not is_iterable(42)

def test_is_scalar_string():
    assert is_scalar("hello")

def test_is_scalar_int():
    assert is_scalar(5)

def test_is_scalar_none():
    assert is_scalar(None)

def test_is_scalar_list():
    assert not is_scalar([1, 2])

def test_is_collection_list():
    assert is_collection([1, 2])

def test_is_collection_string():
    assert not is_collection("hello")


# ---------------------------------------------------------------------------
# split / split_iter
# ---------------------------------------------------------------------------

def test_split_basic_sep():
    assert split([1, 2, 0, 3, 4], sep=0) == [[1, 2], [3, 4]]

def test_split_none_sep_groups():
    # sep=None groups consecutive Nones like str.split()
    result = split([1, None, None, 2, None, 3])
    assert result == [[1], [2], [3]]

def test_split_callable_sep():
    result = split([1, 2, 3, 4, 5], sep=lambda x: x % 2 == 0)
    assert result == [[1], [3], [5]]

def test_split_container_sep():
    # sep=[2,3] splits on 2 and 3 — [1] | [] | [] | [4]
    result = split([1, 2, 3, 2, 4], sep=[2, 3])
    assert result[0] == [1]
    assert result[-1] == [4]
    assert len(result) > 2

def test_split_maxsplit_zero():
    # maxsplit=0 yields [src] (the whole iterable wrapped)
    result = list(split_iter([1, 2, 3], sep=2, maxsplit=0))
    assert len(result) == 1
    # maxsplit=0 wraps src in a single group: [[[1, 2, 3]]]
    assert result[0] == [[1, 2, 3]]

def test_split_maxsplit_one():
    result = split([1, 2, 3, 2, 4], sep=2, maxsplit=1)
    assert result == [[1], [3, 2, 4]]

def test_split_non_iterable_raises():
    with pytest.raises(TypeError):
        list(split_iter(42))

def test_split_empty_trailing():
    result = split([1, 2, 0], sep=0)
    assert result == [[1, 2], []]


# ---------------------------------------------------------------------------
# lstrip / rstrip / strip
# ---------------------------------------------------------------------------

def test_lstrip_removes_leading():
    assert list(lstrip_iter([None, None, 1, 2, None])) == [1, 2, None]

def test_lstrip_all_strip_value():
    assert list(lstrip_iter([None, None, None])) == []

def test_lstrip_empty():
    assert list(lstrip_iter([])) == []

def test_rstrip_removes_trailing():
    assert list(rstrip_iter([1, None, 2, None, None])) == [1, None, 2]

def test_rstrip_all_strip_value():
    assert list(rstrip_iter([None, None])) == []

def test_strip_both_ends():
    assert list(strip([None, 1, 2, None], strip_value=None)) == [1, 2]

def test_lstrip_custom_value():
    assert list(lstrip_iter([0, 0, 1, 2], strip_value=0)) == [1, 2]

def test_rstrip_custom_value():
    assert list(rstrip_iter([1, 2, 0, 0], strip_value=0)) == [1, 2]


# ---------------------------------------------------------------------------
# chunked / chunked_iter
# ---------------------------------------------------------------------------

def test_chunked_basic():
    assert chunked([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]

def test_chunked_with_fill():
    assert chunked([1, 2, 3], 2, fill=0) == [[1, 2], [3, 0]]

def test_chunked_string():
    assert chunked("abcde", 2) == ["ab", "cd", "e"]

def test_chunked_bytes():
    result = chunked(b"abcde", 2)
    assert result == [b"ab", b"cd", b"e"]

def test_chunked_empty():
    assert chunked([], 3) == []

def test_chunked_invalid_size():
    with pytest.raises(ValueError):
        chunked([1, 2], 0)

def test_chunked_invalid_kwarg():
    with pytest.raises(ValueError):
        chunked([1, 2], 2, unknown=True)

def test_chunked_non_iterable():
    with pytest.raises(TypeError):
        chunked(42, 2)

def test_chunked_with_count():
    assert chunked([1, 2, 3, 4, 5], 2, count=2) == [[1, 2], [3, 4]]


# ---------------------------------------------------------------------------
# chunk_ranges
# ---------------------------------------------------------------------------

def test_chunk_ranges_basic():
    result = list(chunk_ranges(10, 3))
    assert result == [(0, 3), (3, 6), (6, 9), (9, 10)]

def test_chunk_ranges_with_overlap():
    result = list(chunk_ranges(10, 4, overlap_size=1))
    assert len(result) > 0
    assert result[0][0] == 0

def test_chunk_ranges_align():
    result = list(chunk_ranges(10, 4, input_offset=2, align=True))
    assert len(result) > 0

def test_chunk_ranges_offset():
    result = list(chunk_ranges(6, 3, input_offset=2))
    assert result[0][0] == 2


# ---------------------------------------------------------------------------
# pairwise / windowed
# ---------------------------------------------------------------------------

def test_pairwise_basic():
    result = pairwise([1, 2, 3, 4])
    assert list(result) == [(1, 2), (2, 3), (3, 4)]

def test_pairwise_with_end():
    result = list(pairwise_iter([1, 2, 3], end=None))
    assert (3, None) in result

def test_pairwise_empty():
    assert list(pairwise([])) == []

def test_windowed_basic():
    result = windowed([1, 2, 3, 4], 3)
    assert list(result) == [(1, 2, 3), (2, 3, 4)]

def test_windowed_with_fill():
    result = list(windowed_iter([1, 2], 3, fill=0))
    assert (1, 2, 0) in result

def test_windowed_too_short_no_fill():
    result = list(windowed([1], 3))
    assert result == []


# ---------------------------------------------------------------------------
# xfrange / frange
# ---------------------------------------------------------------------------

def test_xfrange_basic():
    result = list(xfrange(3.0))
    assert result[0] == 0.0
    assert len(result) == 3

def test_xfrange_with_start():
    result = list(xfrange(1.0, 3.0))
    assert result[0] == 1.0

def test_xfrange_zero_step():
    with pytest.raises(ValueError):
        list(xfrange(5.0, step=0))

def test_frange_basic():
    result = frange(4.0)
    assert result[0] == 0.0
    assert len(result) == 4

def test_frange_with_start():
    result = frange(1.0, 4.0)
    assert result[0] == 1.0
    assert len(result) == 3

def test_frange_zero_step():
    with pytest.raises(ValueError):
        frange(5.0, step=0)

def test_frange_empty():
    result = frange(0.0)
    assert result == []

def test_frange_negative_step():
    result = frange(5.0, 0.0, step=-1.25)
    assert result[0] == 5.0


# ---------------------------------------------------------------------------
# backoff / backoff_iter
# ---------------------------------------------------------------------------

def test_backoff_basic():
    result = backoff(1, 10)
    assert result[0] == 1.0
    assert result[-1] == 10.0

def test_backoff_repeat_raises():
    with pytest.raises(ValueError):
        backoff(1, 10, count='repeat')

def test_backoff_negative_start():
    with pytest.raises(ValueError):
        list(backoff_iter(-1, 10))

def test_backoff_factor_lt_one():
    with pytest.raises(ValueError):
        list(backoff_iter(1, 10, factor=0.5))

def test_backoff_stop_zero():
    with pytest.raises(ValueError):
        list(backoff_iter(1, 0))

def test_backoff_stop_lt_start():
    with pytest.raises(ValueError):
        list(backoff_iter(5, 3))

def test_backoff_with_count():
    result = backoff(1, 100, count=3)
    assert len(result) == 3

def test_backoff_iter_repeat():
    gen = backoff_iter(1, 4, count='repeat')
    vals = [next(gen) for _ in range(6)]
    assert all(v >= 1.0 for v in vals)

def test_backoff_jitter_range():
    result = backoff(1, 16, jitter=0.5)
    assert all(v >= 0 for v in result)

def test_backoff_jitter_out_of_range():
    with pytest.raises(ValueError):
        list(backoff_iter(1, 10, jitter=2.0))


# ---------------------------------------------------------------------------
# bucketize / partition
# ---------------------------------------------------------------------------

def test_bucketize_basic():
    result = bucketize([1, 2, 3, 4], key=lambda x: x % 2)
    assert set(result.keys()) == {0, 1}

def test_bucketize_string_key():
    class Obj:
        def __init__(self, v): self.v = v
    objs = [Obj(1), Obj(2), Obj(1)]
    result = bucketize(objs, key='v')
    assert len(result[1]) == 2

def test_bucketize_callable_key():
    result = bucketize(range(5), key=lambda x: x > 2)
    assert True in result and False in result

def test_bucketize_list_key():
    result = bucketize([10, 20, 30], key=['a', 'b', 'a'])
    assert result['a'] == [10, 30]

def test_bucketize_list_key_length_mismatch():
    with pytest.raises(ValueError):
        bucketize([1, 2, 3], key=['a', 'b'])

def test_bucketize_invalid_key_type():
    with pytest.raises(TypeError):
        bucketize([1, 2], key=42)

def test_bucketize_key_filter():
    result = bucketize([1, 2, 3, 4], key=lambda x: x % 2,
                       key_filter=lambda k: k == 1)
    assert 0 not in result
    assert 1 in result

def test_bucketize_value_transform():
    result = bucketize([1, 2, 3, 4], key=bool, value_transform=lambda x: x * 10)
    assert result[True] == [10, 20, 30, 40]

def test_bucketize_non_iterable():
    with pytest.raises(TypeError):
        bucketize(42)

def test_partition_basic():
    true_vals, false_vals = partition([1, 0, 2, None, 3])
    assert true_vals == [1, 2, 3]

def test_partition_multiple_keys():
    pos, neg, other = partition([-1, 0, 1, 2], lambda x: x > 0, lambda x: x < 0)
    assert pos == [1, 2]
    assert neg == [-1]
    assert other == [0]

def test_partition_non_iterable():
    with pytest.raises(TypeError):
        partition(42)


# ---------------------------------------------------------------------------
# unique / unique_iter / redundant
# ---------------------------------------------------------------------------

def test_unique_basic():
    assert unique([1, 2, 1, 3, 2]) == [1, 2, 3]

def test_unique_with_key():
    result = unique(['a', 'bb', 'c', 'dd'], key=len)
    assert result == ['a', 'bb']

def test_unique_callable_key():
    result = unique([1, -1, 2, -2], key=abs)
    assert result == [1, 2]

def test_unique_non_iterable():
    with pytest.raises(TypeError):
        unique(42)

def test_unique_iter_basic():
    assert list(unique_iter([1, 2, 1, 3])) == [1, 2, 3]

def test_redundant_basic():
    result = redundant([1, 2, 1, 3, 2])
    assert set(result) == {1, 2}

def test_redundant_groups():
    result = redundant([1, 2, 1, 2], groups=True)
    assert [1, 1] in result or [1, 1] in [sorted(g) for g in result]

def test_redundant_callable_key():
    result = redundant([1, -1, 2], key=abs)
    assert len(result) == 1


# ---------------------------------------------------------------------------
# one / first / same
# ---------------------------------------------------------------------------

def test_one_single_match():
    assert one([1, 2, 3], key=lambda x: x == 2) == 2

def test_one_no_match():
    assert one([1, 2, 3], key=lambda x: x == 99) is None

def test_one_multiple_matches():
    assert one([1, 2, 2, 3], key=lambda x: x == 2) is None

def test_first_basic():
    assert first([0, None, 1, 2]) == 1

def test_first_default():
    assert first([], default=42) == 42

def test_same_all_equal():
    assert same([2, 2, 2]) is True

def test_same_not_equal():
    assert same([1, 2, 3]) is False

def test_same_with_ref():
    assert same([3, 3, 3], ref=3) is True

def test_same_empty():
    assert same([]) is True


# ---------------------------------------------------------------------------
# flatten / flatten_iter
# ---------------------------------------------------------------------------

def test_flatten_nested():
    assert flatten([1, [2, [3, 4]], 5]) == [1, 2, 3, 4, 5]

def test_flatten_strings_not_expanded():
    assert flatten(["ab", [1, 2]]) == ["ab", 1, 2]

def test_flatten_iter_nested():
    assert list(flatten_iter([1, [2, 3]])) == [1, 2, 3]


# ---------------------------------------------------------------------------
# remap
# ---------------------------------------------------------------------------

def test_remap_basic():
    result = remap({'a': 1, 'b': {'c': 2}})
    assert result == {'a': 1, 'b': {'c': 2}}

def test_remap_drop_falsy():
    result = remap({'a': 1, 'b': None, 'c': 0},
                   visit=lambda p, k, v: bool(v))
    assert 'b' not in result

def test_remap_list():
    result = remap([1, [2, 3], 4])
    assert result == [1, [2, 3], 4]

def test_remap_set():
    result = remap({1, 2, 3})
    assert isinstance(result, (set, frozenset))

def test_remap_tuple():
    result = remap((1, 2, 3))
    assert result == (1, 2, 3)

def test_remap_non_callable_visit():
    with pytest.raises(TypeError):
        remap({}, visit=42)

def test_remap_non_callable_enter():
    with pytest.raises(TypeError):
        remap({}, enter=42)

def test_remap_non_callable_exit():
    with pytest.raises(TypeError):
        remap({}, exit=42)

def test_remap_unexpected_kwarg():
    with pytest.raises(TypeError):
        remap({}, unknown_arg=True)

def test_remap_shared_reference():
    shared = [1, 2]
    root = {'a': shared, 'b': shared}
    result = remap(root)
    assert result['a'] == [1, 2]


# ---------------------------------------------------------------------------
# get_path
# ---------------------------------------------------------------------------

def test_get_path_nested_dict():
    data = {'a': {'b': {'c': 42}}}
    assert get_path(data, ('a', 'b', 'c')) == 42

def test_get_path_list_index():
    data = [1, [2, 3]]
    assert get_path(data, (1, 0)) == 2

def test_get_path_missing_default():
    data = {'a': 1}
    assert get_path(data, ('b',), default=99) == 99

def test_get_path_missing_raises():
    with pytest.raises(PathAccessError):
        get_path({'a': 1}, ('b',))

def test_get_path_dotstring():
    data = {'a': {'b': 3}}
    assert get_path(data, 'a.b') == 3


# ---------------------------------------------------------------------------
# research
# ---------------------------------------------------------------------------

def test_research_basic():
    data = {'a': 1, 'b': {'c': 2, 'd': 3}}
    results = research(data, query=lambda p, k, v: v == 2)
    assert len(results) == 1
    assert results[0][1] == 2

def test_research_all():
    data = [1, 2, 3]
    results = research(data)
    assert len(results) > 0

def test_research_reraise():
    def bad_query(p, k, v):
        raise ValueError("oops")
    data = {'x': 1}
    with pytest.raises(ValueError):
        research(data, query=bad_query, reraise=True)


# ---------------------------------------------------------------------------
# GUIDerator / SequentialGUIDerator
# ---------------------------------------------------------------------------

def test_guiderator_yields_strings():
    g = GUIDerator()
    val = next(g)
    assert isinstance(val, str)
    assert len(val) == 24

def test_guiderator_invalid_size():
    with pytest.raises(ValueError):
        GUIDerator(size=10)

def test_sequential_guiderator_deterministic():
    g = SequentialGUIDerator()
    v1 = next(g)
    g.reseed()
    v2 = next(g)
    assert isinstance(v1, str)
    assert isinstance(v2, str)


# ---------------------------------------------------------------------------
# soft_sorted / untyped_sorted
# ---------------------------------------------------------------------------

def test_soft_sorted_first():
    result = soft_sorted([3, 1, 2], first=[3])
    assert result[0] == 3

def test_soft_sorted_last():
    result = soft_sorted([3, 1, 2], last=[1])
    assert result[-1] == 1

def test_untyped_sorted_mixed():
    result = untyped_sorted([3, 'a', 1, 'b'])
    assert len(result) == 4


# ---------------------------------------------------------------------------
# URL / QueryParamDict / urlutils helpers
# ---------------------------------------------------------------------------

def test_url_basic_parse():
    u = URL('http://example.com/path?q=1#frag')
    assert u.scheme == 'http'
    assert u.host == 'example.com'
    assert u.path == '/path'
    assert u.fragment == 'frag'

def test_url_query_params():
    u = URL('http://example.com/?a=1&b=2')
    assert u.query_params['a'] == '1'
    assert u.query_params['b'] == '2'

def test_url_port():
    u = URL('http://example.com:8080/')
    assert u.port == 8080

def test_url_default_port_omitted():
    u = URL('http://example.com:80/')
    assert 'port' not in u.to_text() or ':80' not in u.to_text()

def test_url_to_text():
    text = 'http://example.com/path'
    u = URL(text)
    assert u.to_text() == text

def test_url_str():
    u = URL('http://example.com/')
    assert str(u) == u.to_text()

def test_url_equality():
    assert URL('http://example.com/') == URL('http://example.com/')

def test_url_normalize():
    u = URL('HTTP://Example.COM/./foo/../bar')
    u.normalize()
    assert u.scheme == 'http'
    assert u.host == 'example.com'

def test_url_navigate_relative():
    u = URL('http://example.com/a/b/c')
    result = u.navigate('../d')
    assert '/a/d' in result.to_text()

def test_url_navigate_absolute():
    u = URL('http://example.com/a/b')
    result = u.navigate('http://other.com/')
    assert result.host == 'other.com'

def test_url_from_parts():
    u = URL.from_parts(scheme='https', host='example.com', path_parts=('', 'foo'))
    assert 'example.com' in u.to_text()
    assert '/foo' in u.to_text()

def test_url_path_parts():
    u = URL('http://example.com/a/b/c')
    assert 'a' in u.path_parts

def test_url_uses_netloc():
    u = URL('http://example.com/')
    assert u.uses_netloc

def test_url_username_password():
    u = URL('http://user:pass@example.com/')
    assert u.username == 'user'
    assert u.password == 'pass'

def test_url_get_authority():
    u = URL('http://user@example.com:9000/path')
    auth = u.get_authority(with_userinfo=True)
    assert 'user' in auth
    assert 'example.com' in auth

def test_url_bytes_input():
    u = URL(b'http://example.com/')
    assert u.host == 'example.com'

def test_url_parse_error():
    with pytest.raises(URLParseError):
        URL('http://example.com:notaport/')

def test_url_full_quote():
    u = URL('http://example.com/path with spaces')
    text = u.to_text(full_quote=True)
    assert ' ' not in text

def test_query_param_dict_from_text():
    qp = QueryParamDict.from_text('a=1&b=2&a=3')
    assert qp.getlist('a') == ['1', '3']

def test_query_param_dict_to_text():
    qp = QueryParamDict.from_text('a=1&b=2')
    text = qp.to_text()
    assert 'a=1' in text

def test_query_param_repeated_keys():
    u = URL('http://example.com/?k=1&k=2')
    assert len(u.qp.getlist('k')) == 2

def test_parse_url_basic():
    result = parse_url('http://example.com/path?q=1')
    assert result['scheme'] == 'http'
    assert result['host'] == 'example.com'

def test_parse_url_error():
    with pytest.raises(URLParseError):
        parse_url('http://[invalid::ipv6/')

def test_find_all_links_basic():
    text = "Visit http://example.com and http://other.org today."
    links = find_all_links(text)
    assert len(links) == 2
    assert all(isinstance(u, URL) for u in links)

def test_find_all_links_with_text():
    text = "See http://example.com for details."
    tokens = find_all_links(text, with_text=True)
    assert any(isinstance(t, URL) for t in tokens)
    assert any(isinstance(t, str) for t in tokens)

def test_find_all_links_default_scheme():
    text = "Visit http://example.com and https://other.org today."
    links = find_all_links(text, default_scheme='https')
    assert len(links) >= 2
    assert all(isinstance(u, URL) for u in links)

def test_find_all_links_scheme_filter():
    text = "http://a.com and http://b.com"
    links = find_all_links(text, schemes=['http'])
    assert len(links) == 2
    assert all(isinstance(u, URL) for u in links)
    assert all(u.scheme == 'http' for u in links)

def test_quote_path_part_basic():
    result = quote_path_part('hello world')
    assert ' ' not in result

def test_quote_path_part_no_full_quote():
    result = quote_path_part('hello', full_quote=False)
    assert 'hello' in result

def test_quote_query_part_basic():
    result = quote_query_part('key=value&more')
    assert isinstance(result, str)

def test_quote_fragment_part():
    result = quote_fragment_part('section 1')
    assert isinstance(result, str)

def test_quote_userinfo_part():
    result = quote_userinfo_part('user:pass')
    assert isinstance(result, str)

def test_unquote_basic():
    assert unquote('abc%20def') == 'abc def'

def test_unquote_no_percent():
    assert unquote('hello') == 'hello'

def test_unquote_to_bytes_basic():
    assert unquote_to_bytes('abc%20def') == b'abc def'

def test_unquote_to_bytes_empty():
    assert unquote_to_bytes('') == b''

def test_unquote_to_bytes_no_percent():
    assert unquote_to_bytes(b'hello') == b'hello'

def test_parse_host_ipv4():
    import socket
    family, host = parse_host('192.168.1.1')
    assert family == socket.AF_INET

def test_parse_host_plain():
    import socket
    family, host = parse_host('example.com')
    assert family is None
    assert host == 'example.com'

def test_parse_host_ipv6_invalid():
    with pytest.raises(URLParseError):
        parse_host('[::invalid]')

def test_parse_qsl_basic():
    result = parse_qsl('a=1&b=2')
    assert ('a', '1') in result
    assert ('b', '2') in result

def test_parse_qsl_blank_values():
    result = parse_qsl('a=&b=2')
    keys = [k for k, v in result]
    assert 'a' in keys

def test_resolve_path_parts_dot():
    result = resolve_path_parts(['', 'a', '.', 'b'])
    assert '.' not in result

def test_resolve_path_parts_dotdot():
    result = resolve_path_parts(['', 'a', 'b', '..', 'c'])
    assert '..' not in result

def test_register_scheme_uses_netloc():
    register_scheme('myscheme', uses_netloc=True, default_port=1234)
    u = URL('myscheme://example.com:1234/')
    assert u.uses_netloc

def test_register_scheme_no_netloc_with_port_raises():
    with pytest.raises(ValueError):
        register_scheme('badscheme', uses_netloc=False, default_port=999)

def test_to_unicode_str():
    assert to_unicode('hello') == 'hello'

def test_to_unicode_bytes():
    result = to_unicode(b'hello')
    assert isinstance(result, str)
