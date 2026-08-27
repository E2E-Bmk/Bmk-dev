# Pebble Commit Feeds

This document defines an observation API for applications that need to react to
successful Pebble mutations while a database handle is open. The repository is
pinned at `github.com/cockroachdb/pebble/v2` v2.1.6. Existing Pebble behavior
remains authoritative outside this extension.

## Purpose

Pebble accepts mutations through individual `DB` methods, `DB.Apply`, and
`Batch.Commit`. Those paths share a commit order but callers currently have no
public, handle-local way to observe that order as atomic mutation groups. A
commit feed exposes successful logical mutations without exposing WAL records,
memtables, table files, MANIFEST edits, or compaction choices.

The feed is live only. It is not a durable change-data-capture log and does not
replay commits made before subscription. Applications that need durable replay
must maintain their own state from received batches.

## Public API

The extension is part of package `pebble`.

```go
var ErrCommitFeedUnavailable error
var ErrCommitFeedLagged error

type CommitKind string

const (
    CommitKindSet            CommitKind = "set"
    CommitKindMerge          CommitKind = "merge"
    CommitKindDelete         CommitKind = "delete"
    CommitKindSingleDelete   CommitKind = "single-delete"
    CommitKindDeleteSized    CommitKind = "delete-sized"
    CommitKindDeleteRange    CommitKind = "delete-range"
    CommitKindRangeKeySet    CommitKind = "range-key-set"
    CommitKindRangeKeyUnset  CommitKind = "range-key-unset"
    CommitKindRangeKeyDelete CommitKind = "range-key-delete"
)

type CommitOperation struct {
    Kind      CommitKind
    Key       []byte
    End       []byte
    Suffix    []byte
    Value     []byte
    ValueSize uint32
}

type CommitBatch struct {
    SequenceStart uint64
    SequenceEnd   uint64
    Operations    []CommitOperation
}

type CommitFeedOptions struct {
    LowerBound []byte
    UpperBound []byte
    Buffer     int
}

func (d *DB) SubscribeCommits(
    ctx context.Context,
    options CommitFeedOptions,
) (*CommitFeed, error)

func (f *CommitFeed) Events() <-chan CommitBatch
func (f *CommitFeed) Err() error
func (f *CommitFeed) Close() error
```

## Subscription

`SubscribeCommits` registers a feed on one open database handle. `Buffer` must
be positive. Bounds are optional and use the database's configured comparer.
When both are present, the lower bound must precede the upper bound. Invalid
options, a nil or already-cancelled context, and a closed database return an
error wrapping `ErrCommitFeedUnavailable`; an already-cancelled context also
preserves the context error for `errors.Is`.

Option byte slices are copied during registration. Changing them later does not
change the feed. A successful subscription establishes its live boundary before
returning. It receives later successful commits but no earlier commit.

Several feeds may observe the same database independently. Closing, cancelling,
or overflowing one feed does not close another and does not affect database
writes.

## Commit batches

Each successful logical commit that contains at least one matching operation
produces one `CommitBatch`. Operations from one `DB.Apply` or `Batch.Commit`
stay in one event and retain their batch order. An individual mutation method
such as `Set` or `DeleteRange` therefore appears as a one-operation batch.

`SequenceStart` and `SequenceEnd` identify the committed Pebble sequence
interval for the entire original batch. The interval is inclusive. Intervals
seen by a feed are strictly increasing and never overlap. A filtered feed may
observe gaps because an earlier commit contained no matching operation. It
must not renumber the retained events or shrink an interval around the matching
subset.

The operation projection follows the mutation requested by the caller:

- point sets and merge operands use `Key` and `Value`;
- deletes and single deletes use `Key`;
- sized deletes additionally report `ValueSize`;
- range deletions use the half-open `Key` to `End` span;
- range-key sets use `Key`, `End`, `Suffix`, and `Value`;
- range-key unsets use `Key`, `End`, and `Suffix`;
- range-key deletions use `Key` and `End`.

Merge events contain the merge operand, not a value resolved by reading the
database. Log-data records and physical storage transitions are not logical
mutation events.

All byte slices and operation arrays returned through the feed are owned by the
receiver. They do not alias the submitted batch, database storage, subscription
options, another feed, or a later event.

## Range filtering

With no bounds, all supported logical mutations match. A point operation
matches when its key is within the configured half-open interval. A range
operation matches when its own half-open span overlaps the subscription
interval. The operation is delivered in full; bounds do not rewrite its start
or end.

Filtering is per operation, not per batch. A matching subset retains original
operation order in a single event. If no operation matches, that feed receives
no event for the commit. Other feeds may receive a different subset of the
same batch while retaining the same sequence interval.

## Publication and lifecycle

An event represents a completed logical publication. When a receiver obtains
an event, fresh database point and iterator reads may already observe that
commit. A failed or rejected mutation produces no event. Aborted, reset, or
merely closed batches produce no event.

Flush, compaction, format ratcheting, checkpoint construction, and other
physical maintenance do not repeat earlier mutations. A checkpoint opened as a
different database has its own feed lifetime and does not inherit the source
handle's feed or history.

Feed delivery must never wait indefinitely inside Pebble's commit path. If the
feed's buffer cannot accept the next matching batch, that feed terminates with
an error wrapping `ErrCommitFeedLagged`. Already buffered events remain
receivable, after which `Events` is closed. The commit itself still succeeds
and other feeds continue independently.

`Close` is concurrency-safe and idempotent. An explicitly closed feed ends
without a terminal error. Context cancellation ends the feed with the context
error. Closing the database ends all of its feeds with an error wrapping
`ErrClosed`. Once termination wins, no later batch is published to that feed.
`Err` is concurrency-safe and returns nil while the feed is active or after an
explicit close; after another terminal condition it returns that condition.

## Concurrency and ordering

Subscription, feed closure, context cancellation, and commit publication may
occur concurrently. Every successful commit still occupies one position in
Pebble's commit order. A feed observes matching batches in that order. The API
does not prescribe an order between a cancellation and a commit that are truly
concurrent; it does require one complete outcome—either the full matching batch
is delivered or it is not delivered at all.

## Environment

Evaluation runs on Linux amd64 with the pinned Go toolchain, the pinned module
closure, and networking disabled. Tests use isolated temporary directories or
`vfs.NewMem`; no CockroachDB server, remote object provider, or external
service is required.
