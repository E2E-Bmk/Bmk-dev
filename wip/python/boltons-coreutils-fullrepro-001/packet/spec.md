# Boltons Core Utilities Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Boltons is a collection of focused Python utilities that extend the standard library without introducing a shared framework. This contract covers caching, ordered multi-value mappings, iterable transformation, and URL manipulation.

## Non-Goals

- This specification does not require Modules outside the four selected functional domains (caching, ordered mappings, iterable transformation, URL manipulation)unless needed for a documented behavior.
- This specification does not require Private linked-list internals, regular-expression implementation objects, or test helper shapes.
- This specification does not require Exact wording of exception messagesunless this specification gives exact text.
- This specification does not require Micro-optimization or thread scheduling details; performance should be reasonable for ordinary inputs.

## Representative Workflows

### LRU cache with eviction

```python
from boltons.cacheutils import LRU

cache = LRU(max_size=3)
cache["a"] = 1
cache["b"] = 2
cache["c"] = 3
# Access "a" to make it most recently used
_ = cache["a"]
# Insert a new key; "b" is least recently used and should be evicted
cache["d"] = 4
assert "b" not in cache
assert cache["a"] == 1
assert cache["d"] == 4
```

Creating an `LRU` with `max_size=3`, inserting three keys, then accessing `"a"` updates its recency. Inserting `"d"` evicts the least-recently-used key `"b"`, while `"a"` and `"c"` remain.

### OrderedMultiDict manipulation

```python
from boltons.dictutils import OrderedMultiDict

omd = OrderedMultiDict([("x", 1), ("y", 2), ("x", 3)])
assert omd["x"] == 3  # most recent value for "x"
assert omd.getlist("x") == [1, 3]

omd.add("y", 99)
assert omd.getlist("y") == [2, 99]

inv = omd.inverted()
copy = omd.copy()
assert copy.items(multi=True) == omd.items(multi=True)
```

Building an `OrderedMultiDict` from repeated pairs preserves insertion order. `getlist` returns all values, `add` appends without replacing, `inverted` maps values back to keys, and `copy` produces an independent snapshot.

### URL parsing, navigation, and normalization

```python
from boltons.urlutils import URL

u = URL("https://example.com:443/path?q=1#frag")
assert u.scheme == "https"
assert u.query_params["q"] == "1"

u.query_params["lang"] = "en"
u2 = u.navigate("../other?x=2")
u2.normalize()
assert u2.host == "example.com"
assert "other" in u2.to_text()
```

Parsing text into `URL` exposes components and an editable `query_params`. Navigating to a relative destination resolves `..` segments per RFC 3986. After `normalize()`, default ports are removed and dot-segments resolved, and `to_text()` serializes the final state.

## General Conventions

- Preserve input order where a type is documented as ordered.
- Mapping-like classes should interoperate with normal `dict` operations where
  documented: construction from mappings or iterable pairs, `len()`, truth
  testing, membership, iteration over keys, item lookup, assignment, deletion,
  `get()`, `items()`, `keys()`, `values()`, `update()`, `clear()`, equality,
  copying, pickling where natural, and representation.
- Python 3 text APIs should accept native `str`. URL APIs should also accept
  `bytes` where documented and decode them as UTF-8 unless otherwise specified.
- Exception types should be stable enough for callers to catch by class.
- Exact exception message wording is not part of the contract unless this spec
  gives exact text.

## Cache Behavior

Caching utilities provide dictionary-like containers with eviction policies, function result caching, and lazy property evaluation.

### `LRI`

`LRI` is a mutable dictionary-like cache with least-recently-inserted eviction. It accepts `max_size`, initial `values`, and an optional `on_miss` callable.

Behavior:

- `max_size` must be greater than zero; invalid sizes raise `ValueError`.
- `on_miss`, when supplied, must be callable; otherwise raise `TypeError`.
- Constructing from `values` inserts initial items in input order.
- Setting a new key when the cache is full evicts the oldest key by insertion
  order.
- Reassigning an existing key updates its value and makes that key newly
  inserted for eviction purposes.
- `__getitem__(key)` returns the cached value. On a miss, if `on_miss` is
  callable, call it with the key, store the returned value, and return it.
  Without `on_miss`, misses raise `KeyError`.
- `get(key, default=None)` returns the cached value when present. For missing
  keys with `on_miss`, it calls `on_miss(key)`, stores the result, and returns
  it. For missing keys without `on_miss`, it records a soft miss and returns
  `default`.
