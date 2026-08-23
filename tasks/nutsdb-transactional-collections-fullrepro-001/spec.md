# NutsDB Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`nutsdb` is an embedded, directory-backed database that organizes byte keys and values into typed buckets and changes them through serializable transactions. The same committed state is observable through direct key/value reads, ordered scans and iterators, list/set/sorted-set operations, watch callbacks, reopened databases, backups, and post-merge state.

The Go package is imported from `github.com/nutsdb/nutsdb`. Every workflow uses local files and requires no external service.

## Non-Goals

- This specification does not require HTTP servers, network protocols, remote storage, replication, or distributed coordination.
- This specification does not require compatibility with Redis commands or any external database wire format.
- This specification does not require low-level entry encoding, metadata CRCs, data-file managers, hint-file formats, merge manifests, recovery readers, index nodes, skip-list internals, or bucket-manager internals.
- This specification does not require write batches, compressed backup archives, bit operations, integer increments, raw list writes, list TTLs, random set pops, cross-bucket set algebra, or key-enumeration helpers for collections.
- This specification does not require exact error text, logging text, filesystem filenames, segment byte layout, file-descriptor cache behavior, mmap behavior, or timing measurements.
- This specification does not define ordering for set members or sorted-set members whose scores are equal.
- This specification does not require a command-line executable.

## Representative Workflows

### Commit, inspect, and reopen key/value state

```go
opts := nutsdb.DefaultOptions
db, _ := nutsdb.Open(opts, nutsdb.WithDir(dir))
_ = db.Update(func(tx *nutsdb.Tx) error {
    if err := tx.NewKVBucket("accounts"); err != nil {
        return err
    }
    return tx.Put("accounts", []byte("alice"), []byte("active"), nutsdb.Persistent)
})
_ = db.Close()

later, _ := nutsdb.Open(opts, nutsdb.WithDir(dir))
defer later.Close()
_ = later.View(func(tx *nutsdb.Tx) error {
    value, err := tx.Get("accounts", []byte("alice"))
    _, _ = value, err
    return err
})
```

A successful managed update creates the bucket and entry atomically. Reopening the same directory exposes the committed value; returning an error from the update leaves neither change visible.

### Use collection projections in one transaction

```go
_ = db.Update(func(tx *nutsdb.Tx) error {
    _ = tx.NewListBucket("queues")
    _ = tx.NewSetBucket("labels")
    _ = tx.NewSortSetBucket("ranking")
    _ = tx.RPush("queues", []byte("jobs"), []byte("a"), []byte("b"))
    _ = tx.SAdd("labels", []byte("ready"), []byte("a"), []byte("b"))
    return tx.ZAdd("ranking", []byte("scores"), 10, []byte("a"))
})
```

The list preserves position, the set preserves distinct membership, and the sorted set preserves member scores and rank. Their transaction outcome agrees with later read transactions and reopened database state.

### Observe a committed change

```go
opts := nutsdb.DefaultOptions
opts.EnableWatch = true
db, _ := nutsdb.Open(opts, nutsdb.WithDir(dir))

go func() {
    _ = db.Watch("events", []byte("job"), func(m *nutsdb.Message) error {
        observed <- m
        return stopWatching
    })
}()
```

After the subscription is active, a committed write for the selected bucket and key produces a callback message. A rolled-back write produces no message.

## Database Lifecycle and Transactions

Database construction and transaction boundaries determine which changes become durable and visible to every other projection.

**Opening and closing.**

When `Open` receives an `Options` value plus functional options, the database must apply the functional options after the base value and use the resulting `Dir` as its local storage directory.

When the selected directory does not contain a database, `Open` must create the directory and an empty usable database.

When the selected directory is already locked by an open database, `Open` must return an error matching `ErrDirLocked`.

When `Close` succeeds, `IsClose` must return true and later database operations must return an error matching `ErrDBClosed`.

If `Close` is called on an already closed database, then it must return an error matching `ErrDBClosed`.

**Managed transactions.**

When an `Update` callback returns nil, the database must atomically commit the callback's bucket and entry changes.

When an `Update` callback returns an error, the database must return that error and must discard every change made by that callback.

If `Update` or `View` receives a nil callback, then it must return an error matching `ErrFn`.

While a `View` callback is running, reads must observe the latest committed state.

If a write method is called through a read-only transaction, then it must return an error matching `ErrTxNotWritable` and leave state unchanged.

**Manual transactions.**

When `Begin(true)` returns a manual transaction, `Commit` must publish all staged changes and `Rollback` must publish none of them.

