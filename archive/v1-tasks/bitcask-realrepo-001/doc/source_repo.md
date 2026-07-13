# Source Repository

- Repository: `SarthakMakhija/bitcask`
- Local checkout: `benchmark/bitcask-main`
- Language of source: Go 1.20
- Reference paper: Riak's [bitcask](https://riak.com/assets/bitcask-intro.pdf)

## Source Signals

`bitcask` is an educational Go implementation of a disk-based, log-structured
hash-table key/value store. The README, `Tasks.md`, and the `kv`, `kv/log`,
`merge`, and `config` packages show a product surface spanning:

- `put`, `get`, `update`, and `delete` over an append-only data log
- an in-memory key directory (`map[Key]*Entry`) that maps each key to the
  `fileId`, `offset`, and `entryLength` of its latest record
- active-segment rollover once a size threshold is exceeded; closed segments are
  immutable and used only for reads
- merge / compaction (`merge/Worker.go`, `KVStore.WriteBack`) that reads
  inactive segments and writes back only the latest value of each live key,
  reclaiming the space taken by superseded records and tombstones
- state reload on start-up (`KVStore.reload`) that rebuilds the key directory by
  replaying the inactive segments — the durability path

Key observable behaviors in the source:

- `Update` is an append followed by an in-place key-directory update.
- `Delete` appends a tombstone and removes the key from the directory.
- `Get` returns an error for an absent key; `SilentGet` returns `(nil, false)`.
- The latest record for a key wins regardless of how many superseded copies
  remain in the log.

## Benchmark Adaptation

The candidate does not rebuild the full Go package, the goroutine-based merge
scheduler, generics, or the on-disk binary encoding. The benchmark asks for a
compact Python 3.11 CLI named `kvmini.py` that implements a useful subset of the
bitcask lifecycle: append-only writes, latest-value-wins reads, tombstone
deletes, metadata, and an explicit `compact` step, with all state persisted to a
directory so it survives across separate process invocations.

The missing-key behavior for `update` and `delete` is a deliberate public
mini-task CLI contract, not a hidden assumption about the Go repository. The PRD
defines these malformed state transitions as non-zero failures that append
nothing and preserve existing state, so the rubric can test error atomicity
through observable CLI behavior.

This case is promising because the output artifact is **durable on-disk state**,
not formatted command output. Correctness requires append-only logging, a
correct latest-record-wins reload, tombstone semantics that survive compaction,
and atomic failure handling. A model can implement each command in isolation and
still get the system wrong: the interesting failures appear when overwrite,
delete, compaction, and reload have to compose into one consistent final state.

## What Is Deliberately Out Of Scope

To keep the task self-contained and the scoring deterministic, the benchmark
does not require: concurrency / a background merge scheduler, hint files, range
queries, transactions, generic key types, or the source's exact binary record
encoding. The on-disk layout is the candidate's choice; only CLI-observable
behavior is scored.
