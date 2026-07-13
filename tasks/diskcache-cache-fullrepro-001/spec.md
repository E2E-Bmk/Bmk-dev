# DiskCache Specification

## Product Overview

DiskCache is a pure-Python, disk-backed caching package. It stores keys, values, expiration metadata, tags, queue items, persistent containers, and synchronization state in a directory that survives object re-creation. The primary data type is `Cache`; `FanoutCache` shards the same cache model for concurrent writers; `Deque` and `Index` expose persistent container views; recipe helpers build memoization and synchronization patterns on top of a cache.

## Scope

This specification covers:

- The public import surface from `diskcache`.
- `Cache` key-value operations, metadata, expiration, tag eviction, iteration, queue helpers, statistics, transactions, and persistence.
- `FanoutCache` operations that mirror `Cache`, plus named cache/deque/index views.
- `Deque` as a persistent double-ended queue.
- `Index` as a persistent ordered mutable mapping.
- `Averager`, `Lock`, `RLock`, `BoundedSemaphore`, `barrier`, `throttle`, and `memoize_stampede`.

## Installable Surface

Install a package named `diskcache`. The top-level package must export these names:

```python
from diskcache import (
    Averager,
    BoundedSemaphore,
    Cache,
    DEFAULT_SETTINGS,
    Deque,
    Disk,
    ENOVAL,
    EVICTION_POLICY,
    EmptyDirWarning,
    FanoutCache,
    Index,
    JSONDisk,
    Lock,
    RLock,
    Timeout,
    UNKNOWN,
    UnknownFileWarning,
    barrier,
    memoize_stampede,
    throttle,
)
```

`DjangoCache` is not required for this package profile. The package must be importable without Django installed. No console script is required.

## Public API

### Cache

```python
Cache(directory=None, timeout=60, disk=Disk, **settings)
```

`directory` is a cache directory path. When it is omitted, the cache creates a temporary directory. When the path does not exist, the cache must create it. The public `directory`, `timeout`, and `disk` attributes must return the directory path, SQLite timeout value, and disk serialization object. A `disk` argument that is not a subclass of `Disk` must raise `ValueError`.

The cache supports the mapping protocol:

```python
cache[key] = value
value = cache[key]
del cache[key]
key in cache
len(cache)
iter(cache)
reversed(cache)
with cache:
    ...
```

`cache[key]` must raise `KeyError` when a key is missing or expired. `del cache[key]` must raise `KeyError` when a key is missing. `__contains__` must return `False` for missing and expired keys. `len(cache)` and insertion-order iteration may include expired items until `expire()` is called.

The cache provides:

```python
set(key, value, expire=None, read=False, tag=None, retry=False) -> bool
add(key, value, expire=None, read=False, tag=None, retry=False) -> bool
get(key, default=None, read=False, expire_time=False, tag=False, retry=False)
read(key, retry=False)
touch(key, expire=None, retry=False) -> bool
delete(key, retry=False) -> bool
pop(key, default=None, expire_time=False, tag=False, retry=False)
incr(key, delta=1, default=0, retry=False)
decr(key, delta=1, default=0, retry=False)
expire(now=None, retry=False) -> int
evict(tag, retry=False) -> int
clear(retry=False) -> int
cull(retry=False) -> int
iterkeys(reverse=False)
peekitem(last=True, expire_time=False, tag=False, retry=False)
push(value, prefix=None, side="back", expire=None, read=False, tag=None, retry=False)
pull(prefix=None, default=(None, None), side="front", expire_time=False, tag=False, retry=False)
peek(prefix=None, default=(None, None), side="front", expire_time=False, tag=False, retry=False)
stats(enable=True, reset=False) -> tuple[int, int]
volume() -> int
check(fix=False, retry=False) -> list
reset(key, value=ENOVAL, update=True)
create_tag_index()
drop_tag_index()
memoize(name=None, typed=False, expire=None, tag=None, ignore=())
transact(retry=False)
close()
```

### FanoutCache

