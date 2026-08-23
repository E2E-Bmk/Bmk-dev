# bbolt Transactional KV Reimplementation Specification

## Product Overview

`bbolt` is an embedded Go key/value database that stores a hierarchy of buckets in one local file and exposes fully serializable read-only and read-write transactions. The implementation must provide durable commit/rollback behavior, transaction snapshots, ordered cursors, nested buckets, sequences, backups, and the public lifecycle contracts described here without reproducing the reference B+tree, mmap, page, or freelist internals.

The module path must be `go.etcd.io/bbolt`; the primary package name is `bbolt`.

## Scope

The required surface covers public database, transaction, bucket, cursor, backup, persistence, and statistics behavior. Storage pages, mmap layout, freelists, command-line tools, and other excluded surfaces are listed under Non-Goals.

## Context and Orientation

### Core Concepts

A `DB` owns a single database file. A `Tx` is a consistent database view and is either read-only or writable. A `Bucket` belongs to one transaction and contains byte-slice keys mapped either to byte-slice values or nested buckets. A `Cursor` traverses one bucket in lexicographic byte order.

Only committed writable transactions modify durable state. Multiple read-only transactions must observe stable snapshots while a single writer prepares changes. Values returned by buckets and cursors are transaction-scoped; callers copy them when they need longer ownership.

## Representative Workflows

**Managed update and view.** A caller opens a database, uses `Update` to create buckets and write values, then uses `View` to read the committed state. Returning an error from an update callback rolls the entire transaction back and returns that error.

**Manual transaction.** A caller starts a transaction with `Begin`, mutates or reads through its buckets, and explicitly calls `Commit` or `Rollback`. Closing a transaction makes every later commit/rollback attempt fail with `ErrTxClosed`.

**Snapshot and persistence.** A read transaction continues to observe the state from its start even after a later writer commits. Closing and reopening the database preserves only committed buckets, values, and sequences.

**Ordered traversal and backup.** A caller scans keys through a cursor or `ForEach`, then copies a consistent transaction to a writer or file. The copied file must open independently with the copied snapshot.

## Behavior

### Database Lifecycle

`Open(path, mode, options)` must create a missing database file, open an existing valid database, acquire the database lock, and return a usable `DB`. Nil options use `DefaultOptions`. `Path` returns the opened path. `Close` flushes and releases resources; a second close succeeds as an idempotent no-op, while operations that require an open database return `ErrDatabaseNotOpen`.

`Options.Timeout` bounds waiting for a conflicting file lock and returns `ErrTimeout` when the bound expires. `Options.ReadOnly` opens an existing database without permitting writable transactions, and `IsReadOnly` reports that mode. `Options.NoSync`, `InitialMmapSize`, and `PageSize` must be accepted; acceptance tests do not inspect their storage implementation. `Sync` must make completed writes durable or return an error.

### Managed and Manual Transactions

`Update` starts a writable transaction, invokes its callback, commits on nil, and rolls back on a returned error or panic. The callback's returned error must be propagated. `View` starts a read-only transaction and always rolls it back after the callback; the callback error is propagated. A nil callback must return an error or panic consistently without committing state.

`Begin(true)` starts a writable transaction unless the database is read-only. `Begin(false)` starts a read-only transaction. `Writable`, `DB`, and `ID` report transaction properties. IDs must increase across committed writable transactions. `Commit` persists all staged changes atomically. `Rollback` discards them. Calling `Commit` on a read-only transaction returns `ErrTxNotWritable`; the caller must close it with `Rollback`.

Only one writable transaction is permitted to be active at a time. Independent read-only transactions are permitted to coexist. Objects obtained from a closed transaction must reject mutation and must not be used to infer durable changes.

`OnCommit` registers callbacks that run exactly once after a successful commit and never after rollback or failed commit. `Batch` must provide update semantics; its callback is permitted to be retried, so only the final successful invocation determines durable state.

### Bucket Lifecycle

Bucket names must be non-empty. `CreateBucket` creates a bucket and returns `ErrBucketExists` if a value or bucket already uses the name. `CreateBucketIfNotExists` returns the existing bucket or creates it. `Bucket` returns nil for an absent bucket. `DeleteBucket` removes the named bucket recursively and returns `ErrBucketNotFound` when absent.

Top-level bucket methods on `Tx` and nested bucket methods on `Bucket` follow the same lifecycle rules. `Tx.ForEach` enumerates every top-level bucket once. `Bucket.ForEachBucket` enumerates every direct nested bucket once. `Bucket.Tx` and `Bucket.Writable` agree with the owning transaction.

A key cannot simultaneously hold a value and a nested bucket. Attempts to put a value at a bucket key, create a bucket at a value key, or delete a bucket through value deletion return `ErrIncompatibleValue` where the public method returns an error.

### Key/Value Operations

`Put` stores or replaces a value in a writable bucket. Empty keys return `ErrKeyRequired`. Nil and zero-length values are stored as present empty byte slices. `Get` returns the current value or nil for an absent key. `Delete` removes a value, succeeds when an ordinary key is absent, and rejects read-only mutation with `ErrTxNotWritable`.

