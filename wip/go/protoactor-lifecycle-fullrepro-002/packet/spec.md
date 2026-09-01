# Proto.Actor Passivation and Reactivation

## Context

Proto.Actor hosts independent Go actors behind process identifiers. Actors receive
one message at a time, may supervise children, may schedule later work, and may be
addressed directly or through a router. Applications that create many short-lived
actors commonly passivate an actor after a period of inactivity and reactivate the
same logical name when more work arrives.

This document defines passivation as an actor-incarnation lifecycle boundary. The
boundary covers the idle clock, admitted mailbox work, scheduled callbacks,
supervision, request completion, router membership, and persistent reactivation.
It uses the existing `plugin.PassivationPlugin`, `plugin.PassivationHolder`, actor,
scheduler, router, event-stream, and persistence APIs.

Remote transport, cluster discovery, provider services, wall-clock precision,
logging text, metrics formatting, and durable files are outside this feature. All
examples are process-local and use caller-owned in-memory providers.

## Orientation

### A passivating actor

An actor opts in by embedding `plugin.PassivationHolder` and installing
`plugin.Use` with a `plugin.PassivationPlugin` receiver middleware.

```go
type worker struct {
    plugin.PassivationHolder
    total int
}

func (w *worker) Receive(ctx actor.Context) {
    switch msg := ctx.Message().(type) {
    case int:
        w.total += msg
        ctx.Respond(w.total)
    }
}

system := actor.NewActorSystem()
props := actor.PropsFromProducer(func() actor.Actor { return &worker{} },
    actor.WithReceiverMiddleware(plugin.Use(&plugin.PassivationPlugin{
        Duration: 250 * time.Millisecond,
    })))
pid, err := system.Root.SpawnNamed(props, "cart-41")
if err != nil {
    return err
}
value, err := system.Root.RequestFuture(pid, 3, time.Second).Result()
```

The inactivity period begins only after the actor is ready. Completing ordinary
work starts a fresh inactivity period. If no further work is accepted during that
period, the actor drains its admitted work, stops, leaves the process registry,
and notifies its watchers.

### Persistent reactivation

A persistent actor may combine passivation and persistence middleware. The
inactivity period starts after startup and recovery have completed. Events
accepted before passivation remain visible when the same logical name is spawned
again with the same provider.

```go
provider := persistence.NewInMemoryProvider(4)
props := actor.PropsFromProducer(func() actor.Actor { return &accountActor{} },
    actor.WithReceiverMiddleware(
        plugin.Use(&plugin.PassivationPlugin{Duration: 250 * time.Millisecond}),
        persistence.Using(provider),
    ))

first, err := system.Root.SpawnNamed(props, "account-7")
if err != nil {
    return err
}
system.Root.Send(first, deposit)
// After passivation has completed, the same name may be spawned again.
second, err := system.Root.SpawnNamed(props, "account-7")
```

Callers observe completion through replies, `Terminated`, process-registry
resolution, dead letters, router membership, and recovered actor state. They do
not need an event ledger or a special lifecycle report.

## Behavior

### Completed-idle periods

The passivation duration measures completed inactivity for the current actor
incarnation. The first period begins after `Started` handling and any synchronous
recovery have completed. When an ordinary message begins, the current idle period
is suspended; a full new period begins only after that handler returns normally.
Time spent in `Started`, recovery, or an ordinary handler is busy time and cannot
by itself make the actor idle. Repeated activity therefore produces repeated,
non-overlapping idle periods rather than extending an already expired callback.

Lifecycle transitions do not renew an incarnation's idle period. `Restarting`,
`Stopping`, and `Stopped` cancel the period owned by that incarnation. Calling
`Cancel` more than once is safe, and a later `Reset` applies only to a still-live
incarnation that has already been initialized.

### Admission and passivation closure

Expiry establishes one FIFO boundary in the target mailbox. Ordinary messages
accepted ahead of that boundary finish in mailbox order before `Stopping` and
`Stopped`. Messages that fall behind the boundary are not delivered to the old
actor instance. A one-way send behind the boundary is observable as a dead
letter, and a request behind the boundary completes with `actor.ErrDeadLetter`
rather than waiting for its requested timeout.

Passivation is idempotent. Racing expiry, explicit poison, and repeated stop
requests produce one terminal actor lifecycle and one `Terminated` notification
per watcher. Registry removal, `Stopped`, watcher notification, and dead-letter
routing describe the same closed incarnation. Reusing the same logical name
creates a new incarnation; cached work from the prior one cannot address it.

### Scheduled work belongs to an incarnation

A `scheduler.TimerScheduler` created from an actor `Context` belongs to the actor
incarnation that created it. A delayed or repeated callback may run while that
incarnation remains live, but it must not issue work after the incarnation enters
restart or passivation. Cancellation is a fence: once it returns, a callback that
has not begun cannot begin, and a repeated callback that was already running
cannot re-arm itself afterward.

A scheduler created from a root context is not owned by an actor incarnation. Its
callbacks remain governed by its own cancellation and by the liveness of their
target processes.

### Supervision handoff

