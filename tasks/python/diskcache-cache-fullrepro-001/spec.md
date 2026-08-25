<!-- specs/01_base_spec.md -->
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

<!-- specs/02_v21_clarifications.md -->
# DiskCache final behavioral clarifications

This document supplements the base specification.  It states observable
contracts only; it does not describe the assessment layout, test cases, vote
counts, storage schema, or implementation strategy.

## Persistent state and transactions

- Objects opened on the same directory project one durable state, including
  settings, statistics, queue entries, named views, persistent containers, and
  recipe coordination records.  Closing and reusing an object automatically
  reopens that state.
- A transaction commits all of its public mutations when its outermost context
  exits normally and rolls them all back when the outermost context exits with
  an exception.  Nested contexts in one thread participate in that outer
  transaction.  Therefore an exception raised by an inner context but caught
  by user code before the outer context exits does not independently roll back
  the outer transaction.
- These rules apply to `Cache`, `FanoutCache`, `Deque`, and `Index` and remain
  observable after another handle or process reopens the directory.

## Cache projections

- Expired entries are absent from all mapping, method, iteration, length, and
  endpoint projections.  Operations on an already-expired entry have the same
  missing-key result as operations on an absent entry.
- `get` and `pop` always retain their documented metadata tuple shape.  For a
  missing key, `expire_time=True, tag=True` returns
  `(default, None, None)`; requesting one metadata field returns the analogous
  two-element tuple.
- `add`, `incr`, `decr`, `pop`, queue-key allocation, and recipe updates are
  atomic across independently opened handles.  Normal bounded contention must
  not leak backend-lock exceptions.
- Mapping insertion order is persistent.  Updating an existing key preserves
  its position; deleting and reinserting it moves it to the end.  `iterkeys`
  is instead sorted by key for mutually comparable keys.
- Statistics are persistent and shared.  Successful and unsuccessful `get`
  calls change hit/miss counts while enabled; membership and other mapping
  projections do not.
- A constructor setting explicitly supplied by a later handle updates the
  persistent setting seen by handles opened afterward.  `reset(name, value)`
  returns the previous value and persists the replacement.
- Explicit `cull()` first removes expired entries and then follows the selected
  eviction policy until the cache satisfies its size limit.  Policy `none`
  never removes a live entry solely to meet that limit.

## Queue projections

- Queue-formatted mapping keys and queue methods are two public projections of
  the same entries.  Integer queue keys begin at `500000000000000`; prefixed
  keys use `"prefix-integer"`.  An occupied key in either projection is never
  overwritten by allocation.
- Prefixes are independent and front/back operations share the documented
  order within a prefix.  Allocation is atomic across handles and facades.
- With metadata flags, the logical queue pair is the first result element:
  `((key, value), expire_timestamp, tag)` when both flags are requested, with
  the corresponding shorter forms for one flag.  Empty queues return the
  supplied default.
- Updating, touching, popping, evicting, clearing, expiring, or rolling back a
  queue entry through one public projection is reflected by every other
  projection and by reopened objects.

## Fanout and named views

- `FanoutCache` preserves Cache method contracts for routed keys and aggregates
  whole-cache operations across shards.  Aggregate counts, settings, tag-index
  changes, statistics, iteration, and queue state are durable across facades.
- A Fanout transaction groups all routed shards and follows the same nested
  commit/rollback rule as Cache.  Ordinary method forms that cannot acquire a
  routed shard within the configured timeout return their documented failure
  value without later applying a stale mutation; mapping forms retry.
- Named cache, deque, and index views are persistent and isolated by both name
  and view kind.

## Persistent containers

- `Deque` bulk and endpoint mutations are transactional and persistent.
  Independently opened handles observe the same ordered sequence; bounded
  deques discard only from the opposite side on overflow.  `fromcache` uses
  the supplied cache and `copy` is another facade over the same deque state.
- `Index` preserves insertion order and exposes live `keys`, `values`, and
  `items` views across mutations by other handles.  Updating a key preserves
  its position; deleting and reinserting moves it to the end.  Endpoint,
  `setdefault`, queue-helper, and memoize operations share the same persistent
  mapping state and are atomic where their method contract requires it.

## Recipe coordination

- Recipe state is coordinated by directory and public key/name, not Python
  object identity.  Lock leases are ownership-safe; a stale release cannot
  remove a newer lease.  RLock ownership is determined by the process/thread
  calling `acquire`, and BoundedSemaphore capacity is shared across handles.
- `expire` and `tag` supplied to Lock, RLock, BoundedSemaphore, and barrier are
  applied to the persistent coordination entry and are publicly observable
  while that entry exists.
- Separately constructed barriers and throttles with the same explicit name
  coordinate through shared state.  Injected clock/sleep functions make the
  throttle bucket deterministic.
- Averager updates are atomic shared total/count updates.  Memoization keys are
  stable across equivalent positional/keyword calls and honor ignored argument
  names.  A failed initial stampede computation is not cached and releases its
  coordination; a successful entry stores the documented `(value, elapsed)`
  record under the wrapper's public cache key.

