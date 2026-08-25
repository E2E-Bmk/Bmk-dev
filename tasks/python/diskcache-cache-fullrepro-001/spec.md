# DiskCache Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`diskcache` is a disk-backed caching library. It provides pure-Python, disk-backed caching. It stores keys, values, expiration metadata, tags, queue items, persistent containers, and synchronization state in a directory that survives object re-creation. The primary data type is `Cache`; `FanoutCache` shards the same cache model for concurrent writers; `Deque` and `Index` expose persistent container views; recipe helpers build memoization and synchronization patterns on top of a cache.

## Non-Goals

- This specification does not require Django cache backend behavior or Django model pickling.
- This specification does not require Exact private SQLite schema, file names, trigger names, private attributes, or internal helper functions.
- This specification does not require Exact `repr()` strings.
- This specification does not require Exact exception message text.
- This specification does not require Performance measurement equivalence.
- This specification does not require Cross-process stress timing beyond observable persistence or basic synchronization semantics.

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

## Cache Behavior

`Cache` is a disk-backed key-value store that supports mapping operations, metadata tagging, expiration, queue operations, statistics, and transactions.

**Set and add.** `set` must store a key and value and return `True` when the write succeeds. It must overwrite an existing key. When `tag` is supplied, the tag must be stored with the entry. When `read=True` is supplied, the value must be stored so that `read(key)` returns a file-like object. `add` must store a key only when the key is absent or expired, return `True` when it inserts, and return `False` without changing the stored value when the key is present and unexpired.

**Get and read.** `get` must return `default` for a missing or expired key. When `expire_time=True` or `tag=True`, it must return a tuple whose first element is the value and whose later elements are the requested expiration timestamp and tag. `read(key)` must return a readable file-like object for values stored with `read=True`; it must raise `KeyError` when the key is missing.

**Touch and delete.** `touch` must update a key's expiration and return `True`; it must return `False` for a missing key. `delete` must remove a key and return `True`; it must return `False` for a missing key.

**Pop.** `pop` must remove a key atomically and return its value. It must return `default` for a missing key. When metadata flags are requested, it must return a tuple like `get`.

**Increment and decrement.** `incr` and `decr` must atomically add or subtract `delta`. When a key is missing and `default` is not `None`, the stored value must start from `default`; when `default=None`, a missing key must raise `KeyError`.

**Expiration and eviction.** `expire` must remove expired keys and return the number removed. When `now` is supplied, it must be used as the reference time instead of the current system time. `evict(tag)` must remove keys whose stored tag equals the supplied tag and return the number removed. `clear` must remove all keys and return the number removed. `cull` must remove expired keys first and then remove keys according to the current eviction policy until the cache is under `size_limit`.

**Iteration.** `iter(cache)` must produce keys in insertion order. `iterkeys()` must produce keys in sorted key order for comparable key types. `reversed(cache)` must produce insertion order in reverse.

**Peek.** `peekitem(last=True)` must return the last inserted unexpired key and value; `peekitem(last=False)` must return the first. It must raise `KeyError` when no item is available.

**Queue operations.** `push` must create a queue key and store the value. With `prefix=None`, keys must be integers starting at `500000000000000`; pushing to the back increments keys and pushing to the front decrements keys. With a string prefix, keys must use the format `"prefix-integer"`. `pull` must remove and return `(key, value)` from the chosen side; it must return `default` when the queue is empty. `peek` must return `(key, value)` from the chosen side without removing it; it must return `default` when the queue is empty.

**Statistics.** `stats(enable=True)` must enable statistics and return current `(hits, misses)`. Cache hits and misses from `get` must be counted while enabled. `stats(enable=False, reset=True)` must return the counts and reset them.

**Volume and check.** `volume` must return an integer estimate of the cache directory size. `check` must return a list of warning objects and, when `fix=True`, may repair recoverable inconsistencies.

**Settings.** `reset(key, value)` must update a supported setting and return its previous value; `reset(key)` must reload and return the current setting value. `create_tag_index` and `drop_tag_index` must toggle the public `tag_index` setting between enabled and disabled values.

**Memoize.** `memoize` must be called to produce a decorator (e.g., `@cache.memoize()`). Passing a callable directly as the `name` argument must raise `TypeError`. Memoized functions must expose a `__cache_key__` method that returns the cache key for given arguments.

**Transactions.** `transact` must be a context manager. Writes inside a transaction must be grouped atomically for other writers, and nested transactions in the same thread must be allowed.

**Persistence.** A closed `Cache` must reopen automatically on later access. Creating a new `Cache` on the same directory must see all previously stored entries.

**Disk validation.** When `disk` is supplied to the constructor, it must be a `Disk` subclass; otherwise `ValueError` must be raised.

## Settings, Constants, and Eviction

