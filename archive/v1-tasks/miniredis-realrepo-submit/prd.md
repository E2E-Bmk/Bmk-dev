# MiniRedis Unit/System Public Packet

## Overview

Build `miniredis.py`, a compact in-memory data structure store. It should support the core workflows of a lightweight Redis-like server: string keys, lists, sets, hashes, key expiry, pattern-based key enumeration, and type-aware error handling.

This task is designed around the distinction between local feature correctness and system correctness. Individual commands should work on their own, but the product is only complete if one canonical key namespace, its type metadata, its expiry metadata, and its value objects remain consistent across multi-command workflows.

The implementation language is Python 3.11. Place `miniredis.py` at the root of your solution directory. It must support both one-shot and batch-session execution:

```console
py -3.11 miniredis.py COMMAND [ARGS...]
py -3.11 miniredis.py --batch < commands.txt
```

In one-shot mode, the command runs against a fresh empty in-memory database. In batch mode, each non-empty input line is one command with shell-like whitespace splitting and all lines in that process share the same in-memory database. Quoted values and quoted glob patterns are part of the CLI interface contract, but they are local input-parsing behavior rather than system-gap evidence. Batch mode is the intended way to exercise multi-command workflows without requiring persistence. Data-returning commands must print results to stdout, one record per line for simple values, and compact single-line JSON for collections (sets, hashes, key lists). Failed commands in one-shot mode must exit non-zero and print a useful message to stderr. Failed commands in batch mode must print a useful message to stderr, preserve the current database state, and continue with subsequent input lines. The benchmark does not inspect private implementation details.

## Feature Set

The product has seven feature modules:

1. String key-value operations (SET, GET, DEL, EXISTS).
2. List data structure operations (LPUSH, RPUSH, LPOP, RPOP, LRANGE, LLEN).
3. Set data structure operations (SADD, SREM, SMEMBERS, SISMEMBER, SCARD).
4. Hash data structure operations (HSET, HGET, HDEL, HGETALL, HEXISTS).
5. Key management and expiry (KEYS, TYPE, EXPIRE, TTL).
6. Database management (FLUSHDB, DBSIZE).
7. Error handling and atomicity.

These modules are intentionally state-dependent. SET creates string keys; LPUSH/RPUSH create list keys; SADD creates set keys; HSET creates hash keys. TYPE reflects the key's current canonical type. GET, LRANGE, SMEMBERS, and HGETALL are type-specific projections of the same namespace. KEYS, DBSIZE, TTL, and EXISTS are global projections over that namespace. EXPIRE affects TTL and live-key visibility. DEL and FLUSHDB remove state. Type mismatches (e.g., LPOP on a string key) must fail. Expired keys must be excluded from every live-key projection.

## Global Invariants

The following invariants define system correctness:

- The canonical fact source is the live key namespace: key name, type tag, value object, and optional expiry timestamp.
- Every derived view of that fact source must agree. KEYS, DBSIZE, EXISTS, TYPE, TTL, GET, LRANGE, SMEMBERS, and HGETALL must all reflect the same live/deleted/expired state after each command in a batch.
- A key's type is determined by the current live value. SET -> string; LPUSH/RPUSH -> list; SADD -> set; HSET -> hash.
- SET overwrites any previous value, type, and expiry for that key.
- Type-restricted operations must fail on keys of the wrong type and preserve the original value, type, key-listing visibility, DBSIZE contribution, and TTL.
- DEL must remove the key entirely from all projections; after DEL, the key name can be reused with a different type.
- LPUSH/RPUSH must preserve insertion order; LPOP/RPOP must remove and return elements in the correct order.
- SADD must deduplicate members; SMEMBERS must return unique members.
- HSET must store field-value pairs; HGET must retrieve them exactly.
- EXPIRE on a non-existent key must return 0 and not create the key.
- EXPIRE with zero or negative seconds must make the key immediately expired, so it is invisible to all reads and live-key projections that follow.
- TTL must return -2 for non-existent keys and -1 for keys without expiry.
- KEYS must exclude deleted and expired keys. DBSIZE must count only live, non-expired keys.
- FLUSHDB must remove all keys regardless of type and expiry.
- Failed commands, including wrong-type operations and invalid syntax, must be atomic across value contents, type metadata, key listing, DBSIZE, TTL, and later batch-visible reads.

## Data Model

A key can hold exactly one of four types:
- **string**: a text value created by SET.
- **list**: an ordered sequence of string elements created by LPUSH/RPUSH.
- **set**: an unordered collection of unique string members created by SADD.
- **hash**: a mapping of field names to string values created by HSET.

Timestamps for expiry are based on wall-clock time at second granularity. Expired keys should be lazily removed on access (GET, EXISTS, TYPE, LRANGE, SMEMBERS, HGET, etc.) and also excluded from KEYS and DBSIZE. A timeout of zero or less is an immediate expiry.

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
Set a timeout on a key. Return `1` if the timeout was set, `0` if the key does not exist. A timeout of zero or less expires the key immediately.

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

Failed commands must not corrupt existing key state, data structure contents, type metadata, key-listing visibility, DBSIZE contribution, TTL, or later batch-visible reads. Ordinary commands with no matching results (e.g., LRANGE of empty list returning `[]`, HGET of missing field returning `(nil)`, SISMEMBER returning `0`) should succeed with exit code 0.

## Non-Goals

- No network server or client protocol. This is a CLI-only tool.
- No sorted sets, streams, bitmaps, hyperloglogs, or geospatial types.
- No pub/sub, transactions (MULTI/EXEC), Lua scripting, or pipelining.
- No persistence (SAVE/LOAD/BGSAVE); batch mode keeps state only for the lifetime of one process.
- No automatic expiry eviction thread; lazy expiry on access is sufficient.
- No Redis serialization protocol (RESP) compatibility.

## Evaluation Style

Hidden tests are split into two scores:

- Unit tests exercise one feature module or one interface contract at a time. When a command needs existing key state, tests may set up state via direct command invocation within the same module. Shell-like quoting, glob argument parsing, command arity validation, and collection display syntax belong in this layer.
- System tests exercise interactions across at least two feature modules. They use otherwise valid commands, except for type-correctness failures, and assert projection consistency over one type-tagged key namespace after mixed SET/DEL/EXPIRE/LPUSH/SADD/HSET operations, wrong-type failures, immediate expiry, FLUSHDB, and later batch-visible reads. A system case should fail because KEYS, TYPE, value readers, TTL, DBSIZE, expiry, delete, wrong-type atomicity, or batch-visible state disagree, not merely because shell parsing, quoted arguments, arity validation, or output formatting is missing.

System tests are labeled by dimension:

- `projection_consistency`
- `global_invariant`
- `error_atomicity`
- `operation_order_sensitivity`
- `boundary_crossing`
