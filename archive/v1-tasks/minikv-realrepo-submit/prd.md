# MiniKV Public Packet

## Overview

Build `minikv.py`, an in-memory data structure store library. It exposes one Python class, `QueueServer`, that stores strings/numbers, lists, sets, and hashes in a single key namespace. Every key has one public type at a time, and all API methods must read and update that same canonical type-tagged state.

The implementation language is Python 3.11. Place `minikv.py` at the root of your solution directory. Use only the Python standard library.

Public API:

```python
from minikv import QueueServer

server = QueueServer(use_gevent=False)
server.kv_set("name", "Alice")
print(server.kv_get("name"))       # "Alice"
print(server.kv_incr("counter"))   # 1
server.lpush("items", "a", "b")
server.sadd("tags", "python")
server.hset("user:1", "name", "Alice")
```

The benchmark does not inspect private implementation details.

## Product Model

MiniKV has one canonical fact source: a key namespace where each live key maps to a stored value, a type tag, and optional expiry metadata. The public methods are projections over that fact source:

- direct key reads and writes through `kv_get`, `kv_set`, `kv_mget`, `kv_mset`, `kv_delete`, `kv_exists`, and counters;
- list views through `lpush`, `rpush`, `lpop`, `rpop`, and `lrange`;
- set views through `sadd`, `srem`, `smembers`, and `scard`;
- hash views through `hset`, `hget`, `hdel`, and `hgetall`;
- lifecycle views through `expire`, `kv_flush`, `save_to_disk`, and `restore_from_disk`.

Correctness is not just that each method works by itself. Mixed operations must keep those projections consistent. For example, if a key was created as a set, then `kv_get`, `smembers`, `scard`, persistence, wrong-type errors, and later deletion must all agree about that same set key.

## Feature Set

The product has six feature modules:

1. String and scalar key-value operations: `kv_set`, `kv_get`, `kv_delete`, `kv_exists`, `kv_incr`, `kv_decr`.
2. Bulk key-value operations: `kv_mset`, `kv_mget`.
3. List operations: `lpush`, `rpush`, `lpop`, `rpop`, `lrange`.
4. Set operations: `sadd`, `srem`, `smembers`, `scard`.
5. Hash operations: `hset`, `hget`, `hdel`, `hgetall`.
6. Key management and persistence: `expire`, `kv_flush`, `save_to_disk`, `restore_from_disk`.

## Global Invariants

- There is one canonical key namespace. A live key has exactly one type tag and every public method must consult that same tag.
- A key's type is determined by the operation that created or overwrote it: `dict` values are `HASH`, `list` values are `QUEUE`, `set` values are `SET`, and all other values are `KV`. `lpush`/`rpush` create `QUEUE`, `sadd`/`smembers`/`scard` create `SET`, and `hset`/`hgetall` create `HASH`.
- `kv_set` overwrites the previous value, type, and expiry for the key. `kv_delete` removes the value, type, and expiry so the name can be reused with a different type.
- Type-restricted operations must raise `CommandError` on wrong-type keys. Failed operations must be atomic: the key's value, type, expiry, existence, type-specific views, and persisted representation must remain unchanged.
- `kv_get` is the direct read projection of the stored value. Type-specific methods such as `lrange`, `smembers`, `scard`, `hget`, and `hgetall` must agree with direct reads for the same live key.
- `smembers` returns the actual stored set object. Mutating that returned set is reflected in later `smembers`, `scard`, `kv_get`, and persistence.
- `hgetall` returns the actual stored dict object. Mutating that returned dict is reflected in later `hgetall`, `hget`, `kv_get`, and persistence.
- `expire` sets an absolute timeout for a live key. Expired keys are lazily removed by public operations, and expiry removal clears the key's value and type so the name can be reused.
- `kv_flush` removes every live key and its type/expiry metadata. After a flush, direct reads report missing keys and collection APIs behave as they do for missing keys.
- `save_to_disk` and `restore_from_disk` round-trip the public semantic state: values, type tags, mutable set/hash contents, counters, and unexpired expiry metadata. A restored server must expose the same direct reads, type-specific views, wrong-type behavior, and later persistence behavior as the original.
- State is private to each `QueueServer` instance.

## Class: QueueServer

### Constructor

`QueueServer(use_gevent=False)`

Create a new data store instance. The `use_gevent` parameter can be ignored for this task; always pass `False`.

### String and Scalar Operations

#### `kv_set(key, value)`

Store a value. Returns `1`. The type is auto-detected: `dict` becomes `HASH`, `list` becomes `QUEUE`, `set` becomes `SET`, and anything else becomes `KV`. This overwrites any previous value, type, and expiry for the key.

