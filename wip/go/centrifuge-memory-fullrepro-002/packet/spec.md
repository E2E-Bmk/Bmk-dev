# Centrifuge In-Memory State Snapshot

> This document is the sole behavioral authority for the requested extension.
> The repository is pinned; behavior outside the extension remains that of the
> delivered source tree.

## Purpose

Centrifuge coordinates several process-local views of the same messaging
activity: retained publications in `MemoryBroker`, subscriptions in `Hub` and
`Client`, membership in `MemoryPresenceManager`, and connection lifecycle on
`Node`. Operators need a deterministic diagnostic snapshot that joins those
views without exposing mutable runtime storage.

The extension adds `Node.CaptureMemorySnapshot`. It is an observation API. It
does not publish, subscribe, recover, disconnect, repair, or restore state.
The existing public messaging APIs remain the only way to perform those
transitions.

## Scope

Snapshots are supported for a `Node` configured with the built-in
`MemoryBroker` and `MemoryPresenceManager`. The node may have no channels,
multiple retained streams, connected clients, server-side subscriptions, and
presence entries. Network listeners and external brokers are outside scope.

Calling the extension on a node using a different broker or presence manager,
on a node that has begun shutdown, or with an invalid request returns an error
wrapping `ErrMemorySnapshotUnavailable`. A cancelled or expired context returns
its context error. An unsuccessful call publishes no partial snapshot.

## Public API

The extension is part of package `github.com/centrifugal/centrifuge`.

```go
var ErrMemorySnapshotUnavailable error

type MemorySnapshotRequest struct {
    Channels     []string
    Since        map[string]StreamPosition
    HistoryLimit int
}

func (n *Node) CaptureMemorySnapshot(
    ctx context.Context,
    request MemorySnapshotRequest,
) (MemorySnapshot, error)
```

The result types are:

```go
type MemorySnapshot struct {
    Channels   []MemoryChannelSnapshot
    Clients    []MemoryClientSnapshot
    Consistent bool
    Problems   []string
}

type MemoryChannelSnapshot struct {
    Channel      string
    Position     StreamPosition
    Publications []MemoryPublicationSnapshot
    Recovery     MemoryRecoverySnapshot
    Subscribers  []string
    Presence     []MemoryPresenceSnapshot
}

type MemoryRecoverySnapshot struct {
    Requested    bool
    Since        StreamPosition
    Recoverable  bool
    Publications []MemoryPublicationSnapshot
}

type MemoryPublicationSnapshot struct {
    Offset uint64
    Data   []byte
    Info   *ClientInfo
    Tags   map[string]string
    Time   int64
}

type MemoryPresenceSnapshot struct {
    ClientID string
    UserID   string
    ConnInfo []byte
    ChanInfo []byte
}

type MemoryClientSnapshot struct {
    ClientID string
    UserID   string
    Info     []byte
    Channels []string
}
```

## Selecting channels

`MemorySnapshotRequest.Channels` is a channel scope, not a preferred output
order. When it is non-empty, every entry must be a non-blank, unique channel
name. The result contains exactly that scope, including selected channels that
currently have no retained publications or members.

When `Channels` is empty, the extension discovers the union of channels
currently visible in any supported in-memory view: retained-stream metadata,
Hub subscription membership, or presence membership. A channel appearing in
more than one view is emitted once.

Channel rows are ordered by channel name. Caller input order and Go map
iteration order do not affect the result.

Every key in `Since` must name a selected or discovered channel. A recovery
request for a channel outside the effective scope is invalid; the extension
must not silently widen the snapshot.

## Retained history projection

Each channel row carries the stream top returned by the configured memory
broker and a caller-owned projection of the selected retained publications.
`HistoryLimit` has the same meaning as `HistoryFilter.Limit`:

- `-1` selects the complete currently retained view;
- `0` selects no publication rows while still reporting the stream position;
- a positive value bounds the retained view using the broker's ordinary
  forward history selection;
- values below `-1` are invalid.

Publication projections preserve offset, data, optional client information,
tags, and publication time. They describe the broker's current retained rows;
they do not invent entries for live messages that were not retained.

`RemoveHistory` follows the semantics of the pinned memory broker. It removes
the retained rows selected by later reads. Stream metadata may remain long
enough for a subsequent retained publish to continue the current epoch and
offset sequence. The snapshot reports the actual broker position and retained
window rather than assuming that removal creates a new epoch.

An idempotent publish served from the broker result cache remains one retained
publication. Snapshotting must not turn the cached result into another history
row.

## Recovery projection

