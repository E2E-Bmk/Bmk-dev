# NutsDB Transaction Savepoints Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`nutsdb` is an embedded transactional database that stages key/value, list, set, sorted-set, bucket, expiration, and watch-visible changes before commit. This extension adds transaction-local savepoints so a writable transaction retains an accepted prefix of staged work while discarding a later suffix. A savepoint covers the whole transaction rather than one collection.

## Non-Goals

- This specification does not require savepoints to survive transaction commit, rollback, database close, or process restart.
- This specification does not define savepoint names, serialization, cross-transaction transfer, or partial commit.
- This specification does not require savepoints for read-only transactions.
- This specification does not define changes to the existing on-disk format.

## Representative Workflows

**Retaining an accepted prefix.** A caller stages a durable value, captures a boundary, discards speculative work, and commits the prefix.

```go
tx, _ := db.Begin(true)
_ = tx.Put("kv", []byte("accepted"), []byte("yes"), nutsdb.Persistent)
sp, _ := tx.Savepoint()
_ = tx.Put("kv", []byte("speculative"), []byte("no"), nutsdb.Persistent)
_ = tx.RollbackTo(sp)
_ = tx.Commit()
```

**Nested correction across collections.** An outer boundary protects list and set work while an inner boundary isolates later sorted-set work.

```go
tx, _ := db.Begin(true)
outer, _ := tx.Savepoint()
_ = tx.LPush("lists", []byte("jobs"), []byte("compile"))
_ = tx.SAdd("sets", []byte("ready"), []byte("worker-1"))
inner, _ := tx.Savepoint()
_ = tx.ZAdd("scores", []byte("rank"), 7, []byte("discarded"))
_ = tx.RollbackTo(inner)
_ = tx.ReleaseSavepoint(outer)
_ = tx.Commit()
```

## Savepoint Lifecycle

Savepoints provide a stack-shaped lifecycle inside one writable transaction.

**Creation and identity.** When `Savepoint` succeeds, the transaction must return a non-zero `SavepointID`, append a live savepoint, and capture every mutation staged before the call. IDs returned by later calls in the same transaction must be greater than earlier IDs. A consumed ID must not be reused.

**Depth.** When `SavepointDepth` is called on an open transaction, it must return the number of live savepoints. The initial depth must be zero. Successful creation must increase it by one.

**Release.** When `ReleaseSavepoint` names the most recent live savepoint, it must remove that savepoint without changing staged mutations. If the ID exists below a newer savepoint, then it must return `ErrSavepointNotTopmost` and leave state and depth unchanged. If the ID is unknown or consumed, then it must return `ErrSavepointNotFound`.

## Rollback Boundaries

Rollback-to restores a complete transaction prefix while keeping the transaction open for further work.

**Restoration.** When `RollbackTo` names a live savepoint, the transaction must restore the exact staged mutations and accounting state captured at creation. It must consume the target and every newer savepoint. Mutations staged after the target must not become durable after commit.

**Nested boundaries.** When rollback targets an inner savepoint, mutations staged before that inner boundary must remain staged and older savepoints must remain live. When rollback targets an older savepoint, every younger ID must become invalid.

**Continued use.** After successful rollback-to, the transaction must accept new mutations, new savepoints, release, commit, and full rollback under their normal contracts.

## Data Structures, Buckets, and Expiration

A savepoint captures every mutation domain represented by the transaction.

**Key/value and expiration.** When rollback removes a staged `Put`, `Delete`, overwrite, or TTL-bearing write, transaction reads and committed reads must expose the value and expiration state from the restored prefix. When release removes only the boundary, staged key/value and TTL changes must remain staged.

**Collections.** When rollback removes staged list, set, or sorted-set operations, those operations must not appear after commit. Operations staged before the boundary must remain and must preserve ordinary collection ordering, membership, and score behavior.

**Bucket lifecycle.** When rollback removes a staged bucket creation or deletion, commit must behave as though that lifecycle operation was never staged. A restored bucket must accept later writes in the same transaction.

## Commit, Watch, and Failure Semantics

Terminal transaction behavior and watch delivery reflect only restored staged state.

**Commit and full rollback.** When commit follows savepoint operations, only current staged state must persist. When full rollback follows them, no staged state must persist. After either terminal operation, every savepoint method must return `ErrTxClosed`.

**Watch visibility.** Where watch support is enabled, a savepoint operation must not itself publish an event. When commit follows rollback-to, callbacks must receive events only for mutations still staged at commit. Discarded writes and bucket lifecycle operations must publish no event.

**Transaction mode.** If `Savepoint`, `RollbackTo`, or `ReleaseSavepoint` is called on an open read-only transaction, then it must return `ErrTxNotWritable` without changing depth. `SavepointDepth` must return zero and no error on an open read-only transaction.