- `pop(key[, default])`, `popitem()`, `clear()`, `copy()`, `setdefault()`, and
  `update()` behave like dictionary operations while preserving cache capacity
  and eviction semantics.
- Iterating, `keys()`, `values()`, and `items()` expose current entries in
  cache order. Equality with another mapping compares flattened key/value
  pairs.
- Cache instances expose hit/miss/soft-miss statistics where public attributes
  are present; cache hits and misses should update those counters consistently.

### `LRU`

`LRU` is an `LRI`-compatible mutable cache with least-recently-used eviction, accepting the same `max_size`, `values`, and `on_miss` parameters.

Behavior:

- Setting a key makes it most recently used.
- Successful `__getitem__` access makes that key most recently used.
- When a new key is inserted over capacity, evict the least recently used key.
- Dictionary-like operations and `on_miss` behavior match `LRI`.
- Replacing an existing key updates both the stored value and recency without
  creating duplicate observable entries.
- `get()` follows `LRI.get()` miss behavior: missing keys with `on_miss` are
  generated and stored; missing keys without `on_miss` return the default.

### Cache Key Construction

`make_cache_key` returns a hashable key representing positional arguments and keyword arguments.

Behavior:

- Positional values appear first.
- Keyword arguments are included in deterministic key order after a marker.
- When `typed=True`, include argument value types so calls like `1` and `1.0`
  do not collide.
- Single fast hashable arguments may be returned directly when safe.

### `cached`

`cached` is a decorator for functions that stores return values in a provided cache.

Behavior:

- The decorated function stores return values in `cache`.
- `cache` may be a mutable mapping instance or a zero-argument callable returning
  a mapping. Invalid cache providers raise `TypeError`.
- If `key` is supplied, call it as a cache-key builder with
  `(args, kwargs, typed=typed)` and use its return value as the cache key.
- Otherwise build a key from call arguments using `make_cache_key`.
- `scoped` is stored on the wrapper and reflected in representation; function
  calls build cache keys from `(args, kwargs, typed=typed)` through the key
  builder.
- With `typed=True`, include argument types in the generated key.
- Cache hits return the stored value without calling the wrapped function.
- The wrapper should preserve ordinary descriptor/call behavior and have a
  useful `repr`.

### `cachedmethod`

`cachedmethod` decorates instance methods, accepting `cache`, `scoped`, `typed`, and `key` parameters.

Behavior:

- `cache` may be a mapping, a callable accepting the instance and returning a
  mapping, or the name of an instance attribute containing the mapping. Invalid
  cache providers raise `TypeError`.
- Cache keys are built from method arguments excluding `self`, plus optional
  scope/type information as in `cached`. A custom `key` callable is called as a
  cache-key builder with `(args, kwargs, typed=typed)`, not as the original
  method.
- Cache hits do not call the original method.
- Binding through an instance should return a callable that uses that instance's
  cache.
- `scoped` is stored on the wrapper and reflected in representation; method
  calls build cache keys from bound-call arguments through the key builder.

### `cachedproperty`

`cachedproperty` is a non-data descriptor for expensive attributes.

Behavior:

- On first instance access, call `func(instance)`, store the result directly on
  the instance under the property name, and return it.
- Later access returns the stored value without calling `func`.
- Access on the class returns the descriptor object.
- Deleting the stored instance attribute or editing `__dict__` clears the cache.

### `ThresholdCounter`

`ThresholdCounter` counts items while separating common and uncommon counts using a frequency `threshold`.

Behavior:

- `threshold` must be between `0` and `1`; invalid values raise `ValueError`.
- `add(key)` increments the count for `key`.
- `update(iterable, **kwargs)` adds each element from an iterable, mapping, or
  keyword counts.
- `threshold` is exposed as a read-only numeric property.
- The structure compacts periodically. A key missing from the common mapping is
  known to be below the threshold ratio, not necessarily absent from all input.
- `__getitem__(key)` returns the count for common keys and raises `KeyError` for
  absent or below-threshold keys.
- `get(key, default=0)`, `__contains__`, `__len__`, `keys()`, `values()`,
  `items()`, `iterkeys()`, `itervalues()`, and `iteritems()` expose common
  counted keys.