A failure suspends ordinary delivery while the supervisor selects a directive.
Resume keeps the same actor incarnation and starts a fresh idle period after the
failed receive has been resolved. Restart cancels every passivation period and
actor-owned scheduled callback belonging to the old incarnation; the replacement
starts its first idle period after its `Started` handling is complete. Work
accepted while restart is in progress is handled by the replacement in admission
order and is not attributed to the old incarnation.

If passivation has already crossed its mailbox boundary, a later restart signal
cannot resurrect the closing incarnation. If failure occurs first and the
supervisor chooses restart, the replacement may continue until its own independent
idle period expires.

### Requests at the boundary

A request that meets passivation has exactly one terminal outcome. If its envelope
was admitted ahead of the boundary and the handler responds, the response wins.
Otherwise dead-letter completion wins. Timeout is reserved for a live request
that receives neither response nor terminal delivery before its own duration; it
is not a substitute for discarding work during passivation.

Only the first terminal outcome is retained. Later replies, dead-letter responses,
timer callbacks, and stop notifications cannot replace it. Every PID passed to
`Future.PipeTo` receives that one retained terminal value or error at most once.

### Router membership

A group router watches its caller-owned routees. When a routee passivates, a
membership view obtained afterward excludes that PID; later routed work does not
select it. The group does not create a replacement because it does not own its
routees. Direct sends to another live caller-owned routee remain independent of
the group.

A pool router owns its routees. While the router remains live, a passivated routee
is replaced with a fresh actor so that the configured pool size is restored. The
replacement has its own idle period and process identity. While the pool router
itself is stopping, terminated children are removed without replacement.

Membership changes and selection must agree after a `GetRoutees` response. A
request routed after that response either reaches a PID in the returned view or
receives a terminal dead-letter result; it cannot be delivered to a routee that
the same view has already removed.

### Persistent reactivation

Persistence recovery is part of startup, not idle time. A passivation period for
a persistent actor begins after the snapshot and following events have been
applied and `persistence.ReplayComplete` has been delivered. A short duration
therefore cannot interrupt an in-progress replay.

Each new event is assigned the next event index exactly once. A snapshot records
the index of the first event not represented by that snapshot. Reactivation from
that snapshot applies only the following events, in index order. Thus non-
idempotent events accepted before passivation have the same aggregate effect
before and after reactivation. The old incarnation's idle callback cannot stop or
otherwise affect the reactivated actor that later uses the same logical name.

## Contract

### State model

The passivation lifecycle connects these states:

1. **Starting** — the actor is receiving `Started` and, when applicable,
   restoring persistent state.
2. **Active** — a user handler or actor-owned scheduled callback is running.
3. **Idle** — no handler is running and one incarnation-owned duration is active.
4. **Restarting** — supervision has suspended delivery and is replacing the actor
   instance while preserving the PID.
5. **Passivating** — the idle duration has expired and its mailbox boundary has
   been admitted.
6. **Stopped** — the old PID is absent, watchers have a terminal notification,
   and later delivery follows the dead-letter path.
7. **Reactivated** — a newly spawned PID with the same logical name owns a fresh
   idle period and, when persistent, restored state.

### Error semantics

| Condition | Result |
|---|---|
| A request is admitted ahead of passivation and responds | `Future.Result` returns that response and nil error. |
| A request falls behind passivation | `Future.Result` returns `actor.ErrDeadLetter`. |
| A live request has no response or terminal delivery before its duration | `Future.Result` returns `actor.ErrTimeout`. |
| A duplicate named spawn occurs before registry removal | `SpawnNamed` returns `actor.ErrNameExists` and preserves the existing process. |
| The same name is spawned after passivation completes | A new PID and actor incarnation are created. |
| A pool routee passivates while its router is live | The routee is removed and a fresh owned routee restores pool size. |
| A group routee passivates | The routee is removed and is not replaced. |
| A supervisor chooses stop at the boundary | The actor closes once and cannot later restart. |

### Cross-view invariants

1. Handler start and completion bracket active time; neither startup, recovery,
   nor a running handler is an idle period.
2. The mailbox's passivation boundary agrees with actor delivery, future outcome,
   registry state, `Stopped`, `Terminated`, and dead-letter observation.
3. Restart preserves PID identity but replaces timer, actor, and scheduled-
   callback ownership.
4. A completed membership view and subsequent route selection agree about which
   passivated PIDs are eligible.
5. Pool replacement creates a fresh routee; group removal does not transfer
   ownership to the router.
6. Persistent state immediately before passivation and state after reactivation
   are equivalent under replay, including non-idempotent event histories.
7. The first terminal future outcome is stable across response, timeout,
   passivation, dead-letter, and piping races.
8. A callback or PID cached by an older incarnation cannot act on a newer actor
   that later uses the same logical name.

## Reference

### Import surface

```go
import (
    "time"

    "github.com/asynkron/protoactor-go/actor"
    "github.com/asynkron/protoactor-go/eventstream"
    "github.com/asynkron/protoactor-go/persistence"
    "github.com/asynkron/protoactor-go/plugin"
    "github.com/asynkron/protoactor-go/router"
    "github.com/asynkron/protoactor-go/scheduler"
)
```