Writes within a transaction are immediately visible through that transaction's `Get`, `ForEach`, and cursors. They are invisible to pre-existing read snapshots and become visible to new transactions only after commit. Rollback removes every staged mutation across all involved buckets.

Keys and values are arbitrary byte slices. Ordering comparisons use raw lexicographic byte order. Tests copy values before a transaction closes and do not require returned slices to remain valid afterward.

### Cursor and Enumeration

`First` and `Last` position at the smallest and largest key. `Next` and `Prev` move one key in their respective direction. Passing the boundary returns `(nil, nil)`. `Seek(target)` positions at the first key greater than or equal to the target, or returns nil at the end. Cursor results include values and nested-bucket entries; a nested bucket is represented by a non-nil key and nil value.

`Cursor.Delete` deletes the current value in a writable transaction, returns `ErrTxNotWritable` for a read-only cursor, and returns `ErrIncompatibleValue` when positioned on a nested bucket. `Bucket.ForEach` visits keys in byte-sorted order, including nested bucket keys with nil values, and stops by returning the callback's first error.

### Nested Buckets and Sequences

Nested buckets support values and further nested buckets. Committing or rolling back a transaction applies to the entire hierarchy atomically. Deleting a parent removes every descendant.

Each bucket has an unsigned sequence. `Sequence` returns it, `SetSequence` replaces it in a writable transaction, and `NextSequence` increments then returns it. Sequence mutations commit and roll back with other bucket state and survive close/reopen. Sequence operations on read-only buckets return `ErrTxNotWritable` where an error is returned.

### Snapshot Isolation

A read-only transaction must continue returning the values and bucket hierarchy visible at its start while a later writer commits replacements, additions, or deletions. A new read transaction must observe the committed writer state. An uncommitted writer is invisible to other transactions.

### Copy and Reopen

`Tx.WriteTo` and `Tx.Copy` write a consistent, reopenable database snapshot to an `io.Writer`; `CopyFile` writes the same logical snapshot to a path with the requested mode. Copying from a read transaction must not include later commits. A copied database is independent: later source mutations do not modify it.

Closing and reopening the original database must preserve committed top-level and nested buckets, key/value bytes, and bucket sequences. Rolled-back and callback-error changes must remain absent.

### Statistics

`Bucket.Stats().KeyN` must reflect the number of direct key/value entries plus nested-bucket entries observable by iteration, and `BucketN` must include the bucket and its descendants. `DB.Stats().TxN` increases as read transactions begin and `OpenTxN` reflects currently open read transactions. `Stats.Sub` returns counter differences for transaction counters while retaining current freelist gauges. When `NoStatistics` is true, zero statistics are acceptable.

Acceptance does not require exact page counts, allocation bytes, timings, addresses, or file sizes.

## Contract

## State Model

The durable database state is the latest successful writable commit. A transaction transitions from open to committed or rolled back exactly once. Buckets and cursors derive their validity and writability from their owning open transaction.

## Error Semantics

The sentinel errors listed in the public interface must support `errors.Is`. Required conditions are: database closed (`ErrDatabaseNotOpen`), lock timeout (`ErrTimeout`), mutation in a read-only transaction (`ErrTxNotWritable`), repeated transaction close (`ErrTxClosed`), writable begin on a read-only database (`ErrDatabaseReadOnly`), missing/existing/blank buckets (`ErrBucketNotFound`, `ErrBucketExists`, and `ErrBucketNameRequired`), blank keys (`ErrKeyRequired`), and key/bucket type conflicts (`ErrIncompatibleValue`).

Callback errors from `Update`, `View`, `Batch`, `ForEach`, and bucket enumeration must be returned without message rewriting. Failed managed updates and failed manual commits must not expose partial durable state.

## Cross-View Invariants

- `Get`, `ForEach`, and cursor traversal within one transaction must agree on every visible key/value pair.
- Managed and manual transactions must produce the same durable state for equivalent successful mutations.
- A bucket's sequence, iteration view, and statistics must describe the same committed bucket state after reopen.
- A transaction backup and the source transaction must expose the same bucket hierarchy and values at copy time.
- Read snapshot stability must coexist with visibility of later commits to newly opened transactions.

### Concurrency and Isolation

`DB` transaction creation must be safe for concurrent use. Acceptance tests run independent readers concurrently and coordinate one writer with readers. A single `Tx`, `Bucket`, or `Cursor` is not required to support concurrent method calls. Tests avoid timing-sensitive throughput and randomized stress.

