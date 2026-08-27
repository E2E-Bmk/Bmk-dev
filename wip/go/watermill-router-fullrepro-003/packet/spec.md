# Watermill Durable Delivery Views

## Product Overview

Watermill Durable Delivery Views adds versioned CQRS routing, output publication journaling, terminal settlement, retry identity, drain barriers, and recovery checkpoints to Watermill. Each concern has an independently owned Go package and an immutable exported view. Applications join those views at their own workflow boundary instead of relying on a global coordinator or aggregate receipt.

The extension is additive to `github.com/ThreeDotsLabs/watermill` v1.5.2. Existing messages, routers, publishers, subscribers, and CQRS marshalers retain their established behavior.

## Non-Goals

- This specification does not require a durable database, network broker, metrics backend, or distributed lock service.
- This specification does not define delivery ordering across unrelated logical messages.
- This specification does not require a global workflow object, combined receipt, validator, digest, or dispatcher.
- This specification does not define a replacement for Watermill Router, Publisher, Subscriber, or CQRS handlers.
- This specification does not require wall-clock scheduling or background goroutines.

## Representative Workflows

The packages support event, command, and query routes. Every workflow uses public exported values, and every state transition returns a view owned by the package that performed it.

## Route planning workflows

### Versioned command publication

1. An application binds `CreateOrder` as a command route with an input topic, handler owner, ordered outputs, required brokers, dead-letter topic, and retry limit.
2. The application places the route kind, type, and revision in Watermill message metadata and uses the route type with a CQRS marshaler.
3. A publication journal opens a batch whose intents derive from the route outputs and handler owner.
4. Each output and broker pair receives an independent publication observation.
5. The journal seals only after every required pair commits. The settlement ledger acknowledges the delivery only from that sealed batch view.
6. The application applies the resulting terminal decision to the Watermill message.

### Partial publication recovery

1. A publisher commits one required broker observation and rejects another observation with a cause.
2. The journal reports an incomplete publication and rejects both sealing and rollback while committed work lacks compensation.
3. The application records compensation for every committed pair, then rolls the batch back.
4. The settlement ledger records a negative terminal decision with the failure cause.
5. Independently captured journal and settlement views retain the same delivery and batch identities.

## Delivery recovery workflows

### Cross-broker retry lineage

1. The retry index observes the first delivery on a primary broker using logical, delivery, correlation, and dedup identities.
2. A mirror broker observation for the same logical attempt merges into that attempt. Repeating the same observation marks a duplicate without creating another ordinal.
3. A retry uses the next contiguous ordinal and preserves correlation and dedup identities while using a distinct delivery identity.
4. Route resolution for the retry reads the current compatible route revision.

### Drain, cancellation, and checkpoint replay

1. A drain barrier admits deliveries and records output work tokens before drain begins.
2. Beginning drain freezes the admitted unsettled set and rejects later admission.
3. A cancellation request records its cause. A terminal cancellation observation does not close the barrier while an output token remains active.
4. Finishing the last output token closes the barrier after every frozen delivery has a terminal settlement.
5. A checkpoint records route, journal, settlement, retry, and drain positions.
6. A fresh checkpoint store replays saved checkpoints. Recovery derives retry, dead-letter, cancellation, resume, or completion from the independently supplied current views.

## State Model

### Route plan state

`routeplan.Catalog` assigns a strictly increasing revision to each successful binding. `Resolve` returns the current binding for a kind and type name. `AtRevision` returns the historical binding at an exact revision. Rebinding the same key creates history without changing earlier returned values. `Snapshot` returns one current binding per key in deterministic kind-and-name order.

`routeplan.Compatible` reports true when kind, type name, handler, and input topic remain equal. Output or retry-policy changes do not by themselves change compatibility.

### Publication journal state

`pubjournal.Journal` owns batches and a monotonically increasing cursor. `Open` declares the complete ordered output intent set. Every intent belongs to the route handler and names one or more unique required brokers.

Each output and broker pair begins pending. `Observe` records exactly one of committed or rejected from pending, and records compensated only after committed. Rejected and compensated observations include a non-empty cause. A sealed batch has every pair committed. A rolled-back batch has no uncompensated committed pair. Sealed and rolled-back are mutually exclusive terminal batch states.

### Settlement ledger state

`settlement.Ledger` admits a delivery with its route revision and publication batch. Each admitted delivery begins pending and reaches exactly one of ack, nack, or cancel. Ack requires the matching sealed batch. Nack and cancel require the matching rolled-back batch and a non-empty cause. The ledger cursor increases for admission and terminal decisions.

### Retry identity state

`retrylineage.Index` owns logical lineages and dedup ownership. A logical lineage begins at ordinal zero and grows through contiguous ordinals. Every ordinal preserves its lineage correlation and dedup identities. Broker, topic, and token identify an observation. A second distinct broker observation merges into the ordinal; repeating an identical observation marks the returned attempt as duplicate. A dedup key belongs to one logical identity.