- `elements()` yields counted elements repeated by count for common keys.
- `most_common(n=None)` returns `(key, count)` pairs ordered by descending count.
- `get_common_count()` returns the total count represented by common keys.
- `get_uncommon_count()` returns the count represented by keys below threshold.
- `get_commonality()` returns the fraction of all observations represented by
  common keys.

### `MinIDMap`

`MinIDMap` maps live Python objects to compact integer identifiers.

Behavior:

- `get(obj)` returns a stable integer id for the object while it remains alive.
- Repeated calls for the same live object return the same id.
- `drop(obj)` removes an object mapping when present.
- `obj in map`, `len(map)`, iteration, and `iteritems()` expose live mappings.
- Object ids may be reused after objects are dropped or garbage-collected.
- Objects should be weak-referenceable where weak references are required.

## Ordered Mapping Behavior

Ordered mapping utilities provide multi-value dictionaries, bijective mappings, immutable dictionaries, and subset extraction.

### `OrderedMultiDict`, `OMD`, and `MultiDict`

`OrderedMultiDict` is an ordered mapping from keys to one or more values.
`OMD` and `MultiDict` are public aliases for `OrderedMultiDict`.

Construction accepts a mapping, another ordered multi-dict, or an iterable of
`(key, value)` pairs. Duplicate keys are preserved internally in insertion
order.

Lookup and views:

- `omd[key]` returns the most recent value for `key`.
- `get(key, default=None)` returns the most recent value or `default` and never
  raises `KeyError`.
- `getlist(key, default=None)` returns all values for `key` in insertion order.
  If the key is missing and no default is supplied, return an empty list.
- `len(omd)` counts unique keys, not total pairs.
- Iteration yields unique keys in first-insertion order.
- `items(multi=False)`, `keys(multi=False)`, and `values(multi=False)` return
  lists. With `multi=False`, include each key once with its most recent value.
  With `multi=True`, include every stored pair in insertion order.
- `iteritems()`, `iterkeys()`, and `itervalues()` are iterator counterparts.
- `todict(multi=False)` returns a plain dict. With `multi=True`, values are
  lists of all stored values.

Mutation:

- `add(key, value)` appends a new value for the key without removing previous
  values.
- `addlist(key, values)` appends all values from an iterable for the key.
- `omd[key] = value` replaces all existing values for that key with one value.
- `setdefault(key, default=None)` returns the current value if present; otherwise
  stores and returns `default`.
- `update(other, **kwargs)` replaces each updated key with the incoming most
  recent value.
- `update_extend(other, **kwargs)` appends incoming values, preserving existing
  values.
- `pop(key[, default])` removes the key and returns its most recent value.
- `popall(key[, default])` removes the key and returns all values.
- `poplast(key=_MISSING[, default])` removes and returns the last inserted value
  globally, or the last value for the supplied key. Missing keys without a
  default raise `KeyError`.
- `clear()` removes all pairs.

Other behavior:

- Equality with another `OrderedMultiDict` compares ordered multi-pairs.
- Equality with a normal mapping compares flattened most-recent values.
- `copy()` returns an independent ordered multi-dict preserving all pairs.
- Pickle round trips must preserve repeated values and order.
- `sorted(key=None, reverse=False)` returns a new ordered multi-dict sorted by
  item pairs.
- `sortedvalues(key=None, reverse=False)` sorts values within each key.
- `inverted()` returns an ordered multi-dict mapping values back to keys.
- `counts()` returns counts per key.
- `viewkeys()`, `viewvalues()`, and `viewitems()` provide set-like views where
  feasible on Python 3.

### `FastIterOrderedMultiDict`

`FastIterOrderedMultiDict` behaves like `OrderedMultiDict` but optimizes
iteration. Observable mapping and multi-value behavior should match
`OrderedMultiDict`.

### `OneToOne`

`OneToOne` is a dict-like one-to-one mapping that maintains an inverse mapping
available as `.inv`.

Behavior:

- Values are unique. Assigning `mapping[key] = value` removes any previous key
  that mapped to `value`, and removes any previous inverse entry for `key`.
- Assigning through `.inv[value] = key` updates the forward mapping with the
  same one-to-one invariant.
- Deleting or popping a key updates `.inv`.
- `unique()` constructs a one-to-one mapping and raises `ValueError` if the
  provided initial data maps two keys to the same value.
- `copy()`, `clear()`, `pop()`, `popitem()`, `setdefault()`, and `update()`
  keep the forward and inverse mappings consistent.