When `Begin(false)` returns a manual transaction, `Commit` or `Rollback` must close it without changing database state.

If `Commit` or `Rollback` is called after the same transaction has closed, then it must return a closed-transaction error.


The retained functional options are `WithDir`, `WithSegmentSize`, `WithRWMode`, `WithSyncEnable`, `WithEntryIdxMode`, `WithEnableMergeV2`, and `WithListImpl`. Watch support is enabled by setting the exported `Options.EnableWatch` field before calling `Open`. The assessment uses `FileIO`; `MMap` remains public vocabulary but no mmap-specific behavior is required.

## Buckets, Key/Value Data, and Ordered Reads

Typed buckets provide namespaces for transactional data, while scans and iterators expose deterministic key order.

**Bucket lifecycle.**

When `NewBucket` receives one of the four retained `DataStructure` constants and a non-empty name, the transaction must create that typed bucket on commit.

When `NewKVBucket`, `NewListBucket`, `NewSetBucket`, or `NewSortSetBucket` succeeds, `ExistBucket` must report the corresponding bucket kind.

If a transaction creates a bucket whose kind and name already exist, then it must return an error matching `ErrBucketAlreadyExist`.

When `DeleteBucket` commits, bucket enumeration and later operations must no longer expose that bucket or its entries.

When `IterateBuckets` receives a pattern, it must call the callback for matching bucket names and must stop when the callback returns false.

**Key/value mutation.**

When `Put` writes a non-empty key in an existing key/value bucket, `Get` must return the latest committed byte value.

When `Delete` commits, `Has` must return false and `Get` must return an error matching `ErrKeyNotFound`.

If a key is empty, then write operations must return an error matching `ErrKeyEmpty` and leave the bucket unchanged.

If a referenced bucket does not exist, then direct entry operations must return an error matching `ErrNotFoundBucket`, while bucket lifecycle and TTL operations must return an error matching `ErrBucketNotFound`.

When `PutIfNotExists` receives a missing key, it must write the value, and when it receives an existing key, it must preserve the existing value.

When `PutIfExists` receives an existing key, it must replace the value, and when it receives a missing key, it must return an error matching `ErrKeyNotFound` and leave the bucket without that key.

When `MSet` receives alternating key and value arguments, it must stage all pairs with the supplied TTL as one transaction change.

If `MSet` receives an odd number of key/value arguments, then it must return an error matching `ErrKVArgsLenNotEven` and write none of the pairs.

When `MGet` receives keys, it must return values in the same order as the requested keys or return the relevant missing-key error.

When `GetSet` succeeds, it must return the previous value and stage the replacement value.

When `Append` succeeds, later reads must return the previous bytes followed by the appended bytes, and `ValueLen` must return the resulting byte length.

When `GetAll`, `GetKeys`, or `GetValues` succeeds, the returned key and value projections must describe the same committed entries in byte-sorted key order.

When a bucket is non-empty, `GetMinKey` and `GetMaxKey` must return its lowest and highest keys under the configured ordering.

**Scans and iterators.**

When `PrefixScan` succeeds, it must return values for matching keys in key order after applying `offsetNum` and the `limitNum` cap, where `ScanNoLimit` means no cap.

When `PrefixSearchScan` receives a regular expression, it must filter the suffix after the requested prefix before applying offset and limit.

When `RangeScan` succeeds, it must return values whose keys lie in the closed byte-order interval from `start` through `end`.

If a prefix or range query has no matching entry, then it must return its documented scan sentinel instead of a successful non-empty result.

When `NewIterator` receives an existing key/value bucket, it must position a forward iterator at the first key and a reverse iterator at the last key.

While an iterator is valid, `Key` and `Value` must project the same entry, and `Next` must move in the configured direction.

When `Seek` receives a key, the iterator must position at the first key not less than it, after which `Next` must continue in the configured direction.

When `Rewind` is called, the iterator must return to the first position in its configured direction.

When iteration is complete, `Valid` must return false, and `Release` must make later iterator use invalid.

**Expiration.**

When `Put` receives `Persistent`, `GetTTL` must return minus one while the key exists.

When `Put` receives a positive TTL, the key must remain readable before expiration and must become missing after expiration.

When `Persist` succeeds for an expiring key, `GetTTL` must return minus one and the key must survive its former expiration time.


`IteratorOptions.Reverse` selects the direction. `SortedSetMember` is not used by key/value iterators; iterator values are returned through `Value`.

## Lists, Sets, and Sorted Sets

Collection buckets share the transaction lifecycle while preserving different public ordering and membership rules.

**Lists.**

