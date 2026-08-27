# NutsDB commit streams

> This document is the sole public behavioral authority for the additive
> commit-stream API in this module version.

## Purpose

Applications sometimes need a lightweight signal that an open NutsDB
generation has advanced before they reconcile state through ordinary read
transactions. A commit stream provides that signal without exposing WAL
records, storage files, transaction internals, or the existing best-effort
key watcher.

The feature is local to one open database generation. It is not a durable
change log, replication protocol, or replacement for `View`, `Backup`, or the
existing watch API.

## Public API

The root `nutsdb` package adds:

```go
type CommitRevision uint64

var ErrCommitStreamClosed error
var ErrInvalidCommitStreamRequest error

func (db *DB) CommitStream() (*CommitStream, error)
func (s *CommitStream) Next(ctx context.Context) (CommitRevision, error)
func (s *CommitStream) Close() error
```

`CommitStream` has no public fields. A successfully returned stream is active
before `CommitStream` returns to its caller.

## Commit boundary

Every successful transaction that changes the logical database state advances
the open generation once. Each stream that was active at that boundary receives
exactly one revision for that transaction. A transaction may touch multiple
keys, buckets, or native data structures; it still advances the stream once.

Read-only transactions, empty writable transactions, rolled-back callbacks,
and failed commits do not advance a stream. Database maintenance that leaves
the logical state unchanged is not a commit-stream event. Library-owned
transactions that perform a logical change, such as an expiration deletion,
use the same boundary as caller-owned updates.

Revisions are nonzero and strictly increase in the database's commit order.
They are opaque database-local values: callers may compare their order but
must not infer a wall-clock time, WAL location, or transaction identifier.
A stream begins after its creation boundary and does not replay earlier
revisions. Revisions are not resume tokens across `Close`/`Open`, backup, or
another database directory.

## Delivery and ownership

`Next` returns revisions in FIFO order. Once a revision is returned by `Next`,
it is consumed only for that stream. Separate streams own independent delivery
state; consuming, delaying, canceling, or closing one stream does not consume
or reorder another stream and does not change database contents.

Commit publication does not borrow caller buffers and does not depend on the
existing watch manager's channel capacity or drop policy. A slow stream may
accumulate pending revisions, but it must not cause another active stream to
miss a commit.

The revision is a notification boundary, not an embedded snapshot. Callers
reconcile through a fresh `View` after receiving it. If more commits complete
before that read, the read may observe the later state, as ordinary NutsDB
transactions do.

## Waiting, cancellation, and lifecycle

`Next` waits until a revision or terminal stream state is available. If its
context is canceled first, it returns the context error and leaves the next
revision pending. A nil context returns `ErrInvalidCommitStreamRequest`.

`Close` releases only that stream and is idempotent. After stream close,
`Next` returns `ErrCommitStreamClosed`; pending revisions owned by that stream
are discarded. Closing a stream does not close the database and does not
affect native transactions or other streams.

When the database closes, revisions already published to a stream remain
available in their original order. After that queue is drained, `Next` returns
`ErrDBClosed`. Creating a stream from a nil or closed database also returns
`ErrDBClosed`. A newly opened database is a new generation with no inherited
subscriptions.

## Compatibility

All existing transaction, bucket, BTree, List, Set, SortedSet, TTL, backup,
merge, watcher, and lifecycle behavior remains compatible. The feature adds no
network service, credential, goroutine-scheduling guarantee, file-format
contract, or exported storage representation.

The pinned target is module `github.com/nutsdb/nutsdb` at tag `v1.0.4` and
commit `b346859068f98ef382d83bc4d485fd6fecdc5e86`, built with Go 1.25.11 in the
offline Linux amd64 evaluation environment.