```python
FanoutCache(directory=None, shards=8, timeout=0.01, disk=Disk, **settings)
```

`FanoutCache` exposes the same key-value, metadata, expiration, tag, stats, memoize, and mapping operations as `Cache`, except it shards storage across multiple cache directories. `FanoutCache` must not raise `Timeout` to callers; operations that cannot finish before the timeout must abort according to the method contract. Mapping operations must retry internally. `FanoutCache.transact()` must return a context manager that holds transactions across all shards and yields no public shard object.

Additional public view constructors are:

```python
cache(name, timeout=60, disk=None, **settings) -> Cache
deque(name, maxlen=None) -> Deque
index(name) -> Index
```

Each named view must live under the fanout directory, reuse the same named persistent state when opened again, and remain independent from other names.

### Deque

```python
Deque(iterable=(), directory=None, maxlen=None)
Deque.fromcache(cache, iterable=(), maxlen=None)
```

`Deque` is a persistent, double-ended queue compatible with the usual behavior of `collections.deque` for the covered methods:

```python
append(value)
appendleft(value)
extend(iterable)
extendleft(iterable)
pop()
popleft()
peek()
peekleft()
remove(value)
reverse()
rotate(steps=1)
clear()
copy()
count(value)
index(value, start=0, stop=None)
transact()
```

It supports `len(deque)`, iteration from left to right, reversed iteration, containment by value, positive and negative indexing, item assignment, item deletion, equality comparisons against sequences, and a public `directory` attribute. A deque created with an existing directory must see the same contents. A bounded deque with `maxlen` must discard items from the opposite end when appending past capacity.

### Index

```python
Index(*args, **kwargs)
Index.fromcache(cache, *args, **kwargs)
```

`Index` is a persistent ordered mutable mapping. If the first positional argument is a string or bytes path, it is treated as the backing directory; otherwise the arguments and keyword arguments initialize mapping contents. A keyword named `directory` is ordinary mapping data, not a backing directory selector. It supports:

```python
get(key, default=None)
setdefault(key, default=None)
pop(key, default=ENOVAL)
popitem(last=True)
peekitem(last=True)
push(value, prefix=None, side="back")
pull(prefix=None, default=(None, None), side="front")
clear()
keys()
values()
items()
update(...)
memoize(name=None, typed=False, ignore=())
transact()
```

It also supports `index[key]`, assignment, deletion, containment, length, insertion-order iteration, reverse insertion-order iteration, equality comparisons with mappings, and a public `directory` attribute. An index opened on an existing directory must see the same contents.

### Recipes

```python
Averager(cache, key, expire=None, tag=None)
Lock(cache, key, expire=None, tag=None)
RLock(cache, key, expire=None, tag=None)
BoundedSemaphore(cache, key, value=1, expire=None, tag=None)
barrier(cache, lock_factory, name=None, expire=None, tag=None)
throttle(cache, count, seconds, name=None, expire=None, tag=None, time_func=time.time, sleep_func=time.sleep)
memoize_stampede(cache, expire, name=None, typed=False, tag=None, beta=1, ignore=())
```

`Averager.add(value)` must add a numeric sample; `Averager.get()` must return the current mean or `None` when no samples exist; `Averager.pop()` must return the current mean and remove the stored state.

`Lock` must acquire by reserving its key in the cache, release by deleting it, report `locked()` from cache membership, and work as a context manager. `RLock` must allow repeated acquisition by the same thread and must raise `AssertionError` when releasing an unacquired lock. `BoundedSemaphore` must allow at most `value` active acquisitions and must raise `AssertionError` when released more times than acquired.

`barrier` must wrap a callable so each call runs while holding a lock produced by `lock_factory(cache, key, expire=..., tag=...)`. `throttle` must wrap a callable so calls are delayed to the configured average rate. `memoize_stampede` must wrap a callable so repeated calls with the same cache key return cached results until expiration and expose `__wrapped__` and `__cache_key__`. The cache entry stored at that key contains the callable result together with timing metadata used for early recomputation.