## State Model

An open transaction has a staged mutation state and an ordered stack of snapshots. Each snapshot contains a transaction-local ID, complete staged writes, staged bucket lifecycle, and write accounting at its boundary. Commit projects current staged state to durable indexes and watch messages. Rollback-to projects a stored snapshot into the open transaction. Release changes only the stack. Commit and full rollback invalidate the stack.

## Error Semantics

| Condition | Result |
|---|---|
| A savepoint mutation method is called on a read-only transaction | `ErrTxNotWritable` |
| Any savepoint method is called after commit or full rollback | `ErrTxClosed` |
| Rollback or release names an unknown, consumed, or foreign ID | `ErrSavepointNotFound` |
| Release names a live savepoint below a newer live savepoint | `ErrSavepointNotTopmost` |
| A retained database operation violates its existing precondition | The existing NutsDB error remains unchanged |

Errors are exported sentinel values and must support identity comparison through `errors.Is`.

## Cross-View Invariants

1. Savepoint depth and ID validity must describe the same live stack after every create, rollback, and release operation.
2. Transaction reads after rollback-to and database reads after commit must expose the same restored key/value prefix.
3. List, set, and sorted-set views after commit must omit mutations discarded by rollback-to while retaining mutations before the boundary.
4. Bucket existence after commit and writes accepted through restored buckets must agree with the restored bucket lifecycle.
5. TTL reported after commit must belong to the retained write, never to an overwritten or discarded write.
6. Watch callbacks and durable reads after commit must describe the same retained mutation set.
7. Savepoint IDs and depth must remain transaction-local; an ID from another transaction must not select a snapshot.

## Public Interface

### Import Surface

```go
import "github.com/nutsdb/nutsdb"
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `SavepointID` | type | Transaction-local boundary identifier |
| `Tx.Savepoint` | method | Capture staged transaction state |
| `Tx.RollbackTo` | method | Restore and consume a boundary |
| `Tx.ReleaseSavepoint` | method | Remove the topmost boundary without restoring |
| `Tx.SavepointDepth` | method | Report live boundary count |
| `ErrSavepointNotFound` | error | Unknown, foreign, or consumed ID |
| `ErrSavepointNotTopmost` | error | Release attempted below a newer boundary |
| `ErrTxNotWritable` | error | Mutation attempted in a read-only transaction |
| `ErrTxClosed` | error | Operation attempted after termination |
| `Open`, `DefaultOptions`, `WithDir` | function/value | Open an embedded database in a selected directory |
| `Options`, `Options.EnableWatch` | type/field | Configure database behavior and enable committed watch events |
| `DB`, `DB.Begin`, `DB.Update`, `DB.View`, `DB.Close`, `DB.Watch` | type/methods | Database, transaction, and watch lifecycle |
| `Tx`, `Tx.Commit`, `Tx.Rollback` | type/methods | Existing transaction boundaries |
| `Tx.NewKVBucket`, `Tx.NewListBucket`, `Tx.NewSetBucket`, `Tx.NewSortSetBucket` | methods | Create typed buckets |
| `Tx.NewBucket`, `Tx.DeleteBucket`, `Tx.ExistBucket` | methods | General bucket lifecycle |
| `Tx.Put`, `Tx.Get`, `Tx.Delete`, `Tx.GetTTL` | methods | Key/value and expiration projection |
| `Tx.LPush`, `Tx.LRange` | methods | List mutation and read projection |
| `Tx.SAdd`, `Tx.SMembers` | methods | Set mutation and read projection |
| `Tx.ZAdd`, `Tx.ZMembers` | methods | Sorted-set mutation and read projection |
| `SortedSetMember`, `SortedSetMember.Value`, `SortedSetMember.Score` | type/fields | Expose sorted-set member payloads and scores |
| `Persistent` | constant | Disable key/value expiration |
| `DataStructureBTree`, `DataStructureList`, `DataStructureSet`, `DataStructureSortedSet` | constants | Select a bucket domain |
| `Message`, `Message.Key`, `Message.Value`, `WatchOptions` | types/fields | Describe committed watch events and callback timing |

### CLI Entry Points

There is no console script for this package. Programmatic use is through Go imports.

## Appendix A: Environment

The working environment runs Go 1.25 or newer on Linux without network access during assessment. The starter module contains the NutsDB source tree and its declared dependencies. The delivery must retain a valid `go.mod` at the project root.

## Appendix B: Assessment Notes

Assessment exercises public savepoint identity, stack transitions, failure paths, key/value restoration, expiration, typed collections, bucket lifecycle, transaction termination, persistence after reopen, and watch consistency. Individual checks cover single transitions and composed workflows. Results are counted per top-level Go test.