### `ManyToMany`

`ManyToMany(items=None)` stores a bidirectional mapping between keys and sets of
values. The inverse relation is available as `.inv`.

Behavior:

- Construction accepts `(key, value)` pairs.
- `add(key, value)` links one key/value pair.
- `mapping[key]` returns a `frozenset` of values linked to `key`.
- `mapping[key] = values` replaces all values for that key.
- `get(key, default=frozenset())` returns linked values or the default.
- `remove(key, value)` removes one link and deletes empty key/value buckets.
- `replace(key, newkey)` moves all values from one key to another key.
- `del mapping[key]` removes all links for that key.
- Iteration and `keys()` expose keys. `iteritems()` yields stored `(key, value)`
  links.
- Equality compares the visible bidirectional link relation.

### `FrozenDict` and `FrozenHashError`

`FrozenDict` is an immutable dict subclass.

Behavior:

- Construction and lookup match `dict`.
- Mutation methods such as assignment, deletion, `clear()`, `pop()`,
  `popitem()`, `setdefault()`, and `update()` raise `TypeError`.
- `updated(*args, **kwargs)` returns a new `FrozenDict` with updates applied.
- `fromkeys(keys, value=None)` returns a `FrozenDict`.
- Hashing succeeds if all contained keys and values are hashable; otherwise
  raise `FrozenHashError`.

### `subdict`

`subdict(d, keep=None, drop=None)` returns a new mapping of `type(d)` containing
selected items from `d`.

Behavior:

- If `keep` is supplied, include only those keys that are present in `d`.
- If `drop` is supplied, exclude those keys.
- If both are supplied, apply `keep` first, then `drop`.
- The original mapping is not mutated.

## Iterable Transformation Behavior

Iterable utilities provide type checks, splitting, chunking, windowing, numeric sequences, grouping, deduplication, flattening, nested traversal, and identifier generation.

### Type Checks

- `is_iterable(obj)` is true for objects that can be iterated.
- `is_scalar(obj)` is true for common scalar values such as strings, bytes,
  numbers, booleans, and `None`, and false for normal containers.
- `is_collection(obj)` is true for non-scalar iterable collections.

### Splitting and Stripping

`split` returns a list of lists split from `src`.
`split_iter` is the generator form.

Behavior:

- `src` must be iterable; non-iterables raise `TypeError`.
- With `sep=None`, split on elements equal to `None`, grouping contiguous
  `None` separators like `str.split()`.
- With a single separator value, split when an element equals it.
- With a container of separators, split when an element is a member.
- With a callable separator, split when `sep(element)` is true.
- `maxsplit` limits the number of splits.

`lstrip`, `rstrip`, and `strip` remove leading, trailing, or both leading and
trailing elements equal to `strip_value`. With `strip_value=None`, they remove
elements equal to `None`, not all falsey elements. Their `_iter` counterparts
yield lazily.

### Chunking and Windows

- `chunked` returns a list of chunks from `src`.
- `chunked_iter` yields chunks lazily.
- `src` must be iterable; non-iterables raise `TypeError`.
- Chunks preserve the input container style where documented: strings become
  strings, bytes become bytes, and other iterables become lists.
- `size` must be a positive integer; invalid values raise `ValueError`.
- `count` limits the number of chunks.
- If `fill` is supplied as a keyword argument, incomplete final chunks are
  padded with that value. Without `fill`, the final chunk may be shorter.
- Unknown keyword arguments raise `ValueError`.
- `chunk_ranges` yields `(start, stop)` integer ranges covering the input. With
  overlap, adjacent ranges overlap by `overlap_size`. With `align=True`, ranges
  align to chunk-size boundaries relative to zero while still covering the
  requested offset and size.
- `pairwise` returns adjacent pairs as a list.
- `pairwise_iter` yields adjacent pairs. If `end` is supplied,
  include the final `(last, end)` pair.
- `windowed` returns a list of overlapping tuples.
- `windowed_iter` yields overlapping tuples. If `fill`
  is supplied, emit trailing windows padded with that fill value.

### Numeric Sequences and Backoff

