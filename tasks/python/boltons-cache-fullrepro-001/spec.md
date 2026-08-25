# Boltons sharded cache fabric

The ordinary public behavior of `boltons.cacheutils.LRI`, `LRU`,
`make_cache_key`, `cached`, and `cachedmethod` remains available.  Insertion-
age and least-recently-used eviction, overwrite behavior, counters, typed keys,
call suppression, and recomputation retain the declared runtime's semantics.

The new module `boltons.cachefabric` supplies a deterministic, offline cache
fabric.  It performs no I/O, reads no clock, creates no thread, and uses no
randomness.  Names, owners, transaction identifiers, operation identifiers,
delivery tokens, and reasons are non-empty strings.  Generations, revisions,
capacities, costs, budgets, sequences, and attempt limits are positive integers
where present.  Values and durable keys are finite JSON data.  Public views are
independent copies.  A failed operation leaves topology, entries, order,
budgets, graphs, transactions, revision history, deliveries, and snapshots
unchanged.

## Construction, routing, and topology generations

`CacheFabric(*, shards, layers, capacity, admission_budget, eviction_budget,
max_attempts=3)` creates revision one and topology generation one.  Shards and
layers are non-empty ordered sequences of unique names; later layers have
higher precedence.  Capacity and both budgets are positive per-shard integers,
accepted either as one integer for every shard or as an exact shard mapping.

`canonical_key(value)` returns a stable JSON string.  Mapping order and equal
finite numeric values are canonicalized recursively; unsupported values are
rejected.  `route(key, *, expected_generation=None)` hashes that canonical key
onto the ordered shard ring and returns the key, canonical key, shard, and
generation without mutating the fabric.  `topology()`, `entries(shard=None)`,
`budgets()`, `dependencies()`, `history()`, and `revision()` return independent
views in topology, shard eviction, dependency, or revision order.

`reconfigure(*, shards=None, layers=None, expected_generation,
expected_revision)` creates the next topology generation.  Existing entries
are routed again in their prior global order, preserving values, owners,
layers, costs, and dependencies.  New shards receive the constructor's default
limits; removed shards disappear only after successful re-routing.  Capacity
evictions consume the destination shard's eviction budget.  Open transactions
and route plans pinned to the old generation become fenced.  The change is one
atomic revision.

## Layered values and dependency invalidation

An entry has a durable key, value, owner, configured layer, positive admission
cost, and zero or more dependency keys.  Dependencies form an acyclic directed
graph in which an entry depends on the listed keys.  A dependency need not
currently have a value, but self-dependencies and cycles are invalid.

`put(key, value, *, layer, owner, cost=1, depends_on=(),
expected_generation, expected_revision) -> dict` routes and admits one entry.
For the same key, a lower-precedence layer cannot replace a higher layer; an
equal or higher layer overwrites as a new insertion.  Admission consumes the
destination budget.  Overwrite or removal refunds the old cost up to the
shard's configured admission limit.  Capacity evictions consume eviction
budget and refund evicted admission cost.  Evicting or invalidating an entry
also invalidates every transitive dependent in deterministic breadth-first
order, using shard order and entry order as tie breakers.

`invalidate(keys, *, owner, expected_generation, expected_revision) -> dict`
removes the union of the requested keys and their transitive dependents.
Requested order is stable after duplicate canonical keys are removed.  Missing
keys may seed dependency closure but are otherwise no-ops.  Removed costs are
refunded.  The entire closure is one atomic revision.

`replenish(shard, *, admission=0, eviction=0, expected_revision) -> dict`
adds non-negative budget without exceeding each shard's configured limits.
At least one amount must be positive.  Budget exhaustion rejects the whole
operation that would consume it.

## Fenced plans, transactions, and compensation

`begin(transaction, *, owner, expected_generation, expected_revision) ->
dict` opens a globally unique transaction pinned to generation and revision.
`stage(transaction, key, value, *, layer, cost=1, depends_on=()) -> dict`
replaces the transaction's staged proposal for the same key and layer while
preserving the proposal's first stage position.

`plan(transaction) -> dict` is a non-mutating route/dependency DAG.  For each
key only the highest configured staged layer wins, with later staging breaking
a same-layer tie.  The plan contains its pinned generation and revision,
deterministic winning operations, dependency edges, per-shard admission and
worst-case eviction requirements, and a digest over the plan.  Planning rejects
cycles, unknown layers, lower-layer overwrites, and impossible budgets.