## Product State Model

The core state is the persistent cache directory. Public projections of that state include mapping operations (`cache[key]`, `key in cache`, iteration, `len(cache)`), method operations (`get`, `set`, `pop`, `expire`, `evict`, `stats`, `push`, `pull`), reopened objects that point to the same directory, `FanoutCache` named views, and container views (`Deque` and `Index`).

The directory state must survive `close()` and object re-creation. A closed `Cache` must reopen automatically on later access. Removing the cache directory from outside the library is the caller's responsibility.

## Cache Behavior

- `set` must store a key and value and return `True` when the write succeeds. It must overwrite an existing key.
- `add` must store a key only when the key is absent or expired, return `True` when it inserts, and return `False` without changing the stored value when the key is present and unexpired.
- `get` must return `default` for a missing or expired key. When `expire_time=True` or `tag=True`, it must return a tuple whose first element is the value and whose later elements are the requested expiration timestamp and tag.
- `read(key)` must return a readable file-like object for values stored with `read=True`; it must raise `KeyError` when the key is missing.
- `touch` must update a key's expiration and return `True`; it must return `False` for a missing key.
- `delete` must remove a key and return `True`; it must return `False` for a missing key.
- `pop` must remove a key atomically and return its value. It must return `default` for a missing key. When metadata flags are requested, it must return a tuple like `get`.
- `incr` and `decr` must atomically add or subtract `delta`. When a key is missing and `default` is not `None`, the stored value starts from `default`; when `default=None`, a missing key must raise `KeyError`.
- `expire` must remove expired keys and return the number removed.
- `evict(tag)` must remove keys whose stored tag equals `tag` and return the number removed.
- `clear` must remove all keys and return the number removed.
- `cull` must remove expired keys first and then remove keys according to the current eviction policy until the cache is under `size_limit`; it must return the number removed.
- `iter(cache)` must produce keys in insertion order. `iterkeys()` must produce keys in sorted key order for comparable key types. `reversed(cache)` must produce insertion order in reverse.
- `peekitem(last=True)` must return the last inserted unexpired key and value; `peekitem(last=False)` must return the first inserted unexpired key and value; it must raise `KeyError` when no item is available.
- `push` must create a queue key and store the value. With `prefix=None`, keys must be integers starting at `500000000000000`; pushing to `back` increments keys and pushing to `front` decrements keys. With a string prefix, keys must use the format `"prefix-integer"`.
- `pull` must remove and return `(key, value)` from the chosen side of the queue. It must return `default` when the queue is empty.
- `peek` must return `(key, value)` from the chosen side without removing it. It must return `default` when the queue is empty.
- `stats(enable=True)` must enable statistics and return current `(hits, misses)`. Cache hits and misses from `get` must be counted while enabled. `stats(enable=False, reset=True)` must return the counts and reset them.
- `volume` must return an integer estimate of the cache directory size.
- `check` must return a list of warning objects and, when `fix=True`, may repair recoverable on-disk inconsistencies.
- `reset(key, value)` must update a supported setting and return its previous value; `reset(key)` must reload and return the current setting value.
- `create_tag_index` and `drop_tag_index` must toggle the public `tag_index` setting between enabled and disabled values.
- `memoize` must be called to produce a decorator. Passing a callable directly as the `name` argument must raise `TypeError`.
- `transact` must be a context manager. Writes inside a transaction must be grouped atomically for other writers, and nested transactions in the same thread must be allowed.

## Settings, Constants, and Eviction

`DEFAULT_SETTINGS` must contain the documented settings for statistics, tag indexing, eviction policy, size limit, culling, SQLite pragmas, minimum file size, and pickle protocol. `EVICTION_POLICY` must include `least-recently-stored`, `least-recently-used`, `least-frequently-used`, and `none`.

The default eviction policy is `least-recently-stored`. `least-recently-used` must prefer keys not recently read. `least-frequently-used` must prefer keys with lower access counts. `none` must disable eviction-policy removal while still allowing explicit `expire`, `evict`, `clear`, and `delete`.