- `xfrange` yields floats from `start` up to but not including `stop`; when `start` is omitted, it must start at `0.0`. A zero `step` must raise `ValueError`.
- `frange` returns a list from `xfrange`.
- `backoff` returns a list of increasing retry delays. It must not accept `count="repeat"`; that value must raise `ValueError`.
- `backoff_iter` is the generator form and supports `count="repeat"`.
- Backoff begins at `start`, grows by `factor`, never exceeds `stop`, and honors
  positive `count` when supplied.
- `start`, `stop`, `factor`, `count`, and numeric `jitter` are validated:
  starts and stops are non-negative, `stop >= start`, `factor >= 1.0`, count is
  positive or `"repeat"` where supported, and numeric jitter is between `-1`
  and `1`.
- `jitter=False` is deterministic. Numeric jitter offsets values by a bounded
  amount. `jitter=True` applies random jitter while preserving list length and
  non-negative delay values.

### Grouping, Uniqueness, and Reduction

- `bucketize` returns a dict mapping derived keys to lists of transformed values. `key` may be a
  callable, attribute name string, or a list of keys aligned with `src`.
  `value_transform` may be callable, attribute name, or item index.
  `key_filter` may reject buckets.
- `partition` divides input into buckets for false/true or the provided predicates. With multiple predicates, each item is placed in the
  first matching bucket, and a final bucket receives items that match none.
- `unique` returns a list of first occurrences.
- `unique_iter` yields first occurrences lazily.
- `redundant` returns first duplicate elements, or duplicate groups when `groups` is `True`.
- `one` returns the only matching element, or `default` if there are zero or multiple matches.
- `first` returns the first truthy/matching element, or `default`.
- `same` reports whether all values are equal to each other or to `ref`.
- `soft_sorted` sorts while forcing selected values to the front or back.
- `untyped_sorted` sorts heterogeneous values deterministically without requiring cross-type comparisons. Explicitly
  unorderable objects may still raise `TypeError`.

### Flattening and Nested Traversal

- `flatten_iter(iterable)` recursively yields scalar leaves from nested
  iterable containers.
- `flatten(iterable)` returns a list from `flatten_iter()`.

`remap` walks nested data structures and builds a remapped copy.

Traversal behavior:

- The walk visits mappings, lists, tuples, sets, and other supported iterable
  containers.
- `visit(path, key, value)` controls item inclusion and transformation. It may
  return `True` to keep an item unchanged, `False` or `None` to drop it, or a
  `(new_key, new_value)` pair to transform it.
- `enter(path, key, value)` controls whether and how to descend into a value. It
  returns `(new_parent, items)` or `False` to treat the value as a leaf.
- `exit(path, key, old_parent, new_parent, new_items)` finalizes a remapped
  container.
- `path` is a tuple of keys/indexes leading to the current parent.
- Shared references and self-referential structures are tracked by identity when
  caching is enabled, preserving repeated references in the remapped output
  rather than recursing forever.
- Non-callable `visit`, `enter`, or `exit` arguments raise `TypeError`.
- `reraise_visit` controls whether exceptions raised by `visit` are propagated
  or suppressed, and `trace` may request traversal event tracing. Unexpected
  keyword arguments beyond documented options raise `TypeError`.
- `default_visit`, `default_enter`, and `default_exit` are public helpers with
  the default behavior described above.

`get_path` indexes through nested mappings and sequences.

Behavior:

- `path` may be a tuple/list of segments or a dot-separated string.
- Path segments are applied through item access (`__getitem__`) on each current
  object. Integer segments naturally index sequences, and string segments
  naturally access mapping keys; attribute lookup is not part of `get_path()`.
- If a segment cannot be accessed and no default was supplied, raise
  `PathAccessError`, a subclass of `KeyError`, `IndexError`, and `TypeError`.
- If a default was supplied, return it instead of raising.

`research` walks a nested structure and returns a list of `(path, value)` matches where the `query` callable returns true for `(path, key, value)`. `query` must be callable. Query errors are
suppressed unless `reraise=True`.

### GUID Generators

- `GUIDerator` is an iterator yielding random URL-safe text ids of the
  requested `size`. The `size` must satisfy `20 < size <= 36`; invalid sizes must raise
  `ValueError`. `reseed` resets its random source.
- `SequentialGUIDerator` yields deterministic sequential ids of the
  requested length and supports `reseed`.

## URL Behavior

URL utilities provide parsing, normalization, navigation, query parameter management, and link extraction for web addresses.

### Public Constants and Exceptions

- `URLParseError` is a `ValueError` subclass raised for malformed URLs, hosts,
  or ports.