When list values are pushed at the left or right, `LRange` must expose their resulting order using inclusive zero-based indices and negative indices counted from the tail.

When `LPop` or `RPop` succeeds, it must return and remove the head or tail value, and `LSize` must reflect the removal.

When `LPeek` or `RPeek` succeeds, it must return the head or tail value without changing `LSize`.

When `LTrim` commits, only the selected inclusive range must remain.

When `LRem` receives a positive count it must remove matching values from head to tail, when it receives a negative count it must remove from tail to head, and when it receives zero it must remove every match.

Where either retained list implementation is selected, public list results and persistence behavior must remain equivalent.

**Sets.**

When `SAdd` receives duplicate members, the set must retain each distinct byte value once and `SCard` must report the distinct count.

When `SIsMember` and `SMembers` inspect a set, their membership projections must agree without requiring an iteration order.

When `SRem` commits, removed members must disappear and unrelated members must remain.

When `SUnionByOneBucket` or `SDiffByOneBucket` succeeds, it must return the mathematical union or left-minus-right difference of the two named set keys.

When `SMoveByOneBucket` succeeds, the member must leave the source set and appear in the destination set atomically.

**Sorted sets.**

When `ZAdd` writes a new member, `ZScore` must return its score and `ZCard` must count it once.

When `ZAdd` writes an existing member with a new score, it must update that member instead of increasing cardinality.

When scores are distinct, `ZRank` must return one-based ascending rank and `ZRevRank` must return one-based descending rank.

When `ZRangeByRank` succeeds, it must return `SortedSetMember` values in ascending score order for the inclusive one-based rank interval, with minus one denoting the last rank.

When `ZRangeByScore` or `ZCount` receives nil options, it must use the closed score interval without a result limit.

Where `GetByScoreRangeOptions` is present, `ExcludeStart`, `ExcludeEnd`, and a positive `Limit` must control endpoint inclusion and maximum result count.

When `ZPeekMin` or `ZPeekMax` succeeds, it must return the boundary member without removing it, while `ZPopMin` or `ZPopMax` must return and remove that member.

When `ZRem` commits, score, rank, range, and cardinality projections must all omit the removed member.


`SortedSetMember` exposes `Value` and `Score`. `GetByScoreRangeOptions` exposes `Limit`, `ExcludeStart`, and `ExcludeEnd`.

## Durability, Backup, Merge, and Watch Events

Durability operations and event subscriptions project committed logical state beyond one transaction or process lifetime.

**Reopen, backup, and merge.**

When a database closes after successful commits, reopening the same directory with compatible options must restore buckets, key/value entries, collections, and unexpired TTL state.

When `Backup` succeeds, opening the backup directory must expose the same committed logical state that existed when the read-only backup transaction began.

If fewer than two data segments are eligible, then `Merge` must return an error matching `ErrDontNeedMerge`.

Where `WithEnableMergeV2(true)` is present, when `Merge` succeeds, every live public projection must remain unchanged and deleted, replaced, or expired values must not reappear after close and reopen.

**Watch lifecycle.**

If watch support is disabled, then `Watch` must return an error matching `ErrWatchFeatureDisabled`.

Where watch support is enabled, `Watch` must deliver committed set and delete events for the subscribed bucket and key to the callback.

When a watched transaction rolls back, the callback must receive no event for its staged writes.

When a set event is delivered, `Message.BucketName`, `Key`, `Value`, `Flag`, and `Timestamp` must identify the committed change, and the flag must equal `DataSetFlag`.

When a delete event is delivered, its bucket and key must identify the deleted entry and its flag must equal `DataDeleteFlag`.

If a callback exceeds `WatchOptions.CallbackTimeout`, then `Watch` must return an error matching `ErrWatchingCallbackTimeout`.

When the callback returns an error, `Watch` must return that error and stop the subscription.

When the database closes, active `Watch` calls must finish and release their subscriptions.


`NewWatchOptions` returns options with `CallbackTimeout` set to `DefaultCallbackTimeout`, and `WithCallbackTimeout` replaces that value.

## State Model

The core state is a directory-backed sequence of committed transactions. Each live entry belongs to a typed bucket and has key/value or collection semantics plus optional expiration.

The public projections are:

- Transaction results through `Update`, `View`, `Begin`, `Commit`, and `Rollback`.
- Bucket and direct data views through existence checks, key/value methods, collection methods, scans, and iterators.
- Lifecycle views through `IsClose`, close/reopen recovery, `Backup`, and `Merge`.
- Event views through `Watch` and public `Message` fields.
- Error-category views through exported sentinel errors and classifier helpers.

