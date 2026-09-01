# Badger Live Checkpoints

> **Specification authority:** This document defines the supported public
> behavior of live checkpoints for this module version.

# Context

## Product overview

Badger is an embedded transactional key-value database with snapshot reads,
managed versions, iterators, expiring entries, backup and load, and online
maintenance. A live checkpoint creates a new Badger directory
that represents one committed source view while the source remains available.

Checkpoints are useful for local backup rotation, test fixtures, offline
inspection, migration staging, and fast creation of an independent database.
They are ordinary Badger directories after publication. They do not require a
service, a sidecar process, or a checkpoint-specific reader.

## Non-goals

- A checkpoint is not a continuing replica and does not receive later source
  writes.
- A checkpoint is not a replacement for cursor-based incremental backup.
- The contract does not require a particular construction strategy.
- The contract does not expose private storage or scheduling details.
- The returned timestamp is a database version boundary, not wall-clock time.

# Orientation

## Creating and opening a checkpoint

The application chooses a destination whose final path does not yet exist.
`Checkpoint` publishes that path only after it contains a complete database.
It returns the source read timestamp represented by the new directory.

```go
sourceOptions := badger.DefaultOptions(sourceDir).WithLogger(nil)
source, err := badger.Open(sourceOptions)
if err != nil {
	return err
}
defer source.Close()

readTs, err := source.Checkpoint(ctx, checkpointDir)
if err != nil {
	return err
}

copyOptions := source.Opts().
	WithDir(checkpointDir).
	WithValueDir(checkpointDir).
	WithReadOnly(true)
copy, err := badger.Open(copyOptions)
if err != nil {
	return err
}
defer copy.Close()

return inspect(copy, readTs)
```

For a managed source, the checkpoint is opened with `OpenManaged` when the
caller wants managed transaction semantics. An encrypted checkpoint is opened
with the same encryption key required by its source. Once open, the checkpoint
uses the normal Badger API.

# Behavior

## Snapshot boundary

`DB.Checkpoint` selects one committed read timestamp and returns it on success.
The checkpoint represents a coherent source view at that timestamp. Every
source commit whose version is at or below the returned boundary is eligible
for that view; a commit above it is not part of the view. Parallel range work
must not combine facts from different source boundaries.

The checkpoint preserves the public logical lineage observable at that
boundary: keys, values, deletions, user metadata, expiration timestamps, and
managed versions. Large and small values have the same contract. Expiration
continues to use Badger's ordinary wall-clock rules, so an expiration timestamp
is preserved even when its visibility changes after time advances.

The source can remain open for reads and writes while checkpoint creation is in
progress. Writes committed after the chosen boundary remain source-only. A
write that was staged but not committed at the boundary is not published by
the checkpoint.

## Independent database

After success, the destination is a self-contained Badger directory. Closing,
reopening, reading, iterating, backing up, loading from, compacting, or writing
the checkpoint does not require the source directory to remain present or
open.

The two databases are independent generations. Later writes, deletes, prefix
removal, expiration, and maintenance in one database do not change the other.
Repeated checkpoints use distinct destinations and each retains its own
returned boundary.

Sources whose key and value directories differ produce one self-contained
destination directory. An in-memory source can also publish a filesystem
checkpoint. Read-only sources may create checkpoints. Managed timestamps and
encryption remain observable through the normal opening mode and key supplied
by the application.

## Destination publication

The final destination path must not exist when checkpoint creation begins and
must still be available when publication occurs. A successful call makes the
complete destination visible as one publication. It never reports success for
an empty, partial, or unopenable destination.

An empty destination string is invalid. An existing file or directory is not
replaced, merged, truncated, or adopted. The parent directory must already be
usable for creation. Source and destination must not resolve to the same final
directory.

## Failure and recovery

A nil context or empty destination returns `ErrInvalidRequest`. A call on a
closed source returns `ErrDBClosed`. Context cancellation remains discoverable
with `errors.Is`. Existing-destination and filesystem failures retain their
ordinary `os` error identity.

If validation, cancellation, source lifecycle, destination I/O, or final
publication fails, the requested final destination is not newly exposed in a
partial state and a pre-existing destination is unchanged. The source remains
usable whenever its own lifecycle permits it. A later call with a fresh
context and destination starts from fresh source state rather than resuming
unpublished work.

# Contract

## State model

A checkpoint call progresses through validation, source-boundary selection,
private construction, durable completion, and destination publication. Only
the last transition creates the caller-selected final path. The returned
timestamp belongs to the published generation.

The source and every successfully published checkpoint have independent open,
closed, logical-version, and maintenance state. No later transition of one is
implicitly a transition of another.

## Cross-view invariants

1. Point reads and forward, reverse, prefix, and all-version iterators in the
   opened checkpoint agree on one source boundary.
2. A value, its user metadata, its expiration timestamp, and its version belong
   to the same committed entry in both source-boundary and checkpoint views.
3. A deletion at the returned boundary does not expose an older value as the
   current checkpoint value.
4. The checkpoint's maximum represented version does not exceed the returned
   timestamp.
5. Backup and load performed from a published checkpoint reproduce that
   checkpoint view without consulting the original source.
6. A failed checkpoint attempt changes neither an existing destination nor the
   committed logical source view.
7. A successful later source write can diverge from the checkpoint without
   changing any checkpoint observation.
8. Two successful checkpoints created around different committed generations
   retain their respective boundaries after close and reopen.

# Reference

## Public interface

The feature is additive to the root Badger package.

```go
import (
	"context"

	badger "github.com/dgraph-io/badger/v4"
)

func (db *badger.DB) Checkpoint(
	ctx context.Context,
	dir string,
) (readTs uint64, err error)
```

`Checkpoint` does not add a database option, operating mode, artifact format,
receipt type, callback protocol, trace surface, or command-line entry point.

## Input-generation guidance

Compatibility suites should vary ordinary application data rather than rely
on private storage layout. Useful generations include:

- empty, single-key, multi-prefix, and repeated-key histories;
- set, metadata update, delete, delete-then-rewrite, and aborted transaction;
- inline-sized and larger values, write batches, TTL entries, and managed
  timestamps;
- in-memory, filesystem, separate key/value-directory, read-only, and
  encrypted sources;
- checkpoints bracketed by source commits, followed by independent changes in
  both generations;
- canceled contexts, existing destinations, unusable parents, closed sources,
  and a successful recovery attempt at a fresh path.

Generated checks should observe results only through the public return value,
filesystem existence, ordinary database opening, point reads, iterators,
backup/load, maintenance, and close/reopen behavior. Concurrent cases should
use explicit barriers around public commits and verify the returned timestamp
rather than assume a scheduling order.

# Meta

## Environment

The supported evaluation environment is Windows amd64 with Go 1.25.6 and a
pinned offline dependency closure. Filesystem cases use fresh temporary parent
directories. No network access, daemon, container, credential, fixed port, or
shared database directory is required.

## Compatibility

The module path remains `github.com/dgraph-io/badger/v4` at tag `v4.9.6` and
commit `fbd8d2eefad8be8757249767255faf989945b599`. Existing APIs and
compatibility-mode behavior remain source compatible. Public results and fresh
database observations determine checkpoint compatibility; private file layout
does not.
