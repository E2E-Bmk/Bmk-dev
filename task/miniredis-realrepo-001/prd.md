# MiniRedis Unit/System Public Packet

## Overview

Build `miniredis.py`, a compact in-memory data structure store. It should support the core workflows of a lightweight Redis-like server: string keys, lists, sets, hashes, key expiry, pattern-based key enumeration, and type-aware error handling.

This task is designed around the distinction between local feature correctness and system correctness. Individual commands should work on their own, but the product is only complete if key types, data structure semantics, expiry, and failure recovery remain consistent across multi-command workflows.

The implementation language is Python 3.11. Place `miniredis.py` at the root of your solution directory. It must run as:

```console
py -3.11 miniredis.py COMMAND [ARGS...]
```

Data-returning commands must print results to stdout, one record per line for simple values, and compact single-line JSON for collections (sets, hashes, key lists). Failed commands must exit non-zero and print a useful message to stderr. The benchmark does not inspect private implementation details.

## Feature Set

The product has seven feature modules:

1. String key-value operations (SET, GET, DEL, EXISTS).
2. List data structure operations (LPUSH, RPUSH, LPOP, RPOP, LRANGE, LLEN).
3. Set data structure operations (SADD, SREM, SMEMBERS, SISMEMBER, SCARD).
4. Hash data structure operations (HSET, HGET, HDEL, HGETALL, HEXISTS).
5. Key management and expiry (KEYS, TYPE, EXPIRE, TTL).
6. Database management (FLUSHDB, DBSIZE).
7. Error handling and atomicity.

These modules are intentionally state-dependent. SET creates string keys; LPUSH creates list keys; SADD creates set keys; HSET creates hash keys. TYPE reflects how a key was created. EXPIRE affects TTL. DEL and FLUSHDB remove state. Type mismatches (e.g., LPOP on a string key) must fail. Expired keys must be excluded from KEYS and DBSIZE.

## Global Invariants

The following invariants define system correctness:

- A key's type is determined by the first operation that created it. SET → string; LPUSH/RPUSH → list; SADD → set; HSET → hash.
- Type-restricted operations must fail on keys of the wrong type and preserve both the original value and the key's original type.
- DEL must remove the key entirely; after DEL, the key name can be reused with a different type.
- LPUSH/RPUSH must preserve insertion order; LPOP/RPOP must remove and return elements in the correct order.
- SADD must deduplicate members; SMEMBERS must return unique members.
- HSET must store field-value pairs; HGET must retrieve them exactly.
- EXPIRE on a non-existent key must return 0 and not create the key.
- TTL must return -2 for non-existent keys and -1 for keys without expiry.
- KEYS must exclude expired keys. DBSIZE must count only live, non-expired keys.
- FLUSHDB must remove all keys regardless of type.
- Failed commands must not corrupt existing key state, data structure contents, type metadata, or expiry.

## Data Model

A key can hold exactly one of four types:
- **string**: a text value created by SET.
- **list**: an ordered sequence of string elements created by LPUSH/RPUSH.
- **set**: an unordered collection of unique string members created by SADD.
- **hash**: a mapping of field names to string values created by HSET.

Timestamps for expiry are based on wall-clock time at second granularity. Expired keys should be lazily removed on access (GET, EXISTS, TYPE, LRANGE, SMEMBERS, HGET, etc.) and also excluded from KEYS and DBSIZE.

## Commands

### String Operations

#### `SET key value`
Set a string key. Returns `OK`. Overwrites any previous value and type.

#### `GET key`
Return the value of the key, or `(nil)` if it does not exist or has expired.

#### `DEL key [key...]`
Delete one or more keys regardless of type. Return the number of keys actually removed.

#### `EXISTS key`
Return `1` if the key exists (any type, not expired), `0` otherwise.

### List Operations

#### `LPUSH key element [element...]`
Prepend one or more elements to the head of a list. If the key does not exist, create an empty list first. Return the length of the list after the operation.

#### `RPUSH key element [element...]`
Append one or more elements to the tail of a list. If the key does not exist, create an empty list first. Return the length of the list after the operation.