## Serialization and diagnostics

- `read=True` file-like values, custom `Disk` subclasses, and `JSONDisk`
  round-trip through reopened handles and process boundaries using their public
  serialization contracts.
- `check()` reports unrelated files and empty subdirectories using the public
  `UnknownFileWarning` and `EmptyDirWarning` categories.  No cache-internal
  file or schema name is part of this contract.

<!-- specs/03_v22_public_semantics.md -->
# DiskCache v22 public-semantics clarification

This document supplements the base specification and the consolidated final
clarifications.  Every rule below is part of the public behavior boundary.  It
does not prescribe a database schema, file layout, private helper, or test
implementation.

## Ordered lifetime and cleanup

- Updating a live mapping key preserves its insertion position.  Once an
  entry is logically expired, writing that key again creates a new insertion
  and places it at the end.  Observing an expired entry as missing through the
  public read path also performs its lazy cleanup, so a later `expire()` does
  not count that already-observed entry again.
- With an eviction policy other than `none` and a positive `cull_limit`, a
  successful `set`, `add`, or `push` performs the documented bounded automatic
  culling step.  Explicit `cull()` remains available for complete convergence.

## Numeric and statistics projections

- `Cache.incr` and `Cache.decr` change only the numeric value of an existing,
  unexpired entry.  They preserve its expiration timestamp, tag, insertion
  position, and queue projection.  `FanoutCache.incr` and
  `FanoutCache.decr` preserve the same metadata and projections through the
  routed facade.
- Hit/miss statistics measure value reads, not structural inspection.  In
  particular, membership checks and queue `peek` operations do not increment
  either count.

## Queue validation and empty results

- The `side` argument accepted by `peek` and `pull` is either `"front"` or
  `"back"`.  Any other value raises `KeyError` without changing queue state.
- With no explicit default, an empty Cache queue returns `(None, None)` from
  `peek` and `pull`.  Metadata flags wrap that logical queue result in the same
  nested shape used for non-empty queues; for example, requesting both fields
  returns `((None, None), None, None)`.  `Index` queue helpers inherit these
  empty/default contracts.

## Named Fanout views and JSON behavior

- `FanoutCache.cache(name, timeout=60, disk=None, **settings)` accepts public
  Cache settings for the named view.  `disk=None` inherits the parent Fanout
  disk class.  Named-view settings and serialized values persist on reopen.
- `JSONDisk` follows ordinary JSON conversion semantics.  JSON-compatible
  mapping keys such as integers are converted as JSON specifies, and mapping
  member order is retained through a value round trip; implementations must
  not impose sorting that rejects otherwise valid mixed JSON object keys.

## Persistent container properties

- Assigning a smaller non-negative `Deque.maxlen` immediately trims durable
  contents from the left until the new bound is satisfied.  The trimmed order
  is visible through other facades and after reopen.
- `Index.memoize(..., ignore=...)` and `memoize_stampede(..., ignore=...)`
  accept both argument names and zero-based integer positional indexes.  An
  ignored argument is excluded from public cache-key construction, so calls
  differing only in that argument reuse one persistent result.

## Recipe initialization

- Constructing a `throttle` decorator with an explicit `name`, `count`, and
  injected `time_func` initializes its shared persistent bucket at decoration
  time as `(time_func(), count)` under that name.  Separate wrappers with the
  same name then continue from that one bucket.

<!-- specs/04_v23_protocol.md -->
# DiskCache v23 ordered-protocol clarification

- `reversed(index)` returns keys in reverse persistent insertion order, and the
  order remains the same through a separately opened `Index` facade.
- `Cache.peekitem` accepts `expire_time` and `tag` flags. Requested metadata
  wraps the logical endpoint pair in the same way as queue metadata; with both
  flags the result is `((key, value), expire_timestamp, tag)`.

These are public protocol and method-return contracts. They require no
particular database, file, or helper layout.

<!-- specs/05_v24_cross_protocol.md -->
# DiskCache v24 cross-protocol clarification

This clarification defines public interactions between existing methods and
facades.  It does not prescribe internal tables, files, shards, or helpers.

## Read statistics

- While Cache statistics are enabled, a successful mapping read
  (`cache[key]`) and a successful `Cache.read(key)` are value-read hits.
  Structural membership and queue `peek` remain non-counting observations.
- `FanoutCache.stats()` aggregates those same mapping-read and `read()` hits
  from the routed shards.

## Persistent container projections

- `Deque.fromcache(cache, ...)` adopts the supplied Cache's unprefixed queue
  projection.  Pre-existing queue items are deque items, and later deque
  appends remain visible through the Cache queue methods.
- `Deque.maxlen` is configuration of a deque facade, not durable metadata.
  Trimming changes durable contents, but reopening the directory without a
  `maxlen` argument creates an unbounded facade over those trimmed contents.
