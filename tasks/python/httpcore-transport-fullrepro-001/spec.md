# HTTPcore transport and durable state specification

## Authority and scope

This document is the sole authority for the covered behavior of a source-only
package importable as `httpcore`. Requirements describe public behavior
families, not evaluator examples, internal classes, file layouts, or exact
diagnostic text. The implementation must run offline.

The ordinary transport surface is compatible with httpcore 1.0.9. It includes
URL, Origin, Request, Response, Proxy, synchronous and asyncio network streams
and backends, mock streams, direct connections, connection pools, the public
transport exception hierarchy, and `default_ssl_context`. The declared
environment provides the ordinary runtime modules. A submitted package may
extend that runtime through a source-owned package shim, but must own the
extension module described below and must not delegate it elsewhere.

## Ordinary transport behavior

Wire values are ASCII byte-oriented. URL targets preserve path and query;
origins supply scheme defaults while explicit ports remain observable. Request
normalization preserves duplicate header order, opaque extensions, target
override locality, and the declared sync or async body protocol. Response
bodies are single-consumption streams whose successful full read is cached;
close delegates to the matching body protocol.

Pool capacity remains owned while a response is streaming. A terminal safe
response may release compatible same-route capacity; incomplete framing,
timeout, cancellation, protocol ambiguity, proxy failure, TLS failure, and
stream-local failure must not advertise unsafe capacity as reusable. Failure
on one origin or route does not erase an unrelated healthy owner.

Direct, forward-proxy, CONNECT-tunnel, and Unix-socket routes remain distinct.
Proxy credentials do not leak into direct traffic. HTTPS tunnel negotiation
keeps proxy and destination TLS roles distinct. HTTP/2 logical streams keep
their response bytes, flow-control state, reset outcome, and terminal ownership
separate. GOAWAY drains affected capacity while preserving accepted streams and
unrelated routes.

## Durable transport state extension

`httpcore.transport_state` provides deterministic, filesystem-backed control
of transport intent and terminal results. It exports `TransportStateError`,
`ConflictError`, `OwnershipError`, `IntegrityError`, `IncompleteError`, the
immutable records `Receipt`, `RouteSnapshot`, `CapacityLease`,
`ExchangeSnapshot`, `PublicationSnapshot`, and `TransportState(path)`.
Returned mappings and sequences are detached immutable values. Digests are
lowercase SHA-256 text over deterministic logical content. Reopening the same
path in a fresh process exposes the same committed state or fails closed on
corrupt UTF-8 data.

### Route partitions

`register_route(name, kind, destination, *, via=(), metadata=None, owner,
operation_id)` publishes one named route revision. Kinds include direct,
forward proxy, CONNECT tunnel, and Unix socket. Parent routes must already
exist; duplicate parents and cycles fail atomically. Equivalent operation-id
replay is idempotent, while conflicting reuse fails without replacing the last
revision. `route(name)` returns the current revision.

Route identity includes kind, destination, ordered parent path, and relevant
metadata. Capacity, request targets, proxy credentials, TLS roles, and later
publication stay in that partition. Idle capacity from a different partition
cannot be borrowed merely because it is available.

### Capacity leases and ownership fencing

`acquire(key, route, *, owner, operation_id, protocol="h1", stream_limit=1)`
creates a route-bound capacity lease. HTTP/1.1 admits one active exchange;
HTTP/2 admits distinct client stream identities up to its peer limit.
`handoff(lease, *, new_owner, operation_id)` advances the generation and fences
the old owner. Every exchange transition validates current lease ownership and
generation. A rejected waiter, timeout, cancellation, or stale owner cannot
later steal capacity.

### Request framing and exchange state

`begin(lease, *, stream_id, target, body=b"", framing="auto", operation_id)`
opens an exchange. Byte bodies receive matching content length under automatic
framing; iterable bodies use streaming framing. Explicit framing must agree
with the supplied body. Origin-form and absolute-form targets are retained as
given and must agree with the selected route.

`receive(exchange, *, status, headers, chunks, end_stream)` associates ordered
response metadata and exact bytes with that logical owner. Partial and terminal
responses remain distinct. `update_window(exchange, delta)` changes only the
selected HTTP/2 stream's flow-control credit. `cancel(exchange, *, category)`
records a local terminal failure without converting partial bytes into success.

### Response release and cleanup

`close_response(exchange, *, reusable)` ends response ownership. Reuse is
effective only for a complete safe response. Partial, cancelled, timed-out, or
otherwise indeterminate exchanges retire their capacity even if the caller
requests reuse.

Each exchange records lifecycle frames that actually began: connection,
optional proxy negotiation, optional destination TLS, and response ownership.
`discharge(exchange, action)` clears exactly the next reverse-order cleanup
obligation. Cleanup failure or interruption leaves the obligation owed after
reopen. It cannot be hidden by publishing a response.

### Publication, recovery, and reconciliation

`publish(exchange, events, *, operation_id)` publishes a response generation
only after terminal safe release and complete cleanup. Publication binds route
revision, lease/exchange receipt closure, status, exact body digest, and ordered
events. An incomplete or failed exchange preserves the prior acknowledged
generation. `current(route)` returns that generation, `verify(publication)`
validates it against durable exchange bytes, and `recover(operation_id, *,
owner)` reopens an exchange only for its current fenced owner.

Independent route and stream owners remain isolated across failure, handoff,
replacement, reopen, and reconciliation. A corrected attempt may create fresh
capacity but cannot inherit unread bytes, proxy-only metadata, a stale permit,
or another HTTP/2 stream's window.

## Out of scope

Live Internet access, DNS, wall-clock races, sleeps, private container
inspection, exact repr/error prose, exact parser classes, exact frame chunking,
and a prescribed persistence layout are outside conformance. The durable state
extension records public transport intent and outcomes; it does not itself open
a network connection.
