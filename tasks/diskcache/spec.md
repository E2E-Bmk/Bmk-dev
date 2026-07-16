# DiskCache Specification

## Product Overview

DiskCache is a pure-Python, disk-backed cache library. It stores cache metadata in SQLite and may store larger values as files in a cache directory. The public API is designed to feel like Python mappings and containers while remaining persistent, thread-safe, process-safe, and usable without a separate server process.

The package centers on three cache-facing types:

- `Cache`, a single disk-backed mapping with expiration, tags, size limits, eviction policies, transactions, memoization, file-value access, and metadata/statistics helpers.
- `FanoutCache`, a sharded cache that distributes keys across multiple `Cache` instances to reduce write contention.
- `DjangoCache`, available when Django is installed, a Django-compatible cache backend built on `FanoutCache`.

DiskCache also provides persistent container types, `Deque` and `Index`, plus synchronization and memoization recipes that use a cache as cross-thread and cross-process coordination storage.

## Scope

This specification covers the public behavior of:

- Package-level imports from `diskcache`.
- Cache construction, persistence, mapping operations, expiration, tag metadata, eviction, queue helpers, statistics, consistency checks, settings, serialization, and transactions.
- Fanout sharding behavior and shard-local container factories.
- Django cache backend behavior, including Django key versioning and timeout conversion.
- Persistent `Deque` and `Index` behavior.
- Public `Disk` and `JSONDisk` serialization extension points.
- Public recipe classes and decorators.
- Error and warning classes visible to callers.

## Installable Surface

Install the package as `diskcache`. It has no runtime third-party dependency for the core APIs. Django is optional and is required only for the Django backend.

Public package imports:

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

When Django is importable, `DjangoCache` is also available:

```python
from diskcache import DjangoCache
```

The Django backend path is:

```python
"diskcache.DjangoCache"
```

There is no public `diskcache` console script or installed command-line interface.

## Public API

### Constants And Exceptions

`DEFAULT_SETTINGS` is a mapping of default cache settings. Its public keys are:

- `statistics`: disabled by default.
- `tag_index`: disabled by default.
- `eviction_policy`: default `"least-recently-stored"`.
- `size_limit`: default one gigabyte, measured as an approximate on-disk cache size limit.
- `cull_limit`: default `10`, the maximum number of items culled during automatic culling from `set` and `add`.
- `sqlite_auto_vacuum`, `sqlite_cache_size`, `sqlite_journal_mode`, `sqlite_mmap_size`, `sqlite_synchronous`: SQLite pragma settings.
- `disk_min_file_size`: default 32 KiB, the minimum value size that is stored in a separate file by the default disk.
- `disk_pickle_protocol`: Pickle protocol used by the default disk for non-native data.

`EVICTION_POLICY` names the supported policy strings:

- `"least-recently-stored"` evicts oldest stored items first and is the default.
- `"least-recently-used"` updates access metadata on reads and evicts least recently used items first.
- `"least-frequently-used"` updates access metadata on reads and evicts least frequently used items first.
- `"none"` disables size-based eviction; expiration can still remove items.

`Timeout` is raised by `Cache` methods when a database transaction cannot be obtained within the configured timeout and the operation is not retrying.

`UnknownFileWarning` and `EmptyDirWarning` are warning categories returned by consistency checks when filesystem entries do not match the cache database.

`ENOVAL` and `UNKNOWN` are exported sentinel values used by public defaults and extension points. Treat them as identity sentinels; they are not cache data values.

### Cache

```python
Cache(directory=None, timeout=60, disk=Disk, **settings)
```

`directory` is the cache directory. If omitted, a temporary directory is created and is not automatically removed. User and environment variables in paths are expanded. If the directory does not exist, it is created. Multiple `Cache` instances may point at the same directory from different threads or processes.

`timeout` is the SQLite transaction timeout in seconds. `disk` is a `Disk` class or subclass used for serialization. Keyword settings may use any key in `DEFAULT_SETTINGS`; `disk_` settings configure the disk instance without the prefix.

Public attributes:

- `cache.directory`: directory path as a string.
- `cache.timeout`: SQLite timeout in seconds.
- `cache.disk`: serialization disk instance.
- Settings keys are readable as attributes after initialization or reset.

Core mapping and metadata methods:

