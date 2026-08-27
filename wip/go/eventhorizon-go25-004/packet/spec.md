# Bounded replay and quiescence

Event Horizon applications need a deterministic way to rebuild read-side state
and to stop asynchronous in-process components at a known boundary. Add the
following maintenance primitives while preserving the existing event store,
aggregate store, projector, event bus, and outbox behavior.

## Event stream ranges

Add an `EventRangeStore` interface in the root package. It extends `EventStore`
with:

```go
LoadRange(ctx context.Context, id uuid.UUID, fromVersion, toVersion int) ([]Event, error)
```

The bounds are inclusive. A valid range starts at version one or later and its
upper bound is not below its lower bound. Invalid bounds relate to the exported
`ErrInvalidEventRange` error and use the normal event-store load error context.

The memory event store implements the interface. It returns the existing events
within the requested interval in ascending version order. Extending the upper
bound beyond the current head is allowed; asking for an aggregate that is not
stored keeps the existing not-found behavior. A canceled context is observed
before reading. Returned events and their data are caller-owned in the same way
as other memory-store loads: changing one result must not change the stored
stream or a later read.

## Historical aggregate loads

Add a root `HistoricalAggregateStore` interface extending `AggregateStore` with:

```go
LoadVersion(context.Context, AggregateType, uuid.UUID, int) (Aggregate, error)
```

The event-sourced aggregate store implements it. The method reconstructs the
aggregate at exactly the requested accepted event version without modifying the
event stream, the current aggregate, or stored snapshots. Version zero returns
a newly created aggregate before any events have been applied. Negative versions
relate to an exported `events.ErrInvalidAggregateVersion`; a positive version
that the stream has not reached relates to
`events.ErrAggregateVersionNotFound`.

Historical loading follows the same aggregate factory, event application, and
error wrapping rules as current loading. A snapshot may be used only when it is
not newer than the requested version. Events after the requested version are
not applied. Implementations should use an `EventRangeStore` when available and
must retain compatibility with ordinary `EventStore` implementations.

## Projector replay

Add this method to `projector.EventHandler`:

```go
Replay(context.Context, []eventhorizon.Event) error
```

Replay handles the supplied sequence in caller order through the handler's
ordinary projection path. The existing duplicate, version-gap, irregular
versioning, entity lookup, removal, retry, and repository persistence behavior
continues to apply. An empty sequence succeeds. Cancellation or the first
projection error stops the replay; projections already completed remain visible
through the repository.

## Local event bus wait boundary

Add this method to `local.EventBus`:

```go
Wait(context.Context) error
```

Wait establishes a barrier after publications accepted before the call. It
returns only after every handler queue in the bus group has reached that
barrier, or when the context ends. The barrier itself is not an event, is not
matched or decoded, and is not delivered to handlers. Handler failures remain
reported through `Errors` and do not prevent the queue from reaching a later
barrier. Separate queues keep their existing ordering and a wait on an empty
group succeeds. Existing queue capacity, fan-out, codec, and close behavior
remain compatible.

## Memory outbox wait boundary

Add this method to `memory.Outbox`:

```go
Wait(context.Context) error
```

Wait returns when the memory outbox has no remaining handler work. An event is
not complete until every matching handler has handled it successfully; work for
a failing handler therefore remains pending while successful sibling handlers
are not repeated. The supplied context bounds the wait. Closing an outbox with
pending work releases waiters with cancellation, while an already empty outbox
is quiescent.

The method participates in the existing at-least-once processing path; it does
not introduce a second delivery engine. Admission, event copying, matching,
asynchronous error reporting, periodic retry, and close semantics remain
compatible.

## Compatibility

The new interfaces are additive. Existing implementations of `EventStore` and
`AggregateStore` remain valid. No global replay coordinator, combined receipt,
digest, or validation facade is part of this feature. Applications compose the
five native primitives and observe results through event loads, aggregate state,
repositories, handlers, and error channels.