## Error Semantics

| Condition | Required result |
|---|---|
| Storage directory is locked | Return an error matching `ErrDirLocked` |
| Database is closed | Return an error matching `ErrDBClosed`; `IsDBClosed` returns true |
| Managed callback is nil | Return an error matching `ErrFn` |
| Write through read-only transaction | Return an error matching `ErrTxNotWritable` |
| Transaction already closed | Return a closed-transaction error |
| Bucket name is empty | Return an error matching `ErrBucketEmpty` |
| Duplicate typed bucket | Return an error matching `ErrBucketAlreadyExist` |
| Bucket is missing in bucket lifecycle or TTL operations | Return an error matching `ErrBucketNotFound`; `IsBucketNotFound` returns true |
| Bucket is missing in direct entry operations | Return an error matching `ErrNotFoundBucket` |
| Key is empty | Return an error matching `ErrKeyEmpty`; `IsKeyEmpty` returns true |
| Key is missing | Return an error matching `ErrKeyNotFound`; `IsKeyNotFound` returns true |
| Prefix scan has no result | Return an error matching `ErrPrefixScan`; `IsPrefixScan` returns true |
| Range scan has no result | Return an error matching `ErrRangeScan` |
| List is missing or empty | Return `ErrListNotFound` or `ErrEmptyList` for the corresponding condition |
| Set is missing | Return an error matching `ErrSetNotExist` |
| Sorted set or member is missing | Return `ErrSortedSetNotFound` or `ErrSortedSetMemberNotExist` for the corresponding condition |
| Watch support is disabled | Return an error matching `ErrWatchFeatureDisabled` |
| Watch callback exceeds timeout | Return an error matching `ErrWatchingCallbackTimeout` |
| Too few data segments are mergeable | Return an error matching `ErrDontNeedMerge` |

## Cross-View Invariants

1. A committed key/value write must agree across `Get`, `Has`, `GetAll`, scans, an iterator, and close/reopen state.
2. A rolled-back transaction must remain absent from direct reads, collection views, reopened state, backups, and watch callbacks.
3. Bucket creation or deletion must agree across `ExistBucket`, `IterateBuckets`, entry operations, and reopened state.
4. TTL status returned by `GetTTL` must agree with readability before expiration, missing-key behavior after expiration, and reopened state.
5. List order returned by `LRange` must agree with peek/pop operations and both retained list implementations.
6. Set membership returned by `SMembers` must agree with `SCard`, `SIsMember`, union, difference, move, and reopened state.
7. Sorted-set members and scores must agree across score lookup, rank, score ranges, boundary peek/pop, cardinality, and reopened state.
8. A successful backup must expose the same committed bucket, key/value, and collection projections when opened independently.
9. A successful merge must preserve every live logical projection before and after close/reopen while keeping deleted and expired entries absent.
10. A committed watched write must agree with the callback message and the value read from a later transaction.
11. Closing a database must agree with `IsClose`, operation errors, directory-lock release, and the completion of active watchers.

## Public Interface

### Import Surface

```go
import "github.com/nutsdb/nutsdb"
```