## Public Interface

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Open`, `Options`, `DefaultOptions` | constructor/configuration | Open and configure a database file. |
| `DB` | type | Owns lifecycle, managed transactions, sync, and database statistics. |
| `Tx` | type | Provides a read snapshot or staged writable transaction. |
| `Bucket` | type | Stores values, nested buckets, a sequence, and ordered traversal. |
| `Cursor` | type | Traverses and deletes ordered entries. |
| `Stats`, `TxStats`, `BucketStats`, `Info` | types | Expose stable public database projections. |
| documented `Err*` variables | variables | Identify lifecycle, transaction, bucket, key, and lock failures. |

### CLI Entry Points

There is no console script or command-line entry point required by this specification.

### Dependencies

The implementation must use the Go standard library only. The submitted `go.mod` must declare module `go.etcd.io/bbolt` and must not require the pinned reference module or another embedded database implementation.

## Reference and Acceptance

### Acceptance Basis

Acceptance tests use temporary local files and the public surface above. They compare values, errors with `errors.Is`, transaction-visible states, ordering, snapshot behavior, copied databases, and stable statistic relationships. They do not inspect pages, mmap regions, fre​​elists, private fields, exact error text, or timing performance.

### Compatibility Target

The behavioral reference is `etcd-io/bbolt` at commit `28382919c46fc32af9c5ed532bd67b64c21cee76`. Where this specification narrows the upstream project, this document is authoritative.

## Meta

## Non-Goals

- This specification does not require reproducing B+tree pages, mmap management, freelists, checksums, spill/rebalance algorithms, or file bytes.
- This specification does not require the `bbolt` CLI, compact/check/inspect/page APIs, custom logging, failpoints, crash injection, or raw database repair.
- This specification does not require exact performance, allocation, file-size, timing, or page-statistic equivalence.
- This specification does not define cross-process behavior beyond documented lock timeout and read-only opening.
- This specification does not require platform-specific permission, mlock, endian, filesystem, or long randomized stress behavior.

### Implementation Freedom

Any durable representation and transaction mechanism is acceptable when it satisfies the public signatures and observable contracts. The candidate does not need to use mmap or a B+tree.

## Environment

The submission must be a Go module with module path `go.etcd.io/bbolt`. It must build and test offline on Linux with the configured Go toolchain and may use only the Go standard library.

## Assessment Notes

Acceptance checks exercise only the documented public surface and compare observable values, error identity, transaction state, ordering, persistence, backups, and stable statistics relationships. Private storage representation and exact diagnostic wording are outside the contract.

## Appendix A — Required Go Signatures

```go
func Open(path string, mode os.FileMode, options *Options) (*DB, error)
func (db *DB) Path() string
func (db *DB) Close() error
func (db *DB) Begin(writable bool) (*Tx, error)
func (db *DB) Update(func(*Tx) error) error
func (db *DB) View(func(*Tx) error) error
func (db *DB) Batch(func(*Tx) error) error
func (db *DB) Sync() error
func (db *DB) Stats() Stats
func (db *DB) Info() *Info
func (db *DB) IsReadOnly() bool

func (tx *Tx) ID() int
func (tx *Tx) DB() *DB
func (tx *Tx) Size() int64
func (tx *Tx) Writable() bool
func (tx *Tx) Cursor() *Cursor
func (tx *Tx) Stats() TxStats
func (tx *Tx) Bucket([]byte) *Bucket
func (tx *Tx) CreateBucket([]byte) (*Bucket, error)
func (tx *Tx) CreateBucketIfNotExists([]byte) (*Bucket, error)
func (tx *Tx) DeleteBucket([]byte) error
func (tx *Tx) ForEach(func([]byte, *Bucket) error) error
func (tx *Tx) OnCommit(func())
func (tx *Tx) Commit() error
func (tx *Tx) Rollback() error
func (tx *Tx) Copy(io.Writer) error
func (tx *Tx) WriteTo(io.Writer) (int64, error)
func (tx *Tx) CopyFile(string, os.FileMode) error

func (b *Bucket) Tx() *Tx
func (b *Bucket) Writable() bool
func (b *Bucket) Cursor() *Cursor
func (b *Bucket) Bucket([]byte) *Bucket
func (b *Bucket) CreateBucket([]byte) (*Bucket, error)
func (b *Bucket) CreateBucketIfNotExists([]byte) (*Bucket, error)
func (b *Bucket) DeleteBucket([]byte) error
func (b *Bucket) Get([]byte) []byte
func (b *Bucket) Put([]byte, []byte) error
func (b *Bucket) Delete([]byte) error
func (b *Bucket) Sequence() uint64
func (b *Bucket) SetSequence(uint64) error
func (b *Bucket) NextSequence() (uint64, error)
func (b *Bucket) ForEach(func([]byte, []byte) error) error
func (b *Bucket) ForEachBucket(func([]byte) error) error
func (b *Bucket) Stats() BucketStats

func (c *Cursor) Bucket() *Bucket
func (c *Cursor) First() ([]byte, []byte)
func (c *Cursor) Last() ([]byte, []byte)
func (c *Cursor) Next() ([]byte, []byte)
func (c *Cursor) Prev() ([]byte, []byte)
func (c *Cursor) Seek([]byte) ([]byte, []byte)
func (c *Cursor) Delete() error
```