- `SCHEME_PORT_MAP` maps scheme names to default ports or `None`.
- `NO_NETLOC_SCHEMES` contains schemes that normally do not use network
  locations, such as `mailto` and `urn`.

### Text Conversion and Quoting

- `to_unicode(obj)` converts `str` and `bytes` URL input to text.
- `quote_path_part(text, full_quote=True)`, `quote_query_part`,
  `quote_fragment_part`, and `quote_userinfo_part` percent-encode one URL
  component using that component's safe-character rules.
- With `full_quote=True`, non-ASCII and reserved characters are percent-encoded
  where required for that component.
- With `full_quote=False`, readable Unicode may be preserved where the URL
  component allows it.
- `unquote(string, encoding="utf-8", errors="replace")` decodes percent escapes
  to text.
- `unquote_to_bytes(string)` decodes percent escapes to bytes.

### Parsing Helpers

- `parse_host(host)` parses host text and returns `(family, host_text)`, where
  `family` is `socket.AF_INET`, `socket.AF_INET6`, or `None`. Invalid IPv6
  syntax raises `URLParseError`.
- `parse_url(url_text)` returns a dict-like decomposition containing `scheme`,
  `_netloc_sep`, `authority`, `username`, `password`, `family`, `host`, `port`,
  `path`, `query`, and `fragment`. Non-integer ports and unparseable URL text
  raise `URLParseError`.
- `parse_qsl(qs, keep_blank_values=True, encoding="utf-8")` parses a query
  string into ordered `(key, value)` text pairs. Values may contain `=`.
- `resolve_path_parts(path_parts)` resolves `.` and `..` path segments while
  preserving leading/trailing slash semantics.
- `register_scheme(text, uses_netloc=None, default_port=None)` registers or
  updates scheme metadata used by `URL.uses_netloc`, `URL.default_port`, and
  `URL.to_text()`. `default_port` must be an integer or `None`; `uses_netloc`
  must be `True`, `False`, or `None`; incompatible combinations raise
  `ValueError`.

### `QueryParamDict`

`QueryParamDict` is an ordered multi-dict for URL query parameters. It behaves
like `OrderedMultiDict` for repeated keys and exposes:

- `QueryParamDict.from_text(query_string)` to parse query text into a query
  multi-dict.
- `to_text(full_quote=False)` to serialize parameters in order, quoting names
  and values as query components.

Blank values, repeated keys, Unicode values, and values containing `=` must
round-trip through parse and serialization.

### `URL`

`URL` parses a URL string, UTF-8 bytes value, or another `URL`.

Public attributes:

- `scheme`: scheme text when present; preserve parsed case until
  `normalize(with_case=True)` is applied.
- `username` and `password`: decoded userinfo strings; absent fields are empty
  strings after normal parsing.
- `host`: decoded host string, including Unicode for IDNA names when
  `full_quote=False` is used for output.
- `port`: integer port or `None`.
- `path`: textual path beginning with `/` when present.
- `path_parts`: tuple of slash-separated path segments. Leading and trailing
  slashes are represented by empty segments.
- `query_params` and alias `qp`: `QueryParamDict`.
- `fragment`: decoded fragment text or empty string.
- `uses_netloc`: whether the scheme uses `//authority`.
- `default_port`: the registered default port for the scheme, if any.

Construction and serialization:

- `URL.from_parts` builds a URL from structured parts including `scheme`, `host`, `path_parts`, `query_params`, `fragment`, `port`, `username`, and `password`.
- `to_text(full_quote=False)` serializes the URL. With `full_quote=True`, output
  is network-safe ASCII: IDNA hostnames are encoded and path/query/fragment
  Unicode is percent-encoded. With `full_quote=False`, human-readable Unicode is
  preserved where valid.
- Default ports are omitted from serialized output.
- Empty paths, leading/trailing slashes, query strings, fragments, `mailto`-like
  no-netloc schemes, and custom registered schemes are preserved according to
  URL rules.
- `__str__` should return text equivalent to `to_text()`.
- `__repr__` should identify the URL value.
- Equality compares the current parsed URL components (`scheme`, host, port,
  path parts, query params, fragment, and userinfo), not object identity and not
  a freshly normalized serialization.

Normalization and navigation:

- `normalize` mutates the URL in place and returns `None`.
  Normalization removes default ports, resolves path dot segments,
  canonicalizes quoting, and normalizes scheme/host case when `with_case=True`.