### Drain barrier state

`drainbarrier.Barrier` owns admitted delivery IDs, active output tokens, cancellation requests, terminal observations, and one drain generation. Beginning drain freezes every admitted unsettled delivery. The closed view is true exactly when drain has begun and no frozen delivery lacks a terminal settlement or retains an active output token.

### Recovery checkpoint state

`recovery.Store` owns checkpoints by ID. Replacing a checkpoint preserves logical delivery identity and never decreases route revision, journal cursor, settlement cursor, retry ordinal, or drain generation. Snapshot order is deterministic by checkpoint ID.

`recovery.BuildResume` consumes a checkpoint plus route, batch, settlement, lineage, and drain views. All identities and positions must cover the checkpoint. An acknowledged delivery completes. A recorded drain cancellation takes precedence over retry. A rolled-back delivery retries below the route limit and uses the input topic; at the limit it uses the dead-letter topic. A sealed pending delivery resumes on the input topic.

## Error Semantics

- `routeplan.ErrInvalid` reports malformed route declarations. `routeplan.ErrNotFound` reports an unknown route key or revision.
- `pubjournal.ErrInvalid` reports malformed batch ownership or broker declarations. `pubjournal.ErrConflict` reports an unknown pair, repeated terminal transition, or incompatible batch state. `pubjournal.ErrNotReady` reports pending pairs. `pubjournal.ErrPartial` reports rejected work or uncompensated committed work.
- `settlement.ErrInvalid` reports malformed admission. `settlement.ErrConflict` reports identity mismatch or a second terminal decision. `settlement.ErrNotReady` reports a publication view that does not authorize the requested terminal decision.
- `retrylineage.ErrInvalid` reports incomplete identity or broker observations. `retrylineage.ErrConflict` reports dedup ownership changes, identity changes within an ordinal, or a non-contiguous ordinal.
- `drainbarrier.ErrInvalid` reports empty identities, causes, tokens, or drain generations. `drainbarrier.ErrConflict` reports repeated or impossible transitions. `drainbarrier.ErrDraining` reports admission after drain begins.
- `recovery.ErrInvalid` reports an incomplete checkpoint. `recovery.ErrConflict` reports identity changes or decreasing checkpoint positions. `recovery.ErrStale` reports supplied views that do not cover the checkpoint.

Errors support `errors.Is`. Failed calls leave the owning package state unchanged.

## Cross-View Invariants

1. A route binding, publication intent, settlement record, and checkpoint preserve the same handler-owned delivery path without a shared aggregate object.
2. An acknowledged delivery references a sealed publication batch; a negatively settled delivery references a rolled-back publication batch.
3. A partial publication never authorizes acknowledgement, and rollback never hides an uncompensated committed output.
4. A retry preserves logical, correlation, and dedup identity across broker observations while advancing exactly one ordinal.
5. Two indexes that observe the same broker set in different orders reconcile to equivalent lineage identities and observation counts.
6. A drain barrier remains open while any frozen delivery retains active output work, even when its terminal settlement arrives first.
7. A checkpoint never describes a journal, settlement, retry, route, or drain position ahead of the supplied recovery views.
8. Recovery after checkpoint replay selects a topic from the compatible current CQRS route and preserves the checkpoint delivery identity.
9. Watermill message metadata carries the route and retry identities used by the independent package views.
10. Applying an ack, nack, or context cancellation to a Watermill message agrees with the terminal settlement and drain view selected by the application.

## Public Interface

All new packages are safe for use by concurrent callers. Constructors return independent in-memory owners. Returned slices and nested broker lists are copies; modifying a returned view does not mutate owner state.

### Route plan declarations

`routeplan.NewCatalog` constructs a catalog. `Catalog.Bind`, `Resolve`, `AtRevision`, and `Snapshot` manage immutable `Binding` values. `Compatible` compares the stable execution identity of two bindings.

### Publication and settlement declarations

`pubjournal.NewJournal` constructs a journal. `Journal.Open`, `Observe`, `Seal`, `Rollback`, `Batch`, `Cursor`, and `Snapshot` expose publication state. `settlement.NewLedger` constructs a ledger. `Ledger.Admit`, `Acknowledge`, `Reject`, `Cancel`, `Lookup`, `Cursor`, and `Snapshot` expose terminal state.

The publication view types are `pubjournal.Intent`, `pubjournal.Observation`, and `pubjournal.BatchView`.

### Identity, drain, and recovery declarations

`retrylineage.NewIndex` constructs an index. `Index.Observe`, `Lookup`, `Lineage`, and `ResolveDedup` expose retry identity. `drainbarrier.NewBarrier` constructs a barrier. `Barrier.Admit`, `StartOutput`, `FinishOutput`, `Begin`, `RequestCancel`, `Observe`, and `Snapshot` expose drain state. `recovery.NewStore`, `Store.Save`, `Load`, `Snapshot`, and `BuildResume` expose checkpoint recovery.

