# MiniKV Unit/System Public Packet

## Overview

Build `minikv.py`, a compact in-memory key-value store with optional persistence. It should support the core workflows of a lightweight data store: set/get/delete string keys, bulk operations, integer counters, key expiry with TTL, key enumeration with glob patterns, and save/load persistence to disk.

This task is designed around the distinction between local feature correctness and system correctness. Individual commands should work on their own, but the product is only complete if key state, expiry, type metadata, persistence, and failure recovery remain consistent across multi-command workflows.

The implementation language is Python 3.11. Place `minikv.py` at the root of your solution directory. It must run as:

```console
py -3.11 minikv.py [--dbfile PATH] COMMAND [ARGS...]
```

The optional `--dbfile PATH` flag specifies a persistent database file. When omitted, the store is entirely in-memory with no persistence between runs. When provided, the store should automatically load existing data from the file on startup and save on each mutating command.

Data-returning commands must print results to stdout, one record per line where appropriate. JSON output must be compact single-line JSON. Failed commands must exit non-zero and print a useful message to stderr. The benchmark does not inspect private implementation details.

## Feature Set

The product has seven feature modules:

1. String key-value operations (SET, GET, EXISTS, DELETE).
2. Bulk operations (MSET, MGET).
3. Integer counter operations (INCR, DECR).
4. Key expiry (EXPIRE, TTL, PERSIST).
5. Key enumeration and metadata (KEYS, TYPE, DBSIZE).
6. Persistence (SAVE, LOAD, FLUSH).
7. Error and atomicity behavior.

These modules are intentionally state-dependent. Keys set by SET are later read by GET; TTL reflects prior EXPIRE calls; INCR depends on the current value type; KEYS and DBSIZE reflect the accumulated state; SAVE/LOAD/FLUSH affect all persisted state.

## Global Invariants

The following invariants define system correctness:

- GET after SET must return the exact value that was set (after INCR/DECR, the string representation of the updated integer).
- EXISTS must return 1 for keys that have been SET and not DELETEd or FLUSHed, and must return 0 after DELETE or FLUSH.
- INCR/DECR on a non-existent key must create it with value "0" before incrementing/decrementing.
- INCR/DECR on a key holding a non-integer string must fail and preserve the original value.
- EXPIRE on a non-existent key must return 0 and not create the key.
- TTL must return -2 for non-existent keys and -1 for keys without expiry.
- After EXPIRE seconds have elapsed, GET must return (nil) and EXISTS must return 0.
- PERSIST must remove expiry from an existing key; after PERSIST, TTL must return -1.
- SAVE must persist all current data to the specified file. LOAD must restore it exactly.
- FLUSH must remove all keys without affecting the db file (the file is only overwritten on the next mutating command or explicit SAVE).
- DBSIZE must reflect the exact number of currently live (non-expired) keys.
- TYPE must return "string" for SET/GET values and "integer" for INCR/DECR values.
- Failed commands must not corrupt existing key state, expiry, or persisted data.

## Data Model

The store holds keys mapping to (value, type, optional_expiry) tuples. Types are "string" or "integer". Integer values stored via INCR/DECR are internally integers but serialized as their string representation.

Timestamps for expiry are based on wall-clock time at second granularity. Expired keys should be lazily removed on access (GET, EXISTS) and also excluded from KEYS and DBSIZE.

## Commands

### `SET key value [EX seconds]`

Set a string key. With `EX`, the key expires after the given number of seconds. Always returns `OK`.

### `GET key`

Return the value of the key, or `(nil)` if it does not exist or has expired.

### `EXISTS key`

Return `1` if the key exists (and is not expired), `0` otherwise.

### `DELETE key [key...]`

Delete one or more keys. Return the number of keys that were actually removed (non-existent keys do not count).

### `MSET key1 value1 [key2 value2...]`

Set multiple string keys atomically. Always returns `OK`.

### `MGET key1 [key2...]`

Return the values of the requested keys as a compact JSON array. Non-existent or expired keys appear as `null` in the array.

### `INCR key`

Increment the integer value of a key by 1. If the key does not exist, set it to `0` before incrementing. Return the new integer value. Fail if the key holds a non-integer value.

### `DECR key`

Decrement the integer value of a key by 1. If the key does not exist, set it to `0` before decrementing. Return the new integer value. Fail if the key holds a non-integer value.

### `EXPIRE key seconds`

Set a timeout on key. Return `1` if the timeout was set, `0` if the key does not exist.

### `TTL key`

Return the remaining time to live in seconds. Return `-1` if the key exists but has no expiry. Return `-2` if the key does not exist or has expired.

### `PERSIST key`

Remove the expiry from a key. Return `1` if the expiry was removed, `0` if the key does not exist or has no expiry.

### `KEYS [pattern]`

Return matching keys as a compact JSON array. If `pattern` is omitted, return all keys. The pattern supports `*` (any characters) and `?` (single character) glob wildcards. Expired keys must be excluded.

### `TYPE key`

Return the type of the value stored at key: `"string"`, `"integer"`, or `"none"` if the key does not exist or has expired.

### `DBSIZE`

Return the number of currently live keys as an integer.

### `SAVE path`

Persist the current database to a JSON file at `path`. The format should be a JSON object. Returns `OK`.

### `LOAD path`

Replace the current database with the contents of a previously saved JSON file at `path`. Returns `OK`. Fail if the file does not exist or contains invalid data.

### `FLUSH`

Remove all keys from the current database. Always returns `OK`.

## Error Behavior

Invalid command syntax, missing required arguments, LOAD from a non-existent or malformed file, INCR/DECR on a non-integer value, and globally malformed values must fail with a non-zero exit code and useful stderr.

Failed commands must not corrupt existing key state, expiry, type metadata, or persisted data. Ordinary commands with no matching results (e.g., KEYS returning an empty list, GET returning nil, EXISTS returning 0) should succeed with exit code 0.

## Non-Goals

- No network server or client protocol is required. This is a CLI-only tool.
- No Redis protocol compatibility is required.
- No data structure types beyond string and integer (no lists, sets, hashes).
- No pub/sub, transactions, Lua scripting, or multi-threaded access.
- No automatic expiry eviction thread is required; lazy expiry on access is sufficient.
- No LRU/LFU eviction policies are required.

## Evaluation Style

Hidden tests are split into two scores:

- Unit tests exercise one feature module at a time. When a command needs existing key state, tests may set up state via direct command invocation of that same module rather than crossing module boundaries.
- System tests exercise interactions across at least two feature modules. They inspect stdout, stderr, JSON outputs, key state via subsequent GET/EXISTS/TYPE calls, expiry behavior after time delays, and failed-command atomicity.

System tests are labeled by dimension:

- `cross_feature_dataflow`
- `state_accumulation`
- `global_invariant`
- `error_atomicity`
- `operation_order_sensitivity`
- `boundary_crossing`
