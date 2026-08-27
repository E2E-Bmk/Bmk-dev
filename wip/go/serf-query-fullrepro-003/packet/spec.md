# Consistent query targets for Serf

## Overview

Serf queries ordinarily remain open until their timeout and identify responders
by node name. That behavior is useful for broad, best-effort collection and is
unchanged. Some controllers instead need a bounded answer about one coherent
membership cohort: the members selected by the node and tag filters should come
from one point-in-time view, a departed instance should stop delaying the
collector, and a later process using the same node name should not answer for
its predecessor.

`QueryParam` therefore has one additional opt-in field:

```go
type QueryParam struct {
    FilterNodes     []string
    FilterTags      map[string]string
    RequestAck      bool
    RelayFactor     uint8
    Timeout         time.Duration
    CoherentTargets bool
}
```

When `CoherentTargets` is false, including its zero value, query filtering,
delivery, acknowledgement, response collection, and timeout behavior remain
compatible with existing Serf releases. The option does not add an endpoint,
event kind, result type, or persistence format.

## Using a coherent query

Applications enable the option on an ordinary query and consume the existing
`QueryResponse` channels:

```go
response, err := node.Query("ready", payload, &serf.QueryParam{
    FilterTags:      map[string]string{"role": "^worker$"},
    RequestAck:      true,
    Timeout:         2 * time.Second,
    CoherentTargets: true,
})
if err != nil {
    return err
}
defer response.Close()

for reply := range response.ResponseCh() {
    use(reply.From, reply.Payload)
}
```

The caller continues to use `Members`, `LocalMember`, membership events,
`Query`, `Query.Respond`, `AckCh`, `ResponseCh`, `Deadline`, `Finished`, and
`Close`. A target does not need a new handler API and responds through the
`Query` event it already receives.

## Target cohort

For a successful coherent query, Serf selects the target cohort from one
complete member-and-tag view that exists at a single point while the query is
being admitted. The cohort is the intersection of `FilterNodes`, all
`FilterTags` expressions, and members that are alive in that view. An omitted
filter does not restrict its dimension. Invalid tag expressions are rejected
without publishing a query.

Membership and tag updates are whole transitions. A coherent query cannot use
a node list from one transition and tags from another. Changes after the cohort
has been selected do not retroactively add a member or move an existing member
out of that cohort. A query started after the transition observes a later
cohort in the same way.

Member identity for this behavior includes one live membership lifetime, not
only the public node name. If a member leaves and another Serf process later
joins under that name, the new process belongs only to cohorts selected after
its join. It cannot acknowledge or respond on behalf of a prior lifetime.

## Collection and completion

An acknowledgement or response is accepted only when it belongs to the member
instance selected in the cohort and that instance is still the current member
for the selected lifetime. Existing duplicate suppression still permits at
most one acknowledgement and at most one response per node. Relayed copies are
subject to the same checks as direct replies.

Each target reaches a terminal outcome when one of the following happens:

- its response is accepted;
- when `RequestAck` is set, its acknowledgement is accepted; or
- that same member instance completes a graceful leave.

The collector finishes when every selected target has a terminal outcome. An
empty cohort therefore finishes without waiting for the timeout. The configured
deadline remains an upper bound: failure detection, abrupt shutdown, an
unanswered target, or any other non-graceful disappearance does not stand in
for a response, requested acknowledgement, or graceful leave.

Finishing closes `ResponseCh` and the optional `AckCh` once. Values accepted
before closure remain available to channel consumers. `Finished` then reports
true, and `Close` remains safe to call repeatedly. A late reply, a reply from a
replacement instance, or a delivery after closure does not reopen the
collector or alter values already accepted.

## Membership and tag changes

`SetTags` continues to publish a normal member update. A query whose cohort was
selected before that update keeps its selected instances; a later query applies
its expressions to the new complete tag view. This preserves a clear boundary
without making tag propagation part of the response payload.

`Leave` continues to move the member through Serf's graceful lifecycle and to
publish the existing membership event. Only the departure of the selected
instance satisfies that target. A leave belonging to an earlier lifetime and
a join belonging to a later lifetime cannot be combined into one target
outcome.

Failed members retain the existing failure and reaping behavior. A failure may
change `Members` and membership events, but a coherent collector still waits
until another documented terminal outcome or its deadline.

## Restart and snapshot boundaries