- `navigate` resolves a relative or absolute destination against the URL,
  following RFC 3986 relative-reference behavior for `.` and `..`, absolute
  paths, query-only changes, fragment-only changes, scheme changes, and full
  absolute destinations. `dest` may be text or `URL`.
- `get_authority` returns the authority
  string `[userinfo@]host[:port]`, respecting IDNA/quoting and default-port
  elision.

### Link Extraction

`find_all_links` extracts URL-like links from arbitrary text.

Behavior:

- Recognize common web links with schemes and bare domains.
- IPv6 addresses and netloc-less schemes such as `mailto` are outside the link
  extraction matcher's supported surface.
- Trim surrounding punctuation such as brackets, angle brackets, trailing
  commas, and sentence-final periods while preserving valid URL punctuation.
- Use `default_scheme` for bare links without a scheme.
- Restrict to the provided `schemes` when supplied.
- With `with_text=False`, return a list of `URL` objects.
- With `with_text=True`, return a token list that preserves non-link text
  segments and replaces link segments with `URL` objects.

## State Model

Each stateful utility exposes one logical value through more than one public view. Cache mapping operations and cached callables must observe the same cached entries. Ordered multi-value mappings must preserve the same key/value associations through single-value lookup, multi-value lookup, iteration, copying, and inversion. URL attributes, query parameters, serialization, normalization, and navigation must describe the same URL state. Iterable helpers are stateless transformations whose output order must follow their input traversal order.

## Error Semantics

### Cache Errors

- When `LRI` or `LRU` is constructed with `max_size` less than or equal to zero, the constructor must raise `ValueError`.
- When `LRI` or `LRU` is constructed with a non-callable `on_miss`, the constructor must raise `TypeError`.
- When `LRI.__getitem__` or `LRU.__getitem__` encounters a missing key without `on_miss`, it must raise `KeyError`.
- When `cached` receives an invalid `cache` argument that is neither a mapping nor a callable, it must raise `TypeError`.
- When `cachedmethod` receives an invalid `cache` argument that is neither a mapping, callable, nor string attribute name, it must raise `TypeError`.
- When `ThresholdCounter` is constructed with a `threshold` not between 0 and 1, it must raise `ValueError`.
- When `ThresholdCounter.__getitem__` is called with an absent or below-threshold key, it must raise `KeyError`.
- When `GUIDerator` or `SequentialGUIDerator` is constructed with a `size` not satisfying `20 < size <= 36`, it must raise `ValueError`.

### Mapping Errors

- When a mutation method is called on `FrozenDict`, it must raise `TypeError`.
- When a `FrozenDict` containing unhashable values is hashed, it must raise `FrozenHashError`.
- When `OneToOne.unique()` receives initial data mapping two keys to the same value, it must raise `ValueError`.
- When `OrderedMultiDict.poplast` is called with a missing key and no default, it must raise `KeyError`.

### Iterable Errors

- When `split` or `split_iter` receives a non-iterable `src`, it must raise `TypeError`.
- When `chunked` or `chunked_iter` receives a non-iterable `src`, it must raise `TypeError`.
- When `chunked` or `chunked_iter` receives a non-positive `size`, it must raise `ValueError`.
- When `chunked` or `chunked_iter` receives unknown keyword arguments, it must raise `ValueError`.
- When `xfrange` receives a zero `step`, it must raise `ValueError`.
- When `backoff` receives `count="repeat"`, it must raise `ValueError`.
- When `backoff` or `backoff_iter` receives `start` or `stop` that are negative, `stop < start`, `factor < 1.0`, or invalid count, it must raise `ValueError`.
- When `remap` receives a non-callable `visit`, `enter`, or `exit` argument, it must raise `TypeError`.
- When `remap` receives unexpected keyword arguments beyond documented options, it must raise `TypeError`.
- When `get_path` cannot access a path segment and no default is supplied, it must raise `PathAccessError`.

### URL Errors

- When `URL` receives malformed input that cannot be parsed, it must raise `URLParseError`.
- When `parse_host` receives invalid IPv6 syntax, it must raise `URLParseError`.
- When `parse_url` encounters a non-integer port, it must raise `URLParseError`.
- When `register_scheme` receives incompatible `default_port` and `uses_netloc` combinations, it must raise `ValueError`.