```python
cache.set(key, value, expire=None, read=False, tag=None, retry=False) -> bool
cache.add(key, value, expire=None, read=False, tag=None, retry=False) -> bool
cache.touch(key, expire=None, retry=False) -> bool
cache.get(key, default=None, read=False, expire_time=False, tag=False, retry=False)
cache.read(key, retry=False)
cache.pop(key, default=None, expire_time=False, tag=False, retry=False)
cache.delete(key, retry=False) -> bool
cache.incr(key, delta=1, default=0, retry=False)
cache.decr(key, delta=1, default=0, retry=False)
```

Mapping operators are supported:

```python
cache[key] = value
value = cache[key]
key in cache
del cache[key]
len(cache)
iter(cache)
reversed(cache)
```

`set` stores or replaces a key and returns `True`. `add` stores only when the key is missing or expired and returns whether the value was added. `touch` changes a live key's expiration and returns whether a live key was touched. `delete` ignores missing keys and returns whether an item was deleted. `pop` removes a live item and returns its value, or `default` for a missing item.

`expire` is a relative number of seconds. `None` means no expiration. Expired items are invisible to `get`, `read`, `__getitem__`, `__contains__`, `pop`, and `delete`, but expired rows may still contribute to `len(cache)` and iteration until culling or explicit expiration removes them.

When `read=True` in `set` or `add`, `value` must be a file-like object opened for binary reading; DiskCache reads and stores its bytes. When `read=True` in `get`, or when using `read`, the returned value is an open binary file handle. Values stored with `read=True` are guaranteed to be file-backed, so the handle has a filesystem `name`.

When `expire_time=True` or `tag=True`, `get` and `pop` return tuples. The base value is followed by the absolute expiration timestamp when requested and the tag when requested. For a missing key, the same tuple shape is returned with the requested metadata positions set to `None`.

`incr` and `decr` are atomic. For a missing or expired key, `default=None` raises `KeyError`; otherwise the operation stores `default +/- delta` and returns the new value. Negative values are allowed. These operations assume the stored value can be represented in SQLite's integer or numeric storage.

Queue helpers:

```python
cache.push(value, prefix=None, side="back", expire=None, read=False, tag=None, retry=False)
cache.pull(prefix=None, default=(None, None), side="front", expire_time=False, tag=False, retry=False)
cache.peek(prefix=None, default=(None, None), side="front", expire_time=False, tag=False, retry=False)
cache.peekitem(last=True, expire_time=False, tag=False, retry=False)
cache.iterkeys(reverse=False)
```

`push` stores a value under an automatically generated queue key and returns that key. With `prefix=None`, keys are integers. With a string prefix, keys have the form `"prefix-number"`. Queue numbering starts around the middle of the supported key range so both front and back pushes can grow. `side` is `"front"` or `"back"`. `pull` removes and returns a `(key, value)` pair from a side. `peek` returns without removing. Empty queues return the supplied `default`. `peekitem` returns the first or last item in insertion order and raises `KeyError` when the cache is empty.

Maintenance and inspection:

```python
cache.expire(now=None, retry=False) -> int
cache.evict(tag, retry=False) -> int
cache.cull(retry=False) -> int
cache.clear(retry=False) -> int
cache.create_tag_index()
cache.drop_tag_index()
cache.stats(enable=True, reset=False) -> tuple[int, int]
cache.volume() -> int
cache.check(fix=False, retry=False) -> list
cache.reset(key, value=ENOVAL, update=True)
cache.close()
cache.transact(retry=False)
cache.memoize(name=None, typed=False, expire=None, tag=None, ignore=())
```

`expire` removes expired items and returns the number removed. `evict` removes items whose tag equals `tag`. `cull` first removes expired items and then applies the configured eviction policy until the cache volume is under `size_limit`. `clear` removes all items. These removal methods work in batches and return the number removed.

`stats` returns `(hits, misses)`, optionally enabling statistics collection and optionally resetting counters after reading them. Statistics are disabled by default and do not count `incr` or `decr`.

`volume` returns an estimated byte size based on the SQLite database and file-backed values; it does not include directory metadata. `check` returns recorded warning objects for database/filesystem inconsistencies and may repair inconsistencies when `fix=True`.

`reset` reads or updates durable settings. Updating `disk_` settings updates the associated disk attribute. Updating `sqlite_` settings executes the corresponding SQLite pragma. Settings attributes may be stale; call `reset(key)` or use higher-level methods such as `len(cache)` and `volume()` when fresh values are needed.