Serf snapshots continue to restore previous-node and Lamport positions. They do
not persist an open `QueryResponse`. After a snapshot owner closes and a new
instance reopens the same snapshot, a newly admitted coherent query selects
from the rejoined member view of that new lifetime. Replies associated with a
collector owned by the closed instance cannot contribute to the new query.

The same rule applies to ordinary same-name restarts without a snapshot. Once
the replacement has joined and appears as the current live member, a fresh
query may select it; an older collector, if still within its deadline, remains
bound to its own cohort.

## State and cross-view consistency

The feature connects five existing views:

1. `Members` and `LocalMember` expose names, addresses, tags, and statuses.
2. Membership events expose join, update, graceful leave, and failure
   transitions.
3. Query filters determine admission from a member-and-tag view.
4. `AckCh` and `ResponseCh` expose accepted target outcomes.
5. `Deadline`, `Finished`, and channel closure expose the collector lifetime.

The following relationships hold:

1. The selected names and tags are obtainable from one complete `Members`
   state during query admission.
2. Every accepted acknowledgement or response names a selected live instance.
3. A tag transition affects later cohort selection as one whole update.
4. A graceful leave satisfies only collectors that selected that departing
   instance.
5. A same-name replacement is distinct across member, event, response, and
   completion views.
6. Direct and relayed copies have identical admission and uniqueness rules.
7. Collector completion agrees across `Finished`, response-channel closure,
   acknowledgement-channel closure, and rejection of later deliveries.
8. Snapshot reopen affects subsequent membership selection but does not carry
   an open collector across shutdown.

Member names, tag keys and values, query names, payloads, cohort sizes, filter
combinations, response order, acknowledgement order, update order, leave
position, restart position, and snapshot boundary may vary independently. The
rules above apply to every valid combination; slice order from `Members` and
wall-clock scheduling are not semantic results.

## Errors and compatibility

Existing query size, response size, protocol-version, duplicate-response, and
deadline errors remain in force. Coherent target selection adds no public error
type. A malformed filter or another admission error returns no usable
`QueryResponse`. Runtime membership change does not turn an already admitted
query into a call error; it is reflected through target outcomes and the
deadline rules.

A nil `QueryParam` and a zero-valued `QueryParam` keep the existing best-effort
mode. Default timeout calculation, relay selection, event delivery, user
events, membership coalescing, leave state, shutdown state, and snapshot file
ownership otherwise retain their current behavior.

## Public interface

```go
import (
    "time"

    "github.com/hashicorp/memberlist"
    "github.com/hashicorp/serf/serf"
)
```

| Name | Kind | Role |
|---|---|---|
| `serf.QueryParam` | struct | Configures filters, acknowledgement, relay, timeout, and optional coherent target selection. |
| `serf.Serf.Query` | method | Admits a query and returns its existing response collector. |
| `serf.QueryResponse` | type | Owns acknowledgement, response, deadline, finished, and closure views. |
| `serf.QueryResponse.AckCh` | method | Returns requested target acknowledgements. |
| `serf.QueryResponse.ResponseCh` | method | Returns accepted node responses. |
| `serf.QueryResponse.Deadline` | method | Reports the query's upper time bound. |
| `serf.QueryResponse.Finished` | method | Reports terminal collector state. |
| `serf.QueryResponse.Close` | method | Idempotently ends collection. |
| `serf.Query` | type | Represents an admitted query event on a target node. |
| `serf.Query.Respond` | method | Sends that node instance's response. |
| `serf.Serf.Members` | method | Returns the point-in-time member view. |
| `serf.Serf.LocalMember` | method | Returns the local member projection. |
| `serf.Serf.SetTags` | method | Publishes a complete local tag update. |
| `serf.Serf.Leave` | method | Performs a graceful member departure. |
| `serf.Serf.Shutdown` | method | Ends the local Serf lifetime. |
| `serf.Config.SnapshotPath` | field | Selects existing snapshot persistence and rejoin behavior. |
| `memberlist.MockNetwork` | type | Provides the in-process transport used by local cluster workflows. |

## Supported environment

The supported build uses Go 1.25.6 on Linux amd64 with `GOTOOLCHAIN=local`.
Dependencies are resolved offline from the supplied module cache. In-process
cluster workflows use `memberlist.MockNetwork` and fresh caller-owned temporary
directories; they require no fixed port, remote service, credential, or
external clock.
