# structlog durable delivery extension

structlog continues to provide its ordinary public logging, processor, context-variable, testing, and standard-library integration APIs.  This extension adds an offline state model for applications that must preserve the provenance and delivery status of structured events across configuration changes and process restarts.

The extension is available as `structlog.delivery`.  It does not start threads, perform I/O, or read a clock.  Identifiers are non-empty strings.  Times are finite numbers; durations are positive finite numbers.  Public records are plain dictionaries or tuples and are returned as independent copies.  Callers supply every time value, so equal inputs and operation order produce equal observable state.

## `DeliveryState`

`DeliveryState()` creates an empty delivery state.  Its public methods are described below.  A failed operation leaves every public view, counter, lease, and audit record unchanged.

### Prepared processor graphs and configuration generations

`prepare(generation, *, processors, sinks, parent=None) -> dict` registers a configuration without making it active.  `processors` is a sequence of mappings with a unique `name` and an `after` collection naming predecessor processors.  Dependencies must be internal to the submitted graph and acyclic.  The deterministic processor order preserves declaration order among simultaneously ready nodes.  `sinks` is a sequence of mappings with a unique `name`, positive integer `capacity`, and non-negative integer `retry_limit`.  A parent, when supplied, names an existing generation.

`activate(generation, *, expected_active) -> dict` activates a prepared generation only if `expected_active` is the currently active generation (including `None` before the first activation).  The prior active generation becomes retired.  A failed comparison or invalid target changes neither generation.  Retired configurations remain readable and may finish events that began while they were active.

`configuration(generation) -> dict`, `configurations() -> list[dict]`, and `active_generation() -> str | None` expose independent views.  Registration order is stable.  Configuration records include state and the computed processor order.

### Context ownership and handoff provenance

`open_context(owner, values=None) -> dict` creates an owned context.  `fork_context(token, *, owner, inherit=None, values=None) -> dict` creates an independent child.  `inherit=None` copies all parent fields; otherwise it copies only the named fields.  Child values override inherited values.  Each stored field retains provenance identifying the context token that supplied it.

`handoff_context(token) -> dict` returns a sealed JSON-compatible handoff document.  `accept_handoff(document, *, owner, values=None) -> dict` validates the seal before creating a new owned context; local values override handed-off values.  Mutation of either the handoff document or returned records cannot mutate state.  The contract applies equally when the handoff crosses an asynchronous task, thread, or process boundary; no ambient context is consulted.

`merge_context(token, fields=None) -> dict` returns `values` and `provenance`.  Call fields override context fields and are marked with call provenance.  `context(token) -> dict` and `contexts(*, owner=None) -> list[dict]` return independent views in creation order.

### Cross-view event transactions

`begin(event_id, *, context, fields=None) -> dict` opens an event under the configuration active at that instant.  The event pins that generation even if another generation is activated later.  Context and call fields are merged according to the rules above.

`stage(event_id, processor, *, patch=None, remove=()) -> dict` applies the next processor in the pinned graph.  Processors may replace fields and remove existing fields; every affected field records processor provenance.  A processor may be staged only once and only after all of its predecessors.  Invalid patches, removals, or order do not partially advance the transaction.

`commit(event_id) -> dict` requires every processor to have completed.  It atomically marks the event committed and creates one pending delivery per sink of the pinned generation.  `rollback(event_id, *, reason) -> dict` aborts an open event and creates no deliveries.  Event identifiers are unique across open and terminal events.  `event(event_id)`, `events(*, state=None)`, and `deliveries(*, sink=None, status=None)` return independent deterministic views.

### Sink leases, backpressure, retries, and poison compensation

`claim(sink, event_id, *, worker, now, ttl) -> dict` leases a ready delivery.  A sink may have at most its configured capacity in live leases.  Tokens are opaque and unique.  Lease generations increase on every later claim of the same delivery.  A live lease excludes every worker.

`acknowledge(sink, event_id, token, *, now) -> dict` marks the matching live delivery delivered.  `fail(sink, event_id, token, *, reason, retryable, now, backoff=0) -> dict` consumes the lease and increments attempts.  A retryable failure whose retry limit is not exceeded becomes retryable at `now + backoff`; otherwise it becomes poisoned.  Claims before that time fail.  `compensate(sink, event_id, *, reason) -> dict` moves a poisoned delivery to compensated and is otherwise rejected.

`expire(*, now) -> list[dict]` consumes leases whose expiry is not later than `now` and returns their deliveries to retry without acknowledging them.  Stale or expired tokens cannot acknowledge or fail a delivery.  Failures on one sink do not change sibling sink deliveries for the same event.

`reconcile(*, now) -> dict` expires due leases, then reports ready deliveries, live leased deliveries, poisoned deliveries, and the active generation.  Ready order is commit order followed by sink declaration order.  Apart from lease expiry, reconciliation is observational.

### Audit chain and restart

Every successful activation, event commit or rollback, acknowledgement, failed attempt, lease expiry, and compensation appends an audit record.  Each record contains a monotonic `sequence`, a `kind`, a stable subject, a `previous_hash`, and a hash covering those fields and its detail.  `audit(*, after=0) -> list[dict]` returns records after a sequence.  `verify_audit() -> bool` verifies sequence continuity and the full hash chain.

`snapshot() -> dict` returns a complete JSON-compatible document containing configurations, active generation, contexts and provenance, events, deliveries, leases, audit records, ordering counters, and token counters.  `DeliveryState.from_snapshot(document) -> DeliveryState` constructs an independent state after validating schema, uniqueness, counters, graph order, references, state/lease agreement, pinned generations, sink membership, terminal relationships, handoff and audit hashes, and cross-view consistency.  Malformed or contradictory documents are rejected.  Snapshot/reopen cycles preserve all public views and allow pending work, retries, and active leases to continue under the same fencing rules.

The restart contract is cross-plane: an accepted handoff context, an event pinned to a retired generation, and a lease acquired before restart must remain mutually consistent after reopen.  In particular the active generation, context provenance, pinned event generation, expiry fencing, later lease generation, and continued audit chain cannot be reconstructed as unrelated local views.

## Scope

The extension specifies durable state transitions and public records, not storage layout, classes used internally, hash library objects, exact token spelling, or exception prose.  Invalid inputs raise a suitable `ValueError`, `KeyError`, or `RuntimeError`.  Exact event examples, evaluator ordering, private attributes, and a particular implementation algorithm are not part of the product contract.