`close` closes the current thread's database connection. A closed cache reopens automatically on later access. `Cache` can be used as a context manager, and cache objects may be pickled by directory, timeout, and disk type.

`transact` is a context manager that makes grouped operations atomic for a single `Cache`. Transactions may be nested and are not shared between threads. While a transaction is held, other writes to the same cache are blocked; reads may proceed.

`memoize` returns a decorator. It caches function results by function name and arguments. `typed=True` treats different argument types as distinct. `ignore` names or positions arguments omitted from the cache key. The wrapper exposes `__wrapped__` and `__cache_key__(*args, **kwargs)`. `expire=0` skips storing newly computed results while still allowing lookups. Calling `@cache.memoize` without parentheses raises `TypeError`.

### FanoutCache

```python
FanoutCache(directory=None, shards=8, timeout=0.010, disk=Disk, **settings)
```

`FanoutCache` shards keys across `shards` underlying cache directories. Its API mirrors `Cache` for normal cache operations, and `FanoutCache.memoize` behaves like `Cache.memoize`.

The configured `size_limit` applies to the whole fanout cache and is divided evenly across shards. The default timeout is 10 milliseconds. A key always maps to one shard according to the disk's portable hash.

`FanoutCache` never raises `Timeout` to callers. Methods with `retry=False` return failure-style values on timeout: writes and deletes return `False`, `get` returns `default`, and `incr`/`decr` return `None`. Mapping operators retry automatically.

Fanout-specific methods:

```python
fanout.cache(name, timeout=60, disk=None, **settings) -> Cache
fanout.deque(name, maxlen=None) -> Deque
fanout.index(name) -> Index
fanout.close()
fanout.transact(retry=True)
```

`cache`, `deque`, and `index` create or return cached named structures in subdirectories under the fanout directory. Repeated calls with the same name return the same object from that `FanoutCache` instance. `deque` and `index` use eviction policy `"none"`.

`FanoutCache.transact()` locks all shards and therefore can make operations across shards atomic. It requires retrying and blocks until all shard transactions are held.

`FanoutCache.close()` closes shard resources and clears named structure handles held by that fanout instance. Closing a fanout cache does not delete the fanout directory, shard directories, or cached data; later cache access may reopen shard resources as needed. `FanoutCache` can be used as a context manager. Entering returns the same fanout cache instance, and exiting calls `close()`.

### DjangoCache

When Django is installed, `DjangoCache` provides a Django-compatible backend:

```python
DjangoCache(directory, params)
```

In Django settings:

```python
CACHES = {
    "default": {
        "BACKEND": "diskcache.DjangoCache",
        "LOCATION": "/path/to/cache/directory",
        "TIMEOUT": 300,
        "SHARDS": 8,
        "DATABASE_TIMEOUT": 0.010,
        "OPTIONS": {"size_limit": 2 ** 30},
    }
}
```

Only `BACKEND` and `LOCATION` are required by the documented setup. `SHARDS` defaults to `8`; `DATABASE_TIMEOUT` defaults to `0.010`; `OPTIONS` is passed to the underlying `FanoutCache`; Django's `TIMEOUT` supplies the default per-key timeout.

Public methods include:

```python
cache.add(key, value, timeout=DEFAULT_TIMEOUT, version=None, read=False, tag=None, retry=True)
cache.set(key, value, timeout=DEFAULT_TIMEOUT, version=None, read=False, tag=None, retry=True)
cache.get(key, default=None, version=None, read=False, expire_time=False, tag=False, retry=False)
cache.read(key, version=None)
cache.touch(key, timeout=DEFAULT_TIMEOUT, version=None, retry=True)
cache.pop(key, default=None, version=None, expire_time=False, tag=False, retry=True)
cache.delete(key, version=None, retry=True)
cache.get_many(keys, version=None)
cache.set_many(data, timeout=DEFAULT_TIMEOUT, version=None)
cache.delete_many(keys, version=None)
cache.get_or_set(key, default, timeout=DEFAULT_TIMEOUT, version=None)
cache.incr(key, delta=1, version=None, default=None, retry=True)
cache.decr(key, delta=1, version=None, default=None, retry=True)
cache.incr_version(key, delta=1, version=None)
cache.decr_version(key, delta=1, version=None)
cache.has_key(key, version=None)
key in cache
cache.expire()
cache.stats(enable=True, reset=False)
cache.create_tag_index()
cache.drop_tag_index()
cache.evict(tag)
cache.cull()
cache.clear()
cache.close(**kwargs)
cache.get_backend_timeout(timeout=DEFAULT_TIMEOUT)
cache.memoize(name=None, timeout=DEFAULT_TIMEOUT, version=None, typed=False, tag=None, ignore=())
cache.cache(name)
cache.deque(name, maxlen=None)
cache.index(name)
```