## Fanout Behavior

- `FanoutCache` key-value methods must route a given key consistently to the same shard so that `set`, `get`, containment, deletion, increment/decrement, metadata, expiration, and tag behavior agree with `Cache`.
- `len`, iteration, reverse iteration, `volume`, `stats`, `expire`, `evict`, `clear`, `cull`, `check`, tag index toggling, and settings reset must combine or apply across shards.
- The total `size_limit` belongs to the fanout cache; each shard receives a divided share of that limit.
- `FanoutCache.cache(name)` must return a `Cache` rooted under the fanout directory for that name.
- `FanoutCache.deque(name)` must return a `Deque` rooted under the fanout directory for that name.
- `FanoutCache.index(name)` must return an `Index` rooted under the fanout directory for that name.
- Named views must persist and reopen by name.
- `FanoutCache.transact()` must hold transactions across all cache shards for the duration of the context.

## Persistent Containers

### Deque Behavior

- Construction from an iterable must append items from left to right.
- `append` and `appendleft` must add to the right and left ends. `extend` must append each item from the iterable to the right. `extendleft` must append each item from the iterable to the left.
- `pop` and `popleft` must remove and return rightmost and leftmost items; they must raise `IndexError` when empty.
- `peek` and `peekleft` must return rightmost and leftmost items without removal; they must raise `IndexError` when empty.
- Indexing must support positive and negative integer positions. Out-of-range indexes must raise `IndexError`.
- Item assignment and deletion by index must update the sequence visible through iteration.
- `remove(value)` must delete the first matching value from the left and raise `ValueError` when the value is absent.
- `reverse()` must reverse contents in place. `rotate(steps)` must rotate right for positive values and left for negative values.
- `copy()` must return another deque object opened on the same persistent directory; mutations through either object must be visible through the other.
- Bounded deques must keep at most `maxlen` items, discarding from the opposite side on overflow.
- `Deque.fromcache(cache, ...)` must build a deque on an existing cache object and expose that cache through the public `cache` attribute.

### Index Behavior

- Construction from mapping, iterable pairs, and keyword arguments must load items in insertion order.
- `get` must return the stored value or `default` when missing.
- `setdefault` must insert the default only for a missing key and must always return the stored value.
- `pop(key)` must remove and return a value; when the key is missing, it must return `default` if provided and raise `KeyError` otherwise.
- `popitem(last=True)` must remove and return the last inserted item; `popitem(last=False)` must remove and return the first inserted item; empty indexes must raise `KeyError`.
- `peekitem` must return the same item pair as `popitem` for the side without removing it.
- `push` and `pull` must provide queue behavior using the same key rules as `Cache`.
- `keys`, `values`, and `items` must return live view objects consistent with the mapping protocol.
- Equality with another `Index` or an `OrderedDict` must be order-sensitive. Equality with ordinary mappings must be order-insensitive.
- `Index.fromcache(cache, ...)` must build an index on an existing cache object and expose that cache through the public `cache` attribute.

## Recipe Behavior

- `Averager` must store its total/count state in the provided cache under the provided key. `pop()` must delete that state.
- `Lock.acquire()` must block until it stores the lock key; `release()` must remove that key; `locked()` must reflect whether the key is present.
- `RLock.acquire()` must allow repeated acquisition by the same process/thread. Each `release()` must decrement the ownership count. Releasing without ownership must raise `AssertionError`.
- `BoundedSemaphore.acquire()` must block until capacity is available. Each acquire consumes one unit and each release restores one unit. Releasing beyond the configured bound must raise `AssertionError`.
- Recipe context managers must acquire on entry and release on exit even when the wrapped block raises.
- `barrier` must preserve the wrapped function's return value and metadata while serializing calls through the selected lock.
- `throttle` must preserve the wrapped function's return value and metadata while using the cache to track the rate bucket.
- `memoize_stampede` must preserve the wrapped function's return value and metadata. Repeated calls with equivalent cache keys must avoid re-executing the wrapped function until the cached item expires.