Cache settings and eviction policies determine storage limits and key removal behavior.

**Default settings.** `DEFAULT_SETTINGS` must contain the documented settings for statistics, tag indexing, eviction policy, size limit, culling, SQLite pragmas, minimum file size, and pickle protocol. The default eviction policy must be `"least-recently-stored"`.

**Eviction policies.** `EVICTION_POLICY` must include `"least-recently-stored"`, `"least-recently-used"`, `"least-frequently-used"`, and `"none"`. `least-recently-used` must prefer keys not recently read. `least-frequently-used` must prefer keys with lower access counts. `none` must disable eviction-policy removal while still allowing explicit `expire`, `evict`, `clear`, and `delete`.

## Fanout Behavior

`FanoutCache` shards key-value operations across multiple `Cache` instances and exposes named sub-views.

**Shard routing.** Key-value methods must route a given key consistently to the same shard so that `set`, `get`, containment, deletion, increment/decrement, metadata, expiration, and tag behavior agree with `Cache`.

**Aggregate operations.** `len`, iteration, reverse iteration, `volume`, `stats`, `expire`, `evict`, `clear`, `cull`, `check`, tag index toggling, and settings reset must combine or apply across shards. The total `size_limit` belongs to the fanout cache; each shard receives a divided share.

**Named views.** `FanoutCache.cache(name)` must return a `Cache` rooted under the fanout directory for that name. `FanoutCache.deque(name)` must return a `Deque`. `FanoutCache.index(name)` must return an `Index`. Named views must persist and reopen by name. Entries in one named view must not leak into a different named view.

**Fanout transactions.** `FanoutCache.transact()` must hold transactions across all cache shards for the duration of the context.

**Persistence.** A `FanoutCache` value written through one instance must be visible through another `FanoutCache` opened on the same directory.

## Persistent Containers

Deque and Index provide persistent double-ended queue and ordered mapping abstractions backed by cache storage.

**Deque construction.** Construction from an iterable must append items from left to right. The `directory` parameter specifies the storage location. When `maxlen` is supplied, bounded deques must keep at most `maxlen` items, discarding from the opposite side on overflow.

**Deque endpoints.** `append` and `appendleft` must add to the right and left ends. `extend` and `extendleft` must append each item from the iterable to the right and left respectively. `pop` and `popleft` must remove and return rightmost and leftmost items; they must raise `IndexError` when empty. `peek` and `peekleft` must return rightmost and leftmost items without removal; they must raise `IndexError` when empty.

**Deque indexing.** Indexing must support positive and negative integer positions. Out-of-range indexes must raise `IndexError`. Item assignment and deletion by index must update the sequence visible through iteration.

**Deque mutations.** `remove(value)` must delete the first matching value from the left and raise `ValueError` when absent. `reverse()` must reverse contents in place. `rotate(steps)` must rotate right for positive values and left for negative values. `count(value)` must return the number of occurrences.

**Deque sharing.** `copy()` must return another deque object opened on the same persistent directory; mutations through either object must be visible through the other. `Deque.fromcache(cache, ...)` must build a deque on an existing cache object and expose that cache through the public `cache` attribute.

**Index mapping.** Construction from mapping, iterable pairs, and keyword arguments must load items. `get` must return the stored value or `default` when missing. `setdefault` must insert the default only for a missing key and must always return the stored value. `pop(key)` must remove and return a value; when the key is missing, it must return `default` if provided and raise `KeyError` otherwise.

**Index endpoints.** `popitem(last=True)` must remove and return the last inserted item; `popitem(last=False)` must remove the first; empty indexes must raise `KeyError`. `peekitem` must return the same item pair as `popitem` for the side without removing it.

**Index queue helpers.** `push` and `pull` must provide queue behavior using the same key rules as `Cache`.

**Index views and equality.** `keys`, `values`, and `items` must return live view objects consistent with the mapping protocol. Equality with another `Index` or an `OrderedDict` must be order-sensitive. Equality with ordinary mappings must be order-insensitive.

**Index construction from cache.** `Index.fromcache(cache, ...)` must build an index on an existing cache object and expose that cache through the public `cache` attribute.

**Index memoize.** `Index` must support `memoize()` to produce a decorator, with the same semantics as `Cache.memoize()`.

**Container persistence.** A `Deque` and a reopened `Deque` for the same directory must report the same length, order, and endpoint values. An `Index` and a reopened `Index` for the same directory must report the same keys, values, and insertion order.

## Recipe Behavior

Recipe helpers build synchronization and memoization patterns on top of a cache.

**Averager.** `Averager` must store its total/count state in the provided cache under the provided key. `add(value)` accumulates values. `get()` must return the running average or `None` when no values have been added. `pop()` must delete the state and return the last average.