Logical keys are passed through Django's key transformation before storage or lookup. The configured key prefix, default version, explicit `version` argument, and custom key function are applied consistently to single-key methods, `get_many`, `set_many`, `delete_many`, `get_or_set`, `has_key`, containment checks, `incr_version`, and `decr_version`. Different key prefixes, versions, or custom key functions isolate otherwise identical logical keys.

`timeout=DEFAULT_TIMEOUT` uses the backend default timeout. `timeout=None` stores without expiration. `timeout=0` is converted to an already-expired backend timeout. `set_many(data, timeout=DEFAULT_TIMEOUT, version=None)` applies the same timeout conversion to every key/value pair and returns an empty list when all writes succeed.

`get_many(keys, version=None)` returns a mapping from requested logical keys to values for found, live entries and omits missing or expired keys. Cached `None` values are returned as values rather than treated as misses. `delete_many(keys, version=None)` deletes each requested key and ignores missing keys.

`get_or_set(key, default, timeout=DEFAULT_TIMEOUT, version=None)` returns the live cached value when one exists. For a missing key, it stores and returns `default`; when `default` is callable, the callable is evaluated and its result is stored. A stored `None` value is a valid cached value and is returned on later lookups.

`has_key(key, version=None)` and `key in cache` are equivalent live-key lookups. `incr_version(key, delta=1, version=None)` stores a live value under the version incremented by `delta`, deletes the old versioned key, and returns the new version. `decr_version(key, delta=1, version=None)` applies the same operation with the version decremented by `delta`. Missing keys for version-changing operations raise `ValueError`.

`DjangoCache` does not raise `Timeout`; its methods default to retrying writes. `incr` and `decr` translate a missing key with `default=None` into `ValueError`. Serialization failures from values that cannot be stored by the configured disk propagate from `add` and `set`; those operations do not silently report success for unserializable values.

`read=True` and `read()` support file-backed responses for sendfile-style integrations.

### Deque

```python
Deque(iterable=(), directory=None, maxlen=None)
Deque.fromcache(cache, iterable=(), maxlen=None)
```

`Deque` is a persistent double-ended sequence. It stores items in a `Cache` with eviction policy `"none"` and does not expire or evict items. If `directory` is omitted, a temporary directory is created and is not automatically removed. A second `Deque` opened on the same directory observes the same contents.

Public attributes and operations:

```python
deque.cache
deque.directory
deque.maxlen
deque.maxlen = value
deque.append(value)
deque.appendleft(value)
deque.extend(iterable)
deque.extendleft(iterable)
deque.pop()
deque.popleft()
deque.peek()
deque.peekleft()
deque.remove(value)
deque.clear()
deque.copy()
deque.count(value)
deque.reverse()
deque.rotate(steps=1)
deque.transact()
```

Standard sequence behavior includes indexing, assignment by index, deletion by index, iteration from front to back, reversed iteration, length, comparisons to sequences, and `+=`.

`maxlen` limits length. Appending at the back drops items from the front when the limit is exceeded; appending at the front drops items from the back. Setting `maxlen` after construction pops from the left until the deque fits. `extendleft` processes the iterable in order by repeated `appendleft`, so the resulting front-to-back order is reversed relative to the iterable.

`pop`, `popleft`, `peek`, and `peekleft` raise `IndexError` on an empty deque. Index access outside the current length raises `IndexError`. `remove` deletes the first equal item from the front and raises `ValueError` when the value is absent. `rotate` rotates right for positive steps and left for negative steps; non-integer steps raise `TypeError`.

`Deque.transact()` groups operations atomically for that deque.

### Index

```python
Index(*args, **kwargs)
Index.fromcache(cache, *args, **kwargs)
```

`Index` is a persistent mutable mapping with insertion-order iteration. If the first positional argument is a string or bytes path, it is treated as the directory and remaining arguments initialize mapping contents. If the first positional argument is `None` or no directory is provided, a temporary directory is created. `Index` stores items in a `Cache` with eviction policy `"none"` and does not expire or evict items.

Public attributes and operations:

