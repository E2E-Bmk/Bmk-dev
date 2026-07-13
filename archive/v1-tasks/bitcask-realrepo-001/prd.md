# MiniBitcask KV Store — Unit/System Public Packet

## Overview

Build `kvmini.py`, a compact disk-backed key/value store. It writes key/value
records to an append-only log directory, reads back the latest value of each
key, deletes keys with tombstones, reports database state, and reclaims space
with an explicit compaction step.

This task is designed around the distinction between local feature correctness
and system correctness. Individual commands should work on their own, but the
product is only complete if values, deletions, metadata, and reclaimed state
remain consistent across multi-command workflows **and across separate process
invocations**, because the store is durable on disk.

The implementation language is Python 3.11. Place `kvmini.py` at the root of your
solution directory. It must run as:

```console
py -3.11 kvmini.py DBDIR COMMAND [ARGS...]
```

`DBDIR` is a directory that holds the store's append-only segment files. Each
invocation opens the store, reloads its state from `DBDIR`, performs one command,
persists any change, and exits. Use only the Python standard library. Mutation
commands may print a short success message. Data-returning commands must print
compact JSON to stdout, except `get` (raw value) and `count` (integer).

## Feature Set

The product has seven feature modules:

1. `put` / `update`
2. `get` / `mget`
3. `delete`
4. `keys` / `count` / `list`
5. `stats`
6. `compact`
7. error, atomicity, and durability behavior

These modules are intentionally state-dependent. Records written by `put` are
read by `get`, changed by `update`, removed by `delete`, summarized by `keys`,
`count`, `list`, and `stats`, and rewritten by `compact`. All of them must agree
on what the current live state is after any sequence of commands.

## Global Invariants

The following invariants define system correctness:

- The value returned for a key is always the value of its most recent successful
  `put` or `update`, regardless of how many superseded records remain on disk.
- A `delete`d key stays deleted until it is `put` again. Compaction must never
  resurrect a deleted key.
- A key re-created after deletion exists again with its new value.
- `keys`, `count`, and `list` reflect exactly the current live key set.
- `compact` preserves the latest value of every live key and removes tombstones
  and superseded records; it must not change any observable value.
- All committed state survives across separate invocations (durability): a value
  written by one process is readable by the next.
- A command that fails must append nothing and leave existing state unchanged.

## Commands

### `put KEY VALUE`

Store `VALUE` under `KEY`, overwriting any existing value. Always succeeds for a
well-formed call. Appends one record.

### `update KEY VALUE`

Set `KEY` to `VALUE`, but only if `KEY` already exists. If `KEY` does not exist,
fail non-zero and append nothing.

### `get KEY`

Print the current value of `KEY` as a raw string followed by a newline. If `KEY`
does not exist, fail non-zero.

### `mget KEY [KEY...]`

Print a compact JSON object mapping each requested key that exists to its value.
Missing keys are omitted (not included as null).

### `delete KEY`

Delete `KEY` (append a tombstone). If `KEY` does not exist, fail non-zero and
append nothing.

### `keys`

Print a compact JSON array of the live keys, sorted lexicographically.

### `count`

Print the number of live keys as a bare integer.

### `list`

Print a compact JSON object mapping every live key to its value.

### `stats`

Print a compact JSON object with exactly:

- `live_keys`: the number of live keys.
- `log_entries`: the number of physical records currently persisted on disk,
  including superseded versions and tombstones that have not yet been compacted.

`log_entries` is the product's own reported measure of reclaimable space; it must
drop after a successful `compact`.

### `compact`

Rewrite the log so that only the latest value of each live key remains and all
tombstones and superseded records are discarded. After `compact`, every value
returned by `get`, `mget`, `list`, `keys`, and `count` must be unchanged, and
`stats.log_entries` must equal `stats.live_keys`.

## Durability And Storage

`DBDIR` is the durable home of the store. Writes are append-only: a command must
not rewrite or truncate existing records except during `compact`. When the active
segment grows past a size threshold, start a new segment; closed segments are
immutable. On open, the store rebuilds its live state by replaying records in
write order, with the latest record for a key winning and tombstones removing the
key.

The on-disk format, segment file naming, and threshold are the candidate's
choice and are not inspected by the benchmark. The optional environment variable
`KVMINI_MAX_SEGMENT_BYTES` may set the rollover threshold; behavior must be
identical regardless of how many segments the data spans.

## Error Behavior

These must fail non-zero with a useful stderr message and append nothing:
`update` or `get` on a missing key, `delete` on a missing key, and malformed
command lines. A failed command must not corrupt existing records, lose committed
data, or change `stats.log_entries`.

## Non-Goals

- No concurrency or background merge scheduler.
- No hint files.
- No range queries.
- No transactions.
- No generic key types; keys and values are UTF-8 strings.
- No network or remote replication.

## Evaluation Style

Hidden tests are split into two scores:

- Unit tests exercise one feature module at a time. When a command needs existing
  store state, tests set up that state through the same public CLI commands a
  user would run.
- System tests exercise interactions across at least two feature modules. They
  inspect final values, the live key set, metadata, compaction results, and
  durability across invocations, plus atomic failure behavior.

System tests are labeled by dimension:

- `cross_feature_dataflow`
- `state_accumulation`
- `global_invariant`
- `error_atomicity`
- `operation_order_sensitivity`
- `boundary_crossing`
- `durability_reload`

The benchmark does not inspect private implementation details (file layout,
encoding, segment counts); it observes only CLI output and exit codes.