## Cross-View Invariants

- A value inserted into an `LRI` or `LRU` through mapping assignment must be returned by lookup until public eviction or deletion removes it.
- A result stored by `cached`, `cachedmethod`, or `cachedproperty` must be reused by subsequent calls that resolve to the same public cache key.
- An ordered multi-value mapping changed through `add`, `addlist`, assignment, update, or deletion must expose the same associations through lookup, `getlist`, iteration, `items(multi=True)`, and copying.
- Inverting a `OneToOne` or `ManyToMany` relation must expose the reverse of the same public associations, and changes through either public view must remain visible from the other.
- A `URL` serialized with `to_text()` and parsed again must preserve its public components, subject to the documented quoting and default-port normalization rules.
- Navigating or normalizing a `URL` must update its attributes, query parameters, authority, and serialized form consistently.
- `remap`, `get_path`, and `research` must agree on the paths produced by the same nested mapping and sequence structure.

## Public Interface

### Import Surface

The package is imported as `boltons`. Public imports must work from the documented module paths, including:

```python
from boltons.cacheutils import LRU, LRI, cached, cachedmethod, cachedproperty
from boltons.cacheutils import ThresholdCounter, MinIDMap, make_cache_key
from boltons.dictutils import MultiDict, OMD, OrderedMultiDict, FastIterOrderedMultiDict
from boltons.dictutils import OneToOne, ManyToMany, FrozenDict, FrozenHashError, subdict
from boltons.iterutils import remap, get_path, research, chunked, windowed
from boltons.iterutils import default_visit, default_enter, default_exit, PathAccessError
from boltons.urlutils import URL, QueryParamDict, URLParseError, parse_url, find_all_links
```

The four modules are independent utility domains. Callers must not need private helpers or a particular internal package layout to use them.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| `LRI` | class | Least-recently-inserted eviction cache |
| `LRU` | class | Least-recently-used eviction cache |
| `cached` | decorator | Cache function return values in a mapping |
| `cachedmethod` | decorator | Cache method return values per instance |
| `cachedproperty` | descriptor | Lazy-computed instance attribute |
| `make_cache_key` | function | Build a hashable key from call arguments |
| `ThresholdCounter` | class | Frequency counter with common/uncommon separation |
| `MinIDMap` | class | Compact integer id mapping for live objects |
| `OrderedMultiDict` | class | Ordered mapping supporting repeated keys |
| `OMD` | class | Alias for `OrderedMultiDict` |
| `MultiDict` | class | Alias for `OrderedMultiDict` |
| `FastIterOrderedMultiDict` | class | Iteration-optimized ordered multi-dict |
| `OneToOne` | class | Bijective mapping with inverse view |
| `ManyToMany` | class | Bidirectional many-to-many relation |
| `FrozenDict` | class | Immutable hashable dict subclass |
| `FrozenHashError` | exception | Raised when hashing a `FrozenDict` with unhashable values |
| `subdict` | function | Extract a subset of keys from a mapping |
| `remap` | function | Walk and rebuild nested data structures |
| `get_path` | function | Index through nested mappings and sequences |
| `research` | function | Search nested structures by predicate |
| `PathAccessError` | exception | Raised when a nested path segment is inaccessible |
| `flatten` | function | Recursively flatten nested iterables to a list |
| `chunked` | function | Split an iterable into fixed-size chunks |
| `windowed` | function | Produce overlapping sliding windows from an iterable |
| `unique` | function | Deduplicate an iterable preserving first occurrences |
| `bucketize` | function | Group iterable elements by a key function |
| `backoff` | function | Generate increasing retry-delay sequences |
| `URL` | class | Parsed and editable URL with component access |
| `QueryParamDict` | class | Ordered multi-dict for URL query parameters |
| `URLParseError` | exception | Raised for malformed URLs, hosts, or ports |
| `parse_url` | function | Decompose URL text into a component mapping |
| `find_all_links` | function | Extract URL-like links from arbitrary text |

### CLI Entry Points

Boltons is a Python library. It provides no covered console script, and `python -m boltons` is not supported for these utilities.

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Assessment calls only the documented module paths and public names. It exercises direct utility behavior, state changes observed through multiple public views, errors by class rather than exact wording, and complete cache, mapping, traversal, and URL workflows. Private nodes, parser expressions, registry shapes, internal cache sentinels, and exact object representations are not part of this contract.