```python
index.cache
index.directory
index[key]
index[key] = value
del index[key]
index.setdefault(key, default=None)
index.peekitem(last=True)
index.pop(key, default=ENOVAL)
index.popitem(last=True)
index.push(value, prefix=None, side="back")
index.pull(prefix=None, default=(None, None), side="front")
index.clear()
index.keys()
index.values()
index.items()
index.memoize(name=None, typed=False, ignore=())
index.transact()
```

Standard mutable mapping behavior includes `get`, `update`, membership, iteration over keys in insertion order, reversed iteration, length, equality, and inequality.

`pop(key)` raises `KeyError` when the key is missing unless an explicit default is supplied. `popitem(last=True)` removes and returns the most recently inserted pair; `last=False` removes the oldest pair. `peekitem` returns without removing. `push` and `pull` provide the same generated-key queue semantics as `Cache`, without expiration or tag parameters.

Equality with another `Index` or an `OrderedDict` is order-sensitive. Equality with other mappings is order-insensitive.

`Index.memoize` behaves like cache memoization but stores results in the index without an expiration parameter. `Index.transact()` groups operations atomically for that index.

### Disk And JSONDisk

```python
Disk(directory, min_file_size=0, pickle_protocol=0)
JSONDisk(directory, compress_level=1, **kwargs)
```

`Disk` controls key and value serialization. Keys are always stored in the metadata database. Values may be stored in the database or in separate files. The default disk stores integers, floats, strings, and bytes natively; other values are pickled. Equality for lookup is based on serialized representation, not Python's hash protocol. For native strings, bytes, integers, and floats, equality follows Python's ordinary equality. Large integers and non-native types compare according to serialized bytes.

Public extension methods:

```python
disk.hash(key)
disk.put(key)
disk.get(key, raw)
disk.store(value, read, key=UNKNOWN)
disk.fetch(mode, filename, value, read)
disk.filename(key=UNKNOWN, value=UNKNOWN)
disk.remove(file_path)
```

Subclasses may override these methods to define consistent custom serialization. All clients using the same cache directory are expected to use the same serialization behavior.

`JSONDisk` serializes keys and non-file values as JSON bytes compressed with zlib. `compress_level` is an integer from `0` to `9`, where `0` disables compression, `1` is fastest, and `9` compresses most.

### Recipes

Recipes assume their coordination keys will not be evicted. Use a cache with eviction policy `"none"` when the key must be preserved.

```python
Averager(cache, key, expire=None, tag=None)
averager.add(value)
averager.get()
averager.pop()
```

`Averager` keeps a running total and count under one cache key. `get` returns the current average or `None` when no values have been added. `pop` returns the current average and deletes the key.

```python
Lock(cache, key, expire=None, tag=None)
lock.acquire()
lock.release()
lock.locked()
```

`Lock` is a cross-thread and cross-process lock. It can be used as a context manager. `acquire` blocks until the lock key can be added. `release` deletes the lock key.

```python
RLock(cache, key, expire=None, tag=None)
rlock.acquire()
rlock.release()
```

`RLock` is a re-entrant lock for the same process/thread owner. Releasing when not acquired by the caller raises `AssertionError`.

```python
BoundedSemaphore(cache, key, value=1, expire=None, tag=None)
semaphore.acquire()
semaphore.release()
```

`BoundedSemaphore` allows up to `value` concurrent acquisitions. It can be used as a context manager. Releasing above the bound raises `AssertionError`.

```python
throttle(cache, count, seconds, name=None, expire=None, tag=None, time_func=time.time, sleep_func=time.sleep)
barrier(cache, lock_factory, name=None, expire=None, tag=None)
memoize_stampede(cache, expire, name=None, typed=False, tag=None, beta=1, ignore=())
```

`throttle` returns a decorator that rate-limits calls to at most `count` calls per `seconds`, sleeping as needed. `name` overrides the default key derived from the function's full name.

`barrier` returns a decorator that wraps function execution inside a lock created by `lock_factory`, such as `Lock`, `RLock`, or `BoundedSemaphore`.

`memoize_stampede` returns a memoization decorator with probabilistic early recomputation. Cached entries store both a result and timing metadata. Before expiration, a caller may receive the cached result while one background thread recomputes and refreshes the entry. The wrapper exposes `__wrapped__` and `__cache_key__`.

## Cache Behavior

Cache state persists in the cache directory until the directory is removed by the caller. `close()` releases database resources but does not delete data. Reopening a cache on the same directory exposes previously stored values.