#### `LPOP key`
Remove and return the first element of the list, or `(nil)` if the key does not exist.

#### `RPOP key`
Remove and return the last element of the list, or `(nil)` if the key does not exist.

#### `LRANGE key start stop`
Return a JSON array of elements from the list. Indices are 0-based. Negative indices count from the end (-1 is the last element). `start` and `stop` are inclusive. Return an empty array if the key does not exist.

#### `LLEN key`
Return the length of the list, or `0` if the key does not exist.

### Set Operations

#### `SADD key member [member...]`
Add one or more members to a set. If the key does not exist, create an empty set first. Return the number of members actually added (excluding duplicates).

#### `SREM key member [member...]`
Remove one or more members from a set. Return the number of members actually removed.

#### `SMEMBERS key`
Return a JSON array of all members of the set, or an empty array if the key does not exist.

#### `SISMEMBER key member`
Return `1` if member is in the set, `0` otherwise.

#### `SCARD key`
Return the cardinality (number of members) of the set, or `0` if the key does not exist.

### Hash Operations

#### `HSET key field value [field value...]`
Set one or more field-value pairs in a hash. If the key does not exist, create an empty hash first. Return the number of fields that were newly added (not updated).

#### `HGET key field`
Return the value of the field, or `(nil)` if the key or field does not exist.

#### `HDEL key field [field...]`
Delete one or more fields from a hash. Return the number of fields actually removed.

#### `HGETALL key`
Return a JSON object of all field-value pairs, or an empty JSON object `{}` if the key does not exist.

#### `HEXISTS key field`
Return `1` if the field exists in the hash, `0` otherwise.

### Key Management

#### `KEYS [pattern]`
Return matching keys as a compact JSON array. If `pattern` is omitted, return all keys. The pattern supports `*` (any characters) and `?` (single character) glob wildcards. Expired keys must be excluded.

#### `TYPE key`
Return the type: `"string"`, `"list"`, `"set"`, `"hash"`, or `"none"` if the key does not exist or has expired.

#### `EXPIRE key seconds`
Set a timeout on a key. Return `1` if the timeout was set, `0` if the key does not exist.

#### `TTL key`
Return the remaining time to live in seconds. Return `-1` if the key exists but has no expiry. Return `-2` if the key does not exist or has expired.

### Database Management

#### `FLUSHDB`
Remove all keys from the current database regardless of type. Always returns `OK`.

#### `DBSIZE`
Return the number of currently live (non-expired) keys as an integer.

## Error Behavior

Type mismatch errors (e.g., LPUSH on a string key, SADD on a list key, HGET on a set key, LPOP on a hash key) must fail non-zero with useful stderr and preserve the original key state.

Invalid command syntax, missing required arguments, and invalid LRANGE indices (non-integer) must fail non-zero.

Failed commands must not corrupt existing key state, data structure contents, type metadata, or expiry. Ordinary commands with no matching results (e.g., LRANGE of empty list returning `[]`, HGET of missing field returning `(nil)`, SISMEMBER returning `0`) should succeed with exit code 0.

## Non-Goals

- No network server or client protocol. This is a CLI-only tool.
- No sorted sets, streams, bitmaps, hyperloglogs, or geospatial types.
- No pub/sub, transactions (MULTI/EXEC), Lua scripting, or pipelining.
- No persistence (SAVE/LOAD/BGSAVE).
- No automatic expiry eviction thread; lazy expiry on access is sufficient.
- No Redis serialization protocol (RESP) compatibility.

## Evaluation Style

Hidden tests are split into two scores:

- Unit tests exercise one feature module at a time. When a command needs existing key state, tests may set up state via direct command invocation within the same module.
- System tests exercise interactions across at least two feature modules. They inspect stdout, stderr, JSON outputs, key state via subsequent GET/LRANGE/SMEMBERS/HGETALL/TYPE calls, expiry behavior, and failed-command atomicity.

System tests are labeled by dimension:

- `cross_feature_dataflow`
- `state_accumulation`
- `global_invariant`
- `error_atomicity`
- `operation_order_sensitivity`
- `boundary_crossing`
