# Transactional Savepoints for bbolt

## Context

A bbolt writable transaction normally has two outcomes: commit every change or
roll back every change.  Applications that build one transaction from several
logical phases often need a narrower recovery boundary.  They may want to try
one branch, discard that branch, and continue the transaction without losing
the work that preceded it.

Transactional savepoints provide that boundary.  A savepoint records the
observable state of one open writable transaction.  The transaction may later
return to that state, or discard the recovery point while retaining its current
work.  No intermediate state is published to other transactions.

## API

The `go.etcd.io/bbolt` package adds:

```go
var ErrInvalidSavepoint error

type Savepoint struct { /* opaque */ }

type ChangeKind uint8

const (
    ChangeBucketCreated ChangeKind = iota + 1
    ChangeBucketDeleted
    ChangeValuePut
    ChangeValueDeleted
    ChangeSequenceSet
)

type Change struct {
    Kind           ChangeKind
    Path           [][]byte
    Key            []byte
    Before         []byte
    After          []byte
    BeforeSequence uint64
    AfterSequence  uint64
}

func (tx *Tx) Savepoint() (*Savepoint, error)
func (tx *Tx) RollbackTo(point *Savepoint) error
func (tx *Tx) Release(point *Savepoint) error
func (tx *Tx) ChangesSince(point *Savepoint) ([]Change, error)
```

A `Savepoint` is an opaque transaction-local capability.  Its fields and its
representation are not public data.

## Inspecting a branch

`ChangesSince(point)` reports the logical difference between an active point
and the transaction's current branch without changing either state.  This is a
logical change view, not an undo log or a description of pages touched.

For entry changes, `Path` contains the top-level bucket name followed by nested
bucket names and identifies the containing bucket.  `Key` identifies the value
or child bucket in that bucket.  A top-level bucket therefore has an empty
path.  Sequence changes use the bucket path and a nil key.  `Before` and
`After`, or the sequence fields, describe the relevant endpoints for the
reported kind.

The result is deterministic and owns every byte slice it exposes.  Records
follow byte-lexical bucket traversal.  Creating a subtree reports its parent
before its contents; deleting a subtree reports its contents before its
parent.  A value/bucket transition is reported as removal of the old entry and
creation of the new entry.  A bucket move is the corresponding removal and
creation because bucket identity is its path in the logical tree.

An unchanged branch produces an empty slice.  Rolling back to the target makes
its change view empty.  Rebranching produces a view of only the new branch.
Calling `ChangesSince` with an invalid point follows the same error precedence
and non-mutation rules as `RollbackTo` and `Release`.

## Recorded state

`Savepoint` records the current logical contents of its writable transaction:

- all top-level and nested buckets;
- the distinction between a value entry and a nested-bucket entry;
- key and value bytes;
- the lexical order implied by those keys; and
- the sequence value of every bucket.

The recorded state owns the bytes it needs.  Later reuse or mutation of caller
buffers cannot change what a rollback restores.

Commit handlers registered with `Tx.OnCommit` also follow the savepoint
boundary.  A rollback keeps handlers registered before the target and removes
handlers registered after it.  A release does not remove handlers because it
does not discard the current branch.

Transaction statistics describe work attempted by the transaction and need
not decrease after a rollback.  Page identifiers, node allocation, fill
percentages, and in-memory object identity are not recorded state.

## Creating savepoints

`Savepoint` succeeds only while `tx` is an open writable transaction.  It may
be called from an explicitly begun transaction or from the writable transaction
provided to `DB.Update` or `DB.Batch`.

Calling it on an open read-only transaction returns an error matching
`ErrTxNotWritable`.  Calling it on a closed transaction returns an error
matching `ErrTxClosed`.

More than one savepoint may be active.  Their order is the order in which they
were created, and later points are descendants of earlier points.

## Rolling back to a point

`RollbackTo(point)` replaces the transaction's current logical state with the
state recorded at `point`.  It does not close, commit, or publish the
transaction.  Work performed before the point remains; work performed after
the point is absent.

The target point remains active.  The caller may make a different set of
changes and roll back to the same point again.  Every point created after the
target is invalidated, including points created on a branch that has just been
discarded.

Restoration applies to the bucket tree as a whole.  It covers creates,
deletes, overwrites, sequence changes, bucket moves, transitions between a
value and a bucket at the same key, empty buckets, deeply nested buckets, and
values large enough to use overflow pages.  It must not combine topology or
values from the recorded branch and the discarded branch.

After a successful rollback, callers reacquire buckets and cursors from the
transaction.  Object identity and the continued usability of handles acquired
before the rollback are not guaranteed.

## Releasing points

`Release(point)` discards the recovery point without changing the current
logical state.  The target and every point created after it become invalid.
Earlier active points remain available.  Releasing an inner point therefore
keeps its current work and permits a later rollback to an older point.

## Invalid points

A nil point, a point from another transaction, a released point, a descendant
invalidated by rollback, or any point invalidated when its transaction ended is
invalid.  `RollbackTo` and `Release` return an error matching
`ErrInvalidSavepoint` for such a point.  Rejected calls do not change bucket
contents, sequences, active points, or commit handlers.

The transaction's own state determines error precedence.  Calls on a closed
transaction match `ErrTxClosed`; savepoint operations on an open read-only
transaction match `ErrTxNotWritable`.

## Commit, full rollback, and isolation

`Tx.Commit` publishes exactly the branch that is current at commit time.
`Tx.Rollback` discards the entire transaction, regardless of active
savepoints.  Either operation invalidates every point created by that
transaction.

Readers retain ordinary bbolt snapshot isolation.  A reader opened before a
writer commit continues to observe its earlier generation.  A fresh reader
after commit observes the writer's final branch, not a discarded branch.

After commit and reopen, normal bucket lookup, forward and reverse cursors,
sequences, and `Tx.Check` must agree on the same state.  Hot backups and
compacted copies made from the committed database preserve that state through
ordinary bbolt APIs.

## Compatibility

Code that does not use savepoints is unchanged.  Savepoints do not add a new
file format, durable journal, top-level bookkeeping bucket, companion file, or
alternate transaction type.  Existing commit, rollback, locking, backup,
compaction, and read-snapshot behavior retains its contract.

## Usage sketch

```go
err := db.Update(func(tx *bbolt.Tx) error {
    accounts := tx.Bucket([]byte("accounts"))
    if err := accounts.Put([]byte("phase"), []byte("prepared")); err != nil {
        return err
    }

    point, err := tx.Savepoint()
    if err != nil {
        return err
    }

    if err := attemptOptionalBranch(tx); err != nil {
        if rollbackErr := tx.RollbackTo(point); rollbackErr != nil {
            return rollbackErr
        }
        accounts = tx.Bucket([]byte("accounts"))
        return accounts.Put([]byte("result"), []byte("fallback"))
    }
    return tx.Release(point)
})
```

The sketch illustrates control flow only.  Savepoints are suitable for any
bucket layout and do not require these names or values.