## Error Semantics

- Missing mapping reads must raise `KeyError`.
- Missing mapping deletes must raise `KeyError`.
- `get`, `pop`, `pull`, and `peek` methods with defaults must return the default rather than raising for the documented missing-key cases.
- `touch` and `delete` must return `False` when the key is missing.
- `incr` and `decr` with `default=None` must raise `KeyError` for missing keys.
- Empty `Deque.pop`, `Deque.popleft`, `Deque.peek`, and `Deque.peekleft` must raise `IndexError`.
- Empty `Index.popitem` and `Index.peekitem` must raise `KeyError`.
- Releasing an unacquired `RLock` or `BoundedSemaphore` must raise `AssertionError`.
- `Cache(..., disk=...)` must raise `ValueError` when `disk` is not a `Disk` subclass.
- `FanoutCache.transact()` must produce a usable context manager.
- Implementations do not need to reproduce exact exception message text.

## Cross-View Invariants

- A value written with `cache[key] = value` must be visible through `cache.get(key)`, membership testing, iteration, and a new `Cache(cache.directory)` instance.
- A value written with `cache.set(key, value, tag=tag)` must be removable through `cache.evict(tag)` and then absent from `get`, membership, and mapping reads.
- A value written with `expire` must remain visible before expiration and must become absent from `get` and membership after `expire()` removes it.
- A queue value written with `Cache.push` must be visible through normal key lookup at the returned key and through `peek`/`pull` from the matching queue side.
- A `FanoutCache` value written through one instance must be visible through another `FanoutCache` opened on the same directory and through the method or mapping forms for the same key.
- A `FanoutCache.cache(name)`, `.deque(name)`, or `.index(name)` view must persist its state and must not leak entries into a different named view.
- A `Deque` and a reopened `Deque` for the same directory must report the same length, order, and endpoint values.
- An `Index` and a reopened `Index` for the same directory must report the same keys, values, insertion order, and item lookup results.
- Recipe objects using the same cache and key must coordinate through the cache state rather than only through in-memory object state.

## Representative Workflows

```python
from diskcache import Cache

cache = Cache()
cache.set("user:1", {"name": "Ada"}, tag="users")
assert cache["user:1"] == {"name": "Ada"}
same_cache = Cache(cache.directory)
assert same_cache.get("user:1") == {"name": "Ada"}
assert same_cache.evict("users") == 1
assert cache.get("user:1") is None
cache.close()
same_cache.close()
```

```python
from diskcache import FanoutCache

fanout = FanoutCache(shards=4)
fanout.set("alpha", 1)
named = fanout.cache("jobs")
queue = fanout.deque("queue")
index = fanout.index("results")
named.set("status", "ready")
queue.append("job-1")
index["job-1"] = "queued"
assert fanout.cache("jobs").get("status") == "ready"
assert list(fanout.deque("queue")) == ["job-1"]
assert fanout.index("results")["job-1"] == "queued"
```

## Non-Goals

- Django cache backend behavior and Django model pickling are not required.
- Exact private SQLite schema, file names, trigger names, private attributes, and internal helper functions are not required.
- Exact `repr()` strings are not required.
- Exact exception message text is not required.
- Performance measurement equivalence is not required.
- Cross-process stress timing is not required beyond observable persistence and basic synchronization semantics.

## Invocation Protocol

There is no required command-line interface for this package profile. `python -m diskcache` is not supported.

Expected package usage is direct Python import from the `diskcache` package. The implementation should be placed so that `import diskcache` loads the candidate package.

## Evaluation Notes

The package will be exercised through public Python imports. Checks cover key-value cache operations, persistence across reopened objects, metadata and expiration behavior, queue helpers, fanout named views, persistent containers, recipe helpers, and documented error behavior. The tests focus on observable return values, raised exception classes, public attributes, and filesystem-backed persistence.