All normal cache operations are atomic. `set`, `add`, `delete`, `pop`, `incr`, `decr`, queue operations, and removal operations serialize their writes through SQLite. Separate cache objects may communicate through the same directory across threads or processes.

Expiration is lazy. Reads treat expired items as missing, but expired records can remain stored until a write culls them, `expire()` removes them, or a queue/peek operation encounters and removes them. `len(cache)` and insertion-order iteration include expired records that have not yet been removed.

Tag metadata is optional and may be any integer, float, string, bytes, or `None`. `evict(tag)` removes entries with exactly matching tags. Creating a tag index changes performance characteristics, not observable tag equality.

Automatic culling happens during `set` and `add` according to `cull_limit`. A `cull_limit` of `0` disables automatic culling but does not disable explicit `expire`, `evict`, `cull`, or `clear`.

All cache clients for one directory are expected to use the same eviction policy and disk serialization. Changing an eviction policy after initialization changes future behavior but does not remove previously created indexes.

## Sharding Behavior

`FanoutCache` provides the same core cache view as `Cache` but distributes keys across shards. Per-key operations are routed to exactly one shard. Aggregate operations such as `len`, iteration, `stats`, `volume`, `expire`, `evict`, `cull`, and `clear` combine shard results.

`FanoutCache` iteration walks shard iteration order. It is not globally sorted across shards. For sorted queue-style behavior or single-cache transactions, use a named `Cache`, `Deque`, or `Index` returned by the fanout factories.

`FanoutCache.cache(name)`, `.deque(name)`, and `.index(name)` store named structures separately from the main shard directories. These structures are persistent and are addressed by their names under the fanout directory.

## Persistent Container Behavior

`Deque` and `Index` are persistent data structures built from cache directories. They are intended as disk-backed replacements for memory-only `collections.deque` and ordered mutable mappings when state must outlive a process or be shared across processes.

Neither `Deque` nor `Index` uses expiration or size-based eviction for its contents. They use a fixed amount of application memory regardless of the number or size of serialized items, aside from values being materialized when read or iterated.

Container iteration reflects insertion/order semantics:

- `Deque` iterates values from front to back.
- `reversed(Deque)` iterates values from back to front.
- `Index` iterates keys in insertion order.
- `reversed(Index)` iterates keys in reverse insertion order.

## Error Semantics

- `Cache` methods that acquire write transactions raise `Timeout` when the database timeout expires and `retry=False`. With `retry=True`, they retry until they can proceed.
- `Cache.evict`, `Cache.expire`, `Cache.cull`, and `Cache.clear` may raise `Timeout(count)` where `count` is the number of removed items before the timeout.
- `FanoutCache` catches `Timeout` for public operations and returns method-specific failure values instead of raising `Timeout`.
- `DjangoCache` does not raise `Timeout` for its public cache API.
- `cache[key]`, `cache.read(key)`, `del cache[key]`, missing `Index` key access, and missing `Index.pop(key)` without a default raise `KeyError`.
- `Cache.get`, `FanoutCache.get`, `DjangoCache.get`, and `pop` methods with a default return that default for missing or expired keys.
- `Cache.incr` and `Cache.decr` raise `KeyError` for missing or expired keys only when `default=None`.
- `DjangoCache.incr` and `DjangoCache.decr` raise `ValueError` for missing keys when `default=None`.
- Empty `Deque.pop`, `Deque.popleft`, `Deque.peek`, and `Deque.peekleft` raise `IndexError`.
- Out-of-range `Deque` indexing, assignment, or deletion raises `IndexError`.
- `Deque.remove(value)` raises `ValueError` when no equal item exists.
- `Deque.rotate(steps)` raises `TypeError` when `steps` is not an integer.
- `Index.peekitem` and `Index.popitem` raise `KeyError` when empty.
- `Cache.memoize`, `DjangoCache.memoize`, and `Index.memoize` raise `TypeError` if used directly as `@object.memoize` rather than called to create a decorator.
- `RLock.release` and `BoundedSemaphore.release` raise `AssertionError` when released without a matching acquisition.
- Write operations can propagate `sqlite3.OperationalError` when the disk or database is full; reads continue to work as long as they do not need to write metadata such as statistics.
- `Cache.check(fix=False)` returns recorded warnings, including `UnknownFileWarning` and `EmptyDirWarning`, instead of raising them directly.