### API catalog

| Name | Kind | Role |
|---|---|---|
| `plugin.PassivationAware` | interface | Connects an actor to passivation initialization, renewal, and cancellation. |
| `plugin.PassivationHolder` | type | Implements incarnation-owned idle timing for an embedded actor. |
| `plugin.PassivationHolder.Init`, `Reset`, `Cancel` | methods | Start, renew, and cancel the current incarnation's idle period. |
| `plugin.PassivationPlugin`, `plugin.PassivationPlugin.Duration` | type and field | Configures the inactivity duration used by receiver middleware. |
| `plugin.Use` | function | Installs a receiver lifecycle plugin in actor props. |
| `actor.NewActorSystem`, `actor.ActorSystem` | function and type | Create and own local processes, registry state, events, and supervision. |
| `actor.ActorSystem.Root`, `ProcessRegistry`, `EventStream` | fields | Expose external process operations and independent public views. |
| `actor.RootContext.Spawn`, `SpawnNamed` | methods | Create anonymous or logically named processes. |
| `actor.RootContext.Send`, `RequestFuture` | methods | Submit one-way work or a bounded request. |
| `actor.RootContext.StopFuture`, `PoisonFuture` | methods | Observe immediate or mailbox-ordered process closure. |
| `actor.Actor`, `actor.Context`, `actor.ReceiveFunc` | interfaces and function type | Define actor behavior and its current message context. |
| `actor.Context.Message`, `Self`, `Sender`, `Respond` | methods | Observe delivery identity and complete requests. |
| `actor.Context.Spawn`, `Watch`, `RequestFuture` | methods | Create children, observe termination, and create actor-owned requests. |
| `actor.Props`, `actor.PropsFromProducer`, `actor.PropsFromFunc` | type and functions | Describe actor production and receiver behavior. |
| `actor.WithReceiverMiddleware`, `actor.WithSupervisor` | functions | Attach lifecycle middleware and supervision. |
| `actor.NewOneForOneStrategy`, `actor.DeciderFunc`, `actor.Directive` | function and types | Select resume, restart, stop, or escalation after failure. |
| `actor.Started`, `Restarting`, `Stopping`, `Stopped`, `Terminated` | message types | Expose actor lifecycle and watcher completion. |
| `actor.Terminated.Who`, `actor.Terminated.Why` | fields | Identify the stopped PID and terminal reason. |
| `actor.DeadLetterEvent` and its `PID`, `Message`, `Sender` fields | type and fields | Describe one undeliverable envelope. |
| `actor.Future`, `Future.Result`, `Wait`, `PipeTo`, `PID` | type and methods | Observe and forward one stable terminal request result. |
| `actor.ErrDeadLetter`, `actor.ErrTimeout`, `actor.ErrNameExists` | errors | Report terminal delivery, timeout, and name conflicts. |
| `actor.ProcessRegistryValue.Get` | method | Resolve whether a PID still names a live process. |
| `eventstream.EventStream.Subscribe`, `Unsubscribe` | methods | Observe and remove process-event subscriptions. |
| `scheduler.NewTimerScheduler`, `scheduler.TimerScheduler` | function and type | Create root-owned or actor-incarnation-owned delayed work. |
| `scheduler.TimerScheduler.SendOnce`, `SendRepeatedly` | methods | Schedule one-way messages. |
| `scheduler.TimerScheduler.RequestOnce`, `RequestRepeatedly` | methods | Schedule requests carrying the scheduler context's sender. |
| `scheduler.CancelFunc` | function type | Fence later execution or re-arming. |
| `router.NewRoundRobinGroup`, `router.NewRoundRobinPool` | functions | Create caller-owned groups or router-owned pools. |
| `router.GetRoutees`, `router.Routees`, `router.Routees.PIDs` | message types and field | Obtain a completed routee membership view. |
| `router.AddRoutee`, `router.RemoveRoutee`, `router.BroadcastMessage` | message types | Change membership or deliver to current routees. |
| `persistence.Mixin`, `Recovering`, `PersistReceive`, `PersistSnapshot` | type and methods | Restore and append actor state. |
| `persistence.Using` | function | Install persistence recovery in receiver middleware. |
| `persistence.NewInMemoryProvider`, `persistence.InMemoryProvider` | function and type | Create a process-local provider shared across reactivations. |
| `persistence.RequestSnapshot`, `persistence.ReplayComplete` | message types | Request a snapshot and mark the end of recovery. |
| `time.Duration` | type | Configures idle periods, schedules, and request deadlines. |

There is no command-line interface for this module.

## Meta

The supported environment is Linux amd64 with Go 1.25.6. The module path remains
`github.com/asynkron/protoactor-go`. The delivered `go.mod`, `go.sum`, standard
library, and frozen module cache are the complete dependency closure. Execution
is offline.

All actors, routers, timers, futures, event subscriptions, and persistence
providers used here are process-local. No fixed port, daemon, container,
credential, remote service, DNS lookup, or durable shared directory is required.
Correctness is synchronized with actor replies and explicit caller-owned channel
barriers. Durations bound inactivity and safety waits; correctness does not depend
on exact scheduler delay.
