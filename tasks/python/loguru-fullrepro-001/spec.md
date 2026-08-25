# Loguru durable relay specification

## Package contract

The package exposes a non-empty `__version__` and a ready-to-use `logger` through
`from loguru import logger`.  The familiar Loguru interfaces remain available:
sink registration and removal, named and numeric levels, structured records,
binding, contextual values, patching, filtering, serialization, exception
capture, coroutine sinks, standard-library logging handlers, file sinks and
completion of accepted work.

`logger.add()` returns a distinct active handler identifier.  A handler observes
only records accepted by its level and filter.  Stream and path output uses the
configured format, while `serialize=True` emits one JSON object containing the
rendered text and record data.  Callable sinks receive a string-like message
whose `.record` mapping contains at least the level, message and extra fields.
`logger.remove(identifier)` closes one handler and `logger.remove()` closes all.

`logger.bind()` creates an independent view.  Values supplied to
`logger.contextualize()` nest, shadow and restore according to Python context
variable semantics, including independent threads and asynchronous tasks.  A
configured patcher runs before patchers attached to a view.  Exceptions from a
handler are isolated when `catch=True` and propagated when `catch=False`.
`logger.complete()` is awaitable and finishes coroutine sinks; invoking it also
drains queued synchronous work accepted before the call.

## Durable multi-sink relay

Applications that must survive a process interruption may use `loguru.relay`.
It stores state below caller-provided directories and exposes only immutable
receipts and snapshots.  Every write operation accepts a caller-chosen
`operation_id`.  Repeating an operation with the same identity is idempotent;
reusing it for different content raises `RelayError`.  Generations increase per
logical object.  Reopening an owner on the same directory reconstructs the same
visible state.  Corrupt state or altered receipts raise `IntegrityError` before
new state becomes visible.

The module defines `RelayError`, `IntegrityError`, `OwnershipError`,
`StaleGenerationError`, `IncompleteDeliveryError`, `OwnerReceipt`,
`SinkRouteSnapshot`, `DeliveryLease`, `DispatchAttempt`,
`SinkArtifactSnapshot`, `DrainObligation`, and `DeliveryEventBatch`.
`OwnerReceipt` exposes `kind`, `task`, `operation_id`, `generation`, `owner`,
`digest`, `state`, and ordered `prerequisites`.

### Sink routes

`SinkRouteCatalog(path)` stores named route definitions.  A definition is a
mapping whose durable routing fields are `kind`, `destination`, `deps`, and
`artifacts`; other JSON-compatible policy fields are retained.  `deps` names
other routes and must form a complete acyclic graph without duplicates.

- `prepare(name, definition, *, owner, operation_id)` returns a prepared
  receipt without changing the current route.
- `commit(receipt)` atomically publishes and returns a `SinkRouteSnapshot`.
- `get(name)` returns the current snapshot.
- `recover(operation_id, *, owner)` returns the prepared receipt or committed
  snapshot and rejects a different owner.

### Delivery leases

`DeliveryLeaseRegistry(path)` owns the dependency closure selected for one
delivery invocation.  `acquire(invocation_id, requested, graph, *, owner,
operation_id)` returns a `DeliveryLease`; its `selected` tuple is a stable,
deduplicated dependency-first closure.  `handoff(lease, *, new_owner,
operation_id)` transfers the same generation, `release(lease, *, operation_id)`
closes it.  `current(invocation_id)` returns the current lease and
`recover(operation_id, *, owner)` resumes an operation.  A superseded owner
cannot release or continue the transferred lease.

### Dispatch journal

`DispatchJournal(path)` separates an attempt from its terminal and acknowledged
states.  `begin(task, *, owner, operation_id, prerequisites=())` creates a
prepared `DispatchAttempt`.  `complete(attempt, *, result=None, values=None)` or
`fail(attempt, *, category, detail="")` records a terminal outcome.
`acknowledge(attempt, *, owner, operation_id)` publishes a completed result as
current; a failed attempt cannot be acknowledged as successful.  `current(task)`
returns only acknowledged work and `recover(operation_id, *, owner)` preserves
ownership and exact state.

### Sink artifacts

`SinkArtifactIndex(path)` stores the exact byte renditions associated with a
route.  Text values are encoded as UTF-8.  `prepare(task, targets, *, owner,
operation_id, prerequisites=())` is invisible until `publish(receipt)`;
`seal()` combines both operations.  `read(task, target)`, `current(task)`,
`recover(operation_id, *, owner)`, and `verify(snapshot)` preserve names,
content digests, generation and receipt dependencies.  A failed replacement
does not disturb the previous published generation.

### Drain obligations

`DrainObligationLedger(path)` records resources entered while delivering a
message.  `open(task, setups, teardowns, *, owner, operation_id,
prerequisites=())` returns a `DrainObligation`.  `setup()`, `body()`, and
`teardown()` advance it.  Setup names are entered in declared order and the
corresponding teardown work is discharged in reverse order.  `close()` succeeds
only after a body outcome and every owed action; `recover()` returns the exact
next durable state.

### Delivery events

`DeliveryEventOutbox(path)` separates durable publication from subscriber
delivery.  `prepare(batch_id, events, *, owner, operation_id, prerequisites=())`
returns a receipt; `publish(receipt)` makes one ordered `DeliveryEventBatch`
pending.  `claim(batch_id, *, owner, operation_id)` establishes a delivery
owner, and `acknowledge(batch, *, owner, operation_id)` removes the batch from
`pending()`.  `events(batch_id)` preserves event order and `recover()` resumes
each intermediate state.  Publication alone is never an acknowledgement.

### Coordinated recovery

`RecoverableLogRelay(path)` coordinates all six stores for a multi-route
delivery.  `plan(definitions, requested, *, invocation_id, owner, operation_id)`
commits the route graph and returns a prepared receipt.  `execute(receipt,
runner=None)` records each selected route.  A supplied runner receives
`(route_name, definition)` and may return
`(status, result, values, artifacts, events)`; status zero is successful.
`publish(receipt, *, owner, operation_id)` acknowledges successful dispatches
and their event batches.  `recover(operation_id, *, owner, runner=None)` resumes
prepared or executed work without duplicating a committed delivery.

`handoff(operation_id, *, current_owner, new_owner, transfer_operation_id)` is
allowed only before execution and fences the former owner.  `current(route)`
returns the last published coordinated receipt, `verify(receipt)` checks the
complete receipt closure, and `owner_generations(route)` reports the definition,
selection, journal, artifact, lifecycle and outbox generations.  Failure,
incomplete cleanup, corrupt artifacts or a stale owner must leave the previous
published generation visible.

## Operational boundaries

State writes must be atomic within one local filesystem.  Receipt digests are
deterministic for equivalent content.  Network delivery, distributed locking,
encryption, remote databases, private Loguru implementation layout and exact
diagnostic wording are outside this contract.