`commit(transaction, plan_digest, *, operation_id) -> dict` revalidates the
transaction, plan digest, topology generation, revision, dependencies, layer
precedence, and budgets before applying every winner in plan order.  It is one
revision and one history record.  Reusing the same operation identifier with
the same committed intent returns the prior result; a different intent is an
error.  `rollback(transaction, *, reason) -> dict` makes any open transaction
terminal without changing entries.  Terminal identifiers cannot be reused.

Each content-changing history record contains complete before and after entry,
dependency, order, and budget images plus a chained digest.  `compensate(
revision, *, reason, owner, expected_generation, expected_revision,
operation_id) -> dict` applies the target record's before image as a new
ordinary revision.  Compensation never rewinds revision, generation, delivery
counters, or history; it records the target and reason and is idempotent by
operation identifier.  A target may be compensated at most once.

## Durable write-back delivery

`subscribe(sink, *, max_attempts=None) -> dict` registers a durable sink in
registration order.  Content-changing revisions enqueue one delivery per sink
in that order.  A delivery contains a globally monotonic token and sequence,
revision, generation, content digest, state, attempt count, and failure reason.

`deliver(token, sink) -> dict` moves `pending` or `retryable` work to
`delivered` and increments attempts.  `ack(token, sink, *, operation_id) ->
dict` moves delivered work to `acknowledged`.  `retry(token, sink, *, reason,
operation_id) -> dict` records a failed delivered attempt and returns the work
to `retryable`, or to `exhausted` when its attempt limit is reached.  Repeating
an acknowledgement or retry operation identifier with the same intent is
idempotent.  Foreign tokens, invalid states, and changed intents fail without
mutation.  `deliveries(*, sink=None, after=0)` filters without renumbering.

## Snapshots and reopen

`snapshot() -> dict` returns a complete finite JSON document containing schema,
lineage, topology and its generation, ordered entries, dependency graph,
budgets and limits, open and terminal transactions, history chain,
compensations, subscribers, deliveries, idempotency records, all counters, and
a digest over the document.  Equal state produces an equal snapshot.

`CacheFabric.from_snapshot(document)` validates schema, uniqueness, canonical
keys, routing, layer membership, order, capacities, dependency acyclicity,
budgets, generation/revision fencing, transaction terminal relationships,
history and delivery chains, counters, references, idempotency records, and the
outer digest before constructing an independent fabric.  Reopen preserves
route results, live transaction fencing, remaining budgets, delivery attempts,
lineage, counters, and the ability to continue every digest chain.

## Federation and anti-entropy

`export(*, owner) -> dict` returns a sealed independent document containing the
source lineage, revision, topology generation, routing definition, ordered
entries and dependencies, budget limits, history head, acknowledged delivery
content digests, and a digest over the document.

`reconcile(document, *, owner, expected_generation, expected_revision,
replace=False, operation_id) -> dict` validates the seal and requires the same
ordered shard and layer topology.  Remote entries are considered in remote
shard and eviction order.  Equal entry records are idempotent.  Missing records
are admitted using ordinary local routing and budgets.  A differing record is
a conflict unless replacement is enabled and the reconciliation owner owns the
local value; replacements take that owner.  Dependencies are validated as one
combined graph.  Remote acknowledgement digests suppress equivalent pending
local work but never acknowledge different content.  Capacity eviction,
dependency invalidation, budget use, history, and new deliveries use ordinary
local rules.  Any later conflict rolls back the whole reconciliation.

Operation identifiers are idempotent only for byte-equivalent reconciliation
intent.  Divergent reopened fabrics share a lineage but not mutable state;
anti-entropy never bypasses explicit generation, revision, ownership, budget,
dependency, or delivery rules.

## Scope and generation rules

The contract defines externally observable state transitions, deterministic
ordering, fencing, and integrity relations.  It does not prescribe private
classes, token spelling, hash objects, storage layout, or exception prose.
Invalid inputs raise a suitable `ValueError`, `KeyError`, or `RuntimeError`.

Capability instances are generated across multiple shard counts, layer
orders, capacities, dependency depths, transaction sizes, delivery states,
snapshot boundaries, and federation histories.  Composition capabilities join
at least two workflow planes; system capabilities cross a generation,
snapshot/reopen boundary, compensation boundary, or federation boundary.