#### `kv_get(key)`

Return the stored value, or `None` if the key does not exist or has expired.

#### `kv_delete(key)`

Remove the key, including type and expiry metadata. Returns `1` if deleted, `0` if not found.

#### `kv_exists(key)`

Return `1` if the key exists and has not expired, otherwise `0`.

#### `kv_incr(key)`

Increment a numeric `KV` value by `1`. If the key does not exist, create it at `0` and then increment to `1`. Values of type `int` and `float` are numeric. Strings are not parsed as numbers; incrementing a string value raises `CommandError`. Returns the new value.

#### `kv_decr(key)`

Decrement a numeric `KV` value by `1`. If the key does not exist, create it at `0` and then decrement to `-1`. It has the same numeric and error semantics as `kv_incr`.

### Bulk Operations

#### `kv_mset(__data=None, **kwargs)`

Set multiple keys from a dict and/or keyword arguments. Each key uses the same type detection and overwrite rules as `kv_set`. Returns the count of keys set.

#### `kv_mget(*keys)`

Return a list of direct-read values in the same order as the requested keys. Missing or expired keys appear as `None`.

### List Operations

#### `lpush(key, *values)`

Prepend values to the head of a list. Creates the list if it does not exist. Values are applied in argument order, so `lpush("q", "a", "b")` leaves `"b"` at the head. Returns the number of values pushed.

#### `rpush(key, *values)`

Append values to the tail. Creates the list if it does not exist. Returns the number of values pushed.

#### `lpop(key)`

Remove and return the first element, or `None` if the list is empty or missing.

#### `rpop(key)`

Remove and return the last element, or `None` if the list is empty or missing.

#### `lrange(key, start, end=None)`

Return a list slice using Python slice semantics: `[start:end]`. `None` for `end` means "to the end". Missing keys return `[]`. Raises `CommandError` on non-list keys.

### Set Operations

#### `sadd(key, *members)`

Add members to a set. Creates it if it does not exist. Returns the new cardinality.

#### `srem(key, *members)`

Remove members. Returns the count of members actually removed. Missing set keys return `0`.

#### `smembers(key)`

Return the internal set object. If the key does not exist, create an empty set first. Raises `CommandError` on non-set keys.

#### `scard(key)`

Return the cardinality. If the key does not exist, create an empty set and return `0`. Raises `CommandError` on non-set keys.

### Hash Operations

#### `hset(key, field, value)`

Set a field. Creates the hash if it does not exist. Returns `1`.

#### `hget(key, field)`

Return the field value, or `None` if the hash or field does not exist. Raises `CommandError` on non-hash keys.

#### `hdel(key, field)`

Delete a field. Returns `1` if deleted, `0` if not found. Raises `CommandError` on non-hash keys.

#### `hgetall(key)`

Return the internal dict object. If the key does not exist, create an empty hash first. Raises `CommandError` on non-hash keys.

### Key Management

#### `expire(key, nseconds)`

Set a timeout in seconds for a live key. Returns `None`. Calling `expire` for a missing key is a no-op.

#### `kv_flush()`

Remove all live keys and metadata. Returns the number of live keys removed.

#### `save_to_disk(filename)`

Persist the entire database state to a file using `pickle`. Returns `True`.

#### `restore_from_disk(filename)`

Restore database state from a pickle file. Returns `True` if restored, `False` if the file does not exist.

## Error Behavior

- `CommandError` is raised for type mismatches, such as list operations on scalar keys, hash operations on set keys, or set operations on hash keys.
- `CommandError` is raised for `kv_incr`/`kv_decr` on non-numeric values, including numeric-looking strings.
- Error messages should be descriptive, but exact text is not part of the public API.

## Non-Goals

- No network server or client protocol. Only the Python class API.
- No RESP protocol, gevent integration, or connection handling.
- No sorted sets, streams, pub/sub, transactions, or Lua scripting.
- No scheduled task queue.

## Evaluation Style

Hidden tests are split into two scores:

- Unit tests exercise isolated method contracts with short Python snippets.
- System tests exercise cross-view invariants over the canonical type-tagged key namespace.

System tests are labeled by dimension: `projection_consistency`, `error_atomicity`, `lifecycle_consistency`, `expiry_consistency`, `round_trip`, and `boundary_crossing`.

System scoring is intended to count a failure only when a downstream public projection diverges after the relevant local primitive behavior has been established. Counter auto-creation and `lrange` on missing keys are local contracts covered by unit tests; system cases use counters that already exist and test post-delete/flush list behavior through fresh type reuse rather than repeating the missing-key `lrange` primitive.