- Index storage is non-evicting container state.  Reducing the backing Cache
  size limit must not silently remove Index entries; they persist until an
  explicit Index/Cache mutation removes them.

## Settings across public objects

- Resetting a `disk_*` Cache setting immediately updates both the Cache's
  public setting projection and the corresponding unprefixed attribute on its
  associated public `Disk` object, and the value persists on reopen.
- Fanout `size_limit` is one facade total.  Resetting it distributes that total
  across shards; the public `FanoutCache.size_limit` remains the requested
  total rather than multiplying it by the shard count.

## Serialization strategies

- `JSONDisk` applies ordinary JSON validation and conversion.  A value rejected
  by `json.dumps` raises `TypeError` and is not silently stored through a
  pickle fallback.
- A supplied custom `Disk` controls Cache public key serialization through its
  `put`/`get` protocol.  Overrides may normalize keys, and iteration returns
  the normalized public key.
- Fanout routing uses the supplied Disk key/hash protocol so keys that are
  equivalent under that Disk route to the same shard and retrieve one value.

## Context and memoization protocols

- `FanoutCache.transact()` yields `None` as its context-manager `as` value.
- For `Index.memoize(..., ignore=...)` and
  `memoize_stampede(..., ignore=...)`, an integer ignore value indexes actual
  positional call slots, including individual values captured by `*args`.
  Calls differing only in an ignored variadic slot reuse one persistent result.

<!-- specs/06_public_lifecycle_handoff.md -->
# DiskCache public lifecycle and handoff contract

This document replaces the v26, v28, and v29 addenda. It supplements the base
specification and the v21-v24 clarifications. The rules below describe only
observable public behavior; they do not prescribe a database schema, file
layout, private helper, or serialized byte representation.

## Logical absence and consistency checks

- `Cache.check(fix=False)` reports an unrelated ordinary file anywhere below
  the cache directory with the public `UnknownFileWarning` category. Exact
  warning text, cache-owned filenames, and repair behavior are not prescribed.
- Expired entries are logically absent from removal counts. An expired tagged
  entry contributes zero to `evict(tag)`, and an expired-only cache contributes
  zero to `clear()`.

## Facade lifecycle and public options

- A closed `Cache` automatically reopens for structural operations such as
  `len(cache)` and iteration, and it remains writable afterwards.
- `Cache.read(key, retry=True)` accepts the public retry option and returns the
  same readable value stream as the ordinary successful read path.
- `Cache.reset(key, value, update=False)` changes the current facade's setting
  projection without persisting that temporary value to a newly opened facade.
  This rule does not redefine the normal reset setter's return value.
- Closing the public backing Cache exposed as `deque.cache` or `index.cache`
  does not invalidate the container facade. Structural reads and later
  mutations automatically reopen and continue to share durable state.
- A closed `FanoutCache` likewise reopens for `len`, iteration, and later
  routed writes on the same facade.

## JSONDisk key conversion

- `JSONDisk` applies ordinary JSON conversion to keys as well as values. A
  tuple key and its equivalent JSON list denote one live key through get,
  membership, add, metadata, iteration, and reopen. Iteration exposes the
  normalized JSON list.

## Custom Disk value and resource protocols

- A public `Disk` subclass controls the `store`/`fetch` value protocol. Its
  value field may be an ordinary persistence-compatible scalar associated
  with an opaque custom mode; Cache must return that value through `fetch`
  across metadata reads and reopen.
- `FanoutCache` honors the same value protocol through routed set/get,
  metadata, and reopen.
- A custom `Disk` may instead manage a stored value through an external
  resource identified by its `store` result and consumed by `fetch`. After a
  successful public deletion, Cache delegates release of that resource to the
  strategy's public `remove` hook. `FanoutCache` honors the same lifecycle
  after routing the value. Exact callback counts, internal filenames, and
  storage layout are not prescribed.

## Fanout context and memoization

- `FanoutCache` is a context manager. Writes made inside its context persist
  after exit, and later operations on that same facade automatically reopen
  it. No semantic meaning is assigned to an optional `as` binding.
- `FanoutCache.memoize(...)` provides persistent memoization: repeated
  equivalent calls reuse one stored result, the wrapped function exposes
  public `__cache_key__`, and a Fanout facade reopened on the same directory
  can read the value at that key.

## Same-runtime serialization handoff

DiskCache facades support standard-library `pickle` when producer and consumer
use the same installed DiskCache implementation in one trusted Python runtime.
This is not a cross-version or untrusted-data format.

After a round trip, a reconstructed `Cache` or `FanoutCache` addresses the same
persistent directory, reads values stored before serialization, and shares
later public mutations with the original facade. Fanout reconstruction
preserves the routing configuration needed to reach that logical store.

A reconstructed `Deque` or `Index` likewise reads the persistent contents
stored before serialization and shares later public mutations with the
original facade. `Deque` also preserves its public `maxlen` configuration.

No exact pickle payload, private state, connection identity, active
transaction, context-manager return value, or compatibility across Python or
DiskCache versions is prescribed.