## Cross-View Invariants

1. A value written through `cache[key] = value` is visible through `cache.get(key)`, `cache[key]`, membership checks, and iteration until it is deleted, expired and removed, or evicted.
2. `Cache.add(key, value)` and `Cache.set(key, value)` expose the same stored value to readers after success, but `add` preserves an existing live value and reports `False`.
3. For any live key, `get(key, expire_time=True, tag=True)` and `pop(key, expire_time=True, tag=True)` return the same value and metadata shape; `pop` additionally removes the item.
4. Expired items are missing from lookup views but may remain visible to length and iteration views until explicit or lazy cleanup removes them.
5. A `Cache` opened on a directory, a later `Cache` opened on the same directory, and a pickled/unpickled `Cache` referring to that directory observe the same persisted items when they use compatible disk serialization.
6. `FanoutCache` per-key operations produce the same user-visible value semantics as `Cache` for successful operations; aggregate views combine all shards.
7. A named structure returned by `FanoutCache.deque(name)` or `FanoutCache.index(name)` is persistent under that name and remains separate from ordinary sharded key/value entries.
8. `Deque` order views agree: `peekleft()` equals the first value yielded by iteration, `peek()` equals the first value yielded by reversed iteration, `popleft()` removes from the iteration front, and `pop()` removes from the iteration back.
9. `Index` order views agree: iteration, `peekitem(last=False)`, and `popitem(last=False)` refer to the oldest key, while reversed iteration, `peekitem()`, and `popitem()` refer to the newest key.
10. `Index.push`/`pull` and `Cache.push`/`pull` use compatible generated-key queue semantics, so the key returned by `push` can be used as a normal mapping key until it is pulled or deleted.
11. A file-like value stored with `read=True` is available both as a normal cache value and as a readable binary file handle through `read=True` lookup or `read()`.
12. Django key versioning is applied before data reaches the underlying fanout cache, so two versions of the same Django key are independent cache entries.

## Representative Workflow

The following workflow shows the intended interaction between persistent cache state, metadata, expiration, queues, transactions, and recipes:

```python
from io import BytesIO
from tempfile import TemporaryDirectory

from diskcache import Cache, Deque, Index, Lock

with TemporaryDirectory() as directory:
    cache = Cache(directory, tag_index=True, eviction_policy="least-recently-stored")

    cache.set("profile:alice", {"name": "Alice"}, expire=60, tag="profiles")
    cache.add("visits", 0)
    cache.incr("visits")

    cache.set("asset:logo", BytesIO(b"image-bytes"), read=True, tag="assets")
    with cache.read("asset:logo") as reader:
        payload = reader.read()

    with cache.transact():
        total = cache.incr("latency-total", 120)
        count = cache.incr("latency-count")

    work_key = cache.push("send-email", prefix="jobs")
    queued_key, queued_value = cache.pull(prefix="jobs")

    profiles_removed = cache.evict("profiles")

    deque = Deque(directory=directory + "-deque", maxlen=3)
    deque.extend(["a", "b", "c"])
    deque.append("d")
    newest = deque.peek()

    index = Index(directory + "-index", one=1)
    index["two"] = 2
    oldest = index.peekitem(last=False)

    lock = Lock(cache, "critical-section", tag="locks")
    with lock:
        cache.set("protected", True)

    cache.close()
```

This workflow relies on these guarantees: cache values persist in their directories, metadata such as tags and expiration is part of the public lookup contract, file-backed values can be streamed, transactions group related updates, queue helpers generate usable keys, persistent containers keep their own ordering, and recipes coordinate by storing cache keys.

## Non-Goals

- No asynchronous API is provided. Use an executor if cache calls must be driven from `asyncio`.
- No server process or network protocol is part of the package.
- No installed command-line interface is part of the public package surface.
- DiskCache does not remove temporary or configured cache directories automatically.
- DiskCache does not promise correct behavior on filesystems where SQLite locking is unreliable, such as many NFS mounts.
- DiskCache does not use Python's `hash()` or object `__eq__` protocol for general key lookup; lookup is based on disk serialization.
- `FanoutCache` and `DjangoCache` do not provide single-shard `Cache` transactions over arbitrary sharded keys except through `FanoutCache.transact()` locking all shards or through named shard-local structures.
- Eviction policies are cache policies, not durability guarantees; use eviction policy `"none"` for persistent containers and recipe coordination keys that must not be culled.