When `Since` contains a channel, its recovery row has `Requested` set and
preserves the requested `StreamPosition`. Recovery is marked successful only
when the current epoch is compatible and the retained publications form the
complete, unbroken suffix immediately after the requested offset through the
current stream top.

The successful suffix is returned in ascending offset order. A request already
at the current top is a successful empty suffix. An epoch mismatch, a trimmed
gap, or a removed portion of the required suffix is not recoverable and must
not expose a misleading partial replay. Recovery selection is complete and is
not shortened by `HistoryLimit`, which controls only the ordinary retained
history projection.

Channels without a `Since` entry have an unrequested zero recovery row.

## Hub, client, and presence projection

For each channel, `Subscribers` contains the current Hub subscriber client IDs
in lexical order. A duplicate subscription must not duplicate an identity.

`MemorySnapshot.Clients` contains connected Hub clients that subscribe to at
least one selected channel. Client rows are ordered by client ID. Their
`Channels` field contains only memberships inside the effective snapshot scope
and is ordered by channel name. A connected client with no selected membership
is not added merely because it exists elsewhere on the node.

Presence rows preserve the key used by the presence manager together with the
current user, connection information, and channel information. They are
ordered by client ID. Distinct clients sharing a user remain distinct presence
rows; unique-user aggregation remains the responsibility of `PresenceStats`.

Normal Centrifuge lifecycle transitions determine what the snapshot sees:

- a completed server-side subscription is reflected by both the client and
  Hub views;
- a subscription using `WithEmitPresence(true)` also appears in presence;
- unsubscribe removes the selected membership and its emitted presence while
  preserving sibling subscriptions;
- disconnect removes all of that client's memberships and emitted presence;
- later publications can advance retained history without reintroducing a
  removed subscriber.

The extension observes these transitions after their ordinary public API
completion points. It does not treat transport queue timing as part of the
snapshot result.

## Consistency diagnosis

`Consistent` describes agreement among the selected Hub, client, and presence
views. It is true exactly when `Problems` is empty. Problems are deterministic
and lexically ordered.

At minimum, the diagnostic detects:

- a Hub subscriber that is absent from the captured connected-client view;
- a Hub subscription not represented by that client's selected channel view;
- a presence member for a selected channel without corresponding Hub
  subscription membership.

An inconsistent runtime is still a successful observation: the snapshot
contains the facts that were observed and reports their disagreement. This is
different from an invalid request or unavailable backend, which returns an
error and no snapshot.

## Ownership and determinism

Every returned slice, byte slice, map, `ClientInfo`, and nested projection is
owned by the caller. Changing any part of one snapshot must not mutate the
broker, Hub, client, presence manager, or a later snapshot. The extension must
also avoid returning aliases shared between two fields of the same result when
mutation of one would change the other.

For a quiescent node and the same request, observable ordering and values are
stable. Runtime-generated client IDs, epochs, and publication times are facts
and are not normalized away; deterministic ordering means that their container
order is stable once those facts exist.

The context is checked before publishing a result and during multi-channel
work. Cancellation returns the context error and no partially assembled
channel or client rows. Observation must not modify the runtime, regardless of
success or cancellation.

## Representative use

```go
snapshot, err := node.CaptureMemorySnapshot(ctx, centrifuge.MemorySnapshotRequest{
    Channels:     []string{"room:operations", "room:alerts"},
    Since:        map[string]centrifuge.StreamPosition{"room:operations": lastSeen},
    HistoryLimit: -1,
})
if err != nil {
    return err
}
if !snapshot.Consistent {
    report(snapshot.Problems)
}
```

The example illustrates request shape only. Correct implementations must work
for arbitrary valid channel names, client and user identities, retained
windows, lifecycle orders, and payloads.

## Existing behavior used by the extension

The pinned repository's existing public contracts remain authoritative:

- retained publishes receive monotonic offsets within an epoch;
- `Node.History` and `HistoryFilter` select the memory broker's current view;
- `Hub` owns current local connection and subscription membership;
- `Client.Channels` reports completed subscriptions;
- `MemoryPresenceManager` owns process-local presence and statistics;
- `Client.Unsubscribe`, `Client.Disconnect`, and `Node.Shutdown` perform their
  existing cleanup;
- caller-owned `Transport` implementations remain responsible for recording or
  delivering encoded pushes.

The snapshot extension must reconcile those owners. Reimplementing a parallel
messaging model or accepting caller-supplied synthetic facts is not equivalent.

## Environment

Final evaluation runs on Linux amd64 with the pinned Go toolchain and no network
access. The repository's existing `go.mod`, `go.sum`, and cached dependency
graph are available. Tests use only in-process nodes, memory backends, and
caller-owned recording transports. No external service, fixed port, or durable
filesystem state is required.