**Lock.** `Lock.acquire()` must block until it stores the lock key; `release()` must remove that key; `locked()` must reflect whether the key is present. The lock must support context-manager usage.

**RLock.** `RLock.acquire()` must allow repeated acquisition by the same process/thread. Each `release()` must decrement the ownership count. Releasing without ownership must raise `AssertionError`.

**BoundedSemaphore.** `BoundedSemaphore.acquire()` must block until capacity is available. Each acquire consumes one unit and each release restores one unit. Releasing beyond the configured bound must raise `AssertionError`.

**Context manager cleanup.** Recipe context managers must acquire on entry and release on exit even when the wrapped block raises.

**Barrier.** `barrier` must preserve the wrapped function's return value and metadata while serializing calls through the selected lock.

**Throttle.** `throttle` must preserve the wrapped function's return value and metadata while using the cache to track the rate bucket. It accepts optional `time_func` and `sleep_func` for testing.

**Memoize stampede.** `memoize_stampede` must preserve the wrapped function's return value and metadata. Repeated calls with equivalent cache keys must avoid re-executing the wrapped function until the cached item expires. The cached entry must store a `(value, elapsed)` tuple where `elapsed` is the computation time. Memoized functions must expose a `__cache_key__` method.

## State Model

The core state is the persistent cache directory. Public projections of that state include mapping operations (`cache[key]`, `key in cache`, iteration, `len(cache)`), method operations (`get`, `set`, `pop`, `expire`, `evict`, `stats`, `push`, `pull`), reopened objects that point to the same directory, `FanoutCache` named views, and container views (`Deque` and `Index`).

The directory state must survive `close()` and object re-creation. A closed `Cache` must reopen automatically on later access. Removing the cache directory from outside the library is the caller's responsibility.

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

1. A value written with `cache[key] = value` must be visible through `cache.get(key)`, membership testing, iteration, and a new `Cache(cache.directory)` instance.
2. A value written with `cache.set(key, value, tag=tag)` must be removable through `cache.evict(tag)` and then absent from `get`, membership, and mapping reads.
3. A value written with `expire` must remain visible before expiration and must become absent from `get` and membership after `expire()` removes it.
4. A queue value written with `Cache.push` must be visible through normal key lookup at the returned key and through `peek`/`pull` from the matching queue side.
5. A `FanoutCache` value written through one instance must be visible through another `FanoutCache` opened on the same directory and through the method or mapping forms for the same key.
6. A `FanoutCache.cache(name)`, `.deque(name)`, or `.index(name)` view must persist its state and must not leak entries into a different named view.
7. A `Deque` and a reopened `Deque` for the same directory must report the same length, order, and endpoint values.
8. An `Index` and a reopened `Index` for the same directory must report the same keys, values, insertion order, and item lookup results.
9. Recipe objects using the same cache and key must coordinate through the cache state rather than only through in-memory object state.

## Public Interface

### Import Surface

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

### API Catalog

| Name | Kind | Role |
|------|------|------|
| `Cache` | class | Disk-backed key-value cache with mapping, queue, and transaction support |
| `FanoutCache` | class | Sharded cache facade with named sub-views |
| `Deque` | class | Persistent double-ended queue |
| `Index` | class | Persistent ordered mutable mapping |
| `Disk` | class | Base disk serialization strategy |
| `JSONDisk` | class | JSON disk serialization strategy |
| `Averager` | class | Running-average helper backed by cache state |
| `Lock` | class | Distributed lock backed by a cache key |
| `RLock` | class | Reentrant lock backed by a cache key |
| `BoundedSemaphore` | class | Bounded semaphore backed by cache state |
| `barrier` | function | Serialize calls to a wrapped callable through a lock |
| `throttle` | function | Rate-limit calls to a wrapped callable |
| `memoize_stampede` | function | Memoize a callable with stampede protection |
| `DEFAULT_SETTINGS` | constant | Default cache settings mapping |
| `EVICTION_POLICY` | constant | Supported eviction policy names |
| `ENOVAL` | constant | Sentinel for unset reset values |
| `UNKNOWN` | constant | Sentinel for unknown metadata values |
| `EmptyDirWarning` | warning | Warn when operating on an empty cache directory |
| `UnknownFileWarning` | warning | Warn when encountering an unknown cache file |
| `Timeout` | exception | Timeout while waiting for cache access |

### CLI Entry Points

There is no required command-line interface for this package profile. `python -m diskcache` is not supported.

Expected package usage is direct Python import from the `diskcache` package.

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Cache methods, mapping operations, reopened objects, fanout views, persistent containers, and recipe helpers should all project the same filesystem-backed state described above. Public return values, exception classes, documented attributes, and durable side effects form the compatibility boundary; SQLite schema and helper layout do not.