The retry and drain view types are `retrylineage.Attempt`, `retrylineage.BrokerObservation`, `drainbarrier.View`, and `drainbarrier.DeliveryView`.

## Import Surface

```go
import (
    "github.com/ThreeDotsLabs/watermill/components/cqrs"
    "github.com/ThreeDotsLabs/watermill/message"
    "github.com/ThreeDotsLabs/watermill/message/drainbarrier"
    "github.com/ThreeDotsLabs/watermill/message/pubjournal"
    "github.com/ThreeDotsLabs/watermill/message/recovery"
    "github.com/ThreeDotsLabs/watermill/message/retrylineage"
    "github.com/ThreeDotsLabs/watermill/message/routeplan"
    "github.com/ThreeDotsLabs/watermill/message/settlement"
    "github.com/ThreeDotsLabs/watermill/pubsub/gochannel"
)
```

Only exported identifiers from these imports form the supported surface.

## API Catalog

| Name | Kind | Role |
| --- | --- | --- |
| `routeplan.Kind`, `Event`, `Command`, `Query` | type and constants | Identify CQRS route domains. |
| `routeplan.Output` | struct | Declare an ordered output topic and required brokers. |
| `routeplan.Binding` | struct | Describe one versioned handler route. |
| `routeplan.Catalog`, `NewCatalog` | owner and constructor | Own current and historical route bindings. |
| `Catalog.Bind`, `Resolve`, `AtRevision`, `Snapshot` | methods | Change and read route plans. |
| `routeplan.Compatible` | function | Compare stable execution identity. |
| `pubjournal.Status`, `Pending`, `Committed`, `Rejected`, `Compensated` | type and constants | Identify publication pair states. |
| `pubjournal.Intent`, `Observation`, `BatchView` | structs | Describe output declarations and publication views. |
| `pubjournal.Journal`, `NewJournal` | owner and constructor | Own publication batches and cursor state. |
| `Journal.Open`, `Observe`, `Seal`, `Rollback` | methods | Advance publication state. |
| `Journal.Batch`, `Cursor`, `Snapshot` | methods | Read publication state. |
| `settlement.Decision`, `Pending`, `Ack`, `Nack`, `Cancel` | type and constants | Identify delivery terminal state. |
| `settlement.Record` | struct | Describe one admitted or terminal delivery. |
| `settlement.Ledger`, `NewLedger` | owner and constructor | Own terminal decisions and cursor state. |
| `Ledger.Admit`, `Acknowledge`, `Reject`, `Cancel` | methods | Advance settlement state. |
| `Ledger.Lookup`, `Cursor`, `Snapshot` | methods | Read settlement state. |
| `retrylineage.BrokerObservation`, `Attempt` | structs | Describe broker evidence and logical attempts. |
| `retrylineage.Index`, `NewIndex` | owner and constructor | Own lineages and dedup ownership. |
| `Index.Observe`, `Lookup`, `Lineage`, `ResolveDedup` | methods | Reconcile and read retry identity. |
| `drainbarrier.DeliveryView`, `View` | structs | Describe delivery-local and barrier-wide drain state. |
| `drainbarrier.Barrier`, `NewBarrier` | owner and constructor | Own drain admission, output work, and terminal observations. |
| `Barrier.Admit`, `StartOutput`, `FinishOutput`, `Begin` | methods | Advance drain and output state. |
| `Barrier.RequestCancel`, `Observe`, `Snapshot` | methods | Record cancellation, settlement, and read state. |
| `recovery.Checkpoint` | struct | Persist positions across independent views. |
| `recovery.Store`, `NewStore` | owner and constructor | Own replayable checkpoints. |
| `Store.Save`, `Load`, `Snapshot` | methods | Change and read checkpoints. |
| `recovery.Action`, `Resume`, `Retry`, `DeadLetter`, `Cancel`, `Complete` | type and constants | Identify recovery results. |
| `recovery.ResumePlan` | struct | Describe the next CQRS delivery action. |
| `recovery.BuildResume` | function | Reconcile one checkpoint with current independent views. |
| Package error values | variables | Support stable `errors.Is` classification. |

## Appendix A: Environment

The supported environment is Linux on amd64 with Go 1.25.6 and no network access. The exact `go.mod`, `go.sum`, standard library, and frozen module cache define the dependency graph. Runtime state belongs to the calling process and its fresh temporary directory. No fixed TCP or UDP port, credential, container runtime, clock service, or external broker is required.

## Appendix B: Compatibility Notes

The extension targets `github.com/ThreeDotsLabs/watermill` v1.5.2 at commit `19b6816f64940527fad49eccb8d26d4df7dbbba3`. New packages do not alter existing Watermill interfaces. Applications explicitly translate package-owned views into Watermill message acknowledgements, negative acknowledgements, metadata, contexts, GoChannel operations, and CQRS marshaling.