The retained exported identifiers are listed in the API catalog.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Open` | function | Open or create a local database |
| `DB` | type | Coordinate transactions, durability, and watches |
| `Options` | type | Hold database configuration |
| `Option` | type | Apply a construction override |
| `DefaultOptions` | variable | Provide the default option value |
| `WithDir` | function | Select the storage directory |
| `WithSegmentSize` | function | Select the data segment capacity |
| `WithRWMode` | function | Select standard I/O or mmap mode |
| `WithSyncEnable` | function | Select commit syncing |
| `WithEntryIdxMode` | function | Select a public entry-index mode |
| `Options.EnableWatch` | field | Enable or disable watch support before `Open` |
| `WithEnableMergeV2` | function | Enable or disable the merge-v2 lifecycle |
| `WithListImpl` | function | Select a list implementation |
| `EntryIdxMode` | type | Identify an entry-index mode |
| `HintKeyValAndRAMIdxMode` | constant | Select in-memory key and value indexing |
| `HintKeyAndRAMIdxMode` | constant | Select in-memory key-only indexing |
| `RWMode` | type | Identify a file access mode |
| `FileIO` | constant | Select standard file I/O |
| `MMap` | constant | Select memory-mapped I/O |
| `ListImplementationType` | type | Identify a list implementation |
| `ListImplDoublyLinkedList` | constant | Select linked-list behavior |
| `ListImplBTree` | constant | Select tree-backed list behavior |
| `Tx` | type | Represent a read-only or writable transaction |
| `DataStructure` | type | Identify a bucket kind |
| `DataStructureBTree` | constant | Identify key/value buckets |
| `DataStructureList` | constant | Identify list buckets |
| `DataStructureSet` | constant | Identify set buckets |
| `DataStructureSortedSet` | constant | Identify sorted-set buckets |
| `Iterator` | type | Traverse one key/value bucket |
| `IteratorOptions` | type | Select iterator direction |
| `NewIterator` | function | Construct an iterator for a transaction and bucket |
| `Persistent` | constant | Select no expiration |
| `ScanNoLimit` | constant | Select an unlimited scan |
| `SortedSetMember` | type | Return one sorted-set value and score |
| `GetByScoreRangeOptions` | type | Configure score interval endpoints and limit |
| `Message` | type | Describe one watched committed change |
| `WatchOptions` | type | Configure callback timeout |
| `NewWatchOptions` | function | Construct default watch options |
| `DataFlag` | type | Identify a watched operation |
| `DataSetFlag` | constant | Identify a set operation |
| `DataDeleteFlag` | constant | Identify a delete operation |
| `DefaultCallbackTimeout` | constant | Provide the default watch callback limit |
| `ErrDBClosed` | error variable | Classify closed-database failures |
| `ErrDirLocked` | error variable | Classify locked-directory failures |
| `ErrFn` | error variable | Classify missing managed callbacks |
| `ErrTxClosed` | error variable | Classify operations on closed transactions |
| `ErrTxNotWritable` | error variable | Classify writes through read-only transactions |
| `ErrBucketEmpty` | error variable | Classify empty bucket names |
| `ErrBucketAlreadyExist` | error variable | Classify duplicate bucket creation |
| `ErrBucketNotFound` | error variable | Classify missing buckets in lifecycle and TTL operations |
| `ErrNotFoundBucket` | error variable | Classify missing buckets in direct entry operations |
| `ErrKeyEmpty` | error variable | Classify empty keys |
| `ErrKeyNotFound` | error variable | Classify missing keys |
| `ErrRangeScan` | error variable | Classify empty range scans |
| `ErrPrefixScan` | error variable | Classify empty prefix scans |
| `ErrKVArgsLenNotEven` | error variable | Classify malformed multi-set arguments |
| `ErrListNotFound` | error variable | Classify missing lists |
| `ErrEmptyList` | error variable | Classify empty list endpoints |
| `ErrSetNotExist` | error variable | Classify missing sets |
| `ErrSortedSetNotFound` | error variable | Classify missing sorted sets |
| `ErrSortedSetMemberNotExist` | error variable | Classify missing sorted-set members |
| `ErrWatchFeatureDisabled` | error variable | Classify disabled watch support |
| `ErrWatchingCallbackTimeout` | error variable | Classify watch callback timeouts |
| `ErrDontNeedMerge` | error variable | Report that merge has too few segments |
| `IsDBClosed` | function | Recognize a closed-database error |
| `IsBucketNotFound` | function | Recognize `ErrBucketNotFound` |
| `IsKeyNotFound` | function | Recognize a missing-key error |
| `IsKeyEmpty` | function | Recognize an empty-key error |
| `IsPrefixScan` | function | Recognize an empty-prefix-scan error |

Public methods retained on `DB`, `Tx`, `Iterator`, and `WatchOptions` are the methods described in the behavior sections above.

### CLI Entry Points

There is no console script for this package. Programmatic use is through the Go import path.

## Appendix A: Environment

The working environment runs Go 1.26.6 on Linux/amd64 without network access. The module cache contains the target's locked public dependencies: `github.com/antlabs/timer`, `github.com/bwmarrin/snowflake`, `github.com/edsrzf/mmap-go`, `github.com/gofrs/flock`, `github.com/pkg/errors`, `github.com/tidwall/btree`, `github.com/xujiajun/gorouter`, and `github.com/xujiajun/utils`. The assessment environment provides the same toolchain and cached module set.

The project must provide a standard `go.mod` at its root with module path `github.com/nutsdb/nutsdb`. Tests and builds must resolve without network access.

## Appendix B: Assessment Notes

Implementations are exercised through exported Go identifiers. Checks cover construction, managed and manual transaction boundaries, bucket lifecycle, key/value and TTL behavior, scans and iterators, list/set/sorted-set semantics, close/reopen durability, backup, merge preservation, watch events, and cross-view agreement. Temporary local directories are used instead of external services. Private storage structures, exact text, raw file layout, and platform-specific mmap behavior are not assessed.
